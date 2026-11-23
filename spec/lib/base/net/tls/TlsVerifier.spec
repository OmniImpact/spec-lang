#! Package base:net:tls
#! TLS server-identity verification: RFC 6125 DNS wildcard hostname matching
#! layered over base:math:crypto:X509 certificate chain verification.

Class is TlsVerifier{
	namespace: ['base', 'net', 'tls'];

	replace Array of Array of String is using: [
		['base', 'math', 'crypto', X509Cert],
		['base', 'math', 'crypto', as X509()],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## RFC 6125 hostname matching (exact or single-label wildcard `*.domain`).
	Function of Boolean is patternMatchesHost(String is pattern, String is host){
		local String is p: pattern:toLower():trim();
		local String is h: host:toLower():trim();
		if({ p == '' || h == '' }, { return false; });
		if({ p == h }, { return true; });
		if({ p:startsWith(prefix: '*.') }, {
			local String is suffix: p:substring(start: 1, end: p:length());
			if({ h:endsWith(suffix: suffix) && h:length() > suffix:length() }, {
				local String is prefix: h:substring(start: 0, end: h:length() - suffix:length());
				return !prefix:contains(needle: '.');
			});
		});
		return false;
	}

	## Returns `true` when [host] matches [cert]'s SAN dNSName entries
	## (or Subject CN when no SAN dNSName entries are present).
	Function of Boolean is matchesHost(X509Cert is cert, String is host){
		if({ !cert:valid }, { return false; });
		if({ cert:sanDnsNames:length() > 0 }, {
			local Boolean is matched: false;
			local Int is i: 0;
			while({ i < cert:sanDnsNames:length() }, local Function of Boolean(){
				if({ :patternMatchesHost(pattern: cert:sanDnsNames:get(index: i, default: ''), host: host) }, {
					matched: true;
					return false;
				});
				i: i + 1;
				return true;
			});
			return matched;
		});
		return :patternMatchesHost(pattern: cert:commonName, host: host);
	}

	## Verifies a TLS server certificate chain against [host] and the OS CA store.
	Function of Boolean is verifyServerChain(Array of Array of Int is certChain, String is host, Array of String is errOut){
		local Array of X509Cert is parsed: Array();
		if({ !X509:verifyTrustChain(certChain: certChain, parsedOut: parsed, errOut: errOut) }, {
			return false;
		});
		local X509Cert is leaf: parsed:get(index: 0);
		if({ !:matchesHost(cert: leaf, host: host) }, {
			errOut:add(item: "Certificate hostname mismatch for '" . host . "' (CN='" . leaf:commonName . "')");
			return false;
		});
		return true;
	}
}
