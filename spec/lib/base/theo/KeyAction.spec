#! Package base:theo
#! Key event phase (press, repeat, or release) for [KeyEvent].

Enum of String is KeyAction {
	replace [String] is namespace: ['base', 'theo'];
	PRESS: 'press',
	REPEAT: 'repeat',
	RELEASE: 'release'
}
