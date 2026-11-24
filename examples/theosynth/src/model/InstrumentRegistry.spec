#! Package theosynth:model
#! Registry of available [Instrument] implementations for TheoSynth.

Class is InstrumentRegistry{
	replace [String] is namespace: ['theosynth', 'model'];

	merge [[String]] is using: [
		['theosynth', 'model', [Instrument, Waveform]],
		['theosynth', 'model', 'instruments', [SineInstrument, SquareInstrument, SawtoothInstrument, PluckInstrument, PianoInstrument]],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	Array of Instrument is instruments: Array();

	replace Function is init(){
		instruments: Array([
			SineInstrument(),
			SquareInstrument(),
			SawtoothInstrument(),
			PluckInstrument(),
			PianoInstrument()
		]);
	}

	Function of [String] is optionNames(){
		local [String] is names: [];
		local Int is i: 0;
		while({ i < instruments:length() }, {
			names:push(item: instruments:get(index: i):name());
			i: i + 1;
		});
		return names;
	}

	Function of Instrument is findByName(String is name){
		local Int is i: 0;
		while({ i < instruments:length() }, {
			local Instrument is inst: instruments:get(index: i);
			if({ inst:name() == name }, { return inst; });
			i: i + 1;
		});
		return instruments:get(index: 0);
	}

	Function of Instrument is findByWaveform(Waveform is wave){
		local Int is i: 0;
		while({ i < instruments:length() }, {
			local Instrument is inst: instruments:get(index: i);
			if({ inst:waveform() == wave }, { return inst; });
			i: i + 1;
		});
		return instruments:get(index: 0);
	}
}
