#! Package theosynth:model:instruments
#! Square-wave oscillator voice.

Class of InstrumentVoice is SquareVoice{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', InstrumentVoice],
		['base', 'sys', as Conditional()]
	];

	replace Function of Float is nextSample(){
		local Float is out: if({ phase < 0.5 }, { 1.0 }, { -1.0 });
		phase: phase + step;
		if({ phase >= 1.0 }, { phase: phase - 1.0; });
		return out;
	}
}
