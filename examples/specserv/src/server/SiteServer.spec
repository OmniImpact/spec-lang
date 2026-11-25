#! Package specserv:server
#! Non-blocking-accept HTTP/1.1 server for a single [SiteConfig] directory.

Class is SiteServer{
	replace [String] is namespace: ['specserv', 'server'];

	merge [[String]] is using: [
		['specserv', 'model', SiteConfig],
		['specserv', 'server', [HttpRequestParser, MimeTypes, SpecPageRunner]],
		['base', 'core', SpecError],
		['base', 'net', [as Socket(), NetError]],
		['base', 'struct', [Array, Map]],
		['base', 'sys', [as File(), as Process(), as Time()]],
		['base', 'sys', 'thread', [Channel, ThreadScope]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	SiteConfig is site: SiteConfig();
	Boolean is running: false;
	Channel of Boolean is stopSignal: Channel:bounded(capacity: 4);
	Channel of String is logChannel: Channel:bounded(capacity: 256);

	replace Function is init(SiteConfig is site: SiteConfig()){
		:site: site;
	}

	local Function is emitLog(String is msg){
		logChannel:send(item: msg);
	}

	local Function of String is formatDuration(Int is elapsedNs){
		local Int is us: elapsedNs / 1000;
		if({ us < 0 }, { us: 0; });
		if({ us < 1000 }, {
			return (us as String) . 'us';
		});
		if({ us < 1000000 }, {
			local Int is ms: us / 1000;
			local Int is tenths: (us % 1000) / 100;
			return (ms as String) . '.' . (tenths as String) . 'ms';
		});
		local Int is secs: us / 1000000;
		local Int is tenths: (us % 1000000) / 100000;
		return (secs as String) . '.' . (tenths as String) . 's';
	}

	local Function of String is statusReason(Int is code){
		return match(when: [
			{ code == 200 }: { 'OK' },
			{ code == 301 }: { 'Moved Permanently' },
			{ code == 302 }: { 'Found' },
			{ code == 400 }: { 'Bad Request' },
			{ code == 403 }: { 'Forbidden' },
			{ code == 404 }: { 'Not Found' },
			{ code == 500 }: { 'Internal Server Error' },
			else: { 'OK' }
		]);
	}

	local Function is sendResponse(Socket is client, Int is status, String is contentType, Map of String to String is extraHeaders, String is body){
		local String is hdr: 'HTTP/1.1 ' . (status as String) . ' ' . statusReason(code: status) . "\r\n"
			. 'Content-Type: ' . contentType . "\r\n"
			. 'Content-Length: ' . (body:byteLength() as String) . "\r\n"
			. "Connection: close\r\n"
			. "Server: SpecServ/0.1\r\n";
		local Array of String is keys: extraHeaders:keys();
		times(count: keys:length(), worker: local Function(Int is i){
			local String is k: keys:get(index: i, default: '');
			local String is kl: k:toLower();
			if({ kl != 'content-type' && kl != 'content-length' && kl != 'connection' }, {
				hdr: hdr . k . ': ' . extraHeaders:getString(key: k, default: '') . "\r\n";
			});
		});
		hdr: hdr . "\r\n";
		client:sendString(text: hdr, onError: local Function(SpecError is _e){});
		if({ body:byteLength() > 0 }, {
			client:sendString(text: body, onError: local Function(SpecError is _e){});
		});
	}

	local Function of String is resolvePath(String is urlPath){
		local String is rel: urlPath;
		if({ rel == '' || rel == '/' }, {
			rel: '/index.html';
		});
		if({ rel:contains(needle: '..') || rel:contains(needle: "\\") }, {
			return '';
		});
		local String is root: site:directory;
		while({ root:endsWith(suffix: '/') && root:length() > 1 }, {
			root: root:substring(start: 0, end: root:length() - 1);
		});
		if({ !rel:startsWith(prefix: '/') }, { rel: '/' . rel; });
		return root . rel;
	}

	local Function is handleClient(Socket is client){
		client:setTimeout(timeoutMs: 3000);
		local String is raw: '';
		local Int is sep: -1;
		local Int is reads: 0;
		while({ sep < 0 && reads < 16 }, {
			local String is chunk: client:receiveString(maxBytes: 8192, onError: local Function(SpecError is _e){});
			if({ chunk == '' }, {
				reads: 16;
			}, {
				raw: raw . chunk;
				sep: raw:indexOf(search: "\r\n\r\n", default: -1);
				reads++;
			});
		});
		if({ sep < 0 }, {
			client:close();
			return;
		});

		local String is rawHead: raw:substring(start: 0, end: sep);
		local String is bodyBuf: raw:substring(start: sep + 4, end: raw:length());
		local HttpRequestParser is req: HttpRequestParser():parse(rawHead: rawHead, bodyText: bodyBuf);
		if({ !req:valid }, {
			sendResponse(client: client, status: 400, contentType: 'text/plain; charset=utf-8', extraHeaders: Map:init(), body: '400 Bad Request');
			client:close();
			return;
		});

		while({ bodyBuf:byteLength() < req:contentLength }, {
			local String is more: client:receiveString(maxBytes: 8192, onError: local Function(SpecError is _e){});
			if({ more == '' }, {
				req:contentLength: bodyBuf:byteLength();
			}, {
				bodyBuf: bodyBuf . more;
			});
		});
		if({ req:method == 'POST' && bodyBuf != req:body }, {
			req:postArgs: HttpRequestParser():parseFormParams(raw: bodyBuf);
		});

		local Int is startNs: monotonicNs();
		local String is fsPath: resolvePath(urlPath: req:path);
		if({ fsPath == '' }, {
			sendResponse(client: client, status: 403, contentType: 'text/plain; charset=utf-8', extraHeaders: Map:init(), body: '403 Forbidden');
			client:close();
			emitLog(msg: ':' . (site:port as String) . ' ' . req:method . ' ' . req:path . ' -> 403 (' . formatDuration(elapsedNs: monotonicNs() - startNs) . ')');
			return;
		});

		if({ !fileExists(path: fsPath) }, {
			if({ fileExists(path: fsPath . '/index.html') }, {
				fsPath: fsPath . '/index.html';
			}, {
				sendResponse(client: client, status: 404, contentType: 'text/html; charset=utf-8', extraHeaders: Map:init(), body: '<h1>404 Not Found</h1><p>' . req:path . '</p>');
				client:close();
				emitLog(msg: ':' . (site:port as String) . ' ' . req:method . ' ' . req:path . ' -> 404 (' . formatDuration(elapsedNs: monotonicNs() - startNs) . ')');
				return;
			});
		});

		if({ fsPath:endsWith(suffix: '.spec') }, {
			local SpecPageRunner is pr: SpecPageRunner():runPage(specPath: fsPath, docRoot: site:directory, getArgs: req:getArgs, postArgs: req:postArgs);
			if({ !pr:ok }, {
				sendResponse(client: client, status: pr:statusCode, contentType: 'text/plain; charset=utf-8', extraHeaders: Map:init(), body: pr:errorMessage);
				client:close();
				emitLog(msg: ':' . (site:port as String) . ' ' . req:method . ' ' . req:path . ' -> ' . (pr:statusCode as String) . ' (' . formatDuration(elapsedNs: monotonicNs() - startNs) . ')');
				return;
			});
			sendResponse(client: client, status: pr:statusCode, contentType: pr:contentType, extraHeaders: pr:headers, body: pr:body);
			client:close();
			emitLog(msg: ':' . (site:port as String) . ' ' . req:method . ' ' . req:path . ' -> ' . (pr:statusCode as String) . ' (' . formatDuration(elapsedNs: monotonicNs() - startNs) . ')');
			return;
		});

		local String is content: fileRead(path: fsPath, onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');
		local String is mime: MimeTypes():forPath(path: fsPath);
		sendResponse(client: client, status: 200, contentType: mime, extraHeaders: Map:init(), body: content);
		client:close();
		emitLog(msg: ':' . (site:port as String) . ' ' . req:method . ' ' . req:path . ' -> 200 (' . formatDuration(elapsedNs: monotonicNs() - startNs) . ')');
	}

	Function is serveLoop(){
		local Boolean is listenOk: true;
		local Socket is listener: listen(host: '127.0.0.1', port: site:port, onError: local Function(SpecError of NetError is err){
			listenOk: false;
			emitLog(msg: 'Failed to bind :' . (site:port as String) . ': ' . err:description);
		});
		if({ !listenOk || !listener:isOpen() }, {
			running: false;
			return;
		});

		running: true;
		emitLog(msg: 'Serving ' . site:directory . ' at http://localhost:' . (site:port as String));
		while({ running }, {
			local Boolean is stopped: stopSignal:tryReceive(default: false);
			if({ stopped }, {
				running: false;
			}, {
				if({ listener:poll(mode: 1, timeoutMs: 80) }, {
					local Boolean is accOk: true;
					local Socket is client: listener:accept(onError: local Function(SpecError of NetError is _e){
						accOk: false;
					});
					if({ accOk && client:isOpen() }, {
						handleClient(client: client);
					});
				});
			});
		});
		listener:close();
		emitLog(msg: 'Stopped :' . (site:port as String));
	}

	Function is requestStop(){
		running: false;
		stopSignal:send(item: true);
	}
}
