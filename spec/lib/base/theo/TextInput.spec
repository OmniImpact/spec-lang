#! Package base:theo
#! Single-line focusable text input widget.

Class of Widget is TextInput{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [Widget, FocusTarget, KeyEvent, MouseEvent, TheoColor, TheoBuffer, TheoRenderer]],
		['base', 'sys', as Conditional()]
	];

	String is text: '';
	String is placeholder: '';
	Int is cursor: 0;
	FocusTarget is focusTarget: FocusTarget();
	TheoColor is fg: TheoColor:none();
	TheoColor is placeholderFg: TheoColor:none();
	Function is onChange: local Function(String is _s){};
	Function is onSubmit: local Function(String is _s){};

	replace Function is init(
		String is value: '',
		String is placeholder: '',
		FocusTarget is focusTarget: FocusTarget(),
		Function is onChange: local Function(String is _s){},
		Function is onSubmit: local Function(String is _s){},
		TheoColor is fg: TheoColor:none(),
		TheoColor is placeholderFg: TheoColor:none()
	){
		:text: value;
		:placeholder: placeholder;
		:cursor: value:length();
		:focusTarget: focusTarget;
		:onChange: onChange;
		:onSubmit: onSubmit;
		:fg: fg;
		:placeholderFg: placeholderFg;
	}

	Function is bindOnChange(Function is cb){
		:onChange: cb;
	}

	Function is bindOnSubmit(Function is cb){
		:onSubmit: cb;
	}

	Function is setText(String is value){
		:text: value;
		:cursor: value:length();
		invalidate();
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		return 1;
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		local TheoColor is effFg: if({ fg:isSet() }, { fg }, { activeTheme:titleColor });
		local TheoColor is effPlaceholderFg: if({ placeholderFg:isSet() }, { placeholderFg }, { activeTheme:mutedColor });
		if({ text:length() == 0 && placeholder:length() > 0 }, {
			buf:drawText(x: boxX, y: boxY, text: placeholder, fg: effPlaceholderFg);
		}, {
			buf:drawText(x: boxX, y: boxY, text: text, fg: effFg);
		});
		if({ focusTarget:focused }, {
			local Int is cx: cursor;
			if({ cx >= boxW }, { cx: boxW - 1; });
			renderer:setCursor(visible: true, x: boxX + cx, y: boxY);
		});
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ event:isLeftPress() && containsPoint(x: event:x, y: event:y) }, {
			focusTarget:requestFocus();
			local Int is targetCol: event:x - boxX;
			if({ targetCol < 0 }, { targetCol: 0; });
			if({ targetCol > text:length() }, { targetCol: text:length(); });
			:cursor: targetCol;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !focusTarget:focused }, { return false; });
		if({ event:isEnter() }, {
			onSubmit(text);
			return true;
		});
		if({ event:isLeft() }, {
			if({ cursor > 0 }, { :cursor: cursor - 1; invalidate(); });
			return true;
		});
		if({ event:isRight() }, {
			if({ cursor < text:length() }, { :cursor: cursor + 1; invalidate(); });
			return true;
		});
		if({ event:isHome() }, {
			:cursor: 0;
			invalidate();
			return true;
		});
		if({ event:isEnd() }, {
			:cursor: text:length();
			invalidate();
			return true;
		});
		if({ event:isBackspace() }, {
			if({ cursor > 0 }, {
				local String is left: text:substring(start: 0, end: cursor - 1);
				local String is right: text:substring(start: cursor, end: text:length());
				:text: "{{left}}{{right}}";
				:cursor: cursor - 1;
				onChange(text);
				invalidate();
			});
			return true;
		});
		if({ event:isDelete() }, {
			if({ cursor < text:length() }, {
				local String is left: text:substring(start: 0, end: cursor);
				local String is right: text:substring(start: cursor + 1, end: text:length());
				:text: "{{left}}{{right}}";
				onChange(text);
				invalidate();
			});
			return true;
		});
		if({ event:isChar() && !event:ctrl && !event:alt }, {
			local String is left: text:substring(start: 0, end: cursor);
			local String is right: text:substring(start: cursor, end: text:length());
			:text: "{{left}}{{event:key}}{{right}}";
			:cursor: cursor + event:key:length();
			onChange(text);
			invalidate();
			return true;
		});
		return false;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		targets:add(item: focusTarget);
		owners:add(item: :);
	}
}
