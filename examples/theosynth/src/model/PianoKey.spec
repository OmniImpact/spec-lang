#! Package theosynth:model
#! Metadata for a single piano key mapped to a computer keyboard character and MIDI pitch.

Class is PianoKey{
	replace [String] is namespace: ['theosynth', 'model'];

	Int is midi: 60;
	String is noteName: 'C4';
	String is keyChar: 'q';
	Boolean is isSharp: false;
	Int is octaveRow: 1;
	Int is semitoneCol: 0;

	replace Function is init(
		Int is midi,
		String is noteName,
		String is keyChar,
		Boolean is isSharp,
		Int is octaveRow,
		Int is semitoneCol
	){
		:midi: midi;
		:noteName: noteName;
		:keyChar: keyChar;
		:isSharp: isSharp;
		:octaveRow: octaveRow;
		:semitoneCol: semitoneCol;
	}
}
