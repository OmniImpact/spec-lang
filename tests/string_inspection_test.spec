Class is StringInspectionTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'struct', Array],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== String Inspection & Predicates Test ===');

		# Case 1: isDigit
		local Boolean is d1: '12345':isDigit();
		local Boolean is d2: '0':isDigit();
		local Boolean is d3: '9':isDigit();
		local Boolean is dEmpty: '':isDigit();
		local Boolean is dAlpha: '12a3':isDigit();
		local Boolean is dSpace: ' 123':isDigit();
		local Boolean is dNeg: '-5':isDigit();
		if (d1 && d2 && d3 && !dEmpty && !dAlpha && !dSpace && !dNeg) {
			Output:line('[PASS] String:isDigit accepts digits and rejects non-digits');
		} else {
			Output:line('[FAIL] String:isDigit');
		}

		# Case 2: isAlpha
		local Boolean is a1: 'abc':isAlpha();
		local Boolean is a2: 'XYZ':isAlpha();
		local Boolean is a3: 'HelloWorld':isAlpha();
		local Boolean is aEmpty: '':isAlpha();
		local Boolean is aDigit: 'abc1':isAlpha();
		local Boolean is aSpace: 'hello world':isAlpha();
		local Boolean is aUnderscore: 'foo_bar':isAlpha();
		if (a1 && a2 && a3 && !aEmpty && !aDigit && !aSpace && !aUnderscore) {
			Output:line('[PASS] String:isAlpha accepts letters and rejects non-letters');
		} else {
			Output:line('[FAIL] String:isAlpha');
		}

		# Case 3: isWhitespace
		local Boolean is wSpace: ' ':isWhitespace();
		local Boolean is wTab: "\t":isWhitespace();
		local Boolean is wNewline: "\n":isWhitespace();
		local Boolean is wCR: "\r":isWhitespace();
		local Boolean is wMixed: " \t\n\r ":isWhitespace();
		local Boolean is wEmpty: '':isWhitespace();
		local Boolean is wWord: ' a ':isWhitespace();
		if (wSpace && wTab && wNewline && wCR && wMixed && !wEmpty && !wWord) {
			Output:line('[PASS] String:isWhitespace accepts whitespace and rejects non-whitespace');
		} else {
			Output:line('[FAIL] String:isWhitespace');
		}

		# Case 4: countLeading
		local Int is spCount: '    four spaces':countLeading(search: ' ');
		local Int is tabCount: "\t\t\ttabs":countLeading(search: "\t");
		local Int is noCount: 'no leading':countLeading(search: ' ');
		local Int is repCount: 'abababrest':countLeading(search: 'ab');
		if (spCount == 4 && tabCount == 3 && noCount == 0 && repCount == 3) {
			Output:line('[PASS] String:countLeading counts leading repetitions correctly');
		} else {
			Output:line('[FAIL] String:countLeading');
		}

		# Case 5: trim
		local String is t1: '   hello world   ':trim();
		local String is t2: "\t\r\nclean\n\r\t":trim();
		local String is t3: '   ':trim();
		local String is t4: '':trim();
		local String is t5: 'already clean':trim();
		if (t1 == 'hello world' && t2 == 'clean' && t3 == '' && t4 == '' && t5 == 'already clean') {
			Output:line('[PASS] String:trim strips leading and trailing whitespace');
		} else {
			Output:line('[FAIL] String:trim');
		}

		# Case 6: startsWith, endsWith, contains
		local String is text: 'The quick brown fox';
		local Boolean is swTrue: text:startsWith(prefix: 'The');
		local Boolean is swFalse: text:startsWith(prefix: 'fox');
		local Boolean is swEmpty: text:startsWith(prefix: '');
		local Boolean is ewTrue: text:endsWith(suffix: 'fox');
		local Boolean is ewFalse: text:endsWith(suffix: 'The');
		local Boolean is ewEmpty: text:endsWith(suffix: '');
		local Boolean is cTrue: text:contains(needle: 'quick');
		local Boolean is cFalse: text:contains(needle: 'lazy');
		if (swTrue && !swFalse && swEmpty && ewTrue && !ewFalse && ewEmpty && cTrue && !cFalse) {
			Output:line('[PASS] String predicates: startsWith, endsWith, contains');
		} else {
			Output:line('[FAIL] String predicates: startsWith, endsWith, contains');
		}

		# Case 7: split
		local Array of String is parts: 'apple,banana,cherry':split(delimiter: ',');
		local Array of String is emptyDelim: 'abc':split(delimiter: '');
		local Boolean is pOk: parts:length() == 3 && parts:get(index: 0, default: '') == 'apple' && parts:get(index: 1, default: '') == 'banana' && parts:get(index: 2, default: '') == 'cherry';
		local Boolean is eOk: emptyDelim:length() == 3 && emptyDelim:get(index: 0, default: '') == 'a' && emptyDelim:get(index: 1, default: '') == 'b' && emptyDelim:get(index: 2, default: '') == 'c';
		if (pOk && eOk) {
			Output:line('[PASS] String:split splits with and without delimiter');
		} else {
			Output:line('[FAIL] String:split');
		}

		# Case 8: lines
		local Array of String is linesList: "line1\nline2\r\nline3\n":lines();
		local Boolean is lOk: linesList:length() == 3 && linesList:get(index: 0, default: '') == 'line1' && linesList:get(index: 1, default: '') == 'line2' && linesList:get(index: 2, default: '') == 'line3';
		if (lOk) {
			Output:line('[PASS] String:lines handles unix and crlf newlines');
		} else {
			Output:line('[FAIL] String:lines');
		}

		# Case 9: parseInt
		local Int is p10: '12345':parseInt(base: 10, default: -1);
		local Int is pNeg: '-999':parseInt(base: 10, default: -1);
		local Int is pHex: '0x1A':parseInt(base: 16, default: -1);
		local Int is pBin: '0b1011':parseInt(base: 2, default: -1);
		local Int is pOct: '0o77':parseInt(base: 8, default: -1);
		local Int is pSep: '1_000_000':parseInt(base: 10, default: -1);
		local Int is pDef: 'not_a_number':parseInt(base: 10, default: 42);
		if (p10 == 12345 && pNeg == -999 && pHex == 26 && pBin == 11 && pOct == 63 && pSep == 1000000 && pDef == 42) {
			Output:line('[PASS] String:parseInt parses bases, prefixes, separators, and defaults');
		} else {
			Output:line('[FAIL] String:parseInt');
		}

		# Case 10: charAt
		local String is c0: 'hello':charAt(index: 0, default: '?');
		local String is c4: 'hello':charAt(index: 4, default: '?');
		local String is cOut: 'hello':charAt(index: 10, default: '?');
		local String is cNeg: 'hello':charAt(index: -1, default: '?');
		if (c0 == 'h' && c4 == 'o' && cOut == '?' && cNeg == '?') {
			Output:line('[PASS] String:charAt extracts characters and handles bounds');
		} else {
			Output:line('[FAIL] String:charAt');
		}

		# Case 11: replaceAll
		local String is rep1: 'foo bar foo':replaceAll(search: 'foo', replacement: 'baz');
		local String is repEmpty: 'abc':replaceAll(search: '', replacement: 'x');
		local String is repNone: 'hello':replaceAll(search: 'xyz', replacement: 'abc');
		if (rep1 == 'baz bar baz' && repEmpty == 'abc' && repNone == 'hello') {
			Output:line('[PASS] String:replaceAll replaces occurrences');
		} else {
			Output:line('[FAIL] String:replaceAll');
		}
	}

}
