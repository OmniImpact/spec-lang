#! Package theojack:view
#! Options screen for TheoJack with Card Style, Starting Amount, and Rounds selectors, live centered card preview, and Cancel/Save actions.

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
	Int is selectedAmount: 500;
	Int is selectedRounds: 10;
	CardView is previewCard: CardView(card: Card(rank: Rank:ACE, suit: Suit:HEARTS));
	FocusTarget is styleFocus: FocusTarget(initial: true);
	FocusTarget is amountFocus: FocusTarget();
	FocusTarget is roundsFocus: FocusTarget();
	FocusTarget is cancelFocus: FocusTarget();
	FocusTarget is saveFocus: FocusTarget();
	Function is onCancel: {};
	Function is onSave: local Function(CardStyle is _s){};

	replace Function is init(
		OptionsStorage is storage: OptionsStorage(),
		CardStyle is initialStyle: CardStyle:WIREFRAME,
		Int is initialAmount: 500,
		Int is initialRounds: 10,
		Function is onCancel: {},
		Function is onSave: local Function(CardStyle is _s){}
	){
		:storage: storage;
		:selectedStyle: initialStyle;
		:selectedAmount: initialAmount;
		:selectedRounds: initialRounds;
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

	Function is selectAmount(Int is next){
		:selectedAmount: next;
		invalidate();
	}

	Function is selectRounds(Int is next){
		:selectedRounds: next;
		invalidate();
	}

	Function is saveAndClose(){
		storage:save(style: selectedStyle, startingAmount: selectedAmount, numRounds: selectedRounds);
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
											focusTarget: styleFocus,
											onSelect: local Function(String is chosen){
												selectStyle(next: storage:styleFromName(name: chosen));
											}
										)
									])
								),
								Row(
									gap: 2,
									children: Array([
										TextLine(value: HomeStrings:OPTION_STARTING_AMOUNT, bold: true),
										Dropdown(
											host: :,
											options: ['100', '500', '1000', '2500'],
											selected: selectedAmount as String,
											focusTarget: amountFocus,
											onSelect: local Function(String is chosen){
												selectAmount(next: chosen as Int);
											}
										)
									])
								),
								Row(
									gap: 2,
									children: Array([
										TextLine(value: HomeStrings:OPTION_NUM_ROUNDS, bold: true),
										Dropdown(
											host: :,
											options: ['5', '10', '20', '50'],
											selected: selectedRounds as String,
											focusTarget: roundsFocus,
											onSelect: local Function(String is chosen){
												selectRounds(next: chosen as Int);
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
