#! Package base:cleo
#! ANSI-aware UTF-8 display-width measurement, padding, and truncation.

Class is CleoText{
	namespace: ['base', 'cleo'];

	replace Array of Array of String is using: [
		['base', 'sys', as Ansi()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Function of String is repeatStr(String is s, Int is count){
		if({ count <= 0 || s == '' }, { return ''; });
		local String is out: '';
		local Int is i: 0;
		while({ i < count }, {
			out: out . s;
			i: i + 1;
		});
		return out;
	}

	Function of Int is utf8SeqLen(Int is b0){
		if({ b0 < 128 }, { return 1; });
		if({ b0 >= 192 && b0 < 224 }, { return 2; });
		if({ b0 >= 224 && b0 < 240 }, { return 3; });
		if({ b0 >= 240 }, { return 4; });
		return 1;
	}

	Function of Int is charDisplayWidth(String is s, Int is idx, Int is len){
		local Int is b0: s:byteAt(index: idx, default: 0);
		if({ b0 < 32 || b0 == 127 }, { return 0; });
		if({ b0 < 128 }, { return 1; });
		if({ b0 >= 192 && b0 < 224 && (idx + 1) < len }, {
			local Int is b1: s:byteAt(index: idx + 1, default: 0);
			local Int is cp2: ((b0 & 31) << 6) | (b1 & 63);
			if({ (cp2 >= 128 && cp2 <= 159) || cp2 == 173 || (cp2 >= 768 && cp2 <= 879) || (cp2 >= 1155 && cp2 <= 1161) || (cp2 >= 1425 && cp2 <= 1469) }, {
				return 0;
			});
			return 1;
		});
		if({ b0 >= 240 && (idx + 3) < len }, {
			local Int is b1: s:byteAt(index: idx + 1, default: 0);
			local Int is b2: s:byteAt(index: idx + 2, default: 0);
			local Int is b3: s:byteAt(index: idx + 3, default: 0);
			local Int is cp4: ((b0 & 7) << 18) | ((b1 & 63) << 12) | ((b2 & 63) << 6) | (b3 & 63);
			if({ cp4 >= 917760 && cp4 <= 917999 }, { return 0; });
			if({ (cp4 >= 126976 && cp4 <= 129791) || (cp4 >= 131072 && cp4 <= 262141) }, { return 2; });
			return 1;
		});
		if({ b0 >= 224 && b0 < 240 && (idx + 2) < len }, {
			local Int is b1: s:byteAt(index: idx + 1, default: 0);
			local Int is b2: s:byteAt(index: idx + 2, default: 0);
			local Int is cp: ((b0 - 224) * 4096) + ((b1 - 128) * 64) + (b2 - 128);
			# Combining marks, zero-width spaces/joiners, and variation selectors
			if({ (cp >= 6832 && cp <= 6911) || (cp >= 7616 && cp <= 7679) || (cp >= 8203 && cp <= 8207) || (cp >= 8400 && cp <= 8447) || (cp >= 65024 && cp <= 65039) || (cp >= 65056 && cp <= 65071) || cp == 65279 }, {
				return 0;
			});
			# East Asian Wide / Fullwidth / CJK / Hangul / Emoji ranges
			if({ (cp >= 4352 && cp <= 4447) || (cp >= 8986 && cp <= 8987) || (cp >= 9001 && cp <= 9002) || (cp >= 11904 && cp <= 42191 && cp != 12349) || (cp >= 44032 && cp <= 55203) || (cp >= 63744 && cp <= 64255) || (cp >= 65040 && cp <= 65049) || (cp >= 65072 && cp <= 65135) || (cp >= 65281 && cp <= 65376) || (cp >= 65504 && cp <= 65510) }, {
				return 2;
			});
			return 1;
		});
		return 1;
	}

	Function of Int is displayWidth(String is text){
		local Int is len: text:length();
		local Int is i: 0;
		local Int is cols: 0;
		while({ i < len }, {
			local Int is b: text:byteAt(index: i, default: 0);
			if(check: { b == 27 && (i + 1) < len && text:byteAt(index: i + 1, default: 0) == 91 }, then: {
				i: i + 2;
				local Boolean is inSeq: true;
				while({ i < len && inSeq }, {
					local Int is cb: text:byteAt(index: i, default: 0);
					i: i + 1;
					if({ cb >= 64 && cb <= 126 }, {
						inSeq: false;
					});
				});
			}, else: {
				local Int is seqLen: :utf8SeqLen(b0: b);
				cols: cols + :charDisplayWidth(s: text, idx: i, len: len);
				i: i + seqLen;
			});
		});
		return cols;
	}

	Function of String is truncate(String is text, Int is maxCols){
		if({ maxCols <= 0 }, { return ''; });
		local Int is total: :displayWidth(text: text);
		if({ total <= maxCols }, { return text; });
		local Int is limit: if({ maxCols > 3 }, { maxCols - 3 }, { maxCols });
		local Int is len: text:length();
		local Int is i: 0;
		local Int is cols: 0;
		local Int is cutByte: 0;
		local Boolean is keepGoing: true;
		while({ i < len && keepGoing }, {
			local Int is b: text:byteAt(index: i, default: 0);
			if(check: { b == 27 && (i + 1) < len && text:byteAt(index: i + 1, default: 0) == 91 }, then: {
				i: i + 2;
				local Boolean is inSeq: true;
				while({ i < len && inSeq }, {
					local Int is cb: text:byteAt(index: i, default: 0);
					i: i + 1;
					if({ cb >= 64 && cb <= 126 }, {
						inSeq: false;
					});
				});
				cutByte: i;
			}, else: {
				local Int is seqLen: :utf8SeqLen(b0: b);
				local Int is w: :charDisplayWidth(s: text, idx: i, len: len);
				if(check: { cols + w > limit }, then: {
					keepGoing: false;
				}, else: {
					cols: cols + w;
					i: i + seqLen;
					cutByte: i;
				});
			});
		});
		local String is prefix: text:substring(start: 0, end: cutByte);
		if({ maxCols > 3 }, {
			return prefix . '...' . Ansi:reset();
		});
		return prefix . Ansi:reset();
	}

	## Byte offset up to which [text]'s prefix fits [maxCols] display
	## columns — the cut point [truncate] computes before appending
	## its ellipsis, exposed for hard-breaking oversized words.
	Function of Int is widthCutByte(String is text, Int is maxCols){
		local Int is limit: if({ maxCols > 0 }, { maxCols }, { 0 });
		local Int is len: text:length();
		local Int is i: 0;
		local Int is cols: 0;
		local Int is cutByte: 0;
		local Boolean is keepGoing: true;
		while({ i < len && keepGoing }, {
			local Int is b: text:byteAt(index: i, default: 0);
			if(check: { b == 27 && (i + 1) < len && text:byteAt(index: i + 1, default: 0) == 91 }, then: {
				i: i + 2;
				local Boolean is inSeq: true;
				while({ i < len && inSeq }, {
					local Int is cb: text:byteAt(index: i, default: 0);
					i: i + 1;
					if({ cb >= 64 && cb <= 126 }, {
						inSeq: false;
					});
				});
				cutByte: i;
			}, else: {
				local Int is seqLen: :utf8SeqLen(b0: b);
				local Int is w: :charDisplayWidth(s: text, idx: i, len: len);
				if(check: { cols + w > limit }, then: {
					keepGoing: false;
				}, else: {
					cols: cols + w;
					i: i + seqLen;
					cutByte: i;
				});
			});
		});
		return cutByte;
	}

	## Splits [text] into wrap atoms: ANSI escape sequences carry no
	## width and attach to the word that follows them, so a color
	## never strands alone at a line end.
	Function of Array of String is atomsOf(String is text){
		local Array of String is out: Array();
		local Int is len: text:length();
		local Int is i: 0;
		local String is atom: '';
		while({ i < len }, {
			local Int is b: text:byteAt(index: i, default: 0);
			if(check: { b == 27 && (i + 1) < len && text:byteAt(index: i + 1, default: 0) == 91 }, then: {
				local Int is seqStart: i;
				i: i + 2;
				local Boolean is inSeq: true;
				while({ i < len && inSeq }, {
					local Int is cb: text:byteAt(index: i, default: 0);
					i: i + 1;
					if({ cb >= 64 && cb <= 126 }, {
						inSeq: false;
					});
				});
				atom: atom . text:substring(start: seqStart, end: i);
			}, else: {
				if(check: { b == 32 }, then: {
					if(check: { atom != '' }, then: {
						out:add(item: atom);
						atom: '';
					});
					i: i + 1;
				}, else: {
					local Int is seqLen: :utf8SeqLen(b0: b);
					atom: atom . text:substring(start: i, end: i + seqLen);
					i: i + seqLen;
				});
			});
		});
		if(check: { atom != '' }, then: {
			out:add(item: atom);
		});
		return out;
	}

	## Word-wraps [text] to [maxCols] display columns, returning the
	## wrapped rows. Where [truncate] loses everything past the
	## column, [wrap] loses nothing: it is for error and diagnostic
	## output where every character matters. Words wider than the
	## column hard-break at the column boundary.
	Function of Array of String is wrap(String is text, Int is maxCols){
		local Array of String is out: Array();
		if(check: { maxCols <= 0 }, then: {
			out:add(item: text);
			return out;
		});
		local Array of String is atoms: :atomsOf(text: text);
		local String is cur: '';
		local Int is curW: 0;
		local Int is ai: 0;
		while({ ai < atoms:length() }, {
			local String is atom: atoms:get(index: ai, default: '');
			local Int is aw: :displayWidth(text: atom);
			if(check: { aw > maxCols }, then: {
				# Flush the pending row, then hard-break the oversized
				# atom at the column boundary. Trailing ANSI in the
				# remainder stays with it; rows re-style per line.
				if(check: { curW > 0 }, then: {
					out:add(item: cur);
					cur: '';
					curW: 0;
				});
				local Boolean is keepGoing: true;
				while({ keepGoing }, {
					if(check: { :displayWidth(text: atom) <= maxCols }, then: {
						keepGoing: false;
					}, else: {
						local Int is cut: :widthCutByte(text: atom, maxCols: maxCols);
						if(check: { cut <= 0 }, then: {
							keepGoing: false;
						}, else: {
							out:add(item: atom:substring(start: 0, end: cut));
							atom: atom:substring(start: cut, end: atom:length());
						});
					});
				});
			}, else: {
				if(check: { curW > 0 && curW + 1 + aw <= maxCols }, then: {
					cur: cur . ' ' . atom;
					curW: curW + 1 + aw;
				}, else: {
					if(check: { curW > 0 }, then: {
						out:add(item: cur);
					});
					cur: atom;
					curW: aw;
				});
			});
			ai++;
		});
		if(check: { cur != '' || out:length() == 0 }, then: {
			out:add(item: cur);
		});
		return out;
	}

	Function of String is padRight(String is text, Int is width){
		local String is fitted: :truncate(text: text, maxCols: width);
		local Int is w: :displayWidth(text: fitted);
		if({ w >= width }, { return fitted; });
		return fitted . :repeatStr(s: ' ', count: width - w);
	}
}
