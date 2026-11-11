#! Package entrybase
#! Base of the inherited-entry-init regression: the root file's entry
#! class extends this class and has no init of its own.

Class is BaseApp{
	namespace: ['entrybase'];

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('[PASS] inherited entry init ran at the owner symbol');
	}
}
