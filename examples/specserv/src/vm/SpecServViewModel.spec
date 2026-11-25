#! Package specserv:vm
#! ViewModel managing SpecServ site configuration, JSON persistence, server lifecycle, and live request logs.

Class is SpecServViewModel{
	replace [String] is namespace: ['specserv', 'vm'];

	merge [[String]] is using: [
		['specserv', 'model', [ServerConfig, SiteConfig]],
		['base', 'core', SpecError],
		['base', 'net', [as Socket(), NetError]],
		['base', 'struct', Array],
		['base', 'sys', [as Dir(), as File(), as Process()]],
		['base', 'sys', 'thread', [Channel, ThreadScope]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	ServerConfig is config: ServerConfig();
	String is configPath: 'specserv.json';
	Int is selectedIndex: -1;
	Boolean is serversRunning: false;
	Int is controlPort: 0;
	Int is logCursor: 0;
	String is logFilePath: '';
	Channel of Int is exitChannel: Channel:bounded(capacity: 4);
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

	local Function of String is findSpecServBinary(){
		local String is exeDirPath: exeDir();
		if({ exeDirPath != '' && fileExists(path: exeDirPath . '/specserv') }, {
			return exeDirPath . '/specserv';
		});
		if({ fileExists(path: 'bin/specserv') }, { return 'bin/specserv'; });
		return 'specserv';
	}

	local Function of Int is pickControlPort(){
		local Int is candidate: 47900 + (getPid() % 500);
		local Boolean is clash: true;
		while({ clash }, {
			clash: false;
			times(count: config:sites:length(), worker: local Function(Int is i){
				if({ config:sites:get(index: i):port == candidate }, {
					clash: true;
				});
			});
			if({ clash }, {
				candidate++;
			});
		});
		return candidate;
	}

	local Function of String is sendControl(String is cmd){
		if({ controlPort <= 0 }, { return ''; });
		local Boolean is ok: true;
		local Socket is sock: connect(host: '127.0.0.1', port: controlPort, timeoutMs: 250, onError: local Function(SpecError of NetError is _e){
			ok: false;
		});
		if({ !ok || !sock:isOpen() }, {
			return '';
		});
		sock:setTimeout(timeoutMs: 500);
		sock:sendString(text: cmd . "\n", onError: local Function(SpecError of NetError is _e){
			ok: false;
		});
		local String is out: '';
		if({ ok }, {
			local Boolean is reading: true;
			while({ reading }, {
				local String is chunk: sock:receiveString(maxBytes: 8192, onError: local Function(SpecError of NetError is _e){});
				if({ chunk == '' }, {
					reading: false;
				}, {
					out: out . chunk;
				});
			});
		});
		sock:close();
		return out;
	}

	Function is startServers(){
		if({ serversRunning }, { return; });
		local Int is enabledCount: 0;
		times(count: config:sites:length(), worker: local Function(Int is i){
			if({ config:sites:get(index: i):enabled }, {
				enabledCount++;
			});
		});
		if({ enabledCount == 0 }, {
			statusMessage: 'No enabled sites to start';
			appendLog(line: statusMessage);
			onChanged();
			return;
		});

		controlPort: pickControlPort();
		logCursor: 0;
		while({ exitChannel:tryReceive(default: -1) != -1 }, {});

		if({ !config:saveToFile(path: configPath) }, {
			statusMessage: 'Failed to save ' . configPath;
			appendLog(line: statusMessage);
			onChanged();
			return;
		});

		local String is binPath: findSpecServBinary();
		local Array of String is procArgs: Array(['--config', configPath, '--control-port', controlPort as String]);
		if({ logFilePath != '' }, {
			procArgs:add(item: '--log-file');
			procArgs:add(item: logFilePath);
		});
		local Channel of Int is doneCh: exitChannel;

		if({ allowThreads }, {
			ThreadScope:dispatch(task: local Function(){
				local Int is code: execute(command: binPath, args: procArgs);
				doneCh:send(item: code);
			});
		});
		serversRunning: true;
		statusMessage: 'Running (' . (enabledCount as String) . ' site(s))';
		appendLog(line: 'Started ' . binPath . ' (' . (enabledCount as String) . ' site(s))');
		onChanged();
	}

	Function is stopServers(){
		if({ !serversRunning }, { return; });
		if({ allowThreads }, {
			sendControl(cmd: 'STOP');
			local Int is waited: 0;
			local Boolean is exited: false;
			while({ !exited && waited < 30 }, {
				if({ exitChannel:tryReceive(default: -9999) != -9999 }, {
					exited: true;
				}, {
					sleep(milliseconds: 25);
					waited++;
				});
			});
		});
		serversRunning: false;
		controlPort: 0;
		statusMessage: 'Stopped';
		appendLog(line: 'Stopped specserv');
		onChanged();
	}

	Function of Boolean is pollLogs(){
		local Boolean is anyNew: false;
		if({ serversRunning && controlPort > 0 }, {
			local String is resp: sendControl(cmd: 'LOGS ' . (logCursor as String));
			if({ resp != '' }, {
				local Array of String is lines: resp:split(delimiter: "\n");
				times(count: lines:length(), worker: local Function(Int is i){
					local String is ln: lines:get(index: i, default: '');
					if({ ln:startsWith(prefix: 'LOG ') }, {
						appendLog(line: ln:substring(start: 4, end: ln:length()));
						anyNew: true;
					}, {
						if({ ln:startsWith(prefix: 'END ') }, {
							local Int is nextCur: ln:substring(start: 4, end: ln:length()):trim():parseInt(default: logCursor);
							if({ nextCur > logCursor }, {
								logCursor: nextCur;
							});
						});
					});
				});
			});
		});
		if({ serversRunning }, {
			local Int is exitCode: exitChannel:tryReceive(default: -9999);
			if({ exitCode != -9999 }, {
				serversRunning: false;
				controlPort: 0;
				statusMessage: 'Stopped (exit ' . (exitCode as String) . ')';
				appendLog(line: 'specserv exited with code ' . (exitCode as String));
				onChanged();
				anyNew: true;
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
