#! Package base:scrap
#! Single-line editable text input widget derived from [Theme] and participating in Sew layout.

Class of SewNode is TextInput{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', DrawContext]
	];

	String is text: '';
	String is placeholder: '';
	String is suffix: '';
	Boolean is focused: false;
	Boolean is hovered: false;
	Int is cursorPos: 0;
	Int is scrollX: 0;
	Float is minWidthPt: 0.0;
	Float is heightPt: 0.0;
	Boolean is expand: false;
	Function is onChange: local Function(String is _next){};
	Function is onSubmit: local Function(String is _val){};
	Function is onUp: local Function(){};
	Function is onDown: local Function(){};

	replace Function is init(
		String is text: '',
		String is placeholder: '',
		String is suffix: '',
		Boolean is focused: false,
		Float is minWidthPt: 0.0,
		Float is heightPt: 0.0,
		Boolean is expand: false,
		Function is onChange: local Function(String is _next){},
		Function is onSubmit: local Function(String is _val){},
		Function is onUp: local Function(){},
		Function is onDown: local Function(){},
		String is tooltip: ''
	){
		:text: text;
		:placeholder: placeholder;
		:suffix: suffix;
		:focused: focused;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:expand: expand;
		:onChange: onChange;
		:onSubmit: onSubmit;
		:onUp: onUp;
		:onDown: onDown;
		:hovered: false;
		:tooltip: tooltip;
	}

	local Function of String is stripSuffix(String is s){
		if({ suffix == '' }, { return s; });
		local Int is sl: s:length();
		local Int is fl: suffix:length();
		if({ sl >= fl && s:substring(start: sl - fl, end: sl) == suffix }, {
			return s:substring(start: 0, end: sl - fl);
		});
		return s;
	}

	local Function of String is ensureSuffix(String is s){
		if({ suffix == '' || s == '' }, { return s; });
		local Int is sl: s:length();
		local Int is fl: suffix:length();
		if({ sl >= fl && s:substring(start: sl - fl, end: sl) == suffix }, {
			return s;
		});
		return s . suffix;
	}

	Function is setText(String is next){
		local String is val: if({ focused }, { :stripSuffix(s: next) }, { next });
		if({ text != val }, {
			:text: val;
			if({ cursorPos > text:length() }, { :cursorPos: text:length(); });
			invalidate();
		});
	}

	replace Function of Boolean is canFocus(){
		return true;
	}

	replace Function of Boolean is isFocused(){
		return focused;
	}

	replace Function is setFocused(Boolean is next){
		if({ focused != next }, {
			:focused: next;
			if({ next }, {
				:text: :stripSuffix(s: text);
				:cursorPos: text:length();
			}, {
				local Function is scb: onSubmit;
				scb(text);
				:text: :ensureSuffix(s: text);
				:cursorPos: 0;
				:scrollX: 0;
			});
			invalidate();
		});
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 15.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Boolean is contains(Int is x, Int is y){
		local Rect is b: bounds();
		return x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is minW: activeScale:px(pt: if({ minWidthPt > 0.0 }, { minWidthPt }, { activeTheme:inputMinWidthPt }));
		local Int is h: activeScale:px(pt: if({ heightPt > 0.0 }, { heightPt }, { activeTheme:inputHeightPt }));
		local Int is fpx: :fontPx();
		local Int is tw: DrawContext:measureWidth(text: text, pixelHeight: fpx) + activeScale:px(pt: activeTheme:paddingPt * 2.5);
		local Int is natW: if({ tw > minW }, { tw }, { minW });
		local Int is w: if({ expand && c:maxW > natW }, { c:maxW }, { natW });
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:borderPx(scaleFactor: activeScale:factor);
		local Int is border: if({ focused }, { activeTheme:textAccent }, {
			if({ hovered }, { activeTheme:textMuted }, { activeTheme:buttonBorder })
		});
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:windowBg);
		if({ bw > 0 }, {
			ctx:strokeRect(x: b:x, y: b:y, w: b:width, h: b:height, color: border, thickness: bw);
		});

		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		local Int is fpx: :fontPx();
		local Int is th: DrawContext:measureHeight(pixelHeight: fpx);
		local Int is clipW: b:width - padX * 2;
		if({ clipW > 4 }, {
			ctx:setClip(x: b:x + padX, y: b:y, w: clipW, h: b:height);
			local Int is textY: b:y + (b:height - th) / 2;
			if({ text == '' && !focused && placeholder != '' }, {
				ctx:drawText(x: b:x + padX, y: textY, text: placeholder, color: activeTheme:textMuted, pixelHeight: fpx);
			}, {
				local Int is cPos: cursorPos;
				if({ cPos < 0 }, { cPos: 0; });
				if({ cPos > text:length() }, { cPos: text:length(); });
				local Int is caretOff: if({ focused && cPos > 0 }, {
					ctx:measureTextWidth(text: text:substring(start: 0, end: cPos), pixelHeight: fpx)
				}, { 0 });
				local Int is caretW: activeScale:px(pt: 1.0);
				if({ caretW < 1 }, { caretW: 1; });
				if({ focused }, {
					if({ caretOff - scrollX > clipW - caretW }, {
						:scrollX: caretOff - (clipW - caretW);
					});
					if({ caretOff - scrollX < 0 }, {
						:scrollX: caretOff;
					});
					if({ scrollX < 0 }, { :scrollX: 0; });
				}, {
					:scrollX: 0;
				});
				ctx:drawText(x: b:x + padX - scrollX, y: textY, text: text, color: activeTheme:textPrimary, pixelHeight: fpx);
				if({ focused }, {
					ctx:fillRect(x: b:x + padX + caretOff - scrollX, y: textY, w: caretW, h: th, color: activeTheme:textPrimary);
				});
			});
			ctx:clearClip();
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is h: :contains(x: x, y: y);
		if({ h != hovered }, {
			:hovered: h;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function is clearHover(){
		if({ hovered }, {
			:hovered: false;
			invalidate();
		});
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ :contains(x: x, y: y) }, { return CursorShape:TEXT; });
		return CursorShape:DEFAULT;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods){
		local Boolean is inside: :contains(x: x, y: y);
		if({ inside != focused }, {
			:setFocused(next: inside);
		});
		if({ inside }, {
			local Rect is b: bounds();
			local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
			local Int is fpx: :fontPx();
			local Int is relX: (x - (b:x + padX)) + scrollX;
			local Int is best: 0;
			if({ relX > 0 && text:length() > 0 }, {
				local Int is bestDist: relX;
				local Int is i: 1;
				while({ i <= text:length() }, {
					local Int is w: DrawContext:measureWidth(text: text:substring(start: 0, end: i), pixelHeight: fpx);
					local Int is d: if({ w >= relX }, { w - relX }, { relX - w });
					if({ d <= bestDist }, {
						bestDist: d;
						best: i;
					});
					i: i + 1;
				});
			});
			if({ best != cursorPos }, {
				:cursorPos: best;
				invalidate();
			});
			return true;
		});
		return false;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ !focused }, { return false; });
		if({ key == 1001 }, {
			local Function is ucb: onUp;
			ucb();
			return true;
		});
		if({ key == 1002 }, {
			local Function is dcb: onDown;
			dcb();
			return true;
		});
		if({ key == 1003 }, {
			if({ cursorPos > 0 }, {
				:cursorPos: cursorPos - 1;
				invalidate();
			});
			return true;
		});
		if({ key == 1004 }, {
			if({ cursorPos < text:length() }, {
				:cursorPos: cursorPos + 1;
				invalidate();
			});
			return true;
		});
		if({ key == 1005 }, {
			if({ cursorPos != 0 }, {
				:cursorPos: 0;
				invalidate();
			});
			return true;
		});
		if({ key == 1006 }, {
			if({ cursorPos != text:length() }, {
				:cursorPos: text:length();
				invalidate();
			});
			return true;
		});
		if({ key == 8 }, {
			if({ cursorPos > 0 }, {
				:text: text:substring(start: 0, end: cursorPos - 1) . text:substring(start: cursorPos, end: text:length());
				:cursorPos: cursorPos - 1;
				local Function is cb: onChange;
				cb(text);
				invalidate();
			});
			return true;
		});
		if({ key == 127 }, {
			if({ cursorPos < text:length() }, {
				:text: text:substring(start: 0, end: cursorPos) . text:substring(start: cursorPos + 1, end: text:length());
				local Function is cb: onChange;
				cb(text);
				invalidate();
			});
			return true;
		});
		if({ key == 10 || key == 13 }, {
			local Function is scb: onSubmit;
			scb(text);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		if({ !focused || ch == '' }, { return false; });
		local Int is cPos: cursorPos;
		if({ cPos < 0 }, { cPos: 0; });
		if({ cPos > text:length() }, { cPos: text:length(); });
		:text: text:substring(start: 0, end: cPos) . ch . text:substring(start: cPos, end: text:length());
		:cursorPos: cPos + ch:length();
		local Function is cb: onChange;
		cb(text);
		invalidate();
		return true;
	}
}