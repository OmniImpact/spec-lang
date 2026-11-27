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
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', BoolCollector],
		['base', 'signal', IntEmitter],
		['base', 'signal', TextEmitter],
		['base', 'signal', TextCollector],
		['base', 'suit', SuitWindow],
		['base', 'suit', SuitCanvas],
		['base', 'sew', SewNode],
		['base', 'sew', FocusNav],
		['base', 'sew', Column],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', CursorShape],
		['base', 'fabric', Color],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', DragDropState],
		['base', 'fabric', 'svg', SvgRenderer],
		['base', 'fabric', 'svg', SvgBitmap],
		['base', 'scrap', Bar],
		['base', 'scrap', Tooltip],
		['base', 'scrap', 'menu', MenuContext],
		['base', 'scrap', 'tab', TabBar],
		['base', 'scrap', 'toolbar', ToolbarContainer],
		['base', 'scrap', ScrapPanel],
		['base', 'scrap', VulkanSurface],
		['base', 'scrap', Dialog],
		['base', 'wardrobe', 'file', FileDialog]
	];

	TextEmitter is title: TextEmitter(initial: 'Suit');
	String is iconSvg: '';
	BoolEmitter is running: BoolEmitter(initial: true);
	IntEmitter is targetFps: IntEmitter(initial: 0);
	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	Float is uiZoom: 1.0;
	Float is widthPt: 800.0;
	Float is heightPt: 600.0;
	Boolean is useVulkan: false;
	Boolean is gpuPresent: false;
	ToolbarContainer is toolbarSlot: ToolbarContainer(hasToolbar: false);
	TabBar is tabBar: TabBar();
	SewNode is bodyPanel: ScrapPanel();
	VulkanSurface is vulkanBody: VulkanSurface();
	Bar is bottomBar: Bar();
	Dialog is dialog: Dialog();
	Array of Dialog is extraDialogs: Array();
	FileDialog is fileDialog: FileDialog();
	MenuContext is contextMenu: MenuContext();
	Boolean is hasToolbarSlot: false;
	Boolean is hasTabBar: false;
	Boolean is hasBody: false;
	Boolean is hasBottomBar: false;
	Boolean is hasDialog: false;
	Boolean is hasFileDialog: false;
	Boolean is isDirty: false;
	Int is loopW: 0;
	Int is loopH: 0;
	Int is lastPtrX: -1;
	Int is lastPtrY: -1;
	Boolean is wasPtrDown: false;
	Int is ptrCaptureTarget: 0;
	Boolean is lastClickInOverlay: false;
	Boolean is closedByWm: false;
	Int is idleFrames: 0;
	Int is windowAlphaPct: 100;
	SuitWindow is activeWin: SuitWindow();
	Function is onInitVulkan: local Function(VulkanSurface is s){};
	Function is onFrame: local Function(VulkanSurface is s, Int is elapsedMs, Int is width, Int is height){};
	Function is onDispose: local Function(){};
	Function of Boolean is onAppKey: local Function of Boolean(Int is key, Int is mods){ false };

	replace Function is init(
		TextEmitter is title: TextEmitter(initial: 'Suit'),
		String is iconSvg: '',
		BoolEmitter is running: BoolEmitter(initial: true),
		IntEmitter is targetFps: IntEmitter(initial: 0),
		Theme is theme: Theme(preset: 'light_grayscale'),
		Float is widthPt: 800.0,
		Float is heightPt: 600.0,
		Boolean is useVulkan: false,
		ToolbarContainer is toolbar: ToolbarContainer(hasToolbar: false),
		TabBar is tabBar: TabBar(),
		Boolean is hasTabBar: false,
		SewNode is body: ScrapPanel(),
		VulkanSurface is vulkanSurface: VulkanSurface(),
		Bar is bottomBar: Bar(),
		Boolean is hasBottomBar: false,
		Dialog is dialog: Dialog(),
		Boolean is hasDialog: false,
		FileDialog is fileDialog: FileDialog(),
		Boolean is hasFileDialog: false,
		MenuContext is contextMenu: MenuContext(),
		Function is onInitVulkan: local Function(VulkanSurface is s){},
		Function is onFrame: local Function(VulkanSurface is s, Int is elapsedMs, Int is width, Int is height){},
		Function is onDispose: local Function(){},
		Function of Boolean is onKey: local Function of Boolean(Int is key, Int is mods){ false }
	){
		:title: title;
		:iconSvg: iconSvg;
		:running: running;
		:targetFps: targetFps;
		:theme: theme;
		:scale: Scale(factor: 1.0);
		:widthPt: widthPt;
		:heightPt: heightPt;
		:useVulkan: useVulkan;
		:toolbarSlot: toolbar;
		:tabBar: tabBar;
		:bodyPanel: body;
		:vulkanBody: vulkanSurface;
		:bottomBar: bottomBar;
		if({ hasBottomBar }, { :bottomBar:borderSide: DockSide:TOP; });
		:dialog: dialog;
		:fileDialog: fileDialog;
		:contextMenu: contextMenu;
		:hasToolbarSlot: toolbar:hasToolbar;
		:hasTabBar: hasTabBar;
		:hasBody: true;
		:hasBottomBar: hasBottomBar;
		:hasDialog: hasDialog;
		:hasFileDialog: hasFileDialog;
		:onInitVulkan: onInitVulkan;
		:onFrame: onFrame;
		:onDispose: onDispose;
		:onAppKey: onKey;
		:applyTheme(theme: theme);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		:theme: theme;
		if({ hasToolbarSlot }, { toolbarSlot:applyTheme(theme: theme); });
		if({ hasTabBar }, { tabBar:applyTheme(theme: theme); });
		if({ hasBody && !useVulkan }, { bodyPanel:applyTheme(theme: theme); });
		if({ hasBottomBar }, { bottomBar:applyTheme(theme: theme); });
		if({ hasDialog }, { dialog:applyTheme(theme: theme); });
		if({ hasFileDialog }, { fileDialog:applyTheme(theme: theme); });
		contextMenu:applyTheme(theme: theme);
	}

	## Updates the live theme across the window and all child widgets and schedules a redraw.
	Function is setTheme(Theme is nextTheme){
		:applyTheme(theme: nextTheme);
		local Int is ei: 0;
		while({ ei < extraDialogs:length() }, {
			extraDialogs:get(index: ei):applyTheme(theme: nextTheme);
			ei: ei + 1;
		});
		:isDirty: true;
	}

	## Sets the window background opacity percentage (0..100).
	Function is setWindowAlphaPct(Int is pct){
		local Int is clamped: pct;
		if({ clamped < 0 }, { clamped: 0; });
		if({ clamped > 100 }, { clamped: 100; });
		if({ clamped != windowAlphaPct }, {
			windowAlphaPct: clamped;
			:isDirty: true;
		});
	}

	Function is addDialog(Dialog is d){
		d:applyTheme(theme: theme);
		d:setScale(scale: scale);
		extraDialogs:add(item: d);
	}

	local Function is applyScaleToChildren(){
		if({ hasToolbarSlot }, { toolbarSlot:setScale(scale: scale); });
		if({ hasTabBar }, { tabBar:setScale(scale: scale); });
		if({ hasBody && !useVulkan }, { bodyPanel:setScale(scale: scale); });
		if({ hasBottomBar }, { bottomBar:setScale(scale: scale); });
		if({ hasDialog }, { dialog:setScale(scale: scale); });
		local Int is ei: 0;
		while({ ei < extraDialogs:length() }, {
			extraDialogs:get(index: ei):setScale(scale: scale);
			ei: ei + 1;
		});
		if({ hasFileDialog }, { fileDialog:setScale(scale: scale); });
		contextMenu:setScale(scale: scale);
	}

	Function is setZoom(Float is zoomFactor){
		local Float is z: if({ zoomFactor < 0.5 }, { 0.5 }, { if({ zoomFactor > 2.5 }, { 2.5 }, { zoomFactor }) });
		:uiZoom: z;
		local Float is baseFactor: if({ activeWin:isOpen() }, { activeWin:scaleFactor() }, { 1.0 });
		:scale: Scale(factor: baseFactor * uiZoom);
		:applyScaleToChildren();
		:isDirty: true;
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
		if({ hasTabBar }, {
			col:addChild(child: tabBar, expand: false);
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

	local Function is clearHoverBelow(Int is startLayer){
		if({ startLayer <= 1 && hasToolbarSlot }, { toolbarSlot:clearHover(); });
		if({ startLayer <= 2 && hasTabBar }, { tabBar:clearHover(); });
		if({ startLayer <= 3 && hasBottomBar }, { bottomBar:clearHover(); });
		if({ startLayer <= 4 && hasBody && !useVulkan }, { bodyPanel:clearHover(); });
	}

	String is activeTooltip: '';
	Boolean is tooltipVisible: false;
	Int is tooltipHoverStartMs: 0;
	Int is lastCursorKind: 0;
	Time is tipClock: Time();

	local Function of Int is cursorKindOf(CursorShape is shape){
		if({ shape == CursorShape:TEXT }, { return 1; });
		if({ shape == CursorShape:POINTER }, { return 2; });
		if({ shape == CursorShape:EW_RESIZE }, { return 3; });
		if({ shape == CursorShape:NS_RESIZE }, { return 4; });
		return 0;
	}

	local Function of CursorShape is resolveCursorAt(Int is x, Int is y){
		if({ contextMenu:isOpen }, { return CursorShape:DEFAULT; });
		if({ hasToolbarSlot && toolbarSlot:blocksPointerAt(x: x, y: y) }, { return CursorShape:POINTER; });
		if({ hasTabBar && tabBar:blocksPointerAt(x: x, y: y) }, { return CursorShape:POINTER; });
		if({ hasBottomBar && bottomBar:blocksPointerAt(x: x, y: y) }, { return bottomBar:cursorAt(x: x, y: y); });
		if({ hasBody && !useVulkan }, { return bodyPanel:cursorAt(x: x, y: y); });
		return CursorShape:DEFAULT;
	}

	local Function of String is resolveTooltipAt(Int is x, Int is y){
		if({ contextMenu:isOpen }, { return ''; });
		if({ hasToolbarSlot }, {
			local String is t1: toolbarSlot:tooltipAt(x: x, y: y);
			if({ t1 != '' }, { return t1; });
			if({ toolbarSlot:blocksPointerAt(x: x, y: y) }, { return ''; });
		});
		if({ hasTabBar }, {
			local String is t2: tabBar:tooltipAt(x: x, y: y);
			if({ t2 != '' }, { return t2; });
			if({ tabBar:blocksPointerAt(x: x, y: y) }, { return ''; });
		});
		if({ hasBottomBar }, {
			local String is t3: bottomBar:tooltipAt(x: x, y: y);
			if({ t3 != '' }, { return t3; });
			if({ bottomBar:blocksPointerAt(x: x, y: y) }, { return ''; });
		});
		if({ hasBody && !useVulkan }, {
			return bodyPanel:tooltipAt(x: x, y: y);
		});
		return '';
	}

	local Function of Array of SewNode is collectAllFocusables(){
		local Array of SewNode is out: Array();
		if({ hasToolbarSlot }, { toolbarSlot:collectFocusables(out: out); });
		if({ hasTabBar }, { tabBar:collectFocusables(out: out); });
		if({ hasBody && !useVulkan }, { bodyPanel:collectFocusables(out: out); });
		if({ hasBottomBar }, { bottomBar:collectFocusables(out: out); });
		return out;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		if({ contextMenu:isOpen }, {
			local Boolean is cmMoved: contextMenu:handlePointerMove(x: x, y: y, viewW: loopW, viewH: loopH);
			if({ contextMenu:blocksPointerAt(x: x, y: y) }, {
				:clearHoverBelow(startLayer: 1);
				return cmMoved;
			});
		});
		if({ hasBody && !useVulkan && bodyPanel:onOverlayPointerMove(x: x, y: y) }, {
			:clearHoverBelow(startLayer: 1);
			local String is nextTipOvl: :resolveTooltipAt(x: x, y: y);
			:activeTooltip: nextTipOvl;
			if({ tooltipVisible }, {
				:tooltipVisible: false;
				:tooltipHoverStartMs: tipClock:monotonicMs();
			}, {
				:tooltipHoverStartMs: tipClock:monotonicMs();
			});
			return true;
		});
		local Boolean is changed: false;
		local Boolean is blocked: false;
		if({ hasToolbarSlot }, {
			if({ !blocked }, {
				if({ toolbarSlot:onPointerMove(x: x, y: y) }, { changed: true; });
				if({ toolbarSlot:blocksPointerAt(x: x, y: y) }, { blocked: true; });
			}, {
				toolbarSlot:clearHover();
			});
		});
		if({ hasTabBar }, {
			if({ !blocked }, {
				if({ tabBar:onPointerMove(x: x, y: y) }, { changed: true; });
				if({ tabBar:blocksPointerAt(x: x, y: y) }, { blocked: true; });
			}, {
				tabBar:clearHover();
			});
		});
		if({ hasBottomBar }, {
			if({ !blocked }, {
				if({ bottomBar:onPointerMove(x: x, y: y) }, { changed: true; });
				if({ bottomBar:blocksPointerAt(x: x, y: y) }, { blocked: true; });
			}, {
				bottomBar:clearHover();
			});
		});
		if({ hasBody && !useVulkan }, {
			if({ !blocked }, {
				if({ bodyPanel:onPointerMove(x: x, y: y) }, { changed: true; });
			}, {
				bodyPanel:clearHover();
			});
		});
		local String is nextTip: :resolveTooltipAt(x: x, y: y);
		:activeTooltip: nextTip;
		if({ tooltipVisible }, {
			:tooltipVisible: false;
			changed: true;
		});
		:tooltipHoverStartMs: tipClock:monotonicMs();
		return changed;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		:lastClickInOverlay: false;
		if({ contextMenu:isOpen }, {
			:lastClickInOverlay: true;
			return contextMenu:handlePointerClick(x: x, y: y, viewW: loopW, viewH: loopH);
		});
		if({ hasBody && !useVulkan && bodyPanel:onOverlayPointerClickMod(x: x, y: y, mods: mods) }, {
			:lastClickInOverlay: true;
			return true;
		});
		if({ hasBody && !useVulkan }, {
			if({ bodyPanel:closePopupsOutside(x: x, y: y) }, {
				:isDirty: true;
			});
		});
		if({ hasToolbarSlot }, {
			if({ toolbarSlot:onPointerClick(x: x, y: y) }, { return true; });
			if({ toolbarSlot:blocksPointerAt(x: x, y: y) }, { return true; });
		});
		if({ hasTabBar }, {
			if({ tabBar:onPointerClickMod(x: x, y: y, mods: mods) }, { return true; });
			if({ tabBar:blocksPointerAt(x: x, y: y) }, { return true; });
		});
		if({ hasBottomBar }, {
			if({ bottomBar:onPointerClickMod(x: x, y: y, mods: mods) }, { return true; });
			if({ bottomBar:blocksPointerAt(x: x, y: y) }, { return true; });
		});
		if({ hasBody && !useVulkan }, {
			if({ bodyPanel:closePopupsOutside(x: x, y: y) }, {
				:isDirty: true;
			});
			return bodyPanel:onPointerClickMod(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		if({ contextMenu:isOpen }, {
			contextMenu:close();
		});
		if({ hasTabBar }, {
			if({ tabBar:onRightClickMod(x: x, y: y, mods: mods) }, { return true; });
		});
		if({ hasBody && !useVulkan }, {
			return bodyPanel:onRightClickMod(x: x, y: y, mods: mods);
		});
		return false;
	}

	## Renders body (when software 2D or 2D-over-Vulkan), bars, and overlay popups in z-order into [ctx].
	replace Function is paint(DrawContext is ctx){
		if({ useVulkan && gpuPresent }, {
			ctx:clearTransparent();
		}, {
			local Int is alphaByte: (windowAlphaPct * 255) / 100;
			local Color is baseC: Color:fromArgb(argb: theme:windowBg);
			local Int is bgCol: Color(
				r: (baseC:red() * alphaByte) / 255,
				g: (baseC:green() * alphaByte) / 255,
				b: (baseC:blue() * alphaByte) / 255,
				a: alphaByte
			):toArgb();
			ctx:canvas:fillRect(x: 0, y: 0, w: loopW, h: loopH, color: bgCol);
			if({ hasBody }, { bodyPanel:paint(ctx: ctx); });
		});
		if({ hasTabBar }, { tabBar:paint(ctx: ctx); });
		if({ hasBottomBar }, { bottomBar:paint(ctx: ctx); });
		if({ hasToolbarSlot }, { toolbarSlot:paint(ctx: ctx); });
		if({ hasToolbarSlot }, { toolbarSlot:paintOverlay(ctx: ctx); });
		if({ hasBody && !useVulkan }, { bodyPanel:paintOverlay(ctx: ctx); });
		contextMenu:paint(ctx: ctx);
		DragDropState:shared:paintOverlay(ctx: ctx, theme: theme, scale: scale, winW: loopW, winH: loopH);
		if({ tooltipVisible && activeTooltip != '' && lastPtrX >= 0 && lastPtrY >= 0 }, {
			Tooltip:shared:paint(ctx: ctx, theme: theme, scale: scale, text: activeTooltip, ptrX: lastPtrX, ptrY: lastPtrY, winW: loopW, winH: loopH);
		});
	}

	## Writes [text] to the native window system clipboard.
	Function is setClipboard(String is text){
		activeWin:setClipboard(text: text);
	}

	## Reads UTF-8 text from the native window system clipboard.
	Function of String is getClipboard(){
		return activeWin:getClipboard();
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
			useVulkan: useVulkan
		);

		if({ !win:open() }, {
			Stderr():line(text: 'Failed to open window: ':concat(other: win:lastError()));
			Process():exit(status: 1);
		});
		activeWin: win;

		gpuPresent: false;
		if({ useVulkan }, {
			gpuPresent: vulkanBody:attach(window: win);
			if({ gpuPresent }, {
				local Function is initVkCb: onInitVulkan;
				initVkCb(vulkanBody);
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
				activeWin: win;
			});
		});

		scale: Scale(factor: win:scaleFactor() * uiZoom);
		if({ iconSvg != '' }, {
			local Int is iconPx: scale:px(pt: 32.0);
			if({ iconPx < 32 }, { iconPx: 32; });
			local SvgBitmap is iconBmp: SvgRenderer:shared:rasterize(svgSrc: iconSvg, widthPx: iconPx, heightPx: iconPx);
			if({ iconBmp:argbAddr != 0 }, {
				win:setIcon(pixelsAddr: iconBmp:argbAddr, width: iconBmp:width, height: iconBmp:height);
			});
		});
		:applyScaleToChildren();

		:isDirty: false;
		:bindDirty(cb: local Function(){ :isDirty: true; });
		if({ hasToolbarSlot }, { toolbarSlot:bindDirty(cb: local Function(){ :isDirty: true; }); });
		if({ hasTabBar }, { tabBar:bindDirty(cb: local Function(){ :isDirty: true; }); });
		if({ hasBody && !useVulkan }, { bodyPanel:bindDirty(cb: local Function(){ :isDirty: true; }); });
		if({ hasBottomBar }, { bottomBar:bindDirty(cb: local Function(){ :isDirty: true; }); });
		contextMenu:bindDirty(cb: local Function(){ :isDirty: true; });

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

		loopW: win:width();
		loopH: win:height();
		local SuitCanvas is canvas: SuitCanvas(width: loopW, height: loopH);
		local DrawContext is ctx: DrawContext(canvas: canvas);

		:layout(widthPx: loopW, heightPx: loopH);
		:paint(ctx: ctx);
		if({ gpuPresent }, {
			vulkanBody:setOverlay(canvas: canvas);
			if({ !useVulkan }, {
				vulkanBody:presentOverlay(width: loopW, height: loopH);
			});
		}, {
			win:present(canvas: canvas);
		});

		local Time is clock: Time();
		local Int is startMs: clock:monotonicMs();
		lastPtrX: -1;
		lastPtrY: -1;
		wasPtrDown: false;
		activeTooltip: '';
		tooltipVisible: false;
		tooltipHoverStartMs: 0;
		lastCursorKind: 0;
		ptrCaptureTarget: 0;
		closedByWm: false;
		idleFrames: 0;

		while({ running:current() }, {
			:stepLoopFrame(win: win, canvas: canvas, ctx: ctx, clock: clock, startMs: startMs, durationMs: durationMs);
		});

		local Function is dispCb: onDispose;
		dispCb();
		if({ hasBottomBar }, { bottomBar:dispose(); });
		if({ hasDialog }, { dialog:dispose(); });
		local Int is ei: 0;
		while({ ei < extraDialogs:length() }, {
			extraDialogs:get(index: ei):dispose();
			ei: ei + 1;
		});
		if({ hasFileDialog }, { fileDialog:dispose(); });
		signalBag:clear();
		canvas:dispose();
		if({ !gpuPresent || !closedByWm }, {
			if({ gpuPresent }, { vulkanBody:dispose(); });
			win:close();
		});
	}

	local Function is stepLoopFrame(SuitWindow is win, SuitCanvas is canvas, DrawContext is ctx, Time is clock, Int is startMs, Int is durationMs){
		local Int is loopStartNs: clock:monotonicNs();
		local Int is pollWaitMs: 0;
		if({ !(useVulkan && gpuPresent) && !isDirty }, {
			if({ idleFrames < 4 }, {
				pollWaitMs: 16;
			}, {
			if({ idleFrames < 10 }, {
				pollWaitMs: 50;
			}, {
				pollWaitMs: 100;
			}); });
			local Boolean is anyDialogOpen: (hasDialog && dialog:isShown) || (hasFileDialog && fileDialog:isShown);
			local Int is odi: 0;
			while({ !anyDialogOpen && odi < extraDialogs:length() }, {
				if({ extraDialogs:get(index: odi):isShown }, { anyDialogOpen: true; });
				odi: odi + 1;
			});
			if({ anyDialogOpen && pollWaitMs > 16 }, {
				pollWaitMs: 16;
			});
		});
		if({ durationMs > 0 }, {
			local Int is remMs: durationMs - (clock:monotonicMs() - startMs);
			if({ remMs <= 0 }, {
				pollWaitMs: 0;
			}, {
			if({ pollWaitMs > remMs }, {
				pollWaitMs: remMs;
			}); });
		});
		if({ !win:pollTimeout(timeoutMs: pollWaitMs) }, {
			closedByWm: true;
			running:emit(value: false);
		});

		local Boolean is hadActivity: isDirty;
		local Int is curMods: win:mods();
		if({ running:current() }, {
			local Int is key: win:nextKey();
			while({ key != 0 }, {
				hadActivity: true;
				if({ key == 27 }, {
					if({ contextMenu:isOpen }, {
						contextMenu:close();
						:isDirty: true;
					}, {
						running:emit(value: false);
					});
				}, {
					local Function of Boolean is appKeyFn: onAppKey;
					if({ appKeyFn(key, curMods) }, {
						:isDirty: true;
					}, {
						local Boolean is handledKey: false;
						if({ hasBody && !useVulkan && bodyPanel:onKey(key: key, mods: curMods) }, {
							handledKey: true;
							:isDirty: true;
						});
						if({ !handledKey && hasToolbarSlot && toolbarSlot:onKey(key: key, mods: curMods) }, {
							handledKey: true;
							:isDirty: true;
						});
						if({ !handledKey && hasTabBar && tabBar:onKey(key: key, mods: curMods) }, {
							handledKey: true;
							:isDirty: true;
						});
						if({ !handledKey && hasBottomBar && bottomBar:onKey(key: key, mods: curMods) }, {
							handledKey: true;
							:isDirty: true;
						});
						if({ !handledKey && key == 9 }, {
							if({ FocusNav:shared:stepTab(focusables: :collectAllFocusables(), reverse: (curMods & 1) != 0) }, {
								handledKey: true;
								:isDirty: true;
							});
						});
						if({ !handledKey && hasBody && !useVulkan }, {
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
				hadActivity: true;
				if({ cp >= 32 }, {
					local String is ch: String:fromCodePoint(code: cp);
					local Boolean is handledText: false;
					if({ hasBody && !useVulkan && bodyPanel:onText(ch: ch, mods: curMods) }, {
						handledText: true;
						:isDirty: true;
					});
					if({ !handledText && hasToolbarSlot && toolbarSlot:onText(ch: ch, mods: curMods) }, {
						handledText: true;
						:isDirty: true;
					});
					if({ !handledText && hasTabBar && tabBar:onText(ch: ch, mods: curMods) }, {
						handledText: true;
						:isDirty: true;
					});
					if({ !handledText && hasBottomBar && bottomBar:onText(ch: ch, mods: curMods) }, {
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
				if({ dialog:poll() }, { hadActivity: true; });
			});
			local Int is edi: 0;
			while({ edi < extraDialogs:length() }, {
				if({ extraDialogs:get(index: edi):poll() }, { hadActivity: true; });
				edi: edi + 1;
			});
			if({ hasFileDialog }, {
				if({ fileDialog:poll() }, { hadActivity: true; });
			});

			local Int is w: win:width();
			local Int is h: win:height();
			if({ w > 0 && h > 0 && (w != loopW || h != loopH) }, {
				hadActivity: true;
				loopW: w;
				loopH: h;
				canvas:resize(width: loopW, height: loopH);
				:isDirty: true;
			});

			local Int is sy: win:pollScrollY();
			if({ sy != 0 && hasBody && !useVulkan }, {
				hadActivity: true;
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
				hadActivity: true;
				if({ bodyPanel:onScrollX(deltaX: sx) }, {
					:isDirty: true;
				});
			});

			local Boolean is ptrDown: win:pointerDown();
			local Int is px: win:pointerX();
			local Int is py: win:pointerY();
			if({ ptrDown && !wasPtrDown }, {
				hadActivity: true;
				if({ DragDropState:shared:active }, {
					DragDropState:shared:finishDrag();
					:isDirty: true;
				});
				ptrCaptureTarget: 0;
				if({ !contextMenu:isOpen }, {
					if({ hasToolbarSlot && px >= toolbarSlot:bounds():x && px < toolbarSlot:bounds():x + toolbarSlot:bounds():width && py >= toolbarSlot:bounds():y && py < toolbarSlot:bounds():y + toolbarSlot:bounds():height }, {
						ptrCaptureTarget: 1;
					}, {
					if({ hasTabBar && px >= tabBar:bounds():x && px < tabBar:bounds():x + tabBar:bounds():width && py >= tabBar:bounds():y && py < tabBar:bounds():y + tabBar:bounds():height }, {
						ptrCaptureTarget: 2;
					}, {
					if({ hasBottomBar && px >= bottomBar:bounds():x && px < bottomBar:bounds():x + bottomBar:bounds():width && py >= bottomBar:bounds():y && py < bottomBar:bounds():y + bottomBar:bounds():height }, {
						ptrCaptureTarget: 3;
					}, {
					if({ hasBody && !useVulkan && px >= bodyPanel:bounds():x && px < bodyPanel:bounds():x + bodyPanel:bounds():width && py >= bodyPanel:bounds():y && py < bodyPanel:bounds():y + bodyPanel:bounds():height }, {
						ptrCaptureTarget: 4;
					}); }); }); });
				});
			});
			if({ px != lastPtrX || py != lastPtrY }, {
				hadActivity: true;
				lastPtrX: px;
				lastPtrY: py;
				if({ ptrDown && hasBody && !useVulkan }, {
					if({ DragDropState:shared:active }, {
						DragDropState:shared:updatePointer(x: px, y: py);
					});
					if({ bodyPanel:onOverlayPointerDrag(x: px, y: py, mods: curMods) }, {
						:isDirty: true;
					}, {
					if({ ptrCaptureTarget == 4 }, {
						if({ bodyPanel:onPointerDrag(x: px, y: py, mods: curMods) }, {
							:isDirty: true;
						});
						if({ DragDropState:shared:active }, {
							bodyPanel:onPointerMove(x: px, y: py);
						});
					}); });
				});
				if({ :onPointerMove(x: px, y: py) }, {
					:isDirty: true;
				});
				local Int is nextCursor: :cursorKindOf(shape: :resolveCursorAt(x: px, y: py));
				if({ nextCursor != lastCursorKind }, {
					:lastCursorKind: nextCursor;
					win:setCursor(kind: nextCursor);
				});
			});
			if({ !ptrDown && wasPtrDown }, {
				hadActivity: true;
				if({ hasBody && !useVulkan }, {
					if({ bodyPanel:onOverlayPointerUp(x: px, y: py) }, {
						:isDirty: true;
					}, {
					if({ ptrCaptureTarget == 4 }, {
						if({ bodyPanel:onPointerUp(x: px, y: py) }, {
							:isDirty: true;
						});
					}); });
				});
				if({ DragDropState:shared:active }, {
					DragDropState:shared:finishDrag();
					:isDirty: true;
				});
				ptrCaptureTarget: 0;
			});
			wasPtrDown: ptrDown;

			if({ win:pollClick() }, {
				hadActivity: true;
				local Int is cx: win:clickX();
				local Int is cy: win:clickY();
				if({ :onPointerClickMod(x: cx, y: cy, mods: curMods) }, {
					:isDirty: true;
				});
				if({ !lastClickInOverlay && FocusNav:shared:syncClick(focusables: :collectAllFocusables(), x: cx, y: cy) }, {
					:isDirty: true;
				});
			});

			if({ win:pollRightClick() }, {
				hadActivity: true;
				if({ :onRightClickMod(x: win:rightClickX(), y: win:rightClickY(), mods: curMods) }, {
					:isDirty: true;
				});
			});

			local Int is frameNowMs: clock:monotonicMs();
			if({ !tooltipVisible && activeTooltip != '' && lastPtrX >= 0 && lastPtrY >= 0 && (frameNowMs - tooltipHoverStartMs >= 480) }, {
				:tooltipVisible: true;
				:isDirty: true;
			});
			if({ hasBody && !useVulkan }, {
				if({ bodyPanel:tick(nowMs: frameNowMs) }, {
					hadActivity: true;
					:isDirty: true;
				});
			});
			if({ hasDialog }, {
				if({ dialog:tick(nowMs: frameNowMs) }, {
					hadActivity: true;
				});
			});
			local Int is edi2: 0;
			while({ edi2 < extraDialogs:length() }, {
				if({ extraDialogs:get(index: edi2):tick(nowMs: frameNowMs) }, {
					hadActivity: true;
				});
				edi2: edi2 + 1;
			});

			if({ isDirty && running:current() }, {
				hadActivity: true;
				:isDirty: false;
				:layout(widthPx: loopW, heightPx: loopH);
				:paint(ctx: ctx);
				if({ gpuPresent }, {
					vulkanBody:setOverlay(canvas: canvas);
					if({ !useVulkan }, {
						vulkanBody:presentOverlay(width: loopW, height: loopH);
					});
				}, {
					win:present(canvas: canvas);
				});
			});

			if({ useVulkan && gpuPresent && running:current() }, {
				local Function is frameCb: onFrame;
				frameCb(vulkanBody, elapsedMs, loopW, loopH);
				local Int is fpsCap: targetFps:current();
				if({ fpsCap > 0 }, {
					local Int is budgetNs: 1000000000 / fpsCap;
					clock:sleepUntilNs(targetNs: loopStartNs + budgetNs);
				});
			});

			if({ hadActivity }, {
				idleFrames: 0;
			}, {
				idleFrames: idleFrames + 1;
			});
		});
	}
}
