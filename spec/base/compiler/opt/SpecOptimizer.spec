#! Package base:compiler:opt
#! Base class for pluggable IR optimization passes.
##
## Subclasses are discovered via Introspection at compiler startup, sorted
## deterministically by (order(), name()), and executed on the IR module.

Class is SpecOptimizer{
	replace [String] is namespace: ['base', 'compiler', 'opt'];

	replace [[String]] is using: [
		['base', 'compiler', 'ir', IrModule],
		['base', 'compiler', 'ir', IrFunction],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	replace Function is init(){
		return;
	}

	## Human-readable pass identifier (also used as deterministic tie-breaker).
	Function of String is name(){
		return 'SpecOptimizer';
	}

	## Deterministic pipeline ordering key (lower runs earlier).
	Function of Int is order(){
		return 100;
	}

	## Module-level optimization hook. Default delegates to runOnFunction()
	## for each non-external function in [mod].
	Function is runOnModule(IrModule is mod){
		local Int is i: 0;
		while({ i < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: i);
			if({ !fn:isExternal }, {
				:runOnFunction(fn: fn);
			});
			i++;
		});
	}

	## Function-level optimization hook.
	Function is runOnFunction(IrFunction is fn){
	}
}
