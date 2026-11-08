#! N25 (FUNCTIONS.md Part IV IV.2c): same-named inner classes under
#! different enclosing classes are legal declarations — the ambiguity
#! moved to the reference. A bare reference to a nested-class name that
#! more than one as-import provides names the providers; the user
#! qualifies the reference (LibA:Helper).

Class is N25Consume{
	replace Array of Array of String is using: [
		['wallprobe', 'liba', as LibA()],
		['wallprobe', 'libb', as LibB()]
	];

	replace Function is init(Map of String to String is args){
		local Helper is h: LibA:Helper:init();
		Output:line((h:value() as String));
	}
}