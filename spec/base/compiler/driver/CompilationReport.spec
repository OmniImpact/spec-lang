#! Package base:compiler:driver
#! The friendly compilation output: stage progress and the final summary.
##
## The Driver gathers measurements and hands them here; all user-facing
## formatting lives in this class so the report's shape changes in one
## place (including the Phase-G7 json emitter later).

Class is CompilationReport{
	namespace: ['base', 'compiler', 'driver'];

	replace Array of Array of String is using: [
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	## True when stage lines and the summary are suppressed.
	local Boolean is quiet: false;
	local Cleo is ui: Cleo:toolUi(title: ' spec ', directOutput: true);
	local CleoSection is stageSec: CleoSection:init();
	local Boolean is uiStarted: false;

	replace Function is init(Boolean is quiet){
		:quiet: quiet;
		:ui: Cleo:toolUi(title: ' spec ', directOutput: true);
		:uiStarted: false;
	}

	local Function is ensureStarted(){
		if({ !:uiStarted }, {
			:uiStarted: true;
			:stageSec: :ui:addToolSection(title: ' Stages ');
			:ui:startDirect();
		});
	}

	## One stage-progress line, e.g. `  [1/4] loading packages · 6 files`.
	##
	## @param n: One-based stage number.
	## @param total: Total stage count.
	## @param label: Stage description.
	Function is stage(Int is n, Int is total, String is label){
		if({ :quiet }, {
			return;
		});
		:ensureStarted();
		local Int is pct: if({ total > 0 }, { (n * 100) / total }, { 100 });
		:stageSec:addLine(
			text: '[' . (n as String) . '/' . (total as String) . '] ' . label,
			color: CleoColor:ansi(code: 250),
			rightText: (pct as String) . '%'
		);
	}

	## One-line progress note inside a stage (no numbering).
	Function is note(String is label){
		if({ :quiet }, {
			return;
		});
		:ensureStarted();
		:stageSec:addLine(text: label, color: CleoColor:ansi(code: 245));
	}

	## Prints the end-of-run summary: paths, counts, time breakdown.
	##
	## @param inputPath: Compiled source path.
	## @param outputPath: Binary or emit-c target path.
	## @param classCount: Classes across the program.
	## @param methodCount: Methods across the program.
	## @param specLines: Source line count.
	## @param cLines: Generated C line count.
	## @param totalMs: Whole-run wall time.
	## @param loadMs/checkMs/genMs/ccMs: Stage timings (ccMs -1 when no binary).
	## @param peakKb: Process peak memory in KB.
	## @param avgMemKb: Process average memory in KB.
	## @param avgCpuPct: Process average CPU usage percentage (can exceed 100%).
	## @param peakCpuPct: Process peak interval CPU usage percentage.
	## @param binKb: Binary size in KB (-1 when no binary was produced).
	Function is summary(String is inputPath, String is outputPath, Int is classCount, Int is methodCount, Int is specLines, Int is cLines, Int is totalMs, Int is loadMs, Int is checkMs, Int is genMs, Int is ccMs, Int is peakKb, Int is avgMemKb, Int is avgCpuPct, Int is peakCpuPct, Int is binKb){
		if({ :quiet }, {
			return;
		});
		:ensureStarted();
		local CleoSection is bSec: :ui:addToolSection(title: ' Build ');
		bSec:addLine(
			text: inputPath . ' -> ' . outputPath,
			color: CleoColor:ansi(code: 252),
			rightText: '✔ COMPILED'
		);
		bSec:addLine(
			text: (classCount as String) . ' classes · ' . (methodCount as String) . ' methods · ' . (specLines as String) . ' lines of spec -> ' . (cLines as String) . ' lines of LLVM IR',
			color: CleoColor:ansi(code: 250)
		);
		local CleoSection is mSec: :ui:addToolSection(title: ' Metrics ');
		local String is times: 'time ' . (totalMs as String) . 'ms  (load ' . (loadMs as String) . ' · check ' . (checkMs as String) . ' · gen ' . (genMs as String);
		if({ ccMs >= 0 }, {
			times: times . ' · cc ' . (ccMs as String);
		});
		times: times . ')';
		local String is memLine: 'memory ' . ((avgMemKb / 1024) as String) . ' MB avg · ' . ((peakKb / 1024) as String) . ' MB peak';
		if({ binKb >= 0 }, {
			memLine: memLine . ' · binary ' . ((binKb / 1024) as String) . ' KB';
		});
		local String is cpuLine: 'cpu ' . (avgCpuPct as String) . '% avg · ' . (peakCpuPct as String) . '% peak';
		mSec:addLine(text: times, color: CleoColor:ansi(code: 250));
		mSec:addLine(text: memLine, color: CleoColor:ansi(code: 250), rightText: cpuLine);
		:ui:finish();
	}
}
