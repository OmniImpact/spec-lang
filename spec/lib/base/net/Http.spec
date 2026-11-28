#! Package base:net
#! Pure-Spec async HTTP/1.1 client over base:net:Socket and base:net:tls:TlsClient.
#! Every request executes on a ThreadScope worker thread with onSuccess / onError callbacks.

Class is Http{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', HttpError],
		['base', 'net', Url],
		['base', 'net', HttpRequest],
		['base', 'net', HttpResponse],
		['base', 'net', Socket],
		['base', 'net', 'tls', TlsClient],
		['base', 'net', 'tls', TlsError],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'struct', Array],
		['base', 'struct', List],
		['base', 'struct', Map]
	];

	local Function of String is decodeChunked(String is raw){
		local [Byte] is out;
		local Int is pos: 0;
		local Int is n: raw:byteLength();
		while({ pos < n }, local Function of Boolean(){
			local Int is crlf: raw:indexOfFrom(search: "\r\n", from: pos, default: -1);
			if({ crlf < 0 }, {
				return false;
			});
			local String is sizeLine: raw:substring(start: pos, end: crlf):trim();
			local Int is semi: sizeLine:indexOf(search: ';', default: -1);
			if({ semi >= 0 }, {
				sizeLine: sizeLine:substring(start: 0, end: semi):trim();
			});
			local Int is chunkSize: sizeLine:parseInt(base: 16, default: 0);
			pos: crlf + 2;
			if({ chunkSize <= 0 }, {
				return false;
			});
			local Int is endPos: if({ pos + chunkSize > n }, { n }, { pos + chunkSize });
			out:appendString(raw:substring(start: pos, end: endPos));
			pos: pos + chunkSize + 2;
			return true;
		});
		return out:toString();
	}

	local Function of String is buildRawRequest(Url is u, HttpRequest is req){
		local String is out: req:method . ' ' . u:requestTarget() . " HTTP/1.1\r\n"
			. 'Host: ' . u:hostHeader() . "\r\n";

		local Boolean is hasUa: false;
		local Boolean is hasAccept: false;
		local Boolean is hasAcceptEnc: false;
		local Boolean is hasConn: false;
		local Boolean is hasContentLen: false;

		local Array of String is hKeys: req:headers:keys();
		local Int is i: 0;
		while({ i < hKeys:length() }, {
			local String is k: hKeys:get(index: i, default: '');
			local String is v: req:headers:getString(key: k, default: '');
			local String is kl: k:toLower();
			if({ kl == 'user-agent' }, { hasUa: true; });
			if({ kl == 'accept' }, { hasAccept: true; });
			if({ kl == 'accept-encoding' }, { hasAcceptEnc: true; });
			if({ kl == 'connection' }, { hasConn: true; });
			if({ kl == 'content-length' }, { hasContentLen: true; });
			out: out . k . ': ' . v . "\r\n";
			i: i + 1;
		});

		if({ !hasUa }, { out: out . "User-Agent: SpecNet/0.1\r\n"; });
		if({ !hasAccept }, { out: out . "Accept: application/geo+json, application/json, */*\r\n"; });
		if({ !hasAcceptEnc }, { out: out . "Accept-Encoding: identity\r\n"; });
		if({ !hasConn }, { out: out . "Connection: close\r\n"; });
		if({ !hasContentLen && req:body:byteLength() > 0 }, {
			out: out . 'Content-Length: ' . (req:body:byteLength() as String) . "\r\n";
		});

		return out . "\r\n" . req:body;
	}

	local Function of HttpResponse is parseResponse(String is rawResp){
		local Int is sep: rawResp:indexOf(search: "\r\n\r\n", default: -1);
		if({ sep < 0 }, {
			return HttpResponse:init(status: 0, statusText: 'Invalid HTTP response', body: rawResp);
		});

		local String is headerBlock: rawResp:substring(start: 0, end: sep);
		local String is body: rawResp:substring(start: sep + 4, end: rawResp:length());
		local Array of String is lines: headerBlock:split(delimiter: "\r\n");

		local Int is status: 0;
		local String is statusText: '';
		if({ lines:length() > 0 }, {
			local String is sLine: lines:get(index: 0, default: '');
			local Int is sp1: sLine:indexOf(search: ' ', default: -1);
			if({ sp1 >= 0 }, {
				local String is afterProto: sLine:substring(start: sp1 + 1, end: sLine:length()):trim();
				local Int is sp2: afterProto:indexOf(search: ' ', default: -1);
				if({ sp2 >= 0 }, {
					status: afterProto:substring(start: 0, end: sp2):parseInt(default: 0);
					statusText: afterProto:substring(start: sp2 + 1, end: afterProto:length()):trim();
				}, {
					status: afterProto:parseInt(default: 0);
				});
			});
		});

		local HttpResponse is resp: HttpResponse:init(status: status, statusText: statusText, body: '');
		local Int is li: 1;
		while({ li < lines:length() }, {
			local String is ln: lines:get(index: li, default: '');
			local Int is col: ln:indexOf(search: ':', default: -1);
			if({ col > 0 }, {
				local String is hName: ln:substring(start: 0, end: col):trim():toLower();
				local String is hVal: ln:substring(start: col + 1, end: ln:length()):trim();
				resp:headers:set(key: hName, value: hVal);
			});
			li: li + 1;
		});

		if({ resp:header(name: 'transfer-encoding'):toLower():contains(needle: 'chunked') }, {
			body: :decodeChunked(raw: body);
		}, {
			local String is clStr: resp:header(name: 'content-length');
			if({ clStr != '' }, {
				local Int is cl: clStr:parseInt(default: -1);
				if({ cl >= 0 && cl < body:byteLength() }, {
					body: body:substring(start: 0, end: cl);
				});
			});
		});

		resp:body: body;
		return resp;
	}

	local Function of String is exchangeOnce(Url is u, String is rawReq, Int is timeoutMs, Array of SpecError of HttpError is errOut){
		if({ u:isHttps() }, {
			local TlsClient is tls: TlsClient:init();
			local String is tlsErr: '';
			if({ !tls:connect(host: u:host, port: u:port, timeoutMs: timeoutMs, onError: local Function(SpecError of TlsError is e){
				tlsErr: e:description;
			}) }, {
				errOut:add(item: SpecError:init(kind: HttpError:CONNECTION_FAILED, description: 'TLS connect failed: ' . tlsErr));
				return '';
			});
			if({ !tls:sendString(text: rawReq, onError: local Function(SpecError of TlsError is e){
				tlsErr: e:description;
			}) }, {
				errOut:add(item: SpecError:init(kind: HttpError:SEND_FAILED, description: 'TLS send failed: ' . tlsErr));
				tls:close();
				return '';
			});
			local String is raw: tls:recvAllString();
			tls:close();
			return raw;
		});

		local String is errMsg: '';
		local Socket is sock: Socket:init():connect(host: u:host, port: u:port, timeoutMs: timeoutMs, onError: local Function(SpecError of NetError is e){
			errMsg: e:description;
		});
		if({ !sock:isOpen() }, {
			local String is eStr: if({ errMsg != '' }, { errMsg }, { 'TCP connect failed to ' . u:host });
			errOut:add(item: SpecError:init(kind: HttpError:CONNECTION_FAILED, description: eStr));
			return '';
		});
		sock:setTimeout(timeoutMs: timeoutMs);
		sock:sendString(text: rawReq);
		local [Byte] is acc;
		while({ true }, local Function of Boolean(){
			local List of Byte is chunk: sock:receive(maxBytes: 16384);
			if({ chunk:length() == 0 }, {
				return false;
			});
			acc:appendBytes(chunk);
			return true;
		});
		sock:close();
		return acc:toString();
	}

	local Function of HttpResponse is sendSync(HttpRequest is req, Function is onSuccess, Function is onError){
		local Url is curUrl: Url:parse(raw: req:url);
		local HttpRequest is curReq: req;
		local Int is hops: 0;
		local HttpResponse is resp: HttpResponse:init(status: 0, body: '');

		while({ hops <= req:maxRedirects }, local Function of Boolean(){
			local String is rawReq: :buildRawRequest(u: curUrl, req: curReq);
			local Array of SpecError of HttpError is errOut: Array();
			local String is rawResp: :exchangeOnce(u: curUrl, rawReq: rawReq, timeoutMs: curReq:timeoutMs, errOut: errOut);
			if({ errOut:length() > 0 }, {
				if({ Mem:hasClosure(cb: onError) }, { onError(errOut:get(index: 0)); });
				resp: HttpResponse:init(status: 0, body: '');
				return false;
			});
			resp: :parseResponse(rawResp: rawResp);
			if({ resp:status == 0 }, {
				if({ Mem:hasClosure(cb: onError) }, { onError(SpecError:init(kind: HttpError:INVALID_RESPONSE, description: 'Invalid HTTP response from ' . curUrl:toString())); });
				return false;
			});
			if({ resp:isRedirect() && hops < req:maxRedirects }, {
				local String is loc: resp:header(name: 'location');
				if({ loc != '' }, {
					curUrl: curUrl:resolve(location: loc);
					if({ resp:status == 303 }, {
						curReq: HttpRequest:init(method: 'GET', url: curUrl:toString(), timeoutMs: curReq:timeoutMs, maxRedirects: curReq:maxRedirects);
					});
					hops: hops + 1;
					return true;
				});
			});
			return false;
		});

		if({ resp:status == 0 }, {
			return resp;
		});
		if({ resp:status < 200 || resp:status >= 400 }, {
			local String is msg: 'HTTP ' . (resp:status as String) . ' for ' . curUrl:toString();
			if({ Mem:hasClosure(cb: onError) }, { onError(SpecError:init(kind: HttpError:HTTP_ERROR, description: msg)); });
			return resp;
		});
		if({ Mem:hasClosure(cb: onSuccess) }, { onSuccess(resp); });
		return resp;
	}

	## Sends an asynchronous [HttpRequest] inside [scope], invoking
	## [onSuccess](HttpResponse) or [onError] (a `SpecError of HttpError`)
	## on the worker thread.
	Function of Task of HttpResponse is send(ThreadScope is scope, HttpRequest is request, Function is onSuccess: local Function(HttpResponse is _r){}, Function is onError: local Function(SpecError of HttpError is e){ :raiseError(error: e); }){
		return scope:spawn(task: local Function of HttpResponse(){
			return :sendSync(req: request, onSuccess: onSuccess, onError: onError);
		});
	}

	## Performs an asynchronous HTTP/HTTPS GET inside [scope], invoking
	## [onSuccess](HttpResponse) or [onError] (a `SpecError of HttpError`)
	## on the worker thread.
	Function of Task of HttpResponse is get(ThreadScope is scope, String is url, Function is onSuccess: local Function(HttpResponse is _r){}, Function is onError: local Function(SpecError of HttpError is e){ :raiseError(error: e); }, String is userAgent: 'SpecNet/0.1'){
		local HttpRequest is req: HttpRequest:init(method: 'GET', url: url);
		req:setHeader(name: 'User-Agent', value: userAgent);
		return :send(scope: scope, request: req, onSuccess: onSuccess, onError: onError);
	}

	## Performs an asynchronous HTTP/HTTPS POST inside [scope], invoking
	## [onSuccess](HttpResponse) or [onError] (a `SpecError of HttpError`)
	## on the worker thread.
	Function of Task of HttpResponse is post(ThreadScope is scope, String is url, String is body, String is contentType: 'application/json', Function is onSuccess: local Function(HttpResponse is _r){}, Function is onError: local Function(SpecError of HttpError is e){ :raiseError(error: e); }, String is userAgent: 'SpecNet/0.1'){
		local HttpRequest is req: HttpRequest:init(method: 'POST', url: url);
		req:setHeader(name: 'User-Agent', value: userAgent);
		req:withBody(body: body, contentType: contentType);
		return :send(scope: scope, request: req, onSuccess: onSuccess, onError: onError);
	}
}
