#! specunit: negative
#! expect: ClassInfo 'TestUnconstructible' does not implement abstract member 'init' required by parent 'SpecUnitTest'.

#! SpecUnit framework rule: test classes construct with no arguments
#! (the runner instantiates them through the registry's zero-argument
#! constructor). A test class declaring an init that matches neither
#! of the base's overloads is rejected at compile time by the
#! member-compatibility check — the compile-time wall the former
#! --test validator provided, from a general guardian.

Class of SpecUnitTest is TestUnconstructible{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	replace Function is init(Int is seed){
	}
}
