#! Package base:audio
#! Audio playback interface for raw PCM sound output.

Class is Audio{
	namespace: ['base', 'audio'];

	replace Array of Array of String is using: [
		['base', 'struct', List],
		['base', 'sys', as AudioDevice()],
		['base', 'sys', as Conditional()]
	];

	local Int is handle: -1;
	local Boolean is isClosed: true;
	local Int is sampleRate: 44100;
	local Int is channels: 2;

	## Opens an audio playback stream.
	##
	## @param sampleRate: Sampling rate in Hz (default 44100).
	## @param channels: Number of channels (1=mono, 2=stereo, default 2).
	## @param format: PCM format (1=16-bit signed integer PCM, default 1).
	## @param onError: Optional callback receiving error description on failure: `Function(String is error)`.
	## @return: Configured Audio instance, or closed/invalid on failure.
	Function of Audio is open(Int is sampleRate: 44100, Int is channels: 2, Int is format: 1, Function is onError: local Function(String is error){}){
		local Audio is a: Audio:init();
		local Int is h: AudioDevice:open(sampleRate: sampleRate, channels: channels, format: format, onError: onError);
		if({ h > 0 }, {
			a:handle: h;
			a:isClosed: false;
			a:sampleRate: sampleRate;
			a:channels: channels;
		});
		return a;
	}

	## Writes raw PCM audio samples from [samples] to the output stream.
	##
	## @param samples: List of Byte containing raw PCM data.
	## @param onError: Optional callback receiving error description on failure: `Function(String is error)`.
	## @return: Number of bytes written, or -1 on error.
	Function of Int is write(List of Byte is samples, Function is onError: local Function(String is error){}){
		return AudioDevice:write(handle: self:handle, buffer: samples, onError: onError);
	}

	## Drains the output queue, blocking until all buffered audio finishes playing.
	Function is drain(){
		if({ !self:isClosed }, {
			AudioDevice:drain(handle: self:handle);
		});
	}

	## Closes the audio stream and releases hardware resources.
	Function is close(){
		if({ !self:isClosed }, {
			AudioDevice:close(handle: self:handle);
			self:isClosed: true;
			self:handle: -1;
		});
	}

	## Returns true if the audio stream is open.
	Function of Boolean is isOpen(){
		return !self:isClosed;
	}
}
