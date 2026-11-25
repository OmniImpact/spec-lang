#! Package specserv:vm
#! ViewModel managing SpecServ site configuration, JSON persistence, server lifecycle, and live request logs.

Class is SpecServViewModel{
	replace [String] is namespace: ['specserv', 'vm'];

	merge [[String]] is using: [
		['specserv', 'model', [ServerConfig, SiteConfig]],
		['specserv', 'server', SiteServer],
		['base', 'core', SpecError],
		['base', 'struct', Array],
		['base', 'sys', [as Dir(), as File()]],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	ServerConfig is config: ServerConfig();
	String is configPath: 'specserv.json';
	Int is selectedIndex: -1;
	Boolean is serversRunning: false;
	[SiteServer] is activeServers: [];
	Array of String is logs: Array();
	String is statusMessage: 'Stopped';

	String is draftName: 'Spec Docs';
	String is draftDirectory: 'examples/specserv/site';
	String is draftPort: '47321';

	Boolean is allowThreads: false;

	Function is onChanged: {};
	Function is onLogsChanged: {};
	Function is onQuit: {};

	replace Function is init(Boolean is allowThreads: false, String is configPath: 'specserv.json', Function is onQuit: {}){
		:allowThreads: allowThreads;
		:configPath: configPath;
		:onQuit: onQuit;
		if({ fileExists(path: configPath) }, {
			:config: ServerConfig():loadFromFile(path: configPath);
		}, {
			if({ dirList(path: 'examples/specserv/site'):length() > 0 }, {
				:config:addDirectory(name: 'Spec Docs', directory: 'examples/specserv/site', port: 0, enabled: true);
			});
		});
		if({ config:sites:length() > 0 }, {
			selectSite(index: 0);
		}, {
			draftPort: config:nextAvailablePort() as String;
		});
	}

	local Function is appendLog(String is line){
		logs:add(item: line);
		if({ logs:length() > 200 }, {
			local Array of String is trimmed: Array();
			range(start: logs:length() - 200, end: logs:length(), worker: local Function(Int is i){
				trimmed:add(item: logs:get(index: i, default: ''));
			});
			logs: trimmed;
		});
	}

	Function of Array of String is siteItems(){
		local Array of String is out: Array();
		times(count: config:sites:length(), worker: local Function(Int is i){
			out:add(item: config:sites:get(index: i):summary());
		});
		return out;
	}

	Function is selectSite(Int is index){
		if({ index < 0 || index >= config:sites:length() }, {
			selectedIndex: -1;
			return;
		});
		selectedIndex: index;
		local SiteConfig is s: config:sites:get(index: index);
		draftName: s:name;
		draftDirectory: s:directory;
		draftPort: s:port as String;
		onChanged();
	}

	Function is addSite(String is name, String is directory, String is portText){
		local Int is p: portText:trim():parseInt(default: 0);
		local String is dir: directory:trim();
		if({ dir == '' }, { dir: '.'; });
		local SiteConfig is s: config:addDirectory(name: name, directory: dir, port: p, enabled: true);
		selectedIndex: config:sites:length() - 1;
		draftName: s:name;
		draftDirectory: s:directory;
		draftPort: s:port as String;
		statusMessage: 'Added ' . s:name . ' on :' . (s:port as String);
		appendLog(line: statusMessage);
		onChanged();
	}

	Function is updateSelectedSite(String is name, String is directory, String is portText){
		if({ selectedIndex < 0 || selectedIndex >= config:sites:length() }, {
			addSite(name: name, directory: directory, portText: portText);
			return;
		});
		local SiteConfig is s: config:sites:get(index: selectedIndex);
		local String is cleanName: name:trim();
		if({ cleanName != '' }, { s:name: cleanName; });
		local String is cleanDir: directory:trim();
		if({ cleanDir != '' }, { s:directory: cleanDir; });
		local Int is p: portText:trim():parseInt(default: 0);
		if({ p > 0 }, {
			local Boolean is conflict: false;
			times(count: config:sites:length(), worker: local Function(Int is i){
				if({ i != selectedIndex && config:sites:get(index: i):port == p }, {
					conflict: true;
				});
			});
			if({ !conflict }, {
				s:port: p;
			}, {
				s:port: config:nextAvailablePort();
			});
		});
		draftName: s:name;
		draftDirectory: s:directory;
		draftPort: s:port as String;
		statusMessage: 'Updated ' . s:name;
		onChanged();
	}

	Function is removeSelectedSite(){
		if({ selectedIndex < 0 || selectedIndex >= config:sites:length() }, { return; });
		local String is removed: config:sites:get(index: selectedIndex):name;
		config:removeAt(index: selectedIndex);
		if({ config:sites:length() == 0 }, {
			selectedIndex: -1;
			draftName: '';
			draftDirectory: '';
			draftPort: config:nextAvailablePort() as String;
		}, {
			if({ selectedIndex >= config:sites:length() }, {
				selectedIndex: config:sites:length() - 1;
			});
			selectSite(index: selectedIndex);
		});
		statusMessage: 'Removed ' . removed;
		onChanged();
	}

	Function is toggleSelectedEnabled(){
		if({ selectedIndex < 0 || selectedIndex >= config:sites:length() }, { return; });
		local SiteConfig is s: config:sites:get(index: selectedIndex);
		s:enabled: !s:enabled;
		statusMessage: s:name . if({ s:enabled }, { ' enabled' }, { ' disabled' });
		onChanged();
	}

	Function is saveConfig(String is path){
		local String is target: if({ path:trim() != '' }, { path:trim() }, { configPath });
		configPath: target;
		if({ config:saveToFile(path: target) }, {
			statusMessage: 'Saved config to ' . target;
			appendLog(line: statusMessage);
		}, {
			statusMessage: 'Failed to save ' . target;
			appendLog(line: statusMessage);
		});
		onChanged();
	}

	Function is loadConfig(String is path){
		local String is target: if({ path:trim() != '' }, { path:trim() }, { configPath });
		configPath: target;
		config: ServerConfig():loadFromFile(path: target);
		if({ config:sites:length() > 0 }, {
			selectSite(index: 0);
		}, {
			selectedIndex: -1;
			draftPort: config:nextAvailablePort() as String;
		});
		statusMessage: 'Loaded ' . (config:sites:length() as String) . ' site(s) from ' . target;
		appendLog(line: statusMessage);
		onChanged();
	}

	Function is startServers(){
		if({ serversRunning }, { return; });
		activeServers: [];
		local Int is started: 0;
		times(count: config:sites:length(), worker: local Function(Int is i){
			local SiteConfig is s: config:sites:get(index: i);
			if({ s:enabled }, {
				local SiteServer is srv: SiteServer(site: s);
				activeServers:push(item: srv);
				if({ allowThreads }, {
					ThreadScope:dispatch(task: local Function(){
						srv:serveLoop();
					});
				});
				started++;
			});
		});
		if({ started == 0 }, {
			statusMessage: 'No enabled sites to start';
			appendLog(line: statusMessage);
			onChanged();
			return;
		});
		serversRunning: true;
		statusMessage: 'Running (' . (started as String) . ' site(s))';
		onChanged();
	}

	Function is stopServers(){
		if({ !serversRunning }, { return; });
		times(count: activeServers:length(), worker: local Function(Int is i){
			activeServers:get(index: i):requestStop();
		});
		serversRunning: false;
		statusMessage: 'Stopped';
		appendLog(line: 'All sites stopped');
		onChanged();
	}

	Function of Boolean is pollLogs(){
		local Boolean is anyNew: false;
		times(count: activeServers:length(), worker: local Function(Int is i){
			local SiteServer is srv: activeServers:get(index: i);
			local Boolean is draining: true;
			while({ draining }, {
				local String is msg: srv:logChannel:tryReceive(default: '');
				if({ msg != '' }, {
					appendLog(line: msg);
					anyNew: true;
				}, {
					draining: false;
				});
			});
		});
		if({ anyNew }, {
			onLogsChanged();
		});
		return anyNew;
	}

	Function is quit(){
		stopServers();
		onQuit();
	}
}
