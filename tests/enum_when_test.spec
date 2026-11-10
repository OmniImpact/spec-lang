##
# Example and test suite for Spec Enums, Cases:match dispatch, and inline 'if/else'
##

Enum is TokenKind2 {
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
		['base', 'sys', as Conditional()],
		['base', 'cases', as Cases()]
	];

	replace init(Map of String to String is args){
		Output:line('=== Testing Enum, Match, and Inline If/Else ===');

		self:testInlineIfElse();
		self:testEnumBasics();
		self:testMatchStatement();
		self:testMatchExpression();

		Output:line('=== All Enum, Match, and If/Else Tests Passed Successfully ===');
	}

	testInlineIfElse(){
		Output:line('--- 1. Testing Inline If/Else Expressions ---');
		local Int is score: 85;
		local String is grade: Conditional:if(check: { score >= 90 }, then: { 'A' }, else: { Conditional:if(check: { score >= 80 }, then: { 'B' }, else: { 'C' }) });
		Output:line('Grade: ' . grade);

		local Boolean is isReady: true;
		local String is statusText: Conditional:if(check: { isReady }, then: { 'Ready' }, else: { 'Not Ready' });
		Output:line('Status: ' . statusText);

		local Int is bonus: Conditional:if(check: { score > 80 }, then: { 10 }, else: { 0 });
		Output:line('Bonus: ' . bonus);
	}

	testEnumBasics(){
		Output:line('--- 2. Testing Enum Reflection & Properties ---');
		local TokenKind2 is tok: TokenKind2:KEYWORD;
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

		local Array is allTokens: TokenKind2:values();
		Output:line('TokenKind variant count: ' . allTokens:length());
	}

	testMatchStatement(){
		Output:line('--- 3. Testing Match Statement ---');
		local HttpStatus is status: HttpStatus:OK;

		Cases:match(on: status, arms: [
			[HttpStatus:OK, HttpStatus:CREATED]: {
				Output:line('Status category: Success');
			},
			HttpStatus:NOT_FOUND: {
				Output:line('Status category: Client Error');
			},
			else: {
				Output:line('Status category: Other');
			}
		]);

		local String is method: 'POST';
		Cases:match(on: method, arms: [
			'GET': {
				Output:line('HTTP Method: Read');
			},
			['POST', 'PUT']: {
				Output:line('HTTP Method: Write');
			},
			else: {
				Output:line('HTTP Method: Unknown');
			}
		]);
	}

	testMatchExpression(){
		Output:line('--- 4. Testing Match Expression ---');
		local TokenKind2 is tok: TokenKind2:IDENTIFIER;

		local String is tokDescription: Cases:match(on: tok, arms: [
			TokenKind2:KEYWORD: { 'Reserved Keyword' },
			TokenKind2:IDENTIFIER: { 'Variable/Type Identifier' },
			TokenKind2:NUMBER: { 'Numeric Constant' },
			TokenKind2:STRING: { 'String Literal' },
			TokenKind2:EOF: { 'End of File' }
		]);
		Output:line('Token description: ' . tokDescription);

		# String-backed reverse lookup: the tag maps back to its variant,
		# no match yields the empty-tag default.
		Conditional:if(check: { LogLevel:of(value: 'WRN') == LogLevel:WARN && LogLevel:of(value: 'nope') == LogLevel:NONE }, then: {
			Output:line('Reverse lookup of() round-trips and defaults');
		}, else: {
			Output:line('FAIL: of() lookup');
		});

		local HttpStatus is status: HttpStatus:SERVER_ERROR;
		local Boolean is canRetry: Cases:match(on: status, arms: [
			HttpStatus:SERVER_ERROR: { true },
			HttpStatus:NOT_FOUND: { false },
			else: { false }
		]);
		Output:line('Can retry: ' . canRetry);

		local Int is priority: Cases:match(on: LogLevel:ERROR, arms: [
			LogLevel:NONE: { 0 },
			LogLevel:DEBUG: { 1 },
			LogLevel:INFO: { 2 },
			LogLevel:WARN: { 3 },
			LogLevel:ERROR: { 4 }
		]);
		Output:line('Error priority: ' . priority);
	}
}
