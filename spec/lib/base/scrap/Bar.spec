#! Package base:scrap
#! Horizontal bar widget supporting top/bottom borders and left/center/right-aligned reactive text.

Class of SewNode is Bar{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'signal', TextEmitter],
		['base', 'signal', TextCollector],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	Float is heightPt: 26.0;
	String is borderSide: 'bottom';
	TextEmitter is leftText: TextEmitter(initial: '');
	TextEmitter is centerText: TextEmitter(initial: '');
	TextEmitter is rightText: TextEmitter(initial: '');

	replace Function is init(
		Float is heightPt: 26.0,
		String is borderSide: 'bottom',
		TextEmitter is leftText: TextEmitter(initial: ''),
		TextEmitter is centerText: TextEmitter(initial: ''),
		TextEmitter is rightText: TextEmitter(initial: ''),
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0)
	){
		:heightPt: heightPt;
		:borderSide: borderSide;
		:leftText: leftText;
		:centerText: centerText;
		:rightText: rightText;
		:theme: theme;
		:scale: scale;
		:bindTextEmitters();
	}

	local Function is bindTextEmitters(){
		signalBag:clear();
		signalBag:track(
			slot: 'left',
			emitter: leftText,
			collector: TextCollector(onEmit: local Function(String is _v){ invalidate(); })
		);
		signalBag:track(
			slot: 'center',
			emitter: centerText,
			collector: TextCollector(onEmit: local Function(String is _v){ invalidate(); })
		);
		signalBag:track(
			slot: 'right',
			emitter: rightText,
			collector: TextCollector(onEmit: local Function(String is _v){ invalidate(); })
		);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		:theme: theme;
	}

	Function is setScale(Scale is scale){
		:scale: scale;
	}

	Function is setHeightPt(Float is heightPt){
		:heightPt: heightPt;
	}

	local Function of Int is textScale(){
		local Int is ts: scale:px(pt: 2.0);
		return if({ ts < 1 }, { 1 }, { ts });
	}

	replace Function of Size is measure(Constraints is c){
		local Int is h: scale:px(pt: heightPt);
		desiredSize: Size(width: c:clampW(w: c:maxW), height: c:clampH(h: h));
		return desiredSize;
	}

	Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: theme:toolbarBg);
		local Int is borderH: if({ scale:px(pt: 1.0) < 1 }, { 1 }, { scale:px(pt: 1.0) });
		if({ borderSide == 'top' }, {
			ctx:fillRect(x: b:x, y: b:y, w: b:width, h: borderH, color: theme:toolbarBorder);
		}, {
			if({ borderSide == 'bottom' }, {
				ctx:fillRect(x: b:x, y: b:y + b:height - borderH, w: b:width, h: borderH, color: theme:toolbarBorder);
			});
		});

		local Int is ts: :textScale();
		local Int is th: ctx:measureTextHeight(scale: ts);
		local Int is ty: b:y + (b:height - th) / 2;
		local Int is padX: scale:px(pt: 10.0);

		local String is lStr: leftText:current();
		if({ lStr != '' }, {
			ctx:drawText(x: b:x + padX, y: ty, text: lStr, color: theme:textPrimary, scale: ts);
		});

		local String is cStr: centerText:current();
		if({ cStr != '' }, {
			local Int is cw: ctx:measureTextWidth(text: cStr, scale: ts);
			ctx:drawText(x: b:x + (b:width - cw) / 2, y: ty, text: cStr, color: theme:textPrimary, scale: ts);
		});

		local String is rStr: rightText:current();
		if({ rStr != '' }, {
			local Int is rw: ctx:measureTextWidth(text: rStr, scale: ts);
			ctx:drawText(x: b:x + b:width - padX - rw, y: ty, text: rStr, color: theme:textPrimary, scale: ts);
		});
	}

	Function is dispose(){
		signalBag:clear();
	}
}
