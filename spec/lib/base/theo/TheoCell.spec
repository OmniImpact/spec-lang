#! Package base:theo
#! Single terminal character cell in a [TheoBuffer].

Class is TheoCell{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', TheoColor]
	];

	String is ch: ' ';
	TheoColor is fg: TheoColor:none();
	TheoColor is bg: TheoColor:none();
	Boolean is bold: false;
	Boolean is underline: false;
	Boolean is reverse: false;

	replace Function is init(){
	}
}
