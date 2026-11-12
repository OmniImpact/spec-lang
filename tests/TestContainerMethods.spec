#! SpecUnit sweep (from container_methods_test.spec): container
#! methods — Array:slice, Array:indexOf, Array:join, the Array
#! combinators (each/filter/count/any), and the Map surface (set, get,
#! getString, getInt, has, remove, length, keys).

Class of SpecUnitTest is TestContainerMethods{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map]
	];

	## Case 1: Array:slice extracts subarrays and clamps bounds.
	Function is testSlice(){
		local Array of String is words: ['zero', 'one', 'two', 'three', 'four'];
		local Array of String is mid: words:slice(start: 1, end: 4);
		local Array of String is emptySlice: words:slice(start: 3, end: 2);
		Assert:areEqualInt(3, mid:length());
		Assert:areEqualString('one', mid:get(index: 0, default: ''));
		Assert:areEqualString('two', mid:get(index: 1, default: ''));
		Assert:areEqualString('three', mid:get(index: 2, default: ''));
		Assert:areEqualInt(0, emptySlice:length());
	}

	## Case 2: Array:indexOf locates elements and returns the fallback.
	Function is testIndexOf(){
		local Array of String is words: ['zero', 'one', 'two', 'three', 'four'];
		Assert:areEqualInt(1, words:indexOf(search: 'one', default: -1));
		Assert:areEqualInt(4, words:indexOf(search: 'four', default: -1));
		Assert:areEqualInt(-99, words:indexOf(search: 'five', default: -99));
	}

	## Case 3: Array:join concatenates elements with the separator.
	Function is testJoin(){
		local Array of String is words: ['zero', 'one', 'two', 'three', 'four'];
		local Array of String is singleArr: ['only'];
		Assert:areEqualString('zero, one, two, three, four', words:join(separator: ', '));
		Assert:areEqualString('zeroonetwothreefour', words:join(separator: ''));
		Assert:areEqualString('only', singleArr:join(separator: '-'));
	}

	## Case 4: Array combinators: count, any, filter.
	Function is testArrayCombinators(){
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
		Assert:areEqualInt(3, aCount);
		Assert:isTrue(hasCherry);
		Assert:isFalse(hasGrape);
		Assert:areEqualInt(3, aWords:length());
		Assert:areEqualString('apple', aWords:get(index: 0, default: ''));
		Assert:areEqualString('avocado', aWords:get(index: 1, default: ''));
		Assert:areEqualString('apricot', aWords:get(index: 2, default: ''));
	}

	## Case 5: Map methods: set, getString, getInt, has, remove, length,
	## keys.
	Function is testMapMethods(){
		local Map of String to String is dict: [:];
		dict:set(key: 'name', value: 'Spec');
		dict:set(key: 'type', value: 'Language');
		dict:set(key: 'version', value: '1');
		Assert:areEqualInt(3, dict:length());
		Assert:isTrue(dict:has(key: 'name'));
		Assert:isFalse(dict:has(key: 'missing'));
		Assert:areEqualString('Spec', dict:getString(key: 'name', default: ''));
		Assert:areEqualString('fallback', dict:getString(key: 'foo', default: 'fallback'));
		Assert:areEqualInt(1, dict:getInt(key: 'version', default: 0));
		Assert:areEqualInt(42, dict:getInt(key: 'absent_num', default: 42));

		Assert:isTrue(dict:remove(key: 'type'));
		Assert:isFalse(dict:remove(key: 'type'));
		Assert:areEqualInt(2, dict:length());

		local Array of String is k: dict:keys();
		Assert:areEqualInt(2, k:length());
		Assert:isTrue(k:indexOf(search: 'name', default: -1) >= 0);
		Assert:isTrue(k:indexOf(search: 'version', default: -1) >= 0);
	}
}
