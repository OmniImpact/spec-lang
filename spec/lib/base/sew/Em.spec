#! Package base:sew
#! Typographic em unit ([SuitUnit] implementation relative to current theme font pixel size).

Class of SuitUnit is Em{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SuitUnit],
		['base', 'sew', Scale]
	];

	Float is value: 0.0;

	replace Function is init(Float is value: 0.0){
		:value: value;
	}

	replace Function of Int is toPx(Scale is scale, Float is emPx: 12.0){
		local Float is px: value * emPx;
		return if({ px >= 0.0 }, { (px + 0.5) as Int }, { (px - 0.5) as Int });
	}
}