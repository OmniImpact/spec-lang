#! Package base:math:crypto
#! Pure-Spec SHA-1 (RFC 3174) for WebSocket RFC 6455 Sec-WebSocket-Accept handshake.

Class is Sha1{
	replace [String] is namespace: ['base', 'math', 'crypto'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Int is u32(Int is x){ x & 4294967295 }

	local Function of Int is rotl32(Int is x, Int is n){
		local Int is v: :u32(x: x);
		return :u32(x: (v << n) | (v >> (32 - n)));
	}

	## Computes SHA-1 over raw bytes [data] (`0..255`), returning 20 bytes.
	Function of Array of Int is digest(Array of Int is data){
		local Int is h0: 1732584193;
		local Int is h1: 4023233417;
		local Int is h2: 2562383102;
		local Int is h3: 271733878;
		local Int is h4: 3285377520;

		local Int is msgLen: data:length();
		local Array of Int is padded: Array();
		local Int is i: 0;
		while({ i < msgLen }, {
			padded:add(item: data:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		padded:add(item: 128);
		while({ (padded:length() % 64) != 56 }, {
			padded:add(item: 0);
		});
		local Int is bitLen: msgLen * 8;
		local Int is sh: 56;
		while({ sh >= 0 }, {
			padded:add(item: (bitLen >> sh) & 255);
			sh: sh - 8;
		});

		local Array of Int is w: Array();
		local Int is wi: 0;
		while({ wi < 80 }, { w:add(item: 0); wi: wi + 1; });

		local Int is off: 0;
		while({ off < padded:length() }, {
			wi: 0;
			while({ wi < 16 }, {
				local Int is base: off + wi * 4;
				local Int is word: (padded:get(index: base, default: 0) << 24) | (padded:get(index: base + 1, default: 0) << 16) | (padded:get(index: base + 2, default: 0) << 8) | padded:get(index: base + 3, default: 0);
				w:set(index: wi, item: :u32(x: word));
				wi: wi + 1;
			});
			while({ wi < 80 }, {
				local Int is xw: w:get(index: wi - 3, default: 0) ^ w:get(index: wi - 8, default: 0) ^ w:get(index: wi - 14, default: 0) ^ w:get(index: wi - 16, default: 0);
				w:set(index: wi, item: :rotl32(x: xw, n: 1));
				wi: wi + 1;
			});

			local Int is a: h0;
			local Int is b: h1;
			local Int is c: h2;
			local Int is d: h3;
			local Int is e: h4;

			local Int is r: 0;
			while({ r < 80 }, {
				local Int is f: 0;
				local Int is k: 0;
				if({ r < 20 }, {
					f: :u32(x: (b & c) | ((~b) & d));
					k: 1518500249;
				}, {
					if({ r < 40 }, {
						f: :u32(x: b ^ c ^ d);
						k: 1859775393;
					}, {
						if({ r < 60 }, {
							f: :u32(x: (b & c) | (b & d) | (c & d));
							k: 2400959708;
						}, {
							f: :u32(x: b ^ c ^ d);
							k: 3395469782;
						});
					});
				});
				local Int is temp: :u32(x: :rotl32(x: a, n: 5) + f + e + k + w:get(index: r, default: 0));
				e: d;
				d: c;
				c: :rotl32(x: b, n: 30);
				b: a;
				a: temp;
				r: r + 1;
			});

			h0: :u32(x: h0 + a);
			h1: :u32(x: h1 + b);
			h2: :u32(x: h2 + c);
			h3: :u32(x: h3 + d);
			h4: :u32(x: h4 + e);
			off: off + 64;
		});

		local Array of Int is hs: Array([h0, h1, h2, h3, h4]);
		local Array of Int is out: Array();
		local Int is hi: 0;
		while({ hi < 5 }, {
			local Int is hv: hs:get(index: hi, default: 0);
			out:add(item: (hv >> 24) & 255);
			out:add(item: (hv >> 16) & 255);
			out:add(item: (hv >> 8) & 255);
			out:add(item: hv & 255);
			hi: hi + 1;
		});
		return out;
	}

	Function of Array of Int is digestString(String is text){
		local Array of Int is b: Array();
		local Int is i: 0;
		while({ i < text:byteLength() }, {
			b:add(item: text:byteAt(index: i, default: 0));
			i: i + 1;
		});
		return :digest(data: b);
	}
}
