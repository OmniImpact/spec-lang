#! Package base:scrap
#! Generic non-blocking secondary dialog window host bound to a `BoolEmitter` and a `SewNode` content tree.

Class is Dialog{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'signal', BoolEmitter],
		['base', 'signal', SignalBag],
		['base', 'suit', SuitWindow],
		['base', 'suit', SuitCanvas],
		['base', 'sew', SewNode],
		['base', 'sew', Constraints],
		['base', 'sew', Rect],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	String is title: 'Dialog';
	BoolEmitter is open: BoolEmitter(initial: false);
	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	Float is widthPt: 480.0;
	Float is heightPt: 180.0;
	SewNode is content: SewNode();
	Boolean is hasContent: false;
	Function is onPaint: local Function(DrawContext is ctx, Int is w, Int is h, Theme is theme, Scale is scale){};

	SuitWindow is win: SuitWindow();
	SuitCanvas is canvas: SuitCanvas(width: 1, height: 1);
	DrawContext is paintCtx: DrawContext(canvas: SuitCanvas(width: 1, height: 1));
	Boolean is isShown: false;
	Boolean is isDirty: false;
	SignalBag is signalBag: SignalBag();

	replace Function is init(
		String is title: 'Dialog',
		BoolEmitter is open: BoolEmitter(initial: false),
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0),
		Float is widthPt: 480.0,
		Float is heightPt: 180.0,
		SewNode is content: SewNode(),
		Boolean is hasContent: true,
		Function is onPaint: local Function(DrawContext is ctx, Int is w, Int is h, Theme is theme, Scale is scale){}
	){
		:title: title;
		:open: open;
		:theme: theme;
		:scale: scale;
		:widthPt: widthPt;
		:heightPt: heightPt;
		:content: content;
		:hasContent: hasContent;
		:onPaint: onPaint;
		isShown: false;
		isDirty: false;
	}

	Function is applyTheme(Theme is theme){
		:theme: theme;
		if({ hasContent }, { content:applyTheme(theme: theme); });
		isDirty: true;
	}

	Function is setScale(Scale is scale){
		:scale: scale;
		if({ hasContent }, { content:setScale(scale: scale); });
		isDirty: true;
	}

	local Function is paintDialog(){
		local Int is w: win:width();
		local Int is h: win:height();
		if({ w <= 0 || h <= 0 }, { return; });
		canvas:resize(width: w, height: h);
		paintCtx:rebind(canvas: canvas);
		local DrawContext is ctx: paintCtx;
		ctx:fillRect(x: 0, y: 0, w: w, h: h, color: theme:windowBg);
		if({ hasContent }, {
			content:applyTheme(theme: theme);
			content:setScale(scale: scale);
			content:measure(c: Constraints(minW: w, maxW: w, minH: h, maxH: h));
			content:arrange(bounds: Rect(x: 0, y: 0, width: w, height: h));
			content:paint(ctx: ctx);
		}, {
			local Function is cb: onPaint;
			cb(ctx, w, h, theme, scale);
		});
		win:present(canvas: canvas);
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
		if({ hasContent }, {
			content:bindDirty(cb: local Function(){ :isDirty: true; });
		});
		canvas: SuitCanvas(width: win:width(), height: win:height());
		isShown: true;
		:paintDialog();
	}

	Function is closeWindow(){
		if({ !isShown }, { return; });
		isShown: false;
		canvas:dispose();
		win:close();
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
			:closeWindow();
			open:emit(value: false);
			return;
		});

		local Int is key: win:nextKey();
		while({ key != 0 }, {
			if({ key == 27 }, {
				:closeWindow();
				open:emit(value: false);
				return;
			});
			key: win:nextKey();
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
