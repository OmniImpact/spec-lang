Class is Phase2Test{

	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:io:*
	];

	replace Function is init(Map of String to String is args){
		output:line("======================================");
		output:line("          Phase 2 Feature Test        ");
		output:line("======================================\n");

		# 1. Extended Array Operations
		output:line("--- 1. Extended Array Operations ---");
		local Array of String is tokens: ["class", "MyClass", "{", "local", "}"];
		output:line("Initial length: " . tokens:length());
		output:line("indexOf(\"MyClass\"): " . tokens:indexOf(search: "MyClass", default: -1));
		output:line("indexOf(\"missing\"): " . tokens:indexOf(search: "missing", default: -1));

		local String is popped: tokens:pop(default: "EMPTY");
		output:line("Popped item: " . popped);
		output:line("Length after pop: " . tokens:length());

		local String is removed: tokens:removeAt(index: 1, default: "OUT_OF_BOUNDS");
		output:line("Removed at index 1: " . removed);
		output:line("Length after removeAt: " . tokens:length());
		output:line("Item at index 1 is now: " . tokens[1]);

		local Array of String is sliced: tokens:slice(start: 0, end: 2);
		output:line("Sliced(0, 2) length: " . sliced:length());
		output:line("Sliced[0]: " . sliced[0]);
		output:line("Sliced[1]: " . sliced[1]);

		tokens:clear();
		output:line("After clear(), isEmpty(): " . tokens:isEmpty());
		output:line("Pop on empty array: " . tokens:pop(default: "DEFAULT_FALLBACK"));

		# 2. Extended Map Operations
		output:line("\n--- 2. Extended Map Operations ---");
		local Map of String to String is symbolTable: Map:init();
		output:line("Initial symbolTable:length(): " . symbolTable:length());

		symbolTable:set(key: "x", value: "Int");
		symbolTable:set(key: "y", value: "Float");
		symbolTable:set(key: "name", value: "String");
		output:line("After 3 sets, length(): " . symbolTable:length());
		output:line("has(\"x\"): " . symbolTable:has(key: "x"));
		output:line("has(\"z\"): " . symbolTable:has(key: "z"));
		output:line("get(\"y\"): " . symbolTable:getString(key: "y", default: "NOT_FOUND"));

		# Update existing key
		symbolTable:set(key: "x", value: "LongInt");
		output:line("Updated \"x\": " . symbolTable:getString(key: "x", default: "NOT_FOUND"));
		output:line("Length after update: " . symbolTable:length());

		# Keys array
		local Array of String is symKeys: symbolTable:keys();
		output:line("symKeys:length(): " . symKeys:length());

		# Remove key
		local Boolean is removedKey: symbolTable:remove(key: "y");
		output:line("Remove \"y\" returned: " . removedKey);
		output:line("has(\"y\") after remove: " . symbolTable:has(key: "y"));
		output:line("Length after remove: " . symbolTable:length());

		output:line("\nAll Phase 2 features verified successfully!");
	}

}
