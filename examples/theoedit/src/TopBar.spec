#! Top bar frame displaying the active file name and status hint.

Class of Frame is TopBar{
	replace Array of Array of String is using: [
		['base', 'theo', [Frame, Widget, Panel, Row, Spacer, TextLine]],
		['base', 'signal', TextEmitter]
	];

	TextEmitter is title;
	TextEmitter is status;

	replace Function is init(TextEmitter is title, TextEmitter is status){
		:title: title;
		:status: status;
	}

	replace Function of Widget is ui(){
		Panel(
			border: true,
			padX: 1,
			padY: 0,
			child: Row(
				children: [
					TextLine(
						value: title,
						color: activeTheme:titleColor,
						bold: true
					),
					Spacer(weight: 1.0),
					TextLine(
						value: status,
						color: activeTheme:mutedColor
					)
				]
			)
		);
	}
}
