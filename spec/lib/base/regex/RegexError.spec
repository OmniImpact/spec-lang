#! Package base:regex
#! The Arex error kinds: the variant set for `SpecError of RegexError`
#! payloads on Arex's callback surfaces.
##
## Variants mirror the failure modes the regex surface actually reports:
## pattern compilation failures — malformed groups, invalid escapes,
## unsupported lookaround/backreference constructs — with the parser's
## detail text riding the SpecError description.

Enum is RegexError {
	namespace: ['base', 'regex'];
	COMPILE_FAILED
}
