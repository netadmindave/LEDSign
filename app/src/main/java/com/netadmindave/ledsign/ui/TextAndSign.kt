package com.netadmindave.ledsign.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.unit.dp
import com.netadmindave.ledsign.ble.LinkState
import com.netadmindave.ledsign.data.LedColors
import com.netadmindave.ledsign.data.TextRender
import com.netadmindave.ledsign.protocol.CoolLedX
import kotlinx.coroutines.launch

private val QUICK = listOf("HAPPY HALLOWEEN", "Trick or treat!", "Reading - do not disturb", "Merry Christmas",
    "Happy New Year", "Happy Thanksgiving", "Light speed ahead", "Be right back", "Welcome!")

@Composable
fun ColorPicker(selected: Int, onPick: (Int) -> Unit, includeOff: Boolean = false, rainbow: Boolean? = null,
                onRainbow: (() -> Unit)? = null) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
        for (c in (if (includeOff) 0 else 1)..7) {
            val sel = selected == c && rainbow != true
            Box(
                Modifier.size(if (sel) 36.dp else 30.dp).clip(CircleShape)
                    .background(Color(LedColors.argb[c]))
                    .border(if (sel) 3.dp else 1.dp, if (sel) Color.White else Color.Gray, CircleShape)
                    .clickable { onPick(c) }
            ) { if (c == 0) Icon(Icons.Filled.Clear, "Eraser", Modifier.align(Alignment.Center), tint = Color.White) }
        }
        if (onRainbow != null) {
            Box(
                Modifier.size(if (rainbow == true) 36.dp else 30.dp).clip(CircleShape)
                    .background(Brush.sweepGradient(LedColors.argb.drop(1).map { Color(it) }))
                    .border(if (rainbow == true) 3.dp else 1.dp, Color.White, CircleShape)
                    .clickable { onRainbow() }
            )
        }
    }
}

@Composable
fun TextScreen(vm: AppVM) {
    var text by rememberSaveable { mutableStateOf("HAPPY HALLOWEEN") }
    var color by rememberSaveable { mutableIntStateOf(3) }
    var rainbow by rememberSaveable { mutableStateOf(false) }
    var bold by rememberSaveable { mutableStateOf(true) }
    var mode by rememberSaveable { mutableStateOf(CoolLedX.Mode.LEFT) }
    var speed by rememberSaveable { mutableFloatStateOf(180f) }
    val sending by vm.ble.progress.collectAsState()
    val (w, h) = vm.panel()
    val grid = remember(text, color, rainbow, bold, mode, w, h) {
        TextRender.render(text.ifBlank { " " }, h, w, color, bold, rainbow, center = mode == CoolLedX.Mode.STATIC)
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)) {
        LedPreview(listOf(grid), 100, panelW = w, panelH = h, scrollMode = mode)
        OutlinedTextField(text, { text = it.take(255) }, Modifier.fillMaxWidth(), label = { Text("Message") },
            singleLine = true)
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            QUICK.forEach { q -> AssistChip(onClick = { text = q }, label = { Text(q) }) }
        }
        Text("Colour", fontWeight = FontWeight.SemiBold)
        ColorPicker(color, { color = it; rainbow = false }, rainbow = rainbow, onRainbow = { rainbow = true })
        Row(verticalAlignment = Alignment.CenterVertically) {
            Switch(bold, { bold = it }); Spacer(Modifier.width(8.dp)); Text("Bold (easier to read from a distance)")
        }
        Text("Motion", fontWeight = FontWeight.SemiBold)
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            listOf(CoolLedX.Mode.STATIC, CoolLedX.Mode.LEFT, CoolLedX.Mode.RIGHT, CoolLedX.Mode.UP,
                CoolLedX.Mode.DOWN, CoolLedX.Mode.SNOW, CoolLedX.Mode.LASER).forEach { m ->
                FilterChip(mode == m, { mode = m }, label = { Text(m.label) })
            }
        }
        if (mode != CoolLedX.Mode.STATIC) {
            Text("Scroll speed", fontWeight = FontWeight.SemiBold)
            Slider(speed, { speed = it }, valueRange = 0f..255f)
        }
        Button(onClick = { vm.sendText(text, grid, mode, speed.toInt()) }, enabled = sending == null && text.isNotBlank(),
            modifier = Modifier.fillMaxWidth().height(52.dp)) {
            Icon(Icons.Filled.Send, null); Spacer(Modifier.width(8.dp)); Text("Show on sign")
        }
    }
}

@Composable
fun SignScreen(vm: AppVM) {
    val state by vm.ble.state.collectAsState()
    val found by vm.ble.found.collectAsState()
    val conn by vm.ble.connected.collectAsState()
    var bright by rememberSaveable { mutableFloatStateOf(160f) }
    val scope = rememberCoroutineScope()
    val flip by vm.flip.collectAsState()
    val mirror by vm.mirror.collectAsState()
    val logLines by vm.ble.log.collectAsState()
    var showLog by rememberSaveable { mutableStateOf(false) }
    val clipboard = LocalClipboardManager.current

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)) {
        ElevatedCard(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                if (conn != null) {
                    Text("Connected to ${conn!!.name}", style = MaterialTheme.typography.titleMedium)
                    Text("${conn!!.sizeLabel} panel", style = MaterialTheme.typography.bodySmall)
                    Text("Brightness", fontWeight = FontWeight.SemiBold)
                    Slider(bright, { bright = it }, valueRange = 1f..255f, onValueChangeFinished = { vm.brightness(bright.toInt()) })
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton({ vm.power(true) }) { Icon(Icons.Filled.LightMode, null); Spacer(Modifier.width(4.dp)); Text("Display on") }
                        OutlinedButton({ vm.power(false) }) { Icon(Icons.Filled.DarkMode, null); Spacer(Modifier.width(4.dp)); Text("Display off") }
                    }
                    Button({ vm.sendTestPattern() }) { Icon(Icons.Filled.GridView, null); Spacer(Modifier.width(6.dp)); Text("Send test pattern") }
                    Text("Shows red/blue halves swapping, with a white corner mark at the top-left.",
                        style = MaterialTheme.typography.bodySmall)
                    TextButton({ vm.ble.disconnect() }) { Text("Disconnect") }
                } else {
                    Text("No sign connected", style = MaterialTheme.typography.titleMedium)
                    Text("Turn the sign on, close the stock CoolLED app (only one phone can connect at a time), then scan.",
                        style = MaterialTheme.typography.bodySmall)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button({ vm.ble.startScan() }, enabled = state != LinkState.SCANNING && state != LinkState.CONNECTING) {
                            Icon(Icons.Filled.BluetoothSearching, null); Spacer(Modifier.width(6.dp))
                            Text(if (state == LinkState.SCANNING) "Scanning…" else "Scan for signs")
                        }
                        if (vm.ble.hasLast()) OutlinedButton({ scope.launch { vm.ble.reconnectLast() } }) { Text("Reconnect last") }
                    }
                    if (state == LinkState.CONNECTING) LinearProgressIndicator(Modifier.fillMaxWidth())
                }
            }
        }
        found.forEach { s ->
            ListItem(
                headlineContent = { Text(s.name) },
                supportingContent = {
                    Text("${s.sizeLabel} · signal ${s.rssi} dBm" +
                        if (!s.supported) " · CoolLED${s.family} family (protocol not supported yet)" else "")
                },
                leadingContent = { Icon(Icons.Filled.Bluetooth, null) },
                trailingContent = {
                    Button({ scope.launch { vm.ble.connect(s) } }, enabled = state != LinkState.CONNECTING) { Text("Connect") }
                },
                modifier = Modifier.clip(MaterialTheme.shapes.medium)
            )
        }
        HorizontalDivider()
        Text("Orientation", fontWeight = FontWeight.SemiBold)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Switch(flip, { vm.setFlip(it) }); Spacer(Modifier.width(10.dp))
            Column { Text("Upside-down (rotate 180°)"); Text("For a sign mounted inverted", style = MaterialTheme.typography.bodySmall) }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Switch(mirror, { vm.setMirror(it) }); Spacer(Modifier.width(10.dp))
            Column { Text("Mirror (reverse left-right)"); Text("For reading through a window from behind", style = MaterialTheme.typography.bodySmall) }
        }
        Text("Applies to everything you send from now on; scroll directions are adjusted to match.",
            style = MaterialTheme.typography.bodySmall)
        HorizontalDivider()
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Diagnostics log (${logLines.size})", fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f))
            TextButton({ showLog = !showLog }) { Text(if (showLog) "Hide" else "Show") }
            TextButton({ clipboard.setText(AnnotatedString(logLines.joinToString("\n"))) }) { Text("Copy") }
        }
        if (showLog) {
            Surface(color = Color(0xFF0B0B0F), shape = MaterialTheme.shapes.small) {
                Text(logLines.takeLast(80).joinToString("\n").ifEmpty { "Nothing logged yet." },
                    fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.labelSmall,
                    modifier = Modifier.fillMaxWidth().padding(8.dp))
            }
            TextButton({ vm.ble.clearLog() }) { Text("Clear log") }
        }
        HorizontalDivider()
        Text("Privacy", fontWeight = FontWeight.SemiBold)
        Text("This app has no internet permission, no ads, no analytics and no accounts. It only talks to your sign over " +
            "Bluetooth. Your creations stay on this phone.", style = MaterialTheme.typography.bodySmall)
    }
}
