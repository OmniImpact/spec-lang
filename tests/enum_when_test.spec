##
# Example and test suite for Spec Enums, 'when' branching, and inline 'if/else'
##

Enum is TokenKind {
	KEYWORD,
	IDENTIFIER,
	NUMBER,
	STRING,
	EOF
}

Enum of Int is HttpStatus {
	OK: 200,
	CREATED: 201,
	NOT_FOUND: 404,
	SERVER_ERROR: 500
}

Enum of String is LogLevel {
	NONE: '',
	DEBUG: 'DBG',
	INFO: 'INF',
	WARN: 'WRN',
	ERROR: 'ERR'
}

Class is EnumWhenTest{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'io', Output],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace init(Map of String to String is args){
		Output:line('=== Testing Enum, When, and Inline If/Else ===');

		self:testInlineIfElse();
		self:testEnumBasics();
		self:testWhenStatement();
		self:testWhenExpression();

		Output:line('=== All Enum, When, and If/Else Tests Passed Successfully ===');
	}

	testInlineIfElse(){
		Output:line('--- 1. Testing Inline If/Else Expressions ---');
		local Int is score: 85;
		local String is grade: if (score >= 90) 'A' else if (score >= 80) 'B' else 'C';
		Output:line('Grade: ' . grade);

		local Boolean is isReady: true;
		local String is statusText: if (isReady) 'Ready' else 'Not Ready';
		Output:line('Status: ' . statusText);

		local Int is bonus: if (score > 80) 10 else 0;
		Output:line('Bonus: ' . bonus);
	}

	testEnumBasics(){
		Output:line('--- 2. Testing Enum Reflection & Properties ---');
		local TokenKind is tok: TokenKind:KEYWORD;
		Output:line('Token name: ' . tok:name());
		Output:line('Token ordinal: ' . tok:ordinal());

		local HttpStatus is status: HttpStatus:NOT_FOUND;
		Output:line('Status name: ' . status:name());
		Output:line('Status value: ' . status:value());
		Output:line('Status ordinal: ' . status:ordinal());

		local LogLevel is level: LogLevel:WARN;
		Output:line('Level name: ' . level:name());
		Output:line('Level value: ' . level:value());
		Output:line('Level ordinal: ' . level:ordinal());

		local Array is allTokens: TokenKind:values();
		Output:line('TokenKind variant count: ' . allTokens:length());
	}

	testWhenStatement(){
		Output:line('--- 3. Testing When Statement ---');
		local HttpStatus is status: HttpStatus:OK;

		when (status) {
			is OK, CREATED: {
				Output:line('Status category: Success');
			}
			is NOT_FOUND: {
				Output:line('Status category: Client Error');
			}
			else: {
				Output:line('Status category: Other');
			}
		}

		local String is method: 'POST';
		when (method) {
			is 'GET': {
				Output:line('HTTP Method: Read');
			}
			is 'POST', 'PUT': {
				Output:line('HTTP Method: Write');
			}
			else: {
				Output:line('HTTP Method: Unknown');
			}
		}
	}

	testWhenExpression(){
		Output:line('--- 4. Testing When Expression ---');
		local TokenKind is tok: TokenKind:IDENTIFIER;

		local String is tokDescription: when (tok) {
			is KEYWORD: 'Reserved Keyword';
			is IDENTIFIER: 'Variable/Type Identifier';
			is NUMBER: 'Numeric Constant';
			is STRING: 'String Literal';
			is EOF: 'End of File';
		};
		Output:line('Token description: ' . tokDescription);

		# String-backed reverse lookup: the tag maps back to its variant,
		# no match yields the empty-tag default.
		if (LogLevel:of(value: 'WRN') == LogLevel:WARN && LogLevel:of(value: 'nope') == LogLevel:NONE) {
			Output:line('Reverse lookup of() round-trips and defaults');
		} else {
			Output:line('FAIL: of() lookup');
		}

		local HttpStatus is status: HttpStatus:SERVER_ERROR;
		local Boolean is canRetry: when (status) {
			is SERVER_ERROR: true;
			is NOT_FOUND: false;
			else: false;
		};
		Output:line('Can retry: ' . canRetry);

		local Int is priority: when (LogLevel:ERROR) {
			is NONE: 0;
			is DEBUG: 1;
			is INFO: 2;
			is WARN: 3;
			is ERROR: 4;
		};
		Output:line('Error priority: ' . priority);
	}
}
