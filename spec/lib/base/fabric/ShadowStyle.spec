#! Package base:fabric
#! Reusable drop-shadow or inner-shadow style configuration in logical points (pt).

Class is ShadowStyle{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Color]
	];

	Float is blurPt: 0.0;
	Float is offsetXPt: 0.0;
	Float is offsetYPt: 0.0;
	Color is shadowColor: Color(r: 0, g: 0, b: 0, a: 85);
	Boolean is inset: false;
	Boolean is specified: true;

	replace Function is init(
		Float is blurPt: 0.0,
		Float is offsetXPt: 0.0,
		Float is offsetYPt: 0.0,
		Color is color: Color(r: 0, g: 0, b: 0, a: 85),
		Boolean is inset: false,
		Boolean is specified: true
	){
		:blurPt: if({ blurPt < 0.0 }, { 0.0 }, { blurPt });
		:offsetXPt: offsetXPt;
		:offsetYPt: offsetYPt;
		:shadowColor: color;
		:inset: inset;
		:specified: specified;
	}

	Function of Boolean is isActive(){
		return blurPt > 0.0 || offsetXPt != 0.0 || offsetYPt != 0.0;
	}
}
