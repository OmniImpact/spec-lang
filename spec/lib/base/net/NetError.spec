#! Package base:net
#! The Socket/Url error kinds: the variant set for
#! `SpecError of NetError` payloads on Socket and Url surfaces.
##
## Variants mirror the failure modes the net floor actually reports:
## connect/listen establishment failures, OS-level socket IO errors
## (errno text rides the description), and malformed URLs.

Enum is NetError {
	replace [String] is namespace: ['base', 'net'];
	CONNECT_FAILED,
	LISTEN_FAILED,
	IO_ERROR,
	INVALID_URL
}
