#! Package theosynth:util
#! Shared UI strings, labels, and About text for TheoSynth.

Class is SynthStrings{
	replace [String] is namespace: ['theosynth', 'util'];

	held String is APP_TITLE: 'TheoSynth';
	held String is ACTION_QUIT: 'Quit';
	held String is ACTION_ABOUT: 'About';
	held String is ACTION_CLOSE: 'Close';
	held String is LABEL_INSTRUMENT: 'Instrument:';

	held String is WAVE_SINE: 'Sine';
	held String is WAVE_SQUARE: 'Square';
	held String is WAVE_SAWTOOTH: 'Sawtooth';
	held String is WAVE_PLUCK: 'Pluck';

	held String is ABOUT_TITLE: ' About TheoSynth ';
	held String is ABOUT_BODY_1: 'Interactive 3-octave white-key synthesizer built in Spec + Theo.';
	held String is ABOUT_BODY_2: 'Row 1 (Oct 5): q w e r t y u  (C5 - B5)';
	held String is ABOUT_BODY_3: 'Row 2 (Oct 4): a s d f g h j  (C4 - B4)';
	held String is ABOUT_BODY_4: 'Row 3 (Oct 3): z x c v b n m  (C3 - B3)';
	held String is ABOUT_KEYS: 'Ctrl+P toggles Play Mode / Controls. Ctrl+A or ? About. Ctrl+Q quits.';

	held Function of [String] is instrumentOptions(){
		[SynthStrings:WAVE_SINE, SynthStrings:WAVE_SQUARE, SynthStrings:WAVE_SAWTOOTH, SynthStrings:WAVE_PLUCK]
	}
}
