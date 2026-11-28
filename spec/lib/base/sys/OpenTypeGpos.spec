#! Package base:sys
#! Pure-Spec OpenType `cmap` + `GPOS` PairPos (Type 2 / Extension Type 9) kerning parser.

Class is OpenTypeGpos{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'struct', Array]
	];

	String is cmapData: '';
	String is gposData: '';
	Int is cmapFmt12Off: -1;
	Int is cmapFmt4Off: -1;
	Boolean is valid: false;
	Int is asciiKernPtr: 0;
	Int is pairCachePtr: 0;
	Int is pairCacheCap: 0;
	Int is pairCacheCount: 0;

	## Parallel arrays describing each PairPos subtable with xAdvance1 support.
	Array of Int is subOffsets: Array();
	Array of Int is subFormats: Array();
	Array of Int is subCovOffsets: Array();
	Array of Int is subVr1Sizes: Array();
	Array of Int is subVr2Sizes: Array();
	Array of Int is subXAdvOff1s: Array();

	local Function of Int is u16(String is s, Int is off){
		return ((s:byteAt(index: off) & 255) << 8) | (s:byteAt(index: off + 1) & 255);
	}

	local Function of Int is i16(String is s, Int is off){
		local Int is u: :u16(s: s, off: off);
		if({ u >= 32768 }, { return u - 65536; });
		return u;
	}

	local Function of Int is u32(String is s, Int is off){
		local Int is b0: s:byteAt(index: off) & 255;
		local Int is b1: s:byteAt(index: off + 1) & 255;
		local Int is b2: s:byteAt(index: off + 2) & 255;
		local Int is b3: s:byteAt(index: off + 3) & 255;
		return (b0 << 24) | (b1 << 16) | (b2 << 8) | b3;
	}

	local Function of Boolean is matchTag(String is s, Int is off, Int is a, Int is b, Int is c, Int is d){
		return (s:byteAt(index: off) & 255) == a
			&& (s:byteAt(index: off + 1) & 255) == b
			&& (s:byteAt(index: off + 2) & 255) == c
			&& (s:byteAt(index: off + 3) & 255) == d;
	}

	local Function of Int is popcount8(Int is v){
		local Int is x: v & 255;
		local Int is c: 0;
		while({ x != 0 }, {
			if({ (x & 1) != 0 }, { c: c + 1; });
			x: x >> 1;
		});
		return c;
	}

	local Function is reset(){
		if({ asciiKernPtr != 0 }, {
			Mem:free(ptr: asciiKernPtr);
			:asciiKernPtr: 0;
		});
		if({ pairCachePtr != 0 }, {
			Mem:free(ptr: pairCachePtr);
			:pairCachePtr: 0;
			:pairCacheCap: 0;
			:pairCacheCount: 0;
		});
		cmapData: '';
		gposData: '';
		cmapFmt12Off: -1;
		cmapFmt4Off: -1;
		valid: false;
		subOffsets: Array();
		subFormats: Array();
		subCovOffsets: Array();
		subVr1Sizes: Array();
		subVr2Sizes: Array();
		subXAdvOff1s: Array();
	}

	replace Function is init(){
		:reset();
	}

	Function is destroy(){
		if({ asciiKernPtr != 0 }, {
			Mem:free(ptr: asciiKernPtr);
			:asciiKernPtr: 0;
		});
		if({ pairCachePtr != 0 }, {
			Mem:free(ptr: pairCachePtr);
			:pairCachePtr: 0;
			:pairCacheCap: 0;
			:pairCacheCount: 0;
		});
	}

	## Parses `cmap` and `GPOS` tables from raw SFNT [fontBytes].
	Function of Boolean is parse(String is fontBytes){
		:reset();
		local Int is flen: fontBytes:length();
		if({ flen < 12 }, { return false; });
		local Int is numTables: :u16(s: fontBytes, off: 4);
		if({ 12 + numTables * 16 > flen }, { return false; });

		local Int is cmapOff: -1;
		local Int is cmapLen: 0;
		local Int is gposOff: -1;
		local Int is gposLen: 0;
		local Int is i: 0;
		while({ i < numTables }, {
			local Int is rec: 12 + i * 16;
			if({ :matchTag(s: fontBytes, off: rec, a: 99, b: 109, c: 97, d: 112) }, {
				cmapOff: :u32(s: fontBytes, off: rec + 8);
				cmapLen: :u32(s: fontBytes, off: rec + 12);
			});
			if({ :matchTag(s: fontBytes, off: rec, a: 71, b: 80, c: 79, d: 83) }, {
				gposOff: :u32(s: fontBytes, off: rec + 8);
				gposLen: :u32(s: fontBytes, off: rec + 12);
			});
			i: i + 1;
		});

		if({ cmapOff < 0 || cmapLen <= 4 || cmapOff + cmapLen > flen }, { return false; });
		if({ gposOff < 0 || gposLen < 12 || gposOff + gposLen > flen }, { return false; });

		cmapData: fontBytes:substring(start: cmapOff, end: cmapOff + cmapLen);
		gposData: fontBytes:substring(start: gposOff, end: gposOff + gposLen);

		:parseCmap();
		if({ cmapFmt12Off < 0 && cmapFmt4Off < 0 }, {
			cmapData: '';
			gposData: '';
			return false;
		});

		:parseGpos();
		valid: subOffsets:length() > 0;
		if({ !valid }, {
			cmapData: '';
			gposData: '';
		}, {
			:buildAsciiKernCache();
		});
		return valid;
	}

	local Function of Int is pairKey(Int is cp1, Int is cp2){
		return (1 << 42) | ((cp1 & 2097151) << 21) | (cp2 & 2097151);
	}

	local Function of Int is pairSlot(Int is key, Int is mask){
		return (key ^ (key >> 17) ^ (key >> 33)) & mask;
	}

	local Function is ensurePairCacheCap(){
		if({ pairCacheCap == 0 }, {
			local Int is initCap: 64;
			local Int is ptr: Mem:alloc(bytes: initCap * 16);
			if({ ptr == 0 }, { return; });
			Mem:set(dst: ptr, byteVal: 0, bytes: initCap * 16);
			:pairCachePtr: ptr;
			:pairCacheCap: initCap;
			:pairCacheCount: 0;
			return;
		});
		if({ (pairCacheCount + 1) * 2 >= pairCacheCap }, {
			local Int is newCap: pairCacheCap * 2;
			local Int is newPtr: Mem:alloc(bytes: newCap * 16);
			if({ newPtr == 0 }, { return; });
			Mem:set(dst: newPtr, byteVal: 0, bytes: newCap * 16);
			local Int is newMask: newCap - 1;
			local Int is i: 0;
			while({ i < pairCacheCap }, {
				local Int is k: Mem:loadI64(ptr: pairCachePtr, byteOffset: i * 16);
				if({ k != 0 }, {
					local Int is s: :pairSlot(key: k, mask: newMask);
					while({ Mem:loadI64(ptr: newPtr, byteOffset: s * 16) != 0 }, {
						s: (s + 1) & newMask;
					});
					Mem:storeI64(ptr: newPtr, byteOffset: s * 16, val: k);
					Mem:storeI32(ptr: newPtr, byteOffset: s * 16 + 8, val: Mem:loadI32(ptr: pairCachePtr, byteOffset: i * 16 + 8));
				});
				i: i + 1;
			});
			Mem:free(ptr: pairCachePtr);
			:pairCachePtr: newPtr;
			:pairCacheCap: newCap;
		});
	}

	local Function is cachePair(Int is cp1, Int is cp2){
		if({ !valid }, { return; });
		if({ cp1 >= 32 && cp1 <= 126 && cp2 >= 32 && cp2 <= 126 }, { return; });
		:ensurePairCacheCap();
		if({ pairCachePtr == 0 || pairCacheCap == 0 }, { return; });
		local Int is k: :pairKey(cp1: cp1, cp2: cp2);
		local Int is mask: pairCacheCap - 1;
		local Int is s: :pairSlot(key: k, mask: mask);
		while({ true }, {
			local Int is cur: Mem:loadI64(ptr: pairCachePtr, byteOffset: s * 16);
			if({ cur == k }, { return; });
			if({ cur == 0 }, {
				local Int is kv: 0;
				local Int is g1: :glyphId(cp: cp1);
				if({ g1 != 0 }, {
					local Int is g2: :glyphId(cp: cp2);
					if({ g2 != 0 }, {
						kv: :kernAdvanceByGid(g1: g1, g2: g2);
					});
				});
				Mem:storeI64(ptr: pairCachePtr, byteOffset: s * 16, val: k);
				Mem:storeI32(ptr: pairCachePtr, byteOffset: s * 16 + 8, val: kv);
				:pairCacheCount: pairCacheCount + 1;
				return;
			});
			s: (s + 1) & mask;
		});
	}

	## Pre-populates the lock-free pair cache for all non-ASCII character pairs present in [text].
	Function is prewarmText(String is text){
		if({ !valid || text == '' }, { return; });
		local Int is len: text:length();
		local Int is idx: 0;
		local Int is prevCp: 0;
		while({ idx < len }, {
			local Int is c0: text:byteAt(index: idx) & 255;
			local Int is cp: c0;
			local Int is step: 1;
			if({ c0 >= 128 }, {
				if({ (c0 & 224) == 192 && idx + 1 < len }, {
					cp: ((c0 & 31) << 6) | (text:byteAt(index: idx + 1) & 63);
					step: 2;
				}, {
				if({ (c0 & 240) == 224 && idx + 2 < len }, {
					cp: ((c0 & 15) << 12) | ((text:byteAt(index: idx + 1) & 63) << 6) | (text:byteAt(index: idx + 2) & 63);
					step: 3;
				}, {
				if({ (c0 & 248) == 240 && idx + 3 < len }, {
					cp: ((c0 & 7) << 18) | ((text:byteAt(index: idx + 1) & 63) << 12) | ((text:byteAt(index: idx + 2) & 63) << 6) | (text:byteAt(index: idx + 3) & 63);
					step: 4;
				}); }); });
			});
			if({ cp == 10 || cp == 13 || cp == 9 }, {
				prevCp: 0;
			}, {
				if({ cp >= 32 }, {
					if({ prevCp != 0 && (prevCp > 126 || cp > 126) }, {
						:cachePair(cp1: prevCp, cp2: cp);
					});
					prevCp: cp;
				});
			});
			idx: idx + step;
		});
	}

	local Function is buildAsciiKernCache(){
		local Int is gids: Mem:alloc(bytes: 95 * 4);
		local Int is kbuf: Mem:alloc(bytes: 95 * 95 * 4);
		if({ gids == 0 || kbuf == 0 }, {
			if({ gids != 0 }, { Mem:free(ptr: gids); });
			if({ kbuf != 0 }, { Mem:free(ptr: kbuf); });
			return;
		});
		local Int is ci: 0;
		while({ ci < 95 }, {
			Mem:storeI32(ptr: gids, byteOffset: ci * 4, val: :glyphId(cp: 32 + ci));
			ci: ci + 1;
		});
		local Int is i: 0;
		while({ i < 95 }, {
			local Int is g1: Mem:loadI32(ptr: gids, byteOffset: i * 4);
			local Int is rowOff: i * 95;
			local Int is j: 0;
			while({ j < 95 }, {
				local Int is kv: 0;
				if({ g1 != 0 }, {
					local Int is g2: Mem:loadI32(ptr: gids, byteOffset: j * 4);
					if({ g2 != 0 }, {
						kv: :kernAdvanceByGid(g1: g1, g2: g2);
					});
				});
				Mem:storeI32(ptr: kbuf, byteOffset: (rowOff + j) * 4, val: kv);
				j: j + 1;
			});
			i: i + 1;
		});
		Mem:free(ptr: gids);
		:asciiKernPtr: kbuf;
	}

	local Function is parseCmap(){
		local Int is clen: cmapData:length();
		if({ clen < 4 }, { return; });
		local Int is numSub: :u16(s: cmapData, off: 2);
		local Int is i: 0;
		while({ i < numSub && 4 + (i + 1) * 8 <= clen }, {
			local Int is rec: 4 + i * 8;
			local Int is pid: :u16(s: cmapData, off: rec);
			local Int is eid: :u16(s: cmapData, off: rec + 2);
			local Int is subOff: :u32(s: cmapData, off: rec + 4);
			if({ subOff >= 0 && subOff + 4 <= clen }, {
				local Int is fmt: :u16(s: cmapData, off: subOff);
				if({ fmt == 12 && cmapFmt12Off < 0 }, {
					if({ (pid == 3 && eid == 10) || pid == 0 }, {
						cmapFmt12Off: subOff;
					});
				});
				if({ fmt == 4 && cmapFmt4Off < 0 }, {
					if({ (pid == 3 && eid == 1) || pid == 0 }, {
						cmapFmt4Off: subOff;
					});
				});
			});
			i: i + 1;
		});
	}

	local Function is addPairPosSubtable(Int is p){
		local Int is glen: gposData:length();
		if({ p < 0 || p + 10 > glen }, { return; });
		local Int is fmt: :u16(s: gposData, off: p);
		if({ fmt != 1 && fmt != 2 }, { return; });
		local Int is vf1: :u16(s: gposData, off: p + 4);
		local Int is vf2: :u16(s: gposData, off: p + 6);
		if({ (vf1 & 4) == 0 }, { return; });
		local Int is covRel: :u16(s: gposData, off: p + 2);
		local Int is vr1Size: :popcount8(v: vf1 & 255) * 2;
		local Int is vr2Size: :popcount8(v: vf2 & 255) * 2;
		local Int is xAdvOff1: :popcount8(v: vf1 & 3) * 2;
		subOffsets:add(item: p);
		subFormats:add(item: fmt);
		subCovOffsets:add(item: p + covRel);
		subVr1Sizes:add(item: vr1Size);
		subVr2Sizes:add(item: vr2Size);
		subXAdvOff1s:add(item: xAdvOff1);
	}

	local Function is parseGpos(){
		local Int is glen: gposData:length();
		if({ glen < 10 }, { return; });
		local Int is lookupListOff: :u16(s: gposData, off: 8);
		if({ lookupListOff + 2 > glen }, { return; });
		local Int is lookupCount: :u16(s: gposData, off: lookupListOff);
		local Int is li: 0;
		while({ li < lookupCount && lookupListOff + 2 + (li + 1) * 2 <= glen }, {
			local Int is lOff: lookupListOff + :u16(s: gposData, off: lookupListOff + 2 + li * 2);
			if({ lOff + 6 <= glen }, {
				local Int is lType: :u16(s: gposData, off: lOff);
				local Int is subCnt: :u16(s: gposData, off: lOff + 4);
				if({ lType == 2 || lType == 9 }, {
					local Int is si: 0;
					while({ si < subCnt && lOff + 6 + (si + 1) * 2 <= glen }, {
						local Int is sOff: lOff + :u16(s: gposData, off: lOff + 6 + si * 2);
						if({ lType == 2 }, {
							:addPairPosSubtable(p: sOff);
						}, {
							if({ sOff + 8 <= glen }, {
								local Int is extType: :u16(s: gposData, off: sOff + 2);
								if({ extType == 2 }, {
									local Int is extOff: sOff + :u32(s: gposData, off: sOff + 4);
									:addPairPosSubtable(p: extOff);
								});
							});
						});
						si: si + 1;
					});
				});
			});
			li: li + 1;
		});
	}

	local Function of Int is glyphId(Int is cp){
		if({ cmapFmt12Off >= 0 && cmapFmt12Off + 16 <= cmapData:length() }, {
			local Int is nGroups: :u32(s: cmapData, off: cmapFmt12Off + 12);
			local Int is lo: 0;
			local Int is hi: nGroups - 1;
			while({ lo <= hi }, {
				local Int is mid: (lo + hi) / 2;
				local Int is gOff: cmapFmt12Off + 16 + mid * 12;
				local Int is startC: :u32(s: cmapData, off: gOff);
				local Int is endC: :u32(s: cmapData, off: gOff + 4);
				if({ cp < startC }, {
					hi: mid - 1;
				}, {
					if({ cp > endC }, {
						lo: mid + 1;
					}, {
						local Int is startG: :u32(s: cmapData, off: gOff + 8);
						return startG + (cp - startC);
					});
				});
			});
			return 0;
		});
		if({ cmapFmt4Off >= 0 && cp <= 65535 && cmapFmt4Off + 16 <= cmapData:length() }, {
			local Int is segCount: :u16(s: cmapData, off: cmapFmt4Off + 6) / 2;
			local Int is endBase: cmapFmt4Off + 14;
			local Int is startBase: endBase + segCount * 2 + 2;
			local Int is deltaBase: startBase + segCount * 2;
			local Int is rangeBase: deltaBase + segCount * 2;
			local Int is lo: 0;
			local Int is hi: segCount - 1;
			while({ lo <= hi }, {
				local Int is mid: (lo + hi) / 2;
				local Int is ec: :u16(s: cmapData, off: endBase + mid * 2);
				if({ cp > ec }, {
					lo: mid + 1;
				}, {
					local Int is sc: :u16(s: cmapData, off: startBase + mid * 2);
					if({ cp < sc }, {
						hi: mid - 1;
					}, {
						local Int is rOffVal: :u16(s: cmapData, off: rangeBase + mid * 2);
						if({ rOffVal == 0 }, {
							local Int is delta: :i16(s: cmapData, off: deltaBase + mid * 2);
							return (cp + delta) & 65535;
						}, {
							local Int is glyphPtr: rangeBase + mid * 2 + rOffVal + (cp - sc) * 2;
							if({ glyphPtr + 2 <= cmapData:length() }, {
								local Int is gid: :u16(s: cmapData, off: glyphPtr);
								if({ gid == 0 }, { return 0; });
								local Int is delta: :i16(s: cmapData, off: deltaBase + mid * 2);
								return (gid + delta) & 65535;
							});
							return 0;
						});
					});
				});
			});
		});
		return 0;
	}

	local Function of Int is coverageIndex(Int is covOff, Int is gid){
		local Int is glen: gposData:length();
		if({ covOff < 0 || covOff + 4 > glen }, { return -1; });
		local Int is fmt: :u16(s: gposData, off: covOff);
		local Int is cnt: :u16(s: gposData, off: covOff + 2);
		if({ fmt == 1 }, {
			local Int is lo: 0;
			local Int is hi: cnt - 1;
			while({ lo <= hi }, {
				local Int is mid: (lo + hi) / 2;
				local Int is g: :u16(s: gposData, off: covOff + 4 + mid * 2);
				if({ gid < g }, {
					hi: mid - 1;
				}, {
					if({ gid > g }, {
						lo: mid + 1;
					}, {
						return mid;
					});
				});
			});
			return -1;
		});
		if({ fmt == 2 }, {
			local Int is lo: 0;
			local Int is hi: cnt - 1;
			while({ lo <= hi }, {
				local Int is mid: (lo + hi) / 2;
				local Int is rOff: covOff + 4 + mid * 6;
				local Int is sg: :u16(s: gposData, off: rOff);
				local Int is eg: :u16(s: gposData, off: rOff + 2);
				if({ gid < sg }, {
					hi: mid - 1;
				}, {
					if({ gid > eg }, {
						lo: mid + 1;
					}, {
						local Int is scIdx: :u16(s: gposData, off: rOff + 4);
						return scIdx + (gid - sg);
					});
				});
			});
		});
		return -1;
	}

	local Function of Int is classDefValue(Int is cdOff, Int is gid){
		local Int is glen: gposData:length();
		if({ cdOff < 0 || cdOff + 4 > glen }, { return 0; });
		local Int is fmt: :u16(s: gposData, off: cdOff);
		if({ fmt == 1 }, {
			if({ cdOff + 6 > glen }, { return 0; });
			local Int is startG: :u16(s: gposData, off: cdOff + 2);
			local Int is cnt: :u16(s: gposData, off: cdOff + 4);
			if({ gid >= startG && gid < startG + cnt && cdOff + 6 + (gid - startG) * 2 + 2 <= glen }, {
				return :u16(s: gposData, off: cdOff + 6 + (gid - startG) * 2);
			});
			return 0;
		});
		if({ fmt == 2 }, {
			local Int is cnt: :u16(s: gposData, off: cdOff + 2);
			local Int is lo: 0;
			local Int is hi: cnt - 1;
			while({ lo <= hi }, {
				local Int is mid: (lo + hi) / 2;
				local Int is rOff: cdOff + 4 + mid * 6;
				local Int is sg: :u16(s: gposData, off: rOff);
				local Int is eg: :u16(s: gposData, off: rOff + 2);
				if({ gid < sg }, {
					hi: mid - 1;
				}, {
					if({ gid > eg }, {
						lo: mid + 1;
					}, {
						return :u16(s: gposData, off: rOff + 4);
					});
				});
			});
		});
		return 0;
	}

	## Returns raw `GPOS` horizontal kerning adjustment (in font units) between [cp1] and [cp2].
	Function of Int is kernAdvance(Int is cp1, Int is cp2){
		if({ !valid }, { return 0; });
		if({ asciiKernPtr != 0 && cp1 >= 32 && cp1 <= 126 && cp2 >= 32 && cp2 <= 126 }, {
			return Mem:loadS32(ptr: asciiKernPtr, byteOffset: ((cp1 - 32) * 95 + (cp2 - 32)) * 4);
		});
		if({ pairCachePtr != 0 && pairCacheCap > 0 }, {
			local Int is k: :pairKey(cp1: cp1, cp2: cp2);
			local Int is mask: pairCacheCap - 1;
			local Int is s: :pairSlot(key: k, mask: mask);
			local Int is probes: 0;
			while({ probes < pairCacheCap }, {
				local Int is cur: Mem:loadI64(ptr: pairCachePtr, byteOffset: s * 16);
				if({ cur == k }, {
					return Mem:loadS32(ptr: pairCachePtr, byteOffset: s * 16 + 8);
				});
				if({ cur == 0 }, {
					probes: pairCacheCap;
				}, {
					s: (s + 1) & mask;
					probes: probes + 1;
				});
			});
		});
		local Int is g1: :glyphId(cp: cp1);
		if({ g1 == 0 }, { return 0; });
		local Int is g2: :glyphId(cp: cp2);
		if({ g2 == 0 }, { return 0; });
		return :kernAdvanceByGid(g1: g1, g2: g2);
	}

	local Function of Int is kernAdvanceByGid(Int is g1, Int is g2){
		local Int is glen: gposData:length();
		local Int is si: 0;
		local Int is scount: subOffsets:length();
		while({ si < scount }, {
			local Int is p: subOffsets:get(index: si);
			local Int is covIdx: :coverageIndex(covOff: subCovOffsets:get(index: si), gid: g1);
			if({ covIdx >= 0 }, {
				local Int is fmt: subFormats:get(index: si);
				local Int is vr1Size: subVr1Sizes:get(index: si);
				local Int is vr2Size: subVr2Sizes:get(index: si);
				local Int is xAdvOff1: subXAdvOff1s:get(index: si);
				if({ fmt == 1 }, {
					local Int is pairSetCount: :u16(s: gposData, off: p + 8);
					if({ covIdx < pairSetCount }, {
						local Int is psOff: p + :u16(s: gposData, off: p + 10 + covIdx * 2);
						local Int is pairCount: :u16(s: gposData, off: psOff);
						local Int is recSize: 2 + vr1Size + vr2Size;
						local Int is lo: 0;
						local Int is hi: pairCount - 1;
						while({ lo <= hi }, {
							local Int is mid: (lo + hi) / 2;
							local Int is recOff: psOff + 2 + mid * recSize;
							local Int is sg: :u16(s: gposData, off: recOff);
							if({ g2 < sg }, {
								hi: mid - 1;
							}, {
								if({ g2 > sg }, {
									lo: mid + 1;
								}, {
									return :i16(s: gposData, off: recOff + 2 + xAdvOff1);
								});
							});
						});
					});
				}, {
					local Int is cd1Off: p + :u16(s: gposData, off: p + 8);
					local Int is cd2Off: p + :u16(s: gposData, off: p + 10);
					local Int is c1Count: :u16(s: gposData, off: p + 12);
					local Int is c2Count: :u16(s: gposData, off: p + 14);
					local Int is c1: :classDefValue(cdOff: cd1Off, gid: g1);
					local Int is c2: :classDefValue(cdOff: cd2Off, gid: g2);
					if({ c1 < c1Count && c2 < c2Count }, {
						local Int is pairSize: vr1Size + vr2Size;
						local Int is recOff: p + 16 + (c1 * c2Count + c2) * pairSize;
						if({ recOff + xAdvOff1 + 2 <= glen }, {
							return :i16(s: gposData, off: recOff + xAdvOff1);
						});
					});
				});
			});
			si: si + 1;
		});
		return 0;
	}
}
