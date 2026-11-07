#! Package examples
#! Demonstrates scoped region desugaring (`as`) for resource management,
#! automatic cleanup, benchmark timing, and flat pipelines without callback pyramids.

## Shows how Spec's `as` statement linearizes nested higher-order callbacks:
## - Automatic resource cleanup (RAII / Python with / Go defer pattern)
## - Timing and audit wrappers (`as: measure(...)`)
## - Dynamic resource parameter binding (`as (path): withTempFile(...)`)
## - Scoped inline loops (`While`) parsing data within the managed region
Class is ScopeAsDemo{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'io', Output],
		['base', 'io', File],
		['base', 'iterator'],
		['base', 'sys', Process],
		['base', 'io', as File()],
		['base', 'io', as Output()],
		['base', 'sys', as Process()],
		['base', 'iterator', as While()]
	];

	## Measures and prints elapsed execution time for an arbitrary block.
	##
	## @param label: Description of the timed operation.
	## @param block: The code region to execute and measure.
	Function is measure(String is label, Function is block){
		Output:line("[Timer] Starting: " . label);
		local Int is start: Process:clockMs();
		block();
		local Int is elapsed: Process:clockMs() - start;
		Output:line("[Timer] Finished: " . label . " (" . elapsed . " ms elapsed)\n");
	}

	## Creates a temporary file, provides its path to the callback, and
	## guarantees file deletion upon block completion.
	##
	## @param path: Path to create the temporary file at.
	## @param content: Initial file data.
	## @param block: Callback receiving the temporary file's path.
	Function is withTempFile(String is path, String is content, Function is block){
		Output:line("[File] Creating managed resource: " . path);
		File:write(path: path, content: content);
		block(path);
		if (File:exists(path)) {
			File:remove(path);
			Output:line("[File] Cleaned up managed resource: " . path);
		}
	}

	## Entry point demonstrating linear `as` scopes.
	##
	## @param args: CLI arguments map.
	replace Function is init(Map of String to String is args){
		Output:line("=================================================");
		Output:line("       Spec Scoped Region (`as`) Demo            ");
		Output:line("=================================================\n");

		local String is tempPath: "/tmp/spec_users.csv";
		local String is csvData: "id,name,role,department\n" .
			"101,Alice,Systems Engineer,Infrastructure\n" .
			"102,Bob,Database Architect,Platform\n" .
			"103,Charlie,Security Analyst,SecOps\n" .
			"104,Diana,Compiler Engineer,Core Tooling\n";

		# Outer scope: Benchmark timer wrapper
		as: self:measure(label: "Data Ingestion & Report Pipeline");

		# Middle scope: Temporary file resource with guaranteed LIFO deletion
		as (String is path): self:withTempFile(path: tempPath, content: csvData);

		# Inner workflow: Read file and process records sequentially
		Output:line("[Task] Reading records from " . path . "...");
		local String is raw: File:read(path: path, default: "");
		local Array of String is lines: raw:lines();
		Output:line("[Task] Total lines read: " . lines:length());

		local Array of String is names: [];
		local Array of String is roles: [];

		# Parse rows using a scoped loop starting after header (row 1)
		While(
			[Int is row: 1, Int is totalRows: lines:length()],
			evaluate: { row < totalRows },
			iterate: {
				local String is line: lines:get(index: row);
				local Array of String is fields: line:split(delimiter: ",");
				if (fields:length() >= 4) {
					names:add(item: fields:get(index: 1));
					roles:add(item: fields:get(index: 2));
					Output:line("  -> User #" . fields:get(index: 0) . ": " . fields:get(index: 1) . " (" . fields:get(index: 2) . ")");
				}
				row++;
			}
		);

		Output:line("\n[Report] Successfully processed " . names:length() . " employee profiles.");
		Output:line("[Report] Exiting block - all resource scopes will now unwind in reverse (LIFO) order:");
	}
}
