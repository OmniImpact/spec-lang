#! specunit: suite

#! Entry-init preference: an argv-capable init wins over an empty init
#! wherever each sits — main feeds the command-line Map when the entry
#! can take it, even though the empty overload was declared first.
#! Standalone (not a SpecUnit class): the semantics under test ARE the
#! entry class, which a suite's inherited entry would displace. The
#! runner gates on the exit code — the wrong-path overload prints [FAIL]
#! and exits 1.

Class is EntryPreferenceTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Process()]
	];

	replace Function is init(){
		Output:line('[FAIL] empty overload ran; the argv overload should have won');
		Process:exit(status: 1);
	}

	replace Function is init(Map of String to String is args){
		Output:line('[PASS] argv overload ran and took the command-line Map');
	}
}
