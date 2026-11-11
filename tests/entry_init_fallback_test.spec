#! Entry-init fallback: an entry whose other overloads cannot take the
#! command-line args still runs through its empty init — the argv Map is
#! left out, and no compile-time error fires. The non-constructible
#! overload is declared FIRST, so a first-init-wins probe would have
#! rejected the whole program; the argv/empty preference must skip it.

Class is EntryFallbackTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	replace Function is init(String is tag){
		Output:line('[FAIL] the non-constructible overload ran');
	}

	replace Function is init(){
		Output:line('[PASS] empty fallback ran, args left out');
	}
}
