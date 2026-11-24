#! Package cleopi:view
#! Pure Cleo view bound to [CleoPiViewModel].

## Renders the Cleo dashboard (domain grid, worker bar, live stats, and progress bar) from [CleoPiViewModel].
Class is CleoDashboard{
	replace [String] is namespace: ['cleopi', 'view'];

	merge [[String]] is using: [
		['base', 'cleo', [Cleo, CleoSection, CleoColor, as CleoColor(), CleoWidth, as CleoWidth(), BorderStyle, TitlePlacement]],
		['base', 'sys', 'thread', ThreadScope],
		['cleopi', 'view', DomainGrid],
		['cleopi', 'vm', CleoPiViewModel]
	];

	local CleoPiViewModel is vm: CleoPiViewModel();
	local DomainGrid is grid: DomainGrid();

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

	replace Function is init(CleoPiViewModel is vm){
		:vm: vm;
		grid: DomainGrid(width: vm:gridWidth, height: vm:gridHeight);

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
			title: vm:domainTitle(),
			titleColor: ansi(code: 159),
			titleBgColor: ansi(code: 23),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 195)
		);
		domainSlots: [];
		local Int is r: 0;
		while({ r < grid:height }, {
			domainSlots:push(item: domainSec:addLine(text: grid:renderRow(row: r, threads: vm:threads, telemetry: vm:telemetry), color: ansi(code: 195)));
			r: r + 1;
		});

		wSec: ui:addSection(
			title: vm:workersTitle(),
			titleColor: ansi(code: 120),
			titleBgColor: ansi(code: 22),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 82)
		);
		wBarSlot: wSec:addLine(text: vm:workerBarText(), color: ansi(code: 82), rightText: vm:workerCountText());

		sSec: ui:addSection(
			title: ' Live Stats ',
			titleColor: ansi(code: 159),
			titleBgColor: ansi(code: 23),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 195)
		);
		estSlot: sSec:addLine(text: vm:piEstimateText(), color: ansi(code: 82), rightText: vm:piErrorText(), bold: true);
		statSlot: sSec:addLine(text: vm:samplesText(), color: ansi(code: 117), rightText: vm:throughputText());

		pSec: ui:addSection(
			title: ' Progress ',
			titleColor: ansi(code: 120),
			titleBgColor: ansi(code: 22),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: ansi(code: 195)
		);
		pSlot: pSec:addProgressArea(
			text: vm:progressText(),
			stage1Color: ansi(code: 46),
			stage2Color: ansi(code: 39),
			trackColor: ansi(code: 236),
			showTwoStagePercent: false
		);

		vm:onStateChanged: {
			sync();
		};
	}

	## Starts the Cleo live render loop on [scope].
	Function is start(ThreadScope is scope){
		ui:start(scope: scope);
	}

	## Refreshes all dashboard sections from [vm].
	Function is sync(){
		local Int is r: 0;
		while({ r < grid:height }, {
			domainSec:updateText(index: domainSlots:get(index: r), text: grid:renderRow(row: r, threads: vm:threads, telemetry: vm:telemetry));
			r: r + 1;
		});

		wSec:updateText(index: wBarSlot, text: vm:workerBarText(), rightText: vm:workerCountText());
		sSec:updateText(index: estSlot, text: vm:piEstimateText(), rightText: vm:piErrorText());
		sSec:updateText(index: statSlot, text: vm:samplesText(), rightText: vm:throughputText());
		pSec:updateProgress(index: pSlot, text: vm:progressText(), stage1: vm:progressFraction(), stage2: 0.0);

		ui:markDirty();
		ui:flush();
	}

	## Finalizes the Cleo terminal UI.
	Function is finish(){
		ui:finish();
	}
}
