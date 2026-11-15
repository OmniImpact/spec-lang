#! Package base:sys
#! Public wrapper over the sysinternal audio floor.

Class is AudioDevice{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', List],
		['base', 'sysinternal', Audio]
	];

	Function of Int is open(Int is sampleRate, Int is channels, Int is format){
		return base:sysinternal:Audio:audio_open(sample_rate: sampleRate, channels: channels, format: format);
	}

	Function of Int is write(Int is handle, List of Byte is buffer){
		return base:sysinternal:Audio:audio_write(handle: handle, buffer: buffer);
	}

	Function of Int is drain(Int is handle){
		return base:sysinternal:Audio:audio_drain(handle: handle);
	}

	Function is close(Int is handle){
		base:sysinternal:Audio:audio_close(handle: handle);
	}
}
