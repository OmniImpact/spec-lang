#! Package theosynth:vm
#! ViewModel managing the 3-octave keyboard map, active waveform, key press/release state, About modal, and audio.

Class is SynthViewModel{
	replace [String] is namespace: ['theosynth', 'vm'];

	merge [[String]] is using: [
		['theosynth', 'model', [Waveform, PianoKey, SynthEngine]],
		['theosynth', 'util', SynthStrings],
		['base', 'sys', [as Conditional(), as Loops()]],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'struct', Map]
	];

	Array of PianoKey is keys: Array();
	Map of String to Int is keyIndexByChar: Map();
	[Int] is activeTicks: [];
	[Int] is heldFlags: [];
	[Int] is fallbackTicks: [];

	Waveform is selectedWaveform: Waveform:SINE;
	Int is lastPlayedIdx: -1;
	Boolean is aboutOpen: false;
	Boolean is audioEnabled: true;

	Function is onStateChanged: {};
	Function is onAboutChanged: {};
	Function is onQuit: {};

	SynthEngine is engine: SynthEngine();

	replace Function is init(Function is onQuit: {}, Boolean is audioEnabled: true){
		:onQuit: onQuit;
		:audioEnabled: audioEnabled;
		buildKeyboard();
	}

	Function is startAudio(ThreadScope is scope){
		if({ audioEnabled }, {
			engine:startAudio(scope: scope);
		});
	}

	local Function is buildOctave(Int is row, Int is baseMidi, String is octStr, [String] is chars){
		local [String] is noteNames: ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
		local [Boolean] is sharps: [false, true, false, true, false, false, true, false, true, false, true, false];
		local Int is col: 0;
		while({ col < 12 }, {
			local String is ch: chars:get(index: col);
			local String is name: "{{noteNames:get(index: col)}}{{octStr}}";
			local Int is idx: keys:length();
			keys:add(item: PianoKey(
				midi: baseMidi + col,
				noteName: name,
				keyChar: ch,
				isSharp: sharps:get(index: col),
				octaveRow: row,
				semitoneCol: col
			));
			keyIndexByChar:set(key: ch, value: idx);
			activeTicks:push(item: 0);
			heldFlags:push(item: 0);
			fallbackTicks:push(item: 0);
			col: col + 1;
		});
	}

	local Function is buildKeyboard(){
		keys: Array();
		keyIndexByChar: Map();
		activeTicks: [];
		heldFlags: [];
		fallbackTicks: [];
		buildOctave(row: 0, baseMidi: 72, octStr: '5', chars: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=']);
		buildOctave(row: 1, baseMidi: 60, octStr: '4', chars: ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']']);
		buildOctave(row: 2, baseMidi: 48, octStr: '3', chars: ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '\\']);
	}

	Function is selectInstrument(String is name){
		if({ name == SynthStrings:WAVE_SQUARE }, {
			selectedWaveform: Waveform:SQUARE;
		}, {
			if({ name == SynthStrings:WAVE_SAWTOOTH }, {
				selectedWaveform: Waveform:SAWTOOTH;
			}, {
				selectedWaveform: Waveform:SINE;
			});
		});
		onStateChanged();
	}

	Function of String is selectedInstrumentName(){
		if({ selectedWaveform == Waveform:SQUARE }, { return SynthStrings:WAVE_SQUARE; });
		if({ selectedWaveform == Waveform:SAWTOOTH }, { return SynthStrings:WAVE_SAWTOOTH; });
		return SynthStrings:WAVE_SINE;
	}

	Function of String is lastNoteLabel(){
		if({ lastPlayedIdx < 0 || lastPlayedIdx >= keys:length() }, { return 'Ready'; });
		local PianoKey is k: keys:get(index: lastPlayedIdx);
		return "{{k:noteName}} ({{k:keyChar}}) · {{selectedInstrumentName()}}";
	}

	## Triggers a note on key press (or mouse click with short auto-release).
	Function is triggerKeyIndex(Int is idx, Boolean is autoRelease: true){
		if({ idx < 0 || idx >= keys:length() }, { return; });
		lastPlayedIdx: idx;
		heldFlags:set(index: idx, item: 1);
		activeTicks:set(index: idx, item: 1);
		fallbackTicks:set(index: idx, item: if({ autoRelease }, { 12 }, { 24 }));
		onStateChanged();
		if({ audioEnabled }, {
			engine:noteOn(midi: keys:get(index: idx):midi, wave: selectedWaveform);
		});
	}

	## Releases a note immediately on key-up.
	Function is releaseKeyIndex(Int is idx){
		if({ idx < 0 || idx >= keys:length() }, { return; });
		if({ heldFlags:get(index: idx) == 0 && activeTicks:get(index: idx) == 0 }, { return; });
		heldFlags:set(index: idx, item: 0);
		activeTicks:set(index: idx, item: 0);
		fallbackTicks:set(index: idx, item: 0);
		onStateChanged();
		if({ audioEnabled }, {
			engine:noteOff(midi: keys:get(index: idx):midi);
		});
	}

	Function of Boolean is triggerChar(String is ch){
		if({ !keyIndexByChar:has(key: ch) }, { return false; });
		local Int is idx: keyIndexByChar:get(key: ch, default: -1);
		triggerKeyIndex(idx: idx, autoRelease: true);
		return true;
	}

	Function of Boolean is tickDecay(){
		local Boolean is changed: false;
		local Int is i: 0;
		while({ i < fallbackTicks:length() }, {
			local Int is ft: fallbackTicks:get(index: i);
			if({ ft > 0 }, {
				local Int is next: ft - 1;
				fallbackTicks:set(index: i, item: next);
				if({ next == 0 }, {
					heldFlags:set(index: i, item: 0);
					activeTicks:set(index: i, item: 0);
					if({ audioEnabled }, {
						engine:noteOff(midi: keys:get(index: i):midi);
					});
					changed: true;
				});
			});
			i: i + 1;
		});
		return changed;
	}

	Function is openAbout(){
		if({ aboutOpen }, { return; });
		aboutOpen: true;
		onAboutChanged();
	}

	Function is closeAbout(){
		if({ !aboutOpen }, { return; });
		aboutOpen: false;
		onAboutChanged();
	}

	Function is quit(){
		engine:close();
		onQuit();
	}

	Function of Boolean is handleKeyAction(String is key, Boolean is ctrl, Boolean is isPress, Boolean is isRepeat, Boolean is isRelease){
		if({ ctrl && (key == 'q' || key == 'Q') }, {
			if({ isPress }, { quit(); });
			return true;
		});
		if({ key == '?' }, {
			if({ isPress }, { openAbout(); });
			return true;
		});
		if({ !keyIndexByChar:has(key: key) }, { return false; });
		local Int is idx: keyIndexByChar:get(key: key, default: -1);
		if({ isRelease }, {
			releaseKeyIndex(idx: idx);
			return true;
		});
		if({ isRepeat }, {
			fallbackTicks:set(index: idx, item: 24);
			return true;
		});
		if({ isPress }, {
			if({ heldFlags:get(index: idx) == 0 }, {
				triggerKeyIndex(idx: idx, autoRelease: false);
			});
			return true;
		});
		return false;
	}
}
