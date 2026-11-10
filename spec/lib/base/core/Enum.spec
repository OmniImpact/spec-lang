#! Package base:core
#! The enum root: every `Enum of <type> is Name` declaration inherits
#! the Loadable machinery through this root.

## Root of enum DECLARATIONS. The enum contract methods (name, ordinal,
## value, values, of) are synthesized per enum by the generator; this
## root supplies the Loadable machinery (the namespace, the using
## slot, the constructor) to every enum declaration. The identity
## contract (name, ordinal) moves onto this root as real, visible
## methods over the Introspection metadata floor in the next landing
## (the held metadata now carries the variant accessors).

Class of Loadable is Enum{
	namespace: ['base', 'core'];
}
