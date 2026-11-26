#! Package base:scrap
#! Top-level GUI toolkit container managing window lifecycle, canvas, emitter bindings,
#! theme, point scale, toolbar slot, and body.

Class of SewNode is ToolkitContainer{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Stderr],
		['base', 'sys', Process],
		['base', 'sys', Time],
		['base', 'signal', BoolEmitter],
		['base', 'signal', BoolCollector],
		['base', 'signal', TextEmitter],
		['base', 'signal', TextCollector],
		['base', 'suit', SuitWindow],
		['base', 'suit', SuitCanvas],
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

	TextEmitter is title: TextEmitter(initial: 'Suit');
	BoolEmitter is running: BoolEmitter(initial: true);
	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	Float is widthPt: 800.0;
	Float is heightPt: 600.0;
	ToolbarContainer is toolbarSlot: ToolbarContainer();
	ScrapPanel is bodyPanel: ScrapPanel();
	Boolean is hasToolbarSlot: false;
	Boolean is hasBody: false;

	replace Function is init(
		TextEmitter is title: TextEmitter(initial: 'Suit'),
		BoolEmitter is running: BoolEmitter(initial: true),
		Theme is theme: Theme(preset: 'light_grayscale'),
		Float is widthPt: 800.0,
		Float is heightPt: 600.0,
		ToolbarContainer is toolbar: ToolbarContainer(hasToolbar: false),
		ScrapPanel is body: ScrapPanel()
	){
		:title: title;
		:running: running;
		:theme: theme;
		:scale: Scale(factor: 1.0);
		:widthPt: widthPt;
		:heightPt: heightPt;
		toolbarSlot: toolbar;
		bodyPanel: body;
		hasToolbarSlot: toolbar:hasToolbar;
		hasBody: true;
		:applyTheme(theme: theme);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		:theme: theme;
		if({ hasToolbarSlot }, { toolbarSlot:applyTheme(theme: theme); });
		if({ hasBody }, { bodyPanel:applyTheme(theme: theme); });
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

	## Opens the native window, binds reactive ViewModel emitters, runs the event/render loop,
	## and disposes window & canvas resources internally on exit.
	Function is run(Int is durationMs: 0){
		local Boolean is alive: running:current();
		local String is curTitle: title:current();

		local SuitWindow is win: SuitWindow(
			title: curTitle,
			width: scale:px(pt: widthPt),
			height: scale:px(pt: heightPt),
			decorated: true,
			useVulkan: false
		);

		if({ !win:open() }, {
			Stderr():line(text: 'Failed to open window: ':concat(other: win:lastError()));
			Process():exit(status: 1);
		});

		scale: Scale(factor: win:scaleFactor());
		if({ hasToolbarSlot }, { toolbarSlot:setScale(scale: scale); });

		local Boolean is dirtyFlag: false;
		:bindDirty(cb: local Function(){ dirtyFlag: true; });
		if({ hasToolbarSlot }, { toolbarSlot:bindDirty(cb: local Function(){ dirtyFlag: true; }); });

		signalBag:track(
			slot: 'running',
			emitter: running,
			collector: BoolCollector(onEmit: local Function(){
				alive: running:current();
			})
		);
		signalBag:track(
			slot: 'title',
			emitter: title,
			collector: TextCollector(onEmit: local Function(String is nextTitle){
				curTitle: nextTitle;
			})
		);

		local Int is curW: win:width();
		local Int is curH: win:height();
		local SuitCanvas is canvas: SuitCanvas(width: curW, height: curH);
		local DrawContext is ctx: DrawContext(canvas: canvas);

		:layout(widthPx: curW, heightPx: curH);
		:paint(ctx: ctx);
		win:present(canvas: canvas);

		local Time is clock: Time();
		local Int is startMs: clock:monotonicMs();
		local Int is lastPtrX: -1;
		local Int is lastPtrY: -1;

		while({ alive && win:poll() }, {
			local Int is key: win:nextKey();
			while({ key != 0 }, {
				if({ key == 27 }, {
					running:emit(value: false);
				});
				key: win:nextKey();
			});

			if({ durationMs > 0 && (clock:monotonicMs() - startMs) >= durationMs }, {
				running:emit(value: false);
			});

			if({ alive }, {
				local Boolean is dirty: false;
				local Int is w: win:width();
				local Int is h: win:height();
				if({ w > 0 && h > 0 && (w != curW || h != curH) }, {
					curW: w;
					curH: h;
					canvas:resize(width: curW, height: curH);
					:layout(widthPx: curW, heightPx: curH);
					dirty: true;
				});

				local Int is px: win:pointerX();
				local Int is py: win:pointerY();
				if({ px != lastPtrX || py != lastPtrY }, {
					lastPtrX: px;
					lastPtrY: py;
					if({ :onPointerMove(x: px, y: py) }, {
						dirty: true;
					});
				});

				if({ win:pollClick() }, {
					if({ :onPointerClick(x: win:clickX(), y: win:clickY()) }, {
						dirty: true;
					});
				});

				if({ dirty && alive }, {
					:paint(ctx: ctx);
					win:present(canvas: canvas);
				});
			});
		});

		signalBag:clear();
		canvas:dispose();
		win:close();
	}
}
