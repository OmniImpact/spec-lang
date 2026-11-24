#! Package theosynth:model:instruments
#! Karplus-Strong plucked-string instrument.

Class of Instrument is PluckInstrument{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', [Instrument, InstrumentVoice, Waveform]],
		['theosynth', 'model', 'instruments', PluckVoice],
		['theosynth', 'util', SynthStrings],
		['base', 'math', [as Math(), Vector]],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	Int is seed: 1337;

	replace Function of Waveform is waveform(){ Waveform:PLUCK }

	replace Function of String is name(){ SynthStrings:WAVE_PLUCK }

	Function of Vector is makeNoiseDelayLine(Float is freqHz, Int is rate){
		local Int is delayLen: toInt(value: round(value: toFloat(value: rate) / freqHz));
		if({ delayLen < 2 }, { delayLen: 2; });
		local Vector is dl: Vector(length: delayLen);
		local Int is i: 0;
		while({ i < delayLen }, {
			seed: (seed * 1103515245 + 12345) % 2147483647;
			if({ seed < 0 }, { seed: -seed; });
			local Float is n: (toFloat(value: seed % 20001) / 10000.0) - 1.0;
			dl:set(index: i, value: n);
			i: i + 1;
		});
		return dl;
	}

	replace Function of InstrumentVoice is createVoice(Int is midi, Float is freqHz, Int is sampleRate){
		PluckVoice(midi: midi, dl: makeNoiseDelayLine(freqHz: freqHz, rate: sampleRate))
	}
}
