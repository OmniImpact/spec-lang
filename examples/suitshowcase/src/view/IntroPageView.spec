#! Package suitshowcase:view
#! Intro landing page for SuitShowcase summarizing the Suit/Sew/Scrap/Fabric widget system.

Class is IntroPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		return SectionV(
			children: Array([
				Label(text: 'SUIT · SEW · SCRAP · FABRIC', style: TextStyle:OVERLINE),
				Label(text: 'Welcome to SuitShowcase', style: TextStyle:DISPLAY),
				TextScrap(
					text: TextEmitter(initial: 'This interactive gallery exercises the Suit, Sew, Scrap, and Fabric UI framework. Use the category list on the left (or Tab / Shift+Tab) to explore each widget group.'),
					wrap: true,
					muted: true
				),
				Frame(
					title: 'Architecture Layers',
					child: SectionV(
						children: Array([
							TextScrap(text: TextEmitter(initial: 'base:fabric — Color tokens, Theme presets, DrawContext (clip stack & alpha)'), wrap: true),
							TextScrap(text: TextEmitter(initial: 'base:sew — SewNode layout, Column, Row, Padding, NavStack, FocusNav'), wrap: true),
							TextScrap(text: TextEmitter(initial: 'base:scrap — Clickable, ScrapButton, SectionV/H, Switch, Slider, TextInput, ScrollView, TreeView, Tooltip'), wrap: true),
							TextScrap(text: TextEmitter(initial: 'base:wardrobe — High-level FileDialog and FileTree components'), wrap: true)
						])
					)
				),
				Frame(
					title: 'Quick Jump',
					child: SectionH(
						children: Array([
							ScrapButton(
								label: 'Open Theme Builder',
								tooltip: 'Load Light/Dark presets and override any Theme token live',
								onClick: local Function(){ vm:selectRoute(routeName: 'theme'); }
							),
							ScrapButton(
								label: 'Buttons & Sections',
								tooltip: 'Inspect ScrapButton and segmented SectionV/SectionH controls',
								onClick: local Function(){ vm:selectRoute(routeName: 'buttons'); }
							),
							ScrapButton(
								label: 'Inputs & Toggles',
								tooltip: 'Test TextInput, DecoratedTextInput, and Switch',
								onClick: local Function(){ vm:selectRoute(routeName: 'inputs'); }
							)
						])
					)
				)
			])
		);
	}
}
