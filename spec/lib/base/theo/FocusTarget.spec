#! Package base:theo
#! Focus handle for interactive Theo widgets.

Class is FocusTarget{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	Boolean is focused: false;
	Boolean is initial: false;
	Array of Function is ownerHooks: Array();

	replace Function is init(Boolean is initial: false){
		:initial: initial;
		:focused: initial;
		:ownerHooks: Array();
	}

	Function is bindOwner(Function is handler){
		:ownerHooks: Array([handler]);
	}

	Function is requestFocus(){
		:focused: true;
		if({ ownerHooks:length() > 0 }, {
			local Function is fn: ownerHooks:get(index: 0);
			fn(:);
		});
	}
}
