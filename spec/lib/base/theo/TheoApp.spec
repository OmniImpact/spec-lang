#! Package base:theo
#! Top-level Theo application host managing alternate-screen lifecycle, raw input, and rendering.

Class is TheoApp{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [TheoScreen, Frame, Widget, FocusTarget, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, KeyAction, MouseEvent, KeyReader]],
		['base', 'struct', Map],
		['base', 'sys', [Process, as Ansi(), as Input(), as Conditional(), as Loops()]]
	];

	Boolean is running: false;
	Boolean is dirty: true;
	TheoTheme is theme: TheoTheme();
	Map of String to Int is relSlotByKey: Map();
	[KeyEvent] is pendingRelEvents: [];
	[Int] is pendingRelTicks: [];
	[Int] is lastRelMs: [];

	replace Function is init(TheoTheme is theme: TheoTheme()){
		:theme: theme;
		:running: false;
		:dirty: true;
	}

	Function is quit(){
		:running: false;
	}

	local Function is syncFocus(Frame is frame){
		local Array of FocusTarget is targets: Array();
		local Array of Widget is owners: Array();
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
		local Array of FocusTarget is targets: Array();
		local Array of Widget is owners: Array();
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

	## Paints [screen] into [buf] if dirty, clearing the dirty flag.
	Function is paintIfDirty(TheoScreen is screen, TheoBuffer is buf, TheoRenderer is renderer){
		if({ !dirty }, { return; });
		:dirty: false;
		buf:clear();
		renderer:setCursor(visible: false);
		local Frame is activeFrame: screen:current();
		activeFrame:applyTheme(theme: theme);
		activeFrame:layout(x: 0, y: 0, w: buf:width, h: buf:height);
		syncFocus(frame: activeFrame);
		activeFrame:paint(buf: buf, renderer: renderer);
	}

	## Dispatches a single key or mouse event to [screen] and marks dirty if handled.
	Function is dispatchKeyEvent(TheoScreen is screen, KeyEvent is ev, MouseEvent is mouse){
		if({ ev:isNone() }, { return; });
		local Frame is activeFrame: screen:current();
		if({ ev:isMouse() }, {
			local Boolean is mHandled: activeFrame:handleMouse(event: mouse);
			if({ mHandled }, {
				syncFocus(frame: screen:current());
				:dirty: true;
			});
			return;
		});
		if({ ev:isRelease() && !activeFrame:wantsKeyRelease() }, {
			return;
		});
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
	}

	local Function of String is keySig(KeyEvent is ev){
		local String is c: if({ ev:ctrl }, { '1' }, { '0' });
		local String is a: if({ ev:alt }, { '1' }, { '0' });
		return "{{ev:kind:value()}}:{{ev:key}}:{{c}}:{{a}}";
	}

	local Function is flushPendingReleases(TheoScreen is screen, Boolean is forceAll){
		local MouseEvent is emptyMouse: MouseEvent();
		local Int is i: 0;
		while({ i < pendingRelTicks:length() }, {
			local Int is t: pendingRelTicks:get(index: i);
			if({ t > 0 }, {
				local Int is nextT: if({ forceAll }, { 0 }, { t - 1 });
				pendingRelTicks:set(index: i, item: nextT);
				if({ nextT == 0 }, {
					dispatchKeyEvent(screen: screen, ev: pendingRelEvents:get(index: i), mouse: emptyMouse);
				});
			});
			i: i + 1;
		});
	}

	local Function is dispatchNormalizedEvent(TheoScreen is screen, KeyEvent is ev, MouseEvent is mouse){
		if({ ev:isNone() }, { return; });
		if({ ev:isMouse() }, {
			dispatchKeyEvent(screen: screen, ev: ev, mouse: mouse);
			return;
		});
		local Frame is activeFrame: screen:current();
		if({ !activeFrame:wantsKeyRelease() }, {
			if({ ev:isRelease() }, { return; });
			dispatchKeyEvent(screen: screen, ev: ev, mouse: mouse);
			return;
		});
		local String is sig: keySig(ev: ev);
		if({ ev:isRelease() }, {
			local Int is nowMs: Process():clockMs();
			if({ relSlotByKey:has(key: sig) }, {
				local Int is slot: relSlotByKey:get(key: sig, default: 0);
				pendingRelEvents:set(index: slot, item: ev);
				pendingRelTicks:set(index: slot, item: 2);
				lastRelMs:set(index: slot, item: nowMs);
			}, {
				local Int is newSlot: pendingRelEvents:length();
				relSlotByKey:set(key: sig, value: newSlot);
				pendingRelEvents:push(item: ev);
				pendingRelTicks:push(item: 2);
				lastRelMs:push(item: nowMs);
			});
			return;
		});
		if({ ev:isPress() && relSlotByKey:has(key: sig) }, {
			local Int is slot2: relSlotByKey:get(key: sig, default: 0);
			local Int is nowMs2: Process():clockMs();
			local Int is pr: pendingRelTicks:get(index: slot2);
			local Int is lr: lastRelMs:get(index: slot2);
			if({ pr > 0 || (lr > 0 && (nowMs2 - lr) < 15) }, {
				# Coalesce synthetic RELEASE+PRESS auto-repeat into a single REPEAT event.
				pendingRelTicks:set(index: slot2, item: 0);
				local KeyEvent is repEv: KeyEvent(kind: ev:kind, key: ev:key, ctrl: ev:ctrl, alt: ev:alt, action: KeyAction:REPEAT);
				dispatchKeyEvent(screen: screen, ev: repEv, mouse: mouse);
				return;
			});
		});
		if({ ev:isRepeat() && relSlotByKey:has(key: sig) }, {
			pendingRelTicks:set(index: relSlotByKey:get(key: sig, default: 0), item: 0);
		});
		dispatchKeyEvent(screen: screen, ev: ev, mouse: mouse);
	}

	## Headless test runner: steps [screen] through [keys] without a TTY and returns the final [TheoBuffer].
	Function of TheoBuffer is runHeadless(TheoScreen is screen, [KeyEvent] is keys, Int is width: 80, Int is height: 24){
		:running: true;
		:dirty: true;
		:relSlotByKey: Map();
		:pendingRelEvents: [];
		:pendingRelTicks: [];
		:lastRelMs: [];
		screen:bindDirty(cb: {
			:dirty: true;
		});
		local TheoRenderer is renderer: TheoRenderer();
		local TheoBuffer is buf: TheoBuffer(width: width, height: height);
		local MouseEvent is emptyMouse: MouseEvent();
		paintIfDirty(screen: screen, buf: buf, renderer: renderer);

		local Int is ki: 0;
		while({ running && ki < keys:length() }, {
			dispatchNormalizedEvent(screen: screen, ev: keys:get(index: ki), mouse: emptyMouse);
			flushPendingReleases(screen: screen, forceAll: false);
			if({ screen:current():onTick() }, {
				:dirty: true;
			});
			paintIfDirty(screen: screen, buf: buf, renderer: renderer);
			ki: ki + 1;
		});
		flushPendingReleases(screen: screen, forceAll: true);
		paintIfDirty(screen: screen, buf: buf, renderer: renderer);
		screen:current():onExit();
		:running: false;
		return buf;
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

			if({ dirty }, {
				paintIfDirty(screen: screen, buf: buf, renderer: renderer);
				renderer:render(buffer: buf);
			});

			local [KeyEvent] is batch: reader:pollBatch(timeoutMs: 16);
			local Int is bi: 0;
			while({ running && bi < batch:length() }, {
				dispatchNormalizedEvent(screen: screen, ev: batch:get(index: bi), mouse: reader:lastMouse);
				bi: bi + 1;
			});
			flushPendingReleases(screen: screen, forceAll: false);
			if({ screen:current():onTick() }, {
				:dirty: true;
			});
		});

		screen:current():onExit();
		setRawMode(enabled: false);
		renderer:exitAltScreenMode();
	}
}
