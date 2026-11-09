#! Package base:sys
#! Public wrapper over the sysinternal Loadable root.

## The loadable surface: the wrapper through which the lattice
## (Stringable, Class, Enum) extends the floor's machinery defaults.
## The ONLY class allowed to call base:sysinternal:Loadable is the
## same-name wrapper (the sysinternal discipline).

Class of base:sysinternal:Loadable is Loadable{
	namespace: ['base', 'sys'];
}
