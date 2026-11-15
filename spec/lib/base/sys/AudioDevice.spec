#! Package base:sys
#! Public wrapper over the sysinternal audio floor.

Class is AudioDevice{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', List],
		['base', 'sysinternal', Audio]
	];

	Function of Int is open(Int is sampleRate, Int is channels, Int is format, Function is onError: local Function(String is error){}){
		return base:sysinternal:Audio:audio_open_cb(sample_rate: sampleRate, channels: channels, format: format, on_error: onError);
	}

	Function of Int is write(Int is handle, List of Byte is buffer, Function is onError: local Function(String is error){}){
		return base:sysinternal:Audio:audio_write_cb(handle: handle, buffer: buffer, on_error: onError);
	}

	Function of Int is drain(Int is handle){
		return base:sysinternal:Audio:audio_drain(handle: handle);
	}

	Function is close(Int is handle){
		base:sysinternal:Audio:audio_close(handle: handle);
	}
}
