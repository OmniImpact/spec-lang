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
	Function is onConfirm;
	Function is onCancel;

	FocusTarget is listFocus: FocusTarget(initial: true);
	FocusTarget is inputFocus: FocusTarget();
	FocusTarget is okFocus: FocusTarget();
	FocusTarget is cancelFocus: FocusTarget();

	Array of ListView is listViews: Array();
	Array of TextInput is nameInputs: Array();

	replace Function is init(
		String is mode: 'open',
		String is initialDir: '.',
		String is initialName: '',
		Function is onConfirm,
		Function is onCancel
	){
		:onConfirm: onConfirm;
		:onCancel: onCancel;
		vm: FileManagerViewModel(mode: mode, initialDir: initialDir, initialName: initialName);
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
						submitCurrent();
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
			onSubmit: local Function(String is _typed){
				submitCurrent();
			}
		);
		nameInputs: Array([ti]);
	}

	local Function is submitCurrent(){
		if({ nameInputs:length() == 0 }, { return; });
		vm:submit(typedName: nameInputs:get(index: 0):text, onConfirmed: onConfirm);
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			onCancel();
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
									onClick: onCancel
								),
								Spacer(weight: 1.0),
								Button(
									label: vm:actionLabel(),
									shortcutKey: vm:actionKey(),
									focusTarget: okFocus,
									onClick: { submitCurrent(); }
								)
							])
						)
					)
				)
			])
		);
	}
}
