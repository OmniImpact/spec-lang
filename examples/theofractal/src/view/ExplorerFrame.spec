#! Package theofractal:view
#! Pure view frame bound to [ExplorerViewModel]: empty main canvas, bottom control bar, and Help overlay sync.

Class of Frame is ExplorerFrame{
	replace [String] is namespace: ['theofractal', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theofractal', 'util', FractalStrings],
		['theofractal', 'vm', ExplorerViewModel],
		['theofractal', 'view', [FractalCanvas, HelpDialog]]
	];

	ExplorerViewModel is vm: ExplorerViewModel();
	FocusTarget is quitFocus: FocusTarget();
	FocusTarget is fractalFocus: FocusTarget(initial: true);
	FocusTarget is themeFocus: FocusTarget();
	FocusTarget is helpFocus: FocusTarget();
	FocusTarget is helpCloseFocus: FocusTarget(initial: true);

	Array of Dropdown is fractalPickers: Array();
	Array of Dropdown is themePickers: Array();
	Array of Button is helpButtons: Array();
	Array of Overlay is helpOverlays: Array();

	replace Function is init(ExplorerViewModel is vm: ExplorerViewModel()){
		:vm: vm;
		:vm:onRenderChanged: {
			invalidate();
		};
		:vm:onHelpChanged: {
			syncHelpOverlay();
		};
		:fractalPickers: Array([
			Dropdown(
				host: :,
				options: vm:fractalOptions(),
				selected: FractalStrings:OPT_SELECT_FRACTAL,
				focusTarget: fractalFocus,
				onSelect: local Function(String is chosen){
					:vm:selectFractal(name: chosen);
				}
			)
		]);
		:themePickers: Array([
			Dropdown(
				host: :,
				options: FractalStrings:themeOptions(),
				selected: FractalStrings:THEME_GRAYSCALE,
				focusTarget: themeFocus,
				onSelect: local Function(String is chosen){
					:vm:selectTheme(name: chosen);
				}
			)
		]);
		:helpButtons: Array([
			Button(
				label: FractalStrings:ACTION_HELP,
				focusTarget: helpFocus,
				onClick: { :vm:openHelp(); }
			)
		]);
		local Overlay is hOv: Overlay(
			closeOnEsc: true,
			closeOnBackdrop: true,
			onClose: { :vm:closeHelp(); },
			content: HelpDialog:build(closeFocus: helpCloseFocus, onClose: { :vm:closeHelp(); })
		);
		:helpOverlays: Array([hOv]);
		addOverlay(overlay: hOv);
	}

	local Function is syncHelpOverlay(){
		if({ helpOverlays:length() == 0 || helpButtons:length() == 0 }, { return; });
		local Overlay is hOv: helpOverlays:get(index: 0);
		if({ vm:helpOpen }, {
			if({ !hOv:open }, {
				showOverlay(overlay: hOv, anchor: helpButtons:get(index: 0));
			});
		}, {
			if({ hOv:open }, {
				closeOverlay(overlay: hOv);
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
						label: FractalStrings:ACTION_QUIT,
						focusTarget: quitFocus,
						onClick: { :vm:quit(); }
					),
					Spacer(weight: 1.0),
					fractalPickers:get(index: 0),
					TextLine(value: FractalStrings:LABEL_THEME),
					themePickers:get(index: 0),
					Spacer(weight: 1.0),
					helpButtons:get(index: 0)
				])
			)
		);
		return Col(
			gap: 0,
			children: Array([
				FractalCanvas(vm: vm),
				bottomBar
			])
		);
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		return vm:handleShortcut(key: event:key, ctrl: event:ctrl);
	}
}
