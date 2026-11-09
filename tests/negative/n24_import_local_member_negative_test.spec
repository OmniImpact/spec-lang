#! N24 (Part IV IV.1): the as-import grants functions under the
#! callee's visibility — a `local` member of the imported class is not
#! callable through the import. The same check the qualified path runs.


Class is WallProbe{
	replace Array of Array of String is using: [
		['instimport', 'counter', as StatefulCounter(label: 'w')],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local Int is x: hidden(1) + 0;
		Output:line(x as String);
	}
}
