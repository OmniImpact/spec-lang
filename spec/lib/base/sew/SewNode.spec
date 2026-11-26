#! Package base:sew
#! Base layout, theme, and reactive invalidation node for Sew/Scrap widgets.

Class is SewNode{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'signal', SignalBag],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	Rect is layoutBounds: Rect();
	Size is desiredSize: Size();
	Theme is activeTheme: Theme();
	Scale is activeScale: Scale(factor: 1.0);
	Boolean is pointerTransparent: false;
	SignalBag is signalBag: SignalBag();
	Array of Function is dirtyListeners: Array();

	## Propagates [theme] down the widget tree.
	Function is applyTheme(Theme is theme){
		:activeTheme: theme;
	}

	## Propagates point [scale] down the widget tree.
	Function is setScale(Scale is scale){
		:activeScale: scale;
	}

	## Paints this node into [ctx].
	Function is paint(DrawContext is ctx){
		local Int is _noop: 0;
	}

	## Handles vertical scroll wheel delta; returns `true` if redraw is needed.
	Function of Boolean is onScroll(Int is deltaY){
		return false;
	}

	## Handles horizontal scroll delta; returns `true` if redraw is needed.
	Function of Boolean is onScrollX(Int is deltaX){
		return false;
	}

	## Handles pointer click at ([x], [y], [mods]); returns `true` if redraw is needed.
	Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return false;
	}

	## Handles secondary (right) pointer click at ([x], [y], [mods]); returns `true` if redraw is needed.
	Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		return false;
	}

	## Handles pointer move at ([x], [y]); returns `true` if redraw is needed.
	Function of Boolean is onPointerMove(Int is x, Int is y){
		return false;
	}

	## Returns `true` when ([x], [y]) lies inside this node's arranged bounds.
	Function of Boolean is containsPoint(Int is x, Int is y){
		return x >= layoutBounds:x && x < layoutBounds:x + layoutBounds:width && y >= layoutBounds:y && y < layoutBounds:y + layoutBounds:height;
	}

	## Returns `true` when this surface intercepts pointer events at ([x], [y]) instead of passing them through.
	Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		return :containsPoint(x: x, y: y);
	}

	## Clears any active hover state when a surface above intercepts the pointer.
	Function is clearHover(){
		local Int is _noop: 0;
	}

	## Handles pointer drag while primary button is held at ([x], [y], [mods]); returns `true` if redraw is needed.
	Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		return false;
	}

	## Handles primary button release at ([x], [y]); returns `true` if redraw is needed.
	Function of Boolean is onPointerUp(Int is x, Int is y){
		return false;
	}

	## Periodic frame tick in monotonic milliseconds; returns `true` if redraw is needed.
	Function of Boolean is tick(Int is nowMs){
		return false;
	}

	## Handles key press ([key], [mods]); returns `true` if redraw is needed.
	Function of Boolean is onKey(Int is key, Int is mods){
		return false;
	}

	## Handles UTF-8 text input ([ch], [mods]); returns `true` if redraw is needed.
	Function of Boolean is onText(String is ch, Int is mods){
		return false;
	}

	## Registers a dirty/redraw listener [cb] (Theo-style invalidation).
	Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
	}

	## Marks this node dirty and notifies any registered listener.
	Function is invalidate(){
		if({ dirtyListeners:length() > 0 }, {
			local Function is fn: dirtyListeners:get(index: 0);
			fn();
		});
	}

	Function of Size is measure(Constraints is c){
		desiredSize: Size(width: c:clampW(w: 0), height: c:clampH(h: 0));
		return desiredSize;
	}

	Function is arrange(Rect is bounds){
		layoutBounds: bounds;
	}

	Function of Rect is bounds(){
		return layoutBounds;
	}
}
