#! Package base:fabric
#! Reusable line-width style component in logical points (pt).

Class is LineWidthStyle{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];

	Float is widthPt: 0.7;
	Boolean is hasWidth: false;

	replace Function is init(Float is widthPt: -1.0){
		if({ widthPt >= 0.0 }, {
			:widthPt: widthPt;
			:hasWidth: true;
		}, {
			:widthPt: 0.7;
			:hasWidth: false;
		});
	}

	Function of Float is getWidthPt(){ return widthPt; }
	Function of Boolean is isWidthSet(){ return hasWidth; }
}
