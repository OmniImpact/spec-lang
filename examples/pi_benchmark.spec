#! Package examples
#! Monte Carlo Pi benchmark: parallel point sampling with a live domain
#! visualization, per-thread sample markers, and a running approximation.

## Benchmarks parallel execution by estimating Pi via Monte Carlo sampling.
##
## Uniform random points are generated in the unit square; those inside the
## quarter-illustrated unit circle are counted. With S samples and H inside
## hits, Pi is approximated as 4 * H / S. Workers run on N pthreads, each
## with a lock-free per-thread RNG; the display (rendered on the first
## worker thread) shows every thread's current sample as a colored marker.
Class is PiBenchmark{

	replace Array of String is using: [
		base:struct:*,
		base:iterator:*,
		base:math:*,
		base:io:*,
		base:sys:Process,
		base:sys:Parallel
	];

	## Domain grid dimensions in characters.
	local Int is gridW: 44;
	local Int is gridH: 22;

	## Slot conventions: 0 = samples done, 1 = hits so far, thread i (0-based)
	## publishes its current sample to slots 2i+2 (x) and 2i+3 (y), scaled by 1000.
	local Int is slotSamples: 0;
	local Int is slotHits: 1;

	## Entry point: parses arguments, launches the workers, and prints the
	## final statistics.
	##
	## @param args: CLI map; keys: threads, points, refresh.
	replace Function is init(Map of String to String is args){
		local Int is threads: args:getInt(key: 'threads', default: 4);
		local Int is points: args:getInt(key: 'points', default: 1_000_000_000);
		local Int is refreshMs: args:getInt(key: 'refresh', default: 40);

		if (threads < 1) { threads: 1; }
		if (threads > 16) { threads: 16; }

		output:line(Ansi:clearScreen() . Ansi:moveTo(row: 1, col: 1) . Ansi:hideCursor());
		local String is title: 'Monte Carlo Pi Benchmark';
		output:line(Ansi:bold() . Ansi:color256(code: 51, text: '╔═ ' . title . ' ' . self:bar(width: 76 - title:length() - 5) . '╗'));
		output:line(Ansi:color256(code: 51, text: self:boxed(inner: 'Threads: ' . threads . '   Points: ' . points . '   Refresh: ' . refreshMs . 'ms', width: 76)));
		output:line(Ansi:bold() . Ansi:color256(code: 51, text: '╚' . self:bar(width: 74) . '╝'));

		self:drawDomain(threads: threads);

		local Function of Int is sampler: local Function of Int(Int is threadIndex, Int is count){
			local Int is hits: 0;
			local Int is done: 0;
			local Int is batch: count / 100 + 1;
			local Int is lastX: 500;
			local Int is lastY: 500;
			local Int is lastHits: 0;
			local Int is lastDraw: Process:clockMs();

			While:condition(
				evaluate: local Function of Boolean(){
					return done < count;
				},
				iteration: local Function(){
					local Int is b: 0;
					While:condition(
						evaluate: local Function of Boolean(){
							return b < batch && done < count;
						},
						iteration: local Function(){
							local Float is x: math:fastRandom();
							local Float is y: math:fastRandom();
							if ((x * x + y * y) <= 1.0) {
								hits: hits + 1;
							}
							lastX: math:toInt(value: x * 1000.0);
							lastY: math:toInt(value: y * 1000.0);
							done: done + 1;
							b: b + 1;
						}
					);
					Process:atomicAdd(slot: 0, value: batch);
					Process:atomicAdd(slot: 1, value: hits - lastHits);
					lastHits: hits;
					Process:atomicPut(slot: threadIndex * 2 + 2, value: lastX);
					Process:atomicPut(slot: threadIndex * 2 + 3, value: lastY);

					# Thread 0 doubles as the display thread.
					if (threadIndex == 0) {
						local Int is now: Process:clockMs();
						if (now - lastDraw >= refreshMs) {
							self:drawProgress(threads: threads);
							lastDraw: now;
						}
					}
				}
			);
			return hits;
		};

		local Int is startedAtMs: Process:clockMs();
		local Int is totalHits: Parallel:run(threads: threads, iterations: points, worker: sampler);
		local Int is elapsedMs: Process:clockMs() - startedAtMs;

		self:drawProgress(threads: threads);
		output:line(Ansi:showCursor());
		self:printStats(totalHits: totalHits, points: points, elapsedMs: elapsedMs, threads: threads);
	}

	## Renders the sampling domain: unit square with the inscribed circle.
	##
	## @param threads: Thread count (markers appear as sampling proceeds).
	local Function is drawDomain(Int is threads){
		local Int is row: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return row < self:gridH; },
			iteration: local Function(){
				output:line(self:domainRow(row: row, threads: threads));
				row: row + 1;
			}
		);
		output:line('');
	}

	## Builds one domain row: circle interior/exterior shading plus any live
	## thread markers.
	##
	## @param row: Grid row index.
	## @param threads: Thread count for marker lookup.
	## @return: Rendered row string.
	local Function of String is domainRow(Int is row, Int is threads){
		local String is buf: '';
		local Int is col: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return col < self:gridW; },
			iteration: local Function(){
				local Float is cx: ((math:toFloat(value: col) + 0.5) / math:toFloat(value: self:gridW)) * 2.0 - 1.0;
				local Float is cy: ((math:toFloat(value: row) + 0.5) / math:toFloat(value: self:gridH)) * 2.0 - 1.0;
				local Float is dist: math:sqrt(value: cx * cx + cy * cy);

				local Int is marker: self:markerAt(col: col, row: row, threads: threads);
				if (marker >= 0) {
					buf: buf . Ansi:color256(code: self:threadColor(index: marker), text: '●');
				} else if (dist <= 1.0) {
					buf: buf . Ansi:color256(code: 236, text: '·');
				} else {
					buf: buf . ' ';
				}
				col: col + 1;
			}
		);
		return buf;
	}

	## Returns the index of the thread whose current sample lands on this cell,
	## or -1 when none does.
	##
	## @param col: Grid column.
	## @param row: Grid row.
	## @param threads: Thread count.
	## @return: Thread index, or -1.
	local Function of Int is markerAt(Int is col, Int is row, Int is threads){
		local Int is i: 0;
		local Int is found: -1;
		While:condition(
			evaluate: local Function of Boolean(){
				return i < threads && found < 0;
			},
			iteration: local Function(){
				local Int is gx: (Process:atomicGet(slot: i * 2 + 2) * self:gridW) / 1000;
				local Int is gy: (Process:atomicGet(slot: i * 2 + 3) * self:gridH) / 1000;
				if (gx == col && gy == row) {
					found: i;
				}
				i: i + 1;
			}
		);
		return found;
	}

	## Redraws the domain grid and the live statistics panel in place.
	##
	## @param threads: Thread count.
	local Function is drawProgress(Int is threads){
		output:line(Ansi:moveTo(row: 4, col: 1));
		self:drawDomain(threads: threads);

		local Int is samples: Process:atomicGet(slot: 0);
		local Int is hits: Process:atomicGet(slot: 1);
		local Float is pi: 0.0;
		if (samples > 0) {
			pi: (4.0 * math:toFloat(value: hits)) / math:toFloat(value: samples);
		}
		output:line(Ansi:color256(code: 220, text: '  samples: ' . samples . '  hits: ' . hits . '  pi ≈ ' . self:piText(value: pi) . '  threads: ' . threads));
	}

	## Prints the final statistics block.
	##
	## @param totalHits: Sum of all worker hit counts.
	## @param points: Total samples requested.
	## @param elapsedMs: Wall-clock run duration.
	## @param threads: Thread count used.
	local Function is printStats(Int is totalHits, Int is points, Int is elapsedMs, Int is threads){
		local Float is pi: (4.0 * math:toFloat(value: totalHits)) / math:toFloat(value: points);
		local Float is err: math:abs(value: pi - 3.14159265358979);
		local Int is perSec: 0;
		if (elapsedMs > 0) {
			perSec: (points * 1000) / elapsedMs;
		}

		output:line('');
		output:line(Ansi:bold() . Ansi:color256(code: 51, text: '╔═ Results ' . self:bar(width: 64) . '╗'));
		output:line(Ansi:color256(code: 51, text: '║ Pi ≈ ' . self:piText(value: pi) . '  (error ' . self:piText(value: err) . ')'));
		output:line(Ansi:color256(code: 51, text: '║ Points: ' . points . '  Hits: ' . totalHits . '  Threads: ' . threads));
		output:line(Ansi:color256(code: 51, text: '║ Time: ' . elapsedMs . ' ms  Throughput: ' . perSec . ' points/sec'));
		output:line(Ansi:bold() . Ansi:color256(code: 51, text: '╚' . self:bar(width: 74) . '╝'));
	}

	## Formats a float with three decimal places (fixed-width approximation).
	##
	## @param value: Value to format.
	## @return: Text with exactly three decimals.
	local Function of String is piText(Float is value){
		local Int is thousandths: math:toInt(value: math:round(value: value * 1000.0));
		local Int is whole: thousandths / 1000;
		local Int is frac: thousandths % 1000;
		local String is fracText: '' . frac;
		if (frac < 10) {
			fracText: '00' . fracText;
		} else if (frac < 100) {
			fracText: '0' . fracText;
		}
		return '' . whole . '.' . fracText;
	}

	## Maps a thread index to a distinct 256-color code.
	##
	## @param index: Thread index.
	## @return: Color code spread across the 6x6x6 cube.
	local Function of Int is threadColor(Int is index){
		return Ansi:cubeIndex(r: index % 6, g: (index / 2) % 6, b: 5 - (index % 5));
	}

	## Pads an inner text with spaces inside a `║ ... ║` border of the given width.
	##
	## @param inner: Row text.
	## @param width: Total rendered width including borders.
	## @return: Padded, bordered row.
	local Function of String is boxed(String is inner, Int is width){
		local String is line: '║ ' . inner;
		local Int is pad: width - 2 - inner:length();
		if (pad < 1) {
			pad: 1;
		}
		local Int is i: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return i < pad; },
			iteration: local Function(){
				line: line . ' ';
				i: i + 1;
			}
		);
		return line . '║';
	}

	## Builds a horizontal box bar of the given length.
	##
	## @param width: Number of `═` segments.
	## @return: Bar string.
	local Function of String is bar(Int is width){
		local String is barText: '';
		local Int is i: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return i < width; },
			iteration: local Function(){
				barText: barText . '═';
				i: i + 1;
			}
		);
		return barText;
	}

}
