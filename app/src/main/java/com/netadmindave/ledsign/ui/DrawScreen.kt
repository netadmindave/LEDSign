package com.netadmindave.ledsign.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.netadmindave.ledsign.data.LedAnimation
import com.netadmindave.ledsign.data.LedColors
import com.netadmindave.ledsign.protocol.PixelGrid

@Composable
fun DrawScreen(vm: AppVM) {
    val (pw, ph) = vm.panel()
    val request by vm.editRequest.collectAsState()
    var frames by remember { mutableStateOf(listOf(PixelGrid(pw, ph))) }
    var cur by remember { mutableIntStateOf(0) }
    var color by remember { mutableIntStateOf(3) }
    var speed by remember { mutableFloatStateOf(150f) }
    var name by remember { mutableStateOf("My design") }
    var editingId by remember { mutableStateOf<String?>(null) }
    var tick by remember { mutableIntStateOf(0) }   // forces redraw after in-place edits
    var preview by remember { mutableStateOf(false) }
    var saved by remember { mutableStateOf(false) }

    LaunchedEffect(request) {
        request?.let { a ->
            frames = a.frames.map { it.copy().fitTo(pw, ph) }
            cur = 0; speed = a.speedMs.toFloat()
            name = if (a.builtIn) "${a.name} (copy)" else a.name
            editingId = if (a.builtIn) null else a.id
            vm.editRequest.value = null
        }
    }

    fun paint(off: Offset, cell: Float) {
        val x = (off.x / cell).toInt(); val y = (off.y / cell).toInt()
        val g = frames[cur]
        if (x in 0 until g.width && y in 0 until g.height && g[x, y] != color) { g[x, y] = color; tick++ }
    }

    fun shift(dx: Int, dy: Int) {
        val g = frames[cur]; val n = PixelGrid(g.width, g.height)
        for (y in 0 until g.height) for (x in 0 until g.width) {
            n[(x + dx + g.width) % g.width, (y + dy + g.height) % g.height] = g[x, y]
        }
        frames = frames.toMutableList().also { it[cur] = n }
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)) {

        if (preview) {
            LedPreview(frames, speed.toInt(), panelW = pw, panelH = ph)
        } else {
            val g = frames[cur]
            val prev = if (cur > 0) frames[cur - 1] else null
            Canvas(
                Modifier.fillMaxWidth().aspectRatio(pw.toFloat() / ph).background(Color(0xFF070709))
                    .pointerInput(cur, color) {
                        detectTapGestures { paint(it, size.width.toFloat() / pw) }
                    }
                    .pointerInput(cur, color) {
                        detectDragGestures { change, _ -> paint(change.position, size.width.toFloat() / pw) }
                    }
            ) {
                if (tick < 0) return@Canvas
                val cell = size.width / pw
                for (y in 0 until ph) for (x in 0 until pw) {
                    val c = g[x, y]
                    val col = when {
                        c != 0 -> Color(LedColors.argb[c])
                        prev != null && prev[x, y] != 0 -> Color(LedColors.argb[prev[x, y]]).copy(alpha = 0.18f) // onion skin
                        else -> Color(0xFF24242B)
                    }
                    drawRect(col, Offset(x * cell + 0.5f, y * cell + 0.5f), Size(cell - 1f, cell - 1f))
                }
                for (x in 8 until pw step 8) drawLine(Color(0x33FFFFFF), Offset(x * cell, 0f), Offset(x * cell, size.height))
                drawLine(Color(0x33FFFFFF), Offset(0f, size.height / 2), Offset(size.width, size.height / 2))
            }
        }

        Row(Modifier.horizontalScroll(rememberScrollState()), verticalAlignment = Alignment.CenterVertically) {
            ColorPicker(color, { color = it }, includeOff = true)
        }

        // tools
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            FilledTonalIconButton({ shift(-1, 0) }) { Icon(Icons.Filled.KeyboardArrowLeft, "Shift left") }
            FilledTonalIconButton({ shift(1, 0) }) { Icon(Icons.Filled.KeyboardArrowRight, "Shift right") }
            FilledTonalIconButton({ shift(0, -1) }) { Icon(Icons.Filled.KeyboardArrowUp, "Shift up") }
            FilledTonalIconButton({ shift(0, 1) }) { Icon(Icons.Filled.KeyboardArrowDown, "Shift down") }
            FilledTonalIconButton({ frames = frames.toMutableList().also { it[cur] = PixelGrid(pw, ph) } }) {
                Icon(Icons.Filled.LayersClear, "Clear frame")
            }
            FilledTonalIconButton({ preview = !preview }) {
                Icon(if (preview) Icons.Filled.Edit else Icons.Filled.PlayArrow, if (preview) "Edit" else "Play")
            }
        }

        // frames
        Text("Frame ${cur + 1} of ${frames.size}", fontWeight = FontWeight.SemiBold)
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            OutlinedIconButton({ if (cur > 0) cur-- }) { Icon(Icons.Filled.SkipPrevious, "Previous frame") }
            OutlinedIconButton({ if (cur < frames.size - 1) cur++ }) { Icon(Icons.Filled.SkipNext, "Next frame") }
            OutlinedButton({
                if (frames.size < 64) { frames = frames.toMutableList().also { it.add(cur + 1, PixelGrid(pw, ph)) }; cur++ }
            }) { Text("+ Blank") }
            OutlinedButton({
                if (frames.size < 64) { frames = frames.toMutableList().also { it.add(cur + 1, frames[cur].copy()) }; cur++ }
            }) { Text("+ Copy") }
            OutlinedButton({
                if (frames.size > 1) { frames = frames.toMutableList().also { it.removeAt(cur) }; cur = cur.coerceAtMost(frames.size - 1) }
            }) { Text("Delete") }
        }
        if (frames.size > 1) {
            Text("Frame time: ${speed.toInt()} ms")
            Slider(speed, { speed = it }, valueRange = 40f..600f)
        }
        OutlinedTextField(name, { name = it; saved = false }, label = { Text("Name") }, singleLine = true,
            modifier = Modifier.fillMaxWidth())
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton({
                val id = editingId ?: ("u" + System.currentTimeMillis())
                editingId = id
                vm.save(LedAnimation(id, name, "My Creations", speed.toInt(), frames.map { it.copy() }, false))
                saved = true
            }, Modifier.weight(1f)) { Icon(Icons.Filled.Save, null); Spacer(Modifier.width(6.dp)); Text(if (saved) "Saved" else "Save") }
            Button({ vm.sendAnimation(frames.map { it.copy() }, speed.toInt(), name) }, Modifier.weight(1f)) {
                Icon(Icons.Filled.Send, null); Spacer(Modifier.width(6.dp)); Text("Show on sign")
            }
        }
        TextButton({
            frames = listOf(PixelGrid(pw, ph)); cur = 0; editingId = null; name = "My design"; saved = false
        }) { Text("Start a new design") }
    }
}
