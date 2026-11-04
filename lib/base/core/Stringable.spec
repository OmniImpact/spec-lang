#! Package base:core
#! Root object contracts composed into the class lattice.

## Contract supplying a textual representation.
##
## Composed into the root class `Any` via inheritance; every class therefore
## satisfies this contract. Override `toString` with `replace` to customize.
Class is Stringable{

	## Renders this object as text.
	##
	## @return: Textual representation.
	replace Function of String is toString(){
	}
}
