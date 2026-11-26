#! Package base:wardrobe
#! Reusable non-blocking file picker dialog supporting Open/Save modes, top path bar,
#! editable filename bar, left "Pinned" favorites sidebar with drag-and-drop folder pinning,
#! directory navigation, scroll wheel/scrollbar, and resize redraw.

Class is FileDialog{
	replace [String] is namespace: ['base', 'wardrobe', 'file'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', Dir],
		['base', 'sys', as File()],
		['base', 'sys', Uri],
		['base', 'sys', Process],
		['base', 'sys', Time],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'signal', SignalBag],
		['base', 'suit', SuitWindow],
		['base', 'suit', SuitCanvas],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'wardrobe', 'file', FilePinnedLocations]
	];

	String is title: 'Open File';
	BoolEmitter is open: BoolEmitter(initial: false);
	BoolEmitter is saveMode: BoolEmitter(initial: false);
	BoolEmitter is directoryMode: BoolEmitter(initial: false);
	TextEmitter is dialogTitle: TextEmitter(initial: '');
	TextEmitter is suggestedName: TextEmitter(initial: '');
	Boolean is allowMultiple: false;
	String is initialDir: '.';
	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	Float is widthPt: 640.0;
	Float is heightPt: 440.0;
	Function is onSelect: local Function(Array of String is paths){};
	Function is onCancel: local Function(){};

	SuitWindow is win: SuitWindow();
	SuitCanvas is canvas: SuitCanvas(width: 1, height: 1);
	DrawContext is paintCtx: DrawContext(canvas: SuitCanvas(width: 1, height: 1));
	Time is clock: Time();
	Boolean is isShown: false;
	Boolean is isDirty: false;
	Int is lastW: 0;
	Int is lastH: 0;
	SignalBag is signalBag: SignalBag();

	String is curDir: '.';
	String is editPath: '.';
	String is fileName: '';
	Boolean is showHidden: false;
	Int is focusTarget: 0; ## 0=list, 1=path bar, 2=filename input
	Array of String is entryNames: Array();
	Array of Boolean is entryIsDir: Array();
	Array of String is selectedPaths: Array();
	FilePinnedLocations is pinned: FilePinnedLocations();
	Int is selectedRow: -1;
	Int is scrollRow: 0;
	Int is hoverRow: -1;
	Int is hoverPinIdx: -1;
	Int is hoverBtn: 0; ## 0=none, 1=Cancel, 2=Open/Save, 3=Up
	Int is lastClickRow: -1;
	Int is lastClickMs: 0;
	Boolean is dragScrollbar: false;
	Int is dragCandidateRow: -1;
	Int is dragStartX: 0;
	Int is dragStartY: 0;
	Boolean is isDraggingFolder: false;
	String is dragFolderName: '';
	String is dragFolderPath: '';
	Boolean is dragOverPinned: false;

	replace Function is init(
		String is title: 'Open File',
		BoolEmitter is open: BoolEmitter(initial: false),
		BoolEmitter is saveMode: BoolEmitter(initial: false),
		BoolEmitter is directoryMode: BoolEmitter(initial: false),
		TextEmitter is dialogTitle: TextEmitter(initial: ''),
		TextEmitter is suggestedName: TextEmitter(initial: ''),
		Boolean is allowMultiple: false,
		String is initialDir: '.',
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0),
		Float is widthPt: 640.0,
		Float is heightPt: 440.0,
		Function is onSelect: local Function(Array of String is paths){},
		Function is onCancel: local Function(){}
	){
		:title: title;
		:open: open;
		:saveMode: saveMode;
		:directoryMode: directoryMode;
		:dialogTitle: dialogTitle;
		:suggestedName: suggestedName;
		:allowMultiple: allowMultiple;
		:initialDir: :resolveDir(dirPath: initialDir);
		:curDir: :initialDir;
		:editPath: :initialDir;
		:theme: theme;
		:scale: scale;
		:widthPt: widthPt;
		:heightPt: heightPt;
		:onSelect: onSelect;
		:onCancel: onCancel;
		:entryNames: Array();
		:entryIsDir: Array();
		:selectedPaths: Array();
		:pinned: FilePinnedLocations();
		:pinned:load();
		isShown: false;
		isDirty: false;
		lastW: 0;
		lastH: 0;
		showHidden: false;
		focusTarget: 0;
		selectedRow: -1;
		scrollRow: 0;
		hoverRow: -1;
		hoverPinIdx: -1;
		hoverBtn: 0;
		lastClickRow: -1;
		lastClickMs: 0;
		dragScrollbar: false;
		dragCandidateRow: -1;
		isDraggingFolder: false;
		dragOverPinned: false;
	}

	local Function of String is resolveDir(String is dirPath){
		if({ dirPath == '.' || dirPath == '' }, {
			local String is pwd: Process():getEnv(key: 'PWD', default: '');
			if({ pwd != '' && Dir():isDir(path: pwd) }, { return pwd; });
			return '.';
		});
		return dirPath;
	}

	local Function is savePinnedToConfig(){
		pinned:save();
	}

	local Function is addPinned(String is name, String is path){
		if({ pinned:add(name: name, path: path) }, {
			isDirty: true;
		});
	}

	Function is applyTheme(Theme is theme){
		:theme: theme;
		isDirty: true;
	}

	Function is setScale(Scale is scale){
		:scale: scale;
		isDirty: true;
	}

	local Function of String is joinPath(String is dir, String is name){
		if({ dir == '' || dir == '.' }, { return name; });
		local Int is len: dir:length();
		if({ dir:byteAt(index: len - 1) == 47 }, {
			return dir . name;
		});
		return dir . '/' . name;
	}

	local Function of String is parentDir(String is dir){
		if({ dir == '' || dir == '.' }, { return '..'; });
		if({ dir == '..' }, { return '../..'; });
		if({ dir == '/' }, { return '/'; });
		local Int is len: dir:length();
		if({ len >= 3 && dir:substring(start: len - 3, end: len) == '/..' }, {
			return dir . '/..';
		});
		local Int is i: len - 1;
		while({ i > 0 && dir:byteAt(index: i) == 47 }, { i: i - 1; });
		while({ i > 0 && dir:byteAt(index: i) != 47 }, { i: i - 1; });
		if({ i == 0 }, {
			if({ dir:byteAt(index: 0) == 47 }, { return '/'; });
			return '.';
		});
		return dir:substring(start: 0, end: i);
	}

	local Function of Boolean is isPathSelected(String is fullPath){
		local Int is i: 0;
		while({ i < selectedPaths:length() }, {
			if({ selectedPaths:get(index: i) == fullPath }, { return true; });
			i: i + 1;
		});
		return false;
	}

	local Function is selectSingleFile(String is fullPath){
		selectedPaths: Array();
		selectedPaths:add(item: fullPath);
	}

	local Function is toggleSelect(String is fullPath){
		if({ !allowMultiple }, {
			:selectSingleFile(fullPath: fullPath);
			return;
		});
		local Int is found: -1;
		local Int is i: 0;
		while({ i < selectedPaths:length() }, {
			if({ selectedPaths:get(index: i) == fullPath }, { found: i; });
			i: i + 1;
		});
		if({ found >= 0 }, {
			selectedPaths:removeAt(index: found);
		}, {
			selectedPaths:add(item: fullPath);
		});
	}

	local Function is sortStrings(Array of String is arr){
		local Int is n: arr:length();
		local Int is i: 1;
		while({ i < n }, {
			local String is key: arr:get(index: i);
			local Int is j: i - 1;
			while({ j >= 0 && arr:get(index: j) > key }, {
				arr:set(index: j + 1, item: arr:get(index: j));
				j: j - 1;
			});
			arr:set(index: j + 1, item: key);
			i: i + 1;
		});
	}

	local Function is loadDirectory(String is dirPath){
		local Dir is d: Dir();
		local Array of String is raw: d:dirList(path: dirPath);
		local Array of String is dirs: Array();
		local Array of String is files: Array();
		local Int is i: 0;
		while({ i < raw:length() }, {
			local String is name: raw:get(index: i);
			local Boolean is isDot: name:length() > 0 && name:byteAt(index: 0) == 46;
			local Boolean is visible: showHidden || !isDot;
			if({ name != '.' && name != '..' && visible }, {
				local String is full: :joinPath(dir: dirPath, name: name);
				if({ d:isDir(path: full) }, {
					dirs:add(item: name);
				}, {
					files:add(item: name);
				});
			});
			i: i + 1;
		});
		:sortStrings(arr: dirs);
		:sortStrings(arr: files);

		entryNames: Array();
		entryIsDir: Array();
		i: 0;
		while({ i < dirs:length() }, {
			entryNames:add(item: dirs:get(index: i));
			entryIsDir:add(item: true);
			i: i + 1;
		});
		i: 0;
		while({ i < files:length() }, {
			entryNames:add(item: files:get(index: i));
			entryIsDir:add(item: false);
			i: i + 1;
		});

		curDir: dirPath;
		editPath: dirPath;
		selectedRow: -1;
		scrollRow: 0;
		hoverRow: -1;
		lastClickRow: -1;
		dragCandidateRow: -1;
		isDraggingFolder: false;
		dragOverPinned: false;
		if({ !allowMultiple }, {
			selectedPaths: Array();
		});
		isDirty: true;
	}

	local Function of Int is fontPx(){
		local Int is px: scale:px(pt: theme:scaledTextPt(defaultPt: 16.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is headerHeightPx(){
		return scale:px(pt: 38.0);
	}

	local Function of Int is footerHeightPx(){
		return scale:px(pt: 78.0);
	}

	local Function of Int is sidebarWidthPx(Int is totalW){
		local Int is sw: scale:px(pt: 140.0);
		if({ totalW < sw * 2 }, { return 0; });
		return sw;
	}

	local Function of Boolean is canConfirm(){
		if({ saveMode:current() }, { return fileName != ''; });
		return fileName != '' || selectedPaths:length() > 0;
	}

	local Function of String is popLastChar(String is s){
		local Int is len: s:length();
		if({ len <= 0 }, { return s; });
		local Int is i: len - 1;
		while({ i > 0 && ((s:byteAt(index: i) & 192) == 128) }, {
			i: i - 1;
		});
		return s:substring(start: 0, end: i);
	}

	local Function is paintDialog(){
		local Int is w: win:width();
		local Int is h: win:height();
		if({ w <= 0 || h <= 0 }, { return; });
		canvas:resize(width: w, height: h);
		paintCtx:rebind(canvas: canvas);
		local DrawContext is ctx: paintCtx;

		local Int is headerH: :headerHeightPx();
		local Int is footerH: :footerHeightPx();
		local Int is rowH: scale:px(pt: 28.0);
		local Int is padX: scale:px(pt: 10.0);
		local Int is sbW: scale:px(pt: 12.0);
		local Int is sideW: :sidebarWidthPx(totalW: w);
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);

		ctx:fillRect(x: 0, y: 0, w: w, h: h, color: theme:windowBg);

		## Top path bar: Up button + editable directory path box
		ctx:fillRect(x: 0, y: 0, w: w, h: headerH, color: theme:toolbarBg);
		local Int is linePx: theme:borderPx(scaleFactor: scale:factor);
		ctx:fillRect(x: 0, y: headerH - linePx, w: w, h: linePx, color: theme:toolbarBorder);

		local Int is upW: scale:px(pt: 44.0);
		local Int is hidW: scale:px(pt: 70.0);
		local Int is topBoxH: scale:px(pt: 26.0);
		local Int is topBoxY: (headerH - topBoxH) / 2;
		local Int is upBg: if({ hoverBtn == 3 }, { theme:hoverBg }, { theme:menuBg });
		ctx:fillRect(x: padX, y: topBoxY, w: upW, h: topBoxH, color: upBg);
		ctx:strokeRect(x: padX, y: topBoxY, w: upW, h: topBoxH, color: theme:menuBorder);
		local Int is uw: ctx:measureTextWidth(text: 'Up', pixelHeight: fpx);
		ctx:drawText(x: padX + (upW - uw) / 2, y: topBoxY + (topBoxH - th) / 2, text: 'Up', color: theme:textPrimary, pixelHeight: fpx);

		local Int is hidX: w - padX - hidW;
		local Int is hidBg: if({ showHidden }, { theme:activeBg }, { if({ hoverBtn == 4 }, { theme:hoverBg }, { theme:menuBg }) });
		ctx:fillRect(x: hidX, y: topBoxY, w: hidW, h: topBoxH, color: hidBg);
		ctx:strokeRect(x: hidX, y: topBoxY, w: hidW, h: topBoxH, color: theme:menuBorder);
		local Int is hw: ctx:measureTextWidth(text: 'Hidden', pixelHeight: fpx);
		ctx:drawText(x: hidX + (hidW - hw) / 2, y: topBoxY + (topBoxH - th) / 2, text: 'Hidden', color: theme:textPrimary, pixelHeight: fpx);

		local Int is pathX: padX + upW + scale:px(pt: 8.0);
		local Int is pathW: if({ hidX - scale:px(pt: 8.0) > pathX }, { hidX - scale:px(pt: 8.0) - pathX }, { 40 });
		local Int is pathBorder: if({ focusTarget == 1 }, { theme:activeBg }, { theme:menuBorder });
		ctx:fillRect(x: pathX, y: topBoxY, w: pathW, h: topBoxH, color: theme:windowBg);
		ctx:strokeRect(x: pathX, y: topBoxY, w: pathW, h: topBoxH, color: pathBorder);
		local String is pathShown: if({ focusTarget == 1 }, { editPath . '|' }, { curDir });
		ctx:setClip(x: pathX + 2, y: topBoxY, w: pathW - 4, h: topBoxH);
		ctx:drawText(x: pathX + scale:px(pt: 6.0), y: topBoxY + (topBoxH - th) / 2, text: pathShown, color: theme:textPrimary, pixelHeight: fpx);
		ctx:clearClip();

		## Middle split: Left "Pinned" panel + File list + Right scrollbar
		local Int is listY: headerH;
		local Int is listH: if({ h > headerH + footerH }, { h - headerH - footerH }, { 0 });
		local Int is listX: sideW;
		local Int is listW: if({ w - sideW > sbW }, { w - sideW - sbW }, { w - sideW });

		if({ sideW > 0 && listH > 0 }, {
			local Int is pinBg: if({ dragOverPinned }, { theme:activeBg }, { theme:menuBg });
			ctx:fillRect(x: 0, y: listY, w: sideW, h: listH, color: pinBg);
			ctx:fillRect(x: sideW - linePx, y: listY, w: linePx, h: listH, color: theme:toolbarBorder);
			local Int is pinHdrH: scale:px(pt: 24.0);
			ctx:setClip(x: 0, y: listY, w: sideW - 1, h: listH);
			ctx:drawText(x: padX, y: listY + (pinHdrH - th) / 2, text: 'Pinned', color: theme:textMuted, pixelHeight: fpx);
			local Int is pi: 0;
			while({ pi < pinned:names:length() }, {
				local Int is py: listY + pinHdrH + pi * rowH;
				if({ py < listY + listH }, {
					local Boolean is isCurPin: pinned:paths:get(index: pi) == curDir;
					if({ isCurPin }, {
						ctx:fillRect(x: 4, y: py + 2, w: sideW - 9, h: rowH - 4, color: theme:activeBg);
					}, {
						if({ hoverPinIdx == pi }, {
							ctx:fillRect(x: 4, y: py + 2, w: sideW - 9, h: rowH - 4, color: theme:hoverBg);
						});
					});
					ctx:drawText(x: padX, y: py + (rowH - th) / 2, text: pinned:names:get(index: pi), color: theme:textPrimary, pixelHeight: fpx);
				});
				pi: pi + 1;
			});
			ctx:clearClip();
		});

		local Int is visRows: if({ rowH > 0 }, { listH / rowH }, { 0 });
		local Int is maxScroll: if({ entryNames:length() > visRows }, { entryNames:length() - visRows }, { 0 });
		if({ scrollRow > maxScroll }, { scrollRow: maxScroll; });
		if({ scrollRow < 0 }, { scrollRow: 0; });

		ctx:setClip(x: listX, y: listY, w: listW, h: listH);
		local Int is r: 0;
		while({ r <= visRows && (scrollRow + r) < entryNames:length() }, {
			local Int is idx: scrollRow + r;
			local Int is ry: listY + r * rowH;
			local String is name: entryNames:get(index: idx);
			local Boolean is isD: entryIsDir:get(index: idx);
			local String is full: :joinPath(dir: curDir, name: name);
			local Boolean is isSel: if({ isD }, { selectedRow == idx }, { :isPathSelected(fullPath: full) });

			if({ isSel }, {
				ctx:fillRect(x: listX + 4, y: ry + 2, w: listW - 8, h: rowH - 4, color: theme:activeBg);
			}, {
				if({ hoverRow == idx }, {
					ctx:fillRect(x: listX + 4, y: ry + 2, w: listW - 8, h: rowH - 4, color: theme:hoverBg);
				});
			});

			if({ isD }, {
				ctx:strokeRect(x: listX + 4, y: ry + 2, w: listW - 8, h: rowH - 4, color: theme:menuBorder);
			});

			ctx:drawText(x: listX + padX, y: ry + (rowH - th) / 2, text: name, color: theme:textPrimary, pixelHeight: fpx);
			r: r + 1;
		});
		ctx:clearClip();

		## Right-side scrollbar for file list
		local Int is sbX: listX + listW;
		ctx:fillRect(x: sbX, y: listY, w: sbW, h: listH, color: theme:menuBg);
		ctx:fillRect(x: sbX, y: listY, w: linePx, h: listH, color: theme:toolbarBorder);
		if({ entryNames:length() > visRows && entryNames:length() > 0 && listH > 0 }, {
			local Int is thumbH: (listH * visRows) / entryNames:length();
			if({ thumbH < scale:px(pt: 20.0) }, { thumbH: scale:px(pt: 20.0); });
			if({ thumbH > listH }, { thumbH: listH; });
			local Int is trackRange: listH - thumbH;
			local Int is thumbY: listY + if({ maxScroll > 0 }, { (scrollRow * trackRange) / maxScroll }, { 0 });
			ctx:fillRect(x: sbX + 2, y: thumbY + 1, w: sbW - 4, h: thumbH - 2, color: theme:activeBg);
		});

		## Footer bar: editable Name input + Cancel + Open/Save buttons
		local Int is fy: h - footerH;
		ctx:fillRect(x: 0, y: fy, w: w, h: footerH, color: theme:toolbarBg);
		ctx:fillRect(x: 0, y: fy, w: w, h: linePx, color: theme:toolbarBorder);

		local String is nameLbl: 'Name:';
		local Int is lw: ctx:measureTextWidth(text: nameLbl, pixelHeight: fpx);
		local Int is boxX: padX + lw + scale:px(pt: 8.0);
		local Int is boxY: fy + scale:px(pt: 8.0);
		local Int is boxH: scale:px(pt: 26.0);
		local Int is boxW: if({ w - padX > boxX }, { w - padX - boxX }, { 40 });
		local Int is nameBorder: if({ focusTarget == 2 }, { theme:activeBg }, { theme:menuBorder });
		ctx:drawText(x: padX, y: boxY + (boxH - th) / 2, text: nameLbl, color: theme:textPrimary, pixelHeight: fpx);
		ctx:fillRect(x: boxX, y: boxY, w: boxW, h: boxH, color: theme:windowBg);
		ctx:strokeRect(x: boxX, y: boxY, w: boxW, h: boxH, color: nameBorder);
		local String is nameShown: if({ focusTarget == 2 }, { fileName . '|' }, { fileName });
		ctx:setClip(x: boxX + 2, y: boxY, w: boxW - 4, h: boxH);
		ctx:drawText(x: boxX + scale:px(pt: 6.0), y: boxY + (boxH - th) / 2, text: nameShown, color: theme:textPrimary, pixelHeight: fpx);
		ctx:clearClip();

		local Int is btnW: scale:px(pt: 86.0);
		local Int is btnH: scale:px(pt: 28.0);
		local Int is btnY: fy + footerH - btnH - scale:px(pt: 8.0);
		local Int is openX: w - padX - btnW;
		local Int is cancelX: openX - scale:px(pt: 10.0) - btnW;

		local Int is cBg: if({ hoverBtn == 1 }, { theme:hoverBg }, { theme:menuBg });
		ctx:fillRect(x: cancelX, y: btnY, w: btnW, h: btnH, color: cBg);
		ctx:strokeRect(x: cancelX, y: btnY, w: btnW, h: btnH, color: theme:menuBorder);
		local Int is cw: ctx:measureTextWidth(text: 'Cancel', pixelHeight: fpx);
		ctx:drawText(x: cancelX + (btnW - cw) / 2, y: btnY + (btnH - th) / 2, text: 'Cancel', color: theme:textPrimary, pixelHeight: fpx);

		local Boolean is canOk: :canConfirm();
		local String is okLabel: if({ saveMode:current() }, { 'Save' }, { 'Open' });
		local Int is oBg: if({ !canOk }, { theme:toolbarBg }, { if({ hoverBtn == 2 }, { theme:hoverBg }, { theme:activeBg }) });
		ctx:fillRect(x: openX, y: btnY, w: btnW, h: btnH, color: oBg);
		ctx:strokeRect(x: openX, y: btnY, w: btnW, h: btnH, color: theme:menuBorder);
		local Int is ow: ctx:measureTextWidth(text: okLabel, pixelHeight: fpx);
		local Int is oCol: if({ !canOk }, { theme:textMuted }, { theme:textPrimary });
		ctx:drawText(x: openX + (btnW - ow) / 2, y: btnY + (btnH - th) / 2, text: okLabel, color: oCol, pixelHeight: fpx);

		## Floating drag badge when dragging a folder onto Pinned
		if({ isDraggingFolder && dragFolderName != '' }, {
			local Int is dx: win:pointerX() + 10;
			local Int is dy: win:pointerY() + 10;
			local Int is dw: ctx:measureTextWidth(text: dragFolderName, pixelHeight: fpx) + scale:px(pt: 16.0);
			local Int is dh: scale:px(pt: 24.0);
			ctx:fillRect(x: dx, y: dy, w: dw, h: dh, color: theme:menuBg);
			ctx:strokeRect(x: dx, y: dy, w: dw, h: dh, color: theme:activeBg);
			ctx:drawText(x: dx + scale:px(pt: 8.0), y: dy + (dh - th) / 2, text: dragFolderName, color: theme:textPrimary, pixelHeight: fpx);
		});

		win:present(canvas: canvas);
		lastW: w;
		lastH: h;
		isDirty: false;
	}

	local Function is openWindow(){
		if({ isShown }, { return; });
		local String is effTitle: if({ dialogTitle:current() != '' }, { dialogTitle:current() }, { title });
		fileName: if({ saveMode:current() }, { suggestedName:current() }, { '' });
		focusTarget: if({ saveMode:current() }, { 2 }, { 0 });
		win: SuitWindow(
			title: effTitle,
			width: scale:px(pt: widthPt),
			height: scale:px(pt: heightPt),
			decorated: true,
			useVulkan: false
		);
		if({ !win:open() }, {
			open:emit(value: false);
			local Function is ccb: onCancel;
			ccb();
			return;
		});
		win:setMinSize(minW: scale:px(pt: 460.0), minH: scale:px(pt: 320.0));
		canvas: SuitCanvas(width: win:width(), height: win:height());
		isShown: true;
		:loadDirectory(dirPath: initialDir);
		:paintDialog();
	}

	Function is closeWindow(){
		if({ !isShown }, { return; });
		isShown: false;
		canvas:dispose();
		win:close();
	}

	local Function is finishCancel(){
		:closeWindow();
		open:emit(value: false);
		local Function is ccb: onCancel;
		ccb();
	}

	local Function is finishOpen(){
		if({ directoryMode:current() }, {
			local String is chosenDir: curDir;
			if({ selectedRow >= 0 && selectedRow < entryIsDir:length() && entryIsDir:get(index: selectedRow) }, {
				chosenDir: :joinPath(dir: curDir, name: entryNames:get(index: selectedRow));
			});
			selectedPaths: Array([chosenDir]);
		}, {
		if({ saveMode:current() }, {
			if({ fileName == '' }, { return; });
			selectedPaths: Array([:joinPath(dir: curDir, name: fileName)]);
		}, {
			if({ selectedPaths:length() == 0 }, {
				if({ fileName == '' }, { return; });
				local String is resolved: if({ fileName:byteAt(index: 0) == 47 }, { fileName }, { :joinPath(dir: curDir, name: fileName) });
				selectedPaths: Array([resolved]);
			});
		}); });
		local Array of String is chosen: selectedPaths;
		:closeWindow();
		open:emit(value: false);
		local Function is scb: onSelect;
		scb(chosen);
	}

	## Polled once per frame by `ToolkitContainer:run`.
	Function is poll(){
		local Boolean is wantOpen: open:current();
		if({ wantOpen && !isShown }, {
			:openWindow();
			return;
		});
		if({ !wantOpen && isShown }, {
			:closeWindow();
			return;
		});
		if({ !isShown }, { return; });

		if({ !win:poll() }, {
			:finishCancel();
			return;
		});

		local Int is key: win:nextKey();
		while({ key != 0 }, {
			if({ key == 27 }, {
				if({ focusTarget == 1 }, {
					editPath: curDir;
					focusTarget: 0;
					isDirty: true;
				}, {
					:finishCancel();
					return;
				});
			});
			if({ key == 13 }, {
				if({ focusTarget == 1 }, {
					if({ editPath != '' && Dir():isDir(path: editPath) }, {
						:loadDirectory(dirPath: editPath);
					}, {
						editPath: curDir;
					});
					focusTarget: 0;
					isDirty: true;
				}, {
					if({ :canConfirm() }, {
						:finishOpen();
						return;
					});
				});
			});
			if({ key == 8 }, {
				if({ focusTarget == 1 && editPath:length() > 0 }, {
					editPath: :popLastChar(s: editPath);
					isDirty: true;
				});
				if({ focusTarget == 2 && fileName:length() > 0 }, {
					fileName: :popLastChar(s: fileName);
					if({ !saveMode:current() }, { selectedPaths: Array(); });
					isDirty: true;
				});
			});
			key: win:nextKey();
		});

		local Int is cp: win:nextChar();
		while({ cp != 0 }, {
			if({ cp >= 32 }, {
				if({ focusTarget == 1 }, {
					editPath: editPath . String:fromCodePoint(code: cp);
					isDirty: true;
				});
				if({ focusTarget == 2 }, {
					fileName: fileName . String:fromCodePoint(code: cp);
					if({ !saveMode:current() }, { selectedPaths: Array(); });
					isDirty: true;
				});
			});
			cp: win:nextChar();
		});

		local Int is sy: win:pollScrollY();
		if({ sy != 0 }, {
			local Int is step: if({ sy > 0 }, { 2 }, { -2 });
			scrollRow: scrollRow + step;
			if({ scrollRow < 0 }, { scrollRow: 0; });
			isDirty: true;
		});

		local Int is w: win:width();
		local Int is h: win:height();
		if({ w != lastW || h != lastH }, {
			isDirty: true;
		});

		local Int is headerH: :headerHeightPx();
		local Int is footerH: :footerHeightPx();
		local Int is rowH: scale:px(pt: 28.0);
		local Int is padX: scale:px(pt: 10.0);
		local Int is sbW: scale:px(pt: 12.0);
		local Int is sideW: :sidebarWidthPx(totalW: w);
		local Int is listY: headerH;
		local Int is listH: if({ h > headerH + footerH }, { h - headerH - footerH }, { 0 });
		local Int is listX: sideW;
		local Int is listW: if({ w - sideW > sbW }, { w - sideW - sbW }, { w - sideW });
		local Int is sbX: listX + listW;

		local Int is upW: scale:px(pt: 44.0);
		local Int is hidW: scale:px(pt: 70.0);
		local Int is topBoxH: scale:px(pt: 26.0);
		local Int is topBoxY: (headerH - topBoxH) / 2;
		local Int is hidX: w - padX - hidW;
		local Int is pathX: padX + upW + scale:px(pt: 8.0);
		local Int is pathW: if({ hidX - scale:px(pt: 8.0) > pathX }, { hidX - scale:px(pt: 8.0) - pathX }, { 40 });

		local Int is fy: h - footerH;
		local Int is boxY: fy + scale:px(pt: 8.0);
		local Int is boxH: scale:px(pt: 26.0);
		local Int is btnW: scale:px(pt: 86.0);
		local Int is btnH: scale:px(pt: 28.0);
		local Int is btnY: fy + footerH - btnH - scale:px(pt: 8.0);
		local Int is openX: w - padX - btnW;
		local Int is cancelX: openX - scale:px(pt: 10.0) - btnW;

		local Int is px: win:pointerX();
		local Int is py: win:pointerY();
		local Int is pinHdrH: scale:px(pt: 24.0);

		local Int is nextHoverRow: -1;
		if({ px >= listX && px < sbX && py >= listY && py < listY + listH && rowH > 0 }, {
			local Int is cand: scrollRow + (py - listY) / rowH;
			if({ cand >= 0 && cand < entryNames:length() }, { nextHoverRow: cand; });
		});
		local Int is nextHoverPin: -1;
		if({ sideW > 0 && px >= 0 && px < sideW && py >= listY + pinHdrH && py < listY + listH && rowH > 0 }, {
			local Int is pcand: (py - (listY + pinHdrH)) / rowH;
			if({ pcand >= 0 && pcand < pinned:names:length() }, { nextHoverPin: pcand; });
		});
		local Int is nextHoverBtn: 0;
		if({ py >= topBoxY && py < topBoxY + topBoxH }, {
			if({ px >= padX && px < padX + upW }, { nextHoverBtn: 3; });
			if({ px >= hidX && px < hidX + hidW }, { nextHoverBtn: 4; });
		});
		if({ py >= btnY && py < btnY + btnH }, {
			if({ px >= cancelX && px < cancelX + btnW }, { nextHoverBtn: 1; });
			if({ px >= openX && px < openX + btnW }, { nextHoverBtn: 2; });
		});
		if({ nextHoverRow != hoverRow || nextHoverPin != hoverPinIdx || nextHoverBtn != hoverBtn }, {
			hoverRow: nextHoverRow;
			hoverPinIdx: nextHoverPin;
			hoverBtn: nextHoverBtn;
			isDirty: true;
		});

		## Folder drag-and-drop onto the left "Pinned" panel
		if({ win:pointerDown() }, {
			if({ dragCandidateRow >= 0 && !isDraggingFolder }, {
				local Int is dx: px - dragStartX;
				local Int is dy: py - dragStartY;
				if({ dx * dx + dy * dy > 36 }, {
					isDraggingFolder: true;
					isDirty: true;
				});
			});
			if({ isDraggingFolder }, {
				local Boolean is overPin: sideW > 0 && px >= 0 && px < sideW && py >= listY && py < listY + listH;
				if({ overPin != dragOverPinned }, {
					dragOverPinned: overPin;
				});
				isDirty: true;
			});
		}, {
			if({ isDraggingFolder }, {
				if({ sideW > 0 && px >= 0 && px < sideW && py >= listY && py < listY + listH }, {
					:addPinned(name: dragFolderName, path: dragFolderPath);
					:savePinnedToConfig();
				});
				isDraggingFolder: false;
				dragOverPinned: false;
				dragFolderName: '';
				dragFolderPath: '';
				isDirty: true;
			});
			dragCandidateRow: -1;
			dragScrollbar: false;
		});

		if({ dragScrollbar && listH > 0 && rowH > 0 }, {
			local Int is visRows: listH / rowH;
			local Int is maxScroll: if({ entryNames:length() > visRows }, { entryNames:length() - visRows }, { 0 });
			if({ maxScroll > 0 }, {
				local Int is nextRow: ((py - listY) * maxScroll) / listH;
				if({ nextRow < 0 }, { nextRow: 0; });
				if({ nextRow > maxScroll }, { nextRow: maxScroll; });
				if({ nextRow != scrollRow }, {
					scrollRow: nextRow;
					isDirty: true;
				});
			});
		});

		if({ win:pollClick() }, {
			local Int is cx: win:clickX();
			local Int is cy: win:clickY();

			## Top path bar clicks
			if({ cy >= topBoxY && cy < topBoxY + topBoxH }, {
				if({ cx >= padX && cx < padX + upW }, {
					focusTarget: 0;
					:loadDirectory(dirPath: :parentDir(dir: curDir));
					return;
				});
				if({ cx >= hidX && cx < hidX + hidW }, {
					focusTarget: 0;
					showHidden: !showHidden;
					:loadDirectory(dirPath: curDir);
					return;
				});
				if({ cx >= pathX && cx < pathX + pathW }, {
					focusTarget: 1;
					editPath: curDir;
					isDirty: true;
					return;
				});
			});

			## Footer Name input & Cancel/Open/Save clicks
			if({ cy >= boxY && cy < boxY + boxH }, {
				focusTarget: 2;
				isDirty: true;
				return;
			});
			if({ cy >= btnY && cy < btnY + btnH }, {
				if({ cx >= cancelX && cx < cancelX + btnW }, {
					:finishCancel();
					return;
				});
				if({ cx >= openX && cx < openX + btnW }, {
					:finishOpen();
					return;
				});
			});

			## Left "Pinned" panel clicks
			if({ sideW > 0 && cx >= 0 && cx < sideW && cy >= listY + pinHdrH && cy < listY + listH && rowH > 0 }, {
				local Int is pidx: (cy - (listY + pinHdrH)) / rowH;
				if({ pidx >= 0 && pidx < pinned:paths:length() }, {
					focusTarget: 0;
					local String is target: pinned:paths:get(index: pidx);
					if({ Dir():isDir(path: target) }, {
						:loadDirectory(dirPath: target);
					});
					return;
				});
			});

			## Scrollbar click
			if({ cx >= sbX && cx < w && cy >= listY && cy < listY + listH && listH > 0 && rowH > 0 }, {
				focusTarget: 0;
				dragScrollbar: true;
				local Int is visRows: listH / rowH;
				local Int is maxScroll: if({ entryNames:length() > visRows }, { entryNames:length() - visRows }, { 0 });
				if({ maxScroll > 0 }, {
					scrollRow: ((cy - listY) * maxScroll) / listH;
					if({ scrollRow < 0 }, { scrollRow: 0; });
					if({ scrollRow > maxScroll }, { scrollRow: maxScroll; });
					isDirty: true;
				});
				return;
			});

			## File list click
			if({ cx >= listX && cx < sbX && cy >= listY && cy < listY + listH && rowH > 0 }, {
				focusTarget: 0;
				local Int is idx: scrollRow + (cy - listY) / rowH;
				if({ idx >= 0 && idx < entryNames:length() }, {
					local Int is nowMs: clock:monotonicMs();
					local Boolean is isDouble: (idx == lastClickRow) && ((nowMs - lastClickMs) <= 450);
					lastClickRow: idx;
					lastClickMs: nowMs;

					local String is name: entryNames:get(index: idx);
					local Boolean is isD: entryIsDir:get(index: idx);
					if({ isD }, {
						if({ isDouble }, {
							if({ name == '..' }, {
								:loadDirectory(dirPath: :parentDir(dir: curDir));
							}, {
								:loadDirectory(dirPath: :joinPath(dir: curDir, name: name));
							});
						}, {
							selectedRow: idx;
							if({ name != '..' }, {
								dragCandidateRow: idx;
								dragStartX: cx;
								dragStartY: cy;
								dragFolderName: name;
								dragFolderPath: :joinPath(dir: curDir, name: name);
							});
							isDirty: true;
						});
					}, {
						local String is full: :joinPath(dir: curDir, name: name);
						selectedRow: idx;
						fileName: name;
						if({ isDouble }, {
							if({ !saveMode:current() }, { :selectSingleFile(fullPath: full); });
							:finishOpen();
							return;
						}, {
							if({ !saveMode:current() }, { :toggleSelect(fullPath: full); });
							isDirty: true;
						});
					});
				});
			});
		});

		if({ isDirty }, {
			:paintDialog();
		});
	}

	Function is dispose(){
		signalBag:clear();
		:closeWindow();
	}
}
