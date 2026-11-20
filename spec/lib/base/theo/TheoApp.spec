#! Package base:theo
#! Top-level Theo application host managing alternate-screen lifecycle, raw input, and rendering.

Class is TheoApp{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [TheoScreen, Frame, Widget, FocusTarget, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, KeyReader]],
		['base', 'sys', [as Ansi(), as Input(), as Conditional(), as Loops()]]
	];

	Boolean is running: false;
	Boolean is dirty: true;
	TheoTheme is theme: TheoTheme();

	replace Function is init(TheoTheme is theme: TheoTheme()){
		:theme: theme;
		:running: false;
		:dirty: true;
	}

	Function is quit(){
		:running: false;
	}

	local Function is syncFocus(Frame is frame){
		local Array of FocusTarget is targets: [];
		local Array of Widget is owners: [];
		frame:collectFocus(targets: targets, owners: owners);
		if({ targets:length() == 0 }, { return; });

		local Int is focusedCount: 0;
		targets:each(action: local Function(FocusTarget is ft){
			if({ ft:focused }, { focusedCount: focusedCount + 1; });
			ft:bindOwner(handler: local Function(FocusTarget is chosen){
				targets:each(action: local Function(FocusTarget is other){
					if({ other != chosen }, {
						other:focused: false;
					});
				});
				chosen:focused: true;
				:dirty: true;
			});
		});
		if({ focusedCount == 0 }, {
			local Boolean is pickedInitial: false;
			targets:each(action: local Function(FocusTarget is ft){
				if({ !pickedInitial && ft:initial }, {
					ft:focused: true;
					pickedInitial: true;
				});
			});
			if({ !pickedInitial }, {
				targets:get(index: 0):focused: true;
			});
		});
	}

	local Function is cycleFocus(Frame is frame, Boolean is reverse){
		local Array of FocusTarget is targets: [];
		local Array of Widget is owners: [];
		frame:collectFocus(targets: targets, owners: owners);
		local Int is n: targets:length();
		if({ n <= 1 }, { return; });
		local Int is cur: 0;
		local Int is i: 0;
		while({ i < n }, {
			if({ targets:get(index: i):focused }, {
				cur: i;
			});
			i: i + 1;
		});
		local Int is next: if({ reverse }, { (cur - 1 + n) % n }, { (cur + 1) % n });
		targets:get(index: next):requestFocus();
	}

	Function is run(TheoScreen is screen){
		:running: true;
		:dirty: true;
		screen:bindDirty(cb: {
			:dirty: true;
		});

		local TheoRenderer is renderer: TheoRenderer();
		local KeyReader is reader: KeyReader();
		local Int is w: terminalWidth();
		local Int is h: terminalHeight();
		if({ w <= 0 }, { w: 80; });
		if({ h <= 0 }, { h: 24; });
		local TheoBuffer is buf: TheoBuffer(width: w, height: h);

		renderer:enterAltScreenMode();
		setRawMode(enabled: true);

		while({ running }, {
			local Int is nw: terminalWidth();
			local Int is nh: terminalHeight();
			if({ nw <= 0 }, { nw: 80; });
			if({ nh <= 0 }, { nh: 24; });
			if({ nw != w || nh != h }, {
				w: nw;
				h: nh;
				buf:resize(width: w, height: h);
				:dirty: true;
			});

			local Frame is activeFrame: screen:current();
			if({ dirty }, {
				:dirty: false;
				buf:clear();
				renderer:setCursor(visible: false);
				activeFrame:applyTheme(theme: theme);
				activeFrame:layout(x: 0, y: 0, w: w, h: h);
				syncFocus(frame: activeFrame);
				activeFrame:paint(buf: buf, renderer: renderer);
				renderer:render(buffer: buf);
			});

			local KeyEvent is ev: reader:pollKey(timeoutMs: 16);
			if({ !ev:isNone() }, {
				if({ ev:isMouse() }, {
					local Boolean is mHandled: activeFrame:handleMouse(event: reader:lastMouse);
					if({ mHandled }, {
						syncFocus(frame: screen:current());
						:dirty: true;
					});
				}, {
					local Boolean is handled: activeFrame:handleKey(event: ev);
					if({ !handled }, {
						if({ ev:isTab() }, {
							cycleFocus(frame: activeFrame, reverse: false);
							handled: true;
						});
						if({ ev:isBackTab() }, {
							cycleFocus(frame: activeFrame, reverse: true);
							handled: true;
						});
					});
					if({ handled }, {
						syncFocus(frame: screen:current());
						:dirty: true;
					});
				});
			});
		});

		screen:current():onExit();
		setRawMode(enabled: false);
		renderer:exitAltScreenMode();
	}
}
