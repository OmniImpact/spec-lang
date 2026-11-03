class FileAsyncTest{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:io:File,
		base:sys:Process
	];

	replace local Function is init(Map of String to String is args){
		output:line("======================================");
		output:line("    Spec Async File Operations Test   ");
		output:line("======================================\n");

		local String is asyncFile: "/tmp/spec_async_test.txt";
		local String is content: "Async write data from background worker!";

		output:line("1. Initiating File:writeAsync on worker thread...");
		File:writeAsync(
			path: asyncFile,
			content: content,
			onSuccess: local Function(Int is bytes){
				output:line("[PASS] Background File:writeAsync completed! Written bytes: " . bytes);
			},
			onError: local Function(String is err){
				output:line("[FAIL] File:writeAsync failed: " . err);
			}
		);

		# Wait for background thread write to finish
		Process:execute(command: "sleep", args: ["0.1"]);

		output:line("\n2. Initiating File:readAsync on worker thread...");
		File:readAsync(
			path: asyncFile,
			onSuccess: local Function(String is data){
				output:line("[PASS] Background File:readAsync completed! Content: '" . data . "'");
			},
			onError: local Function(String is err){
				output:line("[FAIL] File:readAsync failed: " . err);
			}
		);

		# Wait for background thread read to finish
		Process:execute(command: "sleep", args: ["0.1"]);

		output:line("\nAsync File Operations test completed successfully!");
	}

}
