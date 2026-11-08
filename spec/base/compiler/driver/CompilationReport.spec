#! Package base:compiler:driver
#! The friendly compilation output: stage progress and the final summary.
##
## The Driver gathers measurements and hands them here; all user-facing
## formatting lives in this class so the report's shape changes in one
## place (including the Phase-G7 json emitter later).

Class is CompilationReport{
	namespace: ['base', 'compiler', 'driver'];

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	## True when stage lines and the summary are suppressed.
	local Boolean is quiet: false;

	replace Function is init(Boolean is quiet){
		self:quiet: quiet;
	}

	## One stage-progress line, e.g. `  [1/4] loading packages · 6 files`.
	##
	## @param n: One-based stage number.
	## @param total: Total stage count.
	## @param label: Stage description.
	Function is stage(Int is n, Int is total, String is label){
		Conditional:branch(check: { self:quiet }, then: {
			return;
		});
		Output:line('  [' . (n as String) . '/' . (total as String) . '] ' . label);
	}

	## One-line progress note inside a stage (no numbering).
	Function is note(String is label){
		Conditional:branch(check: { self:quiet }, then: {
			return;
		});
		Output:line('  ' . label);
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
	## @param binKb: Binary size in KB (-1 when no binary was produced).
	Function is summary(String is inputPath, String is outputPath, Int is classCount, Int is methodCount, Int is specLines, Int is cLines, Int is totalMs, Int is loadMs, Int is checkMs, Int is genMs, Int is ccMs, Int is peakKb, Int is binKb){
		Conditional:branch(check: { self:quiet }, then: {
			return;
		});
		Output:line('');
		Output:line('  ' . inputPath . ' -> ' . outputPath);
		Output:line('  ' . (classCount as String) . ' classes · ' . (methodCount as String) . ' methods · ' . (specLines as String) . ' lines of spec -> ' . (cLines as String) . ' lines of C');
		local String is times: '  time ' . (totalMs as String) . 'ms  (load ' . (loadMs as String) . ' · check ' . (checkMs as String) . ' · gen ' . (genMs as String);
		Conditional:branch(check: { ccMs >= 0 }, then: {
			times: times . ' · cc ' . (ccMs as String);
		});
		times: times . ')';
		Output:line(times);
		local String is last: '  peak memory ' . ((peakKb / 1024) as String) . ' MB';
		Conditional:branch(check: { binKb >= 0 }, then: {
			last: last . ' · binary ' . ((binKb / 1024) as String) . ' KB';
		});
		Output:line(last);
	}
}
