#! Package base:theo
#! Nestable vertical or horizontal grid splitting a frame into fixed or weighted panes.

Class of Widget is Grid{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [Widget, GridPane, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'sys', [as Conditional(), as Loops()]],
		['base', 'math', as Math()]
	];

	String is orientation: 'vertical';
	Array of GridPane is panes: [];

	replace Function is init(String is orientation: 'vertical', Array of GridPane is panes: []){
		:orientation: orientation;
		:panes: panes;
	}

	held Function of GridPane is fixed(Int is size, Widget is child){
		return GridPane(isFixed: true, fixedSize: size, weightVal: 0.0, child: child);
	}

	held Function of GridPane is weight(Float is weight, Widget is child){
		return GridPane(isFixed: false, fixedSize: 0, weightVal: weight, child: child);
	}

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		panes:each(action: local Function(GridPane is gp){
			gp:child:applyTheme(theme: theme);
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: [cb];
		panes:each(action: local Function(GridPane is gp){
			gp:child:bindDirty(cb: cb);
		});
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		local Int is total: if({ orientation == 'horizontal' }, { w }, { h });
		local Int is fixedUsed: 0;
		local Float is weightSum: 0.0;
		panes:each(action: local Function(GridPane is gp){
			if({ gp:isFixed }, {
				fixedUsed: fixedUsed + gp:fixedSize;
			}, {
				weightSum: weightSum + gp:weightVal;
			});
		});
		local Int is rem: if({ total > fixedUsed }, { total - fixedUsed }, { 0 });
		local Int is pos: 0;
		local Int is idx: 0;
		local Int is count: panes:length();
		while({ idx < count }, {
			local GridPane is gp: panes:get(index: idx);
			local Int is sz: 0;
			if({ gp:isFixed }, {
				sz: gp:fixedSize;
			}, {
				if({ idx == count - 1 }, {
					sz: total - pos;
				}, {
					if({ weightSum > 0.0 }, {
						sz: toInt(value: (toFloat(value: rem) * gp:weightVal) / weightSum);
					});
				});
			});
			if({ sz < 0 }, { sz: 0; });
			if({ orientation == 'horizontal' }, {
				gp:child:layout(x: x + pos, y: y, w: sz, h: h);
			}, {
				gp:child:layout(x: x, y: y + pos, w: w, h: sz);
			});
			pos: pos + sz;
			idx: idx + 1;
		});
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		panes:each(action: local Function(GridPane is gp){
			gp:child:paint(buf: buf, renderer: renderer);
		});
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		local Int is i: 0;
		while({ i < panes:length() }, {
			local GridPane is gp: panes:get(index: i);
			if({ gp:child:handleKey(event: event) }, {
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		local Boolean is isMove: event:isMove();
		local Boolean is anyChanged: false;
		local Int is i: 0;
		while({ i < panes:length() }, {
			local GridPane is gp: panes:get(index: i);
			if({ gp:child:handleMouse(event: event) }, {
				if({ !isMove }, { return true; });
				anyChanged: true;
			});
			i: i + 1;
		});
		return anyChanged;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		panes:each(action: local Function(GridPane is gp){
			gp:child:collectFocus(targets: targets, owners: owners);
		});
	}

	replace Function is dispose(){
		panes:each(action: local Function(GridPane is gp){
			gp:child:dispose();
		});
	}
}
