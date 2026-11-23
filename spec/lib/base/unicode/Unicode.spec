#! Package base:unicode
#! Unicode character properties, case conversion, case folding, display width,
#! extended grapheme cluster segmentation (UAX #29), and canonical normalization (UAX #15).

Class is Unicode{
	namespace: ['base', 'unicode'];

	replace Array of Array of String is using: [
		['base', 'sys', as Lazy()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'struct', Map]
	];

	## Lazily initialized map of irregular uppercase -> lowercase code points.
	local Map of Int to Int is irregularLower: lazy({
		local Map of Int to Int is m: Map:init();
		# Latin Extended-A / B & Greek irregular uppercase -> lowercase
		m:set(key: 304, value: 105);   # U+0130 İ -> i
		m:set(key: 376, value: 255);   # U+0178 Ÿ -> ÿ
		m:set(key: 385, value: 595);   # U+0181 Ɓ -> ɓ
		m:set(key: 390, value: 596);   # U+0186 Ɔ -> ɔ
		m:set(key: 393, value: 598);   # U+0189 Ɖ -> ɖ
		m:set(key: 394, value: 599);   # U+018A Ɗ -> ɗ
		m:set(key: 398, value: 477);   # U+018E Ǝ -> ǝ
		m:set(key: 399, value: 601);   # U+018F Ə -> ə
		m:set(key: 400, value: 603);   # U+0190 Ɛ -> ɛ
		m:set(key: 403, value: 608);   # U+0193 Ɠ -> ɠ
		m:set(key: 404, value: 611);   # U+0194 Ɣ -> ɣ
		m:set(key: 406, value: 617);   # U+0196 Ɩ -> ɩ
		m:set(key: 407, value: 616);   # U+0197 Ɨ -> ɨ
		m:set(key: 412, value: 623);   # U+019C Ɯ -> ɯ
		m:set(key: 413, value: 626);   # U+019D Ɲ -> ɲ
		m:set(key: 415, value: 629);   # U+019F Ɵ -> ɵ
		m:set(key: 902, value: 940);   # U+0386 Ά -> ά
		m:set(key: 904, value: 941);   # U+0388 Έ -> έ
		m:set(key: 905, value: 942);   # U+0389 Ή -> ή
		m:set(key: 906, value: 943);   # U+038A Ί -> ί
		m:set(key: 908, value: 972);   # U+038C Ό -> ό
		m:set(key: 910, value: 973);   # U+038E Ύ -> ύ
		m:set(key: 911, value: 974);   # U+038F Ώ -> ώ
		m:set(key: 7838, value: 223);  # U+1E9E ẞ -> ß
		return m;
	});

	## Lazily initialized map of irregular lowercase -> uppercase code points.
	local Map of Int to Int is irregularUpper: lazy({
		local Map of Int to Int is m: Map:init();
		m:set(key: 181, value: 924);   # U+00B5 µ -> Μ
		m:set(key: 255, value: 376);   # U+00FF ÿ -> Ÿ
		m:set(key: 305, value: 73);    # U+0131 ı -> I
		m:set(key: 383, value: 83);    # U+017F ſ -> S
		m:set(key: 595, value: 385);   # U+0253 ɓ -> Ɓ
		m:set(key: 596, value: 390);   # U+0254 ɔ -> Ɔ
		m:set(key: 598, value: 393);   # U+0256 ɖ -> Ɖ
		m:set(key: 599, value: 394);   # U+0257 ɗ -> Ɗ
		m:set(key: 601, value: 399);   # U+0259 ə -> Ə
		m:set(key: 603, value: 400);   # U+025B ɛ -> Ɛ
		m:set(key: 940, value: 902);   # U+03AC ά -> Ά
		m:set(key: 941, value: 904);   # U+03AD έ -> Έ
		m:set(key: 942, value: 905);   # U+03AE ή -> Ή
		m:set(key: 943, value: 906);   # U+03AF ί -> Ί
		m:set(key: 962, value: 931);   # U+03C2 ς -> Σ
		m:set(key: 972, value: 908);   # U+03CC ό -> Ό
		m:set(key: 973, value: 910);   # U+03CD ύ -> Ύ
		m:set(key: 974, value: 911);   # U+03CE ώ -> Ώ
		return m;
	});

	## Lazily initialized canonical decomposition map (precomposed cp -> "base:mark").
	local Map of Int to String is canonicalDecomp: lazy({
		local Map of Int to String is m: Map:init();
		# Latin-1 Supplement uppercase (U+00C0..U+00DD) & lowercase (U+00E0..U+00FF)
		m:set(key: 192, value: '65:768');  # À -> A + `
		m:set(key: 193, value: '65:769');  # Á -> A + ´
		m:set(key: 194, value: '65:770');  # Â -> A + ^
		m:set(key: 195, value: '65:771');  # Ã -> A + ~
		m:set(key: 196, value: '65:776');  # Ä -> A + ¨
		m:set(key: 197, value: '65:778');  # Å -> A + °
		m:set(key: 199, value: '67:807');  # Ç -> C + ¸
		m:set(key: 200, value: '69:768');  # È -> E + `
		m:set(key: 201, value: '69:769');  # É -> E + ´
		m:set(key: 202, value: '69:770');  # Ê -> E + ^
		m:set(key: 203, value: '69:776');  # Ë -> E + ¨
		m:set(key: 204, value: '73:768');  # Ì -> I + `
		m:set(key: 205, value: '73:769');  # Í -> I + ´
		m:set(key: 206, value: '73:770');  # Î -> I + ^
		m:set(key: 207, value: '73:776');  # Ï -> I + ¨
		m:set(key: 209, value: '78:771');  # Ñ -> N + ~
		m:set(key: 210, value: '79:768');  # Ò -> O + `
		m:set(key: 211, value: '79:769');  # Ó -> O + ´
		m:set(key: 212, value: '79:770');  # Ô -> O + ^
		m:set(key: 213, value: '79:771');  # Õ -> O + ~
		m:set(key: 214, value: '79:776');  # Ö -> O + ¨
		m:set(key: 217, value: '85:768');  # Ù -> U + `
		m:set(key: 218, value: '85:769');  # Ú -> U + ´
		m:set(key: 219, value: '85:770');  # Û -> U + ^
		m:set(key: 220, value: '85:776');  # Ü -> U + ¨
		m:set(key: 221, value: '89:769');  # Ý -> Y + ´
		m:set(key: 224, value: '97:768');  # à -> a + `
		m:set(key: 225, value: '97:769');  # á -> a + ´
		m:set(key: 226, value: '97:770');  # â -> a + ^
		m:set(key: 227, value: '97:771');  # ã -> a + ~
		m:set(key: 228, value: '97:776');  # ä -> a + ¨
		m:set(key: 229, value: '97:778');  # å -> a + °
		m:set(key: 231, value: '99:807');  # ç -> c + ¸
		m:set(key: 232, value: '101:768'); # è -> e + `
		m:set(key: 233, value: '101:769'); # é -> e + ´
		m:set(key: 234, value: '101:770'); # ê -> e + ^
		m:set(key: 235, value: '101:776'); # ë -> e + ¨
		m:set(key: 236, value: '105:768'); # ì -> i + `
		m:set(key: 237, value: '105:769'); # í -> i + ´
		m:set(key: 238, value: '105:770'); # î -> i + ^
		m:set(key: 239, value: '105:776'); # ï -> i + ¨
		m:set(key: 241, value: '110:771'); # ñ -> n + ~
		m:set(key: 242, value: '111:768'); # ò -> o + `
		m:set(key: 243, value: '111:769'); # ó -> o + ´
		m:set(key: 244, value: '111:770'); # ô -> o + ^
		m:set(key: 245, value: '111:771'); # õ -> o + ~
		m:set(key: 246, value: '111:776'); # ö -> o + ¨
		m:set(key: 249, value: '117:768'); # ù -> u + `
		m:set(key: 250, value: '117:769'); # ú -> u + ´
		m:set(key: 251, value: '117:770'); # û -> u + ^
		m:set(key: 252, value: '117:776'); # ü -> u + ¨
		m:set(key: 253, value: '121:769'); # ý -> y + ´
		m:set(key: 255, value: '121:776'); # ÿ -> y + ¨
		return m;
	});

	## Lazily initialized canonical composition map ("base:mark" -> precomposed cp).
	local Map of String to Int is canonicalComp: lazy({
		local Map of String to Int is m: Map:init();
		local Array of Int is keys: :canonicalDecomp:keys();
		while([Int is i: 0], { i < keys:length() }, {
			local Int is k: keys:get(index: i, default: 0);
			local String is pair: :canonicalDecomp:get(key: k, default: '');
			if({ pair != '' }, {
				m:set(key: pair, value: k);
			});
			i++;
		});
		return m;
	});

	replace Function is init(){
	}

	## True when [cp] is a Unicode `White_Space` code point.
	Function of Boolean is isWhitespace(Int is cp){
		if({ cp == 32 || (cp >= 9 && cp <= 13) }, { return true; });
		if({ cp == 133 || cp == 160 || cp == 5760 }, { return true; });
		if({ cp >= 8192 && cp <= 8202 }, { return true; });
		if({ cp == 8232 || cp == 8233 || cp == 8239 || cp == 8287 || cp == 12288 }, { return true; });
		return false;
	}

	## True when [cp] is a Unicode decimal digit (`Nd`).
	Function of Boolean is isDigit(Int is cp){
		if({ cp >= 48 && cp <= 57 }, { return true; });
		if({ (cp >= 1632 && cp <= 1641) || (cp >= 1776 && cp <= 1785) || (cp >= 1984 && cp <= 1993) }, { return true; });
		if({ (cp >= 2406 && cp <= 2415) || (cp >= 2534 && cp <= 2543) || (cp >= 2662 && cp <= 2671) }, { return true; });
		if({ (cp >= 2790 && cp <= 2799) || (cp >= 2918 && cp <= 2927) || (cp >= 3046 && cp <= 3055) }, { return true; });
		if({ (cp >= 3174 && cp <= 3183) || (cp >= 3302 && cp <= 3311) || (cp >= 3430 && cp <= 3439) }, { return true; });
		if({ (cp >= 3664 && cp <= 3673) || (cp >= 3792 && cp <= 3801) || (cp >= 3872 && cp <= 3881) }, { return true; });
		if({ (cp >= 4160 && cp <= 4169) || (cp >= 6112 && cp <= 6121) || (cp >= 6160 && cp <= 6169) }, { return true; });
		if({ (cp >= 65296 && cp <= 65305) || (cp >= 120782 && cp <= 120831) }, { return true; });
		return false;
	}

	## True when [cp] is an uppercase letter (`Lu`).
	Function of Boolean is isUpper(Int is cp){
		if({ cp >= 65 && cp <= 90 }, { return true; });
		if({ (cp >= 192 && cp <= 214) || (cp >= 216 && cp <= 222) }, { return true; });
		if({ cp >= 256 && cp <= 310 && (cp & 1) == 0 }, { return true; });
		if({ cp >= 313 && cp <= 327 && (cp & 1) == 1 }, { return true; });
		if({ cp >= 330 && cp <= 374 && (cp & 1) == 0 }, { return true; });
		if({ cp == 376 || (cp >= 377 && cp <= 381 && (cp & 1) == 1) }, { return true; });
		if({ (cp >= 913 && cp <= 937 && cp != 930) || (cp >= 1024 && cp <= 1071) }, { return true; });
		if({ (cp >= 1329 && cp <= 1366) || (cp >= 7312 && cp <= 7354) }, { return true; });
		if({ cp >= 7680 && cp <= 7929 && (cp & 1) == 0 }, { return true; });
		if({ (cp >= 65313 && cp <= 65338) || (cp >= 66560 && cp <= 66599) }, { return true; });
		return :irregularLower:has(key: cp);
	}

	## True when [cp] is a lowercase letter (`Ll`).
	Function of Boolean is isLower(Int is cp){
		if({ cp >= 97 && cp <= 122 }, { return true; });
		if({ cp == 181 || (cp >= 223 && cp <= 246) || (cp >= 248 && cp <= 255) }, { return true; });
		if({ cp >= 257 && cp <= 311 && (cp & 1) == 1 }, { return true; });
		if({ cp == 312 || (cp >= 314 && cp <= 328 && (cp & 1) == 0) }, { return true; });
		if({ cp == 329 || (cp >= 331 && cp <= 375 && (cp & 1) == 1) }, { return true; });
		if({ (cp >= 378 && cp <= 382 && (cp & 1) == 0) || cp == 383 }, { return true; });
		if({ (cp >= 945 && cp <= 969) || (cp >= 1072 && cp <= 1119) }, { return true; });
		if({ (cp >= 1377 && cp <= 1415) || (cp >= 4304 && cp <= 4346) }, { return true; });
		if({ cp >= 7681 && cp <= 7929 && (cp & 1) == 1 }, { return true; });
		if({ (cp >= 65345 && cp <= 65370) || (cp >= 66600 && cp <= 66639) }, { return true; });
		return :irregularUpper:has(key: cp);
	}

	## True when [cp] is a Unicode alphabetic letter (`Lu`, `Ll`, `Lt`, `Lm`, `Lo`).
	Function of Boolean is isLetter(Int is cp){
		if({ :isUpper(cp: cp) || :isLower(cp: cp) }, { return true; });
		if({ cp == 170 || cp == 186 || (cp >= 256 && cp <= 687) }, { return true; });
		if({ (cp >= 880 && cp <= 1023) || (cp >= 1024 && cp <= 1327) }, { return true; });
		if({ (cp >= 1329 && cp <= 1415) || (cp >= 1488 && cp <= 1514) }, { return true; });
		if({ (cp >= 1568 && cp <= 1610) || (cp >= 1646 && cp <= 1747) }, { return true; });
		if({ (cp >= 2308 && cp <= 2361) || (cp >= 3585 && cp <= 3630) }, { return true; });
		if({ (cp >= 4256 && cp <= 4346) || (cp >= 4352 && cp <= 4607) }, { return true; });
		if({ (cp >= 7424 && cp <= 7935) || (cp >= 12353 && cp <= 12438) }, { return true; });
		if({ (cp >= 12449 && cp <= 12538) || (cp >= 12549 && cp <= 12591) }, { return true; });
		if({ (cp >= 12593 && cp <= 12686) || (cp >= 13312 && cp <= 19903) }, { return true; });
		if({ (cp >= 19968 && cp <= 40959) || (cp >= 40960 && cp <= 42124) }, { return true; });
		if({ (cp >= 44032 && cp <= 55203) || (cp >= 131072 && cp <= 196605) }, { return true; });
		return false;
	}

	## True when [cp] is a C0/C1 control character (`Cc`).
	Function of Boolean is isControl(Int is cp){
		return (cp >= 0 && cp <= 31) || (cp >= 127 && cp <= 159);
	}

	## True when [cp] is a zero-width combining mark, variation selector, or
	## emoji modifier (`Mn`, `Me`, `Cf` extenders).
	Function of Boolean is isCombiningMark(Int is cp){
		if({ (cp >= 768 && cp <= 879) || (cp >= 1155 && cp <= 1161) }, { return true; });
		if({ (cp >= 1425 && cp <= 1469) || (cp >= 1552 && cp <= 1562) || (cp >= 1611 && cp <= 1631) }, { return true; });
		if({ (cp >= 6832 && cp <= 6911) || (cp >= 7616 && cp <= 7679) }, { return true; });
		if({ (cp >= 8400 && cp <= 8447) || (cp >= 65024 && cp <= 65039) || (cp >= 65056 && cp <= 65071) }, { return true; });
		if({ (cp >= 127995 && cp <= 127999) || (cp >= 917760 && cp <= 917999) }, { return true; });
		return false;
	}

	## Returns the 2-letter Unicode General Category of [cp].
	Function of String is category(Int is cp){
		if({ cp < 0 || cp > 1114111 }, { return 'Cn'; });
		if({ cp >= 55296 && cp <= 57343 }, { return 'Cs'; });
		if({ :isControl(cp: cp) }, { return 'Cc'; });
		if({ cp == 8232 }, { return 'Zl'; });
		if({ cp == 8233 }, { return 'Zp'; });
		if({ :isWhitespace(cp: cp) }, { return 'Zs'; });
		if({ :isDigit(cp: cp) }, { return 'Nd'; });
		if({ :isUpper(cp: cp) }, { return 'Lu'; });
		if({ :isLower(cp: cp) }, { return 'Ll'; });
		if({ :isCombiningMark(cp: cp) }, { return 'Mn'; });
		if({ :isLetter(cp: cp) }, { return 'Lo'; });
		if({ cp == 8203 || cp == 8204 || cp == 8205 || cp == 65279 }, { return 'Cf'; });
		if({ (cp >= 33 && cp <= 47) || (cp >= 58 && cp <= 64) || (cp >= 91 && cp <= 96) || (cp >= 123 && cp <= 126) }, {
			return 'Po';
		});
		return 'So';
	}

	## Maps a single Unicode code point [cp] to its simple lowercase mapping.
	Function of Int is toLowerCodePoint(Int is cp){
		if({ cp >= 65 && cp <= 90 }, { return cp + 32; });
		if({ :irregularLower:has(key: cp) }, {
			return :irregularLower:get(key: cp, default: cp);
		});
		if({ (cp >= 192 && cp <= 214) || (cp >= 216 && cp <= 222) }, { return cp + 32; });
		if({ cp >= 256 && cp <= 310 && (cp & 1) == 0 }, { return cp + 1; });
		if({ cp >= 313 && cp <= 327 && (cp & 1) == 1 }, { return cp + 1; });
		if({ cp >= 330 && cp <= 374 && (cp & 1) == 0 }, { return cp + 1; });
		if({ cp >= 377 && cp <= 381 && (cp & 1) == 1 }, { return cp + 1; });
		if({ cp >= 913 && cp <= 937 && cp != 930 }, { return cp + 32; });
		if({ cp >= 1024 && cp <= 1039 }, { return cp + 80; });
		if({ cp >= 1040 && cp <= 1071 }, { return cp + 32; });
		if({ cp >= 1120 && cp <= 1214 && (cp & 1) == 0 }, { return cp + 1; });
		if({ cp >= 1329 && cp <= 1366 }, { return cp + 48; });
		if({ cp >= 7312 && cp <= 7354 }, { return cp - 3008; });
		if({ cp >= 7680 && cp <= 7929 && (cp & 1) == 0 }, { return cp + 1; });
		if({ cp >= 65313 && cp <= 65338 }, { return cp + 32; });
		if({ cp >= 66560 && cp <= 66599 }, { return cp + 40; });
		return cp;
	}

	## Maps a single Unicode code point [cp] to its simple uppercase mapping.
	Function of Int is toUpperCodePoint(Int is cp){
		if({ cp >= 97 && cp <= 122 }, { return cp - 32; });
		if({ :irregularUpper:has(key: cp) }, {
			return :irregularUpper:get(key: cp, default: cp);
		});
		if({ (cp >= 224 && cp <= 246) || (cp >= 248 && cp <= 254) }, { return cp - 32; });
		if({ cp >= 257 && cp <= 311 && (cp & 1) == 1 }, { return cp - 1; });
		if({ cp >= 314 && cp <= 328 && (cp & 1) == 0 }, { return cp - 1; });
		if({ cp >= 331 && cp <= 375 && (cp & 1) == 1 }, { return cp - 1; });
		if({ cp >= 378 && cp <= 382 && (cp & 1) == 0 }, { return cp - 1; });
		if({ cp >= 945 && cp <= 969 && cp != 962 }, { return cp - 32; });
		if({ cp >= 1072 && cp <= 1103 }, { return cp - 32; });
		if({ cp >= 1104 && cp <= 1119 }, { return cp - 80; });
		if({ cp >= 1121 && cp <= 1215 && (cp & 1) == 1 }, { return cp - 1; });
		if({ cp >= 1377 && cp <= 1414 }, { return cp - 48; });
		if({ cp >= 4304 && cp <= 4346 }, { return cp + 3008; });
		if({ cp >= 7681 && cp <= 7929 && (cp & 1) == 1 }, { return cp - 1; });
		if({ cp >= 65345 && cp <= 65370 }, { return cp - 32; });
		if({ cp >= 66600 && cp <= 66639 }, { return cp - 40; });
		return cp;
	}

	## Simple case folding for a single code point [cp] (`CaseFolding.txt` C+S).
	Function of Int is foldCodePoint(Int is cp){
		if({ cp == 181 }, { return 956; });  # µ -> μ
		if({ cp == 383 }, { return 115; });  # ſ -> s
		if({ cp == 962 }, { return 963; });  # ς -> σ
		return :toLowerCodePoint(cp: cp);
	}

	## Converts UTF-8 string [s] to lowercase using Unicode case mappings.
	Function of String is toLower(String is s){
		local String is out: '';
		local Int is len: s:byteLength();
		local Int is i: 0;
		while({ i < len }, {
			local Int is cp: s:codePointAt(byteIndex: i, default: 65533);
			local Int is bLen: s:codePointByteLen(byteIndex: i);
			out: out . String:fromCodePoint(code: :toLowerCodePoint(cp: cp));
			i: i + bLen;
		});
		return out;
	}

	## Alias for [toLower].
	Function of String is toLowerUnicode(String is s){
		return :toLower(s: s);
	}

	## Converts UTF-8 string [s] to uppercase using Unicode case mappings.
	Function of String is toUpper(String is s){
		local String is out: '';
		local Int is len: s:byteLength();
		local Int is i: 0;
		while({ i < len }, {
			local Int is cp: s:codePointAt(byteIndex: i, default: 65533);
			local Int is bLen: s:codePointByteLen(byteIndex: i);
			out: out . String:fromCodePoint(code: :toUpperCodePoint(cp: cp));
			i: i + bLen;
		});
		return out;
	}

	## Alias for [toUpper].
	Function of String is toUpperUnicode(String is s){
		return :toUpper(s: s);
	}

	## Full Unicode case folding (`CaseFolding.txt` C+F) for case-insensitive comparison.
	Function of String is caseFold(String is s){
		local String is out: '';
		local Int is len: s:byteLength();
		local Int is i: 0;
		while({ i < len }, {
			local Int is cp: s:codePointAt(byteIndex: i, default: 65533);
			local Int is bLen: s:codePointByteLen(byteIndex: i);
			if({ cp == 223 || cp == 7838 }, {
				# U+00DF ß and U+1E9E ẞ fold to "ss"
				out: out . 'ss';
			}, {
				if({ cp == 64256 }, {
					out: out . 'ff';
				}, {
					if({ cp == 64257 }, {
						out: out . 'fi';
					}, {
						if({ cp == 64258 }, {
							out: out . 'fl';
						}, {
							if({ cp == 64259 }, {
								out: out . 'ffi';
							}, {
								if({ cp == 64260 }, {
									out: out . 'ffl';
								}, {
									out: out . String:fromCodePoint(code: :foldCodePoint(cp: cp));
								});
							});
						});
					});
				});
			});
			i: i + bLen;
		});
		return out;
	}

	## Terminal display width (`wcwidth`) of a single Unicode code point [cp]:
	## 0 for controls, combining marks, zero-width joiners, and variation selectors;
	## 2 for East Asian Wide/Fullwidth and emoji pictographs; 1 otherwise.
	Function of Int is displayWidth(Int is cp){
		if({ cp <= 0 }, { return 0; });
		if({ :isControl(cp: cp) }, { return 0; });
		if({ cp == 173 || cp == 8203 || cp == 8204 || cp == 8205 || cp == 65279 }, { return 0; });
		if({ (cp >= 8206 && cp <= 8207) || (cp >= 8234 && cp <= 8238) || (cp >= 8288 && cp <= 8303) }, { return 0; });
		if({ :isCombiningMark(cp: cp) }, { return 0; });
		if({ cp >= 4448 && cp <= 4607 }, { return 0; }); # Hangul Jungseong/Jongseong conjoining jamo
		# East Asian Wide (W) & Fullwidth (F) + Emoji ranges
		if({ cp >= 4352 && cp <= 4447 }, { return 2; });
		if({ cp == 8986 || cp == 8987 || (cp >= 9193 && cp <= 9203) }, { return 2; });
		if({ (cp >= 11904 && cp <= 12350) || (cp >= 12352 && cp <= 13311) }, { return 2; });
		if({ (cp >= 13312 && cp <= 19903) || (cp >= 19968 && cp <= 42191) }, { return 2; });
		if({ (cp >= 44032 && cp <= 55203) || (cp >= 63744 && cp <= 64255) }, { return 2; });
		if({ (cp >= 65040 && cp <= 65049) || (cp >= 65072 && cp <= 65135) }, { return 2; });
		if({ (cp >= 65281 && cp <= 65376) || (cp >= 65504 && cp <= 65510) }, { return 2; });
		if({ (cp >= 127462 && cp <= 127487) || (cp >= 127744 && cp <= 129535) || (cp >= 129648 && cp <= 129791) }, { return 2; });
		if({ cp >= 131072 && cp <= 262141 }, { return 2; });
		return 1;
	}

	## Terminal display width of UTF-8 string [s], handling combining marks,
	## variation selectors (`U+FE0F` emoji presentation), Regional Indicator
	## flag pairs, and ZWJ (`U+200D`) emoji sequences.
	Function of Int is stringDisplayWidth(String is s){
		local Int is len: s:byteLength();
		local Int is i: 0;
		local Int is cols: 0;
		local Boolean is afterZwj: false;
		local Int is riCount: 0;
		local Int is prevWidth: 0;
		while({ i < len }, {
			local Int is cp: s:codePointAt(byteIndex: i, default: 65533);
			local Int is bLen: s:codePointByteLen(byteIndex: i);
			if({ cp == 8205 }, {
				afterZwj: true;
				riCount: 0;
			}, {
				if({ cp == 65039 }, {
					# U+FE0F VS16 widens a narrow base character into 2-column emoji presentation
					if({ prevWidth == 1 && !afterZwj }, {
						cols: cols + 1;
						prevWidth: 2;
					});
				}, {
					if({ cp >= 127462 && cp <= 127487 }, {
						# Regional Indicator: a pair forms one 2-column flag
						riCount: riCount + 1;
						if({ (riCount & 1) == 1 }, {
							cols: cols + 2;
							prevWidth: 2;
						});
						afterZwj: false;
					}, {
						riCount: 0;
						local Int is w: :displayWidth(cp: cp);
						if({ afterZwj }, {
							if({ w > 0 }, {
								afterZwj: false;
							});
						}, {
							cols: cols + w;
							if({ w > 0 }, {
								prevWidth: w;
							});
						});
					});
				});
			});
			i: i + bLen;
		});
		return cols;
	}

	## True when [cp] is a grapheme-extending code point (UAX #29 `Extend` / `SpacingMark`).
	local Function of Boolean is isGraphemeExtend(Int is cp){
		if({ :isCombiningMark(cp: cp) }, { return true; });
		if({ (cp >= 2305 && cp <= 2307) || (cp >= 2362 && cp <= 2383) }, { return true; });
		if({ (cp >= 2433 && cp <= 2435) || (cp >= 2492 && cp <= 2509) }, { return true; });
		if({ cp == 8204 || (cp >= 127995 && cp <= 127999) }, { return true; });
		return false;
	}

	## Hangul syllable type for UAX #29 (0 = Other, 1 = L, 2 = V, 3 = T, 4 = LV, 5 = LVT).
	local Function of Int is hangulSyllableType(Int is cp){
		if({ (cp >= 4352 && cp <= 4447) || (cp >= 43360 && cp <= 43388) }, { return 1; });
		if({ (cp >= 4448 && cp <= 4519) || (cp >= 55216 && cp <= 55238) }, { return 2; });
		if({ (cp >= 4520 && cp <= 4607) || (cp >= 55243 && cp <= 55291) }, { return 3; });
		if({ cp >= 44032 && cp <= 55203 }, {
			if({ ((cp - 44032) % 28) == 0 }, { return 4; });
			return 5;
		});
		return 0;
	}

	## Segments UTF-8 string [s] into extended grapheme clusters (UAX #29).
	## Preserves `CR+LF`, base + combining marks, Hangul Jamo syllables,
	## Regional Indicator flag pairs, and emoji ZWJ sequences as single clusters.
	Function of Array of String is graphemes(String is s){
		local Array of String is out: Array();
		local Int is len: s:byteLength();
		if({ len <= 0 }, { return out; });

		local Int is clusterStart: 0;
		local Int is prevCp: s:codePointAt(byteIndex: 0, default: -1);
		local Int is i: s:codePointByteLen(byteIndex: 0);
		local Int is riRun: if({ prevCp >= 127462 && prevCp <= 127487 }, { 1 }, { 0 });

		while({ i < len }, {
			local Int is cp: s:codePointAt(byteIndex: i, default: 65533);
			local Int is bLen: s:codePointByteLen(byteIndex: i);
			local Boolean is join: false;

			# GB3: CR x LF
			if({ prevCp == 13 && cp == 10 }, {
				join: true;
			}, {
				local Boolean is prevCtrl: prevCp == 13 || prevCp == 10 || :isControl(cp: prevCp);
				local Boolean is curCtrl: cp == 13 || cp == 10 || :isControl(cp: cp);
				if({ !prevCtrl && !curCtrl }, {
					# GB9: x (Extend | ZWJ)
					if({ :isGraphemeExtend(cp: cp) || cp == 8205 }, {
						join: true;
					});
					# GB11: ZWJ x Extended_Pictographic
					if({ prevCp == 8205 }, {
						join: true;
					});
					# GB12/GB13: RI x RI (pairs only)
					if({ cp >= 127462 && cp <= 127487 && (riRun & 1) == 1 }, {
						join: true;
					});
					# GB6/GB7/GB8: Hangul L/V/T/LV/LVT rules
					local Int is hPrev: :hangulSyllableType(cp: prevCp);
					local Int is hCur: :hangulSyllableType(cp: cp);
					if({ hPrev == 1 && (hCur == 1 || hCur == 2 || hCur == 4 || hCur == 5) }, { join: true; });
					if({ (hPrev == 2 || hPrev == 4) && (hCur == 2 || hCur == 3) }, { join: true; });
					if({ (hPrev == 3 || hPrev == 5) && hCur == 3 }, { join: true; });
				});
			});

			if({ !join }, {
				out:add(item: s:substring(start: clusterStart, end: i));
				clusterStart: i;
				riRun: 0;
			});
			if({ cp >= 127462 && cp <= 127487 }, {
				riRun: riRun + 1;
			}, {
				if({ !:isGraphemeExtend(cp: cp) && cp != 8205 }, {
					riRun: 0;
				});
			});
			prevCp: cp;
			i: i + bLen;
		});
		out:add(item: s:substring(start: clusterStart, end: len));
		return out;
	}

	## Returns the number of extended grapheme clusters in [s] (UAX #29).
	Function of Int is graphemeCount(String is s){
		return :graphemes(s: s):length();
	}

	## Canonical Combining Class (CCC) for common combining marks (0 = starter).
	local Function of Int is combiningClass(Int is cp){
		if({ cp >= 768 && cp <= 789 }, { return 230; }); # Above marks
		if({ cp >= 790 && cp <= 819 }, { return 220; }); # Below marks
		if({ cp == 807 || cp == 808 }, { return 202; }); # Cedilla / Ogonek attached below
		if({ :isCombiningMark(cp: cp) }, { return 230; });
		return 0;
	}

	## Returns the NFD (Canonical Decomposition, UAX #15) form of [s].
	Function of String is normalizeNfd(String is s){
		local Array of Int is cps: Array();
		local Int is len: s:byteLength();
		local Int is i: 0;
		while({ i < len }, {
			local Int is cp: s:codePointAt(byteIndex: i, default: 65533);
			local Int is bLen: s:codePointByteLen(byteIndex: i);
			if({ cp >= 44032 && cp <= 55203 }, {
				# Algorithmic Hangul syllable decomposition (SBase = 0xAC00)
				local Int is sIndex: cp - 44032;
				local Int is lPart: 4352 + (sIndex / 588);
				local Int is vPart: 4449 + ((sIndex % 588) / 28);
				local Int is tPart: 4519 + (sIndex % 28);
				cps:add(item: lPart);
				cps:add(item: vPart);
				if({ tPart != 4519 }, {
					cps:add(item: tPart);
				});
			}, {
				if({ :canonicalDecomp:has(key: cp) }, {
					local String is pair: :canonicalDecomp:get(key: cp, default: '');
					local Array of String is parts: pair:split(delimiter: ':');
					if({ parts:length() == 2 }, {
						cps:add(item: parts:get(index: 0, default: '0'):parseInt(base: 10, default: 0));
						cps:add(item: parts:get(index: 1, default: '0'):parseInt(base: 10, default: 0));
					});
				}, {
					cps:add(item: cp);
				});
			});
			i: i + bLen;
		});

		# Canonical Ordering Algorithm: sort adjacent marks with CCC > 0 by CCC
		local Int is n: cps:length();
		while([Int is k: 1], { k < n }, {
			local Int is curCp: cps:get(index: k, default: 0);
			local Int is curCcc: :combiningClass(cp: curCp);
			if({ curCcc > 0 }, {
				local Int is j: k;
				local Boolean is swapping: true;
				while({ j > 0 && swapping }, {
					local Int is prevCp: cps:get(index: j - 1, default: 0);
					local Int is prevCcc: :combiningClass(cp: prevCp);
					if({ prevCcc > curCcc }, {
						cps:set(index: j, item: prevCp);
						cps:set(index: j - 1, item: curCp);
						j: j - 1;
					}, {
						swapping: false;
					});
				});
			});
			k++;
		});

		local String is out: '';
		while([Int is m: 0], { m < n }, {
			out: out . String:fromCodePoint(code: cps:get(index: m, default: 0));
			m++;
		});
		return out;
	}

	## Returns the NFC (Canonical Decomposition followed by Canonical Composition, UAX #15) form of [s].
	Function of String is normalizeNfc(String is s){
		local String is decomp: :normalizeNfd(s: s);
		local Array of Int is cps: decomp:codePoints();
		local Int is n: cps:length();
		if({ n == 0 }, { return ''; });

		local Array of Int is outCps: Array();
		local Int is i: 0;
		while({ i < n }, {
			local Int is starter: cps:get(index: i, default: 0);
			# Hangul L + V (+ T) composition
			if({ starter >= 4352 && starter <= 4370 && (i + 1) < n }, {
				local Int is nextV: cps:get(index: i + 1, default: 0);
				if({ nextV >= 4449 && nextV <= 4469 }, {
					local Int is lIdx: starter - 4352;
					local Int is vIdx: nextV - 4449;
					local Int is lvCp: 44032 + ((lIdx * 21 + vIdx) * 28);
					i: i + 2;
					if({ i < n }, {
						local Int is nextT: cps:get(index: i, default: 0);
						if({ nextT >= 4520 && nextT <= 4546 }, {
							lvCp: lvCp + (nextT - 4519);
							i: i + 1;
						});
					});
					outCps:add(item: lvCp);
				}, {
					outCps:add(item: starter);
					i: i + 1;
				});
			}, {
				if({ (i + 1) < n }, {
					local Int is mark: cps:get(index: i + 1, default: 0);
					local String is key: (starter as String) . ':' . (mark as String);
					if({ :canonicalComp:has(key: key) }, {
						outCps:add(item: :canonicalComp:get(key: key, default: starter));
						i: i + 2;
					}, {
						outCps:add(item: starter);
						i: i + 1;
					});
				}, {
					outCps:add(item: starter);
					i: i + 1;
				});
			});
		});

		local String is out: '';
		while([Int is m: 0], { m < outCps:length() }, {
			out: out . String:fromCodePoint(code: outCps:get(index: m, default: 0));
			m++;
		});
		return out;
	}
}
