#! Package base:regex
#! Asynchronous callback-based regular expression engine (`Arex`).
##
## Instantiate `Arex` (`Arex:init()`, or `as Arex()` in `using`) and call
## `compile`, `test`, and `find` with callbacks. All operations dispatch via
## `ThreadScope:dispatch`: when called inside a `ThreadScope:open` block they
## run concurrently on the enclosing scope; when called outside one they open
## a temporary scope and wait for completion before returning.
##
## Supported syntax: literals, `.`, `^`, `$`, `*`, `+`, `?`, `{m}`, `{m,}`,
## `{m,n}`, `( ... )` groups, `|` alternation, `[...]` / `[^...]` character
## classes with ranges, and `\d`, `\D`, `\w`, `\W`, `\s`, `\S`, `\n`, `\r`, `\t`,
## plus backslash escapes.

Class is Arex{
	namespace: ['base', 'regex'];

	replace Array of Array of String is using: [
		['base', 'core', Str],
		['base', 'core', String],
		['base', 'regex', ArexPattern],
		['base', 'sys', 'thread', ThreadScope]
	];

	## Compiles [pattern] into a reusable [ArexPattern] and invokes [result] with it.
	## Runs asynchronously inside an active `ThreadScope:open`, or waits if called outside one.
	Function is compile(Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is compiled: ArexPattern:compile(pattern: pattern);
			result(compiled);
		});
	}

	## Tests whether [input] matches [pattern] and invokes [result] with a `Boolean`.
	## Runs asynchronously inside an active `ThreadScope:open`, or waits if called outside one.
	Function is test(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):testSync(input: input, result: result);
		});
	}

	## Tests whether [input] matches [pattern] and invokes [result] with a `Boolean`.
	Function is test(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):testSync(input: input, result: result);
		});
	}

	## Tests whether [input] matches the precompiled [pattern] and invokes [result] with a `Boolean`.
	Function is test(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:testSync(input: input, result: result);
		});
	}

	## Tests whether [input] matches the precompiled [pattern] and invokes [result] with a `Boolean`.
	Function is test(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:testSync(input: input, result: result);
		});
	}

	## Finds the leftmost-longest match of [pattern] in [input] and invokes [result]
	## with `(Boolean is found, Str is match, Int is start, Int is end)`.
	## When no match is found, passes `(false, '', -1, -1)`.
	Function is find(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):findSync(input: input, result: result);
		});
	}

	## Finds the leftmost-longest match of [pattern] in [input] and invokes [result]
	## with `(Boolean is found, Str is match, Int is start, Int is end)`.
	Function is find(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):findSync(input: input, result: result);
		});
	}

	## Finds the leftmost-longest match of the precompiled [pattern] in [input] and invokes
	## [result] with `(Boolean is found, Str is match, Int is start, Int is end)`.
	Function is find(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:findSync(input: input, result: result);
		});
	}

	## Finds the leftmost-longest match of the precompiled [pattern] in [input] and invokes
	## [result] with `(Boolean is found, Str is match, Int is start, Int is end)`.
	Function is find(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:findSync(input: input, result: result);
		});
	}
}
