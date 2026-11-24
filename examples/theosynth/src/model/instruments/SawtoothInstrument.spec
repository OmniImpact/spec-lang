#! Package theosynth:model:instruments
#! Sawtooth-wave oscillator instrument.

Class of Instrument is SawtoothInstrument{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', [Instrument, InstrumentVoice, Waveform]],
		['theosynth', 'model', 'instruments', SawtoothVoice],
		['theosynth', 'util', SynthStrings],
		['base', 'math', as Math()]
	];

	replace Function of Waveform is waveform(){ Waveform:SAWTOOTH }

	replace Function of String is name(){ SynthStrings:WAVE_SAWTOOTH }

	replace Function of InstrumentVoice is createVoice(Int is midi, Float is freqHz, Int is sampleRate){
		SawtoothVoice(midi: midi, step: freqHz / toFloat(value: sampleRate), initialEnv: 0.0)
	}
}
