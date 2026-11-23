#! Package theoedit:view
#! File manager screen for Open and Save As, pushed onto [TheoScreen].
#! Pure view: delegates directory listing, navigation, and path resolution
#! to [FileManagerViewModel].

Class of Frame is FileManagerFrame{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', '*'],
		['theoedit', 'vm', FileManagerViewModel]
	];

	FileManagerViewModel is vm;

	FocusTarget is listFocus: FocusTarget(initial: true);
	FocusTarget is inputFocus: FocusTarget();
	FocusTarget is okFocus: FocusTarget();
	FocusTarget is cancelFocus: FocusTarget();

	Array of ListView is listViews: Array();
	Array of TextInput is nameInputs: Array();

	replace Function is init(FileManagerViewModel is vm){
		:vm: vm;
		if({ vm:isSaveAs() }, {
			listFocus: FocusTarget(initial: false);
			inputFocus: FocusTarget(initial: true);
		});

		local ListView is lv: ListView(
			items: vm:entries,
			focusTarget: listFocus,
			onActivate: local Function(String is entry){ vm:activateEntry(entry: entry); },
			onSelectChange: local Function(String is entry){ vm:selectEntry(entry: entry); }
		);
		listViews: Array([lv]);

		local TextInput is ti: TextInput(
			value: vm:initialName,
			placeholder: 'filename',
			focusTarget: inputFocus,
			onSubmit: local Function(String is typed){ vm:confirm(typedName: typed); }
		);
		nameInputs: Array([ti]);

		vm:onListUpdated: local Function(Array of String is nextItems){
			lv:setItems(nextItems: nextItems);
		};
		vm:onNameUpdated: local Function(String is fileName){
			ti:setText(value: fileName);
		};
		vm:listFocused:collect(onEmit: {
			if({ vm:listFocused:current() }, { listFocus:requestFocus(); });
		});
		vm:inputFocused:collect(onEmit: {
			if({ vm:inputFocused:current() }, { inputFocus:requestFocus(); });
		});
		vm:okFocused:collect(onEmit: {
			if({ vm:okFocused:current() }, { okFocus:requestFocus(); });
		});
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			vm:handleEscKey();
			return true;
		});
		if({ (event:ctrl || event:alt) && event:key == 'm' }, {
			vm:handleMenuKey(actionsFocused: okFocus:focused || cancelFocus:focused);
			return true;
		});
		if({ (event:ctrl || event:alt) && event:key == 'f' }, {
			vm:handleFocusToggleKey(listIsFocused: listFocus:focused);
			return true;
		});
		if({ event:isUp() }, {
			return vm:handleUpFromActions(actionsFocused: okFocus:focused || cancelFocus:focused);
		});
		false;
	}

	replace Function of Widget is ui(){
		Grid(
			orientation: 'vertical',
			panes: Array([
				Grid:fixed(
					size: 3,
					child: Panel(
						border: true,
						padX: 1,
						padY: 0,
						child: Row(
							children: Array([
								TextLine(
									value: vm:headerTitle,
									color: activeTheme:titleColor,
									bold: true
								),
								Spacer(weight: 1.0),
								TextLine(
									value: 'Ctrl+M: menu · Ctrl+F: files/name',
									color: activeTheme:mutedColor
								)
							])
						)
					)
				),
				Grid:weight(
					weight: 1.0,
					child: Panel(
						border: true,
						padX: 1,
						padY: 0,
						scrollable: true,
						child: listViews:get(index: 0)
					)
				),
				Grid:fixed(
					size: 3,
					child: Panel(
						border: true,
						padX: 1,
						padY: 0,
						child: Row(
							gap: 1,
							children: Array([
								TextLine(
									value: 'Name: ',
									color: activeTheme:mutedColor
								),
								nameInputs:get(index: 0)
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
							gap: 2,
							arrowFocus: true,
							children: Array([
								Button(
									label: ' Cancel ',
									shortcutKey: 'c',
									focusTarget: cancelFocus,
									onClick: { vm:cancel(); }
								),
								Spacer(weight: 1.0),
								Button(
									label: vm:actionLabel(),
									shortcutKey: vm:actionKey(),
									focusTarget: okFocus,
									onClick: {
										if({ nameInputs:length() > 0 }, {
											vm:confirm(typedName: nameInputs:get(index: 0):text);
										});
									}
								)
							])
						)
					)
				)
			])
		);
	}
}
