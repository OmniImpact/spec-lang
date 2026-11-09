Class is SyntacticSugarTest{

	replace Array of Array of String is using: [
		['base', 'io'],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator', Loops],
		['base', 'io', as Output()],
		['base', 'iterator', as Loops()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Testing Syntactic Sugar & Standard Library Additions ===');

		# 1. Test self:field constructor shorthand
		local Issue is issue: Issue:init(line: 42, isWarning: false, message: 'Tab indentation required');
		Output:line('Issue line: ' . issue:getLine());
		Output:line('Issue message: ' . issue:getMessage());
		Output:line('Issue warning: ' . issue:getIsWarning());

		# 2. Test 'is' equality operator
		local String is status: 'OK';
		Conditional:if(check: { status is 'OK' }, then: {
			Output:line('is operator (string match): true');
		});
		local Int is count: 10;
		Conditional:if(check: { count is 10 }, then: {
			Output:line('is operator (int match): true');
		});

		# 3. Test String helper inspection methods
		local String is multiline: "Line 1\n  Line 2\n\tLine 3";
		local Array of String is lineList: multiline:lines();
		Output:line('Lines count: ' . lineList:length());

		local String is sample: '   hello world   ';
		local String is trimmed: sample:trim();
		Output:line('Trimmed: \'' . trimmed . '\'');

		local String is leadingSpaces: '    four spaces';
		local Int is spaceCount: leadingSpaces:countLeading(search: ' ');
		Output:line('Count leading spaces: ' . spaceCount);

		local String is prefixTest: '#! Package base';
		Conditional:if(check: { prefixTest:startsWith(prefix: '#!') }, then: {
			Output:line('startsWith \'#!\': true');
		});

		# 4. Test Array higher-order methods with anonymous functions
		local Array of String is words: ['apple', 'banana', 'cherry', 'avocado'];

		# Array:each
		Output:line('--- Array:each ---');
		words:each(action: local Function(word){
			Output:line('Word: ' . word);
		});

		# Array:any
		local Boolean is hasBanana: words:any(predicate: local Function of Boolean(word){
			return word is 'banana';
		});
		Output:line('Has banana: ' . hasBanana);

		local Boolean is hasGrape: words:any(predicate: local Function of Boolean(word){
			return word is 'grape';
		});
		Output:line('Has grape: ' . hasGrape);

		# Array:count
		local Int is aWordsCount: words:count(predicate: local Function of Boolean(word){
			return word:startsWith(prefix: 'a');
		});
		Output:line('Words starting with \'a\': ' . aWordsCount);

		# Array:filter
		local Array of String is aWords: words:filter(predicate: local Function of Boolean(word){
			return word:startsWith(prefix: 'a');
		});
		Output:line('Filtered length: ' . aWords:length());
		aWords:each(action: local Function(item){
			Output:line('Filtered item: ' . item);
		});

		# 5. Test String:contains, String:endsWith, String:replaceAll, String:split, Array:join
		local String is pathStr: '/usr/local/bin/spec';
		Output:line('contains \'local\': ' . pathStr:contains(needle: 'local'));
		Output:line('endsWith \'spec\': ' . pathStr:endsWith(suffix: 'spec'));
		local String is replacedStr: pathStr:replaceAll(search: '/', replacement: '::');
		Output:line('replaceAll: ' . replacedStr);
		local Array of String is parts: 'alpha,beta,gamma':split(delimiter: ',');
		Output:line('split & join: ' . parts:join(separator: ' | '));

		# 6. Test Generic Map of String to Object & Int
		local Map of String to Issue is issueMap: Map:init();
		issueMap:set(key: 'first', value: issue);
		local Issue is fetchedIssue: issueMap:get(key: 'first', default: issue);
		Output:line('Generic Map Issue line: ' . fetchedIssue:getLine());

		# 7. Test the while() inline loop
		local Int is counter: 0;
		while(
			evaluate: local Function of Boolean(){ return counter < 3; },
			iteration: local Function of Boolean(){
				counter: counter + 1;
				return true;
			}
		);
		Output:line('while() counter: ' . counter);

		Output:line('=== Syntactic Sugar Test Completed Successfully ===');
	}

}

Class is Issue{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()],
		['base', 'iterator', as Loops()]
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
