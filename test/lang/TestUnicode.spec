#! specunit: suite
#! Tests for UTF-8 & Unicode support: Buf -> Str -> String hierarchy, UTF-8 safety,
#! lazy sparse checkpoints, \uXXXX / \u{...} escapes, and base:unicode:Unicode.

Class of SpecUnitTest is TestUnicode{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'core', Str],
		['base', 'unicode', as Unicode()],
		['base', 'cleo', as CleoText()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Parallel()],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array]
	];

	## 1. Buf -> Str -> String hierarchy, Str fast path, and UTF-8 safety/recovery.
	Function is testStrHierarchyAndUtf8Safety(){
		local Str is rawAscii: 'Hello, World!';
		Assert:areEqualInt(13, rawAscii:length());
		Assert:areEqualInt(13, rawAscii:byteLength());
		Assert:areEqualInt(72, rawAscii:charCodeAt(index: 0));
		Assert:areEqualString('hello, world!', rawAscii:toLower());
		Assert:areEqualString('HELLO, WORLD!', rawAscii:toUpper());
		Assert:isTrue(rawAscii:isValidUtf8());

		# Seamless assignability between Str and String
		local String is promoted: rawAscii;
		local Str is demoted: promoted;
		Assert:areEqualString('Hello, World!', promoted);
		Assert:areEqualString('Hello, World!', demoted);

		# Construct an ill-formed byte sequence using raw byte codes:
		# 'A' (0x41), orphan continuation (0x80), 'B' (0x42), truncated 2-byte lead (0xC3), 'C' (0x43)
		local Str is badBytes: Str:fromCharCode(code: 65)
			. Str:fromCharCode(code: 128)
			. Str:fromCharCode(code: 66)
			. Str:fromCharCode(code: 195)
			. Str:fromCharCode(code: 67);
		Assert:areEqualInt(5, badBytes:byteLength());
		Assert:isFalse(badBytes:isValidUtf8());

		local String is sanitized: badBytes:sanitizeUtf8();
		Assert:isTrue(sanitized:isValidUtf8());
		Assert:areEqualString("A\uFFFD" . "B\uFFFD" . "C", sanitized);
		Assert:areEqualInt(5, sanitized:runeCount());

		# Boundary-safe byte slicing (sliceUtf8) clamps mid-code-point indices backward
		local Str is utf8Str: "a\u00E9\u65E5\u{1F680}z";
		# Byte layout:
		# 'a'       -> byte 0 (len 1)
		# '\u00E9'  -> bytes 1..2 (len 2)
		# '\u65E5'  -> bytes 3..5 (len 3)
		# '\u{1F680}' -> bytes 6..9 (len 4)
		# 'z'       -> byte 10 (len 1)
		Assert:areEqualInt(11, utf8Str:byteLength());
		Assert:isTrue(utf8Str:isValidUtf8());
		# Slicing from mid-sequence byte 2 to mid-sequence byte 8 clamps to 1..6 ("\u00E9\u65E5")
		local String is clamped: utf8Str:sliceUtf8(start: 2, end: 8);
		Assert:isTrue(clamped:isValidUtf8());
		Assert:areEqualString("\u00E9\u65E5", clamped);
	}

	## 2. String Unicode escapes (\uXXXX and \u{...}) and code-point operations.
	Function is testUnicodeEscapesAndCodePointOps(){
		local String is s: "A\u00E9\u65E5\u{1F680}!";
		Assert:areEqualInt(11, s:byteLength());
		Assert:areEqualInt(5, s:runeCount());

		Assert:areEqualInt(65, s:codePointAtRune(runeIndex: 0));
		Assert:areEqualInt(233, s:codePointAtRune(runeIndex: 1));
		Assert:areEqualInt(26085, s:codePointAtRune(runeIndex: 2));
		Assert:areEqualInt(128640, s:codePointAtRune(runeIndex: 3));
		Assert:areEqualInt(33, s:codePointAtRune(runeIndex: 4));
		Assert:areEqualInt(-1, s:codePointAtRune(runeIndex: 5, default: -1));

		Assert:areEqualString('A', s:runeAt(runeIndex: 0));
		Assert:areEqualString("\u00E9", s:runeAt(runeIndex: 1));
		Assert:areEqualString("\u65E5", s:runeAt(runeIndex: 2));
		Assert:areEqualString("\u{1F680}", s:runeAt(runeIndex: 3));
		Assert:areEqualString('!', s:runeAt(runeIndex: 4));

		Assert:areEqualString("\u00E9\u65E5\u{1F680}", s:sliceRunes(start: 1, end: 4));

		local Array of Int is cps: s:codePoints();
		Assert:areEqualInt(5, cps:length());
		Assert:areEqualInt(65, cps:get(index: 0, default: 0));
		Assert:areEqualInt(233, cps:get(index: 1, default: 0));
		Assert:areEqualInt(26085, cps:get(index: 2, default: 0));
		Assert:areEqualInt(128640, cps:get(index: 3, default: 0));
		Assert:areEqualInt(33, cps:get(index: 4, default: 0));

		# Invalid code points passed to String:fromCodePoint produce U+FFFD (65533)
		local String is rep1: String:fromCodePoint(code: -5);
		local String is rep2: String:fromCodePoint(code: 55296);
		local String is rep3: String:fromCodePoint(code: 1114112);
		Assert:areEqualInt(65533, rep1:codePointAt(byteIndex: 0));
		Assert:areEqualInt(65533, rep2:codePointAt(byteIndex: 0));
		Assert:areEqualInt(65533, rep3:codePointAt(byteIndex: 0));

		# Unicode-aware String:toLower and String:toUpper
		local String is mixed: "Caf\u00C9 \u03A9\u0414";
		Assert:areEqualString("caf\u00E9 \u03C9\u0434", mixed:toLower());
		Assert:areEqualString("CAF\u00C9 \u03A9\u0414", mixed:toLower():toUpper());
	}

	## 3. Lazy sparse checkpoints (K = 32 runes) on long strings (> 64 bytes) and concurrent reads.
	Function is testLazySparseCheckpointsAndConcurrency(){
		# 3a. Long pure-ASCII string (> 64 bytes) uses the -1 ASCII sentinel
		local String is longAscii: '';
		local Int is i: 0;
		while({ i < 100 }, {
			longAscii: longAscii . String:fromCharCode(code: 65 + (i % 26));
			i: i + 1;
		});
		Assert:areEqualInt(100, longAscii:byteLength());
		Assert:areEqualInt(100, longAscii:runeCount());
		Assert:areEqualInt(65 + (64 % 26), longAscii:codePointAtRune(runeIndex: 64));
		Assert:areEqualString('ABC', longAscii:sliceRunes(start: 0, end: 3));

		# 3b. Long multi-byte string (> 64 bytes, 120 runes across 4 checkpoint chunks)
		local String is longUtf8: '';
		i: 0;
		while({ i < 120 }, {
			local Int is kind: i % 4;
			if({ kind == 0 }, {
				longUtf8: longUtf8 . 'a';
			}, {
				if({ kind == 1 }, {
					longUtf8: longUtf8 . "\u00E9";
				}, {
					if({ kind == 2 }, {
						longUtf8: longUtf8 . "\u65E5";
					}, {
						longUtf8: longUtf8 . "\u{1F680}";
					});
				});
			});
			i: i + 1;
		});
		# Each group of 4 runes is 1 + 2 + 3 + 4 = 10 bytes -> 30 groups = 300 bytes, 120 runes
		Assert:areEqualInt(300, longUtf8:byteLength());

		# Concurrent threads racing to build and query checkpoints on the same String
		local Int is sumRunes: 0;
		ThreadScope:open(body: local Function(ThreadScope is scope){
			sumRunes: Parallel:run(
				scope: scope,
				threads: 4,
				iterations: 4,
				worker: local Function of Int(Int is threadIdx, Int is _count){
					local Int is rc: longUtf8:runeCount();
					local Int is cp0: longUtf8:codePointAtRune(runeIndex: 0);
					local Int is cp31: longUtf8:codePointAtRune(runeIndex: 31);
					local Int is cp32: longUtf8:codePointAtRune(runeIndex: 32);
					local Int is cp64: longUtf8:codePointAtRune(runeIndex: 64);
					local Int is cp99: longUtf8:codePointAtRune(runeIndex: 99);
					if({ rc == 120 && cp0 == 97 && cp31 == 128640 && cp32 == 97 && cp64 == 97 && cp99 == 128640 }, {
						return 1;
					});
					return 0;
				}
			);
		});
		Assert:areEqualInt(4, sumRunes);

		# Verify sliceRunes across checkpoint boundaries (runes 30..66)
		local String is sub: longUtf8:sliceRunes(start: 30, end: 35);
		Assert:areEqualInt(5, sub:runeCount());
		Assert:areEqualString("\u65E5\u{1F680}a\u00E9\u65E5", sub);

		# Verify in-place append invalidates cached checkpoints cleanly
		longUtf8: longUtf8 . "\u{1F680}Z";
		Assert:areEqualInt(122, longUtf8:runeCount());
		Assert:areEqualInt(128640, longUtf8:codePointAtRune(runeIndex: 120));
		Assert:areEqualInt(90, longUtf8:codePointAtRune(runeIndex: 121));
	}

	## 4. Negative compiler tests: invalid \uXXXX and \u{...} escapes are rejected at compile time.
	Function is testInvalidUnicodeEscapesRejected(){
		Assert:compilerRejects(
			source: '''
Class is BadUnicodeOutRange{
	replace Function is init(){
		local String is s: "\u{110000}";
	}
}
''',
			expect: 'exceeds maximum U+10FFFF'
		);

		Assert:compilerRejects(
			source: '''
Class is BadUnicodeSurrogate{
	replace Function is init(){
		local String is s: "\uD800";
	}
}
''',
			expect: 'surrogate'
		);

		Assert:compilerRejects(
			source: '''
Class is BadUnicodeMalformed{
	replace Function is init(){
		local String is s: "\u12G4";
	}
}
''',
			expect: 'Invalid Unicode escape'
		);
	}

	## 5. base:unicode:Unicode properties, case folding, display width, graphemes, and normalization.
	Function is testUnicodeStdlibModule(){
		# Properties & categories
		Assert:isTrue(Unicode:isLetter(cp: 65));
		Assert:isTrue(Unicode:isLetter(cp: 233));
		Assert:isTrue(Unicode:isLetter(cp: 937));
		Assert:isTrue(Unicode:isLetter(cp: 26085));
		Assert:isFalse(Unicode:isLetter(cp: 48));

		Assert:isTrue(Unicode:isWhitespace(cp: 32));
		Assert:isTrue(Unicode:isWhitespace(cp: 160));
		Assert:isTrue(Unicode:isWhitespace(cp: 12288));
		Assert:isFalse(Unicode:isWhitespace(cp: 65));

		Assert:isTrue(Unicode:isDigit(cp: 57));
		Assert:isTrue(Unicode:isDigit(cp: 1634));
		Assert:isFalse(Unicode:isDigit(cp: 65));

		Assert:isTrue(Unicode:isCombiningMark(cp: 769));
		Assert:areEqualString('Lu', Unicode:category(cp: 65));
		Assert:areEqualString('Ll', Unicode:category(cp: 233));
		Assert:areEqualString('Mn', Unicode:category(cp: 769));
		Assert:areEqualString('Nd', Unicode:category(cp: 48));
		Assert:areEqualString('Lo', Unicode:category(cp: 26085));
		Assert:areEqualString('So', Unicode:category(cp: 128640));

		# Case mapping and full case folding (including German sharp s 'ß' -> 'ss')
		Assert:areEqualString("stra\u00DFe", Unicode:toLower(s: "STRA\u1E9EE"));
		Assert:areEqualString("strasse", Unicode:caseFold(s: "Stra\u00DFe"));
		Assert:areEqualString("strasse", Unicode:caseFold(s: "STRASSE"));

		# Display width (Unicode and CleoText)
		# "e\u0301" (e + combining acute) -> width 1
		# "\u65E5\u672C" (2 CJK chars) -> width 4
		# "\u{1F680}" (emoji) -> width 2
		Assert:areEqualInt(1, Unicode:stringDisplayWidth(s: "e\u0301"));
		Assert:areEqualInt(4, Unicode:stringDisplayWidth(s: "\u65E5\u672C"));
		Assert:areEqualInt(2, Unicode:stringDisplayWidth(s: "\u{1F680}"));
		Assert:areEqualInt(1, CleoText:displayWidth(text: "e\u0301"));
		Assert:areEqualInt(4, CleoText:displayWidth(text: "\u65E5\u672C"));
		Assert:areEqualInt(2, CleoText:displayWidth(text: "\u{1F680}"));

		# Grapheme cluster segmentation (UAX #29)
		# "a" + "e\u0301" + "\r\n" + "\u{1F1FA}\u{1F1F8}" (US flag) + "\u{1F468}\u200D\u{1F4BB}" (ZWJ technologist)
		local String is gText: "ae\u0301\r\n\u{1F1FA}\u{1F1F8}\u{1F468}\u200D\u{1F4BB}";
		local Array of String is clusters: Unicode:graphemes(s: gText);
		Assert:areEqualInt(5, clusters:length());
		Assert:areEqualInt(5, Unicode:graphemeCount(s: gText));
		Assert:areEqualString("a", clusters:get(index: 0, default: ''));
		Assert:areEqualString("e\u0301", clusters:get(index: 1, default: ''));
		Assert:areEqualString("\r\n", clusters:get(index: 2, default: ''));
		Assert:areEqualString("\u{1F1FA}\u{1F1F8}", clusters:get(index: 3, default: ''));
		Assert:areEqualString("\u{1F468}\u200D\u{1F4BB}", clusters:get(index: 4, default: ''));

		# Normalization (NFC / NFD)
		local String is precomposed: "\u00E9";
		local String is decomposed: "e\u0301";
		Assert:areEqualInt(1, precomposed:runeCount());
		Assert:areEqualInt(2, decomposed:runeCount());
		Assert:areEqualString(decomposed, Unicode:normalizeNfd(s: precomposed));
		Assert:areEqualString(precomposed, Unicode:normalizeNfc(s: decomposed));

		# Hangul algorithmic NFD / NFC: U+AC00 ('가') <-> U+1100 + U+1161
		local String is hangulSyllable: "\uAC00";
		local String is hangulJamo: "\u1100\u1161";
		Assert:areEqualString(hangulJamo, Unicode:normalizeNfd(s: hangulSyllable));
		Assert:areEqualString(hangulSyllable, Unicode:normalizeNfc(s: hangulJamo));
	}
}
