#! Package base:sew
#! Reactive layout node switching between two child subtrees based on a `BoolEmitter`.

Class of SewNode is ViewSwitch{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'signal', BoolEmitter],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	BoolEmitter is condition: BoolEmitter(initial: true);
	SewNode is first: SewNode();
	SewNode is second: SewNode();

	replace Function is init(
		BoolEmitter is condition: BoolEmitter(initial: true),
		SewNode is first: SewNode(),
		SewNode is second: SewNode()
	){
		:condition: condition;
		:first: first;
		:second: second;
		signalBag:track(
			slot: 'condition',
			emitter: :condition,
			collector: :condition:collect(onEmit: local Function(Boolean is _v){
				invalidate();
			})
		);
	}

	local Function of SewNode is activeChild(){
		return if({ condition:current() }, { first }, { second });
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		first:applyTheme(theme: theme);
		second:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		first:setScale(scale: scale);
		second:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		first:bindDirty(cb: cb);
		second:bindDirty(cb: cb);
	}

	replace Function of Size is measure(Constraints is c){
		local Size is s1: first:measure(c: c);
		local Size is s2: second:measure(c: c);
		local Size is active: if({ condition:current() }, { s1 }, { s2 });
		desiredSize: active;
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		first:arrange(bounds: bounds);
		second:arrange(bounds: bounds);
	}

	replace Function is paint(DrawContext is ctx){
		:activeChild():paint(ctx: ctx);
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

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return :activeChild():onPointerMove(x: x, y: y);
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
}
