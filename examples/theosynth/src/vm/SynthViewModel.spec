#! Package theosynth:vm
#! ViewModel managing the 3-octave keyboard map, active waveform, key highlights, About modal, and audio playback.

Class is SynthViewModel{
	replace [String] is namespace: ['theosynth', 'vm'];

	merge [[String]] is using: [
		['theosynth', 'model', [Waveform, PianoKey, SynthEngine]],
		['theosynth', 'util', SynthStrings],
		['base', 'sys', [as Conditional(), as Loops()]],
		['base', 'struct', Map]
	];

	Array of PianoKey is keys: Array();
	Map of String to Int is keyIndexByChar: Map();
	[Int] is activeTicks: [];

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
			col: col + 1;
		});
	}

	local Function is buildKeyboard(){
		keys: Array();
		keyIndexByChar: Map();
		activeTicks: [];
		# Row 0: Octave 5 (MIDI 72..83) -> 1 2 3 4 5 6 7 8 9 0 - =
		buildOctave(row: 0, baseMidi: 72, octStr: '5', chars: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=']);
		# Row 1: Octave 4 (MIDI 60..71) -> q w e r t y u i o p [ ]
		buildOctave(row: 1, baseMidi: 60, octStr: '4', chars: ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']']);
		# Row 2: Octave 3 (MIDI 48..59) -> a s d f g h j k l ; ' backslash
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

	Function is triggerKeyIndex(Int is idx){
		if({ idx < 0 || idx >= keys:length() }, { return; });
		lastPlayedIdx: idx;
		activeTicks:set(index: idx, item: 8);
		onStateChanged();
		if({ audioEnabled }, {
			engine:playMidi(midi: keys:get(index: idx):midi, wave: selectedWaveform);
		});
	}

	Function of Boolean is triggerChar(String is ch){
		if({ !keyIndexByChar:has(key: ch) }, { return false; });
		triggerKeyIndex(idx: keyIndexByChar:get(key: ch, default: -1));
		return true;
	}

	Function of Boolean is tickDecay(){
		local Boolean is changed: false;
		local Int is i: 0;
		while({ i < activeTicks:length() }, {
			local Int is t: activeTicks:get(index: i);
			if({ t > 0 }, {
				activeTicks:set(index: i, item: t - 1);
				changed: true;
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

	Function of Boolean is handleShortcut(String is key, Boolean is ctrl){
		if({ ctrl && (key == 'q' || key == 'Q') }, {
			quit();
			return true;
		});
		if({ key == '?' }, {
			openAbout();
			return true;
		});
		return triggerChar(ch: key);
	}
}
