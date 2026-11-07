Class is Phase6LoaderTest{

	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		spec:base:compiler:ast:ClassInfo,
		spec:base:compiler:lexer:Token,
		spec:base:compiler:lexer:Lexer,
		spec:base:compiler:parser:Parser,
		spec:base:compiler:loader:Loader
	];

	replace Function is init(Map of String to String is args){
		output:line('======================================');
		output:line('     Phase 6 Module Loader Test       ');
		output:line("======================================\n");

		local Loader is loader: Loader:init();

		# 1. Test Single File / Hello World
		output:line('1. Loading examples/helloworld.spec and its dependencies...');
		local ProgramNode is helloProg: loader:loadProgram(rootPath: 'examples/helloworld.spec');
		output:line('Loaded classes count: ' . helloProg:classes:length());

		if (helloProg:classes:length() >= 1) {
			output:line("[PASS] Successfully loaded HelloWorld program with modules\n");
		} else {
			output:line("[FAIL] Expected at least 1 class in HelloWorld\n");
		}

		# 2. Test Multi-file Standard Library Package Resolution
		output:line('2. Testing path resolution on \'base:struct:Array\'...');
		local String is resolvedPath: loader:resolvePath(rawPath: 'base:struct:Array');
		output:line('Resolved path: ' . resolvedPath);
		# The migration stdlib shadows the legacy lib: the resolver returns
		# the spec/lib path when the class has moved.
		if (resolvedPath:endsWith(suffix: 'base/struct/Array.spec')) {
			output:line("[PASS] Correctly resolved package to filesystem path\n");
		} else {
			output:line('[FAIL] Path resolution mismatch: ' . resolvedPath . "\n");
		}

		# 3. Test Wildcard Import Expansion
		# base:io:* currently expands to: Ansi, File, Input, InputHandler, Output
		output:line('3. Testing wildcard expansion on \'base:io:*\'...');
		local Array of String is wildcardFiles: loader:expandWildcard(rawPath: 'base:io:*');
		output:line('Wildcard files count: ' . wildcardFiles:length());
		if (wildcardFiles:length() == 5) {
			output:line("[PASS] Correctly expanded base:io:* to constituent files\n");
		} else {
			output:line('[FAIL] Wildcard count mismatch: ' . wildcardFiles:length() . "\n");
		}

		output:line('Phase 6 Module Loader test completed successfully!');
	}

}
