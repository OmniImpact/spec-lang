#! Package base:theo
#! Kinds of decoded mouse input carried by [MouseEvent].

Enum of String is MouseKind {
	replace [String] is namespace: ['base', 'theo'];
	NONE: 'none',
	PRESS: 'press',
	RELEASE: 'release',
	MOVE: 'move',
	WHEEL_UP: 'wheelUp',
	WHEEL_DOWN: 'wheelDown'
}
