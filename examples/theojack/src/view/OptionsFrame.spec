#! Package theojack:view
#! Options screen for TheoJack with Card Style selection, live centered card preview, and Cancel/Save actions.

Class of Frame is OptionsFrame{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theojack', 'model', [Card, CardStyle, Rank, Suit]],
		['theojack', 'util', [HomeStrings, OptionsStorage]],
		['theojack', 'view', CardView]
	];

	OptionsStorage is storage: OptionsStorage();
	CardStyle is selectedStyle: CardStyle:WIREFRAME;
	CardView is previewCard: CardView(card: Card(rank: Rank:ACE, suit: Suit:HEARTS));
	FocusTarget is styleFocus: FocusTarget(initial: true);
	FocusTarget is cancelFocus: FocusTarget();
	FocusTarget is saveFocus: FocusTarget();
	Function is onCancel: {};
	Function is onSave: local Function(CardStyle is _s){};

	replace Function is init(
		OptionsStorage is storage: OptionsStorage(),
		CardStyle is initialStyle: CardStyle:WIREFRAME,
		Function is onCancel: {},
		Function is onSave: local Function(CardStyle is _s){}
	){
		:storage: storage;
		:selectedStyle: initialStyle;
		:onCancel: onCancel;
		:onSave: onSave;
		:previewCard: CardView(
			card: Card(rank: Rank:ACE, suit: Suit:HEARTS),
			style: initialStyle
		);
	}

	Function is selectStyle(CardStyle is next){
		:selectedStyle: next;
		previewCard:setStyle(next: next);
		invalidate();
	}

	Function is saveAndClose(){
		storage:saveCardStyle(style: selectedStyle);
		onSave(selectedStyle);
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			onCancel();
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		Grid(
			orientation: 'vertical',
			panes: Array([
				Grid:weight(
					weight: 1.0,
					child: Panel(
						border: true,
						padX: 2,
						padY: 1,
						topTitle: HomeStrings:OPTIONS_TITLE,
						topTitleAlign: 'center',
						titleFg: TheoColor:ansi(code: 16),
						titleBg: TheoColor:ansi(code: 252),
						child: Col(
							gap: 1,
							children: Array([
								Row(
									gap: 2,
									children: Array([
										TextLine(value: HomeStrings:OPTION_CARD_STYLE, bold: true),
										Dropdown(
											host: :,
											options: [
												CardStyle:WIREFRAME:value(),
												CardStyle:BLACK:value(),
												CardStyle:WHITE:value(),
												CardStyle:METALLIC:value()
											],
											selected: selectedStyle:value(),
											width: 14,
											focusTarget: styleFocus,
											onSelect: local Function(String is chosen){
												selectStyle(next: storage:styleFromName(name: chosen));
											}
										)
									])
								),
								Spacer(weight: 1.0),
								Row(
									children: Array([
										Spacer(weight: 1.0),
										previewCard,
										Spacer(weight: 1.0)
									])
								)
							])
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
							arrowFocus: true,
							children: Array([
								Button(
									label: HomeStrings:LABEL_CANCEL,
									shortcutKey: 'c',
									focusTarget: cancelFocus,
									onClick: { onCancel(); }
								),
								Spacer(weight: 1.0),
								Button(
									label: HomeStrings:LABEL_SAVE,
									shortcutKey: 's',
									focusTarget: saveFocus,
									onClick: { saveAndClose(); }
								)
							])
						)
					)
				)
			])
		);
	}
}
