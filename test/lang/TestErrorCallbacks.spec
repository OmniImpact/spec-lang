#! SpecUnit sweep: verifies that `onError` callbacks receive non-empty error
#! descriptions across File, Dir, Socket, and Audio failure paths.

Class of SpecUnitTest is TestErrorCallbacks{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', List],
		['base', 'core', SpecError],
		['base', 'sys', FileError],
		['base', 'sys', as File()],
		['base', 'sys', as Dir()],
		['base', 'sys', as Process()],
		['base', 'sys', as Conditional()],
		['base', 'net', as Socket()],
		['base', 'audio', as Audio()]
	];

	Function is testFileRemoveOnError(){
		Process:atomicPut(slot: 65, value: 0);
		local Boolean is ok: fileRemove(
			path: '/tmp/spec_nonexistent_remove_target_xyz_987.txt',
			onError: local Function(SpecError of FileError is error){
				if({ error:description:length() > 0 }, {
					Process:atomicPut(slot: 65, value: 1);
				});
			}
		);
		Assert:isFalse(ok);
		Assert:areEqualInt(1, Process:atomicGet(slot: 65));
	}

	Function is testFileTempInvalidDirOnError(){
		Process:atomicPut(slot: 66, value: 0);
		local String is tmpPath: fileTemp(
			template: '/non_existent_dir_xyz_987/spec_XXXXXX.txt',
			onError: local Function(SpecError of FileError is error){
				if({ error:description:length() > 0 }, {
					Process:atomicPut(slot: 66, value: 1);
				});
			}
		);
		Assert:areEqualString('', tmpPath);
		Assert:areEqualInt(1, Process:atomicGet(slot: 66));
	}

	Function is testDirListOnError(){
		Process:atomicPut(slot: 67, value: 0);
		local Array of String is entries: dirList(
			path: '/non_existent_dir_xyz_987',
			onError: local Function(String is error){
				if({ error:length() > 0 }, {
					Process:atomicPut(slot: 67, value: 1);
				});
			}
		);
		Assert:areEqualInt(0, entries:length());
		Assert:areEqualInt(1, Process:atomicGet(slot: 67));
	}

	Function is testSocketOnError(){
		Process:atomicPut(slot: 68, value: 0);
		local Socket is sock: connect(
			host: '127.0.0.1',
			port: 0,
			timeoutMs: 100,
			onError: local Function(String is error){
				if({ error:length() > 0 }, {
					Process:atomicPut(slot: 68, value: 1);
				});
			}
		);
		Assert:isFalse(sock:isOpen());
		Assert:areEqualInt(1, Process:atomicGet(slot: 68));

		Process:atomicPut(slot: 69, value: 0);
		local Int is sent: sock:sendString(
			text: 'hello',
			onError: local Function(String is error){
				if({ error:length() > 0 }, {
					Process:atomicPut(slot: 69, value: 1);
				});
			}
		);
		Assert:areEqualInt(-1, sent);
		Assert:areEqualInt(1, Process:atomicGet(slot: 69));

		Process:atomicPut(slot: 70, value: 0);
		local String is recvd: sock:receiveString(
			maxBytes: 64,
			onError: local Function(String is error){
				if({ error:length() > 0 }, {
					Process:atomicPut(slot: 70, value: 1);
				});
			}
		);
		Assert:areEqualString('', recvd);
		Assert:areEqualInt(1, Process:atomicGet(slot: 70));
	}

	Function is testClosedAudioWriteOnError(){
		Process:atomicPut(slot: 71, value: 0);
		local Audio is audio: Audio:init();
		local [Byte] is buf;
		local Int is written: audio:write(
			samples: buf,
			onError: local Function(String is error){
				if({ error:length() > 0 }, {
					Process:atomicPut(slot: 71, value: 1);
				});
			}
		);
		Assert:areEqualInt(-1, written);
		Assert:areEqualInt(1, Process:atomicGet(slot: 71));
	}
}
