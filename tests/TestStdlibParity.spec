#! SpecUnit suite for collections parity (Array, List, Map),
#! Conditional (unless, choose), Loops (times, range, rangeStep, forever),
#! and Math (constants, Int overloads, sign, lerp, degToRad, radToDeg, hypot, randomInt).

Class of SpecUnitTest is TestStdlibParity{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'struct', as Sort()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'math', as Math()],
		['base', 'math', Stats],
		['base', 'math', as Stats()]
	];

	Function is testArrayParity(){
		local Array of String is items: ['a', 'b', 'c'];
		Assert:isTrue(items:contains(search: 'b'));
		Assert:isFalse(items:contains(search: 'z'));
		Assert:areEqualString('a', items:first(default: ''));
		Assert:areEqualString('c', items:last(default: ''));

		local Array of String is empty: [];
		Assert:areEqualString('x', empty:first(default: 'x'));
		Assert:areEqualString('y', empty:last(default: 'y'));

		local Array of String is rev: items:reverse();
		Assert:areEqualString('c,b,a', rev:join(separator: ','));

		local Array of String is taken: items:take(n: 2);
		Assert:areEqualString('a,b', taken:join(separator: ','));
		Assert:areEqualInt(0, items:take(n: 0):length());

		local Array of String is dropped: items:drop(n: 1);
		Assert:areEqualString('b,c', dropped:join(separator: ','));

		local Array of String is copied: items:copy();
		copied:add(item: 'd');
		Assert:areEqualInt(3, items:length());
		Assert:areEqualInt(4, copied:length());

		local Array of Int is nums: [2, 4, 6];
		Assert:isTrue(nums:all(predicate: local Function of Boolean(Int is n){ return (n % 2) == 0; }));
		Assert:isTrue(nums:none(predicate: local Function of Boolean(Int is n){ return n > 10; }));

		local String is foundItem: items:find(predicate: local Function of Boolean(String is s){ return s == 'b'; }, default: 'none');
		Assert:areEqualString('b', foundItem);
		local String is missedItem: items:find(predicate: local Function of Boolean(String is s){ return s == 'z'; }, default: 'none');
		Assert:areEqualString('none', missedItem);
	}

	Function is testMapParity(){
		local Map of String to String is m: ['a': '1', 'b': '2'];
		Assert:isFalse(m:isEmpty());
		Assert:areEqualInt(2, m:values():length());

		local Map of String to String is extra: ['b': '20', 'c': '3'];
		m:merge(other: extra);
		Assert:areEqualInt(3, m:length());
		Assert:areEqualString('20', m:getString(key: 'b', default: ''));
		Assert:areEqualString('3', m:getString(key: 'c', default: ''));

		local Map is filtered: m:filter(predicate: local Function of Boolean(String is k, String is v){
			return k != 'a';
		});
		Assert:areEqualInt(2, filtered:length());
		Assert:isFalse(filtered:has(key: 'a'));

		Assert:isTrue(m:any(predicate: local Function of Boolean(String is k, Any is v){ return k == 'c'; }));
		Assert:areEqualInt(2, m:count(predicate: local Function of Boolean(String is k, Any is v){ return k != 'a'; }));

		m:clear();
		Assert:isTrue(m:isEmpty());
		Assert:areEqualInt(0, m:length());
	}

	Function is testConditionalHelpers(){
		local Int is x: 0;
		unless(check: { return false; }, then: {
			x: 10;
		});
		Assert:areEqualInt(10, x);

		unless(check: { return true; }, then: {
			x: 99;
		}, else: {
			x: 20;
		});
		Assert:areEqualInt(20, x);
	}

	Function is testLoopHelpers(){
		local Int is sumTimes: 0;
		times(count: 4, worker: local Function(Int is i){
			sumTimes: sumTimes + i;
		});
		Assert:areEqualInt(6, sumTimes);

		local Int is sumRange: 0;
		range(start: 2, end: 5, worker: local Function(Int is i){
			sumRange: sumRange + i;
		});
		Assert:areEqualInt(9, sumRange);

		local Int is sumDown: 0;
		rangeStep(start: 6, end: 0, step: -2, worker: local Function(Int is i){
			sumDown: sumDown + i;
		});
		Assert:areEqualInt(12, sumDown);

		local Int is ticks: 0;
		forever(worker: local Function of Boolean(){
			ticks: ticks + 1;
			return ticks < 3;
		});
		Assert:areEqualInt(3, ticks);
	}

	Function is testStats(){
		local Array of Int is nums: [10, 2, 8, 4, 6];
		Assert:areEqualInt(30, sum(values: nums));
		Assert:areEqualInt(2, Stats:min(values: nums));
		Assert:areEqualInt(10, Stats:max(values: nums));
		Assert:isTrue(abs(value: average(values: nums) - 6.0) < 0.0001);
		Assert:isTrue(abs(value: median(values: nums) - 6.0) < 0.0001);
		Assert:isTrue(abs(value: variance(values: nums) - 8.0) < 0.0001);
		Assert:isTrue(abs(value: stdDev(values: nums) - sqrt(value: 8.0)) < 0.0001);

		local Array of Int is evenNums: [4, 1, 9, 2];
		Assert:isTrue(abs(value: median(values: evenNums) - 3.0) < 0.0001);

		local Array of Int is empty: [];
		Assert:areEqualInt(0, sum(values: empty));
		Assert:areEqualInt(-1, Stats:min(values: empty, default: -1));
		Assert:areEqualInt(-1, Stats:max(values: empty, default: -1));
		Assert:isTrue(abs(value: average(values: empty)) < 0.0001);
	}

	Function is testMathHelpers(){
		Assert:isTrue(pi() > 3.14 && pi() < 3.15);
		Assert:isTrue(tau() > 6.28 && tau() < 6.29);
		Assert:isTrue(e() > 2.71 && e() < 2.72);
		Assert:areEqualInt(-1, sign(value: -42));
		Assert:areEqualInt(0, sign(value: 0));
		Assert:areEqualInt(1, sign(value: 42));
		Assert:isTrue(abs(value: sign(value: -3.5) + 1.0) < 0.0001);
		Assert:isTrue(abs(value: lerp(a: 10.0, b: 20.0, t: 0.25) - 12.5) < 0.0001);
		Assert:isTrue(abs(value: hypot(x: 3.0, y: 4.0) - 5.0) < 0.0001);
		Assert:isTrue(abs(value: degToRad(deg: 180.0) - pi()) < 0.0001);
		Assert:isTrue(abs(value: radToDeg(rad: pi()) - 180.0) < 0.0001);
		Assert:areEqualInt(7, abs(value: -7));
		Assert:areEqualInt(2, Math:min(values: [10, 2, 8, 4]));
		Assert:areEqualInt(10, Math:max(values: [10, 2, 8, 4]));
		Assert:isTrue(abs(value: floor(value: 2.7) - 2.0) < 0.0001);
		Assert:isTrue(abs(value: floor(value: -2.3) + 3.0) < 0.0001);
		Assert:isTrue(abs(value: ceil(value: 2.3) - 3.0) < 0.0001);
		Assert:isTrue(abs(value: ceil(value: -2.7) + 2.0) < 0.0001);
		Assert:isTrue(abs(value: round(value: 2.5) - 3.0) < 0.0001);
		Assert:isTrue(abs(value: round(value: -2.5) + 3.0) < 0.0001);
		Assert:isTrue(abs(value: round(value: 0.49999999999999994)) < 0.0001);
		local Float is rnd: random(min: 5.0, max: 10.0);
		Assert:isTrue(rnd >= 5.0 && rnd < 10.0);
		Assert:isTrue(abs(value: exp(value: 1.0) - e()) < 0.0001);
		Assert:isTrue(abs(value: log10(value: 1000.0) - 3.0) < 0.0001);
		Assert:isTrue(abs(value: cbrt(value: 27.0) - 3.0) < 0.0001);
		Assert:isTrue(abs(value: asin(value: 1.0) - (pi() / 2.0)) < 0.0001);
		Assert:isTrue(abs(value: acos(value: 1.0)) < 0.0001);
		Assert:isTrue(abs(value: atan(value: 1.0) - (pi() / 4.0)) < 0.0001);
		Assert:isTrue(abs(value: fma(a: 2.0, b: 3.0, c: 4.0) - 10.0) < 0.0001);
		Assert:isTrue(abs(value: sinh(value: 0.0)) < 0.0001);
		Assert:isTrue(abs(value: cosh(value: 0.0) - 1.0) < 0.0001);
		Assert:isTrue(abs(value: tanh(value: 0.0)) < 0.0001);
		Assert:isTrue(abs(value: tanh(value: 30.0) - 1.0) < 0.0001);
	}

	Function is testSort(){
		local Array of Int is nums: [5, 1, 4, 2, 3];
		local Array of Int is asc: ints(values: nums);
		Assert:areEqualInt(1, asc:get(index: 0, default: 0));
		Assert:areEqualInt(3, asc:get(index: 2, default: 0));
		Assert:areEqualInt(5, asc:get(index: 4, default: 0));
		Assert:areEqualInt(5, nums:get(index: 0, default: 0));

		local Array of Int is desc: intsDesc(values: nums);
		Assert:areEqualInt(5, desc:get(index: 0, default: 0));
		Assert:areEqualInt(1, desc:get(index: 4, default: 0));

		local Array of String is words: ['pear', 'apple', 'banana'];
		local Array of String is sortedWords: strings(values: words);
		Assert:areEqualString('apple,banana,pear', sortedWords:join(separator: ','));
		local Array of String is descWords: stringsDesc(values: words);
		Assert:areEqualString('pear,banana,apple', descWords:join(separator: ','));

		local Array of String is byLen: by(values: words, compare: local Function of Int(String is a, String is b){
			return a:length() - b:length();
		});
		Assert:areEqualString('pear,apple,banana', byLen:join(separator: ','));
	}

}
