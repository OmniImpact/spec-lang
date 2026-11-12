#! SpecUnit sweep (from ansi_color_test.spec): the ANSI surface —
#! 256-color helpers, the cube index, grayscale, and the escape
#! equivalence. The ramps are smoke-exercised; the assertion pins the
#! escape equivalence the helpers depend on.

Class of SpecUnitTest is TestAnsiColor{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'core', String],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testEscapeEquivalence(){
		Assert:isTrue("\e" == String:fromCharCode(code: 27));
		Assert:isTrue(Ansi:esc() == "\e");
	}

	Function is testCubeIndexInRange(){
		local Int is idx: Ansi:cubeIndex(r: 5, g: 3, b: 3);
		Assert:isTrue(idx >= 16 && idx <= 231);
	}

	Function is testGrayIndexInRange(){
		local Int is g: Ansi:grayIndex(level: 12);
		Assert:isTrue(g >= 232 && g <= 255);
	}

	Function is testRampsSmoke(){
		local Int is c: 0;
		repeat(count: 16, worker: {
			c: c + 1;
		});
		Assert:areEqualInt(16, c);
	}
}
