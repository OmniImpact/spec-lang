#! Live Cleo terminal UI dashboard for CleoPi.

## Manages the Cleo layout (domain grid, worker bar, live stats, and progress bar) and periodic updates.
Class is CleoDashboard{
	merge [[String]] is using: [
		['base', 'cleo', [Cleo, CleoSection, CleoColor, as CleoColor(), CleoWidth, as CleoWidth(), BorderStyle, TitlePlacement]],
		['base', 'math', as Math()],
		['base', 'sys', 'thread', ThreadScope],
		[DomainGrid],
		[PiStats],
		[PiTelemetry]
	];

	local Int is threads: 4;
	local Int is points: 1000000000;
	local Int is startedAtMs: 0;
	local DomainGrid is grid: DomainGrid();
	local PiStats is stats: PiStats();

	local Cleo is ui: Cleo();
	local CleoSection is domainSec: CleoSection();
	local CleoSection is wSec: CleoSection();
	local CleoSection is sSec: CleoSection();
	local CleoSection is pSec: CleoSection();
	local [Int] is domainSlots: [];
	local Int is wBarSlot: 0;
	local Int is estSlot: 0;
	local Int is statSlot: 0;
	local Int is pSlot: 0;

	replace Function is init(Int is threads, Int is points, Int is startedAtMs, DomainGrid is grid, PiTelemetry is telemetry){
		:threads: threads;
		:points: points;
		:startedAtMs: startedAtMs;
		:grid: grid;

		ui: Cleo(
			title: ' cleopi ',
			titleColor: ansi(code: 231),
			titleBgColor: ansi(code: 24),
			width: percent(pct: 100),
			outerBorder: BorderStyle:THICK,
			dividerBorder: BorderStyle:THICK,
			borderColor: ansi(code: 33),
			dividerColor: ansi(code: 30),
			tickIntervalMs: 0
		);

		domainSec: ui:addSection(
			title: " Unit Circle Domain ({{threads}} threads · {{points}} pts) ",
			titleColor: ansi(code: 159),
			titleBgColor: ansi(code: 23),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 195)
		);
		domainSlots: [];
		local Int is r: 0;
		while({ r < grid:height }, {
			domainSlots:push(item: domainSec:addLine(text: grid:renderRow(row: r, threads: threads, telemetry: telemetry), color: ansi(code: 195)));
			r: r + 1;
		});

		wSec: ui:addSection(
			title: " Workers ({{threads}} threads) ",
			titleColor: ansi(code: 120),
			titleBgColor: ansi(code: 22),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 82)
		);
		wBarSlot: wSec:addLine(text: '', color: ansi(code: 82), rightText: "0/{{threads}} active");

		sSec: ui:addSection(
			title: ' Live Stats ',
			titleColor: ansi(code: 159),
			titleBgColor: ansi(code: 23),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 195)
		);
		estSlot: sSec:addLine(text: 'Pi ≈ 0.000', color: ansi(code: 82), rightText: 'error 3.142', bold: true);
		statSlot: sSec:addLine(text: 'Samples: 0 · Hits: 0', color: ansi(code: 117), rightText: '0 ms · 0 pts/sec');

		pSec: ui:addSection(
			title: ' Progress ',
			titleColor: ansi(code: 120),
			titleBgColor: ansi(code: 22),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 195)
		);
		pSlot: pSec:addProgressArea(
			text: "0/{{points}} points",
			stage1Color: ansi(code: 46),
			stage2Color: ansi(code: 39),
			trackColor: ansi(code: 236),
			showTwoStagePercent: false
		);
	}

	## Starts the Cleo live render loop on [scope].
	Function is start(ThreadScope is scope){
		ui:start(scope: scope);
	}

	## Refreshes all dashboard sections from [curSamples], [curHits], [nowMs], and [telemetry].
	Function is sync(Int is curSamples, Int is curHits, Int is nowMs, PiTelemetry is telemetry){
		local Int is r: 0;
		while({ r < grid:height }, {
			domainSec:updateText(index: domainSlots:get(index: r), text: grid:renderRow(row: r, threads: threads, telemetry: telemetry));
			r: r + 1;
		});

		local Int is activeCount: 0;
		local String is boxes: '';
		local Int is wi: 0;
		while({ wi < threads }, {
			if({ wi > 0 }, { boxes: "{{boxes}} "; });
			if({ telemetry:isWorkerActive(threadIndex: wi) }, {
				boxes: "{{boxes}}■";
				activeCount: activeCount + 1;
			}, {
				boxes: "{{boxes}}□";
			});
			wi: wi + 1;
		});
		wSec:updateText(index: wBarSlot, text: boxes, rightText: "{{activeCount}}/{{threads}} active");

		local Float is pi: stats:estimatePi(hits: curHits, samples: curSamples);
		local Float is err: abs(value: pi - 3.14159265358979);
		local Int is elapsed: nowMs - startedAtMs;
		local Int is perSec: if({ elapsed > 0 }, { (curSamples * 1000) / elapsed }, { 0 });
		sSec:updateText(index: estSlot, text: "Pi ≈ {{stats:piText(value: pi)}}", rightText: "error {{stats:piText(value: err)}}");
		sSec:updateText(index: statSlot, text: "Samples: {{curSamples}} · Hits: {{curHits}}", rightText: "{{elapsed}} ms · {{perSec}} pts/sec");

		local Float is pct: if({ points > 0 }, { toFloat(value: curSamples) / toFloat(value: points) }, { 1.0 });
		if({ pct > 1.0 }, { pct: 1.0; });
		pSec:updateProgress(index: pSlot, text: "{{curSamples}}/{{points}} points", stage1: pct, stage2: 0.0);

		ui:markDirty();
		ui:flush();
	}

	## Finalizes the Cleo terminal UI.
	Function is finish(){
		ui:finish();
	}
}
