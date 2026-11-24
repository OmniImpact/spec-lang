#! Package theojack:view
#! Scrollable Rules screen displaying JSON-driven text, headers, and example card hands.

Class of Frame is RulesFrame{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theojack', 'model', CardStyle],
		['theojack', 'util', [HomeStrings, RulesLoader]]
	];

	RulesLoader is loader: RulesLoader();
	CardStyle is cardStyle: CardStyle:WIREFRAME;
	FocusTarget is doneFocus: FocusTarget(initial: true);
	Function is onDone: {};

	replace Function is init(
		RulesLoader is loader: RulesLoader(),
		CardStyle is cardStyle: CardStyle:WIREFRAME,
		Function is onDone: {}
	){
		:loader: loader;
		:cardStyle: cardStyle;
		:onDone: onDone;
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() || (event:isChar() && event:key:toLower() == 'd') }, {
			onDone();
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		local Array of Widget is contentWidgets: loader:loadWidgets(style: cardStyle);
		Grid(
			orientation: 'vertical',
			panes: Array([
				Grid:weight(
					weight: 1.0,
					child: Panel(
						border: true,
						padX: 0,
						padY: 0,
						scrollable: true,
						verticalScrollbar: 'auto',
						topTitle: HomeStrings:RULES_TITLE,
						topTitleAlign: 'center',
						titleFg: TheoColor:ansi(code: 16),
						titleBg: TheoColor:ansi(code: 252),
						child: Col(
							gap: 1,
							scrollable: true,
							padX: 2,
							padY: 1,
							children: contentWidgets
						)
					)
				),
				Grid:fixed(
					size: 3,
					child: Panel(
						border: true,
						padX: 1,
						padY: 0,
						child: Row(
							children: Array([
								Spacer(weight: 1.0),
								Button(
									label: HomeStrings:LABEL_DONE,
									shortcutKey: 'd',
									focusTarget: doneFocus,
									onClick: { onDone(); }
								)
							])
						)
					)
				)
			])
		);
	}
}
