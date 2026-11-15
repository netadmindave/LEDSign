package com.netadmindave.ledsign.ble

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.Build
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.util.UUID

data class FoundSign(
    val address: String,
    val name: String,
    val rssi: Int,
    val rows: Int?,
    val cols: Int?,
    val colorType: Int?,
) {
    val sizeLabel: String get() = if (rows != null && cols != null) "${rows}×${cols}" else "size unknown"
    val family: String
        get() = when {
            name.startsWith("CoolLEDUX") || name.startsWith("iLed") || name.startsWith("iDevil") -> "UX"
            name.startsWith("CoolLEDU") -> "U"
            name.startsWith("CoolLEDM") -> "M"
            else -> "X"
        }
    /** This app speaks the CoolLEDX / CoolLED1248 protocol. */
    val supported: Boolean get() = family == "X"
}

enum class LinkState { IDLE, SCANNING, CONNECTING, READY, SENDING, ERROR }

data class SendProgress(val done: Int, val total: Int)

/**
 * Minimal, privacy-respecting BLE client for CoolLED signs.
 * Service 0xFFF0, characteristic 0xFFF1 (write + notify).
 */
@SuppressLint("MissingPermission") // permissions are requested by MainActivity before any call
class SignBle(private val ctx: Context) {
    companion object {
        private const val TAG = "SignBle"
        val SERVICE: UUID = UUID.fromString("0000fff0-0000-1000-8000-00805f9b34fb")
        val CHAR: UUID = UUID.fromString("0000fff1-0000-1000-8000-00805f9b34fb")
        val CCCD: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
        private val NAME_PREFIXES = listOf("CoolLED", "iLed", "iDevilEyes")
    }

    private val adapter: BluetoothAdapter? =
        (ctx.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager).adapter
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    private val _state = MutableStateFlow(LinkState.IDLE)
    val state: StateFlow<LinkState> = _state.asStateFlow()
    private val _found = MutableStateFlow<List<FoundSign>>(emptyList())
    val found: StateFlow<List<FoundSign>> = _found.asStateFlow()
    private val _connected = MutableStateFlow<FoundSign?>(null)
    val connected: StateFlow<FoundSign?> = _connected.asStateFlow()
    private val _progress = MutableStateFlow<SendProgress?>(null)
    val progress: StateFlow<SendProgress?> = _progress.asStateFlow()
    private val _message = MutableStateFlow<String?>(null)
    val message: StateFlow<String?> = _message.asStateFlow()

    private var gatt: BluetoothGatt? = null
    private var ch: BluetoothGattCharacteristic? = null
    private var mtuPayload = 20
    private val writeMutex = Mutex()
    private var writeAck: CompletableDeferred<Boolean>? = null
    private var notifyAck: CompletableDeferred<ByteArray>? = null
    private var readyAck: CompletableDeferred<Boolean>? = null

    val bluetoothOn: Boolean get() = adapter?.isEnabled == true
    fun clearMessage() { _message.value = null }

    // ------------------------------------------------------------------ scanning
    private val scanCb = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val name = result.scanRecord?.deviceName ?: result.device.name ?: return
            if (NAME_PREFIXES.none { name.startsWith(it) }) return
            val raw = result.scanRecord?.bytes
            var rows: Int? = null; var cols: Int? = null; var color: Int? = null
            if (raw != null && raw.size >= 22) {
                val r = raw[17].toInt() and 0xFF
                val c = ((raw[18].toInt() and 0xFF) shl 8) or (raw[19].toInt() and 0xFF)
                if (r in 8..64 && r % 8 == 0 && c in 16..512) { rows = r; cols = c; color = raw[20].toInt() and 0xFF }
            }
            val s = FoundSign(result.device.address, name, result.rssi, rows, cols, color)
            _found.value = (_found.value.filter { it.address != s.address } + s).sortedByDescending { it.rssi }
        }

        override fun onScanFailed(errorCode: Int) {
            _message.value = "Scan failed (code $errorCode). Toggle Bluetooth and try again."
            _state.value = LinkState.IDLE
        }
    }

    fun startScan(seconds: Long = 8) {
        val sc = adapter?.bluetoothLeScanner ?: run { _message.value = "Bluetooth is off"; return }
        _found.value = emptyList()
        _state.value = LinkState.SCANNING
        sc.startScan(null, ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build(), scanCb)
        scope.launch {
            delay(seconds * 1000)
            stopScan()
        }
    }

    fun stopScan() {
        try { adapter?.bluetoothLeScanner?.stopScan(scanCb) } catch (_: Exception) {}
        if (_state.value == LinkState.SCANNING) _state.value = LinkState.IDLE
    }

    // ------------------------------------------------------------------ connection
    private val gattCb = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_CONNECTED) {
                g.requestConnectionPriority(BluetoothGatt.CONNECTION_PRIORITY_HIGH)
                if (!g.requestMtu(247)) g.discoverServices()
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                Log.i(TAG, "disconnected status=$status")
                g.close()
                if (gatt == g) gatt = null
                ch = null
                readyAck?.complete(false)
                writeAck?.complete(false)
                scope.launch {
                    if (_connected.value != null) _message.value = "Sign disconnected"
                    _connected.value = null
                    _state.value = LinkState.IDLE
                }
            }
        }

        override fun onMtuChanged(g: BluetoothGatt, mtu: Int, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) mtuPayload = (mtu - 3).coerceIn(20, 244)
            g.discoverServices()
        }

        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            val c = g.getService(SERVICE)?.getCharacteristic(CHAR)
            if (c == null) { readyAck?.complete(false); return }
            ch = c
            g.setCharacteristicNotification(c, true)
            val d = c.getDescriptor(CCCD)
            if (d == null) { readyAck?.complete(true); return }
            if (Build.VERSION.SDK_INT >= 33) {
                g.writeDescriptor(d, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
            } else {
                @Suppress("DEPRECATION")
                d.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                @Suppress("DEPRECATION")
                g.writeDescriptor(d)
            }
        }

        override fun onDescriptorWrite(g: BluetoothGatt, d: BluetoothGattDescriptor, status: Int) {
            readyAck?.complete(true)
        }

        override fun onCharacteristicWrite(g: BluetoothGatt, c: BluetoothGattCharacteristic, status: Int) {
            writeAck?.complete(status == BluetoothGatt.GATT_SUCCESS)
        }

        @Deprecated("pre-33 path")
        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic) {
            @Suppress("DEPRECATION")
            notifyAck?.complete(c.value ?: ByteArray(0))
        }

        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic, value: ByteArray) {
            notifyAck?.complete(value)
        }
    }

    suspend fun connect(sign: FoundSign): Boolean {
        stopScan()
        disconnect()
        val dev = adapter?.getRemoteDevice(sign.address) ?: return false
        _state.value = LinkState.CONNECTING
        readyAck = CompletableDeferred()
        gatt = dev.connectGatt(ctx, false, gattCb, BluetoothDevice.TRANSPORT_LE)
        val ok = withTimeoutOrNull(12_000) { readyAck!!.await() } ?: false
        return if (ok) {
            _connected.value = sign
            _state.value = LinkState.READY
            ctx.getSharedPreferences("sign", Context.MODE_PRIVATE).edit()
                .putString("last_addr", sign.address).putString("last_name", sign.name)
                .putInt("rows", sign.rows ?: 16).putInt("cols", sign.cols ?: 64).apply()
            true
        } else {
            _message.value = "Couldn't connect to ${sign.name}. Make sure the stock app isn't connected to it."
            disconnect()
            _state.value = LinkState.ERROR
            false
        }
    }

    /** Reconnect to the last sign used, without scanning. */
    suspend fun reconnectLast(): Boolean {
        val p = ctx.getSharedPreferences("sign", Context.MODE_PRIVATE)
        val addr = p.getString("last_addr", null) ?: return false
        val s = FoundSign(addr, p.getString("last_name", "CoolLED")!!, 0, p.getInt("rows", 16), p.getInt("cols", 64), null)
        return connect(s)
    }

    fun hasLast(): Boolean =
        ctx.getSharedPreferences("sign", Context.MODE_PRIVATE).getString("last_addr", null) != null

    fun disconnect() {
        gatt?.let { try { it.disconnect(); it.close() } catch (_: Exception) {} }
        gatt = null; ch = null
        _connected.value = null
        if (_state.value != LinkState.SCANNING) _state.value = LinkState.IDLE
    }

    // ------------------------------------------------------------------ writing
    private suspend fun writeRaw(bytes: ByteArray): Boolean {
        val g = gatt ?: return false
        val c = ch ?: return false
        val withResp = (c.properties and BluetoothGattCharacteristic.PROPERTY_WRITE) != 0
        val type = if (withResp) BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
        else BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
        var off = 0
        var busyRetries = 0
        while (off < bytes.size) {
            val piece = bytes.copyOfRange(off, minOf(bytes.size, off + mtuPayload))
            writeAck = CompletableDeferred()
            val started = if (Build.VERSION.SDK_INT >= 33) {
                g.writeCharacteristic(c, piece, type) == BluetoothStatusCodes.SUCCESS
            } else {
                @Suppress("DEPRECATION")
                c.writeType = type
                @Suppress("DEPRECATION")
                c.value = piece
                @Suppress("DEPRECATION")
                g.writeCharacteristic(c)
            }
            if (!started) { // stack busy: retry the same piece a few times
                if (++busyRetries > 60) return false
                delay(30); continue
            }
            busyRetries = 0
            val ok = withTimeoutOrNull(2_000) { writeAck!!.await() } ?: false
            if (!ok) return false
            off += piece.size
        }
        return true
    }

    /** Send framed packets; data commands wait for the sign's per-chunk notification. */
    suspend fun send(packets: List<ByteArray>, waitForAck: Boolean = true, label: String? = null): Boolean =
        writeMutex.withLock {
            if (gatt == null && !reconnectLast()) {
                _message.value = "Not connected to a sign"
                return@withLock false
            }
            _state.value = LinkState.SENDING
            _progress.value = SendProgress(0, packets.size)
            var ok = true
            var missedAcks = 0
            for ((i, p) in packets.withIndex()) {
                notifyAck = CompletableDeferred()
                if (!writeRaw(p)) { ok = false; break }
                if (waitForAck) {
                    if (withTimeoutOrNull(1_500) { notifyAck!!.await() } == null) missedAcks++
                } else delay(15)
                _progress.value = SendProgress(i + 1, packets.size)
            }
            _progress.value = null
            _state.value = if (gatt != null) LinkState.READY else LinkState.IDLE
            if (!ok) _message.value = "Send failed — move closer to the sign and try again"
            else if (label != null) _message.value = "Sent: $label"
            if (missedAcks > 0) Log.w(TAG, "$missedAcks chunk(s) were not acknowledged")
            ok
        }
}
