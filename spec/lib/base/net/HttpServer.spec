#! Package base:net
#! Reusable HTTP/1.1 & HTTPS (TLS 1.3) server over `Socket`, `TlsServer`, and `ThreadScope`.

Class is HttpServer{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', Socket],
		['base', 'net', NetError],
		['base', 'net', HttpRequest],
		['base', 'net', HttpResponse],
		['base', 'net', 'tls', TlsServer],
		['base', 'net', 'tls', TlsServerSession],
		['base', 'struct', Array],
		['base', 'struct', List],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as File()],
		['base', 'sys', as Mem()],
		['base', 'sys', 'thread', ThreadScope]
	];

	local Socket is tcpListener: Socket:init();
	local TlsServer is tlsListener: TlsServer:init();
	local Boolean is useTls: false;
	local Boolean is running: false;
	local Int is clientTimeoutMs: 15000;
	local Map of String to Function is routes: Map:init();
	local Function is fallbackHandler: local Function of HttpResponse(HttpRequest is _req){
		return HttpResponse:init(status: 404, statusText: 'Not Found', body: 'Not Found');
	};

	replace Function is init(Int is timeoutMs: 15000){
		:tcpListener: Socket:init();
		:tlsListener: TlsServer:init();
		:useTls: false;
		:running: false;
		:clientTimeoutMs: timeoutMs;
		:routes: Map:init();
	}

	## Registers a handler closure `Function of HttpResponse(HttpRequest is req)` for [method] and [path].
	Function is route(String is method, String is path, Function is handler){
		local String is key: method:toUpper() . ' ' . path;
		:routes:set(key: key, value: handler);
	}

	## Sets the fallback handler invoked when no exact route matches.
	Function is setHandler(Function is handler){
		:fallbackHandler: handler;
	}

	## Starts listening for plain HTTP/1.1 on [host]:[port] (`port: 0` selects an ephemeral port).
	Function of Boolean is listen(String is host: '0.0.0.0', Int is port: 8080, Int is backlog: 128){
		:useTls: false;
		local Boolean is failed: false;
		:tcpListener: Socket:init():listen(host: host, port: port, backlog: backlog, onError: local Function(SpecError of NetError is _e){
			failed: true;
		});
		if({ failed || !:tcpListener:isOpen() }, { return false; });
		:running: true;
		return true;
	}

	## Starts listening for HTTPS (TLS 1.3) on [host]:[port] with DER [certChain] and 32-byte [ed25519Seed].
	Function of Boolean is listenTls(String is host: '0.0.0.0', Int is port: 8443, Array of Array of Int is certChain, Array of Int is ed25519Seed, Int is backlog: 128){
		:useTls: true;
		:tlsListener: TlsServer:init();
		:tlsListener:setCredentials(certChain: certChain, ed25519Seed: ed25519Seed);
		if({ !:tlsListener:listen(host: host, port: port, backlog: backlog) }, { return false; });
		:running: true;
		return true;
	}

	Function of Int is localPort(){
		if({ :useTls }, { return :tlsListener:localPort(); });
		return :tcpListener:localPort();
	}

	Function is stop(){
		:running: false;
		if({ :useTls }, {
			:tlsListener:close();
		}, {
			:tcpListener:close();
		});
	}

	local Function of String is defaultStatusText(Int is code){
		if({ code == 200 }, { return 'OK'; });
		if({ code == 201 }, { return 'Created'; });
		if({ code == 204 }, { return 'No Content'; });
		if({ code == 301 }, { return 'Moved Permanently'; });
		if({ code == 302 }, { return 'Found'; });
		if({ code == 400 }, { return 'Bad Request'; });
		if({ code == 403 }, { return 'Forbidden'; });
		if({ code == 404 }, { return 'Not Found'; });
		if({ code == 405 }, { return 'Method Not Allowed'; });
		if({ code == 500 }, { return 'Internal Server Error'; });
		return 'OK';
	}

	local Function of HttpRequest is parseRawRequest(String is raw){
		local HttpRequest is req: HttpRequest:init();
		local Int is sep: raw:indexOf(search: "\r\n\r\n", default: -1);
		local String is head: if({ sep >= 0 }, { raw:substring(start: 0, end: sep) }, { raw });
		local String is body: if({ sep >= 0 }, { raw:substring(start: sep + 4, end: raw:length()) }, { '' });
		req:body: body;

		local Int is firstNl: head:indexOf(search: "\r\n", default: -1);
		local String is reqLine: if({ firstNl >= 0 }, { head:substring(start: 0, end: firstNl) }, { head });
		local Int is sp1: reqLine:indexOf(search: ' ', default: -1);
		if({ sp1 > 0 }, {
			req:method: reqLine:substring(start: 0, end: sp1):trim():toUpper();
			local Int is sp2: reqLine:indexOfFrom(search: ' ', from: sp1 + 1, default: -1);
			if({ sp2 > sp1 }, {
				req:url: reqLine:substring(start: sp1 + 1, end: sp2):trim();
			}, {
				req:url: reqLine:substring(start: sp1 + 1, end: reqLine:length()):trim();
			});
		});

		if({ firstNl >= 0 }, {
			local Int is pos: firstNl + 2;
			local Int is hLen: head:length();
			while({ pos < hLen }, {
				local Int is nl: head:indexOfFrom(search: "\r\n", from: pos, default: -1);
				local Int is lineEnd: if({ nl >= 0 }, { nl }, { hLen });
				local String is line: head:substring(start: pos, end: lineEnd);
				local Int is colon: line:indexOf(search: ':', default: -1);
				if({ colon > 0 }, {
					local String is k: line:substring(start: 0, end: colon):trim():toLower();
					local String is v: line:substring(start: colon + 1, end: line:length()):trim();
					req:headers:set(key: k, value: v);
				});
				pos: if({ nl >= 0 }, { nl + 2 }, { hLen });
			});
		});
		return req;
	}

	local Function of String is serializeResponse(HttpResponse is resp){
		local Int is code: if({ resp:status > 0 }, { resp:status }, { 200 });
		local String is stText: if({ resp:statusText != '' }, { resp:statusText }, { :defaultStatusText(code: code) });
		local String is out: 'HTTP/1.1 ' . (code as String) . ' ' . stText . "\r\n";
		local Boolean is hasLen: false;
		local Boolean is hasConn: false;
		local Array of String is ks: resp:headers:keys();
		local Int is i: 0;
		while({ i < ks:length() }, {
			local String is k: ks:get(index: i, default: '');
			local String is kl: k:toLower();
			if({ kl == 'content-length' }, { hasLen: true; });
			if({ kl == 'connection' }, { hasConn: true; });
			out: out . k . ': ' . resp:headers:getString(key: k, default: '') . "\r\n";
			i: i + 1;
		});
		if({ !hasLen }, {
			out: out . 'Content-Length: ' . (resp:body:byteLength() as String) . "\r\n";
		});
		if({ !hasConn }, {
			out: out . "Connection: close\r\n";
		});
		return out . "\r\n" . resp:body;
	}

	local Function of HttpResponse is dispatchRequest(HttpRequest is req){
		local String is path: req:url;
		local Int is qIdx: path:indexOf(search: '?', default: -1);
		if({ qIdx >= 0 }, { path: path:substring(start: 0, end: qIdx); });
		local String is key: req:method:toUpper() . ' ' . path;
		if({ :routes:has(key: key) }, {
			local Function is h: :routes:get(key: key, default: :fallbackHandler);
			if({ Mem:hasClosure(cb: h) }, {
				return h(req) as HttpResponse;
			});
		});
		if({ Mem:hasClosure(cb: :fallbackHandler) }, {
			return :fallbackHandler(req) as HttpResponse;
		});
		return HttpResponse:init(status: 404, statusText: 'Not Found', body: 'Not Found');
	}

	## Serves a static file under [rootDir] for [reqPath], rejecting `..` path traversal.
	Function of HttpResponse is staticFileResponse(String is rootDir, String is reqPath){
		local String is p: reqPath;
		local Int is qIdx: p:indexOf(search: '?', default: -1);
		if({ qIdx >= 0 }, { p: p:substring(start: 0, end: qIdx); });
		if({ p:contains(needle: '..') || p:contains(needle: "\\") }, {
			return HttpResponse:init(status: 403, statusText: 'Forbidden', body: 'Forbidden');
		});
		if({ p == '' || p == '/' }, { p: '/index.html'; });
		local String is fullPath: rootDir . p;
		if({ !File:fileExists(path: fullPath) }, {
			return HttpResponse:init(status: 404, statusText: 'Not Found', body: 'Not Found');
		});
		local String is content: File:fileRead(path: fullPath, onSuccess: local Function(String is _s){}, onError: local Function(SpecError of FileError is _e){}, default: '');
		local HttpResponse is resp: HttpResponse:init(status: 200, statusText: 'OK', body: content);
		resp:headers:set(key: 'Content-Type', value: 'application/octet-stream');
		if({ fullPath:endsWith(suffix: '.html') }, { resp:headers:set(key: 'Content-Type', value: 'text/html; charset=utf-8'); });
		if({ fullPath:endsWith(suffix: '.txt') }, { resp:headers:set(key: 'Content-Type', value: 'text/plain; charset=utf-8'); });
		if({ fullPath:endsWith(suffix: '.json') }, { resp:headers:set(key: 'Content-Type', value: 'application/json'); });
		if({ fullPath:endsWith(suffix: '.css') }, { resp:headers:set(key: 'Content-Type', value: 'text/css; charset=utf-8'); });
		if({ fullPath:endsWith(suffix: '.js') }, { resp:headers:set(key: 'Content-Type', value: 'application/javascript; charset=utf-8'); });
		return resp;
	}

	local Function is handlePlainClient(Socket is client){
		client:setTimeout(timeoutMs: :clientTimeoutMs);
		local String is raw: '';
		local Int is expectedTotal: -1;
		local Boolean is reading: true;
		while({ reading }, {
			local Boolean is err: false;
			local String is chunk: client:receiveString(maxBytes: 8192, onError: local Function(SpecError of NetError is _e){ err: true; });
			if({ err || chunk:byteLength() == 0 }, {
				reading: false;
			}, {
				raw: raw . chunk;
				if({ expectedTotal < 0 }, {
					local Int is sep: raw:indexOf(search: "\r\n\r\n", default: -1);
					if({ sep >= 0 }, {
						local HttpRequest is tmpReq: :parseRawRequest(raw: raw);
						local Int is cl: tmpReq:headers:getString(key: 'content-length', default: '0'):parseInt(default: 0);
						expectedTotal: sep + 4 + cl;
					});
				});
				if({ expectedTotal >= 0 && raw:byteLength() >= expectedTotal }, { reading: false; });
			});
		});
		if({ raw:byteLength() > 0 }, {
			local HttpRequest is req: :parseRawRequest(raw: raw);
			local HttpResponse is resp: :dispatchRequest(req: req);
			client:sendString(text: :serializeResponse(resp: resp), onError: local Function(SpecError of NetError is _e){});
		});
		client:close();
	}

	local Function is handleTlsClient(TlsServerSession is sess){
		if({ !sess:isConnected() }, {
			sess:close();
			return;
		});
		local String is raw: '';
		local Int is expectedTotal: -1;
		local Boolean is reading: true;
		while({ reading }, {
			local String is chunk: sess:recvString();
			if({ chunk:byteLength() == 0 }, {
				reading: false;
			}, {
				raw: raw . chunk;
				if({ expectedTotal < 0 }, {
					local Int is sep: raw:indexOf(search: "\r\n\r\n", default: -1);
					if({ sep >= 0 }, {
						local HttpRequest is tmpReq: :parseRawRequest(raw: raw);
						local Int is cl: tmpReq:headers:getString(key: 'content-length', default: '0'):parseInt(default: 0);
						expectedTotal: sep + 4 + cl;
					});
				});
				if({ expectedTotal >= 0 && raw:byteLength() >= expectedTotal }, { reading: false; });
			});
		});
		if({ raw:byteLength() > 0 }, {
			local HttpRequest is req: :parseRawRequest(raw: raw);
			local HttpResponse is resp: :dispatchRequest(req: req);
			sess:sendString(text: :serializeResponse(resp: resp));
		});
		sess:close();
	}

	## Accepts and serves a single HTTP or HTTPS connection synchronously.
	Function of Boolean is serveOne(){
		if({ !:running }, { return false; });
		if({ :useTls }, {
			local TlsServerSession is sess: :tlsListener:accept(timeoutMs: :clientTimeoutMs);
			if({ !sess:isConnected() }, {
				sess:close();
				return false;
			});
			:handleTlsClient(sess: sess);
			return true;
		});
		local Boolean is err: false;
		local Socket is client: :tcpListener:accept(onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err || !client:isOpen() }, { return false; });
		:handlePlainClient(client: client);
		return true;
	}

	## Runs a concurrent accept loop inside [scope] until `stop()` is called.
	Function is serve(ThreadScope is scope){
		while({ :running }, {
			if({ :useTls }, {
				if({ :tlsListener:poll(timeoutMs: 100) }, {
					local TlsServerSession is sess: :tlsListener:accept(timeoutMs: :clientTimeoutMs);
					if({ sess:isConnected() }, {
						scope:spawn(task: local Function(){
							:handleTlsClient(sess: sess);
						});
					});
				});
			}, {
				if({ :tcpListener:poll(mode: 1, timeoutMs: 100) }, {
					local Boolean is err: false;
					local Socket is client: :tcpListener:accept(onError: local Function(SpecError of NetError is _e){ err: true; });
					if({ !err && client:isOpen() }, {
						scope:spawn(task: local Function(){
							:handlePlainClient(client: client);
						});
					});
				});
			});
		});
	}
}
