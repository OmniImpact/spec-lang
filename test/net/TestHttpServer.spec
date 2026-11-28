#! specunit: suite

Class of SpecUnitTest is TestHttpServer{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'core', SpecError],
		['base', 'struct', Array],
		['base', 'net', [Http, HttpServer, HttpRequest, HttpResponse, HttpError]],
		['base', 'net', 'tls', TlsClient],
		['base', 'sys', 'thread', [ThreadScope, Task]]
	];

	Function is testHttpServerGetPostAndTraversalGuard(){
		local HttpServer is srv: HttpServer:init(timeoutMs: 5000);
		srv:route(method: 'GET', path: '/ping', handler: local Function of HttpResponse(HttpRequest is _req){
			local HttpResponse is r: HttpResponse:init(status: 200, statusText: 'OK', body: 'pong');
			r:headers:set(key: 'Content-Type', value: 'text/plain');
			return r;
		});
		srv:route(method: 'POST', path: '/echo', handler: local Function of HttpResponse(HttpRequest is req){
			return HttpResponse:init(status: 201, statusText: 'Created', body: 'echo:' . req:body);
		});

		# Traversal rejection on staticFileResponse
		local HttpResponse is badStatic: srv:staticFileResponse(rootDir: '/tmp', reqPath: '/../../etc/passwd');
		Assert:areEqualInt(403, badStatic:status);

		Assert:isTrue(srv:listen(host: '127.0.0.1', port: 0));
		local Int is port: srv:localPort();
		Assert:isTrue(port > 0);

		local Int is stGet: 0;
		local String is bodyGet: '';
		local Int is stPost: 0;
		local String is bodyPost: '';

		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _e){ return false; },
			body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					srv:serveOne();
					srv:serveOne();
				});
				local Http is client: Http:init();
				local Task of HttpResponse is t1: client:get(scope: scope, url: 'http://127.0.0.1:' . (port as String) . '/ping');
				local HttpResponse is r1: t1:await();
				stGet: r1:status;
				bodyGet: r1:body;

				local Task of HttpResponse is t2: client:post(scope: scope, url: 'http://127.0.0.1:' . (port as String) . '/echo', body: 'spec-body', contentType: 'text/plain');
				local HttpResponse is r2: t2:await();
				stPost: r2:status;
				bodyPost: r2:body;
			}
		);
		srv:stop();

		Assert:areEqualInt(200, stGet);
		Assert:areEqualString('pong', bodyGet);
		Assert:areEqualInt(201, stPost);
		Assert:areEqualString('echo:spec-body', bodyPost);
	}

	Function is testHttpsServerWithTls13(){
		local Array of Int is seed: Array([
			11, 22, 33, 44, 55, 66, 77, 88, 99, 100, 101, 102, 103, 104, 105, 106,
			107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122
		]);
		local Array of Array of Int is certs: Array([Array([48, 3, 2, 1, 1])]);

		local HttpServer is srv: HttpServer:init(timeoutMs: 5000);
		srv:route(method: 'GET', path: '/secure', handler: local Function of HttpResponse(HttpRequest is _req){
			return HttpResponse:init(status: 200, statusText: 'OK', body: 'https-ok');
		});
		Assert:isTrue(srv:listenTls(host: '127.0.0.1', port: 0, certChain: certs, ed25519Seed: seed));
		local Int is port: srv:localPort();

		local String is rawResp: '';
		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _e){ return false; },
			body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					srv:serveOne();
				});
				scope:spawn(task: local Function(){
					local TlsClient is cli: TlsClient:init();
					if({ cli:connect(host: '127.0.0.1', port: port, timeoutMs: 5000, verifyCert: false) }, {
						cli:sendString(text: "GET /secure HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n");
						rawResp: cli:recvAllString();
					});
					cli:close();
				});
			}
		);
		srv:stop();

		Assert:isTrue(rawResp:contains(needle: 'HTTP/1.1 200 OK'));
		Assert:isTrue(rawResp:contains(needle: 'https-ok'));
	}
}
