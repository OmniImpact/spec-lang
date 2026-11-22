#! Package base:cleo
#! A stacked content section within a Cleo surface, with its own title and colors.

Class is CleoSection{
	namespace: ['base', 'cleo'];

	replace Array of Array of String is using: [
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoSlot],
		['base', 'cleo', CleoImage],
		['base', 'cleo', ThrobberShape],
		['base', 'cleo', ThrobberEffect],
		['base', 'cleo', TitlePlacement],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Output()],
		['base', 'sys', as Parallel()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is title: '';
	CleoColor is titleColor: CleoColor:default();
	CleoColor is titleBgColor: CleoColor:default();
	TitlePlacement is titlePlacement: TitlePlacement:INLINE_BORDER;
	CleoColor is fgColor: CleoColor:default();
	CleoColor is bgColor: CleoColor:default();

	Array of CleoSlot is slots: [];
	Map of Int to CleoSlot is slotMap: Map:init();
	Array of Int is idCounter: [0];
	Array of Boolean is dirtyRef: [false];
	Array of Boolean is directRef: [false];
	Array of Boolean is directStartedRef: [false];
	Boolean is directHeaderPrinted: false;
	Boolean is hasDirectEmitCb: false;
	Function is directEmitCb: local Function(CleoSection is _sec, CleoSlot is _s){};
	Boolean is groupResolvedFirst: false;

	replace Function is init(){
	}

	Function is markDirty(){
		:dirtyRef:set(index: 0, value: true);
	}

	Function of Int is allocSlot(CleoSlot is slot){
		local Int is sid: :idCounter:get(index: 0, default: 0);
		:idCounter:set(index: 0, value: sid + 1);
		slot:id: sid;
		:slots:add(item: slot);
		:slotMap:set(key: sid, value: slot);
		:markDirty();
		return sid;
	}

	Function of Int is addLine(String is text, CleoColor is color: CleoColor:default(), String is rightText: '', Boolean is bold: false, Boolean is wrap: false){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 0);
		s:text: text;
		s:rightText: rightText;
		s:fgColor: color;
		s:bold: bold;
		s:wrap: wrap;
		local Int is sid: :allocSlot(slot: s);
		if({ :directRef:get(index: 0, default: false) && :directStartedRef:get(index: 0, default: false) && :hasDirectEmitCb }, {
			Parallel:syncWith(lock: 77, action: {
				local Function is cb: :directEmitCb;
				cb(:, s);
			});
		});
		return sid;
	}

	Function of Int is addThrobber(String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 1);
		s:text: text;
		s:rightText: rightText;
		s:fgColor: color;
		return :allocSlot(slot: s);
	}

	Function of Int is addShapeThrobber(ThrobberShape is shape: ThrobberShape:DOT, ThrobberEffect is effect: ThrobberEffect:BLINK, String is text: '', CleoColor is color: CleoColor:default(), Array of CleoColor is palette: [], String is rightText: '', Boolean is queued: false){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 2);
		s:shape: shape;
		s:effect: effect;
		s:text: text;
		s:rightText: rightText;
		s:fgColor: color;
		s:palette: palette;
		s:queued: queued;
		return :allocSlot(slot: s);
	}

	Function of Int is addProgressArea(String is text: '', CleoColor is stage1Color: CleoColor:ansi(code: 252), CleoColor is stage2Color: CleoColor:ansi(code: 243), CleoColor is trackColor: CleoColor:ansi(code: 236), Boolean is showTwoStagePercent: true){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 3);
		s:text: text;
		s:stage1Color: stage1Color;
		s:stage2Color: stage2Color;
		s:trackColor: trackColor;
		s:showTwoStagePercent: showTwoStagePercent;
		return :allocSlot(slot: s);
	}

	Function of Int is addImage(CleoImage is image){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 4);
		s:hasImage: true;
		s:image: image;
		return :allocSlot(slot: s);
	}

	Function of Int is addAsciiImage(Array of String is lines){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 4);
		s:asciiLines: lines;
		return :allocSlot(slot: s);
	}

	Function is setTitle(String is title){
		:title: title;
		:markDirty();
	}

	Function is setColors(CleoColor is fgColor: CleoColor:default(), CleoColor is bgColor: CleoColor:default()){
		:fgColor: fgColor;
		:bgColor: bgColor;
		:markDirty();
	}

	Function is updateText(Int is index, String is text, String is rightText: ''){
		if({ !:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: :slotMap:get(key: index);
		s:text: text;
		if({ rightText != '' }, { s:rightText: rightText; });
		:markDirty();
	}

	Function is setColor(Int is index, CleoColor is color){
		if({ !:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: :slotMap:get(key: index);
		s:fgColor: color;
		:markDirty();
	}

	Function is resolveSlot(Int is index, String is badge, String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		if({ !:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: :slotMap:get(key: index);
		s:queued: false;
		s:resolved: true;
		s:badge: badge;
		s:text: text;
		if({ rightText != '' }, { s:rightText: rightText; });
		if({ color:isSet() }, { s:fgColor: color; });
		if({ :groupResolvedFirst }, {
			local Int is n: :slots:length();
			local Int is curPos: -1;
			local Int is k: 0;
			while({ k < n && curPos < 0 }, {
				if({ :slots:get(index: k):id == s:id }, { curPos: k; });
				k: k + 1;
			});
			if({ curPos > 0 }, {
				local Int is insPos: 0;
				while({ insPos < curPos && :slots:get(index: insPos):resolved }, {
					insPos: insPos + 1;
				});
				if({ insPos < curPos }, {
					local Int is sh: curPos;
					while({ sh > insPos }, {
						:slots:set(index: sh, value: :slots:get(index: sh - 1));
						sh: sh - 1;
					});
					:slots:set(index: insPos, value: s);
				});
			});
		});
		:markDirty();
		if({ :directRef:get(index: 0, default: false) && :directStartedRef:get(index: 0, default: false) && :hasDirectEmitCb }, {
			Parallel:syncWith(lock: 77, action: {
				local Function is cb: :directEmitCb;
				cb(:, s);
			});
		});
	}

	Function is reopenThrobber(Int is index, String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		if({ !:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: :slotMap:get(key: index);
		s:queued: false;
		s:resolved: false;
		s:badge: '';
		s:text: text;
		if({ rightText != '' }, { s:rightText: rightText; });
		if({ color:isSet() }, { s:fgColor: color; });
		:markDirty();
	}

	Function is updateProgress(Int is index, String is text, Float is stage1, Float is stage2, String is rightText: ''){
		if({ !:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: :slotMap:get(key: index);
		s:text: text;
		s:stage1: stage1;
		s:stage2: stage2;
		if({ rightText != '' }, { s:rightText: rightText; });
		:markDirty();
	}

	Function is updateImage(Int is index, CleoImage is image){
		if({ !:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: :slotMap:get(key: index);
		s:hasImage: true;
		s:image: image;
		:markDirty();
	}

	Function is removeSlot(Int is index){
		if({ !:slotMap:has(key: index) }, { return; });
		:slotMap:remove(key: index);
		local Array of CleoSlot is kept: [];
		local Int is k: 0;
		while({ k < :slots:length() }, {
			local CleoSlot is cur: :slots:get(index: k);
			if({ cur:id != index }, {
				kept:add(item: cur);
			});
			k: k + 1;
		});
		:slots: kept;
		:markDirty();
	}
}
