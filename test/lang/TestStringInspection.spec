#! SpecUnit sweep (from string_inspection_test.spec): String
#! inspection and predicates — isDigit/isAlpha/isWhitespace,
#! countLeading, trim, startsWith/endsWith/contains, split, lines,
#! parseInt, charAt, and replaceAll.

Class of SpecUnitTest is TestStringInspection{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array]
	];

	## Case 1: isDigit accepts digits and rejects non-digits.
	Function is testIsDigit(){
		Assert:isTrue('12345':isDigit());
		Assert:isTrue('0':isDigit());
		Assert:isTrue('9':isDigit());
		Assert:isFalse('':isDigit());
		Assert:isFalse('12a3':isDigit());
		Assert:isFalse(' 123':isDigit());
		Assert:isFalse('-5':isDigit());
	}

	## Case 2: isAlpha accepts letters and rejects non-letters.
	Function is testIsAlpha(){
		Assert:isTrue('abc':isAlpha());
		Assert:isTrue('XYZ':isAlpha());
		Assert:isTrue('HelloWorld':isAlpha());
		Assert:isFalse('':isAlpha());
		Assert:isFalse('abc1':isAlpha());
		Assert:isFalse('hello world':isAlpha());
		Assert:isFalse('foo_bar':isAlpha());
	}

	## Case 3: isWhitespace accepts whitespace and rejects non-whitespace.
	Function is testIsWhitespace(){
		Assert:isTrue(' ':isWhitespace());
		Assert:isTrue("\t":isWhitespace());
		Assert:isTrue("\n":isWhitespace());
		Assert:isTrue("\r":isWhitespace());
		Assert:isTrue(" \t\n\r ":isWhitespace());
		Assert:isFalse('':isWhitespace());
		Assert:isFalse(' a ':isWhitespace());
	}

	## Case 4: countLeading counts leading repetitions correctly.
	Function is testCountLeading(){
		Assert:areEqualInt(4, '    four spaces':countLeading(search: ' '));
		Assert:areEqualInt(3, "\t\t\ttabs":countLeading(search: "\t"));
		Assert:areEqualInt(0, 'no leading':countLeading(search: ' '));
		Assert:areEqualInt(3, 'abababrest':countLeading(search: 'ab'));
	}

	## Case 5: trim strips leading and trailing whitespace.
	Function is testTrim(){
		Assert:areEqualString('hello world', '   hello world   ':trim());
		Assert:areEqualString('clean', "\t\r\nclean\n\r\t":trim());
		Assert:areEqualString('', '   ':trim());
		Assert:areEqualString('', '':trim());
		Assert:areEqualString('already clean', 'already clean':trim());
	}

	## Case 6: startsWith, endsWith, contains.
	Function is testStartsEndsContains(){
		local String is text: 'The quick brown fox';
		Assert:isTrue(text:startsWith(prefix: 'The'));
		Assert:isFalse(text:startsWith(prefix: 'fox'));
		Assert:isTrue(text:startsWith(prefix: ''));
		Assert:isTrue(text:endsWith(suffix: 'fox'));
		Assert:isFalse(text:endsWith(suffix: 'The'));
		Assert:isTrue(text:endsWith(suffix: ''));
		Assert:isTrue(text:contains(needle: 'quick'));
		Assert:isFalse(text:contains(needle: 'lazy'));
	}

	## Case 7: split splits with and without delimiter.
	Function is testSplit(){
		local Array of String is parts: 'apple,banana,cherry':split(delimiter: ',');
		local Array of String is emptyDelim: 'abc':split(delimiter: '');
		Assert:areEqualInt(3, parts:length());
		Assert:areEqualString('apple', parts:get(index: 0, default: ''));
		Assert:areEqualString('banana', parts:get(index: 1, default: ''));
		Assert:areEqualString('cherry', parts:get(index: 2, default: ''));
		Assert:areEqualInt(3, emptyDelim:length());
		Assert:areEqualString('a', emptyDelim:get(index: 0, default: ''));
		Assert:areEqualString('b', emptyDelim:get(index: 1, default: ''));
		Assert:areEqualString('c', emptyDelim:get(index: 2, default: ''));
	}

	## Case 8: lines handles unix and crlf newlines.
	Function is testLines(){
		local Array of String is linesList: "line1\nline2\r\nline3\n":lines();
		Assert:areEqualInt(3, linesList:length());
		Assert:areEqualString('line1', linesList:get(index: 0, default: ''));
		Assert:areEqualString('line2', linesList:get(index: 1, default: ''));
		Assert:areEqualString('line3', linesList:get(index: 2, default: ''));
	}

	## Case 9: parseInt parses bases, prefixes, separators, and defaults.
	Function is testParseInt(){
		Assert:areEqualInt(12345, '12345':parseInt(base: 10, default: -1));
		Assert:areEqualInt(-999, '-999':parseInt(base: 10, default: -1));
		Assert:areEqualInt(26, '0x1A':parseInt(base: 16, default: -1));
		Assert:areEqualInt(11, '0b1011':parseInt(base: 2, default: -1));
		Assert:areEqualInt(63, '0o77':parseInt(base: 8, default: -1));
		Assert:areEqualInt(1000000, '1_000_000':parseInt(base: 10, default: -1));
		Assert:areEqualInt(42, 'not_a_number':parseInt(base: 10, default: 42));
	}

	## Case 10: charAt extracts characters and handles bounds.
	Function is testCharAt(){
		Assert:areEqualString('h', 'hello':charAt(index: 0, default: '?'));
		Assert:areEqualString('o', 'hello':charAt(index: 4, default: '?'));
		Assert:areEqualString('?', 'hello':charAt(index: 10, default: '?'));
		Assert:areEqualString('?', 'hello':charAt(index: -1, default: '?'));
	}

	## Case 11: replaceAll replaces occurrences.
	Function is testReplaceAll(){
		Assert:areEqualString('baz bar baz', 'foo bar foo':replaceAll(search: 'foo', replacement: 'baz'));
		Assert:areEqualString('abc', 'abc':replaceAll(search: '', replacement: 'x'));
		Assert:areEqualString('hello', 'hello':replaceAll(search: 'xyz', replacement: 'abc'));
	}
}
