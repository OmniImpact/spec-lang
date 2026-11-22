#! Package base:core
#! The result-return transport: a value or the error that replaced it.
##
## Jurisdiction (SPECDEV §8): sync operations whose failure is
## EXPECTED and for which no sensible default exists — parsing,
## decoding, lookups that can legitimately miss. "Never Null"
## default-parameter APIs remain the convenience face; this is the
## core they unwrap. Consume via `when` destructuring (construct
## dispatch) or the `try(...)` construct.
##
## The Err variant carries the full error currency — a `SpecError of
## E` with its kind enum, description, and captured stack trace — so
## a result converts to an unwind without information loss:
## `raiseError(try(r))`.

Enum is Result of T to E {
	Array of Array of String is using: [
		['base', 'core', SpecError]
	];

	namespace: ['base', 'core'];

	Ok(T is value),
	Err(SpecError of E is error)
}
