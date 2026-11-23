#! Package base:theo
#! Focus handle for interactive Theo widgets.

Class is FocusTarget{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Boolean is focused: false;
	Boolean is initial: false;
	Boolean is hovered: false;
	Array of Function is ownerHooks: Array();
	Array of Function is focusListeners: Array();
	Array of Function is hoverListeners: Array();

	replace Function is init(Boolean is initial: false){
		:initial: initial;
		:focused: initial;
		:hovered: false;
		:ownerHooks: Array();
		:focusListeners: Array();
		:hoverListeners: Array();
	}

	Function is bindOwner(Function is handler){
		:ownerHooks: Array([handler]);
	}

	Function is onFocus(Function is handler){
		:focusListeners:add(item: handler);
	}

	Function is onHover(Function is handler){
		:hoverListeners:add(item: handler);
	}

	Function is setHovered(Boolean is next){
		if({ :hovered == next }, { return; });
		:hovered: next;
		local Int is i: 0;
		while({ i < hoverListeners:length() }, {
			local Function is fn: hoverListeners:get(index: i);
			fn(:);
			i: i + 1;
		});
	}

	Function is requestFocus(){
		:focused: true;
		if({ ownerHooks:length() > 0 }, {
			local Function is fn: ownerHooks:get(index: 0);
			fn(:);
		});
		local Int is i: 0;
		while({ i < focusListeners:length() }, {
			local Function is lfn: focusListeners:get(index: i);
			lfn(:);
			i: i + 1;
		});
	}
}
