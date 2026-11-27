#! Package suitshowcase:view
#! Showcase page demonstrating standard [TextStyle] typographic roles (DISPLAY, H1..H3, SUBTITLE, BODY, CAPTION, OVERLINE, CODE).

Class is TextStylesPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', SectionV],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		return SectionV(
			children: Array([
				Label(text: 'Text Styles & Hierarchy', style: TextStyle:H1),
				Label(text: 'Standard typographic roles scaled with the active theme.', style: TextStyle:SUBTITLE),
				Frame(
					title: 'Display & Header Hierarchy',
					child: SectionV(
						children: Array([
							Label(text: 'OVERLINE · SECTION EYEBROW', style: TextStyle:OVERLINE),
							Label(text: 'Display Title (DISPLAY)', style: TextStyle:DISPLAY),
							Label(text: 'Page Heading 1 (H1)', style: TextStyle:H1),
							Label(text: 'Section Heading 2 (H2)', style: TextStyle:H2),
							Label(text: 'Subsection Heading 3 (H3)', style: TextStyle:H3),
							Label(text: 'Lead Subtitle (SUBTITLE) — supporting summary text', style: TextStyle:SUBTITLE)
						])
					)
				),
				Frame(
					title: 'Body, Caption & Monospace',
					child: SectionV(
						children: Array([
							Label(text: 'Standard Body Text (BODY) — default UI and paragraph copy.', style: TextStyle:BODY),
							Label(text: 'Caption / Helper Text (CAPTION) — secondary metadata and hints.', style: TextStyle:CAPTION),
							Label(text: 'Label(text: "Code (CODE)", style: TextStyle:CODE)', style: TextStyle:CODE, boxed: true)
						])
					)
				)
			])
		);
	}
}
