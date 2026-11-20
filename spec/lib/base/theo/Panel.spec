#! Package base:theo
#! Styled container with foreground/background colors, border, padding, and optional scrolling.

Class of Widget is Panel{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
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
		TheoColor is scrollThumbColor: TheoColor:none()
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
	}

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		child:applyTheme(theme: theme);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: [cb];
		child:bindDirty(cb: cb);
	}

	local Function of Int is innerPadX(){
		local Int is bPad: if({ border }, { 1 }, { 0 });
		return bPad + if({ padX >= 0 }, { padX }, { padding });
	}

	local Function of Int is innerPadY(){
		local Int is bPad: if({ border }, { 1 }, { 0 });
		return bPad + if({ padY >= 0 }, { padY }, { padding });
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

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		local Int is px: innerPadX();
		local Int is py: innerPadY();
		local Int is innerW: w - (px * 2);
		local Int is innerH: h - (py * 2);
		if({ innerW < 0 }, { innerW: 0; });
		if({ innerH < 0 }, { innerH: 0; });
		local Boolean is hasV: showVScroll(innerW: innerW, innerH: innerH);
		local Boolean is hasH: showHScroll(innerW: innerW, innerH: innerH, hasV: hasV);
		local Int is childW: innerW - if({ hasV }, { 1 }, { 0 });
		local Int is childH: innerH - if({ hasH }, { 1 }, { 0 });
		if({ childW < 0 }, { childW: 0; });
		if({ childH < 0 }, { childH: 0; });
		child:layout(x: x + px, y: y + py, w: childW, h: childH);
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		if({ background:isSet() || foreground:isSet() }, {
			buf:fillRect(x: boxX, y: boxY, w: boxW, h: boxH, fg: foreground, bg: background);
		});
		if({ border }, {
			local Array of FocusTarget is fts: [];
			local Array of Widget is fws: [];
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
		local Int is px: innerPadX();
		local Int is py: innerPadY();
		local Int is innerW: boxW - (px * 2);
		local Int is innerH: boxH - (py * 2);
		if({ innerW > 0 && innerH > 0 }, {
			local Boolean is hasV: showVScroll(innerW: innerW, innerH: innerH);
			local Boolean is hasH: showHScroll(innerW: innerW, innerH: innerH, hasV: hasV);
			local Int is childW: innerW - if({ hasV }, { 1 }, { 0 });
			local Int is childH: innerH - if({ hasH }, { 1 }, { 0 });
			if({ childW > 0 && childH > 0 }, {
				buf:setClip(x: boxX + px, y: boxY + py, w: childW, h: childH);
				child:paint(buf: buf, renderer: renderer);
				buf:clearClip();
			});
			if({ hasV || hasH }, {
				local TheoColor is effTrack: if({ scrollTrackColor:isSet() }, { scrollTrackColor }, { activeTheme:scrollTrackColor });
				local TheoColor is effThumb: if({ scrollThumbColor:isSet() }, { scrollThumbColor }, { activeTheme:scrollThumbColor });
				buf:setClip(x: boxX + px, y: boxY + py, w: innerW, h: innerH);
				if({ hasV }, {
					paintScrollbar(
						buf: buf,
						vertical: true,
						startX: boxX + px + childW,
						startY: boxY + py,
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
						startX: boxX + px,
						startY: boxY + py + childH,
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
		child:dispose();
	}
}
