#! Demonstrates scoped region desugaring (`as`) for resource management,
#! automatic cleanup, benchmark timing, flat pipelines without callback pyramids,
#! and SpecUnit-style Cleo terminal output.

## Demonstrates scoped region desugaring (`as`) for resource management and timing.
Class is ScopeAsDemo{

	replace Array of Array of String is using: [
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', TitlePlacement],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Uri()],
		[CsvParser]
	];

	## Measures and logs the wall-clock duration of [block] under [label].
	Function is measure(String is label, CleoSection is sec, Function is block){
		sec:addLine(text: "[Timer] Starting: {{label}}", color: CleoColor:ansi(code: 250));
		local Int is start: clockMs();
		block();
		local Int is elapsed: clockMs() - start;
		sec:addLine(text: "[Timer] Finished: {{label}}", color: CleoColor:ansi(code: 255), rightText: "{{elapsed}} ms");
	}

	## Writes [content] to [path], invokes [block] with [path], and removes the file on exit.
	Function is withTempFile(String is path, String is content, CleoSection is sec, Function is block){
		sec:addLine(text: "[File] Creating managed resource: {{path}}", color: CleoColor:ansi(code: 250));
		fileWrite(path: path, content: content);
		block(path);
		if({ fileExists(path: path) }, {
			fileRemove(path: path);
			sec:addLine(text: "[File] Cleaned up managed resource: {{path}}", color: CleoColor:ansi(code: 245));
		});
	}

	## Entry point; runs a temp-file CSV ingestion pipeline inside nested `as` scopes.
	replace Function is init(Map of String to String is args){
		local Cleo is ui: Cleo(
			title: ' scope_as_demo ',
			titleColor: CleoColor:ansi(code: 255),
			titleBgColor: CleoColor:ansi(code: 236),
			width: CleoWidth:percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 237)
		);
		local CleoSection is recSec: ui:addSection(
			title: ' Parsed Profiles ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		local CleoSection is logSec: ui:addSection(
			title: ' Lifecycle & Unwind Log ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);

		local String is tempPath: Uri:tempFile();
		local Str is csvData: "id,name,role,department\n" .
			"101,Alice,Systems Engineer,Infrastructure\n" .
			"102,Bob,Database Architect,Platform\n" .
			"103,Charlie,Security Analyst,SecOps\n" .
			"104,Diana,Compiler Engineer,Core Tooling\n";

		runPipeline(tempPath: tempPath, csvData: csvData, recSec: recSec, logSec: logSec);
		ui:flushFinal();
	}

	local Function is runPipeline(String is tempPath, Str is csvData, CleoSection is recSec, CleoSection is logSec){
		:measure(label: 'Data Ingestion & Report Pipeline', sec: logSec, block: local Function(){
			:withTempFile(path: tempPath, content: "{{csvData}}", sec: logSec, block: local Function(String is path){
				local String is raw: fileRead(path: path, default: '');
				local CsvParser is parser: CsvParser();
				local Array of Array of String is rows: parser:parseRows(raw: raw, skipHeader: true);

				rows:each(action: local Function(Array of String is fields){
					if({ fields:length() >= 4 }, {
						recSec:addLine(
							text: "#{{fields:get(index: 0)}} · {{fields:get(index: 1)}}",
							color: CleoColor:ansi(code: 252),
							rightText: "{{fields:get(index: 2)}} ({{fields:get(index: 3)}})"
						);
					});
				});
				logSec:addLine(text: "[Report] Processed {{rows:length()}} employee profiles; unwinding scopes in LIFO order", color: CleoColor:ansi(code: 250));
			});
		});
	}

}
