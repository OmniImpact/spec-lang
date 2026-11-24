#! Package base:sys
#! The Audio error kinds: the variant set for `SpecError of AudioError`
#! payloads on the audio callback surfaces.
##
## Variants mirror the failure modes the audio surface actually reports:
## device open failures (busy, unsupported rate or format) and write
## failures (invalid handle, driver errors) — the OS text rides the
## SpecError description.

Enum is AudioError {
	replace [String] is namespace: ['base', 'sys'];
	OPEN_FAILED,
	WRITE_FAILED
}
