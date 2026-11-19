#! SpecUnit tests for `base:regex:Arex` (`r*`), `Str`, and `String` (`s*`) parity APIs.

Class of SpecUnitTest is TestArex{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'core', Str],
		['base', 'regex', as Arex() is ar],
		['base', 'regex', ArexPattern],
		['base', 'struct', Array],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Channel],
		['base', 'sys', as Process()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Int is expectSync(Str is input, Str is pattern, Boolean is want){
		local Int is slot: 600;
		Process:atomicPut(slot: slot, value: -1);
		ar:rContains(
			input: input,
			pattern: pattern,
			result: local Function(Boolean is matched){
				local Int is resInt: 0;
				if({ matched }, { resInt: 1; });
				Process:atomicPut(slot: slot, value: resInt);
			}
		);
		local Int is got: Process:atomicGet(slot: slot);
		local Int is wantInt: 0;
		if({ want }, { wantInt: 1; });
		Assert:areEqualInt(wantInt, got);
		return got;
	}

	## Outside ThreadScope:open, ar:rContains waits for completion before returning.
	Function is testSyncOutsideScope(){
		Assert:isFalse(ThreadScope:inScope());

		:expectSync(input: 'hello world', pattern: 'world', want: true);
		:expectSync(input: 'hello world', pattern: 'xyz', want: false);
		:expectSync(input: 'abc', pattern: 'a.c', want: true);
		:expectSync(input: 'ac', pattern: 'a.c', want: false);
		:expectSync(input: 'ac', pattern: 'ab*c', want: true);
		:expectSync(input: 'abbbc', pattern: 'ab*c', want: true);
		:expectSync(input: 'axc', pattern: 'ab*c', want: false);
		:expectSync(input: 'abc', pattern: '^abc$', want: true);
		:expectSync(input: 'xabc', pattern: '^abc$', want: false);
		:expectSync(input: 'abcx', pattern: '^abc$', want: false);
		:expectSync(input: 'a.c', pattern: 'a\\.c', want: true);
		:expectSync(input: 'axc', pattern: 'a\\.c', want: false);
		:expectSync(input: '', pattern: '^$', want: true);
		:expectSync(input: 'a', pattern: '^$', want: false);
		:expectSync(input: 'aaaaaaaaaaaaaaaaaaaaab', pattern: 'a*a*a*a*a*a*c', want: false);
	}

	## Inside ThreadScope:open, ar:rContains runs asynchronously on the scope and is joined on exit.
	Function is testAsyncInsideScope(){
		local Arex is rx: Arex();
		Process:atomicPut(slot: 601, value: -1);
		Process:atomicPut(slot: 602, value: -1);
		Process:atomicPut(slot: 603, value: -1);

		ThreadScope:open(body: local Function(ThreadScope is scope){
			Assert:isTrue(ThreadScope:inScope());
			rx:rContains(
				input: 'async spec regex',
				pattern: '^async .* regex$',
				result: local Function(Boolean is matched){
					local Int is v: 0;
					if({ matched }, { v: 1; });
					Process:atomicPut(slot: 601, value: v);
				}
			);
			rx:rContains(
				input: 'no match here',
				pattern: '^async',
				result: local Function(Boolean is matched){
					local Int is v: 0;
					if({ matched }, { v: 1; });
					Process:atomicPut(slot: 602, value: v);
				}
			);
			rx:rContains(
				input: 'abbbbbc',
				pattern: 'ab*c',
				result: local Function(Boolean is matched){
					local Int is v: 0;
					if({ ThreadScope:inScope() }, { v: v + 10; });
					if({ matched }, { v: v + 1; });
					Process:atomicPut(slot: 603, value: v);
				}
			);
		});

		Assert:areEqualInt(1, Process:atomicGet(slot: 601));
		Assert:areEqualInt(0, Process:atomicGet(slot: 602));
		Assert:areEqualInt(11, Process:atomicGet(slot: 603));
	}

	## Quantifiers (+, ?, {m,n}), groups, alternation, character classes, and shorthands.
	Function is testExtendedSyntax(){
		:expectSync(input: 'ac', pattern: 'ab+c', want: false);
		:expectSync(input: 'abc', pattern: 'ab+c', want: true);
		:expectSync(input: 'abbbc', pattern: 'ab+c', want: true);

		:expectSync(input: 'color', pattern: 'colou?r', want: true);
		:expectSync(input: 'colour', pattern: 'colou?r', want: true);
		:expectSync(input: 'colouur', pattern: 'colou?r', want: false);

		:expectSync(input: 'ab', pattern: '^a{2,3}b$', want: false);
		:expectSync(input: 'aab', pattern: '^a{2,3}b$', want: true);
		:expectSync(input: 'aaab', pattern: '^a{2,3}b$', want: true);
		:expectSync(input: 'aaaab', pattern: '^a{2,3}b$', want: false);
		:expectSync(input: 'abab', pattern: '^(ab){2}$', want: true);

		:expectSync(input: 'catdogcat', pattern: '^(cat|dog)+$', want: true);
		:expectSync(input: 'catbird', pattern: '^(cat|dog)+$', want: false);

		:expectSync(input: 'v2026', pattern: '^v\\d+$', want: true);
		:expectSync(input: 'v20x6', pattern: '^v\\d+$', want: false);
		:expectSync(input: 'hello_99', pattern: '^\\w+$', want: true);
		:expectSync(input: 'hello 99', pattern: '^\\w+\\s+\\d+$', want: true);
		:expectSync(input: 'b7', pattern: '^[a-f][0-9]$', want: true);
		:expectSync(input: 'g7', pattern: '^[a-f][0-9]$', want: false);
		:expectSync(input: 'x', pattern: '^[^0-9]$', want: true);
		:expectSync(input: '5', pattern: '^[^0-9]$', want: false);
	}

	## rFind returns leftmost-longest match text and byte span via callback.
	Function is testFind(){
		local Channel of Str is ch: Channel();
		ar:rFind(
			input: 'order #1234 and #5678',
			pattern: '#\\d+',
			result: local Function(Boolean is found, Str is match, Int is start, Int is end){
				if({ found && start == 6 && end == 11 }, {
					ch:send(item: match);
				}, {
					ch:send(item: 'ERR');
				});
				return;
			}
		);
		Assert:areEqualString('#1234', ch:receive(default: ''));

		local Channel of Str is chMiss: Channel();
		ThreadScope:open(body: local Function(ThreadScope is scope){
			ar:rFind(
				input: 'no numbers here',
				pattern: '\\d+',
				result: local Function(Boolean is found, Str is match, Int is start, Int is end){
					if({ !found && start == -1 && end == -1 && match == '' }, {
						chMiss:send(item: 'MISS');
					}, {
						chMiss:send(item: 'ERR');
					});
					return;
				}
			);
		});
		Assert:areEqualString('MISS', chMiss:receive(default: ''));
	}

	## Compiled ArexPattern via callback-based rCompile works with overloaded rContains and rFind.
	Function is testCompiledPatternReuse(){
		local Arex is rx: Arex();
		local Channel of ArexPattern is patCh: Channel();

		rx:rCompile(
			pattern: '[a-z]+-\\d+',
			result: local Function(ArexPattern is compiled){
				patCh:send(item: compiled);
				return;
			}
		);
		local ArexPattern is pat: patCh:receive(default: ArexPattern());
		Assert:areEqualString('[a-z]+-\\d+', pat:pattern());

		Process:atomicPut(slot: 604, value: -1);
		rx:rContains(
			input: 'item-42',
			pattern: pat,
			result: local Function(Boolean is matched){
				local Int is v: 0;
				if({ matched }, { v: 1; });
				Process:atomicPut(slot: 604, value: v);
			}
		);
		Assert:areEqualInt(1, Process:atomicGet(slot: 604));

		local Channel of Str is chA: Channel();
		local Channel of Str is chB: Channel();
		ThreadScope:open(body: local Function(ThreadScope is scope){
			ar:rFind(
				input: 'first alpha-100 end',
				pattern: pat,
				result: local Function(Boolean is found, Str is match, Int is start, Int is end){
					if({ found }, { chA:send(item: match); }, { chA:send(item: 'ERR'); });
					return;
				}
			);
			ar:rFind(
				input: 'second beta-2026 end',
				pattern: pat,
				result: local Function(Boolean is found, Str is match, Int is start, Int is end){
					if({ found }, { chB:send(item: match); }, { chB:send(item: 'ERR'); });
					return;
				}
			);
			ar:rCompile(
				pattern: '^v\\d+$',
				result: local Function(ArexPattern is verPat){
					ar:rContains(
						input: 'v12',
						pattern: verPat,
						result: local Function(Boolean is matched){
							local Int is v: 0;
							if({ matched }, { v: 1; });
							Process:atomicPut(slot: 605, value: v);
						}
					);
				}
			);
		});
		Assert:areEqualString('alpha-100', chA:receive(default: ''));
		Assert:areEqualString('beta-2026', chB:receive(default: ''));
		Assert:areEqualInt(1, Process:atomicGet(slot: 605));
	}

	## Leading colon `:ar` disambiguates the class-level `as Arex() is ar` import from a local `ar`.
	Function is testAliasedImportDisambiguation(){
		local Int is ar: 7;
		Assert:areEqualInt(7, ar);

		Process:atomicPut(slot: 606, value: -1);
		:ar:rContains(
			input: 'spec-2026',
			pattern: '^spec-\\d+$',
			result: local Function(Boolean is matched){
				local Int is v: 0;
				if({ matched }, { v: 1; });
				Process:atomicPut(slot: 606, value: v);
			}
		);
		Assert:areEqualInt(1, Process:atomicGet(slot: 606));
	}

	## rEquals, rStartsWith, and rEndsWith match anchored regions safely even with alternation.
	Function is testEqualsStartsEnds(){
		Process:atomicPut(slot: 607, value: -1);
		ar:rEquals(
			input: 'ax',
			pattern: 'a|b',
			result: local Function(Boolean is matched){
				local Int is v: 0;
				if({ matched }, { v: 1; });
				Process:atomicPut(slot: 607, value: v);
			}
		);
		Assert:areEqualInt(0, Process:atomicGet(slot: 607));

		Process:atomicPut(slot: 608, value: -1);
		ar:rEquals(
			input: 'b',
			pattern: 'a|b',
			result: local Function(Boolean is matched){
				local Int is v: 0;
				if({ matched }, { v: 1; });
				Process:atomicPut(slot: 608, value: v);
			}
		);
		Assert:areEqualInt(1, Process:atomicGet(slot: 608));

		Process:atomicPut(slot: 609, value: -1);
		ar:rStartsWith(
			input: '2026-spec',
			pattern: '\\d+',
			result: local Function(Boolean is matched){
				local Int is v: 0;
				if({ matched }, { v: 1; });
				Process:atomicPut(slot: 609, value: v);
			}
		);
		Assert:areEqualInt(1, Process:atomicGet(slot: 609));

		Process:atomicPut(slot: 610, value: -1);
		ar:rEndsWith(
			input: 'spec-2026',
			pattern: '\\d+',
			result: local Function(Boolean is matched){
				local Int is v: 0;
				if({ matched }, { v: 1; });
				Process:atomicPut(slot: 610, value: v);
			}
		);
		Assert:areEqualInt(1, Process:atomicGet(slot: 610));
	}

	## rCount and rFindAll return all non-overlapping matches.
	Function is testCountAndFindAll(){
		Process:atomicPut(slot: 611, value: -1);
		ar:rCount(
			input: 'a1 b22 c333',
			pattern: '\\d+',
			result: local Function(Int is total){
				Process:atomicPut(slot: 611, value: total);
			}
		);
		Assert:areEqualInt(3, Process:atomicGet(slot: 611));

		local Channel of Str is chJoined: Channel();
		ar:rFindAll(
			input: 'Grace   Brewster  Hopper',
			pattern: '\\S+',
			result: local Function(Array of Str is matches){
				local String is joined: matches:join(separator: '|');
				chJoined:send(item: joined);
				return;
			}
		);
		Assert:areEqualString('Grace|Brewster|Hopper', chJoined:receive(default: ''));
	}

	## rSplit separates on regex matches and respects optional limit.
	Function is testSplit(){
		local Channel of Str is ch1: Channel();
		ar:rSplit(
			input: 'Grace   Brewster  Hopper',
			pattern: '\\s+',
			result: local Function(Array of Str is parts){
				ch1:send(item: parts:join(separator: '|'));
				return;
			}
		);
		Assert:areEqualString('Grace|Brewster|Hopper', ch1:receive(default: ''));

		local Channel of Str is ch2: Channel();
		ar:rSplit(
			input: 'a=b=c',
			pattern: '=',
			limit: 2,
			result: local Function(Array of Str is parts){
				ch2:send(item: parts:join(separator: '|'));
				return;
			}
		);
		Assert:areEqualString('a|b=c', ch2:receive(default: ''));

		local Channel of Str is ch3: Channel();
		ar:rSplit(
			input: 'a,b,',
			pattern: ',',
			result: local Function(Array of Str is parts){
				ch3:send(item: (parts:length() as String) . ':' . parts:join(separator: '|'));
				return;
			}
		);
		Assert:areEqualString('3:a|b|', ch3:receive(default: ''));
	}

	## rReplace, rReplaceWith, rReplaceAll, and rReplaceAllWith.
	Function is testReplaceAndReplaceAll(){
		local Channel of Str is ch1: Channel();
		ar:rReplace(
			input: 'a1 b2 c3',
			pattern: '\\d+',
			replacement: 'X',
			result: local Function(Str is out){
				ch1:send(item: out);
				return;
			}
		);
		Assert:areEqualString('aX b2 c3', ch1:receive(default: ''));

		local Channel of Str is ch2: Channel();
		ar:rReplaceAll(
			input: 'a1 b2 c3',
			pattern: '\\d+',
			replacement: 'X',
			result: local Function(Str is out){
				ch2:send(item: out);
				return;
			}
		);
		Assert:areEqualString('aX bX cX', ch2:receive(default: ''));

		local Channel of Str is ch3: Channel();
		ThreadScope:open(body: local Function(ThreadScope is scope){
			ar:rCompile(
				pattern: '\\d+',
				result: local Function(ArexPattern is numPat){
					ar:rReplaceAllWith(
						input: '[10] + [20]',
						pattern: numPat,
						replacer: local Function of Str(Str is m, Int is start, Int is end){
							return '<' . (m as String) . '>';
						},
						result: local Function(Str is out){
							ch3:send(item: out);
							return;
						}
					);
				}
			);
		});
		Assert:areEqualString('[<10>] + [<20>]', ch3:receive(default: ''));
	}

	## Str byte-level and String Unicode rune-aware parity methods with caseSensitive.
	Function is testStrAndStringParity(){
		local Str is raw: 'Hello Spec hello';
		Assert:isTrue(raw:contains(needle: 'SPEC', caseSensitive: false));
		Assert:isFalse(raw:contains(needle: 'SPEC'));
		Assert:isTrue(raw:startsWith(prefix: 'hello', caseSensitive: false));
		Assert:isTrue(raw:endsWith(suffix: 'HELLO', caseSensitive: false));
		Assert:isTrue(('Spec':equals(other: 'SPEC', caseSensitive: false)));
		Assert:areEqualInt(0, raw:find(needle: 'hello', caseSensitive: false));
		Assert:areEqualInt(11, raw:find(needle: 'hello', from: 1, caseSensitive: false));
		Assert:areEqualInt(2, raw:count(needle: 'hello', caseSensitive: false));
		Assert:areEqualString('Hello|hello', raw:findAll(needle: 'hello', caseSensitive: false):join(separator: '|'));
		Assert:areEqualString('Hi Spec hello', raw:replaceFirst(search: 'hello', replacement: 'Hi', caseSensitive: false));
		Assert:areEqualString('[Hello] Spec [hello]', raw:replaceAllWith(search: 'hello', replacer: local Function of Str(Str is m, Int is s, Int is e){ return '[' . (m as String) . ']'; }, caseSensitive: false));
		Assert:areEqualString('a|b=c', ('a=b=c' as Str):split(delimiter: '=', limit: 2):join(separator: '|'));

		local String is uni: 'Café café';
		Assert:isTrue(uni:sContains(needle: 'CAFÉ', caseSensitive: false));
		Assert:isFalse(uni:sContains(needle: 'CAFÉ'));
		Assert:isTrue(uni:sStartsWith(prefix: 'café', caseSensitive: false));
		Assert:isTrue(uni:sEndsWith(suffix: 'CAFÉ', caseSensitive: false));
		Assert:isTrue(('Café':sEquals(other: 'CAFÉ', caseSensitive: false)));
		Assert:areEqualInt(5, uni:sFind(needle: 'CAFÉ', fromRune: 1, caseSensitive: false));
		Assert:areEqualInt(2, uni:sCount(needle: 'café', caseSensitive: false));
		Assert:areEqualString('Café|café', uni:sFindAll(needle: 'café', caseSensitive: false):join(separator: '|'));
		Assert:areEqualString('Tea café', uni:sReplace(search: 'CAFÉ', replacement: 'Tea', caseSensitive: false));
		Assert:areEqualString('Tea Tea', uni:sReplaceAll(search: 'CAFÉ', replacement: 'Tea', caseSensitive: false));
		Assert:areEqualString('C|a|f|é', ('Café':sSplit(delimiter: '')):join(separator: '|'));
		Assert:areEqualString('<Café> <café>', uni:sReplaceAllWith(search: 'café', replacer: local Function of Str(String is m, Int is s, Int is e){ return '<' . m . '>'; }, caseSensitive: false));
	}
}
