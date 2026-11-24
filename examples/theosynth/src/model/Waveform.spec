#! Package theosynth:model
#! Synthesizer waveform selection enum.

Class of Enum is Waveform{
	replace [String] is namespace: ['theosynth', 'model'];

	held Waveform is SINE: Waveform:init();
	held Waveform is SQUARE: Waveform:init();
	held Waveform is SAWTOOTH: Waveform:init();
	held Waveform is PLUCK: Waveform:init();
}
