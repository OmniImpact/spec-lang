#! N26 (FUNCTIONS.md Part IV IV.6): the as-import grants FUNCTIONS ONLY —
#! a public FIELD of the imported class is not reachable through the
#! class-name prefix. The field wall (INSTANCE.md §2.3).

Class is N26FieldWall{
	replace Array of Array of String is using: [
		['wallprobe', 'fielddep', as FieldDep()]
	];

	replace Function is init(Map of String to String is args){
		local String is v: FieldDep:secretField;
		Output:line(v);
	}
}
