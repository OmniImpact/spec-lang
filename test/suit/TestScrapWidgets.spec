#! specunit: suite

Class of SpecUnitTest is TestScrapWidgets{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'signal', TextEmitter],
		['base', 'suit', [KeyCode, KeyMod, SuitCanvas]],
		['base', 'fabric', [DrawContext, Color, Theme, ThemePreset]],
		['base', 'sew', [Rect, Constraints, Size, CursorShape, Scale]],
		['base', 'scrap', [SelectDropdown, ListView, TableView, Slider, Clickable, ScrapButton, DropTarget, DragDropState, Toast, ToastKind, Label, ColorSwatchHistory, Switch, Spinner, SectionH, SectionV, TextInput, TextArea, NumberInput, Popover, Checkbox, RadioButton]],
		['base', 'scrap', 'text', TextView],
		['base', 'scrap', 'menu', [MenuConfig, MenuItemConfig, MenuItemKind]],
		['base', 'scrap', 'toolbar', ToolbarConfig],
		['base', 'scrap', 'tab', [TabBar, TabItemConfig]],
		['base', 'scrap', 'tree', [TreeNode, TreeView]]
	];

	Function is testKeyCodeAndKeyModHelpers(){
		Assert:isTrue(KeyCode:isEnter(key: KeyCode:ENTER));
		Assert:isTrue(KeyCode:isEnter(key: KeyCode:LINE_FEED));
		Assert:isFalse(KeyCode:isEnter(key: KeyCode:SPACE));
		Assert:isTrue(KeyMod:hasShift(mods: KeyMod:SHIFT));
		Assert:isFalse(KeyMod:hasShift(mods: KeyMod:CTRL));
		Assert:isTrue(KeyMod:hasCtrl(mods: KeyMod:CTRL | KeyMod:SHIFT));
	}

	Function is testSelectDropdownKeyboardNavigation(){
		local Int is pickedIdx: -1;
		local String is pickedVal: '';
		local SelectDropdown is dd: SelectDropdown(
			options: Array(['Alpha', 'Beta', 'Gamma']),
			selectedIndex: 0,
			searchable: true,
			onSelect: local Function(Int is idx, String is val){
				pickedIdx: idx;
				pickedVal: val;
			}
		);
		dd:setFocused(next: true);
		Assert:isFalse(dd:open);
		Assert:isTrue(dd:onKey(key: KeyCode:ENTER, mods: KeyMod:NONE));
		Assert:isTrue(dd:open);
		Assert:isTrue(dd:onKey(key: KeyCode:DOWN, mods: KeyMod:NONE));
		Assert:isTrue(dd:onKey(key: KeyCode:DOWN, mods: KeyMod:NONE));
		Assert:isTrue(dd:onKey(key: KeyCode:UP, mods: KeyMod:NONE));
		Assert:isTrue(dd:onKey(key: KeyCode:LINE_FEED, mods: KeyMod:NONE));
		Assert:isFalse(dd:open);
		Assert:areEqualInt(1, pickedIdx);
		Assert:areEqualString('Beta', pickedVal);
		Assert:isTrue(dd:onKey(key: KeyCode:SPACE, mods: KeyMod:NONE));
		Assert:isTrue(dd:open);
		Assert:isTrue(dd:onKey(key: KeyCode:ESC, mods: KeyMod:NONE));
		Assert:isFalse(dd:open);
	}

	Function is testListViewAndTableViewKeyboardAndClipBalance(){
		local Int is lvSel: -1;
		local ListView is lv: ListView(
			items: Array(['One', 'Two', 'Three', 'Four']),
			selectedIndex: 0,
			onSelect: local Function(Int is idx){ lvSel: idx; }
		);
		lv:arrange(bounds: Rect(x: 0, y: 0, width: 200, height: 200));
		lv:setFocused(next: true);
		Assert:isTrue(lv:onKey(key: KeyCode:DOWN, mods: KeyMod:NONE));
		Assert:areEqualInt(1, lvSel);
		Assert:isTrue(lv:onKey(key: KeyCode:END, mods: KeyMod:NONE));
		Assert:areEqualInt(3, lvSel);
		Assert:isTrue(lv:onKey(key: KeyCode:UP, mods: KeyMod:NONE));
		Assert:areEqualInt(2, lvSel);
		Assert:isTrue(lv:onKey(key: KeyCode:HOME, mods: KeyMod:NONE));
		Assert:areEqualInt(0, lvSel);

		local Int is tvSel: -1;
		local TableView is tv: TableView(
			columns: Array(['Name', 'Role']),
			rows: Array([Array(['A', 'Dev']), Array(['B', 'QA']), Array(['C', 'Ops'])]),
			selectedIndex: 0,
			onSelect: local Function(Int is idx){ tvSel: idx; }
		);
		tv:arrange(bounds: Rect(x: 0, y: 0, width: 200, height: 200));
		tv:setFocused(next: true);
		Assert:isTrue(tv:onKey(key: KeyCode:DOWN, mods: KeyMod:NONE));
		Assert:areEqualInt(1, tvSel);
		Assert:isTrue(tv:onKey(key: KeyCode:END, mods: KeyMod:NONE));
		Assert:areEqualInt(2, tvSel);
		Assert:isTrue(tv:onKey(key: KeyCode:HOME, mods: KeyMod:NONE));
		Assert:areEqualInt(0, tvSel);

		local SuitCanvas is canvas: SuitCanvas(width: 220, height: 220);
		local DrawContext is ctx: DrawContext(canvas: canvas);
		tv:paint(ctx: ctx);
		Assert:isFalse(ctx:hasClip);
		canvas:dispose();
	}

	Function is testSliderKeyNavigationAndNoopGuard(){
		local Int is changes: 0;
		local Slider is sl: Slider(
			minVal: 0,
			maxVal: 100,
			value: 50,
			onChange: local Function(Int is _v){ changes: changes + 1; }
		);
		sl:setFocused(next: true);
		Assert:isTrue(sl:onKey(key: KeyCode:RIGHT, mods: KeyMod:NONE));
		Assert:areEqualInt(51, sl:value);
		Assert:isTrue(sl:onKey(key: KeyCode:RIGHT, mods: KeyMod:SHIFT));
		Assert:areEqualInt(56, sl:value);
		Assert:isTrue(sl:onKey(key: KeyCode:HOME, mods: KeyMod:NONE));
		Assert:areEqualInt(0, sl:value);
		local Int is beforeNoop: changes;
		Assert:isTrue(sl:onKey(key: KeyCode:HOME, mods: KeyMod:NONE));
		Assert:areEqualInt(beforeNoop, changes);
	}

	Function is testClickableHoverAndScrapButtonCursor(){
		local Int is dirtyCount: 0;
		local Clickable is btn: Clickable(label: 'Click');
		btn:bindDirty(cb: local Function(){ dirtyCount: dirtyCount + 1; });
		btn:arrange(bounds: Rect(x: 0, y: 0, width: 80, height: 30));
		Assert:isTrue(btn:onPointerMove(x: 10, y: 10));
		Assert:areEqualInt(1, dirtyCount);
		Assert:isTrue(btn:onPointerMove(x: 200, y: 200));
		Assert:areEqualInt(2, dirtyCount);

		local ScrapButton is sb: ScrapButton(label: 'OK');
		sb:arrange(bounds: Rect(x: 0, y: 0, width: 80, height: 30));
		Assert:isTrue(sb:cursorAt(x: 10, y: 10) == CursorShape:POINTER);
		Assert:isTrue(sb:cursorAt(x: 200, y: 10) == CursorShape:DEFAULT);
	}

	Function is testDropTargetFiresOnce(){
		local Int is dropCount: 0;
		local String is lastPayload: '';
		local DropTarget is dt: DropTarget(
			child: Label(text: 'Drop Here'),
			onDrop: local Function(String is p){
				dropCount: dropCount + 1;
				lastPayload: p;
			}
		);
		dt:arrange(bounds: Rect(x: 0, y: 0, width: 100, height: 40));
		DragDropState:shared:beginDrag(payload: 'item-42', label: 'Item', x: 10, y: 10);
		dt:onPointerMove(x: 20, y: 20);
		Assert:isTrue(dt:onPointerUp(x: 20, y: 20));
		if({ DragDropState:shared:active }, {
			DragDropState:shared:finishDrag();
		});
		Assert:areEqualInt(1, dropCount);
		Assert:areEqualString('item-42', lastPayload);
		Assert:isFalse(DragDropState:shared:active);
	}

	Function is testToastKindAndMenuItemKind(){
		local MenuItemConfig is item: MenuItemConfig(id: 'm1', label: 'Toggle', kind: MenuItemKind:TOGGLE, checked: true);
		Assert:isTrue(item:kind == MenuItemKind:TOGGLE);
		Assert:isTrue(item:checked);

		local Toast is toast: Toast(title: 'Done', message: 'Saved', kind: ToastKind:SUCCESS);
		Assert:isTrue(toast:kind == ToastKind:SUCCESS);
		toast:show(title: 'Err', message: 'Boom', kind: ToastKind:ERROR);
		Assert:isTrue(toast:kind == ToastKind:ERROR);
	}

	Function is testTreeViewCycleGuard(){
		local TreeNode is a: TreeNode(id: 'a', label: 'A', expandable: true, expanded: true);
		local TreeNode is b: TreeNode(id: 'b', label: 'B', expandable: true, expanded: true);
		a:children:add(item: b);
		b:children:add(item: a);
		local TreeView is tv: TreeView(roots: Array([a]));
		# Must terminate cleanly with exactly 2 unique nodes
		Assert:areEqualInt(2, tv:flatNodes:length());
	}

	Function is testColorSwatchHistoryNoHardColCap(){
		local Array of Color is swatches: Array();
		local Int is i: 0;
		while({ i < 12 }, {
			swatches:add(item: Color(r: i * 20, g: 100, b: 180));
			i: i + 1;
		});
		local ColorSwatchHistory is hist: ColorSwatchHistory(colors: swatches, swatchSizePt: 20.0);
		local Size is sz: hist:measure(c: Constraints(minW: 0, maxW: 600, minH: 0, maxH: 200));
		# All 12 swatches fit on 1 row when width is 600px (height <= 30px)
		Assert:isTrue(sz:height <= 30);
	}

	Function is testTabBarMutatorsAndDeclarativeToolbarConfig(){
		local TabBar is tb: TabBar();
		tb:addTab(tab: TabItemConfig(id: 'a', label: 'A'), activate: true);
		tb:addTab(tab: TabItemConfig(id: 'b', label: 'B'), activate: false);
		tb:addTab(tab: TabItemConfig(id: 'c', label: 'C'), activate: true);
		Assert:areEqualInt(3, tb:tabs:length());
		Assert:areEqualInt(2, tb:activeIndex);
		tb:selectTab(index: 1);
		Assert:areEqualInt(1, tb:activeIndex);
		tb:removeTab(index: 0);
		Assert:areEqualInt(2, tb:tabs:length());
		Assert:areEqualInt(0, tb:activeIndex);

		local ToolbarConfig is cfg: ToolbarConfig(
			menus: Array([
				MenuConfig(id: 'f', label: 'File', items: Array([
					MenuItemConfig(id: 't', label: 'Toggle', kind: MenuItemKind:TOGGLE)
				]))
			])
		);
		Assert:areEqualInt(1, cfg:menus:length());
		# Default icon SVGs are empty so Toolbar uses native Checkbox/RadioButton indicator visuals
		Assert:areEqualString('', cfg:checkboxOnIconSvg);
		Assert:areEqualString('', cfg:radioOnIconSvg);
	}

	Function is testSwitchEnabledAndSpinnerParity(){
		local Switch is sw: Switch(checked: false, enabled: false);
		sw:arrange(bounds: Rect(x: 0, y: 0, width: 40, height: 24));
		Assert:isFalse(sw:canFocus());
		Assert:isFalse(sw:onPointerClickMod(x: 10, y: 10));
		Assert:isFalse(sw:checked);

		local Spinner is sp: Spinner(indeterminate: true);
		sp:setIndeterminate(next: false);
		Assert:isFalse(sp:indeterminate);
		sp:setValue(next: 0.75);
		Assert:isTrue(sp:progress > 0.74 && sp:progress < 0.76);
	}

	Function is testSegmentedSectionRoundingAndClipBalance(){
		local Theme is t: Theme:forPreset(preset: ThemePreset:DARK);
		t:setButtonCornerRadiusPt(pt: 10.0);
		t:setButtonBorderThicknessPt(pt: 2.0);
		local SectionH is sh: SectionH(
			segmented: true,
			options: Array(['One', 'Two', 'Three']),
			selectedIndex: 0
		);
		sh:applyTheme(theme: t);
		sh:measure(c: Constraints(minW: 0, maxW: 300, minH: 0, maxH: 100));
		sh:arrange(bounds: Rect(x: 10, y: 10, width: 240, height: 32));
		local SuitCanvas is canvas: SuitCanvas(width: 280, height: 80);
		local DrawContext is ctx: DrawContext(canvas: canvas);
		local Int is bg: 255 << 24;
		canvas:clear(color: bg);
		sh:paint(ctx: ctx);
		Assert:isFalse(ctx:hasClip);
		# Outer corner pixel (10, 10) must stay untouched background because of 10pt corner radius
		local Int is px: canvas:pixelsAddr();
		Assert:areEqualInt(bg, loadI32(ptr: px, byteOffset: (10 * 280 + 10) * 4));
		canvas:dispose();
	}

	Function is testTextInputIconsClearableAndAutocomplete(){
		local String is lastChanged: '';
		local String is lastAccepted: '';
		local Array of String is dict: Array(['Apple', 'Apricot', 'Banana', 'Cherry']);
		local TextInput is inp: TextInput(
			leftIconSvg: TextInput:ICON_SEARCH_SVG,
			clearable: true,
			hasAutocomplete: true,
			autocompleteProvider: local Function of Array of String(String is q){
				local Array of String is out: Array();
				local String is lq: q:toLower();
				local Int is i: 0;
				while({ i < dict:length() }, {
					local String is s: dict:get(index: i);
					if({ lq == '' || s:toLower():contains(needle: lq) }, { out:add(item: s); });
					i: i + 1;
				});
				return out;
			},
			onChange: local Function(String is v){ lastChanged: v; },
			onAutocompleteSelect: local Function(String is v){ lastAccepted: v; }
		);
		inp:arrange(bounds: Rect(x: 0, y: 0, width: 220, height: 30));
		inp:setFocused(next: true);
		Assert:isTrue(inp:onText(ch: 'a', mods: 0));
		Assert:isTrue(inp:onText(ch: 'p', mods: 0));
		Assert:isTrue(inp:acOpen);
		Assert:areEqualInt(2, inp:suggestions:length());
		# Down moves highlight from Apple (0) -> Apricot (1); Enter accepts Apricot
		Assert:isTrue(inp:onKey(key: KeyCode:DOWN, mods: KeyMod:NONE));
		Assert:isTrue(inp:onKey(key: KeyCode:ENTER, mods: KeyMod:NONE));
		Assert:isFalse(inp:acOpen);
		Assert:areEqualString('Apricot', inp:text);
		Assert:areEqualString('Apricot', lastAccepted);

		# Clicking right clear button clears text
		Assert:isTrue(inp:cursorAt(x: 210, y: 15) == CursorShape:POINTER);
		Assert:areEqualString('Clear', inp:tooltipAt(x: 210, y: 15));
		Assert:isTrue(inp:onPointerClickMod(x: 210, y: 15));
		Assert:areEqualString('', inp:text);
		Assert:areEqualString('', lastChanged);
	}

	Function is testCheckboxAndRadioIndicatorSymmetryAndRadius(){
		local Theme is t: Theme:forPreset(preset: ThemePreset:DARK);
		local Scale is sc: Scale(factor: 1.0);
		local SuitCanvas is canvas: SuitCanvas(width: 64, height: 64);
		local DrawContext is ctx: DrawContext(canvas: canvas);
		local Int is px: canvas:pixelsAddr();
		local Int is bg: 255 << 24;

		# Even size (14) and odd size (15): Checkbox inner square must be pixel-symmetric
		local Array of Int is sizes: Array([14, 15]);
		local Int is si: 0;
		while({ si < sizes:length() }, {
			local Int is sz: sizes:get(index: si);
			t:setButtonCornerRadiusPt(pt: 0.0);
			canvas:clear(color: bg);
			Checkbox:paintIndicator(ctx: ctx, theme: t, scale: sc, x: 10, y: 10, sizePx: sz, checked: true);
			local Int is midY: 10 + sz / 2;
			local Int is dx: 0;
			while({ dx < sz }, {
				local Int is leftCol: loadI32(ptr: px, byteOffset: (midY * 64 + 10 + dx) * 4);
				local Int is rightCol: loadI32(ptr: px, byteOffset: (midY * 64 + 10 + sz - 1 - dx) * 4);
				Assert:areEqualInt(leftCol, rightCol);
				dx: dx + 1;
			});

			# RadioButton inner circle must also be pixel-symmetric
			canvas:clear(color: bg);
			RadioButton:paintIndicator(ctx: ctx, theme: t, scale: sc, x: 10, y: 10, sizePx: sz, selected: true);
			dx: 0;
			while({ dx < sz }, {
				local Int is leftCol: loadI32(ptr: px, byteOffset: (midY * 64 + 10 + dx) * 4);
				local Int is rightCol: loadI32(ptr: px, byteOffset: (midY * 64 + 10 + sz - 1 - dx) * 4);
				Assert:areEqualInt(leftCol, rightCol);
				dx: dx + 1;
			});
			si: si + 1;
		});

		# Checkbox inner square corner follows buttonCornerRadiusPt (sharp at 0pt vs rounded at 6pt)
		t:setButtonCornerRadiusPt(pt: 0.0);
		canvas:clear(color: bg);
		Checkbox:paintIndicator(ctx: ctx, theme: t, scale: sc, x: 10, y: 10, sizePx: 14, checked: true);
		local Int is sharpCorner: loadI32(ptr: px, byteOffset: (13 * 64 + 13) * 4);

		t:setButtonCornerRadiusPt(pt: 6.0);
		canvas:clear(color: bg);
		Checkbox:paintIndicator(ctx: ctx, theme: t, scale: sc, x: 10, y: 10, sizePx: 14, checked: true);
		local Int is roundCorner: loadI32(ptr: px, byteOffset: (13 * 64 + 13) * 4);
		Assert:isTrue(sharpCorner != roundCorner);

		canvas:dispose();
	}

	Function is testCtrlASelectAllOnEditableTextWidgets(){
		local TextInput is inp: TextInput(text: 'Hello World');
		inp:setFocused(next: true);
		Assert:isTrue(inp:onKey(key: 97, mods: KeyMod:CTRL));
		Assert:areEqualInt(0, inp:selAnchor);
		Assert:areEqualInt(11, inp:cursorPos);

		local TextArea is ta: TextArea(text: 'Line 1\nLine 2');
		ta:setFocused(next: true);
		Assert:isTrue(ta:onKey(key: 97, mods: KeyMod:CTRL));
		Assert:areEqualInt(0, ta:selAnchor);
		Assert:areEqualInt(14, ta:cursorPos);

		local NumberInput is ni: NumberInput(value: 42.0);
		ni:setFocused(next: true);
		Assert:isTrue(ni:onKey(key: 97, mods: KeyMod:CTRL));
		Assert:isTrue(ni:editing);
		Assert:isTrue(ni:allSelected);

		local TextView is tv: TextView(text: TextEmitter(initial: 'Alpha\nBeta'));
		local Popover is pop: Popover(anchor: Label(text: 'Open'), content: tv, open: true);
		pop:arrange(bounds: Rect(x: 0, y: 0, width: 100, height: 30));
		tv:setFocused(next: true);
		Assert:isTrue(pop:onKey(key: 97, mods: KeyMod:CTRL));
		Assert:areEqualString('Alpha\nBeta', tv:selectedText());
	}
}
