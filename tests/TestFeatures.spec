#! SpecUnit sweep (from features_test.spec): the language features smoke —
#! string escape processing vs raw single-quoted literals, integer
#! arithmetic, Float primitives, the base:math wrappers, and the
#! base:struct:Array bracket/method access with single and batch adds.
#! The random draws are asserted by range only — the seed varies per
#! binary, the old suite printed them without checking.

Class of SpecUnitTest is TestFeatures{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'math'],
		['base', 'math', as Math()]
	];

	## 1. Double-quoted strings process escapes (tab and newline are one
	## character each); single-quoted strings stay raw (backslash-n is
	## two characters).
	Function is testStringEscapesAndRaw(){
		local String is tabbed: "a\tb";
		local String is newliney: "a\nb";
		local String is raw: 'a\nb';
		Assert:areEqualInt(3, tabbed:length());
		Assert:areEqualInt(3, newliney:length());
		Assert:areEqualInt(4, raw:length());
	}

	## 2. Primitives and arithmetic: the integer operators and grouping.
	Function is testIntegerArithmetic(){
		local Int is a: 10;
		local Int is b: 3;
		Assert:areEqualInt(13, a + b);
		Assert:areEqualInt(7, a - b);
		Assert:areEqualInt(30, a * b);
		Assert:areEqualInt(3, a / b);
		Assert:areEqualInt(1, a % b);
		Assert:areEqualInt(26, (a + b) * 2);
	}

	## 2b. The Float primitive renders and compares within tolerance.
	Function is testFloatPrimitive(){
		local Float is pi: 3.14159;
		Assert:areClose(3.14159, pi, 0.000001);
	}

	## 3. base:math package: round/floor/ceil wrap libm; the random draws
	## stay inside their documented ranges.
	Function is testBaseMath(){
		local Float is val1: 3.7;
		local Float is val2: 3.2;
		Assert:areClose(4.0, Math:round(value: val1), 0.0001);
		Assert:areClose(3.0, Math:floor(value: val1), 0.0001);
		Assert:areClose(4.0, Math:ceil(value: val2), 0.0001);
		Assert:isTrue(Math:random() >= 0.0 && Math:random() < 1.0);
		Assert:isTrue(Math:random(min: 10.0, max: 50.0) >= 10.0 && Math:random(min: 10.0, max: 50.0) < 50.0);
	}

	## 4. base:struct:Array: bracket and method indexing, single add and
	## batch add.
	Function is testArrayAccessAndAdds(){
		local Array of String is fruits: ['Apple', 'Banana', 'Cherry'];
		Assert:areEqualInt(3, fruits:length());
		Assert:areEqualString('Apple', fruits[0]);
		Assert:areEqualString('Banana', fruits:get(index: 1));

		fruits:add(item: 'Date');
		fruits:add(['Elderberry', 'Fig']);
		Assert:areEqualInt(6, fruits:length());
		Assert:areEqualString('Date', fruits[3]);
		Assert:areEqualString('Elderberry', fruits[4]);
		Assert:areEqualString('Fig', fruits[5]);
	}
}
