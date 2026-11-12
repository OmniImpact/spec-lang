#! specunit: negative
#! expect: 'init' is construct-only

#! N10: init on an instance is banned; init is construct-only (E7).

Class is N10InitOnInstance {
	replace Function is init(Map of String to String is args) {
		local N10InitOnInstance is again: N10InitOnInstance:init();
		again:init();
	}
}
