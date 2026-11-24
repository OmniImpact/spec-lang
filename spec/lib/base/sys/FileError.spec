#! Package base:sys
#! The File error kinds: the variant set for `SpecError of FileError`
#! payloads on File's callback and result surfaces.
##
## Variants mirror the failure modes the File surface actually reports:
## malformed paths, allocation failure during buffering, and OS-level
## read/write errors (the errno text rides the SpecError description).

Enum is FileError {
	replace [String] is namespace: ['base', 'sys'];
	INVALID_PATH,
	OUT_OF_MEMORY,
	IO_ERROR
}
