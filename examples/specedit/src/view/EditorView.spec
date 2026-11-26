#! Package specedit:view
#! Absolutely pure MVVM View for SpecEdit.
#! Binds exclusively to `EditorViewModel` and assembles the Scrap toolkit hierarchy.

Class is EditorView{
	replace [String] is namespace: ['specedit', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', Stderr],
		['base', 'sys', Process],
		['base', 'sys', Time],
		['base', 'suit', SuitWindow],
		['base', 'suit', SuitCanvas],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', ToolkitContainer],
		['base', 'scrap', ToolbarContainer],
		['base', 'scrap', Toolbar],
		['base', 'scrap', ToolbarConfig],
		['base', 'scrap', MenuConfig],
		['base', 'scrap', MenuItemConfig],
		['base', 'scrap', ScrapPanel],
		['specedit', 'model', EditorModel],
		['specedit', 'viewmodel', EditorViewModel]
	];

	EditorViewModel is vm: EditorViewModel(model: EditorModel());

	replace Function is init(EditorViewModel is vm){
		:vm: vm;
	}

	Function is run(Int is durationMs: 0){
		local SuitWindow is win: SuitWindow(
			title: vm:windowTitle(),
			width: 800,
			height: 600,
			decorated: true,
			useVulkan: false
		);

		if({ !win:open() }, {
			Stderr():line(text: 'Failed to open SpecEdit window: ':concat(other: win:lastError()));
			Process():exit(status: 1);
		});

		local Theme is theme: Theme(preset: 'light_grayscale');
		local Scale is scale: Scale(factor: win:scaleFactor());

		## 1. Create toolkit container
		local ToolkitContainer is toolkit: ToolkitContainer(theme: theme, scale: scale);

		## 2. Create toolbar container and add toolbar to it
		local ToolbarContainer is toolbarContainer: ToolbarContainer();
		local Toolbar is toolbar: Toolbar(theme: theme, scale: scale);
		toolbarContainer:addToolbar(toolbar: toolbar);

		## 3. Build toolbar config from ViewModel and push config + quit callback
		local ToolbarConfig is tbConfig: ToolbarConfig(heightPt: vm:toolbarHeightPt);
		local MenuConfig is fileMenu: MenuConfig(id: 'file', label: 'File');
		times(count: vm:fileMenuItemIds():length(), worker: local Function(Int is i){
			local String is itemId: vm:fileMenuItemIds():get(index: i);
			fileMenu:addItem(item: MenuItemConfig(
				id: itemId,
				label: vm:itemLabelForId(id: itemId)
			));
		});
		tbConfig:addMenu(menu: fileMenu);

		toolbarContainer:pushConfig(
			config: tbConfig,
			onQuit: local Function(){ vm:requestQuit(); }
		);

		## 4. Assemble toolkit container: toolbar container + white body
		toolkit:addToolbarContainer(container: toolbarContainer);
		toolkit:setBody(body: ScrapPanel(bgColor: theme:windowBg));

		local Int is curW: win:width();
		local Int is curH: win:height();
		local SuitCanvas is canvas: SuitCanvas(width: curW, height: curH);
		local DrawContext is ctx: DrawContext(canvas: canvas);

		toolkit:layout(widthPx: curW, heightPx: curH);
		toolkit:paint(ctx: ctx);
		win:present(canvas: canvas);

		local Time is clock: Time();
		local Int is startMs: clock:monotonicMs();
		local Int is lastPtrX: -1;
		local Int is lastPtrY: -1;

		while({ vm:isRunning() && win:poll() }, {
			local Int is key: win:nextKey();
			while({ key != 0 }, {
				if({ key == 27 }, { vm:requestQuit(); });
				key: win:nextKey();
			});

			if({ durationMs > 0 && (clock:monotonicMs() - startMs) >= durationMs }, {
				vm:requestQuit();
			});

			if({ vm:isRunning() }, {
				local Boolean is dirty: false;
				local Int is w: win:width();
				local Int is h: win:height();
				if({ w > 0 && h > 0 && (w != curW || h != curH) }, {
					curW: w;
					curH: h;
					canvas:resize(width: curW, height: curH);
					toolkit:layout(widthPx: curW, heightPx: curH);
					dirty: true;
				});

				local Int is px: win:pointerX();
				local Int is py: win:pointerY();
				if({ px != lastPtrX || py != lastPtrY }, {
					lastPtrX: px;
					lastPtrY: py;
					if({ toolkit:onPointerMove(x: px, y: py) }, {
						dirty: true;
					});
				});

				if({ win:pollClick() }, {
					if({ toolkit:onPointerClick(x: win:clickX(), y: win:clickY()) }, {
						dirty: true;
					});
				});

				if({ dirty && vm:isRunning() }, {
					toolkit:paint(ctx: ctx);
					win:present(canvas: canvas);
				});
			});
		});

		canvas:dispose();
		win:close();
	}
}
