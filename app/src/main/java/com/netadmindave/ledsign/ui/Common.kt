package com.netadmindave.ledsign.ui

import android.app.Application
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.netadmindave.ledsign.ble.SignBle
import com.netadmindave.ledsign.data.LedAnimation
import com.netadmindave.ledsign.data.LedColors
import com.netadmindave.ledsign.data.Library
import com.netadmindave.ledsign.protocol.CoolLedX
import com.netadmindave.ledsign.protocol.PixelGrid
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

// ------------------------------------------------------------------ theme
private val Scheme = darkColorScheme(
    primary = Color(0xFFFFB347), onPrimary = Color(0xFF231400),
    secondary = Color(0xFF6EC6FF), background = Color(0xFF111116), surface = Color(0xFF1A1A21),
    surfaceVariant = Color(0xFF262630), onSurface = Color(0xFFECECF1),
)

@Composable
fun LedTheme(content: @Composable () -> Unit) = MaterialTheme(colorScheme = Scheme, content = content)

// ------------------------------------------------------------------ LED preview
/**
 * Draws a grid as round LEDs. If [frames] has >1 entry it animates at [speedMs].
 * [scrollMode] simulates the sign's own text scrolling for wide grids.
 */
@Composable
fun LedPreview(
    frames: List<PixelGrid>,
    speedMs: Int,
    modifier: Modifier = Modifier,
    panelW: Int = 64,
    panelH: Int = 16,
    scrollMode: CoolLedX.Mode? = null,
    playing: Boolean = true,
) {
    var idx by remember(frames) { mutableIntStateOf(0) }
    var offset by remember(frames, scrollMode) { mutableIntStateOf(0) }
    val wide = frames.firstOrNull()?.let { it.width > panelW } ?: false
    LaunchedEffect(frames, speedMs, playing, scrollMode) {
        if (!playing) return@LaunchedEffect
        while (true) {
            if (frames.size > 1) {
                delay(speedMs.coerceIn(20, 2000).toLong()); idx = (idx + 1) % frames.size
            } else if (scrollMode != null && scrollMode != CoolLedX.Mode.STATIC) {
                delay(45); offset++
            } else return@LaunchedEffect
        }
    }
    val g = frames.getOrNull(idx) ?: return
    Canvas(
        modifier
            .fillMaxWidth()
            .aspectRatio(panelW.toFloat() / panelH)
            .clip(RoundedCornerShape(10.dp))
            .background(Color(0xFF070709))
    ) {
        val cell = size.width / panelW
        val r = cell * 0.36f
        val span = g.width + panelW
        val oy = (offset / 2) % (panelH * 2)
        val cx = if (wide) 0 else (panelW - g.width) / 2
        for (y in 0 until panelH) for (x in 0 until panelW) {
            val (sx, sy) = when (scrollMode) {
                CoolLedX.Mode.LEFT -> Pair(x + (offset % span) - panelW, y)
                CoolLedX.Mode.RIGHT -> Pair(x - (offset % span) + g.width, y)
                CoolLedX.Mode.UP -> Pair(x - cx, y + oy - panelH)
                CoolLedX.Mode.DOWN -> Pair(x - cx, y - oy + panelH)
                else -> Pair(x - cx, y - (panelH - g.height) / 2)
            }
            val c = if (sx in 0 until g.width && sy in 0 until g.height) g[sx, sy] else 0
            drawCircle(Color(LedColors.argb[c]), r, Offset((x + 0.5f) * cell, (y + 0.5f) * cell))
        }
    }
}


// ------------------------------------------------------------------ view model
class AppVM(app: Application) : AndroidViewModel(app) {
    val ble = SignBle(app)
    val builtIn: List<LedAnimation> by lazy { Library.builtIn(app) }

    private val _creations: MutableStateFlow<List<LedAnimation>> =
        MutableStateFlow(com.netadmindave.ledsign.data.Library.creations(app))
    val creations: StateFlow<List<LedAnimation>> = _creations.asStateFlow()
    private val _favs: MutableStateFlow<Set<String>> =
        MutableStateFlow(com.netadmindave.ledsign.data.Library.favorites(app))
    val favs: StateFlow<Set<String>> = _favs.asStateFlow()

    /** Shared with the Draw tab when the user picks "Edit a copy". */
    val editRequest = MutableStateFlow<LedAnimation?>(null)

    fun toggleFav(id: String) { _favs.value = Library.toggleFavorite(getApplication(), id) }

    fun save(a: LedAnimation) {
        Library.saveCreation(getApplication(), a)
        _creations.value = Library.creations(getApplication())
    }

    fun delete(id: String) {
        Library.deleteCreation(getApplication(), id)
        _creations.value = Library.creations(getApplication())
    }

    // ---------------------------------------------------------------- orientation
    private val prefs = app.getSharedPreferences("sign", android.content.Context.MODE_PRIVATE)
    private val _flip = MutableStateFlow(prefs.getBoolean("flip", false))
    val flip: StateFlow<Boolean> = _flip.asStateFlow()
    private val _mirror = MutableStateFlow(prefs.getBoolean("mirror", false))
    val mirror: StateFlow<Boolean> = _mirror.asStateFlow()
    fun setFlip(v: Boolean) { _flip.value = v; prefs.edit().putBoolean("flip", v).apply() }
    fun setMirror(v: Boolean) { _mirror.value = v; prefs.edit().putBoolean("mirror", v).apply() }

    private fun orient(g: PixelGrid): PixelGrid {
        var o = g
        if (_mirror.value) o = o.mirrored()
        if (_flip.value) o = o.rotated180()
        return o
    }

    /** Scrolling direction as seen by the viewer must survive the flip/mirror. */
    private fun orientMode(m: CoolLedX.Mode): CoolLedX.Mode {
        var mode = m
        if (_mirror.value xor _flip.value) mode = when (mode) {
            CoolLedX.Mode.LEFT -> CoolLedX.Mode.RIGHT; CoolLedX.Mode.RIGHT -> CoolLedX.Mode.LEFT; else -> mode
        }
        if (_flip.value) mode = when (mode) {
            CoolLedX.Mode.UP -> CoolLedX.Mode.DOWN; CoolLedX.Mode.DOWN -> CoolLedX.Mode.UP; else -> mode
        }
        return mode
    }

    fun panel(): Pair<Int, Int> {
        val s = ble.connected.value
        return (s?.cols ?: 64) to (s?.rows ?: 16)
    }

    fun sendAnimation(frames: List<PixelGrid>, speedMs: Int, label: String) = viewModelScope.launch {
        val (w, h) = panel()
        val fitted = withContext(Dispatchers.Default) { frames.map { orient(it.fitTo(w, h)) } }
        if (fitted.size == 1) {
            val packets = withContext(Dispatchers.Default) { CoolLedX.sendImage(fitted[0]) }
            ble.upload(CoolLedX.CMD_TEXT, packets, label,
                before = listOf(CoolLedX.mode(CoolLedX.Mode.STATIC)), after = listOf(CoolLedX.mode(CoolLedX.Mode.STATIC)))
        } else {
            val packets = withContext(Dispatchers.Default) {
                CoolLedX.sendAnimation(fitted.take(minOf(79, CoolLedX.maxFramesFor(w, h))), speedMs.coerceIn(20, 2000))
            }
            ble.upload(CoolLedX.CMD_ANIMATION, packets, label)
        }
    }

    fun sendText(text: String, grid: PixelGrid, mode: CoolLedX.Mode, speed: Int) = viewModelScope.launch {
        val m = orientMode(mode)
        val packets = withContext(Dispatchers.Default) { CoolLedX.sendText(text, orient(grid)) }
        val modeCmds = listOf(CoolLedX.mode(m), CoolLedX.speed(speed))
        ble.upload(CoolLedX.CMD_TEXT, packets, "\"$text\"", before = modeCmds, after = listOf(CoolLedX.mode(m)))
    }

    /** Two-frame test: red left half / blue right half, then swapped, with a white top-left corner marker. */
    fun sendTestPattern() {
        val (w, h) = panel()
        fun frame(a: Int, b: Int) = PixelGrid(w, h).also { g ->
            for (y in 0 until h) for (x in 0 until w) g[x, y] = if (x < w / 2) a else b
            for (k in 0 until 4) { g[k, 0] = 7; g[0, k] = 7 }
        }
        sendAnimation(listOf(frame(1, 4), frame(4, 1)), 500, "Test pattern")
    }

    fun brightness(v: Int) = viewModelScope.launch { ble.sendCommands(listOf(CoolLedX.brightness(v))) }
    fun power(on: Boolean) = viewModelScope.launch { ble.sendCommands(listOf(CoolLedX.power(on))) }

    override fun onCleared() { ble.disconnect() }
}
