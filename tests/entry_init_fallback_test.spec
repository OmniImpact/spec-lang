#! specunit: suite

#! Entry-init fallback: an entry whose other overloads cannot take the
#! command-line args still runs through its empty init — the argv Map is
#! left out, and no compile-time error fires. The non-constructible
#! overload is declared FIRST, so a first-init-wins probe would have
#! rejected the whole program; the argv/empty preference must skip it.
#! Standalone (not a SpecUnit class): the semantics under test ARE the
#! entry class, which a suite's inherited entry would displace. The
#! runner gates on the exit code — the wrong-path overload prints [FAIL]
#! and exits 1.

Class is EntryFallbackTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Process()]
	];

	replace Function is init(String is tag){
		Output:line('[FAIL] the non-constructible overload ran');
		Process:exit(status: 1);
	}

	replace Function is init(){
		Output:line('[PASS] empty fallback ran, args left out');
	}
}
