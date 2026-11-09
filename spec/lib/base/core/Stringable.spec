#! Package base:core
#! Root object contracts composed into the class lattice.

## Contract supplying a textual representation.
##
## An interface and a ClassLoadable (of Loadable — the machinery comes
## with it): declares the `toString` contract ABSTRACT (no body — an
## interface method). [Class] provides the default implementation
## (`TypeName@hash`); classes override with `replace` to customize;
## overrides dispatch virtually through the contract's vtable slot.

Class of Loadable is Stringable{
	namespace: ['base', 'core'];

	## Renders this object as text.
	##
	## @return: Textual representation.
	Function of String is toString();
}
