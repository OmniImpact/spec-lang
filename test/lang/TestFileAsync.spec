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
		['base', 'sys', as Time()],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Polls an atomic slot until it leaves the pending (-1) sentinel or [timeoutMs] elapses.
	Function of Int is waitForSlot(Int is slot, Int is timeoutMs: 5000){
		local Int is start: Time:monotonicMs();
		while(evaluate: { Process:atomicGet(slot: slot) == -1 && (Time:monotonicMs() - start) < timeoutMs }, iterate: {
			Time:sleepMs(ms: 5);
		});
		return Process:atomicGet(slot: slot);
	}

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
		local Int is wrote: :waitForSlot(slot: 50);
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
		local Int is wrote: :waitForSlot(slot: 50);
		local Int is expectedBytes: content:length();
		Assert:areEqualInt(expectedBytes, wrote);

		# Slot 51: -1 pending, 1 when the delivered content matches, 0 on
		# mismatch, -2 on error.
		Process:atomicPut(slot: 51, value: -1);
		fileReadAsync(
			path: asyncFile,
			onSuccess: local Function(String is data){
				if(check: { data == content }, then: {
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
		local Int is readOutcome: :waitForSlot(slot: 51);
		Assert:areEqualInt(1, readOutcome);
	}
}
