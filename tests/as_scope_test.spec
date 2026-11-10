Class is AsScopeTest{

	replace Array of Array of String is using: [
		['base', 'sys', Output],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
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
		Conditional:if(check: { log1:length() == 4 && log1:get(index: 0) == 'open:file.txt' && log1:get(index: 1) == 'read:1' && log1:get(index: 2) == 'read:2' && log1:get(index: 3) == 'close:file.txt' }, then: {
			Output:line('[PASS] Parameterless as: helper();');
		}, else: {
			Output:line('[FAIL] Parameterless as: helper();');
		});
	}

	Function is testTypedParam(){
		local Int is receivedVal: 0;
		as (Int is x): self:withVal(val: 42);
		receivedVal: x + 8;
		Conditional:if(check: { receivedVal == 50 }, then: {
			Output:line('[PASS] Typed parameter as (Int is x):');
		}, else: {
			Output:line('[FAIL] Typed parameter as (Int is x): val=' . receivedVal);
		});
	}

	Function is testUntypedParam(){
		local String is untypedStr: '';
		as (s): self:withString(str: 'spec');
		untypedStr: 'hello ' . s;
		Conditional:if(check: { untypedStr == 'hello spec' }, then: {
			Output:line('[PASS] Untyped parameter as (s):');
		}, else: {
			Output:line('[FAIL] Untyped parameter as (s): str=' . untypedStr);
		});
	}

	Function is testMultipleTyped(){
		local String is pairStr: '';
		as (String is k, Int is v): self:withPair(key: 'alpha', val: 7);
		pairStr: k . '=' . v;
		Conditional:if(check: { pairStr == 'alpha=7' }, then: {
			Output:line('[PASS] Multiple typed parameters as (String is k, Int is v):');
		}, else: {
			Output:line('[FAIL] Multiple typed parameters as (String is k, Int is v): ' . pairStr);
		});
	}

	Function is testNestedPipeline(){
		local Array of String is pipelineLog: [];
		as (Int is a): self:withVal(val: 10);
		as (Int is b): self:withVal(val: a * 2);
		as (Int is c): self:withVal(val: b + 5);
		pipelineLog:add(item: '' . c);
		Conditional:if(check: { pipelineLog:length() == 1 && pipelineLog:get(index: 0) == '25' }, then: {
			Output:line('[PASS] Nested linear as chain');
		}, else: {
			Output:line('[FAIL] Nested linear as chain');
		});
	}

	Function is runNestedResources(Array of String is log){
		as: self:withResource(name: 'A', log: log);
		as: self:withResource(name: 'B', log: log);
		log:add(item: 'work');
	}

	Function is testNestedResources(){
		local Array of String is resLog: [];
		self:runNestedResources(log: resLog);
		Conditional:if(check: { resLog:length() == 5 && resLog:get(index: 0) == 'open:A' && resLog:get(index: 1) == 'open:B' && resLog:get(index: 2) == 'work' && resLog:get(index: 3) == 'close:B' && resLog:get(index: 4) == 'close:A' }, then: {
			Output:line('[PASS] Nested resource manager LIFO execution');
		}, else: {
			Output:line('[FAIL] Nested resource manager LIFO execution');
		});
	}

	Function is runContainerEach(Array of Int is nums, Array of Int is collected){
		as (n): nums:each();
		collected:add(item: n * 10);
	}

	Function is testContainerEach(){
		local Array of Int is nums: [1, 2, 3, 4];
		local Array of Int is collected: [];
		self:runContainerEach(nums: nums, collected: collected);
		Conditional:if(check: { collected:length() == 4 && collected:get(index: 0) == 10 && collected:get(index: 3) == 40 }, then: {
			Output:line('[PASS] Container each method with as (n):');
		}, else: {
			Output:line('[FAIL] Container each method with as (n):');
		});
	}

	Function of Int is testReturnValue(){
		return as of Int: self:computeWith(base: 2);
		return 5;
	}

	replace Function is init(Map of String to String is args){
		Output:line('=== As Scope Statement Test ===');
		self:testParameterless();
		self:testTypedParam();
		self:testUntypedParam();
		self:testMultipleTyped();
		self:testNestedPipeline();
		self:testNestedResources();
		self:testContainerEach();

		local Int is computed: self:computeWith(
			base: 3,
			block: local Function of Int(){
				return self:testReturnValue();
			}
		);
		Conditional:if(check: { computed == 30 }, then: {
			Output:line('[PASS] as of Type: callback return value');
		}, else: {
			Output:line('[FAIL] as of Type: callback return value, computed=' . computed);
		});
	}
}
