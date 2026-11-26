#! Package base:sew
#! Resolution-independent point (pt) <-> physical pixel (px) conversion helpers.

Class is Scale{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'math', Math]
	];

	Float is factor: 1.0;

	replace Function is init(Float is factor: 1.0){
		:factor: if({ factor > 0.0 }, { factor }, { 1.0 });
	}

	## Converts logical points ([pt]) to rounded physical pixels.
	Function of Int is px(Float is pt){
		local Math is math: Math();
		local Float is v: math:round(value: pt * factor);
		return math:toInt(value: v);
	}

	## Converts physical pixels ([px]) to logical points.
	Function of Float is pt(Int is px){
		local Math is math: Math();
		return math:toFloat(value: px) / factor;
	}
}
