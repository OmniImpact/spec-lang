#! Package base:theo
#! Vertical container placing children one after another with optional [gap] and [Spacer] flex.

Class of Widget is Col{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', Widget],
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'theo', TheoCallback],
		['base', 'theo', KeyEvent],
		['base', 'theo', FocusTarget],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'math', as Math()]
	];

	Int is gap: 0;
	Array of Widget is children: [];

	replace Function is init(Int is gap: 0, Array of Widget is children: []){
		:gap: gap;
		:children: children;
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: [TheoCallback(fn: cb)];
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
				fixedTotal: fixedTotal + ch:measureHeight(maxW: w, maxH: h);
			});
			i: i + 1;
		});
		local Int is rem: if({ h > fixedTotal }, { h - fixedTotal }, { 0 });
		local Int is curY: y;
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
				chH: ch:measureHeight(maxW: w, maxH: h);
			});
			ch:layout(x: x, y: curY, w: w, h: chH);
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
