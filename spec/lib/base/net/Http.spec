#! Package base:net
#! Pure-Spec async HTTP/1.1 client over base:net:Socket and base:net:tls:TlsClient.
#! Every request executes on a ThreadScope worker thread with onSuccess / onError callbacks.

Class is Http{
	namespace: ['base', 'net'];

	replace Array of Array of String is using: [
		['base', 'net', HttpResponse],
		['base', 'net', Socket],
		['base', 'net', 'tls', TlsClient],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'struct', Array],
		['base', 'struct', List]
	];

	local Function of Boolean is hasClosure(Function is cb){
		local Int is addr: Mem:objToAddr(obj: cb);
		if({ addr == 0 }, { return false; });
		return Mem:loadI64(ptr: addr, byteOffset: 0) != 0;
	}

	local Function of String is decodeChunked(String is raw){
		local [Byte] is out;
		local Int is pos: 0;
		local Int is n: raw:byteLength();
		local Boolean is done: false;
		while({ !done && pos < n }, {
			local Int is crlf: raw:indexOfFrom(search: "\r\n", start: pos, default: -1);
			if({ crlf < 0 }, {
				done: true;
			}, {
				local String is sizeLine: raw:substring(start: pos, end: crlf):trim();
				local Int is semi: sizeLine:indexOf(search: ';', default: -1);
				if({ semi >= 0 }, {
					sizeLine: sizeLine:substring(start: 0, end: semi):trim();
				});
				local Int is chunkSize: sizeLine:parseInt(base: 16, default: 0);
				pos: crlf + 2;
				if({ chunkSize <= 0 }, {
					done: true;
				}, {
					local Int is i: 0;
					while({ i < chunkSize && (pos + i) < n }, {
						out:push((raw:byteAt(index: pos + i, default: 0) & 255) as Byte);
						i: i + 1;
					});
					pos: pos + chunkSize + 2;
				});
			});
		});
		return out:toString();
	}

	local Function of HttpResponse is fetchSync(String is url, Function is onSuccess, Function is onError, String is userAgent){
		local Boolean is useTls: false;
		local String is rest: url;
		if({ rest:startsWith(prefix: 'https://') }, {
			useTls: true;
			rest: rest:substring(start: 8, end: rest:length());
		}, {
			if({ rest:startsWith(prefix: 'http://') }, {
				rest: rest:substring(start: 7, end: rest:length());
			});
		});

		local Int is slashIdx: rest:indexOf(search: '/', default: -1);
		local String is hostPort: if({ slashIdx >= 0 }, { rest:substring(start: 0, end: slashIdx) }, { rest });
		local String is path: if({ slashIdx >= 0 }, { rest:substring(start: slashIdx, end: rest:length()) }, { '/' });

		local String is host: hostPort;
		local Int is port: if({ useTls }, { 443 }, { 80 });
		local Int is colonIdx: hostPort:indexOf(search: ':', default: -1);
		if({ colonIdx >= 0 }, {
			host: hostPort:substring(start: 0, end: colonIdx);
			port: hostPort:substring(start: colonIdx + 1, end: hostPort:length()):parseInt(default: port);
		});

		local String is req: 'GET ' . path . " HTTP/1.1\r\n"
			. 'Host: ' . host . "\r\n"
			. 'User-Agent: ' . userAgent . "\r\n"
			. "Accept: application/geo+json, application/json, */*\r\n"
			. "Accept-Encoding: identity\r\n"
			. "Connection: close\r\n\r\n";

		local String is rawResp: '';
		if({ useTls }, {
			local TlsClient is tls: TlsClient:init();
			if({ !tls:connect(host: host, port: port, timeoutMs: 15000) }, {
				local String is err: 'TLS connect failed: ' . tls:lastError();
				if({ :hasClosure(cb: onError) }, { onError(err); });
				return HttpResponse:init(status: 0, body: '');
			});
			if({ !tls:sendString(text: req) }, {
				local String is err: 'TLS send failed: ' . tls:lastError();
				tls:close();
				if({ :hasClosure(cb: onError) }, { onError(err); });
				return HttpResponse:init(status: 0, body: '');
			});
			rawResp: tls:recvAllString();
			tls:close();
		}, {
			local String is errMsg: '';
			local Socket is sock: Socket:init():connect(host: host, port: port, timeoutMs: 15000, onError: local Function(String is e){
				errMsg: e;
			});
			if({ !sock:isOpen() }, {
				local String is err: if({ errMsg != '' }, { errMsg }, { 'TCP connect failed to ' . host });
				if({ :hasClosure(cb: onError) }, { onError(err); });
				return HttpResponse:init(status: 0, body: '');
			});
			sock:setTimeout(timeoutMs: 15000);
			sock:sendString(text: req);
			local [Byte] is acc;
			local Boolean is reading: true;
			while({ reading }, {
				local List of Byte is chunk: sock:receive(maxBytes: 16384);
				if({ chunk:length() == 0 }, {
					reading: false;
				}, {
					local Int is ci: 0;
					while({ ci < chunk:length() }, {
						acc:push(chunk:get(index: ci, default: 0 as Byte));
						ci: ci + 1;
					});
				});
			});
			sock:close();
			rawResp: acc:toString();
		});

		local Int is sep: rawResp:indexOf(search: "\r\n\r\n", default: -1);
		if({ sep < 0 }, {
			local String is err: 'Invalid HTTP response (missing header separator)';
			if({ :hasClosure(cb: onError) }, { onError(err); });
			return HttpResponse:init(status: 0, body: rawResp);
		});

		local String is headerBlock: rawResp:substring(start: 0, end: sep);
		local String is body: rawResp:substring(start: sep + 4, end: rawResp:length());

		local Int is firstNl: headerBlock:indexOf(search: "\r\n", default: headerBlock:length());
		local String is statusLine: headerBlock:substring(start: 0, end: firstNl);
		local Array of String is statusParts: statusLine:split(delimiter: ' ');
		local Int is status: if({ statusParts:length() >= 2 }, { statusParts:get(index: 1, default: '0'):parseInt(default: 0) }, { 0 });

		if({ headerBlock:toLower():contains(needle: 'transfer-encoding: chunked') }, {
			body: :decodeChunked(raw: body);
		});

		local HttpResponse is resp: HttpResponse:init(status: status, body: body);
		if({ status < 200 || status >= 400 }, {
			local String is msg: 'HTTP ' . (status as String) . ' for ' . url;
			if({ :hasClosure(cb: onError) }, { onError(msg); });
			return resp;
		});
		if({ :hasClosure(cb: onSuccess) }, { onSuccess(resp); });
		return resp;
	}

	## Performs an asynchronous HTTP/HTTPS GET inside [scope], invoking
	## [onSuccess](HttpResponse) or [onError](String) on the worker thread.
	Function of Task of HttpResponse is get(ThreadScope is scope, String is url, Function is onSuccess: local Function(HttpResponse is _r){}, Function is onError: local Function(String is _e){}, String is userAgent: 'SpecNet/0.1'){
		return scope:spawn(task: local Function of HttpResponse(){
			return :fetchSync(url: url, onSuccess: onSuccess, onError: onError, userAgent: userAgent);
		});
	}
}
