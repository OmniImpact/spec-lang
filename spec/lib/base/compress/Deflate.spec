#! Package base:compress
#! Minimal RFC 1951 DEFLATE compressor (LZ77 + Fixed Huffman BTYPE=01 with Stored BTYPE=00 fallback)
#! and full RFC 1951 INFLATE decompressor (supporting BTYPE 00, 01, and 10 Dynamic Huffman).

Class is Deflate{
	replace [String] is namespace: ['base', 'compress'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	# Bit-writer state (used during compress)
	local Array of Int is outBytes: Array();
	local Int is bitBuf: 0;
	local Int is bitCount: 0;

	# Bit-reader state (used during decompress)
	local Array of Int is inBytes: Array();
	local Int is inPos: 0;
	local Int is rBitBuf: 0;
	local Int is rBitCount: 0;

	local Function is resetWriter(){
		:outBytes: Array();
		:bitBuf: 0;
		:bitCount: 0;
	}

	local Function is writeBits(Int is val, Int is nBits){
		:bitBuf: :bitBuf | ((val & ((1 << nBits) - 1)) << :bitCount);
		:bitCount: :bitCount + nBits;
		while({ :bitCount >= 8 }, {
			:outBytes:add(item: :bitBuf & 255);
			:bitBuf: :bitBuf >> 8;
			:bitCount: :bitCount - 8;
		});
	}

	local Function is flushWriter(){
		if({ :bitCount > 0 }, {
			:outBytes:add(item: :bitBuf & 255);
			:bitBuf: 0;
			:bitCount: 0;
		});
	}

	local Function of Int is reverseBits(Int is val, Int is nBits){
		local Int is rev: 0;
		local Int is i: 0;
		while({ i < nBits }, {
			rev: (rev << 1) | ((val >> i) & 1);
			i: i + 1;
		});
		return rev;
	}

	local Function is writeFixedLitLen(Int is sym){
		if({ sym <= 143 }, {
			:writeBits(val: :reverseBits(val: 48 + sym, nBits: 8), nBits: 8);
			return;
		});
		if({ sym <= 255 }, {
			:writeBits(val: :reverseBits(val: 400 + (sym - 144), nBits: 9), nBits: 9);
			return;
		});
		if({ sym <= 279 }, {
			:writeBits(val: :reverseBits(val: sym - 256, nBits: 7), nBits: 7);
			return;
		});
		:writeBits(val: :reverseBits(val: 192 + (sym - 280), nBits: 8), nBits: 8);
	}

	local Function is writeMatch(Int is matchLen, Int is dist){
		local Array of Int is lenBase: Array([3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258]);
		local Array of Int is lenExtra: Array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0]);
		local Int is li: 0;
		while({ li + 1 < 29 && matchLen >= lenBase:get(index: li + 1, default: 259) }, {
			li: li + 1;
		});
		:writeFixedLitLen(sym: 257 + li);
		local Int is le: lenExtra:get(index: li, default: 0);
		if({ le > 0 }, {
			:writeBits(val: matchLen - lenBase:get(index: li, default: 3), nBits: le);
		});

		local Array of Int is distBase: Array([1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577]);
		local Array of Int is distExtra: Array([0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13]);
		local Int is di: 0;
		while({ di + 1 < 30 && dist >= distBase:get(index: di + 1, default: 32769) }, {
			di: di + 1;
		});
		:writeBits(val: :reverseBits(val: di, nBits: 5), nBits: 5);
		local Int is de: distExtra:get(index: di, default: 0);
		if({ de > 0 }, {
			:writeBits(val: dist - distBase:get(index: di, default: 1), nBits: de);
		});
	}

	local Function of Array of Int is emitStored(Array of Int is data){
		local Array of Int is out: Array();
		local Int is n: data:length();
		local Int is off: 0;
		if({ n == 0 }, {
			out:add(item: 1);
			out:add(item: 0); out:add(item: 0);
			out:add(item: 255); out:add(item: 255);
			return out;
		});
		while({ off < n }, {
			local Int is chunk: n - off;
			if({ chunk > 65535 }, { chunk: 65535; });
			local Int is bfinal: if({ off + chunk >= n }, { 1 }, { 0 });
			out:add(item: bfinal);
			out:add(item: chunk & 255);
			out:add(item: (chunk >> 8) & 255);
			local Int is nlen: (~chunk) & 65535;
			out:add(item: nlen & 255);
			out:add(item: (nlen >> 8) & 255);
			local Int is i: 0;
			while({ i < chunk }, {
				out:add(item: data:get(index: off + i, default: 0) & 255);
				i: i + 1;
			});
			off: off + chunk;
		});
		return out;
	}

	## Compresses [data] using RFC 1951 LZ77 + Fixed Huffman (falling back to Stored if smaller).
	Function of Array of Int is compress(Array of Int is data){
		local Int is n: data:length();
		if({ n == 0 }, { return :emitStored(data: data); });

		:resetWriter();
		# BFINAL=1, BTYPE=01 (Fixed Huffman)
		:writeBits(val: 1, nBits: 1);
		:writeBits(val: 1, nBits: 2);

		local Map of Int to Int is headTable: Map();
		local Int is i: 0;
		while({ i < n }, {
			local Int is bestLen: 0;
			local Int is bestDist: 0;
			if({ i + 3 <= n }, {
				local Int is key: ((data:get(index: i, default: 0) & 255) << 16) | ((data:get(index: i + 1, default: 0) & 255) << 8) | (data:get(index: i + 2, default: 0) & 255);
				local Int is prev: headTable:get(key: key, default: -1);
				headTable:set(key: key, value: i);
				if({ prev >= 0 && (i - prev) <= 32768 }, {
					local Int is maxL: n - i;
					if({ maxL > 258 }, { maxL: 258; });
					local Int is mLen: 0;
					while({ mLen < maxL && (data:get(index: prev + mLen, default: 0) & 255) == (data:get(index: i + mLen, default: 0) & 255) }, {
						mLen: mLen + 1;
					});
					if({ mLen >= 3 }, {
						bestLen: mLen;
						bestDist: i - prev;
					});
				});
			});
			if({ bestLen >= 3 }, {
				:writeMatch(matchLen: bestLen, dist: bestDist);
				local Int is k: 1;
				while({ k < bestLen && (i + k + 3) <= n }, {
					local Int is k2: ((data:get(index: i + k, default: 0) & 255) << 16) | ((data:get(index: i + k + 1, default: 0) & 255) << 8) | (data:get(index: i + k + 2, default: 0) & 255);
					headTable:set(key: k2, value: i + k);
					k: k + 1;
				});
				i: i + bestLen;
			}, {
				:writeFixedLitLen(sym: data:get(index: i, default: 0) & 255);
				i: i + 1;
			});
		});
		:writeFixedLitLen(sym: 256);
		:flushWriter();

		local Int is storedEst: n + 5 * ((n / 65535) + 1);
		if({ :outBytes:length() > storedEst }, {
			return :emitStored(data: data);
		});
		return :outBytes;
	}

	# --- Full RFC 1951 Inflate (BTYPE 00, 01, 10) ---

	local Function of Int is readBits(Int is nBits){
		while({ :rBitCount < nBits }, {
			local Int is b: if({ :inPos < :inBytes:length() }, { :inBytes:get(index: :inPos, default: 0) & 255 }, { 0 });
			:inPos: :inPos + 1;
			:rBitBuf: :rBitBuf | (b << :rBitCount);
			:rBitCount: :rBitCount + 8;
		});
		local Int is val: :rBitBuf & ((1 << nBits) - 1);
		:rBitBuf: :rBitBuf >> nBits;
		:rBitCount: :rBitCount - nBits;
		return val;
	}

	local Function is alignByte(){
		local Int is drop: :rBitCount & 7;
		if({ drop > 0 }, {
			:rBitBuf: :rBitBuf >> drop;
			:rBitCount: :rBitCount - drop;
		});
	}

	# Builds canonical Huffman decode table: returns [counts(16), symbols(N)] packed in two Arrays
	local Function is buildHuff(Array of Int is lengths, Array of Int is countsOut, Array of Int is symsOut){
		local Int is i: 0;
		while({ i < 16 }, { countsOut:add(item: 0); i: i + 1; });
		i: 0;
		while({ i < lengths:length() }, {
			local Int is l: lengths:get(index: i, default: 0);
			if({ l > 0 && l < 16 }, {
				countsOut:set(index: l, item: countsOut:get(index: l, default: 0) + 1);
			});
			i: i + 1;
		});
		local Array of Int is offs: Array();
		i: 0;
		while({ i < 16 }, { offs:add(item: 0); i: i + 1; });
		local Int is total: 0;
		i: 1;
		while({ i < 16 }, {
			offs:set(index: i, item: total);
			total: total + countsOut:get(index: i, default: 0);
			i: i + 1;
		});
		i: 0;
		while({ i < total }, { symsOut:add(item: 0); i: i + 1; });
		i: 0;
		while({ i < lengths:length() }, {
			local Int is l2: lengths:get(index: i, default: 0);
			if({ l2 > 0 && l2 < 16 }, {
				local Int is pos: offs:get(index: l2, default: 0);
				symsOut:set(index: pos, item: i);
				offs:set(index: l2, item: pos + 1);
			});
			i: i + 1;
		});
	}

	local Function of Int is decodeSym(Array of Int is counts, Array of Int is syms){
		local Int is code: 0;
		local Int is first: 0;
		local Int is index: 0;
		local Int is len: 1;
		while({ len < 16 }, {
			code: (code << 1) | :readBits(nBits: 1);
			local Int is c: counts:get(index: len, default: 0);
			if({ code - c < first }, {
				return syms:get(index: index + (code - first), default: -1);
			});
			index: index + c;
			first: (first + c) << 1;
			len: len + 1;
		});
		return -1;
	}

	## Decompresses an RFC 1951 DEFLATE stream [data] (supports BTYPE 00, 01, and 10).
	Function of Array of Int is decompress(Array of Int is data){
		:inBytes: data;
		:inPos: 0;
		:rBitBuf: 0;
		:rBitCount: 0;
		local Array of Int is out: Array();

		local Array of Int is lenBase: Array([3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258]);
		local Array of Int is lenExtra: Array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0]);
		local Array of Int is distBase: Array([1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577]);
		local Array of Int is distExtra: Array([0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13]);
		local Array of Int is clOrder: Array([16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]);

		local Boolean is done: false;
		while({ !done }, {
			local Int is bfinal: :readBits(nBits: 1);
			local Int is btype: :readBits(nBits: 2);
			if({ btype == 0 }, {
				:alignByte();
				local Int is slen: :readBits(nBits: 16);
				local Int is _nlen: :readBits(nBits: 16);
				local Int is si: 0;
				while({ si < slen }, {
					out:add(item: :readBits(nBits: 8));
					si: si + 1;
				});
			}, {
				local Array of Int is litLens: Array();
				local Array of Int is distLens: Array();
				if({ btype == 1 }, {
					local Int is k: 0;
					while({ k <= 143 }, { litLens:add(item: 8); k: k + 1; });
					while({ k <= 255 }, { litLens:add(item: 9); k: k + 1; });
					while({ k <= 279 }, { litLens:add(item: 7); k: k + 1; });
					while({ k <= 287 }, { litLens:add(item: 8); k: k + 1; });
					k: 0;
					while({ k < 32 }, { distLens:add(item: 5); k: k + 1; });
				}, {
					if({ btype == 2 }, {
						local Int is hlit: :readBits(nBits: 5) + 257;
						local Int is hdist: :readBits(nBits: 5) + 1;
						local Int is hclen: :readBits(nBits: 4) + 4;
						local Array of Int is clLens: Array();
						local Int is ci: 0;
						while({ ci < 19 }, { clLens:add(item: 0); ci: ci + 1; });
						ci: 0;
						while({ ci < hclen }, {
							clLens:set(index: clOrder:get(index: ci, default: 0), item: :readBits(nBits: 3));
							ci: ci + 1;
						});
						local Array of Int is clCounts: Array();
						local Array of Int is clSyms: Array();
						:buildHuff(lengths: clLens, countsOut: clCounts, symsOut: clSyms);

						local Array of Int is allLens: Array();
						local Int is totalCodes: hlit + hdist;
						while({ allLens:length() < totalCodes }, {
							local Int is sym: :decodeSym(counts: clCounts, syms: clSyms);
							if({ sym < 0 }, { return out; });
							if({ sym < 16 }, {
								allLens:add(item: sym);
							}, {
								if({ sym == 16 }, {
									local Int is rep: :readBits(nBits: 2) + 3;
									local Int is prevL: if({ allLens:length() > 0 }, { allLens:get(index: allLens:length() - 1, default: 0) }, { 0 });
									local Int is ri: 0;
									while({ ri < rep }, { allLens:add(item: prevL); ri: ri + 1; });
								}, {
									if({ sym == 17 }, {
										local Int is rep2: :readBits(nBits: 3) + 3;
										local Int is ri2: 0;
										while({ ri2 < rep2 }, { allLens:add(item: 0); ri2: ri2 + 1; });
									}, {
										local Int is rep3: :readBits(nBits: 7) + 11;
										local Int is ri3: 0;
										while({ ri3 < rep3 }, { allLens:add(item: 0); ri3: ri3 + 1; });
									});
								});
							});
						});
						local Int is ai: 0;
						while({ ai < hlit }, { litLens:add(item: allLens:get(index: ai, default: 0)); ai: ai + 1; });
						while({ ai < totalCodes }, { distLens:add(item: allLens:get(index: ai, default: 0)); ai: ai + 1; });
					}, {
						return out;
					});
				});

				local Array of Int is litCounts: Array();
				local Array of Int is litSyms: Array();
				:buildHuff(lengths: litLens, countsOut: litCounts, symsOut: litSyms);
				local Array of Int is distCounts: Array();
				local Array of Int is distSyms: Array();
				:buildHuff(lengths: distLens, countsOut: distCounts, symsOut: distSyms);

				local Boolean is blockDone: false;
				while({ !blockDone }, {
					local Int is s: :decodeSym(counts: litCounts, syms: litSyms);
					if({ s < 0 || s == 256 }, {
						blockDone: true;
					}, {
						if({ s < 256 }, {
							out:add(item: s);
						}, {
							local Int is lIdx: s - 257;
							local Int is mLen: lenBase:get(index: lIdx, default: 3) + :readBits(nBits: lenExtra:get(index: lIdx, default: 0));
							local Int is dSym: :decodeSym(counts: distCounts, syms: distSyms);
							local Int is dist: distBase:get(index: dSym, default: 1) + :readBits(nBits: distExtra:get(index: dSym, default: 0));
							local Int is mi: 0;
							while({ mi < mLen }, {
								local Int is srcIdx: out:length() - dist;
								local Int is bVal: if({ srcIdx >= 0 }, { out:get(index: srcIdx, default: 0) }, { 0 });
								out:add(item: bVal);
								mi: mi + 1;
							});
						});
					});
				});
			});
			if({ bfinal != 0 }, { done: true; });
		});
		return out;
	}
}
