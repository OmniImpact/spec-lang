#! Package base:math:crypto
#! Pure-Spec AES-128-GCM AEAD (FIPS 197 + NIST SP 800-38D).

Class is Aes128Gcm{
	replace [String] is namespace: ['base', 'math', 'crypto'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Array of Int is sbox: Array([
		 99, 124, 119, 123, 242, 107, 111, 197,  48,   1, 103,  43, 254, 215, 171, 118,
		202, 130, 201, 125, 250,  89,  71, 240, 173, 212, 162, 175, 156, 164, 114, 192,
		183, 253, 147,  38,  54,  63, 247, 204,  52, 165, 229, 241, 113, 216,  49,  21,
		  4, 199,  35, 195,  24, 150,   5, 154,   7,  18, 128, 226, 235,  39, 178, 117,
		  9, 131,  44,  26,  27, 110,  90, 160,  82,  59, 214, 179,  41, 227,  47, 132,
		 83, 209,   0, 237,  32, 252, 177,  91, 106, 203, 190,  57,  74,  76,  88, 207,
		208, 239, 170, 251,  67,  77,  51, 133,  69, 249,   2, 127,  80,  60, 159, 168,
		 81, 163,  64, 143, 146, 157,  56, 245, 188, 182, 218,  33,  16, 255, 243, 210,
		205,  12,  19, 236,  95, 151,  68,  23, 196, 167, 126,  61, 100,  93,  25, 115,
		 96, 129,  79, 220,  34,  42, 144, 136,  70, 238, 184,  20, 222,  94,  11, 219,
		224,  50,  58,  10,  73,   6,  36,  92, 194, 211, 172,  98, 145, 149, 228, 121,
		231, 200,  55, 109, 141, 213,  78, 169, 108,  86, 244, 234, 101, 122, 174,   8,
		186, 120,  37,  46,  28, 166, 180, 198, 232, 221, 116,  31,  75, 189, 139, 138,
		112,  62, 181, 102,  72,   3, 246,  14,  97,  53,  87, 185, 134, 193,  29, 158,
		225, 248, 152,  17, 105, 217, 142, 148, 155,  30, 135, 233, 206,  85,  40, 223,
		140, 161, 137,  13, 191, 230,  66, 104,  65, 153,  45,  15, 176,  84, 187,  22
	]);

	local Array of Int is rcon: Array([1, 2, 4, 8, 16, 32, 64, 128, 27, 54]);

	local Function of Int is xtime(Int is a){
		local Int is x: (a << 1) & 255;
		if({ (a & 128) != 0 }, {
			x: x ^ 27;
		});
		return x;
	}

	local Function of Array of Int is expandKey128(Array of Int is key){
		local Array of Int is rk: Array();
		local Int is i: 0;
		while({ i < 16 }, {
			rk:add(item: key:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		local Int is r: 0;
		while({ r < 10 }, {
			local Int is prev: rk:length() - 4;
			local Int is t0: :sbox:get(index: rk:get(index: prev + 1, default: 0), default: 0) ^ :rcon:get(index: r, default: 0);
			local Int is t1: :sbox:get(index: rk:get(index: prev + 2, default: 0), default: 0);
			local Int is t2: :sbox:get(index: rk:get(index: prev + 3, default: 0), default: 0);
			local Int is t3: :sbox:get(index: rk:get(index: prev, default: 0), default: 0);

			local Int is base: rk:length() - 16;
			rk:add(item: rk:get(index: base, default: 0) ^ t0);
			rk:add(item: rk:get(index: base + 1, default: 0) ^ t1);
			rk:add(item: rk:get(index: base + 2, default: 0) ^ t2);
			rk:add(item: rk:get(index: base + 3, default: 0) ^ t3);

			local Int is w: 1;
			while({ w < 4 }, {
				local Int is p: rk:length() - 4;
				local Int is b: rk:length() - 16;
				rk:add(item: rk:get(index: b, default: 0) ^ rk:get(index: p, default: 0));
				rk:add(item: rk:get(index: b + 1, default: 0) ^ rk:get(index: p + 1, default: 0));
				rk:add(item: rk:get(index: b + 2, default: 0) ^ rk:get(index: p + 2, default: 0));
				rk:add(item: rk:get(index: b + 3, default: 0) ^ rk:get(index: p + 3, default: 0));
				w: w + 1;
			});
			r: r + 1;
		});
		return rk;
	}

	## Encrypts one 16-byte block with expanded AES-128 round keys [rk] (176 bytes).
	Function of Array of Int is aesEncryptBlock(Array of Int is rk, Array of Int is block){
		local Array of Int is st: Array();
		local Int is i: 0;
		while({ i < 16 }, {
			st:add(item: (block:get(index: i, default: 0) ^ rk:get(index: i, default: 0)) & 255);
			i: i + 1;
		});

		local Int is round: 1;
		while({ round <= 10 }, {
			# SubBytes
			i: 0;
			while({ i < 16 }, {
				st:set(index: i, item: :sbox:get(index: st:get(index: i, default: 0), default: 0));
				i: i + 1;
			});
			# ShiftRows (column-major state)
			local Int is t: st:get(index: 1, default: 0);
			st:set(index: 1, item: st:get(index: 5, default: 0));
			st:set(index: 5, item: st:get(index: 9, default: 0));
			st:set(index: 9, item: st:get(index: 13, default: 0));
			st:set(index: 13, item: t);

			t: st:get(index: 2, default: 0);
			st:set(index: 2, item: st:get(index: 10, default: 0));
			st:set(index: 10, item: t);
			t: st:get(index: 6, default: 0);
			st:set(index: 6, item: st:get(index: 14, default: 0));
			st:set(index: 14, item: t);

			t: st:get(index: 15, default: 0);
			st:set(index: 15, item: st:get(index: 11, default: 0));
			st:set(index: 11, item: st:get(index: 7, default: 0));
			st:set(index: 7, item: st:get(index: 3, default: 0));
			st:set(index: 3, item: t);

			# MixColumns (rounds 1..9)
			if({ round < 10 }, {
				local Int is c: 0;
				while({ c < 16 }, {
					local Int is s0: st:get(index: c, default: 0);
					local Int is s1: st:get(index: c + 1, default: 0);
					local Int is s2: st:get(index: c + 2, default: 0);
					local Int is s3: st:get(index: c + 3, default: 0);
					local Int is u: s0 ^ s1 ^ s2 ^ s3;
					st:set(index: c,     item: s0 ^ u ^ :xtime(a: s0 ^ s1));
					st:set(index: c + 1, item: s1 ^ u ^ :xtime(a: s1 ^ s2));
					st:set(index: c + 2, item: s2 ^ u ^ :xtime(a: s2 ^ s3));
					st:set(index: c + 3, item: s3 ^ u ^ :xtime(a: s3 ^ s0));
					c: c + 4;
				});
			});

			# AddRoundKey
			local Int is rkOff: round * 16;
			i: 0;
			while({ i < 16 }, {
				st:set(index: i, item: st:get(index: i, default: 0) ^ rk:get(index: rkOff + i, default: 0));
				i: i + 1;
			});
			round: round + 1;
		});
		return st;
	}

	## GF(2^128) multiplication Z = X * Y mod (x^128 + x^7 + x^2 + x + 1) using UInt64 halves.
	local Function of Array of UInt64 is gf128Mul(UInt64 is xHi, UInt64 is xLo, UInt64 is yHi, UInt64 is yLo){
		local UInt64 is zHi: 0 as UInt64;
		local UInt64 is zLo: 0 as UInt64;
		local UInt64 is vHi: yHi;
		local UInt64 is vLo: yLo;
		local UInt64 is rPoly: -2233785415175766016 as UInt64; # 0xE100000000000000
		local UInt64 is highBit: -9223372036854775808 as UInt64; # 0x8000000000000000
		local UInt64 is zero: 0 as UInt64;
		local UInt64 is one: 1 as UInt64;

		local Int is i: 0;
		while({ i < 128 }, {
			local Boolean is bitSet: false;
			if({ i < 64 }, {
				bitSet: ((xHi >> (63 - i)) & one) != zero;
			}, {
				bitSet: ((xLo >> (127 - i)) & one) != zero;
			});
			if({ bitSet }, {
				zHi: zHi ^ vHi;
				zLo: zLo ^ vLo;
			});
			local Boolean is lsb: (vLo & one) != zero;
			local UInt64 is carry: if({ (vHi & one) != zero }, { highBit }, { zero });
			vLo: (vLo >> 1) | carry;
			vHi: vHi >> 1;
			if({ lsb }, {
				vHi: vHi ^ rPoly;
			});
			i: i + 1;
		});
		return Array([zHi, zLo]);
	}

	local Function of UInt64 is loadBe64(Array of Int is b, Int is off){
		local UInt64 is v: 0 as UInt64;
		local Int is i: 0;
		while({ i < 8 }, {
			v: (v << 8) | ((b:get(index: off + i, default: 0) & 255) as UInt64);
			i: i + 1;
		});
		return v;
	}

	local Function of Array of Int is ghash(Array of Int is hBytes, Array of Int is aad, Array of Int is ct){
		local UInt64 is hHi: :loadBe64(b: hBytes, off: 0);
		local UInt64 is hLo: :loadBe64(b: hBytes, off: 8);
		local UInt64 is yHi: 0 as UInt64;
		local UInt64 is yLo: 0 as UInt64;

		# Process AAD in 16-byte zero-padded blocks
		local Int is off: 0;
		while({ off < aad:length() }, {
			local Array of Int is blk: Array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
			local Int is j: 0;
			while({ j < 16 && (off + j) < aad:length() }, {
				blk:set(index: j, item: aad:get(index: off + j, default: 0) & 255);
				j: j + 1;
			});
			local Array of UInt64 is prod: :gf128Mul(xHi: yHi ^ :loadBe64(b: blk, off: 0), xLo: yLo ^ :loadBe64(b: blk, off: 8), yHi: hHi, yLo: hLo);
			yHi: prod:get(index: 0, default: 0 as UInt64);
			yLo: prod:get(index: 1, default: 0 as UInt64);
			off: off + 16;
		});

		# Process ciphertext in 16-byte zero-padded blocks
		off: 0;
		while({ off < ct:length() }, {
			local Array of Int is blk: Array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
			local Int is j: 0;
			while({ j < 16 && (off + j) < ct:length() }, {
				blk:set(index: j, item: ct:get(index: off + j, default: 0) & 255);
				j: j + 1;
			});
			local Array of UInt64 is prod: :gf128Mul(xHi: yHi ^ :loadBe64(b: blk, off: 0), xLo: yLo ^ :loadBe64(b: blk, off: 8), yHi: hHi, yLo: hLo);
			yHi: prod:get(index: 0, default: 0 as UInt64);
			yLo: prod:get(index: 1, default: 0 as UInt64);
			off: off + 16;
		});

		# Final length block: len(aad)*8 || len(ct)*8 (64-bit big-endian each)
		local UInt64 is aadBits: (aad:length() * 8) as UInt64;
		local UInt64 is ctBits: (ct:length() * 8) as UInt64;
		local Array of UInt64 is fin: :gf128Mul(xHi: yHi ^ aadBits, xLo: yLo ^ ctBits, yHi: hHi, yLo: hLo);
		yHi: fin:get(index: 0, default: 0 as UInt64);
		yLo: fin:get(index: 1, default: 0 as UInt64);

		local Array of Int is out: Array();
		local Int is s: 56;
		while({ s >= 0 }, {
			out:add(item: ((yHi >> s) as Int) & 255);
			s: s - 8;
		});
		s: 56;
		while({ s >= 0 }, {
			out:add(item: ((yLo >> s) as Int) & 255);
			s: s - 8;
		});
		return out;
	}

	local Function of Array of Int is gctr(Array of Int is rk, Array of Int is iv12, Int is startCounter, Array of Int is data){
		local Array of Int is out: Array();
		local Int is n: data:length();
		local Int is pos: 0;
		local UInt32 is ctr: startCounter as UInt32;
		while({ pos < n }, {
			local Array of Int is cb: Array();
			local Int is i: 0;
			while({ i < 12 }, {
				cb:add(item: iv12:get(index: i, default: 0) & 255);
				i: i + 1;
			});
			cb:add(item: ((ctr >> 24) as Int) & 255);
			cb:add(item: ((ctr >> 16) as Int) & 255);
			cb:add(item: ((ctr >> 8) as Int) & 255);
			cb:add(item: (ctr as Int) & 255);
			local Array of Int is ks: :aesEncryptBlock(rk: rk, block: cb);
			i: 0;
			while({ i < 16 && pos < n }, {
				out:add(item: (data:get(index: pos, default: 0) ^ ks:get(index: i, default: 0)) & 255);
				pos: pos + 1;
				i: i + 1;
			});
			ctr: ctr + (1 as UInt32);
		});
		return out;
	}

	## AEAD encrypt (AES-128-GCM): returns ciphertext || 16-byte GMAC tag.
	Function of Array of Int is seal(Array of Int is key, Array of Int is nonce, Array of Int is aad, Array of Int is plaintext){
		local Array of Int is rk: :expandKey128(key: key);
		local Array of Int is zeroBlk: Array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
		local Array of Int is hBytes: :aesEncryptBlock(rk: rk, block: zeroBlk);
		local Array of Int is j0: Array();
		local Int is i: 0;
		while({ i < 12 }, { j0:add(item: nonce:get(index: i, default: 0) & 255); i: i + 1; });
		j0:add(item: 0); j0:add(item: 0); j0:add(item: 0); j0:add(item: 1);
		local Array of Int is s0: :aesEncryptBlock(rk: rk, block: j0);

		local Array of Int is ct: :gctr(rk: rk, iv12: nonce, startCounter: 2, data: plaintext);
		local Array of Int is gh: :ghash(hBytes: hBytes, aad: aad, ct: ct);
		i: 0;
		while({ i < 16 }, {
			ct:add(item: (gh:get(index: i, default: 0) ^ s0:get(index: i, default: 0)) & 255);
			i: i + 1;
		});
		return ct;
	}

	## AEAD decrypt (AES-128-GCM): verifies 16-byte GMAC tag on [ctWithTag].
	Function of Array of Int is open(Array of Int is key, Array of Int is nonce, Array of Int is aad, Array of Int is ctWithTag, Array of Boolean is okOut){
		if({ ctWithTag:length() < 16 }, {
			okOut:add(item: false);
			return Array();
		});
		local Int is ctLen: ctWithTag:length() - 16;
		local Array of Int is ct: Array();
		local Int is i: 0;
		while({ i < ctLen }, {
			ct:add(item: ctWithTag:get(index: i, default: 0));
			i: i + 1;
		});

		local Array of Int is rk: :expandKey128(key: key);
		local Array of Int is zeroBlk: Array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
		local Array of Int is hBytes: :aesEncryptBlock(rk: rk, block: zeroBlk);
		local Array of Int is j0: Array();
		i: 0;
		while({ i < 12 }, { j0:add(item: nonce:get(index: i, default: 0) & 255); i: i + 1; });
		j0:add(item: 0); j0:add(item: 0); j0:add(item: 0); j0:add(item: 1);
		local Array of Int is s0: :aesEncryptBlock(rk: rk, block: j0);

		local Array of Int is gh: :ghash(hBytes: hBytes, aad: aad, ct: ct);
		local Int is diff: 0;
		i: 0;
		while({ i < 16 }, {
			local Int is expB: (gh:get(index: i, default: 0) ^ s0:get(index: i, default: 0)) & 255;
			diff: diff | (expB ^ (ctWithTag:get(index: ctLen + i, default: 0) & 255));
			i: i + 1;
		});
		if({ diff != 0 }, {
			okOut:add(item: false);
			return Array();
		});
		okOut:add(item: true);
		return :gctr(rk: rk, iv12: nonce, startCounter: 2, data: ct);
	}
}
