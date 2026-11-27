#! Package suitshowcase:view
#! Dedicated showcase page for the Slider widget (continuous, signed range, and window opacity).

Class is SlidersPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', Slider],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	Slider is opacitySlider: Slider();
	TextEmitter is opacityLabel: TextEmitter(initial: '100%');
	TextEmitter is signedLabel: TextEmitter(initial: '0');
	TextEmitter is rgbLabel: TextEmitter(initial: '128');

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		:opacitySlider: Slider(
			minVal: 0,
			maxVal: 100,
			value: vm:windowAlphaPct,
			minWidthPt: 220.0,
			tooltip: 'Live window background opacity (0% - 100%)',
			onChange: local Function(Int is v){
				vm:setWindowAlphaPct(pct: v);
			}
		);
		opacityLabel:emit(value: (vm:windowAlphaPct as String) . '%');

		local Slider is signedSlider: Slider(
			minVal: -50,
			maxVal: 50,
			value: 0,
			minWidthPt: 220.0,
			tooltip: 'Signed integer range (-50 to +50)',
			onChange: local Function(Int is v){
				signedLabel:emit(value: v as String);
			}
		);

		local Slider is rgbSlider: Slider(
			minVal: 0,
			maxVal: 255,
			value: 128,
			minWidthPt: 220.0,
			tooltip: 'Byte range (0 to 255)',
			onChange: local Function(Int is v){
				rgbLabel:emit(value: v as String);
			}
		);

		return SectionV(
			children: Array([
				Label(text: 'Sliders', style: TextStyle:H1),
				TextScrap(
					text: TextEmitter(initial: 'Drag along any Slider track, or Tab to focus and use Left/Right arrows (Shift for +/- 5) or Home/End.'),
					wrap: true,
					muted: true
				),
				Frame(
					title: 'Window Opacity (0% - 100%)',
					child: SectionH(
						children: Array([
							opacitySlider,
							TextScrap(text: opacityLabel, muted: true)
						])
					)
				),
				Frame(
					title: 'Signed Range (-50 to +50)',
					child: SectionH(
						children: Array([
							signedSlider,
							TextScrap(text: signedLabel, muted: true)
						])
					)
				),
				Frame(
					title: 'Byte Channel (0 to 255)',
					child: SectionH(
						children: Array([
							rgbSlider,
							TextScrap(text: rgbLabel, muted: true)
						])
					)
				)
			])
		);
	}

	Function is sync(){
		opacitySlider:setValue(next: vm:windowAlphaPct);
		opacityLabel:emit(value: (vm:windowAlphaPct as String) . '%');
	}
}
