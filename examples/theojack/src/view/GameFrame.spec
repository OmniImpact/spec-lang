#! Package theojack:view
#! Blackjack gameplay screen: pure view bound to [GameViewModel] with Dealer/Player panels, padded action buttons, tooltips, and result overlays.

Class of Frame is GameFrame{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theojack', 'util', HomeStrings],
		['theojack', 'vm', GameViewModel],
		['theojack', 'view', CardView]
	];

	GameViewModel is vm: GameViewModel();
	FocusTarget is primaryFocus: FocusTarget(initial: true);
	FocusTarget is secondaryFocus: FocusTarget();
	FocusTarget is doubleFocus: FocusTarget();
	FocusTarget is homeFocus: FocusTarget();
	FocusTarget is dialogActionFocus: FocusTarget(initial: true);
	FocusTarget is dialogHomeFocus: FocusTarget();
	Array of Overlay is resultOverlays: Array();

	replace Function is init(GameViewModel is vm: GameViewModel()){
		:vm: vm;
		vm:onStateChanged: {
			rebuild();
			syncResultOverlay();
		};
	}

	local Function is syncResultOverlay(){
		if({ vm:isResultShown() }, {
			local Widget is nextBtn: Button(
				label: vm:resultButtonLabel(),
				focusTarget: dialogActionFocus,
				onClick: { vm:advanceFromResult(); }
			);
			local Widget is homeBtn: Button(
				label: HomeStrings:ACTION_HOME,
				focusTarget: dialogHomeFocus,
				onClick: { vm:goHome(); }
			);
			local Widget is btnRow: Row(
				gap: 2,
				arrowFocus: true,
				children: Array([Spacer(weight: 1.0), nextBtn, homeBtn, Spacer(weight: 1.0)])
			);
			local Widget is dialogPanel: Panel(
				border: true,
				padX: 2,
				padY: 1,
				topTitle: vm:resultTitle(),
				topTitleAlign: 'center',
				child: Col(
					gap: 1,
					children: Array([TextLine(value: vm:resultMessage()), btnRow])
				)
			);
			local Overlay is ov: Overlay(
				closeOnEsc: false,
				closeOnBackdrop: false,
				content: Center(child: Surface(child: dialogPanel))
			);
			:resultOverlays: Array([ov]);
			:overlays: Array();
			showOverlay(overlay: ov);
			return;
		});
		:resultOverlays: Array();
		:overlays: Array();
	}

	local Function of Array of Widget is buildDealerCards(){
		local Array of Widget is out: Array();
		local Boolean is hideHole: vm:shouldHideDealerHole();
		local Int is i: 0;
		while({ i < vm:game:dealerHand:count() }, {
			out:add(item: CardView(
				card: vm:game:dealerHand:cards:get(index: i),
				style: vm:cardStyle,
				faceDown: hideHole && i == 1
			));
			i: i + 1;
		});
		return out;
	}

	local Function of Array of Widget is buildPlayerCards(){
		local Array of Widget is out: Array();
		local Int is i: 0;
		while({ i < vm:game:playerHand:count() }, {
			out:add(item: CardView(
				card: vm:game:playerHand:cards:get(index: i),
				style: vm:cardStyle
			));
			i: i + 1;
		});
		return out;
	}

	local Function of Array of Widget is buildActionButtons(){
		local Array of Widget is btns: Array();
		if({ vm:isBetting() }, {
			btns:add(item: Tooltip(
				host: :,
				text: 'Decrease bet by $10',
				side: 'top',
				child: Button(
					label: HomeStrings:ACTION_BET_DOWN,
					padX: 2,
					padY: 1,
					focusTarget: secondaryFocus,
					onClick: { vm:adjustBet(delta: -10); }
				)
			));
			btns:add(item: Tooltip(
				host: :,
				text: 'Increase bet by $10',
				side: 'top',
				child: Button(
					label: HomeStrings:ACTION_BET_UP,
					padX: 2,
					padY: 1,
					focusTarget: doubleFocus,
					onClick: { vm:adjustBet(delta: 10); }
				)
			));
			btns:add(item: Tooltip(
				host: :,
				text: 'Deal a new hand',
				side: 'top',
				child: Button(
					label: HomeStrings:ACTION_DEAL,
					shortcut: ShortcutKey:ctrl(key: 'd'),
					padX: 2,
					padY: 1,
					focusTarget: primaryFocus,
					onClick: { vm:deal(); }
				)
			));
		}, {
			btns:add(item: Button(
				label: HomeStrings:ACTION_HIT,
				shortcut: ShortcutKey:ctrl(key: 'h'),
				padX: 2,
				padY: 1,
				focusTarget: primaryFocus,
				onClick: { vm:hit(); }
			));
			btns:add(item: Button(
				label: HomeStrings:ACTION_STAND,
				shortcut: ShortcutKey:ctrl(key: 's'),
				padX: 2,
				padY: 1,
				focusTarget: secondaryFocus,
				onClick: { vm:stand(); }
			));
			if({ vm:canDouble() }, {
				btns:add(item: Button(
					label: HomeStrings:ACTION_DOUBLE,
					shortcut: ShortcutKey:ctrl(key: 'b'),
					padX: 2,
					padY: 1,
					focusTarget: doubleFocus,
					onClick: { vm:doubleDown(); }
				));
			});
		});
		btns:add(item: Spacer(weight: 1.0));
		btns:add(item: Button(
			label: HomeStrings:ACTION_HOME,
			shortcut: ShortcutKey:ctrl(key: 'q'),
			padX: 2,
			padY: 1,
			focusTarget: homeFocus,
			onClick: { vm:goHome(); }
		));
		return btns;
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			vm:goHome();
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		local Widget is statusRow: Row(
			children: Array([
				TextLine(value: vm:roundText(), bold: true),
				Spacer(weight: 1.0),
				TextLine(value: vm:bankrollText(), color: activeTheme:accentColor, bold: true),
				Spacer(weight: 1.0),
				TextLine(value: vm:betText(), bold: true)
			])
		);
		local Widget is statusBar: Panel(border: true, padX: 1, padY: 0, child: statusRow);

		local Widget is dealerRow: Row(
			align: 'center',
			children: Array([
				Row(gap: 2, children: buildDealerCards()),
				Spacer(weight: 1.0),
				TextLine(value: vm:dealerScoreText(), color: activeTheme:mutedColor)
			])
		);
		local Widget is dealerPanel: Panel(
			border: true,
			padX: 2,
			padY: 1,
			rightTitle: HomeStrings:DEALER_TITLE,
			rightTitleAlign: 'center',
			child: dealerRow
		);

		local Widget is playerRow: Row(
			align: 'center',
			children: Array([
				Row(gap: 2, children: buildPlayerCards()),
				Spacer(weight: 1.0),
				TextLine(value: vm:playerScoreText(), color: activeTheme:mutedColor)
			])
		);
		local Widget is playerPanel: Panel(
			border: true,
			padX: 2,
			padY: 1,
			leftTitle: HomeStrings:PLAYER_TITLE,
			leftTitleAlign: 'center',
			child: playerRow
		);

		local Widget is actionsBar: Panel(
			border: true,
			padX: 1,
			padY: 0,
			child: Row(gap: 2, arrowFocus: true, children: buildActionButtons())
		);

		Grid(
			orientation: 'vertical',
			panes: Array([
				Grid:fixed(size: 3, child: statusBar),
				Grid:weight(weight: 1.0, child: dealerPanel),
				Grid:weight(weight: 1.0, child: playerPanel),
				Grid:fixed(size: 5, child: actionsBar)
			])
		);
	}
}
