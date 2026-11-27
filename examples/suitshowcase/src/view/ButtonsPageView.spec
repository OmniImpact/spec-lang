#! Package suitshowcase:view
#! Showcase page for ScrapButton variants, SectionH, and SectionV segmented controls.

Class is ButtonsPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	TextEmitter is clickLabel: TextEmitter(initial: 'Clicks: 0');
	TextEmitter is segLabel: TextEmitter(initial: 'Horizontal: Alpha | Vertical: Two');

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		local Array of String is hOpts: Array(['Alpha', 'Beta', 'Gamma']);
		local Array of String is vOpts: Array(['One', 'Two', 'Three']);

		return SectionV(
			children: Array([
				Label(text: 'Buttons & Sections', heading: true),
				Frame(
					title: 'ScrapButton States',
					child: SectionV(
						children: Array([
							SectionH(
								children: Array([
									ScrapButton(
										label: 'Click Me',
										tooltip: 'Increments click counter',
										onClick: local Function(){ vm:incrementClicks(); }
									),
									ScrapButton(
										label: 'Selected',
										selected: true,
										tooltip: 'Button in selected state'
									),
									ScrapButton(
										label: 'Disabled',
										enabled: false,
										tooltip: 'Disabled button does not accept focus or clicks'
									)
								])
							),
							TextScrap(text: clickLabel, muted: true)
						])
					)
				),
				Frame(
					title: 'Segmented SectionH & SectionV',
					child: SectionV(
						children: Array([
							SectionH(
								title: 'Horizontal Segmented',
								segmented: true,
								options: hOpts,
								selectedIndex: vm:segHIdx,
								itemMinWidthPt: 64.0,
								onSelect: local Function(Int is idx){
									vm:segHIdx: idx;
									segLabel:emit(value: 'Horizontal: ' . hOpts:get(index: vm:segHIdx) . ' | Vertical: ' . vOpts:get(index: vm:segVIdx));
								}
							),
							SectionV(
								title: 'Vertical Segmented',
								segmented: true,
								options: vOpts,
								selectedIndex: vm:segVIdx,
								itemMinWidthPt: 90.0,
								onSelect: local Function(Int is idx){
									vm:segVIdx: idx;
									segLabel:emit(value: 'Horizontal: ' . hOpts:get(index: vm:segHIdx) . ' | Vertical: ' . vOpts:get(index: vm:segVIdx));
								}
							),
							TextScrap(text: segLabel, muted: true)
						])
					)
				)
			])
		);
	}

	Function is sync(){
		clickLabel:emit(value: 'Clicks: ' . (vm:clickCount as String));
	}
}
