#! Package base:cleo
#! ANSI-aware UTF-8 display-width measurement, padding, and truncation.

Class is CleoText{
	namespace: ['base', 'cleo'];

	replace Array of Array of String is using: [
		['base', 'sys', as Ansi()],
		['base', 'sys', as Buf()],
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
		local Int is b0: Buf:bufGetByte(b: s, idx: idx, def: 0);
		if({ b0 < 32 }, { return 0; });
		if({ b0 < 128 }, { return 1; });
		if({ b0 >= 192 && b0 < 224 }, { return 1; });
		if({ b0 >= 240 }, { return 2; });
		if({ b0 >= 224 && b0 < 240 && (idx + 2) < len }, {
			local Int is b1: Buf:bufGetByte(b: s, idx: idx + 1, def: 0);
			local Int is b2: Buf:bufGetByte(b: s, idx: idx + 2, def: 0);
			local Int is cp: ((b0 - 224) * 4096) + ((b1 - 128) * 64) + (b2 - 128);
			# CJK / Hangul / Fullwidth ranges
			if({ (cp >= 12288 && cp <= 40959) || (cp >= 44032 && cp <= 55203) || (cp >= 65281 && cp <= 65376) }, {
				return 2;
			});
			return 1;
		});
		return 1;
	}

	Function of Int is displayWidth(String is text){
		local Int is len: Buf:bufLength(b: text);
		local Int is i: 0;
		local Int is cols: 0;
		while({ i < len }, {
			local Int is b: Buf:bufGetByte(b: text, idx: i, def: 0);
			if(check: { b == 27 && (i + 1) < len && Buf:bufGetByte(b: text, idx: i + 1, def: 0) == 91 }, then: {
				i: i + 2;
				local Boolean is inSeq: true;
				while({ i < len && inSeq }, {
					local Int is cb: Buf:bufGetByte(b: text, idx: i, def: 0);
					i: i + 1;
					if({ cb >= 64 && cb <= 126 }, {
						inSeq: false;
					});
				});
			}, else: {
				local Int is seqLen: self:utf8SeqLen(b0: b);
				cols: cols + self:charDisplayWidth(s: text, idx: i, len: len);
				i: i + seqLen;
			});
		});
		return cols;
	}

	Function of String is truncate(String is text, Int is maxCols){
		if({ maxCols <= 0 }, { return ''; });
		local Int is total: self:displayWidth(text: text);
		if({ total <= maxCols }, { return text; });
		local Int is limit: if({ maxCols > 3 }, { maxCols - 3 }, { maxCols });
		local Int is len: Buf:bufLength(b: text);
		local Int is i: 0;
		local Int is cols: 0;
		local Int is cutByte: 0;
		local Boolean is keepGoing: true;
		while({ i < len && keepGoing }, {
			local Int is b: Buf:bufGetByte(b: text, idx: i, def: 0);
			if(check: { b == 27 && (i + 1) < len && Buf:bufGetByte(b: text, idx: i + 1, def: 0) == 91 }, then: {
				i: i + 2;
				local Boolean is inSeq: true;
				while({ i < len && inSeq }, {
					local Int is cb: Buf:bufGetByte(b: text, idx: i, def: 0);
					i: i + 1;
					if({ cb >= 64 && cb <= 126 }, {
						inSeq: false;
					});
				});
				cutByte: i;
			}, else: {
				local Int is seqLen: self:utf8SeqLen(b0: b);
				local Int is w: self:charDisplayWidth(s: text, idx: i, len: len);
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

	Function of String is padRight(String is text, Int is width){
		local String is fitted: self:truncate(text: text, maxCols: width);
		local Int is w: self:displayWidth(text: fitted);
		if({ w >= width }, { return fitted; });
		return fitted . self:repeatStr(s: ' ', count: width - w);
	}
}
