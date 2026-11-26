#! Package base:sew
#! Vertical flexible split-grid container with movable dividers and per-panel min/max constraints.

Class of FlexGridBase is FlexGridV{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', FlexGridBase],
		['base', 'sew', FlexGridPanel]
	];

	replace Function is init(
		Array of FlexGridPanel is panels: Array(),
		Float is spacingPt: 4.0,
		Boolean is movable: true
	){
		:panels: panels;
		:spacingPt: spacingPt;
		:movable: movable;
		:horizontal: false;
	}
}
