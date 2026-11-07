#! Package examples
#! Comprehensive test suite and verification for Spec next-generation language features.

## Tagged union enum representing an operation outcome with payload variants.
Enum is Result {
	Ok(String is data),
	Err(Int is code, String is msg),
	Pending
}

## Tagged union enum representing an optional integer value.
Enum is Option {
	Some(Int is value),
	None
}

## Generic single-value container class demonstrating user-defined generic type parameters.
Class is Box of T{

	## Stored value of generic type T.
	local T is val;

	## Initializes the box with a value.
	##
	## @param val: Initial value.
	replace Function is init(T is val){
		self:val: val;
	}

	## Retrieves the stored value.
	##
	## @return: Stored value of type T.
	Function of T is get(){
		return self:val;
	}

	## Updates the stored value.
	##
	## @param newVal: New value to store.
	Function is set(T is newVal){
		self:val: newVal;
	}

}

## Generic pair container class demonstrating multi-parameter user-defined generics.
Class is Pair of A to B{

	## First item in pair.
	local A is first;

	## Second item in pair.
	local B is second;

	## Initializes the pair with two values.
	##
	## @param first: First value of type A.
	## @param second: Second value of type B.
	replace Function is init(A is first, B is second){
		self:first: first;
		self:second: second;
	}

	## Retrieves the first value.
	##
	## @return: Value of type A.
	Function of A is getFirst(){
		return self:first;
	}

	## Retrieves the second value.
	##
	## @return: Value of type B.
	Function of B is getSecond(){
		return self:second;
	}

}

## Main test suite validating next-generation language features.
Class is NextGenFeaturesTest{

	replace Array of Array of String is using: [
		['base', 'io'],
		['base', 'struct', Array],
		['base', 'struct', Map],
	];

	## Helper method demonstrating default parameter values and call-site reordering.
	##
	## @param name: Target name string.
	## @param prefix: Salutation prefix with default.
	## @param suffix: Punctuation suffix with default.
	## @return: Formatted greeting.
	local Function of String is greet(String is name, String is prefix: 'Hello', String is suffix: '!'){
		return prefix . ', ' . name . suffix;
	}

	## Helper method demonstrating multiple numeric default parameters.
	##
	## @param a: Base value.
	## @param b: Intermediate factor with default.
	## @param c: Offset with default.
	## @return: Calculated integer result.
	local Function of Int is calculate(Int is a, Int is b: 10, Int is c: 100){
		return (a * b) + c;
	}

	## Verifies Feature 2: Functional Collection Combinators (Array:map, Array:fold, Map:each).
	local Function is testCombinators(){
		output:line('--- Feature 2: Functional Collection Combinators ---');

		# 1. Array:map transforming integers
		local Array of Int is nums: [1, 2, 3, 4, 5];
		local Array of Int is doubled: nums:map(transform: local Function of Int(Int is x){
			return x * 2;
		});
		output:line('Original length: ' . nums:length() . ', doubled length: ' . doubled:length());
		output:line('doubled[0]: ' . doubled[0] . ', doubled[4]: ' . doubled[4]);

		# 2. Array:fold accumulating sum
		local Int is sum: nums:fold(initial: 0, reducer: local Function of Int(Int is acc, Int is x){
			return acc + x;
		});
		output:line('Fold sum: ' . sum);

		# 3. Array:fold accumulating product
		local Int is product: nums:fold(initial: 1, reducer: local Function of Int(Int is acc, Int is x){
			return acc * x;
		});
		output:line('Fold product: ' . product);

		# 4. Map:each iterating key-value entries
		local Map of String to Int is inventory: ['apples': 50, 'bananas': 120, 'oranges': 75];
		output:line('Inventory entries count: ' . inventory:length());
		inventory:each(action: local Function(String is item, Int is qty){
			output:line('Item: ' . item . ' => Quantity: ' . qty);
		});
	}

	## Verifies Feature 3: Default Parameter Values and Call-Site Named-Argument Reordering.
	local Function is testDefaultsAndReordering(){
		output:line('--- Feature 3: Default Parameter Values & Named Argument Reordering ---');

		# All defaults used except required name
		local String is g1: self:greet(name: 'Spec');
		output:line('g1 (default prefix/suffix): ' . g1);

		# Override suffix only, leaving prefix default
		local String is g2: self:greet(name: 'World', suffix: '.');
		output:line('g2 (override suffix): ' . g2);

		# Reordered named arguments: suffix, prefix, name
		local String is g3: self:greet(suffix: '!!!', prefix: 'Welcome', name: 'Developer');
		output:line('g3 (fully reordered): ' . g3);

		# Numeric defaults
		local Int is calc1: self:calculate(a: 5);
		output:line('calculate(a: 5): ' . calc1);

		# Reordered numeric call omitting b
		local Int is calc2: self:calculate(c: 200, a: 3);
		output:line('calculate(c: 200, a: 3): ' . calc2);
	}

	## Verifies Feature 4: Map Literals and Index Assignment.
	local Function is testMapLiteralsAndIndexAssignment(){
		output:line('--- Feature 4: Map Literals & Index Assignment ---');

		# Initial map literal
		local Map of String to Int is scores: ['alice': 95, 'bob': 88];
		output:line('Initial scores length: ' . scores:length());
		output:line('scores[\'alice\']: ' . scores['alice']);
		output:line('scores[\'bob\']: ' . scores['bob']);

		# L-value bracket assignment on Map
		scores['charlie']: 100;
		scores['alice']: 98;
		output:line('Updated scores length: ' . scores:length());
		output:line('scores[\'charlie\']: ' . scores['charlie']);
		output:line('Updated scores[\'alice\']: ' . scores['alice']);

		# Empty map literal
		local Map of String to String is emptyMap: [:];
		output:line('emptyMap length before insertion: ' . emptyMap:length());
		emptyMap['framework']: 'Spec Standard Library';
		output:line('emptyMap length after insertion: ' . emptyMap:length());
		output:line('emptyMap[\'framework\']: ' . emptyMap['framework']);

		# Array bracket index read and write
		local Array of String is languages: ['C', 'Rust', 'Spec'];
		output:line('languages[0]: ' . languages[0]);
		output:line('languages[1]: ' . languages[1]);
		output:line('languages[2]: ' . languages[2]);

		languages[1]: 'Spec C11';
		output:line('Updated languages[1]: ' . languages[1]);
	}

	## Verifies Feature 5: User-Defined Generic Classes.
	local Function is testGenericClasses(){
		output:line('--- Feature 5: User-Defined Generic Classes ---');

		# Single-parameter generic with String
		local Box of String is stringBox: Box:init(val: 'Generics in Spec');
		output:line('stringBox get: ' . stringBox:get());
		stringBox:set(newVal: 'Updated Generic String');
		output:line('stringBox get after set: ' . stringBox:get());

		# Single-parameter generic with Int
		local Box of Int is intBox: Box:init(val: 777);
		output:line('intBox get: ' . intBox:get());
		intBox:set(newVal: 888);
		output:line('intBox get after set: ' . intBox:get());

		# Multi-parameter generic Pair of String to Int
		local Pair of String to Int is pair: Pair:init(first: 'HTTP_PORT', second: 8080);
		output:line('Pair key: ' . pair:getFirst() . ', value: ' . pair:getSecond());

		# Multi-parameter generic Pair of Int to String
		local Pair of Int to String is statusPair: Pair:init(first: 200, second: 'OK');
		output:line('Status code: ' . statusPair:getFirst() . ', text: ' . statusPair:getSecond());
	}

	## Verifies Feature 6: First-ClassInfo Capturing Closures and Direct Function Invocation.
	local Function is testClosuresAndDirectInvocation(){
		output:line('--- Feature 6: First-ClassInfo Capturing Closures & Direct Invocation ---');

		local Int is factor: 10;
		local Int is baseline: 5;

		# Closure capturing outer local variables 'factor' and 'baseline'
		local Function of Int is compute: local Function of Int(Int is x){
			return (x * factor) + baseline;
		};

		# Direct invocation of Function variable
		local Int is r1: compute(x: 3);
		local Int is r2: compute(x: 7);
		output:line('compute(x: 3): ' . r1);
		output:line('compute(x: 7): ' . r2);

		# Closure capturing a string prefix
		local String is tag: '[INFO]';
		local Function of String is logMsg: local Function of String(String is text){
			return tag . ' ' . text;
		};
		local String is formatted: logMsg(text: 'Compiler ready');
		output:line('logMsg: ' . formatted);
	}

	## Verifies Feature 7: Tagged Union Enums and Destructuring when.
	local Function is testTaggedUnionEnums(){
		output:line('--- Feature 7: Tagged Union Enums & Destructuring When ---');

		local Result is resOk: Result:Ok(data: 'Payload verified');
		local Result is resErr: Result:Err(code: 404, msg: 'Endpoint missing');
		local Result is resPending: Result:Pending;

		# When statement destructuring
		output:line('Destructuring in when statement:');
		self:inspectResult(res: resOk);
		self:inspectResult(res: resErr);
		self:inspectResult(res: resPending);

		# When expression destructuring
		local String is descOk: when (resOk) {
			is Ok(d): 'Handled OK -> ' . d;
			is Err(c, m): 'Handled ERR ' . c . ': ' . m;
			is Pending: 'Awaiting resolution';
		};
		output:line('descOk: ' . descOk);

		local String is descErr: when (resErr) {
			is Ok(d): 'Handled OK -> ' . d;
			is Err(c, m): 'Handled ERR ' . c . ': ' . m;
			is Pending: 'Awaiting resolution';
		};
		output:line('descErr: ' . descErr);

		local String is descPending: when (resPending) {
			is Ok(d): 'Handled OK -> ' . d;
			is Err(c, m): 'Handled ERR ' . c . ': ' . m;
			is Pending: 'Awaiting resolution';
		};
		output:line('descPending: ' . descPending);

		# Option tagged enum testing
		local Option is someVal: Option:Some(value: 42);
		local Option is noneVal: Option:None;

		local Int is extracted: when (someVal) {
			is Some(v): v;
			is None: 0;
		};
		output:line('Option:Some extracted: ' . extracted);

		local Int is extractedNone: when (noneVal) {
			is Some(v): v;
			is None: -1;
		};
		output:line('Option:None extracted: ' . extractedNone);
	}

	## Helper method to pattern match a Result variant in a when statement.
	##
	## @param res: Target Result instance to inspect.
	local Function is inspectResult(Result is res){
		when (res) {
			is Ok(d): {
				output:line('  [when stmt] Result:Ok with data: ' . d);
			}
			is Err(c, m): {
				output:line('  [when stmt] Result:Err with code ' . c . ', msg: ' . m);
			}
			is Pending: {
				output:line('  [when stmt] Result:Pending variant');
			}
		}
	}

	## Entry point executing all verification tests.
	##
	## @param args: Command line arguments map.
	replace Function is init(Map of String to String is args){
		output:line('==================================================');
		output:line(' Spec Next-Generation Language Features Test Suite');
		output:line('==================================================');

		self:testCombinators();
		self:testDefaultsAndReordering();
		self:testMapLiteralsAndIndexAssignment();
		self:testGenericClasses();
		self:testClosuresAndDirectInvocation();
		self:testTaggedUnionEnums();

		output:line('==================================================');
		output:line(' All Next-Gen Feature Tests Passed Successfully! ');
		output:line('==================================================');
	}

}
