#! Package theojack:view
#! Options screen for TheoJack: pure view bound to [OptionsViewModel].

Class of Frame is OptionsFrame{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theojack', 'model', [Card, CardStyle, Rank, Suit]],
		['theojack', 'util', HomeStrings],
		['theojack', 'vm', OptionsViewModel],
		['theojack', 'view', CardView]
	];

	OptionsViewModel is vm: OptionsViewModel();
	CardView is previewCard: CardView(card: Card(rank: Rank:ACE, suit: Suit:HEARTS));
	FocusTarget is styleFocus: FocusTarget(initial: true);
	FocusTarget is amountFocus: FocusTarget();
	FocusTarget is roundsFocus: FocusTarget();
	FocusTarget is cancelFocus: FocusTarget();
	FocusTarget is saveFocus: FocusTarget();

	replace Function is init(OptionsViewModel is vm: OptionsViewModel()){
		:vm: vm;
		:previewCard: CardView(
			card: Card(rank: Rank:ACE, suit: Suit:HEARTS),
			style: vm:selectedStyle:current()
		);
		vm:selectedStyle:collect(onEmit: {
			previewCard:setStyle(next: vm:selectedStyle:current());
			invalidate();
		});
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			vm:cancel();
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
									align: 'center',
									children: Array([
										TextLine(value: HomeStrings:OPTION_CARD_STYLE, bold: true, width: 16),
										Dropdown(
											host: :,
											options: [
												CardStyle:WIREFRAME:value(),
												CardStyle:BLACK:value(),
												CardStyle:WHITE:value(),
												CardStyle:METALLIC:value()
											],
											selected: vm:selectedStyle:current():value(),
											width: 15,
											focusTarget: styleFocus,
											onSelect: local Function(String is chosen){
												vm:selectStyleByName(name: chosen);
											}
										)
									])
								),
								Row(
									gap: 2,
									align: 'center',
									children: Array([
										TextLine(value: HomeStrings:OPTION_STARTING_AMOUNT, bold: true, width: 16),
										Surface(
											background: activeTheme:buttonBg,
											width: 15,
											padX: 1,
											child: Row(
												gap: 0,
												children: Array([
													TextLine(value: '$', bold: true),
													TextInput(
														value: vm:selectedAmount:current() as String,
														placeholder: '500',
														width: 12,
														focusTarget: amountFocus,
														onChange: local Function(String is typed){
															vm:selectAmountText(raw: typed);
														}
													)
												])
											)
										)
									])
								),
								Row(
									gap: 2,
									align: 'center',
									children: Array([
										TextLine(value: HomeStrings:OPTION_NUM_ROUNDS, bold: true, width: 16),
										Dropdown(
											host: :,
											options: ['5', '10', '20', '50'],
											selected: vm:selectedRounds:current() as String,
											width: 15,
											focusTarget: roundsFocus,
											onSelect: local Function(String is chosen){
												vm:selectRounds(next: chosen as Int);
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
									onClick: { vm:cancel(); }
								),
								Spacer(weight: 1.0),
								Button(
									label: HomeStrings:LABEL_SAVE,
									shortcutKey: 's',
									focusTarget: saveFocus,
									onClick: { vm:save(); }
								)
							])
						)
					)
				)
			])
		);
	}
}
