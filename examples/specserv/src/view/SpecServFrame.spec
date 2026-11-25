#! Package specserv:view
#! Theo TUI frame for configuring sites, saving/loading JSON config, and starting/stopping SpecServ.

Class of Frame is SpecServFrame{
	replace [String] is namespace: ['specserv', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['specserv', 'vm', SpecServViewModel]
	];

	SpecServViewModel is vm: SpecServViewModel();

	FocusTarget is sitesFocus: FocusTarget(initial: true);
	FocusTarget is nameFocus: FocusTarget();
	FocusTarget is dirFocus: FocusTarget();
	FocusTarget is portFocus: FocusTarget();
	FocusTarget is cfgPathFocus: FocusTarget();
	FocusTarget is addFocus: FocusTarget();
	FocusTarget is updateFocus: FocusTarget();
	FocusTarget is toggleFocus: FocusTarget();
	FocusTarget is removeFocus: FocusTarget();
	FocusTarget is saveFocus: FocusTarget();
	FocusTarget is loadFocus: FocusTarget();
	FocusTarget is startStopFocus: FocusTarget();
	FocusTarget is quitFocus: FocusTarget();
	FocusTarget is logFocus: FocusTarget();

	Array of ListView is siteLists: Array();
	Array of ListView is logLists: Array();
	Array of TextInput is nameInputs: Array();
	Array of TextInput is dirInputs: Array();
	Array of TextInput is portInputs: Array();
	Array of TextInput is cfgInputs: Array();
	Array of Button is startStopBtns: Array();
	Array of TextLine is statusLines: Array();

	replace Function is init(SpecServViewModel is vm: SpecServViewModel()){
		:vm: vm;
		vm:onChanged: {
			syncFromVm();
			invalidate();
		};
		vm:onLogsChanged: {
			syncLogs();
			invalidate();
		};
	}

	local Function is syncLogs(){
		if({ logLists:length() > 0 }, {
			local ListView is lv: logLists:get(index: 0);
			lv:setItems(nextItems: vm:logs);
			if({ vm:logs:length() > 0 }, {
				lv:selectedIdx: vm:logs:length() - 1;
			});
		});
	}

	local Function of String is formattedStatus(){
		if({ vm:serversRunning && !vm:statusMessage:startsWith(prefix: 'Running') }, {
			return 'Status: Running (' . vm:statusMessage . ')';
		});
		return 'Status: ' . vm:statusMessage;
	}

	local Function is syncFromVm(){
		if({ siteLists:length() > 0 }, {
			local ListView is sv: siteLists:get(index: 0);
			sv:setItems(nextItems: vm:siteItems());
			sv:selectedIdx: vm:selectedIndex;
		});
		if({ nameInputs:length() > 0 }, {
			nameInputs:get(index: 0):setText(value: vm:draftName);
		});
		if({ dirInputs:length() > 0 }, {
			dirInputs:get(index: 0):setText(value: vm:draftDirectory);
		});
		if({ portInputs:length() > 0 }, {
			portInputs:get(index: 0):setText(value: vm:draftPort);
		});
		if({ cfgInputs:length() > 0 }, {
			cfgInputs:get(index: 0):setText(value: vm:configPath);
		});
		if({ startStopBtns:length() > 0 }, {
			local Button is sb: startStopBtns:get(index: 0);
			sb:label: if({ vm:serversRunning }, { ' Stop ' }, { ' Start ' });
			sb:invalidate();
		});
		if({ statusLines:length() > 0 }, {
			local TextLine is sl: statusLines:get(index: 0);
			sl:textValue: formattedStatus();
			sl:invalidate();
		});
		syncLogs();
	}

	replace Function of Boolean is onTick(){
		return vm:pollLogs();
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:ctrl && (event:key == 'q' || event:key == 'Q') }, {
			vm:quit();
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		local TextLine is statusLine: TextLine(value: formattedStatus(), bold: true, width: 44);
		statusLines: Array([statusLine]);

		local ListView is siteList: ListView(
			items: vm:siteItems(),
			focusTarget: sitesFocus,
			onSelectChange: local Function(String is _item){
				if({ siteLists:length() > 0 }, {
					:vm:selectSite(index: siteLists:get(index: 0):selectedIdx);
				});
			}
		);
		siteList:selectedIdx: vm:selectedIndex;
		siteLists: Array([siteList]);

		local TextInput is nameIn: TextInput(value: vm:draftName, placeholder: 'Site Name', focusTarget: nameFocus);
		local TextInput is dirIn: TextInput(value: vm:draftDirectory, placeholder: 'Directory path', focusTarget: dirFocus);
		local TextInput is portIn: TextInput(value: vm:draftPort, placeholder: 'Port (default 47321)', focusTarget: portFocus);
		local TextInput is cfgIn: TextInput(value: vm:configPath, placeholder: 'specserv.json', focusTarget: cfgPathFocus);
		nameInputs: Array([nameIn]);
		dirInputs: Array([dirIn]);
		portInputs: Array([portIn]);
		cfgInputs: Array([cfgIn]);

		local Button is startBtn: Button(
			label: if({ vm:serversRunning }, { ' Stop ' }, { ' Start ' }),
			focusTarget: startStopFocus,
			onClick: {
				if({ :vm:serversRunning }, { :vm:stopServers(); }, { :vm:startServers(); });
			}
		);
		startStopBtns: Array([startBtn]);

		local ListView is logList: ListView(
			items: vm:logs,
			focusTarget: logFocus
		);
		if({ vm:logs:length() > 0 }, { logList:selectedIdx: vm:logs:length() - 1; });
		logLists: Array([logList]);

		local Widget is header: Panel(
			border: true,
			padX: 1,
			padY: 0,
			topTitle: ' SpecServ — Web Server & Config Manager ',
			topTitleAlign: TitleAlign:LEFT,
			child: Row(
				gap: 2,
				children: Array([
					statusLine,
					Spacer(weight: 1.0),
					startBtn,
					Button(label: ' Quit ', focusTarget: quitFocus, onClick: { :vm:quit(); })
				])
			)
		);

		local Widget is sitesPanel: Panel(
			border: true,
			padX: 1,
			padY: 0,
			topTitle: ' Configured Sites ',
			child: siteList
		);

		local Widget is editorPanel: Panel(
			border: true,
			padX: 1,
			padY: 0,
			topTitle: ' Site & Config Editor ',
			child: Col(
				gap: 0,
				children: Array([
					Row(gap: 1, children: Array([TextLine(value: 'Name:  '), nameIn])),
					Row(gap: 1, children: Array([TextLine(value: 'Dir:   '), dirIn])),
					Row(gap: 1, children: Array([TextLine(value: 'Port:  '), portIn])),
					Row(
						gap: 1,
						arrowFocus: true,
						children: Array([
							Button(label: ' Add ', focusTarget: addFocus, onClick: {
								:vm:addSite(name: nameIn:text, directory: dirIn:text, portText: portIn:text);
							}),
							Button(label: ' Update ', focusTarget: updateFocus, onClick: {
								:vm:updateSelectedSite(name: nameIn:text, directory: dirIn:text, portText: portIn:text);
							}),
							Button(label: ' Enable/Disable ', focusTarget: toggleFocus, onClick: {
								:vm:toggleSelectedEnabled();
							}),
							Button(label: ' Remove ', focusTarget: removeFocus, onClick: {
								:vm:removeSelectedSite();
							})
						])
					),
					Row(gap: 1, children: Array([TextLine(value: 'Config:'), cfgIn])),
					Row(
						gap: 1,
						arrowFocus: true,
						children: Array([
							Button(label: ' Save JSON ', focusTarget: saveFocus, onClick: {
								:vm:saveConfig(path: cfgIn:text);
							}),
							Button(label: ' Load JSON ', focusTarget: loadFocus, onClick: {
								:vm:loadConfig(path: cfgIn:text);
							})
						])
					)
				])
			)
		);

		local Widget is topSplit: Grid(
			orientation: Orientation:HORIZONTAL,
			gap: 1,
			panes: Array([
				Grid:weight(weight: 1.0, child: sitesPanel),
				Grid:weight(weight: 1.2, child: editorPanel)
			])
		);

		local Widget is logPanel: Panel(
			border: true,
			padX: 1,
			padY: 0,
			topTitle: ' Request Log ',
			child: logList
		);

		return Grid(
			orientation: Orientation:VERTICAL,
			gap: 0,
			panes: Array([
				Grid:fixed(size: 3, child: header),
				Grid:fixed(size: 10, child: topSplit),
				Grid:weight(weight: 1.0, child: logPanel)
			])
		);
	}
}
