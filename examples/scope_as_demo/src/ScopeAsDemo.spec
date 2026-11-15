#! Demonstrates scoped region desugaring (`as`) for resource management,
#! automatic cleanup, benchmark timing, and flat pipelines without callback pyramids.

## Demonstrates scoped region desugaring (`as`) for resource management and timing.
Class is ScopeAsDemo{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Uri()],
		[CsvParser]
	];

	## Measures and prints the wall-clock duration of [block] under [label].
	Function is measure(String is label, Function is block){
		line("[Timer] Starting: " . label);
		local Int is start: clockMs();
		block();
		local Int is elapsed: clockMs() - start;
		line("[Timer] Finished: " . label . " (" . elapsed . " ms elapsed)\n");
	}

	## Writes [content] to [path], invokes [block] with [path], and removes the file on exit.
	Function is withTempFile(String is path, String is content, Function is block){
		line("[File] Creating managed resource: " . path);
		fileWrite(path: path, content: content);
		block(path);
		if({ fileExists(path: path) }, {
			fileRemove(path: path);
			line("[File] Cleaned up managed resource: " . path);
		});
	}

	## Entry point; runs a temp-file CSV ingestion pipeline inside nested `as` scopes.
	replace Function is init(Map of String to String is args){
		line("=================================================");
		line("       Spec Scoped Region (`as`) Demo            ");
		line("=================================================\n");

		local String is tempPath: Uri:tempFile();
		local String is csvData: "id,name,role,department\n" .
			"101,Alice,Systems Engineer,Infrastructure\n" .
			"102,Bob,Database Architect,Platform\n" .
			"103,Charlie,Security Analyst,SecOps\n" .
			"104,Diana,Compiler Engineer,Core Tooling\n";

		as: self:measure(label: "Data Ingestion & Report Pipeline");
		as (String is path): self:withTempFile(path: tempPath, content: csvData);

		line("[Task] Reading records from " . path . "...");
		local String is raw: fileRead(path: path, default: "");
		local CsvParser is parser: CsvParser:init();
		local Array of Array of String is rows: parser:parseRows(raw: raw, skipHeader: true);
		line("[Task] Total data rows parsed: " . (rows:length() as String));

		rows:each(action: local Function(Array of String is fields){
			if({ fields:length() >= 4 }, {
				line("  -> User #" . fields:get(index: 0) . ": " . fields:get(index: 1) . " (" . fields:get(index: 2) . ")");
			});
		});

		line("\n[Report] Successfully processed " . (rows:length() as String) . " employee profiles.");
		line("[Report] Exiting block - all resource scopes will now unwind in reverse (LIFO) order:");
	}

}
