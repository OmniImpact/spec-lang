#! Package base:theo
#! Base layout and painting node for all Theo UI widgets and containers.

Class is Widget{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [TheoBuffer, TheoRenderer, TheoTheme, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'sys', as Conditional()]
	];

	Int is boxX: 0;
	Int is boxY: 0;
	Int is boxW: 0;
	Int is boxH: 0;
	TheoTheme is activeTheme: TheoTheme();
	Array of Function is dirtyListeners: Array();

	Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
	}

	Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
	}

	Function is invalidate(){
		if({ dirtyListeners:length() > 0 }, {
			local Function is fn: dirtyListeners:get(index: 0);
			fn();
		});
	}

	Function of Int is measureWidth(Int is maxW){
		return maxW;
	}

	Function of Int is measureHeight(Int is maxW, Int is maxH){
		return 1;
	}

	Function of Int is scrollOffsetY(){
		return 0;
	}

	Function of Int is scrollContentH(){
		return 0;
	}

	Function of Int is scrollViewportH(){
		return boxH;
	}

	Function of Int is scrollOffsetX(){
		return 0;
	}

	Function of Int is scrollContentW(){
		return 0;
	}

	Function of Int is scrollViewportW(){
		return boxW;
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

	Function of Boolean is containsPoint(Int is x, Int is y){
		return x >= boxX && x < boxX + boxW && y >= boxY && y < boxY + boxH;
	}

	Function of Boolean is handleMouse(MouseEvent is event){
		return false;
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
