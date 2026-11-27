#! Package base:sew
#! Navigation stack region that does not impact layout and switches between named child containers.

Class of SewNode is NavStack{
	replace [String] is namespace: ['base', 'sew', 'nav'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', 'nav', NavRoute],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	TextEmitter is route: TextEmitter(initial: '');
	Array of NavRoute is routes: Array();
	Array of String is history: Array();

	replace Function is init(
		TextEmitter is route: TextEmitter(initial: ''),
		Array of NavRoute is routes: Array()
	){
		:route: route;
		:routes: routes;
		:history: Array();
		local String is initialName: route:current();
		if({ initialName != '' }, {
			history:add(item: initialName);
		}, {
			if({ routes:length() > 0 }, {
				local String is firstName: routes:get(index: 0):name;
				history:add(item: firstName);
				:route:emit(value: firstName);
			});
		});
		signalBag:track(
			slot: 'route',
			emitter: :route,
			collector: :route:collect(onEmit: local Function(String is next){
				if({ next != '' && (history:length() == 0 || history:get(index: history:length() - 1) != next) }, {
					history:add(item: next);
				});
				invalidate();
			})
		);
	}

	Function is addRoute(String is name, SewNode is child){
		routes:add(item: NavRoute(name: name, child: child));
	}

	Function is push(String is name){
		history:add(item: name);
		route:emit(value: name);
	}

	Function is replaceRoute(String is name){
		if({ history:length() > 0 }, {
			history:set(index: history:length() - 1, item: name);
		}, {
			history:add(item: name);
		});
		route:emit(value: name);
	}

	Function of Boolean is pop(){
		if({ history:length() <= 1 }, { return false; });
		history:removeAt(index: history:length() - 1);
		local String is prev: history:get(index: history:length() - 1);
		route:emit(value: prev);
		return true;
	}

	Function of String is currentRoute(){
		return route:current();
	}

	local Function of SewNode is activeChild(){
		local String is cur: route:current();
		local Int is i: 0;
		while({ i < routes:length() }, {
			local NavRoute is r: routes:get(index: i);
			if({ r:name == cur }, { return r:child; });
			i: i + 1;
		});
		if({ routes:length() > 0 }, { return routes:get(index: 0):child; });
		return SewNode();
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		times(count: routes:length(), worker: local Function(Int is i){
			routes:get(index: i):child:applyTheme(theme: theme);
		});
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		times(count: routes:length(), worker: local Function(Int is i){
			routes:get(index: i):child:setScale(scale: scale);
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		times(count: routes:length(), worker: local Function(Int is i){
			routes:get(index: i):child:bindDirty(cb: cb);
		});
	}

	replace Function of Size is measure(Constraints is c){
		desiredSize: :activeChild():measure(c: c);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		:activeChild():arrange(bounds: bounds);
	}

	replace Function is paint(DrawContext is ctx){
		:activeChild():paint(ctx: ctx);
	}

	replace Function is paintOverlay(DrawContext is ctx){
		:activeChild():paintOverlay(ctx: ctx);
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		return :activeChild():closePopupsOutside(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return :activeChild():onOverlayPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		return :activeChild():onOverlayPointerMove(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		return :activeChild():onOverlayPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		return :activeChild():onOverlayPointerUp(x: x, y: y);
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		return :activeChild():onScroll(deltaY: deltaY);
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		return :activeChild():onScrollX(deltaX: deltaX);
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return :activeChild():onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		return :activeChild():onRightClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		return :containsPoint(x: x, y: y) || :activeChild():blocksPointerAt(x: x, y: y);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return :activeChild():onPointerMove(x: x, y: y);
	}

	replace Function is clearHover(){
		:activeChild():clearHover();
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		return :activeChild():onPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		return :activeChild():onPointerUp(x: x, y: y);
	}

	replace Function of Boolean is tick(Int is nowMs){
		return :activeChild():tick(nowMs: nowMs);
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		return :activeChild():onKey(key: key, mods: mods);
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		return :activeChild():onText(ch: ch, mods: mods);
	}

	replace Function is collectFocusables(Array of SewNode is out){
		local SewNode is ch: :activeChild();
		if({ ch:canFocus() }, { out:add(item: ch); }, { ch:collectFocusables(out: out); });
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		return :activeChild():tooltipAt(x: x, y: y);
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		return :activeChild():cursorAt(x: x, y: y);
	}
}
