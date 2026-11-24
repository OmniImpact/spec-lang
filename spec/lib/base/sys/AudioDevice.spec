#! Package base:sys
#! Public wrapper over the sysinternal audio floor.

Class is AudioDevice{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'sys', AudioError],
		['base', 'struct', List],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Audio]
	];

	local Function is emitLastError(AudioError is kind, Function is onError){
		local Int is errCstr: base:sysinternal:Audio:pal_audio_last_error();
		local String is msg: if({ errCstr != 0 }, {
			Mem:strFromBytes(srcAddr: errCstr, len: Mem:cstrLen(cstrAddr: errCstr))
		}, {
			'Audio error'
		});
		onError(SpecError:init(kind: kind, description: msg));
	}

	Function of Int is open(Int is sampleRate, Int is channels, Int is format, Function is onError: local Function(SpecError of AudioError is error){}){
		local Int is h: base:sysinternal:Audio:pal_audio_open(sample_rate: sampleRate, channels: channels, format: format);
		if({ h < 0 }, {
			:emitLastError(kind: AudioError:OPEN_FAILED, onError: onError);
		});
		return h;
	}

	Function of Int is write(Int is handle, List of Byte is buffer, Function is onError: local Function(SpecError of AudioError is error){}){
		local Int is ptr: buffer:rawDataAddr();
		local Int is len: buffer:length();
		local Int is n: base:sysinternal:Audio:pal_audio_write(handle: handle, data_addr: ptr, len: len);
		if({ n < 0 }, {
			:emitLastError(kind: AudioError:WRITE_FAILED, onError: onError);
		});
		return n;
	}

	Function of Int is drain(Int is handle){
		return base:sysinternal:Audio:audio_drain(handle: handle);
	}

	Function is close(Int is handle){
		base:sysinternal:Audio:audio_close(handle: handle);
	}
}
