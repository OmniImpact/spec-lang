#! specunit: suite

Class of SpecUnitTest is TestTheoEditor{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'theo', [TheoBuffer, TheoRenderer, TheoScreen, KeyEvent, KeyKind, Frame, FocusTarget]],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['theoedit', 'model', [EditorDocument, DirectoryListing]],
		['theoedit', 'util', [EditorFocus, EditorMessageMode, EditorStrings, FileDialogMode, FileManagerFocus, FileStorage, DirectoryScanner, PathTransformer]],
		['theoedit', 'vm', [EditorViewModel, FileManagerViewModel]],
		['theoedit', 'view', [EditorFrame, FileManagerFrame]]
	];

	local Function is wireEditorFocus(EditorFrame is frame){
		frame:editorFocus:bindOwner(handler: local Function(Any is _t){
			frame:editorFocus:focused: true;
			frame:saveFocus:focused: false;
			frame:saveAsFocus:focused: false;
			frame:openFocus:focused: false;
			frame:exitFocus:focused: false;
			frame:msgSaveFocus:focused: false;
			frame:msgDiscardFocus:focused: false;
			frame:msgCancelFocus:focused: false;
		});
		frame:saveFocus:bindOwner(handler: local Function(Any is _t){
			frame:editorFocus:focused: false;
			frame:saveFocus:focused: true;
			frame:saveAsFocus:focused: false;
			frame:openFocus:focused: false;
			frame:exitFocus:focused: false;
			frame:msgSaveFocus:focused: false;
			frame:msgDiscardFocus:focused: false;
			frame:msgCancelFocus:focused: false;
		});
		frame:saveAsFocus:bindOwner(handler: local Function(Any is _t){
			frame:editorFocus:focused: false;
			frame:saveFocus:focused: false;
			frame:saveAsFocus:focused: true;
			frame:openFocus:focused: false;
			frame:exitFocus:focused: false;
		});
		frame:openFocus:bindOwner(handler: local Function(Any is _t){
			frame:editorFocus:focused: false;
			frame:saveFocus:focused: false;
			frame:saveAsFocus:focused: false;
			frame:openFocus:focused: true;
			frame:exitFocus:focused: false;
		});
		frame:exitFocus:bindOwner(handler: local Function(Any is _t){
			frame:editorFocus:focused: false;
			frame:saveFocus:focused: false;
			frame:saveAsFocus:focused: false;
			frame:openFocus:focused: false;
			frame:exitFocus:focused: true;
		});
		frame:msgSaveFocus:bindOwner(handler: local Function(Any is _t){
			frame:editorFocus:focused: false;
			frame:msgSaveFocus:focused: true;
			frame:msgDiscardFocus:focused: false;
			frame:msgCancelFocus:focused: false;
		});
		frame:msgDiscardFocus:bindOwner(handler: local Function(Any is _t){
			frame:editorFocus:focused: false;
			frame:msgSaveFocus:focused: false;
			frame:msgDiscardFocus:focused: true;
			frame:msgCancelFocus:focused: false;
		});
		frame:msgCancelFocus:bindOwner(handler: local Function(Any is _t){
			frame:editorFocus:focused: false;
			frame:msgSaveFocus:focused: false;
			frame:msgDiscardFocus:focused: false;
			frame:msgCancelFocus:focused: true;
		});
	}

	Function is testEditorLayoutTypingFocusAndSave(){
		local String is tmpPath: "/tmp/theo_editor_test_{{Process:getPid()}}.txt";
		fileWrite(path: tmpPath, content: "hello\nworld");

		local Boolean is exited: false;
		local EditorViewModel is vm: EditorViewModel(filePath: tmpPath);
		local EditorFrame is frame: EditorFrame(vm: vm, onQuit: {
			exited: true;
		});
		local TheoScreen is scr: TheoScreen(root: frame);
		frame:bindScreen(screen: scr);
		wireEditorFocus(frame: frame);

		local TheoBuffer is buf: TheoBuffer(width: 60, height: 14);
		local TheoRenderer is renderer: TheoRenderer();
		frame:layout(x: 0, y: 0, w: 60, h: 14);
		frame:paint(buf: buf, renderer: renderer);

		Assert:isTrue(buf:rowText(y: 1):contains(needle: tmpPath));
		Assert:isTrue(buf:rowText(y: 4):contains(needle: 'hello'));
		Assert:isTrue(buf:rowText(y: 5):contains(needle: 'world'));
		Assert:isTrue(buf:rowText(y: 12):contains(needle: ' Save '));
		Assert:isTrue(buf:rowText(y: 12):contains(needle: ' Save As '));
		Assert:isTrue(buf:rowText(y: 12):contains(needle: ' Open '));
		Assert:isTrue(buf:rowText(y: 12):contains(needle: ' Quit '));
		Assert:areEqualInt(255, buf:cellAt(x: 0, y: 3):fg:c1);
		Assert:areEqualInt(240, buf:cellAt(x: 0, y: 11):fg:c1);

		# Type '!' and Tab
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: '!')));
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:TAB)));
		Assert:areEqualString("!\thello\nworld", vm:content:current());
		Assert:isTrue(vm:title:current():endsWith(suffix: ' *'));

		# Ctrl+M toggles menu focus and back
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'm', ctrl: true)));
		Assert:isTrue(frame:saveFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'm', ctrl: true)));
		Assert:isTrue(frame:editorFocus:focused);

		# Move to menu, Right -> Save As -> Open, Left -> Save As -> Save -> Quit
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'm', ctrl: true)));
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:RIGHT)));
		Assert:isTrue(frame:saveAsFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:RIGHT)));
		Assert:isTrue(frame:openFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:LEFT)));
		Assert:isTrue(frame:saveAsFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:LEFT)));
		Assert:isTrue(frame:saveFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:LEFT)));
		Assert:isTrue(frame:exitFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:RIGHT)));
		Assert:isTrue(frame:saveFocus:focused);

		# Enter on Save writes file and clears '*'
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:ENTER)));
		Assert:areEqualString("!\thello\nworld", fileRead(path: tmpPath, default: ''));
		Assert:areEqualString(tmpPath, vm:title:current());
		Assert:isTrue(frame:editorFocus:focused);

		fileRemove(path: tmpPath);
	}

	Function is testMessagePanelAndFileManagerNavigation(){
		local String is savePath: "/tmp/theo_fm_save_{{Process:getPid()}}.txt";
		local Boolean is exited: false;
		local EditorViewModel is vm: EditorViewModel(filePath: '');
		local EditorFrame is frame: EditorFrame(vm: vm, onQuit: {
			exited: true;
		});
		local TheoScreen is scr: TheoScreen(root: frame);
		frame:bindScreen(screen: scr);
		wireEditorFocus(frame: frame);

		local TheoBuffer is buf: TheoBuffer(width: 72, height: 16);
		local TheoRenderer is renderer: TheoRenderer();
		frame:layout(x: 0, y: 0, w: 72, h: 16);
		frame:paint(buf: buf, renderer: renderer);
		Assert:isTrue(buf:rowText(y: 1):contains(needle: '[untitled]'));

		# Edit buffer and press Ctrl+Q -> MessagePanel appears between editor and bottom bar
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'x')));
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'q', ctrl: true)));
		Assert:isTrue(vm:messageMode == EditorMessageMode:CONFIRM_QUIT);
		Assert:isTrue(frame:msgSaveFocus:focused);

		buf:clear();
		frame:layout(x: 0, y: 0, w: 72, h: 16);
		frame:paint(buf: buf, renderer: renderer);
		Assert:isTrue(buf:rowText(y: 11):contains(needle: 'Unsaved changes'));
		Assert:isTrue(buf:rowText(y: 11):contains(needle: ' Discard '));

		# Right moves to Discard button, Enter discards and exits
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:RIGHT)));
		Assert:isTrue(frame:msgDiscardFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:ENTER)));
		Assert:isTrue(exited);

		# Cancel message panel and open FileManagerFrame via Ctrl+S on untitled
		vm:clearMessage();
		frame:rebuild();
		frame:editorFocus:requestFocus();
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 's', ctrl: true)));
		Assert:isTrue(scr:stack:length() == 2);

		local Frame is top: scr:current();
		buf:clear();
		top:layout(x: 0, y: 0, w: 72, h: 16);
		top:paint(buf: buf, renderer: renderer);
		Assert:isTrue(buf:rowText(y: 1):contains(needle: 'File Manager'));
		Assert:isTrue(buf:rowText(y: 1):contains(needle: 'Ctrl+M: menu'));
		Assert:isTrue(buf:rowText(y: 11):contains(needle: 'Name:'));
		Assert:isTrue(buf:rowText(y: 14):contains(needle: ' Save '));
		Assert:isTrue(buf:rowText(y: 14):contains(needle: ' Cancel '));

		# Ctrl+F toggles between filename input and file list
		local FileManagerFrame is fmTop: top as FileManagerFrame;
		fmTop:listFocus:bindOwner(handler: local Function(Any is _t){
			fmTop:listFocus:focused: true;
			fmTop:inputFocus:focused: false;
			fmTop:okFocus:focused: false;
			fmTop:cancelFocus:focused: false;
		});
		fmTop:inputFocus:bindOwner(handler: local Function(Any is _t){
			fmTop:listFocus:focused: false;
			fmTop:inputFocus:focused: true;
			fmTop:okFocus:focused: false;
			fmTop:cancelFocus:focused: false;
		});
		fmTop:okFocus:bindOwner(handler: local Function(Any is _t){
			fmTop:listFocus:focused: false;
			fmTop:inputFocus:focused: false;
			fmTop:okFocus:focused: true;
			fmTop:cancelFocus:focused: false;
		});
		fmTop:cancelFocus:bindOwner(handler: local Function(Any is _t){
			fmTop:listFocus:focused: false;
			fmTop:inputFocus:focused: false;
			fmTop:okFocus:focused: false;
			fmTop:cancelFocus:focused: true;
		});
		Assert:isTrue(fmTop:inputFocus:focused);
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'f', ctrl: true)));
		Assert:isTrue(fmTop:listFocus:focused);
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'f', ctrl: true)));
		Assert:isTrue(fmTop:inputFocus:focused);

		# Ctrl+M focuses Save/Cancel menu bar, Left->Cancel, Right->Save, Ctrl+M returns
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'm', ctrl: true)));
		Assert:isTrue(fmTop:okFocus:focused);
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: KeyKind:LEFT)));
		Assert:isTrue(fmTop:cancelFocus:focused);
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: KeyKind:RIGHT)));
		Assert:isTrue(fmTop:okFocus:focused);
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'm', ctrl: true)));
		Assert:isTrue(fmTop:inputFocus:focused);

		# Type savePath into FileManagerFrame's TextInput and press Enter -> saves & pops back
		local Int is i: 0;
		while({ i < savePath:length() }, {
			top:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: savePath:charAt(index: i, default: '')));
			i: i + 1;
		});
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: KeyKind:ENTER)));
		Assert:isTrue(scr:stack:length() == 1);
		Assert:areEqualString('x', fileRead(path: savePath, default: ''));
		Assert:areEqualString(savePath, vm:title:current());
		fileRemove(path: savePath);
	}

	Function is testFileManagerDirectoriesFirstAlphabetical(){
		local String is rootDir: "/tmp/theo_fm_sort_{{Process:getPid()}}";
		local String is subZ: "{{rootDir}}/zebraDir";
		local String is subA: "{{rootDir}}/AlphaDir";
		Process:execute(command: 'mkdir', args: Array(['-p', subZ, subA]));
		fileWrite(path: "{{subZ}}/keep", content: '1');
		fileWrite(path: "{{subA}}/keep", content: '1');
		fileWrite(path: "{{rootDir}}/zeta.txt", content: 'z');
		fileWrite(path: "{{rootDir}}/beta.txt", content: 'b');
		fileWrite(path: "{{rootDir}}/Alpha.txt", content: 'a');

		local FileManagerViewModel is fmVm: FileManagerViewModel(
			mode: FileDialogMode:OPEN,
			initialDir: rootDir,
			onConfirm: local Function(String is _p){},
			onCancel: {}
		);
		local FileManagerFrame is fm: FileManagerFrame(vm: fmVm);
		local [String] is sortedEntries: fm:vm:entries:current();
		Assert:areEqualInt(6, sortedEntries:length());
		Assert:areEqualString('..', sortedEntries:get(index: 0));
		Assert:areEqualString('AlphaDir/', sortedEntries:get(index: 1));
		Assert:areEqualString('zebraDir/', sortedEntries:get(index: 2));
		Assert:areEqualString('Alpha.txt', sortedEntries:get(index: 3));
		Assert:areEqualString('beta.txt', sortedEntries:get(index: 4));
		Assert:areEqualString('zeta.txt', sortedEntries:get(index: 5));

		Process:execute(command: 'rm', args: Array(['-rf', rootDir]));
	}

	Function is testPureModelsAndViewModels(){
		# Pure EditorDocument model (zero I/O, zero formatting)
		local EditorDocument is doc: EditorDocument(filePath: 'notes.txt', text: 'initial', dirty: false);
		Assert:areEqualString('initial', doc:text);
		Assert:isFalse(doc:dirty);
		doc:updateText(nextText: 'updated');
		Assert:areEqualString('updated', doc:text);
		Assert:isTrue(doc:dirty);
		doc:markSaved(path: 'saved.txt');
		Assert:areEqualString('saved.txt', doc:filePath);
		Assert:isFalse(doc:dirty);

		# PathTransformer + FileStorage utilities + EditorViewModel
		local PathTransformer is paths: PathTransformer();
		Assert:areEqualString('[untitled]', paths:formatDocumentTitle(filePath: '', dirty: false));
		Assert:areEqualString('notes.txt *', paths:formatDocumentTitle(filePath: 'notes.txt', dirty: true));
		Assert:areEqualString('/a/b', paths:parentDir(dir: '/a/b/c'));
		Assert:areEqualString('/', paths:parentDir(dir: '/a'));
		Assert:areEqualString('/a/b/sub', paths:childDir(dir: '/a/b', entry: 'sub/'));
		Assert:areEqualString('/a/b/file.spec', paths:resolveTargetPath(dir: '/a/b', typedName: ' file.spec '));
		Assert:areEqualString('/abs/file.spec', paths:resolveTargetPath(dir: '/a/b', typedName: '/abs/file.spec'));
		Assert:isTrue(paths:isDirectoryEntry(entry: '..'));
		Assert:isTrue(paths:isDirectoryEntry(entry: 'src/'));
		Assert:isFalse(paths:isDirectoryEntry(entry: 'Main.spec'));

		local String is fmDir: "/tmp/theo_fm_vm_{{Process:getPid()}}";
		Process:execute(command: 'mkdir', args: Array(['-p', fmDir]));
		local FileManagerViewModel is fmVm: FileManagerViewModel(mode: FileDialogMode:SAVE_AS, initialDir: fmDir, initialName: 'out.txt');
		Assert:isTrue(fmVm:isSaveAs());
		Assert:areEqualString(EditorStrings:LABEL_SAVE, fmVm:actionLabel());
		Assert:areEqualString(EditorStrings:KEY_SAVE, fmVm:actionKey());
		Assert:isTrue(fmVm:focus:current() == FileManagerFocus:INPUT);
		Process:execute(command: 'rm', args: Array(['-rf', fmDir]));

		# Two-way EnumEmitter focus + hover sync on EditorFrame / EditorViewModel
		local EditorViewModel is eVm: EditorViewModel(filePath: '');
		local EditorFrame is eFrame: EditorFrame(vm: eVm);
		wireEditorFocus(frame: eFrame);
		Assert:isTrue(eVm:focus:current() == EditorFocus:EDITOR);
		Assert:isTrue(eVm:hover:current() == EditorFocus:NONE);
		# View -> VM focus sync
		eFrame:openFocus:requestFocus();
		Assert:isTrue(eVm:focus:current() == EditorFocus:OPEN);
		# VM -> View focus sync
		eVm:setFocus(target: EditorFocus:SAVE_AS);
		Assert:isTrue(eFrame:saveAsFocus:focused);
		Assert:isFalse(eFrame:openFocus:focused);
		# Hover sync via FocusTarget
		eFrame:saveFocus:setHovered(next: true);
		Assert:isTrue(eVm:hover:current() == EditorFocus:SAVE);
		eFrame:saveFocus:setHovered(next: false);
		Assert:isTrue(eVm:hover:current() == EditorFocus:NONE);
	}
}
