Class is MultiFileTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'math'],
		['base', 'io'],
		['base', 'iterator'],
		['base', 'math', as Math()],
		['base', 'io', as Output()],
		['base', 'iterator', as While()]
	];

	# Declared variable initialized in init before use
	local String is title;
	local Int is counter: 0;

	Class of Loop is StepCounterLoop{

		replace Array of Array of String is using: [
			['base', 'math', as Math()],
			['base', 'io', as Output()],
			['base', 'iterator', as While()],
		['base', 'sys', as Conditional()],
		];
		local MultiFileTest is app;

		replace Function is init(MultiFileTest is app){
			self:app: app;
		}

		replace Function of Boolean is evaluate(){
			return app:counter < 10;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			app:counter: app:counter + 1;
			Conditional:branch(check: { app:counter == 5 }, then: {
				Output:line('Stop reached at counter = ' . app:counter);
				return false;
			});
			return true;
		}
	}

	replace Function is init(Map of String to String is args){
		self:title: '=== Multi-File & Pure Spec Library Test ===';
		Output:line(self:title);

		# 1. Pure Spec Math library methods
		Output:line("\n--- Pure Spec Math Methods ---");
		local Float is neg: -42.5;
		Output:line('abs(-42.5) = ' . Math:abs(value: neg));
		Output:line('min(10.0, 20.0) = ' . Math:min(a: 10.0, b: 20.0));
		Output:line('max(10.0, 20.0) = ' . Math:max(a: 10.0, b: 20.0));
		Output:line('clamp(15.0, 0.0, 10.0) = ' . Math:clamp(val: 15.0, minVal: 0.0, maxVal: 10.0));

		# 2. Pure Spec Array method
		Output:line("\n--- Pure Spec Array Methods ---");
		local Array of String is emptyList: [];
		Output:line('emptyList:isEmpty() = ' . emptyList:isEmpty());
		emptyList:add(item: 'First Item');
		Output:line('After add, emptyList:isEmpty() = ' . emptyList:isEmpty());

		# 3. Decoupled Loop and Control
		Output:line("\n--- Decoupled Iterator Loop ---");
		While:run(loop: StepCounterLoop:init(app: self));
		Output:line('Final counter value = ' . self:counter);

		Output:line("\nAll multi-file and pure Spec tests completed successfully.");
	}

}
