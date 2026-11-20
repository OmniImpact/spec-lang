#! File manager screen for Open and Save As, pushed onto [TheoScreen].

Class of Frame is FileManagerFrame{
	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'theo', Widget],
		['base', 'theo', Grid],
		['base', 'theo', Panel],
		['base', 'theo', Row],
		['base', 'theo', Spacer],
		['base', 'theo', TextLine],
		['base', 'theo', TextInput],
		['base', 'theo', ListView],
		['base', 'theo', Button],
		['base', 'theo', FocusTarget],
		['base', 'theo', KeyEvent],
		['base', 'theo', TheoTheme],
		['base', 'signal', TextEmitter],
		['base', 'sys', as Dir()],
		['base', 'sys', as Uri()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is mode: 'open';
	String is curDir: '.';
	TheoTheme is theme: TheoTheme();
	Function is onConfirm;
	Function is onCancel;

	TextEmitter is headerTitle: TextEmitter(initial: 'File Manager');
	FocusTarget is listFocus: FocusTarget(initial: true);
	FocusTarget is inputFocus: FocusTarget();
	FocusTarget is okFocus: FocusTarget();
	FocusTarget is cancelFocus: FocusTarget();

	Array of String is dirEntries: [];
	Array of ListView is listViews: [];
	Array of TextInput is nameInputs: [];

	replace Function is init(
		String is mode: 'open',
		String is initialDir: '.',
		String is initialName: '',
		Function is onConfirm,
		Function is onCancel,
		TheoTheme is theme: TheoTheme()
	){
		:mode: mode;
		:curDir: Uri:fromFilePath(filePath: initialDir):toFilePath();
		:onConfirm: onConfirm;
		:onCancel: onCancel;
		:theme: theme;
		if({ mode == 'saveAs' }, {
			:listFocus: FocusTarget(initial: false);
			:inputFocus: FocusTarget(initial: true);
		});
		:dirEntries: buildEntries(dir: :curDir);
		headerTitle:emit(value: "File Manager — {{:curDir}}");

		local ListView is lv: ListView(
			items: :dirEntries,
			focusTarget: listFocus,
			fg: theme:foreground,
			selectedFg: theme:buttonFocusFg,
			selectedBg: theme:buttonFocusBg
		);
		lv:bindOnActivate(cb: local Function(String is entry){
			handleEntryActivate(entry: entry);
		});
		lv:bindOnSelectChange(cb: local Function(String is entry){
			if({ entry != '..' && !entry:endsWith(suffix: '/') && nameInputs:length() > 0 }, {
				nameInputs:get(index: 0):setText(value: entry);
			});
		});
		:listViews: [lv];

		local TextInput is ti: TextInput(
			value: initialName,
			placeholder: 'filename',
			focusTarget: inputFocus,
			fg: theme:titleColor,
			placeholderFg: theme:mutedColor
		);
		ti:bindOnSubmit(cb: local Function(String is typed){
			submitCurrent();
		});
		:nameInputs: [ti];
	}

	local Function of Array of String is buildEntries(String is dir){
		local Array of String is out: ['..'];
		Dir:dirList(path: dir):each(action: local Function(String is name){
			if({ name:startsWith(prefix: '.') }, { return; });
			local String is full: "{{dir}}/{{name}}";
			if({ Dir:dirList(path: full):length() > 0 }, {
				out:add(item: "{{name}}/");
			}, {
				out:add(item: name);
			});
		});
		return out;
	}

	local Function is navigateTo(String is nextDir){
		:curDir: nextDir;
		:dirEntries: buildEntries(dir: curDir);
		if({ listViews:length() > 0 }, {
			listViews:get(index: 0):setItems(nextItems: dirEntries);
		});
		headerTitle:emit(value: "File Manager — {{curDir}}");
	}

	local Function is handleEntryActivate(String is entry){
		if({ entry == '..' }, {
			local Array of String is parts: curDir:split(delimiter: '/');
			if({ parts:length() > 2 }, {
				parts:removeAt(index: parts:length() - 1);
				navigateTo(nextDir: parts:join(sep: '/'));
			}, {
				navigateTo(nextDir: '/');
			});
			return;
		});
		if({ entry:endsWith(suffix: '/') }, {
			local String is sub: entry:substring(start: 0, end: entry:length() - 1);
			local String is next: if({ curDir == '/' }, { "/{{sub}}" }, { "{{curDir}}/{{sub}}" });
			navigateTo(nextDir: next);
			return;
		});
		if({ nameInputs:length() > 0 }, {
			nameInputs:get(index: 0):setText(value: entry);
		});
		submitCurrent();
	}

	local Function is submitCurrent(){
		if({ nameInputs:length() == 0 }, { return; });
		local String is typed: nameInputs:get(index: 0):text:trim();
		if({ typed == '' }, { return; });
		local String is full: if({ typed:startsWith(prefix: '/') }, { typed }, {
			if({ curDir == '/' }, { "/{{typed}}" }, { "{{curDir}}/{{typed}}" })
		});
		local Function is fn: onConfirm;
		fn(full);
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			local Function is fn: onCancel;
			fn();
			return true;
		});
		if({ (event:ctrl || event:alt) && event:key == 'm' }, {
			if({ okFocus:focused || cancelFocus:focused }, {
				if({ mode == 'saveAs' }, {
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
		if({ okFocus:focused || cancelFocus:focused }, {
			if({ event:isUp() }, {
				inputFocus:requestFocus();
				return true;
			});
			if({ event:isLeft() }, {
				cancelFocus:requestFocus();
				return true;
			});
			if({ event:isRight() }, {
				okFocus:requestFocus();
				return true;
			});
		});
		return false;
	}

	replace Function of Widget is ui(){
		local String is actionLabel: if({ mode == 'saveAs' }, { ' Save ' }, { ' Open ' });
		local String is actionKey: if({ mode == 'saveAs' }, { 's' }, { 'o' });

		Grid(
			orientation: 'vertical',
			panes: [
				Grid:fixed(
					size: 3,
					child: Panel(
						border: true,
						borderColor: theme:borderColor,
						rounded: theme:roundedBorders,
						padX: 1,
						padY: 0,
						child: Row(
							children: [
								TextLine(
									value: headerTitle,
									color: theme:titleColor,
									bold: true
								),
								Spacer(weight: 1.0),
								TextLine(
									value: 'Ctrl+M: menu · Ctrl+F: files/name',
									color: theme:mutedColor
								)
							]
						)
					)
				),
				Grid:weight(
					weight: 1.0,
					child: Panel(
						border: true,
						borderColor: theme:borderColor,
						rounded: theme:roundedBorders,
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
						borderColor: theme:borderColor,
						rounded: theme:roundedBorders,
						padX: 1,
						padY: 0,
						child: Row(
							gap: 1,
							children: [
								TextLine(
									value: 'Name: ',
									color: theme:mutedColor
								),
								nameInputs:get(index: 0)
							]
						)
					)
				),
				Grid:fixed(
					size: 3,
					child: Panel(
						border: true,
						borderColor: theme:borderColor,
						rounded: theme:roundedBorders,
						padX: 1,
						padY: 0,
						child: Row(
							gap: 2,
							children: [
								Button(
									label: ' Cancel ',
									shortcutKey: 'c',
									focusTarget: cancelFocus,
									fg: theme:buttonFg,
									bg: theme:buttonBg,
									focusFg: theme:buttonFocusFg,
									focusBg: theme:buttonFocusBg,
									onClick: onCancel
								),
								Spacer(weight: 1.0),
								Button(
									label: actionLabel,
									shortcutKey: actionKey,
									focusTarget: okFocus,
									fg: theme:buttonFg,
									bg: theme:buttonBg,
									focusFg: theme:buttonFocusFg,
									focusBg: theme:buttonFocusBg,
									onClick: {
										submitCurrent();
									}
								)
							]
						)
					)
				)
			]
		);
	}
}
