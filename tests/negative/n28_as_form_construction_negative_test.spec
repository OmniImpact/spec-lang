#! N28 (Part IV IV.6): construction requires the plain
#! type-import form. The as-form grants functions, instance dispatch,
#! and the qualified nested-type references — never the bare parent
#! type reference, and with it never the construction.

Class is N28AsFormConstruction{
	replace Array of Array of String is using: [
		['dimath', as Math2()],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local Math2 is m: Math2:init();
		Output:line((m:half(10)) as String);
	}
}
