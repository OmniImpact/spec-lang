#! Package base:theo
#! Focusable, scrollable multi-line text editing widget.

Class of Widget is TextArea{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [Widget, FocusTarget, KeyEvent, MouseEvent, TheoColor, TheoBuffer, TheoRenderer]],
		['base', 'signal', [TextEmitter, TextCollector]],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	Array of String is lines: [''];
	Int is cursorRow: 0;
	Int is cursorCol: 0;
	Int is scrollX: 0;
	Int is scrollY: 0;
	Boolean is followCursor: true;
	FocusTarget is focusTarget: FocusTarget();
	Function is onChange: local Function(String is _s){};
	Array of TextEmitter is boundEmitters: [];
	Array of TextCollector is boundCollectors: [];
	Boolean is suppressSync: false;

	replace Function is init(String is value: '', FocusTarget is focusTarget: FocusTarget(), Function is onChange: local Function(String is _s){}){
		:focusTarget: focusTarget;
		:onChange: onChange;
		:boundEmitters: [];
		:boundCollectors: [];
		setText(text: value);
	}

	Function is bindValue(TextEmitter is value){
		if({ boundEmitters:length() > 0 && boundCollectors:length() > 0 }, {
			boundEmitters:get(index: 0):detach(collector: boundCollectors:get(index: 0));
		});
		:boundEmitters: [value];
		setText(text: value:current());
		local TextCollector is col: value:collect(onEmit: local Function(String is next){
			if({ !suppressSync }, {
				setText(text: next);
				invalidate();
			});
		});
		:boundCollectors: [col];
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
		onLinesChanged();
	}

	Function is onLinesChanged(){
		return;
	}

	Function is paintLine(TheoBuffer is buf, Int is y, Int is lineIndex, String is rawLine, Int is scrollX){
		local String is ln: rawLine:replaceAll(target: "\t", replacement: '    ');
		if({ scrollX > 0 }, {
			if({ scrollX < ln:length() }, {
				ln: ln:substring(start: scrollX, end: ln:length());
			}, {
				ln: '';
			});
		});
		buf:drawText(x: boxX, y: y, text: ln);
	}

	Function of String is getText(){
		return lines:join(sep: "\n");
	}

	local Function is notifyChanged(){
		onLinesChanged();
		:suppressSync: true;
		onChange(getText());
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

	local Function of Int is visualCol(String is ln, Int is col){
		local Int is vis: 0;
		local Int is i: 0;
		while({ i < col && i < ln:length() }, {
			if({ ln:charAt(index: i, default: '') == "\t" }, {
				vis: vis + 4;
			}, {
				vis: vis + 1;
			});
			i: i + 1;
		});
		return vis;
	}

	replace Function of Int is scrollOffsetY(){
		return scrollY;
	}

	replace Function of Int is scrollContentH(){
		return lines:length();
	}

	replace Function of Int is scrollViewportH(){
		return boxH;
	}

	replace Function of Int is scrollOffsetX(){
		return scrollX;
	}

	replace Function of Int is scrollContentW(){
		local Int is maxW: 0;
		local Int is i: 0;
		while({ i < lines:length() }, {
			local String is ln: lines:get(index: i);
			local Int is w: visualCol(ln: ln, col: ln:length());
			if({ w > maxW }, { maxW: w; });
			i: i + 1;
		});
		return maxW;
	}

	replace Function of Int is scrollViewportW(){
		return boxW;
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		if({ followCursor }, {
			if({ cursorRow < scrollY }, { :scrollY: cursorRow; });
			if({ cursorRow >= scrollY + boxH }, { :scrollY: cursorRow - boxH + 1; });
		});
		if({ scrollY < 0 }, { :scrollY: 0; });

		local Int is visCol: 0;
		if({ focusTarget:focused }, {
			local String is curLine: lines:get(index: cursorRow);
			visCol: visualCol(ln: curLine, col: cursorCol);
			if({ followCursor }, {
				if({ visCol < scrollX }, { :scrollX: visCol; });
				if({ visCol >= scrollX + boxW }, { :scrollX: visCol - boxW + 1; });
			});
			if({ scrollX < 0 }, { :scrollX: 0; });
		});

		local Int is r: 0;
		while({ r < boxH && scrollY + r < lines:length() }, {
			paintLine(buf: buf, y: boxY + r, lineIndex: scrollY + r, rawLine: lines:get(index: scrollY + r), scrollX: scrollX);
			r: r + 1;
		});
		if({ focusTarget:focused }, {
			local Int is drawRow: cursorRow - scrollY;
			local Int is drawCol: visCol - scrollX;
			if({ drawRow >= 0 && drawRow < boxH && drawCol >= 0 && drawCol < boxW }, {
				renderer:setCursor(visible: true, x: boxX + drawCol, y: boxY + drawRow, style: 5, color: '#ffffff');
			});
		});
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ !containsPoint(x: event:x, y: event:y) }, { return false; });
		if({ event:isWheelUp() }, {
			if({ scrollY > 0 }, {
				:scrollY: scrollY - 3;
				if({ scrollY < 0 }, { :scrollY: 0; });
				:followCursor: false;
				invalidate();
				return true;
			});
			return false;
		});
		if({ event:isWheelDown() }, {
			local Int is maxScroll: lines:length() - boxH;
			if({ maxScroll < 0 }, { maxScroll: 0; });
			if({ scrollY < maxScroll }, {
				:scrollY: scrollY + 3;
				if({ scrollY > maxScroll }, { :scrollY: maxScroll; });
				:followCursor: false;
				invalidate();
				return true;
			});
			return false;
		});
		if({ event:isLeftPress() }, {
			focusTarget:requestFocus();
			local Int is targetRow: scrollY + (event:y - boxY);
			if({ targetRow < 0 }, { targetRow: 0; });
			if({ targetRow >= lines:length() }, { targetRow: lines:length() - 1; });
			local Int is targetVis: scrollX + (event:x - boxX);
			if({ targetVis < 0 }, { targetVis: 0; });
			local String is ln: lines:get(index: targetRow);
			local Int is col: 0;
			local Int is vis: 0;
			local Boolean is done: false;
			while({ !done && col < ln:length() && vis < targetVis }, {
				local Int is step: if({ ln:charAt(index: col, default: '') == "\t" }, { 4 }, { 1 });
				if({ vis + step > targetVis }, {
					done: true;
				}, {
					vis: vis + step;
					col: col + 1;
				});
			});
			:cursorRow: targetRow;
			:cursorCol: col;
			:followCursor: true;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !focusTarget:focused }, { return false; });
		:followCursor: true;
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
