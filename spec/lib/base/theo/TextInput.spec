#! Package base:theo
#! Single-line focusable text input widget.

Class of Widget is TextInput{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', Widget],
		['base', 'theo', FocusTarget],
		['base', 'theo', KeyEvent],
		['base', 'theo', TheoColor],
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'theo', TheoCallback],
		['base', 'sys', as Conditional()]
	];

	String is text: '';
	String is placeholder: '';
	Int is cursor: 0;
	FocusTarget is focusTarget: FocusTarget();
	TheoColor is fg: TheoColor:ansi(code: 255);
	TheoColor is placeholderFg: TheoColor:ansi(code: 245);
	Array of TheoCallback is changeHooks: [];
	Array of TheoCallback is submitHooks: [];

	replace Function is init(
		String is value: '',
		String is placeholder: '',
		FocusTarget is focusTarget: FocusTarget()
	){
		:text: value;
		:placeholder: placeholder;
		:cursor: value:length();
		:focusTarget: focusTarget;
		:changeHooks: [];
		:submitHooks: [];
	}

	Function is bindOnChange(Function is cb){
		:changeHooks: [TheoCallback(fn: cb)];
	}

	Function is bindOnSubmit(Function is cb){
		:submitHooks: [TheoCallback(fn: cb)];
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
		if({ text:length() == 0 && placeholder:length() > 0 }, {
			buf:drawText(x: boxX, y: boxY, text: placeholder, fg: placeholderFg);
		}, {
			buf:drawText(x: boxX, y: boxY, text: text, fg: fg);
		});
		if({ focusTarget:focused }, {
			local Int is cx: cursor;
			if({ cx >= boxW }, { cx: boxW - 1; });
			renderer:setCursor(visible: true, x: boxX + cx, y: boxY);
		});
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !focusTarget:focused }, { return false; });
		if({ event:isEnter() }, {
			if({ submitHooks:length() > 0 }, {
				submitHooks:get(index: 0):callStr(s: text);
			});
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
				if({ changeHooks:length() > 0 }, {
					changeHooks:get(index: 0):callStr(s: text);
				});
				invalidate();
			});
			return true;
		});
		if({ event:isDelete() }, {
			if({ cursor < text:length() }, {
				local String is left: text:substring(start: 0, end: cursor);
				local String is right: text:substring(start: cursor + 1, end: text:length());
				:text: "{{left}}{{right}}";
				if({ changeHooks:length() > 0 }, {
					changeHooks:get(index: 0):callStr(s: text);
				});
				invalidate();
			});
			return true;
		});
		if({ event:isChar() && !event:ctrl && !event:alt }, {
			local String is left: text:substring(start: 0, end: cursor);
			local String is right: text:substring(start: cursor, end: text:length());
			:text: "{{left}}{{event:key}}{{right}}";
			:cursor: cursor + event:key:length();
			if({ changeHooks:length() > 0 }, {
				changeHooks:get(index: 0):callStr(s: text);
			});
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
