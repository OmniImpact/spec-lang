#! Package base:fabric
#! Composable line style (width, color, stroke style: single/double/bevel/groove/inset/outset/none).

Class is LineStyle{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Color],
		['base', 'fabric', StrokeStyle]
	];

	Float is widthPt: 0.7;
	Boolean is hasWidth: false;
	Color is lineColor: Color(r: 120, g: 130, b: 150);
	Boolean is hasColor: false;
	StrokeStyle is style: StrokeStyle:SINGLE;
	Boolean is hasStyle: false;

	replace Function is init(
		Float is widthPt: -1.0,
		Color is color: Color(r: 0, g: 0, b: 0, a: 0),
		StrokeStyle is style: StrokeStyle:SINGLE,
		Boolean is hasStyle: false
	){
		if({ widthPt >= 0.0 }, {
			:widthPt: widthPt;
			:hasWidth: true;
		}, {
			:widthPt: 0.7;
			:hasWidth: false;
		});
		if({ color:alpha() > 0 }, {
			:lineColor: color;
			:hasColor: true;
		}, {
			:lineColor: Color(r: 120, g: 130, b: 150);
			:hasColor: false;
		});
		:style: style;
		:hasStyle: hasStyle || style != StrokeStyle:SINGLE;
	}

	Function of Float is getWidthPt(){
		return :widthPt;
	}
	Function of Boolean is isWidthSet(){
		return :hasWidth;
	}
	Function of Color is getLineColor(){
		return :lineColor;
	}
	Function of Boolean is isColorSet(){
		return :hasColor;
	}
}
