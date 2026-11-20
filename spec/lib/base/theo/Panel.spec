#! Package base:theo
#! Styled container with foreground/background colors, border, padding, and optional scrolling.

Class of Widget is Panel{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [Widget, TheoColor, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, FocusTarget]],
		['base', 'sys', as Conditional()]
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
		Boolean is scrollable: false
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
	}

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		child:applyTheme(theme: theme);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: [cb];
		child:bindDirty(cb: cb);
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		local Int is bPad: if({ border }, { 1 }, { 0 });
		local Int is px: bPad + if({ padX >= 0 }, { padX }, { padding });
		local Int is py: bPad + if({ padY >= 0 }, { padY }, { padding });
		local Int is innerW: w - (px * 2);
		local Int is innerH: h - (py * 2);
		if({ innerW < 0 }, { innerW: 0; });
		if({ innerH < 0 }, { innerH: 0; });
		child:layout(x: x + px, y: y + py, w: innerW, h: innerH);
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
		local Int is bPad: if({ border }, { 1 }, { 0 });
		local Int is px: bPad + if({ padX >= 0 }, { padX }, { padding });
		local Int is py: bPad + if({ padY >= 0 }, { padY }, { padding });
		local Int is innerW: boxW - (px * 2);
		local Int is innerH: boxH - (py * 2);
		if({ innerW > 0 && innerH > 0 }, {
			buf:setClip(x: boxX + px, y: boxY + py, w: innerW, h: innerH);
			child:paint(buf: buf, renderer: renderer);
			buf:clearClip();
		});
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		return child:handleKey(event: event);
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		child:collectFocus(targets: targets, owners: owners);
	}

	replace Function is dispose(){
		child:dispose();
	}
}
