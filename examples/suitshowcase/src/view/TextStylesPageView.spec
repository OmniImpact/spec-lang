#! Package suitshowcase:view
#! Showcase page demonstrating standard [TextStyle] typographic roles (DISPLAY, H1..H3, SUBTITLE, BODY, CAPTION, OVERLINE, CODE).

Class is TextStylesPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'fabric', Color],
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
				),
				Frame(
					title: 'Text Effects (Border & Shadow)',
					child: SectionV(
						children: Array([
							Label(
								text: 'Outlined Header (outlinePt: 1.5)',
								style: TextStyle:H1,
								outlinePt: 1.5,
								outlineColor: Color(r: 40, g: 120, b: 220, a: 230),
								useCustomOutlineColor: true
							),
							Label(
								text: 'Crisp Drop Shadow (1pt, 1pt)',
								style: TextStyle:H2,
								shadowOffsetXPt: 1.0,
								shadowOffsetYPt: 1.0,
								shadowAlpha: 140
							),
							Label(
								text: 'Soft Blurred Shadow (blur: 3pt)',
								style: TextStyle:H2,
								shadowOffsetXPt: 1.5,
								shadowOffsetYPt: 2.0,
								shadowBlurPt: 3.0,
								shadowAlpha: 160
							),
							Label(
								text: 'Border + Shadow Combined',
								style: TextStyle:DISPLAY,
								outlinePt: 1.5,
								outlineColor: Color(r: 20, g: 24, b: 36, a: 235),
								useCustomOutlineColor: true,
								shadowOffsetXPt: 2.0,
								shadowOffsetYPt: 3.0,
								shadowBlurPt: 4.0,
								shadowAlpha: 170
							)
						])
					)
				)
			])
		);
	}
}
