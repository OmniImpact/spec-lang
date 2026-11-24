#! Package base:theo
#! One fixed-size or weight-based pane inside a [Grid].

Class is GridPane{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', Widget]
	];

	Boolean is isFixed: true;
	Int is fixedSize: 1;
	Float is weightVal: 1.0;
	Widget is child;

	replace Function is init(Boolean is isFixed, Int is fixedSize, Float is weightVal, Widget is child){
		:isFixed: isFixed;
		:fixedSize: fixedSize;
		:weightVal: weightVal;
		:child: child;
	}
}
