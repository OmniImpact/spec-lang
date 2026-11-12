#! SpecUnit sweep (from file_management_test.spec): the synchronous file
#! callback surface — fileWrite/fileRead round-trip through onSuccess,
#! and the onError path catching missing-file reads and unwritable
#! directories. Callback outcomes are signaled through atomic slots
#! (closure capture does not write back into the enclosing frame); the
#! synchronous return values carry the written/read data directly.

Class of SpecUnitTest is TestFileManagement{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', File],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Conditional()]
	];

	## Write with callbacks, then read with callbacks: onSuccess fires on
	## both, the write reports the full byte count, and the read delivers
	## exactly the written content (through both the callback comparison
	## and the synchronous return value).
	Function is testWriteReadCallbacks(){
		local String is testFile: '/tmp/spec_file_test.txt';
		local String is testContent: 'Hello from Spec File Management with Callbacks!';

		# Slot 60: -1 pending, byte count on success, -2 on error.
		Process:atomicPut(slot: 60, value: -1);
		local Boolean is writeOk: fileWrite(
			path: testFile,
			content: testContent,
			onSuccess: local Function(Int is bytes){
				Process:atomicPut(slot: 60, value: bytes);
			},
			onError: local Function(String is err){
				Process:atomicPut(slot: 60, value: -2);
			}
		);
		Assert:isTrue(writeOk);
		local Int is wrote: Process:atomicGet(slot: 60);
		local Int is expectedBytes: testContent:length();
		Assert:areEqualInt(expectedBytes, wrote);

		# Slot 61: -1 pending, 1 when the delivered content matches, 0 on
		# mismatch, -2 on error.
		Process:atomicPut(slot: 61, value: -1);
		local String is readBack: fileRead(
			path: testFile,
			default: '',
			onSuccess: local Function(String is content){
				Conditional:if(check: { content == testContent }, then: {
					Process:atomicPut(slot: 61, value: 1);
				}, else: {
					Process:atomicPut(slot: 61, value: 0);
				});
			},
			onError: local Function(String is err){
				Process:atomicPut(slot: 61, value: -2);
			}
		);
		Assert:areEqualString(testContent, readBack);
		local Int is readOutcome: Process:atomicGet(slot: 61);
		Assert:areEqualInt(1, readOutcome);
	}

	## Reading a non-existent file must trigger onError, never onSuccess.
	Function is testReadNonExistentTriggersOnError(){
		local String is nonExistent: '/tmp/non_existent_spec_file_xyz123.txt';

		# Slot 60: -1 pending, 1 when onError fired, -2 when onSuccess fired.
		Process:atomicPut(slot: 60, value: -1);
		fileRead(
			path: nonExistent,
			default: '',
			onSuccess: local Function(String is content){
				Process:atomicPut(slot: 60, value: -2);
			},
			onError: local Function(String is err){
				Process:atomicPut(slot: 60, value: 1);
			}
		);

		local Int is errorCaught: Process:atomicGet(slot: 60);
		Assert:areEqualInt(1, errorCaught);
	}

	## Writing into a non-existent directory must trigger onError, never
	## onSuccess, and the write call itself reports failure.
	Function is testWriteInvalidPathTriggersOnError(){
		local String is invalidPath: '/non_existent_directory_xyz/file.txt';

		# Slot 60: -1 pending, 1 when onError fired, -2 when onSuccess fired.
		Process:atomicPut(slot: 60, value: -1);
		local Boolean is writeOk: fileWrite(
			path: invalidPath,
			content: 'data',
			onSuccess: local Function(Int is bytes){
				Process:atomicPut(slot: 60, value: -2);
			},
			onError: local Function(String is err){
				Process:atomicPut(slot: 60, value: 1);
			}
		);
		Assert:isFalse(writeOk);
		local Int is errorCaught: Process:atomicGet(slot: 60);
		Assert:areEqualInt(1, errorCaught);
	}
}
