#! Package suitshowcase:view
#! Showcase page for FlowH and FlowV wrapping flow layout containers.

Class is FlowPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', FlowH],
		['base', 'sew', FlowV],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', SectionV],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	TextEmitter is flowStatus: TextEmitter(initial: 'Click any item or resize the window to see FlowH/FlowV reflow');

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		local Array of String is tagNames: Array([
			'Vulkan', 'Wayland', 'SewLayout', 'FlowH', 'FlowV',
			'FabricTheme', 'ScrapWidgets', 'Signals', 'Reactive',
			'ZeroCopy', 'HiDPI', 'Typography'
		]);
		local Array of SewNode is compactChips: Array();
		times(count: tagNames:length(), worker: local Function(Int is i){
			local String is tag: tagNames:get(index: i);
			compactChips:add(item: ScrapButton(
				label: tag,
				onClick: local Function(){
					flowStatus:emit(value: 'Compact FlowH clicked: ' . tag);
					vm:statusText:emit(value: 'FlowH compact: ' . tag);
				}
			));
		});

		local Array of String is cardTitles: Array([
			'Audio', 'Shaders', 'Meshes', 'Textures', 'Materials', 'Physics', 'UI Tree'
		]);
		local Array of SewNode is fillCards: Array();
		times(count: cardTitles:length(), worker: local Function(Int is i){
			local String is title: cardTitles:get(index: i);
			fillCards:add(item: Frame(
				padPt: 8.0,
				fillBg: true,
				child: SectionV(
					children: Array([
						Label(text: title, style: TextStyle:H3),
						TextScrap(text: TextEmitter(initial: '110-180pt'), muted: true)
					])
				)
			));
		});

		local Array of String is vItems: Array([
			'File', 'Edit', 'View', 'Search', 'Build', 'Run', 'Debug', 'Tools', 'Help'
		]);
		local Array of SewNode is compactColItems: Array();
		times(count: vItems:length(), worker: local Function(Int is i){
			local String is name: vItems:get(index: i);
			compactColItems:add(item: ScrapButton(
				label: name,
				onClick: local Function(){
					flowStatus:emit(value: 'Compact FlowV clicked: ' . name);
					vm:statusText:emit(value: 'FlowV compact: ' . name);
				}
			));
		});

		local Array of String is vFillNames: Array([
			'Layer A', 'Layer B', 'Layer C', 'Layer D', 'Layer E', 'Layer F'
		]);
		local Array of SewNode is fillColItems: Array();
		times(count: vFillNames:length(), worker: local Function(Int is i){
			local String is name: vFillNames:get(index: i);
			fillColItems:add(item: Frame(
				padPt: 6.0,
				fillBg: true,
				child: Label(text: name)
			));
		});

		return SectionV(
			children: Array([
				Label(text: 'Flow Layout', style: TextStyle:H1),
				TextScrap(text: flowStatus, muted: true),
				Frame(
					title: 'Horizontal Flow — Compact (FlowH, fill: false — resize window)',
					child: FlowH(
						gapPt: 6.0,
						lineGapPt: 6.0,
						fill: false,
						children: compactChips
					)
				),
				Frame(
					title: 'Horizontal Flow — Fill (FlowH, minItemPt: 110, maxItemPt: 180, fill: true)',
					child: FlowH(
						gapPt: 8.0,
						lineGapPt: 8.0,
						minItemPt: 110.0,
						maxItemPt: 180.0,
						fill: true,
						stretchCross: true,
						children: fillCards
					)
				),
				Frame(
					title: 'Vertical Flow — Compact (FlowV, maxLinePt: 110, fill: false)',
					child: FlowV(
						gapPt: 6.0,
						lineGapPt: 8.0,
						maxLinePt: 110.0,
						fill: false,
						children: compactColItems
					)
				),
				Frame(
					title: 'Vertical Flow — Fill (FlowV, maxLinePt: 130, minItemPt: 34, maxItemPt: 60, fill: true)',
					child: FlowV(
						gapPt: 6.0,
						lineGapPt: 8.0,
						maxLinePt: 130.0,
						minItemPt: 34.0,
						maxItemPt: 60.0,
						fill: true,
						stretchCross: true,
						children: fillColItems
					)
				)
			])
		);
	}
}
