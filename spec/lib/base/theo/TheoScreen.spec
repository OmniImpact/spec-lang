#! Package base:theo
#! Navigation stack of [Frame]s managed by a [TheoApp].

Class is TheoScreen{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'sys', as Conditional()]
	];

	Array of Frame is stack: Array();
	Array of Function is dirtyHooks: Array();

	replace Function is init(Frame is root){
		:stack: Array();
		:dirtyHooks: Array();
		push(frame: root);
	}

	Function is bindDirty(Function is cb){
		:dirtyHooks: Array([cb]);
		stack:each(action: local Function(Frame is f){
			f:bindDirty(cb: cb);
		});
	}

	Function is markDirty(){
		if({ dirtyHooks:length() > 0 }, {
			local Function is fn: dirtyHooks:get(index: 0);
			fn();
		});
	}

	Function of Frame is current(){
		return stack:get(index: stack:length() - 1);
	}

	Function is push(Frame is frame){
		if({ stack:length() > 0 }, {
			current():onPause();
		});
		if({ dirtyHooks:length() > 0 }, {
			frame:bindDirty(cb: dirtyHooks:get(index: 0));
		});
		stack:add(item: frame);
		frame:onEnter();
		markDirty();
	}

	Function is pop(){
		if({ stack:length() <= 1 }, { return; });
		local Int is topIdx: stack:length() - 1;
		local Frame is top: stack:get(index: topIdx);
		top:onExit();
		stack:removeAt(index: topIdx);
		current():onResume();
		markDirty();
	}

	Function is replace(Frame is frame){
		if({ stack:length() > 0 }, {
			local Int is topIdx: stack:length() - 1;
			local Frame is top: stack:get(index: topIdx);
			top:onExit();
			stack:removeAt(index: topIdx);
		});
		if({ dirtyHooks:length() > 0 }, {
			frame:bindDirty(cb: dirtyHooks:get(index: 0));
		});
		stack:add(item: frame);
		frame:onEnter();
		markDirty();
	}
}
