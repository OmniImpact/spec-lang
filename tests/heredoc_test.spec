#! Heredoc and string-template regression: raw ''' blocks, fancy ``` blocks,
#! double-quote templates, brace escapes, and backward-compatible escapes.

Class is HeredocTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Heredoc & Template Test ===');
		local Int is failures: 0;

		# Case 1: raw heredoc — escapes stay literal, quotes are free, multi-line
		local String is raw: '''
line \n stays literal
quotes " and ' are free
''';
		Conditional:branch(check: { raw:contains(needle: "\\n") && raw:contains(needle: '"') }, then: {
			Output:line('[PASS] raw heredoc keeps escapes and quotes literal');
		}, otherwise: {
			Output:line('[FAIL] raw heredoc processed content');
			failures: failures + 1;
		});

		# Case 2: raw heredoc spans lines with real newlines
		Conditional:branch(check: { raw:lines():length() == 2 }, then: {
			Output:line('[PASS] raw heredoc spans lines (delimiter newline stripped)');
		}, otherwise: {
			Output:line('[FAIL] raw heredoc line count');
			failures: failures + 1;
		});

		# Case 3: fancy heredoc — escapes processed, templates expanded
		local String is who: 'world';
		local Int is count: 2;
		local String is fancy: ```
hello {{who}}, n={{count}}
```;
		Conditional:branch(check: { fancy == "hello world, n=2\n" }, then: {
			Output:line('[PASS] fancy heredoc expands holes and escapes');
		}, otherwise: {
			Output:line('[FAIL] fancy heredoc expansion');
			failures: failures + 1;
		});

		# Case 4: double-quote template with a method call and named args
		local String is mixed: "chars={{who:length()}} up={{who:replaceAll(search: 'o', replacement: '0')}}";
		Conditional:branch(check: { mixed == "chars=5 up=w0rld" }, then: {
			Output:line('[PASS] double-quote templates with named-arg calls');
		}, otherwise: {
			Output:line('[FAIL] double-quote template: ' . mixed);
			failures: failures + 1;
		});

		# Case 5: brace escape renders literal braces
		local String is braced: "a \{\{ b }} c";
		Conditional:branch(check: { braced == 'a {{ b }} c' }, then: {
			Output:line('[PASS] brace escape renders literal braces');
		}, otherwise: {
			Output:line('[FAIL] brace escape: ' . braced);
			failures: failures + 1;
		});

		# Case 6: double-quote escapes unchanged (backward compatibility)
		local String is esc: "tab:\tend";
		Conditional:branch(check: { esc:length() == 8 }, then: {
			Output:line('[PASS] double-quote escapes unchanged');
		}, otherwise: {
			Output:line('[FAIL] double-quote escapes changed');
			failures: failures + 1;
		});

		# Case 7: single-quote minimal escapes unchanged
		local String is sq: 'it\'s';
		Conditional:branch(check: { sq == "it's" }, then: {
			Output:line('[PASS] single-quote minimal escapes unchanged');
		}, otherwise: {
			Output:line('[FAIL] single-quote escapes changed');
			failures: failures + 1;
		});

		Conditional:branch(check: { failures == 0 }, then: {
			Output:line('[PASS] heredoc & template test complete');
		}, otherwise: {
			Output:line('[FAIL] heredoc & template test: ' . (failures as String) . ' failures');
		});
	}
}
