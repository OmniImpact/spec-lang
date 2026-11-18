#! SpecUnit sweep (from container_methods_test.spec): container
#! methods — Array:slice, Array:indexOf, Array:join, the Array
#! combinators (each/filter/count/any), and the Map surface (set, get,
#! getString, getInt, has, remove, length, keys).

Class of SpecUnitTest is TestContainerMethods{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Vector()],
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

	## Case 6: Vector sys floor direct operations and Array delegation.
	Function is testVectorFloor(){
		local Array of String is arr: ['a', 'b', 'c'];
		Assert:areEqualInt(3, Vector:vecLength(v: arr));
		Assert:areEqualInt(3, arr:length());

		Vector:vecSetAt(v: arr, idx: 1, item: 'beta');
		Assert:areEqualString('beta', arr:get(index: 1, default: ''));

		Vector:vecAdd(v: arr, item: 'd');
		Assert:areEqualInt(4, arr:length());
		Assert:areEqualString('d', arr:get(index: 3, default: ''));

		local String is popped: arr:pop(default: '');
		Assert:areEqualString('d', popped);
		Assert:areEqualInt(3, arr:length());

		local String is removed: arr:removeAt(index: 0, default: '');
		Assert:areEqualString('a', removed);
		Assert:areEqualInt(2, arr:length());
		Assert:areEqualString('beta', arr:get(index: 0, default: ''));

		Vector:vecClear(v: arr);
		Assert:areEqualInt(0, arr:length());
		Assert:isTrue(arr:isEmpty());
	}

	## Case 7: Array mutations and FIFO/LIFO behaviors.
	Function is testArrayMutationsAndDefaults(){
		local Array of String is arr: [];
		Assert:areEqualInt(0, arr:length());
		Assert:isTrue(arr:isEmpty());

		arr:add(item: 'first');
		arr:add(item: 'second');
		arr:add(item: 'third');
		Assert:areEqualInt(3, arr:length());
		Assert:isFalse(arr:isEmpty());
		Assert:areEqualString('first', arr:get(index: 0, default: ''));
		Assert:areEqualString('second', arr:get(index: 1, default: ''));
		Assert:areEqualString('third', arr:get(index: 2, default: ''));

		arr:set(index: 1, item: 'SECOND');
		Assert:areEqualString('SECOND', arr:get(index: 1, default: ''));

		local String is popped: arr:pop(default: '');
		Assert:areEqualString('third', popped);
		Assert:areEqualInt(2, arr:length());

		local String is removed: arr:removeAt(index: 0, default: '');
		Assert:areEqualString('first', removed);
		Assert:areEqualInt(1, arr:length());
		Assert:areEqualString('SECOND', arr:get(index: 0, default: ''));

		arr:clear();
		Assert:areEqualInt(0, arr:length());
		Assert:isTrue(arr:isEmpty());
	}

	## Case 8: Comprehensive Map operations: overwrites, type conversions, and scaling.
	Function is testMapComprehensive(){
		local Map of String to String is m: [:];
		Assert:areEqualInt(0, m:length());
		Assert:isFalse(m:has(key: 'missing'));
		Assert:areEqualInt(0, m:keys():length());

		m:set(key: 'key1', value: 'val1');
		Assert:areEqualInt(1, m:length());
		Assert:isTrue(m:has(key: 'key1'));
		Assert:areEqualString('val1', m:getString(key: 'key1', default: ''));

		# Overwrite key
		m:set(key: 'key1', value: 'val1_updated');
		Assert:areEqualInt(1, m:length());
		Assert:areEqualString('val1_updated', m:getString(key: 'key1', default: ''));

		# Booleans
		m:set(key: 'bool_true', value: 'true');
		m:set(key: 'bool_false', value: 'false');
		m:set(key: 'bool_other', value: 'not_bool');
		Assert:isTrue(m:getBool(key: 'bool_true', default: false));
		Assert:isFalse(m:getBool(key: 'bool_false', default: true));
		Assert:isTrue(m:getBool(key: 'bool_other', default: true));
		Assert:isFalse(m:getBool(key: 'non_existent', default: false));

		# Integers
		m:set(key: 'int_pos', value: '12345');
		m:set(key: 'int_neg', value: '-99');
		m:set(key: 'int_invalid', value: 'abc');
		Assert:areEqualInt(12345, m:getInt(key: 'int_pos', default: 0));
		Assert:areEqualInt(-99, m:getInt(key: 'int_neg', default: 0));
		Assert:areEqualInt(777, m:getInt(key: 'int_invalid', default: 777));
		Assert:areEqualInt(888, m:getInt(key: 'int_missing', default: 888));

		# Growth and scale (50 entries)
		local Map of String to String is bigMap: [:];
		local Int is i: 0;
		while({ i < 50 }, {
			bigMap:set(key: 'k_' . (i as String), value: 'v_' . (i as String));
			i: i + 1;
		});
		Assert:areEqualInt(50, bigMap:length());
		Assert:areEqualInt(50, bigMap:keys():length());

		local Int is j: 0;
		while({ j < 50 }, {
			Assert:isTrue(bigMap:has(key: 'k_' . (j as String)));
			Assert:areEqualString('v_' . (j as String), bigMap:getString(key: 'k_' . (j as String), default: ''));
			j: j + 1;
		});

		# Remove 25 entries
		local Int is r: 0;
		while({ r < 25 }, {
			Assert:isTrue(bigMap:remove(key: 'k_' . (r as String)));
			r: r + 1;
		});
		Assert:areEqualInt(25, bigMap:length());
		Assert:isFalse(bigMap:has(key: 'k_0'));
		Assert:isTrue(bigMap:has(key: 'k_25'));
	}
}
