Class is FeaturesTest{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'math'],
		['base', 'io'],
		['base', 'math', as Math()],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		# 1. Double quote strings with escaped whitespace characters and single quote raw strings
		Output:line('=== Strings ===');
		Output:line("Double-quoted with tab:\t[TAB] and newline:\n[NEXT LINE]");
		Output:line('Single-quoted literal with backslash-n: \n (not a newline)');

		# 2. Primitives and arithmetic
		Output:line('=== Math & Primitives ===');
		local Int is a: 10;
		local Int is b: 3;
		local Float is pi: 3.14159;

		local Int is sum: a + b;
		local Int is diff: a - b;
		local Int is prod: a * b;
		local Int is quot: a / b;
		local Int is rem: a % b;
		local Int is grouped: (a + b) * 2;

		Output:line('10 + 3 = ' . sum);
		Output:line('10 - 3 = ' . diff);
		Output:line('10 * 3 = ' . prod);
		Output:line('10 / 3 = ' . quot);
		Output:line('10 % 3 = ' . rem);
		Output:line('(10 + 3) * 2 = ' . grouped);
		Output:line('Float pi = ' . pi);

		# 3. base:math package
		Output:line('=== base:math ===');
		local Float is val1: 3.7;
		local Float is val2: 3.2;

		Output:line('round(3.7) = ' . Math:round(value: val1));
		Output:line('floor(3.7) = ' . Math:floor(value: val1));
		Output:line('ceil(3.2) = ' . Math:ceil(value: val2));
		Output:line('random() [0.0 - 1.0] = ' . Math:random());
		Output:line('random(10.0, 50.0) = ' . Math:random(min: 10.0, max: 50.0));

		# 4. Arrays
		Output:line('=== base:struct:Array ===');
		local Array of String is fruits: ['Apple', 'Banana', 'Cherry'];
		Output:line('Initial length: ' . fruits:length());
		Output:line('Index 0 (bracket syntax): ' . fruits[0]);
		Output:line('Index 1 (method syntax): ' . fruits:get(index: 1));

		fruits:add(item: 'Date');
		fruits:add(['Elderberry', 'Fig']);
		Output:line('After adding Date, Elderberry, Fig, length: ' . fruits:length());
		Output:line('Index 3: ' . fruits[3]);
		Output:line('Index 4: ' . fruits[4]);
		Output:line('Index 5: ' . fruits[5]);
	}

}
