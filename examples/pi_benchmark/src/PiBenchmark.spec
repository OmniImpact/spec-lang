#! Monte Carlo Pi benchmark: parallel point sampling wrapped in a live
#! dynamic Cleo UI with thick green/blue borders, worker activity bar,
#! running stats, and progress bar.

## Parallel Monte Carlo Pi benchmark with live Cleo terminal UI.
Class is PiBenchmark{

	replace [[String]] is using: [
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
		['base', 'struct', Array],
		[PiStats]
	];

	local Int is gridW: 44;
	local Int is gridH: 20;
	local PiStats is stats: PiStats();

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

		# Reset atomic slots: 0=samples, 1=hits, 2..33=thread coords, 100..115=worker active
		atomicPut(slot: 0, value: 0);
		atomicPut(slot: 1, value: 0);
		while([Int is wi: 0], { wi < threads }, {
			atomicPut(slot: wi * 2 + 2, value: 500);
			atomicPut(slot: wi * 2 + 3, value: 500);
			atomicPut(slot: 100 + wi, value: 0);
			wi++;
		});

		local Cleo is ui: Cleo(
			title: ' pi_benchmark ',
			titleColor: CleoColor:ansi(code: 231),
			titleBgColor: CleoColor:ansi(code: 24),
			width: CleoWidth:percent(pct: 100),
			outerBorder: BorderStyle:THICK,
			dividerBorder: BorderStyle:THICK,
			borderColor: CleoColor:ansi(code: 33),
			dividerColor: CleoColor:ansi(code: 30),
			tickIntervalMs: 0
		);

		local CleoSection is domainSec: ui:addSection(
			title: " Unit Circle Domain ({{threads}} threads · {{points}} pts) ",
			titleColor: CleoColor:ansi(code: 159),
			titleBgColor: CleoColor:ansi(code: 23),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 195)
		);
		local Array of Int is domainSlots: Array();
		while([Int is r: 0], { r < gridH }, {
			domainSlots:add(item: domainSec:addLine(text: domainRow(row: r, threads: threads), color: CleoColor:ansi(code: 195)));
			r++;
		});

		local CleoSection is wSec: ui:addSection(
			title: " Workers ({{threads}} threads) ",
			titleColor: CleoColor:ansi(code: 120),
			titleBgColor: CleoColor:ansi(code: 22),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 82)
		);
		local Int is wBarSlot: wSec:addLine(text: '', color: CleoColor:ansi(code: 82), rightText: "0/{{threads}} active");

		local CleoSection is sSec: ui:addSection(
			title: ' Live Stats ',
			titleColor: CleoColor:ansi(code: 159),
			titleBgColor: CleoColor:ansi(code: 23),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 195)
		);
		local Int is estSlot: sSec:addLine(text: 'Pi ≈ 0.000', color: CleoColor:ansi(code: 82), rightText: 'error 3.142', bold: true);
		local Int is statSlot: sSec:addLine(text: 'Samples: 0 · Hits: 0', color: CleoColor:ansi(code: 117), rightText: '0 ms · 0 pts/sec');

		local CleoSection is pSec: ui:addSection(
			title: ' Progress ',
			titleColor: CleoColor:ansi(code: 120),
			titleBgColor: CleoColor:ansi(code: 22),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 195)
		);
		local Int is pSlot: pSec:addProgressArea(
			text: "0/{{points}} points",
			stage1Color: CleoColor:ansi(code: 46),
			stage2Color: CleoColor:ansi(code: 39),
			trackColor: CleoColor:ansi(code: 236),
			showTwoStagePercent: false
		);

		local Int is startedAtMs: clockMs();

		local Function is syncUi: local Function(Int is curSamples, Int is curHits, Int is nowMs){
			local Int is r2: 0;
			while({ r2 < gridH }, {
				domainSec:updateText(index: domainSlots:get(index: r2), text: domainRow(row: r2, threads: threads));
				r2: r2 + 1;
			});

			local Int is activeCount: 0;
			local String is boxes: '';
			local Int is wi2: 0;
			while({ wi2 < threads }, {
				if({ wi2 > 0 }, { boxes: "{{boxes}} "; });
				if(check: { atomicGet(slot: 100 + wi2) != 0 }, then: {
					boxes: "{{boxes}}■";
					activeCount: activeCount + 1;
				}, else: {
					boxes: "{{boxes}}□";
				});
				wi2: wi2 + 1;
			});
			wSec:updateText(index: wBarSlot, text: boxes, rightText: "{{activeCount}}/{{threads}} active");

			local Float is pi: stats:estimatePi(hits: curHits, samples: curSamples);
			local Float is err: abs(value: pi - 3.14159265358979);
			local Int is elapsed: nowMs - startedAtMs;
			local Int is perSec: if({ elapsed > 0 }, { (curSamples * 1000) / elapsed }, { 0 });
			sSec:updateText(index: estSlot, text: "Pi ≈ {{stats:piText(value: pi)}}", rightText: "error {{stats:piText(value: err)}}");
			sSec:updateText(index: statSlot, text: "Samples: {{curSamples}} · Hits: {{curHits}}", rightText: "{{elapsed}} ms · {{perSec}} pts/sec");

			local Float is pct: if({ points > 0 }, { (curSamples as Float) / (points as Float) }, { 1.0 });
			if({ pct > 1.0 }, { pct: 1.0; });
			pSec:updateProgress(index: pSlot, text: "{{curSamples}}/{{points}} points", stage1: pct, stage2: 0.0);

			ui:markDirty();
			ui:flush();
		};

		local Function of Int is sampler: local Function of Int(Int is threadIndex, Int is count){
			atomicPut(slot: 100 + threadIndex, value: 1);
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
						syncUi(curSamples: atomicGet(slot: 0), curHits: atomicGet(slot: 1), nowMs: now);
						lastDraw: now;
					});
				});
			});
			atomicPut(slot: 100 + threadIndex, value: 0);
			return hits;
		};

		local Int is totalHits: 0;
		ThreadScope:open(body: local Function(ThreadScope is scope){
			ui:start(scope: scope);
			totalHits: Parallel:run(scope: scope, threads: threads, iterations: points, worker: sampler);
			syncUi(curSamples: points, curHits: totalHits, nowMs: clockMs());
			ui:finish();
		});
	}

	## Builds one rendered [row] of the unit-circle visualization across [threads].
	local Function of String is domainRow(Int is row, Int is threads){
		local String is buf: '';
		while(
			[Int is col: 0],
			{ col < gridW },
			{
				local Float is cx: ((toFloat(value: col) + 0.5) / toFloat(value: gridW)) * 2.0 - 1.0;
				local Float is cy: ((toFloat(value: row) + 0.5) / toFloat(value: gridH)) * 2.0 - 1.0;
				local Float is dist: sqrt(value: cx * cx + cy * cy);

				local Int is marker: markerAt(col: col, row: row, threads: threads);
				match(when: [
					{ marker >= 0 }: {
						buf: buf . color256(code: stats:threadColor(index: marker), text: '●');
					},
					{ dist <= 1.0 }: {
						buf: buf . color256(code: 24, text: '·');
					},
					else: {
						buf: "{{buf}} ";
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
			local Int is gx: (atomicGet(slot: i * 2 + 2) * gridW) / 1000;
			local Int is gy: (atomicGet(slot: i * 2 + 3) * gridH) / 1000;
			if({ gx == col && gy == row }, {
				found: i;
				return false;
			});
			i++;
			return true;
		});
		return found;
	}
}
