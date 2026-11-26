#! Package base:scrap
#! Generic non-blocking secondary dialog window host bound to a `BoolEmitter`.

Class is Dialog{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'signal', BoolEmitter],
		['base', 'signal', SignalBag],
		['base', 'suit', SuitWindow],
		['base', 'suit', SuitCanvas],
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
	Function is onPaint: local Function(DrawContext is ctx, Int is w, Int is h, Theme is theme, Scale is scale){};

	SuitWindow is win: SuitWindow();
	SuitCanvas is canvas: SuitCanvas(width: 1, height: 1);
	Boolean is isShown: false;
	SignalBag is signalBag: SignalBag();

	replace Function is init(
		String is title: 'Dialog',
		BoolEmitter is open: BoolEmitter(initial: false),
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0),
		Float is widthPt: 480.0,
		Float is heightPt: 180.0,
		Function is onPaint: local Function(DrawContext is ctx, Int is w, Int is h, Theme is theme, Scale is scale){}
	){
		:title: title;
		:open: open;
		:theme: theme;
		:scale: scale;
		:widthPt: widthPt;
		:heightPt: heightPt;
		:onPaint: onPaint;
		isShown: false;
	}

	Function is applyTheme(Theme is theme){
		:theme: theme;
	}

	Function is setScale(Scale is scale){
		:scale: scale;
	}

	local Function is paintDialog(){
		local Int is w: win:width();
		local Int is h: win:height();
		if({ w <= 0 || h <= 0 }, { return; });
		canvas:resize(width: w, height: h);
		local DrawContext is ctx: DrawContext(canvas: canvas);
		ctx:fillRect(x: 0, y: 0, w: w, h: h, color: theme:windowBg);
		local Function is cb: onPaint;
		cb(ctx, w, h, theme, scale);
		win:present(canvas: canvas);
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
	}

	Function is dispose(){
		signalBag:clear();
		:closeWindow();
	}
}
