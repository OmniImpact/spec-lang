#! Package base:net:tls
#! Pure-Spec TLS 1.3 server session (RFC 8446) over an accepted `base:net:Socket`.
#! Negotiates TLS_AES_128_GCM_SHA256 (0x1301) or TLS_CHACHA20_POLY1305_SHA256 (0x1303)
#! with X25519 key exchange and Ed25519 (0x0807) CertificateVerify.

Class is TlsServerSession{
	replace [String] is namespace: ['base', 'net', 'tls'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', Socket],
		['base', 'net', NetError],
		['base', 'net', 'tls', TlsError],
		['base', 'math', 'crypto', as Sha256()],
		['base', 'math', 'crypto', as X25519()],
		['base', 'math', 'crypto', as Ed25519()],
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
	local TlsError is lastKind: TlsError:HANDSHAKE_FAILED;
	local Int is cipherSuite: 0;
	local String is sni: '';

	local List of Byte is rxBuf;
	local Int is rxPos: 0;

	local Array of Int is cAppKey: Array();
	local Array of Int is cAppIv: Array();
	local Int is cAppSeq: 0;

	local Array of Int is sAppKey: Array();
	local Array of Int is sAppIv: Array();
	local Int is sAppSeq: 0;

	replace Function is init(){
		local [Byte] is emptyRx;
		:rxBuf: emptyRx;
	}

	local Function is setFail(TlsError is kind, String is msg){
		:lastErr: msg;
		:lastKind: kind;
	}

	local Function is appendBytes(Array of Int is dst, Array of Int is src){
		local Int is i: 0;
		while({ i < src:length() }, {
			dst:add(item: src:get(index: i, default: 0) & 255);
			i: i + 1;
		});
	}

	local Function of Array of Int is sliceBytes(Array of Int is src, Int is start, Int is count){
		local Array of Int is out: Array();
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
		local Array of Int is out: Array();
		local Int is i: 0;
		while({ i < 32 }, {
			out:add(item: if({ rc == 0 }, { Mem:loadByte(ptr: buf, byteOffset: i) }, { 0 }));
			i: i + 1;
		});
		Mem:free(ptr: buf);
		return out;
	}

	local Function of Array of Int is makeNonce(Array of Int is iv, Int is seq){
		local Array of Int is nonce: Array();
		local Int is i: 0;
		while({ i < 12 }, { nonce:add(item: iv:get(index: i, default: 0) & 255); i: i + 1; });
		local Int is k: 0;
		while({ k < 8 }, {
			local Int is sb: (seq >> ((7 - k) * 8)) & 255;
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
		local Int is sent: :sock:send(data: buf, onError: local Function(SpecError of NetError is e){ errMsg: e:description; });
		if({ sent < 0 }, {
			:setFail(kind: TlsError:SEND_FAILED, msg: if({ errMsg != '' }, { errMsg }, { 'socket send failed' }));
			return false;
		});
		return true;
	}

	local Function of Boolean is ensureRxBytes(Int is needed){
		local Boolean is ok: true;
		while({ ok && (:rxBuf:length() - :rxPos) < needed }, {
			if({ :rxPos >= 4096 && :rxPos * 2 >= :rxBuf:length() }, {
				:rxBuf: :rxBuf:slice(:rxPos, :rxBuf:length());
				:rxPos: 0;
			});
			local String is errMsg: '';
			local List of Byte is chunk: :sock:receive(maxBytes: 16384, onError: local Function(SpecError of NetError is e){ errMsg: e:description; });
			if({ errMsg != '' }, {
				:setFail(kind: TlsError:RECV_FAILED, msg: errMsg);
				ok: false;
			}, {
				if({ chunk:length() == 0 }, {
					ok: false;
				}, {
					:rxBuf:appendBytes(chunk);
				});
			});
		});
		return (:rxBuf:length() - :rxPos) >= needed;
	}

	local Function of Array of Int is readRecord(Array of Int is headerOut){
		if({ !:ensureRxBytes(needed: 5) }, { return Array(); });
		local Int is rType: :rxBuf:get(:rxPos, 0 as Byte) as Int;
		local Int is vMaj: :rxBuf:get(:rxPos + 1, 0 as Byte) as Int;
		local Int is vMin: :rxBuf:get(:rxPos + 2, 0 as Byte) as Int;
		local Int is rLen: ((:rxBuf:get(:rxPos + 3, 0 as Byte) as Int) << 8) | (:rxBuf:get(:rxPos + 4, 0 as Byte) as Int);
		:rxPos: :rxPos + 5;
		headerOut:add(item: rType);
		headerOut:add(item: vMaj);
		headerOut:add(item: vMin);
		headerOut:add(item: (rLen >> 8) & 255);
		headerOut:add(item: rLen & 255);
		if({ !:ensureRxBytes(needed: rLen) }, { return Array(); });
		local Array of Int is payload: Array();
		local Int is i: 0;
		while({ i < rLen }, {
			payload:add(item: :rxBuf:get(:rxPos + i, 0 as Byte) as Int);
			i: i + 1;
		});
		:rxPos: :rxPos + rLen;
		return payload;
	}

	local Function of Boolean is sendPlainRecord(Int is rType, Array of Int is payload){
		local Array of Int is rec: Array([rType & 255, 3, 3, (payload:length() >> 8) & 255, payload:length() & 255]);
		:appendBytes(dst: rec, src: payload);
		return :sendRawBytes(data: rec);
	}

	local Function of Boolean is sendEncryptedRecord(Array of Int is key, Array of Int is iv, Int is seq, Int is innerType, Array of Int is plaintext){
		local Array of Int is inner: Array();
		:appendBytes(dst: inner, src: plaintext);
		inner:add(item: innerType & 255);
		local Int is ctLen: inner:length() + 16;
		local Array of Int is aad: Array([23, 3, 3, (ctLen >> 8) & 255, ctLen & 255]);
		local Array of Int is nonce: :makeNonce(iv: iv, seq: seq);
		local Array of Int is ctTag: if({ :cipherSuite == 4867 }, {
			ChaCha20Poly1305:seal(key: key, nonce: nonce, aad: aad, plaintext: inner)
		}, {
			Aes128Gcm:seal(key: key, nonce: nonce, aad: aad, plaintext: inner)
		});
		local Array of Int is rec: Array();
		:appendBytes(dst: rec, src: aad);
		:appendBytes(dst: rec, src: ctTag);
		return :sendRawBytes(data: rec);
	}

	local Function of Array of Int is decryptRecord(Array of Int is key, Array of Int is iv, Int is seq, Array of Int is hdr, Array of Int is payload, Array of Int is innerTypeOut){
		local Array of Int is nonce: :makeNonce(iv: iv, seq: seq);
		local Array of Boolean is okFlag: Array();
		local Array of Int is plain: if({ :cipherSuite == 4867 }, {
			ChaCha20Poly1305:open(key: key, nonce: nonce, aad: hdr, ctWithTag: payload, okOut: okFlag)
		}, {
			Aes128Gcm:open(key: key, nonce: nonce, aad: hdr, ctWithTag: payload, okOut: okFlag)
		});
		if({ okFlag:length() == 0 || !okFlag:get(index: 0, default: false) }, {
			:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'TLS record AEAD authentication failed');
			return Array();
		});
		local Int is endIdx: plain:length() - 1;
		while({ endIdx >= 0 && plain:get(index: endIdx, default: 0) == 0 }, { endIdx: endIdx - 1; });
		if({ endIdx < 0 }, {
			:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'TLS inner plaintext missing content type');
			return Array();
		});
		innerTypeOut:add(item: plain:get(index: endIdx, default: 0));
		return :sliceBytes(src: plain, start: 0, count: endIdx);
	}

	## Performs the RFC 8446 TLS 1.3 server handshake on an accepted [clientSocket]
	## using DER certificate chain [certChain] and 32-byte [ed25519Seed].
	Function of Boolean is acceptHandshake(Socket is clientSocket, Array of Array of Int is certChain, Array of Int is ed25519Seed, Int is timeoutMs: 15000){
		:sock: clientSocket;
		:sock:setTimeout(timeoutMs: timeoutMs);
		:connected: false;
		:lastErr: '';

		# 1. Read ClientHello record
		local Array of Int is chHdr: Array();
		local Array of Int is chRec: :readRecord(headerOut: chHdr);
		if({ chHdr:length() < 5 || chHdr:get(index: 0, default: 0) != 22 || chRec:length() < 42 }, {
			:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'Expected TLS ClientHello');
			return false;
		});
		if({ chRec:get(index: 0, default: 0) != 1 }, {
			:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'Expected ClientHello handshake type');
			return false;
		});
		local Int is chMsgLen: (chRec:get(index: 1, default: 0) << 16) | (chRec:get(index: 2, default: 0) << 8) | chRec:get(index: 3, default: 0);
		local Array of Int is chMsg: :sliceBytes(src: chRec, start: 0, count: 4 + chMsgLen);

		# Parse ClientHello fields
		local Int is pos: 4 + 2 + 32;
		local Int is sidLen: chMsg:get(index: pos, default: 0);
		pos: pos + 1;
		local Array of Int is sessionId: :sliceBytes(src: chMsg, start: pos, count: sidLen);
		pos: pos + sidLen;

		local Int is csLen: (chMsg:get(index: pos, default: 0) << 8) | chMsg:get(index: pos + 1, default: 0);
		pos: pos + 2;
		local Boolean is hasAes128: false;
		local Boolean is hasChaCha: false;
		local Int is ci: 0;
		while({ ci + 1 < csLen }, {
			local Int is cs: (chMsg:get(index: pos + ci, default: 0) << 8) | chMsg:get(index: pos + ci + 1, default: 0);
			if({ cs == 4865 }, { hasAes128: true; });
			if({ cs == 4867 }, { hasChaCha: true; });
			ci: ci + 2;
		});
		pos: pos + csLen;
		if({ hasAes128 }, {
			:cipherSuite: 4865;
		}, {
			if({ hasChaCha }, {
				:cipherSuite: 4867;
			}, {
				:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'No supported TLS 1.3 cipher suite offered');
				return false;
			});
		});

		# Skip compression methods
		local Int is compLen: chMsg:get(index: pos, default: 0);
		pos: pos + 1 + compLen;

		# Parse extensions for SNI (0x0000) and X25519 key_share (0x0033)
		local Array of Int is clientX25519Pub: Array();
		if({ pos + 2 <= chMsg:length() }, {
			local Int is extTotal: (chMsg:get(index: pos, default: 0) << 8) | chMsg:get(index: pos + 1, default: 0);
			pos: pos + 2;
			local Int is extEnd: pos + extTotal;
			while({ pos + 4 <= extEnd && pos + 4 <= chMsg:length() }, {
				local Int is eType: (chMsg:get(index: pos, default: 0) << 8) | chMsg:get(index: pos + 1, default: 0);
				local Int is eLen: (chMsg:get(index: pos + 2, default: 0) << 8) | chMsg:get(index: pos + 3, default: 0);
				pos: pos + 4;
				if({ eType == 0 && eLen >= 5 }, {
					# SNI: listLen(2) + nameType(1) + nameLen(2) + bytes
					local Int is nLen: (chMsg:get(index: pos + 3, default: 0) << 8) | chMsg:get(index: pos + 4, default: 0);
					if({ 5 + nLen <= eLen }, {
						local [Byte] is sniBytes;
						local Int is si: 0;
						while({ si < nLen }, {
							sniBytes:push((chMsg:get(index: pos + 5 + si, default: 0) & 255) as Byte);
							si: si + 1;
						});
						:sni: sniBytes:toString();
					});
				});
				if({ eType == 51 && eLen >= 6 }, {
					local Int is ksListLen: (chMsg:get(index: pos, default: 0) << 8) | chMsg:get(index: pos + 1, default: 0);
					local Int is kp: pos + 2;
					local Int is kEnd: kp + ksListLen;
					while({ kp + 4 <= kEnd }, {
						local Int is grp: (chMsg:get(index: kp, default: 0) << 8) | chMsg:get(index: kp + 1, default: 0);
						local Int is kLen: (chMsg:get(index: kp + 2, default: 0) << 8) | chMsg:get(index: kp + 3, default: 0);
						kp: kp + 4;
						if({ grp == 29 && kLen == 32 && kp + 32 <= chMsg:length() }, {
							clientX25519Pub: :sliceBytes(src: chMsg, start: kp, count: 32);
						});
						kp: kp + kLen;
					});
				});
				pos: pos + eLen;
			});
		});

		if({ clientX25519Pub:length() != 32 }, {
			:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'ClientHello missing X25519 key_share');
			return false;
		});

		# 2. Ephemeral X25519 keypair + shared secret
		local Array of Int is sPriv: :makeRandom32();
		local Array of Int is sPub: X25519:publicKey(privateKey: sPriv);
		local Array of Int is sharedSecret: X25519:scalarMult(scalar: sPriv, uCoord: clientX25519Pub);

		# 3. Build & send ServerHello
		local Array of Int is shBody: Array([3, 3]);
		:appendBytes(dst: shBody, src: :makeRandom32());
		shBody:add(item: sessionId:length() & 255);
		:appendBytes(dst: shBody, src: sessionId);
		shBody:add(item: (:cipherSuite >> 8) & 255);
		shBody:add(item: :cipherSuite & 255);
		shBody:add(item: 0);
		# Extensions: supported_versions (6 bytes) + key_share (40 bytes) = 46 bytes
		shBody:add(item: 0); shBody:add(item: 46);
		# supported_versions (0x002b): len 2, 0x0304
		shBody:add(item: 0); shBody:add(item: 43); shBody:add(item: 0); shBody:add(item: 2); shBody:add(item: 3); shBody:add(item: 4);
		# key_share (0x0033): len 36, group 0x001d, keylen 32, sPub
		shBody:add(item: 0); shBody:add(item: 51); shBody:add(item: 0); shBody:add(item: 36);
		shBody:add(item: 0); shBody:add(item: 29); shBody:add(item: 0); shBody:add(item: 32);
		:appendBytes(dst: shBody, src: sPub);

		local Int is shLen: shBody:length();
		local Array of Int is shMsg: Array([2, (shLen >> 16) & 255, (shLen >> 8) & 255, shLen & 255]);
		:appendBytes(dst: shMsg, src: shBody);
		if({ !:sendPlainRecord(rType: 22, payload: shMsg) }, { return false; });
		# Middlebox compatibility ChangeCipherSpec
		if({ !:sendPlainRecord(rType: 20, payload: Array([1])) }, { return false; });

		# 4. Transcript & handshake key schedule
		local Array of Int is transcript: Array();
		:appendBytes(dst: transcript, src: chMsg);
		:appendBytes(dst: transcript, src: shMsg);
		local Array of Int is shHash: Sha256:digest(data: transcript);

		local Array of Int is zeros32: Array();
		local Int is zi: 0;
		while({ zi < 32 }, { zeros32:add(item: 0); zi: zi + 1; });
		local Array of Int is emptyHash: Sha256:digest(data: Array());

		local Array of Int is earlySecret: Sha256:hkdfExtract(salt: zeros32, ikm: zeros32);
		local Array of Int is derived1: Sha256:hkdfExpandLabel(secret: earlySecret, label: 'derived', context: emptyHash, length: 32);
		local Array of Int is hsSecret: Sha256:hkdfExtract(salt: derived1, ikm: sharedSecret);
		local Array of Int is cHsTraffic: Sha256:hkdfExpandLabel(secret: hsSecret, label: 'c hs traffic', context: shHash, length: 32);
		local Array of Int is sHsTraffic: Sha256:hkdfExpandLabel(secret: hsSecret, label: 's hs traffic', context: shHash, length: 32);

		local Int is keyLen: if({ :cipherSuite == 4867 }, { 32 }, { 16 });
		local Array of Int is sHsKey: Sha256:hkdfExpandLabel(secret: sHsTraffic, label: 'key', context: Array(), length: keyLen);
		local Array of Int is sHsIv: Sha256:hkdfExpandLabel(secret: sHsTraffic, label: 'iv', context: Array(), length: 12);
		local Array of Int is cHsKey: Sha256:hkdfExpandLabel(secret: cHsTraffic, label: 'key', context: Array(), length: keyLen);
		local Array of Int is cHsIv: Sha256:hkdfExpandLabel(secret: cHsTraffic, label: 'iv', context: Array(), length: 12);

		# 5a. EncryptedExtensions (empty)
		local Array of Int is eeMsg: Array([8, 0, 0, 2, 0, 0]);
		:appendBytes(dst: transcript, src: eeMsg);
		if({ !:sendEncryptedRecord(key: sHsKey, iv: sHsIv, seq: 0, innerType: 22, plaintext: eeMsg) }, { return false; });

		# 5b. Certificate
		local Array of Int is certEntries: Array();
		local Int is ceri: 0;
		while({ ceri < certChain:length() }, {
			local Array of Int is der: certChain:get(index: ceri);
			local Int is dLen: der:length();
			certEntries:add(item: (dLen >> 16) & 255);
			certEntries:add(item: (dLen >> 8) & 255);
			certEntries:add(item: dLen & 255);
			:appendBytes(dst: certEntries, src: der);
			certEntries:add(item: 0);
			certEntries:add(item: 0);
			ceri: ceri + 1;
		});
		local Int is ceLen: certEntries:length();
		local Int is certBodyLen: 4 + ceLen;
		local Array of Int is certMsg: Array([11, (certBodyLen >> 16) & 255, (certBodyLen >> 8) & 255, certBodyLen & 255, 0, (ceLen >> 16) & 255, (ceLen >> 8) & 255, ceLen & 255]);
		:appendBytes(dst: certMsg, src: certEntries);
		:appendBytes(dst: transcript, src: certMsg);
		if({ !:sendEncryptedRecord(key: sHsKey, iv: sHsIv, seq: 1, innerType: 22, plaintext: certMsg) }, { return false; });

		# 5c. CertificateVerify (Ed25519 = 0x0807)
		local Array of Int is cvHash: Sha256:digest(data: transcript);
		local Array of Int is cvSignIn: Array();
		local Int is sp: 0;
		while({ sp < 64 }, { cvSignIn:add(item: 32); sp: sp + 1; });
		local String is ctxStr: 'TLS 1.3, server CertificateVerify';
		local Int is csi: 0;
		while({ csi < ctxStr:byteLength() }, { cvSignIn:add(item: ctxStr:byteAt(index: csi, default: 0)); csi: csi + 1; });
		cvSignIn:add(item: 0);
		:appendBytes(dst: cvSignIn, src: cvHash);
		local Array of Int is sig64: Ed25519:sign(seed: ed25519Seed, msg: cvSignIn);
		local Array of Int is cvMsg: Array([15, 0, 0, 68, 8, 7, 0, 64]);
		:appendBytes(dst: cvMsg, src: sig64);
		:appendBytes(dst: transcript, src: cvMsg);
		if({ !:sendEncryptedRecord(key: sHsKey, iv: sHsIv, seq: 2, innerType: 22, plaintext: cvMsg) }, { return false; });

		# 5d. Server Finished
		local Array of Int is sFinKey: Sha256:hkdfExpandLabel(secret: sHsTraffic, label: 'finished', context: Array(), length: 32);
		local Array of Int is sVerify: Sha256:hmac(key: sFinKey, msg: Sha256:digest(data: transcript));
		local Array of Int is sFinMsg: Array([20, 0, 0, 32]);
		:appendBytes(dst: sFinMsg, src: sVerify);
		:appendBytes(dst: transcript, src: sFinMsg);
		if({ !:sendEncryptedRecord(key: sHsKey, iv: sHsIv, seq: 3, innerType: 22, plaintext: sFinMsg) }, { return false; });

		# 6. Derive application traffic keys
		local Array of Int is sFinHash: Sha256:digest(data: transcript);
		local Array of Int is derived2: Sha256:hkdfExpandLabel(secret: hsSecret, label: 'derived', context: emptyHash, length: 32);
		local Array of Int is masterSecret: Sha256:hkdfExtract(salt: derived2, ikm: zeros32);
		local Array of Int is cAppTraffic: Sha256:hkdfExpandLabel(secret: masterSecret, label: 'c ap traffic', context: sFinHash, length: 32);
		local Array of Int is sAppTraffic: Sha256:hkdfExpandLabel(secret: masterSecret, label: 's ap traffic', context: sFinHash, length: 32);

		:cAppKey: Sha256:hkdfExpandLabel(secret: cAppTraffic, label: 'key', context: Array(), length: keyLen);
		:cAppIv: Sha256:hkdfExpandLabel(secret: cAppTraffic, label: 'iv', context: Array(), length: 12);
		:cAppSeq: 0;
		:sAppKey: Sha256:hkdfExpandLabel(secret: sAppTraffic, label: 'key', context: Array(), length: keyLen);
		:sAppIv: Sha256:hkdfExpandLabel(secret: sAppTraffic, label: 'iv', context: Array(), length: 12);
		:sAppSeq: 0;

		# 7. Read & verify Client Finished (skipping any plaintext CCS record type 20)
		local Boolean is gotClientFin: false;
		local Boolean is waitingFin: true;
		while({ waitingFin && !gotClientFin }, {
			local Array of Int is cfHdr: Array();
			local Array of Int is cfPayload: :readRecord(headerOut: cfHdr);
			if({ cfHdr:length() < 5 }, {
				:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'Unexpected EOF waiting for Client Finished');
				waitingFin: false;
			}, {
				local Int is rt: cfHdr:get(index: 0, default: 0);
				if({ rt == 20 }, {
					# Skip middlebox CCS
				}, {
					if({ rt != 23 }, {
						:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'Expected encrypted Client Finished record');
						waitingFin: false;
					}, {
						local Array of Int is inType: Array();
						local Array of Int is cfPlain: :decryptRecord(key: cHsKey, iv: cHsIv, seq: 0, hdr: cfHdr, payload: cfPayload, innerTypeOut: inType);
						if({ inType:length() == 0 || inType:get(index: 0, default: 0) != 22 || cfPlain:length() < 36 || cfPlain:get(index: 0, default: 0) != 20 }, {
							:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'Invalid Client Finished message');
							waitingFin: false;
						}, {
							local Array of Int is cFinKey: Sha256:hkdfExpandLabel(secret: cHsTraffic, label: 'finished', context: Array(), length: 32);
							local Array of Int is expectedFin: Sha256:hmac(key: cFinKey, msg: sFinHash);
							local Int is diff: 0;
							local Int is fi: 0;
							while({ fi < 32 }, {
								diff: diff | ((cfPlain:get(index: 4 + fi, default: 0) & 255) ^ (expectedFin:get(index: fi, default: 0) & 255));
								fi: fi + 1;
							});
							if({ diff != 0 }, {
								:setFail(kind: TlsError:HANDSHAKE_FAILED, msg: 'Client Finished MAC mismatch');
							}, {
								gotClientFin: true;
							});
							waitingFin: false;
						});
					});
				});
			});
		});

		if({ !gotClientFin }, { return false; });
		:connected: true;
		return true;
	}

	## Sends [text] as encrypted TLS 1.3 application data.
	Function of Boolean is sendString(String is text){
		if({ !:connected }, { return false; });
		local Int is totalLen: text:byteLength();
		local Int is off: 0;
		while({ off < totalLen }, {
			local Int is chunkLen: if({ (totalLen - off) > 16000 }, { 16000 }, { totalLen - off });
			local Array of Int is chunk: Array();
			local Int is i: 0;
			while({ i < chunkLen }, {
				chunk:add(item: text:byteAt(index: off + i, default: 0));
				i: i + 1;
			});
			local Boolean is ok: :sendEncryptedRecord(key: :sAppKey, iv: :sAppIv, seq: :sAppSeq, innerType: 23, plaintext: chunk);
			:sAppSeq: :sAppSeq + 1;
			if({ !ok }, { return false; });
			off: off + chunkLen;
		});
		return true;
	}

	## Reads one decrypted application-data record as a String (returns '' on close_notify/EOF).
	Function of String is recvString(){
		local [Byte] is buf;
		local Int is n: :recvChunk(outBuf: buf);
		if({ n <= 0 }, { return ''; });
		return buf:toString();
	}

	## Reads one decrypted application-data record into [outBuf] and returns byte count (`<= 0` on EOF/alert).
	Function of Int is recvChunk(List of Byte is outBuf){
		if({ !:connected }, { return 0; });
		local Int is got: 0;
		local Boolean is reading: true;
		while({ reading }, {
			local Array of Int is hdr: Array();
			local Array of Int is payload: :readRecord(headerOut: hdr);
			if({ hdr:length() < 5 }, {
				reading: false;
			}, {
				local Int is rt: hdr:get(index: 0, default: 0);
				if({ rt == 20 }, {
					# skip CCS
				}, {
					if({ rt != 23 }, {
						reading: false;
					}, {
						local Array of Int is inType: Array();
						local Array of Int is plain: :decryptRecord(key: :cAppKey, iv: :cAppIv, seq: :cAppSeq, hdr: hdr, payload: payload, innerTypeOut: inType);
						:cAppSeq: :cAppSeq + 1;
						if({ inType:length() == 0 }, {
							reading: false;
						}, {
							local Int is it: inType:get(index: 0, default: 0);
							if({ it == 23 }, {
								local Int is i: 0;
								while({ i < plain:length() }, {
									outBuf:push((plain:get(index: i, default: 0) & 255) as Byte);
									i: i + 1;
								});
								got: plain:length();
								reading: false;
							}, {
								if({ it == 21 }, { reading: false; });
							});
						});
					});
				});
			});
		});
		return got;
	}

	Function is close(){
		if({ :connected }, {
			# Send encrypted close_notify alert (level=1, desc=0)
			:sendEncryptedRecord(key: :sAppKey, iv: :sAppIv, seq: :sAppSeq, innerType: 21, plaintext: Array([1, 0]));
			:sAppSeq: :sAppSeq + 1;
			:connected: false;
		});
		:sock:close();
	}

	Function of Boolean is isConnected(){ :connected }

	Function of String is clientSni(){ :sni }

	Function of Int is negotiatedCipher(){ :cipherSuite }

	Function of String is lastError(){ :lastErr }
}
