#! Package theosynth:view
#! Main TheoSynth frame: 3-octave piano keyboard in the main panel and Quit / Instrument / About in the bottom bar.

Class of Frame is SynthFrame{
	replace [String] is namespace: ['theosynth', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theosynth', 'util', SynthStrings],
		['theosynth', 'vm', SynthViewModel],
		['theosynth', 'view', [PianoBoard, AboutDialog]]
	];

	SynthViewModel is vm: SynthViewModel();
	FocusTarget is quitFocus: FocusTarget();
	FocusTarget is instrumentFocus: FocusTarget(initial: true);
	FocusTarget is aboutFocus: FocusTarget();
	FocusTarget is aboutCloseFocus: FocusTarget(initial: true);

	Array of Dropdown is instrumentPickers: Array();
	Array of Button is aboutButtons: Array();
	Array of Overlay is aboutOverlays: Array();

	replace Function is init(SynthViewModel is vm: SynthViewModel()){
		:vm: vm;
		vm:onStateChanged: {
			invalidate();
		};
		vm:onAboutChanged: {
			syncAboutOverlay();
		};
		instrumentPickers: Array([
			Dropdown(
				host: :,
				options: SynthStrings:instrumentOptions(),
				selected: SynthStrings:WAVE_SINE,
				focusTarget: instrumentFocus,
				onSelect: local Function(String is chosen){
					:vm:selectInstrument(name: chosen);
				}
			)
		]);
		aboutButtons: Array([
			Button(
				label: SynthStrings:ACTION_ABOUT,
				focusTarget: aboutFocus,
				onClick: { :vm:openAbout(); }
			)
		]);
		local Overlay is aOv: Overlay(
			closeOnEsc: true,
			closeOnBackdrop: true,
			onClose: { :vm:closeAbout(); },
			content: AboutDialog:build(closeFocus: aboutCloseFocus, onClose: { :vm:closeAbout(); })
		);
		aboutOverlays: Array([aOv]);
		addOverlay(overlay: aOv);
	}

	local Function is syncAboutOverlay(){
		if({ aboutOverlays:length() == 0 || aboutButtons:length() == 0 }, { return; });
		local Overlay is aOv: aboutOverlays:get(index: 0);
		if({ vm:aboutOpen }, {
			if({ !aOv:open }, {
				showOverlay(overlay: aOv, anchor: aboutButtons:get(index: 0));
			});
		}, {
			if({ aOv:open }, {
				closeOverlay(overlay: aOv);
			});
		});
	}

	replace Function of Widget is ui(){
		local Widget is bottomBar: Panel(
			border: true,
			padX: 1,
			padY: 0,
			child: Row(
				gap: 1,
				arrowFocus: true,
				children: Array([
					Button(
						label: SynthStrings:ACTION_QUIT,
						focusTarget: quitFocus,
						onClick: { :vm:quit(); }
					),
					Spacer(weight: 1.0),
					TextLine(value: SynthStrings:LABEL_INSTRUMENT),
					instrumentPickers:get(index: 0),
					Spacer(weight: 1.0),
					aboutButtons:get(index: 0)
				])
			)
		);
		return Col(
			gap: 0,
			children: Array([
				PianoBoard(vm: vm),
				bottomBar
			])
		);
	}

	replace Function of Boolean is wantsKeyRelease(){ true }

	replace Function of Boolean is onTick(){
		return vm:tickDecay();
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		return vm:handleKeyAction(
			key: event:key,
			ctrl: event:ctrl,
			isPress: event:isPress(),
			isRepeat: event:isRepeat(),
			isRelease: event:isRelease()
		);
	}
}
