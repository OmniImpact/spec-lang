#! Package base:regex
#! Asynchronous callback-based regular expression engine (`Arex`).
##
## All operations are callback-based and dispatch via `ThreadScope:dispatch`:
## when called inside a `ThreadScope:open` block they run concurrently on the
## enclosing scope; when called outside one they open a temporary scope and
## wait for completion before returning.
##
## Supported syntax: literals, `.`, `^`, `$`, `*`, `+`, `?`, `{m}`, `{m,}`,
## `{m,n}`, `( ... )` groups, `|` alternation, `[...]` / `[^...]` character
## classes with ranges, and `\d`, `\D`, `\w`, `\W`, `\s`, `\S`, `\n`, `\r`, `\t`,
## plus backslash escapes.

Class is Arex{
	namespace: ['base', 'regex'];

	replace Array of Array of String is using: [
		['base', 'core', Str],
		['base', 'struct', Array],
		['base', 'regex', ArexProgram],
		['base', 'sys', Conditional],
		['base', 'sys', 'thread', ThreadScope]
	];

	held local Conditional is heldCond: Conditional:init();

	## Tests whether [input] matches [pattern] and invokes [result] with a `Boolean`.
	## Runs asynchronously inside an active `ThreadScope:open`, or waits if called outside one.
	held Function is test(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			local ArexProgram is prog: ArexProgram:compile(pattern: pattern);
			local Array of Int is matchRes: prog:findFirstSync(input: input);
			local Boolean is matched: matchRes:get(index: 0) == 1;
			result(matched);
		});
	}

	## Finds the leftmost-longest match of [pattern] in [input] and invokes [result]
	## with `(Boolean is found, Str is match, Int is start, Int is end)`.
	## When no match is found, passes `(false, '', -1, -1)`.
	held Function is find(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			local ArexProgram is prog: ArexProgram:compile(pattern: pattern);
			local Array of Int is matchRes: prog:findFirstSync(input: input);
			local Boolean is found: matchRes:get(index: 0) == 1;
			local Int is start: matchRes:get(index: 1);
			local Int is end: matchRes:get(index: 2);
			local Str is matchedText: '';
			Arex:heldCond:if({ found }, {
				matchedText: input:substring(start: start, end: end);
			});
			result(found, matchedText, start, end);
		});
	}
}
