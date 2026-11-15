package com.netadmindave.ledsign

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import com.netadmindave.ledsign.ble.LinkState
import com.netadmindave.ledsign.ui.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent { LedTheme { App() } }
    }
}

private fun blePermissions(): Array<String> =
    if (Build.VERSION.SDK_INT >= 31) arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT)
    else arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun App(vm: AppVM = viewModel()) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    var granted by remember {
        mutableStateOf(blePermissions().all { ContextCompat.checkSelfPermission(ctx, it) == PackageManager.PERMISSION_GRANTED })
    }
    val askPerms = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { r ->
        granted = r.values.all { it }
        if (granted) vm.ble.startScan()
    }
    var tab by rememberSaveable { mutableIntStateOf(0) }
    val state by vm.ble.state.collectAsState()
    val conn by vm.ble.connected.collectAsState()
    val progress by vm.ble.progress.collectAsState()
    val msg by vm.ble.message.collectAsState()
    val snack = remember { SnackbarHostState() }

    LaunchedEffect(granted) {
        if (granted && vm.ble.bluetoothOn && vm.ble.hasLast() && conn == null) vm.ble.reconnectLast()
    }
    LaunchedEffect(msg) { msg?.let { snack.showSnackbar(it); vm.ble.clearMessage() } }

    Scaffold(
        snackbarHost = { SnackbarHost(snack) },
        topBar = {
            TopAppBar(
                title = { Text("LED Sign Studio") },
                actions = {
                    val (label, col) = when {
                        state == LinkState.SENDING -> "Sending…" to Color(0xFFFFB347)
                        conn != null -> conn!!.name to Color(0xFF4CD964)
                        state == LinkState.CONNECTING -> "Connecting…" to Color(0xFFFFB347)
                        state == LinkState.SCANNING -> "Scanning…" to Color(0xFF6EC6FF)
                        else -> "Not connected" to Color(0xFFFF6B6B)
                    }
                    AssistChip(
                        onClick = { tab = 3 },
                        label = { Text(label) },
                        leadingIcon = { Icon(Icons.Filled.Circle, null, tint = col, modifier = Modifier.size(10.dp)) },
                        modifier = Modifier.padding(end = 8.dp)
                    )
                }
            )
        },
        bottomBar = {
            NavigationBar {
                listOf(
                    Triple("Library", Icons.Filled.Collections, 0),
                    Triple("Text", Icons.Filled.TextFields, 1),
                    Triple("Draw", Icons.Filled.Brush, 2),
                    Triple("Sign", Icons.Filled.Settings, 3),
                ).forEach { (l, ic, i) ->
                    NavigationBarItem(selected = tab == i, onClick = { tab = i }, icon = { Icon(ic, l) }, label = { Text(l) })
                }
            }
        }
    ) { pad ->
        Column(Modifier.padding(pad).fillMaxSize()) {
            progress?.let { p ->
                LinearProgressIndicator(progress = { p.done.toFloat() / p.total.coerceAtLeast(1) }, modifier = Modifier.fillMaxWidth())
            }
            if (!granted) {
                Card(Modifier.fillMaxWidth().padding(12.dp)) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text("Allow Bluetooth access so the app can find your sign.", Modifier.weight(1f))
                        Button({ askPerms.launch(blePermissions()) }) { Text("Allow") }
                    }
                }
            } else if (!vm.ble.bluetoothOn) {
                Card(Modifier.fillMaxWidth().padding(12.dp)) {
                    Text("Bluetooth is off. Turn it on in quick settings, then open the Sign tab.", Modifier.padding(12.dp))
                }
            }
            Box(Modifier.weight(1f)) {
                when (tab) {
                    0 -> LibraryScreen(vm, onEdit = { vm.editRequest.value = it; tab = 2 })
                    1 -> TextScreen(vm)
                    2 -> DrawScreen(vm)
                    else -> SignScreen(vm)
                }
            }
        }
    }
}
