#! Package theosynth:model:instruments
#! Sawtooth-wave oscillator voice.

Class of InstrumentVoice is SawtoothVoice{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', InstrumentVoice],
		['base', 'sys', as Conditional()]
	];

	replace Function of Float is nextSample(){
		local Float is out: 2.0 * phase - 1.0;
		phase: phase + step;
		if({ phase >= 1.0 }, { phase: phase - 1.0; });
		return out;
	}
}
