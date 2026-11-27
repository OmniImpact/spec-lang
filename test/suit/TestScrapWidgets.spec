#! specunit: suite

Class of SpecUnitTest is TestScrapWidgets{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', as Conditional()],
		['base', 'suit', [KeyCode, KeyMod, SuitCanvas]],
		['base', 'fabric', [DrawContext]],
		['base', 'sew', [Rect, CursorShape]],
		['base', 'scrap', [SelectDropdown, ListView, TableView, Slider, Clickable, ScrapButton, DropTarget, DragDropState, Toast, ToastKind, Label]],
		['base', 'scrap', 'menu', [MenuItemConfig, MenuItemKind]]
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
}
