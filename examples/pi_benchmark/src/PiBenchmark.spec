#! Monte Carlo Pi benchmark: parallel point sampling with a live domain
#! visualization, per-thread sample markers, and a running approximation.

## Parallel Monte Carlo Pi benchmark with live terminal domain rendering.
Class is PiBenchmark{

	replace Array of Array of String is using: [
		['base', 'sys', as Ansi()],
		['base', 'math', as Math()],
		['base', 'sys', as Output()],
		['base', 'sys', as Parallel()],
		['base', 'sys', as Process()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		[PiStats]
	];

	local Int is gridW: 44;
	local Int is gridH: 22;
	local PiStats is stats: PiStats:init();

	## Entry point; reads optional [args] (`threads`, `points`, `refresh`) and runs the parallel benchmark.
	replace Function is init(Map of String to String is args){
		local Int is threads: args:getInt(key: 'threads', default: 4);
		local Int is points: args:getInt(key: 'points', default: 1_000_000_000);
		local Int is refreshMs: args:getInt(key: 'refresh', default: 40);

		if(check: { threads < 1 }, then: {
			threads: 1;
		});
		if(check: { threads > 16 }, then: {
			threads: 16;
		});

		line(clearScreen() . moveTo(row: 1, col: 1) . hideCursor());
		local String is title: 'Monte Carlo Pi Benchmark';
		line(bold() . color256(code: 51, text: '╔═ ' . title . ' ' . self:stats:bar(width: 76 - title:length() - 5) . '╗'));
		line(color256(code: 51, text: self:stats:boxed(inner: 'Threads: ' . threads . '   Points: ' . points . '   Refresh: ' . refreshMs . 'ms', width: 76)));
		line(bold() . color256(code: 51, text: '╚' . self:stats:bar(width: 74) . '╝'));

		self:drawDomain(threads: threads);

		local Function of Int is sampler: local Function of Int(Int is threadIndex, Int is count){
			local Int is hits: 0;
			local Int is done: 0;
			local Int is batch: count / 100 + 1;
			local Int is lastX: 500;
			local Int is lastY: 500;
			local Int is lastHits: 0;
			local Int is lastDraw: clockMs();

			while({ done < count }, {
				while([Int is b: 0], { b < batch && done < count }, {
					local Float is x: fastRandom();
					local Float is y: fastRandom();
					if({ (x * x + y * y) <= 1.0 }, {
						hits++;
					});
					lastX: toInt(value: x * 1000.0);
					lastY: toInt(value: y * 1000.0);
					done++;
					b++;
				});
				atomicAdd(slot: 0, value: batch);
				atomicAdd(slot: 1, value: hits - lastHits);
				lastHits: hits;
				atomicPut(slot: threadIndex * 2 + 2, value: lastX);
				atomicPut(slot: threadIndex * 2 + 3, value: lastY);

				if({ threadIndex == 0 }, {
					local Int is now: clockMs();
					if({ now - lastDraw >= refreshMs }, {
						self:drawProgress(threads: threads);
						lastDraw: now;
					});
				});
			});
			return hits;
		};

		local Int is startedAtMs: clockMs();
		local Int is totalHits: Parallel:run(threads: threads, iterations: points, worker: sampler);
		local Int is elapsedMs: clockMs() - startedAtMs;

		self:drawProgress(threads: threads);
		line(showCursor());
		self:printStats(totalHits: totalHits, points: points, elapsedMs: elapsedMs, threads: threads);
	}

	## Renders the full `[gridW x gridH]` unit-circle domain with live thread markers.
	local Function is drawDomain(Int is threads){
		while(
			[Int is row: 0],
			{ row < self:gridH },
			{
				line(self:domainRow(row: row, threads: threads));
				row++;
			}
		);
		line('');
	}

	## Builds one rendered [row] of the unit-circle visualization across [threads].
	local Function of String is domainRow(Int is row, Int is threads){
		local String is buf: '';
		while(
			[Int is col: 0],
			{ col < self:gridW },
			{
				local Float is cx: ((toFloat(value: col) + 0.5) / toFloat(value: self:gridW)) * 2.0 - 1.0;
				local Float is cy: ((toFloat(value: row) + 0.5) / toFloat(value: self:gridH)) * 2.0 - 1.0;
				local Float is dist: sqrt(value: cx * cx + cy * cy);

				local Int is marker: self:markerAt(col: col, row: row, threads: threads);
				match(when: [
					{ marker >= 0 }: {
						buf: buf . color256(code: self:stats:threadColor(index: marker), text: '●');
					},
					{ dist <= 1.0 }: {
						buf: buf . color256(code: 236, text: '·');
					},
					else: {
						buf: buf . ' ';
					}
				]);
				col++;
			}
		);
		return buf;
	}

	## Returns the thread index currently occupying `(col, row)`, or `-1` if none.
	local Function of Int is markerAt(Int is col, Int is row, Int is threads){
		local Int is found: -1;
		while(
			[Int is i: 0],
			{ i < threads && found < 0 },
			{
				local Int is gx: (atomicGet(slot: i * 2 + 2) * self:gridW) / 1000;
				local Int is gy: (atomicGet(slot: i * 2 + 3) * self:gridH) / 1000;
				if({ gx == col && gy == row }, {
					found: i;
				});
				i++;
			}
		);
		return found;
	}

	## Redraws the live domain and running `pi` estimate from atomic counters.
	local Function is drawProgress(Int is threads){
		line(moveTo(row: 4, col: 1));
		self:drawDomain(threads: threads);

		local Int is samples: atomicGet(slot: 0);
		local Int is hits: atomicGet(slot: 1);
		local Float is pi: self:stats:estimatePi(hits: hits, samples: samples);
		line(color256(code: 220, text: '  samples: ' . samples . '  hits: ' . hits . '  pi ≈ ' . self:stats:piText(value: pi) . '  threads: ' . threads));
	}

	## Prints the final Pi estimate, error, elapsed time, and throughput summary box.
	local Function is printStats(Int is totalHits, Int is points, Int is elapsedMs, Int is threads){
		local Float is pi: self:stats:estimatePi(hits: totalHits, samples: points);
		local Float is err: abs(value: pi - 3.14159265358979);
		local Int is perSec: 0;
		if(check: { elapsedMs > 0 }, then: {
			perSec: (points * 1000) / elapsedMs;
		});

		line('');
		line(bold() . color256(code: 51, text: '╔═ Results ' . self:stats:bar(width: 64) . '╗'));
		line(color256(code: 51, text: '║ Pi ≈ ' . self:stats:piText(value: pi) . '  (error ' . self:stats:piText(value: err) . ')'));
		line(color256(code: 51, text: '║ Points: ' . points . '  Hits: ' . totalHits . '  Threads: ' . threads));
		line(color256(code: 51, text: '║ Time: ' . elapsedMs . ' ms  Throughput: ' . perSec . ' points/sec'));
		line(bold() . color256(code: 51, text: '╚' . self:stats:bar(width: 74) . '╝'));
	}

}
