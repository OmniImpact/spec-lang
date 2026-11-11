// =============================================================================
// Monte Carlo pi benchmark — Kotlin (JVM), same algorithm as mc_pi.c
// (xorshift64, identical constants, identical per-point work). Plain threads +
// join; the JIT is warmed with three throwaway rounds before the measured
// round. Written against the Kotlin 1.3 language level so it compiles on old
// and new compilers alike.
//
// Build: kotlinc mc_pi.kt -include-runtime -d mc_pi_kt.jar
// Run:   java -jar mc_pi_kt.jar <threads> <points>
// =============================================================================
import java.lang.Thread
import kotlin.system.measureTimeMillis

private fun nx(s: Long): Long {
    var v = s
    v = v xor (v shl 13)
    v = v xor (v ushr 7)
    v = v xor (v shl 17)
    return v
}

private fun slice(idx: Int, n: Long, t: Int): Long {
    // The seed constants exceed Long.MAX_VALUE, and Kotlin (2.x) promotes
    // such hex literals to BigInteger — build them from 32-bit halves so the
    // bit pattern is exactly the C anchor's while staying a plain Long.
    val seed = (0x9E3779B9L shl 32) or 0x7F4A7C15L
    val mul = (0xBF58476DL shl 32) or 0x1CE4E5B9L
    val add = (0x94D049BBL shl 32) or 0x133111EBL
    var st = seed xor (idx.toLong() * mul + add) // Long overflow wraps, as in C
    if (st == 0L) st = 1L
    st = nx(st); st = nx(st); st = nx(st)
    var h = 0L
    val per = n / t + (if (idx < n % t) 1L else 0L)
    val scale = 1.0 / 9007199254740992.0
    for (k in 0 until per) {
        st = nx(st)
        val x = (st ushr 11).toDouble() * scale
        st = nx(st)
        val y = (st ushr 11).toDouble() * scale
        if (x * x + y * y <= 1.0) h++
    }
    return h
}

private fun runOnce(t: Int, n: Long, report: Boolean): Long {
    val hits = LongArray(t)
    val th = arrayOfNulls<Thread>(t)
    val ms = measureTimeMillis {
        for (i in 0 until t) {
            th[i] = Thread { hits[i] = slice(i, n, t) }
            th[i]!!.start()
        }
        for (i in 0 until t) th[i]!!.join()
    }
    if (report) {
        var h = 0L
        for (v in hits) h += v
        println("pi=%.5f threads=%d points=%d ms=%d rate=%.4e".format(
            4.0 * h / n.toDouble(), t, n, ms, n.toDouble() / (ms / 1000.0)))
    }
    return ms
}

fun main(args: Array<String>) {
    var t = if (args.isNotEmpty()) args[0].toInt() else 8
    val n = if (args.size > 1) args[1].toLong() else 200_000_000L
    if (t < 1) t = 1
    for (w in 0 until 3) runOnce(t, n / 4, false) // JIT warm-up
    runOnce(t, n, true)
}
