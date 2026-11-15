package com.netadmindave.ledsign.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.StarBorder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.netadmindave.ledsign.data.ImageImport
import com.netadmindave.ledsign.data.LedAnimation
import com.netadmindave.ledsign.protocol.PixelGrid
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

private val CATEGORIES = listOf("All", "★ Favorites", "Halloween", "Holidays", "Reading", "Optics", "My Creations")

@Composable
fun LibraryScreen(vm: AppVM, onEdit: (LedAnimation) -> Unit) {
    val ctx = LocalContext.current
    val favs by vm.favs.collectAsState()
    val mine by vm.creations.collectAsState()
    val sending by vm.ble.progress.collectAsState()
    var cat by rememberSaveable { mutableStateOf("All") }
    var open by remember { mutableStateOf<LedAnimation?>(null) }
    var imported by remember { mutableStateOf<Pair<List<PixelGrid>, Int>?>(null) }
    val scope = rememberCoroutineScope()

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null) scope.launch {
            val (w, h) = vm.panel()
            imported = try {
                withContext(Dispatchers.Default) { ImageImport.load(ctx, uri, w, h, fill = false) }
            } catch (e: Exception) { null }
        }
    }

    val all = vm.builtIn + mine
    val shown = when (cat) {
        "All" -> all
        "★ Favorites" -> all.filter { it.id in favs }
        else -> all.filter { it.category == cat }
    }

    Column(Modifier.fillMaxSize()) {
        Row(
            Modifier.horizontalScroll(rememberScrollState()).padding(horizontal = 12.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            CATEGORIES.forEach { c ->
                FilterChip(selected = cat == c, onClick = { cat = c }, label = { Text(c) })
            }
        }
        if (shown.isEmpty()) {
            Box(Modifier.fillMaxSize().padding(32.dp), contentAlignment = Alignment.Center) {
                Text(
                    if (cat == "★ Favorites") "Tap the ☆ on any animation to add it here."
                    else "Nothing here yet — make something in the Draw tab or import a GIF.",
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        }
        Box(Modifier.weight(1f)) {
            LazyVerticalGrid(
                columns = GridCells.Adaptive(300.dp),
                contentPadding = PaddingValues(12.dp, 4.dp, 12.dp, 96.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                items(shown, key = { it.id }) { a ->
                    ElevatedCard(Modifier.fillMaxWidth().clickable { open = a }) {
                        Column(Modifier.padding(10.dp)) {
                            LedPreview(a.frames, a.speedMs)
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f).padding(top = 6.dp)) {
                                    Text(a.name, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                    Text("${a.category} · ${a.frames.size} frames", style = MaterialTheme.typography.labelSmall)
                                }
                                IconButton(onClick = { vm.toggleFav(a.id) }) {
                                    if (a.id in favs) Icon(Icons.Filled.Star, "Unfavorite", tint = MaterialTheme.colorScheme.primary)
                                    else Icon(Icons.Outlined.StarBorder, "Favorite")
                                }
                                FilledTonalButton(
                                    onClick = { vm.sendAnimation(a.frames, a.speedMs, a.name) },
                                    enabled = sending == null
                                ) { Icon(Icons.Filled.Send, null); Spacer(Modifier.width(6.dp)); Text("Show") }
                            }
                        }
                    }
                }
            }
            ExtendedFloatingActionButton(
                onClick = { picker.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) },
                icon = { Icon(Icons.Filled.AddPhotoAlternate, null) },
                text = { Text("Import image / GIF") },
                modifier = Modifier.align(Alignment.BottomEnd).padding(16.dp)
            )
        }
    }

    open?.let { a ->
        AnimationDialog(a, vm, onDismiss = { open = null }, onEdit = { open = null; onEdit(a) },
            onDelete = if (!a.builtIn) ({ vm.delete(a.id); open = null }) else null)
    }

    imported?.let { (frames, speed) ->
        var name by remember { mutableStateOf("Imported ${System.currentTimeMillis() % 10000}") }
        AlertDialog(
            onDismissRequest = { imported = null },
            title = { Text("Imported ${if (frames.size > 1) "animation (${frames.size} frames)" else "image"}") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    LedPreview(frames, speed)
                    Text("Colours are reduced to the sign's 7 colours. High-contrast art works best.",
                        style = MaterialTheme.typography.bodySmall)
                    OutlinedTextField(name, { name = it }, label = { Text("Name") }, singleLine = true)
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    vm.save(LedAnimation("u" + System.currentTimeMillis(), name, "My Creations", speed, frames, false))
                    vm.sendAnimation(frames, speed, name); imported = null
                }) { Text("Save & show") }
            },
            dismissButton = { TextButton(onClick = { imported = null }) { Text("Cancel") } }
        )
    }
}

@Composable
private fun AnimationDialog(
    a: LedAnimation, vm: AppVM, onDismiss: () -> Unit, onEdit: () -> Unit, onDelete: (() -> Unit)?,
) {
    var speed by remember(a) { mutableFloatStateOf(a.speedMs.toFloat()) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(a.name) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                LedPreview(a.frames, speed.toInt())
                if (a.frames.size > 1) {
                    Text("Frame time: ${speed.toInt()} ms", style = MaterialTheme.typography.labelLarge)
                    Slider(speed, { speed = it }, valueRange = 40f..600f)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = onEdit) { Icon(Icons.Filled.Edit, null); Spacer(Modifier.width(4.dp)); Text("Edit a copy") }
                    if (onDelete != null) OutlinedButton(onClick = onDelete) { Icon(Icons.Filled.Delete, null) }
                }
            }
        },
        confirmButton = {
            Button(onClick = { vm.sendAnimation(a.frames, speed.toInt(), a.name); onDismiss() }) { Text("Show on sign") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Close") } }
    )
}
