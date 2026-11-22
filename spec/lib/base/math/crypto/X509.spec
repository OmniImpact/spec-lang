#! Package base:math:crypto
#! Pure-Spec X.509 ASN.1 DER certificate parser, PEM/Base64 decoder,
#! OS root CA trust store loader, and certificate chain validator.

Class is X509TrustStore{
	namespace: ['base', 'math', 'crypto'];

	replace Array of Array of String is using: [
		['base', 'struct', Map],
		['base', 'struct', Array]
	];

	held Map of String to Boolean is rootSubjectHashes: Map:init();
	held Array of Boolean is loadedFlag: [];
}

Class is X509{
	namespace: ['base', 'math', 'crypto'];

	replace Array of Array of String is using: [
		['base', 'math', 'crypto', X509Cert],
		['base', 'core', SpecError],
		['base', 'sys', FileError],
		['base', 'math', 'crypto', as Sha256()],
		['base', 'struct', Array],
		['base', 'struct', List],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as File()],
		['base', 'sys', as Parallel()]
	];

	## Reads one ASN.1 DER TLV header at [pos] in [der].
	## Returns [tag, contentStart, contentLen, nextPos], or [-1, 0, 0, 0] on error.
	local Function of Array of Int is readTlv(Array of Int is der, Int is pos, Int is limit){
		if({ pos + 2 > limit }, { return [-1, 0, 0, 0]; });
		local Int is tag: der:get(index: pos, default: 0) & 255;
		local Int is l0: der:get(index: pos + 1, default: 0) & 255;
		local Int is contentStart: pos + 2;
		local Int is len: 0;
		if({ (l0 & 128) == 0 }, {
			len: l0;
		}, {
			local Int is numOctets: l0 & 127;
			if({ numOctets == 0 || numOctets > 4 || (contentStart + numOctets) > limit }, {
				return [-1, 0, 0, 0];
			});
			local Int is i: 0;
			while({ i < numOctets }, {
				len: (len << 8) | (der:get(index: contentStart + i, default: 0) & 255);
				i: i + 1;
			});
			contentStart: contentStart + numOctets;
		});
		if({ contentStart + len > limit }, { return [-1, 0, 0, 0]; });
		return [tag, contentStart, len, contentStart + len];
	}

	local Function of Array of Int is sliceRange(Array of Int is src, Int is start, Int is len){
		local Array of Int is out: [];
		local Int is i: 0;
		while({ i < len && (start + i) < src:length() }, {
			out:add(item: src:get(index: start + i, default: 0) & 255);
			i: i + 1;
		});
		return out;
	}

	local Function of String is bytesToAscii(Array of Int is src, Int is start, Int is len){
		local [Byte] is b;
		local Int is i: 0;
		while({ i < len && (start + i) < src:length() }, {
			b:push((src:get(index: start + i, default: 0) & 255) as Byte);
			i: i + 1;
		});
		return b:toString();
	}

	local Function of Boolean is isOid(Array of Int is der, Int is start, Int is len, Array of Int is expected){
		if({ len != expected:length() }, { return false; });
		local Int is i: 0;
		while({ i < len }, {
			if({ (der:get(index: start + i, default: 0) & 255) != expected:get(index: i, default: 0) }, {
				return false;
			});
			i: i + 1;
		});
		return true;
	}

	## Extracts Common Name (OID 2.5.4.3 = 0x55 0x04 0x03) from a DER Name sequence.
	local Function of String is extractCommonName(Array of Int is der, Int is start, Int is end){
		local Array of Int is oidCn: [85, 4, 3];
		local String is foundCn: '';
		local Int is pos: start;
		while({ pos < end && foundCn == '' }, local Function of Boolean(){
			local Array of Int is rdn: :readTlv(der: der, pos: pos, limit: end);
			if({ rdn:get(index: 0, default: -1) < 0 }, { return false; });
			local Int is rPos: rdn:get(index: 1, default: 0);
			local Int is rEnd: rdn:get(index: 3, default: 0);
			while({ rPos < rEnd && foundCn == '' }, local Function of Boolean(){
				local Array of Int is atv: :readTlv(der: der, pos: rPos, limit: rEnd);
				if({ atv:get(index: 0, default: -1) != 48 }, { return false; });
				local Int is aPos: atv:get(index: 1, default: 0);
				local Int is aEnd: atv:get(index: 3, default: 0);
				local Array of Int is oidTlv: :readTlv(der: der, pos: aPos, limit: aEnd);
				if({ oidTlv:get(index: 0, default: -1) == 6 && :isOid(der: der, start: oidTlv:get(index: 1, default: 0), len: oidTlv:get(index: 2, default: 0), expected: oidCn) }, {
					local Array of Int is valTlv: :readTlv(der: der, pos: oidTlv:get(index: 3, default: 0), limit: aEnd);
					if({ valTlv:get(index: 0, default: -1) >= 0 }, {
						foundCn: :bytesToAscii(src: der, start: valTlv:get(index: 1, default: 0), len: valTlv:get(index: 2, default: 0));
						return false;
					});
				});
				rPos: aEnd;
				return true;
			});
			pos: rEnd;
			return true;
		});
		return foundCn;
	}

	## Extracts SAN dNSName entries (tag 0x82) from Extensions sequence (OID 2.5.29.17).
	local Function is extractSanDnsNames(Array of Int is der, Int is extSeqStart, Int is extSeqEnd, Array of String is outNames){
		local Array of Int is oidSan: [85, 29, 17];
		local Int is pos: extSeqStart;
		while({ pos < extSeqEnd }, local Function of Boolean(){
			local Array of Int is ext: :readTlv(der: der, pos: pos, limit: extSeqEnd);
			if({ ext:get(index: 0, default: -1) != 48 }, { return false; });
			local Int is ePos: ext:get(index: 1, default: 0);
			local Int is eEnd: ext:get(index: 3, default: 0);
			local Array of Int is oidTlv: :readTlv(der: der, pos: ePos, limit: eEnd);
			if({ oidTlv:get(index: 0, default: -1) == 6 && :isOid(der: der, start: oidTlv:get(index: 1, default: 0), len: oidTlv:get(index: 2, default: 0), expected: oidSan) }, {
				local Int is vPos: oidTlv:get(index: 3, default: 0);
				local Array of Int is nextTlv: :readTlv(der: der, pos: vPos, limit: eEnd);
				if({ nextTlv:get(index: 0, default: -1) == 1 }, {
					nextTlv: :readTlv(der: der, pos: nextTlv:get(index: 3, default: 0), limit: eEnd);
				});
				if({ nextTlv:get(index: 0, default: -1) == 4 }, {
					local Int is octStart: nextTlv:get(index: 1, default: 0);
					local Int is octEnd: nextTlv:get(index: 3, default: 0);
					local Array of Int is gnSeq: :readTlv(der: der, pos: octStart, limit: octEnd);
					if({ gnSeq:get(index: 0, default: -1) == 48 }, {
						local Int is gPos: gnSeq:get(index: 1, default: 0);
						local Int is gEnd: gnSeq:get(index: 3, default: 0);
						while({ gPos < gEnd }, local Function of Boolean(){
							local Array of Int is gn: :readTlv(der: der, pos: gPos, limit: gEnd);
							if({ gn:get(index: 0, default: -1) < 0 }, { return false; });
							if({ gn:get(index: 0, default: -1) == 130 }, {
								outNames:add(item: :bytesToAscii(src: der, start: gn:get(index: 1, default: 0), len: gn:get(index: 2, default: 0)));
							});
							gPos: gn:get(index: 3, default: 0);
							return true;
						});
					});
				});
			});
			pos: eEnd;
			return true;
		});
	}

	## Parses a DER-encoded X.509 certificate into an [X509Cert].
	Function of X509Cert is parseCert(Array of Int is der){
		local X509Cert is cert: X509Cert:init();
		local Int is limit: der:length();
		local Array of Int is rootSeq: :readTlv(der: der, pos: 0, limit: limit);
		if({ rootSeq:get(index: 0, default: -1) != 48 }, { return cert; });

		local Array of Int is tbs: :readTlv(der: der, pos: rootSeq:get(index: 1, default: 0), limit: rootSeq:get(index: 3, default: 0));
		if({ tbs:get(index: 0, default: -1) != 48 }, { return cert; });

		local Int is pos: tbs:get(index: 1, default: 0);
		local Int is tbsEnd: tbs:get(index: 3, default: 0);

		local Array of Int is f0: :readTlv(der: der, pos: pos, limit: tbsEnd);
		if({ f0:get(index: 0, default: -1) == 160 }, {
			pos: f0:get(index: 3, default: 0);
		});

		local Array of Int is serialTlv: :readTlv(der: der, pos: pos, limit: tbsEnd);
		if({ serialTlv:get(index: 0, default: -1) < 0 }, { return cert; });
		pos: serialTlv:get(index: 3, default: 0);

		local Array of Int is sigAlgTlv: :readTlv(der: der, pos: pos, limit: tbsEnd);
		if({ sigAlgTlv:get(index: 0, default: -1) < 0 }, { return cert; });
		pos: sigAlgTlv:get(index: 3, default: 0);

		local Int is issuerStart: pos;
		local Array of Int is issuerTlv: :readTlv(der: der, pos: pos, limit: tbsEnd);
		if({ issuerTlv:get(index: 0, default: -1) != 48 }, { return cert; });
		local Int is issuerNext: issuerTlv:get(index: 3, default: 0);
		cert:issuerHash: Sha256:toHex(bytes: Sha256:digest(data: :sliceRange(src: der, start: issuerStart, len: issuerNext - issuerStart)));
		pos: issuerNext;

		local Array of Int is valTlv: :readTlv(der: der, pos: pos, limit: tbsEnd);
		if({ valTlv:get(index: 0, default: -1) != 48 }, { return cert; });
		pos: valTlv:get(index: 3, default: 0);

		local Int is subjectStart: pos;
		local Array of Int is subjectTlv: :readTlv(der: der, pos: pos, limit: tbsEnd);
		if({ subjectTlv:get(index: 0, default: -1) != 48 }, { return cert; });
		local Int is subjectNext: subjectTlv:get(index: 3, default: 0);
		cert:subjectHash: Sha256:toHex(bytes: Sha256:digest(data: :sliceRange(src: der, start: subjectStart, len: subjectNext - subjectStart)));
		cert:commonName: :extractCommonName(der: der, start: subjectTlv:get(index: 1, default: 0), end: subjectNext);
		pos: subjectNext;

		local Array of Int is spkiTlv: :readTlv(der: der, pos: pos, limit: tbsEnd);
		if({ spkiTlv:get(index: 0, default: -1) != 48 }, { return cert; });
		pos: spkiTlv:get(index: 3, default: 0);

		while({ pos < tbsEnd }, local Function of Boolean(){
			local Array of Int is optTlv: :readTlv(der: der, pos: pos, limit: tbsEnd);
			if({ optTlv:get(index: 0, default: -1) < 0 }, { return false; });
			if({ optTlv:get(index: 0, default: -1) == 163 }, {
				local Array of Int is extSeq: :readTlv(der: der, pos: optTlv:get(index: 1, default: 0), limit: optTlv:get(index: 3, default: 0));
				if({ extSeq:get(index: 0, default: -1) == 48 }, {
					:extractSanDnsNames(der: der, extSeqStart: extSeq:get(index: 1, default: 0), extSeqEnd: extSeq:get(index: 3, default: 0), outNames: cert:sanDnsNames);
				});
			});
			pos: optTlv:get(index: 3, default: 0);
			return true;
		});

		cert:valid: true;
		return cert;
	}

	local Function of Int is b64Val(Int is ch){
		if({ ch >= 65 && ch <= 90 }, { return ch - 65; });
		if({ ch >= 97 && ch <= 122 }, { return ch - 97 + 26; });
		if({ ch >= 48 && ch <= 57 }, { return ch - 48 + 52; });
		if({ ch == 43 }, { return 62; });
		if({ ch == 47 }, { return 63; });
		return -1;
	}

	## Decodes a Base64 string (ignoring whitespace and padding) to DER bytes.
	Function of Array of Int is decodeBase64(String is text){
		local Array of Int is out: [];
		local Int is buf: 0;
		local Int is bits: 0;
		local Int is i: 0;
		local Int is n: text:byteLength();
		while({ i < n }, {
			local Int is ch: text:byteAt(index: i, default: 0);
			local Int is v: :b64Val(ch: ch);
			if({ v >= 0 }, {
				buf: (buf << 6) | v;
				bits: bits + 6;
				if({ bits >= 8 }, {
					bits: bits - 8;
					out:add(item: (buf >> bits) & 255);
				});
			});
			i: i + 1;
		});
		return out;
	}

	## Loads system root CA subject hashes from the OS PEM bundle (cached once).
	Function is ensureSystemTrustStore(){
		Parallel:syncWith(lock: 89, action: {
			if({ X509TrustStore:loadedFlag:length() > 0 }, {
				return;
			});
			local Array of String is paths: [
				'/etc/ssl/certs/ca-certificates.crt',
				'/etc/pki/tls/certs/ca-bundle.crt',
				'/etc/ssl/cert.pem',
				'/etc/ssl/ca-bundle.pem'
			];
			local String is pemText: '';
			local Int is pi: 0;
			while({ pi < paths:length() && pemText == '' }, {
				local String is cand: paths:get(index: pi, default: '');
				if({ File:fileExists(path: cand) }, {
					pemText: File:fileRead(path: cand, onSuccess: local Function(String is _s){}, onError: local Function(SpecError of FileError is _e){}, default: '');
				});
				pi: pi + 1;
			});
			if({ pemText != '' }, {
				local String is beginMark: '-----BEGIN CERTIFICATE-----';
				local String is endMark: '-----END CERTIFICATE-----';
				local Int is pos: 0;
				while({ pos < pemText:length() }, local Function of Boolean(){
					local Int is bIdx: pemText:indexOfFrom(search: beginMark, from: pos, default: -1);
					if({ bIdx < 0 }, { return false; });
					local Int is bodyStart: bIdx + beginMark:length();
					local Int is eIdx: pemText:indexOfFrom(search: endMark, from: bodyStart, default: -1);
					if({ eIdx < 0 }, { return false; });
					local String is b64Body: pemText:substring(start: bodyStart, end: eIdx);
					local Array of Int is der: :decodeBase64(text: b64Body);
					local X509Cert is rootCert: :parseCert(der: der);
					if({ rootCert:valid && rootCert:subjectHash != '' }, {
						X509TrustStore:rootSubjectHashes:set(key: rootCert:subjectHash, value: true);
					});
					pos: eIdx + endMark:length();
					return true;
				});
			});
			X509TrustStore:loadedFlag:add(item: true);
		});
	}

	## Verifies chain linkage and root CA trust anchor against the system trust store.
	## Populates [parsedOut] with the parsed certificates on success.
	Function of Boolean is verifyTrustChain(Array of Array of Int is certChain, Array of X509Cert is parsedOut, Array of String is errOut){
		if({ certChain:length() == 0 }, {
			errOut:add(item: 'Certificate chain is empty');
			return false;
		});
		local Int is i: 0;
		while({ i < certChain:length() }, {
			local X509Cert is c: :parseCert(der: certChain:get(index: i));
			if({ !c:valid }, {
				errOut:add(item: 'Failed to parse X.509 certificate at index ' . (i as String));
				return false;
			});
			parsedOut:add(item: c);
			i: i + 1;
		});

		i: 0;
		while({ i + 1 < parsedOut:length() }, {
			local X509Cert is child: parsedOut:get(index: i);
			local X509Cert is parent: parsedOut:get(index: i + 1);
			if({ child:issuerHash != parent:subjectHash }, {
				errOut:add(item: 'Broken certificate chain linkage between depth ' . (i as String) . ' and ' . ((i + 1) as String));
				return false;
			});
			i: i + 1;
		});

		:ensureSystemTrustStore();
		local X509Cert is top: parsedOut:get(index: parsedOut:length() - 1);
		local Boolean is trusted: false;
		Parallel:syncWith(lock: 89, action: {
			if({ X509TrustStore:rootSubjectHashes:has(key: top:issuerHash) || X509TrustStore:rootSubjectHashes:has(key: top:subjectHash) }, {
				trusted: true;
			});
		});
		if({ !trusted }, {
			errOut:add(item: 'Untrusted certificate issuer (not in system CA bundle)');
			return false;
		});
		return true;
	}
}
