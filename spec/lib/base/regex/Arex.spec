#! Package base:regex
#! Asynchronous callback-based regular expression engine (`Arex`).
##
## Instantiate `Arex` (`Arex()`, `Arex:init()`, or `as Arex() is ar` in `using`)
## and call `rCompile`, `rContains`, `rEquals`, `rStartsWith`, `rEndsWith`, `rFind`,
## `rCount`, `rFindAll`, `rSplit`, `rReplace`, `rReplaceWith`, `rReplaceAll`, or
## `rReplaceAllWith` with callbacks. All operations dispatch via `ThreadScope:dispatch`:
## when called inside a `ThreadScope:open` block they run concurrently on the
## enclosing scope; when called outside one they open a temporary scope and wait
## for completion before returning.
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
	Function is rCompile(Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is compiled: ArexPattern:compile(pattern: pattern);
			result(compiled);
		});
	}

	## Tests whether [pattern] matches anywhere in [input] and invokes [result] with a `Boolean`.
	Function is rContains(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rContainsSync(input: input, result: result);
		});
	}

	## Tests whether [pattern] matches anywhere in [input] and invokes [result] with a `Boolean`.
	Function is rContains(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rContainsSync(input: input, result: result);
		});
	}

	## Tests whether the precompiled [pattern] matches anywhere in [input] and invokes [result] with a `Boolean`.
	Function is rContains(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rContainsSync(input: input, result: result);
		});
	}

	## Tests whether the precompiled [pattern] matches anywhere in [input] and invokes [result] with a `Boolean`.
	Function is rContains(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rContainsSync(input: input, result: result);
		});
	}

	## Tests whether the entire [input] matches [pattern] and invokes [result] with a `Boolean`.
	Function is rEquals(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rEqualsSync(input: input, result: result);
		});
	}

	## Tests whether the entire [input] matches [pattern] and invokes [result] with a `Boolean`.
	Function is rEquals(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rEqualsSync(input: input, result: result);
		});
	}

	## Tests whether the entire [input] matches the precompiled [pattern] and invokes [result] with a `Boolean`.
	Function is rEquals(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rEqualsSync(input: input, result: result);
		});
	}

	## Tests whether the entire [input] matches the precompiled [pattern] and invokes [result] with a `Boolean`.
	Function is rEquals(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rEqualsSync(input: input, result: result);
		});
	}

	## Tests whether [input] starts with a match of [pattern] and invokes [result] with a `Boolean`.
	Function is rStartsWith(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rStartsWithSync(input: input, result: result);
		});
	}

	## Tests whether [input] starts with a match of [pattern] and invokes [result] with a `Boolean`.
	Function is rStartsWith(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rStartsWithSync(input: input, result: result);
		});
	}

	## Tests whether [input] starts with a match of the precompiled [pattern] and invokes [result] with a `Boolean`.
	Function is rStartsWith(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rStartsWithSync(input: input, result: result);
		});
	}

	## Tests whether [input] starts with a match of the precompiled [pattern] and invokes [result] with a `Boolean`.
	Function is rStartsWith(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rStartsWithSync(input: input, result: result);
		});
	}

	## Tests whether [input] ends with a match of [pattern] and invokes [result] with a `Boolean`.
	Function is rEndsWith(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rEndsWithSync(input: input, result: result);
		});
	}

	## Tests whether [input] ends with a match of [pattern] and invokes [result] with a `Boolean`.
	Function is rEndsWith(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rEndsWithSync(input: input, result: result);
		});
	}

	## Tests whether [input] ends with a match of the precompiled [pattern] and invokes [result] with a `Boolean`.
	Function is rEndsWith(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rEndsWithSync(input: input, result: result);
		});
	}

	## Tests whether [input] ends with a match of the precompiled [pattern] and invokes [result] with a `Boolean`.
	Function is rEndsWith(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rEndsWithSync(input: input, result: result);
		});
	}

	## Finds the leftmost-longest match of [pattern] in [input] and invokes [result]
	## with `(Boolean is found, Str is match, Int is start, Int is end)`.
	Function is rFind(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rFindSync(input: input, result: result);
		});
	}

	## Finds the leftmost-longest match of [pattern] in [input] and invokes [result]
	## with `(Boolean is found, Str is match, Int is start, Int is end)`.
	Function is rFind(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rFindSync(input: input, result: result);
		});
	}

	## Finds the leftmost-longest match of the precompiled [pattern] in [input] and invokes
	## [result] with `(Boolean is found, Str is match, Int is start, Int is end)`.
	Function is rFind(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rFindSync(input: input, result: result);
		});
	}

	## Finds the leftmost-longest match of the precompiled [pattern] in [input] and invokes
	## [result] with `(Boolean is found, Str is match, Int is start, Int is end)`.
	Function is rFind(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rFindSync(input: input, result: result);
		});
	}

	## Counts non-overlapping matches of [pattern] in [input] and invokes [result] with an `Int`.
	Function is rCount(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rCountSync(input: input, result: result);
		});
	}

	## Counts non-overlapping matches of [pattern] in [input] and invokes [result] with an `Int`.
	Function is rCount(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rCountSync(input: input, result: result);
		});
	}

	## Counts non-overlapping matches of the precompiled [pattern] in [input] and invokes [result] with an `Int`.
	Function is rCount(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rCountSync(input: input, result: result);
		});
	}

	## Counts non-overlapping matches of the precompiled [pattern] in [input] and invokes [result] with an `Int`.
	Function is rCount(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rCountSync(input: input, result: result);
		});
	}

	## Finds all non-overlapping matches of [pattern] in [input] and invokes [result] with an `Array of Str`.
	Function is rFindAll(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rFindAllSync(input: input, result: result);
		});
	}

	## Finds all non-overlapping matches of [pattern] in [input] and invokes [result] with an `Array of Str`.
	Function is rFindAll(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rFindAllSync(input: input, result: result);
		});
	}

	## Finds all non-overlapping matches of the precompiled [pattern] in [input] and invokes [result] with an `Array of Str`.
	Function is rFindAll(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rFindAllSync(input: input, result: result);
		});
	}

	## Finds all non-overlapping matches of the precompiled [pattern] in [input] and invokes [result] with an `Array of Str`.
	Function is rFindAll(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rFindAllSync(input: input, result: result);
		});
	}

	## Splits [input] around non-overlapping matches of [pattern] and invokes [result] with an `Array of Str`.
	Function is rSplit(Str is input, Str is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rSplitSync(input: input, result: result, limit: -1);
		});
	}

	## Splits [input] around non-overlapping matches of [pattern] and invokes [result] with an `Array of Str`.
	Function is rSplit(String is input, String is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rSplitSync(input: input, result: result, limit: -1);
		});
	}

	## Splits [input] around non-overlapping matches of [pattern] (at most [limit] parts) and invokes [result] with an `Array of Str`.
	Function is rSplit(Str is input, Str is pattern, Int is limit, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rSplitSync(input: input, result: result, limit: limit);
		});
	}

	## Splits [input] around non-overlapping matches of [pattern] (at most [limit] parts) and invokes [result] with an `Array of Str`.
	Function is rSplit(String is input, String is pattern, Int is limit, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rSplitSync(input: input, result: result, limit: limit);
		});
	}

	## Splits [input] around non-overlapping matches of the precompiled [pattern] and invokes [result] with an `Array of Str`.
	Function is rSplit(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rSplitSync(input: input, result: result, limit: -1);
		});
	}

	## Splits [input] around non-overlapping matches of the precompiled [pattern] and invokes [result] with an `Array of Str`.
	Function is rSplit(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rSplitSync(input: input, result: result, limit: -1);
		});
	}

	## Splits [input] around non-overlapping matches of the precompiled [pattern] (at most [limit] parts) and invokes [result] with an `Array of Str`.
	Function is rSplit(Str is input, ArexPattern is pattern, Int is limit, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rSplitSync(input: input, result: result, limit: limit);
		});
	}

	## Splits [input] around non-overlapping matches of the precompiled [pattern] (at most [limit] parts) and invokes [result] with an `Array of Str`.
	Function is rSplit(String is input, ArexPattern is pattern, Int is limit, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rSplitSync(input: input, result: result, limit: limit);
		});
	}

	## Replaces the first match of [pattern] in [input] with [replacement] and invokes [result] with the resulting `Str`.
	Function is rReplace(Str is input, Str is pattern, Str is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rReplaceStrSync(input: input, replacement: replacement, all: false, result: result);
		});
	}

	## Replaces the first match of [pattern] in [input] with [replacement] and invokes [result] with the resulting `Str`.
	Function is rReplace(String is input, String is pattern, String is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rReplaceStrSync(input: input, replacement: replacement, all: false, result: result);
		});
	}

	## Replaces the first match of the precompiled [pattern] in [input] with [replacement].
	Function is rReplace(Str is input, ArexPattern is pattern, Str is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rReplaceStrSync(input: input, replacement: replacement, all: false, result: result);
		});
	}

	## Replaces the first match of the precompiled [pattern] in [input] with [replacement].
	Function is rReplace(String is input, ArexPattern is pattern, String is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rReplaceStrSync(input: input, replacement: replacement, all: false, result: result);
		});
	}

	## Replaces the first match of [pattern] in [input] using [replacer] `(Str is match, Int is start, Int is end) -> Str`.
	Function is rReplaceWith(Str is input, Str is pattern, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rReplaceFnSync(input: input, replacer: replacer, all: false, result: result);
		});
	}

	## Replaces the first match of [pattern] in [input] using [replacer] `(Str is match, Int is start, Int is end) -> Str`.
	Function is rReplaceWith(String is input, String is pattern, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rReplaceFnSync(input: input, replacer: replacer, all: false, result: result);
		});
	}

	## Replaces the first match of the precompiled [pattern] in [input] using [replacer].
	Function is rReplaceWith(Str is input, ArexPattern is pattern, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rReplaceFnSync(input: input, replacer: replacer, all: false, result: result);
		});
	}

	## Replaces the first match of the precompiled [pattern] in [input] using [replacer].
	Function is rReplaceWith(String is input, ArexPattern is pattern, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rReplaceFnSync(input: input, replacer: replacer, all: false, result: result);
		});
	}

	## Replaces all non-overlapping matches of [pattern] in [input] with [replacement] and invokes [result] with the resulting `Str`.
	Function is rReplaceAll(Str is input, Str is pattern, Str is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rReplaceStrSync(input: input, replacement: replacement, all: true, result: result);
		});
	}

	## Replaces all non-overlapping matches of [pattern] in [input] with [replacement] and invokes [result] with the resulting `Str`.
	Function is rReplaceAll(String is input, String is pattern, String is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rReplaceStrSync(input: input, replacement: replacement, all: true, result: result);
		});
	}

	## Replaces all non-overlapping matches of the precompiled [pattern] in [input] with [replacement].
	Function is rReplaceAll(Str is input, ArexPattern is pattern, Str is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rReplaceStrSync(input: input, replacement: replacement, all: true, result: result);
		});
	}

	## Replaces all non-overlapping matches of the precompiled [pattern] in [input] with [replacement].
	Function is rReplaceAll(String is input, ArexPattern is pattern, String is replacement, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rReplaceStrSync(input: input, replacement: replacement, all: true, result: result);
		});
	}

	## Replaces all non-overlapping matches of [pattern] in [input] using [replacer] `(Str is match, Int is start, Int is end) -> Str`.
	Function is rReplaceAllWith(Str is input, Str is pattern, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rReplaceFnSync(input: input, replacer: replacer, all: true, result: result);
		});
	}

	## Replaces all non-overlapping matches of [pattern] in [input] using [replacer] `(Str is match, Int is start, Int is end) -> Str`.
	Function is rReplaceAllWith(String is input, String is pattern, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			ArexPattern:compile(pattern: pattern):rReplaceFnSync(input: input, replacer: replacer, all: true, result: result);
		});
	}

	## Replaces all non-overlapping matches of the precompiled [pattern] in [input] using [replacer].
	Function is rReplaceAllWith(Str is input, ArexPattern is pattern, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rReplaceFnSync(input: input, replacer: replacer, all: true, result: result);
		});
	}

	## Replaces all non-overlapping matches of the precompiled [pattern] in [input] using [replacer].
	Function is rReplaceAllWith(String is input, ArexPattern is pattern, Function of Str is replacer, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rReplaceFnSync(input: input, replacer: replacer, all: true, result: result);
		});
	}
}
