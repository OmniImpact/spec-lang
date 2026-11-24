#! Package theosynth:model:instruments
#! Acoustic hammer-struck piano instrument built on dual-string Karplus-Strong with felt-hammer & soundboard filtering.

Class of Instrument is PianoInstrument{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', [Instrument, InstrumentVoice, Waveform]],
		['theosynth', 'model', 'instruments', [PianoVoice, PluckInstrument]],
		['theosynth', 'util', SynthStrings],
		['base', 'math', [as Math(), Vector]],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	PluckInstrument is pluckBase: PluckInstrument();

	replace Function of Waveform is waveform(){ Waveform:PIANO }

	replace Function of String is name(){ SynthStrings:WAVE_PIANO }

	local Function of Vector is makeHammerDelayLine(Float is freqHz, Int is rate){
		local Vector is dl: pluckBase:makeNoiseDelayLine(freqHz: freqHz, rate: rate);
		local Int is dLen: dl:length();
		local Int is pass: 0;
		while({ pass < 6 }, {
			local Float is prev: dl:get(index: dLen - 1);
			local Int is i: 0;
			while({ i < dLen }, {
				local Float is cur: dl:get(index: i);
				dl:set(index: i, value: 0.5 * (cur + prev));
				prev: cur;
				i: i + 1;
			});
			pass: pass + 1;
		});
		local Float is twoPi: 6.283185307179586;
		local Int is j: 0;
		while({ j < dLen }, {
			local Float is ph: twoPi * toFloat(value: j) / toFloat(value: dLen);
			local Float is harm: 0.62 * sin(value: ph) + 0.26 * sin(value: 2.0 * ph) + 0.12 * sin(value: 3.0 * ph);
			dl:set(index: j, value: 0.90 * harm + 0.10 * dl:get(index: j));
			j: j + 1;
		});
		return dl;
	}

	replace Function of InstrumentVoice is createVoice(Int is midi, Float is freqHz, Int is sampleRate){
		local Vector is dl1: makeHammerDelayLine(freqHz: freqHz, rate: sampleRate);
		local Vector is dl2: makeHammerDelayLine(freqHz: freqHz * 1.0022, rate: sampleRate);
		return PianoVoice(midi: midi, dl1: dl1, dl2: dl2);
	}
}
