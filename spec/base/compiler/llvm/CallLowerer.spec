#! Package base:compiler:llvm
#! Base class for pluggable call lowering handlers in IrBuilder.
##
## Subclasses are discovered via Introspection, sorted deterministically by
## (order(), name()), and consulted by IrBuilder:lowerCall() before falling
## back to general method/constructor dispatch.

Class is CallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'llvm', IrBuilder]
	];

	replace Function is init(){
		return;
	}

	Function of String is name(){
		return 'CallLowerer';
	}

	Function of Int is order(){
		return 100;
	}

	Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		return false;
	}

	Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		return '0';
	}
}
