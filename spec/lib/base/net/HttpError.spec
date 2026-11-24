#! Package base:net
#! The Http error kinds: the variant set for `SpecError of HttpError`
#! payloads on Http's callback surfaces.
##
## Variants mirror the failure modes Http actually reports: connection
## establishment (TLS/TCP), request send failures, malformed responses,
## and non-success status lines (the detail rides the description).

Enum is HttpError {
	replace [String] is namespace: ['base', 'net'];
	CONNECTION_FAILED,
	SEND_FAILED,
	INVALID_RESPONSE,
	HTTP_ERROR
}
