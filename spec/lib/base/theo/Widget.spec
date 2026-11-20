#! Package base:theo
#! Base layout and painting node for all Theo UI widgets and containers.

Class is Widget{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'theo', TheoCallback],
		['base', 'theo', KeyEvent],
		['base', 'theo', FocusTarget],
		['base', 'sys', as Conditional()]
	];

	Int is boxX: 0;
	Int is boxY: 0;
	Int is boxW: 0;
	Int is boxH: 0;
	Array of TheoCallback is dirtyListeners: [];

	replace Function is init(){
		:dirtyListeners: [];
	}

	Function is bindDirty(Function is cb){
		:dirtyListeners: [TheoCallback(fn: cb)];
	}

	Function is invalidate(){
		if({ dirtyListeners:length() > 0 }, {
			dirtyListeners:get(index: 0):call();
		});
	}

	Function of Int is measureWidth(Int is maxW){
		return maxW;
	}

	Function of Int is measureHeight(Int is maxW, Int is maxH){
		return 1;
	}

	Function of Float is flexWeight(){
		return 0.0;
	}

	Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
	}

	Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		return;
	}

	Function of Boolean is handleKey(KeyEvent is event){
		return false;
	}

	Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		return;
	}

	Function is dispose(){
		return;
	}
}
