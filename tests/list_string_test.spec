Class is Greeting{

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];
	local String is value: '';

	replace Function is init(String is text){
		self:value: text;
	}

	Function of String is getValue(){
		return self:value;
	}
}

Class is ListStringTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'struct', List],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== List Vector Test ===');

		# Case 1: string literal
		local [String] is names: ['alice', 'bob'];
		if (names:length() == 2) {
			Output:line('[PASS] string literal constructs');
		} else {
			Output:line('[FAIL] literal length: ' . names:length() as String);
		}

		# Case 2: string get reads back; OOB yields default + notification
		local [Byte] is errFlag;
		local String is first: names:get(index: 0, default: '', error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		local String is missing: names:get(index: 9, default: 'fallback', error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		if (first == 'alice' && missing == 'fallback' && errFlag:length() == 1) {
			Output:line('[PASS] string get, default, and error notification');
		} else {
			Output:line('[FAIL] string get: first=' . first . ' missing=' . missing);
		}

		# Case 3: string push + set + pop (ownership round-trip)
		names:push(item: 'carol');
		names:set(index: 1, item: 'bea', error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		local String is popped: names:pop(default: '');
		if (popped == 'carol' && names:length() == 2 && errFlag:length() == 1) {
			Output:line('[PASS] string push/set/pop ownership round-trip');
		} else {
			Output:line('[FAIL] push/set/pop: popped=' . popped . ' len=' . names:length() as String);
		}

		# Case 4: int literal elements
		local [Int] is nums: [1, 2, 3];
		local Int is mid: nums:get(index: 1, default: 0);
		nums:push(item: 4);
		if (mid == 2 && nums:length() == 4 && nums:get(index: 3, default: 0) == 4) {
			Output:line('[PASS] int literal elements');
		} else {
			Output:line('[FAIL] int list: mid=' . mid as String . ' len=' . nums:length() as String);
		}

		# Case 5: object elements — push retains, get returns usable instance
		local [Greeting] is seen: [Greeting:init(text: 'hello')];
		seen:push(item: Greeting:init(text: 'world'));
		local Greeting is g1: seen:get(index: 1, default: Greeting:init(text: 'none'));
		if (g1:getValue() == 'world') {
			Output:line('[PASS] object elements retained and readable');
		} else {
			Output:line('[FAIL] object element: ' . g1:getValue());
		}

		# Case 6: aliasing — assignment shares the vector
		local [Greeting] is alias: seen;
		alias:pop(default: Greeting:init(text: 'none'));
		if (seen:length() == 1) {
			Output:line('[PASS] alias pop observed through original reference');
		} else {
			Output:line('[FAIL] alias: len=' . seen:length() as String);
		}

		# Case 7: clear empties and stays usable
		names:clear();
		names:push(item: 'zed');
		if (names:length() == 1 && names:get(index: 0, default: '') == 'zed') {
			Output:line('[PASS] clear empties and vector stays usable');
		} else {
			Output:line('[FAIL] clear');
		}

		# Case 8: fresh-insert ownership — fresh constructor claims transfer into the
		# container (no orphan), mixed with borrowed inserts in one literal
		local [Greeting] is fresh: [Greeting:init(text: 'lit1'), g1];
		fresh:push(item: Greeting:init(text: 'lit2'));
		fresh:set(index: 2, item: Greeting:init(text: 'lit3'), error: local Function(String is m){
			errFlag:push(item: 1 as Byte);
		});
		local Greeting is f1: fresh:get(index: 0, default: Greeting:init(text: 'none'));
		local Greeting is f2: fresh:get(index: 1, default: Greeting:init(text: 'none'));
		local Greeting is f3: fresh:get(index: 2, default: Greeting:init(text: 'none'));
		if (f1:getValue() == 'lit1' && f2:getValue() == 'world' && f3:getValue() == 'lit3' && errFlag:length() == 1) {
			Output:line('[PASS] fresh and borrowed inserts coexist with balanced ownership');
		} else {
			Output:line('[FAIL] fresh inserts: f1=' . f1:getValue() . ' f2=' . f2:getValue() . ' f3=' . f3:getValue() . ' err=' . errFlag:length() as String);
		}

		Output:line('=== End List Vector Test ===');
	}
}
