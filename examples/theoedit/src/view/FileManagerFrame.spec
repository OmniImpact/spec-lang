#! Package theoedit:view
#! File manager screen for Open and Save As, pushed onto [TheoScreen].

Class of Frame is FileManagerFrame{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', '*'],
		['base', 'signal', TextEmitter],
		['base', 'sys', as Dir()],
		['base', 'sys', as Uri()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is mode: 'open';
	String is curDir: '.';
	Function is onConfirm;
	Function is onCancel;

	TextEmitter is headerTitle: TextEmitter(initial: 'File Manager');
	FocusTarget is listFocus: FocusTarget(initial: true);
	FocusTarget is inputFocus: FocusTarget();
	FocusTarget is okFocus: FocusTarget();
	FocusTarget is cancelFocus: FocusTarget();

	Array of String is dirEntries: Array();
	Array of ListView is listViews: Array();
	Array of TextInput is nameInputs: Array();

	replace Function is init(
		String is mode: 'open',
		String is initialDir: '.',
		String is initialName: '',
		Function is onConfirm,
		Function is onCancel
	){
		:mode: mode;
		curDir: Uri:fromFilePath(filePath: initialDir):toFilePath();
		:onConfirm: onConfirm;
		:onCancel: onCancel;
		if({ mode == 'saveAs' }, {
			listFocus: FocusTarget(initial: false);
			inputFocus: FocusTarget(initial: true);
		});
		dirEntries: buildEntries(dir: curDir);
		headerTitle:emit(value: "File Manager — {{curDir}}");

		local ListView is lv: ListView(
			items: dirEntries,
			focusTarget: listFocus,
			onActivate: local Function(String is entry){
				handleEntryActivate(entry: entry);
			},
			onSelectChange: local Function(String is entry){
				if({ entry != '..' && !entry:endsWith(suffix: '/') && nameInputs:length() > 0 }, {
					nameInputs:get(index: 0):setText(value: entry);
				});
			}
		);
		listViews: Array([lv]);

		local TextInput is ti: TextInput(
			value: initialName,
			placeholder: 'filename',
			focusTarget: inputFocus,
			onSubmit: local Function(String is _typed){
				submitCurrent();
			}
		);
		nameInputs: Array([ti]);
	}

	local Function is sortAlpha(Array of String is items){
		local Int is n: items:length();
		local Int is i: 1;
		while({ i < n }, {
			local String is key: items:get(index: i);
			local String is keyLow: key:toLower();
			local Int is j: i - 1;
			local Boolean is done: false;
			while({ !done && j >= 0 }, {
				local String is cur: items:get(index: j);
				local String is curLow: cur:toLower();
				local Boolean is gt: curLow > keyLow || (curLow == keyLow && cur > key);
				if({ gt }, {
					items:set(index: j + 1, item: cur);
					j: j - 1;
				}, {
					done: true;
				});
			});
			items:set(index: j + 1, item: key);
			i: i + 1;
		});
	}

	local Function of Array of String is buildEntries(String is dir){
		local Array of String is dirs: Array();
		local Array of String is files: Array();
		Dir:dirList(path: dir):each(action: local Function(String is name){
			if({ name:startsWith(prefix: '.') }, { return; });
			local String is full: "{{dir}}/{{name}}";
			if({ Dir:dirList(path: full):length() > 0 }, {
				dirs:add(item: "{{name}}/");
			}, {
				files:add(item: name);
			});
		});
		sortAlpha(items: dirs);
		sortAlpha(items: files);
		local Array of String is out: Array(['..']);
		dirs:each(action: local Function(String is d){ out:add(item: d); });
		files:each(action: local Function(String is f){ out:add(item: f); });
		out;
	}

	local Function is navigateTo(String is nextDir){
		curDir: nextDir;
		dirEntries: buildEntries(dir: curDir);
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
				navigateTo(nextDir: parts:join(separator: '/'));
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
		onConfirm(full);
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			onCancel();
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
		if({ (okFocus:focused || cancelFocus:focused) && event:isUp() }, {
			inputFocus:requestFocus();
			return true;
		});
		false;
	}

	replace Function of Widget is ui(){
		local String is actionLabel: if({ mode == 'saveAs' }, { ' Save ' }, { ' Open ' });
		local String is actionKey: if({ mode == 'saveAs' }, { 's' }, { 'o' });

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
									value: headerTitle,
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
									label: actionLabel,
									shortcutKey: actionKey,
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
