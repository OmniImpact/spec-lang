#! Package base:sew
#! Panel descriptor for [FlexGridH] and [FlexGridV] with size, flex, and min/max constraints.

Class is FlexGridPanel{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sew', SewNode]
	];

	SewNode is child: SewNode();
	Float is sizePt: 0.0;
	Float is minSizePt: 40.0;
	Float is maxSizePt: 0.0;
	Boolean is flex: true;
	Boolean is visible: true;

	replace Function is init(
		SewNode is child: SewNode(),
		Float is sizePt: 0.0,
		Float is minSizePt: 40.0,
		Float is maxSizePt: 0.0,
		Boolean is flex: true,
		Boolean is visible: true
	){
		:child: child;
		:sizePt: sizePt;
		:minSizePt: minSizePt;
		:maxSizePt: maxSizePt;
		:flex: flex;
		:visible: visible;
	}
}
