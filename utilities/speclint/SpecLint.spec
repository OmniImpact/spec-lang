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
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Stderr()],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['base', 'sys', as File()],
		['base', 'sys', Ansi],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		local String is inputPath: args:getString(key: 'i', default: '');
		if({ inputPath == '' }, {
			inputPath: args:getString(key: 'input', default: '');
		});
		local String is dirsRaw: args:getString(key: 't', default: '');
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
			self:auditFile(path: inputPath);
			Process:exit(status: 0);
		});

		# Single file: the old `spec --lint <file>` shape, byte-identical
		# report, with the standalone exit contract (1 on findings).
		if({ inputPath != '' }, {
			if({ !fileExists(path: inputPath) }, {
				Stderr:line('Error: Source file not found: ' . inputPath);
				Process:exit(status: 1);
			});
			local LintTally is tally: LintTally:init();
			self:lintOne(path: inputPath, strict: true, tally: tally);
			if({ (tally:warnings + tally:notices) > 0 }, {
				Process:exit(status: 1);
			});
			Process:exit(status: 0);
		});

		# Tree walk: every .spec under the -t roots (repeatable,
		# comma/newline separated — the argv parser accumulates repeats).
		local LintTally is tally: LintTally:init();
		local Int is roots: 0;
		dirsRaw:split(delimiter: "\n"):each(action: local Function(String is seg){
			seg:split(delimiter: ','):each(action: local Function(String is dir){
				if({ dir != '' }, {
					roots: roots + 1;
					self:walkTree(absDir: dir, tally: tally);
				});
			});
		});
		if({ roots == 0 }, {
			Output:line('SpecLint (Pure Spec)');
			Stderr:line('Usage: speclint -i <file.spec> | speclint -t <dir> [-t <dir> ...] | speclint -a -i <file.spec>');
			Process:exit(status: 2);
		});
		local String is tail: '';
		if({ tally:broken > 0 }, {
			tail: ', ' . (tally:broken as String) . ' syntax-broken';
		});
		local String is text: '== ' . (tally:files as String) . ' file(s) linted, ' . (tally:warnings as String) . ' warning(s), ' . (tally:notices as String) . ' notice(s)' . tail . ' ==';
		if({ (tally:warnings + tally:notices + tally:broken) > 0 }, {
			Output:line(bold() . color256(code: 203, text: text));
		}, {
			Output:line(bold() . color256(code: 114, text: text));
		});
		if({ (tally:warnings + tally:notices + tally:broken) > 0 }, {
			Process:exit(status: 1);
		});
		Process:exit(status: 0);
	}

	## Lints one file: lex, parse, run the standards walk, print the
	## per-file report — byte-identical to what the compiler's retired
	## --lint mode printed, because it is the same Linter.report. With
	## [strict] (single-file mode) lex/parse errors abort with exit 1
	## exactly as the old mode did; in tree mode they are tallied and
	## the walk continues.
	##
	## @param path: The file to lint.
	## @param strict: Abort on syntax errors instead of tallying them.
	## @param tally: The run tally to update.
	Function is lintOne(String is path, Boolean is strict, LintTally is tally){
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
		linter:report(filePath: path, issues: issues);
		tally:files: tally:files + 1;
		tally:warnings: tally:warnings + linter:countWarnings(issues: issues);
		tally:notices: tally:notices + linter:countNotices(issues: issues);
	}

	## Walks [absDir] recursively (dot entries skipped), linting every
	## non-empty .spec file. A directory is any entry whose dirList is
	## non-empty (spec_dir_list on a file returns empty) — the specunit
	## discovery convention.
	##
	## @param absDir: The tree root to walk.
	## @param tally: The run tally to update.
	Function is walkTree(String is absDir, LintTally is tally){
		Dir:dirList(path: absDir):each(action: local Function(String is name){
			if({ name:startsWith(prefix: '.') }, {
				return;
			});
			local String is childAbs: absDir . '/' . name;
			local Array of String is children: Dir:dirList(path: childAbs);
			if({ children:length() > 0 }, {
				self:walkTree(absDir: childAbs, tally: tally);
			}, {
				if({ name:endsWith(suffix: '.spec') }, {
					local String is content: fileRead(path: childAbs, default: '');
					if({ content != '' && self:bannerKind(content: content) != 'negative' }, {
						self:lintOne(path: childAbs, strict: false, tally: tally);
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
