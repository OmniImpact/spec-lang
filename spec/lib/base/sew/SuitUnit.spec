#! Package base:sew
#! Base unit abstraction for resolution-independent sizing (e.g. [Pt] and [Em]).

Class is SuitUnit{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sew', Scale]
	];

	## Converts this unit to physical pixels using [scale] and current em size [emPx].
	Function of Int is toPx(Scale is scale, Float is emPx: 12.0){
		return 0;
	}
}