#! Package theosynth:vm
#! ViewModel managing the 3-octave white-key letter-row map, Play Mode, key-down/up state, and polyphonic audio.

Class is SynthViewModel{
	replace [String] is namespace: ['theosynth', 'vm'];

	merge [[String]] is using: [
		['theosynth', 'model', [Waveform, PianoKey, Instrument, InstrumentRegistry, SynthEngine]],
		['base', 'sys', [as Conditional(), as Loops()]],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'struct', Map]
	];

	Array of PianoKey is keys: Array();
	Map of String to Int is keyIndexByChar: Map();
	[Int] is activeTicks: [];
	[Int] is heldFlags: [];
	[Int] is fallbackTicks: [];

	InstrumentRegistry is registry: InstrumentRegistry();
	Waveform is selectedWaveform: Waveform:SINE;
	Int is lastPlayedIdx: -1;
	Boolean is playMode: true;
	Boolean is seenKittyRelease: false;
	Boolean is aboutOpen: false;
	Boolean is audioEnabled: true;

	Function is onStateChanged: {};
	Function is onPlayModeChanged: {};
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
		local [String] is noteNames: ['C', 'D', 'E', 'F', 'G', 'A', 'B'];
		local [Int] is offsets: [0, 2, 4, 5, 7, 9, 11];
		local Int is col: 0;
		while({ col < 7 }, {
			local String is ch: chars:get(index: col);
			local String is name: "{{noteNames:get(index: col)}}{{octStr}}";
			local Int is idx: keys:length();
			keys:add(item: PianoKey(
				midi: baseMidi + offsets:get(index: col),
				noteName: name,
				keyChar: ch,
				isSharp: false,
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
		buildOctave(row: 0, baseMidi: 72, octStr: '5', chars: ['q', 'w', 'e', 'r', 't', 'y', 'u']);
		buildOctave(row: 1, baseMidi: 60, octStr: '4', chars: ['a', 's', 'd', 'f', 'g', 'h', 'j']);
		buildOctave(row: 2, baseMidi: 48, octStr: '3', chars: ['z', 'x', 'c', 'v', 'b', 'n', 'm']);
	}

	Function is setPlayMode(Boolean is enabled){
		if({ playMode == enabled }, { return; });
		:playMode: enabled;
		if({ !enabled }, {
			releaseAllKeys();
		});
		onPlayModeChanged();
		onStateChanged();
	}

	Function is togglePlayMode(){
		setPlayMode(enabled: !playMode);
	}

	Function of [String] is instrumentOptions(){ registry:optionNames() }

	Function is selectInstrument(String is name){
		local Instrument is inst: registry:findByName(name: name);
		selectedWaveform: inst:waveform();
		onStateChanged();
	}

	Function of String is selectedInstrumentName(){
		return registry:findByWaveform(wave: selectedWaveform):name();
	}

	Function of String is lastNoteLabel(){
		if({ lastPlayedIdx < 0 || lastPlayedIdx >= keys:length() }, { return 'Ready'; });
		local PianoKey is k: keys:get(index: lastPlayedIdx);
		return "{{k:noteName}} ({{k:keyChar}}) · {{selectedInstrumentName()}}";
	}

	## Triggers a note on key press (or mouse click with short auto-release, or held until explicit release).
	Function is triggerKeyIndex(Int is idx, Boolean is autoRelease: true, Boolean is holdUntilRelease: false){
		if({ idx < 0 || idx >= keys:length() }, { return; });
		lastPlayedIdx: idx;
		heldFlags:set(index: idx, item: 1);
		activeTicks:set(index: idx, item: 1);
		if({ holdUntilRelease }, {
			fallbackTicks:set(index: idx, item: 0);
		}, {
			if({ autoRelease }, {
				fallbackTicks:set(index: idx, item: 10);
			}, {
				fallbackTicks:set(index: idx, item: if({ seenKittyRelease }, { 0 }, { 10 }));
			});
		});
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

	Function is releaseAllKeys(){
		local Int is i: 0;
		while({ i < keys:length() }, {
			if({ heldFlags:get(index: i) == 1 }, {
				releaseKeyIndex(idx: i);
			});
			i: i + 1;
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
		if({ ctrl && (key == 'p' || key == 'P') }, {
			if({ isPress }, { togglePlayMode(); });
			return true;
		});
		if({ key == '?' }, {
			if({ isPress }, { openAbout(); });
			return true;
		});
		if({ !playMode }, { return false; });
		if({ !keyIndexByChar:has(key: key) }, { return false; });
		local Int is idx: keyIndexByChar:get(key: key, default: -1);
		if({ isRelease }, {
			seenKittyRelease: true;
			releaseKeyIndex(idx: idx);
			return true;
		});
		if({ isRepeat }, {
			# Reject key-repeat while already in key-down state.
			if({ heldFlags:get(index: idx) == 1 }, {
				if({ !seenKittyRelease }, {
					fallbackTicks:set(index: idx, item: 10);
				});
				return true;
			});
			return true;
		});
		if({ isPress }, {
			if({ !seenKittyRelease && heldFlags:get(index: idx) == 1 }, {
				# Non-Kitty OS key-repeat arrives as PRESS every ~30ms; sustain without re-plucking.
				fallbackTicks:set(index: idx, item: 10);
				return true;
			});
			triggerKeyIndex(idx: idx, autoRelease: false);
			return true;
		});
		return false;
	}
}
