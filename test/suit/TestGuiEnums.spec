#! specunit: suite

Class of SpecUnitTest is TestGuiEnums{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'suit', [KeyCode, KeyMod]],
		['base', 'fabric', [Theme, ThemePreset, StrokeStyle, BoxBorderStyle]],
		['base', 'sew', [HAlign]],
		['base', 'scrap', [Slider, Toast, ToastKind, StyledBox]],
		['base', 'scrap', 'menu', [MenuItemConfig, MenuItemKind]],
		['base', 'scrap', 'text', TextScrap],
		['base', 'mold', SpirvBuilder]
	];

	Function is testKeyCodeAndKeyModHelpers(){
		Assert:isTrue(KeyCode:isEnter(key: KeyCode:ENTER));
		Assert:isTrue(KeyCode:isEnter(key: KeyCode:LINE_FEED));
		Assert:isFalse(KeyCode:isEnter(key: KeyCode:SPACE));
		Assert:isTrue(KeyMod:hasShift(mods: KeyMod:SHIFT));
		Assert:isFalse(KeyMod:hasShift(mods: KeyMod:CTRL));
		Assert:isTrue(KeyMod:hasCtrl(mods: KeyMod:CTRL | KeyMod:SHIFT));
	}

	Function is testStrokeStyleRoundTripAndTheme(){
		local Theme is t: Theme:forPreset(preset: ThemePreset:DARK);
		t:setPanelBorderStyle(style: StrokeStyle:BEVEL);
		t:setDividerStyle(style: StrokeStyle:DOUBLE);
		t:setButtonBorderStyle(style: StrokeStyle:OUTSET);

		Assert:areEqualString('bevel', Theme:strokeStyleToString(s: t:panelBorderStyle));
		Assert:areEqualString('double', Theme:strokeStyleToString(s: t:dividerStyle));
		Assert:areEqualString('outset', Theme:strokeStyleToString(s: t:buttonBorderStyle));

		local String is encoded: t:toJson();
		local Theme is t2: Theme:forPreset(preset: ThemePreset:LIGHT);
		Assert:isTrue(t2:fromJson(json: encoded));
		Assert:isTrue(t2:panelBorderStyle == StrokeStyle:BEVEL);
		Assert:isTrue(t2:dividerStyle == StrokeStyle:DOUBLE);
		Assert:isTrue(t2:buttonBorderStyle == StrokeStyle:OUTSET);

		# StrokeStyle:NONE zeroes panelBorderPx
		t2:setPanelBorderStyle(style: StrokeStyle:NONE);
		Assert:areEqualInt(0, t2:panelBorderPx(scaleFactor: 1.0));
	}

	Function is testMenuItemKindAndHAlignAndToastKind(){
		local MenuItemConfig is item: MenuItemConfig(id: 'm1', label: 'Toggle', kind: MenuItemKind:TOGGLE, checked: true);
		Assert:isTrue(item:kind == MenuItemKind:TOGGLE);
		Assert:isTrue(item:checked);

		local TextScrap is ts: TextScrap(align: HAlign:CENTER);
		Assert:isTrue(ts:align == HAlign:CENTER);

		local Toast is toast: Toast(title: 'Done', message: 'Saved', kind: ToastKind:SUCCESS);
		Assert:isTrue(toast:kind == ToastKind:SUCCESS);
		toast:show(title: 'Err', message: 'Boom', kind: ToastKind:ERROR);
		Assert:isTrue(toast:kind == ToastKind:ERROR);
	}

	Function is testSliderKeyCodeAndShiftStep(){
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
		# Pressing HOME again at minVal should not fire onChange
		Assert:isTrue(sl:onKey(key: KeyCode:HOME, mods: KeyMod:NONE));
		Assert:areEqualInt(beforeNoop, changes);
	}

	Function is testSpirvBuilderConstants(){
		Assert:areEqualInt(119734787, SpirvBuilder:MAGIC);
		Assert:areEqualInt(65536, SpirvBuilder:VERSION_1_0);
		Assert:areEqualInt(17, SpirvBuilder:OP_CAPABILITY);
	}
}
