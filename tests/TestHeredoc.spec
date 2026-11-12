#! SpecUnit sweep (from heredoc_test.spec): heredoc and string-template
#! semantics — raw ''' blocks, fancy ``` blocks with template holes,
#! double-quote templates with named-arg calls, brace escapes, and the
#! backward-compatible quote escapes.

Class of SpecUnitTest is TestHeredoc{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	## Case 1: raw heredoc — escapes stay literal, quotes are free.
	Function is testRawHeredocKeepsEscapesLiteral(){
		local String is raw: '''
line \n stays literal
quotes " and ' are free
''';
		Assert:isTrue(raw:contains(needle: "\\n") && raw:contains(needle: '"'));
	}

	## Case 2: raw heredoc spans lines with real newlines (delimiter
	## newline stripped).
	Function is testRawHeredocSpansLines(){
		local String is raw: '''
line \n stays literal
quotes " and ' are free
''';
		Assert:areEqualInt(2, raw:lines():length());
	}

	## Case 3: fancy heredoc — escapes processed, templates expanded.
	Function is testFancyHeredocExpandsHoles(){
		local String is who: 'world';
		local Int is count: 2;
		local String is fancy: ```
hello {{who}}, n={{count}}
```;
		Assert:areEqualString("hello world, n=2\n", fancy);
	}

	## Case 4: double-quote template with a method call and named args.
	Function is testDoubleQuoteTemplateNamedArgs(){
		local String is who: 'world';
		local String is mixed: "chars={{who:length()}} up={{who:replaceAll(search: 'o', replacement: '0')}}";
		Assert:areEqualString("chars=5 up=w0rld", mixed);
	}

	## Case 5: brace escape renders literal braces.
	Function is testBraceEscapeRendersLiteralBraces(){
		local String is braced: "a \{\{ b }} c";
		Assert:areEqualString('a {{ b }} c', braced);
	}

	## Case 6: double-quote escapes unchanged (backward compatibility).
	Function is testDoubleQuoteEscapesUnchanged(){
		local String is esc: "tab:\tend";
		Assert:areEqualInt(8, esc:length());
	}

	## Case 7: single-quote minimal escapes unchanged.
	Function is testSingleQuoteEscapesUnchanged(){
		local String is sq: 'it\'s';
		Assert:areEqualString("it's", sq);
	}
}
