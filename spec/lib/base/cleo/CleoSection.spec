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
	Boolean is groupResolvedFirst: false;

	replace Function is init(){
	}

	Function is markDirty(){
		self:dirtyRef:set(index: 0, value: true);
	}

	Function of Int is allocSlot(CleoSlot is slot){
		local Int is sid: self:idCounter:get(index: 0, default: 0);
		self:idCounter:set(index: 0, value: sid + 1);
		slot:id: sid;
		self:slots:add(item: slot);
		self:slotMap:set(key: sid, value: slot);
		self:markDirty();
		return sid;
	}

	Function of Int is addLine(String is text, CleoColor is color: CleoColor:default(), String is rightText: '', Boolean is bold: false){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 0);
		s:text: text;
		s:rightText: rightText;
		s:fgColor: color;
		s:bold: bold;
		return self:allocSlot(slot: s);
	}

	Function of Int is addThrobber(String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 1);
		s:text: text;
		s:rightText: rightText;
		s:fgColor: color;
		return self:allocSlot(slot: s);
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
		return self:allocSlot(slot: s);
	}

	Function of Int is addProgressArea(String is text: '', CleoColor is stage1Color: CleoColor:ansi(code: 252), CleoColor is stage2Color: CleoColor:ansi(code: 243), CleoColor is trackColor: CleoColor:ansi(code: 236), Boolean is showTwoStagePercent: true){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 3);
		s:text: text;
		s:stage1Color: stage1Color;
		s:stage2Color: stage2Color;
		s:trackColor: trackColor;
		s:showTwoStagePercent: showTwoStagePercent;
		return self:allocSlot(slot: s);
	}

	Function of Int is addImage(CleoImage is image){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 4);
		s:hasImage: true;
		s:image: image;
		return self:allocSlot(slot: s);
	}

	Function of Int is addAsciiImage(Array of String is lines){
		local CleoSlot is s: CleoSlot:init(id: 0, kind: 4);
		s:asciiLines: lines;
		return self:allocSlot(slot: s);
	}

	Function is setTitle(String is title){
		self:title: title;
		self:markDirty();
	}

	Function is setColors(CleoColor is fgColor: CleoColor:default(), CleoColor is bgColor: CleoColor:default()){
		self:fgColor: fgColor;
		self:bgColor: bgColor;
		self:markDirty();
	}

	Function is updateText(Int is index, String is text, String is rightText: ''){
		if({ !self:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: self:slotMap:get(key: index);
		s:text: text;
		if({ rightText != '' }, { s:rightText: rightText; });
		self:markDirty();
	}

	Function is setColor(Int is index, CleoColor is color){
		if({ !self:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: self:slotMap:get(key: index);
		s:fgColor: color;
		self:markDirty();
	}

	Function is resolveSlot(Int is index, String is badge, String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		if({ !self:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: self:slotMap:get(key: index);
		s:queued: false;
		s:resolved: true;
		s:badge: badge;
		s:text: text;
		if({ rightText != '' }, { s:rightText: rightText; });
		if({ color:isSet() }, { s:fgColor: color; });
		if({ self:groupResolvedFirst }, {
			local Int is n: self:slots:length();
			local Int is curPos: -1;
			local Int is k: 0;
			while({ k < n && curPos < 0 }, {
				if({ self:slots:get(index: k):id == s:id }, { curPos: k; });
				k: k + 1;
			});
			if({ curPos > 0 }, {
				local Int is insPos: 0;
				while({ insPos < curPos && self:slots:get(index: insPos):resolved }, {
					insPos: insPos + 1;
				});
				if({ insPos < curPos }, {
					local Int is sh: curPos;
					while({ sh > insPos }, {
						self:slots:set(index: sh, value: self:slots:get(index: sh - 1));
						sh: sh - 1;
					});
					self:slots:set(index: insPos, value: s);
				});
			});
		});
		self:markDirty();
	}

	Function is reopenThrobber(Int is index, String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		if({ !self:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: self:slotMap:get(key: index);
		s:queued: false;
		s:resolved: false;
		s:badge: '';
		s:text: text;
		if({ rightText != '' }, { s:rightText: rightText; });
		if({ color:isSet() }, { s:fgColor: color; });
		self:markDirty();
	}

	Function is updateProgress(Int is index, String is text, Float is stage1, Float is stage2, String is rightText: ''){
		if({ !self:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: self:slotMap:get(key: index);
		s:text: text;
		s:stage1: stage1;
		s:stage2: stage2;
		if({ rightText != '' }, { s:rightText: rightText; });
		self:markDirty();
	}

	Function is updateImage(Int is index, CleoImage is image){
		if({ !self:slotMap:has(key: index) }, { return; });
		local CleoSlot is s: self:slotMap:get(key: index);
		s:hasImage: true;
		s:image: image;
		self:markDirty();
	}

	Function is removeSlot(Int is index){
		if({ !self:slotMap:has(key: index) }, { return; });
		self:slotMap:remove(key: index);
		local Array of CleoSlot is kept: [];
		local Int is k: 0;
		while({ k < self:slots:length() }, {
			local CleoSlot is cur: self:slots:get(index: k);
			if({ cur:id != index }, {
				kept:add(item: cur);
			});
			k: k + 1;
		});
		self:slots: kept;
		self:markDirty();
	}
}
