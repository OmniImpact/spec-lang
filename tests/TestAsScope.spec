#! SpecUnit sweep (from as_scope_test.spec): the as-statement forms —
#! parameterless, typed/untyped parameters, multiple typed parameters,
#! the nested pipeline, LIFO resource nesting, container each, and the
#! as-of-Type callback return.

Class of SpecUnitTest is TestAsScope{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array]
	];

	Function is withResource(String is name, Array of String is log, Function is block){
		log:add(item: 'open:' . name);
		block();
		log:add(item: 'close:' . name);
	}

	Function is withVal(Int is val, Function is block){
		block(val);
	}

	Function is withString(String is str, Function is block){
		block(str);
	}

	Function is withPair(String is key, Int is val, Function is block){
		block(key, val);
	}

	Function of Int is computeWith(Int is base, Function of Int is block){
		return block() * base;
	}

	Function is runResource(Array of String is log){
		as: self:withResource(name: 'file.txt', log: log);
		log:add(item: 'read:1');
		log:add(item: 'read:2');
	}

	Function is testParameterless(){
		local Array of String is log1: [];
		self:runResource(log: log1);
		Assert:isTrue(log1:length() == 4 && log1:get(index: 0) == 'open:file.txt' && log1:get(index: 1) == 'read:1' && log1:get(index: 2) == 'read:2' && log1:get(index: 3) == 'close:file.txt');
	}

	Function is testTypedParam(){
		local Int is receivedVal: 0;
		as (Int is x): self:withVal(val: 42);
		receivedVal: x + 8;
		Assert:areEqualInt(50, receivedVal);
	}

	Function is testUntypedParam(){
		local String is untypedStr: '';
		as (s): self:withString(str: 'spec');
		untypedStr: 'hello ' . s;
		Assert:areEqualString('hello spec', untypedStr);
	}

	Function is testMultipleTyped(){
		local String is pairStr: '';
		as (String is k, Int is v): self:withPair(key: 'alpha', val: 7);
		pairStr: k . '=' . v;
		Assert:areEqualString('alpha=7', pairStr);
	}

	Function is testNestedPipeline(){
		as (Int is a): self:withVal(val: 10);
		as (Int is b): self:withVal(val: a * 2);
		as (Int is c): self:withVal(val: b + 5);
		Assert:areEqualInt(25, c);
	}

	Function is runNestedResources(Array of String is log){
		as: self:withResource(name: 'A', log: log);
		as: self:withResource(name: 'B', log: log);
		log:add(item: 'work');
	}

	Function is testNestedResources(){
		local Array of String is resLog: [];
		self:runNestedResources(log: resLog);
		Assert:isTrue(resLog:length() == 5 && resLog:get(index: 0) == 'open:A' && resLog:get(index: 1) == 'open:B' && resLog:get(index: 2) == 'work' && resLog:get(index: 3) == 'close:B' && resLog:get(index: 4) == 'close:A');
	}

	Function is runContainerEach(Array of Int is nums, Array of Int is collected){
		as (n): nums:each();
		collected:add(item: n * 10);
	}

	Function is testContainerEach(){
		local Array of Int is nums: [1, 2, 3, 4];
		local Array of Int is collected: [];
		self:runContainerEach(nums: nums, collected: collected);
		Assert:isTrue(collected:length() == 4 && collected:get(index: 0) == 10 && collected:get(index: 3) == 40);
	}

	## The as-of-Type callback return: the scoped call's value flows out
	## through the return.
	Function of Int is scopedValue(){
		return as of Int: self:computeWith(base: 2);
		return 5;
	}

	Function is testAsOfTypeCallback(){
		local Int is computed: self:computeWith(
			base: 3,
			block: local Function of Int(){
				return self:scopedValue();
			}
		);
		Assert:areEqualInt(30, computed);
	}
}
