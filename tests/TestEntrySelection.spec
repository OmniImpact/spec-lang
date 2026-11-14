#! SpecUnit test suite: compiler entry selection regressions (a class with
#! no init, a zero-arg entry init called with true arity, and fallback to
#! an empty init when the first overload is non-constructible).

Class of SpecUnitTest is TestEntrySelection{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	## A root class with NO init anywhere on its lattice compiles and runs.
	Function is testEntryNoInit(){
		Assert:runSucceeds(
			source: "Class is EntryNoInit{\n}\n",
			expect: ""
		);
	}

	## A zero-argument entry init is called with its true arity.
	Function is testEntryZeroArgInit(){
		Assert:runSucceeds(
			source: "Class is EntryZeroArgInit{\n\treplace Array of Array of String is using: [\n\t\t['base', 'sys', as Output()]\n\t];\n\treplace Function is init(){\n\t\tOutput:line('zero-arg entry init ran');\n\t}\n}\n",
			expect: "zero-arg entry init ran"
		);
	}

	## An entry whose other overloads cannot take args falls back to its empty init.
	Function is testEntryInitFallback(){
		Assert:runSucceeds(
			source: "Class is EntryFallbackTest{\n\treplace Array of Array of String is using: [\n\t\t['base', 'sys', as Output()],\n\t\t['base', 'sys', as Process()]\n\t];\n\treplace Function is init(String is tag){\n\t\tOutput:line('[FAIL] the non-constructible overload ran');\n\t\tProcess:exit(status: 1);\n\t}\n\treplace Function is init(){\n\t\tOutput:line('[PASS] empty fallback ran');\n\t}\n}\n",
			expect: "empty fallback ran"
		);
	}
}
