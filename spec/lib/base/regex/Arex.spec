#! Package base:regex
#! Asynchronous callback-based regular expression engine (`Arex`).
##
## Instantiate `Arex` (`Arex()`, `Arex:init()`, or `as Arex() is ar` in `using`)
## and call `rCompile`, `rContains`, `rEquals`, `rStartsWith`, `rEndsWith`, `rFind`,
## `rCaptures`, `rCount`, `rFindAll`, `rSplit`, `rReplace`, `rReplaceWith`,
## `rReplaceAll`, or `rReplaceAllWith` with callbacks. All operations dispatch via
## `ThreadScope:dispatch`: when called inside a `ThreadScope:open` block they run
## concurrently on the enclosing scope; when called outside one they open a
## temporary scope and wait for completion before returning.

Class is Arex{
	namespace: ['base', 'regex'];

	replace Array of Array of String is using: [
		['base', 'core', Str],
		['base', 'core', String],
		['base', 'core', SpecError],
		['base', 'regex', RegexError],
		['base', 'regex', ArexPattern],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()]
	];

	local Str is defaultFlags: '';
	local Boolean is lookaroundEnabled: false;
	local Boolean is backrefEnabled: false;
	local Function is errorHandler: local Function(SpecError of RegexError is _err){};
	local Boolean is hasErrorHandler: false;

	replace Function is init(){
		:defaultFlags: '';
		:lookaroundEnabled: false;
		:backrefEnabled: false;
		:errorHandler: local Function(SpecError of RegexError is _err){};
		:hasErrorHandler: false;
	}

	## Sets default regex flags (`i`, `m`, `s`, `u`) for subsequent compiles/matches.
	Function is setFlags(Str is flags){
		:defaultFlags: flags;
	}

	## Enables or disables lookaround assertions (`(?=...)`, `(?!...)`, `(?<=...)`, `(?<!...)`).
	## Disabled by default to preserve guaranteed linear-time NFA execution.
	Function is enableLookaround(Boolean is enabled){
		:lookaroundEnabled: enabled;
	}

	## Enables or disables backreferences (`\1`..`\9`).
	## Disabled by default to preserve guaranteed linear-time NFA execution.
	Function is enableBackreference(Boolean is enabled){
		:backrefEnabled: enabled;
	}

	## Registers an error callback `(Str is errorMessage)` invoked when pattern compilation fails.
	Function is setOnError(Function is handler){
		:errorHandler: handler;
		:hasErrorHandler: true;
	}

	local Function of ArexPattern is compileOrReport(
		Str is pattern,
		Str is flags,
		Boolean is la,
		Boolean is br,
		Boolean is hasErrCb,
		Function is errCb
	){
		local ArexPattern is prog: ArexPattern:compile(
			pattern: pattern,
			flags: flags,
			enableLookaround: la,
			enableBackreference: br
		);
		if({ prog:hasError() && hasErrCb }, {
			errCb(SpecError:init(kind: RegexError:COMPILE_FAILED, description: 'regex compile failed: ' . prog:errorMessage()));
		});
		return prog;
	}

	## Compiles [pattern] into a reusable [ArexPattern] and invokes [result] with it.
	## Optional [flags] (`i`, `m`, `s`, `u`) and [onError] callback `(Str is err)`.
	Function is rCompile(
		Str is pattern,
		Function is result,
		Str is flags: '',
		Function is onError: local Function(SpecError of RegexError is _err){}
	){
		local Str is effFlags: :defaultFlags . flags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasDefErr: :hasErrorHandler;
		local Function is defErr: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is compiled: ArexPattern:compile(
				pattern: pattern,
				flags: effFlags,
				enableLookaround: la,
				enableBackreference: br
			);
			if({ compiled:hasError() }, {
				local Str is msg: compiled:errorMessage();
				onError(SpecError:init(kind: RegexError:COMPILE_FAILED, description: 'regex compile failed: ' . msg));
				if({ hasDefErr }, {
					defErr(SpecError:init(kind: RegexError:COMPILE_FAILED, description: 'regex compile failed: ' . msg));
				});
			}, {
				result(compiled);
			});
		});
	}

	## Tests whether [pattern] matches anywhere in [input] and invokes [result] with a `Boolean`.
	Function is rContains(Str is input, Str is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rContainsSync(input: input, result: result); });
		});
	}

	## Tests whether [pattern] matches anywhere in [input] and invokes [result] with a `Boolean`.
	Function is rContains(String is input, String is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rContainsSync(input: input, result: result); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rEqualsSync(input: input, result: result); });
		});
	}

	## Tests whether the entire [input] matches [pattern] and invokes [result] with a `Boolean`.
	Function is rEquals(String is input, String is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rEqualsSync(input: input, result: result); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rStartsWithSync(input: input, result: result); });
		});
	}

	## Tests whether [input] starts with a match of [pattern] and invokes [result] with a `Boolean`.
	Function is rStartsWith(String is input, String is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rStartsWithSync(input: input, result: result); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rEndsWithSync(input: input, result: result); });
		});
	}

	## Tests whether [input] ends with a match of [pattern] and invokes [result] with a `Boolean`.
	Function is rEndsWith(String is input, String is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rEndsWithSync(input: input, result: result); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rFindSync(input: input, result: result); });
		});
	}

	## Finds the leftmost-longest match of [pattern] in [input] and invokes [result]
	## with `(Boolean is found, Str is match, Int is start, Int is end)`.
	Function is rFind(String is input, String is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rFindSync(input: input, result: result); });
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

	## Finds the first match and capture groups of [pattern] in [input] and invokes [result]
	## with `(Boolean is found, Array of Str is groups)` where `groups[0]` is the full match.
	Function is rCaptures(Str is input, Str is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rCapturesSync(input: input, result: result); });
		});
	}

	## Finds the first match and capture groups of [pattern] in [input] and invokes [result].
	Function is rCaptures(String is input, String is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rCapturesSync(input: input, result: result); });
		});
	}

	## Finds the first match and capture groups of the precompiled [pattern] in [input] and invokes [result].
	Function is rCaptures(Str is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rCapturesSync(input: input, result: result);
		});
	}

	## Finds the first match and capture groups of the precompiled [pattern] in [input] and invokes [result].
	Function is rCaptures(String is input, ArexPattern is pattern, Function is result){
		ThreadScope:dispatch(task: local Function(){
			pattern:rCapturesSync(input: input, result: result);
		});
	}

	## Counts non-overlapping matches of [pattern] in [input] and invokes [result] with an `Int`.
	Function is rCount(Str is input, Str is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rCountSync(input: input, result: result); });
		});
	}

	## Counts non-overlapping matches of [pattern] in [input] and invokes [result] with an `Int`.
	Function is rCount(String is input, String is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rCountSync(input: input, result: result); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rFindAllSync(input: input, result: result); });
		});
	}

	## Finds all non-overlapping matches of [pattern] in [input] and invokes [result] with an `Array of Str`.
	Function is rFindAll(String is input, String is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rFindAllSync(input: input, result: result); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rSplitSync(input: input, result: result, limit: -1); });
		});
	}

	## Splits [input] around non-overlapping matches of [pattern] and invokes [result] with an `Array of Str`.
	Function is rSplit(String is input, String is pattern, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rSplitSync(input: input, result: result, limit: -1); });
		});
	}

	## Splits [input] around non-overlapping matches of [pattern] (at most [limit] parts) and invokes [result] with an `Array of Str`.
	Function is rSplit(Str is input, Str is pattern, Int is limit, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rSplitSync(input: input, result: result, limit: limit); });
		});
	}

	## Splits [input] around non-overlapping matches of [pattern] (at most [limit] parts) and invokes [result] with an `Array of Str`.
	Function is rSplit(String is input, String is pattern, Int is limit, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rSplitSync(input: input, result: result, limit: limit); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rReplaceStrSync(input: input, replacement: replacement, all: false, result: result); });
		});
	}

	## Replaces the first match of [pattern] in [input] with [replacement] and invokes [result] with the resulting `Str`.
	Function is rReplace(String is input, String is pattern, String is replacement, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rReplaceStrSync(input: input, replacement: replacement, all: false, result: result); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rReplaceFnSync(input: input, replacer: replacer, all: false, result: result); });
		});
	}

	## Replaces the first match of [pattern] in [input] using [replacer] `(Str is match, Int is start, Int is end) -> Str`.
	Function is rReplaceWith(String is input, String is pattern, Function of Str is replacer, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rReplaceFnSync(input: input, replacer: replacer, all: false, result: result); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rReplaceStrSync(input: input, replacement: replacement, all: true, result: result); });
		});
	}

	## Replaces all non-overlapping matches of [pattern] in [input] with [replacement] and invokes [result] with the resulting `Str`.
	Function is rReplaceAll(String is input, String is pattern, String is replacement, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rReplaceStrSync(input: input, replacement: replacement, all: true, result: result); });
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
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rReplaceFnSync(input: input, replacer: replacer, all: true, result: result); });
		});
	}

	## Replaces all non-overlapping matches of [pattern] in [input] using [replacer] `(Str is match, Int is start, Int is end) -> Str`.
	Function is rReplaceAllWith(String is input, String is pattern, Function of Str is replacer, Function is result){
		local Str is effFlags: :defaultFlags;
		local Boolean is la: :lookaroundEnabled;
		local Boolean is br: :backrefEnabled;
		local Boolean is hasErr: :hasErrorHandler;
		local Function is errCb: :errorHandler;
		ThreadScope:dispatch(task: local Function(){
			local ArexPattern is p: :compileOrReport(pattern: pattern, flags: effFlags, la: la, br: br, hasErrCb: hasErr, errCb: errCb);
			if({ !p:hasError() }, { p:rReplaceFnSync(input: input, replacer: replacer, all: true, result: result); });
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
