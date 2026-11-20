#! Package base:core
#! The declaration root: composes the [Stringable] contract (which
#! brings the Loadable machinery with it) and provides the default
#! rendering.

## Root of class DECLARATIONS. Reading this class answers "what does a
## class add to what it inherits": the default rendering
## (`TypeName@hash`). The machinery (`using`, `namespace`, `init`) is
## inherited through Stringable -> Loadable; the loader consumes each
## by name, and the constructor is synthesized when a class declares
## none.

Class of Stringable is Class{
	namespace: ['base', 'core'];

	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];
	## Default rendering: the declaring type name and the object's
	## identity hash (`TypeName@hash`). Implements the [Stringable]
	## contract; classes override with `replace` to customize.
	##
	## @return: Textual representation.
	replace Function of String is toString(){
		return typeName(:) . '@' . (Introspection:objectHash(obj: :) as String);
	}

	## Root fallback error handler: returns `false` so unhandled errors keep
	## bubbling up the stack until an enclosing handler returns `true` or the
	## error reaches the top of the stack and terminates the process.
	## Subclasses opt into intercepting bubbling errors with `replace`.
	Function of Boolean is SpecErrorHandler(SpecError is error){
		return false;
	}

	## Raises [error] on the current thread, unwinding the call stack cleanly
	## to the nearest enclosing [SpecErrorHandler] (or [Class:SpecErrorHandler]).
	Function is raiseError(SpecError is error){
		return;
	}
}
