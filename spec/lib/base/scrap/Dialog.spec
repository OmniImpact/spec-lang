#! Package base:scrap
#! Generic non-blocking secondary dialog window host bound to a `BoolEmitter` and a `SewNode` content tree.

Class is Dialog{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', SignalBag],
		['base', 'suit', SuitWindow],
		['base', 'suit', SuitCanvas],
		['base', 'sew', SewNode],
		['base', 'sew', FocusNav],
		['base', 'sew', Constraints],
		['base', 'sew', Rect],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', Tooltip]
	];

	String is title: 'Dialog';
	BoolEmitter is open: BoolEmitter(initial: false);
	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	Float is widthPt: 480.0;
	Float is heightPt: 180.0;
	Float is minWidthPt: 320.0;
	Float is minHeightPt: 140.0;
	SewNode is content: SewNode();
	Boolean is hasContent: false;
	Function is onPaint: local Function(DrawContext is ctx, Int is w, Int is h, Theme is theme, Scale is scale){};
	Function is onTick: local Function(Int is _nowMs){};

	SuitWindow is win: SuitWindow();
	SuitCanvas is canvas: SuitCanvas(width: 1, height: 1);
	DrawContext is paintCtx: DrawContext(canvas: SuitCanvas(width: 1, height: 1));
	Boolean is isShown: false;
	Boolean is isDirty: false;
	Boolean is layoutDirty: true;
	Int is lastW: 0;
	Int is lastH: 0;
	Int is lastPtrX: -1;
	Int is lastPtrY: -1;
	Boolean is wasPtrDown: false;
	String is activeTooltip: '';
	SignalBag is signalBag: SignalBag();

	replace Function is init(
		String is title: 'Dialog',
		BoolEmitter is open: BoolEmitter(initial: false),
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0),
		Float is widthPt: 480.0,
		Float is heightPt: 180.0,
		Float is minWidthPt: 320.0,
		Float is minHeightPt: 140.0,
		SewNode is content: SewNode(),
		Boolean is hasContent: true,
		Function is onPaint: local Function(DrawContext is ctx, Int is w, Int is h, Theme is theme, Scale is scale){},
		Function is onTick: local Function(Int is _nowMs){}
	){
		:title: title;
		:open: open;
		:theme: theme;
		:scale: scale;
		:widthPt: widthPt;
		:heightPt: heightPt;
		:minWidthPt: minWidthPt;
		:minHeightPt: minHeightPt;
		:content: content;
		:hasContent: hasContent;
		:onPaint: onPaint;
		:onTick: onTick;
		isShown: false;
		isDirty: false;
		lastW: 0;
		lastH: 0;
	}

	Function is applyTheme(Theme is theme){
		:theme: theme;
		if({ hasContent }, { content:applyTheme(theme: theme); });
		layoutDirty: true;
		isDirty: true;
	}

	Function is setScale(Scale is scale){
		:scale: scale;
		if({ hasContent }, { content:setScale(scale: scale); });
		layoutDirty: true;
		isDirty: true;
	}

	local Function is paintDialog(){
		local Int is w: win:width();
		local Int is h: win:height();
		if({ w <= 0 || h <= 0 }, { return; });
		if({ w != lastW || h != lastH }, {
			canvas:resize(width: w, height: h);
			layoutDirty: true;
		});
		paintCtx:rebind(canvas: canvas);
		local DrawContext is ctx: paintCtx;
		ctx:fillRect(x: 0, y: 0, w: w, h: h, color: theme:windowBg);
		if({ hasContent }, {
			if({ layoutDirty }, {
				content:applyTheme(theme: theme);
				content:setScale(scale: scale);
				content:measure(c: Constraints(minW: w, maxW: w, minH: h, maxH: h));
				content:arrange(bounds: Rect(x: 0, y: 0, width: w, height: h));
				layoutDirty: false;
			});
			content:paint(ctx: ctx);
			if({ activeTooltip != '' && lastPtrX >= 0 && lastPtrY >= 0 }, {
				Tooltip:shared:paint(ctx: ctx, theme: theme, scale: scale, text: activeTooltip, ptrX: lastPtrX, ptrY: lastPtrY, winW: w, winH: h);
			});
		}, {
			local Function is cb: onPaint;
			cb(ctx, w, h, theme, scale);
		});
		win:present(canvas: canvas);
		lastW: w;
		lastH: h;
		isDirty: false;
	}

	local Function is openWindow(){
		if({ isShown }, { return; });
		win: SuitWindow(
			title: title,
			width: scale:px(pt: widthPt),
			height: scale:px(pt: heightPt),
			decorated: true,
			useVulkan: false
		);
		if({ !win:open() }, {
			open:emit(value: false);
			return;
		});
		if({ minWidthPt > 0.0 || minHeightPt > 0.0 }, {
			win:setMinSize(minW: scale:px(pt: minWidthPt), minH: scale:px(pt: minHeightPt));
		});
		if({ hasContent }, {
			content:bindDirty(cb: local Function(){ :isDirty: true; });
		});
		canvas: SuitCanvas(width: win:width(), height: win:height());
		lastPtrX: -1;
		lastPtrY: -1;
		wasPtrDown: false;
		activeTooltip: '';
		layoutDirty: true;
		isShown: true;
		:paintDialog();
	}

	Function is closeWindow(){
		if({ !isShown }, { return; });
		isShown: false;
		canvas:dispose();
		win:close();
	}

	Function of Boolean is tick(Int is nowMs){
		if({ !isShown }, { return false; });
		local Function is cb: onTick;
		cb(nowMs);
		if({ hasContent && content:tick(nowMs: nowMs) }, {
			isDirty: true;
			return true;
		});
		return false;
	}

	local Function of Boolean is stepFocusTab(Boolean is reverse){
		if({ !hasContent }, { return false; });
		local Array of SewNode is focusables: Array();
		content:collectFocusables(out: focusables);
		return FocusNav:shared:stepTab(focusables: focusables, reverse: reverse);
	}

	local Function is syncFocusOnClick(Int is x, Int is y){
		if({ !hasContent }, { return; });
		local Array of SewNode is focusables: Array();
		content:collectFocusables(out: focusables);
		if({ FocusNav:shared:syncClick(focusables: focusables, x: x, y: y) }, {
			isDirty: true;
		});
	}

	## Polled once per frame by `ToolkitContainer:run`. Returns `true` when activity or redraw occurred.
	Function of Boolean is poll(){
		local Boolean is wantOpen: open:current();
		if({ wantOpen && !isShown }, {
			:openWindow();
			return true;
		});
		if({ !wantOpen && isShown }, {
			:closeWindow();
			return true;
		});
		if({ !isShown }, { return false; });

		if({ !win:pollTimeout(timeoutMs: 0) }, {
			:closeWindow();
			open:emit(value: false);
			return true;
		});

		local Boolean is active: isDirty;
		if({ win:width() != lastW || win:height() != lastH }, {
			layoutDirty: true;
			isDirty: true;
			active: true;
		});
		if({ isDirty }, {
			:paintDialog();
		});

		local Int is curMods: win:mods();
		local Int is key: win:nextKey();
		while({ key != 0 }, {
			active: true;
			if({ key == 27 }, {
				:closeWindow();
				open:emit(value: false);
				return true;
			});
			if({ hasContent }, {
				if({ key == 9 }, {
					if({ :stepFocusTab(reverse: (curMods & 1) != 0) }, {
						isDirty: true;
					});
				}, {
					if({ content:onKey(key: key, mods: curMods) }, {
						isDirty: true;
					});
				});
			});
			key: win:nextKey();
		});

		local Int is cp: win:nextChar();
		while({ cp != 0 }, {
			active: true;
			if({ hasContent && cp >= 32 }, {
				if({ content:onText(ch: String:fromCodePoint(code: cp), mods: curMods) }, {
					isDirty: true;
				});
			});
			cp: win:nextChar();
		});

		local Int is sy: win:pollScrollY();
		if({ sy != 0 && hasContent }, {
			active: true;
			if({ content:onScroll(deltaY: sy) }, {
				isDirty: true;
			});
		});

		local Boolean is ptrDown: win:pointerDown();
		local Int is px: win:pointerX();
		local Int is py: win:pointerY();
		if({ ptrDown && !wasPtrDown && hasContent }, {
			active: true;
			if({ content:onPointerDrag(x: px, y: py, mods: curMods) }, {
				isDirty: true;
			});
		});
		if({ px != lastPtrX || py != lastPtrY }, {
			lastPtrX: px;
			lastPtrY: py;
			active: true;
			if({ hasContent }, {
				if({ ptrDown }, {
					if({ content:onPointerDrag(x: px, y: py, mods: curMods) }, {
						isDirty: true;
					});
				});
				if({ content:onPointerMove(x: px, y: py) }, {
					isDirty: true;
				});
				local String is nextTip: content:tooltipAt(x: px, y: py);
				if({ nextTip != activeTooltip }, {
					:activeTooltip: nextTip;
					isDirty: true;
				});
			});
		});
		if({ !ptrDown && wasPtrDown && hasContent }, {
			active: true;
			if({ content:onPointerUp(x: px, y: py) }, {
				isDirty: true;
			});
		});
		wasPtrDown: ptrDown;

		if({ win:pollClick() }, {
			active: true;
			if({ hasContent }, {
				local Int is cx: win:clickX();
				local Int is cy: win:clickY();
				if({ content:onPointerClickMod(x: cx, y: cy, mods: curMods) }, {
					isDirty: true;
				});
				:syncFocusOnClick(x: cx, y: cy);
			});
		});

		if({ win:width() != lastW || win:height() != lastH }, {
			layoutDirty: true;
			isDirty: true;
			active: true;
		});

		if({ isDirty }, {
			:paintDialog();
			active: true;
		});
		return active;
	}

	Function is dispose(){
		signalBag:clear();
		:closeWindow();
	}
}
