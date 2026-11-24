#! Package theosynth:model:instruments
#! Pure sine-wave oscillator voice.

Class of InstrumentVoice is SineVoice{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', InstrumentVoice],
		['base', 'math', as Math()]
	];

	replace Function of Float is nextSample(){
		local Float is out: sin(value: 6.283185307179586 * phase);
		phase: phase + step;
		if({ phase >= 1.0 }, { phase: phase - 1.0; });
		return out;
	}
}
