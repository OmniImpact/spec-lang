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

	## Returns true when ([px], [py]) lies within this rectangle.
	Function of Boolean is contains(Int is px, Int is py){
		return px >= x && px < x + width && py >= y && py < y + height;
	}
}
