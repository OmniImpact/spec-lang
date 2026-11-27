#! specunit: suite

Class of SpecUnitTest is TestFabricTheme{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'fabric', [Color, Theme, ThemePreset, StrokeStyle, BoxBorderStyle, ShadowStyle, DrawContext]],
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
		t:setPanelShadowBlurPt(pt: 6.0);
		t:setPanelInnerShadowBlurPt(pt: 4.0);
		t:setPanelInnerShadowOffsetXPt(pt: 1.5);
		t:setPanelInnerShadowOffsetYPt(pt: 2.5);

		# Width-only BoxBorderStyle must NOT wipe existing shadows
		t:setPanelBorder(BoxBorderStyle(widthPt: 2.0));
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
		t:setPanelBorder(BoxBorderStyle(shadow: ShadowStyle(blurPt: 0.0)));
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
}
