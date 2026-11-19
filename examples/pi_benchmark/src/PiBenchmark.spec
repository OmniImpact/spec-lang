#! Monte Carlo Pi benchmark: parallel point sampling with a live domain
#! visualization, per-thread sample markers, and a running approximation.

## Parallel Monte Carlo Pi benchmark with live terminal domain rendering.
Class is PiBenchmark{

	replace Array of Array of String is using: [
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', TitlePlacement],
		['base', 'sys', as Ansi()],
		['base', 'math', as Math()],
		['base', 'sys', as Output()],
		['base', 'sys', as Parallel()],
		['base', 'core', SpecError],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Process()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		[PiStats]
	];

	local Int is gridW: 44;
	local Int is gridH: 22;
	local PiStats is stats: PiStats:init();

	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		return false;
	}

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
		line(bold() . color256(code: 51, text: '╔═ ' . title . ' ' . :stats:bar(width: 76 - title:length() - 5) . '╗'));
		line(color256(code: 51, text: :stats:boxed(inner: 'Threads: ' . threads . '   Points: ' . points . '   Refresh: ' . refreshMs . 'ms', width: 76)));
		line(bold() . color256(code: 51, text: '╚' . :stats:bar(width: 74) . '╝'));

		:drawDomain(threads: threads);

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
						:drawProgress(threads: threads);
						lastDraw: now;
					});
				});
			});
			return hits;
		};

		local Int is startedAtMs: clockMs();
		local Int is totalHits: 0;
		ThreadScope:open(body: local Function(ThreadScope is scope){
			totalHits: Parallel:run(scope: scope, threads: threads, iterations: points, worker: sampler);
		});
		local Int is elapsedMs: clockMs() - startedAtMs;

		:drawProgress(threads: threads);
		line(showCursor());
		:printStats(totalHits: totalHits, points: points, elapsedMs: elapsedMs, threads: threads);
	}

	## Renders the full `[gridW x gridH]` unit-circle domain with live thread markers.
	local Function is drawDomain(Int is threads){
		while(
			[Int is row: 0],
			{ row < :gridH },
			{
				line(:domainRow(row: row, threads: threads));
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
			{ col < :gridW },
			{
				local Float is cx: ((toFloat(value: col) + 0.5) / toFloat(value: :gridW)) * 2.0 - 1.0;
				local Float is cy: ((toFloat(value: row) + 0.5) / toFloat(value: :gridH)) * 2.0 - 1.0;
				local Float is dist: sqrt(value: cx * cx + cy * cy);

				local Int is marker: :markerAt(col: col, row: row, threads: threads);
				match(when: [
					{ marker >= 0 }: {
						buf: buf . color256(code: :stats:threadColor(index: marker), text: '●');
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
		local Int is i: 0;
		while({ i < threads }, local Function of Boolean(){
			local Int is gx: (atomicGet(slot: i * 2 + 2) * :gridW) / 1000;
			local Int is gy: (atomicGet(slot: i * 2 + 3) * :gridH) / 1000;
			if({ gx == col && gy == row }, {
				found: i;
				return false;
			});
			i++;
			return true;
		});
		return found;
	}

	## Redraws the live domain and running `pi` estimate from atomic counters.
	local Function is drawProgress(Int is threads){
		line(moveTo(row: 4, col: 1));
		:drawDomain(threads: threads);

		local Int is samples: atomicGet(slot: 0);
		local Int is hits: atomicGet(slot: 1);
		local Float is pi: :stats:estimatePi(hits: hits, samples: samples);
		line(color256(code: 220, text: '  samples: ' . samples . '  hits: ' . hits . '  pi ≈ ' . :stats:piText(value: pi) . '  threads: ' . threads));
	}

	## Prints the final Pi estimate, error, elapsed time, and throughput summary via Cleo.
	local Function is printStats(Int is totalHits, Int is points, Int is elapsedMs, Int is threads){
		local Float is pi: :stats:estimatePi(hits: totalHits, samples: points);
		local Float is err: abs(value: pi - 3.14159265358979);
		local Int is perSec: 0;
		if(check: { elapsedMs > 0 }, then: {
			perSec: (points * 1000) / elapsedMs;
		});

		local Cleo is ui: Cleo:init(
			title: ' pi_benchmark ',
			titleColor: CleoColor:ansi(code: 255),
			titleBgColor: CleoColor:ansi(code: 236),
			width: CleoWidth:percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 237)
		);
		local CleoSection is rSec: ui:addSection(
			title: ' Results ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		rSec:addLine(text: 'Pi ≈ ' . :stats:piText(value: pi), color: CleoColor:ansi(code: 255), rightText: 'error ' . :stats:piText(value: err));
		rSec:addLine(text: 'Points: ' . points . ' · Hits: ' . totalHits, color: CleoColor:ansi(code: 250), rightText: 'Threads: ' . threads);
		rSec:addLine(text: 'Time: ' . elapsedMs . ' ms', color: CleoColor:ansi(code: 250), rightText: 'Throughput: ' . perSec . ' points/sec');
		ui:flushFinal();
	}

}
