#! specunit: negative
#! expect: Undefined identifier 'N21GroupTarget'.

#! N21: the group: partial mechanism is retired (Part IV) —
#! a group: declaration is an ordinary field; no fragment merging happens,
#! so the would-be target never comes into existence.

Class is N21GroupFragment{
	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	Array of String is group: [N21GroupTarget];

	Function is go(){
	}
}

Class is N21GroupCaller{
	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local N21GroupTarget is t: N21GroupTarget:init();
		Output:line(t:toString());
	}
}
