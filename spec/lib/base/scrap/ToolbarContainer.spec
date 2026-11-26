#! Package base:scrap
#! Container owning a `Toolbar` and accepting pushed `ToolbarConfig` + callbacks.

Class of SewNode is ToolbarContainer{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', Toolbar],
		['base', 'scrap', ToolbarConfig],
		['base', 'scrap', MenuConfig],
		['base', 'scrap', MenuItemConfig]
	];

	Toolbar is toolbar: Toolbar();
	Boolean is hasToolbar: false;

	replace Function is init(Toolbar is toolbar: Toolbar(), Boolean is hasToolbar: true){
		:toolbar: toolbar;
		:hasToolbar: hasToolbar;
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		if({ hasToolbar }, { toolbar:applyTheme(theme: theme); });
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		if({ hasToolbar }, { toolbar:bindDirty(cb: cb); });
	}

	Function is setScale(Scale is scale){
		if({ hasToolbar }, { toolbar:setScale(scale: scale); });
	}

	## Attaches a `Toolbar` widget to this container.
	Function is addToolbar(Toolbar is toolbar){
		:toolbar: toolbar;
		hasToolbar: true;
	}

	## Pushes [config] into the toolbar and binds [onQuit] to any `'quit'` menu item.
	Function is pushConfig(ToolbarConfig is config, Function is onQuit: local Function(){}){
		times(count: config:menus:length(), worker: local Function(Int is mi){
			local MenuConfig is m: config:menus:get(index: mi);
			times(count: m:items:length(), worker: local Function(Int is ii){
				local MenuItemConfig is item: m:items:get(index: ii);
				if({ item:id == 'quit' }, {
					item:onClick: onQuit;
				});
			});
		});
		toolbar:setConfig(config: config);
	}

	replace Function of Size is measure(Constraints is c){
		if({ !hasToolbar }, {
			desiredSize: Size(width: c:clampW(w: 0), height: c:clampH(h: 0));
			return desiredSize;
		});
		desiredSize: toolbar:measure(c: c);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		if({ hasToolbar }, {
			toolbar:arrange(bounds: bounds);
		});
	}

	Function of Boolean is onPointerMove(Int is x, Int is y){
		if({ !hasToolbar }, { return false; });
		return toolbar:onPointerMove(x: x, y: y);
	}

	Function of Boolean is onPointerClick(Int is x, Int is y){
		if({ !hasToolbar }, { return false; });
		return toolbar:onPointerClick(x: x, y: y);
	}

	Function is paint(DrawContext is ctx){
		if({ hasToolbar }, { toolbar:paint(ctx: ctx); });
	}

	Function is paintOverlay(DrawContext is ctx){
		if({ hasToolbar }, { toolbar:paintOverlay(ctx: ctx); });
	}
}
