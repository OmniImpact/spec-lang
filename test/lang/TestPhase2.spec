#! SpecUnit sweep (from phase2_test.spec): extended Array operations —
#! indexOf/pop/removeAt/slice/clear — and the extended Map operations —
#! set/has/getString/update/keys/remove.

Class of SpecUnitTest is TestPhase2{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Output()]
	];

	# 1. Extended Array Operations
	Function is testExtendedArrayOperations(){
		local Array of String is tokens: ['class', 'MyClass', '{', 'local', '}'];
		Assert:areEqualInt(5, tokens:length());
		Assert:areEqualInt(1, tokens:indexOf(search: 'MyClass', default: -1));
		Assert:areEqualInt(-1, tokens:indexOf(search: 'missing', default: -1));
		local String is popped: tokens:pop(default: 'EMPTY');
		Assert:areEqualString('}', popped);
		Assert:areEqualInt(4, tokens:length());
		local String is removed: tokens:removeAt(index: 1, default: 'OUT_OF_BOUNDS');
		Assert:areEqualString('MyClass', removed);
		Assert:areEqualInt(3, tokens:length());
		Assert:areEqualString('{', tokens[1]);
		local Array of String is sliced: tokens:slice(start: 0, end: 2);
		Assert:areEqualInt(2, sliced:length());
		Assert:areEqualString('class', sliced[0]);
		Assert:areEqualString('{', sliced[1]);
		tokens:clear();
		Assert:isTrue(tokens:isEmpty());
		Assert:areEqualString('DEFAULT_FALLBACK', tokens:pop(default: 'DEFAULT_FALLBACK'));
	}

	# 2. Extended Map Operations
	Function is testExtendedMapOperations(){
		local Map of String to String is symbolTable: Map:init();
		Assert:areEqualInt(0, symbolTable:length());
		symbolTable:set(key: 'x', value: 'Int');
		symbolTable:set(key: 'y', value: 'Float');
		symbolTable:set(key: 'name', value: 'String');
		Assert:areEqualInt(3, symbolTable:length());
		Assert:isTrue(symbolTable:has(key: 'x'));
		Assert:isFalse(symbolTable:has(key: 'z'));
		Assert:areEqualString('Float', symbolTable:getString(key: 'y', default: 'NOT_FOUND'));
		# Update existing key
		symbolTable:set(key: 'x', value: 'LongInt');
		Assert:areEqualString('LongInt', symbolTable:getString(key: 'x', default: 'NOT_FOUND'));
		Assert:areEqualInt(3, symbolTable:length());
		# Keys array
		local Array of String is symKeys: symbolTable:keys();
		Assert:areEqualInt(3, symKeys:length());
		# Remove key
		local Boolean is removedKey: symbolTable:remove(key: 'y');
		Assert:isTrue(removedKey);
		Assert:isFalse(symbolTable:has(key: 'y'));
		Assert:areEqualInt(2, symbolTable:length());
	}
}
