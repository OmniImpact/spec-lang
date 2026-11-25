#! Package specserv
#! Dedicated headless HTTP/1.1 web server (`specserv`) serving configured static and `.spec` sites.

Class is SpecServ{
	replace [String] is namespace: ['specserv'];

	merge [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', [as Socket(), NetError]],
		['base', 'struct', [Array, Map]],
		['base', 'sys', [as Dir(), as File(), as Output(), as Process(), as Time()]],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['specserv', 'model', [ServerConfig, SiteConfig]],
		['specserv', 'server', SiteServer]
	];

	Array of Int is reqTimestamps: Array();
	Int is lastCpuMs: 0;
	Int is lastWallMs: 0;
	Int is cachedCpuTenths: 0;

	local Function is pruneOldRequests(Int is nowMs){
		local Int is cutoff: nowMs - 60000;
		local Int is firstValid: 0;
		local Int is n: reqTimestamps:length();
		while({ firstValid < n && reqTimestamps:get(index: firstValid, default: 0) < cutoff }, {
			firstValid++;
		});
		if({ firstValid > 0 }, {
			local Array of Int is kept: Array();
			local Int is i: firstValid;
			while({ i < n }, {
				kept:add(item: reqTimestamps:get(index: i, default: 0));
				i++;
			});
			reqTimestamps: kept;
		});
	}

	local Function of Int is currentRssKb(){
		local String is statusTxt: fileRead(path: '/proc/self/status', onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');
		if({ statusTxt != '' }, {
			local Int is idx: statusTxt:indexOf(search: 'VmRSS:', default: -1);
			if({ idx >= 0 }, {
				local Int is nl: statusTxt:indexOfFrom(search: "\n", from: idx, default: statusTxt:length());
				local String is lineStr: statusTxt:substring(start: idx + 6, end: nl):trim();
				local Int is kbIdx: lineStr:indexOf(search: 'kB', default: -1);
				if({ kbIdx > 0 }, {
					lineStr: lineStr:substring(start: 0, end: kbIdx):trim();
				});
				local Int is parsed: lineStr:parseInt(default: 0);
				if({ parsed > 0 }, { return parsed; });
			});
		});
		return peakMemoryKb();
	}

	local Function of Int is sampleCpuTenths(){
		local Int is nowWall: monotonicMs();
		local Int is nowCpu: clockMs();
		local Int is dWall: nowWall - lastWallMs;
		if({ dWall >= 500 }, {
			local Int is dCpu: nowCpu - lastCpuMs;
			if({ dCpu < 0 }, { dCpu: 0; });
			cachedCpuTenths: (dCpu * 1000) / dWall;
			lastWallMs: nowWall;
			lastCpuMs: nowCpu;
		});
		return cachedCpuTenths;
	}

	local Function is recordLog(Array of String is history, String is logFile, String is msg){
		line(text: msg);
		history:add(item: msg);
		if({ msg:startsWith(prefix: ':') }, {
			local Int is nowMs: monotonicMs();
			reqTimestamps:add(item: nowMs);
			pruneOldRequests(nowMs: nowMs);
		});
		if({ logFile != '' }, {
			fileAppend(path: logFile, content: msg . "\n", onSuccess: local Function(Int is _n){}, onError: local Function(Any is _e){});
		});
	}

	local Function of Boolean is handleControlClient(Socket is client, Array of String is history){
		client:setTimeout(timeoutMs: 1000);
		local String is cmd: client:receiveString(maxBytes: 1024, onError: local Function(SpecError is _e){}):trim();
		if({ cmd == 'STOP' }, {
			client:sendString(text: "OK\n", onError: local Function(SpecError is _e){});
			client:close();
			return true;
		});
		if({ cmd:startsWith(prefix: 'LOGS') }, {
			local Int is cursor: 0;
			if({ cmd:length() > 5 }, {
				cursor: cmd:substring(start: 5, end: cmd:length()):trim():parseInt(default: 0);
			});
			if({ cursor < 0 }, { cursor: 0; });
			local Int is total: history:length();
			if({ cursor > total }, { cursor: total; });
			local String is out: '';
			local Int is i: cursor;
			while({ i < total }, {
				out: out . 'LOG ' . history:get(index: i, default: '') . "\n";
				i++;
			});
			local Int is nowMs: monotonicMs();
			pruneOldRequests(nowMs: nowMs);
			local Int is cpuTenths: sampleCpuTenths();
			local Int is rssKb: currentRssKb();
			local Int is reqCount: reqTimestamps:length();
			out: out . 'STATS ' . (cpuTenths as String) . ' ' . (rssKb as String) . ' ' . (reqCount as String) . "\n";
			out: out . 'END ' . (total as String) . "\n";
			client:sendString(text: out, onError: local Function(SpecError is _e){});
		});
		client:close();
		return false;
	}

	replace Function is init(Map of String to String is args){
		if({ args:has(key: 'help') || args:has(key: 'h') }, {
			line(text: 'Usage: specserv [--config <path>] [--control-port <port>] [--log-file <path>]');
			return;
		});

		local String is cfgPath: args:getString(key: 'config', default: 'specserv.json');
		local String is logFile: args:getString(key: 'log-file', default: '');
		local Int is controlPort: args:getString(key: 'control-port', default: '47320'):parseInt(default: 47320);
		lastWallMs: monotonicMs();
		lastCpuMs: clockMs();

		local ServerConfig is cfg: ServerConfig();
		if({ fileExists(path: cfgPath) }, {
			cfg: ServerConfig():loadFromFile(path: cfgPath);
		}, {
			if({ dirList(path: 'examples/specserv/site'):length() > 0 }, {
				cfg:addDirectory(name: 'Spec Docs', directory: 'examples/specserv/site', port: 0, enabled: true);
			});
		});

		local [SiteServer] is servers: [];
		times(count: cfg:sites:length(), worker: local Function(Int is i){
			local SiteConfig is sc: cfg:sites:get(index: i);
			if({ sc:enabled }, {
				servers:push(item: SiteServer(site: sc));
			});
		});

		local Array of String is history: Array();
		if({ servers:length() == 0 }, {
			recordLog(history: history, logFile: logFile, msg: 'SpecServ: no enabled sites to serve.');
			return;
		});

		local Boolean is hasControl: false;
		local Socket is controlListener: Socket();
		if({ controlPort > 0 }, {
			local Boolean is ctrlOk: true;
			controlListener: listen(host: '127.0.0.1', port: controlPort, onError: local Function(SpecError of NetError is err){
				ctrlOk: false;
				recordLog(history: history, logFile: logFile, msg: 'Control socket error: ' . err:description);
			});
			if({ ctrlOk && controlListener:isOpen() }, {
				hasControl: true;
			});
		});

		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _err){ true },
			body: local Function(ThreadScope is scope){
				times(count: servers:length(), worker: local Function(Int is i){
					local SiteServer is srv: servers:get(index: i);
					scope:spawn(task: local Function(){
						srv:serveLoop();
					});
				});

				recordLog(history: history, logFile: logFile, msg: 'SpecServ running (' . (servers:length() as String) . ' site(s)). Press Ctrl-C to stop.');
				local Boolean is keepRunning: true;
				while({ keepRunning }, {
					times(count: servers:length(), worker: local Function(Int is i){
						local SiteServer is srv: servers:get(index: i);
						local Boolean is draining: true;
						while({ draining }, {
							local String is msg: srv:logChannel:tryReceive(default: '');
							if({ msg != '' }, {
								recordLog(history: history, logFile: logFile, msg: msg);
							}, {
								draining: false;
							});
						});
					});
					if({ hasControl }, {
						if({ controlListener:poll(mode: 1, timeoutMs: 30) }, {
							local Boolean is accOk: true;
							local Socket is client: controlListener:accept(onError: local Function(SpecError of NetError is _e){
								accOk: false;
							});
							if({ accOk && client:isOpen() }, {
								if({ handleControlClient(client: client, history: history) }, {
									keepRunning: false;
								});
							});
						});
					}, {
						sleep(milliseconds: 50);
					});
				});

				times(count: servers:length(), worker: local Function(Int is i){
					servers:get(index: i):requestStop();
				});
				sleep(milliseconds: 120);
				times(count: servers:length(), worker: local Function(Int is i){
					local SiteServer is srv: servers:get(index: i);
					local Boolean is draining: true;
					while({ draining }, {
						local String is msg: srv:logChannel:tryReceive(default: '');
						if({ msg != '' }, {
							recordLog(history: history, logFile: logFile, msg: msg);
						}, {
							draining: false;
						});
					});
				});
			}
		);

		if({ hasControl }, {
			controlListener:close();
		});
	}
}
