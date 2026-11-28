#! Package base:math:crypto
#! Pure-Spec SHA-512 (RFC 6234) using 32-bit unsigned (hi, lo) word pairs
#! so all operations stay safely within signed 64-bit Int.

Class is Sha512{
	replace [String] is namespace: ['base', 'math', 'crypto'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Int is u32(Int is x){ x & 4294967295 }

	local Function of Array of Int is rotr64(Int is hi, Int is lo, Int is n){
		local Int is rHi: 0;
		local Int is rLo: 0;
		if({ n < 32 }, {
			rHi: :u32((hi >> n) | (lo << (32 - n)));
			rLo: :u32((lo >> n) | (hi << (32 - n)));
		}, {
			local Int is m: n - 32;
			rHi: :u32((lo >> m) | (hi << (32 - m)));
			rLo: :u32((hi >> m) | (lo << (32 - m)));
		});
		return Array([rHi, rLo]);
	}

	local Function of Array of Int is shr64(Int is hi, Int is lo, Int is n){
		local Int is rHi: 0;
		local Int is rLo: 0;
		if({ n < 32 }, {
			rHi: :u32(hi >> n);
			rLo: :u32((lo >> n) | (hi << (32 - n)));
		}, {
			rHi: 0;
			rLo: :u32(hi >> (n - 32));
		});
		return Array([rHi, rLo]);
	}

	local Function of Array of Int is add64(Int is aHi, Int is aLo, Int is bHi, Int is bLo){
		local Int is loSum: aLo + bLo;
		local Int is carry: (loSum >> 32) & 1;
		local Int is hiSum: :u32(aHi + bHi + carry);
		return Array([hiSum, :u32(loSum)]);
	}

	## Computes SHA-512 over raw byte array [msg] (`0..255`), returning 64 bytes.
	Function of Array of Int is hash(Array of Int is msg){
		local Array of Int is kHi: Array([
			1116352408, 1899447441, 3049323471, 3921009573, 961987163, 1508970993, 2453635748, 2870763221,
			3624381080, 310598401, 607225278, 1426881987, 1925078388, 2162078206, 2614888103, 3248222580,
			3835390401, 4022224774, 264347078, 604807628, 770255983, 1249150122, 1555081692, 1996064986,
			2554220882, 2821834349, 2952996808, 3210313671, 3336571891, 3584528711, 113926993, 338241895,
			666307205, 773529912, 1294757372, 1396182291, 1695183700, 1986661051, 2177026350, 2456956037,
			2730485921, 2820302411, 3259730800, 3345764771, 3516065817, 3600352804, 4094571909, 275423344,
			430227734, 506948616, 659060556, 883997877, 958139571, 1322822218, 1537002063, 1747873779,
			1955562222, 2024104815, 2227730452, 2361852424, 2428436474, 2756734187, 3204031479, 3329325298,
			3391569614, 3515267271, 3940187606, 4118630271, 116418474, 174292421, 289380356, 460393269,
			685471733, 852142971, 1017036298, 1097609486, 1270296089, 1480736809, 1600394916, 1814624676
		]);
		local Array of Int is kLo: Array([
			3609767458, 602891725, 3964484399, 2173295548, 4081628472, 3053834265, 2937671579, 3664609560,
			2734883394, 1164996542, 1323610764, 3590304994, 4068182383, 991336113, 633803317, 3479774868,
			2666613458, 944711139, 2341262773, 2007800933, 1495990901, 1856431235, 3175218132, 2198950837,
			3999719339, 766784016, 2566594879, 3203337956, 1034457026, 2466948901, 3758326383, 168717936,
			1188179964, 1546045734, 1522805485, 2643833823, 2343527390, 1014477480, 1206759142, 344077627,
			1290863460, 3158454273, 3505952657, 106217008, 3606008344, 1432725776, 1467031594, 851169720,
			3100823752, 1363258195, 3750685593, 3785050280, 3318307427, 3812723403, 2003034995, 3602036899,
			1575990012, 1125592928, 2716904306, 442776044, 593698344, 3733110249, 2999351573, 3815920427,
			3391569614, 3515267271, 3940187606, 4118630271, 116418474, 174292421, 289380356, 460393269,
			685471733, 852142971, 1017036298, 1097609486, 1270296089, 1480736809, 1600394916, 1814624676
		]);
		# Fix K[64..79] lo/hi exact RFC 6234 constants
		kHi:set(index: 64, item: 3391569614); kLo:set(index: 64, item: 3928383900);
		kHi:set(index: 65, item: 3515267271); kLo:set(index: 65, item: 566280711);
		kHi:set(index: 66, item: 3940187606); kLo:set(index: 66, item: 3454069534);
		kHi:set(index: 67, item: 4118630271); kLo:set(index: 67, item: 4000239992);
		kHi:set(index: 68, item: 116418474);  kLo:set(index: 68, item: 1914138554);
		kHi:set(index: 69, item: 174292421);  kLo:set(index: 69, item: 2731055270);
		kHi:set(index: 70, item: 289380356);  kLo:set(index: 70, item: 3203993006);
		kHi:set(index: 71, item: 460393269);  kLo:set(index: 71, item: 320620315);
		kHi:set(index: 72, item: 685471733);  kLo:set(index: 72, item: 587496836);
		kHi:set(index: 73, item: 852142971);  kLo:set(index: 73, item: 1086792851);
		kHi:set(index: 74, item: 1017036298); kLo:set(index: 74, item: 365543100);
		kHi:set(index: 75, item: 1126000580); kLo:set(index: 75, item: 2618297676);
		kHi:set(index: 76, item: 1288033470); kLo:set(index: 76, item: 3409855158);
		kHi:set(index: 77, item: 1501505948); kLo:set(index: 77, item: 4234509866);
		kHi:set(index: 78, item: 1607167915); kLo:set(index: 78, item: 987167468);
		kHi:set(index: 79, item: 1816402316); kLo:set(index: 79, item: 1246189591);

		local Array of Int is hHi: Array([1779033703, 3144134277, 1013904242, 2773480762, 1359893119, 2600822924, 528734635, 1541459225]);
		local Array of Int is hLo: Array([4089235720, 2227873595, 4271175723, 1595750129, 2917565137, 725511199, 4215389547, 327033209]);

		local Int is msgLen: msg:length();
		local Array of Int is padded: Array();
		local Int is i: 0;
		while({ i < msgLen }, {
			padded:add(item: msg:get(index: i, default: 0) & 255);
			i: i + 1;
		});
		padded:add(item: 128);
		while({ (padded:length() % 128) != 112 }, {
			padded:add(item: 0);
		});
		# 128-bit big-endian bit length (top 64 bits = 0)
		local Int is z: 0;
		while({ z < 8 }, {
			padded:add(item: 0);
			z: z + 1;
		});
		local Int is bitLen: msgLen * 8;
		local Int is sh: 56;
		while({ sh >= 0 }, {
			padded:add(item: (bitLen >> sh) & 255);
			sh: sh - 8;
		});

		local Array of Int is wHi: Array();
		local Array of Int is wLo: Array();
		local Int is wi: 0;
		while({ wi < 80 }, {
			wHi:add(item: 0);
			wLo:add(item: 0);
			wi: wi + 1;
		});

		local Int is off: 0;
		while({ off < padded:length() }, {
			wi: 0;
			while({ wi < 16 }, {
				local Int is base: off + wi * 8;
				local Int is bh: ((padded:get(index: base, default: 0) << 24) | (padded:get(index: base + 1, default: 0) << 16) | (padded:get(index: base + 2, default: 0) << 8) | padded:get(index: base + 3, default: 0));
				local Int is bl: ((padded:get(index: base + 4, default: 0) << 24) | (padded:get(index: base + 5, default: 0) << 16) | (padded:get(index: base + 6, default: 0) << 8) | padded:get(index: base + 7, default: 0));
				wHi:set(index: wi, item: :u32(bh));
				wLo:set(index: wi, item: :u32(bl));
				wi: wi + 1;
			});
			while({ wi < 80 }, {
				local Int is p15h: wHi:get(index: wi - 15, default: 0);
				local Int is p15l: wLo:get(index: wi - 15, default: 0);
				local Array of Int is r1: :rotr64(hi: p15h, lo: p15l, n: 1);
				local Array of Int is r8: :rotr64(hi: p15h, lo: p15l, n: 8);
				local Array of Int is s7: :shr64(hi: p15h, lo: p15l, n: 7);
				local Int is s0h: :u32(r1:get(index: 0, default: 0) ^ r8:get(index: 0, default: 0) ^ s7:get(index: 0, default: 0));
				local Int is s0l: :u32(r1:get(index: 1, default: 0) ^ r8:get(index: 1, default: 0) ^ s7:get(index: 1, default: 0));

				local Int is p2h: wHi:get(index: wi - 2, default: 0);
				local Int is p2l: wLo:get(index: wi - 2, default: 0);
				local Array of Int is r19: :rotr64(hi: p2h, lo: p2l, n: 19);
				local Array of Int is r61: :rotr64(hi: p2h, lo: p2l, n: 61);
				local Array of Int is s6: :shr64(hi: p2h, lo: p2l, n: 6);
				local Int is s1h: :u32(r19:get(index: 0, default: 0) ^ r61:get(index: 0, default: 0) ^ s6:get(index: 0, default: 0));
				local Int is s1l: :u32(r19:get(index: 1, default: 0) ^ r61:get(index: 1, default: 0) ^ s6:get(index: 1, default: 0));

				local Array of Int is t1: :add64(aHi: wHi:get(index: wi - 16, default: 0), aLo: wLo:get(index: wi - 16, default: 0), bHi: s0h, bLo: s0l);
				local Array of Int is t2: :add64(aHi: t1:get(index: 0, default: 0), aLo: t1:get(index: 1, default: 0), bHi: wHi:get(index: wi - 7, default: 0), bLo: wLo:get(index: wi - 7, default: 0));
				local Array of Int is t3: :add64(aHi: t2:get(index: 0, default: 0), aLo: t2:get(index: 1, default: 0), bHi: s1h, bLo: s1l);
				wHi:set(index: wi, item: t3:get(index: 0, default: 0));
				wLo:set(index: wi, item: t3:get(index: 1, default: 0));
				wi: wi + 1;
			});

			local Int is ah: hHi:get(index: 0, default: 0); local Int is al: hLo:get(index: 0, default: 0);
			local Int is bh: hHi:get(index: 1, default: 0); local Int is bl: hLo:get(index: 1, default: 0);
			local Int is ch: hHi:get(index: 2, default: 0); local Int is cl: hLo:get(index: 2, default: 0);
			local Int is dh: hHi:get(index: 3, default: 0); local Int is dl: hLo:get(index: 3, default: 0);
			local Int is eh: hHi:get(index: 4, default: 0); local Int is el: hLo:get(index: 4, default: 0);
			local Int is fh: hHi:get(index: 5, default: 0); local Int is fl: hLo:get(index: 5, default: 0);
			local Int is gh: hHi:get(index: 6, default: 0); local Int is gl: hLo:get(index: 6, default: 0);
			local Int is hh: hHi:get(index: 7, default: 0); local Int is hl: hLo:get(index: 7, default: 0);

			local Int is r: 0;
			while({ r < 80 }, {
				local Array of Int is e14: :rotr64(hi: eh, lo: el, n: 14);
				local Array of Int is e18: :rotr64(hi: eh, lo: el, n: 18);
				local Array of Int is e41: :rotr64(hi: eh, lo: el, n: 41);
				local Int is S1h: :u32(e14:get(index: 0, default: 0) ^ e18:get(index: 0, default: 0) ^ e41:get(index: 0, default: 0));
				local Int is S1l: :u32(e14:get(index: 1, default: 0) ^ e18:get(index: 1, default: 0) ^ e41:get(index: 1, default: 0));
				local Int is chh: :u32((eh & fh) ^ ((~eh) & gh));
				local Int is chl: :u32((el & fl) ^ ((~el) & gl));

				local Array of Int is q1: :add64(aHi: hh, aLo: hl, bHi: S1h, bLo: S1l);
				local Array of Int is q2: :add64(aHi: q1:get(index: 0, default: 0), aLo: q1:get(index: 1, default: 0), bHi: chh, bLo: chl);
				local Array of Int is q3: :add64(aHi: q2:get(index: 0, default: 0), aLo: q2:get(index: 1, default: 0), bHi: kHi:get(index: r, default: 0), bLo: kLo:get(index: r, default: 0));
				local Array of Int is temp1: :add64(aHi: q3:get(index: 0, default: 0), aLo: q3:get(index: 1, default: 0), bHi: wHi:get(index: r, default: 0), bLo: wLo:get(index: r, default: 0));

				local Array of Int is a28: :rotr64(hi: ah, lo: al, n: 28);
				local Array of Int is a34: :rotr64(hi: ah, lo: al, n: 34);
				local Array of Int is a39: :rotr64(hi: ah, lo: al, n: 39);
				local Int is S0h: :u32(a28:get(index: 0, default: 0) ^ a34:get(index: 0, default: 0) ^ a39:get(index: 0, default: 0));
				local Int is S0l: :u32(a28:get(index: 1, default: 0) ^ a34:get(index: 1, default: 0) ^ a39:get(index: 1, default: 0));
				local Int is majh: :u32((ah & bh) ^ (ah & ch) ^ (bh & ch));
				local Int is majl: :u32((al & bl) ^ (al & cl) ^ (bl & cl));
				local Array of Int is temp2: :add64(aHi: S0h, aLo: S0l, bHi: majh, bLo: majl);

				hh: gh; hl: gl;
				gh: fh; gl: fl;
				fh: eh; fl: el;
				local Array of Int is ne: :add64(aHi: dh, aLo: dl, bHi: temp1:get(index: 0, default: 0), bLo: temp1:get(index: 1, default: 0));
				eh: ne:get(index: 0, default: 0); el: ne:get(index: 1, default: 0);
				dh: ch; dl: cl;
				ch: bh; cl: bl;
				bh: ah; bl: al;
				local Array of Int is na: :add64(aHi: temp1:get(index: 0, default: 0), aLo: temp1:get(index: 1, default: 0), bHi: temp2:get(index: 0, default: 0), bLo: temp2:get(index: 1, default: 0));
				ah: na:get(index: 0, default: 0); al: na:get(index: 1, default: 0);
				r: r + 1;
			});

			local Array of Int is s0: :add64(aHi: hHi:get(index: 0, default: 0), aLo: hLo:get(index: 0, default: 0), bHi: ah, bLo: al);
			local Array of Int is s1: :add64(aHi: hHi:get(index: 1, default: 0), aLo: hLo:get(index: 1, default: 0), bHi: bh, bLo: bl);
			local Array of Int is s2: :add64(aHi: hHi:get(index: 2, default: 0), aLo: hLo:get(index: 2, default: 0), bHi: ch, bLo: cl);
			local Array of Int is s3: :add64(aHi: hHi:get(index: 3, default: 0), aLo: hLo:get(index: 3, default: 0), bHi: dh, bLo: dl);
			local Array of Int is s4: :add64(aHi: hHi:get(index: 4, default: 0), aLo: hLo:get(index: 4, default: 0), bHi: eh, bLo: el);
			local Array of Int is s5: :add64(aHi: hHi:get(index: 5, default: 0), aLo: hLo:get(index: 5, default: 0), bHi: fh, bLo: fl);
			local Array of Int is s6: :add64(aHi: hHi:get(index: 6, default: 0), aLo: hLo:get(index: 6, default: 0), bHi: gh, bLo: gl);
			local Array of Int is s7: :add64(aHi: hHi:get(index: 7, default: 0), aLo: hLo:get(index: 7, default: 0), bHi: hh, bLo: hl);
			hHi:set(index: 0, item: s0:get(index: 0, default: 0)); hLo:set(index: 0, item: s0:get(index: 1, default: 0));
			hHi:set(index: 1, item: s1:get(index: 0, default: 0)); hLo:set(index: 1, item: s1:get(index: 1, default: 0));
			hHi:set(index: 2, item: s2:get(index: 0, default: 0)); hLo:set(index: 2, item: s2:get(index: 1, default: 0));
			hHi:set(index: 3, item: s3:get(index: 0, default: 0)); hLo:set(index: 3, item: s3:get(index: 1, default: 0));
			hHi:set(index: 4, item: s4:get(index: 0, default: 0)); hLo:set(index: 4, item: s4:get(index: 1, default: 0));
			hHi:set(index: 5, item: s5:get(index: 0, default: 0)); hLo:set(index: 5, item: s5:get(index: 1, default: 0));
			hHi:set(index: 6, item: s6:get(index: 0, default: 0)); hLo:set(index: 6, item: s6:get(index: 1, default: 0));
			hHi:set(index: 7, item: s7:get(index: 0, default: 0)); hLo:set(index: 7, item: s7:get(index: 1, default: 0));
			off: off + 128;
		});

		local Array of Int is out: Array();
		local Int is oi: 0;
		while({ oi < 8 }, {
			local Int is oh: hHi:get(index: oi, default: 0);
			local Int is ol: hLo:get(index: oi, default: 0);
			out:add(item: (oh >> 24) & 255);
			out:add(item: (oh >> 16) & 255);
			out:add(item: (oh >> 8) & 255);
			out:add(item: oh & 255);
			out:add(item: (ol >> 24) & 255);
			out:add(item: (ol >> 16) & 255);
			out:add(item: (ol >> 8) & 255);
			out:add(item: ol & 255);
			oi: oi + 1;
		});
		return out;
	}
}
