#! Package base:sysinternal
#! The audio floor: low-level PCM audio output bound to C.

Class is Audio{
	namespace: ['base', 'sysinternal'];

	## Opens an audio playback stream. Bound to `spec_audio_open`.
	##
	## @param sample_rate: Sample rate in Hz (e.g. 44100 or 48000).
	## @param channels: Number of audio channels (1=mono, 2=stereo).
	## @param format: Sample format (1=16-bit signed integer PCM).
	## @return: Audio stream handle (> 0), or -1 on failure.
	Function of Int is audio_open(Int is sample_rate, Int is channels, Int is format);

	## Writes PCM audio data to the output stream. Bound to `spec_audio_write`.
	##
	## @param handle: Audio stream handle returned by audio_open.
	## @param buffer: ByteBuffer containing PCM audio samples.
	## @return: Number of bytes written, or -1 on error.
	Function of Int is audio_write(Int is handle, ByteBuffer is buffer);

	## Drains the pending audio buffer queue until finished. Bound to `spec_audio_drain`.
	##
	## @param handle: Audio stream handle.
	## @return: 0 on success.
	Function of Int is audio_drain(Int is handle);

	## Closes the audio stream and releases hardware resources. Bound to `spec_audio_close`.
	##
	## @param handle: Audio stream handle.
	Function is audio_close(Int is handle);
}
