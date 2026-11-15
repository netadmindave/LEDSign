package com.netadmindave.ledsign

import com.netadmindave.ledsign.protocol.CoolLedX
import com.netadmindave.ledsign.protocol.PixelGrid
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Test

class ProtocolTest {
    private fun hex(b: ByteArray) = b.joinToString("") { "%02x".format(it) }

    @Test fun escapesControlBytes() {
        // payload 01 02 03 04 -> len 00 04, each 01..03 escaped as 02 (b^4)
        assertEquals("01000402050206020704" + "03", hex(CoolLedX.frame(byteArrayOf(1, 2, 3, 4))))
    }

    @Test fun roundTrip() {
        val p = byteArrayOf(0, 1, 2, 3, 7, -1)
        assertArrayEquals(p, CoolLedX.unframe(CoolLedX.frame(p)))
    }

    @Test fun simpleCommands() {
        assertEquals("01000206080a03", hex(CoolLedX.brightness(10)))   // len 0x02 is escaped too
        assertEquals("0100020609020503", hex(CoolLedX.power(true)))
    }

    @Test fun columnMajorPlanes() {
        val g = PixelGrid(64, 16)
        g[0, 0] = 1      // red, top-left -> MSB of first R byte
        g[1, 15] = 6     // cyan, bottom of column 1 -> LSB of 4th G and B bytes
        val p = CoolLedX.planes(g)
        assertEquals(0x80, p[0][0].toInt() and 0xFF)
        assertEquals(0x01, p[1][3].toInt() and 0xFF)
        assertEquals(0x01, p[2][3].toInt() and 0xFF)
        assertEquals(128, p[0].size)
    }

    @Test fun animationChunking() {
        val frames = List(16) { PixelGrid(64, 16) }
        val packets = CoolLedX.sendAnimation(frames, 90)
        // 27 header bytes + 16 frames * 384 bytes = 6171 -> 49 chunks of <=128
        assertEquals(49, packets.size)
        // chunk 0: cmd 04, 00, total 0x181b, index 0000, size 0x80 (escaping applied)
        assertEquals("0100880400181b0000800000", hex(packets[0]).substring(0, 24))
    }
}
