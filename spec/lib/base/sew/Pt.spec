#! Package base:sew
#! Point unit ([SuitUnit] implementation scaled by screen density and UI zoom).

Class of SuitUnit is Pt{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sew', SuitUnit],
		['base', 'sew', Scale]
	];

	Float is value: 0.0;

	replace Function is init(Float is value: 0.0){
		:value: value;
	}

	replace Function of Int is toPx(Scale is scale, Float is emPx: 12.0){
		return scale:px(pt: value);
	}
}