#! Package base:theo
#! When a [Panel] scrollbar is shown.

Enum of String is ScrollbarMode {
	replace [String] is namespace: ['base', 'theo'];
	NEVER: 'never',
	AUTO: 'auto',
	ALWAYS: 'always'
}
