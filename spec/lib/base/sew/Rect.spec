#! Package base:sew
#! 2D integer rectangle assigned during `SewNode:arrange`.

Class is Rect{
	replace [String] is namespace: ['base', 'sew'];

	Int is x: 0;
	Int is y: 0;
	Int is width: 0;
	Int is height: 0;

	replace Function is init(Int is x: 0, Int is y: 0, Int is width: 0, Int is height: 0){
		:x: x;
		:y: y;
		:width: width;
		:height: height;
	}
}
