Class is MultiFileTest{

	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:math:*,
		base:io:*,
		base:iterator:*
	];

	# Declared variable initialized in init before use
	local String is title;
	local Int is counter: 0;

	Class of Loop is StepCounterLoop{
		local MultiFileTest is app;

		replace Function is init(MultiFileTest is app){
			self:app: app;
		}

		replace Function of Boolean is evaluate(){
			return app:counter < 10;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			app:counter: app:counter + 1;
			if (app:counter == 5) {
				output:line('Stop reached at counter = ' . app:counter);
				return false;
			}
			return true;
		}
	}

	replace Function is init(Map of String to String is args){
		self:title: '=== Multi-File & Pure Spec Library Test ===';
		output:line(self:title);

		# 1. Pure Spec Math library methods
		output:line("\n--- Pure Spec Math Methods ---");
		local Float is neg: -42.5;
		output:line('abs(-42.5) = ' . math:abs(value: neg));
		output:line('min(10.0, 20.0) = ' . math:min(a: 10.0, b: 20.0));
		output:line('max(10.0, 20.0) = ' . math:max(a: 10.0, b: 20.0));
		output:line('clamp(15.0, 0.0, 10.0) = ' . math:clamp(val: 15.0, minVal: 0.0, maxVal: 10.0));

		# 2. Pure Spec Array method
		output:line("\n--- Pure Spec Array Methods ---");
		local Array of String is emptyList: [];
		output:line('emptyList:isEmpty() = ' . emptyList:isEmpty());
		emptyList:add(item: 'First Item');
		output:line('After add, emptyList:isEmpty() = ' . emptyList:isEmpty());

		# 3. Decoupled Loop and Control
		output:line("\n--- Decoupled Iterator Loop ---");
		While:run(loop: StepCounterLoop:init(app: self));
		output:line('Final counter value = ' . self:counter);

		output:line("\nAll multi-file and pure Spec tests completed successfully.");
	}

}
