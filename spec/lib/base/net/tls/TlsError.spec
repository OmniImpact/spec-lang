#! Package base:net:tls
#! The TlsClient error kinds: the variant set for `SpecError of TlsError`
#! payloads on the TLS callback surfaces.
##
## Variants mirror the failure modes the TLS client actually reports:
## TCP establishment failures, TLS-protocol handshake failures (alerts,
## EOF, unsupported cipher suites or extensions, MAC/AEAD authentication),
## X.509 certificate verification failures, and send/receive errors on the
## established session — the specific text rides the SpecError description.

Enum is TlsError {
	replace [String] is namespace: ['base', 'net', 'tls'];
	CONNECT_FAILED,
	HANDSHAKE_FAILED,
	CERT_VERIFY_FAILED,
	SEND_FAILED,
	RECV_FAILED,
	NOT_CONNECTED
}
