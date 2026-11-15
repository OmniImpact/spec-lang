#! Package base:compiler:opt
#! Discovers SpecOptimizer subclasses via Introspection and runs them in
#! deterministic (order, name) order over an IrModule.

Class is OptimizerPipeline{
	namespace: ['base', 'compiler', 'opt'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'opt', SpecOptimizer],
		['base', 'compiler', 'opt', ConstantFoldPass],
		['base', 'compiler', 'ir', IrModule],
		['base', 'struct', Array],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Array of SpecOptimizer is passes: [];

	replace Function is init(){
		local Array of String is names: Introspection:classNames();
		local Array of SpecOptimizer is found: [];
		local Int is i: 0;
		while({ i < names:length() }, {
			local String is cname: names:get(index: i, default: '');
			if({ cname != 'SpecOptimizer' && Introspection:extendsClass(className: cname, baseName: 'SpecOptimizer') }, {
				local SpecOptimizer is opt: Introspection:instantiate(className: cname) as SpecOptimizer;
				found:add(item: opt);
			});
			i++;
		});
		# Deterministic insertion sort by (order, name)
		local Int is n: found:length();
		local Int is k: 1;
		while({ k < n }, {
			local SpecOptimizer is cur: found:get(index: k);
			local Int is j: k - 1;
			local Boolean is shifting: true;
			while({ shifting && j >= 0 }, {
				local SpecOptimizer is prev: found:get(index: j);
				local Boolean is after: (prev:order() > cur:order()) || (prev:order() == cur:order() && prev:name() > cur:name());
				if({ after }, {
					found:set(index: j + 1, item: prev);
					j--;
				}, {
					shifting: false;
				});
			});
			found:set(index: j + 1, item: cur);
			k++;
		});
		self:passes: found;
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
