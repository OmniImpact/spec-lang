#! Package base:net:tls
#! Pure-Spec SHA-256 (FIPS 180-4), HMAC-SHA256 (RFC 2104), and
#! HKDF-SHA256 / HKDF-Expand-Label (RFC 5869, RFC 8446 §7.1).

Class is Sha256{
	namespace: ['base', 'net', 'tls'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Array of Int is kTable: [
		1116352408, 1899447441, 3049323471, 3921009573,  961987163, 1508970993, 2453635748, 2870763221,
		3624381080,  310598401,  607225278, 1426881987, 1925078388, 2162078206, 2614888103, 3248222580,
		3835390401, 4022224774,  264347078,  604807628,  770255983, 1249150122, 1555081692, 1996064986,
		2554220882, 2821834349, 2952996808, 3210313671, 3336571891, 3584528711,  113926993,  338241895,
		 666307205,  773529912, 1294757372, 1396182291, 1695183700, 1986661051, 2177026350, 2456956037,
		2730485921, 2820302411, 3259730800, 3345764771, 3516065817, 3600352804, 4094571909,  275423344,
		 430227734,  506948616,  659060556,  883997877,  958139571, 1322822218, 1537002063, 1747873779,
		1955562222, 2024104815, 2227730452, 2361852424, 2428436474, 2756734187, 3204031479, 3329325298
	];

	local Function of Int is rotr32(Int is x, Int is n){
		local Int is u: x & 4294967295;
		return ((u >> n) | (u << (32 - n))) & 4294967295;
	}

	## Computes SHA-256 over [data] (array of byte values 0..255).
	## Returns a 32-element Array of Int (0..255).
	Function of Array of Int is digest(Array of Int is data){
		local Int is origLen: data:length();
		local Array of Int is msg: [];
		local Int is i: 0;
		while({ i < origLen }, {
			msg:add(item: data:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		msg:add(item: 128);
		while({ (msg:length() % 64) != 56 }, {
			msg:add(item: 0);
		});
		local Int is bitLen: origLen * 8;
		local Int is s: 56;
		while({ s >= 0 }, {
			msg:add(item: (bitLen >> s) & 255);
			s: s - 8;
		});

		local Int is h0: 1779033703;
		local Int is h1: 3144134277;
		local Int is h2: 1013904242;
		local Int is h3: 2773480762;
		local Int is h4: 1359893119;
		local Int is h5: 2600822924;
		local Int is h6: 528734635;
		local Int is h7: 1541459225;

		local Array of Int is w: [];
		i: 0;
		while({ i < 64 }, {
			w:add(item: 0);
			i: i + 1;
		});

		local Int is off: 0;
		while({ off < msg:length() }, {
			local Int is t: 0;
			while({ t < 16 }, {
				local Int is b0: msg:get(index: off + t * 4, default: 0);
				local Int is b1: msg:get(index: off + t * 4 + 1, default: 0);
				local Int is b2: msg:get(index: off + t * 4 + 2, default: 0);
				local Int is b3: msg:get(index: off + t * 4 + 3, default: 0);
				w:set(index: t, item: ((b0 << 24) | (b1 << 16) | (b2 << 8) | b3) & 4294967295);
				t: t + 1;
			});
			while({ t < 64 }, {
				local Int is w15: w:get(index: t - 15, default: 0);
				local Int is w2: w:get(index: t - 2, default: 0);
				local Int is s0: :rotr32(x: w15, n: 7) ^ :rotr32(x: w15, n: 18) ^ (w15 >> 3);
				local Int is s1: :rotr32(x: w2, n: 17) ^ :rotr32(x: w2, n: 19) ^ (w2 >> 10);
				local Int is wt: (w:get(index: t - 16, default: 0) + s0 + w:get(index: t - 7, default: 0) + s1) & 4294967295;
				w:set(index: t, item: wt);
				t: t + 1;
			});

			local Int is a: h0;
			local Int is b: h1;
			local Int is c: h2;
			local Int is d: h3;
			local Int is e: h4;
			local Int is f: h5;
			local Int is g: h6;
			local Int is h: h7;

			t: 0;
			while({ t < 64 }, {
				local Int is S1: :rotr32(x: e, n: 6) ^ :rotr32(x: e, n: 11) ^ :rotr32(x: e, n: 25);
				local Int is ch: (e & f) ^ ((e ^ 4294967295) & g);
				local Int is temp1: (h + S1 + ch + :kTable:get(index: t, default: 0) + w:get(index: t, default: 0)) & 4294967295;
				local Int is S0: :rotr32(x: a, n: 2) ^ :rotr32(x: a, n: 13) ^ :rotr32(x: a, n: 22);
				local Int is maj: (a & b) ^ (a & c) ^ (b & c);
				local Int is temp2: (S0 + maj) & 4294967295;

				h: g;
				g: f;
				f: e;
				e: (d + temp1) & 4294967295;
				d: c;
				c: b;
				b: a;
				a: (temp1 + temp2) & 4294967295;
				t: t + 1;
			});

			h0: (h0 + a) & 4294967295;
			h1: (h1 + b) & 4294967295;
			h2: (h2 + c) & 4294967295;
			h3: (h3 + d) & 4294967295;
			h4: (h4 + e) & 4294967295;
			h5: (h5 + f) & 4294967295;
			h6: (h6 + g) & 4294967295;
			h7: (h7 + h) & 4294967295;
			off: off + 64;
		});

		local Array of Int is hs: [h0, h1, h2, h3, h4, h5, h6, h7];
		local Array of Int is out: [];
		i: 0;
		while({ i < 8 }, {
			local Int is hv: hs:get(index: i, default: 0);
			out:add(item: (hv >> 24) & 255);
			out:add(item: (hv >> 16) & 255);
			out:add(item: (hv >> 8) & 255);
			out:add(item: hv & 255);
			i: i + 1;
		});
		return out;
	}

	## Computes HMAC-SHA256(key, msg).
	Function of Array of Int is hmac(Array of Int is key, Array of Int is msg){
		local Array of Int is k: key;
		if({ k:length() > 64 }, {
			k: :digest(data: k);
		});
		local Array of Int is ipad: [];
		local Array of Int is opad: [];
		local Int is i: 0;
		while({ i < 64 }, {
			local Int is kb: if({ i < k:length() }, { k:get(index: i, default: 0) & 255 }, { 0 });
			ipad:add(item: kb ^ 54);
			opad:add(item: kb ^ 92);
			i: i + 1;
		});
		i: 0;
		while({ i < msg:length() }, {
			ipad:add(item: msg:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		local Array of Int is inner: :digest(data: ipad);
		i: 0;
		while({ i < inner:length() }, {
			opad:add(item: inner:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		return :digest(data: opad);
	}

	## HKDF-Extract(salt, ikm) = HMAC-SHA256(salt, ikm).
	Function of Array of Int is hkdfExtract(Array of Int is salt, Array of Int is ikm){
		local Array of Int is s: salt;
		if({ s:length() == 0 }, {
			local Array of Int is zeros: [];
			local Int is i: 0;
			while({ i < 32 }, {
				zeros:add(item: 0);
				i: i + 1;
			});
			s: zeros;
		});
		return :hmac(key: s, msg: ikm);
	}

	## HKDF-Expand(prk, info, length).
	Function of Array of Int is hkdfExpand(Array of Int is prk, Array of Int is info, Int is length){
		local Array of Int is out: [];
		local Array of Int is prev: [];
		local Int is counter: 1;
		while({ out:length() < length }, {
			local Array of Int is input: [];
			local Int is i: 0;
			while({ i < prev:length() }, {
				input:add(item: prev:get(index: i, default: 0));
				i: i + 1;
			});
			i: 0;
			while({ i < info:length() }, {
				input:add(item: info:get(index: i, default: 0));
				i: i + 1;
			});
			input:add(item: counter & 255);
			prev: :hmac(key: prk, msg: input);
			i: 0;
			while({ i < prev:length() && out:length() < length }, {
				out:add(item: prev:get(index: i, default: 0));
				i: i + 1;
			});
			counter: counter + 1;
		});
		return out;
	}

	## TLS 1.3 HKDF-Expand-Label(Secret, Label, Context, Length) (RFC 8446 §7.1).
	Function of Array of Int is hkdfExpandLabel(Array of Int is secret, String is label, Array of Int is context, Int is length){
		local String is fullLabel: 'tls13 ' . label;
		local Int is lblLen: fullLabel:byteLength();
		local Array of Int is hkdfLabel: [];
		hkdfLabel:add(item: (length >> 8) & 255);
		hkdfLabel:add(item: length & 255);
		hkdfLabel:add(item: lblLen & 255);
		local Int is i: 0;
		while({ i < lblLen }, {
			hkdfLabel:add(item: fullLabel:byteAt(index: i, default: 0));
			i: i + 1;
		});
		hkdfLabel:add(item: context:length() & 255);
		i: 0;
		while({ i < context:length() }, {
			hkdfLabel:add(item: context:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		return :hkdfExpand(prk: secret, info: hkdfLabel, length: length);
	}

	## TLS 1.3 Derive-Secret(Secret, Label, TranscriptHash).
	Function of Array of Int is deriveSecret(Array of Int is secret, String is label, Array of Int is transcriptHash){
		return :hkdfExpandLabel(secret: secret, label: label, context: transcriptHash, length: 32);
	}

	## Helper: encodes a byte array as lowercase hex string.
	Function of String is toHex(Array of Int is bytes){
		local String is digits: '0123456789abcdef';
		local String is out: '';
		local Int is i: 0;
		while({ i < bytes:length() }, {
			local Int is b: bytes:get(index: i, default: 0) & 255;
			local Int is hi: (b >> 4) & 15;
			local Int is lo: b & 15;
			out: out . digits:substring(start: hi, end: hi + 1) . digits:substring(start: lo, end: lo + 1);
			i: i + 1;
		});
		return out;
	}
}
