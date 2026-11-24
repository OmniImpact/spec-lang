#! Package theosynth:model:instruments
#! Karplus-Strong plucked-string voice.

Class of InstrumentVoice is PluckVoice{
	replace [String] is namespace: ['theosynth', 'model', 'instruments'];

	merge [[String]] is using: [
		['theosynth', 'model', InstrumentVoice],
		['base', 'math', Vector],
		['base', 'sys', as Conditional()]
	];

	Vector is dl: Vector(length: 0);
	Int is pos: 0;
	Float is prev: 0.0;

	replace Function is init(Int is midi, Vector is dl){
		:midi: midi;
		:dl: dl;
		pos: 0;
		prev: if({ dl:length() > 0 }, { dl:get(index: dl:length() - 1) }, { 0.0 });
		env: 1.0;
		gate: 1;
		holdFrames: 660;
		relPending: 0;
	}

	replace Function of Float is nextSample(){
		local Int is dLen: dl:length();
		if({ dLen < 2 }, { return 0.0; });
		local Float is cur: dl:get(index: pos);
		dl:set(index: pos, value: 0.5 * (cur + prev) * 0.994);
		prev: cur;
		pos: pos + 1;
		if({ pos >= dLen }, { pos: 0; });
		return cur;
	}

	replace Function is destroy(){
		dl:destroy();
	}
}
