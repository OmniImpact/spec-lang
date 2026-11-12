#! specunit: negative
#! expect: 'Math2' is not imported by 'N29AsFormDefault'; add it to the using declaration to construct it

#! N29 (Part IV IV.6): the declaration-side default is
#! construction the declaring class bakes in — it gates against the
#! declaring class's imports. An as-imported type cannot be the default
#! of a parameter (a single-class file: the file grant does not rescue
#! a sibling's plain import).

Class is N29AsFormDefault{
	replace Array of Array of String is using: [
		['dimath', as Math2()],
		['base', 'sys', as Output()]
	];

	replace Function is init(Math2 is m : Math2:init()){
		Output:line((m:half(10)) as String);
	}
}
