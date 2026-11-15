package com.netadmindave.ledsign.protocol

import java.io.ByteArrayOutputStream

/**
 * Pixel grid: one Int per pixel, row-major, value 0..7 where
 * bit0 = red, bit1 = green, bit2 = blue (the sign's 7 colours + off).
 */
class PixelGrid(val width: Int, val height: Int, val px: IntArray = IntArray(width * height)) {
    operator fun get(x: Int, y: Int): Int = px[y * width + x]
    operator fun set(x: Int, y: Int, c: Int) {
        if (x in 0 until width && y in 0 until height) px[y * width + x] = c and 7
    }
    fun copy() = PixelGrid(width, height, px.copyOf())

    /** Turn upside-down (for a sign mounted inverted). */
    fun rotated180(): PixelGrid {
        val o = PixelGrid(width, height)
        for (y in 0 until height) for (x in 0 until width) o[width - 1 - x, height - 1 - y] = this[x, y]
        return o
    }

    /** Left-right mirror (for reading through glass from behind). */
    fun mirrored(): PixelGrid {
        val o = PixelGrid(width, height)
        for (y in 0 until height) for (x in 0 until width) o[width - 1 - x, y] = this[x, y]
        return o
    }

    /** Centre this grid on a canvas of the given size (crops or pads). */
    fun fitTo(w: Int, h: Int): PixelGrid {
        if (w == width && h == height) return this
        val out = PixelGrid(w, h)
        val ox = (w - width) / 2
        val oy = (h - height) / 2
        for (y in 0 until height) for (x in 0 until width) {
            val tx = x + ox
            val ty = y + oy
            if (tx in 0 until w && ty in 0 until h) out[tx, ty] = this[x, y]
        }
        return out
    }
}

/**
 * Encoder for the CoolLEDX ("CoolLED1248"-family) BLE protocol.
 *
 * Wire format of every write:   0x01 | escape(len_hi len_lo payload...) | 0x03
 * where bytes 0x01..0x03 inside are sent as 0x02, (b xor 0x04).
 *
 * Large payloads (text / image / animation) are split into 128-byte chunks:
 *   cmd | 0x00 | total_len(2) | chunk_index(2) | chunk_len(1) | data | xor
 * and each chunk is framed separately; the sign notifies after each one.
 *
 * Reference: open-source reverse-engineering in UpDryTwist/coolledx-driver and
 * oe7set/CoolLedDiy (both MIT/community projects).
 */
object CoolLedX {
    const val CMD_MUSIC = 0x01
    const val CMD_TEXT = 0x02
    const val CMD_IMAGE = 0x03
    const val CMD_ANIMATION = 0x04
    const val CMD_MODE = 0x06
    const val CMD_SPEED = 0x07
    const val CMD_BRIGHTNESS = 0x08
    const val CMD_SWITCH = 0x09

    const val CHUNK = 128
    const val MAX_PAYLOAD = 0xFFFF

    enum class Mode(val code: Int, val label: String) {
        STATIC(1, "Still"), LEFT(2, "Scroll left"), RIGHT(3, "Scroll right"),
        UP(4, "Scroll up"), DOWN(5, "Scroll down"), SNOW(6, "Snowflake"),
        PICTURE(7, "Picture"), LASER(8, "Laser")
    }

    // ------------------------------------------------------------ framing
    fun frame(payload: ByteArray): ByteArray {
        val out = ByteArrayOutputStream(payload.size + 8)
        out.write(0x01)
        fun put(v: Int) {
            if (v in 1..3) { out.write(0x02); out.write(v xor 0x04) } else out.write(v)
        }
        put((payload.size shr 8) and 0xFF)
        put(payload.size and 0xFF)
        for (b in payload) put(b.toInt() and 0xFF)
        out.write(0x03)
        return out.toByteArray()
    }

    fun unframe(data: ByteArray): ByteArray? {
        if (data.size < 4 || data[0].toInt() != 1 || data.last().toInt() != 3) return null
        val out = ByteArrayOutputStream()
        var i = 1
        while (i < data.size - 1) {
            val v = data[i].toInt() and 0xFF
            if (v == 2 && i + 1 < data.size - 1) { out.write((data[i + 1].toInt() and 0xFF) xor 4); i += 2 }
            else { out.write(v); i++ }
        }
        val b = out.toByteArray()
        return if (b.size >= 2) b.copyOfRange(2, b.size) else null
    }

    /** Split a large payload into framed 128-byte chunks for the given command. */
    fun chunked(cmd: Int, data: ByteArray): List<ByteArray> {
        require(data.size <= MAX_PAYLOAD) { "Payload too large (${data.size} bytes)" }
        val frames = ArrayList<ByteArray>()
        var idx = 0
        var off = 0
        while (off < data.size) {
            val n = minOf(CHUNK, data.size - off)
            val body = ByteArrayOutputStream(n + 8)
            body.write(0x00)
            body.write((data.size shr 8) and 0xFF); body.write(data.size and 0xFF)
            body.write((idx shr 8) and 0xFF); body.write(idx and 0xFF)
            body.write(n)
            body.write(data, off, n)
            val bytes = body.toByteArray()
            var x = 0
            for (b in bytes) x = x xor (b.toInt() and 0xFF)
            frames += frame(byteArrayOf(cmd.toByte()) + bytes + byteArrayOf(x.toByte()))
            off += n
            idx++
        }
        return frames
    }

    // ------------------------------------------------------------ simple commands
    fun brightness(v: Int) = frame(byteArrayOf(CMD_BRIGHTNESS.toByte(), v.coerceIn(0, 255).toByte()))
    fun speed(v: Int) = frame(byteArrayOf(CMD_SPEED.toByte(), v.coerceIn(0, 255).toByte()))
    fun mode(m: Mode) = frame(byteArrayOf(CMD_MODE.toByte(), m.code.toByte()))
    fun power(on: Boolean) = frame(byteArrayOf(CMD_SWITCH.toByte(), if (on) 1 else 0))
    /** Stock app "reverse": rotates the whole display 180 degrees on the sign itself. */
    fun reverse(on: Boolean) = frame(byteArrayOf(0x0C, if (on) 1 else 0))

    // ------------------------------------------------------------ pixel encoding
    /**
     * Column-major bit planes: for each column (left->right), rows top->bottom
     * packed 8 per byte, MSB = top pixel. Returns R, G, B planes.
     */
    fun planes(g: PixelGrid): Array<ByteArray> {
        require(g.height % 8 == 0) { "Height must be a multiple of 8" }
        val bpc = g.height / 8
        val r = ByteArray(g.width * bpc); val gr = ByteArray(g.width * bpc); val b = ByteArray(g.width * bpc)
        var i = 0
        for (x in 0 until g.width) {
            for (yb in 0 until bpc) {
                var vr = 0; var vg = 0; var vb = 0
                for (k in 0 until 8) {
                    val c = g[x, yb * 8 + k]
                    vr = (vr shl 1) or (c and 1)
                    vg = (vg shl 1) or ((c shr 1) and 1)
                    vb = (vb shl 1) or ((c shr 2) and 1)
                }
                r[i] = vr.toByte(); gr[i] = vg.toByte(); b[i] = vb.toByte()
                i++
            }
        }
        return arrayOf(r, gr, b)
    }

    fun imagePayload(g: PixelGrid): ByteArray {
        val p = planes(g)
        val bits = p[0] + p[1] + p[2]
        val out = ByteArrayOutputStream()
        out.write(ByteArray(24))
        out.write((bits.size shr 8) and 0xFF); out.write(bits.size and 0xFF)
        out.write(bits)
        return out.toByteArray()
    }

    /** Text is sent as a rendered image plus character metadata; the sign scrolls it per Mode. */
    fun textPayload(text: String, g: PixelGrid): ByteArray {
        val p = planes(g)
        val bits = p[0] + p[1] + p[2]
        val n = minOf(text.length, 255)
        val meta = ByteArray(80) { if (it < n) 0x30 else 0 }
        val out = ByteArrayOutputStream()
        out.write(ByteArray(24))
        out.write(n)
        out.write(meta)
        out.write((bits.size shr 8) and 0xFF); out.write(bits.size and 0xFF)
        out.write(bits)
        return out.toByteArray()
    }

    /** speed: 16-bit frame delay value as used by the stock app (bigger = slower). */
    fun animationPayload(frames: List<PixelGrid>, speed: Int): ByteArray {
        require(frames.isNotEmpty() && frames.size <= 255) { "1..255 frames" }
        val rs = ByteArrayOutputStream(); val gs = ByteArrayOutputStream(); val bs = ByteArrayOutputStream()
        for (f in frames) {
            val p = planes(f)
            rs.write(p[0]); gs.write(p[1]); bs.write(p[2])
        }
        val out = ByteArrayOutputStream()
        out.write(ByteArray(24))
        out.write(frames.size)
        val s = speed.coerceIn(1, 0xFFFF)
        out.write((s shr 8) and 0xFF); out.write(s and 0xFF)
        out.write(rs.toByteArray()); out.write(gs.toByteArray()); out.write(bs.toByteArray())
        return out.toByteArray()
    }

    /** Still image: same as the stock app's getIconDataStrings (cmd 0x03, 24 zeros + len16 + planes). */
    fun sendImage(g: PixelGrid) = chunked(CMD_IMAGE, imagePayload(g))
    fun sendText(text: String, g: PixelGrid) = chunked(CMD_TEXT, textPayload(text, g))
    fun sendAnimation(frames: List<PixelGrid>, speed: Int) = chunked(CMD_ANIMATION, animationPayload(frames, speed))

    fun maxFramesFor(width: Int, height: Int): Int {
        val perFrame = width * (height / 8) * 3
        return minOf(255, (MAX_PAYLOAD - 27) / perFrame)
    }
}
