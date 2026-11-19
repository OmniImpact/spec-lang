#! Package base:net:tls
#! Pure-Spec X25519 Elliptic Curve Diffie-Hellman (RFC 7748).
#! Uses TweetNaCl's 16-limb 16-bit signed field representation over GF(2^255 - 19),
#! keeping all intermediate products safely within signed 64-bit Int.

Class is X25519{
	namespace: ['base', 'net', 'tls'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Array of Int is gfZero(){
		return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
	}

	local Function of Array of Int is gfOne(){
		return [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
	}

	local Function of Array of Int is gf121665(){
		return [56129, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
	}

	local Function of Array of Int is gfAdd(Array of Int is a, Array of Int is b){
		local Array of Int is o: :gfZero();
		local Int is i: 0;
		while({ i < 16 }, {
			o:set(index: i, item: a:get(index: i, default: 0) + b:get(index: i, default: 0));
			i: i + 1;
		});
		return o;
	}

	local Function of Array of Int is gfSub(Array of Int is a, Array of Int is b){
		local Array of Int is o: :gfZero();
		local Int is i: 0;
		while({ i < 16 }, {
			o:set(index: i, item: a:get(index: i, default: 0) - b:get(index: i, default: 0));
			i: i + 1;
		});
		return o;
	}

	local Function is car25519(Array of Int is o){
		local Int is i: 0;
		while({ i < 16 }, {
			local Int is oi: o:get(index: i, default: 0) + 65536;
			local Int is c: oi >> 16;
			local Int is nextIdx: if({ i < 15 }, { i + 1 }, { 0 });
			local Int is addVal: if({ i < 15 }, { c - 1 }, { 38 * (c - 1) });
			o:set(index: nextIdx, item: o:get(index: nextIdx, default: 0) + addVal);
			o:set(index: i, item: oi - (c << 16));
			i: i + 1;
		});
	}

	local Function of Array of Int is gfMul(Array of Int is a, Array of Int is b){
		local Array of Int is t: [];
		local Int is i: 0;
		while({ i < 31 }, {
			t:add(item: 0);
			i: i + 1;
		});
		i: 0;
		while({ i < 16 }, {
			local Int is ai: a:get(index: i, default: 0);
			local Int is j: 0;
			while({ j < 16 }, {
				local Int is idx: i + j;
				t:set(index: idx, item: t:get(index: idx, default: 0) + ai * b:get(index: j, default: 0));
				j: j + 1;
			});
			i: i + 1;
		});
		i: 0;
		while({ i < 15 }, {
			t:set(index: i, item: t:get(index: i, default: 0) + 38 * t:get(index: i + 16, default: 0));
			i: i + 1;
		});
		local Array of Int is o: :gfZero();
		i: 0;
		while({ i < 16 }, {
			o:set(index: i, item: t:get(index: i, default: 0));
			i: i + 1;
		});
		:car25519(o: o);
		:car25519(o: o);
		return o;
	}

	local Function of Array of Int is gfSq(Array of Int is a){
		return :gfMul(a: a, b: a);
	}

	local Function of Array of Int is gfInv(Array of Int is iVal){
		local Array of Int is c: :gfZero();
		local Int is a: 0;
		while({ a < 16 }, {
			c:set(index: a, item: iVal:get(index: a, default: 0));
			a: a + 1;
		});
		a: 253;
		while({ a >= 0 }, {
			c: :gfSq(a: c);
			if({ a != 2 && a != 4 }, {
				c: :gfMul(a: c, b: iVal);
			});
			a: a - 1;
		});
		return c;
	}

	local Function is sel25519(Array of Int is p, Array of Int is q, Int is b){
		local Int is c: 0 - (b & 1);
		local Int is i: 0;
		while({ i < 16 }, {
			local Int is pi: p:get(index: i, default: 0);
			local Int is qi: q:get(index: i, default: 0);
			local Int is t: c & (pi ^ qi);
			p:set(index: i, item: pi ^ t);
			q:set(index: i, item: qi ^ t);
			i: i + 1;
		});
	}

	local Function of Array of Int is unpack25519(Array of Int is n){
		local Array of Int is o: :gfZero();
		local Int is i: 0;
		while({ i < 16 }, {
			local Int is lo: n:get(index: 2 * i, default: 0) & 255;
			local Int is hi: n:get(index: 2 * i + 1, default: 0) & 255;
			o:set(index: i, item: lo + (hi << 8));
			i: i + 1;
		});
		o:set(index: 15, item: o:get(index: 15, default: 0) & 32767);
		return o;
	}

	local Function of Array of Int is pack25519(Array of Int is n){
		local Array of Int is t: :gfZero();
		local Int is i: 0;
		while({ i < 16 }, {
			t:set(index: i, item: n:get(index: i, default: 0));
			i: i + 1;
		});
		:car25519(o: t);
		:car25519(o: t);
		:car25519(o: t);
		local Array of Int is m: :gfZero();
		local Int is j: 0;
		while({ j < 2 }, {
			m:set(index: 0, item: t:get(index: 0, default: 0) - 65517);
			i: 1;
			while({ i < 15 }, {
				local Int is prevM: m:get(index: i - 1, default: 0);
				m:set(index: i, item: t:get(index: i, default: 0) - 65535 - ((prevM >> 16) & 1));
				m:set(index: i - 1, item: prevM & 65535);
				i: i + 1;
			});
			local Int is m14: m:get(index: 14, default: 0);
			m:set(index: 15, item: t:get(index: 15, default: 0) - 32767 - ((m14 >> 16) & 1));
			local Int is b: (m:get(index: 15, default: 0) >> 16) & 1;
			m:set(index: 14, item: m14 & 65535);
			:sel25519(p: t, q: m, b: 1 - b);
			j: j + 1;
		});
		local Array of Int is out: [];
		i: 0;
		while({ i < 16 }, {
			local Int is ti: t:get(index: i, default: 0);
			out:add(item: ti & 255);
			out:add(item: (ti >> 8) & 255);
			i: i + 1;
		});
		return out;
	}

	## Computes X25519(scalar, uCoord) -> 32-byte shared secret / public key.
	Function of Array of Int is scalarMult(Array of Int is scalar, Array of Int is uCoord){
		local Array of Int is z: [];
		local Int is i: 0;
		while({ i < 32 }, {
			z:add(item: scalar:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		z:set(index: 0, item: z:get(index: 0, default: 0) & 248);
		z:set(index: 31, item: (z:get(index: 31, default: 0) & 127) | 64);

		local Array of Int is x: :unpack25519(n: uCoord);
		local Array of Int is a: :gfOne();
		local Array of Int is b: :unpack25519(n: uCoord);
		local Array of Int is c: :gfZero();
		local Array of Int is d: :gfOne();
		local Array of Int is d121665: :gf121665();

		i: 254;
		while({ i >= 0 }, {
			local Int is r: (z:get(index: i >> 3, default: 0) >> (i & 7)) & 1;
			:sel25519(p: a, q: b, b: r);
			:sel25519(p: c, q: d, b: r);
			local Array of Int is e: :gfAdd(a: a, b: c);
			a: :gfSub(a: a, b: c);
			c: :gfAdd(a: b, b: d);
			b: :gfSub(a: b, b: d);
			d: :gfSq(a: e);
			local Array of Int is f: :gfSq(a: a);
			a: :gfMul(a: c, b: a);
			c: :gfMul(a: b, b: e);
			e: :gfAdd(a: a, b: c);
			a: :gfSub(a: a, b: c);
			b: :gfSq(a: a);
			c: :gfSub(a: d, b: f);
			a: :gfMul(a: c, b: d121665);
			a: :gfAdd(a: a, b: d);
			c: :gfMul(a: c, b: a);
			a: :gfMul(a: d, b: f);
			d: :gfMul(a: b, b: x);
			b: :gfSq(a: e);
			:sel25519(p: a, q: b, b: r);
			:sel25519(p: c, q: d, b: r);
			i: i - 1;
		});

		local Array of Int is invC: :gfInv(iVal: c);
		local Array of Int is res: :gfMul(a: a, b: invC);
		return :pack25519(n: res);
	}

	## Computes X25519 public key for 32-byte [privateKey] (basepoint u = 9).
	Function of Array of Int is publicKey(Array of Int is privateKey){
		local Array of Int is basepoint: [
			9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
			0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
		];
		return :scalarMult(scalar: privateKey, uCoord: basepoint);
	}
}
