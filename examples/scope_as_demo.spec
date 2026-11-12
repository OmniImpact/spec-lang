#! specunit: suite

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
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Measures and prints elapsed execution time for an arbitrary block.
	##
	## @param label: Description of the timed operation.
	## @param block: The code region to execute and measure.
	Function is measure(String is label, Function is block){
		line("[Timer] Starting: " . label);
		local Int is start: clockMs();
		block();
		local Int is elapsed: clockMs() - start;
		line("[Timer] Finished: " . label . " (" . elapsed . " ms elapsed)\n");
	}

	## Creates a temporary file, provides its path to the callback, and
	## guarantees file deletion upon block completion. The console
	## functions are named consOut/consIn, so the generic I/O verbs
	## (`write`, `read`, `exists`, `remove`) answer bare for File.
	##
	## @param path: Path to create the temporary file at.
	## @param content: Initial file data.
	## @param block: Callback receiving the temporary file's path.
	Function is withTempFile(String is path, String is content, Function is block){
		line("[File] Creating managed resource: " . path);
		fileWrite(path: path, content: content);
		block(path);
		if({ fileExists(path) }, {
			fileRemove(path);
			line("[File] Cleaned up managed resource: " . path);
		});
	}

## Entry point demonstrating linear `as` scopes.
##
## @param args: CLI arguments map.
replace Function is init(Map of String to String is args){
	line("=================================================");
	line("       Spec Scoped Region (`as`) Demo            ");
	line("=================================================\n");

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
	line("[Task] Reading records from " . path . "...");
	local String is raw: fileRead(path: path, default: "");
	local Array of String is lines: raw:lines();
	line("[Task] Total lines read: " . lines:length());

	local Array of String is names: [];
	local Array of String is roles: [];

	# Parse rows using a scoped loop starting after header (row 1)
	while(
		[Int is row: 1, Int is totalRows: lines:length()],
		{ row < totalRows },
		{
			local String is line: lines:get(index: row);
			local Array of String is fields: line:split(delimiter: ",");
			if({ fields:length() >= 4 }, {
				names:add(item: fields:get(index: 1));
				roles:add(item: fields:get(index: 2));
				line("  -> User #" . fields:get(index: 0) . ": " . fields:get(index: 1) . " (" . fields:get(index: 2) . ")");
			});
			row++;
		}
	);

	line("\n[Report] Successfully processed " . names:length() . " employee profiles.");
	line("[Report] Exiting block - all resource scopes will now unwind in reverse (LIFO) order:");
}
}
