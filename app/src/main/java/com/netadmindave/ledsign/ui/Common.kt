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

    private val _creations = MutableStateFlow(Library.creations(app))
    val creations = _creations.asStateFlow()
    private val _favs = MutableStateFlow(Library.favorites(app))
    val favs = _favs.asStateFlow()

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

    fun panel(): Pair<Int, Int> {
        val s = ble.connected.value
        return (s?.cols ?: 64) to (s?.rows ?: 16)
    }

    fun sendAnimation(frames: List<PixelGrid>, speedMs: Int, label: String) = viewModelScope.launch {
        val (w, h) = panel()
        val fitted = frames.map { it.fitTo(w, h) }
        val packets = withContext(Dispatchers.Default) {
            if (fitted.size == 1) CoolLedX.sendImage(fitted[0])
            else CoolLedX.sendAnimation(fitted.take(CoolLedX.maxFramesFor(w, h)), speedMs)
        }
        ble.send(packets, label = label)
    }

    fun sendText(text: String, grid: PixelGrid, mode: CoolLedX.Mode, speed: Int) = viewModelScope.launch {
        val packets = withContext(Dispatchers.Default) { CoolLedX.sendText(text, grid) }
        if (ble.send(packets, label = "\"$text\"")) {
            ble.send(listOf(CoolLedX.mode(mode), CoolLedX.speed(speed)), waitForAck = false)
        }
    }

    fun brightness(v: Int) = viewModelScope.launch { ble.send(listOf(CoolLedX.brightness(v)), waitForAck = false) }
    fun power(on: Boolean) = viewModelScope.launch { ble.send(listOf(CoolLedX.power(on)), waitForAck = false) }

    override fun onCleared() { ble.disconnect() }
}
