package com.netadmindave.ledsign.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Movie
import android.graphics.Paint
import android.graphics.Typeface
import android.net.Uri
import com.netadmindave.ledsign.protocol.PixelGrid
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

data class LedAnimation(
    val id: String,
    val name: String,
    val category: String,
    val speedMs: Int,
    val frames: List<PixelGrid>,
    val builtIn: Boolean = true,
)

/** The 7 colours the sign can show (index = bit mask R|G<<1|B<<2). */
object LedColors {
    val names = listOf("Off", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White")
    val argb = intArrayOf(
        0xFF2A2A30.toInt(), 0xFFFF3030.toInt(), 0xFF30FF50.toInt(), 0xFFFFE030.toInt(),
        0xFF3060FF.toInt(), 0xFFFF40FF.toInt(), 0xFF30F0FF.toInt(), 0xFFFFFFFF.toInt(),
    )
    /** Nearest sign colour for an arbitrary RGB (each channel on if > threshold). */
    fun quantize(argb: Int, threshold: Int = 110): Int {
        if (Color.alpha(argb) < 128) return 0
        val r = Color.red(argb); val g = Color.green(argb); val b = Color.blue(argb)
        return (if (r > threshold) 1 else 0) or (if (g > threshold) 2 else 0) or (if (b > threshold) 4 else 0)
    }
}

object Library {
    @Volatile private var cache: List<LedAnimation>? = null

    fun builtIn(ctx: Context): List<LedAnimation> = cache ?: synchronized(this) {
        cache ?: run {
            val json = ctx.assets.open("animations.json").bufferedReader().use { it.readText() }
            val arr = JSONObject(json).getJSONArray("animations")
            List(arr.length()) { i -> parse(arr.getJSONObject(i), true) }.also { cache = it }
        }
    }

    private fun parse(o: JSONObject, builtIn: Boolean): LedAnimation {
        val w = o.getInt("width"); val h = o.getInt("height")
        val fr = o.getJSONArray("frames")
        val frames = List(fr.length()) { k -> decodeFrame(fr.getString(k), w, h) }
        return LedAnimation(o.getString("id"), o.getString("name"), o.getString("category"),
            o.getInt("speedMs"), frames, builtIn)
    }

    private fun decodeFrame(hex: String, w: Int, h: Int): PixelGrid {
        val g = PixelGrid(w, h)
        var p = 0
        var i = 0
        while (i + 1 < hex.length && p + 1 < g.px.size) {
            val v = hex.substring(i, i + 2).toInt(16)
            g.px[p++] = (v shr 4) and 7
            g.px[p++] = v and 7
            i += 2
        }
        return g
    }

    private fun encodeFrame(g: PixelGrid): String {
        val sb = StringBuilder(g.px.size)
        var i = 0
        while (i < g.px.size) {
            val v = (g.px[i] shl 4) or (if (i + 1 < g.px.size) g.px[i + 1] else 0)
            sb.append(String.format("%02x", v)); i += 2
        }
        return sb.toString()
    }

    // ------------------------------------------------------------ user creations
    private fun file(ctx: Context) = File(ctx.filesDir, "creations.json")

    fun creations(ctx: Context): List<LedAnimation> {
        val f = file(ctx)
        if (!f.exists()) return emptyList()
        return try {
            val arr = JSONArray(f.readText())
            List(arr.length()) { parse(arr.getJSONObject(it), false) }
        } catch (e: Exception) { emptyList() }
    }

    fun saveCreation(ctx: Context, a: LedAnimation) {
        val list = creations(ctx).filter { it.id != a.id } + a
        val arr = JSONArray()
        for (x in list) {
            arr.put(JSONObject().apply {
                put("id", x.id); put("name", x.name); put("category", "My Creations")
                put("speedMs", x.speedMs); put("width", x.frames[0].width); put("height", x.frames[0].height)
                put("frames", JSONArray().apply { x.frames.forEach { put(encodeFrame(it)) } })
            })
        }
        file(ctx).writeText(arr.toString())
    }

    fun deleteCreation(ctx: Context, id: String) {
        val keep = creations(ctx).filter { it.id != id }
        file(ctx).delete()
        keep.forEach { saveCreation(ctx, it) }
    }

    // ------------------------------------------------------------ favourites
    fun favorites(ctx: Context): Set<String> =
        ctx.getSharedPreferences("lib", Context.MODE_PRIVATE).getStringSet("fav", emptySet())!!.toSet()

    fun toggleFavorite(ctx: Context, id: String): Set<String> {
        val p = ctx.getSharedPreferences("lib", Context.MODE_PRIVATE)
        val s = favorites(ctx).toMutableSet()
        if (!s.add(id)) s.remove(id)
        p.edit().putStringSet("fav", s).apply()
        return s
    }
}

// ================================================================== text rendering
object TextRender {
    /**
     * Render text into a sign-height grid using a crisp (non-antialiased) system font.
     * Width grows with the text; it's padded to at least [minWidth] and centred for still mode.
     */
    fun render(text: String, height: Int, minWidth: Int, color: Int, bold: Boolean,
               rainbow: Boolean = false, center: Boolean = true): PixelGrid {
        val paint = Paint().apply {
            isAntiAlias = false
            typeface = Typeface.create(Typeface.DEFAULT, if (bold) Typeface.BOLD else Typeface.NORMAL)
            textSize = height * 1.0f
            this.color = Color.WHITE
        }
        // shrink until cap height fits the panel
        while (paint.textSize > 6) {
            val fm = paint.fontMetrics
            if (fm.descent - fm.ascent <= height + 3) break
            paint.textSize -= 0.5f
        }
        val tw = maxOf(1, paint.measureText(text).toInt() + 2)
        val bmp = Bitmap.createBitmap(tw, height, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val fm = paint.fontMetrics
        val baseline = (height - (fm.descent + fm.ascent)) / 2f
        c.drawText(text, 1f, baseline, paint)
        val w = maxOf(tw, minWidth)
        val g = PixelGrid(w, height)
        val ox = if (center && tw < minWidth) (minWidth - tw) / 2 else 0
        val rb = intArrayOf(1, 3, 2, 6, 4, 5)
        for (y in 0 until height) for (x in 0 until tw) {
            if (Color.red(bmp.getPixel(x, y)) > 100) {
                g[x + ox, y] = if (rainbow) rb[((x + ox) / 6) % rb.size] else color
            }
        }
        bmp.recycle()
        return g
    }
}

// ================================================================== image / GIF import
object ImageImport {
    private fun toGrid(bmp: Bitmap, w: Int, h: Int, fill: Boolean): PixelGrid {
        val scale = if (fill) maxOf(w.toFloat() / bmp.width, h.toFloat() / bmp.height)
        else minOf(w.toFloat() / bmp.width, h.toFloat() / bmp.height)
        val sw = maxOf(1, (bmp.width * scale).toInt()); val sh = maxOf(1, (bmp.height * scale).toInt())
        val scaled = Bitmap.createScaledBitmap(bmp, sw, sh, true)
        val g = PixelGrid(w, h)
        val ox = (w - sw) / 2; val oy = (h - sh) / 2
        for (y in 0 until sh) for (x in 0 until sw) {
            val tx = x + ox; val ty = y + oy
            if (tx in 0 until w && ty in 0 until h) g[tx, ty] = LedColors.quantize(scaled.getPixel(x, y))
        }
        if (scaled != bmp) scaled.recycle()
        return g
    }

    /** Returns 1 frame for still images, several for animated GIFs (max [maxFrames]). */
    @Suppress("DEPRECATION")
    fun load(ctx: Context, uri: Uri, w: Int, h: Int, fill: Boolean, maxFrames: Int = 32): Pair<List<PixelGrid>, Int> {
        val bytes = ctx.contentResolver.openInputStream(uri)!!.use { it.readBytes() }
        val isGif = bytes.size > 6 && String(bytes, 0, 3) == "GIF"
        if (isGif) {
            val movie = Movie.decodeByteArray(bytes, 0, bytes.size)
            if (movie != null && movie.duration() > 0 && movie.width() > 0) {
                val dur = movie.duration()
                val n = minOf(maxFrames, maxOf(2, dur / 80))
                val step = dur / n
                val bmp = Bitmap.createBitmap(movie.width(), movie.height(), Bitmap.Config.ARGB_8888)
                val canvas = Canvas(bmp)
                val frames = (0 until n).map { k ->
                    bmp.eraseColor(Color.BLACK)
                    movie.setTime(k * step)
                    movie.draw(canvas, 0f, 0f)
                    toGrid(bmp, w, h, fill)
                }
                bmp.recycle()
                return frames to step.coerceIn(30, 1000)
            }
        }
        val bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: error("Unsupported image")
        return listOf(toGrid(bmp, w, h, fill)) to 200
    }
}
