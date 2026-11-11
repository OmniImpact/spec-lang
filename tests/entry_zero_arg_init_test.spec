#! Entry-selection regression: a zero-argument entry init is called with
#! its true arity (X_init(app)). The argv Map is passed only to
#! Map-parameter inits; passing it unconditionally to a zero-arg init
#! failed at the backend C compiler with raw gcc diagnostics.

Class is EntryZeroArgInit{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	replace Function is init(){
		Output:line('[PASS] zero-arg entry init ran with its true arity');
	}
}
