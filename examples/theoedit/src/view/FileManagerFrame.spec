#! Package theoedit:view
#! File manager screen for Open and Save As, pushed onto [TheoScreen].
#! Pure view: delegates directory listing, navigation, and path resolution
#! to [FileManagerViewModel].

Class of Frame is FileManagerFrame{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', '*'],
		['base', 'sys', as Loops()],
		['theoedit', 'util', [EditorStrings, FileManagerFocus]],
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
			placeholder: EditorStrings:FILE_MANAGER_PLACEHOLDER,
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

		local [FocusTarget] is targets: [listFocus, inputFocus, okFocus, cancelFocus];
		local [FileManagerFocus] is focusIds: [FileManagerFocus:LIST, FileManagerFocus:INPUT, FileManagerFocus:OK, FileManagerFocus:CANCEL];

		times(count: targets:length(), worker: local Function(Int is i){
			local FocusTarget is ft: targets:get(index: i);
			local FileManagerFocus is fid: focusIds:get(index: i);
			ft:onFocus(handler: {
				vm:setFocus(target: fid);
			});
			ft:onHover(handler: {
				vm:setHover(target: fid, isHovered: ft:hovered);
			});
		});

		vm:focus:collect(onEmit: {
			local FileManagerFocus is cur: vm:focus:current();
			times(count: targets:length(), worker: local Function(Int is i){
				local FocusTarget is ft: targets:get(index: i);
				if({ focusIds:get(index: i) == cur }, {
					if({ !ft:focused }, {
						ft:requestFocus();
					});
				}, {
					ft:focused: false;
				});
			});
		});
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			vm:handleEscKey();
			return true;
		});
		if({ (event:ctrl || event:alt) && event:key == 'm' }, {
			vm:handleMenuKey();
			return true;
		});
		if({ (event:ctrl || event:alt) && event:key == 'f' }, {
			vm:handleFocusToggleKey();
			return true;
		});
		if({ event:isUp() }, {
			return vm:handleUpFromActions();
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
									value: EditorStrings:FILE_MANAGER_HINTS,
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
									value: EditorStrings:FILE_MANAGER_NAME_LABEL,
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
									label: EditorStrings:LABEL_CANCEL,
									shortcutKey: EditorStrings:KEY_CANCEL,
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
