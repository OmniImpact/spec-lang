#! SpecUnit sweep (from syntactic_sugar_test.spec): syntactic sugar
#! and standard-library additions — the self:field constructor
#! shorthand, the 'is' equality operator, String helper inspection
#! methods, Array higher-order methods with anonymous functions,
#! search/replace/join chains, a generic Map, and the while() inline
#! loop.

Class of SpecUnitTest is TestSyntacticSugar{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', Loops],
		['base', 'sys', as Loops()]
	];

	## 1. The self:field constructor shorthand.
	Function is testSelfFieldConstructorShorthand(){
		local Issue is issue: Issue:init(line: 42, isWarning: false, message: 'Tab indentation required');
		Assert:areEqualInt(42, issue:getLine());
		Assert:areEqualString('Tab indentation required', issue:getMessage());
		Assert:isFalse(issue:getIsWarning());
	}

	## 2. The 'is' equality operator matches strings and ints.
	Function is testIsEqualityOperator(){
		local String is status: 'OK';
		local Int is count: 10;
		Assert:isTrue(status is 'OK');
		Assert:isTrue(count is 10);
	}

	## 3. String helper inspection methods: lines, trim, countLeading,
	## startsWith.
	Function is testStringHelperInspection(){
		local String is multiline: "Line 1\n  Line 2\n\tLine 3";
		local Array of String is lineList: multiline:lines();
		Assert:areEqualInt(3, lineList:length());

		local String is trimmed: '   hello world   ':trim();
		Assert:areEqualString('hello world', trimmed);

		local Int is spaceCount: '    four spaces':countLeading(search: ' ');
		Assert:areEqualInt(4, spaceCount);

		local String is prefixTest: '#! Package base';
		Assert:isTrue(prefixTest:startsWith(prefix: '#!'));
	}

	## 4. Array higher-order methods with anonymous functions: each, any,
	## count, filter.
	Function is testArrayHigherOrder(){
		local Array of String is words: ['apple', 'banana', 'cherry', 'avocado'];

		local Array of String is log: [];
		words:each(action: local Function(word){
			log:add(item: word);
		});
		Assert:areEqualInt(4, log:length());
		Assert:areEqualString('apple', log:get(index: 0, default: ''));
		Assert:areEqualString('avocado', log:get(index: 3, default: ''));

		local Boolean is hasBanana: words:any(predicate: local Function of Boolean(word){
			return word is 'banana';
		});
		Assert:isTrue(hasBanana);

		local Boolean is hasGrape: words:any(predicate: local Function of Boolean(word){
			return word is 'grape';
		});
		Assert:isFalse(hasGrape);

		local Int is aWordsCount: words:count(predicate: local Function of Boolean(word){
			return word:startsWith(prefix: 'a');
		});
		Assert:areEqualInt(2, aWordsCount);

		local Array of String is aWords: words:filter(predicate: local Function of Boolean(word){
			return word:startsWith(prefix: 'a');
		});
		Assert:areEqualInt(2, aWords:length());
		Assert:areEqualString('apple', aWords:get(index: 0, default: ''));
		Assert:areEqualString('avocado', aWords:get(index: 1, default: ''));
	}

	## 5. String:contains, String:endsWith, String:replaceAll, String:split,
	## Array:join.
	Function is testStringSearchAndReplace(){
		local String is pathStr: '/usr/local/bin/spec';
		Assert:isTrue(pathStr:contains(needle: 'local'));
		Assert:isTrue(pathStr:endsWith(suffix: 'spec'));

		local String is replacedStr: pathStr:replaceAll(search: '/', replacement: '::');
		Assert:areEqualString('::usr::local::bin::spec', replacedStr);

		local Array of String is parts: 'alpha,beta,gamma':split(delimiter: ',');
		Assert:areEqualString('alpha | beta | gamma', parts:join(separator: ' | '));
	}

	## 6. A generic Map of String to Issue.
	Function is testGenericMap(){
		local Issue is issue: Issue:init(line: 42, isWarning: false, message: 'Tab indentation required');
		local Map of String to Issue is issueMap: Map:init();
		issueMap:set(key: 'first', value: issue);
		local Issue is fetchedIssue: issueMap:get(key: 'first', default: issue);
		Assert:areEqualInt(42, fetchedIssue:getLine());
		Assert:areEqualString('Tab indentation required', fetchedIssue:getMessage());
	}

	## 7. The while() inline loop drives the counter to 3.
	Function is testWhileInlineLoop(){
		local Int is counter: 0;
		while(
			evaluate: local Function of Boolean(){ return counter < 3; },
			iteration: local Function of Boolean(){
				counter: counter + 1;
				return true;
			}
		);
		Assert:areEqualInt(3, counter);
	}
}

Class is Issue{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()]
	];
	Int is line;
	String is message;
	Boolean is isWarning;

	## Constructor using self:field initialization shorthand
	replace Function is init(self:line, self:isWarning, self:message){
	}

	Function of Int is getLine(){
		return self:line;
	}

	Function of String is getMessage(){
		return self:message;
	}

	Function of Boolean is getIsWarning(){
		return self:isWarning;
	}
}
