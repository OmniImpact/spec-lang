#! Package theosynth:model:instruments
#! Square-wave oscillator instrument.

Class of Instrument is SquareInstrument{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', [Instrument, InstrumentVoice, Waveform]],
		['theosynth', 'model', 'instruments', SquareVoice],
		['theosynth', 'util', SynthStrings],
		['base', 'math', as Math()]
	];

	replace Function of Waveform is waveform(){ Waveform:SQUARE }

	replace Function of String is name(){ SynthStrings:WAVE_SQUARE }

	replace Function of InstrumentVoice is createVoice(Int is midi, Float is freqHz, Int is sampleRate){
		SquareVoice(midi: midi, step: freqHz / toFloat(value: sampleRate), initialEnv: 0.0)
	}
}
