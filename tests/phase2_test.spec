Class is Phase2Test{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('======================================');
		Output:line('          Phase 2 Feature Test        ');
		Output:line("======================================\n");

		# 1. Extended Array Operations
		Output:line('--- 1. Extended Array Operations ---');
		local Array of String is tokens: ['class', 'MyClass', '{', 'local', '}'];
		Output:line('Initial length: ' . tokens:length());
		Output:line('indexOf("MyClass"): ' . tokens:indexOf(search: 'MyClass', default: -1));
		Output:line('indexOf("missing"): ' . tokens:indexOf(search: 'missing', default: -1));

		local String is popped: tokens:pop(default: 'EMPTY');
		Output:line('Popped item: ' . popped);
		Output:line('Length after pop: ' . tokens:length());

		local String is removed: tokens:removeAt(index: 1, default: 'OUT_OF_BOUNDS');
		Output:line('Removed at index 1: ' . removed);
		Output:line('Length after removeAt: ' . tokens:length());
		Output:line('Item at index 1 is now: ' . tokens[1]);

		local Array of String is sliced: tokens:slice(start: 0, end: 2);
		Output:line('Sliced(0, 2) length: ' . sliced:length());
		Output:line('Sliced[0]: ' . sliced[0]);
		Output:line('Sliced[1]: ' . sliced[1]);

		tokens:clear();
		Output:line('After clear(), isEmpty(): ' . tokens:isEmpty());
		Output:line('Pop on empty array: ' . tokens:pop(default: 'DEFAULT_FALLBACK'));

		# 2. Extended Map Operations
		Output:line("\n--- 2. Extended Map Operations ---");
		local Map of String to String is symbolTable: Map:init();
		Output:line('Initial symbolTable:length(): ' . symbolTable:length());

		symbolTable:set(key: 'x', value: 'Int');
		symbolTable:set(key: 'y', value: 'Float');
		symbolTable:set(key: 'name', value: 'String');
		Output:line('After 3 sets, length(): ' . symbolTable:length());
		Output:line('has("x"): ' . symbolTable:has(key: 'x'));
		Output:line('has("z"): ' . symbolTable:has(key: 'z'));
		Output:line('get("y"): ' . symbolTable:getString(key: 'y', default: 'NOT_FOUND'));

		# Update existing key
		symbolTable:set(key: 'x', value: 'LongInt');
		Output:line('Updated "x": ' . symbolTable:getString(key: 'x', default: 'NOT_FOUND'));
		Output:line('Length after update: ' . symbolTable:length());

		# Keys array
		local Array of String is symKeys: symbolTable:keys();
		Output:line('symKeys:length(): ' . symKeys:length());

		# Remove key
		local Boolean is removedKey: symbolTable:remove(key: 'y');
		Output:line('Remove "y" returned: ' . removedKey);
		Output:line('has("y") after remove: ' . symbolTable:has(key: 'y'));
		Output:line('Length after remove: ' . symbolTable:length());

		Output:line("\nAll Phase 2 features verified successfully!");
	}

}
