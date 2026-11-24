#! Package base:sysinternal
#! The audio floor: low-level PCM audio output bound to C.

Class is Audio{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Returns the C-string address of the last audio error on this thread.
	## Bound to `spec_pal_audio_last_error`.
	Function of Int is pal_audio_last_error();

	## Opens an audio playback stream. Bound to `spec_pal_audio_open`.
	Function of Int is pal_audio_open(Int is sample_rate, Int is channels, Int is format);

	## Writes [len] bytes of PCM audio data at [data_addr] to stream [handle].
	## Bound to `spec_pal_audio_write`.
	Function of Int is pal_audio_write(Int is handle, Int is data_addr, Int is len);

	## Drains the pending audio buffer queue until finished. Bound to `spec_audio_drain`.
	Function of Int is audio_drain(Int is handle);

	## Closes the audio stream and releases hardware resources. Bound to `spec_audio_close`.
	Function is audio_close(Int is handle);
}
