#! Package base:wardrobe
#! Reusable non-blocking file picker dialog supporting single or multi-file selection,
#! bordered directory entries, double-click to open, scroll wheel, and `onSelect`/`onCancel` callbacks.

Class is FileDialog{
	replace [String] is namespace: ['base', 'wardrobe'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', Dir],
		['base', 'sys', Time],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'signal', SignalBag],
		['base', 'suit', SuitWindow],
		['base', 'suit', SuitCanvas],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	String is title: 'Open File';
	BoolEmitter is open: BoolEmitter(initial: false);
	BoolEmitter is saveMode: BoolEmitter(initial: false);
	TextEmitter is dialogTitle: TextEmitter(initial: '');
	TextEmitter is suggestedName: TextEmitter(initial: '');
	Boolean is allowMultiple: false;
	String is initialDir: '.';
	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	Float is widthPt: 580.0;
	Float is heightPt: 420.0;
	Function is onSelect: local Function(Array of String is paths){};
	Function is onCancel: local Function(){};

	SuitWindow is win: SuitWindow();
	SuitCanvas is canvas: SuitCanvas(width: 1, height: 1);
	DrawContext is paintCtx: DrawContext(canvas: SuitCanvas(width: 1, height: 1));
	Time is clock: Time();
	Boolean is isShown: false;
	Boolean is isDirty: false;
	SignalBag is signalBag: SignalBag();

	String is curDir: '.';
	Array of String is entryNames: Array();
	Array of Boolean is entryIsDir: Array();
	Array of String is selectedPaths: Array();
	Int is selectedRow: -1;
	Int is scrollRow: 0;
	Int is hoverRow: -1;
	Int is hoverBtn: 0; ## 0=none, 1=Cancel, 2=Open
	Int is lastClickRow: -1;
	Int is lastClickMs: 0;
	Boolean is dragScrollbar: false;
	String is fileName: '';

	replace Function is init(
		String is title: 'Open File',
		BoolEmitter is open: BoolEmitter(initial: false),
		BoolEmitter is saveMode: BoolEmitter(initial: false),
		TextEmitter is dialogTitle: TextEmitter(initial: ''),
		TextEmitter is suggestedName: TextEmitter(initial: ''),
		Boolean is allowMultiple: false,
		String is initialDir: '.',
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0),
		Float is widthPt: 580.0,
		Float is heightPt: 420.0,
		Function is onSelect: local Function(Array of String is paths){},
		Function is onCancel: local Function(){}
	){
		:title: title;
		:open: open;
		:saveMode: saveMode;
		:dialogTitle: dialogTitle;
		:suggestedName: suggestedName;
		:allowMultiple: allowMultiple;
		:initialDir: initialDir;
		:curDir: initialDir;
		:theme: theme;
		:scale: scale;
		:widthPt: widthPt;
		:heightPt: heightPt;
		:onSelect: onSelect;
		:onCancel: onCancel;
		:entryNames: Array();
		:entryIsDir: Array();
		:selectedPaths: Array();
		isShown: false;
		isDirty: false;
		selectedRow: -1;
		scrollRow: 0;
		hoverRow: -1;
		hoverBtn: 0;
		lastClickRow: -1;
		lastClickMs: 0;
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
		if({ dir == '/' }, { return '/'; });
		local Int is len: dir:length();
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

	local Function of Int is strCmp(String is a, String is b){
		local Int is la: a:length();
		local Int is lb: b:length();
		local Int is minL: if({ la < lb }, { la }, { lb });
		local Int is i: 0;
		while({ i < minL }, {
			local Int is ca: a:byteAt(index: i);
			local Int is cb: b:byteAt(index: i);
			if({ ca != cb }, { return ca - cb; });
			i: i + 1;
		});
		return la - lb;
	}

	local Function is loadDirectory(String is dirPath){
		curDir: dirPath;
		entryNames: Array();
		entryIsDir: Array();
		selectedPaths: Array();
		selectedRow: -1;
		scrollRow: 0;
		hoverRow: -1;
		lastClickRow: -1;

		entryNames:add(item: '..');
		entryIsDir:add(item: true);

		local Dir is d: Dir();
		local Array of String is raw: d:dirList(path: curDir);
		local Array of String is dirs: Array();
		local Array of String is files: Array();

		times(count: raw:length(), worker: local Function(Int is i){
			local String is name: raw:get(index: i);
			local String is full: :joinPath(dir: curDir, name: name);
			if({ d:isDir(path: full) }, {
				dirs:add(item: name);
			}, {
				files:add(item: name);
			});
		});

		local Int is di: 1;
		while({ di < dirs:length() }, {
			local String is key: dirs:get(index: di);
			local Int is j: di - 1;
			while({ j >= 0 && :strCmp(a: dirs:get(index: j), b: key) > 0 }, {
				dirs:set(index: j + 1, item: dirs:get(index: j));
				j: j - 1;
			});
			dirs:set(index: j + 1, item: key);
			di: di + 1;
		});
		local Int is fi: 1;
		while({ fi < files:length() }, {
			local String is key: files:get(index: fi);
			local Int is j: fi - 1;
			while({ j >= 0 && :strCmp(a: files:get(index: j), b: key) > 0 }, {
				files:set(index: j + 1, item: files:get(index: j));
				j: j - 1;
			});
			files:set(index: j + 1, item: key);
			fi: fi + 1;
		});

		times(count: dirs:length(), worker: local Function(Int is i){
			entryNames:add(item: dirs:get(index: i));
			entryIsDir:add(item: true);
		});
		times(count: files:length(), worker: local Function(Int is i){
			entryNames:add(item: files:get(index: i));
			entryIsDir:add(item: false);
		});
		isDirty: true;
	}

	local Function of Int is fontPx(){
		local Int is px: scale:px(pt: 17.0);
		return if({ px < 12 }, { 12 }, { px });
	}

	local Function of Int is footerHeightPx(){
		return if({ saveMode:current() }, { scale:px(pt: 78.0) }, { scale:px(pt: 44.0) });
	}

	local Function of Boolean is canConfirm(){
		if({ saveMode:current() }, { return fileName != ''; });
		return selectedPaths:length() > 0;
	}

	local Function is popFileNameChar(){
		local Int is len: fileName:length();
		if({ len <= 0 }, { return; });
		local Int is i: len - 1;
		while({ i > 0 && ((fileName:byteAt(index: i) & 192) == 128) }, {
			i: i - 1;
		});
		fileName: fileName:substring(start: 0, end: i);
	}

	local Function is paintDialog(){
		local Int is w: win:width();
		local Int is h: win:height();
		if({ w <= 0 || h <= 0 }, { return; });
		canvas:resize(width: w, height: h);
		paintCtx:rebind(canvas: canvas);
		local DrawContext is ctx: paintCtx;

		local Int is headerH: scale:px(pt: 32.0);
		local Int is footerH: :footerHeightPx();
		local Int is rowH: scale:px(pt: 28.0);
		local Int is padX: scale:px(pt: 12.0);
		local Int is sbW: scale:px(pt: 12.0);
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);

		ctx:fillRect(x: 0, y: 0, w: w, h: h, color: theme:windowBg);

		## Header bar showing current directory
		ctx:fillRect(x: 0, y: 0, w: w, h: headerH, color: theme:toolbarBg);
		ctx:fillRect(x: 0, y: headerH - 1, w: w, h: 1, color: theme:toolbarBorder);
		ctx:drawText(x: padX, y: (headerH - th) / 2, text: 'Dir: ' . curDir, color: theme:textPrimary, pixelHeight: fpx);

		## File list area + right scrollbar
		local Int is listY: headerH;
		local Int is listH: if({ h > headerH + footerH }, { h - headerH - footerH }, { 0 });
		local Int is listW: if({ w > sbW }, { w - sbW }, { w });
		local Int is visRows: if({ rowH > 0 }, { listH / rowH }, { 0 });
		local Int is maxScroll: if({ entryNames:length() > visRows }, { entryNames:length() - visRows }, { 0 });
		if({ scrollRow > maxScroll }, { scrollRow: maxScroll; });
		if({ scrollRow < 0 }, { scrollRow: 0; });

		ctx:setClip(x: 0, y: listY, w: listW, h: listH);
		local Int is r: 0;
		while({ r <= visRows && (scrollRow + r) < entryNames:length() }, {
			local Int is idx: scrollRow + r;
			local Int is ry: listY + r * rowH;
			local String is name: entryNames:get(index: idx);
			local Boolean is isD: entryIsDir:get(index: idx);
			local String is full: :joinPath(dir: curDir, name: name);
			local Boolean is isSel: if({ isD }, { selectedRow == idx }, { :isPathSelected(fullPath: full) });

			if({ isSel }, {
				ctx:fillRect(x: 4, y: ry + 2, w: listW - 8, h: rowH - 4, color: theme:activeBg);
			}, {
				if({ hoverRow == idx }, {
					ctx:fillRect(x: 4, y: ry + 2, w: listW - 8, h: rowH - 4, color: theme:hoverBg);
				});
			});

			## Directories are rendered with a crisp border around them to differentiate from files
			if({ isD }, {
				ctx:strokeRect(x: 4, y: ry + 2, w: listW - 8, h: rowH - 4, color: theme:menuBorder);
			});

			ctx:drawText(x: padX, y: ry + (rowH - th) / 2, text: name, color: theme:textPrimary, pixelHeight: fpx);
			r: r + 1;
		});
		ctx:clearClip();

		## Right-side scrollbar for file list
		ctx:fillRect(x: listW, y: listY, w: sbW, h: listH, color: theme:menuBg);
		ctx:fillRect(x: listW, y: listY, w: 1, h: listH, color: theme:toolbarBorder);
		if({ entryNames:length() > visRows && entryNames:length() > 0 && listH > 0 }, {
			local Int is thumbH: (listH * visRows) / entryNames:length();
			if({ thumbH < scale:px(pt: 20.0) }, { thumbH: scale:px(pt: 20.0); });
			if({ thumbH > listH }, { thumbH: listH; });
			local Int is trackRange: listH - thumbH;
			local Int is thumbY: listY + if({ maxScroll > 0 }, { (scrollRow * trackRange) / maxScroll }, { 0 });
			ctx:fillRect(x: listW + 2, y: thumbY + 1, w: sbW - 4, h: thumbH - 2, color: theme:activeBg);
		});

		## Footer bar with optional filename input (Save mode), Cancel, and Open/Save buttons
		local Int is fy: h - footerH;
		ctx:fillRect(x: 0, y: fy, w: w, h: footerH, color: theme:toolbarBg);
		ctx:fillRect(x: 0, y: fy, w: w, h: 1, color: theme:toolbarBorder);

		local Int is btnW: scale:px(pt: 86.0);
		local Int is btnH: scale:px(pt: 28.0);
		local Int is btnY: if({ saveMode:current() }, { fy + footerH - btnH - scale:px(pt: 8.0) }, { fy + (footerH - btnH) / 2 });
		local Int is openX: w - padX - btnW;
		local Int is cancelX: openX - scale:px(pt: 10.0) - btnW;

		if({ saveMode:current() }, {
			local String is nameLbl: 'Name:';
			local Int is lw: ctx:measureTextWidth(text: nameLbl, pixelHeight: fpx);
			local Int is boxX: padX + lw + scale:px(pt: 8.0);
			local Int is boxY: fy + scale:px(pt: 8.0);
			local Int is boxH: scale:px(pt: 26.0);
			local Int is boxW: if({ w - padX > boxX }, { w - padX - boxX }, { 40 });
			ctx:drawText(x: padX, y: boxY + (boxH - th) / 2, text: nameLbl, color: theme:textPrimary, pixelHeight: fpx);
			ctx:fillRect(x: boxX, y: boxY, w: boxW, h: boxH, color: theme:windowBg);
			ctx:strokeRect(x: boxX, y: boxY, w: boxW, h: boxH, color: theme:menuBorder);
			ctx:setClip(x: boxX + 2, y: boxY, w: boxW - 4, h: boxH);
			ctx:drawText(x: boxX + scale:px(pt: 6.0), y: boxY + (boxH - th) / 2, text: fileName . '|', color: theme:textPrimary, pixelHeight: fpx);
			ctx:clearClip();
		});

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

		win:present(canvas: canvas);
		isDirty: false;
	}

	local Function is openWindow(){
		if({ isShown }, { return; });
		local String is effTitle: if({ dialogTitle:current() != '' }, { dialogTitle:current() }, { title });
		fileName: if({ saveMode:current() }, { suggestedName:current() }, { '' });
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
		if({ saveMode:current() }, {
			if({ fileName == '' }, { return; });
			selectedPaths: Array([:joinPath(dir: curDir, name: fileName)]);
		}, {
			if({ selectedPaths:length() == 0 }, { return; });
		});
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
				:finishCancel();
				return;
			});
			if({ saveMode:current() }, {
				if({ key == 13 && fileName != '' }, {
					:finishOpen();
					return;
				});
				if({ key == 8 && fileName:length() > 0 }, {
					:popFileNameChar();
					isDirty: true;
				});
			});
			key: win:nextKey();
		});

		local Int is cp: win:nextChar();
		while({ cp != 0 }, {
			if({ saveMode:current() && cp >= 32 }, {
				fileName: fileName . String:fromCodePoint(code: cp);
				isDirty: true;
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
		local Int is headerH: scale:px(pt: 32.0);
		local Int is footerH: :footerHeightPx();
		local Int is rowH: scale:px(pt: 28.0);
		local Int is padX: scale:px(pt: 12.0);
		local Int is sbW: scale:px(pt: 12.0);
		local Int is listY: headerH;
		local Int is listH: if({ h > headerH + footerH }, { h - headerH - footerH }, { 0 });
		local Int is listW: if({ w > sbW }, { w - sbW }, { w });
		local Int is btnW: scale:px(pt: 86.0);
		local Int is btnH: scale:px(pt: 28.0);
		local Int is fy: h - footerH;
		local Int is btnY: if({ saveMode:current() }, { fy + footerH - btnH - scale:px(pt: 8.0) }, { fy + (footerH - btnH) / 2 });
		local Int is openX: w - padX - btnW;
		local Int is cancelX: openX - scale:px(pt: 10.0) - btnW;

		local Int is px: win:pointerX();
		local Int is py: win:pointerY();
		local Int is nextHoverRow: -1;
		if({ px < listW && py >= listY && py < listY + listH && rowH > 0 }, {
			local Int is cand: scrollRow + (py - listY) / rowH;
			if({ cand >= 0 && cand < entryNames:length() }, { nextHoverRow: cand; });
		});
		local Int is nextHoverBtn: 0;
		if({ py >= btnY && py < btnY + btnH }, {
			if({ px >= cancelX && px < cancelX + btnW }, { nextHoverBtn: 1; });
			if({ px >= openX && px < openX + btnW }, { nextHoverBtn: 2; });
		});
		if({ nextHoverRow != hoverRow || nextHoverBtn != hoverBtn }, {
			hoverRow: nextHoverRow;
			hoverBtn: nextHoverBtn;
			isDirty: true;
		});

		if({ !win:pointerDown() }, {
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
			if({ cx >= listW && cx < w && cy >= listY && cy < listY + listH && listH > 0 && rowH > 0 }, {
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
			if({ cx < listW && cy >= listY && cy < listY + listH && rowH > 0 }, {
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
							isDirty: true;
						});
					}, {
						local String is full: :joinPath(dir: curDir, name: name);
						selectedRow: idx;
						if({ saveMode:current() }, {
							fileName: name;
							if({ isDouble }, {
								:finishOpen();
								return;
							});
							isDirty: true;
						}, {
							if({ isDouble }, {
								:selectSingleFile(fullPath: full);
								:finishOpen();
								return;
							}, {
								:toggleSelect(fullPath: full);
								isDirty: true;
							});
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
