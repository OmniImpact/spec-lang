#! Package base:scrap
#! Top-level GUI toolkit container managing window lifecycle (2D software or Vulkan 3D + 2D overlay),
#! emitter bindings, theme propagation, point scale, top toolbar, body, bottom bar, and secondary dialogs.

Class of SewNode is ToolkitContainer{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Stderr],
		['base', 'sys', Process],
		['base', 'sys', Time],
		['base', 'signal', BoolEmitter],
		['base', 'signal', BoolCollector],
		['base', 'signal', IntEmitter],
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
		['base', 'scrap', Bar],
		['base', 'scrap', ToolbarContainer],
		['base', 'scrap', ScrapPanel],
		['base', 'scrap', VulkanSurface],
		['base', 'scrap', Dialog],
		['base', 'wardrobe', FileDialog]
	];

	TextEmitter is title: TextEmitter(initial: 'Suit');
	BoolEmitter is running: BoolEmitter(initial: true);
	IntEmitter is targetFps: IntEmitter(initial: 0);
	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	Float is widthPt: 800.0;
	Float is heightPt: 600.0;
	Boolean is useVulkan: false;
	Boolean is gpuPresent: false;
	ToolbarContainer is toolbarSlot: ToolbarContainer(hasToolbar: false);
	SewNode is bodyPanel: ScrapPanel();
	VulkanSurface is vulkanBody: VulkanSurface();
	Bar is bottomBar: Bar();
	Dialog is dialog: Dialog();
	FileDialog is fileDialog: FileDialog();
	Boolean is hasToolbarSlot: false;
	Boolean is hasBody: false;
	Boolean is hasBottomBar: false;
	Boolean is hasDialog: false;
	Boolean is hasFileDialog: false;
	Boolean is isDirty: false;
	Function is onInitVulkan: local Function(VulkanSurface is s){};
	Function is onFrame: local Function(VulkanSurface is s, Int is elapsedMs, Int is width, Int is height){};
	Function is onDispose: local Function(){};

	replace Function is init(
		TextEmitter is title: TextEmitter(initial: 'Suit'),
		BoolEmitter is running: BoolEmitter(initial: true),
		IntEmitter is targetFps: IntEmitter(initial: 0),
		Theme is theme: Theme(preset: 'light_grayscale'),
		Float is widthPt: 800.0,
		Float is heightPt: 600.0,
		Boolean is useVulkan: false,
		ToolbarContainer is toolbar: ToolbarContainer(hasToolbar: false),
		SewNode is body: ScrapPanel(),
		VulkanSurface is vulkanSurface: VulkanSurface(),
		Bar is bottomBar: Bar(),
		Boolean is hasBottomBar: false,
		Dialog is dialog: Dialog(),
		Boolean is hasDialog: false,
		FileDialog is fileDialog: FileDialog(),
		Boolean is hasFileDialog: false,
		Function is onInitVulkan: local Function(VulkanSurface is s){},
		Function is onFrame: local Function(VulkanSurface is s, Int is elapsedMs, Int is width, Int is height){},
		Function is onDispose: local Function(){}
	){
		:title: title;
		:running: running;
		:targetFps: targetFps;
		:theme: theme;
		:scale: Scale(factor: 1.0);
		:widthPt: widthPt;
		:heightPt: heightPt;
		:useVulkan: useVulkan;
		:toolbarSlot: toolbar;
		:bodyPanel: body;
		:vulkanBody: vulkanSurface;
		:bottomBar: bottomBar;
		:dialog: dialog;
		:fileDialog: fileDialog;
		:hasToolbarSlot: toolbar:hasToolbar;
		:hasBody: true;
		:hasBottomBar: hasBottomBar;
		:hasDialog: hasDialog;
		:hasFileDialog: hasFileDialog;
		:onInitVulkan: onInitVulkan;
		:onFrame: onFrame;
		:onDispose: onDispose;
		:applyTheme(theme: theme);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		:theme: theme;
		if({ hasToolbarSlot }, { toolbarSlot:applyTheme(theme: theme); });
		if({ hasBody && !useVulkan }, { bodyPanel:applyTheme(theme: theme); });
		if({ hasBottomBar }, { bottomBar:applyTheme(theme: theme); });
		if({ hasDialog }, { dialog:applyTheme(theme: theme); });
		if({ hasFileDialog }, { fileDialog:applyTheme(theme: theme); });
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
		useVulkan: false;
	}

	## Runs the two-pass Sew Column layout for ([widthPx], [heightPx]).
	Function is layout(Int is widthPx, Int is heightPx){
		local Column is col: Column();
		if({ hasToolbarSlot }, {
			col:addChild(child: toolbarSlot, expand: false);
		});
		if({ hasBody }, {
			if({ useVulkan && gpuPresent }, {
				col:addChild(child: vulkanBody, expand: true);
			}, {
				col:addChild(child: bodyPanel, expand: true);
			});
		});
		if({ hasBottomBar }, {
			col:addChild(child: bottomBar, expand: false);
		});
		col:measure(c: Constraints(minW: widthPx, maxW: widthPx, minH: heightPx, maxH: heightPx));
		col:arrange(bounds: Rect(x: 0, y: 0, width: widthPx, height: heightPx));
		if({ hasBody && useVulkan && gpuPresent }, {
			local Rect is vb: vulkanBody:bounds();
			vulkanBody:setViewport(x: vb:x, y: vb:y, w: vb:width, h: vb:height);
		});
		layoutBounds: Rect(x: 0, y: 0, width: widthPx, height: heightPx);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is changed: false;
		if({ hasToolbarSlot }, {
			if({ toolbarSlot:onPointerMove(x: x, y: y) }, { changed: true; });
		});
		if({ hasBody && !useVulkan }, {
			if({ bodyPanel:onPointerMove(x: x, y: y) }, { changed: true; });
		});
		return changed;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ hasToolbarSlot }, {
			if({ toolbarSlot:onPointerClick(x: x, y: y) }, { return true; });
		});
		if({ hasBody && !useVulkan }, {
			return bodyPanel:onPointerClickMod(x: x, y: y, mods: mods);
		});
		return false;
	}

	## Renders body (when software 2D or 2D-over-Vulkan), bars, and overlay popups in z-order into [ctx].
	replace Function is paint(DrawContext is ctx){
		if({ useVulkan && gpuPresent }, {
			ctx:clearTransparent();
		}, {
			if({ hasBody }, { bodyPanel:paint(ctx: ctx); });
		});
		if({ hasBottomBar }, { bottomBar:paint(ctx: ctx); });
		if({ hasToolbarSlot }, { toolbarSlot:paint(ctx: ctx); });
		if({ hasToolbarSlot }, { toolbarSlot:paintOverlay(ctx: ctx); });
	}

	## Opens the native window, binds reactive ViewModel emitters, runs the event/render loop,
	## and disposes window & canvas resources internally on exit.
	Function is run(Int is durationMs: 0){
		local String is curTitle: title:current();

		local SuitWindow is win: SuitWindow(
			title: curTitle,
			width: scale:px(pt: widthPt),
			height: scale:px(pt: heightPt),
			decorated: true,
			useVulkan: true
		);

		if({ !win:open() }, {
			Stderr():line(text: 'Failed to open window: ':concat(other: win:lastError()));
			Process():exit(status: 1);
		});

		gpuPresent: vulkanBody:attach(window: win);
		if({ gpuPresent }, {
			if({ useVulkan }, {
				local Function is initVkCb: onInitVulkan;
				initVkCb(vulkanBody);
			});
		}, {
			win:close();
			useVulkan: false;
			win: SuitWindow(
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
		});

		scale: Scale(factor: win:scaleFactor());
		if({ hasToolbarSlot }, { toolbarSlot:setScale(scale: scale); });
		if({ hasBody && !useVulkan }, { bodyPanel:setScale(scale: scale); });
		if({ hasBottomBar }, { bottomBar:setScale(scale: scale); });
		if({ hasDialog }, { dialog:setScale(scale: scale); });
		if({ hasFileDialog }, { fileDialog:setScale(scale: scale); });

		:isDirty: false;
		:bindDirty(cb: local Function(){ :isDirty: true; });
		if({ hasToolbarSlot }, { toolbarSlot:bindDirty(cb: local Function(){ :isDirty: true; }); });
		if({ hasBody && !useVulkan }, { bodyPanel:bindDirty(cb: local Function(){ :isDirty: true; }); });
		if({ hasBottomBar }, { bottomBar:bindDirty(cb: local Function(){ :isDirty: true; }); });

		signalBag:track(
			slot: 'running',
			emitter: running,
			collector: running:collect(onEmit: local Function(){
				:isDirty: true;
			})
		);
		signalBag:track(
			slot: 'title',
			emitter: title,
			collector: title:collect(onEmit: local Function(String is nextTitle){
				win:setTitle(title: nextTitle);
			})
		);

		local Int is curW: win:width();
		local Int is curH: win:height();
		local SuitCanvas is canvas: SuitCanvas(width: curW, height: curH);
		local DrawContext is ctx: DrawContext(canvas: canvas);

		:layout(widthPx: curW, heightPx: curH);
		:paint(ctx: ctx);
		if({ gpuPresent }, {
			vulkanBody:setOverlay(canvas: canvas);
			if({ !useVulkan }, {
				vulkanBody:presentOverlay(width: curW, height: curH);
			});
		}, {
			win:present(canvas: canvas);
		});

		local Time is clock: Time();
		local Int is startMs: clock:monotonicMs();
		local Int is lastPtrX: -1;
		local Int is lastPtrY: -1;
		local Boolean is wasPtrDown: false;
		local Boolean is closedByWm: false;

		while({ running:current() }, {
			local Int is loopStartNs: clock:monotonicNs();
			if({ !win:poll() }, {
				closedByWm: true;
				running:emit(value: false);
			});

			local Int is curMods: win:mods();
			if({ running:current() }, {
				local Int is key: win:nextKey();
				while({ key != 0 }, {
					if({ key == 27 }, {
						running:emit(value: false);
					}, {
						if({ hasBody && !useVulkan }, {
							if({ bodyPanel:onKey(key: key, mods: curMods) }, {
								:isDirty: true;
							}, {
								if({ key == 1001 }, {
									if({ bodyPanel:onScroll(deltaY: -15) }, { :isDirty: true; });
								});
								if({ key == 1002 }, {
									if({ bodyPanel:onScroll(deltaY: 15) }, { :isDirty: true; });
								});
								if({ key == 1003 }, {
									if({ bodyPanel:onScrollX(deltaX: -15) }, { :isDirty: true; });
								});
								if({ key == 1004 }, {
									if({ bodyPanel:onScrollX(deltaX: 15) }, { :isDirty: true; });
								});
								if({ key == 1007 }, {
									if({ bodyPanel:onScroll(deltaY: -80) }, { :isDirty: true; });
								});
								if({ key == 1008 }, {
									if({ bodyPanel:onScroll(deltaY: 80) }, { :isDirty: true; });
								});
							});
						});
					});
					key: win:nextKey();
				});

				local Int is cp: win:nextChar();
				while({ cp != 0 }, {
					if({ hasBody && !useVulkan && cp >= 32 }, {
						if({ bodyPanel:onText(ch: String:fromCodePoint(code: cp), mods: curMods) }, {
							:isDirty: true;
						});
					});
					cp: win:nextChar();
				});
			});

			local Int is elapsedMs: clock:monotonicMs() - startMs;
			if({ durationMs > 0 && elapsedMs >= durationMs }, {
				running:emit(value: false);
			});

			if({ running:current() }, {
				if({ hasDialog }, {
					dialog:poll();
				});
				if({ hasFileDialog }, {
					fileDialog:poll();
				});

				local Int is w: win:width();
				local Int is h: win:height();
				if({ w > 0 && h > 0 && (w != curW || h != curH) }, {
					curW: w;
					curH: h;
					canvas:resize(width: curW, height: curH);
					:layout(widthPx: curW, heightPx: curH);
					:isDirty: true;
				});

				local Int is sy: win:pollScrollY();
				if({ sy != 0 && hasBody && !useVulkan }, {
					if({ (curMods & 1) != 0 }, {
						if({ bodyPanel:onScrollX(deltaX: sy) }, {
							:isDirty: true;
						});
					}, {
						if({ bodyPanel:onScroll(deltaY: sy) }, {
							:isDirty: true;
						});
					});
				});

				local Int is sx: win:pollScrollX();
				if({ sx != 0 && hasBody && !useVulkan }, {
					if({ bodyPanel:onScrollX(deltaX: sx) }, {
						:isDirty: true;
					});
				});

				local Boolean is ptrDown: win:pointerDown();
				local Int is px: win:pointerX();
				local Int is py: win:pointerY();
				if({ px != lastPtrX || py != lastPtrY }, {
					lastPtrX: px;
					lastPtrY: py;
					if({ ptrDown && hasBody && !useVulkan }, {
						if({ bodyPanel:onPointerDrag(x: px, y: py, mods: curMods) }, {
							:isDirty: true;
						});
					});
					if({ :onPointerMove(x: px, y: py) }, {
						:isDirty: true;
					});
				});
				if({ !ptrDown && wasPtrDown && hasBody && !useVulkan }, {
					if({ bodyPanel:onPointerUp(x: px, y: py) }, {
						:isDirty: true;
					});
				});
				wasPtrDown: ptrDown;

				if({ win:pollClick() }, {
					if({ :onPointerClickMod(x: win:clickX(), y: win:clickY(), mods: curMods) }, {
						:isDirty: true;
					});
				});

				if({ hasBody && !useVulkan }, {
					if({ bodyPanel:tick(nowMs: clock:monotonicMs()) }, {
						:isDirty: true;
					});
				});

				if({ isDirty && running:current() }, {
					:isDirty: false;
					:layout(widthPx: curW, heightPx: curH);
					:paint(ctx: ctx);
					if({ gpuPresent }, {
						vulkanBody:setOverlay(canvas: canvas);
						if({ !useVulkan }, {
							vulkanBody:presentOverlay(width: curW, height: curH);
						});
					}, {
						win:present(canvas: canvas);
					});
				});

				if({ useVulkan && gpuPresent && running:current() }, {
					local Function is frameCb: onFrame;
					frameCb(vulkanBody, elapsedMs, curW, curH);
					local Int is fpsCap: targetFps:current();
					if({ fpsCap > 0 }, {
						local Int is budgetNs: 1000000000 / fpsCap;
						clock:sleepUntilNs(targetNs: loopStartNs + budgetNs);
					});
				}, {
					if({ running:current() }, {
						clock:sleepUntilNs(targetNs: loopStartNs + 8000000);
					});
				});
			});
		});

		local Function is dispCb: onDispose;
		dispCb();
		if({ hasBottomBar }, { bottomBar:dispose(); });
		if({ hasDialog }, { dialog:dispose(); });
		if({ hasFileDialog }, { fileDialog:dispose(); });
		signalBag:clear();
		canvas:dispose();
		if({ !gpuPresent || !closedByWm }, {
			if({ gpuPresent }, { vulkanBody:dispose(); });
			win:close();
		});
	}
}
