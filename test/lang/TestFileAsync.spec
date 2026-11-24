#! SpecUnit sweep (from file_async_test.spec): background-thread file
#! operations — fileWriteAsync completes on the worker thread with the
#! full byte count, and a following fileReadAsync delivers exactly the
#! written content. Callback outcomes are signaled through atomic slots
#! (closure capture does not write back into the enclosing frame, and
#! the callbacks run on the worker thread), then asserted on the main
#! thread after the join sleep.

Class of SpecUnitTest is TestFileAsync{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Time()],
		['base', 'core', SpecError],
		['base', 'sys', FileError],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Background write inside ThreadScope: onSuccess fires with the full byte count
	## and the scope joins the task before exiting.
	Function is testWriteAsyncCallback(){
		local String is asyncFile: '/tmp/spec_async_test.txt';
		local String is content: 'Async write data from background worker!';

		# Slot 50: -1 pending, byte count on success, -2 on error.
		Process:atomicPut(slot: 50, value: -1);
		ThreadScope:open(body: local Function(ThreadScope is scope){
			fileWriteAsync(
				scope: scope,
				path: asyncFile,
				content: content,
				onSuccess: local Function(Int is bytes){
					Process:atomicPut(slot: 50, value: bytes);
				},
				onError: local Function(SpecError of FileError is err){
					Process:atomicPut(slot: 50, value: -2);
				}
			);
		});

		local Int is wrote: Process:atomicGet(slot: 50);
		local Int is expectedBytes: content:length();
		Assert:areEqualInt(expectedBytes, wrote);
	}

	## Background read of a background-written file inside ThreadScope: the async-delivered
	## content equals the written content and onError stays silent.
	Function is testReadAsyncRoundTrip(){
		local String is asyncFile: '/tmp/spec_async_test.txt';
		local String is content: 'Async write data from background worker!';

		Process:atomicPut(slot: 50, value: -1);
		ThreadScope:open(body: local Function(ThreadScope is scope){
			fileWriteAsync(
				scope: scope,
				path: asyncFile,
				content: content,
				onSuccess: local Function(Int is bytes){
					Process:atomicPut(slot: 50, value: bytes);
				},
				onError: local Function(SpecError of FileError is err){
					Process:atomicPut(slot: 50, value: -2);
				}
			);
		});

		local Int is wrote: Process:atomicGet(slot: 50);
		local Int is expectedBytes: content:length();
		Assert:areEqualInt(expectedBytes, wrote);

		# Slot 51: -1 pending, 1 when the delivered content matches, 0 on
		# mismatch, -2 on error.
		Process:atomicPut(slot: 51, value: -1);
		ThreadScope:open(body: local Function(ThreadScope is scope){
			fileReadAsync(
				scope: scope,
				path: asyncFile,
				onSuccess: local Function(String is data){
					if(check: { data == content }, then: {
						Process:atomicPut(slot: 51, value: 1);
					}, else: {
						Process:atomicPut(slot: 51, value: 0);
					});
				},
				onError: local Function(SpecError of FileError is err){
					Process:atomicPut(slot: 51, value: -2);
				}
			);
		});

		local Int is readOutcome: Process:atomicGet(slot: 51);
		Assert:areEqualInt(1, readOutcome);
	}
}
