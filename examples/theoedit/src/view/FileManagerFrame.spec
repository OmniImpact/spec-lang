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

	FileManagerViewModel is vm: FileManagerViewModel();

	FocusTarget is listFocus: FocusTarget(initial: true);
	FocusTarget is inputFocus: FocusTarget();
	FocusTarget is okFocus: FocusTarget();
	FocusTarget is cancelFocus: FocusTarget();

	Array of ListView is listViews: Array();
	Array of TextInput is nameInputs: Array();

	replace Function is init(FileManagerViewModel is vm: FileManagerViewModel()){
		:vm: vm;
		if({ vm:isSaveAs() }, {
			listFocus: FocusTarget(initial: false);
			inputFocus: FocusTarget(initial: true);
		});

		local ListView is lv: ListView(
			items: vm:entries,
			focusTarget: listFocus,
			onActivate: local Function(String is entry){
				vm:activateEntry(
					entry: entry,
					onListUpdated: local Function(Array of String is nextItems){
						if({ listViews:length() > 0 }, {
							listViews:get(index: 0):setItems(nextItems: nextItems);
						});
					},
					onFileChosen: local Function(String is fileName){
						if({ nameInputs:length() > 0 }, {
							nameInputs:get(index: 0):setText(value: fileName);
						});
					}
				);
			},
			onSelectChange: local Function(String is entry){
				vm:selectEntry(entry: entry, onFileSelected: local Function(String is fileName){
					if({ nameInputs:length() > 0 }, {
						nameInputs:get(index: 0):setText(value: fileName);
					});
				});
			}
		);
		listViews: Array([lv]);

		local TextInput is ti: TextInput(
			value: vm:initialName,
			placeholder: 'filename',
			focusTarget: inputFocus,
			onSubmit: local Function(String is typed){
				vm:confirm(typedName: typed);
			}
		);
		nameInputs: Array([ti]);
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			vm:cancel();
			return true;
		});
		if({ (event:ctrl || event:alt) && event:key == 'm' }, {
			if({ okFocus:focused || cancelFocus:focused }, {
				if({ vm:isSaveAs() }, {
					inputFocus:requestFocus();
				}, {
					listFocus:requestFocus();
				});
			}, {
				okFocus:requestFocus();
			});
			return true;
		});
		if({ (event:ctrl || event:alt) && event:key == 'f' }, {
			if({ listFocus:focused }, {
				inputFocus:requestFocus();
			}, {
				listFocus:requestFocus();
			});
			return true;
		});
		if({ (okFocus:focused || cancelFocus:focused) && event:isUp() }, {
			inputFocus:requestFocus();
			return true;
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
