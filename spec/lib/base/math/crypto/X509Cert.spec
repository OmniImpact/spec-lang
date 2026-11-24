#! Package base:math:crypto
#! Parsed X.509 certificate metadata (subject/issuer DER hashes, CN, SAN DNS names).

Class is X509Cert{
	replace [String] is namespace: ['base', 'math', 'crypto'];

	replace [[String]] is using: [
		['base', 'struct', Array]
	];

	String is subjectHash: '';
	String is issuerHash: '';
	String is commonName: '';
	Array of String is sanDnsNames: Array();
	Boolean is valid: false;

	replace Function is init(){
		:sanDnsNames: Array();
	}
}
