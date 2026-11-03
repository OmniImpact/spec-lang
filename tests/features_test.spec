Class is FeaturesTest{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:math:*,
		base:io:*
	];

	replace local Function is init(Map of String to String is args){
		# 1. Double quote strings with escaped whitespace characters and single quote raw strings
		output:line("=== Strings ===");
		output:line("Double-quoted with tab:\t[TAB] and newline:\n[NEXT LINE]");
		output:line('Single-quoted literal with backslash-n: \n (not a newline)');

		# 2. Primitives and arithmetic
		output:line("=== Math & Primitives ===");
		local Int is a: 10;
		local Int is b: 3;
		local Float is pi: 3.14159;

		local Int is sum: a + b;
		local Int is diff: a - b;
		local Int is prod: a * b;
		local Int is quot: a / b;
		local Int is rem: a % b;
		local Int is grouped: (a + b) * 2;

		output:line("10 + 3 = " . sum);
		output:line("10 - 3 = " . diff);
		output:line("10 * 3 = " . prod);
		output:line("10 / 3 = " . quot);
		output:line("10 % 3 = " . rem);
		output:line("(10 + 3) * 2 = " . grouped);
		output:line("Float pi = " . pi);

		# 3. base:math package
		output:line("=== base:math ===");
		local Float is val1: 3.7;
		local Float is val2: 3.2;

		output:line("round(3.7) = " . math:round(value: val1));
		output:line("floor(3.7) = " . math:floor(value: val1));
		output:line("ceil(3.2) = " . math:ceil(value: val2));
		output:line("random() [0.0 - 1.0] = " . math:random());
		output:line("random(10.0, 50.0) = " . math:random(min: 10.0, max: 50.0));

		# 4. Arrays
		output:line("=== base:struct:Array ===");
		local Array of String is fruits: ["Apple", "Banana", "Cherry"];
		output:line("Initial length: " . fruits:length());
		output:line("Index 0 (bracket syntax): " . fruits[0]);
		output:line("Index 1 (method syntax): " . fruits:get(index: 1));

		fruits:add(item: "Date");
		fruits:add(["Elderberry", "Fig"]);
		output:line("After adding Date, Elderberry, Fig, length: " . fruits:length());
		output:line("Index 3: " . fruits[3]);
		output:line("Index 4: " . fruits[4]);
		output:line("Index 5: " . fruits[5]);
	}

}
