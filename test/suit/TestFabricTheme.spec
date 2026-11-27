#! specunit: suite

Class of SpecUnitTest is TestFabricTheme{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', as Mem()],
		['base', 'fabric', [Color, Theme, ThemePreset, StrokeStyle, BorderStyleBox, ShadowStyle, DrawContext]],
		['base', 'suit', SuitCanvas]
	];

	Function is testColorHslAndRotateHue(){
		local Color is red: Color(r: 255, g: 0, b: 0);
		local Color is green: red:rotateHue(degrees: 120.0);
		Assert:isTrue(green:green() > 240);
		Assert:isTrue(green:red() < 15);
		local Color is fromHsl: Color:fromHsl(hDeg: 240.0, s: 1.0, l: 0.5);
		Assert:isTrue(fromHsl:blue() > 240);
		Assert:areEqualString('#0000FFFF', fromHsl:toHexAlpha());
	}

	Function is testThemeBorderShadowPreservationAndJsonRoundTrip(){
		local Theme is t: Theme:forPreset(preset: ThemePreset:DARK);
		Assert:areEqualString('#4C4C4C', t:detail:toHex());
		Assert:areEqualString('#828282', t:highlight:toHex());
		Assert:areEqualString('#989898', t:secondary:toHex());
		Assert:areEqualString('#555555', t:accent:toHex());
		t:setPanelShadowBlurPt(pt: 6.0);
		t:setPanelInnerShadowBlurPt(pt: 4.0);
		t:setPanelInnerShadowOffsetXPt(pt: 1.5);
		t:setPanelInnerShadowOffsetYPt(pt: 2.5);

		# Width-only BorderStyleBox must NOT wipe existing shadows
		t:setPanelBorder(BorderStyleBox(widthPt: 2.0));
		Assert:isTrue(t:panelShadowBlurPt > 5.5);
		Assert:isTrue(t:panelInnerShadowBlurPt > 3.5);

		# JSON round-trip must preserve panelInnerShadow* and StrokeStyle fields
		t:setPanelBorderStyle(style: StrokeStyle:BEVEL);
		t:setDividerStyle(style: StrokeStyle:DOUBLE);
		t:setButtonBorderStyle(style: StrokeStyle:OUTSET);
		local String is encoded: t:toJson();
		local Theme is t2: Theme:forPreset(preset: ThemePreset:LIGHT);
		Assert:isTrue(t2:fromJson(json: encoded));
		Assert:isTrue(t2:panelInnerShadowBlurPt > 3.5);
		Assert:isTrue(t2:panelInnerShadowOffsetXPt > 1.0);
		Assert:isTrue(t2:panelInnerShadowOffsetYPt > 2.0);
		Assert:isTrue(t2:panelBorderStyle == StrokeStyle:BEVEL);
		Assert:isTrue(t2:dividerStyle == StrokeStyle:DOUBLE);
		Assert:isTrue(t2:buttonBorderStyle == StrokeStyle:OUTSET);

		# StrokeStyle:NONE zeroes border pixel thickness
		t2:setPanelBorderStyle(style: StrokeStyle:NONE);
		Assert:areEqualInt(0, t2:panelBorderPx(scaleFactor: 1.0));

		# Explicit ShadowStyle(blurPt: 0.0) clears the shadow
		t:setPanelBorder(BorderStyleBox(shadow: ShadowStyle(blurPt: 0.0)));
		Assert:isTrue(t:panelShadowBlurPt < 0.01);
	}

	Function is testDrawContextClipStack(){
		local SuitCanvas is canvas: SuitCanvas(width: 100, height: 100);
		local DrawContext is ctx: DrawContext(canvas: canvas);
		Assert:isFalse(ctx:hasClip);
		ctx:setClip(x: 10, y: 10, w: 50, h: 50);
		Assert:isTrue(ctx:hasClip);
		ctx:setClip(x: 20, y: 20, w: 60, h: 60);
		Assert:areEqualInt(20, ctx:clipX);
		Assert:areEqualInt(40, ctx:clipW);
		ctx:clearClip();
		Assert:isTrue(ctx:hasClip);
		Assert:areEqualInt(10, ctx:clipX);
		ctx:clearClip();
		Assert:isFalse(ctx:hasClip);
		canvas:dispose();
	}

	Function is testDrawContextBlitArgb(){
		local SuitCanvas is canvas: SuitCanvas(width: 10, height: 10);
		local DrawContext is ctx: DrawContext(canvas: canvas);
		local Int is black: 255 << 24;
		canvas:clear(color: black);
		local Int is src: alloc(bytes: 4 * 4);
		local Int is red: (255 << 24) | (255 << 16);
		storeI32(ptr: src, byteOffset: 0, val: red);
		storeI32(ptr: src, byteOffset: 4, val: red);
		storeI32(ptr: src, byteOffset: 8, val: red);
		storeI32(ptr: src, byteOffset: 12, val: 0);
		ctx:setClip(x: 2, y: 2, w: 1, h: 2);
		ctx:blitArgb(dstX: 2, dstY: 2, srcAddr: src, srcW: 2, srcH: 2);
		ctx:clearClip();
		local Int is dst: canvas:pixelsAddr();
		Assert:areEqualInt(red, loadI32(ptr: dst, byteOffset: (2 * 10 + 2) * 4));
		# Clipped column (x=3) must remain black
		Assert:areEqualInt(black, loadI32(ptr: dst, byteOffset: (2 * 10 + 3) * 4));
		free(ptr: src);
		canvas:dispose();
	}
}
