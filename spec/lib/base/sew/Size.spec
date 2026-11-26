#! Package base:sew
#! 2D integer size returned by `SewNode:measure`.

Class is Size{
	replace [String] is namespace: ['base', 'sew'];

	Int is width: 0;
	Int is height: 0;

	replace Function is init(Int is width: 0, Int is height: 0){
		:width: width;
		:height: height;
	}
}
