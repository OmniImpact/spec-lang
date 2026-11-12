#! SpecUnit sweep (from file_async_test.spec): background-thread file
#! operations — fileWriteAsync completes on the worker thread with the
#! full byte count, and a following fileReadAsync delivers exactly the
#! written content. Callback outcomes are signaled through atomic slots
#! (closure capture does not write back into the enclosing frame, and
#! the callbacks run on the worker thread), then asserted on the main
#! thread after the join sleep.

Class of SpecUnitTest is TestFileAsync{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', File],
		['base', 'sys', Process],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Conditional()]
	];

	## Background write: onSuccess fires with the full byte count and
	## onError stays silent.
	Function is testWriteAsyncCallback(){
		local String is asyncFile: '/tmp/spec_async_test.txt';
		local String is content: 'Async write data from background worker!';

		# Slot 50: -1 pending, byte count on success, -2 on error.
		Process:atomicPut(slot: 50, value: -1);
		fileWriteAsync(
			path: asyncFile,
			content: content,
			onSuccess: local Function(Int is bytes){
				Process:atomicPut(slot: 50, value: bytes);
			},
			onError: local Function(String is err){
				Process:atomicPut(slot: 50, value: -2);
			}
		);

		# Wait for background thread write to finish
		Process:execute(command: 'sleep', args: ['0.1']);

		local Int is wrote: Process:atomicGet(slot: 50);
		local Int is expectedBytes: content:length();
		Assert:areEqualInt(expectedBytes, wrote);
	}

	## Background read of a background-written file: the async-delivered
	## content equals the written content and onError stays silent.
	Function is testReadAsyncRoundTrip(){
		local String is asyncFile: '/tmp/spec_async_test.txt';
		local String is content: 'Async write data from background worker!';

		# Seed the file from the background writer thread first.
		Process:atomicPut(slot: 50, value: -1);
		fileWriteAsync(
			path: asyncFile,
			content: content,
			onSuccess: local Function(Int is bytes){
				Process:atomicPut(slot: 50, value: bytes);
			},
			onError: local Function(String is err){
				Process:atomicPut(slot: 50, value: -2);
			}
		);

		# Wait for background thread write to finish
		Process:execute(command: 'sleep', args: ['0.1']);
		local Int is wrote: Process:atomicGet(slot: 50);
		local Int is expectedBytes: content:length();
		Assert:areEqualInt(expectedBytes, wrote);

		# Slot 51: -1 pending, 1 when the delivered content matches, 0 on
		# mismatch, -2 on error.
		Process:atomicPut(slot: 51, value: -1);
		fileReadAsync(
			path: asyncFile,
			onSuccess: local Function(String is data){
				Conditional:if(check: { data == content }, then: {
					Process:atomicPut(slot: 51, value: 1);
				}, else: {
					Process:atomicPut(slot: 51, value: 0);
				});
			},
			onError: local Function(String is err){
				Process:atomicPut(slot: 51, value: -2);
			}
		);

		# Wait for background thread read to finish
		Process:execute(command: 'sleep', args: ['0.1']);

		local Int is readOutcome: Process:atomicGet(slot: 51);
		Assert:areEqualInt(1, readOutcome);
	}
}
