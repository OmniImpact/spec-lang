#! specunit: negative
#! expect: Undefined function 'floor' on class 'N27InnerImportLeak'

#! N27 (Part IV IV.3/IV.6): the inner class's OWN as-import
#! scopes to the inner — it does not leak outward into the enclosing
#! class or a sibling inner. The outer's bare call to the inner's
#! imported function is undefined (E9).

Class is N27InnerImportLeak{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];

	Class is MathUser{
		replace Array of Array of String is using: [
			['base', 'math', as Math()]
		];

		Function of Float is halved(Float is x){
			return Math:floor(value: x) / 2.0;
		}

		replace Function is init(){
		}
	}

	replace Function is init(Map of String to String is args){
		local Float is v: floor(value: 2.7);
		Output:line((v as String));
	}
}
