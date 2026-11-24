#! Package base:theo
#! Vertical container placing children one after another with optional [gap] and [Spacer] flex.

Class of Widget is Col{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'sys', [as Conditional(), as Loops()]],
		['base', 'math', as Math()]
	];

	Int is gap: 0;
	Boolean is arrowFocus: false;
	Boolean is scrollable: false;
	Int is padX: 0;
	Int is padY: 0;
	Int is scrollY: 0;
	Int is contentH: 0;
	Array of Widget is children: Array();

	replace Function is init(Int is gap: 0, Boolean is arrowFocus: false, Boolean is scrollable: false, Int is padX: 0, Int is padY: 0, Array of Widget is children: Array()){
		:gap: gap;
		:arrowFocus: arrowFocus;
		:scrollable: scrollable;
		:padX: padX;
		:padY: padY;
		:scrollY: 0;
		:contentH: 0;
		:children: children;
	}

	replace Function of Int is scrollOffsetY(){
		return scrollY;
	}

	replace Function of Int is scrollContentH(){
		return contentH;
	}

	replace Function of Int is scrollViewportH(){
		return boxH;
	}

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		children:each(action: local Function(Widget is ch){
			ch:applyTheme(theme: theme);
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		children:each(action: local Function(Widget is ch){
			ch:bindDirty(cb: cb);
		});
	}

	replace Function of Int is measureWidth(Int is maxW){
		local Int is best: 0;
		local Int is avail: maxW - (padX * 2);
		if({ avail < 0 }, { avail: 0; });
		local Int is i: 0;
		while({ i < children:length() }, {
			local Widget is ch: children:get(index: i);
			if({ ch:flexWeight() <= 0.0 }, {
				local Int is cw: ch:measureWidth(maxW: avail);
				if({ cw > best }, { best: cw; });
			});
			i: i + 1;
		});
		local Int is total: best + (padX * 2);
		if({ total > maxW }, { return maxW; });
		return total;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		local Int is count: children:length();
		if({ count == 0 }, { return padY * 2; });
		local Int is availW: maxW - (padX * 2);
		if({ availW < 0 }, { availW: 0; });
		local Int is total: (count - 1) * gap + (padY * 2);
		local Int is i: 0;
		while({ i < count }, {
			local Widget is ch: children:get(index: i);
			if({ ch:flexWeight() <= 0.0 }, {
				total: total + ch:measureHeight(maxW: availW, maxH: maxH);
			});
			i: i + 1;
		});
		if({ total > maxH }, { return maxH; });
		return total;
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		local Int is count: children:length();
		if({ count == 0 }, { return; });
		local Int is innerW: w - (padX * 2);
		if({ innerW < 0 }, { innerW: 0; });
		local Int is fixedTotal: (count - 1) * gap + (padY * 2);
		local Float is weightTotal: 0.0;
		local Int is i: 0;
		while({ i < count }, {
			local Widget is ch: children:get(index: i);
			local Float is fw: ch:flexWeight();
			if({ fw > 0.0 }, {
				weightTotal: weightTotal + fw;
			}, {
				fixedTotal: fixedTotal + ch:measureHeight(maxW: innerW, maxH: h);
			});
			i: i + 1;
		});
		local Int is rem: if({ h > fixedTotal }, { h - fixedTotal }, { 0 });
		:contentH: fixedTotal;
		if({ scrollable }, {
			local Int is maxScroll: contentH - h;
			if({ maxScroll < 0 }, { maxScroll: 0; });
			if({ scrollY > maxScroll }, { :scrollY: maxScroll; });
			if({ scrollY < 0 }, { :scrollY: 0; });
		}, {
			:scrollY: 0;
		});
		local Int is curY: if({ scrollable }, { y + padY - scrollY }, { y + padY });
		i: 0;
		while({ i < count }, {
			local Widget is ch: children:get(index: i);
			local Float is fw: ch:flexWeight();
			local Int is chH: 0;
			if({ fw > 0.0 }, {
				if({ weightTotal > 0.0 }, {
					chH: toInt(value: (toFloat(value: rem) * fw) / weightTotal);
				});
			}, {
				chH: ch:measureHeight(maxW: innerW, maxH: h);
			});
			ch:layout(x: x + padX, y: curY, w: innerW, h: chH);
			curY: curY + chH + gap;
			i: i + 1;
		});
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		children:each(action: local Function(Widget is ch){
			ch:paint(buf: buf, renderer: renderer);
		});
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		local Int is i: 0;
		while({ i < children:length() }, {
			if({ children:get(index: i):handleKey(event: event) }, {
				return true;
			});
			i: i + 1;
		});
		if({ arrowFocus && (event:isUp() || event:isDown()) }, {
			local Array of FocusTarget is fts: Array();
			local Array of Widget is fws: Array();
			collectFocus(targets: fts, owners: fws);
			local Int is n: fts:length();
			if({ n > 1 }, {
				local Int is cur: -1;
				local Int is fi: 0;
				while({ fi < n }, {
					if({ fts:get(index: fi):focused }, { cur: fi; });
					fi: fi + 1;
				});
				if({ cur >= 0 }, {
					local Int is next: if({ event:isUp() }, { (cur - 1 + n) % n }, { (cur + 1) % n });
					fts:get(index: next):requestFocus();
					return true;
				});
			});
		});
		if({ scrollable }, {
			local Int is maxScroll: contentH - boxH;
			if({ maxScroll < 0 }, { maxScroll: 0; });
			if({ event:isUp() && scrollY > 0 }, {
				:scrollY: scrollY - 1;
				invalidate();
				return true;
			});
			if({ event:isDown() && scrollY < maxScroll }, {
				:scrollY: scrollY + 1;
				invalidate();
				return true;
			});
			if({ event:isPageUp() && scrollY > 0 }, {
				local Int is nextY: scrollY - boxH;
				if({ nextY < 0 }, { nextY: 0; });
				:scrollY: nextY;
				invalidate();
				return true;
			});
			if({ event:isPageDown() && scrollY < maxScroll }, {
				local Int is nextY: scrollY + boxH;
				if({ nextY > maxScroll }, { nextY: maxScroll; });
				:scrollY: nextY;
				invalidate();
				return true;
			});
		});
		return false;
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ scrollable && containsPoint(x: event:x, y: event:y) }, {
			local Int is maxScroll: contentH - boxH;
			if({ maxScroll < 0 }, { maxScroll: 0; });
			if({ event:isWheelUp() && scrollY > 0 }, {
				:scrollY: scrollY - 1;
				invalidate();
				return true;
			});
			if({ event:isWheelDown() && scrollY < maxScroll }, {
				:scrollY: scrollY + 1;
				invalidate();
				return true;
			});
		});
		local Boolean is isMove: event:isMove();
		local Boolean is anyChanged: false;
		local Int is i: 0;
		while({ i < children:length() }, {
			if({ children:get(index: i):handleMouse(event: event) }, {
				if({ !isMove }, { return true; });
				anyChanged: true;
			});
			i: i + 1;
		});
		return anyChanged;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		children:each(action: local Function(Widget is ch){
			ch:collectFocus(targets: targets, owners: owners);
		});
	}

	replace Function is dispose(){
		children:each(action: local Function(Widget is ch){
			ch:dispose();
		});
	}
}
