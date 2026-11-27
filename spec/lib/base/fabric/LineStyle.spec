#! Package base:fabric
#! Composable line style inheriting [LineWidthStyle] and [LineColorStyle] plus stroke style (single/double/bevel/groove/inset/outset/none).

Class of LineWidthStyle, LineColorStyle is LineStyle{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Color],
		['base', 'fabric', LineWidthStyle],
		['base', 'fabric', LineColorStyle]
	];

	String is style: 'single';
	Boolean is hasStyle: false;

	replace Function is init(
		Float is widthPt: -1.0,
		Color is color: Color(r: 0, g: 0, b: 0, a: 0),
		String is style: ''
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
		if({ style != '' }, {
			:style: style;
			:hasStyle: true;
		}, {
			:style: 'single';
			:hasStyle: false;
		});
	}
}
