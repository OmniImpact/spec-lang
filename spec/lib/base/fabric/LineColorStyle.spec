#! Package base:fabric
#! Reusable line-color style component.

Class is LineColorStyle{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Color]
	];

	Color is lineColor: Color(r: 120, g: 130, b: 150);
	Boolean is hasColor: false;

	replace Function is init(Color is color: Color(r: 0, g: 0, b: 0, a: 0), Boolean is hasColor: false){
		if({ hasColor || color:alpha() > 0 }, {
			:lineColor: color;
			:hasColor: true;
		}, {
			:lineColor: Color(r: 120, g: 130, b: 150);
			:hasColor: false;
		});
	}
}
