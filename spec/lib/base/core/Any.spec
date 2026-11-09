#! Package base:core
#! The root of the class lattice: every VALUE is an Any.

## Root class: the pure identity root. Deliberately EMPTY — no members.
## "Anything is Any": every rootless class lands here through the
## implicit parent rule. The value contract (`toString`) lives on
## [Stringable]/[Class]; the declaration machinery (`using`,
## `namespace`, `init`) likewise.

Class is Any{
	namespace: ['base', 'core'];
}
