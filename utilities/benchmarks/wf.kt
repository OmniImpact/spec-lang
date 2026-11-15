// =============================================================================
// Word/log-line frequency benchmark — Kotlin (JVM), warmed with 50k lines.
// Build: kotlinc wf.kt -include-runtime -d wf_kt.jar
// Run:   java -jar wf_kt.jar [count]
// =============================================================================
import kotlin.system.measureTimeMillis

private fun nx(s: Long): Long {
    var v = s
    v = v xor (v shl 13)
    v = v xor (v ushr 7)
    v = v xor (v shl 17)
    return v
}

private fun runOnce(count: Long, report: Boolean) {
    val services = arrayOf(
        "auth", "api", "billing", "cache",
        "db", "edge", "feed", "gateway",
        "ingest", "jobs", "kv", "logs",
        "metrics", "notify", "proxy", "search"
    )
    val levels = arrayOf("INFO", "WARN", "ERR")

    var st = (0x9E3779B9L shl 32) or 0x7F4A7C15L
    st = nx(st); st = nx(st); st = nx(st)

    val counts = HashMap<String, Long>()
    var total = 0L
    var maxCount = 0L

    val elapsed = measureTimeMillis {
        for (i in 0 until count) {
            st = nx(st)
            val r1 = (st and 15L).toInt()
            st = nx(st)
            val r2 = ((st and 0x7FFFFFFFL) % 3L).toInt()
            st = nx(st)
            val r3 = (st and 0x7FFFFFFFL) % 500L

            val line = services[r1] + ":" + levels[r2] + ":" + r3
            val parts = line.split(":")
            val code = parts[2].toLong()
            val bucket = code and 63L
            val key = parts[0] + ":" + parts[1] + ":" + bucket
            counts[key] = (counts[key] ?: 0L) + 1L
        }
        for (v in counts.values) {
            total += v
            if (v > maxCount) maxCount = v
        }
    }

    val ms = if (elapsed < 1L) 1L else elapsed
    if (report) {
        println("unique=%d total=%d max=%d count=%d ms=%d rate=%.4e".format(
            counts.size, total, maxCount, count, ms, count.toDouble() / (ms / 1000.0)))
    }
}

fun main(args: Array<String>) {
    var count = if (args.isNotEmpty()) args[0].toLong() else 1_000_000L
    if (count < 1L) count = 1L
    runOnce(50_000L, false)
    runOnce(count, true)
}
