#! Package base:core
#! The root of the class lattice.

## Root class: every class without explicit parents implicitly inherits from
## `Any`, gaining default rendering, constructor behavior, and the `using`
## declaration slot. `toString` arrives via the [Stringable] contract.
Class of Stringable is Any{

	## Package dependencies declared by a class (Loader-consumed).
	replace Array of String is using: [];

	## Package namespace declaration slot: every class declares its canonical
	## package here (array form, last-segment = package leaf).
	replace Array of String is namespace: [];

	## Default constructor; subclasses override with their own `init` signature.
	replace Function is init(){
		return;
	}

	## Default textual rendering: the declaring class name.
	replace Function of String is toString(){
		return typeName(self);
	}
}
