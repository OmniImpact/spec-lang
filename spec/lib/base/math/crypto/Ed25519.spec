#! Package base:math:crypto
#! Pure-Spec Ed25519 digital signatures (RFC 8032 / TweetNaCl 16-limb GF(2^255-19)).
#! Provides `publicKey(seed32)`, `sign(seed32, msg)`, and `verify(pubKey32, msg, sig64)`.

Class is Ed25519{
	replace [String] is namespace: ['base', 'math', 'crypto'];

	replace [[String]] is using: [
		['base', 'math', 'crypto', as Sha512()],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Array of Int is gfZero(){
		return Array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
	}

	local Function of Array of Int is gfOne(){
		return Array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
	}

	local Function of Array of Int is gfCopy(Array of Int is a){
		local Array of Int is o: :gfZero();
		local Int is i: 0;
		while({ i < 16 }, {
			o:set(index: i, item: a:get(index: i, default: 0));
			i: i + 1;
		});
		return o;
	}

	local Function of Array of Int is gfD(){
		return Array([30883, 4953, 19914, 30187, 55467, 16705, 2637, 112, 59544, 30585, 16505, 36039, 65139, 11119, 27886, 20995]);
	}

	local Function of Array of Int is gfD2(){
		return Array([61785, 9906, 39828, 60374, 45398, 33411, 5274, 224, 53552, 61171, 33010, 6542, 64743, 22239, 55772, 9222]);
	}

	local Function of Array of Int is gfX(){
		return Array([54554, 36645, 11616, 51542, 42930, 38181, 51040, 26924, 56412, 64982, 57905, 49316, 21502, 52590, 14035, 8553]);
	}

	local Function of Array of Int is gfY(){
		return Array([26200, 26214, 26214, 26214, 26214, 26214, 26214, 26214, 26214, 26214, 26214, 26214, 26214, 26214, 26214, 26214]);
	}

	local Function of Array of Int is gfI(){
		return Array([41136, 18958, 6951, 50414, 58488, 44335, 6150, 12099, 55207, 15867, 153, 11085, 57099, 20417, 9344, 11139]);
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
		local Array of Int is t: Array();
		local Int is i: 0;
		while({ i < 31 }, { t:add(item: 0); i: i + 1; });
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

	local Function of Array of Int is gfInv(Array of Int is z){
		local Array of Int is c: :gfCopy(a: z);
		local Int is a: 253;
		while({ a >= 0 }, {
			c: :gfSq(a: c);
			if({ a != 2 && a != 4 }, { c: :gfMul(a: c, b: z); });
			a: a - 1;
		});
		return c;
	}

	local Function of Array of Int is pow2523(Array of Int is iVal){
		local Array of Int is c: :gfCopy(a: iVal);
		local Int is a: 250;
		while({ a >= 0 }, {
			c: :gfSq(a: c);
			if({ a != 1 }, { c: :gfMul(a: c, b: iVal); });
			a: a - 1;
		});
		return c;
	}

	local Function is sel25519(Array of Int is p, Array of Int is q, Int is b){
		local Int is mask: 0 - (b & 1);
		local Int is i: 0;
		while({ i < 16 }, {
			local Int is pi: p:get(index: i, default: 0);
			local Int is qi: q:get(index: i, default: 0);
			local Int is t: mask & (pi ^ qi);
			p:set(index: i, item: pi ^ t);
			q:set(index: i, item: qi ^ t);
			i: i + 1;
		});
	}

	local Function of Array of Int is pack25519(Array of Int is n){
		local Array of Int is t: :gfCopy(a: n);
		:car25519(o: t);
		:car25519(o: t);
		:car25519(o: t);
		local Array of Int is m: :gfZero();
		local Int is j: 0;
		while({ j < 2 }, {
			m:set(index: 0, item: t:get(index: 0, default: 0) - 65517);
			local Int is i: 1;
			while({ i < 15 }, {
				local Int is prev: m:get(index: i - 1, default: 0);
				m:set(index: i, item: t:get(index: i, default: 0) - 65535 - ((prev >> 16) & 1));
				m:set(index: i - 1, item: prev & 65535);
				i: i + 1;
			});
			local Int is prev14: m:get(index: 14, default: 0);
			m:set(index: 15, item: t:get(index: 15, default: 0) - 32767 - ((prev14 >> 16) & 1));
			local Int is b: (m:get(index: 15, default: 0) >> 16) & 1;
			m:set(index: 14, item: prev14 & 65535);
			:sel25519(p: t, q: m, b: 1 - b);
			j: j + 1;
		});
		local Array of Int is out: Array();
		local Int is k: 0;
		while({ k < 16 }, {
			local Int is tk: t:get(index: k, default: 0);
			out:add(item: tk & 255);
			out:add(item: (tk >> 8) & 255);
			k: k + 1;
		});
		return out;
	}

	local Function of Array of Int is unpack25519(Array of Int is n){
		local Array of Int is o: :gfZero();
		local Int is i: 0;
		while({ i < 16 }, {
			o:set(index: i, item: (n:get(index: 2 * i, default: 0) & 255) + ((n:get(index: 2 * i + 1, default: 0) & 255) << 8));
			i: i + 1;
		});
		o:set(index: 15, item: o:get(index: 15, default: 0) & 32767);
		return o;
	}

	local Function of Int is par25519(Array of Int is a){
		local Array of Int is d: :pack25519(n: a);
		return d:get(index: 0, default: 0) & 1;
	}

	local Function of Boolean is neq25519(Array of Int is a, Array of Int is b){
		local Array of Int is c: :pack25519(n: a);
		local Array of Int is d: :pack25519(n: b);
		local Int is diff: 0;
		local Int is i: 0;
		while({ i < 32 }, {
			diff: diff | (c:get(index: i, default: 0) ^ d:get(index: i, default: 0));
			i: i + 1;
		});
		return diff != 0;
	}

	# Extended point [X, Y, Z, T] as Array of 4 gf elements
	local Function is pointAdd(Array of Array of Int is p, Array of Array of Int is q){
		local Array of Int is p0: p:get(index: 0);
		local Array of Int is p1: p:get(index: 1);
		local Array of Int is p2: p:get(index: 2);
		local Array of Int is p3: p:get(index: 3);
		local Array of Int is q0: q:get(index: 0);
		local Array of Int is q1: q:get(index: 1);
		local Array of Int is q2: q:get(index: 2);
		local Array of Int is q3: q:get(index: 3);

		local Array of Int is a: :gfSub(a: p1, b: p0);
		local Array of Int is t: :gfSub(a: q1, b: q0);
		a: :gfMul(a: a, b: t);
		local Array of Int is b: :gfAdd(a: p0, b: p1);
		t: :gfAdd(a: q0, b: q1);
		b: :gfMul(a: b, b: t);
		local Array of Int is c: :gfMul(a: p3, b: q3);
		c: :gfMul(a: c, b: :gfD2());
		local Array of Int is d: :gfMul(a: p2, b: q2);
		d: :gfAdd(a: d, b: d);
		local Array of Int is e: :gfSub(a: b, b: a);
		local Array of Int is f: :gfSub(a: d, b: c);
		local Array of Int is g: :gfAdd(a: d, b: c);
		local Array of Int is h: :gfAdd(a: b, b: a);

		p:set(index: 0, item: :gfMul(a: e, b: f));
		p:set(index: 1, item: :gfMul(a: h, b: g));
		p:set(index: 2, item: :gfMul(a: g, b: f));
		p:set(index: 3, item: :gfMul(a: e, b: h));
	}

	local Function is cswapPoint(Array of Array of Int is p, Array of Array of Int is q, Int is b){
		local Int is i: 0;
		while({ i < 4 }, {
			:sel25519(p: p:get(index: i), q: q:get(index: i), b: b);
			i: i + 1;
		});
	}

	local Function of Array of Array of Int is scalarMult(Array of Array of Int is qIn, Array of Int is s){
		local Array of Array of Int is p: Array([:gfZero(), :gfOne(), :gfOne(), :gfZero()]);
		local Array of Array of Int is q: Array([:gfCopy(a: qIn:get(index: 0)), :gfCopy(a: qIn:get(index: 1)), :gfCopy(a: qIn:get(index: 2)), :gfCopy(a: qIn:get(index: 3))]);
		local Int is i: 255;
		while({ i >= 0 }, {
			local Int is bit: (s:get(index: i >> 3, default: 0) >> (i & 7)) & 1;
			:cswapPoint(p: p, q: q, b: bit);
			:pointAdd(p: q, q: p);
			:pointAdd(p: p, q: p);
			:cswapPoint(p: p, q: q, b: bit);
			i: i - 1;
		});
		return p;
	}

	local Function of Array of Array of Int is scalarMultBase(Array of Int is s){
		local Array of Int is bx: :gfX();
		local Array of Int is by: :gfY();
		local Array of Array of Int is q: Array([bx, by, :gfOne(), :gfMul(a: bx, b: by)]);
		return :scalarMult(qIn: q, s: s);
	}

	local Function of Array of Int is packPoint(Array of Array of Int is p){
		local Array of Int is zi: :gfInv(z: p:get(index: 2));
		local Array of Int is tx: :gfMul(a: p:get(index: 0), b: zi);
		local Array of Int is ty: :gfMul(a: p:get(index: 1), b: zi);
		local Array of Int is r: :pack25519(n: ty);
		r:set(index: 31, item: r:get(index: 31, default: 0) ^ (:par25519(a: tx) << 7));
		return r;
	}

	local Function of Array of Int is modL(Array of Int is x){
		local Array of Int is L: Array([237, 211, 245, 92, 26, 99, 18, 88, 214, 156, 247, 162, 222, 249, 222, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16]);
		local Int is i: 63;
		while({ i >= 32 }, {
			local Int is carry: 0;
			local Int is j: i - 32;
			local Int is k: i - 12;
			while({ j < k }, {
				local Int is xj: x:get(index: j, default: 0) + carry - 16 * x:get(index: i, default: 0) * L:get(index: j - (i - 32), default: 0);
				carry: (xj + 128) >> 8;
				x:set(index: j, item: xj - carry * 256);
				j: j + 1;
			});
			x:set(index: j, item: x:get(index: j, default: 0) + carry);
			x:set(index: i, item: 0);
			i: i - 1;
		});
		local Int is carry2: 0;
		local Int is j2: 0;
		while({ j2 < 32 }, {
			local Int is xj2: x:get(index: j2, default: 0) + carry2 - (x:get(index: 31, default: 0) >> 4) * L:get(index: j2, default: 0);
			carry2: xj2 >> 8;
			x:set(index: j2, item: xj2 & 255);
			j2: j2 + 1;
		});
		j2: 0;
		while({ j2 < 32 }, {
			x:set(index: j2, item: x:get(index: j2, default: 0) - carry2 * L:get(index: j2, default: 0));
			j2: j2 + 1;
		});
		local Array of Int is r: Array();
		i: 0;
		while({ i < 32 }, {
			local Int is xi: x:get(index: i, default: 0);
			if({ i < 31 }, {
				x:set(index: i + 1, item: x:get(index: i + 1, default: 0) + (xi >> 8));
			});
			r:add(item: xi & 255);
			i: i + 1;
		});
		return r;
	}

	local Function of Array of Int is reduce64(Array of Int is h64){
		local Array of Int is x: Array();
		local Int is i: 0;
		while({ i < 64 }, {
			x:add(item: h64:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		return :modL(x: x);
	}

	## Derives the 32-byte Ed25519 public key from a 32-byte [seed].
	Function of Array of Int is publicKey(Array of Int is seed){
		local Array of Int is d: Sha512:hash(msg: seed);
		d:set(index: 0, item: d:get(index: 0, default: 0) & 248);
		d:set(index: 31, item: (d:get(index: 31, default: 0) & 127) | 64);
		local Array of Array of Int is p: :scalarMultBase(s: d);
		return :packPoint(p: p);
	}

	## Signs [msg] with 32-byte [seed], returning the 64-byte RFC 8032 Ed25519 signature.
	Function of Array of Int is sign(Array of Int is seed, Array of Int is msg){
		local Array of Int is d: Sha512:hash(msg: seed);
		d:set(index: 0, item: d:get(index: 0, default: 0) & 248);
		d:set(index: 31, item: (d:get(index: 31, default: 0) & 127) | 64);
		local Array of Int is pub: :packPoint(p: :scalarMultBase(s: d));

		# r = H(d[32..63] || msg) mod L
		local Array of Int is rIn: Array();
		local Int is i: 32;
		while({ i < 64 }, { rIn:add(item: d:get(index: i, default: 0) & 255); i: i + 1; });
		i: 0;
		while({ i < msg:length() }, { rIn:add(item: msg:get(index: i, default: 0) & 255); i: i + 1; });
		local Array of Int is r: :reduce64(h64: Sha512:hash(msg: rIn));
		local Array of Int is R: :packPoint(p: :scalarMultBase(s: r));

		# h = H(R || pub || msg) mod L
		local Array of Int is hIn: Array();
		i: 0;
		while({ i < 32 }, { hIn:add(item: R:get(index: i, default: 0) & 255); i: i + 1; });
		i: 0;
		while({ i < 32 }, { hIn:add(item: pub:get(index: i, default: 0) & 255); i: i + 1; });
		i: 0;
		while({ i < msg:length() }, { hIn:add(item: msg:get(index: i, default: 0) & 255); i: i + 1; });
		local Array of Int is h: :reduce64(h64: Sha512:hash(msg: hIn));

		# S = (r + h * a) mod L
		local Array of Int is x: Array();
		i: 0;
		while({ i < 64 }, { x:add(item: 0); i: i + 1; });
		i: 0;
		while({ i < 32 }, { x:set(index: i, item: r:get(index: i, default: 0) & 255); i: i + 1; });
		i: 0;
		while({ i < 32 }, {
			local Int is hi: h:get(index: i, default: 0) & 255;
			local Int is j: 0;
			while({ j < 32 }, {
				local Int is idx: i + j;
				x:set(index: idx, item: x:get(index: idx, default: 0) + hi * (d:get(index: j, default: 0) & 255));
				j: j + 1;
			});
			i: i + 1;
		});
		local Array of Int is S: :modL(x: x);

		local Array of Int is sig: Array();
		i: 0;
		while({ i < 32 }, { sig:add(item: R:get(index: i, default: 0) & 255); i: i + 1; });
		i: 0;
		while({ i < 32 }, { sig:add(item: S:get(index: i, default: 0) & 255); i: i + 1; });
		return sig;
	}

	## Verifies a 64-byte Ed25519 [sig] over [msg] against 32-byte [pubKey].
	Function of Boolean is verify(Array of Int is pubKey, Array of Int is msg, Array of Int is sig){
		if({ pubKey:length() != 32 || sig:length() != 64 }, { return false; });
		# Unpack pubKey -> point A
		local Array of Int is py: :unpack25519(n: pubKey);
		local Array of Int is num: :gfSub(a: :gfSq(a: py), b: :gfOne());
		local Array of Int is den: :gfAdd(a: :gfMul(a: :gfD(), b: :gfSq(a: py)), b: :gfOne());
		local Array of Int is den2: :gfSq(a: den);
		local Array of Int is den4: :gfSq(a: den2);
		local Array of Int is den6: :gfMul(a: den4, b: den2);
		local Array of Int is t: :gfMul(a: den6, b: num);
		t: :gfMul(a: t, b: den);
		t: :pow2523(iVal: t);
		t: :gfMul(a: t, b: num);
		t: :gfMul(a: t, b: den);
		t: :gfMul(a: t, b: den);
		local Array of Int is px: :gfMul(a: t, b: den);
		local Array of Int is chk: :gfMul(a: den, b: :gfSq(a: px));
		if({ :neq25519(a: chk, b: num) }, {
			px: :gfMul(a: px, b: :gfI());
		});
		chk: :gfMul(a: den, b: :gfSq(a: px));
		if({ :neq25519(a: chk, b: num) }, { return false; });
		if({ :par25519(a: px) == ((pubKey:get(index: 31, default: 0) >> 7) & 1) }, {
			px: :gfSub(a: :gfZero(), b: px);
		});
		local Array of Array of Int is negA: Array([px, py, :gfOne(), :gfMul(a: px, b: py)]);

		# h = H(R || pubKey || msg) mod L
		local Array of Int is hIn: Array();
		local Int is i: 0;
		while({ i < 32 }, { hIn:add(item: sig:get(index: i, default: 0) & 255); i: i + 1; });
		i: 0;
		while({ i < 32 }, { hIn:add(item: pubKey:get(index: i, default: 0) & 255); i: i + 1; });
		i: 0;
		while({ i < msg:length() }, { hIn:add(item: msg:get(index: i, default: 0) & 255); i: i + 1; });
		local Array of Int is h: :reduce64(h64: Sha512:hash(msg: hIn));

		local Array of Int is sBytes: Array();
		i: 32;
		while({ i < 64 }, { sBytes:add(item: sig:get(index: i, default: 0) & 255); i: i + 1; });

		local Array of Array of Int is p1: :scalarMult(qIn: negA, s: h);
		local Array of Array of Int is p2: :scalarMultBase(s: sBytes);
		:pointAdd(p: p1, q: p2);
		local Array of Int is rCheck: :packPoint(p: p1);

		local Int is diff: 0;
		i: 0;
		while({ i < 32 }, {
			diff: diff | ((rCheck:get(index: i, default: 0) & 255) ^ (sig:get(index: i, default: 0) & 255));
			i: i + 1;
		});
		return diff == 0;
	}
}
