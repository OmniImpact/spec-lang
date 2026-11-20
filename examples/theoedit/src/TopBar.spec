#! Top bar frame displaying the active file name and status hint.

Class of Frame is TopBar{
	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'theo', Widget],
		['base', 'theo', TheoTheme],
		['base', 'theo', Panel],
		['base', 'theo', Row],
		['base', 'theo', Spacer],
		['base', 'theo', TextLine],
		['base', 'signal', TextEmitter]
	];

	TextEmitter is title;
	TextEmitter is status;
	TheoTheme is theme: TheoTheme();

	replace Function is init(TextEmitter is title, TextEmitter is status, TheoTheme is theme: TheoTheme()){
		:title: title;
		:status: status;
		:theme: theme;
	}

	replace Function of Widget is ui(){
		Panel(
			border: true,
			borderColor: theme:borderColor,
			rounded: theme:roundedBorders,
			padX: 1,
			padY: 0,
			child: Row(
				children: [
					TextLine(
						value: title,
						color: theme:titleColor,
						bold: true
					),
					Spacer(weight: 1.0),
					TextLine(
						value: status,
						color: theme:mutedColor
					)
				]
			)
		);
	}
}
