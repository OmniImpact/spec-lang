#! SpecUnit sweep (from next_gen_features_test.spec): next-generation
#! language features — functional combinators, default parameters with
#! call-site reordering, map literals and index assignment, user-defined
#! generics, capturing closures with direct invocation, and tagged
#! union enums with destructuring match.

Class of SpecUnitTest is TestNextGenFeatures{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	## Helper method demonstrating default parameter values and call-site reordering.
	local Function of String is greet(String is name, String is prefix: 'Hello', String is suffix: '!'){
		return prefix . ', ' . name . suffix;
	}

	## Helper method demonstrating multiple numeric default parameters.
	local Function of Int is calculate(Int is a, Int is b: 10, Int is c: 100){
		return (a * b) + c;
	}

	## Helper method to pattern match a Result variant in a when statement,
	## accumulating a tag per variant into [log].
	local Function is inspectResult(Result is res, Array of String is log){
		Conditional:match(on: res, when: [
			Result:Ok: local Function(String is d){
				log:add(item: 'Ok:' . d);
			},
			Result:Err: local Function(Int is c, String is m){
				log:add(item: 'Err:' . c . ':' . m);
			},
			Result:Pending: {
				log:add(item: 'Pending');
			}
		]);
	}

	## Verifies Feature 2: Functional Collection Combinators (Array:map, Array:fold, Map:each).
	Function is testCombinators(){
		# 1. Array:map transforming integers
		local Array of Int is nums: [1, 2, 3, 4, 5];
		local Array of Int is doubled: nums:map(transform: local Function of Int(Int is x){
			return x * 2;
		});
		Assert:areEqualInt(5, doubled:length());
		Assert:areEqualInt(2, doubled[0]);
		Assert:areEqualInt(10, doubled[4]);
		# 2. Array:fold accumulating sum
		local Int is sum: nums:fold(initial: 0, reducer: local Function of Int(Int is acc, Int is x){
			return acc + x;
		});
		Assert:areEqualInt(15, sum);
		# 3. Array:fold accumulating product
		local Int is product: nums:fold(initial: 1, reducer: local Function of Int(Int is acc, Int is x){
			return acc * x;
		});
		Assert:areEqualInt(120, product);
		# 4. Map:each iterating key-value entries
		local Map of String to Int is inventory: ['apples': 50, 'bananas': 120, 'oranges': 75];
		Assert:areEqualInt(3, inventory:length());
		local Array of String is visited: [];
		inventory:each(action: local Function(String is item, Int is qty){
			visited:add(item: item . '=' . qty);
		});
		Assert:areEqualInt(3, visited:length());
	}

	## Verifies Feature 3: Default Parameter Values and Call-Site Named-Argument Reordering.
	Function is testDefaultsAndReordering(){
		# All defaults used except required name
		local String is g1: self:greet(name: 'Spec');
		Assert:areEqualString('Hello, Spec!', g1);
		# Override suffix only, leaving prefix default
		local String is g2: self:greet(name: 'World', suffix: '.');
		Assert:areEqualString('Hello, World.', g2);
		# Reordered named arguments: suffix, prefix, name
		local String is g3: self:greet(suffix: '!!!', prefix: 'Welcome', name: 'Developer');
		Assert:areEqualString('Welcome, Developer!!!', g3);
		# Numeric defaults
		local Int is calc1: self:calculate(a: 5);
		Assert:areEqualInt(150, calc1);
		# Reordered numeric call omitting b
		local Int is calc2: self:calculate(c: 200, a: 3);
		Assert:areEqualInt(230, calc2);
	}

	## Verifies Feature 4: Map Literals and Index Assignment.
	Function is testMapLiteralsAndIndexAssignment(){
		# Initial map literal
		local Map of String to Int is scores: ['alice': 95, 'bob': 88];
		Assert:areEqualInt(2, scores:length());
		Assert:areEqualInt(95, scores['alice']);
		Assert:areEqualInt(88, scores['bob']);
		# L-value bracket assignment on Map
		scores['charlie']: 100;
		scores['alice']: 98;
		Assert:areEqualInt(3, scores:length());
		Assert:areEqualInt(100, scores['charlie']);
		Assert:areEqualInt(98, scores['alice']);
		# Empty map literal
		local Map of String to String is emptyMap: [:];
		Assert:areEqualInt(0, emptyMap:length());
		emptyMap['framework']: 'Spec Standard Library';
		Assert:areEqualInt(1, emptyMap:length());
		Assert:areEqualString('Spec Standard Library', emptyMap['framework']);
		# Array bracket index read and write
		local Array of String is languages: ['C', 'Rust', 'Spec'];
		Assert:areEqualString('C', languages[0]);
		Assert:areEqualString('Rust', languages[1]);
		Assert:areEqualString('Spec', languages[2]);
		languages[1]: 'Spec C11';
		Assert:areEqualString('Spec C11', languages[1]);
	}

	## Verifies Feature 5: User-Defined Generic Classes.
	Function is testGenericClasses(){
		# Single-parameter generic with String
		local Box of String is stringBox: Box:init(val: 'Generics in Spec');
		Assert:areEqualString('Generics in Spec', stringBox:get());
		stringBox:set(newVal: 'Updated Generic String');
		Assert:areEqualString('Updated Generic String', stringBox:get());
		# Single-parameter generic with Int
		local Box of Int is intBox: Box:init(val: 777);
		Assert:areEqualInt(777, intBox:get());
		intBox:set(newVal: 888);
		Assert:areEqualInt(888, intBox:get());
		# Multi-parameter generic Pair of String to Int
		local Pair of String to Int is pair: Pair:init(first: 'HTTP_PORT', second: 8080);
		Assert:areEqualString('HTTP_PORT', pair:getFirst());
		Assert:areEqualInt(8080, pair:getSecond());
		# Multi-parameter generic Pair of Int to String
		local Pair of Int to String is statusPair: Pair:init(first: 200, second: 'OK');
		Assert:areEqualInt(200, statusPair:getFirst());
		Assert:areEqualString('OK', statusPair:getSecond());
	}

	## Verifies Feature 6: First-Class Capturing Closures and Direct Function Invocation.
	Function is testClosuresAndDirectInvocation(){
		local Int is factor: 10;
		local Int is baseline: 5;
		# Closure capturing outer local variables 'factor' and 'baseline'
		local Function of Int is compute: local Function of Int(Int is x){
			return (x * factor) + baseline;
		};
		# Direct invocation of Function variable
		Assert:areEqualInt(35, compute(x: 3));
		Assert:areEqualInt(75, compute(x: 7));
		# Closure capturing a string prefix
		local String is tag: '[INFO]';
		local Function of String is logMsg: local Function of String(String is text){
			return tag . ' ' . text;
		};
		Assert:areEqualString('[INFO] Compiler ready', logMsg(text: 'Compiler ready'));
	}

	## Verifies Feature 7: Tagged Union Enums and Destructuring when.
	Function is testTaggedUnionEnums(){
		local Result is resOk: Result:Ok(data: 'Payload verified');
		local Result is resErr: Result:Err(code: 404, msg: 'Endpoint missing');
		local Result is resPending: Result:Pending;
		# When statement destructuring, accumulated into a log
		local Array of String is log: [];
		self:inspectResult(res: resOk, log: log);
		self:inspectResult(res: resErr, log: log);
		self:inspectResult(res: resPending, log: log);
		Assert:areEqualInt(3, log:length());
		Assert:areEqualString('Ok:Payload verified', log:get(index: 0));
		Assert:areEqualString('Err:404:Endpoint missing', log:get(index: 1));
		Assert:areEqualString('Pending', log:get(index: 2));
		# When expression destructuring
		local String is descOk: Conditional:match(on: resOk, when: [
			Result:Ok: local Function(String is d){ return 'Handled OK -> ' . d; },
			Result:Err: local Function(Int is c, String is m){ return 'Handled ERR ' . c . ': ' . m; },
			Result:Pending: { 'Awaiting resolution' }
		]);
		Assert:areEqualString('Handled OK -> Payload verified', descOk);
		local String is descErr: Conditional:match(on: resErr, when: [
			Result:Ok: local Function(String is d){ return 'Handled OK -> ' . d; },
			Result:Err: local Function(Int is c, String is m){ return 'Handled ERR ' . c . ': ' . m; },
			Result:Pending: { 'Awaiting resolution' }
		]);
		Assert:areEqualString('Handled ERR 404: Endpoint missing', descErr);
		local String is descPending: Conditional:match(on: resPending, when: [
			Result:Ok: local Function(String is d){ return 'Handled OK -> ' . d; },
			Result:Err: local Function(Int is c, String is m){ return 'Handled ERR ' . c . ': ' . m; },
			Result:Pending: { 'Awaiting resolution' }
		]);
		Assert:areEqualString('Awaiting resolution', descPending);
		# Option tagged enum testing
		local Option is someVal: Option:Some(value: 42);
		local Option is noneVal: Option:None;
		local Int is extracted: Conditional:match(on: someVal, when: [
			Option:Some: local Function(Int is v){ return v; },
			Option:None: { 0 }
		]);
		Assert:areEqualInt(42, extracted);
		local Int is extractedNone: Conditional:match(on: noneVal, when: [
			Option:Some: local Function(Int is v){ return v; },
			Option:None: { -1 }
		]);
		Assert:areEqualInt(-1, extractedNone);
	}
}

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

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

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

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

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
