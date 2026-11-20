#! Package base:theo
#! Horizontal container placing children one after another with optional [gap] and [Spacer] flex.

Class of Widget is Row{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [Widget, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, FocusTarget]],
		['base', 'sys', [as Conditional(), as Loops()]],
		['base', 'math', as Math()]
	];

	Int is gap: 0;
	Boolean is arrowFocus: false;
	Array of Widget is children: [];

	replace Function is init(Int is gap: 0, Boolean is arrowFocus: false, Array of Widget is children: []){
		:gap: gap;
		:arrowFocus: arrowFocus;
		:children: children;
	}

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		children:each(action: local Function(Widget is ch){
			ch:applyTheme(theme: theme);
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: [cb];
		children:each(action: local Function(Widget is ch){
			ch:bindDirty(cb: cb);
		});
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		local Int is count: children:length();
		if({ count == 0 }, { return; });
		local Int is fixedTotal: (count - 1) * gap;
		local Float is weightTotal: 0.0;
		local Int is i: 0;
		while({ i < count }, {
			local Widget is ch: children:get(index: i);
			local Float is fw: ch:flexWeight();
			if({ fw > 0.0 }, {
				weightTotal: weightTotal + fw;
			}, {
				fixedTotal: fixedTotal + ch:measureWidth(maxW: w);
			});
			i: i + 1;
		});
		local Int is rem: if({ w > fixedTotal }, { w - fixedTotal }, { 0 });
		local Int is curX: x;
		i: 0;
		while({ i < count }, {
			local Widget is ch: children:get(index: i);
			local Float is fw: ch:flexWeight();
			local Int is cw: 0;
			if({ fw > 0.0 }, {
				if({ weightTotal > 0.0 }, {
					cw: toInt(value: (toFloat(value: rem) * fw) / weightTotal);
				});
			}, {
				cw: ch:measureWidth(maxW: w);
			});
			local Int is chH: ch:measureHeight(maxW: cw, maxH: h);
			if({ chH > h }, { chH: h; });
			ch:layout(x: curX, y: y, w: cw, h: chH);
			curX: curX + cw + gap;
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
		if({ arrowFocus && (event:isLeft() || event:isRight()) }, {
			local Array of FocusTarget is fts: [];
			local Array of Widget is fws: [];
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
					local Int is next: if({ event:isLeft() }, { (cur - 1 + n) % n }, { (cur + 1) % n });
					fts:get(index: next):requestFocus();
					return true;
				});
			});
		});
		return false;
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
