#! Package base:theo
#! Base layout and painting node for all Theo UI widgets and containers.

Class is Widget{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [TheoBuffer, TheoRenderer, TheoTheme, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'signal', [Emitter, Collector, SignalBag]],
		['base', 'sys', as Conditional()]
	];

	Int is boxX: 0;
	Int is boxY: 0;
	Int is boxW: 0;
	Int is boxH: 0;
	TheoTheme is activeTheme: TheoTheme();
	Array of Function is dirtyListeners: Array();
	SignalBag is signalBag: SignalBag();
	Boolean is suppressSync: false;

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

	Function of Int is measureWidth(Int is maxW){ maxW }

	Function of Int is measureHeight(Int is maxW, Int is maxH){ 1 }

	Function of Int is scrollOffsetY(){ 0 }

	Function of Int is scrollContentH(){ 0 }

	Function of Int is scrollViewportH(){ boxH }

	Function of Int is scrollOffsetX(){ 0 }

	Function of Int is scrollContentW(){ 0 }

	Function of Int is scrollViewportW(){ boxW }

	Function of Float is flexWeight(){ 0.0 }

	Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
	}

	Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		return;
	}

	Function of Boolean is containsPoint(Int is x, Int is y){ x >= boxX && x < boxX + boxW && y >= boxY && y < boxY + boxH }

	Function of Boolean is handleMouse(MouseEvent is event){ false }

	Function of Boolean is handleKey(KeyEvent is event){ false }

	Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		return;
	}

	Function is trackBinding(String is slot, Emitter is emitter, Collector is collector){
		signalBag:track(slot: slot, emitter: emitter, collector: collector);
	}

	Function is disposeBindings(){
		signalBag:clear();
	}

	Function is runMuted(Function is action){
		:suppressSync: true;
		action();
		:suppressSync: false;
	}

	Function of Boolean is isMuted(){ suppressSync }

	Function is dispose(){
		disposeBindings();
	}
}
