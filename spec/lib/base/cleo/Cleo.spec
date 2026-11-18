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
		['base', 'sys', as Time()]
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
		Boolean is altScreen: false
	){
		self:title: title;
		self:titleColor: titleColor;
		self:titleBgColor: titleBgColor;
		self:width: width;
		self:outerBorder: outerBorder;
		self:dividerBorder: dividerBorder;
		self:borderColor: borderColor;
		self:dividerColor: dividerColor;
		self:fgColor: fgColor;
		self:bgColor: bgColor;
		self:minWidthCols: minWidthCols;
		self:maxWidthCols: maxWidthCols;
		self:tickIntervalMs: tickIntervalMs;
		self:altScreen: altScreen;
		self:sections: [];
		self:slotMap: Map:init();
		self:idCounter: [0];
		self:prevLines: [];
		self:pendingCommits: [];

		local CleoSection is defSec: self:createSection(
			title: '',
			titleColor: self:titleColor,
			titleBgColor: self:titleBgColor,
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: self:fgColor,
			bgColor: self:bgColor
		);
		self:defaultSection: defSec;
		self:sections:add(item: defSec);
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
		sec:slotMap: self:slotMap;
		sec:idCounter: self:idCounter;
		sec:dirtyRef: self:dirtyRef;
		return sec;
	}

	Function of CleoSection is addSection(
		String is title: '',
		CleoColor is titleColor: CleoColor:default(),
		CleoColor is titleBgColor: CleoColor:default(),
		TitlePlacement is titlePlacement: TitlePlacement:INLINE_BORDER,
		CleoColor is fgColor: CleoColor:default(),
		CleoColor is bgColor: CleoColor:default()
	){
		local CleoColor is effTC: self:titleColor;
		if({ titleColor:isSet() }, { effTC: titleColor; });
		local CleoColor is effTB: self:titleBgColor;
		if({ titleBgColor:isSet() }, { effTB: titleBgColor; });
		local CleoColor is effFg: self:fgColor;
		if({ fgColor:isSet() }, { effFg: fgColor; });
		local CleoColor is effBg: self:bgColor;
		if({ bgColor:isSet() }, { effBg: bgColor; });
		local CleoSection is sec: self:createSection(
			title: title,
			titleColor: effTC,
			titleBgColor: effTB,
			titlePlacement: titlePlacement,
			fgColor: effFg,
			bgColor: effBg
		);
		Parallel:syncWith(lock: 77, action: {
			# Replace unused empty initial defaultSection if this is the first explicit section
			if(check: { self:sections:length() == 1 && self:defaultSection:slots:length() == 0 && self:defaultSection:title == '' }, then: {
				self:sections:set(index: 0, value: sec);
				self:defaultSection: sec;
			}, else: {
				self:sections:add(item: sec);
			});
			self:dirtyRef:set(index: 0, value: true);
		});
		return sec;
	}

	# --- Convenience slot methods delegating to defaultSection under lock ---

	Function of Int is addLine(String is text, CleoColor is color: CleoColor:default(), String is rightText: '', Boolean is bold: false){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: self:defaultSection:addLine(text: text, color: color, rightText: rightText, bold: bold);
		});
		if({ self:running }, { self:flush(); });
		return sid;
	}

	Function of Int is addThrobber(String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: self:defaultSection:addThrobber(text: text, color: color, rightText: rightText);
		});
		if({ self:running }, { self:flush(); });
		return sid;
	}

	Function of Int is addShapeThrobber(ThrobberShape is shape: ThrobberShape:DOT, ThrobberEffect is effect: ThrobberEffect:BLINK, String is text: '', CleoColor is color: CleoColor:default(), Array of CleoColor is palette: [], String is rightText: ''){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: self:defaultSection:addShapeThrobber(shape: shape, effect: effect, text: text, color: color, palette: palette, rightText: rightText);
		});
		if({ self:running }, { self:flush(); });
		return sid;
	}

	Function of Int is addProgressArea(String is text: '', CleoColor is stage1Color: CleoColor:ansi(code: 252), CleoColor is stage2Color: CleoColor:ansi(code: 243), CleoColor is trackColor: CleoColor:ansi(code: 236), Boolean is showTwoStagePercent: true){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: self:defaultSection:addProgressArea(text: text, stage1Color: stage1Color, stage2Color: stage2Color, trackColor: trackColor, showTwoStagePercent: showTwoStagePercent);
		});
		if({ self:running }, { self:flush(); });
		return sid;
	}

	Function of Int is addImage(CleoImage is image){
		local Int is sid: 0;
		Parallel:syncWith(lock: 77, action: {
			sid: self:defaultSection:addImage(image: image);
		});
		if({ self:running }, { self:flush(); });
		return sid;
	}

	Function is updateText(Int is index, String is text, String is rightText: ''){
		Parallel:syncWith(lock: 77, action: {
			self:defaultSection:updateText(index: index, text: text, rightText: rightText);
		});
		if({ self:running }, { self:flush(); });
	}

	Function is setColor(Int is index, CleoColor is color){
		Parallel:syncWith(lock: 77, action: {
			self:defaultSection:setColor(index: index, color: color);
		});
		if({ self:running }, { self:flush(); });
	}

	Function is resolveSlot(Int is index, String is badge, String is text, CleoColor is color: CleoColor:default(), String is rightText: ''){
		Parallel:syncWith(lock: 77, action: {
			self:defaultSection:resolveSlot(index: index, badge: badge, text: text, color: color, rightText: rightText);
		});
		if({ self:running }, { self:flush(); });
	}

	Function is updateProgress(Int is index, String is text, Float is stage1, Float is stage2, String is rightText: ''){
		Parallel:syncWith(lock: 77, action: {
			self:defaultSection:updateProgress(index: index, text: text, stage1: stage1, stage2: stage2, rightText: rightText);
		});
		if({ self:running }, { self:flush(); });
	}

	Function is updateImage(Int is index, CleoImage is image){
		Parallel:syncWith(lock: 77, action: {
			self:defaultSection:updateImage(index: index, image: image);
		});
		if({ self:running }, { self:flush(); });
	}

	Function is commitLineUnlocked(String is text, CleoColor is color: CleoColor:default()){
		local String is styled: if({ color:isSet() }, { color:fgSeq() . text . Ansi:reset() }, { text });
		self:pendingCommits:add(item: styled);
		self:dirtyRef:set(index: 0, value: true);
	}

	Function is commitSlotUnlocked(CleoSection is section, Int is slotId){
		if({ !section:slotMap:has(key: slotId) }, { return; });
		local Int is termW: Ansi:terminalWidth();
		local Int is totalW: self:width:resolve(termWidth: termW, minCols: self:minWidthCols, maxCols: self:maxWidthCols);
		local Boolean is hasOuter: self:outerBorder != BorderStyle:NONE;
		local Int is innerW: if({ hasOuter }, { totalW - 4 }, { totalW });
		if({ innerW < 8 }, { innerW: 8; });
		local BorderGlyphs is og: BorderGlyphs:forStyle(style: self:outerBorder);
		local String is bc: self:borderColor:fgSeq();
		local String is brst: if({ self:borderColor:isSet() }, { Ansi:reset() }, { '' });
		local CleoSlot is slot: section:slotMap:get(key: slotId);
		local Array of String is rows: slot:renderInnerLines(innerW: innerW, secFg: section:fgColor, secBg: section:bgColor, tick: self:tickCount);
		local Int is ri: 0;
		while({ ri < rows:length() }, {
			local String is rowText: rows:get(index: ri, default: '');
			if(check: { hasOuter }, then: {
				local String is padBg: if({ section:bgColor:isSet() }, { section:bgColor:bgSeq() . ' ' . Ansi:reset() }, { ' ' });
				self:pendingCommits:add(item: bc . og:left . brst . padBg . rowText . padBg . bc . og:right . brst);
			}, else: {
				self:pendingCommits:add(item: rowText);
			});
			ri: ri + 1;
		});
		self:dirtyRef:set(index: 0, value: true);
	}

	Function is commitLine(String is text, CleoColor is color: CleoColor:default()){
		local String is styled: if({ color:isSet() }, { color:fgSeq() . text . Ansi:reset() }, { text });
		Parallel:syncWith(lock: 77, action: {
			self:pendingCommits:add(item: styled);
			self:dirtyRef:set(index: 0, value: true);
		});
		if({ self:running }, { self:flush(); });
	}

	# --- Lifecycle ---

	Function is start(){
		Parallel:syncWith(lock: 77, action: {
			if({ self:running }, { return; });
			self:ttyMode: Ansi:isTty();
			if({ self:ttyMode }, {
				Ansi:enableVirtualTerminal();
				if({ self:altScreen }, {
					Output:consOut(text: Ansi:enterAltScreen() . Ansi:hideCursor());
				}, {
					Output:consOut(text: Ansi:hideCursor());
				});
			});
			self:running: true;
			self:dirtyRef:set(index: 0, value: true);
		});
		self:flush();
		if({ self:ttyMode && self:tickIntervalMs > 0 }, {
			self:timerId: Time:setInterval(ms: self:tickIntervalMs, count: 0, callback: {
				self:tick();
			});
		});
	}

	Function is tick(){
		Parallel:syncWith(lock: 77, action: {
			if({ !self:running }, { return; });
			self:tickCount: self:tickCount + 1;
			self:dirtyRef:set(index: 0, value: true);
			self:flushUnlocked();
		});
	}

	Function is finish(){
		local Int is tid: -1;
		Parallel:syncWith(lock: 77, action: {
			tid: self:timerId;
			self:timerId: -1;
			self:running: false;
			self:dirtyRef:set(index: 0, value: true);
		});
		if({ tid >= 0 }, {
			Time:cancelTimer(timerId: tid);
		});
		if({ self:ttyMode && self:altScreen }, {
			Parallel:syncWith(lock: 77, action: {
				self:prevLines: [];
				self:prevTermW: 0;
				self:prevTermH: 0;
				self:lastFrameW: 0;
				Output:consOut(text: Ansi:exitAltScreen());
			});
		});
		self:flushFinal();
		if({ self:ttyMode }, {
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
		local String is bc: self:borderColor:fgSeq();
		local String is brst: if({ self:borderColor:isSet() }, { Ansi:reset() }, { '' });
		if({ self:outerBorder == BorderStyle:NONE }, {
			return styled;
		});
		return bc . leftB . brst . ' ' . styled . ' ' . bc . rightB . brst;
	}

	Function of Array of String is buildFrameLines(){
		local Int is termW: Ansi:terminalWidth();
		local Int is totalW: self:width:resolve(termWidth: termW, minCols: self:minWidthCols, maxCols: self:maxWidthCols);
		self:lastFrameW: totalW;
		local Boolean is hasOuter: self:outerBorder != BorderStyle:NONE;
		local BorderGlyphs is og: BorderGlyphs:forStyle(style: self:outerBorder);
		local BorderGlyphs is dg: BorderGlyphs:forStyle(style: self:dividerBorder);

		local Int is innerW: if({ hasOuter }, { totalW - 4 }, { totalW });
		if({ innerW < 8 }, { innerW: 8; });

		local Array of String is lines: [];
		if(check: { !self:hasCommittedHeader }, then: {
			if(check: { hasOuter }, then: {
				lines:add(item: self:buildRuleLine(
					leftCap: og:topLeft, fill: og:top, rightCap: og:topRight,
					innerW: innerW, lineColor: self:borderColor,
					titleText: self:title, tFg: self:titleColor, tBg: self:titleBgColor
				));
			}, else: {
				if({ self:title != '' }, {
					lines:add(item: self:buildHeaderRow(
						leftB: '', rightB: '', innerW: innerW,
						titleText: self:title, tFg: self:titleColor, tBg: self:titleBgColor,
						secFg: self:fgColor, secBg: self:bgColor
					));
				});
			});
		});

		local String is bc: self:borderColor:fgSeq();
		local String is brst: if({ self:borderColor:isSet() }, { Ansi:reset() }, { '' });
		local Int is si: 0;
		local Int is visIdx: if({ self:hasCommittedHeader }, { 1 }, { 0 });
		while({ si < self:sections:length() }, {
			local CleoSection is sec: self:sections:get(index: si);
			if({ sec:slots:length() > 0 }, {
				if({ visIdx > 0 && !(self:hasCommittedHeader && si == 0) }, {
					local Boolean is inlineSecTitle: sec:title != '' && sec:titlePlacement == TitlePlacement:INLINE_BORDER;
					if(check: { self:dividerBorder != BorderStyle:NONE }, then: {
						local String is dl: if({ hasOuter }, { og:divLeft }, { dg:divLeft });
						local String is dr: if({ hasOuter }, { og:divRight }, { dg:divRight });
						local String is divTitle: '';
						if({ inlineSecTitle }, { divTitle: sec:title; });
						lines:add(item: self:buildRuleLine(
							leftCap: dl, fill: dg:divMid, rightCap: dr,
							innerW: innerW, lineColor: self:dividerColor,
							titleText: divTitle,
							tFg: sec:titleColor, tBg: sec:titleBgColor
						));
					}, else: {
						if({ inlineSecTitle }, {
							lines:add(item: self:buildHeaderRow(
								leftB: og:left, rightB: og:right, innerW: innerW,
								titleText: sec:title, tFg: sec:titleColor, tBg: sec:titleBgColor,
								secFg: sec:fgColor, secBg: sec:bgColor
							));
						});
					});
				});
				if({ !(self:hasCommittedHeader && si == 0) && sec:title != '' && (sec:titlePlacement == TitlePlacement:HEADER_ROW || (visIdx == 0 && self:title != '')) }, {
					lines:add(item: self:buildHeaderRow(
						leftB: og:left, rightB: og:right, innerW: innerW,
						titleText: sec:title, tFg: sec:titleColor, tBg: sec:titleBgColor,
						secFg: sec:fgColor, secBg: sec:bgColor
					));
				});
				local Int is sli: 0;
				while({ sli < sec:slots:length() }, {
					local CleoSlot is slot: sec:slots:get(index: sli);
					local Array of String is rows: slot:renderInnerLines(innerW: innerW, secFg: sec:fgColor, secBg: sec:bgColor, tick: self:tickCount);
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
			lines:add(item: self:buildRuleLine(
				leftCap: og:bottomLeft, fill: og:bottom, rightCap: og:bottomRight,
				innerW: innerW, lineColor: self:borderColor,
				titleText: '', tFg: CleoColor:default(), tBg: CleoColor:default()
			));
		});
		return lines;
	}

	Function is markDirty(){
		self:dirtyRef:set(index: 0, value: true);
	}

	Function is flushUnlocked(){
		if({ !self:dirtyRef:get(index: 0, default: false) && self:pendingCommits:length() == 0 }, { return; });
		self:dirtyRef:set(index: 0, value: false);

		if({ !self:ttyMode }, {
			local Int is ci: 0;
			while({ ci < self:pendingCommits:length() }, {
				Output:line(text: self:pendingCommits:get(index: ci, default: ''));
				ci: ci + 1;
			});
			self:pendingCommits: [];
			return;
		});

		local Int is prevFrameW: self:lastFrameW;
		local Boolean is pinningNow: false;
		if({ self:pendingCommits:length() > 0 && !self:hasCommittedHeader }, {
			self:hasCommittedHeader: true;
			pinningNow: true;
		});
		local Array of String is nextLines: self:buildFrameLines();
		local Int is prevCount: self:prevLines:length();
		local Int is nextCount: nextLines:length();
		local Int is termW: Ansi:terminalWidth();
		local Int is termH: Ansi:terminalHeight();
		local Int is visCap: if({ termH > 1 }, { termH - 1 }, { 23 });
		local Boolean is resized: (self:prevTermW > 0 && termW != self:prevTermW) || (self:prevTermH > 0 && termH != self:prevTermH);
		local String is out: Ansi:beginSyncUpdate();

		local Int is startLineIdx: 0;
		if({ nextCount > visCap }, {
			startLineIdx: nextCount - visCap;
		});

		if(check: { self:altScreen }, then: {
			out: out . Ansi:moveTo(row: 1, col: 1) . Ansi:eraseToEnd();
		}, else: {
			local Int is prevVisCap: if({ self:prevTermH > 1 }, { self:prevTermH - 1 }, { visCap });
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
		while({ ci < self:pendingCommits:length() }, {
			out: out . Ansi:eraseLine() . self:pendingCommits:get(index: ci, default: '') . "\n";
			ci: ci + 1;
		});
		self:pendingCommits: [];

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
		self:prevLines: nextLines;
		self:prevTermW: termW;
		self:prevTermH: termH;
		Output:consOut(text: out);
	}

	Function is flush(){
		Parallel:syncWith(lock: 77, action: {
			self:flushUnlocked();
		});
	}

	Function is flushFinal(){
		Parallel:syncWith(lock: 77, action: {
			self:dirtyRef:set(index: 0, value: false);
			if({ !self:ttyMode }, {
				local Int is ci: 0;
				while({ ci < self:pendingCommits:length() }, {
					Output:line(text: self:pendingCommits:get(index: ci, default: ''));
					ci: ci + 1;
				});
				self:pendingCommits: [];
				local Array of String is finalLines: self:buildFrameLines();
				local Int is fi: 0;
				while({ fi < finalLines:length() }, {
					Output:line(text: finalLines:get(index: fi, default: ''));
					fi: fi + 1;
				});
				return;
			});
			# Re-render final frame cleanly
			local Int is prevFrameW: self:lastFrameW;
			local Array of String is nextLines: self:buildFrameLines();
			local Int is prevCount: self:prevLines:length();
			local Int is nextCount: nextLines:length();
			local Int is termW: Ansi:terminalWidth();
			local Int is termH: Ansi:terminalHeight();
			local Int is visCap: if({ termH > 1 }, { termH - 1 }, { 23 });
			local Boolean is resized: (self:prevTermW > 0 && termW != self:prevTermW) || (self:prevTermH > 0 && termH != self:prevTermH);
			local String is out: Ansi:beginSyncUpdate();

			local Int is prevVisCap: if({ self:prevTermH > 1 }, { self:prevTermH - 1 }, { visCap });
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
			while({ ci < self:pendingCommits:length() }, {
				out: out . Ansi:eraseLine() . self:pendingCommits:get(index: ci, default: '') . "\n";
				ci: ci + 1;
			});
			self:pendingCommits: [];
			local Int is li: 0;
			while({ li < nextCount }, {
				out: out . Ansi:eraseLine() . nextLines:get(index: li, default: '') . "\n";
				li: li + 1;
			});
			out: out . Ansi:endSyncUpdate();
			self:prevLines: nextLines;
			self:prevTermW: termW;
			self:prevTermH: termH;
			Output:consOut(text: out);
		});
	}
}
