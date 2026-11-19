#! Unit and local loopback integration tests for base:net (Url, HttpRequest,
#! HttpResponse, and async Http:get / Http:post with redirects & chunked bodies).

Class of SpecUnitTest is TestHttp{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'core', SpecError],
		['base', 'net', Url],
		['base', 'net', HttpRequest],
		['base', 'net', HttpResponse],
		['base', 'net', Socket],
		['base', 'net', as Http()],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Process()]
	];

	Function is testUrlParseAndResolve(){
		local Url is u: Url:parse(raw: 'https://api.weather.gov/gridpoints/RAH/74,58/forecast?units=us#top');
		Assert:areEqualString('https', u:scheme);
		Assert:areEqualString('api.weather.gov', u:host);
		Assert:areEqualInt(443, u:port);
		Assert:areEqualString('/gridpoints/RAH/74,58/forecast', u:path);
		Assert:areEqualString('units=us', u:query);
		Assert:areEqualString('/gridpoints/RAH/74,58/forecast?units=us', u:requestTarget());
		Assert:areEqualString('api.weather.gov', u:hostHeader());
		Assert:isTrue(u:isHttps());

		local Url is r1: u:resolve(location: '/v2/alerts');
		Assert:areEqualString('https://api.weather.gov/v2/alerts', r1:toString());

		local Url is r2: u:resolve(location: 'hourly');
		Assert:areEqualString('https://api.weather.gov/gridpoints/RAH/74,58/hourly', r2:toString());

		local Url is r3: Url:parse(raw: 'http://127.0.0.1:8080/api');
		Assert:areEqualString('127.0.0.1:8080', r3:hostHeader());
		Assert:isFalse(r3:isHttps());
	}

	Function is testLoopbackGetRedirectChunkedAndPost(){
		local Int is port: 19400 + (Process:getPid() % 1000);
		local Socket is server: Socket:init():listen(host: '127.0.0.1', port: port, backlog: 8);
		Assert:isTrue(server:isOpen());

		local String is getBody: '';
		local Int is getStatus: 0;
		local String is getHeaderVal: '';
		local String is postBody: '';
		local Int is postStatus: 0;

		ThreadScope:open(body: local Function(ThreadScope is scope){
			# Mini HTTP/1.1 test server handling 3 requests:
			# 1. GET /old -> 302 Location: /final
			# 2. GET /final -> 200 Transfer-Encoding: chunked
			# 3. POST /echo -> 200 echoes request body
			scope:spawn(task: local Function(){
				local Int is handled: 0;
				while({ handled < 3 }, {
					local Socket is c: server:accept();
					if({ c:isOpen() }, {
						local String is raw: c:receiveString(maxBytes: 4096);
						if({ raw:startsWith(prefix: 'GET /old ') }, {
							c:sendString(text: "HTTP/1.1 302 Found\r\nLocation: /final\r\nContent-Length: 0\r\nConnection: close\r\n\r\n");
						}, {
							if({ raw:startsWith(prefix: 'GET /final ') }, {
								c:sendString(text: "HTTP/1.1 200 OK\r\nX-Spec-Test: hello-net\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n5\r\nHello\r\n7\r\n, Spec!\r\n0\r\n\r\n");
							}, {
								local Int is sep: raw:indexOf(search: "\r\n\r\n", default: -1);
								local String is reqBody: if({ sep >= 0 }, { raw:substring(start: sep + 4, end: raw:length()) }, { '' });
								local String is respStr: "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " . (reqBody:byteLength() as String) . "\r\nConnection: close\r\n\r\n" . reqBody;
								c:sendString(text: respStr);
							});
						});
						c:close();
						handled: handled + 1;
					});
				});
			});

			local String is baseUrl: 'http://127.0.0.1:' . (port as String);
			local Task of HttpResponse is t1: Http:get(
				scope: scope,
				url: baseUrl . '/old',
				onSuccess: local Function(HttpResponse is r){
					getStatus: r:status;
					getBody: r:body;
					getHeaderVal: r:header(name: 'X-Spec-Test');
				}
			);
			t1:await();

			local Task of HttpResponse is t2: Http:post(
				scope: scope,
				url: baseUrl . '/echo',
				body: '{"ok":true}',
				onSuccess: local Function(HttpResponse is r){
					postStatus: r:status;
					postBody: r:body;
				}
			);
			t2:await();
		});

		server:close();

		Assert:areEqualInt(200, getStatus);
		Assert:areEqualString('Hello, Spec!', getBody);
		Assert:areEqualString('hello-net', getHeaderVal);
		Assert:areEqualInt(200, postStatus);
		Assert:areEqualString('{"ok":true}', postBody);
	}
}
