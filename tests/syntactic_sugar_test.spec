Class is SyntacticSugarTest{

	replace Array of String is using: [
		base:io:*,
		base:struct:Array,
		base:struct:Map,
		base:iterator:While
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Testing Syntactic Sugar & Standard Library Additions ===');

		# 1. Test self:field constructor shorthand
		local Issue is issue: Issue:init(line: 42, isWarning: false, message: 'Tab indentation required');
		output:line('Issue line: ' . issue:getLine());
		output:line('Issue message: ' . issue:getMessage());
		output:line('Issue warning: ' . issue:getIsWarning());

		# 2. Test 'is' equality operator
		local String is status: 'OK';
		if (status is 'OK') {
			output:line('is operator (string match): true');
		}
		local Int is count: 10;
		if (count is 10) {
			output:line('is operator (int match): true');
		}

		# 3. Test String helper inspection methods
		local String is multiline: "Line 1\n  Line 2\n\tLine 3";
		local Array of String is lineList: multiline:lines();
		output:line('Lines count: ' . lineList:length());

		local String is sample: '   hello world   ';
		local String is trimmed: sample:trim();
		output:line('Trimmed: \'' . trimmed . '\'');

		local String is leadingSpaces: '    four spaces';
		local Int is spaceCount: leadingSpaces:countLeading(search: ' ');
		output:line('Count leading spaces: ' . spaceCount);

		local String is prefixTest: '#! Package base';
		if (prefixTest:startsWith(prefix: '#!')) {
			output:line('startsWith \'#!\': true');
		}

		# 4. Test Array higher-order methods with anonymous functions
		local Array of String is words: ['apple', 'banana', 'cherry', 'avocado'];

		# Array:each
		output:line('--- Array:each ---');
		words:each(action: local Function(word){
			output:line('Word: ' . word);
		});

		# Array:any
		local Boolean is hasBanana: words:any(predicate: local Function of Boolean(word){
			return word is 'banana';
		});
		output:line('Has banana: ' . hasBanana);

		local Boolean is hasGrape: words:any(predicate: local Function of Boolean(word){
			return word is 'grape';
		});
		output:line('Has grape: ' . hasGrape);

		# Array:count
		local Int is aWordsCount: words:count(predicate: local Function of Boolean(word){
			return word:startsWith(prefix: 'a');
		});
		output:line('Words starting with \'a\': ' . aWordsCount);

		# Array:filter
		local Array of String is aWords: words:filter(predicate: local Function of Boolean(word){
			return word:startsWith(prefix: 'a');
		});
		output:line('Filtered length: ' . aWords:length());
		aWords:each(action: local Function(item){
			output:line('Filtered item: ' . item);
		});

		# 5. Test String:contains, String:endsWith, String:replaceAll, String:split, Array:join
		local String is pathStr: '/usr/local/bin/spec';
		output:line('contains \'local\': ' . pathStr:contains(needle: 'local'));
		output:line('endsWith \'spec\': ' . pathStr:endsWith(suffix: 'spec'));
		local String is replacedStr: pathStr:replaceAll(search: '/', replacement: '::');
		output:line('replaceAll: ' . replacedStr);
		local Array of String is parts: 'alpha,beta,gamma':split(delimiter: ',');
		output:line('split & join: ' . parts:join(separator: ' | '));

		# 6. Test Generic Map of String to Object & Int
		local Map of String to Issue is issueMap: Map:init();
		issueMap:set(key: 'first', value: issue);
		local Issue is fetchedIssue: issueMap:get(key: 'first', default: issue);
		output:line('Generic Map Issue line: ' . fetchedIssue:getLine());

		# 7. Test While:condition inline loop
		local Int is counter: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return counter < 3; },
			iteration: local Function of Boolean(){
				counter: counter + 1;
				return true;
			}
		);
		output:line('While:condition counter: ' . counter);

		output:line('=== Syntactic Sugar Test Completed Successfully ===');
	}

}

Class is Issue{
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
