#! specunit: suite

Class of SpecUnitTest is TestTheoSynth{
	replace [String] is namespace: ['theosynth', 'tests'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'theo', '*'],
		['base', 'sys', as Loops()],
		['base', 'struct', List],
		['theosynth', 'model', [Waveform, PianoKey, SynthEngine]],
		['theosynth', 'util', SynthStrings],
		['theosynth', 'vm', SynthViewModel],
		['theosynth', 'view', SynthFrame]
	];

	Function is testWaveformsAndPcmSynthesis(){
		local SynthEngine is eng: SynthEngine();
		Assert:isTrue(eng:midiToFreq(midi: 69) > 439.9 && eng:midiToFreq(midi: 69) < 440.1);
		Assert:isTrue(eng:sampleWave(wave: Waveform:SQUARE, phase: 0.25) == 1.0);
		Assert:isTrue(eng:sampleWave(wave: Waveform:SQUARE, phase: 0.75) == -1.0);
		Assert:isTrue(eng:sampleWave(wave: Waveform:SAWTOOTH, phase: 0.5) == 0.0);

		local List of Byte is sinePcm: eng:synthesize(wave: Waveform:SINE, freqHz: 440.0, durationMs: 20, rate: 22050);
		local List of Byte is sqPcm: eng:synthesize(wave: Waveform:SQUARE, freqHz: 440.0, durationMs: 20, rate: 22050);
		local List of Byte is sawPcm: eng:synthesize(wave: Waveform:SAWTOOTH, freqHz: 440.0, durationMs: 20, rate: 22050);
		local List of Byte is pluckPcm: eng:synthesize(wave: Waveform:PLUCK, freqHz: 440.0, durationMs: 20, rate: 22050);
		Assert:isTrue(sinePcm:length() == 441 * 4);
		Assert:isTrue(sqPcm:length() == 441 * 4);
		Assert:isTrue(sawPcm:length() == 441 * 4);
		Assert:isTrue(pluckPcm:length() == 441 * 4);

		eng:noteOn(midi: 60, wave: Waveform:SINE);
		eng:noteOn(midi: 64, wave: Waveform:PLUCK);
		local List of Byte is polyPcm;
		eng:mixChunk(outBuf: polyPcm, frames: 220);
		Assert:isTrue(polyPcm:length() == 220 * 4);
		eng:noteOff(midi: 60);
		eng:noteOff(midi: 64);
	}

	Function is testThreeOctaveKeyboardLayoutAndTriggering(){
		local SynthViewModel is vm: SynthViewModel(audioEnabled: false);
		Assert:isTrue(vm:keys:length() == 21);
		Assert:isTrue(vm:selectedWaveform == Waveform:SINE);
		Assert:isTrue(vm:playMode);

		# Row 0 = Oct 5 ('q' -> C5 = MIDI 72)
		# Row 1 = Oct 4 ('a' -> C4 = MIDI 60)
		# Row 2 = Oct 3 ('z' -> C3 = MIDI 48)
		Assert:isTrue(vm:handleKeyAction(key: 'q', ctrl: false, isPress: true, isRepeat: false, isRelease: false));
		Assert:isTrue(vm:keys:get(index: vm:lastPlayedIdx):midi == 72);
		# Repeat while held is rejected without retriggering
		Assert:isTrue(vm:handleKeyAction(key: 'q', ctrl: false, isPress: false, isRepeat: true, isRelease: false));
		Assert:isTrue(vm:heldFlags:get(index: 0) == 1);
		Assert:isTrue(vm:handleKeyAction(key: 'a', ctrl: false, isPress: true, isRepeat: false, isRelease: false));
		Assert:isTrue(vm:keys:get(index: vm:lastPlayedIdx):midi == 60);
		Assert:isTrue(vm:handleKeyAction(key: 'z', ctrl: false, isPress: true, isRepeat: false, isRelease: false));
		Assert:isTrue(vm:keys:get(index: vm:lastPlayedIdx):midi == 48);

		vm:selectInstrument(name: SynthStrings:WAVE_SQUARE);
		Assert:isTrue(vm:selectedWaveform == Waveform:SQUARE);
		vm:selectInstrument(name: SynthStrings:WAVE_SAWTOOTH);
		Assert:isTrue(vm:selectedWaveform == Waveform:SAWTOOTH);
		vm:selectInstrument(name: SynthStrings:WAVE_PLUCK);
		Assert:isTrue(vm:selectedWaveform == Waveform:PLUCK);
	}

	Function is testFrameBottomBarAndHeadlessApp(){
		local Boolean is quitCalled: false;
		local SynthViewModel is vm: SynthViewModel(audioEnabled: false, onQuit: { quitCalled: true; });
		local SynthFrame is frame: SynthFrame(vm: vm);
		local TheoScreen is screen: TheoScreen(root: frame);
		local TheoApp is app: TheoApp();

		local [KeyEvent] is keys: [
			KeyEvent(kind: KeyKind:CHAR, key: 'a', action: KeyAction:PRESS),
			KeyEvent(kind: KeyKind:CHAR, key: 'a', action: KeyAction:RELEASE),
			KeyEvent(kind: KeyKind:CHAR, key: 's', action: KeyAction:PRESS),
			KeyEvent(kind: KeyKind:CHAR, key: 'p', ctrl: true, action: KeyAction:PRESS),
			KeyEvent(kind: KeyKind:CHAR, key: '?', action: KeyAction:PRESS),
			KeyEvent(kind: KeyKind:ESC),
			KeyEvent(kind: KeyKind:CHAR, key: 'q', ctrl: true)
		];
		local TheoBuffer is buf: app:runHeadless(screen: screen, keys: keys, width: 90, height: 24);
		Assert:isTrue(quitCalled);
		Assert:isTrue(vm:keys:get(index: vm:lastPlayedIdx):noteName == 'D4');
		Assert:isTrue(vm:heldFlags:get(index: 7) == 0);
		Assert:isTrue(vm:heldFlags:get(index: 8) == 0);
		Assert:isFalse(vm:playMode);
		Assert:isFalse(vm:aboutOpen);

		local String is row0: buf:rowText(y: 0);
		Assert:isTrue(row0:contains(needle: 'TheoSynth'));
		local String is botRow: buf:rowText(y: 22);
		Assert:isTrue(botRow:contains(needle: 'Quit'));
		Assert:isTrue(botRow:contains(needle: 'Instrument:'));
		Assert:isTrue(botRow:contains(needle: 'About'));
	}
}
