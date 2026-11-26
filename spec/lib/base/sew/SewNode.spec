#! Package base:sew
#! Base layout, theme, and reactive invalidation node for Sew/Scrap widgets.

Class is SewNode{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'signal', SignalBag],
		['base', 'fabric', Theme],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints]
	];

	Rect is layoutBounds: Rect();
	Size is desiredSize: Size();
	Theme is activeTheme: Theme();
	SignalBag is signalBag: SignalBag();
	Array of Function is dirtyListeners: Array();

	## Propagates [theme] down the widget tree.
	Function is applyTheme(Theme is theme){
		:activeTheme: theme;
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
