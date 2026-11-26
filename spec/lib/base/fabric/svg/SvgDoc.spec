#! Package base:fabric:svg
#! Parsed SVG document containing viewBox dimensions and [SvgShape] primitives.

Class is SvgDoc{
	replace [String] is namespace: ['base', 'fabric', 'svg'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'fabric', 'svg', SvgShape]
	];

	Float is viewX: 0.0;
	Float is viewY: 0.0;
	Float is viewW: 24.0;
	Float is viewH: 24.0;
	Array of SvgShape is shapes: Array();

	replace Function is init(
		Float is viewX: 0.0,
		Float is viewY: 0.0,
		Float is viewW: 24.0,
		Float is viewH: 24.0,
		Array of SvgShape is shapes: Array()
	){
		:viewX: viewX;
		:viewY: viewY;
		:viewW: viewW;
		:viewH: viewH;
		:shapes: shapes;
	}
}
