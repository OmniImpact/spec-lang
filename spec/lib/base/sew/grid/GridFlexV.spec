#! Package base:sew
#! Vertical flexible split-grid container with movable dividers and per-panel min/max constraints.

Class of GridFlex is GridFlexV{
	replace [String] is namespace: ['base', 'sew', 'grid'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', 'grid', GridFlex],
		['base', 'sew', 'grid', GridFlexPanel]
	];

	replace Function is init(
		Array of GridFlexPanel is panels: Array(),
		Float is spacingPt: 0.0,
		Boolean is movable: true
	){
		:panels: panels;
		:spacingPt: spacingPt;
		:movable: movable;
		:horizontal: false;
	}
}
