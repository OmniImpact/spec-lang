#! Package suitshowcase:view
#! Showcase page exercising standalone ColorSelector (full ring + compact), ColorSwatchHistory, and ColorSwatchDropdown modes.

Class is ColorPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'fabric', Color],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ColorSelector],
		['base', 'scrap', ColorSwatchHistory],
		['base', 'scrap', ColorSwatchDropdown],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	TextEmitter is pickedLabel: TextEmitter(initial: 'Selected: #64B4FF');

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		local Color is initialCol: Color(r: 100, g: 180, b: 255);
		local Color is alphaInitCol: Color(r: 100, g: 180, b: 255, a: 180);
		local Color is prevCol: Color(r: 239, g: 83, b: 80);

		local ColorSelector is fullPicker: ColorSelector(
			color: initialCol,
			currentColor: prevCol,
			hasCurrent: true,
			compact: false,
			onChange: local Function(Color is c){
				pickedLabel:emit(value: 'Selected (Full Ring): ' . c:toHex());
			}
		);

		local ColorSelector is fullAlphaPicker: ColorSelector(
			color: alphaInitCol,
			currentColor: prevCol:withAlphaByte(a: 200),
			hasCurrent: true,
			compact: false,
			showAlpha: true,
			onChange: local Function(Color is c){
				pickedLabel:emit(value: 'Selected (Ring + Alpha): ' . c:toHexAlpha());
			}
		);

		local ColorSelector is compactPicker: ColorSelector(
			color: initialCol,
			currentColor: prevCol,
			hasCurrent: true,
			compact: true,
			onChange: local Function(Color is c){
				pickedLabel:emit(value: 'Selected (Compact): ' . c:toHex());
			}
		);

		local ColorSelector is compactAlphaPicker: ColorSelector(
			color: alphaInitCol,
			currentColor: prevCol:withAlphaByte(a: 200),
			hasCurrent: true,
			compact: true,
			showAlpha: true,
			onChange: local Function(Color is c){
				pickedLabel:emit(value: 'Selected (Compact + Alpha): ' . c:toHexAlpha());
			}
		);

		local ColorSwatchHistory is standaloneHist: ColorSwatchHistory(
			colors: Array([
				Color(r: 239, g: 83, b: 80),
				Color(r: 255, g: 167, b: 38),
				Color(r: 255, g: 238, b: 88),
				Color(r: 102, g: 187, b: 106),
				Color(r: 66, g: 165, b: 245),
				Color(r: 171, g: 71, b: 188)
			]),
			onSelect: local Function(Color is c){
				fullPicker:setColor(next: c);
				compactPicker:setColor(next: c);
				pickedLabel:emit(value: 'Swatch clicked: ' . c:toHex());
			}
		);

		local ColorSwatchDropdown is fullDropdown: ColorSwatchDropdown(
			color: initialCol,
			showPicker: true,
			showHistory: true,
			compactPicker: false,
			tooltip: 'Full picker + swatch history dropdown',
			onChange: local Function(Color is c){
				pickedLabel:emit(value: 'Dropdown (Full + History): ' . c:toHex());
			}
		);

		local ColorSwatchDropdown is swatchOnlyDropdown: ColorSwatchDropdown(
			color: prevCol,
			showPicker: false,
			showHistory: true,
			historyColors: Array([
				Color(r: 239, g: 83, b: 80),
				Color(r: 76, g: 175, b: 80),
				Color(r: 66, g: 133, b: 244),
				Color(r: 255, g: 193, b: 7)
			]),
			tooltip: 'Swatch-only dropdown (picker disabled)',
			onChange: local Function(Color is c){
				pickedLabel:emit(value: 'Swatch-only Dropdown: ' . c:toHex());
			}
		);

		local ColorSwatchDropdown is alphaDropdown: ColorSwatchDropdown(
			color: alphaInitCol,
			showPicker: true,
			showHistory: true,
			compactPicker: false,
			showAlpha: true,
			tooltip: 'Full picker + alpha + swatch history dropdown',
			onChange: local Function(Color is c){
				pickedLabel:emit(value: 'Dropdown (Alpha): ' . c:toHexAlpha());
			}
		);

		return SectionV(
			children: Array([
				Label(text: 'Color Selector', style: TextStyle:H1),
				TextScrap(text: pickedLabel, muted: true),
				SectionH(
					children: Array([
						Frame(title: 'Concentric Ring Mode', child: fullPicker),
						Frame(title: 'Concentric Ring + Alpha (Thirds)', child: fullAlphaPicker),
						Frame(title: 'Compact Mode', child: compactPicker),
						Frame(title: 'Compact + Alpha', child: compactAlphaPicker)
					])
				),
				Frame(
					title: 'Standalone ColorSwatchHistory',
					child: standaloneHist
				),
				Frame(
					title: 'ColorSwatchDropdown Variants',
					child: SectionH(
						children: Array([
							SectionV(title: 'Picker + History', children: Array([fullDropdown])),
							SectionV(title: 'Picker + Alpha', children: Array([alphaDropdown])),
							SectionV(title: 'Swatches Only', children: Array([swatchOnlyDropdown]))
						])
					)
				)
			])
		);
	}
}
