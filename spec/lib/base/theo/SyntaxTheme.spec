#! Package base:theo
#! Configurable syntax-highlighting color palette (defaulting to warm light-brown, amber, and orange tones).

Class is SyntaxTheme{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', TheoColor]
	];

	TheoColor is plain: TheoColor:ansi(code: 252);
	TheoColor is keyword: TheoColor:ansi(code: 208);
	TheoColor is type: TheoColor:ansi(code: 214);
	TheoColor is string: TheoColor:ansi(code: 180);
	TheoColor is number: TheoColor:ansi(code: 215);
	TheoColor is comment: TheoColor:ansi(code: 137);
	TheoColor is punctuation: TheoColor:ansi(code: 245);
	TheoColor is heading: TheoColor:ansi(code: 209);
	TheoColor is key: TheoColor:ansi(code: 179);
	TheoColor is boolean: TheoColor:ansi(code: 202);

	replace Function is init(
		TheoColor is plain: TheoColor:ansi(code: 252),
		TheoColor is keyword: TheoColor:ansi(code: 208),
		TheoColor is type: TheoColor:ansi(code: 214),
		TheoColor is string: TheoColor:ansi(code: 180),
		TheoColor is number: TheoColor:ansi(code: 215),
		TheoColor is comment: TheoColor:ansi(code: 137),
		TheoColor is punctuation: TheoColor:ansi(code: 245),
		TheoColor is heading: TheoColor:ansi(code: 209),
		TheoColor is key: TheoColor:ansi(code: 179),
		TheoColor is boolean: TheoColor:ansi(code: 202)
	){
		:plain: plain;
		:keyword: keyword;
		:type: type;
		:string: string;
		:number: number;
		:comment: comment;
		:punctuation: punctuation;
		:heading: heading;
		:key: key;
		:boolean: boolean;
	}
}