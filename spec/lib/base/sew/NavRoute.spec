#! Package base:sew
#! Named route entry pairing a route identifier with a child `SewNode` inside a `NavStack`.

Class is NavRoute{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sew', SewNode]
	];

	String is name: '';
	SewNode is child: SewNode();

	replace Function is init(String is name: '', SewNode is child: SewNode()){
		:name: name;
		:child: child;
	}
}
