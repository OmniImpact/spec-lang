#! SpecUnit sweep: verifies flexible SpecMap key types (Int, Boolean, Float,
#! Enum/object identity, and String) including growth past the 8-bucket
#! initial allocation.

Class of SpecUnitTest is TestFlexibleMap{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	Function is testIntKeysAndGrowth(){
		local Map of Int to String is m: [1: 'one', 2: 'two'];
		Assert:areEqualInt(2, m:length());
		Assert:areEqualString('one', m:get(key: 1, default: ''));
		Assert:areEqualString('two', m[2]);
		Assert:isTrue(m:has(key: 1));
		Assert:isFalse(m:has(key: 99));

		m[3]: 'three';
		Assert:areEqualString('three', m[3]);
		Assert:isTrue(m:remove(key: 2));
		Assert:isFalse(m:has(key: 2));
		Assert:areEqualInt(2, m:length());

		local Int is sumKeys: 0;
		m:each(action: local Function(Int is k, String is v){
			sumKeys: sumKeys + k;
		});
		Assert:areEqualInt(4, sumKeys);

		local Map of Int to Int is big: Map:init();
		local Int is i: 0;
		while({ i < 30 }, {
			big:set(key: i, value: i * 10);
			i: i + 1;
		});
		Assert:areEqualInt(30, big:length());
		Assert:areEqualInt(290, big:get(key: 29, default: -1));
		Assert:areEqualInt(0, big:get(key: 0, default: -1));
		local Array of Int is ks: big:keys();
		Assert:areEqualInt(30, ks:length());
	}

	Function is testBooleanKeys(){
		local Map of Boolean to Int is m: [true: 100, false: 200];
		Assert:areEqualInt(2, m:length());
		Assert:areEqualInt(100, m:get(key: true, default: 0));
		Assert:areEqualInt(200, m[false]);
		Assert:isTrue(m:has(key: true));

		m[true]: 101;
		Assert:areEqualInt(101, m:get(key: true, default: 0));

		local Int is trueCount: 0;
		m:each(action: local Function(Boolean is k, Int is v){
			if({ k }, {
				trueCount: trueCount + 1;
			});
		});
		Assert:areEqualInt(1, trueCount);

		Assert:isTrue(m:remove(key: false));
		Assert:isFalse(m:has(key: false));
		Assert:areEqualInt(1, m:length());
	}

	Function is testFloatKeys(){
		local Map of Float to String is m: [1.5: 'one-half', -0.0: 'zero'];
		Assert:areEqualInt(2, m:length());
		Assert:areEqualString('one-half', m:get(key: 1.5, default: ''));
		Assert:areEqualString('zero', m:get(key: 0.0, default: ''));
		Assert:isTrue(m:has(key: 0.0));
		Assert:isFalse(m:has(key: 2.5));

		local Int is count: 0;
		m:each(action: local Function(Float is k, String is v){
			if({ k > 1.0 }, {
				count: count + 1;
			});
		});
		Assert:areEqualInt(1, count);

		Assert:isTrue(m:remove(key: 1.5));
		Assert:areEqualInt(1, m:length());
	}

	Function is testEnumKeys(){
		local Map of Color to String is names: [
			Color:Red: 'crimson',
			Color:Green: 'emerald'
		];
		Assert:areEqualInt(2, names:length());
		Assert:areEqualString('crimson', names:get(key: Color:Red, default: ''));
		Assert:areEqualString('emerald', names[Color:Green]);
		Assert:isFalse(names:has(key: Color:Blue));

		names:set(key: Color:Blue, value: 'cobalt');
		Assert:areEqualString('cobalt', names[Color:Blue]);
		Assert:areEqualInt(3, names:keys():length());

		local Int is seen: 0;
		names:each(action: local Function(Color is k, String is v){
			seen: seen + 1;
		});
		Assert:areEqualInt(3, seen);

		Assert:isTrue(names:remove(key: Color:Green));
		Assert:isFalse(names:has(key: Color:Green));
		Assert:areEqualInt(2, names:length());
	}

	Function is testStringMapGrowthFromEightBuckets(){
		local Map of String to Int is m: [:];
		local Int is i: 0;
		while({ i < 32 }, {
			m:set(key: 'key_' . i, value: i * 3);
			i: i + 1;
		});
		Assert:areEqualInt(32, m:length());
		Assert:areEqualInt(0, m:get(key: 'key_0', default: -1));
		Assert:areEqualInt(93, m:get(key: 'key_31', default: -1));
	}
}

Enum is Color{
	Red,
	Green,
	Blue
}
