#! Package base:cases
#! The match provider (PLAN-ENUM Stage 3): `when` without the keyword.

## One as-import serves the match construct bare —
## `match(on: subject, arms: [key: { body }, ...])` mirrors
## `Conditional`'s `if(...)`. Runtime-managed: [match] is intercepted
## by the compiler — the arm table resolves against the subject's
## class's held members at compile time and inlines into a comparison
## chain — so no body is emitted. The arm table is a map literal whose
## keys are held-member references (an array key matches several),
## `else` names the fallback arm, and the closures are the arm bodies
## (a closure's last expression is the arm's value).

Class is Cases{
	namespace: ['base', 'cases'];

	## Dispatches [on] over the arm table [arms].
	##
	## @param on: The subject value.
	## @param arms: The arm table: held-member keys (an array key
	## matches several), `else` for the fallback, closures as bodies.
	Function is match(Any is on, Map of Any to Any is arms){
	}
}
