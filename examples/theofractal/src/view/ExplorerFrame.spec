#! Package theofractal:view
#! Main TheoFractal explorer frame: empty main canvas, bottom control bar, Help dialog, and ASDW/QE shortcuts.

Class of Frame is ExplorerFrame{
	replace [String] is namespace: ['theofractal', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theofractal', 'util', FractalStrings],
		['theofractal', 'vm', ExplorerViewModel],
		['theofractal', 'view', FractalCanvas]
	];

	TheoApp is app;
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

	replace Function is init(TheoApp is app: TheoApp(), ExplorerViewModel is vm: ExplorerViewModel()){
		:app: app;
		:vm: vm;
		:vm:onRenderChanged: {
			invalidate();
		};
		:fractalPickers: Array([
			Dropdown(
				host: :,
				options: FractalStrings:fractalOptions(),
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
				onClick: { :openHelp(); }
			)
		]);
		local Overlay is hOv: Overlay(
			closeOnEsc: true,
			closeOnBackdrop: true,
			content: buildHelpDialog()
		);
		:helpOverlays: Array([hOv]);
		addOverlay(overlay: hOv);
	}

	local Function of Widget is buildHelpDialog(){
		return Center(
			child: Surface(
				child: Panel(
					border: true,
					padX: 2,
					padY: 1,
					topTitle: FractalStrings:HELP_TITLE,
					topTitleAlign: TitleAlign:CENTER,
					child: Col(
						gap: 0,
						children: Array([
							TextLine(value: FractalStrings:HELP_ABOUT_HDR, bold: true),
							TextLine(value: FractalStrings:HELP_ABOUT_1),
							TextLine(value: FractalStrings:HELP_ABOUT_2),
							TextLine(value: FractalStrings:HELP_ABOUT_3),
							TextLine(value: FractalStrings:HELP_ABOUT_4),
							TextLine(value: ''),
							TextLine(value: FractalStrings:HELP_KEYS_HDR, bold: true),
							TextLine(value: FractalStrings:HELP_KEY_PAN),
							TextLine(value: FractalStrings:HELP_KEY_ZOOM),
							TextLine(value: FractalStrings:HELP_KEY_RESET),
							TextLine(value: FractalStrings:HELP_KEY_HELP),
							TextLine(value: FractalStrings:HELP_KEY_NAV),
							TextLine(value: ''),
							Row(
								children: Array([
									Spacer(weight: 1.0),
									Button(
										label: FractalStrings:ACTION_CLOSE,
										focusTarget: helpCloseFocus,
										onClick: { :closeHelp(); }
									),
									Spacer(weight: 1.0)
								])
							)
						])
					)
				)
			)
		);
	}

	Function is openHelp(){
		if({ helpOverlays:length() == 0 || helpButtons:length() == 0 }, { return; });
		showOverlay(overlay: helpOverlays:get(index: 0), anchor: helpButtons:get(index: 0));
	}

	Function is closeHelp(){
		if({ helpOverlays:length() == 0 }, { return; });
		closeOverlay(overlay: helpOverlays:get(index: 0));
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
						onClick: { :app:quit(); }
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
		if({ event:ctrl && (event:key == 'q' || event:key == 'Q') }, {
			app:quit();
			return true;
		});
		local String is k: event:key;
		if({ k == 'a' || k == 'A' }, { vm:panLeft(); return true; });
		if({ k == 'd' || k == 'D' }, { vm:panRight(); return true; });
		if({ k == 'w' || k == 'W' }, { vm:panUp(); return true; });
		if({ k == 's' || k == 'S' }, { vm:panDown(); return true; });
		if({ k == 'q' || k == 'Q' }, { vm:zoomOut(); return true; });
		if({ k == 'e' || k == 'E' }, { vm:zoomIn(); return true; });
		if({ k == 'r' || k == 'R' }, { vm:resetView(); return true; });
		if({ k == 'h' || k == 'H' || k == '?' }, { openHelp(); return true; });
		return false;
	}
}
