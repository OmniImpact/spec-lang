#! Package base:compiler:opt
#! Discovers SpecOptimizer subclasses via Introspection and runs them in
#! deterministic (order, name) order over an IrModule.

Class is OptimizerPipeline{
	namespace: ['base', 'compiler', 'opt'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'opt', SpecOptimizer],
		['base', 'compiler', 'opt', ConstantFoldPass],
		['base', 'compiler', 'opt', PoolElisionPass],
		['base', 'compiler', 'opt', WrapperUnwrapPass],
		['base', 'compiler', 'ir', IrModule],
		['base', 'struct', Array],
		['base', 'struct', as Sort()],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Array of SpecOptimizer is passes: [];

	replace Function is init(){
		local Array of Any is found: Introspection:instantiateSubclasses(baseName: 'SpecOptimizer');
		Sort:sortBy(values: found, compare: local Function of Int(Any is a, Any is b){
			local SpecOptimizer is pa: a as SpecOptimizer;
			local SpecOptimizer is pb: b as SpecOptimizer;
			if({ pa:order() != pb:order() }, { return pa:order() - pb:order(); });
			if({ pa:name() < pb:name() }, { return -1; });
			if({ pa:name() > pb:name() }, { return 1; });
			return 0;
		});
		local Int is i: 0;
		while({ i < found:length() }, {
			self:passes:add(item: found:get(index: i) as SpecOptimizer);
			i++;
		});
	}

	Function is run(IrModule is mod){
		local Int is i: 0;
		while({ i < self:passes:length() }, {
			local SpecOptimizer is pass: self:passes:get(index: i);
			pass:runOnModule(mod: mod);
			i++;
		});
	}
}
