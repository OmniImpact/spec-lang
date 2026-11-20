#! Package base:data
#! The Json error kinds: the variant set for `SpecError of JsonError`
#! payloads as Json migrates from the held side channel to results
#! (ERRORS-PLAN.md 3.1).
##
## Variants cover malformed text (offset rides the description),
## structure/type mismatches on typed getters, and absent keys.

Enum is JsonError {
	namespace: ['base', 'data'];
	SYNTAX_ERROR,
	TYPE_MISMATCH,
	MISSING_KEY
}
