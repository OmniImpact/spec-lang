#! Package theosynth:model:instruments
#! Pure sine-wave oscillator instrument.

Class of Instrument is SineInstrument{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', [Instrument, InstrumentVoice, Waveform]],
		['theosynth', 'model', 'instruments', SineVoice],
		['theosynth', 'util', SynthStrings]
	];

	replace Function of Waveform is waveform(){ Waveform:SINE }

	replace Function of String is name(){ SynthStrings:WAVE_SINE }

	replace Function of InstrumentVoice is createVoice(Int is midi, Float is freqHz, Int is sampleRate){
		SineVoice(midi: midi, step: freqHz / toFloat(value: sampleRate), initialEnv: 0.0)
	}
}
