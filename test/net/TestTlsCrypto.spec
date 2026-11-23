#! Unit tests for pure-Spec TLS 1.3 cryptographic primitives:
#! SHA-256 (FIPS 180-4), HMAC-SHA256 (RFC 4231), X25519 (RFC 7748),
#! and ChaCha20-Poly1305 AEAD (RFC 8439).

Class of SpecUnitTest is TestTlsCrypto{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'math', 'crypto', as Sha256()],
		['base', 'math', 'crypto', as X25519()],
		['base', 'math', 'crypto', as ChaCha20Poly1305()],
		['base', 'math', 'crypto', as Aes128Gcm()],
		['base', 'math', 'crypto', X509Cert],
		['base', 'math', 'crypto', as X509()],
		['base', 'net', 'tls', as TlsVerifier()],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Array of Int is strBytes(String is s){
		local Array of Int is out: Array();
		local Int is i: 0;
		while({ i < s:byteLength() }, {
			out:add(item: s:byteAt(index: i, default: 0));
			i: i + 1;
		});
		return out;
	}

	local Function of Array of Int is hexBytes(String is hex){
		local Array of Int is out: Array();
		local Int is i: 0;
		while({ i + 1 < hex:length() }, {
			local String is pair: hex:substring(start: i, end: i + 2);
			out:add(item: pair:parseInt(base: 16, default: 0));
			i: i + 2;
		});
		return out;
	}

	Function is testSha256FipsVector(){
		local Array of Int is d: Sha256:digest(data: :strBytes(s: 'abc'));
		Assert:areEqualString('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad', Sha256:toHex(bytes: d));

		local Array of Int is dEmpty: Sha256:digest(data: Array());
		Assert:areEqualString('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', Sha256:toHex(bytes: dEmpty));
	}

	Function is testHmacSha256Rfc4231(){
		local Array of Int is mac: Sha256:hmac(key: :strBytes(s: 'Jefe'), msg: :strBytes(s: 'what do ya want for nothing?'));
		Assert:areEqualString('5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843', Sha256:toHex(bytes: mac));
	}

	Function is testX25519Rfc7748(){
		local Array of Int is alicePriv: :hexBytes(hex: '77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a');
		local Array of Int is alicePub: X25519:publicKey(privateKey: alicePriv);
		Assert:areEqualString('8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a', Sha256:toHex(bytes: alicePub));

		local Array of Int is bobPriv: :hexBytes(hex: '5dab087e624a8a4b79e17f8b83800ee66f3bb1292618b6fd1c2f8b27ff88e0eb');
		local Array of Int is bobPub: X25519:publicKey(privateKey: bobPriv);
		Assert:areEqualString('de9edb7d7b7dc1b4d35b61c2ece435373f8343c85b78674dadfc7e146f882b4f', Sha256:toHex(bytes: bobPub));

		local Array of Int is sharedA: X25519:scalarMult(scalar: alicePriv, uCoord: bobPub);
		local Array of Int is sharedB: X25519:scalarMult(scalar: bobPriv, uCoord: alicePub);
		Assert:areEqualString('4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742', Sha256:toHex(bytes: sharedA));
		Assert:areEqualString(Sha256:toHex(bytes: sharedA), Sha256:toHex(bytes: sharedB));
	}

	Function is testChaCha20Poly1305Rfc8439(){
		local Array of Int is key: :hexBytes(hex: '808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9f');
		local Array of Int is nonce: :hexBytes(hex: '070000004041424344454647');
		local Array of Int is aad: :hexBytes(hex: '50515253c0c1c2c3c4c5c6c7');
		local Array of Int is pt: :strBytes(s: "Ladies and Gentlemen of the class of '99: If I could offer you only one tip for the future, sunscreen would be it.");

		local Array of Int is ctTag: ChaCha20Poly1305:seal(key: key, nonce: nonce, aad: aad, plaintext: pt);
		local String is expectedHex: 'd31a8d34648e60db7b86afbc53ef7ec2a4aded51296e08fea9e2b5a736ee62d63dbea45e8ca9671282fafb69da92728b1a71de0a9e060b2905d6a5b67ecd3b3692ddbd7f2d778b8c9803aee328091b58fab324e4fad675945585808b4831d7bc3ff4def08e4b7a9de576d26586cec64b61161ae10b594f09e26a7e902ecbd0600691';
		Assert:areEqualString(expectedHex, Sha256:toHex(bytes: ctTag));

		local Array of Boolean is okOut: Array();
		local Array of Int is dec: ChaCha20Poly1305:open(key: key, nonce: nonce, aad: aad, ctWithTag: ctTag, okOut: okOut);
		Assert:isTrue(okOut:get(index: 0, default: false));
		Assert:areEqualString(Sha256:toHex(bytes: pt), Sha256:toHex(bytes: dec));
	}

	Function is testAes128GcmNistVector(){
		# NIST SP 800-38D Test Case 4 (AES-128-GCM with 96-bit IV, AAD, 60-byte plaintext)
		local Array of Int is key: :hexBytes(hex: 'feffe9928665731c6d6a8f9467308308');
		local Array of Int is iv: :hexBytes(hex: 'cafebabefacedbaddecaf888');
		local Array of Int is pt: :hexBytes(hex: 'd9313225f88406e5a55909c5aff5269a86a7a9531534f7da2e4c303d8a318a721c3c0c95956809532fcf0e2449a6b525b16aedf5aa0de657ba637b39');
		local Array of Int is aad: :hexBytes(hex: 'feedfacedeadbeeffeedfacedeadbeefabaddad2');

		local Array of Int is ctTag: Aes128Gcm:seal(key: key, nonce: iv, aad: aad, plaintext: pt);
		local String is expectedHex: '42831ec2217774244b7221b784d0d49ce3aa212f2c02a4e035c17e2329aca12e21d514b25466931c7d8f6a5aac84aa051ba30b396a0aac973d58e0915bc94fbc3221a5db94fae95ae7121a47';
		Assert:areEqualString(expectedHex, Sha256:toHex(bytes: ctTag));

		local Array of Boolean is okOut: Array();
		local Array of Int is dec: Aes128Gcm:open(key: key, nonce: iv, aad: aad, ctWithTag: ctTag, okOut: okOut);
		Assert:isTrue(okOut:get(index: 0, default: false));
		Assert:areEqualString(Sha256:toHex(bytes: pt), Sha256:toHex(bytes: dec));
	}

	Function is testX509Base64AndEmptyChain(){
		local Array of Int is decoded: X509:decodeBase64(text: 'SGVsbG8sIFNwZWMh');
		Assert:areEqualString(Sha256:toHex(bytes: :strBytes(s: 'Hello, Spec!')), Sha256:toHex(bytes: decoded));

		local Array of X509Cert is parsed: Array();
		local Array of String is errs: Array();
		Assert:isFalse(X509:verifyTrustChain(certChain: Array(), parsedOut: parsed, errOut: errs));
		Assert:isTrue(errs:length() > 0);
	}

	Function is testTlsVerifierHostnameMatching(){
		Assert:isTrue(TlsVerifier:patternMatchesHost(pattern: 'api.weather.gov', host: 'api.weather.gov'));
		Assert:isTrue(TlsVerifier:patternMatchesHost(pattern: 'API.Weather.GOV', host: 'api.weather.gov'));
		Assert:isTrue(TlsVerifier:patternMatchesHost(pattern: '*.weather.gov', host: 'api.weather.gov'));
		Assert:isFalse(TlsVerifier:patternMatchesHost(pattern: '*.weather.gov', host: 'a.b.weather.gov'));
		Assert:isFalse(TlsVerifier:patternMatchesHost(pattern: '*.weather.gov', host: 'weather.gov'));

		# SAN takes precedence over CN when present
		local X509Cert is cert: X509Cert:init();
		cert:valid: true;
		cert:commonName: 'fallback.example.com';
		cert:sanDnsNames:add(item: '*.weather.gov');
		Assert:isTrue(TlsVerifier:matchesHost(cert: cert, host: 'api.weather.gov'));
		Assert:isFalse(TlsVerifier:matchesHost(cert: cert, host: 'fallback.example.com'));

		# CN fallback when no SAN entries exist
		local X509Cert is cnOnly: X509Cert:init();
		cnOnly:valid: true;
		cnOnly:commonName: 'fallback.example.com';
		Assert:isTrue(TlsVerifier:matchesHost(cert: cnOnly, host: 'fallback.example.com'));
	}
}
