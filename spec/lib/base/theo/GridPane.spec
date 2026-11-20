#! Package base:theo
#! One fixed-size or weight-based pane inside a [Grid].

Class is GridPane{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
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
