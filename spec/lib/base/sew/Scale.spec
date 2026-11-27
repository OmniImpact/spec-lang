#! Package base:sew
#! Resolution-independent point (pt) <-> physical pixel (px) conversion helpers.

Class is Scale{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'math', Math]
	];

	held Math is sharedMath: Math();

	Float is factor: 1.0;

	replace Function is init(Float is factor: 1.0){
		:factor: if({ factor > 0.0 }, { factor }, { 1.0 });
	}

	## Converts logical points ([pt]) to rounded physical pixels.
	Function of Int is px(Float is pt){
		local Float is v: Scale:sharedMath:round(value: pt * factor);
		return Scale:sharedMath:toInt(value: v);
	}

	## Converts physical pixels ([px]) to logical points.
	Function of Float is pt(Int is px){
		return Scale:sharedMath:toFloat(value: px) / factor;
	}
}
