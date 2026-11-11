#! Package base:core
#! The enum root: every `Enum of <type> is Name` declaration inherits
#! the Loadable machinery through this root, and the reflective half of
#! the enum contract — the identity scan — is implemented HERE, once,
#! over the Introspection metadata floor.

## Root of enum DECLARATIONS. The identity contract (name, ordinal)
## lives on this root as real methods: a desugared enum's variants are
## HELD singletons in declaration order, so asking the metadata floor
## which held slot is the receiver answers both name and ordinal for
## every enum at once. The per-enum remainder (value, of, values, the
## toString render) is synthesized by the compiler's EnumDesugar
## (spec/base/compiler/parser/EnumDesugar.spec) from the variant
## list — it needs the variant types and the backing field, which only
## the desugared class has. Tagged enums (payload variants) override
## name/ordinal with their field readers, also synthesized.

Class of Loadable is Enum{
	namespace: ['base', 'core'];

	replace Array of Array of String is using: [
		['base', 'sys', as Introspection()],
		['base', 'sys', as Conditional()]
	];

	## The variant name of the receiver — the reflective identity scan
	## over the class's held members (the desugared variants are the
	## held fields, declaration order). The scan runs the held
	## once-guards, so first touch constructs every variant singleton.
	##
	## @return: The variant name; '' when the receiver is not a variant.
	Function of String is name(){
		local Int is idx: Introspection:heldIndexOf(obj: self);
		if({ idx >= 0 }, {
			return Introspection:heldName(obj: self, index: idx);
		});
		return '';
	}

	## The declaration-order index of the receiver — the same scan
	## name() runs (the held table preserves declaration order).
	##
	## @return: The ordinal; -1 when the receiver is not a variant.
	Function of Int is ordinal(){
		return Introspection:heldIndexOf(obj: self);
	}
}
