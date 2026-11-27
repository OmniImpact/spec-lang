#! Package base:sew
#! Horizontal flow layout container wrapping children into rows left-to-right, top-to-bottom.

Class of Flow is FlowH{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Flow]
	];

	replace Function is init(
		Array of SewNode is children: Array(),
		Float is gapPt: 6.0,
		Float is lineGapPt: 6.0,
		Float is minItemPt: 0.0,
		Float is maxItemPt: 0.0,
		Float is maxLinePt: 0.0,
		Boolean is fill: false,
		Boolean is stretchCross: false
	){
		:children: children;
		:horizontal: true;
		:gapPt: gapPt;
		:lineGapPt: lineGapPt;
		:minItemPt: minItemPt;
		:maxItemPt: maxItemPt;
		:maxLinePt: maxLinePt;
		:fill: fill;
		:stretchCross: stretchCross;
	}
}
