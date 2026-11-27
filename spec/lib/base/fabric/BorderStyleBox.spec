#! Package base:fabric
#! Composable border & layer-effect style inheriting [LineStyle] (width, color, style) plus corner radius and outer/inner shadows.

Class of LineStyle is BorderStyleBox{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Color],
		['base', 'fabric', LineStyle],
		['base', 'fabric', ShadowStyle],
		['base', 'fabric', StrokeStyle]
	];

	Float is radiusPt: 0.0;
	Boolean is hasRadius: false;
	ShadowStyle is shadow: ShadowStyle(specified: false);
	Boolean is hasShadow: false;
	ShadowStyle is innerShadow: ShadowStyle(inset: true, specified: false);
	Boolean is hasInnerShadow: false;

	replace Function is init(
		Float is widthPt: -1.0,
		Color is color: Color(r: 0, g: 0, b: 0, a: 0),
		StrokeStyle is style: StrokeStyle:SINGLE,
		Boolean is hasStyle: false,
		Float is radiusPt: -1.0,
		ShadowStyle is shadow: ShadowStyle(specified: false),
		ShadowStyle is innerShadow: ShadowStyle(inset: true, specified: false)
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
		if({ radiusPt >= 0.0 }, {
			:radiusPt: radiusPt;
			:hasRadius: true;
		}, {
			:radiusPt: 0.0;
			:hasRadius: false;
		});
		:shadow: shadow;
		:hasShadow: shadow:specified || shadow:isActive();
		:innerShadow: innerShadow;
		:hasInnerShadow: innerShadow:specified || innerShadow:isActive();
	}
}
