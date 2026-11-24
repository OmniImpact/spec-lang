#! Package theojack:view
#! Scrollable Rules screen: pure view rendering [RuleItem]s from [RulesViewModel].

Class of Frame is RulesFrame{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theojack', 'model', [Card, RuleItem, RuleKind]],
		['theojack', 'util', HomeStrings],
		['theojack', 'vm', RulesViewModel],
		['theojack', 'view', CardView]
	];

	RulesViewModel is vm: RulesViewModel();
	FocusTarget is doneFocus: FocusTarget(initial: true);

	replace Function is init(RulesViewModel is vm: RulesViewModel()){
		:vm: vm;
	}

	local Function of Array of Widget is buildContentWidgets(){
		local Array of Widget is out: Array();
		local Int is i: 0;
		while({ i < vm:items:length() }, {
			local RuleItem is item: vm:items:get(index: i);
			if({ item:kind == RuleKind:HEADER }, {
				out:add(item: TextLine(
					value: item:text,
					color: activeTheme:accentColor,
					bold: true
				));
			});
			if({ item:kind == RuleKind:TEXT }, {
				out:add(item: TextGraphic(graphic: item:text));
			});
			if({ item:kind == RuleKind:BULLET }, {
				local Array of Widget is bulletRows: Array();
				local Int is bi: 0;
				while({ bi < item:bullets:length() }, {
					bulletRows:add(item: Row(
						gap: 1,
						children: Array([
							TextLine(value: '•', color: activeTheme:accentColor, bold: true),
							TextGraphic(graphic: item:bullets:get(index: bi))
						])
					));
					bi: bi + 1;
				});
				out:add(item: Col(gap: 0, padX: 1, children: bulletRows));
			});
			if({ item:kind == RuleKind:CARDS }, {
				local Array of Widget is rowKids: Array();
				local Int is ci: 0;
				while({ ci < item:cards:length() }, {
					rowKids:add(item: CardView(card: item:cards:get(index: ci), style: vm:cardStyle));
					ci: ci + 1;
				});
				out:add(item: Row(gap: 2, children: rowKids));
			});
			i: i + 1;
		});
		return out;
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() || (event:isChar() && event:key:toLower() == 'd') }, {
			vm:done();
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		Grid(
			orientation: Orientation:VERTICAL,
			panes: Array([
				Grid:weight(
					weight: 1.0,
					child: Panel(
						border: true,
						padX: 0,
						padY: 0,
						scrollable: true,
						verticalScrollbar: ScrollbarMode:AUTO,
						topTitle: HomeStrings:RULES_TITLE,
						topTitleAlign: TitleAlign:CENTER,
						child: Col(
							gap: 1,
							scrollable: true,
							padX: 2,
							padY: 1,
							children: buildContentWidgets()
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
									shortcut: ShortcutKey:ctrl(key: 'd'),
									focusTarget: doneFocus,
									onClick: { vm:done(); }
								)
							])
						)
					)
				)
			])
		);
	}
}
