#! Entry-init preference: an argv-capable init wins over an empty init
#! wherever each sits — main feeds the command-line Map when the entry
#! can take it, even though the empty overload was declared first.

Class is EntryPreferenceTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	replace Function is init(){
		Output:line('[FAIL] empty overload ran; the argv overload should have won');
	}

	replace Function is init(Map of String to String is args){
		Output:line('[PASS] argv overload ran and took the command-line Map');
	}
}
