#! Package base:theo
#! Styled container with foreground/background colors, border, padding, and optional scrolling.

Class of Widget is Panel{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, TheoColor, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	TheoColor is foreground: TheoColor:none();
	TheoColor is background: TheoColor:none();
	Boolean is border: false;
	TheoColor is borderColor: TheoColor:none();
	TheoColor is focusBorderColor: TheoColor:none();
	Boolean is rounded: true;
	Int is padding: 0;
	Int is padX: -1;
	Int is padY: -1;
	Boolean is scrollable: false;
	String is verticalScrollbar: 'always';
	String is horizontalScrollbar: 'auto';
	String is scrollTrackChar: '▐';
	String is scrollThumbChar: '▐';
	String is scrollHTrackChar: '';
	String is scrollHThumbChar: '';
	TheoColor is scrollTrackColor: TheoColor:none();
	TheoColor is scrollThumbColor: TheoColor:none();
	String is topTitle: '';
	String is topTitleAlign: 'center';
	String is bottomTitle: '';
	String is bottomTitleAlign: 'center';
	String is leftTitle: '';
	String is leftTitleAlign: 'center';
	String is rightTitle: '';
	String is rightTitleAlign: 'center';
	TheoColor is titleFg: TheoColor:none();
	TheoColor is titleBg: TheoColor:none();
	Widget is child;

	replace Function is init(
		Widget is child: Widget(),
		TheoColor is foreground: TheoColor:none(),
		TheoColor is background: TheoColor:none(),
		Boolean is border: false,
		TheoColor is borderColor: TheoColor:none(),
		TheoColor is focusBorderColor: TheoColor:none(),
		Boolean is rounded: true,
		Int is padding: 0,
		Int is padX: -1,
		Int is padY: -1,
		Boolean is scrollable: false,
		String is verticalScrollbar: 'always',
		String is horizontalScrollbar: 'auto',
		String is scrollTrackChar: '▐',
		String is scrollThumbChar: '▐',
		String is scrollHTrackChar: '',
		String is scrollHThumbChar: '',
		TheoColor is scrollTrackColor: TheoColor:none(),
		TheoColor is scrollThumbColor: TheoColor:none(),
		String is topTitle: '',
		String is topTitleAlign: 'center',
		String is bottomTitle: '',
		String is bottomTitleAlign: 'center',
		String is leftTitle: '',
		String is leftTitleAlign: 'center',
		String is rightTitle: '',
		String is rightTitleAlign: 'center',
		TheoColor is titleFg: TheoColor:none(),
		TheoColor is titleBg: TheoColor:none()
	){
		:child: child;
		:foreground: foreground;
		:background: background;
		:border: border;
		:borderColor: borderColor;
		:focusBorderColor: focusBorderColor;
		:rounded: rounded;
		:padding: padding;
		:padX: padX;
		:padY: padY;
		:scrollable: scrollable;
		:verticalScrollbar: verticalScrollbar;
		:horizontalScrollbar: horizontalScrollbar;
		:scrollTrackChar: scrollTrackChar;
		:scrollThumbChar: scrollThumbChar;
		:scrollHTrackChar: scrollHTrackChar;
		:scrollHThumbChar: scrollHThumbChar;
		:scrollTrackColor: scrollTrackColor;
		:scrollThumbColor: scrollThumbColor;
		:topTitle: topTitle;
		:topTitleAlign: topTitleAlign;
		:bottomTitle: bottomTitle;
		:bottomTitleAlign: bottomTitleAlign;
		:leftTitle: leftTitle;
		:leftTitleAlign: leftTitleAlign;
		:rightTitle: rightTitle;
		:rightTitleAlign: rightTitleAlign;
		:titleFg: titleFg;
		:titleBg: titleBg;
	}

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		child:applyTheme(theme: theme);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		child:bindDirty(cb: cb);
	}

	local Function of Int is innerPadLeft(){
		local Int is bPad: if({ border || leftTitle != '' }, { 1 }, { 0 });
		return bPad + if({ padX >= 0 }, { padX }, { padding });
	}

	local Function of Int is innerPadRight(){
		local Int is bPad: if({ border || rightTitle != '' }, { 1 }, { 0 });
		return bPad + if({ padX >= 0 }, { padX }, { padding });
	}

	local Function of Int is innerPadTop(){
		local Int is bPad: if({ border || topTitle != '' }, { 1 }, { 0 });
		return bPad + if({ padY >= 0 }, { padY }, { padding });
	}

	local Function of Int is innerPadBottom(){
		local Int is bPad: if({ border || bottomTitle != '' }, { 1 }, { 0 });
		return bPad + if({ padY >= 0 }, { padY }, { padding });
	}

	replace Function of Int is measureWidth(Int is maxW){
		local Int is padL: innerPadLeft();
		local Int is padR: innerPadRight();
		local Int is avail: maxW - padL - padR;
		if({ avail < 0 }, { avail: 0; });
		local Int is w: child:measureWidth(maxW: avail) + padL + padR;
		if({ w > maxW }, { return maxW; });
		return w;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		local Int is padL: innerPadLeft();
		local Int is padR: innerPadRight();
		local Int is padT: innerPadTop();
		local Int is padB: innerPadBottom();
		local Int is availW: maxW - padL - padR;
		local Int is availH: maxH - padT - padB;
		if({ availW < 0 }, { availW: 0; });
		if({ availH < 0 }, { availH: 0; });
		local Int is h: child:measureHeight(maxW: availW, maxH: availH) + padT + padB;
		if({ h > maxH }, { return maxH; });
		return h;
	}

	local Function of Boolean is showVScroll(Int is innerW, Int is innerH){
		if({ !scrollable || verticalScrollbar == 'never' || innerW <= 1 || innerH <= 0 }, {
			return false;
		});
		if({ verticalScrollbar == 'always' }, { return true; });
		return child:scrollContentH() > innerH;
	}

	local Function of Boolean is showHScroll(Int is innerW, Int is innerH, Boolean is hasV){
		local Int is availW: innerW - if({ hasV }, { 1 }, { 0 });
		if({ !scrollable || horizontalScrollbar == 'never' || innerH <= 1 || availW <= 0 }, {
			return false;
		});
		if({ horizontalScrollbar == 'always' }, { return true; });
		return child:scrollContentW() > availW;
	}

	local Function is paintScrollbar(
		TheoBuffer is buf,
		Boolean is vertical,
		Int is startX,
		Int is startY,
		Int is trackLen,
		Int is offset,
		Int is contentLen,
		Int is viewportLen,
		String is trackChar,
		String is thumbChar,
		TheoColor is trackColor,
		TheoColor is thumbColor
	){
		if({ trackLen <= 0 }, { return; });
		local Int is thumbLen: trackLen;
		local Int is thumbStart: 0;
		if({ contentLen > viewportLen && viewportLen > 0 }, {
			thumbLen: (viewportLen * trackLen) / contentLen;
			if({ thumbLen < 1 }, { thumbLen: 1; });
			if({ thumbLen > trackLen }, { thumbLen: trackLen; });
			local Int is maxOffset: contentLen - viewportLen;
			local Int is maxStart: trackLen - thumbLen;
			if({ maxOffset > 0 && maxStart > 0 }, {
				local Int is clampedOff: offset;
				if({ clampedOff < 0 }, { clampedOff: 0; });
				if({ clampedOff > maxOffset }, { clampedOff: maxOffset; });
				thumbStart: (clampedOff * maxStart) / maxOffset;
			});
		});
		local Int is i: 0;
		while({ i < trackLen }, {
			local Boolean is isThumb: i >= thumbStart && i < thumbStart + thumbLen;
			local String is ch: if({ isThumb }, { thumbChar }, { trackChar });
			local TheoColor is fg: if({ isThumb }, { thumbColor }, { trackColor });
			local Int is cx: if({ vertical }, { startX }, { startX + i });
			local Int is cy: if({ vertical }, { startY + i }, { startY });
			buf:setCell(x: cx, y: cy, ch: ch, fg: fg, bg: background);
			i: i + 1;
		});
	}

	local Function is paintTitleHorizontal(TheoBuffer is buf, Int is y, String is title, String is align, TheoColor is fg, TheoColor is bg){
		if({ title == '' }, { return; });
		local Int is margin: if({ border }, { 1 }, { 0 });
		local Int is spanX: boxX + margin;
		local Int is spanW: boxW - (margin * 2);
		if({ spanW <= 0 }, { return; });
		local String is shown: if({ title:runeCount() > spanW }, { title:sliceRunes(start: 0, end: spanW) }, { title });
		local Int is tLen: shown:runeCount();
		local Int is startX: spanX + (spanW - tLen) / 2;
		if({ align == 'left' }, { startX: spanX; });
		if({ align == 'right' }, { startX: spanX + spanW - tLen; });
		if({ bg:isSet() }, {
			buf:fillRect(x: spanX, y: y, w: spanW, h: 1, fg: fg, bg: bg);
		});
		buf:drawText(x: startX, y: y, text: shown, fg: fg, bg: bg, bold: true);
	}

	local Function is paintTitleVertical(TheoBuffer is buf, Int is x, String is title, String is align, TheoColor is fg, TheoColor is bg){
		if({ title == '' }, { return; });
		local Int is margin: if({ border }, { 1 }, { 0 });
		local Int is spanY: boxY + margin;
		local Int is spanH: boxH - (margin * 2);
		if({ spanH <= 0 }, { return; });
		local String is shown: if({ title:runeCount() > spanH }, { title:sliceRunes(start: 0, end: spanH) }, { title });
		local Int is tLen: shown:runeCount();
		local Int is startY: spanY + (spanH - tLen) / 2;
		if({ align == 'left' }, { startY: spanY; });
		if({ align == 'right' }, { startY: spanY + spanH - tLen; });
		if({ bg:isSet() }, {
			buf:fillRect(x: x, y: spanY, w: 1, h: spanH, fg: fg, bg: bg);
		});
		local Int is i: 0;
		while({ i < tLen }, {
			buf:setCell(x: x, y: startY + i, ch: shown:runeAt(runeIndex: i, default: ' '), fg: fg, bg: bg, bold: true);
			i: i + 1;
		});
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		local Int is pl: innerPadLeft();
		local Int is pr: innerPadRight();
		local Int is pt: innerPadTop();
		local Int is pb: innerPadBottom();
		local Int is innerW: w - pl - pr;
		local Int is innerH: h - pt - pb;
		if({ innerW < 0 }, { innerW: 0; });
		if({ innerH < 0 }, { innerH: 0; });
		local Boolean is hasV: showVScroll(innerW: innerW, innerH: innerH);
		local Boolean is hasH: showHScroll(innerW: innerW, innerH: innerH, hasV: hasV);
		local Int is childW: innerW - if({ hasV }, { 1 }, { 0 });
		local Int is childH: innerH - if({ hasH }, { 1 }, { 0 });
		if({ childW < 0 }, { childW: 0; });
		if({ childH < 0 }, { childH: 0; });
		child:layout(x: x + pl, y: y + pt, w: childW, h: childH);
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		if({ background:isSet() || foreground:isSet() }, {
			buf:fillRect(x: boxX, y: boxY, w: boxW, h: boxH, fg: foreground, bg: background);
		});
		if({ border }, {
			local Array of FocusTarget is fts: Array();
			local Array of Widget is fws: Array();
			child:collectFocus(targets: fts, owners: fws);
			local Boolean is hasFocused: false;
			fts:each(action: local Function(FocusTarget is ft){
				if({ ft:focused }, { hasFocused: true; });
			});
			local TheoColor is effBorder: if({ borderColor:isSet() }, { borderColor }, { activeTheme:borderColor });
			local TheoColor is effFocusBorder: if({ focusBorderColor:isSet() }, { focusBorderColor }, { activeTheme:focusBorderColor });
			local TheoColor is useBorder: if({ hasFocused && effFocusBorder:isSet() }, { effFocusBorder }, { effBorder });
			buf:drawBox(x: boxX, y: boxY, w: boxW, h: boxH, borderColor: useBorder, bg: background, rounded: rounded);
		});
		local TheoColor is effTitleFg: if({ titleFg:isSet() }, { titleFg }, { activeTheme:titleColor });
		local TheoColor is effTitleBg: if({ titleBg:isSet() }, { titleBg }, { background });
		paintTitleHorizontal(buf: buf, y: boxY, title: topTitle, align: topTitleAlign, fg: effTitleFg, bg: effTitleBg);
		paintTitleHorizontal(buf: buf, y: boxY + boxH - 1, title: bottomTitle, align: bottomTitleAlign, fg: effTitleFg, bg: effTitleBg);
		paintTitleVertical(buf: buf, x: boxX, title: leftTitle, align: leftTitleAlign, fg: effTitleFg, bg: effTitleBg);
		paintTitleVertical(buf: buf, x: boxX + boxW - 1, title: rightTitle, align: rightTitleAlign, fg: effTitleFg, bg: effTitleBg);
		local Int is pl: innerPadLeft();
		local Int is pr: innerPadRight();
		local Int is pt: innerPadTop();
		local Int is pb: innerPadBottom();
		local Int is innerW: boxW - pl - pr;
		local Int is innerH: boxH - pt - pb;
		if({ innerW > 0 && innerH > 0 }, {
			local Boolean is hasV: showVScroll(innerW: innerW, innerH: innerH);
			local Boolean is hasH: showHScroll(innerW: innerW, innerH: innerH, hasV: hasV);
			local Int is childW: innerW - if({ hasV }, { 1 }, { 0 });
			local Int is childH: innerH - if({ hasH }, { 1 }, { 0 });
			if({ childW > 0 && childH > 0 }, {
				buf:setClip(x: boxX + pl, y: boxY + pt, w: childW, h: childH);
				child:paint(buf: buf, renderer: renderer);
				buf:clearClip();
			});
			if({ hasV || hasH }, {
				local TheoColor is effTrack: if({ scrollTrackColor:isSet() }, { scrollTrackColor }, { activeTheme:scrollTrackColor });
				local TheoColor is effThumb: if({ scrollThumbColor:isSet() }, { scrollThumbColor }, { activeTheme:scrollThumbColor });
				buf:setClip(x: boxX + pl, y: boxY + pt, w: innerW, h: innerH);
				if({ hasV }, {
					paintScrollbar(
						buf: buf,
						vertical: true,
						startX: boxX + pl + childW,
						startY: boxY + pt,
						trackLen: childH,
						offset: child:scrollOffsetY(),
						contentLen: child:scrollContentH(),
						viewportLen: child:scrollViewportH(),
						trackChar: scrollTrackChar,
						thumbChar: scrollThumbChar,
						trackColor: effTrack,
						thumbColor: effThumb
					);
				});
				if({ hasH }, {
					local String is hTrack: if({ scrollHTrackChar != '' }, { scrollHTrackChar }, { if({ scrollTrackChar == '▐' }, { '▄' }, { scrollTrackChar }) });
					local String is hThumb: if({ scrollHThumbChar != '' }, { scrollHThumbChar }, { if({ scrollThumbChar == '▐' }, { '▄' }, { scrollThumbChar }) });
					paintScrollbar(
						buf: buf,
						vertical: false,
						startX: boxX + pl,
						startY: boxY + pt + childH,
						trackLen: childW,
						offset: child:scrollOffsetX(),
						contentLen: child:scrollContentW(),
						viewportLen: child:scrollViewportW(),
						trackChar: hTrack,
						thumbChar: hThumb,
						trackColor: effTrack,
						thumbColor: effThumb
					);
				});
				buf:clearClip();
			});
		});
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		return child:handleKey(event: event);
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		return child:handleMouse(event: event);
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		child:collectFocus(targets: targets, owners: owners);
	}

	replace Function is dispose(){
		disposeBindings();
		child:dispose();
	}
}
