#! Package theojack:view
#! Home screen for TheoJack: centered playing card beside the main menu.

Class of Frame is HomeFrame{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theojack', 'util', HomeStrings]
	];

	FocusTarget is playFocus: FocusTarget(initial: true);
	FocusTarget is rulesFocus: FocusTarget();
	FocusTarget is aboutFocus: FocusTarget();
	FocusTarget is quitFocus: FocusTarget();
	Function is onQuit: {};

	replace Function is init(Function is onQuit: {}){
		:onQuit: onQuit;
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() || (event:isChar() && event:key:toLower() == 'q') }, {
			onQuit();
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		local Int is w: HomeStrings:CARD_WIDTH;
		Center(
			child: Row(
				gap: 3,
				children: Array([
					TextGraphic(
						graphic: HomeStrings:HERO_CARD
					),
					Col(
						gap: 1,
						arrowFocus: true,
						children: Array([
							Button(
								label: HomeStrings:MENU_PLAY,
								shortcutKey: 'p',
								width: w,
								focusTarget: playFocus,
								onClick: {}
							),
							Button(
								label: HomeStrings:MENU_RULES,
								shortcutKey: 'r',
								width: w,
								focusTarget: rulesFocus,
								onClick: {}
							),
							Button(
								label: HomeStrings:MENU_ABOUT,
								shortcutKey: 'a',
								width: w,
								focusTarget: aboutFocus,
								onClick: {}
							),
							Button(
								label: HomeStrings:MENU_QUIT,
								shortcutKey: 'q',
								width: w,
								focusTarget: quitFocus,
								onClick: { onQuit(); }
							)
						])
					)
				])
			)
		);
	}
}
