#! Package base:net
#! Minimal URL parser and relative-reference resolver for HTTP/HTTPS.

Class is Url{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is scheme: 'http';
	String is host: '';
	Int is port: 80;
	String is path: '/';
	String is query: '';

	replace Function is init(String is scheme: 'http', String is host: '', Int is port: 80, String is path: '/', String is query: ''){
		:scheme: scheme;
		:host: host;
		:port: port;
		:path: path;
		:query: query;
	}

	## Parses an HTTP or HTTPS URL string into a [Url] instance.
	held Function of Url is parse(String is raw){
		return Url:init():parseRaw(raw: raw);
	}

	local Function of Url is parseRaw(String is raw){
		local String is sc: 'http';
		local String is rest: raw:trim();
		if({ rest:startsWith(prefix: 'https://') }, {
			sc: 'https';
			rest: rest:substring(start: 8, end: rest:length());
		}, {
			if({ rest:startsWith(prefix: 'http://') }, {
				sc: 'http';
				rest: rest:substring(start: 7, end: rest:length());
			});
		});

		# Strip fragment (#...)
		local Int is hashIdx: rest:indexOf(search: '#', default: -1);
		if({ hashIdx >= 0 }, {
			rest: rest:substring(start: 0, end: hashIdx);
		});

		local Int is slashIdx: rest:indexOf(search: '/', default: -1);
		local Int is qIdx: rest:indexOf(search: '?', default: -1);
		local Int is authEnd: rest:length();
		if({ slashIdx >= 0 && slashIdx < authEnd }, { authEnd: slashIdx; });
		if({ qIdx >= 0 && qIdx < authEnd }, { authEnd: qIdx; });

		local String is authority: rest:substring(start: 0, end: authEnd);
		local String is pathAndQuery: rest:substring(start: authEnd, end: rest:length());

		local String is h: authority;
		local Int is p: if({ sc == 'https' }, { 443 }, { 80 });
		local Int is colonIdx: authority:indexOf(search: ':', default: -1);
		if({ colonIdx >= 0 }, {
			h: authority:substring(start: 0, end: colonIdx);
			p: authority:substring(start: colonIdx + 1, end: authority:length()):parseInt(default: p);
		});

		local String is pth: '/';
		local String is qry: '';
		if({ pathAndQuery:length() > 0 }, {
			local Int is pqIdx: pathAndQuery:indexOf(search: '?', default: -1);
			if({ pqIdx >= 0 }, {
				pth: pathAndQuery:substring(start: 0, end: pqIdx);
				qry: pathAndQuery:substring(start: pqIdx + 1, end: pathAndQuery:length());
			}, {
				pth: pathAndQuery;
			});
			if({ pth == '' }, { pth: '/'; });
		});

		:scheme: sc;
		:host: h;
		:port: p;
		:path: pth;
		:query: qry;
		return :;
	}

	## Returns `true` when this URL uses HTTPS.
	Function of Boolean is isHttps(){
		return :scheme == 'https';
	}

	## Returns the HTTP/1.1 request-target (`path` or `path?query`).
	Function of String is requestTarget(){
		if({ :query != '' }, {
			return :path . '?' . :query;
		});
		return :path;
	}

	## Returns the HTTP `Host` header value (omitting default ports 80/443).
	Function of String is hostHeader(){
		if({ (:scheme == 'https' && :port == 443) || (:scheme == 'http' && :port == 80) }, {
			return :host;
		});
		return :host . ':' . (:port as String);
	}

	## Resolves a redirect [location] (absolute, scheme-relative, or path-relative)
	## against this base URL.
	Function of Url is resolve(String is location){
		local String is loc: location:trim();
		if({ loc:startsWith(prefix: 'http://') || loc:startsWith(prefix: 'https://') }, {
			return Url:parse(raw: loc);
		});
		if({ loc:startsWith(prefix: '//') }, {
			return Url:parse(raw: :scheme . ':' . loc);
		});
		if({ loc:startsWith(prefix: '/') }, {
			return Url:parse(raw: :scheme . '://' . :hostHeader() . loc);
		});
		local Int is lastSlash: 0;
		local Int is si: 0;
		while({ si < :path:length() }, {
			if({ :path:byteAt(index: si, default: 0) == 47 }, {
				lastSlash: si;
			});
			si: si + 1;
		});
		local String is baseDir: :path:substring(start: 0, end: lastSlash + 1);
		return Url:parse(raw: :scheme . '://' . :hostHeader() . baseDir . loc);
	}

	replace Function of String is toString(){
		return :scheme . '://' . :hostHeader() . :requestTarget();
	}
}
