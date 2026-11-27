#! Package suitshowcase:view
#! Showcase page for Lines & Borders: line color, thickness, border styles (single/double/bevel/groove/inset/outset), shadows, and corner radius.

Class is LinesBordersPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Grid],
		['base', 'sew', Padding],
		['base', 'sew', Center],
		['base', 'fabric', Color],
		['base', 'fabric', DrawContext],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', Slider],
		['base', 'scrap', ScrapPanel],
		['base', 'scrap', StyledBox],
		['base', 'scrap', ColorSwatchDropdown],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	Array of String is styleNames: Array(['single', 'double', 'bevel', 'groove', 'inset', 'outset']);
	Array of String is styleLabels: Array(['Single', 'Double', 'Bevel', 'Groove', 'Inset', 'Outset']);
	StyledBox is previewBox: StyledBox();
	TextEmitter is thickLabel: TextEmitter(initial: '3 pt');
	TextEmitter is radiusLabel: TextEmitter(initial: '8 pt');
	TextEmitter is offXLabel: TextEmitter(initial: '0 pt');
	TextEmitter is offYLabel: TextEmitter(initial: '4 pt');
	TextEmitter is blurLabel: TextEmitter(initial: '8 pt');
	TextEmitter is inOffXLabel: TextEmitter(initial: '0 pt');
	TextEmitter is inOffYLabel: TextEmitter(initial: '0 pt');
	TextEmitter is inBlurLabel: TextEmitter(initial: '0 pt');
	Int is selStyleIdx: 0;

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		:previewBox: StyledBox(
			label: 'Live Preview Box',
			borderStyle: 'single',
			lineColor: Color(r: 90, g: 170, b: 255),
			useThemeBorder: false,
			thicknessPt: 3.0,
			radiusPt: 8.0,
			shadowOffsetXPt: 0.0,
			shadowOffsetYPt: 4.0,
			shadowBlurPt: 8.0,
			shadowAlpha: 110,
			minWidthPt: 260.0,
			minHeightPt: 96.0
		);

		local SectionH is styleSeg: SectionH(
			segmented: true,
			options: styleLabels,
			selectedIndex: selStyleIdx,
			itemMinWidthPt: 52.0,
			onSelect: local Function(Int is idx){
				if({ idx >= 0 && idx < styleNames:length() }, {
					:selStyleIdx: idx;
					previewBox:borderStyle: styleNames:get(index: idx);
					previewBox:invalidate();
					vm:statusText:emit(value: 'Border style: ' . styleNames:get(index: idx));
				});
			}
		);

		local ColorSwatchDropdown is colorPick: ColorSwatchDropdown(
			color: previewBox:lineColor,
			compactPicker: true,
			tooltip: 'Pick border/line color',
			onChange: local Function(Color is c){
				previewBox:lineColor: c;
				previewBox:useThemeBorder: false;
				previewBox:invalidate();
			}
		);

		local Slider is thickSlider: Slider(
			minVal: 1,
			maxVal: 12,
			value: previewBox:thicknessPt as Int,
			minWidthPt: 140.0,
			onChange: local Function(Int is v){
				previewBox:thicknessPt: v as Float;
				thickLabel:emit(value: (v as String) . ' pt');
				previewBox:invalidate();
			}
		);

		local Slider is radiusSlider: Slider(
			minVal: 0,
			maxVal: 24,
			value: previewBox:radiusPt as Int,
			minWidthPt: 140.0,
			onChange: local Function(Int is v){
				previewBox:radiusPt: v as Float;
				radiusLabel:emit(value: (v as String) . ' pt');
				previewBox:invalidate();
			}
		);

		local Slider is offXSlider: Slider(
			minVal: -14,
			maxVal: 14,
			value: previewBox:shadowOffsetXPt as Int,
			minWidthPt: 140.0,
			onChange: local Function(Int is v){
				previewBox:shadowOffsetXPt: v as Float;
				offXLabel:emit(value: (v as String) . ' pt');
				previewBox:invalidate();
			}
		);

		local Slider is offYSlider: Slider(
			minVal: -14,
			maxVal: 14,
			value: previewBox:shadowOffsetYPt as Int,
			minWidthPt: 140.0,
			onChange: local Function(Int is v){
				previewBox:shadowOffsetYPt: v as Float;
				offYLabel:emit(value: (v as String) . ' pt');
				previewBox:invalidate();
			}
		);

		local Slider is blurSlider: Slider(
			minVal: 0,
			maxVal: 20,
			value: previewBox:shadowBlurPt as Int,
			minWidthPt: 140.0,
			onChange: local Function(Int is v){
				previewBox:shadowBlurPt: v as Float;
				blurLabel:emit(value: (v as String) . ' pt');
				previewBox:invalidate();
			}
		);

		local Slider is inOffXSlider: Slider(
			minVal: -14,
			maxVal: 14,
			value: previewBox:innerShadowOffsetXPt as Int,
			minWidthPt: 140.0,
			onChange: local Function(Int is v){
				previewBox:innerShadowOffsetXPt: v as Float;
				inOffXLabel:emit(value: (v as String) . ' pt');
				previewBox:invalidate();
			}
		);

		local Slider is inOffYSlider: Slider(
			minVal: -14,
			maxVal: 14,
			value: previewBox:innerShadowOffsetYPt as Int,
			minWidthPt: 140.0,
			onChange: local Function(Int is v){
				previewBox:innerShadowOffsetYPt: v as Float;
				inOffYLabel:emit(value: (v as String) . ' pt');
				previewBox:invalidate();
			}
		);

		local Slider is inBlurSlider: Slider(
			minVal: 0,
			maxVal: 20,
			value: previewBox:innerShadowBlurPt as Int,
			minWidthPt: 140.0,
			onChange: local Function(Int is v){
				previewBox:innerShadowBlurPt: v as Float;
				inBlurLabel:emit(value: (v as String) . ' pt');
				previewBox:invalidate();
			}
		);

		local Grid is controlsGrid: Grid(
			columns: 3,
			colGapPt: 10.0,
			rowGapPt: 6.0,
			children: Array([
				Label(text: 'Line Color'),
				colorPick,
				Label(text: ''),
				Label(text: 'Thickness'),
				thickSlider,
				TextScrap(text: thickLabel, muted: true),
				Label(text: 'Corner Radius'),
				radiusSlider,
				TextScrap(text: radiusLabel, muted: true),
				Label(text: 'Shadow Offset X'),
				offXSlider,
				TextScrap(text: offXLabel, muted: true),
				Label(text: 'Shadow Offset Y'),
				offYSlider,
				TextScrap(text: offYLabel, muted: true),
				Label(text: 'Shadow Blur'),
				blurSlider,
				TextScrap(text: blurLabel, muted: true),
				Label(text: 'Inner Offset X'),
				inOffXSlider,
				TextScrap(text: inOffXLabel, muted: true),
				Label(text: 'Inner Offset Y'),
				inOffYSlider,
				TextScrap(text: inOffYLabel, muted: true),
				Label(text: 'Inner Blur'),
				inBlurSlider,
				TextScrap(text: inBlurLabel, muted: true)
			])
		);

		local Grid is stylesGrid: Grid(
			columns: 3,
			colGapPt: 8.0,
			rowGapPt: 8.0,
			equalCols: true,
			children: Array([
				StyledBox(label: 'Single', borderStyle: 'single', thicknessPt: 2.0, radiusPt: 5.0, shadowOffsetYPt: 2.0, shadowBlurPt: 4.0, minWidthPt: 120.0, minHeightPt: 64.0),
				StyledBox(label: 'Double', borderStyle: 'double', thicknessPt: 4.0, radiusPt: 5.0, shadowOffsetYPt: 2.0, shadowBlurPt: 4.0, minWidthPt: 120.0, minHeightPt: 64.0),
				StyledBox(label: 'Bevel', borderStyle: 'bevel', thicknessPt: 3.0, radiusPt: 4.0, shadowOffsetYPt: 2.0, shadowBlurPt: 4.0, minWidthPt: 120.0, minHeightPt: 64.0),
				StyledBox(label: 'Groove', borderStyle: 'groove', thicknessPt: 4.0, radiusPt: 4.0, shadowOffsetYPt: 0.0, shadowBlurPt: 0.0, minWidthPt: 120.0, minHeightPt: 64.0),
				StyledBox(label: 'Inset', borderStyle: 'inset', thicknessPt: 3.0, radiusPt: 4.0, shadowOffsetYPt: 0.0, shadowBlurPt: 0.0, innerShadowOffsetYPt: 2.0, innerShadowBlurPt: 5.0, minWidthPt: 120.0, minHeightPt: 64.0),
				StyledBox(label: 'Outset', borderStyle: 'outset', thicknessPt: 3.0, radiusPt: 4.0, shadowOffsetYPt: 3.0, shadowBlurPt: 5.0, minWidthPt: 120.0, minHeightPt: 64.0)
			])
		);

		local ScrapPanel is linesCanvas: ScrapPanel(
			minWidthPt: 340.0,
			minHeightPt: 84.0
		);
		linesCanvas:onPaint: local Function(DrawContext is ctx, Int is x, Int is y, Int is w, Int is h){
			local Int is rowH: h / 4;
			local Int is t1: linesCanvas:activeScale:px(pt: 1.0);
			local Int is t2: linesCanvas:activeScale:px(pt: 2.0);
			local Int is t4: linesCanvas:activeScale:px(pt: 4.0);
			local Int is t6: linesCanvas:activeScale:px(pt: 6.0);
			if({ t1 < 1 }, { t1: 1; });
			if({ t2 < 1 }, { t2: 1; });
			if({ t4 < 1 }, { t4: 1; });
			if({ t6 < 1 }, { t6: 1; });
			ctx:fillRect(x: x + 8, y: y + rowH / 2, w: w - 16, h: t1, color: Color(r: 180, g: 190, b: 210):toArgb());
			ctx:fillRect(x: x + 8, y: y + rowH + rowH / 2 - t2 / 2, w: w - 16, h: t2, color: Color(r: 100, g: 210, b: 255):toArgb());
			ctx:fillRect(x: x + 8, y: y + rowH * 2 + rowH / 2 - t4 / 2, w: w - 16, h: t4, color: Color(r: 76, g: 175, b: 80):toArgb());
			ctx:fillRect(x: x + 8, y: y + rowH * 3 + rowH / 2 - t6 / 2, w: w - 16, h: t6, color: Color(r: 239, g: 83, b: 80):toArgb());
		};

		return SectionV(
			children: Array([
				Label(text: 'Lines & Borders', heading: true),
				Frame(
					title: 'Interactive Border & Layer Effects',
					child: SectionV(
						children: Array([
							Center(child: previewBox),
							styleSeg,
							controlsGrid
						])
					)
				),
				Frame(
					title: 'Border Styles Gallery',
					child: stylesGrid
				),
				Frame(
					title: 'Line Colors & Thicknesses (1pt / 2pt / 4pt / 6pt)',
					child: linesCanvas
				)
			])
		);
	}
}
