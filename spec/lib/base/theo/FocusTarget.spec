#! Package base:theo
#! Focus handle for interactive Theo widgets.

Class is FocusTarget{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', TheoCallback],
		['base', 'sys', as Conditional()]
	];

	Boolean is focused: false;
	Boolean is initial: false;
	Array of TheoCallback is ownerHooks: [];

	replace Function is init(Boolean is initial: false){
		:initial: initial;
		:focused: initial;
		:ownerHooks: [];
	}

	Function is bindOwner(Function is handler){
		:ownerHooks: [TheoCallback(fn: handler)];
	}

	Function is requestFocus(){
		:focused: true;
		if({ ownerHooks:length() > 0 }, {
			ownerHooks:get(index: 0):callAny(v: :);
		});
	}
}
