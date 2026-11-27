#! specunit: suite

Class of SpecUnitTest is TestSewLayout{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'struct', Array],
		['base', 'sew', [SewNode, Size, Rect, Constraints, Scale, CursorShape, Center, Padding, Column, Row, Grid, FlowH, FlowV, ZStack]],
		['base', 'sew', 'grid', [GridFlexH, GridFlexPanel]],
		['base', 'scrap', [ScrapButton, Label]]
	];

	Function is testRectContains(){
		local Rect is r: Rect(x: 10, y: 20, width: 30, height: 40);
		Assert:isTrue(r:contains(px: 10, py: 20));
		Assert:isTrue(r:contains(px: 39, py: 59));
		Assert:isFalse(r:contains(px: 9, py: 20));
		Assert:isFalse(r:contains(px: 40, py: 20));
		Assert:isFalse(r:contains(px: 10, py: 60));
	}

	Function is testSingleChildNodeForwardingInCenterAndPadding(){
		local ScrapButton is btn: ScrapButton(label: 'Go', tooltip: 'Run');
		local Center is centered: Center(child: btn);
		centered:measure(c: Constraints(minW: 0, maxW: 200, minH: 0, maxH: 100));
		centered:arrange(bounds: Rect(x: 0, y: 0, width: 200, height: 100));
		local Rect is bb: btn:bounds();
		local Int is cx: bb:x + bb:width / 2;
		local Int is cy: bb:y + bb:height / 2;
		Assert:isTrue(centered:cursorAt(x: cx, y: cy) == CursorShape:POINTER);
		Assert:areEqualString('Run', centered:tooltipAt(x: cx, y: cy));

		local Array of SewNode is focusables: Array();
		centered:collectFocusables(out: focusables);
		Assert:areEqualInt(1, focusables:length());
	}

	Function is testMultiChildNodeForwardingInGridAndZStack(){
		local ScrapButton is b1: ScrapButton(label: 'One', tooltip: 'Tip1');
		local Grid is g: Grid(columns: 2, children: Array([b1 as SewNode, Label(text: 'Two') as SewNode]));
		g:measure(c: Constraints(minW: 0, maxW: 240, minH: 0, maxH: 100));
		g:arrange(bounds: Rect(x: 0, y: 0, width: 240, height: 100));
		local Rect is b1r: b1:bounds();
		Assert:isTrue(g:cursorAt(x: b1r:x + 4, y: b1r:y + 4) == CursorShape:POINTER);

		local ZStack is zs: ZStack(children: Array([Label(text: 'Back') as SewNode, b1 as SewNode]));
		zs:arrange(bounds: Rect(x: 0, y: 0, width: 200, height: 60));
		Assert:isTrue(zs:cursorAt(x: 10, y: 10) == CursorShape:POINTER);
		local Array of SewNode is focusables: Array();
		zs:collectFocusables(out: focusables);
		Assert:areEqualInt(1, focusables:length());
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

		Assert:isTrue(gf:onPointerClickMod(x: 152, y: 50, mods: 0));
		Assert:isTrue(gf:onPointerDrag(x: 182, y: 50, mods: 0));
		gf:onPointerUp(x: 182, y: 50);

		Assert:isTrue(p0:sizePt > 99.0 && p0:sizePt < 101.0);
		Assert:isTrue(p1:sizePt > 175.0 && p1:sizePt < 185.0);
		Assert:isTrue(p2:sizePt > 115.0 && p2:sizePt < 125.0);
	}

	Function is testFlowHCompactAndFill(){
		local ScrapButton is b1: ScrapButton(label: 'Alpha');
		local ScrapButton is b2: ScrapButton(label: 'Beta');
		local ScrapButton is b3: ScrapButton(label: 'Gamma');
		local FlowH is compact: FlowH(
			gapPt: 10.0,
			lineGapPt: 8.0,
			minItemPt: 90.0,
			fill: false,
			children: Array([b1 as SewNode, b2 as SewNode, b3 as SewNode])
		);
		compact:setScale(scale: Scale(factor: 1.0));
		local Size is m1: compact:measure(c: Constraints(minW: 0, maxW: 200, minH: 0, maxH: 500));
		compact:arrange(bounds: Rect(x: 0, y: 0, width: 200, height: m1:height));
		Assert:areEqualInt(0, b1:bounds():x);
		Assert:areEqualInt(100, b2:bounds():x);
		Assert:areEqualInt(b1:bounds():y, b2:bounds():y);
		Assert:areEqualInt(0, b3:bounds():x);
		Assert:isTrue(b3:bounds():y > b1:bounds():y);

		local FlowH is filled: FlowH(
			gapPt: 10.0,
			lineGapPt: 8.0,
			minItemPt: 80.0,
			maxItemPt: 120.0,
			fill: true,
			children: Array([b1 as SewNode, b2 as SewNode, b3 as SewNode])
		);
		filled:setScale(scale: Scale(factor: 1.0));
		local Size is m2: filled:measure(c: Constraints(minW: 0, maxW: 200, minH: 0, maxH: 500));
		filled:arrange(bounds: Rect(x: 0, y: 0, width: 200, height: m2:height));
		Assert:areEqualInt(95, b1:bounds():width);
		Assert:areEqualInt(95, b2:bounds():width);
		Assert:areEqualInt(120, b3:bounds():width);
	}

	Function is testFlowVWrap(){
		local ScrapButton is b1: ScrapButton(label: 'One');
		local ScrapButton is b2: ScrapButton(label: 'Two');
		local ScrapButton is b3: ScrapButton(label: 'Three');
		local FlowV is fv: FlowV(
			gapPt: 6.0,
			lineGapPt: 10.0,
			minItemPt: 30.0,
			maxLinePt: 70.0,
			fill: false,
			children: Array([b1 as SewNode, b2 as SewNode, b3 as SewNode])
		);
		fv:setScale(scale: Scale(factor: 1.0));
		local Size is m: fv:measure(c: Constraints(minW: 0, maxW: 500, minH: 0, maxH: 500));
		fv:arrange(bounds: Rect(x: 0, y: 0, width: m:width, height: m:height));
		Assert:areEqualInt(0, b1:bounds():x);
		Assert:areEqualInt(0, b2:bounds():x);
		Assert:areEqualInt(36, b2:bounds():y);
		Assert:isTrue(b3:bounds():x > b1:bounds():x);
		Assert:areEqualInt(0, b3:bounds():y);
	}
}
