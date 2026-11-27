#! Package suitshowcase:view
#! Showcase page for the 2D Grid layout container: auto-sized columns, equalCols tiles, and flex columns.

Class is GridPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Grid],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', Switch],
		['base', 'scrap', TextInput],
		['base', 'scrap', SectionV],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	TextEmitter is tileStatus: TextEmitter(initial: 'Selected tile: None');

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		local Array of SewNode is formGridCells: Array([
			Label(text: 'Field', bold: true),
			Label(text: 'Control', bold: true),
			Label(text: 'Notes', bold: true),
			Label(text: 'Project Name'),
			TextInput(text: 'SuitShowcase', minWidthPt: 110.0),
			TextScrap(text: TextEmitter(initial: 'Auto-sized column 1'), muted: true),
			Label(text: 'Auto-Save'),
			Switch(checked: true),
			TextScrap(text: TextEmitter(initial: 'Vertically centered cells'), muted: true),
			Label(text: 'Version'),
			TextInput(text: '0.1.0', minWidthPt: 110.0),
			TextScrap(text: TextEmitter(initial: 'Uniform column widths'), muted: true)
		]);

		local Array of String is tileNames: Array([
			'Alpha', 'Beta', 'Gamma', 'Delta',
			'Epsilon', 'Zeta', 'Eta', 'Theta'
		]);
		local Array of SewNode is tileCells: Array();
		times(count: tileNames:length(), worker: local Function(Int is i){
			local String is name: tileNames:get(index: i);
			tileCells:add(item: ScrapButton(
				label: name,
				tooltip: 'Select tile ' . name,
				onClick: local Function(){
					tileStatus:emit(value: 'Selected tile: ' . name);
					vm:statusText:emit(value: 'Grid tile clicked: ' . name);
				}
			));
		});

		local Array of SewNode is flexGridCells: Array([
			Label(text: 'Host'),
			TextInput(text: 'localhost', minWidthPt: 80.0),
			Label(text: 'Endpoint'),
			TextInput(text: '/api/v1/showcase', minWidthPt: 80.0)
		]);

		return SectionV(
			children: Array([
				Label(text: 'Grid Layout', heading: true),
				Frame(
					title: 'Auto-Sized Columns (3x4)',
					child: Grid(
						columns: 3,
						colGapPt: 12.0,
						rowGapPt: 6.0,
						children: formGridCells
					)
				),
				Frame(
					title: 'Equal-Width Tile Grid (equalCols: true, 4 columns)',
					child: SectionV(
						children: Array([
							Grid(
								columns: 4,
								colGapPt: 6.0,
								rowGapPt: 6.0,
								equalCols: true,
								children: tileCells
							),
							TextScrap(text: tileStatus, muted: true)
						])
					)
				),
				Frame(
					title: 'Flex Column Grid (flexCols: [false, true])',
					child: Grid(
						columns: 2,
						colGapPt: 10.0,
						rowGapPt: 6.0,
						flexCols: Array([false, true]),
						children: flexGridCells
					)
				)
			])
		);
	}
}
