Class is ContainerMethodsTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Container Methods Test ===');

		# Case 1: Array:slice
		local Array of String is words: ['zero', 'one', 'two', 'three', 'four'];
		local Array of String is mid: words:slice(start: 1, end: 4);
		local Array of String is emptySlice: words:slice(start: 3, end: 2);
		local Boolean is midOk: mid:length() == 3 && mid:get(index: 0, default: '') == 'one' && mid:get(index: 1, default: '') == 'two' && mid:get(index: 2, default: '') == 'three';
		local Boolean is emptyOk: emptySlice:length() == 0;
		Conditional:if(check: { midOk && emptyOk }, then: {
			Output:line('[PASS] Array:slice extracts subarrays and clamps bounds');
		}, else: {
			Output:line('[FAIL] Array:slice');
		});

		# Case 2: Array:indexOf
		local Int is idxOne: words:indexOf(search: 'one', default: -1);
		local Int is idxFour: words:indexOf(search: 'four', default: -1);
		local Int is idxAbsent: words:indexOf(search: 'five', default: -99);
		Conditional:if(check: { idxOne == 1 && idxFour == 4 && idxAbsent == -99 }, then: {
			Output:line('[PASS] Array:indexOf locates elements and returns fallback');
		}, else: {
			Output:line('[FAIL] Array:indexOf');
		});

		# Case 3: Array:join
		local String is joinedComma: words:join(separator: ', ');
		local String is joinedEmpty: words:join(separator: '');
		local Array of String is singleArr: ['only'];
		local String is joinedSingle: singleArr:join(separator: '-');
		Conditional:if(check: { joinedComma == 'zero, one, two, three, four' && joinedEmpty == 'zeroonetwothreefour' && joinedSingle == 'only' }, then: {
			Output:line('[PASS] Array:join concatenates elements with separator');
		}, else: {
			Output:line('[FAIL] Array:join');
		});

		# Case 4: Array combinators: each, filter, count, any
		local Array of String is items: ['apple', 'avocado', 'banana', 'apricot', 'cherry'];
		local Int is aCount: items:count(predicate: local Function of Boolean(String is s){
			return s:startsWith(prefix: 'a');
		});
		local Boolean is hasCherry: items:any(predicate: local Function of Boolean(String is s){
			return s == 'cherry';
		});
		local Boolean is hasGrape: items:any(predicate: local Function of Boolean(String is s){
			return s == 'grape';
		});
		local Array of String is aWords: items:filter(predicate: local Function of Boolean(String is s){
			return s:startsWith(prefix: 'a');
		});
		local Boolean is aWordsOk: aWords:length() == 3 && aWords:get(index: 0, default: '') == 'apple' && aWords:get(index: 1, default: '') == 'avocado' && aWords:get(index: 2, default: '') == 'apricot';
		Conditional:if(check: { aCount == 3 && hasCherry && !hasGrape && aWordsOk }, then: {
			Output:line('[PASS] Array combinators: count, any, filter');
		}, else: {
			Output:line('[FAIL] Array combinators');
		});

		# Case 5: Map basic operations: set, get, getString, getInt, has, remove, length, keys
		local Map of String to String is dict: [:];
		dict:set(key: 'name', value: 'Spec');
		dict:set(key: 'type', value: 'Language');
		dict:set(key: 'version', value: '1');
		local Boolean is len3: dict:length() == 3;
		local Boolean is hasName: dict:has(key: 'name');
		local Boolean is hasMissing: !dict:has(key: 'missing');
		local String is nameVal: dict:getString(key: 'name', default: '');
		local String is missVal: dict:getString(key: 'foo', default: 'fallback');
		local Int is verVal: dict:getInt(key: 'version', default: 0);
		local Int is defVerVal: dict:getInt(key: 'absent_num', default: 42);
		local Boolean is removed: dict:remove(key: 'type');
		local Boolean is removeAbsent: !dict:remove(key: 'type');
		local Boolean is len2: dict:length() == 2;
		local Array of String is k: dict:keys();
		local Boolean is keysOk: k:length() == 2 && k:indexOf(search: 'name', default: -1) >= 0 && k:indexOf(search: 'version', default: -1) >= 0;

		Conditional:if(check: { len3 && hasName && hasMissing && nameVal == 'Spec' && missVal == 'fallback' && verVal == 1 && defVerVal == 42 && removed && removeAbsent && len2 && keysOk }, then: {
			Output:line('[PASS] Map methods: set, getString, getInt, has, remove, length, keys');
		}, else: {
			Output:line('[FAIL] Map methods');
		});
	}

}
