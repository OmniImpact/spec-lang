#! Package base:scrap
#! Decorated single-line text input with `-` / `+` stepper buttons on each side.

Class of SewNode is DecoratedTextInput{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', Row],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', TextInput]
	];

	ScrapButton is leftBtn: ScrapButton();
	TextInput is input: TextInput();
	ScrapButton is rightBtn: ScrapButton();
	Row is row: Row();

	replace Function is init(
		String is text: '',
		String is placeholder: '',
		String is leftLabel: '-',
		String is rightLabel: '+',
		Function is onLeftClick: local Function(){},
		Function is onRightClick: local Function(){},
		Function is onChange: local Function(String is _next){},
		Function is onSubmit: local Function(String is _val){},
		Float is inputMinWidthPt: 52.0,
		String is suffix: '',
		String is tooltip: ''
	){
		:tooltip: tooltip;
		:leftBtn: ScrapButton(
			label: leftLabel,
			minWidthPt: 24.0,
			padXPt: 4.0,
			onClick: onLeftClick,
			tooltip: tooltip
		);
		:input: TextInput(
			text: text,
			placeholder: placeholder,
			suffix: suffix,
			minWidthPt: inputMinWidthPt,
			onChange: onChange,
			onSubmit: onSubmit,
			onUp: onRightClick,
			onDown: onLeftClick,
			tooltip: tooltip
		);
		:rightBtn: ScrapButton(
			label: rightLabel,
			minWidthPt: 24.0,
			padXPt: 4.0,
			onClick: onRightClick,
			tooltip: tooltip
		);
		:row: Row(
			children: Array([leftBtn, input, rightBtn]),
			flexFlags: Array([false, false, false])
		);
	}

	Function is setText(String is next){
		input:setText(next: next);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		row:gapPt: theme:paddingTinyPt;
		row:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		row:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		row:bindDirty(cb: cb);
	}

	replace Function of Size is measure(Constraints is c){
		desiredSize: row:measure(c: c);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		row:arrange(bounds: bounds);
	}

	replace Function is paint(DrawContext is ctx){
		row:paint(ctx: ctx);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return row:onPointerMove(x: x, y: y);
	}

	replace Function is clearHover(){
		row:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return row:onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		return row:onKey(key: key, mods: mods);
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		return row:onText(ch: ch, mods: mods);
	}

	replace Function of Boolean is tick(Int is nowMs){
		return row:tick(nowMs: nowMs);
	}

	replace Function is collectFocusables(Array of SewNode is out){
		row:collectFocusables(out: out);
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, { return ''; });
		local String is tip: row:tooltipAt(x: x, y: y);
		if({ tip != '' }, { return tip; });
		return tooltip;
	}
}