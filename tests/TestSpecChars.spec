#! SpecUnit sweep (from spec_chars_test.spec): the compiler's Chars
#! utility classifications — identifier start/continue and uppercase —
#! construct-and-call over the compiled String surface.

Class of SpecUnitTest is TestSpecChars{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'utils', Chars],
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	Function is testIdentifierStart(){
		local Chars is ch: Chars:init();
		Assert:isTrue(ch:isIdentifierStart(ch: '_'));
		Assert:isTrue(ch:isIdentifierStart(ch: 'a'));
		Assert:isFalse(ch:isIdentifierStart(ch: '7'));
	}

	Function is testIdentifierContinue(){
		local Chars is ch: Chars:init();
		Assert:isTrue(ch:isIdentifierContinue(ch: '7'));
		Assert:isTrue(ch:isIdentifierContinue(ch: '_'));
		Assert:isFalse(ch:isIdentifierContinue(ch: '-'));
	}

	Function is testUppercaseClassification(){
		local Chars is ch: Chars:init();
		Assert:isTrue(ch:isUpper(ch: 'A'));
		Assert:isFalse(ch:isUpper(ch: 'a'));
	}
}
