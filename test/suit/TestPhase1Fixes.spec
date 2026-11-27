#! specunit: suite

Class of SpecUnitTest is TestPhase1Fixes{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', as Conditional()],
		['base', 'fabric', [Theme, BoxBorderStyle, ShadowStyle, Color, DrawContext]],
		['base', 'suit', SuitCanvas],
		['base', 'sew', [SewNode, Rect, Constraints, Scale]],
		['base', 'sew', 'grid', [GridFlexH, GridFlexPanel]],
		['base', 'scrap', [SelectDropdown, ListView, TableView, DropTarget, DragDropState, Clickable, Label]],
		['base', 'scrap', 'highlighter', [Highlighter, HighlighterRust]],
		['base', 'scrap', 'text', CodeEditorView],
		['base', 'mold', SphereMesh]
	];

	Function is testSelectDropdownNormalizedKeys(){
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
		# Enter (13) opens popup
		Assert:isTrue(dd:onKey(key: 13, mods: 0));
		Assert:isTrue(dd:open);
		# Down (1002) moves highlight to 1, then 2
		Assert:isTrue(dd:onKey(key: 1002, mods: 0));
		Assert:isTrue(dd:onKey(key: 1002, mods: 0));
		# Up (1001) moves back to 1
		Assert:isTrue(dd:onKey(key: 1001, mods: 0));
		# Enter (10) selects index 1 ('Beta')
		Assert:isTrue(dd:onKey(key: 10, mods: 0));
		Assert:isFalse(dd:open);
		Assert:areEqualInt(1, pickedIdx);
		Assert:areEqualString('Beta', pickedVal);
		# Space (32) re-opens, Esc (27) closes
		Assert:isTrue(dd:onKey(key: 32, mods: 0));
		Assert:isTrue(dd:open);
		Assert:isTrue(dd:onKey(key: 27, mods: 0));
		Assert:isFalse(dd:open);
	}

	Function is testListViewAndTableViewNormalizedKeys(){
		local Int is lvSel: -1;
		local ListView is lv: ListView(
			items: Array(['One', 'Two', 'Three', 'Four']),
			selectedIndex: 0,
			onSelect: local Function(Int is idx){ lvSel: idx; }
		);
		lv:arrange(bounds: Rect(x: 0, y: 0, width: 200, height: 200));
		lv:setFocused(next: true);
		Assert:isTrue(lv:onKey(key: 1002, mods: 0));
		Assert:areEqualInt(1, lvSel);
		Assert:isTrue(lv:onKey(key: 1006, mods: 0));
		Assert:areEqualInt(3, lvSel);
		Assert:isTrue(lv:onKey(key: 1001, mods: 0));
		Assert:areEqualInt(2, lvSel);
		Assert:isTrue(lv:onKey(key: 1005, mods: 0));
		Assert:areEqualInt(0, lvSel);

		local Int is tvSel: -1;
		local TableView is tv: TableView(
			columns: Array(['Name']),
			rows: Array([Array(['A']), Array(['B']), Array(['C'])]),
			selectedIndex: 0,
			onSelect: local Function(Int is idx){ tvSel: idx; }
		);
		tv:arrange(bounds: Rect(x: 0, y: 0, width: 200, height: 200));
		tv:setFocused(next: true);
		Assert:isTrue(tv:onKey(key: 1002, mods: 0));
		Assert:areEqualInt(1, tvSel);
		Assert:isTrue(tv:onKey(key: 1006, mods: 0));
		Assert:areEqualInt(2, tvSel);
		Assert:isTrue(tv:onKey(key: 1005, mods: 0));
		Assert:areEqualInt(0, tvSel);

		# Verify TableView:paint() leaves DrawContext clip stack balanced
		local SuitCanvas is canvas: SuitCanvas(width: 220, height: 220);
		local DrawContext is ctx: DrawContext(canvas: canvas);
		tv:paint(ctx: ctx);
		Assert:isFalse(ctx:hasClip);
		canvas:dispose();
	}

	Function is testDropTargetNoDoubleFire(){
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
		# Simulate ToolkitContainer calling finishDrag() right after bodyPanel:onPointerUp
		if({ DragDropState:shared:active }, {
			DragDropState:shared:finishDrag();
		});
		Assert:areEqualInt(1, dropCount);
		Assert:areEqualString('item-42', lastPayload);
		Assert:isFalse(DragDropState:shared:active);
	}

	Function is testThemeBorderShadowPreservationAndJsonRoundTrip(){
		local Theme is t: Theme(preset: 'dark');
		t:setPanelShadowBlurPt(pt: 6.0);
		t:setPanelInnerShadowBlurPt(pt: 4.0);
		t:setPanelInnerShadowOffsetXPt(pt: 1.5);
		t:setPanelInnerShadowOffsetYPt(pt: 2.5);

		# Setting width-only BoxBorderStyle must NOT wipe existing shadows
		t:setPanelBorder(BoxBorderStyle(widthPt: 2.0));
		Assert:isTrue(t:panelShadowBlurPt > 5.5);
		Assert:isTrue(t:panelInnerShadowBlurPt > 3.5);

		# JSON round-trip must preserve panelInnerShadow* fields
		local String is encoded: t:toJson();
		local Theme is t2: Theme(preset: 'dark');
		Assert:isTrue(t2:fromJson(json: encoded));
		Assert:isTrue(t2:panelInnerShadowBlurPt > 3.5);
		Assert:isTrue(t2:panelInnerShadowOffsetXPt > 1.0);
		Assert:isTrue(t2:panelInnerShadowOffsetYPt > 2.0);

		# Explicit ShadowStyle(blurPt: 0.0) clears the shadow
		t:setPanelBorder(BoxBorderStyle(shadow: ShadowStyle(blurPt: 0.0)));
		Assert:isTrue(t:panelShadowBlurPt < 0.01);
	}

	Function is testGridFlexDividerDragWithHiddenPanel(){
		local GridFlexH is gf: GridFlexH(spacingPt: 6.0);
		local GridFlexPanel is p0: GridFlexPanel(child: Label(text: 'Hidden'), sizePt: 100.0, flex: false, visible: false);
		local GridFlexPanel is p1: GridFlexPanel(child: Label(text: 'Left'), sizePt: 150.0, minSizePt: 40.0, flex: false);
		local GridFlexPanel is p2: GridFlexPanel(child: Label(text: 'Right'), sizePt: 150.0, minSizePt: 40.0, flex: false);
		gf:addPanel(panel: p0);
		gf:addPanel(panel: p1);
		gf:addPanel(panel: p2);
		gf:setScale(scale: Scale(factor: 1.0));
		gf:arrange(bounds: Rect(x: 0, y: 0, width: 306, height: 100));

		# Divider 0 is between visible panels p1 (x=0..150) and p2 (x=156..306), at x=150..156
		Assert:isTrue(gf:onPointerClickMod(x: 152, y: 50, mods: 0));
		Assert:isTrue(gf:onPointerDrag(x: 182, y: 50, mods: 0));
		gf:onPointerUp(x: 182, y: 50);

		# p0 must remain untouched at 100.0, while p1 grew to ~180.0 and p2 shrank to ~120.0
		Assert:isTrue(p0:sizePt > 99.0 && p0:sizePt < 101.0);
		Assert:isTrue(p1:sizePt > 175.0 && p1:sizePt < 185.0);
		Assert:isTrue(p2:sizePt > 115.0 && p2:sizePt < 125.0);
	}

	Function is testClickableInvalidatesOnHover(){
		local Int is dirtyCount: 0;
		local Clickable is btn: Clickable(label: 'Click');
		btn:bindDirty(cb: local Function(){ dirtyCount: dirtyCount + 1; });
		btn:arrange(bounds: Rect(x: 0, y: 0, width: 80, height: 30));
		Assert:isTrue(btn:onPointerMove(x: 10, y: 10));
		Assert:areEqualInt(1, dirtyCount);
		Assert:isTrue(btn:onPointerMove(x: 200, y: 200));
		Assert:areEqualInt(2, dirtyCount);
	}

	Function is testCodeEditorViewClonesHighlighter(){
		local CodeEditorView is ed: CodeEditorView();
		ed:activeHighlighter: HighlighterRust() as Highlighter;
		local Highlighter is copy: ed:createWrapContext();
		Assert:areEqualString('rust', copy:languageId());
	}

	Function is testSphereMeshAccessorsAndDispose(){
		local SphereMesh is s: SphereMesh(radius: 0.5);
		Assert:isTrue(s:vertexAddr() != 0);
		Assert:isTrue(s:vertexBytes() > 0);
		Assert:isTrue(s:indexAddr() != 0);
		Assert:isTrue(s:indexCount() > 0);
		s:dispose();
		Assert:areEqualInt(0, s:vertexAddr());
		Assert:areEqualInt(0, s:indexAddr());
	}
}
