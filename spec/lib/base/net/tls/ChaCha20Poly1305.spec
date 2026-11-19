#! Package base:net:tls
#! Pure-Spec ChaCha20-Poly1305 AEAD (RFC 8439).

Class is ChaCha20Poly1305{
	namespace: ['base', 'net', 'tls'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Int is rotl32(Int is x, Int is n){
		local Int is u: x & 4294967295;
		return ((u << n) | (u >> (32 - n))) & 4294967295;
	}

	local Function of Int is loadLe32(Array of Int is b, Int is off){
		local Int is b0: b:get(index: off, default: 0) & 255;
		local Int is b1: b:get(index: off + 1, default: 0) & 255;
		local Int is b2: b:get(index: off + 2, default: 0) & 255;
		local Int is b3: b:get(index: off + 3, default: 0) & 255;
		return (b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)) & 4294967295;
	}

	local Function is storeLe32(Array of Int is out, Int is v){
		out:add(item: v & 255);
		out:add(item: (v >> 8) & 255);
		out:add(item: (v >> 16) & 255);
		out:add(item: (v >> 24) & 255);
	}

	local Function is quarterRound(Array of Int is st, Int is a, Int is b, Int is c, Int is d){
		local Int is sa: st:get(index: a, default: 0);
		local Int is sb: st:get(index: b, default: 0);
		local Int is sc: st:get(index: c, default: 0);
		local Int is sd: st:get(index: d, default: 0);

		sa: (sa + sb) & 4294967295;
		sd: :rotl32(x: sd ^ sa, n: 16);
		sc: (sc + sd) & 4294967295;
		sb: :rotl32(x: sb ^ sc, n: 12);
		sa: (sa + sb) & 4294967295;
		sd: :rotl32(x: sd ^ sa, n: 8);
		sc: (sc + sd) & 4294967295;
		sb: :rotl32(x: sb ^ sc, n: 7);

		st:set(index: a, item: sa);
		st:set(index: b, item: sb);
		st:set(index: c, item: sc);
		st:set(index: d, item: sd);
	}

	## Computes one 64-byte ChaCha20 keystream block for 32-byte [key],
	## 32-bit [counter], and 12-byte [nonce].
	Function of Array of Int is chacha20Block(Array of Int is key, Int is counter, Array of Int is nonce){
		local Array of Int is initSt: [
			1634760805, 857760878, 2036477234, 1797285236,
			:loadLe32(b: key, off: 0),  :loadLe32(b: key, off: 4),  :loadLe32(b: key, off: 8),  :loadLe32(b: key, off: 12),
			:loadLe32(b: key, off: 16), :loadLe32(b: key, off: 20), :loadLe32(b: key, off: 24), :loadLe32(b: key, off: 28),
			counter & 4294967295,
			:loadLe32(b: nonce, off: 0), :loadLe32(b: nonce, off: 4), :loadLe32(b: nonce, off: 8)
		];
		local Array of Int is st: [];
		local Int is i: 0;
		while({ i < 16 }, {
			st:add(item: initSt:get(index: i, default: 0));
			i: i + 1;
		});
		local Int is r: 0;
		while({ r < 10 }, {
			:quarterRound(st: st, a: 0, b: 4, c: 8,  d: 12);
			:quarterRound(st: st, a: 1, b: 5, c: 9,  d: 13);
			:quarterRound(st: st, a: 2, b: 6, c: 10, d: 14);
			:quarterRound(st: st, a: 3, b: 7, c: 11, d: 15);
			:quarterRound(st: st, a: 0, b: 5, c: 10, d: 15);
			:quarterRound(st: st, a: 1, b: 6, c: 11, d: 12);
			:quarterRound(st: st, a: 2, b: 7, c: 8,  d: 13);
			:quarterRound(st: st, a: 3, b: 4, c: 9,  d: 14);
			r: r + 1;
		});
		local Array of Int is out: [];
		i: 0;
		while({ i < 16 }, {
			local Int is w: (st:get(index: i, default: 0) + initSt:get(index: i, default: 0)) & 4294967295;
			:storeLe32(out: out, v: w);
			i: i + 1;
		});
		return out;
	}

	## Encrypts/decrypts [data] with ChaCha20 starting at [counter].
	Function of Array of Int is chacha20Xor(Array of Int is key, Int is counter, Array of Int is nonce, Array of Int is data){
		local Array of Int is out: [];
		local Int is n: data:length();
		local Int is pos: 0;
		local Int is blkCnt: counter;
		while({ pos < n }, {
			local Array of Int is ks: :chacha20Block(key: key, counter: blkCnt, nonce: nonce);
			local Int is j: 0;
			while({ j < 64 && pos < n }, {
				out:add(item: (data:get(index: pos, default: 0) ^ ks:get(index: j, default: 0)) & 255);
				pos: pos + 1;
				j: j + 1;
			});
			blkCnt: blkCnt + 1;
		});
		return out;
	}

	## Computes 16-byte Poly1305 MAC over [msg] using 32-byte one-time [otk].
	## Uses 5 x 26-bit limbs (Donna-32 style) so all products fit in signed 64-bit Int.
	Function of Array of Int is poly1305Mac(Array of Int is otk, Array of Int is msg){
		local Int is t0: :loadLe32(b: otk, off: 0);
		local Int is t1: :loadLe32(b: otk, off: 4);
		local Int is t2: :loadLe32(b: otk, off: 8);
		local Int is t3: :loadLe32(b: otk, off: 12);

		local Int is r0: t0 & 67108863;
		local Int is r1: ((t0 >> 26) | (t1 << 6)) & 67108611;
		local Int is r2: ((t1 >> 20) | (t2 << 12)) & 67092735;
		local Int is r3: ((t2 >> 14) | (t3 << 18)) & 66076671;
		local Int is r4: (t3 >> 8) & 1048575;

		local Int is s1: r1 * 5;
		local Int is s2: r2 * 5;
		local Int is s3: r3 * 5;
		local Int is s4: r4 * 5;

		local Int is h0: 0;
		local Int is h1: 0;
		local Int is h2: 0;
		local Int is h3: 0;
		local Int is h4: 0;

		local Int is n: msg:length();
		local Int is off: 0;
		while({ off < n }, {
			local Int is rem: n - off;
			local Int is blkLen: if({ rem >= 16 }, { 16 }, { rem });
			local Array of Int is blk: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
			local Int is bi: 0;
			while({ bi < blkLen }, {
				blk:set(index: bi, item: msg:get(index: off + bi, default: 0) & 255);
				bi: bi + 1;
			});
			local Int is hibit: if({ blkLen == 16 }, { 16777216 }, { 0 });
			if({ blkLen < 16 }, {
				blk:set(index: blkLen, item: 1);
			});

			local Int is b0: :loadLe32(b: blk, off: 0);
			local Int is b1: :loadLe32(b: blk, off: 4);
			local Int is b2: :loadLe32(b: blk, off: 8);
			local Int is b3: :loadLe32(b: blk, off: 12);

			h0: h0 + (b0 & 67108863);
			h1: h1 + (((b0 >> 26) | (b1 << 6)) & 67108863);
			h2: h2 + (((b1 >> 20) | (b2 << 12)) & 67108863);
			h3: h3 + (((b2 >> 14) | (b3 << 18)) & 67108863);
			h4: h4 + ((b3 >> 8) | hibit);

			local Int is d0: h0 * r0 + h1 * s4 + h2 * s3 + h3 * s2 + h4 * s1;
			local Int is d1: h0 * r1 + h1 * r0 + h2 * s4 + h3 * s3 + h4 * s2;
			local Int is d2: h0 * r2 + h1 * r1 + h2 * r0 + h3 * s4 + h4 * s3;
			local Int is d3: h0 * r3 + h1 * r2 + h2 * r1 + h3 * r0 + h4 * s4;
			local Int is d4: h0 * r4 + h1 * r3 + h2 * r2 + h3 * r1 + h4 * r0;

			local Int is c: d0 >> 26; h0: d0 & 67108863;
			d1: d1 + c; c: d1 >> 26; h1: d1 & 67108863;
			d2: d2 + c; c: d2 >> 26; h2: d2 & 67108863;
			d3: d3 + c; c: d3 >> 26; h3: d3 & 67108863;
			d4: d4 + c; c: d4 >> 26; h4: d4 & 67108863;
			h0: h0 + c * 5; c: h0 >> 26; h0: h0 & 67108863;
			h1: h1 + c;

			off: off + 16;
		});

		# Final carry & conditional reduction mod 2^130 - 5
		local Int is cf: h1 >> 26; h1: h1 & 67108863;
		h2: h2 + cf; cf: h2 >> 26; h2: h2 & 67108863;
		h3: h3 + cf; cf: h3 >> 26; h3: h3 & 67108863;
		h4: h4 + cf; cf: h4 >> 26; h4: h4 & 67108863;
		h0: h0 + cf * 5; cf: h0 >> 26; h0: h0 & 67108863;
		h1: h1 + cf;

		local Int is g0: h0 + 5; cf: g0 >> 26; g0: g0 & 67108863;
		local Int is g1: h1 + cf; cf: g1 >> 26; g1: g1 & 67108863;
		local Int is g2: h2 + cf; cf: g2 >> 26; g2: g2 & 67108863;
		local Int is g3: h3 + cf; cf: g3 >> 26; g3: g3 & 67108863;
		local Int is g4: h4 + cf - 67108864;

		local Int is mask: (g4 >> 31) & 4294967295;
		local Int is nmask: if({ g4 < 0 }, { 0 }, { 67108863 });
		local Int is kmask: if({ g4 < 0 }, { 67108863 }, { 0 });
		h0: (h0 & kmask) | (g0 & nmask);
		h1: (h1 & kmask) | (g1 & nmask);
		h2: (h2 & kmask) | (g2 & nmask);
		h3: (h3 & kmask) | (g3 & nmask);
		h4: (h4 & kmask) | (g4 & nmask);

		local Int is f0: ((h0) | (h1 << 26)) & 4294967295;
		local Int is f1: ((h1 >> 6) | (h2 << 20)) & 4294967295;
		local Int is f2: ((h2 >> 12) | (h3 << 14)) & 4294967295;
		local Int is f3: ((h3 >> 18) | (h4 << 8)) & 4294967295;

		local Int is p0: f0 + :loadLe32(b: otk, off: 16);
		local Int is p1: f1 + :loadLe32(b: otk, off: 20) + (p0 >> 32);
		local Int is p2: f2 + :loadLe32(b: otk, off: 24) + (p1 >> 32);
		local Int is p3: f3 + :loadLe32(b: otk, off: 28) + (p2 >> 32);

		local Array of Int is tag: [];
		:storeLe32(out: tag, v: p0 & 4294967295);
		:storeLe32(out: tag, v: p1 & 4294967295);
		:storeLe32(out: tag, v: p2 & 4294967295);
		:storeLe32(out: tag, v: p3 & 4294967295);
		return tag;
	}

	local Function of Array of Int is buildPolyData(Array of Int is aad, Array of Int is ct){
		local Array of Int is macData: [];
		local Int is i: 0;
		while({ i < aad:length() }, {
			macData:add(item: aad:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		while({ (macData:length() % 16) != 0 }, {
			macData:add(item: 0);
		});
		i: 0;
		while({ i < ct:length() }, {
			macData:add(item: ct:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		while({ (macData:length() % 16) != 0 }, {
			macData:add(item: 0);
		});
		local Int is al: aad:length();
		local Int is cl: ct:length();
		:storeLe32(out: macData, v: al & 4294967295);
		:storeLe32(out: macData, v: (al >> 32) & 4294967295);
		:storeLe32(out: macData, v: cl & 4294967295);
		:storeLe32(out: macData, v: (cl >> 32) & 4294967295);
		return macData;
	}

	## AEAD encrypt: returns ciphertext || 16-byte Poly1305 tag.
	Function of Array of Int is seal(Array of Int is key, Array of Int is nonce, Array of Int is aad, Array of Int is plaintext){
		local Array of Int is blk0: :chacha20Block(key: key, counter: 0, nonce: nonce);
		local Array of Int is otk: [];
		local Int is i: 0;
		while({ i < 32 }, {
			otk:add(item: blk0:get(index: i, default: 0));
			i: i + 1;
		});
		local Array of Int is ct: :chacha20Xor(key: key, counter: 1, nonce: nonce, data: plaintext);
		local Array of Int is macData: :buildPolyData(aad: aad, ct: ct);
		local Array of Int is tag: :poly1305Mac(otk: otk, msg: macData);
		i: 0;
		while({ i < 16 }, {
			ct:add(item: tag:get(index: i, default: 0));
			i: i + 1;
		});
		return ct;
	}

	## AEAD decrypt: verifies 16-byte tag on [ctWithTag].
	## Returns plaintext on success, or empty array with [okOut] = [false] on auth failure.
	Function of Array of Int is open(Array of Int is key, Array of Int is nonce, Array of Int is aad, Array of Int is ctWithTag, Array of Boolean is okOut){
		if({ ctWithTag:length() < 16 }, {
			okOut:add(item: false);
			return [];
		});
		local Int is ctLen: ctWithTag:length() - 16;
		local Array of Int is ct: [];
		local Int is i: 0;
		while({ i < ctLen }, {
			ct:add(item: ctWithTag:get(index: i, default: 0));
			i: i + 1;
		});
		local Array of Int is blk0: :chacha20Block(key: key, counter: 0, nonce: nonce);
		local Array of Int is otk: [];
		i: 0;
		while({ i < 32 }, {
			otk:add(item: blk0:get(index: i, default: 0));
			i: i + 1;
		});
		local Array of Int is macData: :buildPolyData(aad: aad, ct: ct);
		local Array of Int is expectedTag: :poly1305Mac(otk: otk, msg: macData);
		local Int is diff: 0;
		i: 0;
		while({ i < 16 }, {
			diff: diff | (expectedTag:get(index: i, default: 0) ^ ctWithTag:get(index: ctLen + i, default: 0));
			i: i + 1;
		});
		if({ diff != 0 }, {
			okOut:add(item: false);
			return [];
		});
		okOut:add(item: true);
		return :chacha20Xor(key: key, counter: 1, nonce: nonce, data: ct);
	}
}
