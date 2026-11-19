#! Package base:cleo
#! Command Line Enhanced Output — inline indexed buffer with borders, sections,
#! animated throbbers, two-stage progress areas, and diff-based terminal rendering.

Class is Cleo{
	namespace: ['base', 'cleo'];

	replace Array of Array of String is using: [
		['base', 'cleo', BorderStyle],
		['base', 'cleo', BorderGlyphs],
		['base', 'cleo', as BorderGlyphs()],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', as CleoText()],
		['base', 'cleo', CleoSlot],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoImage],
		['base', 'cleo', ThrobberShape],
		['base', 'cleo', ThrobberEffect],
		['base', 'cleo', TitlePlacement],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Parallel()],
		['base', 'sys', as Time()],
		['base', 'sys', 'thread', ThreadScope]
	];

	String is title: '';
	CleoColor is titleColor: CleoColor:default();
	CleoColor is titleBgColor: CleoColor:default();
	CleoWidth is width: CleoWidth:percent(pct: 100);
	BorderStyle is outerBorder: BorderStyle:ROUNDED;
	BorderStyle is dividerBorder: BorderStyle:THIN;
	CleoColor is borderColor: CleoColor:default();
	CleoColor is dividerColor: CleoColor:default();
	CleoColor is fgColor: CleoColor:default();
	CleoColor is bgColor: CleoColor:default();
	Int is minWidthCols: 24;
	Int is maxWidthCols: 0;
	Int is tickIntervalMs: 140;
	Boolean is altScreen: false;
	Boolean is directOutput: false;

	Array of CleoSection is sections: [];
	CleoSection is defaultSection: CleoSection:init();
	Map of Int to CleoSlot is slotMap: Map:init();
	Array of Int is idCounter: [0];

	Boolean is running: false;
	Boolean is ttyMode: false;
	Int is timerId: -1;
	Int is tickCount: 0;
	Array of String is prevLines: [];
	Array of String is pendingCommits: [];
	Array of Boolean is dirtyRef: [false];
	Array of Boolean is directRef: [false];
	Array of Boolean is directStartedRef: [false];
	Boolean is directTopPrinted: false;
	Int is directSectionsEmitted: 0;
	Boolean is hasCommittedHeader: false;
	Int is prevTermW: 0;
	Int is prevTermH: 0;
	Int is lastFrameW: 0;

	replace Function is init(
		String is title: '',
		CleoColor is titleColor: CleoColor:default(),
		CleoColor is titleBgColor: CleoColor:default(),
		CleoWidth is width: CleoWidth:percent(pct: 100),
		BorderStyle is outerBorder: BorderStyle:ROUNDED,
		BorderStyle is dividerBorder: BorderStyle:THIN,
		CleoColor is borderColor: CleoColor:default(),
		CleoColor is dividerColor: CleoColor:default(),
		CleoColor is fgColor: CleoColor:default(),
		CleoColor is bgColor: CleoColor:default(),
		Int is minWidthCols: 24,
		Int is maxWidthCols: 0,
		Int is tickIntervalMs: 140,
		Boolean is altScreen: false,
		Boolean is directOutput: false
	){
		:title: title;
		:titleColor: titleColor;
		:titleBgColor: titleBgColor;
		:width: width;
		:outerBorder: outerBorder;
		:dividerBorder: dividerBorder;
		:borderColor: borderColor;
		:dividerColor: dividerColor;
		:fgColor: fgColor;
		:bgColor: bgColor;
		:minWidthCols: minWidthCols;
		:maxWidthCols: maxWidthCols;
		:tickIntervalMs: tickIntervalMs;
		:altScreen: altScreen;
		:directOutput: directOutput;
		:directRef: [directOutput];
		:directStartedRef: [false];
		:sections: [];
		:slotMap: Map:init();
		:idCounter: [0];
		:prevLines: [];
		:pendingCommits: [];

		local CleoSection is defSec: :createSection(
			title: '',
			titleColor: :titleColor,
			titleBgColor: :titleBgColor,
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: :fgColor,
			bgColor: :bgColor
		);
		:defaultSection: defSec;
		:sections:add(item: defSec);
	}

	## Creates a standard grayscale rounded Cleo surface for Spec CLI tools.
	held Function of Cleo is toolUi(String is title, Boolean is directOutput: false){
		return Cleo:init(
			title: title,
			titleColor: CleoColor:ansi(code: 255),
			titleBgColor: CleoColor:ansi(code: 236),
			width: CleoWidth:percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 237),
			directOutput: directOutput
		);
	}

	## Adds a standard grayscale section for Spec CLI tools.
	Function of CleoSection is addToolSection(String is title){
		return :addSection(
			title: title,
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
	}

	Function of CleoSection is createSection(
		String is title,
		CleoColor is titleColor,
		CleoColor is titleBgColor,
		TitlePlacement is titlePlacement,
		CleoColor is fgColor,
		CleoColor is bgColor
	){
		local CleoSection is sec: CleoSection:init();
		sec:title: title;
		sec:titleColor: titleColor;
		sec:titleBgColor: titleBgColor;
		sec:titlePlacement: titlePlacement;
		sec:fgColor: fgColor;
		sec:bgColor: bgColor;
		sec:slotMap: :slotMap;
		sec:idCounter: :idCounter;
		sec:dirtyRef: :dirtyRef;
		sec:directRef: :directRef;
		sec:directStartedRef: :directStartedRef;
		sec:hasDirectEmitCb: true;
		sec:directEmitCb: local Function(CleoSection is targetSec, CleoSlot is slot){
			:emitDirectSlotUnlocked(section: targetSec, slot: slot);
		};
		return sec;
	}

	Function is setDirectOutput(Boolean is enabled){
		:directOutput: enabled;
		:directRef:set(index: 0, value: enabled);
	}

	Function of CleoSection is addSection(
		String is title: '',
		CleoColor is titleColor: CleoColor:default(),
		CleoColor is titleBgColor: CleoColor:default(),
		TitlePlacement is titlePlacement: TitlePlacement:INLINE_BORDER,
		CleoColor is fgColor: CleoColor:default(),
		CleoColor is bgColor: CleoColor:default()
	){
		local CleoColor is effTC: :titleColor;
		if({ titleColor:isSet() }, { effTC: titleColor; });
		local CleoColor is effTB: :titleBgColor;
		if({ titleBgColor:isSet() }, { effTB: titleBgColor; });
		local CleoColor is effFg: :fgColor;
		if({ fgColor:isSet() }, { effFg: fgColor; });
		local CleoColor is effBg: :bgColor;
		if({ bgColor:isSet() }, { effBg: bgColor; });
		local CleoSection is sec: :createSection(
			title: title,
			titleColor: effTC,
			titleBgColor: effTB,
			titlePlacement: titlePlacement,
			fgColor: effFg,
			bgColor: effBg
		);
		Parallel:syncWith(lock: 77, action: {
			# Replace unused empty initial defaultSection if this is the first explicit section
			if(check: { :sections:length() == 1 && :defaultSection:slots:length() == 0 && :defaultSection:title == '' }, then: {
				:sections:set(index: 0, value: sec);
				:defaultSection: sec;
			}, else: {
				:sections:add(item: sec);
			});
			:dirtyRef:set(index: 0, value: true);
		});
		return sec;
	}

	# --- Convenience slot methods delegating to defaultSection under lock ---

	Function of Int is addLine(String is text, CleoColor is color: CleoColor:default(), String is rightText: '', Boolean is bold: false){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: :defaultSection:addLine(text: text, color: color, rightText: rightText, bold: bold);
		});
		if({ :running }, { :flush(); });
		return sid;
	}

	Function of Int is addThrobber(String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: :defaultSection:addThrobber(text: text, color: color, rightText: rightText);
		});
		if({ :running }, { :flush(); });
		return sid;
	}

	Function of Int is addShapeThrobber(ThrobberShape is shape: ThrobberShape:DOT, ThrobberEffect is effect: ThrobberEffect:BLINK, String is text: '', CleoColor is color: CleoColor:default(), Array of CleoColor is palette: [], String is rightText: ''){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: :defaultSection:addShapeThrobber(shape: shape, effect: effect, text: text, color: color, palette: palette, rightText: rightText);
		});
		if({ :running }, { :flush(); });
		return sid;
	}

	Function of Int is addProgressArea(String is text: '', CleoColor is stage1Color: CleoColor:ansi(code: 252), CleoColor is stage2Color: CleoColor:ansi(code: 243), CleoColor is trackColor: CleoColor:ansi(code: 236), Boolean is showTwoStagePercent: true){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: :defaultSection:addProgressArea(text: text, stage1Color: stage1Color, stage2Color: stage2Color, trackColor: trackColor, showTwoStagePercent: showTwoStagePercent);
		});
		if({ :running }, { :flush(); });
		return sid;
	}

	Function of Int is addImage(CleoImage is image){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: :defaultSection:addImage(image: image);
		});
		if({ :running }, { :flush(); });
		return sid;
	}

	Function is updateText(Int is index, String is text, String is rightText: ''){
		Parallel:syncWith(lock: 77, action: {
			:defaultSection:updateText(index: index, text: text, rightText: rightText);
		});
		if({ :running }, { :flush(); });
	}

	Function is setColor(Int is index, CleoColor is color){
		Parallel:syncWith(lock: 77, action: {
			:defaultSection:setColor(index: index, color: color);
		});
		if({ :running }, { :flush(); });
	}

	Function is resolveSlot(Int is index, String is badge, String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		Parallel:syncWith(lock: 77, action: {
			:defaultSection:resolveSlot(index: index, badge: badge, text: text, color: color, rightText: rightText);
		});
		if({ :running }, { :flush(); });
	}

	Function is updateProgress(Int is index, String is text, Float is stage1, Float is stage2, String is rightText: ''){
		Parallel:syncWith(lock: 77, action: {
			:defaultSection:updateProgress(index: index, text: text, stage1: stage1, stage2: stage2, rightText: rightText);
		});
		if({ :running }, { :flush(); });
	}

	Function is updateImage(Int is index, CleoImage is image){
		Parallel:syncWith(lock: 77, action: {
			:defaultSection:updateImage(index: index, image: image);
		});
		if({ :running }, { :flush(); });
	}

	Function is commitLineUnlocked(String is text, CleoColor is color: CleoColor:default()){
		local String is styled: if({ color:isSet() }, { color:fgSeq() . text . Ansi:reset() }, { text });
		:pendingCommits:add(item: styled);
		:dirtyRef:set(index: 0, value: true);
	}

	Function is commitSlotUnlocked(CleoSection is section, Int is slotId){
		if({ :directOutput }, { return; });
		if({ !section:slotMap:has(key: slotId) }, { return; });
		local Int is termW: Ansi:terminalWidth();
		local Int is totalW: :width:resolve(termWidth: termW, minCols: :minWidthCols, maxCols: :maxWidthCols);
		local Boolean is hasOuter: :outerBorder != BorderStyle:NONE;
		local Int is innerW: if({ hasOuter }, { totalW - 4 }, { totalW });
		if({ innerW < 8 }, { innerW: 8; });
		local BorderGlyphs is og: BorderGlyphs:forStyle(style: :outerBorder);
		local String is bc: :borderColor:fgSeq();
		local String is brst: if({ :borderColor:isSet() }, { Ansi:reset() }, { '' });
		local CleoSlot is slot: section:slotMap:get(key: slotId);
		local Array of String is rows: slot:renderInnerLines(innerW: innerW, secFg: section:fgColor, secBg: section:bgColor, tick: :tickCount);
		local Int is ri: 0;
		while({ ri < rows:length() }, {
			local String is rowText: rows:get(index: ri, default: '');
			if(check: { hasOuter }, then: {
				local String is padBg: if({ section:bgColor:isSet() }, { section:bgColor:bgSeq() . ' ' . Ansi:reset() }, { ' ' });
				:pendingCommits:add(item: bc . og:left . brst . padBg . rowText . padBg . bc . og:right . brst);
			}, else: {
				:pendingCommits:add(item: rowText);
			});
			ri: ri + 1;
		});
		:dirtyRef:set(index: 0, value: true);
	}

	Function is commitLine(String is text, CleoColor is color: CleoColor:default()){
		local String is styled: if({ color:isSet() }, { color:fgSeq() . text . Ansi:reset() }, { text });
		Parallel:syncWith(lock: 77, action: {
			:pendingCommits:add(item: styled);
			:dirtyRef:set(index: 0, value: true);
		});
		if({ :running }, { :flush(); });
	}

	# --- Lifecycle ---

	Function is emitDirectTopUnlocked(){
		if({ :directTopPrinted }, { return; });
		:directTopPrinted: true;
		local Int is termW: Ansi:terminalWidth();
		local Int is totalW: :width:resolve(termWidth: termW, minCols: :minWidthCols, maxCols: :maxWidthCols);
		:lastFrameW: totalW;
		local Boolean is hasOuter: :outerBorder != BorderStyle:NONE;
		local BorderGlyphs is og: BorderGlyphs:forStyle(style: :outerBorder);
		local Int is innerW: if({ hasOuter }, { totalW - 4 }, { totalW });
		if({ innerW < 8 }, { innerW: 8; });
		if(check: { hasOuter }, then: {
			Output:line(text: :buildRuleLine(
				leftCap: og:topLeft, fill: og:top, rightCap: og:topRight,
				innerW: innerW, lineColor: :borderColor,
				titleText: :title, tFg: :titleColor, tBg: :titleBgColor
			));
		}, else: {
			if({ :title != '' }, {
				Output:line(text: :buildHeaderRow(
					leftB: '', rightB: '', innerW: innerW,
					titleText: :title, tFg: :titleColor, tBg: :titleBgColor,
					secFg: :fgColor, secBg: :bgColor
				));
			});
		});
	}

	Function is emitDirectSlotUnlocked(CleoSection is section, CleoSlot is slot){
		:emitDirectTopUnlocked();
		local Int is termW: Ansi:terminalWidth();
		local Int is totalW: :width:resolve(termWidth: termW, minCols: :minWidthCols, maxCols: :maxWidthCols);
		local Boolean is hasOuter: :outerBorder != BorderStyle:NONE;
		local Int is innerW: if({ hasOuter }, { totalW - 4 }, { totalW });
		if({ innerW < 8 }, { innerW: 8; });
		local BorderGlyphs is og: BorderGlyphs:forStyle(style: :outerBorder);
		local BorderGlyphs is dg: BorderGlyphs:forStyle(style: :dividerBorder);
		local String is bc: :borderColor:fgSeq();
		local String is brst: if({ :borderColor:isSet() }, { Ansi:reset() }, { '' });

		if({ !section:directHeaderPrinted }, {
			section:directHeaderPrinted: true;
			local Int is visIdx: :directSectionsEmitted;
			:directSectionsEmitted: :directSectionsEmitted + 1;
			if({ visIdx > 0 }, {
				local Boolean is inlineSecTitle: section:title != '' && section:titlePlacement == TitlePlacement:INLINE_BORDER;
				if(check: { :dividerBorder != BorderStyle:NONE }, then: {
					local String is dl: if({ hasOuter }, { og:divLeft }, { dg:divLeft });
					local String is dr: if({ hasOuter }, { og:divRight }, { dg:divRight });
					local String is divTitle: '';
					if({ inlineSecTitle }, { divTitle: section:title; });
					Output:line(text: :buildRuleLine(
						leftCap: dl, fill: dg:divMid, rightCap: dr,
						innerW: innerW, lineColor: :dividerColor,
						titleText: divTitle,
						tFg: section:titleColor, tBg: section:titleBgColor
					));
				}, else: {
					if({ inlineSecTitle }, {
						Output:line(text: :buildHeaderRow(
							leftB: og:left, rightB: og:right, innerW: innerW,
							titleText: section:title, tFg: section:titleColor, tBg: section:titleBgColor,
							secFg: section:fgColor, secBg: section:bgColor
						));
					});
				});
			});
			if({ section:title != '' && (section:titlePlacement == TitlePlacement:HEADER_ROW || (visIdx == 0 && :title != '')) }, {
				Output:line(text: :buildHeaderRow(
					leftB: og:left, rightB: og:right, innerW: innerW,
					titleText: section:title, tFg: section:titleColor, tBg: section:titleBgColor,
					secFg: section:fgColor, secBg: section:bgColor
				));
			});
		});

		local Array of String is rows: slot:renderInnerLines(innerW: innerW, secFg: section:fgColor, secBg: section:bgColor, tick: 0);
		local Int is ri: 0;
		while({ ri < rows:length() }, {
			local String is rowText: rows:get(index: ri, default: '');
			if(check: { hasOuter }, then: {
				local String is padBg: if({ section:bgColor:isSet() }, { section:bgColor:bgSeq() . ' ' . Ansi:reset() }, { ' ' });
				Output:line(text: bc . og:left . brst . padBg . rowText . padBg . bc . og:right . brst);
			}, else: {
				Output:line(text: rowText);
			});
			ri: ri + 1;
		});
	}

	Function is start(ThreadScope is scope){
		local Boolean is isDirect: false;
		Parallel:syncWith(lock: 77, action: {
			if({ :running }, { return; });
			isDirect: :directOutput;
			if({ isDirect }, {
				:ttyMode: false;
				:running: true;
				:directStartedRef:set(index: 0, value: true);
				:emitDirectTopUnlocked();
				local Int is si: 0;
				while({ si < :sections:length() }, {
					local CleoSection is sec: :sections:get(index: si);
					local Int is sli: 0;
					while({ sli < sec:slots:length() }, {
						local CleoSlot is sl: sec:slots:get(index: sli);
						if({ sl:kind == 0 }, {
							:emitDirectSlotUnlocked(section: sec, slot: sl);
						});
						sli: sli + 1;
					});
					si: si + 1;
				});
				:dirtyRef:set(index: 0, value: true);
				return;
			});
			:ttyMode: Ansi:isTty();
			if({ :ttyMode }, {
				Ansi:enableVirtualTerminal();
				if({ :altScreen }, {
					Output:consOut(text: Ansi:enterAltScreen() . Ansi:hideCursor());
				}, {
					Output:consOut(text: Ansi:hideCursor());
				});
			});
			:running: true;
			:dirtyRef:set(index: 0, value: true);
		});
		:flush();
		if({ !isDirect && :ttyMode && :tickIntervalMs > 0 }, {
			:timerId: Time:setInterval(scope: scope, ms: :tickIntervalMs, count: 0, callback: {
				:tick();
			});
		});
	}

	Function is tick(){
		Parallel:syncWith(lock: 77, action: {
			if({ !:running }, { return; });
			:tickCount: :tickCount + 1;
			:dirtyRef:set(index: 0, value: true);
			:flushUnlocked();
		});
	}

	Function is finish(){
		local Int is tid: -1;
		Parallel:syncWith(lock: 77, action: {
			tid: :timerId;
			:timerId: -1;
			:running: false;
			:dirtyRef:set(index: 0, value: true);
		});
		if({ tid >= 0 }, {
			Time:cancelTimer(timerId: tid);
		});
		if({ :ttyMode && :altScreen }, {
			Parallel:syncWith(lock: 77, action: {
				:prevLines: [];
				:prevTermW: 0;
				:prevTermH: 0;
				:lastFrameW: 0;
				Output:consOut(text: Ansi:exitAltScreen());
			});
		});
		:flushFinal();
		if({ :ttyMode }, {
			Output:consOut(text: Ansi:showCursor());
		});
	}

	# --- Rendering ---

	Function of String is buildRuleLine(String is leftCap, String is fill, String is rightCap, Int is innerW, CleoColor is lineColor, String is titleText, CleoColor is tFg, CleoColor is tBg){
		local String is lc: lineColor:fgSeq();
		local String is rst: if({ lineColor:isSet() }, { Ansi:reset() }, { '' });
		if({ titleText == '' }, {
			return lc . leftCap . CleoText:repeatStr(s: fill, count: innerW + 2) . rightCap . rst;
		});
		local String is fittedTitle: CleoText:truncate(text: titleText, maxCols: innerW);
		local Int is tw: CleoText:displayWidth(text: fittedTitle);
		local Int is rem: (innerW + 2) - 1 - tw;
		if({ rem < 0 }, { rem: 0; });
		local String is styledTitle: fittedTitle;
		if({ tFg:isSet() || tBg:isSet() }, {
			styledTitle: tBg:bgSeq() . tFg:fgSeq() . Ansi:bold() . fittedTitle . Ansi:reset();
		});
		return lc . leftCap . fill . rst . styledTitle . lc . CleoText:repeatStr(s: fill, count: rem) . rightCap . rst;
	}

	Function of String is buildHeaderRow(String is leftB, String is rightB, Int is innerW, String is titleText, CleoColor is tFg, CleoColor is tBg, CleoColor is secFg, CleoColor is secBg){
		local CleoColor is effFg: if({ tFg:isSet() }, { tFg }, { secFg });
		local CleoColor is effBg: if({ tBg:isSet() }, { tBg }, { secBg });
		local String is padded: CleoText:padRight(text: titleText, width: innerW);
		local String is styled: effBg:bgSeq() . effFg:fgSeq() . Ansi:bold() . padded . Ansi:reset();
		local String is bc: :borderColor:fgSeq();
		local String is brst: if({ :borderColor:isSet() }, { Ansi:reset() }, { '' });
		if({ :outerBorder == BorderStyle:NONE }, {
			return styled;
		});
		return bc . leftB . brst . ' ' . styled . ' ' . bc . rightB . brst;
	}

	Function of Array of String is buildFrameLines(){
		local Int is termW: Ansi:terminalWidth();
		local Int is totalW: :width:resolve(termWidth: termW, minCols: :minWidthCols, maxCols: :maxWidthCols);
		:lastFrameW: totalW;
		local Boolean is hasOuter: :outerBorder != BorderStyle:NONE;
		local BorderGlyphs is og: BorderGlyphs:forStyle(style: :outerBorder);
		local BorderGlyphs is dg: BorderGlyphs:forStyle(style: :dividerBorder);

		local Int is innerW: if({ hasOuter }, { totalW - 4 }, { totalW });
		if({ innerW < 8 }, { innerW: 8; });

		local Array of String is lines: [];
		if(check: { !:hasCommittedHeader }, then: {
			if(check: { hasOuter }, then: {
				lines:add(item: :buildRuleLine(
					leftCap: og:topLeft, fill: og:top, rightCap: og:topRight,
					innerW: innerW, lineColor: :borderColor,
					titleText: :title, tFg: :titleColor, tBg: :titleBgColor
				));
			}, else: {
				if({ :title != '' }, {
					lines:add(item: :buildHeaderRow(
						leftB: '', rightB: '', innerW: innerW,
						titleText: :title, tFg: :titleColor, tBg: :titleBgColor,
						secFg: :fgColor, secBg: :bgColor
					));
				});
			});
		});

		local String is bc: :borderColor:fgSeq();
		local String is brst: if({ :borderColor:isSet() }, { Ansi:reset() }, { '' });
		local Int is si: 0;
		local Int is visIdx: if({ :hasCommittedHeader }, { 1 }, { 0 });
		while({ si < :sections:length() }, {
			local CleoSection is sec: :sections:get(index: si);
			if({ sec:slots:length() > 0 }, {
				if({ visIdx > 0 && !(:hasCommittedHeader && si == 0) }, {
					local Boolean is inlineSecTitle: sec:title != '' && sec:titlePlacement == TitlePlacement:INLINE_BORDER;
					if(check: { :dividerBorder != BorderStyle:NONE }, then: {
						local String is dl: if({ hasOuter }, { og:divLeft }, { dg:divLeft });
						local String is dr: if({ hasOuter }, { og:divRight }, { dg:divRight });
						local String is divTitle: '';
						if({ inlineSecTitle }, { divTitle: sec:title; });
						lines:add(item: :buildRuleLine(
							leftCap: dl, fill: dg:divMid, rightCap: dr,
							innerW: innerW, lineColor: :dividerColor,
							titleText: divTitle,
							tFg: sec:titleColor, tBg: sec:titleBgColor
						));
					}, else: {
						if({ inlineSecTitle }, {
							lines:add(item: :buildHeaderRow(
								leftB: og:left, rightB: og:right, innerW: innerW,
								titleText: sec:title, tFg: sec:titleColor, tBg: sec:titleBgColor,
								secFg: sec:fgColor, secBg: sec:bgColor
							));
						});
					});
				});
				if({ !(:hasCommittedHeader && si == 0) && sec:title != '' && (sec:titlePlacement == TitlePlacement:HEADER_ROW || (visIdx == 0 && :title != '')) }, {
					lines:add(item: :buildHeaderRow(
						leftB: og:left, rightB: og:right, innerW: innerW,
						titleText: sec:title, tFg: sec:titleColor, tBg: sec:titleBgColor,
						secFg: sec:fgColor, secBg: sec:bgColor
					));
				});
				local Int is sli: 0;
				while({ sli < sec:slots:length() }, {
					local CleoSlot is slot: sec:slots:get(index: sli);
					local Array of String is rows: slot:renderInnerLines(innerW: innerW, secFg: sec:fgColor, secBg: sec:bgColor, tick: :tickCount);
					local Int is ri: 0;
					while({ ri < rows:length() }, {
						local String is rowText: rows:get(index: ri, default: '');
						if(check: { hasOuter }, then: {
							local String is padBg: if({ sec:bgColor:isSet() }, { sec:bgColor:bgSeq() . ' ' . Ansi:reset() }, { ' ' });
							lines:add(item: bc . og:left . brst . padBg . rowText . padBg . bc . og:right . brst);
						}, else: {
							lines:add(item: rowText);
						});
						ri: ri + 1;
					});
					sli: sli + 1;
				});
				visIdx: visIdx + 1;
			});
			si: si + 1;
		});

		if({ hasOuter }, {
			lines:add(item: :buildRuleLine(
				leftCap: og:bottomLeft, fill: og:bottom, rightCap: og:bottomRight,
				innerW: innerW, lineColor: :borderColor,
				titleText: '', tFg: CleoColor:default(), tBg: CleoColor:default()
			));
		});
		return lines;
	}

	Function is markDirty(){
		:dirtyRef:set(index: 0, value: true);
	}

	Function is flushUnlocked(){
		if({ !:dirtyRef:get(index: 0, default: false) && :pendingCommits:length() == 0 }, { return; });
		:dirtyRef:set(index: 0, value: false);

		if({ !:ttyMode }, {
			local Int is ci: 0;
			while({ ci < :pendingCommits:length() }, {
				Output:line(text: :pendingCommits:get(index: ci, default: ''));
				ci: ci + 1;
			});
			:pendingCommits: [];
			return;
		});

		local Int is prevFrameW: :lastFrameW;
		local Boolean is pinningNow: false;
		if({ :pendingCommits:length() > 0 && !:hasCommittedHeader }, {
			:hasCommittedHeader: true;
			pinningNow: true;
		});
		local Array of String is nextLines: :buildFrameLines();
		local Int is prevCount: :prevLines:length();
		local Int is nextCount: nextLines:length();
		local Int is termW: Ansi:terminalWidth();
		local Int is termH: Ansi:terminalHeight();
		local Int is visCap: if({ termH > 1 }, { termH - 1 }, { 23 });
		local Boolean is resized: (:prevTermW > 0 && termW != :prevTermW) || (:prevTermH > 0 && termH != :prevTermH);
		local String is out: Ansi:beginSyncUpdate();

		local Int is startLineIdx: 0;
		if({ nextCount > visCap }, {
			startLineIdx: nextCount - visCap;
		});

		if(check: { :altScreen }, then: {
			out: out . Ansi:moveTo(row: 1, col: 1) . Ansi:eraseToEnd();
		}, else: {
			local Int is prevVisCap: if({ :prevTermH > 1 }, { :prevTermH - 1 }, { visCap });
			local Int is drawnPrevLines: if({ prevCount > prevVisCap }, { prevVisCap }, { prevCount });
			local Int is prevVisRows: drawnPrevLines;
			if({ drawnPrevLines > 0 && termW > 0 && prevFrameW > termW }, {
				local Int is wrapFactor: ((prevFrameW - 1) / termW) + 1;
				prevVisRows: drawnPrevLines * wrapFactor;
			});

			local Int is upCount: if({ prevVisRows > visCap }, { visCap }, { prevVisRows });
			if({ pinningNow && upCount >= 2 }, {
				upCount: upCount - 2;
			});

			if({ upCount > 0 }, {
				out: out . Ansi:cursorUp(n: upCount) . Ansi:carriageReturn();
			});
			if({ resized && prevCount > 0 }, {
				out: out . Ansi:eraseToEnd();
			});
		});

		# Emit any committed lines permanently above the live frame
		local Int is ci: 0;
		while({ ci < :pendingCommits:length() }, {
			out: out . Ansi:eraseLine() . :pendingCommits:get(index: ci, default: '') . "\n";
			ci: ci + 1;
		});
		:pendingCommits: [];

		# Emit live frame lines (visible window when frame exceeds terminal height)
		local Int is li: startLineIdx;
		while({ li < nextCount }, {
			out: out . Ansi:eraseLine() . nextLines:get(index: li, default: '') . "\n";
			li: li + 1;
		});
		if({ (nextCount < prevCount && prevCount <= visCap) || resized }, {
			out: out . Ansi:eraseToEnd();
		});
		out: out . Ansi:endSyncUpdate();
		:prevLines: nextLines;
		:prevTermW: termW;
		:prevTermH: termH;
		Output:consOut(text: out);
	}

	Function is flush(){
		Parallel:syncWith(lock: 77, action: {
			:flushUnlocked();
		});
	}

	Function is flushFinal(){
		Parallel:syncWith(lock: 77, action: {
			:dirtyRef:set(index: 0, value: false);
			if({ !:ttyMode }, {
				local Int is ci: 0;
				while({ ci < :pendingCommits:length() }, {
					Output:line(text: :pendingCommits:get(index: ci, default: ''));
					ci: ci + 1;
				});
				:pendingCommits: [];
				if({ :directOutput }, {
					if({ :directTopPrinted && :outerBorder != BorderStyle:NONE }, {
						local Int is termW: Ansi:terminalWidth();
						local Int is totalW: :width:resolve(termWidth: termW, minCols: :minWidthCols, maxCols: :maxWidthCols);
						local Int is innerW: totalW - 4;
						if({ innerW < 8 }, { innerW: 8; });
						local BorderGlyphs is og: BorderGlyphs:forStyle(style: :outerBorder);
						Output:line(text: :buildRuleLine(
							leftCap: og:bottomLeft, fill: og:bottom, rightCap: og:bottomRight,
							innerW: innerW, lineColor: :borderColor,
							titleText: '', tFg: CleoColor:default(), tBg: CleoColor:default()
						));
					});
					return;
				});
				local Array of String is finalLines: :buildFrameLines();
				local Int is fi: 0;
				while({ fi < finalLines:length() }, {
					Output:line(text: finalLines:get(index: fi, default: ''));
					fi: fi + 1;
				});
				return;
			});
			# Re-render final frame cleanly
			local Int is prevFrameW: :lastFrameW;
			local Array of String is nextLines: :buildFrameLines();
			local Int is prevCount: :prevLines:length();
			local Int is nextCount: nextLines:length();
			local Int is termW: Ansi:terminalWidth();
			local Int is termH: Ansi:terminalHeight();
			local Int is visCap: if({ termH > 1 }, { termH - 1 }, { 23 });
			local Boolean is resized: (:prevTermW > 0 && termW != :prevTermW) || (:prevTermH > 0 && termH != :prevTermH);
			local String is out: Ansi:beginSyncUpdate();

			local Int is prevVisCap: if({ :prevTermH > 1 }, { :prevTermH - 1 }, { visCap });
			local Int is drawnPrevLines: if({ prevCount > prevVisCap }, { prevVisCap }, { prevCount });
			local Int is prevVisRows: drawnPrevLines;
			if({ drawnPrevLines > 0 && termW > 0 && prevFrameW > termW }, {
				local Int is wrapFactor: ((prevFrameW - 1) / termW) + 1;
				prevVisRows: drawnPrevLines * wrapFactor;
			});

			local Int is upCount: if({ prevVisRows > visCap }, { visCap }, { prevVisRows });

			if({ upCount > 0 }, {
				out: out . Ansi:cursorUp(n: upCount) . Ansi:carriageReturn();
			});
			if({ prevCount > 0 }, {
				out: out . Ansi:eraseToEnd();
			});
			local Int is ci: 0;
			while({ ci < :pendingCommits:length() }, {
				out: out . Ansi:eraseLine() . :pendingCommits:get(index: ci, default: '') . "\n";
				ci: ci + 1;
			});
			:pendingCommits: [];
			local Int is li: 0;
			while({ li < nextCount }, {
				out: out . Ansi:eraseLine() . nextLines:get(index: li, default: '') . "\n";
				li: li + 1;
			});
			out: out . Ansi:endSyncUpdate();
			:prevLines: nextLines;
			:prevTermW: termW;
			:prevTermH: termH;
			Output:consOut(text: out);
		});
	}

	## Single-buffer mode: builds the current UI buffer once and outputs it immediately
	## without starting a ThreadScope, timer, or cursor control.
	Function is render(){
		local Array of String is lines: :buildFrameLines();
		local Int is i: 0;
		while({ i < lines:length() }, {
			Output:line(text: lines:get(index: i, default: ''));
			i: i + 1;
		});
	}
}
