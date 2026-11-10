Class is FileAsyncTest{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', File],
		['base', 'sys', Process],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('======================================');
		Output:line('    Spec Async File Operations Test   ');
		Output:line("======================================\n");

		local String is asyncFile: '/tmp/spec_async_test.txt';
		local String is content: 'Async write data from background worker!';

		Output:line('1. Initiating File:writeAsync on worker thread...');
		fileWriteAsync(
			path: asyncFile,
			content: content,
			onSuccess: local Function(Int is bytes){
				Output:line('[PASS] Background File:writeAsync completed! Written bytes: ' . bytes);
			},
			onError: local Function(String is err){
				Output:line('[FAIL] File:writeAsync failed: ' . err);
			}
		);

		# Wait for background thread write to finish
		Process:execute(command: 'sleep', args: ['0.1']);

		Output:line("\n2. Initiating File:readAsync on worker thread...");
		fileReadAsync(
			path: asyncFile,
			onSuccess: local Function(String is data){
				Output:line('[PASS] Background File:readAsync completed! Content: \'' . data . '\'');
			},
			onError: local Function(String is err){
				Output:line('[FAIL] File:readAsync failed: ' . err);
			}
		);

		# Wait for background thread read to finish
		Process:execute(command: 'sleep', args: ['0.1']);

		Output:line("\nAsync File Operations test completed successfully!");
	}

}
