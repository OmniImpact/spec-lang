#! specunit: suite

Class of SpecUnitTest is TestTheoEditor{
	merge Array of Array of String is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'theo', [TheoBuffer, TheoRenderer, TheoScreen, KeyEvent, Frame, FocusTarget]],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['theoedit', 'model', [EditorDocument, DirectoryBrowser]],
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
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'char', key: '!')));
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'tab')));
		Assert:areEqualString("!\thello\nworld", vm:content:current());
		Assert:isTrue(vm:title:current():endsWith(suffix: ' *'));

		# Ctrl+M toggles menu focus and back
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'char', key: 'm', ctrl: true)));
		Assert:isTrue(frame:saveFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'char', key: 'm', ctrl: true)));
		Assert:isTrue(frame:editorFocus:focused);

		# Move to menu, Right -> Save As -> Open, Left -> Save As -> Save -> Quit
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'char', key: 'm', ctrl: true)));
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'right')));
		Assert:isTrue(frame:saveAsFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'right')));
		Assert:isTrue(frame:openFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'left')));
		Assert:isTrue(frame:saveAsFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'left')));
		Assert:isTrue(frame:saveFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'left')));
		Assert:isTrue(frame:exitFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'right')));
		Assert:isTrue(frame:saveFocus:focused);

		# Enter on Save writes file and clears '*'
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'enter')));
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
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'char', key: 'x')));
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'char', key: 'q', ctrl: true)));
		Assert:areEqualString('confirmQuit', vm:messageMode);
		Assert:isTrue(frame:msgSaveFocus:focused);

		buf:clear();
		frame:layout(x: 0, y: 0, w: 72, h: 16);
		frame:paint(buf: buf, renderer: renderer);
		Assert:isTrue(buf:rowText(y: 11):contains(needle: 'Unsaved changes'));
		Assert:isTrue(buf:rowText(y: 11):contains(needle: ' Discard '));

		# Right moves to Discard button, Enter discards and exits
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'right')));
		Assert:isTrue(frame:msgDiscardFocus:focused);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'enter')));
		Assert:isTrue(exited);

		# Cancel message panel and open FileManagerFrame via Ctrl+S on untitled
		vm:clearMessage();
		frame:rebuild();
		frame:editorFocus:requestFocus();
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: 'char', key: 's', ctrl: true)));
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
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: 'char', key: 'f', ctrl: true)));
		Assert:isTrue(fmTop:listFocus:focused);
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: 'char', key: 'f', ctrl: true)));
		Assert:isTrue(fmTop:inputFocus:focused);

		# Ctrl+M focuses Save/Cancel menu bar, Left->Cancel, Right->Save, Ctrl+M returns
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: 'char', key: 'm', ctrl: true)));
		Assert:isTrue(fmTop:okFocus:focused);
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: 'left')));
		Assert:isTrue(fmTop:cancelFocus:focused);
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: 'right')));
		Assert:isTrue(fmTop:okFocus:focused);
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: 'char', key: 'm', ctrl: true)));
		Assert:isTrue(fmTop:inputFocus:focused);

		# Type savePath into FileManagerFrame's TextInput and press Enter -> saves & pops back
		local Int is i: 0;
		while({ i < savePath:length() }, {
			top:handleKey(event: KeyEvent(kind: 'char', key: savePath:charAt(index: i, default: '')));
			i: i + 1;
		});
		Assert:isTrue(top:handleKey(event: KeyEvent(kind: 'enter')));
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

		local FileManagerFrame is fm: FileManagerFrame(
			mode: 'open',
			initialDir: rootDir,
			onConfirm: local Function(String is _p){},
			onCancel: {}
		);
		Assert:areEqualInt(6, fm:vm:entries:length());
		Assert:areEqualString('..', fm:vm:entries:get(index: 0));
		Assert:areEqualString('AlphaDir/', fm:vm:entries:get(index: 1));
		Assert:areEqualString('zebraDir/', fm:vm:entries:get(index: 2));
		Assert:areEqualString('Alpha.txt', fm:vm:entries:get(index: 3));
		Assert:areEqualString('beta.txt', fm:vm:entries:get(index: 4));
		Assert:areEqualString('zeta.txt', fm:vm:entries:get(index: 5));

		Process:execute(command: 'rm', args: Array(['-rf', rootDir]));
	}

	Function is testPureModelsAndViewModels(){
		local String is tmpPath: "/tmp/theo_doc_model_{{Process:getPid()}}.txt";
		fileWrite(path: tmpPath, content: 'initial');

		# Pure EditorDocument model
		local EditorDocument is doc: EditorDocument(filePath: tmpPath);
		Assert:areEqualString('initial', doc:text);
		Assert:isFalse(doc:dirty);
		Assert:areEqualString(tmpPath, doc:displayTitle());
		doc:updateText(nextText: 'updated');
		Assert:isTrue(doc:dirty);
		Assert:areEqualString("{{tmpPath}} *", doc:displayTitle());
		Assert:isTrue(doc:save());
		Assert:isFalse(doc:dirty);
		Assert:areEqualString('updated', fileRead(path: tmpPath, default: ''));
		fileRemove(path: tmpPath);

		# Pure DirectoryBrowser model + FileManagerViewModel
		local DirectoryBrowser is browser: DirectoryBrowser();
		Assert:areEqualString('/a/b', browser:parentDir(dir: '/a/b/c'));
		Assert:areEqualString('/', browser:parentDir(dir: '/a'));
		Assert:areEqualString('/a/b/sub', browser:childDir(dir: '/a/b', entry: 'sub/'));
		Assert:areEqualString('/a/b/file.spec', browser:resolveTargetPath(dir: '/a/b', typedName: ' file.spec '));
		Assert:areEqualString('/abs/file.spec', browser:resolveTargetPath(dir: '/a/b', typedName: '/abs/file.spec'));
		Assert:isTrue(browser:isDirectoryEntry(entry: '..'));
		Assert:isTrue(browser:isDirectoryEntry(entry: 'src/'));
		Assert:isFalse(browser:isDirectoryEntry(entry: 'Main.spec'));

		local FileManagerViewModel is fmVm: FileManagerViewModel(mode: 'saveAs', initialDir: '/tmp', initialName: 'out.txt');
		Assert:isTrue(fmVm:isSaveAs());
		Assert:areEqualString(' Save ', fmVm:actionLabel());
		Assert:areEqualString('s', fmVm:actionKey());
	}
}
