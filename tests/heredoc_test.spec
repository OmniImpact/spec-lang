#! Heredoc and string-template regression: raw ''' blocks, fancy ``` blocks,
#! double-quote templates, brace escapes, and backward-compatible escapes.

Class is HeredocTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Heredoc & Template Test ===');
		local Int is failures: 0;

		# Case 1: raw heredoc — escapes stay literal, quotes are free, multi-line
		local String is raw: '''
line \n stays literal
quotes " and ' are free
''';
		if (raw:contains(needle: "\\n") && raw:contains(needle: '"')) {
			Output:line('[PASS] raw heredoc keeps escapes and quotes literal');
		} else {
			Output:line('[FAIL] raw heredoc processed content');
			failures: failures + 1;
		}

		# Case 2: raw heredoc spans lines with real newlines
		if (raw:lines():length() == 2) {
			Output:line('[PASS] raw heredoc spans lines (delimiter newline stripped)');
		} else {
			Output:line('[FAIL] raw heredoc line count');
			failures: failures + 1;
		}

		# Case 3: fancy heredoc — escapes processed, templates expanded
		local String is who: 'world';
		local Int is count: 2;
		local String is fancy: ```
hello {{who}}, n={{count}}
```;
		if (fancy == "hello world, n=2\n") {
			Output:line('[PASS] fancy heredoc expands holes and escapes');
		} else {
			Output:line('[FAIL] fancy heredoc expansion');
			failures: failures + 1;
		}

		# Case 4: double-quote template with a method call and named args
		local String is mixed: "chars={{who:length()}} up={{who:replaceAll(search: 'o', replacement: '0')}}";
		if (mixed == "chars=5 up=w0rld") {
			Output:line('[PASS] double-quote templates with named-arg calls');
		} else {
			Output:line('[FAIL] double-quote template: ' . mixed);
			failures: failures + 1;
		}

		# Case 5: brace escape renders literal braces
		local String is braced: "a \{\{ b }} c";
		if (braced == 'a {{ b }} c') {
			Output:line('[PASS] brace escape renders literal braces');
		} else {
			Output:line('[FAIL] brace escape: ' . braced);
			failures: failures + 1;
		}

		# Case 6: double-quote escapes unchanged (backward compatibility)
		local String is esc: "tab:\tend";
		if (esc:length() == 8) {
			Output:line('[PASS] double-quote escapes unchanged');
		} else {
			Output:line('[FAIL] double-quote escapes changed');
			failures: failures + 1;
		}

		# Case 7: single-quote minimal escapes unchanged
		local String is sq: 'it\'s';
		if (sq == "it's") {
			Output:line('[PASS] single-quote minimal escapes unchanged');
		} else {
			Output:line('[FAIL] single-quote escapes changed');
			failures: failures + 1;
		}

		if (failures == 0) {
			Output:line('[PASS] heredoc & template test complete');
		} else {
			Output:line('[FAIL] heredoc & template test: ' . (failures as String) . ' failures');
		}
	}
}
