#! Package theofractal:view
#! Centered Help dialog widget showing About info and keyboard shortcuts.

Class is HelpDialog{
	replace [String] is namespace: ['theofractal', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theofractal', 'util', FractalStrings]
	];

	held Function of Widget is build(FocusTarget is closeFocus, Function is onClose){
		return Center(
			child: Surface(
				child: Panel(
					border: true,
					padX: 2,
					padY: 1,
					topTitle: FractalStrings:HELP_TITLE,
					topTitleAlign: TitleAlign:CENTER,
					child: Col(
						gap: 0,
						children: Array([
							TextLine(value: FractalStrings:HELP_ABOUT_HDR, bold: true),
							TextLine(value: FractalStrings:HELP_ABOUT_1),
							TextLine(value: FractalStrings:HELP_ABOUT_2),
							TextLine(value: FractalStrings:HELP_ABOUT_3),
							TextLine(value: FractalStrings:HELP_ABOUT_4),
							TextLine(value: ''),
							TextLine(value: FractalStrings:HELP_KEYS_HDR, bold: true),
							TextLine(value: FractalStrings:HELP_KEY_PAN),
							TextLine(value: FractalStrings:HELP_KEY_ZOOM),
							TextLine(value: FractalStrings:HELP_KEY_RESET),
							TextLine(value: FractalStrings:HELP_KEY_HELP),
							TextLine(value: FractalStrings:HELP_KEY_NAV),
							TextLine(value: ''),
							Row(
								children: Array([
									Spacer(weight: 1.0),
									Button(
										label: FractalStrings:ACTION_CLOSE,
										focusTarget: closeFocus,
										onClick: onClose
									),
									Spacer(weight: 1.0)
								])
							)
						])
					)
				)
			)
		);
	}
}
