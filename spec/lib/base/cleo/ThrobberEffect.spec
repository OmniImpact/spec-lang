#! Package base:cleo
#! Animation effect modes for Cleo throbbers.

Enum of String is ThrobberEffect {
	replace [String] is namespace: ['base', 'cleo'];
	SPIN: 'SPIN',
	BLINK: 'BLINK',
	COLOR_CYCLE: 'COLOR_CYCLE',
	BLINK_AND_COLOR: 'BLINK_AND_COLOR'
}
