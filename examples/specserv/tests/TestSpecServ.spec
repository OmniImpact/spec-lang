#! specunit: suite

Class of SpecUnitTest is TestSpecServ{
	replace [String] is namespace: ['specserv', 'tests'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'core', SpecError],
		['base', 'net', [as Socket(), NetError]],
		['base', 'theo', [TheoBuffer, TheoRenderer]],
		['base', 'sys', [as File(), as Process()]],
		['base', 'sys', 'thread', ThreadScope],
		['specserv', 'model', [ServerConfig, SiteConfig]],
		['specserv', 'server', [HttpRequestParser, MimeTypes, SiteServer]],
		['specserv', 'vm', SpecServViewModel],
		['specserv', 'view', SpecServFrame]
	];

	local Function of String is httpGet(Int is port, String is path){
		local Socket is sock: connect(host: '127.0.0.1', port: port, timeoutMs: 5000);
		sock:setTimeout(timeoutMs: 30000);
		sock:sendString(text: 'GET ' . path . " HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n");
		local String is out: '';
		local Boolean is reading: true;
		while({ reading }, {
			local String is chunk: sock:receiveString(maxBytes: 8192, onError: local Function(SpecError of NetError is _e){});
			if({ chunk == '' }, {
				reading: false;
			}, {
				out: out . chunk;
			});
		});
		sock:close();
		return out;
	}

	Function is testConfigPortAllocationAndJsonRoundTrip(){
		local ServerConfig is cfg: ServerConfig();
		local SiteConfig is s1: cfg:addDirectory(name: 'Docs', directory: 'examples/specserv/site');
		Assert:isTrue(s1:port == 47321);
		local SiteConfig is s2: cfg:addDirectory(name: 'Extra', directory: 'examples/helloworld');
		Assert:isTrue(s2:port == 47322);
		local SiteConfig is s3: cfg:addDirectory(name: 'Clash', directory: 'examples/cleopi', port: 47321);
		Assert:isTrue(s3:port == 47323);

		local String is tmpPath: '/tmp/test_specserv_cfg.json';
		Assert:isTrue(cfg:saveToFile(path: tmpPath));
		local ServerConfig is loaded: ServerConfig():loadFromFile(path: tmpPath);
		fileRemove(path: tmpPath, onError: local Function(SpecError is _e){});
		Assert:isTrue(loaded:sites:length() == 3);
		Assert:isTrue(loaded:sites:get(index: 0):name == 'Docs');
		Assert:isTrue(loaded:sites:get(index: 1):port == 47322);
		Assert:isTrue(loaded:sites:get(index: 2):port == 47323);
	}

	Function is testRequestParserAndMimeTypes(){
		local HttpRequestParser is getReq: HttpRequestParser():parse(rawHead: "GET /search.spec?q=ThreadScope+test%21 HTTP/1.1\r\nHost: localhost");
		Assert:isTrue(getReq:valid);
		Assert:isTrue(getReq:path == '/search.spec');
		Assert:isTrue(getReq:getArgs:getString(key: 'q', default: '') == 'ThreadScope test!');

		local HttpRequestParser is postReq: HttpRequestParser():parse(
			rawHead: "POST /search.spec HTTP/1.1\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 11",
			bodyText: 'q=match+arm'
		);
		Assert:isTrue(postReq:postArgs:getString(key: 'q', default: '') == 'match arm');

		local MimeTypes is mt: MimeTypes();
		Assert:isTrue(mt:forPath(path: 'index.html'):startsWith(prefix: 'text/html'));
		Assert:isTrue(mt:forPath(path: 'styles.css'):startsWith(prefix: 'text/css'));
		Assert:isTrue(mt:forPath(path: 'app.js'):startsWith(prefix: 'application/javascript'));
		Assert:isTrue(mt:forPath(path: 'logo.svg') == 'image/svg+xml');
		Assert:isTrue(mt:forPath(path: 'pic.png') == 'image/png');
		Assert:isTrue(mt:forPath(path: 'notes.txt'):startsWith(prefix: 'text/plain'));
	}

	Function is testTheoGuiFrameRenders(){
		local SpecServViewModel is vm: SpecServViewModel(allowThreads: false, configPath: '/tmp/nonexistent_specserv.json');
		local SpecServFrame is frame: SpecServFrame(vm: vm);
		frame:layout(x: 0, y: 0, w: 100, h: 30);
		local TheoBuffer is buf: TheoBuffer(width: 100, height: 30);
		local TheoRenderer is renderer: TheoRenderer();
		frame:paint(buf: buf, renderer: renderer);
		Assert:isTrue(vm:config:sites:length() >= 1);
		vm:addSite(name: 'TestSite', directory: 'examples/helloworld', portText: '47399');
		Assert:isTrue(vm:config:sites:length() >= 2);
	}

	Function is testLiveStaticAndSpecServePage(){
		local Int is port: 47481;
		local SiteConfig is sc: SiteConfig(name: 'Docs', directory: 'examples/specserv/site', port: port, enabled: true);
		local SiteServer is srv: SiteServer(site: sc);

		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _e){ true },
			body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					srv:serveLoop();
				});

				# Wait briefly for listener to bind
				local Int is tries: 0;
				while({ !srv:running && tries < 50 }, {
					sleep(milliseconds: 20);
					tries++;
				});
				Assert:isTrue(srv:running);

				local String is rHtml: httpGet(port: port, path: '/index.html');
				Assert:isTrue(rHtml:contains(needle: '200 OK'));
				Assert:isTrue(rHtml:contains(needle: 'text/html'));
				Assert:isTrue(rHtml:contains(needle: 'The Spec Programming Language'));

				local String is rCss: httpGet(port: port, path: '/styles.css');
				Assert:isTrue(rCss:contains(needle: 'text/css'));

				local String is rJs: httpGet(port: port, path: '/app.js');
				Assert:isTrue(rJs:contains(needle: 'application/javascript'));

				local String is rSvg: httpGet(port: port, path: '/logo.svg');
				Assert:isTrue(rSvg:contains(needle: 'image/svg+xml'));

				local String is rTxt: httpGet(port: port, path: '/notes.txt');
				Assert:isTrue(rTxt:contains(needle: 'text/plain'));

				local String is rSearch: httpGet(port: port, path: '/search.spec?q=ThreadScope');
				Assert:isTrue(rSearch:contains(needle: '200 OK'));
				Assert:isTrue(rSearch:contains(needle: 'Cache-Control: no-store'));
				Assert:isTrue(rSearch:contains(needle: 'Spec Standard Library'));
				Assert:isTrue(rSearch:contains(needle: 'Spec Language Overview'));

				local String is r404: httpGet(port: port, path: '/missing.html');
				Assert:isTrue(r404:contains(needle: '404 Not Found'));

				local Boolean is sawTimedHtmlLog: false;
				local Boolean is sawTimedSearchLog: false;
				local Boolean is draining: true;
				while({ draining }, {
					local String is lm: srv:logChannel:tryReceive(default: '');
					if({ lm == '' }, {
						draining: false;
					}, {
						local Boolean is hasUnit: lm:contains(needle: 'us)') || lm:contains(needle: 'ms)') || lm:contains(needle: 's)');
						if({ lm:contains(needle: 'GET /index.html -> 200 (') && hasUnit }, {
							sawTimedHtmlLog: true;
						});
						if({ lm:contains(needle: 'GET /search.spec -> 200 (') && hasUnit }, {
							sawTimedSearchLog: true;
						});
					});
				});
				Assert:isTrue(sawTimedHtmlLog);
				Assert:isTrue(sawTimedSearchLog);

				srv:requestStop();
			}
		);
	}

	Function is testViewModelControlsSpecServProcess(){
		if({ !fileExists(path: 'bin/specserv') }, { return; });
		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _e){ true },
			body: local Function(ThreadScope is _scope){
				local SpecServViewModel is vm: SpecServViewModel(allowThreads: true, configPath: '/tmp/nonexistent_vm_ctrl.json');
				vm:config:sites: [] ;
				vm:config:addDirectory(name: 'Docs', directory: 'examples/specserv/site', port: 47482, enabled: true);
				vm:startServers();
				Assert:isTrue(vm:serversRunning);

				local Boolean is ready: false;
				local Int is tries: 0;
				while({ !ready && tries < 60 }, {
					vm:pollLogs();
					local Int is li: 0;
					while({ li < vm:logs:length() }, {
						if({ vm:logs:get(index: li, default: ''):contains(needle: 'Serving ') }, {
							ready: true;
						});
						li++;
					});
					if({ !ready }, {
						sleep(milliseconds: 25);
						tries++;
					});
				});
				Assert:isTrue(ready);

				local String is body: httpGet(port: 47482, path: '/index.html');
				Assert:isTrue(body:contains(needle: '200 OK'));

				local Boolean is sawReqLog: false;
				local Int is ltries: 0;
				while({ !sawReqLog && ltries < 30 }, {
					vm:pollLogs();
					local Int is lj: 0;
					while({ lj < vm:logs:length() }, {
						local String is entry: vm:logs:get(index: lj, default: '');
						if({ entry:contains(needle: ':47482 GET /index.html -> 200 (') }, {
							sawReqLog: true;
						});
						lj++;
					});
					if({ !sawReqLog }, {
						sleep(milliseconds: 25);
						ltries++;
					});
				});
				Assert:isTrue(sawReqLog);

				vm:stopServers();
				Assert:isFalse(vm:serversRunning);
				fileRemove(path: '/tmp/nonexistent_vm_ctrl.json', onError: local Function(SpecError is _e){});
			}
		);
	}
}
