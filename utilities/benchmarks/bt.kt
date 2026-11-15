// =============================================================================
// Binary-trees benchmark — Kotlin (JVM), warmed with two depth-12 rounds.
// Build: kotlinc bt.kt -include-runtime -d bt_kt.jar
// Run:   java -jar bt_kt.jar <threads> <max_depth>
// =============================================================================
import java.lang.Thread
import kotlin.system.measureTimeMillis

private class BtNode(val left: BtNode?, val right: BtNode?)

private fun makeTree(depth: Int): BtNode {
    if (depth <= 0) return BtNode(null, null)
    return BtNode(makeTree(depth - 1), makeTree(depth - 1))
}

private fun checkTree(n: BtNode): Long {
    if (n.left == null) return 1L
    return 1L + checkTree(n.left) + checkTree(n.right!!)
}

private fun runOnce(t: Int, maxDepthIn: Int, report: Boolean) {
    val minDepth = 4
    val maxDepth = if (maxDepthIn < minDepth + 2) minDepth + 2 else maxDepthIn
    var totalChecks = 0L

    val elapsed = measureTimeMillis {
        totalChecks += checkTree(makeTree(maxDepth + 1))

        val longLived = makeTree(maxDepth)

        var d = minDepth
        while (d <= maxDepth) {
            val depth = d
            val iterations = 1L shl (maxDepth - d + minDepth)
            if (t <= 1) {
                for (i in 0 until iterations) {
                    totalChecks += checkTree(makeTree(depth))
                }
            } else {
                val sums = LongArray(t)
                val th = arrayOfNulls<Thread>(t)
                val base = iterations / t
                val rem = iterations % t
                for (i in 0 until t) {
                    val cnt = base + (if (i < rem) 1L else 0L)
                    th[i] = Thread {
                        var s = 0L
                        for (k in 0 until cnt) {
                            s += checkTree(makeTree(depth))
                        }
                        sums[i] = s
                    }
                    th[i]!!.start()
                }
                for (i in 0 until t) {
                    th[i]!!.join()
                    totalChecks += sums[i]
                }
            }
            d += 2
        }

        totalChecks += checkTree(longLived)
    }

    val ms = if (elapsed < 1L) 1L else elapsed
    if (report) {
        println("checksum=%d threads=%d depth=%d ms=%d rate=%.4e".format(
            totalChecks, t, maxDepth, ms, totalChecks.toDouble() / (ms / 1000.0)))
    }
}

fun main(args: Array<String>) {
    var t = if (args.isNotEmpty()) args[0].toInt() else 1
    val maxDepth = if (args.size > 1) args[1].toInt() else 18
    if (t < 1) t = 1
    for (w in 0 until 2) runOnce(t, 12, false)
    runOnce(t, maxDepth, true)
}
