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
	DEBUG: "DBG",
	INFO: "INF",
	WARN: "WRN",
	ERROR: "ERR"
}

class EnumWhenTest{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:io:Output
	];

	init(Map of String to String is args){
		output:line("=== Testing Enum, When, and Inline If/Else ===");

		self:testInlineIfElse();
		self:testEnumBasics();
		self:testWhenStatement();
		self:testWhenExpression();

		output:line("=== All Enum, When, and If/Else Tests Passed Successfully ===");
	}

	testInlineIfElse(){
		output:line("--- 1. Testing Inline If/Else Expressions ---");
		local Int is score: 85;
		local String is grade: if (score >= 90) "A" else if (score >= 80) "B" else "C";
		output:line("Grade: " . grade);

		local Boolean is isReady: true;
		local String is statusText: if (isReady) "Ready" else "Not Ready";
		output:line("Status: " . statusText);

		local Int is bonus: if (score > 80) 10 else 0;
		output:line("Bonus: " . bonus);
	}

	testEnumBasics(){
		output:line("--- 2. Testing Enum Reflection & Properties ---");
		local TokenKind is tok: TokenKind:KEYWORD;
		output:line("Token name: " . tok:name());
		output:line("Token ordinal: " . tok:ordinal());

		local HttpStatus is status: HttpStatus:NOT_FOUND;
		output:line("Status name: " . status:name());
		output:line("Status value: " . status:value());
		output:line("Status ordinal: " . status:ordinal());

		local LogLevel is level: LogLevel:WARN;
		output:line("Level name: " . level:name());
		output:line("Level value: " . level:value());
		output:line("Level ordinal: " . level:ordinal());

		local Array is allTokens: TokenKind:values();
		output:line("TokenKind variant count: " . allTokens:length());
	}

	testWhenStatement(){
		output:line("--- 3. Testing When Statement ---");
		local HttpStatus is status: HttpStatus:OK;

		when (status) {
			is OK, CREATED: {
				output:line("Status category: Success");
			}
			is NOT_FOUND: {
				output:line("Status category: Client Error");
			}
			else: {
				output:line("Status category: Other");
			}
		}

		local String is method: "POST";
		when (method) {
			is "GET": {
				output:line("HTTP Method: Read");
			}
			is "POST", "PUT": {
				output:line("HTTP Method: Write");
			}
			else: {
				output:line("HTTP Method: Unknown");
			}
		}
	}

	testWhenExpression(){
		output:line("--- 4. Testing When Expression ---");
		local TokenKind is tok: TokenKind:IDENTIFIER;

		local String is tokDescription: when (tok) {
			is KEYWORD: "Reserved Keyword";
			is IDENTIFIER: "Variable/Type Identifier";
			is NUMBER: "Numeric Constant";
			is STRING: "String Literal";
			is EOF: "End of File";
		};
		output:line("Token description: " . tokDescription);

		local HttpStatus is status: HttpStatus:SERVER_ERROR;
		local Boolean is canRetry: when (status) {
			is SERVER_ERROR: true;
			is NOT_FOUND: false;
			else: false;
		};
		output:line("Can retry: " . canRetry);

		local Int is priority: when (LogLevel:ERROR) {
			is DEBUG: 1;
			is INFO: 2;
			is WARN: 3;
			is ERROR: 4;
		};
		output:line("Error priority: " . priority);
	}
}
