#! Package base:net:tls
#! Pure-Spec TLS 1.3 client (RFC 8446) over base:net:Socket.
#! Negotiates TLS_AES_128_GCM_SHA256 (0x1301) or TLS_CHACHA20_POLY1305_SHA256 (0x1303)
#! with X25519 key exchange, OS CSPRNG, and X.509 certificate chain verification.

Class is TlsClient{
	namespace: ['base', 'net', 'tls'];

	replace Array of Array of String is using: [
		['base', 'net', Socket],
		['base', 'net', 'tls', as TlsVerifier()],
		['base', 'math', 'crypto', as Sha256()],
		['base', 'math', 'crypto', as X25519()],
		['base', 'math', 'crypto', as ChaCha20Poly1305()],
		['base', 'math', 'crypto', as Aes128Gcm()],
		['base', 'struct', Array],
		['base', 'struct', List],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()]
	];

	local Socket is sock: Socket:init();
	local Boolean is connected: false;
	local String is lastErr: '';
	local Int is cipherSuite: 0;

	local List of Byte is rxBuf;
	local Int is rxPos: 0;

	replace Function is init(){
		local [Byte] is emptyRx;
		:rxBuf: emptyRx;
	}

	local Array of Int is cAppKey: [];
	local Array of Int is cAppIv: [];
	local Int is cAppSeq: 0;

	local Array of Int is sAppKey: [];
	local Array of Int is sAppIv: [];
	local Int is sAppSeq: 0;

	Function of String is lastError(){
		return :lastErr;
	}

	Function of Boolean is isConnected(){
		return :connected;
	}

	local Function is appendBytes(Array of Int is dst, Array of Int is src){
		local Int is i: 0;
		while({ i < src:length() }, {
			dst:add(item: src:get(index: i, default: 0) & 255);
			i: i + 1;
		});
	}

	local Function is appendStrBytes(Array of Int is dst, String is s){
		local Int is i: 0;
		while({ i < s:byteLength() }, {
			dst:add(item: s:byteAt(index: i, default: 0));
			i: i + 1;
		});
	}

	local Function of Array of Int is sliceBytes(Array of Int is src, Int is start, Int is count){
		local Array of Int is out: [];
		local Int is i: 0;
		while({ i < count && (start + i) < src:length() }, {
			out:add(item: src:get(index: start + i, default: 0) & 255);
			i: i + 1;
		});
		return out;
	}

	local Function of Array of Int is makeRandom32(){
		local Int is buf: Mem:alloc(bytes: 32);
		local Int is rc: Mem:randomBytes(dstAddr: buf, len: 32);
		local Array of Int is out: [];
		local Int is i: 0;
		while({ i < 32 }, {
			local Int is bVal: if({ rc == 0 }, { Mem:loadByte(ptr: buf, byteOffset: i) }, { 0 });
			out:add(item: bVal);
			i: i + 1;
		});
		Mem:free(ptr: buf);
		return out;
	}

	local Function of Array of Int is makeNonce(Array of Int is iv, Int is seq){
		local Array of Int is nonce: [];
		local Int is i: 0;
		while({ i < 12 }, {
			nonce:add(item: iv:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		local Int is k: 0;
		while({ k < 8 }, {
			local Int is shift: (7 - k) * 8;
			local Int is sb: (seq >> shift) & 255;
			nonce:set(index: 4 + k, item: nonce:get(index: 4 + k, default: 0) ^ sb);
			k: k + 1;
		});
		return nonce;
	}

	local Function of Boolean is sendRawBytes(Array of Int is data){
		local [Byte] is buf;
		local Int is i: 0;
		while({ i < data:length() }, {
			buf:push((data:get(index: i, default: 0) & 255) as Byte);
			i: i + 1;
		});
		local String is errMsg: '';
		local Int is sent: :sock:send(data: buf, onError: local Function(String is e){
			errMsg: e;
		});
		if({ sent < 0 }, {
			:lastErr: if({ errMsg != '' }, { errMsg }, { 'socket send failed' });
			return false;
		});
		return true;
	}

	local Function of Boolean is ensureRxBytes(Int is needed){
		while({ (:rxBuf:length() - :rxPos) < needed }, local Function of Boolean(){
			if({ :rxPos >= 4096 && :rxPos * 2 >= :rxBuf:length() }, {
				:rxBuf: :rxBuf:slice(:rxPos, :rxBuf:length());
				:rxPos: 0;
			});
			local String is errMsg: '';
			local List of Byte is chunk: :sock:receive(maxBytes: 16384, onError: local Function(String is e){
				errMsg: e;
			});
			if({ errMsg != '' }, {
				:lastErr: errMsg;
				return false;
			});
			if({ chunk:length() == 0 }, {
				return false;
			});
			:rxBuf:appendBytes(chunk);
			return true;
		});
		return (:rxBuf:length() - :rxPos) >= needed;
	}

	local Function of Array of Int is readRecord(Array of Int is headerOut){
		if({ !:ensureRxBytes(needed: 5) }, {
			return [];
		});
		local Int is h0: (:rxBuf:get(index: :rxPos, default: 0 as Byte) as Int) & 255;
		local Int is h1: (:rxBuf:get(index: :rxPos + 1, default: 0 as Byte) as Int) & 255;
		local Int is h2: (:rxBuf:get(index: :rxPos + 2, default: 0 as Byte) as Int) & 255;
		local Int is h3: (:rxBuf:get(index: :rxPos + 3, default: 0 as Byte) as Int) & 255;
		local Int is h4: (:rxBuf:get(index: :rxPos + 4, default: 0 as Byte) as Int) & 255;
		local Int is recLen: :rxBuf:readU16BE(:rxPos + 3);
		:rxPos: :rxPos + 5;

		if({ !:ensureRxBytes(needed: recLen) }, {
			return [];
		});
		headerOut:add(item: h0);
		headerOut:add(item: h1);
		headerOut:add(item: h2);
		headerOut:add(item: h3);
		headerOut:add(item: h4);

		local Array of Int is payload: [];
		local Int is pi: 0;
		while({ pi < recLen }, {
			payload:add(item: (:rxBuf:get(index: :rxPos + pi, default: 0 as Byte) as Int) & 255);
			pi: pi + 1;
		});
		:rxPos: :rxPos + recLen;
		return payload;
	}

	local Function of Array of Int is aeadSeal(Array of Int is key, Array of Int is nonce, Array of Int is aad, Array of Int is plaintext){
		if({ :cipherSuite == 4865 }, {
			return Aes128Gcm:seal(key: key, nonce: nonce, aad: aad, plaintext: plaintext);
		});
		return ChaCha20Poly1305:seal(key: key, nonce: nonce, aad: aad, plaintext: plaintext);
	}

	local Function of Array of Int is aeadOpen(Array of Int is key, Array of Int is nonce, Array of Int is aad, Array of Int is ctWithTag, Array of Boolean is okOut){
		if({ :cipherSuite == 4865 }, {
			return Aes128Gcm:open(key: key, nonce: nonce, aad: aad, ctWithTag: ctWithTag, okOut: okOut);
		});
		return ChaCha20Poly1305:open(key: key, nonce: nonce, aad: aad, ctWithTag: ctWithTag, okOut: okOut);
	}

	local Function of Boolean is sendEncryptedRecord(Array of Int is key, Array of Int is iv, Int is seq, Int is innerType, Array of Int is plaintext){
		local Array of Int is inner: [];
		:appendBytes(dst: inner, src: plaintext);
		inner:add(item: innerType & 255);

		local Int is encLen: inner:length() + 16;
		local Array of Int is aad: [23, 3, 3, (encLen >> 8) & 255, encLen & 255];
		local Array of Int is nonce: :makeNonce(iv: iv, seq: seq);
		local Array of Int is ctTag: :aeadSeal(key: key, nonce: nonce, aad: aad, plaintext: inner);

		local Array of Int is rec: [];
		:appendBytes(dst: rec, src: aad);
		:appendBytes(dst: rec, src: ctTag);
		return :sendRawBytes(data: rec);
	}

	local Function of Array of Int is buildClientHello(String is host, Array of Int is clientPub){
		local Array of Int is body: [];
		# legacy_version = TLS 1.2 (0x0303)
		body:add(item: 3);
		body:add(item: 3);
		# random (32 bytes)
		:appendBytes(dst: body, src: :makeRandom32());
		# legacy_session_id (32 bytes for middlebox compat)
		body:add(item: 32);
		:appendBytes(dst: body, src: :makeRandom32());
		# cipher_suites: TLS_AES_128_GCM_SHA256 (0x1301), TLS_CHACHA20_POLY1305_SHA256 (0x1303)
		body:add(item: 0);
		body:add(item: 4);
		body:add(item: 19);
		body:add(item: 1);
		body:add(item: 19);
		body:add(item: 3);
		# legacy_compression_methods: [null]
		body:add(item: 1);
		body:add(item: 0);

		# Extensions
		local Array of Int is exts: [];

		# 1. server_name (SNI, 0x0000)
		local Int is hostLen: host:byteLength();
		local Int is sniEntryLen: hostLen + 3;
		local Int is sniExtLen: sniEntryLen + 2;
		exts:add(item: 0);
		exts:add(item: 0);
		exts:add(item: (sniExtLen >> 8) & 255);
		exts:add(item: sniExtLen & 255);
		exts:add(item: (sniEntryLen >> 8) & 255);
		exts:add(item: sniEntryLen & 255);
		exts:add(item: 0);
		exts:add(item: (hostLen >> 8) & 255);
		exts:add(item: hostLen & 255);
		:appendStrBytes(dst: exts, s: host);

		# 2. supported_versions (0x002b): TLS 1.3 (0x0304)
		exts:add(item: 0); exts:add(item: 43);
		exts:add(item: 0); exts:add(item: 3);
		exts:add(item: 2); exts:add(item: 3); exts:add(item: 4);

		# 3. supported_groups (0x000a): x25519 (0x001d)
		exts:add(item: 0); exts:add(item: 10);
		exts:add(item: 0); exts:add(item: 4);
		exts:add(item: 0); exts:add(item: 2);
		exts:add(item: 0); exts:add(item: 29);

		# 4. signature_algorithms (0x000d)
		exts:add(item: 0); exts:add(item: 13);
		exts:add(item: 0); exts:add(item: 10);
		exts:add(item: 0); exts:add(item: 8);
		exts:add(item: 4); exts:add(item: 3);  # ecdsa_secp256r1_sha256
		exts:add(item: 8); exts:add(item: 4);  # rsa_pss_rsae_sha256
		exts:add(item: 4); exts:add(item: 1);  # rsa_pkcs1_sha256
		exts:add(item: 8); exts:add(item: 7);  # ed25519

		# 5. key_share (0x0033): x25519 (0x001d) + 32-byte clientPub
		exts:add(item: 0); exts:add(item: 51);
		exts:add(item: 0); exts:add(item: 38);
		exts:add(item: 0); exts:add(item: 36);
		exts:add(item: 0); exts:add(item: 29);
		exts:add(item: 0); exts:add(item: 32);
		:appendBytes(dst: exts, src: clientPub);

		body:add(item: (exts:length() >> 8) & 255);
		body:add(item: exts:length() & 255);
		:appendBytes(dst: body, src: exts);

		# Handshake message header: type=1 (ClientHello), 24-bit length
		local Array of Int is hsMsg: [1, (body:length() >> 16) & 255, (body:length() >> 8) & 255, body:length() & 255];
		:appendBytes(dst: hsMsg, src: body);
		return hsMsg;
	}

	local Function is parseCertificateMessage(Array of Int is fullMsg, Array of Array of Int is outChain){
		if({ fullMsg:length() < 8 }, { return; });
		local Int is ctxLen: fullMsg:get(index: 4, default: 0) & 255;
		local Int is pos: 5 + ctxLen;
		if({ pos + 3 > fullMsg:length() }, { return; });
		local Int is listLen: (fullMsg:get(index: pos, default: 0) << 16) | (fullMsg:get(index: pos + 1, default: 0) << 8) | fullMsg:get(index: pos + 2, default: 0);
		pos: pos + 3;
		local Int is listEnd: pos + listLen;
		if({ listEnd > fullMsg:length() }, { listEnd: fullMsg:length(); });
		while({ pos + 3 <= listEnd }, local Function of Boolean(){
			local Int is cLen: (fullMsg:get(index: pos, default: 0) << 16) | (fullMsg:get(index: pos + 1, default: 0) << 8) | fullMsg:get(index: pos + 2, default: 0);
			pos: pos + 3;
			if({ pos + cLen > listEnd }, { return false; });
			outChain:add(item: :sliceBytes(src: fullMsg, start: pos, count: cLen));
			pos: pos + cLen;
			if({ pos + 2 > listEnd }, { return false; });
			local Int is extLen: (fullMsg:get(index: pos, default: 0) << 8) | fullMsg:get(index: pos + 1, default: 0);
			pos: pos + 2 + extLen;
			return true;
		});
	}

	## Connects to [host]:[port] over TCP and performs the TLS 1.3 handshake.
	Function of Boolean is connect(String is host, Int is port: 443, Int is timeoutMs: 15000, Boolean is verifyCert: true){
		local String is errMsg: '';
		:sock: Socket:init():connect(host: host, port: port, timeoutMs: timeoutMs, onError: local Function(String is e){
			errMsg: e;
		});
		if({ !:sock:isOpen() }, {
			:lastErr: if({ errMsg != '' }, { errMsg }, { 'TCP connect failed to ' . host });
			return false;
		});
		:sock:setTimeout(timeoutMs: timeoutMs);

		local Array of Int is clientPriv: :makeRandom32();
		local Array of Int is clientPub: X25519:publicKey(privateKey: clientPriv);
		local Array of Int is chMsg: :buildClientHello(host: host, clientPub: clientPub);

		# Send ClientHello record (type 22, legacy version 0x0301)
		local Array of Int is chRec: [22, 3, 1, (chMsg:length() >> 8) & 255, chMsg:length() & 255];
		:appendBytes(dst: chRec, src: chMsg);
		if({ !:sendRawBytes(data: chRec) }, {
			:close();
			return false;
		});

		local Array of Int is transcript: [];
		:appendBytes(dst: transcript, src: chMsg);

		# Read ServerHello
		local Array of Int is shMsg: [];
		local Boolean is gotSh: false;
		while({ !gotSh }, {
			local Array of Int is hdr: [];
			local Array of Int is payload: :readRecord(headerOut: hdr);
			if({ hdr:length() < 5 }, {
				:lastErr: if({ :lastErr != '' }, { :lastErr }, { 'EOF waiting for ServerHello' });
				:close();
				return false;
			});
			local Int is rType: hdr:get(index: 0, default: 0);
			if({ rType == 21 }, {
				local Int is alertDesc: payload:get(index: 1, default: 0);
				:lastErr: 'TLS alert during handshake (desc=' . (alertDesc as String) . ')';
				:close();
				return false;
			});
			if({ rType == 22 && payload:length() >= 4 && payload:get(index: 0, default: 0) == 2 }, {
				local Int is mLen: (payload:get(index: 1, default: 0) << 16) | (payload:get(index: 2, default: 0) << 8) | payload:get(index: 3, default: 0);
				shMsg: :sliceBytes(src: payload, start: 0, count: 4 + mLen);
				gotSh: true;
			});
		});

		:appendBytes(dst: transcript, src: shMsg);

		# Parse ServerHello to extract server X25519 public key
		local Int is pos: 4 + 2 + 32;
		local Int is sidLen: shMsg:get(index: pos, default: 0);
		pos: pos + 1 + sidLen;
		local Int is csHi: shMsg:get(index: pos, default: 0);
		local Int is csLo: shMsg:get(index: pos + 1, default: 0);
		if({ csHi != 19 || (csLo != 1 && csLo != 3) }, {
			:lastErr: 'Server selected unsupported cipher suite (' . (csHi as String) . ',' . (csLo as String) . ')';
			:close();
			return false;
		});
		:cipherSuite: (csHi << 8) | csLo;
		local Int is keyLen: if({ :cipherSuite == 4865 }, { 16 }, { 32 });
		pos: pos + 3; # cipher_suite(2) + compression(1)
		local Int is extsLen: (shMsg:get(index: pos, default: 0) << 8) | shMsg:get(index: pos + 1, default: 0);
		pos: pos + 2;
		local Int is extsEnd: pos + extsLen;
		local Array of Int is serverPub: [];
		while({ pos + 4 <= extsEnd }, {
			local Int is eType: (shMsg:get(index: pos, default: 0) << 8) | shMsg:get(index: pos + 1, default: 0);
			local Int is eLen: (shMsg:get(index: pos + 2, default: 0) << 8) | shMsg:get(index: pos + 3, default: 0);
			pos: pos + 4;
			if({ eType == 51 && eLen >= 36 }, {
				local Int is grp: (shMsg:get(index: pos, default: 0) << 8) | shMsg:get(index: pos + 1, default: 0);
				local Int is kLen: (shMsg:get(index: pos + 2, default: 0) << 8) | shMsg:get(index: pos + 3, default: 0);
				if({ grp == 29 && kLen == 32 }, {
					serverPub: :sliceBytes(src: shMsg, start: pos + 4, count: 32);
				});
			});
			pos: pos + eLen;
		});
		if({ serverPub:length() != 32 }, {
			:lastErr: 'ServerHello missing X25519 key_share';
			:close();
			return false;
		});

		# TLS 1.3 Handshake Key Schedule (RFC 8446 §7.1)
		local Array of Int is zeros32: [];
		local Int is zi: 0;
		while({ zi < 32 }, { zeros32:add(item: 0); zi: zi + 1; });
		local Array of Int is emptyHash: Sha256:digest(data: []);
		local Array of Int is earlySecret: Sha256:hkdfExtract(salt: zeros32, ikm: zeros32);
		local Array of Int is derived1: Sha256:deriveSecret(secret: earlySecret, label: 'derived', transcriptHash: emptyHash);
		local Array of Int is sharedSecret: X25519:scalarMult(scalar: clientPriv, uCoord: serverPub);
		local Array of Int is hsSecret: Sha256:hkdfExtract(salt: derived1, ikm: sharedSecret);

		local Array of Int is chShHash: Sha256:digest(data: transcript);
		local Array of Int is cHsTraffic: Sha256:deriveSecret(secret: hsSecret, label: 'c hs traffic', transcriptHash: chShHash);
		local Array of Int is sHsTraffic: Sha256:deriveSecret(secret: hsSecret, label: 's hs traffic', transcriptHash: chShHash);

		local Array of Int is sHsKey: Sha256:hkdfExpandLabel(secret: sHsTraffic, label: 'key', context: [], length: keyLen);
		local Array of Int is sHsIv: Sha256:hkdfExpandLabel(secret: sHsTraffic, label: 'iv', context: [], length: 12);
		local Array of Int is cHsKey: Sha256:hkdfExpandLabel(secret: cHsTraffic, label: 'key', context: [], length: keyLen);
		local Array of Int is cHsIv: Sha256:hkdfExpandLabel(secret: cHsTraffic, label: 'iv', context: [], length: 12);

		# Decrypt server encrypted handshake flight until server Finished (type 20)
		local Int is sHsSeq: 0;
		local Array of Int is hsStream: [];
		local Int is hsPos: 0;
		local Boolean is gotFinished: false;
		local Array of Array of Int is serverCertChain: [];

		while({ !gotFinished }, {
			local Array of Int is hdr: [];
			local Array of Int is payload: :readRecord(headerOut: hdr);
			if({ hdr:length() < 5 }, {
				:lastErr: 'EOF during encrypted server handshake';
				:close();
				return false;
			});
			local Int is rType: hdr:get(index: 0, default: 0);
			if({ rType == 21 }, {
				:lastErr: 'Plaintext TLS alert during handshake (desc=' . (payload:get(index: 1, default: 0) as String) . ')';
				:close();
				return false;
			});
			if({ rType == 23 }, {
				local Array of Int is nonce: :makeNonce(iv: sHsIv, seq: sHsSeq);
				sHsSeq: sHsSeq + 1;
				local Array of Boolean is okOut: [];
				local Array of Int is inner: :aeadOpen(key: sHsKey, nonce: nonce, aad: hdr, ctWithTag: payload, okOut: okOut);
				if({ !okOut:get(index: 0, default: false) }, {
					:lastErr: 'AEAD authentication failed on server handshake record';
					:close();
					return false;
				});
				local Int is endIdx: inner:length() - 1;
				while({ endIdx >= 0 && inner:get(index: endIdx, default: 0) == 0 }, {
					endIdx: endIdx - 1;
				});
				if({ endIdx < 0 }, {
					:lastErr: 'Malformed empty TLS inner plaintext';
					:close();
					return false;
				});
				local Int is innerType: inner:get(index: endIdx, default: 0);
				if({ innerType == 21 }, {
					:lastErr: 'Encrypted TLS alert during handshake (desc=' . (inner:get(index: 1, default: 0) as String) . ')';
					:close();
					return false;
				});
				if({ innerType == 22 }, {
					local Int is pi: 0;
					while({ pi < endIdx }, {
						hsStream:add(item: inner:get(index: pi, default: 0));
						pi: pi + 1;
					});
					while({ !gotFinished && (hsStream:length() - hsPos) >= 4 }, local Function of Boolean(){
						local Int is mType: hsStream:get(index: hsPos, default: 0);
						local Int is mLen: (hsStream:get(index: hsPos + 1, default: 0) << 16) | (hsStream:get(index: hsPos + 2, default: 0) << 8) | hsStream:get(index: hsPos + 3, default: 0);
						if({ (hsStream:length() - hsPos) < (4 + mLen) }, {
							return false;
						});
						local Array of Int is fullMsg: :sliceBytes(src: hsStream, start: hsPos, count: 4 + mLen);
						hsPos: hsPos + 4 + mLen;
						if({ mType == 20 }, {
							# Verify server Finished MAC
							local Array of Int is sFinKey: Sha256:hkdfExpandLabel(secret: sHsTraffic, label: 'finished', context: [], length: 32);
							local Array of Int is expMac: Sha256:hmac(key: sFinKey, msg: Sha256:digest(data: transcript));
							local Int is diff: 0;
							local Int is fi: 0;
							while({ fi < 32 }, {
								diff: diff | (expMac:get(index: fi, default: 0) ^ fullMsg:get(index: 4 + fi, default: 0));
								fi: fi + 1;
							});
							if({ mLen != 32 || diff != 0 }, {
								:lastErr: 'Server Finished MAC verification failed';
								:close();
								return false;
							});
							:appendBytes(dst: transcript, src: fullMsg);
							gotFinished: true;
							return false;
						});
						if({ mType == 11 }, {
							:parseCertificateMessage(fullMsg: fullMsg, outChain: serverCertChain);
						});
						:appendBytes(dst: transcript, src: fullMsg);
						return true;
					});
					if({ :lastErr != '' }, {
						return false;
					});
				});
			});
		});

		if({ verifyCert }, {
			local Array of String is certErr: [];
			if({ !TlsVerifier:verifyServerChain(certChain: serverCertChain, host: host, errOut: certErr) }, {
				:lastErr: if({ certErr:length() > 0 }, { certErr:get(index: 0, default: 'X.509 verification failed') }, { 'X.509 verification failed' });
				:close();
				return false;
			});
		});

		# Application Traffic Key Schedule
		local Array of Int is sFinHash: Sha256:digest(data: transcript);
		local Array of Int is derived2: Sha256:deriveSecret(secret: hsSecret, label: 'derived', transcriptHash: emptyHash);
		local Array of Int is masterSecret: Sha256:hkdfExtract(salt: derived2, ikm: zeros32);
		local Array of Int is cAppTraffic: Sha256:deriveSecret(secret: masterSecret, label: 'c ap traffic', transcriptHash: sFinHash);
		local Array of Int is sAppTraffic: Sha256:deriveSecret(secret: masterSecret, label: 's ap traffic', transcriptHash: sFinHash);

		:cAppKey: Sha256:hkdfExpandLabel(secret: cAppTraffic, label: 'key', context: [], length: keyLen);
		:cAppIv: Sha256:hkdfExpandLabel(secret: cAppTraffic, label: 'iv', context: [], length: 12);
		:cAppSeq: 0;

		:sAppKey: Sha256:hkdfExpandLabel(secret: sAppTraffic, label: 'key', context: [], length: keyLen);
		:sAppIv: Sha256:hkdfExpandLabel(secret: sAppTraffic, label: 'iv', context: [], length: 12);
		:sAppSeq: 0;

		# Send Client Finished (encrypted with client handshake key, seq = 0)
		local Array of Int is cFinKey: Sha256:hkdfExpandLabel(secret: cHsTraffic, label: 'finished', context: [], length: 32);
		local Array of Int is cVerify: Sha256:hmac(key: cFinKey, msg: sFinHash);
		local Array of Int is cFinMsg: [20, 0, 0, 32];
		:appendBytes(dst: cFinMsg, src: cVerify);
		if({ !:sendEncryptedRecord(key: cHsKey, iv: cHsIv, seq: 0, innerType: 22, plaintext: cFinMsg) }, {
			:close();
			return false;
		});

		:connected: true;
		return true;
	}

	## Sends [text] as encrypted TLS 1.3 application data.
	Function of Boolean is sendString(String is text){
		if({ !:connected }, {
			:lastErr: 'TLS client not connected';
			return false;
		});
		local Int is totalLen: text:byteLength();
		local Int is off: 0;
		while({ off < totalLen }, {
			local Int is chunkLen: if({ (totalLen - off) > 16000 }, { 16000 }, { totalLen - off });
			local Array of Int is chunk: [];
			local Int is i: 0;
			while({ i < chunkLen }, {
				chunk:add(item: text:byteAt(index: off + i, default: 0));
				i: i + 1;
			});
			local Boolean is ok: :sendEncryptedRecord(key: :cAppKey, iv: :cAppIv, seq: :cAppSeq, innerType: 23, plaintext: chunk);
			:cAppSeq: :cAppSeq + 1;
			if({ !ok }, {
				return false;
			});
			off: off + chunkLen;
		});
		return true;
	}

	## Reads and decrypts all application data until close_notify or EOF.
	Function of String is recvAllString(){
		local [Byte] is out;
		if({ !:connected }, {
			return '';
		});
		while({ true }, local Function of Boolean(){
			local Array of Int is hdr: [];
			local Array of Int is payload: :readRecord(headerOut: hdr);
			if({ hdr:length() < 5 }, {
				return false;
			});
			local Int is rType: hdr:get(index: 0, default: 0);
			if({ rType == 21 }, {
				return false;
			});
			if({ rType != 23 }, {
				return true;
			});
			local Array of Int is nonce: :makeNonce(iv: :sAppIv, seq: :sAppSeq);
			:sAppSeq: :sAppSeq + 1;
			local Array of Boolean is okOut: [];
			local Array of Int is inner: :aeadOpen(key: :sAppKey, nonce: nonce, aad: hdr, ctWithTag: payload, okOut: okOut);
			if({ !okOut:get(index: 0, default: false) }, {
				:lastErr: 'AEAD authentication failed on application data';
				return false;
			});
			local Int is endIdx: inner:length() - 1;
			while({ endIdx >= 0 && inner:get(index: endIdx, default: 0) == 0 }, {
				endIdx: endIdx - 1;
			});
			if({ endIdx < 0 }, {
				return true;
			});
			local Int is innerType: inner:get(index: endIdx, default: 0);
			if({ innerType == 21 }, {
				return false;
			});
			if({ innerType == 23 }, {
				local Int is i: 0;
				while({ i < endIdx }, {
					out:push((inner:get(index: i, default: 0) & 255) as Byte);
					i: i + 1;
				});
			});
			return true;
		});
		return out:toString();
	}

	Function is close(){
		:connected: false;
		:sock:close();
	}
}
