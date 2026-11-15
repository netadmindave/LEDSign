package com.netadmindave.ledsign.ble

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.Build
import android.util.Log
import com.netadmindave.ledsign.protocol.CoolLedX
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
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
 * BLE client for CoolLEDX signs (service FFF0, characteristic FFF1: write-without-response + notify).
 *
 * Upload rules (match the hardware-tested RavestickBoard firmware for the 16x64 7-colour panel):
 *  - every framed packet must go out as ONE write, so the ATT MTU must be large enough;
 *  - after each data packet the sign notifies `01 | 00 05 | cmd 00 idx(2) status | 03`;
 *    status 0 = OK, 6 = checksum error (resend), anything else = rejected;
 *  - short control commands (brightness, mode, speed, power) are not acknowledged.
 */
@SuppressLint("MissingPermission") // permissions are requested by MainActivity before any call
class SignBle(private val ctx: Context) {
    companion object {
        private const val TAG = "SignBle"
        val SERVICE: UUID = UUID.fromString("0000fff0-0000-1000-8000-00805f9b34fb")
        val CHAR: UUID = UUID.fromString("0000fff1-0000-1000-8000-00805f9b34fb")
        val CCCD: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
        private val NAME_PREFIXES = listOf("CoolLED", "iLed", "iDevilEyes")
        private val PASSWORD_PREFIXES = listOf("CoolLEDS", "CoolLEDX", "CoolLEDM")
        private const val NEEDED_PAYLOAD = 180   // largest framed 128-byte chunk is ~150 bytes, escapes included

        fun ackStatusText(s: Int) = when (s) {
            0 -> "OK"; 1 -> "transmission failed"; 2 -> "device abnormality"; 3 -> "data error"
            4 -> "data too long"; 5 -> "data ID error"; 6 -> "checksum error"; else -> "code $s"
        }
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
    private val _log = MutableStateFlow<List<String>>(emptyList())
    val log: StateFlow<List<String>> = _log.asStateFlow()

    private var gatt: BluetoothGatt? = null
    /** CoolLEDX (1248 family) keeps the default MTU and takes 20-byte writes, 15 ms apart — exactly like the stock app. */
    @Volatile private var smallWrites = true
    private val writeSize: Int get() = if (smallWrites) 20 else mtuPayload
    private var ch: BluetoothGattCharacteristic? = null
    @Volatile private var mtuPayload = 20
    private val writeMutex = Mutex()
    private var writeAck: CompletableDeferred<Boolean>? = null
    private var readyAck: CompletableDeferred<Boolean>? = null
    private var mtuAck: CompletableDeferred<Int>? = null
    private val notifications = Channel<ByteArray>(Channel.UNLIMITED)
    private val timeFmt = SimpleDateFormat("HH:mm:ss.SSS", Locale.US)

    val bluetoothOn: Boolean get() = adapter?.isEnabled == true
    fun clearMessage() { _message.value = null }
    fun clearLog() { _log.value = emptyList() }

    private fun log(s: String) {
        Log.i(TAG, s)
        val line = "${timeFmt.format(Date())}  $s"
        scope.launch { _log.value = (_log.value + line).takeLast(400) }
    }

    private fun hex(b: ByteArray, max: Int = 24): String {
        val s = b.take(max).joinToString(" ") { "%02x".format(it) }
        return if (b.size > max) "$s … (${b.size} B)" else s
    }

    // ------------------------------------------------------------------ scanning
    private val scanCb = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val name = result.scanRecord?.deviceName ?: result.device.name ?: return
            if (NAME_PREFIXES.none { name.startsWith(it) }) return
            var rows: Int? = null; var cols: Int? = null; var color: Int? = null
            // Manufacturer data (company ID stripped): MAC(6) | rows | cols(2, BE) | colour type | fw
            val mfg = result.scanRecord?.manufacturerSpecificData
            if (mfg != null && mfg.size() > 0) {
                val d = mfg.valueAt(0)
                if (d != null && d.size >= 10) {
                    val r = d[6].toInt() and 0xFF
                    val c = ((d[7].toInt() and 0xFF) shl 8) or (d[8].toInt() and 0xFF)
                    if (r in 8..64 && r % 8 == 0 && c in 16..512) {
                        rows = r; cols = c; color = d[9].toInt() and 0xFF
                    }
                }
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
        scope.launch { delay(seconds * 1000); stopScan() }
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
                if (smallWrites) {
                    log("connected (status $status); CoolLEDX: default MTU, 20-byte writes")
                    g.discoverServices()
                } else {
                    log("connected (status $status), requesting MTU 247")
                    if (!g.requestMtu(247)) { log("requestMtu refused"); g.discoverServices() }
                }
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                log("disconnected (status $status)")
                g.close()
                if (gatt == g) gatt = null
                ch = null
                readyAck?.complete(false)
                writeAck?.complete(false)
                mtuAck?.complete(0)
                scope.launch {
                    if (_connected.value != null) _message.value = "Sign disconnected"
                    _connected.value = null
                    _state.value = LinkState.IDLE
                }
            }
        }

        override fun onMtuChanged(g: BluetoothGatt, mtu: Int, status: Int) {
            log("MTU $mtu (status $status)")
            if (status == BluetoothGatt.GATT_SUCCESS) mtuPayload = (mtu - 3).coerceIn(20, 512)
            mtuAck?.complete(mtu)
            if (ch == null) g.discoverServices()
        }

        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            val c = g.getService(SERVICE)?.getCharacteristic(CHAR)
            if (c == null) { log("FFF0/FFF1 not found"); readyAck?.complete(false); return }
            ch = c
            log("FFF1 properties 0x%02x".format(c.properties))
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
            log("notifications enabled (status $status)")
            readyAck?.complete(true)
        }

        override fun onCharacteristicWrite(g: BluetoothGatt, c: BluetoothGattCharacteristic, status: Int) {
            writeAck?.complete(status == BluetoothGatt.GATT_SUCCESS)
        }

        @Deprecated("pre-33 path")
        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic) {
            @Suppress("DEPRECATION")
            val v = c.value ?: return
            if (Build.VERSION.SDK_INT < 33) onNotify(v)
        }

        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic, value: ByteArray) {
            onNotify(value)
        }
    }

    private fun onNotify(v: ByteArray) {
        log("RX ${hex(v)}")
        notifications.trySend(v.copyOf())
    }

    suspend fun connect(sign: FoundSign): Boolean {
        stopScan()
        disconnect()
        val dev = adapter?.getRemoteDevice(sign.address) ?: return false
        _state.value = LinkState.CONNECTING
        log("connecting to ${sign.name} ${sign.address} (${sign.sizeLabel})")
        readyAck = CompletableDeferred()
        mtuPayload = 20
        smallWrites = sign.family == "X"
        gatt = dev.connectGatt(ctx, false, gattCb, BluetoothDevice.TRANSPORT_LE)
        val ok = withTimeoutOrNull(12_000) { readyAck!!.await() } ?: false
        if (ok) {
            delay(650)   // the sign needs a moment after connecting before it accepts data
            if (PASSWORD_PREFIXES.any { sign.name.startsWith(it) } && !checkPassword()) {
                disconnect(); _state.value = LinkState.ERROR
                return false
            }
        }
        return if (ok && gatt != null) {
            _connected.value = sign
            _state.value = LinkState.READY
            ctx.getSharedPreferences("sign", Context.MODE_PRIVATE).edit()
                .putString("last_addr", sign.address).putString("last_name", sign.name)
                .putInt("rows", sign.rows ?: 16).putInt("cols", sign.cols ?: 64).apply()
            log("ready, write size $writeSize bytes")
            true
        } else {
            _message.value = "Couldn't connect to ${sign.name}. Close the CoolLED app (only one phone can connect at a time)."
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

    // ------------------------------------------------------------------ password
    private val prefs = ctx.getSharedPreferences("sign", Context.MODE_PRIVATE)
    var password: String
        get() = prefs.getString("password", "000000")!!
        set(v) { prefs.edit().putString("password", v.filter { it.isDigit() }.take(6).padEnd(6, '0')).apply() }

    /**
     * CoolLEDS/X/M signs ignore uploads until the 6-digit password is verified (default 000000):
     * send 0x0D + ASCII digits, the reply's last byte is 0 when accepted.
     */
    private suspend fun checkPassword(): Boolean {
        while (notifications.tryReceive().isSuccess) { }
        val pwd = password
        val frame = CoolLedX.frame(byteArrayOf(0x0D) + pwd.toByteArray(Charsets.US_ASCII))
        log("password check (${"*".repeat(pwd.length)}) TX ${hex(frame)}")
        if (!writeOnce(frame)) { log("password write failed"); return true }
        val reply = withTimeoutOrNull(5_000) { notifications.receive() }
        if (reply == null) { log("no reply to password check — continuing"); return true }
        val p = CoolLedX.unframe(reply)
        val status = p?.lastOrNull()?.toInt()?.and(0xFF)
        return if (status == 0) { log("password accepted"); true } else {
            log("password REJECTED (status $status)")
            _message.value = "The sign rejected the password. Enter the sign's password on the Sign tab (default 000000)."
            false
        }
    }

    // ------------------------------------------------------------------ writing
    /** Make sure one framed packet fits in a single write; re-negotiate the MTU if needed. */
    private suspend fun ensureMtu(): Boolean {
        if (mtuPayload >= NEEDED_PAYLOAD) return true
        val g = gatt ?: return false
        log("write limit $mtuPayload B is too small, asking for MTU 247 again")
        mtuAck = CompletableDeferred()
        if (g.requestMtu(247)) withTimeoutOrNull(3_000) { mtuAck!!.await() }
        return mtuPayload >= NEEDED_PAYLOAD
    }

    private suspend fun writeOnce(bytes: ByteArray): Boolean {
        val g = gatt ?: return false
        val c = ch ?: return false
        val type = if ((c.properties and BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE) != 0)
            BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE else BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
        var off = 0
        var busyRetries = 0
        while (off < bytes.size) {
            val piece = bytes.copyOfRange(off, minOf(bytes.size, off + writeSize))
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
            if (!started) {
                if (++busyRetries > 60) { log("write refused by Android BLE stack"); return false }
                delay(30); continue
            }
            busyRetries = 0
            withTimeoutOrNull(2_000) { writeAck!!.await() } ?: return false
            off += piece.size
            if (off < bytes.size) delay(15)
        }
        return true
    }

    /** Parse `01 | 00 05 | cmd 00 idx(2) status | 03` → (cmd, idx, status). */
    private fun parseAck(v: ByteArray): Triple<Int, Int, Int>? {
        val p = CoolLedX.unframe(v) ?: return null
        if (p.size < 5) return null
        val cmd = p[0].toInt() and 0xFF
        val idx = ((p[2].toInt() and 0xFF) shl 8) or (p[3].toInt() and 0xFF)
        val status = p[p.size - 1].toInt() and 0xFF
        return Triple(cmd, idx, status)
    }

    private suspend fun awaitAck(cmd: Int, idx: Int): Int? = withTimeoutOrNull(5_000) {
        var result: Int? = null
        while (result == null) {
            val a = parseAck(notifications.receive())
            if (a != null && a.first == cmd && a.second == idx) result = a.third
        }
        result
    }

    private suspend fun ensureLink(): Boolean {
        if (gatt != null && ch != null) return true
        return reconnectLast()
    }

    /** Short control command (brightness, mode, speed, power...). Not acknowledged by the sign. */
    suspend fun sendCommands(packets: List<ByteArray>): Boolean = writeMutex.withLock {
        if (!ensureLink()) { _message.value = "Not connected to a sign"; return@withLock false }
        for (p in packets) {
            log("TX ${hex(p)}")
            if (!writeOnce(p)) { _message.value = "Command failed"; return@withLock false }
            delay(90)
        }
        true
    }

    /**
     * Upload a chunked payload (text 0x02 / image / animation 0x04).
     * [before] and [after] are short commands sent around the upload (e.g. mode).
     */
    suspend fun upload(cmd: Int, packets: List<ByteArray>, label: String,
                       before: List<ByteArray> = emptyList(), after: List<ByteArray> = emptyList()): Boolean =
        writeMutex.withLock {
            if (!ensureLink()) { _message.value = "Not connected to a sign"; return@withLock false }
            if (!smallWrites && !ensureMtu()) {
                _message.value = "Bluetooth packet size too small ($mtuPayload B). Disconnect and reconnect, then try again."
                return@withLock false
            }
            _state.value = LinkState.SENDING
            _progress.value = SendProgress(0, packets.size)
            log("upload \"$label\": cmd 0x%02x, ${packets.size} packets".format(cmd))
            var error: String? = null
            try {
                for (p in before) { log("TX ${hex(p)}"); writeOnce(p); delay(90) }
                while (notifications.tryReceive().isSuccess) { /* drop stale notifications */ }
                for ((i, p) in packets.withIndex()) {
                    var status: Int? = null
                    for (attempt in 0 until 3) {
                        if (i < 3 || attempt > 0) log("TX #$i ${hex(p)}")
                        if (!writeOnce(p)) { error = "Write failed at packet ${i + 1}"; break }
                        status = awaitAck(cmd, i)
                        if (status != 6) break
                        log("packet $i checksum error, resending")
                    }
                    if (error != null) break
                    if (status == null) { error = "The sign didn't answer packet ${i + 1} of ${packets.size}"; break }
                    if (status != 0) {
                        error = "The sign rejected packet ${i + 1}: ${ackStatusText(status)}"; break
                    }
                    _progress.value = SendProgress(i + 1, packets.size)
                    delay(20)
                }
                if (error == null) for (p in after) { delay(60); log("TX ${hex(p)}"); writeOnce(p); delay(90) }
            } catch (e: Exception) {
                error = "Send error: ${e.message}"
            }
            _progress.value = null
            _state.value = if (gatt != null) LinkState.READY else LinkState.IDLE
            if (error != null) { log("FAILED: $error"); _message.value = error }
            else { log("upload OK"); _message.value = "Sent: $label" }
            error == null
        }
}
