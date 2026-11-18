#! specunit: negative
#! expect: Members of 'Output' are callable only through an instance

#! Package transitive:use

Class is TransitiveUse{
	namespace: ['transitive', 'use'];

	replace Array of Array of String is using: [
		['transitive', 'dep', as TransitiveLib()]
	];

	replace Function is init(Map of String to String is args){
		local Int is t: triplify(4);
		Output:line(t as String);
	}
}
