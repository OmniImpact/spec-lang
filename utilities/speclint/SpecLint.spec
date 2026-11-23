#! Package speclint
#! The speclint entry program — the Spec code-standards linter, split out
#! of the compiler (the specunit treatment). The binary imports the
#! compiler's front-end by namespace (lexer, parser, ast) plus the
#! speclint rules, so linting is in-process: no compiler subprocess, no
#! diagnostic scraping. Editing anything in utilities/speclint/ rebuilds
#! only this binary — the bootstrap seed never reconverges for a lint
#! change. See KNOWLEDGE-SPECDEV.md §4b.
#!
#! CLI:
#!   speclint -i <file.spec>          lint one file (the old `spec --lint`)
#!   speclint -t <dir> [-t <dir>...]  lint every .spec under the trees
#!                                    (recursive, dot entries skipped;
#!                                    syntax-broken files are tallied and
#!                                    the walk continues)
#!   speclint -a -i <file.spec>       the Phase 0.5 instance-model audit
#!                                    (full loader; informational, always 0)
#! -i takes precedence over -t when both are given.
#!
#! Exit contract: 0 clean; 1 findings or lex/parse errors; 2 usage.

Class is SpecLint{
	namespace: ['speclint'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', Error],
		['base', 'compiler', 'loader', Loader],
		['speclint', Linter],
		['speclint', LintIssue],
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', TitlePlacement],
		['base', 'sys', as Output()],
		['base', 'sys', as Stderr()],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['base', 'sys', as File()],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Time()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		local Int is startMs: Time:monotonicMs();
		local String is inputPath: args:getString(key: 'i', default: '');
		if({ inputPath == '' }, {
			inputPath: args:getString(key: 'input', default: '');
		});
		local String is dirsRaw: args:getString(key: 't', default: '');
		local String is pos0: args:getString(key: '0', default: '');
		if({ inputPath == '' && dirsRaw == '' && pos0 != '' }, {
			if({ Dir:dirList(path: pos0):length() > 0 }, {
				dirsRaw: pos0;
			}, {
				inputPath: pos0;
			});
		});
		local Boolean is auditMode: args:has(key: 'a');
		if({ !auditMode }, {
			auditMode: args:has(key: 'audit');
		});

		# Audit: one file, the full loader (import resolution like the
		# compiler's), informational — the old always-0 contract holds.
		if({ auditMode }, {
			if({ inputPath == '' }, {
				Stderr:line('Usage: speclint -a -i <file.spec>');
				Process:exit(status: 2);
			});
			if({ !fileExists(path: inputPath) }, {
				Stderr:line('Error: Source file not found: ' . inputPath);
				Process:exit(status: 1);
			});
			:auditFile(path: inputPath);
			Process:exit(status: 0);
		});

		# Single file: the old `spec --lint <file>` shape, with Cleo output
		# and the standalone exit contract (1 on warnings).
		if({ inputPath != '' }, {
			if({ !fileExists(path: inputPath) }, {
				Stderr:line('Error: Source file not found: ' . inputPath);
				Process:exit(status: 1);
			});
			local Cleo is ui: Cleo:toolUi(title: ' speclint ');
			local LintTally is tally: LintTally:init();
			:lintOne(path: inputPath, strict: true, tally: tally, ui: ui);
			local CleoSection is sumSec: ui:addToolSection(title: ' Lint Summary ');
			:populateSummary(sumSec: sumSec, tally: tally, startMs: startMs);
			ui:render();
			# Notices are informational (optional-parameter advisories on
			# legitimate call sites) — only warnings gate the exit.
			if({ tally:warnings > 0 }, {
				Process:exit(status: 1);
			});
			Process:exit(status: 0);
		});

		# Tree walk: every .spec under the -t roots (repeatable,
		# comma/newline separated — the argv parser accumulates repeats).
		local Array of String is files: Array();
		local Int is roots: 0;
		dirsRaw:split(delimiter: "\n"):each(action: local Function(String is seg){
			seg:split(delimiter: ','):each(action: local Function(String is dir){
				if({ dir != '' }, {
					roots: roots + 1;
					:collectTreeFiles(absDir: dir, files: files);
				});
			});
		});
		if({ roots == 0 }, {
			Output:line('SpecLint (Pure Spec)');
			Stderr:line('Usage: speclint <file_or_dir> | speclint -i <file.spec> | speclint -t <dir> [-t <dir> ...] | speclint -a -i <file.spec>');
			Process:exit(status: 2);
		});
		local Cleo is ui: Cleo:toolUi(title: ' speclint ');
		local LintTally is tally: LintTally:init();
		local Int is total: files:length();
		local Int is idx: 0;
		files:each(action: local Function(String is fpath){
			if({ total > 1 }, {
				Output:consOut(text: "\r\u001b[2K  " . (idx as String) . '/' . (total as String) . ' files · ' . fpath);
			});
			:lintOne(path: fpath, strict: false, tally: tally, ui: ui);
			idx: idx + 1;
		});
		if({ total > 1 }, {
			Output:consOut(text: "\r\u001b[2K");
		});
		local CleoSection is sumSec: ui:addToolSection(title: ' Lint Summary ');
		:populateSummary(sumSec: sumSec, tally: tally, startMs: startMs);
		if({ total > 1 }, {
			local CleoSection is pSec: ui:addToolSection(title: ' Progress ');
			local Int is pSlot: pSec:addProgressArea(
				text: (total as String) . '/' . (total as String) . ' files',
				stage1Color: CleoColor:ansi(code: 255),
				stage2Color: CleoColor:ansi(code: 243),
				trackColor: CleoColor:ansi(code: 236),
				showTwoStagePercent: true
			);
			pSec:updateProgress(
				index: pSlot,
				text: (total as String) . '/' . (total as String) . ' files',
				stage1: 1.0,
				stage2: 1.0
			);
		});
		ui:render();
		local Boolean is clean: (tally:warnings + tally:broken) == 0;
		if({ !clean }, {
			Process:exit(status: 1);
		});
		Process:exit(status: 0);
	}

	Function is populateSummary(CleoSection is sumSec, LintTally is tally, Int is startMs){
		local String is tail: '';
		if({ tally:broken > 0 }, {
			tail: ' · ' . (tally:broken as String) . ' syntax-broken';
		});
		local Boolean is clean: (tally:warnings + tally:broken) == 0;
		local String is summaryText: (tally:files as String) . ' file(s) linted · ' . (tally:warnings as String) . ' warning(s) · ' . (tally:notices as String) . ' notice(s)' . tail;
		local String is badge: if({ clean }, { '✔ CLEAN' }, { '✖ ISSUES FOUND' });
		local CleoColor is badgeColor: if({ clean }, { CleoColor:ansi(code: 252) }, { CleoColor:ansi(code: 203) });
		sumSec:addLine(text: summaryText, color: badgeColor, rightText: badge);
		local Int is elapsedMs: Time:monotonicMs() - startMs;
		local Int is memMb: Process:peakMemoryKb() / 1024;
		sumSec:addLine(text: 'Elapsed: ' . (elapsedMs as String) . 'ms', color: CleoColor:ansi(code: 245), rightText: 'Peak memory: ' . (memMb as String) . ' MB');
	}

	## Lints one file: lex, parse, run the standards walk, and record
	## findings into a per-file section in [ui].
	##
	## @param path: The file to lint.
	## @param strict: Abort on syntax errors instead of tallying them.
	## @param tally: The run tally to update.
	## @param ui: The Cleo UI to append file sections to.
	Function is lintOne(String is path, Boolean is strict, LintTally is tally, Cleo is ui){
		local String is source: fileRead(path: path, default: '');
		local Lexer is lexer: Lexer:init(source: source);
		local Parser is parser: Parser:init(tokens: []);
		parser:setLexer(lexer: lexer);
		parser:setSourceFile(file: path);
		local ProgramNode is program: parser:parseProgram();
		if({ lexer:hasErrors() }, {
			Stderr:line('Lexical errors encountered during linting:');
			local Array of Error is lexErrors: lexer:getErrors();
			lexErrors:each(action: local Function(Error is err){
				Stderr:line('  [' . path . '] ' . err:toString());
			});
			if({ strict }, {
				Process:exit(status: 1);
			});
			tally:broken: tally:broken + 1;
			return;
		});
		if({ parser:hasErrors() }, {
			Stderr:line('Syntax errors encountered during linting:');
			local Array of Error is parseErrs: parser:getErrors();
			parseErrs:each(action: local Function(Error is err){
				Stderr:line(err:toString());
			});
			if({ strict }, {
				Process:exit(status: 1);
			});
			tally:broken: tally:broken + 1;
			return;
		});
		local Linter is linter: Linter:init();
		local Array of LintIssue is issues: linter:lint(source: source, program: program);
		if({ strict || issues:length() > 0 }, {
			local CleoSection is fSec: ui:addSection(
				title: ' ' . path . ' ',
				titleColor: CleoColor:ansi(code: 254),
				titleBgColor: CleoColor:ansi(code: 237),
				titlePlacement: TitlePlacement:HEADER_ROW,
				fgColor: CleoColor:ansi(code: 250)
			);
			if({ issues:length() == 0 }, {
				fSec:addLine(text: Ansi:color256(code: 114, text: '●') . ' All standard checks passed.', color: CleoColor:ansi(code: 255), rightText: '✔ CLEAN');
			}, {
				issues:each(action: local Function(LintIssue is issue){
					local String is dot: if({ issue:isWarning }, { Ansi:color256(code: 203, text: '●') }, { Ansi:color256(code: 220, text: '●') });
					local String is loc: if({ issue:line > 0 }, { 'line ' . (issue:line as String) }, { '' });
					fSec:addLine(text: dot . ' ' . issue:message, color: CleoColor:ansi(code: 255), rightText: loc);
				});
			});
		});
		tally:files: tally:files + 1;
		tally:warnings: tally:warnings + linter:countWarnings(issues: issues);
		tally:notices: tally:notices + linter:countNotices(issues: issues);
	}

	## Collects all non-empty non-negative `.spec` file paths under [absDir] recursively.
	Function is collectTreeFiles(String is absDir, Array of String is files){
		Dir:dirList(path: absDir):each(action: local Function(String is name){
			if({ name:startsWith(prefix: '.') }, {
				return;
			});
			local String is childAbs: absDir . '/' . name;
			local Array of String is children: Dir:dirList(path: childAbs);
			if({ children:length() > 0 }, {
				:collectTreeFiles(absDir: childAbs, files: files);
			}, {
				if({ name:endsWith(suffix: '.spec') }, {
					local String is content: fileRead(path: childAbs, default: '');
					if({ content != '' && :bannerKind(content: content) != 'negative' }, {
						files:add(item: childAbs);
					});
				});
			});
		});
	}

	## The file's `#! specunit:` banner kind ('' when unmarked) — the
	## repo's self-describing test classification. Negative fixtures are
	## compile-must-fail sources, deliberately broken: linting them is
	## permanent noise, so tree mode skips them (single-file mode still
	## lints whatever it is pointed at).
	##
	## @param content: The file content.
	## @return: The banner kind, or '' when unmarked.
	Function of String is bannerKind(String is content){
		local String is kind: '';
		content:split(delimiter: "\n"):each(action: local Function(String is seg){
			if({ seg:startsWith(prefix: '#! specunit: ') }, {
				kind: seg:substring(start: 13, end: seg:length());
			});
		});
		return kind;
	}

	## The Phase 0.5 instance-model audit over the fully loaded program:
	## the loader resolves the target's imports the same way the
	## compiler's does (executable-tree walk finds the repo's packages).
	## Informational — always exits 0.
	##
	## @param path: The root file of the program to audit.
	Function is auditFile(String is path){
		local Loader is loader: Loader:init();
		local ProgramNode is program: loader:loadProgram(rootPath: path);
		Output:line('loading packages · ' . (loader:loadedFileCount() as String) . ' files, ' . (program:classes:length() as String) . ' classes · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');
		if({ loader:getParseErrors():length() > 0 }, {
			Stderr:line('Compilation errors encountered during loading:');
			local Array of String is loadErrors: loader:getParseErrors();
			loadErrors:each(action: local Function(String is err){
				Stderr:line(err);
			});
			Stderr:line('Compilation aborted due to syntax or load errors.');
			Process:exit(status: 1);
		});
		loader:cleanup();
		local Linter is auditor: Linter:init();
		local Array of LintIssue is auditIssues: auditor:auditProgram(program: program);
		auditor:auditReport(filePath: path, issues: auditIssues);
	}
}

## The run tally: files linted, warnings, notices, syntax-broken files.
## Plain instance state — speclint runs serially (parse-only is
## ms-per-file), so no held machinery is needed; a Parallel wave would
## make this held, the specunit registry pattern.
Class is LintTally{
	namespace: ['speclint'];

	Int is files: 0;
	Int is warnings: 0;
	Int is notices: 0;
	Int is broken: 0;

	replace Function is init(){
	}
}
