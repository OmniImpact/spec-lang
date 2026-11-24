#! Package theosynth:view
#! Centered About modal dialog for TheoSynth.

Class is AboutDialog{
	replace [String] is namespace: ['theosynth', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theosynth', 'util', SynthStrings]
	];

	held Function of Widget is build(FocusTarget is closeFocus, Function is onClose){
		return Center(
			child: Surface(
				child: Panel(
					border: true,
					padX: 2,
					padY: 1,
					topTitle: SynthStrings:ABOUT_TITLE,
					topTitleAlign: TitleAlign:CENTER,
					child: Col(
						gap: 0,
						children: Array([
							TextLine(value: SynthStrings:ABOUT_BODY_1, bold: true),
							TextLine(value: ''),
							TextLine(value: SynthStrings:ABOUT_BODY_2),
							TextLine(value: SynthStrings:ABOUT_BODY_3),
							TextLine(value: SynthStrings:ABOUT_BODY_4),
							TextLine(value: ''),
							TextLine(value: SynthStrings:ABOUT_KEYS),
							TextLine(value: ''),
							Row(
								children: Array([
									Spacer(weight: 1.0),
									Button(
										label: SynthStrings:ACTION_CLOSE,
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
