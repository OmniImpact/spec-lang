#! Package base:scrap
#! Top-level GUI toolkit container managing theme, point scale, toolbar slot, and body.

Class of SewNode is ToolkitContainer{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', ToolbarContainer],
		['base', 'scrap', ScrapPanel]
	];

	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	ToolbarContainer is toolbarSlot: ToolbarContainer();
	ScrapPanel is bodyPanel: ScrapPanel();
	Boolean is hasToolbarSlot: false;
	Boolean is hasBody: false;

	replace Function is init(Theme is theme: Theme(preset: 'light_grayscale'), Scale is scale: Scale(factor: 1.0)){
		:theme: theme;
		:scale: scale;
		toolbarSlot: ToolbarContainer();
		bodyPanel: ScrapPanel(bgColor: theme:windowBg);
		hasToolbarSlot: false;
		hasBody: false;
	}

	## Adds a `ToolbarContainer` at the top of the toolkit workspace.
	Function is addToolbarContainer(ToolbarContainer is container){
		toolbarSlot: container;
		hasToolbarSlot: true;
	}

	## Sets the main body panel filling the remaining workspace below the toolbar.
	Function is setBody(ScrapPanel is body){
		bodyPanel: body;
		hasBody: true;
	}

	## Runs the two-pass Sew Column layout for ([widthPx], [heightPx]).
	Function is layout(Int is widthPx, Int is heightPx){
		local Column is col: Column();
		if({ hasToolbarSlot }, {
			col:addChild(child: toolbarSlot, expand: false);
		});
		if({ hasBody }, {
			col:addChild(child: bodyPanel, expand: true);
		});
		col:measure(c: Constraints(minW: widthPx, maxW: widthPx, minH: heightPx, maxH: heightPx));
		col:arrange(bounds: Rect(x: 0, y: 0, width: widthPx, height: heightPx));
		layoutBounds: Rect(x: 0, y: 0, width: widthPx, height: heightPx);
	}

	Function of Boolean is onPointerMove(Int is x, Int is y){
		if({ !hasToolbarSlot }, { return false; });
		return toolbarSlot:onPointerMove(x: x, y: y);
	}

	Function of Boolean is onPointerClick(Int is x, Int is y){
		if({ !hasToolbarSlot }, { return false; });
		return toolbarSlot:onPointerClick(x: x, y: y);
	}

	## Renders body, toolbar, and overlay popups in z-order into [ctx].
	Function is paint(DrawContext is ctx){
		if({ hasBody }, { bodyPanel:paint(ctx: ctx); });
		if({ hasToolbarSlot }, { toolbarSlot:paint(ctx: ctx); });
		if({ hasToolbarSlot }, { toolbarSlot:paintOverlay(ctx: ctx); });
	}
}
