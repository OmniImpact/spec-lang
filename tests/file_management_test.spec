Class is FileManagementTest{

	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:io:File
	];

	replace Function is init(Map of String to String is args){
		output:line('======================================');
		output:line('   Spec File Management & Error Test  ');
		output:line("======================================\n");

		local String is testFile: '/tmp/spec_file_test.txt';
		local String is testContent: 'Hello from Spec File Management with Callbacks!';

		# 1. Test Write with Callbacks
		output:line('1. Testing File:write with onSuccess and onError callbacks...');
		local Boolean is writeHandled: false;
		File:write(
			path: testFile,
			content: testContent,
			onSuccess: local Function(Int is bytes){
				output:line('[PASS] File:write onSuccess callback executed! Bytes written: ' . bytes);
			},
			onError: local Function(String is err){
				output:line('[FAIL] File:write onError callback triggered: ' . err);
			}
		);

		# 2. Test Read with Callbacks
		output:line("\n2. Testing File:read with onSuccess and onError callbacks...");
		File:read(
			path: testFile,
			onSuccess: local Function(String is content){
				output:line('[PASS] File:read onSuccess callback executed! Content length: ' . content:length());
				output:line('Content: \'' . content . '\'');
			},
			onError: local Function(String is err){
				output:line('[FAIL] File:read onError callback triggered: ' . err);
			}
		);

		# 3. Test Error Handling on Non-Existent File
		output:line("\n3. Testing File:read on non-existent file for error callback...");
		local String is nonExistent: '/tmp/non_existent_spec_file_xyz123.txt';
		File:read(
			path: nonExistent,
			onSuccess: local Function(String is content){
				output:line('[FAIL] File:read should not succeed on non-existent file!');
			},
			onError: local Function(String is err){
				output:line('[PASS] File:read onError callback successfully caught failure: ' . err);
			}
		);

		# 4. Test Error Handling on Invalid Write Path
		output:line("\n4. Testing File:write on invalid directory path...");
		local String is invalidPath: '/non_existent_directory_xyz/file.txt';
		File:write(
			path: invalidPath,
			content: 'data',
			onSuccess: local Function(Int is bytes){
				output:line('[FAIL] File:write should not succeed on invalid path!');
			},
			onError: local Function(String is err){
				output:line('[PASS] File:write onError callback successfully caught failure: ' . err);
			}
		);

		output:line("\nFile Management & Error Handling test completed successfully!");
	}

}
