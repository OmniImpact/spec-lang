#! Package specunit
#! The SpecUnit test runner — a Spec program that tests Spec programs.
#! It is NOT the compiler and has no compiler test mode: it invokes the
#! spec compiler as a command (one compile thread per test), executes
#! each produced binary under a timeout, records the verdict, and
#! deletes the compiled test (see KNOWLEDGE-SPECDEV.md §4a).
#!
#! CLI:
#!   specunit -s ./bin/spec -t tests/
#!   -s  the spec compiler executable (default: <root>/bin/spec)
#!   -t  a test directory, relative to the root; repeat the flag or
#!       separate entries with commas. Scanned recursively (dot
#!       directories skipped).
#!
#! Classification — every candidate .spec file declares itself by its
#! `#!` banner; unmarked files that mention the specunit package are
#! suites, everything else is a helper or a standalone program and is
#! skipped:
#!   #! specunit: suite      compile, run, exit 0 and no [FAIL] required
#!   #! specunit: negative   compilation MUST fail; every
#!                           `#! expect: <text>` must appear in the
#!                           diagnostics
#!   #! specunit: run-fail   compile must succeed, the run MUST exit
#!                           non-zero, every expect must appear in the
#!                           run output
#!   #! specunit: helper     skip (multi-file fixture partners)
#!
#! Architecture:
#! - SpecTestRegistry: the held state — the work queue and the results.
#!   Held arrays and maps are mutex-protected, so the Parallel wave
#!   reads the queue and records results from every worker thread
#!   safely.
#! - SpecUnit: the entry program. Scans the -t trees, dispatches the
#!   compile+execute wave across Parallel:run workers (threads =
#!   cores - 2), and prints the summary when all tests are done.
#!
#! Report ordering: results appear in queue order. dirList order is the
#! filesystem's; a Spec-level ordering primitive (String:compare over
#! the Buf floor) is a tracked follow-up.

Class is SuiteResult{
	replace [String] is namespace: ['specunit'];

	String is name;
	Boolean is passed: true;
	String is note: '';
	String is report: '';

	replace Function is init(String is suiteName){
		:name: suiteName;
	}
}

Class is WorkItem{
	replace [String] is namespace: ['specunit'];

	String is path;
	String is kind;
	[String] is expect: [];
	String is inlineSource: '';
	Int is expectedTests: 1;
	Int is priorityPosition: 0;

	replace Function is init(String is itemPath, String is itemKind, [String] is itemExpect, String is source: '', Int is expectedTests: 1, Int is priorityPosition: 0){
		:path: itemPath;
		:kind: itemKind;
		:expect: itemExpect;
		:inlineSource: source;
		:expectedTests: expectedTests;
		:priorityPosition: priorityPosition;
	}
}

Class is ReadyRunItem{
	replace [String] is namespace: ['specunit'];

	WorkItem is item;
	Int is idx: -1;
	String is binPath: '';
	Int is compileCpuUs: 0;
	Int is compileRssKb: 0;

	replace Function is init(WorkItem is item, Int is idx, String is binPath, Int is compileCpuUs, Int is compileRssKb){
		:item: item;
		:idx: idx;
		:binPath: binPath;
		:compileCpuUs: compileCpuUs;
		:compileRssKb: compileRssKb;
	}
}

Class is SpecTestUi{
	replace [String] is namespace: ['specunit'];

	replace [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Cleo is ui;
	CleoSection is wSec;
	Int is wBarSlot: 0;
	CleoSection is sSec;
	CleoSection is rSec;
	CleoSection is pSec;
	Int is pSlot: 0;
	Int is total: 0;
	Int is testsTotal: 0;

	[Int] is workerActive: [];
	Map of String to Int is suiteNameToSlotId: Map:init();
	Int is startedCount: 0;
	Int is completedCount: 0;
	Int is passedCount: 0;
	Int is failedCount: 0;
	Int is testsCompleted: 0;
	Int is testsPassed: 0;
	Int is testsFailed: 0;
	Int is totalCpuUs: 0;
	Int is totalRssKb: 0;
	Int is peakRssKb: 0;
	Int is metricSamples: 0;

	replace Function is init(Cleo is ui, CleoSection is wSec, Int is wBarSlot, CleoSection is sSec, CleoSection is rSec, CleoSection is pSec, Int is pSlot, Int is total, Int is testsTotal, Int is threads, Map of String to Int is nameToSlot){
		:ui: ui;
		:wSec: wSec;
		:wBarSlot: wBarSlot;
		:sSec: sSec;
		:rSec: rSec;
		:pSec: pSec;
		:pSlot: pSlot;
		:total: total;
		:testsTotal: testsTotal;
		:suiteNameToSlotId: nameToSlot;
		:workerActive: [];
		times(count: threads, worker: local Function(Int is _i){
			:workerActive:push(item: 0);
		});
		:renderWorkersBar();
	}

	Function is renderWorkersBar(){
		local Int is n: :workerActive:length();
		local Int is activeCount: 0;
		local String is boxes: '';
		times(count: n, worker: local Function(Int is i){
			local Int is st: :workerActive:get(index: i);
			if({ i > 0 }, { boxes: boxes . ' '; });
			if(check: { st != 0 }, then: {
				boxes: boxes . '■';
				activeCount: activeCount + 1;
			}, else: {
				boxes: boxes . '□';
			});
		});
		local String is rt: (activeCount as String) . '/' . (n as String) . ' active';
		:wSec:updateText(index: :wBarSlot, text: boxes, rightText: rt);
	}

	Function is syncProgress(){
		local Float is s1: if({ :testsTotal > 0 }, { (:testsCompleted as Float) / (:testsTotal as Float) }, { if({ :total > 0 }, { (:completedCount as Float) / (:total as Float) }, { 1.0 }) });
		local Float is s2: if({ :total > 0 }, { (:startedCount as Float) / (:total as Float) }, { 1.0 });
		if({ s1 > 1.0 }, { s1: 1.0; });
		if({ s2 > 1.0 }, { s2: 1.0; });
		local String is msg: (:completedCount as String) . '/' . (:total as String) . ' suites · ' . (:testsCompleted as String) . '/' . (:testsTotal as String) . ' tests (' . (:failedCount as String) . ' failed)';
		:pSec:updateProgress(index: :pSlot, text: msg, stage1: s1, stage2: s2);
	}

	Function is onStarted(Int is threadIndex, String is itemPath){
		:startedCount: :startedCount + 1;
		if({ !:ui:directOutput }, {
			if({ threadIndex >= 0 && threadIndex < :workerActive:length() }, {
				:workerActive:set(index: threadIndex, item: 1);
			});
			:renderWorkersBar();
		});

		local Int is slotId: :sSec:addShapeThrobber(
			shape: ThrobberShape:CIRCLE_DOT,
			effect: ThrobberEffect:BLINK,
			color: CleoColor:ansi(code: 254),
			text: itemPath,
			rightText: 'compiling'
		);
		:suiteNameToSlotId:set(key: itemPath, value: slotId);
		if({ !:ui:directOutput }, {
			:syncProgress();
			:ui:markDirty();
			:ui:flushUnlocked();
		});
	}

	Function is onCompiledReady(String is itemPath){
		if({ :ui:directOutput }, { return; });
		if({ :suiteNameToSlotId:has(key: itemPath) }, {
			local Int is slotId: :suiteNameToSlotId:get(key: itemPath, default: 0);
			:sSec:updateText(index: slotId, text: itemPath, rightText: 'queued');
			:ui:markDirty();
			:ui:flushUnlocked();
		});
	}

	Function is onRunning(Int is threadIndex, String is itemPath){
		if({ :ui:directOutput }, { return; });
		if({ threadIndex >= 0 && threadIndex < :workerActive:length() }, {
			:workerActive:set(index: threadIndex, item: 1);
		});
		:renderWorkersBar();
		if({ :suiteNameToSlotId:has(key: itemPath) }, {
			local Int is slotId: :suiteNameToSlotId:get(key: itemPath, default: 0);
			:sSec:updateText(index: slotId, text: itemPath, rightText: 'running');
			:ui:markDirty();
			:ui:flushUnlocked();
		});
	}

	Function is onWorkerIdle(Int is threadIndex){
		if({ :ui:directOutput }, { return; });
		if({ threadIndex >= 0 && threadIndex < :workerActive:length() }, {
			:workerActive:set(index: threadIndex, item: 0);
		});
		:renderWorkersBar();
	}

	Function is onResult(String is name, Boolean is passed, String is note, Int is expectedTests, Int is tPassed, Int is tFailed){
		:completedCount: :completedCount + 1;
		if({ passed }, { :passedCount: :passedCount + 1; });
		if({ !passed }, { :failedCount: :failedCount + 1; });
		local Int is actualTests: tPassed + tFailed;
		if({ actualTests <= 0 }, {
			actualTests: if({ expectedTests > 0 }, { expectedTests }, { 1 });
			if({ passed }, {
				tPassed: actualTests;
				tFailed: 0;
			}, {
				tPassed: 0;
				tFailed: actualTests;
			});
		});
		:testsTotal: :testsTotal + (actualTests - expectedTests);
		:testsCompleted: :testsCompleted + actualTests;
		:testsPassed: :testsPassed + tPassed;
		:testsFailed: :testsFailed + tFailed;

		if({ :suiteNameToSlotId:has(key: name) }, {
			local Int is slotId: :suiteNameToSlotId:get(key: name, default: 0);
			local String is rt: if({ passed }, { 'passed' }, { 'failed' });
			if({ :ui:directOutput }, {
				local Int is pct: if({ :total > 0 }, { (:completedCount * 100) / :total }, { 100 });
				rt: rt . ' · ' . (pct as String) . '% (' . (:completedCount as String) . '/' . (:total as String) . ')';
			});
			local String is badge: if({ passed }, { '●' }, { '✘' });
			local CleoColor is c: if({ passed }, { CleoColor:ansi(code: 255) }, { CleoColor:ansi(code: 242) });
			:sSec:resolveSlot(index: slotId, badge: badge, text: name, color: c, rightText: rt);
			:ui:commitSlotUnlocked(section: :sSec, slotId: slotId);
			:sSec:removeSlot(index: slotId);
		});

		if({ !:ui:directOutput }, {
			:syncProgress();
			:ui:markDirty();
			:ui:flushUnlocked();
		});
	}

	Function is onMetrics(Int is cpuUs, Int is rssKb){
		:totalCpuUs: :totalCpuUs + cpuUs;
		if({ rssKb > 0 }, {
			:totalRssKb: :totalRssKb + rssKb;
			:metricSamples: :metricSamples + 1;
			if({ rssKb > :peakRssKb }, { :peakRssKb: rssKb; });
		});
	}

	Function of String is fmtSec(Int is ms){
		local Int is whole: ms / 1000;
		local Int is frac: (ms % 1000) / 10;
		local String is fStr: if({ frac < 10 }, { '0' . (frac as String) }, { (frac as String) });
		return (whole as String) . '.' . fStr . 's';
	}

	Function of String is fmtMb(Int is kb){
		local Int is mb10: (kb * 10) / 1024;
		local Int is whole: mb10 / 10;
		local Int is frac: mb10 % 10;
		return (whole as String) . '.' . (frac as String) . ' MB';
	}

	Function is showResults(Int is wallMs){
		local String is badge: if({ :failedCount == 0 }, { '✔ ALL PASSED' }, { '✘ ' . (:failedCount as String) . ' FAILED' });
		local CleoColor is c: if({ :failedCount == 0 }, { CleoColor:ansi(code: 254) }, { CleoColor:ansi(code: 255) });
		:rSec:addLine(
			text: (:passedCount as String) . ' passed, ' . (:failedCount as String) . ' failed  (' . (:completedCount as String) . ' suites, ' . (:testsPassed as String) . '/' . (:testsCompleted as String) . ' tests)',
			color: c,
			rightText: badge,
			bold: true
		);
		local Int is cpuMs: :totalCpuUs / 1000;
		:rSec:addLine(
			text: 'Wall time: ' . :fmtSec(ms: wallMs),
			color: CleoColor:ansi(code: 250),
			rightText: 'CPU time: ' . :fmtSec(ms: cpuMs)
		);
		local Int is avgKb: if({ :metricSamples > 0 }, { :totalRssKb / :metricSamples }, { 0 });
		:rSec:addLine(
			text: 'Memory avg: ' . :fmtMb(kb: avgKb),
			color: CleoColor:ansi(code: 250),
			rightText: 'Peak: ' . :fmtMb(kb: :peakRssKb)
		);
	}
}

## The held registry: the compile queue, the ready-to-run queue, and the results.
## Held arrays and maps are mutex-protected — the worker pool reads queues and
## records results from every worker thread safely.
Class is SpecTestRegistry{
	replace [String] is namespace: ['specunit'];

	replace [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'sys', Conditional],
		['base', 'sys', as Parallel()]
	];

	held Array of WorkItem is queue: Array();
	held Array of ReadyRunItem is readyRuns: Array();
	held Array of SuiteResult is results: Array();
	held Map of String to SuiteResult is byName: Map:init();
	held Array of Int is nextIdxRef: Array([0]);
	held Array of Int is inFlightCompilesRef: Array([0]);
	held Array of SpecTestUi is uiHolder: Array();

	held Function is setupUi(Cleo is ui, CleoSection is wSec, Int is wBarSlot, CleoSection is sSec, CleoSection is rSec, CleoSection is pSec, Int is pSlot, Int is total, Int is testsTotal, Int is threads, Map of String to Int is nameToSlot){
		local SpecTestUi is helper: SpecTestUi:init(ui: ui, wSec: wSec, wBarSlot: wBarSlot, sSec: sSec, rSec: rSec, pSec: pSec, pSlot: pSlot, total: total, testsTotal: testsTotal, threads: threads, nameToSlot: nameToSlot);
		SpecTestRegistry:uiHolder:add(item: helper);
	}

	held Function is recordMetrics(Int is cpuUs, Int is rssKb){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onMetrics(cpuUs: cpuUs, rssKb: rssKb);
			});
		});
	}

	held Function is showResults(Int is wallMs){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:showResults(wallMs: wallMs);
			});
		});
	}

	held Function of ReadyRunItem is nextReadyRun(){
		local ReadyRunItem is res: ReadyRunItem:init(item: WorkItem:init(itemPath: '', itemKind: '', itemExpect: []), idx: -1, binPath: '', compileCpuUs: 0, compileRssKb: 0);
		Parallel:syncWith(lock: 17, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:readyRuns:length() > 0; }, then: {
				res: SpecTestRegistry:readyRuns:removeAt(index: 0, default: res);
			});
		});
		return res;
	}

	held Function of Int is nextCompileIndex(){
		local Int is res: -1;
		Parallel:syncWith(lock: 17, action: {
			local Int is idx: SpecTestRegistry:nextIdxRef:get(index: 0, default: 0);
			local Int is tot: SpecTestRegistry:queue:length();
			local Conditional is cond: Conditional:init();
			cond:if(check: { return idx < tot; }, then: {
				SpecTestRegistry:nextIdxRef:set(index: 0, item: idx + 1);
				local Int is inf: SpecTestRegistry:inFlightCompilesRef:get(index: 0, default: 0);
				SpecTestRegistry:inFlightCompilesRef:set(index: 0, item: inf + 1);
				res: idx;
			});
		});
		return res;
	}

	held Function is enqueueReadyRun(ReadyRunItem is rItem){
		Parallel:syncWith(lock: 17, action: {
			SpecTestRegistry:readyRuns:add(item: rItem);
			local Int is inf: SpecTestRegistry:inFlightCompilesRef:get(index: 0, default: 0);
			SpecTestRegistry:inFlightCompilesRef:set(index: 0, item: inf - 1);
		});
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onCompiledReady(itemPath: rItem:item:path);
			});
		});
	}

	held Function is finishCompileOnly(){
		Parallel:syncWith(lock: 17, action: {
			local Int is inf: SpecTestRegistry:inFlightCompilesRef:get(index: 0, default: 0);
			SpecTestRegistry:inFlightCompilesRef:set(index: 0, item: inf - 1);
		});
	}

	held Function of Boolean is hasPendingWork(){
		local Boolean is pending: false;
		Parallel:syncWith(lock: 17, action: {
			local Int is idx: SpecTestRegistry:nextIdxRef:get(index: 0, default: 0);
			local Int is tot: SpecTestRegistry:queue:length();
			local Int is rdy: SpecTestRegistry:readyRuns:length();
			local Int is inf: SpecTestRegistry:inFlightCompilesRef:get(index: 0, default: 0);
			local Conditional is cond: Conditional:init();
			cond:if(check: { return idx < tot || rdy > 0 || inf > 0; }, then: {
				pending: true;
			});
		});
		return pending;
	}

	held Function is markStarted(Int is threadIndex, String is itemPath){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onStarted(threadIndex: threadIndex, itemPath: itemPath);
			});
		});
	}

	held Function is markRunning(Int is threadIndex, String is itemPath){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onRunning(threadIndex: threadIndex, itemPath: itemPath);
			});
		});
	}

	held Function is markWorkerIdle(Int is threadIndex){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onWorkerIdle(threadIndex: threadIndex);
			});
		});
	}

	held Function is addResult(String is name, Boolean is passed, String is note, String is report, Int is expectedTests: 1, Int is tPassed: 0, Int is tFailed: 0){
		Parallel:syncWith(lock: 17, action: {
			local SuiteResult is r: SuiteResult:init(suiteName: name);
			r:passed: passed;
			r:note: note;
			r:report: report;
			SpecTestRegistry:results:add(item: r);
			SpecTestRegistry:byName:set(key: name, value: r);
		});
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onResult(name: name, passed: passed, note: note, expectedTests: expectedTests, tPassed: tPassed, tFailed: tFailed);
			});
		});
	}
}

Class is SpecUnit{
	replace [String] is namespace: ['specunit'];

	replace [[String]] is using: [
		# The plain form grants construction (the report's locals), the
		# as-form grants the bare call surface (the overloads pattern).
		['base', 'cli', Cli],
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', ThrobberShape],
		['base', 'cleo', ThrobberEffect],
		['base', 'cleo', TitlePlacement],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Process()],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Parallel()],
		['base', 'sys', as Dir()],
		['base', 'sys', FileError],
		['base', 'sys', as File()],
		['base', 'sys', as Uri()],
		['base', 'sys', as Time()],
		['base', 'core', SpecError],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task]
	];

	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		line(color256(code: 203, text: 'specunit: unhandled error: ' . error:toString()));
		exit(status: 1);
		return true;
	}

	local String is timeoutTool: '';

	## Probes once at startup for GNU `timeout` or Homebrew `gtimeout`.
	## Returns empty string on Windows or POSIX hosts without either (e.g. vanilla macOS).
	Function of String is detectTimeoutTool(){
		if(check: { Process:osName() == 'windows' }, then: {
			return '';
		});
		if(check: { Process:execute(command: 'sh', args: Array(['-c', 'command -v timeout >/dev/null 2>&1'])) == 0 }, then: {
			return 'timeout';
		});
		if(check: { Process:execute(command: 'sh', args: Array(['-c', 'command -v gtimeout >/dev/null 2>&1'])) == 0 }, then: {
			return 'gtimeout';
		});
		return '';
	}

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():parseOrExit();

		:timeoutTool: :detectTimeoutTool();
		local String is specBin: cli:getString(name: 'spec', default: 'bin/spec');
		if(check: { specBin == '.' || specBin == '' }, then: {
			specBin: 'bin/spec';
		});
		local String is root: cli:getString(name: 'root', default: '.');
		local String is dirsRaw: cli:getString(name: 'tests', default: '');
		local String is srcDirsRaw: cli:getString(name: 'source-dirs', default: '');
		local Boolean is useLlvm: cli:getBool(name: 'llvm');
		local Boolean is prettyMode: cli:getBool(name: 'pretty');
		local String is srcDirFlags: :buildSourceDirFlags(raw: srcDirsRaw);
		if(check: { useLlvm }, then: {
			srcDirFlags: ' --llvm' . srcDirFlags;
		});
		local Int is cores: Process:threadCount();
		local Int is threads: if(check: { cli:has(name: 'threads') }, then: {
			cli:getInt(name: 'threads', default: 1)
		}, else: {
			cores - 2
		});
		if(check: { threads < 1 }, then: {
			threads: 1;
		});
		local Int is timeoutSec: cli:getInt(name: 'timeout', default: 120);
		if(check: { timeoutSec < 5 }, then: {
			timeoutSec: 5;
		});
		local Int is compileTimeoutSec: cli:getInt(name: 'compile-timeout', default: 300);
		if(check: { compileTimeoutSec < 10 }, then: {
			compileTimeoutSec: 10;
		});
		:enqueueDirs(dirsRaw: dirsRaw, root: root);
		:sortQueueByPriority();
		local Int is total: SpecTestRegistry:queue:length();
		if(check: { total == 0 }, then: {
			line(color256(code: 203, text: 'specunit: no test suites found in: ' . dirsRaw));
			exit(status: 1);
		});
		local Int is testsTotal: 0;
		SpecTestRegistry:queue:each(action: local Function(WorkItem is wi){
			testsTotal: testsTotal + wi:expectedTests;
		});
		if(check: { threads > total }, then: {
			threads: total;
		});

		# Grayscale Cleo UI at 100% terminal width (direct line-by-line by default; interactive with --pretty)
		local Cleo is ui: Cleo:init(
			title: ' specunit ',
			titleColor: CleoColor:ansi(code: 255),
			titleBgColor: CleoColor:ansi(code: 236),
			width: CleoWidth:percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 237),
			directOutput: !prettyMode
		);
		local CleoSection is sSec: ui:addSection(
			title: ' Test Suites ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		sSec:groupResolvedFirst: true;
		local Map of String to Int is nameToSlot: Map:init();

		local CleoSection is wSec: ui:addSection(
			title: ' Workers (' . (threads as String) . '/' . (cores as String) . ' cores) ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		local Int is wBarSlot: -1;
		if(check: { prettyMode }, then: {
			wBarSlot: wSec:addLine(text: '', color: CleoColor:ansi(code: 252), rightText: '0/' . (threads as String) . ' active');
		});

		local CleoSection is rSec: ui:addSection(
			title: ' Results ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);

		local CleoSection is pSec: ui:addSection(
			title: ' Suite Progress ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		local Int is pSlot: -1;
		if(check: { prettyMode }, then: {
			pSlot: pSec:addProgressArea(
				text: '0/' . (total as String) . ' suites · 0/' . (testsTotal as String) . ' tests (' . specBin . ')',
				stage1Color: CleoColor:ansi(code: 252),
				stage2Color: CleoColor:ansi(code: 243),
				trackColor: CleoColor:ansi(code: 236),
				showTwoStagePercent: true
			);
		});

		SpecTestRegistry:setupUi(ui: ui, wSec: wSec, wBarSlot: wBarSlot, sSec: sSec, rSec: rSec, pSec: pSec, pSlot: pSlot, total: total, testsTotal: testsTotal, threads: threads, nameToSlot: nameToSlot);
		local Int is startMs: Time:monotonicMs();
		ThreadScope:open(body: local Function(ThreadScope is scope){
			ui:start(scope: scope);

			local Array of Task is workers: Array();
			times(count: threads, worker: local Function(Int is ti){
				local Task is wt: scope:spawn(task: local Function(){
					local Boolean is keepGoing: true;
					while({ keepGoing }, {
						# Running takes precedence over compiling whenever a compiled test is ready.
						local ReadyRunItem is rItem: SpecTestRegistry:nextReadyRun();
						if(check: { rItem:idx >= 0 }, then: {
							SpecTestRegistry:markRunning(threadIndex: ti, itemPath: rItem:item:path);
							:executeReadyItem(rItem: rItem, specBin: specBin, root: root, timeoutSec: timeoutSec);
							SpecTestRegistry:markWorkerIdle(threadIndex: ti);
						}, else: {
							local Int is idx: SpecTestRegistry:nextCompileIndex();
							if(check: { idx >= 0 }, then: {
								local WorkItem is item: SpecTestRegistry:queue:get(index: idx);
								SpecTestRegistry:markStarted(threadIndex: ti, itemPath: item:path);
								:compileItem(item: item, idx: idx, specBin: specBin, root: root, srcDirFlags: srcDirFlags, timeoutSec: compileTimeoutSec);
								SpecTestRegistry:markWorkerIdle(threadIndex: ti);
							}, else: {
								if(check: { SpecTestRegistry:hasPendingWork() }, then: {
									Process:sleep(milliseconds: 10);
								}, else: {
									keepGoing: false;
								});
							});
						});
					});
				});
				workers:add(item: wt);
			});
			scope:awaitAll(group: workers);

			local Int is wallMs: Time:monotonicMs() - startMs;
			SpecTestRegistry:showResults(wallMs: wallMs);
			ui:finish();
		});
		:report();
	}

	Function of String is buildSourceDirFlags(String is raw){
		local String is out: '';
		if(check: { raw != '' }, then: {
			raw:split(delimiter: ','):each(action: local Function(String is seg){
				local String is sd: seg:trim();
				if(check: { sd != '' }, then: {
					out: out . ' -s "' . sd . '"';
				});
			});
		});
		local String is exeDir: Dir:exeDir();
		if(check: { exeDir != '' }, then: {
			local String is bundledUnit: exeDir . '/../utilities/specunit';
			if(check: { fileExists(path: bundledUnit) }, then: {
				out: out . ' -s "' . bundledUnit . '"';
			});
			local String is bundledSpec: exeDir . '/../spec';
			if(check: { fileExists(path: bundledSpec) }, then: {
				out: out . ' -s "' . bundledSpec . '"';
			});
		});
		return out;
	}

	Function of String is resolveItemPath(String is root, String is relOrAbs){
		if(check: { relOrAbs:startsWith(prefix: '/') || (relOrAbs:length() >= 2 && relOrAbs:substring(start: 1, end: 2) == ':') }, then: {
			return relOrAbs;
		});
		return root . '/' . relOrAbs;
	}

	## Enqueues every candidate under each comma/newline-separated
	## [dirsRaw] entry (relative to [root]), via a recursive walk.
	Function is enqueueDirs(String is dirsRaw, String is root){
		dirsRaw:split(delimiter: "\n"):each(action: local Function(String is segRaw){
			local String is seg: if(check: { segRaw:endsWith(suffix: "\r") }, then: { segRaw:substring(start: 0, end: segRaw:length() - 1); }, else: { segRaw; });
			seg:split(delimiter: ','):each(action: local Function(String is dirRaw){
				local String is dir: if(check: { dirRaw:endsWith(suffix: "\r") }, then: { dirRaw:substring(start: 0, end: dirRaw:length() - 1); }, else: { dirRaw; });
				if(check: { dir != '' }, then: {
					local String is absDir: :resolveItemPath(root: root, relOrAbs: dir);
					if(check: { !fileExists(path: absDir) }, then: {
						line(color256(code: 203, text: 'specunit: test directory not found: ' . dir));
						exit(status: 1);
					});
					:enqueueTree(absDir: absDir, relDir: dir . '/');
				});
			});
		});
	}

	## Walks [absDir] recursively (dot directories skipped). A directory
	## is any entry whose dirList is non-empty (spec_dir_list on a file
	## returns empty); a candidate file is a non-empty .spec file, whose
	## `#!` banner classifies it.
	Function is enqueueTree(String is absDir, String is relDir){
		Dir:dirList(path: absDir):each(action: local Function(String is name){
			if(check: { name:startsWith(prefix: '.') }, then: {
				return;
			});
			local String is childAbs: absDir . '/' . name;
			local String is childRel: relDir . name;
			local Array of String is children: Dir:dirList(path: childAbs);
			if(check: { children:length() > 0 }, then: {
				:enqueueTree(absDir: childAbs, relDir: childRel . '/');
			}, else: {
				if(check: { name:endsWith(suffix: '.spec') && fileRead(path: childAbs, default: '') != '' }, then: {
					:enqueueFile(relPath: childRel);
				});
			});
		});
	}

	## Counts test methods declared in a suite source file (`Function is test...(`)
	## so the progress bar has a fine-grained test total before suites finish.
	Function of Int is estimateTestCount(String is content){
		local Int is count: 0;
		content:split(delimiter: "\n"):each(action: local Function(String is segRaw){
			local String is t: segRaw:trim();
			if(check: { t:startsWith(prefix: 'Function is test') && t:contains(needle: '(') }, then: {
				count: count + 1;
			});
		});
		return if(check: { count > 0 }, then: { count; }, else: { 1; });
	}

	## Stable insertion sort of `SpecTestRegistry:queue` by `priorityPosition`
	## ascending (lower numbers such as -100 are queued first).
	Function is sortQueueByPriority(){
		local Int is n: SpecTestRegistry:queue:length();
		range(start: 1, end: n, worker: local Function(Int is i){
			local WorkItem is keyItem: SpecTestRegistry:queue:get(index: i);
			local Int is keyPrio: keyItem:priorityPosition;
			local Int is j: i - 1;
			while({ j >= 0 && SpecTestRegistry:queue:get(index: j):priorityPosition > keyPrio }, {
				SpecTestRegistry:queue:set(index: j + 1, item: SpecTestRegistry:queue:get(index: j));
				j: j - 1;
			});
			SpecTestRegistry:queue:set(index: j + 1, item: keyItem);
		});
	}

	## Classifies one candidate: every suite MUST extend the SpecUnitTest
	## base class and produce a SpecUnit report table. Candidates that do not
	## extend the base test class are not runnable as suites.
	## A `#! specunit: negative-suite` file splits into parallel `#! case:` items.
	Function is enqueueFile(String is relPath){
		local String is content: fileRead(path: relPath, default: '');
		local String is kind: '';
		local Int is prio: 0;
		local [String] is expect: [];
		content:split(delimiter: "\n"):each(action: local Function(String is segRaw){
			local String is seg: if(check: { segRaw:endsWith(suffix: "\r") }, then: { segRaw:substring(start: 0, end: segRaw:length() - 1); }, else: { segRaw; });
			if(check: { seg:startsWith(prefix: '#! specunit: ') }, then: {
				kind: seg:substring(start: 13, end: seg:length()):trim();
			}, else: {
				if(check: { seg:startsWith(prefix: '#! priorityPosition: ') }, then: {
					prio: seg:substring(start: 21, end: seg:length()):trim():parseInt(default: 0);
				}, else: {
					if(check: { seg:startsWith(prefix: '#! expect: ') }, then: {
						expect:push(item: seg:substring(start: 11, end: seg:length()));
					});
				});
			});
		});
		if(check: { kind == 'negative-suite' }, then: {
			:enqueueNegativeSuite(relPath: relPath, content: content, prio: prio);
			return;
		});
		if(check: { (kind == '' || kind == 'suite') && content:contains(needle: 'SpecUnitTest') }, then: {
			kind: 'suite';
		}, else: {
			if(check: { kind == 'suite' }, then: {
				kind: '';
			});
		});
		if(check: { kind == '' || kind == 'helper' }, then: {
			return;
		});
		local Int is estTests: if(check: { kind == 'suite' }, then: { :estimateTestCount(content: content); }, else: { 1; });
		SpecTestRegistry:queue:add(item: WorkItem:init(itemPath: relPath, itemKind: kind, itemExpect: expect, source: '', expectedTests: estTests, priorityPosition: prio));
	}

	## Splits a `#! specunit: negative-suite` file on `#! case: <name>` headers
	## into independent parallel `negative-case` work items.
	Function is enqueueNegativeSuite(String is relPath, String is content, Int is prio: 0){
		local String is curCase: '';
		local [String] is curExpect: [];
		local String is curSrc: '';
		content:split(delimiter: "\n"):each(action: local Function(String is segRaw){
			local String is seg: if(check: { segRaw:endsWith(suffix: "\r") }, then: { segRaw:substring(start: 0, end: segRaw:length() - 1); }, else: { segRaw; });
			if(check: { seg:startsWith(prefix: '#! case: ') }, then: {
				if(check: { curCase != '' }, then: {
					SpecTestRegistry:queue:add(item: WorkItem:init(itemPath: relPath . '#' . curCase, itemKind: 'negative-case', itemExpect: curExpect, source: curSrc, expectedTests: 1, priorityPosition: prio));
				});
				curCase: seg:substring(start: 9, end: seg:length()):trim();
				curExpect: [];
				curSrc: '';
			}, else: {
				if(check: { curCase != '' }, then: {
					if(check: { seg:startsWith(prefix: '#! expect: ') }, then: {
						curExpect:push(item: seg:substring(start: 11, end: seg:length()));
					}, else: {
						curSrc: curSrc . seg . "\n";
					});
				});
			});
		});
		if(check: { curCase != '' }, then: {
			SpecTestRegistry:queue:add(item: WorkItem:init(itemPath: relPath . '#' . curCase, itemKind: 'negative-case', itemExpect: curExpect, source: curSrc, expectedTests: 1, priorityPosition: prio));
		});
	}

	## Wraps a shell command with `<timeoutTool> --kill-after=5 <timeoutSec>s`
	## when GNU `timeout` or `gtimeout` is available so hung compiles or hung
	## test binaries are cleanly terminated.
	Function of String is withTimeout(String is cmd, Int is timeoutSec){
		if(check: { :timeoutTool == '' }, then: {
			return cmd;
		});
		return :timeoutTool . ' --kill-after=5 ' . (timeoutSec as String) . 's ' . cmd;
	}

	## Parses `[PASS]` and `[FAIL]` counts from SpecUnit suite output.
	Function of [Int] is countReportTests(String is out){
		local Int is p: 0;
		local Int is f: 0;
		out:split(delimiter: "\n"):each(action: local Function(String is ln){
			if(check: { ln:startsWith(prefix: '[PASS] ') }, then: {
				p: p + 1;
			}, else: {
				if(check: { ln:startsWith(prefix: '[FAIL] ') }, then: {
					f: f + 1;
				});
			});
		});
		return [p, f];
	}

	## Compiles one work item. Negative items finish right here; runnable
	## items (`suite`, `run-fail`) enqueue their compiled binary onto
	## `SpecTestRegistry:readyRuns` so any free worker runs it with priority.
	Function is compileItem(WorkItem is item, Int is idx, String is specBin, String is root, String is srcDirFlags, Int is timeoutSec){
		if(check: { item:kind == 'negative' || item:kind == 'negative-case' }, then: {
			:runNegative(item: item, idx: idx, specBin: specBin, root: root, srcDirFlags: srcDirFlags, timeoutSec: timeoutSec);
			SpecTestRegistry:finishCompileOnly();
			return;
		});
		local String is src: :resolveItemPath(root: root, relOrAbs: item:path);
		local String is exeSuffix: if(check: { Process:osName() == 'windows' }, then: { '.exe' }, else: { '.bin' });
		local String is bin: :workPath(suffix: exeSuffix, idx: idx, stem: :fileStem(path: item:path));
		local String is compileOut: bin . '.compile';
		local String is compileCmd: :withTimeout(cmd: '"' . specBin . '" --quiet --threads 1' . srcDirFlags . ' -i "' . src . '" -o "' . bin . '"', timeoutSec: timeoutSec);
		local Array of String is cArgs: Array(['-c', 'cd "' . root . '" && ' . compileCmd . ' > "' . compileOut . '" 2>&1']);
		local Map of String to String is cRes: Process:measure(command: 'sh', args: cArgs);
		local Int is cStatus: cRes:getInt(key: 'exit', default: -1);
		local Int is cCpu: cRes:getInt(key: 'cpu_us', default: 0);
		local Int is cRss: cRes:getInt(key: 'rss_kb', default: 0);
		if(check: { cStatus != 0 }, then: {
			SpecTestRegistry:recordMetrics(cpuUs: cCpu, rssKb: cRss);
			local String is diag: fileRead(path: compileOut, default: '');
			local String is note: if(check: { cStatus == 124 || cStatus == 137 }, then: { 'compilation timed out after ' . (timeoutSec as String) . 's (killed)'; }, else: { 'compilation failed: ' . :firstLine(text: diag); });
			SpecTestRegistry:addResult(name: item:path, passed: false, note: note, report: diag, expectedTests: item:expectedTests, tPassed: 0, tFailed: item:expectedTests);
			fileRemove(path: compileOut);
			if(check: { File:fileExists(path: bin) }, then: {
				fileRemove(path: bin);
			});
			SpecTestRegistry:finishCompileOnly();
			return;
		});
		fileRemove(path: compileOut);
		SpecTestRegistry:enqueueReadyRun(rItem: ReadyRunItem:init(item: item, idx: idx, binPath: bin, compileCpuUs: cCpu, compileRssKb: cRss));
	}

	## Executes a previously compiled `suite` or `run-fail` binary under timeout,
	## records metrics + test counts, and deletes the compiled binary.
	Function is executeReadyItem(ReadyRunItem is rItem, String is specBin, String is root, Int is timeoutSec){
		local WorkItem is item: rItem:item;
		local String is bin: rItem:binPath;
		local String is runOut: bin . '.out';
		local String is runCmd: :withTimeout(cmd: '"' . bin . '"', timeoutSec: timeoutSec);
		local Array of String is rArgs: Array(['-c', 'cd "' . root . '" && export SPEC_BIN="' . specBin . '" && ' . runCmd . ' < /dev/null > "' . runOut . '" 2>&1']);
		local Map of String to String is rRes: Process:measure(command: 'sh', args: rArgs);
		local Int is rStatus: rRes:getInt(key: 'exit', default: -1);
		local Int is totalCpu: rItem:compileCpuUs + rRes:getInt(key: 'cpu_us', default: 0);
		local Int is rRss: rRes:getInt(key: 'rss_kb', default: 0);
		local Int is maxRss: if(check: { rRss > rItem:compileRssKb }, then: { rRss; }, else: { rItem:compileRssKb; });
		SpecTestRegistry:recordMetrics(cpuUs: totalCpu, rssKb: maxRss);
		local String is out: fileRead(path: runOut, default: '');
		local Boolean is timedOut: rStatus == 124 || rStatus == 137;
		local Boolean is passed: true;
		local String is note: '';
		local Int is tPassed: 0;
		local Int is tFailed: 0;
		if(check: { item:kind == 'run-fail' }, then: {
			if(check: { timedOut }, then: {
				passed: false;
				note: 'timed out after ' . (timeoutSec as String) . 's (killed)';
			}, else: {
				if(check: { rStatus == 0 }, then: {
					passed: false;
					note: 'exited 0 but must fail';
				}, else: {
					if(check: { !:allPresent(text: out, expect: item:expect) }, then: {
						passed: false;
						note: 'missing expected run diagnostic';
					});
				});
			});
			tPassed: if(check: { passed }, then: { 1; }, else: { 0; });
			tFailed: if(check: { passed }, then: { 0; }, else: { 1; });
		}, else: {
			passed: rStatus == 0;
			local [Int] is counts: :countReportTests(out: out);
			tPassed: counts:get(index: 0);
			tFailed: counts:get(index: 1);
			if(check: { timedOut }, then: {
				passed: false;
				note: 'timed out after ' . (timeoutSec as String) . 's (killed)';
			}, else: {
				if(check: { passed && !out:contains(needle: 'SpecUnit') }, then: {
					passed: false;
					note: 'exited 0 but produced no SpecUnit report table';
				});
				if(check: { !passed && note == '' }, then: {
					note: 'exit ' . (rStatus as String) . ' — ' . :firstLine(text: out);
				});
			});
		});
		SpecTestRegistry:addResult(name: item:path, passed: passed, note: note, report: out, expectedTests: item:expectedTests, tPassed: tPassed, tFailed: tFailed);
		fileRemove(path: bin);
		fileRemove(path: runOut);
	}

	## Compile-must-fail: the produced diagnostics must contain every
	## `#! expect:` string from the file's or case's banner.
	Function is runNegative(WorkItem is item, Int is idx, String is specBin, String is root, String is srcDirFlags, Int is timeoutSec){
		local String is src: '';
		local Boolean is tempSrc: false;
		if(check: { item:kind == 'negative-case' }, then: {
			src: :workPath(suffix: '.spec', idx: idx, stem: 'negcase');
			fileWrite(path: src, content: item:inlineSource, onSuccess: local Function(Int is _n){}, onError: local Function(SpecError of FileError is _e){});
			tempSrc: true;
		}, else: {
			src: :resolveItemPath(root: root, relOrAbs: item:path);
		});
		local String is compileOut: :workPath(suffix: '.compile', idx: idx, stem: :fileStem(path: item:path));
		local String is compileCmd: :withTimeout(cmd: '"' . specBin . '" --quiet --threads 1' . srcDirFlags . ' -i "' . src . '" -o "/dev/null"', timeoutSec: timeoutSec);
		local Array of String is cArgs: Array(['-c', 'cd "' . root . '" && ' . compileCmd . ' > "' . compileOut . '" 2>&1']);
		local Map of String to String is cRes: Process:measure(command: 'sh', args: cArgs);
		local Int is cStatus: cRes:getInt(key: 'exit', default: -1);
		SpecTestRegistry:recordMetrics(cpuUs: cRes:getInt(key: 'cpu_us', default: 0), rssKb: cRes:getInt(key: 'rss_kb', default: 0));
		local String is cText: fileRead(path: compileOut, default: '');
		local Boolean is passed: true;
		local String is note: '';
		if(check: { cStatus == 124 || cStatus == 137 }, then: {
			passed: false;
			note: 'compilation timed out after ' . (timeoutSec as String) . 's (killed)';
		}, else: {
			if(check: { cStatus == 0 }, then: {
				passed: false;
				note: 'compilation succeeded but must fail';
			}, else: {
				if(check: { !:allPresent(text: cText, expect: item:expect) }, then: {
					passed: false;
					note: 'missing expected diagnostic';
				});
			});
		});
		local Int is tp: if(check: { passed }, then: { 1; }, else: { 0; });
		local Int is tf: if(check: { passed }, then: { 0; }, else: { 1; });
		SpecTestRegistry:addResult(name: item:path, passed: passed, note: note, report: cText, expectedTests: 1, tPassed: tp, tFailed: tf);
		fileRemove(path: compileOut);
		if(check: { tempSrc }, then: {
			fileRemove(path: src);
		});
	}

	## The flat work path for one item's artifacts: pid + queue
	## index + stem keeps concurrent compiles collision-free.
	Function of String is workPath(String is suffix, Int is idx, String is stem){
		return Uri:systemTempDir() . '/specrun_' . (Process:getPid() as String) . '_' . (idx as String) . '_' . stem . suffix;
	}

	## The report: failed items' evidence printed (if any), then the CI exit.
	Function is report(){
		local Int is passed: 0;
		local Int is failed: 0;
		SpecTestRegistry:results:each(action: local Function(SuiteResult is r){
			if(check: { r:passed }, then: {
				passed: passed + 1;
			}, else: {
				failed: failed + 1;
			});
		});
		if(check: { failed > 0 }, then: {
			line('');
			line(bold() . color256(code: 203, text: '== Failures =='));
			SpecTestRegistry:results:each(action: local Function(SuiteResult is r){
				if(check: { !r:passed }, then: {
					line(color256(code: 203, text: '[FAIL] ' . r:name . '  ' . r:note));
					if(check: { r:report != '' }, then: {
						line(color256(code: 203, text: r:report));
					});
				});
			});
		});
		local Int is exitCode: if(check: { failed > 0 }, then: { 1 }, else: { 0 });
		exit(status: exitCode);
	}

	## Whether [text] contains every expected message.
	Function of Boolean is allPresent(String is text, [String] is expect){
		local Boolean is all: true;
		each(list: expect, action: local Function(String is msg){
			if(check: { !text:contains(needle: msg) }, then: {
				all: false;
			});
		});
		return all;
	}

	## The first line of [text] — the compile/run diagnostic headline.
	Function of String is firstLine(String is text){
		if(check: { text == '' }, then: {
			return '';
		});
		local Int is nl: text:indexOf(search: "\n", default: text:length());
		return text:substring(start: 0, end: nl);
	}

	## The file's basename without the .spec extension.
	Function of String is fileStem(String is path){
		local Array of String is segs: path:split(delimiter: '/');
		local String is base: segs:get(index: segs:length() - 1);
		local Array of String is parts: base:split(delimiter: '.');
		return parts:get(index: 0);
	}
}
