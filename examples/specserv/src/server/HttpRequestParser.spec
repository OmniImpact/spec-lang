#! Package specserv:server
#! HTTP/1.1 request line, header, URL-decoded query string, and form body parser.

Class is HttpRequestParser{
	replace [String] is namespace: ['specserv', 'server'];

	merge [[String]] is using: [
		['base', 'struct', [Array, Map]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is method: 'GET';
	String is path: '/';
	String is rawQuery: '';
	Map of String to String is headers: Map:init();
	Map of String to String is getArgs: Map:init();
	Map of String to String is postArgs: Map:init();
	String is body: '';
	Int is contentLength: 0;
	Boolean is valid: false;

	Function of String is urlDecode(String is s){
		local String is out: '';
		local Int is n: s:length();
		local Int is i: 0;
		while({ i < n }, {
			local String is ch: s:charAt(index: i, default: '');
			if({ ch == '+' }, {
				out: out . ' ';
				i++;
			}, {
				if({ ch == '%' && i + 2 < n }, {
					local Int is code: s:substring(start: i + 1, end: i + 3):parseInt(base: 16, default: -1);
					if({ code >= 0 && code < 128 }, {
						out: out . String:fromCharCode(code: code);
						i: i + 3;
					}, {
						out: out . ch;
						i++;
					});
				}, {
					out: out . ch;
					i++;
				});
			});
		});
		return out;
	}

	Function of Map of String to String is parseFormParams(String is raw){
		local Map of String to String is out: Map:init();
		if({ raw:trim() == '' }, { return out; });
		local Array of String is pairs: raw:split(delimiter: '&');
		times(count: pairs:length(), worker: local Function(Int is i){
			local String is pair: pairs:get(index: i, default: '');
			if({ pair != '' }, {
				local Int is eq: pair:indexOf(search: '=', default: -1);
				if({ eq >= 0 }, {
					local String is k: urlDecode(s: pair:substring(start: 0, end: eq));
					local String is v: urlDecode(s: pair:substring(start: eq + 1, end: pair:length()));
					out:set(key: k, value: v);
				}, {
					out:set(key: urlDecode(s: pair), value: '');
				});
			});
		});
		return out;
	}

	Function of HttpRequestParser is parse(String is rawHead, String is bodyText: ''){
		local HttpRequestParser is req: HttpRequestParser();
		local Int is firstCrlf: rawHead:indexOf(search: "\r\n", default: -1);
		local String is reqLine: if({ firstCrlf >= 0 }, { rawHead:substring(start: 0, end: firstCrlf) }, { rawHead });
		local Array of String is parts: reqLine:trim():split(delimiter: ' ');
		if({ parts:length() < 2 }, { return req; });

		req:method: parts:get(index: 0, default: 'GET'):toUpper();
		local String is target: parts:get(index: 1, default: '/');
		local Int is qIdx: target:indexOf(search: '?', default: -1);
		if({ qIdx >= 0 }, {
			req:path: urlDecode(s: target:substring(start: 0, end: qIdx));
			req:rawQuery: target:substring(start: qIdx + 1, end: target:length());
			req:getArgs: parseFormParams(raw: req:rawQuery);
		}, {
			req:path: urlDecode(s: target);
		});

		if({ firstCrlf >= 0 }, {
			local String is hdrBlock: rawHead:substring(start: firstCrlf + 2, end: rawHead:length());
			local Array of String is lines: hdrBlock:split(delimiter: "\r\n");
			times(count: lines:length(), worker: local Function(Int is li){
				local String is line: lines:get(index: li, default: '');
				local Int is col: line:indexOf(search: ':', default: -1);
				if({ col > 0 }, {
					local String is hk: line:substring(start: 0, end: col):trim():toLower();
					local String is hv: line:substring(start: col + 1, end: line:length()):trim();
					req:headers:set(key: hk, value: hv);
					if({ hk == 'content-length' }, {
						req:contentLength: hv:parseInt(default: 0);
					});
				});
			});
		});

		req:body: bodyText;
		if({ req:method == 'POST' && bodyText != '' }, {
			local String is ct: req:headers:getString(key: 'content-type', default: ''):toLower();
			if({ ct == '' || ct:contains(needle: 'application/x-www-form-urlencoded') }, {
				req:postArgs: parseFormParams(raw: bodyText);
			});
		});

		req:valid: true;
		return req;
	}
}
