#! Package base:fabric:svg
#! Parsed vector shape primitive inside an [SvgDoc].

Class is SvgShape{
	replace [String] is namespace: ['base', 'fabric', 'svg'];

	replace [[String]] is using: [
		['base', 'struct', Array]
	];

	Array of Float is xs: Array();
	Array of Float is ys: Array();
	Boolean is closed: false;
	Boolean is hasFill: false;
	Int is fillColor: 0;
	Boolean is hasStroke: false;
	Int is strokeColor: 0;
	Float is strokeWidth: 1.5;

	replace Function is init(
		Array of Float is xs: Array(),
		Array of Float is ys: Array(),
		Boolean is closed: false,
		Boolean is hasFill: false,
		Int is fillColor: 0,
		Boolean is hasStroke: false,
		Int is strokeColor: 0,
		Float is strokeWidth: 1.5
	){
		:xs: xs;
		:ys: ys;
		:closed: closed;
		:hasFill: hasFill;
		:fillColor: fillColor;
		:hasStroke: hasStroke;
		:strokeColor: strokeColor;
		:strokeWidth: strokeWidth;
	}
}
