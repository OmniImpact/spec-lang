#! Package suitshowcase:view
#! Showcase page for Fill & Effects: linear/radial gradients, centerpoint, blend width, reflected mode, and brightness/tint/saturation effects.

Class is FillEffectsPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Grid],
		['base', 'sew', Center],
		['base', 'fabric', Color],
		['base', 'fabric', FillStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', Slider],
		['base', 'scrap', Switch],
		['base', 'scrap', StyledBox],
		['base', 'scrap', ColorSwatchDropdown],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	Array of String is modeNames: Array(['solid', 'linear', 'radial']);
	Array of String is modeLabels: Array(['Solid', 'Linear', 'Radial']);
	Int is selModeIdx: 1;
	StyledBox is previewBox: StyledBox();
	FillStyle is liveFill: FillStyle(
		mode: 'linear',
		colorA: Color(r: 40, g: 64, b: 120),
		colorB: Color(r: 110, g: 205, b: 255),
		centerX: 0.5,
		centerY: 0.5,
		angleDeg: 35.0,
		blendWidth: 1.0,
		reflected: false
	);

	TextEmitter is cxLabel: TextEmitter(initial: '50%');
	TextEmitter is cyLabel: TextEmitter(initial: '50%');
	TextEmitter is angLabel: TextEmitter(initial: '35 deg');
	TextEmitter is bwLabel: TextEmitter(initial: '1.00');
	TextEmitter is briLabel: TextEmitter(initial: '0.00');
	TextEmitter is tintLabel: TextEmitter(initial: '0 deg');
	TextEmitter is satLabel: TextEmitter(initial: '0.00');

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	local Function of String is fmtTenths(Int is val){
		local Int is t: val;
		local String is sign: '';
		if({ t < 0 }, {
			sign: '-';
			t: 0 - t;
		});
		local Int is whole: t / 100;
		local Int is frac: t - (whole * 100);
		local Int is d1: frac / 10;
		local Int is d2: frac - (d1 * 10);
		return sign . (whole as String) . '.' . (d1 as String) . (d2 as String);
	}

	Function of SewNode is build(){
		:previewBox: StyledBox(
			label: 'Live Fill & Effects',
			borderStyle: 'single',
			thicknessPt: 1.5,
			radiusPt: 8.0,
			shadowOffsetYPt: 3.0,
			shadowBlurPt: 6.0,
			minWidthPt: 280.0,
			minHeightPt: 96.0
		);
		previewBox:useCustomFill: true;
		previewBox:fillStyle: liveFill;

		local SectionH is modeSeg: SectionH(
			segmented: true,
			options: modeLabels,
			selectedIndex: selModeIdx,
			itemMinWidthPt: 64.0,
			onSelect: local Function(Int is idx){
				if({ idx >= 0 && idx < modeNames:length() }, {
					:selModeIdx: idx;
					liveFill:mode: modeNames:get(index: idx);
					previewBox:invalidate();
					vm:statusText:emit(value: 'Fill mode: ' . liveFill:mode);
				});
			}
		);

		local Switch is reflSwitch: Switch(
			checked: liveFill:reflected,
			onChange: local Function(Boolean is on){
				liveFill:reflected: on;
				previewBox:invalidate();
			}
		);

		local ColorSwatchDropdown is colAPick: ColorSwatchDropdown(
			color: liveFill:colorA,
			compactPicker: true,
			tooltip: 'Primary / outer color (Color A)',
			onChange: local Function(Color is c){
				liveFill:colorA: c;
				previewBox:invalidate();
			}
		);

		local ColorSwatchDropdown is colBPick: ColorSwatchDropdown(
			color: liveFill:colorB,
			compactPicker: true,
			tooltip: 'Secondary / center color (Color B)',
			onChange: local Function(Color is c){
				liveFill:colorB: c;
				previewBox:invalidate();
			}
		);

		local Slider is cxSlider: Slider(
			minVal: 0, maxVal: 100, value: 50, minWidthPt: 130.0,
			onChange: local Function(Int is v){
				liveFill:centerX: (v as Float) / 100.0;
				cxLabel:emit(value: (v as String) . '%');
				previewBox:invalidate();
			}
		);

		local Slider is cySlider: Slider(
			minVal: 0, maxVal: 100, value: 50, minWidthPt: 130.0,
			onChange: local Function(Int is v){
				liveFill:centerY: (v as Float) / 100.0;
				cyLabel:emit(value: (v as String) . '%');
				previewBox:invalidate();
			}
		);

		local Slider is angSlider: Slider(
			minVal: 0, maxVal: 360, value: 35, minWidthPt: 130.0,
			onChange: local Function(Int is v){
				liveFill:angleDeg: v as Float;
				angLabel:emit(value: (v as String) . ' deg');
				previewBox:invalidate();
			}
		);

		local Slider is bwSlider: Slider(
			minVal: 10, maxVal: 200, value: 100, minWidthPt: 130.0,
			onChange: local Function(Int is v){
				liveFill:blendWidth: (v as Float) / 100.0;
				bwLabel:emit(value: :fmtTenths(val: v));
				previewBox:invalidate();
			}
		);

		local Slider is briSlider: Slider(
			minVal: -80, maxVal: 80, value: 0, minWidthPt: 130.0,
			onChange: local Function(Int is v){
				liveFill:brightness: (v as Float) / 100.0;
				briLabel:emit(value: :fmtTenths(val: v));
				previewBox:invalidate();
			}
		);

		local Slider is tintSlider: Slider(
			minVal: -180, maxVal: 180, value: 0, minWidthPt: 130.0,
			onChange: local Function(Int is v){
				liveFill:tintShiftDeg: v as Float;
				tintLabel:emit(value: (v as String) . ' deg');
				previewBox:invalidate();
			}
		);

		local Slider is satSlider: Slider(
			minVal: -100, maxVal: 100, value: 0, minWidthPt: 130.0,
			onChange: local Function(Int is v){
				liveFill:saturationShift: (v as Float) / 100.0;
				satLabel:emit(value: :fmtTenths(val: v));
				previewBox:invalidate();
			}
		);

		local Grid is controlsGrid: Grid(
			columns: 3,
			colGapPt: 10.0,
			rowGapPt: 6.0,
			children: Array([
				Label(text: 'Color A'), colAPick, Label(text: ''),
				Label(text: 'Color B'), colBPick, Label(text: ''),
				Label(text: 'Reflected Mode'), reflSwitch, TextScrap(text: TextEmitter(initial: 'Color B at center'), muted: true),
				Label(text: 'Center X'), cxSlider, TextScrap(text: cxLabel, muted: true),
				Label(text: 'Center Y'), cySlider, TextScrap(text: cyLabel, muted: true),
				Label(text: 'Linear Angle'), angSlider, TextScrap(text: angLabel, muted: true),
				Label(text: 'Blend Width'), bwSlider, TextScrap(text: bwLabel, muted: true),
				Label(text: 'Brightness'), briSlider, TextScrap(text: briLabel, muted: true),
				Label(text: 'Tint Shift'), tintSlider, TextScrap(text: tintLabel, muted: true),
				Label(text: 'Saturation Shift'), satSlider, TextScrap(text: satLabel, muted: true)
			])
		);

		local Color is c1: Color(r: 42, g: 58, b: 96);
		local Color is c2: Color(r: 96, g: 196, b: 255);

		local StyledBox is g1: StyledBox(label: 'Linear', radiusPt: 6.0, shadowOffsetYPt: 2.0, shadowBlurPt: 4.0, minWidthPt: 120.0, minHeightPt: 64.0);
		g1:useCustomFill: true;
		g1:fillStyle: FillStyle(mode: 'linear', colorA: c1, colorB: c2, angleDeg: 0.0, blendWidth: 1.0);

		local StyledBox is g2: StyledBox(label: 'Lin Reflected', radiusPt: 6.0, shadowOffsetYPt: 2.0, shadowBlurPt: 4.0, minWidthPt: 120.0, minHeightPt: 64.0);
		g2:useCustomFill: true;
		g2:fillStyle: FillStyle(mode: 'linear', colorA: c1, colorB: c2, angleDeg: 0.0, blendWidth: 0.9, reflected: true);

		local StyledBox is g3: StyledBox(label: 'Radial', radiusPt: 6.0, shadowOffsetYPt: 2.0, shadowBlurPt: 4.0, minWidthPt: 120.0, minHeightPt: 64.0);
		g3:useCustomFill: true;
		g3:fillStyle: FillStyle(mode: 'radial', colorA: c1, colorB: c2, centerX: 0.35, centerY: 0.35, blendWidth: 1.1);

		local StyledBox is g4: StyledBox(label: 'Rad Reflected', radiusPt: 6.0, shadowOffsetYPt: 2.0, shadowBlurPt: 4.0, minWidthPt: 120.0, minHeightPt: 64.0);
		g4:useCustomFill: true;
		g4:fillStyle: FillStyle(mode: 'radial', colorA: c1, colorB: c2, centerX: 0.5, centerY: 0.5, blendWidth: 1.0, reflected: true);

		local StyledBox is g5: StyledBox(label: 'Brightness +', radiusPt: 6.0, shadowOffsetYPt: 2.0, shadowBlurPt: 4.0, minWidthPt: 120.0, minHeightPt: 64.0);
		g5:useCustomFill: true;
		g5:fillStyle: FillStyle(mode: 'linear', colorA: c1, colorB: c2, angleDeg: 45.0, brightness: 0.35);

		local StyledBox is g6: StyledBox(label: 'Tint + Sat', radiusPt: 6.0, shadowOffsetYPt: 2.0, shadowBlurPt: 4.0, minWidthPt: 120.0, minHeightPt: 64.0);
		g6:useCustomFill: true;
		g6:fillStyle: FillStyle(mode: 'linear', colorA: c1, colorB: c2, angleDeg: 45.0, tintShiftDeg: 95.0, saturationShift: 0.45);

		local Grid is galleryGrid: Grid(
			columns: 3,
			colGapPt: 8.0,
			rowGapPt: 8.0,
			equalCols: true,
			children: Array([g1, g2, g3, g4, g5, g6])
		);

		return SectionV(
			children: Array([
				Label(text: 'Fill & Effects', heading: true),
				Frame(
					title: 'Interactive Gradient & Color Effects',
					child: SectionV(
						children: Array([
							Center(child: previewBox),
							modeSeg,
							controlsGrid
						])
					)
				),
				Frame(
					title: 'Gradients & Effects Gallery',
					child: galleryGrid
				)
			])
		);
	}
}
