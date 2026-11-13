#! Package base:audio
#! Audio playback interface for raw PCM sound output.

Class is Audio{
	namespace: ['base', 'audio'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Audio]
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
	## @return: Configured Audio instance, or closed/invalid on failure.
	Function of Audio is open(Int is sampleRate: 44100, Int is channels: 2, Int is format: 1){
		local Audio is a: Audio:init();
		local Int is h: base:sysinternal:Audio:audio_open(sample_rate: sampleRate, channels: channels, format: format);
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
	## @param samples: ByteBuffer containing raw PCM data.
	## @return: Number of bytes written, or -1 on error.
	Function of Int is write(ByteBuffer is samples){
		if({ self:isClosed }, {
			return -1;
		});
		return base:sysinternal:Audio:audio_write(handle: self:handle, buffer: samples);
	}

	## Drains the output queue, blocking until all buffered audio finishes playing.
	Function is drain(){
		if({ !self:isClosed }, {
			base:sysinternal:Audio:audio_drain(handle: self:handle);
		});
	}

	## Closes the audio stream and releases hardware resources.
	Function is close(){
		if({ !self:isClosed }, {
			base:sysinternal:Audio:audio_close(handle: self:handle);
			self:isClosed: true;
			self:handle: -1;
		});
	}

	## Returns true if the audio stream is open.
	Function of Boolean is isOpen(){
		return !self:isClosed;
	}
}
