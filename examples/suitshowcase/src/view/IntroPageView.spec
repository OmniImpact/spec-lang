#! Package suitshowcase:view
#! Intro landing page for SuitShowcase summarizing the Suit/Sew/Scrap/Fabric widget system.

Class is IntroPageView{
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

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		return SectionV(
			children: Array([
				Label(text: 'Welcome to SuitShowcase', heading: true),
				TextScrap(
					text: TextEmitter(initial: 'This interactive gallery exercises the Suit, Sew, Scrap, and Fabric UI framework. Use the category list on the left (or Tab / Shift+Tab) to explore each widget group.'),
					wrap: true,
					muted: true
				),
				Frame(
					title: 'Architecture Layers',
					child: SectionV(
						children: Array([
							Label(text: 'base:fabric — Color tokens, Theme presets, DrawContext (clip stack & alpha)'),
							Label(text: 'base:sew — SewNode layout, Column, Row, Padding, NavStack, FocusNav'),
							Label(text: 'base:scrap — Clickable, ScrapButton, SectionV/H, Switch, TextInput, ScrollView, TreeView, Tooltip'),
							Label(text: 'base:wardrobe — High-level FileDialog and FileTree components')
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
