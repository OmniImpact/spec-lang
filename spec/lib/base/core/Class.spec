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
		['base', 'sys', as Introspection()]
	];
	## Default rendering: the declaring type name and the object's
	## identity hash (`TypeName@hash`). Implements the [Stringable]
	## contract; classes override with `replace` to customize.
	##
	## @return: Textual representation.
	replace Function of String is toString(){
		return typeName(self) . '@' . (Introspection:objectHash(obj: self) as String);
	}
}
