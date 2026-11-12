#! SpecUnit sweep (from multifile_test.spec): multi-file and pure Spec
#! library smoke — the pure Spec base:math methods, the pure Spec Array
#! methods, a declared-then-assigned field, and the decoupled Loop
#! runner with the loop logic in a separate class.

Class of SpecUnitTest is TestMultifile{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'math'],
		['base', 'iterator'],
		['base', 'math', as Math()],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()]
	];

	# Declared variable initialized before use (the old suite's field)
	local String is title;
	local Int is counter: 0;

	## 1. Pure Spec Math library methods. The clamp arguments reach the
	## floor now — the builtin-call generator filled them by argument
	## index (the checker resolves named args into declaration order);
	## its old spelling-grep matched none of the declared parameter
	## names and shipped 0.0/0.0/1.0 defaults for every call.
	Function is testPureSpecMathMethods(){
		local Float is neg: -42.5;
		Assert:areClose(42.5, Math:abs(value: neg), 0.0001);
		Assert:areClose(10.0, Math:min(a: 10.0, b: 20.0), 0.0001);
		Assert:areClose(20.0, Math:max(a: 10.0, b: 20.0), 0.0001);
		Assert:areClose(10.0, Math:clamp(val: 15.0, minVal: 0.0, maxVal: 10.0), 0.0001);
		Assert:areClose(5.0, Math:clamp(val: 5.0, minVal: 0.0, maxVal: 10.0), 0.0001);
		Assert:areClose(0.0, Math:clamp(val: -5.0, minVal: 0.0, maxVal: 10.0), 0.0001);
	}

	## 2. Pure Spec Array methods: isEmpty, add.
	Function is testPureSpecArrayMethods(){
		local Array of String is emptyList: [];
		Assert:isTrue(emptyList:isEmpty());
		emptyList:add(item: 'First Item');
		Assert:isFalse(emptyList:isEmpty());
		Assert:areEqualInt(1, emptyList:length());
		Assert:areEqualString('First Item', emptyList:get(index: 0));
	}

	## The declared field: uninitialized at declaration, assigned before
	## the read.
	Function is testDeclaredFieldInitBeforeUse(){
		self:title: '=== Multi-File & Pure Spec Library Test ===';
		Assert:areEqualString('=== Multi-File & Pure Spec Library Test ===', self:title);
	}

	## 3. Decoupled Loop and Control: the loop logic lives in
	## StepCounterLoop, the runner drives it, the stop at five lands.
	Function is testDecoupledIteratorLoop(){
		Loops:run(loop: StepCounterLoop:init(app: self));
		Assert:areEqualInt(5, self:counter);
	}
}

## The decoupled loop body: a separate class (the old suite nested it,
## but the nesting is not what the suite exercises — the decoupling is;
## as a nested class its init replace now collides with the two init
## signatures the SpecUnitTest base contributes through the enclosing
## link). Holds the app reference and stops the run at five.
Class of Loop is StepCounterLoop{

	replace Array of Array of String is using: [
		['base', 'math', as Math()],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];
	local TestMultifile is app;

	replace Function is init(TestMultifile is app){
		self:app: app;
	}

	replace Function of Boolean is evaluate(){
		return app:counter < 10;
	}

	replace Function of Boolean is iteration(LoopControl is control){
		app:counter: app:counter + 1;
		Conditional:if(check: { app:counter == 5 }, then: {
			return false;
		});
		return true;
	}
}
