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
		local Widget is styleControl: Dropdown(
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
		);
		local Widget is styleRow: Row(
			gap: 2,
			align: 'center',
			children: Array([
				TextLine(value: HomeStrings:OPTION_CARD_STYLE, bold: true, width: 16),
				styleControl
			])
		);

		local Widget is amountInput: TextInput(
			value: vm:selectedAmount:current() as String,
			placeholder: '500',
			width: 12,
			focusTarget: amountFocus,
			onChange: local Function(String is typed){
				vm:selectAmountText(raw: typed);
			}
		);
		local Widget is amountBox: Surface(
			background: activeTheme:buttonBg,
			width: 15,
			padX: 1,
			child: Row(
				gap: 0,
				children: Array([TextLine(value: '$', bold: true), amountInput])
			)
		);
		local Widget is amountRow: Row(
			gap: 2,
			align: 'center',
			children: Array([
				TextLine(value: HomeStrings:OPTION_STARTING_AMOUNT, bold: true, width: 16),
				amountBox
			])
		);

		local Widget is roundsControl: Dropdown(
			host: :,
			options: ['5', '10', '20', '50'],
			selected: vm:selectedRounds:current() as String,
			width: 15,
			focusTarget: roundsFocus,
			onSelect: local Function(String is chosen){
				vm:selectRounds(next: chosen as Int);
			}
		);
		local Widget is roundsRow: Row(
			gap: 2,
			align: 'center',
			children: Array([
				TextLine(value: HomeStrings:OPTION_NUM_ROUNDS, bold: true, width: 16),
				roundsControl
			])
		);

		local Widget is previewRow: Row(
			children: Array([Spacer(weight: 1.0), previewCard, Spacer(weight: 1.0)])
		);

		local Widget is bodyPanel: Panel(
			border: true,
			padX: 2,
			padY: 1,
			topTitle: HomeStrings:OPTIONS_TITLE,
			topTitleAlign: 'center',
			child: Col(
				gap: 1,
				children: Array([styleRow, amountRow, roundsRow, Spacer(weight: 1.0), previewRow])
			)
		);

		local Widget is cancelBtn: Button(
			label: HomeStrings:LABEL_CANCEL,
			shortcut: ShortcutKey:ctrl(key: 'c'),
			focusTarget: cancelFocus,
			onClick: { vm:cancel(); }
		);
		local Widget is saveBtn: Button(
			label: HomeStrings:LABEL_SAVE,
			shortcut: ShortcutKey:ctrl(key: 's'),
			focusTarget: saveFocus,
			onClick: { vm:save(); }
		);
		local Widget is footerPanel: Panel(
			border: true,
			padX: 1,
			padY: 0,
			child: Row(
				arrowFocus: true,
				children: Array([cancelBtn, Spacer(weight: 1.0), saveBtn])
			)
		);

		Grid(
			orientation: 'vertical',
			panes: Array([
				Grid:weight(weight: 1.0, child: bodyPanel),
				Grid:fixed(size: 3, child: footerPanel)
			])
		);
	}
}
