#! Package base:theo
#! Focusable, scrollable multi-line text editing widget.

Class of Widget is TextArea{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', Widget],
		['base', 'theo', FocusTarget],
		['base', 'theo', KeyEvent],
		['base', 'theo', TheoColor],
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'theo', TheoCallback],
		['base', 'signal', TextEmitter],
		['base', 'signal', TextCollector],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Array of String is lines: [''];
	Int is cursorRow: 0;
	Int is cursorCol: 0;
	Int is scrollY: 0;
	FocusTarget is focusTarget: FocusTarget();
	Array of TheoCallback is changeHandlers: [];
	Array of TextEmitter is boundEmitters: [];
	Array of TextCollector is boundCollectors: [];
	Boolean is suppressSync: false;

	replace Function is init(Any is value: '', FocusTarget is focusTarget: FocusTarget(), Function is onChange: local Function(String is _s){}){
		:focusTarget: focusTarget;
		:changeHandlers: [TheoCallback(fn: onChange)];
		:boundEmitters: [];
		:boundCollectors: [];
		initValue(value: value);
	}

	local Function is initValue(Any is value){
		if({ value:typeName() == 'TextEmitter' }, {
			local TextEmitter is em: value as TextEmitter;
			:boundEmitters: [em];
			setText(text: em:current());
			local TextCollector is col: em:collect(onEmit: local Function(String is next){
				if({ !suppressSync }, {
					setText(text: next);
					invalidate();
				});
			});
			:boundCollectors: [col];
		}, {
			setText(text: value as String);
		});
	}

	Function is setText(String is text){
		if({ text == '' }, {
			:lines: [''];
		}, {
			:lines: text:split(delimiter: "\n");
			if({ :lines:length() == 0 }, {
				:lines: [''];
			});
		});
		if({ cursorRow >= :lines:length() }, { :cursorRow: :lines:length() - 1; });
		local Int is rowLen: :lines:get(index: cursorRow):length();
		if({ cursorCol > rowLen }, { :cursorCol: rowLen; });
	}

	Function of String is getText(){
		return lines:join(sep: "\n");
	}

	local Function is notifyChanged(){
		:suppressSync: true;
		local String is full: getText();
		if({ changeHandlers:length() > 0 }, {
			changeHandlers:get(index: 0):callStr(s: full);
		});
		:suppressSync: false;
		invalidate();
	}

	local Function is clampCursor(){
		if({ cursorRow < 0 }, { :cursorRow: 0; });
		if({ cursorRow >= lines:length() }, { :cursorRow: lines:length() - 1; });
		local Int is len: lines:get(index: cursorRow):length();
		if({ cursorCol < 0 }, { :cursorCol: 0; });
		if({ cursorCol > len }, { :cursorCol: len; });
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		return maxH;
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		if({ cursorRow < scrollY }, { :scrollY: cursorRow; });
		if({ cursorRow >= scrollY + boxH }, { :scrollY: cursorRow - boxH + 1; });
		if({ scrollY < 0 }, { :scrollY: 0; });

		local Int is r: 0;
		while({ r < boxH && scrollY + r < lines:length() }, {
			local String is ln: lines:get(index: scrollY + r):replaceAll(target: "\t", replacement: '    ');
			buf:drawText(x: boxX, y: boxY + r, text: ln);
			r: r + 1;
		});
		if({ focusTarget:focused }, {
			local String is curLine: lines:get(index: cursorRow);
			local Int is visCol: 0;
			local Int is ci: 0;
			while({ ci < cursorCol && ci < curLine:length() }, {
				if({ curLine:charAt(index: ci, default: '') == "\t" }, {
					visCol: visCol + 4;
				}, {
					visCol: visCol + 1;
				});
				ci: ci + 1;
			});
			if({ visCol >= boxW }, { visCol: boxW - 1; });
			renderer:setCursor(visible: true, x: boxX + visCol, y: boxY + (cursorRow - scrollY));
		});
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !focusTarget:focused }, { return false; });
		if({ event:isUp() }, {
			if({ cursorRow > 0 }, { :cursorRow: cursorRow - 1; clampCursor(); invalidate(); });
			return true;
		});
		if({ event:isDown() }, {
			if({ cursorRow + 1 < lines:length() }, { :cursorRow: cursorRow + 1; clampCursor(); invalidate(); });
			return true;
		});
		if({ event:isLeft() }, {
			if({ cursorCol > 0 }, {
				:cursorCol: cursorCol - 1;
			}, {
				if({ cursorRow > 0 }, {
					:cursorRow: cursorRow - 1;
					:cursorCol: lines:get(index: cursorRow):length();
				});
			});
			invalidate();
			return true;
		});
		if({ event:isRight() }, {
			local Int is len: lines:get(index: cursorRow):length();
			if({ cursorCol < len }, {
				:cursorCol: cursorCol + 1;
			}, {
				if({ cursorRow + 1 < lines:length() }, {
					:cursorRow: cursorRow + 1;
					:cursorCol: 0;
				});
			});
			invalidate();
			return true;
		});
		if({ event:isHome() }, {
			:cursorCol: 0;
			invalidate();
			return true;
		});
		if({ event:isEnd() }, {
			:cursorCol: lines:get(index: cursorRow):length();
			invalidate();
			return true;
		});
		if({ event:isEnter() }, {
			local String is cur: lines:get(index: cursorRow);
			local String is left: cur:substring(start: 0, end: cursorCol);
			local String is right: cur:substring(start: cursorCol, end: cur:length());
			lines:set(index: cursorRow, value: left);
			local Array of String is nextLines: [];
			local Int is i: 0;
			while({ i < lines:length() }, {
				nextLines:add(item: lines:get(index: i));
				if({ i == cursorRow }, {
					nextLines:add(item: right);
				});
				i: i + 1;
			});
			:lines: nextLines;
			:cursorRow: cursorRow + 1;
			:cursorCol: 0;
			notifyChanged();
			return true;
		});
		if({ event:isBackspace() }, {
			if({ cursorCol > 0 }, {
				local String is cur: lines:get(index: cursorRow);
				local String is left: cur:substring(start: 0, end: cursorCol - 1);
				local String is right: cur:substring(start: cursorCol, end: cur:length());
				lines:set(index: cursorRow, value: "{{left}}{{right}}");
				:cursorCol: cursorCol - 1;
				notifyChanged();
			}, {
				if({ cursorRow > 0 }, {
					local String is prev: lines:get(index: cursorRow - 1);
					local String is cur: lines:get(index: cursorRow);
					local Int is joinCol: prev:length();
					lines:set(index: cursorRow - 1, value: "{{prev}}{{cur}}");
					lines:removeAt(index: cursorRow);
					:cursorRow: cursorRow - 1;
					:cursorCol: joinCol;
					notifyChanged();
				});
			});
			return true;
		});
		if({ event:isDelete() }, {
			local String is cur: lines:get(index: cursorRow);
			if({ cursorCol < cur:length() }, {
				local String is left: cur:substring(start: 0, end: cursorCol);
				local String is right: cur:substring(start: cursorCol + 1, end: cur:length());
				lines:set(index: cursorRow, value: "{{left}}{{right}}");
				notifyChanged();
			}, {
				if({ cursorRow + 1 < lines:length() }, {
					local String is nextLn: lines:get(index: cursorRow + 1);
					lines:set(index: cursorRow, value: "{{cur}}{{nextLn}}");
					lines:removeAt(index: cursorRow + 1);
					notifyChanged();
				});
			});
			return true;
		});
		if({ event:isTab() }, {
			local String is cur: lines:get(index: cursorRow);
			local String is left: cur:substring(start: 0, end: cursorCol);
			local String is right: cur:substring(start: cursorCol, end: cur:length());
			lines:set(index: cursorRow, value: "{{left}}\t{{right}}");
			:cursorCol: cursorCol + 1;
			notifyChanged();
			return true;
		});
		if({ event:isChar() && !event:ctrl && !event:alt }, {
			local String is cur: lines:get(index: cursorRow);
			local String is left: cur:substring(start: 0, end: cursorCol);
			local String is right: cur:substring(start: cursorCol, end: cur:length());
			lines:set(index: cursorRow, value: "{{left}}{{event:key}}{{right}}");
			:cursorCol: cursorCol + event:key:length();
			notifyChanged();
			return true;
		});
		return false;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		targets:add(item: focusTarget);
		owners:add(item: :);
	}

	replace Function is dispose(){
		if({ boundEmitters:length() > 0 && boundCollectors:length() > 0 }, {
			boundEmitters:get(index: 0):detach(collector: boundCollectors:get(index: 0));
			:boundEmitters: [];
			:boundCollectors: [];
		});
	}
}
