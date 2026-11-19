#! SpecUnit tests for `base:regex:Arex` asynchronous callback-based regex matching.

Class of SpecUnitTest is TestArex{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'regex', as Arex() is ar],
		['base', 'regex', ArexPattern],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Channel],
		['base', 'sys', as Process()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Int is expectSync(Str is input, Str is pattern, Boolean is want){
		local Int is slot: 600;
		Process:atomicPut(slot: slot, value: -1);
		ar:test(
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

	## Outside ThreadScope:open, Arex:test waits for completion before returning.
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

	## Inside ThreadScope:open, Arex:test runs asynchronously on the scope and is joined on exit.
	Function is testAsyncInsideScope(){
		local Arex is rx: Arex:init();
		Process:atomicPut(slot: 601, value: -1);
		Process:atomicPut(slot: 602, value: -1);
		Process:atomicPut(slot: 603, value: -1);

		ThreadScope:open(body: local Function(ThreadScope is scope){
			Assert:isTrue(ThreadScope:inScope());
			rx:test(
				input: 'async spec regex',
				pattern: '^async .* regex$',
				result: local Function(Boolean is matched){
					local Int is v: 0;
					if({ matched }, { v: 1; });
					Process:atomicPut(slot: 601, value: v);
				}
			);
			rx:test(
				input: 'no match here',
				pattern: '^async',
				result: local Function(Boolean is matched){
					local Int is v: 0;
					if({ matched }, { v: 1; });
					Process:atomicPut(slot: 602, value: v);
				}
			);
			rx:test(
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

	## Arex:find returns leftmost-longest match text and byte span via callback.
	Function is testFind(){
		local Channel of Str is ch: Channel();
		ar:find(
			input: 'order #1234 and #5678',
			pattern: '#\\d+',
			result: local Function(Boolean is found, Str is match, Int is start, Int is end){
				if({ found && start == 6 && end == 11 }, {
					ch:send(item: match);
				}, {
					ch:send(item: 'ERR');
				});
			}
		);
		Assert:areEqualString('#1234', ch:receive(default: ''));

		local Channel of Str is chMiss: Channel();
		ThreadScope:open(body: local Function(ThreadScope is scope){
			ar:find(
				input: 'no numbers here',
				pattern: '\\d+',
				result: local Function(Boolean is found, Str is match, Int is start, Int is end){
					if({ !found && start == -1 && end == -1 && match == '' }, {
						chMiss:send(item: 'MISS');
					}, {
						chMiss:send(item: 'ERR');
					});
				}
			);
		});
		Assert:areEqualString('MISS', chMiss:receive(default: ''));
	}

	## Compiled ArexPattern via callback-based compile works with overloaded test and find.
	Function is testCompiledPatternReuse(){
		local Arex is rx: Arex();
		local Channel of ArexPattern is patCh: Channel();

		# Outside ThreadScope:open, rx:compile waits for compilation before returning.
		rx:compile(
			pattern: '[a-z]+-\\d+',
			result: local Function(ArexPattern is compiled){
				patCh:send(item: compiled);
			}
		);
		local ArexPattern is pat: patCh:receive(default: ArexPattern());
		Assert:areEqualString('[a-z]+-\\d+', pat:pattern());

		# Overloaded rx:test with precompiled ArexPattern outside scope (waits).
		Process:atomicPut(slot: 604, value: -1);
		rx:test(
			input: 'item-42',
			pattern: pat,
			result: local Function(Boolean is matched){
				local Int is v: 0;
				if({ matched }, { v: 1; });
				Process:atomicPut(slot: 604, value: v);
			}
		);
		Assert:areEqualInt(1, Process:atomicGet(slot: 604));

		# Overloaded ar:find with precompiled ArexPattern inside ThreadScope:open (async).
		local Channel of Str is chA: Channel();
		local Channel of Str is chB: Channel();
		ThreadScope:open(body: local Function(ThreadScope is scope){
			ar:find(
				input: 'first alpha-100 end',
				pattern: pat,
				result: local Function(Boolean is found, Str is match, Int is start, Int is end){
					if({ found }, { chA:send(item: match); }, { chA:send(item: 'ERR'); });
				}
			);
			ar:find(
				input: 'second beta-2026 end',
				pattern: pat,
				result: local Function(Boolean is found, Str is match, Int is start, Int is end){
					if({ found }, { chB:send(item: match); }, { chB:send(item: 'ERR'); });
				}
			);
			# Async ar:compile chaining into overloaded ar:test inside the same scope.
			ar:compile(
				pattern: '^v\\d+$',
				result: local Function(ArexPattern is verPat){
					ar:test(
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
		:ar:test(
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
}
