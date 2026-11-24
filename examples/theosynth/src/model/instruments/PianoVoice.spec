#! Package theosynth:model:instruments
#! Acoustic hammer-struck piano voice with dual-string Karplus-Strong waveguides.

Class of InstrumentVoice is PianoVoice{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', InstrumentVoice],
		['base', 'math', Vector],
		['base', 'sys', as Conditional()]
	];

	Vector is dl1: Vector(length: 0);
	Int is pos1: 0;
	Float is prev1: 0.0;
	Vector is dl2: Vector(length: 0);
	Int is pos2: 0;
	Float is prev2: 0.0;
	Float is body: 0.0;

	replace Function is init(Int is midi, Vector is dl1, Vector is dl2){
		:midi: midi;
		:dl1: dl1;
		pos1: 0;
		prev1: if({ dl1:length() > 0 }, { dl1:get(index: dl1:length() - 1) }, { 0.0 });
		:dl2: dl2;
		pos2: 0;
		prev2: if({ dl2:length() > 0 }, { dl2:get(index: dl2:length() - 1) }, { 0.0 });
		body: 0.0;
		env: 0.0;
		gate: 1;
		holdFrames: 660;
		relPending: 0;
	}

	replace Function of Float is nextSample(){
		local Int is dLen1: dl1:length();
		if({ dLen1 < 2 }, { return 0.0; });
		local Float is c1: dl1:get(index: pos1);
		dl1:set(index: pos1, value: 0.5 * (c1 + prev1) * 0.9996);
		prev1: c1;
		pos1: pos1 + 1;
		if({ pos1 >= dLen1 }, { pos1: 0; });

		local Float is sOut: c1;
		local Int is dLen2: dl2:length();
		if({ dLen2 >= 2 }, {
			local Float is c2: dl2:get(index: pos2);
			dl2:set(index: pos2, value: 0.5 * (c2 + prev2) * 0.9996);
			prev2: c2;
			pos2: pos2 + 1;
			if({ pos2 >= dLen2 }, { pos2: 0; });
			sOut: 0.5 * (c1 + c2);
		});
		body: body * 0.45 + sOut * 0.55;
		return body;
	}

	replace Function is destroy(){
		dl1:destroy();
		dl2:destroy();
	}
}
