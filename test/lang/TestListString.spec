#! SpecUnit sweep (from list_string_test.spec): the [String] and [Int]
#! vectors — literal construction, get with defaults and error
#! notification, push/set/pop ownership round-trips, object elements,
#! ARC aliasing, clear-then-reuse, and fresh-vs-borrowed insert
#! ownership balance.

Class of SpecUnitTest is TestListString{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', List]
	];

	## Case 1: string literal constructs.
	Function is testStringLiteralConstructs(){
		local [String] is names: ['alice', 'bob'];
		Assert:areEqualInt(2, names:length());
	}

	## Cases 2+3: string get/[] reads back, push/set/pop ownership round-trip.
	Function is testGetPushSetPopOwnership(){
		local [String] is names: ['alice', 'bob'];
		local String is first: names:get(index: 0);
		Assert:areEqualString('alice', first);
		Assert:areEqualString('bob', names[1]);

		names:push(item: 'carol');
		names:set(index: 1, item: 'bea');
		local String is popped: names:pop();
		Assert:areEqualString('carol', popped);
		Assert:areEqualInt(2, names:length());
		Assert:areEqualString('bea', names:get(index: 1));
	}

	## Case 4: int literal elements.
	Function is testIntLiteralElements(){
		local [Int] is nums: [1, 2, 3];
		local Int is mid: nums:get(index: 1);
		nums:push(item: 4);
		Assert:areEqualInt(2, mid);
		Assert:areEqualInt(4, nums:length());
		Assert:areEqualInt(4, nums:get(index: 3));
	}

	## Case 5: object elements — push retains, get returns usable instance.
	Function is testObjectElements(){
		local [Greeting] is seen: [Greeting:init(text: 'hello')];
		seen:push(item: Greeting:init(text: 'world'));
		local Greeting is g1: seen:get(index: 1);
		Assert:areEqualString('world', g1:getValue());
	}

	## Case 6: aliasing — assignment shares the vector.
	Function is testAliasPopObserved(){
		local [Greeting] is seen: [Greeting:init(text: 'hello')];
		seen:push(item: Greeting:init(text: 'world'));
		local [Greeting] is alias: seen;
		alias:pop();
		Assert:areEqualInt(1, seen:length());
	}

	## Case 7: clear empties and the vector stays usable.
	Function is testClearStaysUsable(){
		local [String] is names: ['alice', 'bob'];
		names:clear();
		names:push(item: 'zed');
		Assert:areEqualInt(1, names:length());
		Assert:areEqualString('zed', names:get(index: 0));
	}

	## Case 8: fresh-insert ownership — fresh constructor claims transfer
	## into the container (no orphan), mixed with borrowed inserts in one
	## literal.
	Function is testFreshAndBorrowedInserts(){
		local [Greeting] is seen: [Greeting:init(text: 'hello')];
		seen:push(item: Greeting:init(text: 'world'));
		local Greeting is g1: seen:get(index: 1);

		local [Greeting] is fresh: [Greeting:init(text: 'lit1'), g1];
		fresh:push(item: Greeting:init(text: 'lit2'));
		fresh:set(index: 2, item: Greeting:init(text: 'lit3'));
		local Greeting is f1: fresh:get(index: 0);
		local Greeting is f2: fresh:get(index: 1);
		local Greeting is f3: fresh:get(index: 2);
		Assert:areEqualString('lit1', f1:getValue());
		Assert:areEqualString('world', f2:getValue());
		Assert:areEqualString('lit3', f3:getValue());
	}
}

Class is Greeting{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()]
	];
	local String is value: '';

	replace Function is init(String is text){
		:value: text;
	}

	Function of String is getValue(){
		return :value;
	}
}
