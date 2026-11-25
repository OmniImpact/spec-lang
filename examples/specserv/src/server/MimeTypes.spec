#! Package specserv:server
#! Maps file extensions to HTTP Content-Type headers.

Class is MimeTypes{
	replace [String] is namespace: ['specserv', 'server'];

	Function of String is forPath(String is path){
		local String is lp: path:toLower();
		if({ lp:endsWith(suffix: '.html') || lp:endsWith(suffix: '.htm') }, { return 'text/html; charset=utf-8'; });
		if({ lp:endsWith(suffix: '.css') }, { return 'text/css; charset=utf-8'; });
		if({ lp:endsWith(suffix: '.js') || lp:endsWith(suffix: '.mjs') }, { return 'application/javascript; charset=utf-8'; });
		if({ lp:endsWith(suffix: '.json') }, { return 'application/json; charset=utf-8'; });
		if({ lp:endsWith(suffix: '.xml') }, { return 'application/xml; charset=utf-8'; });
		if({ lp:endsWith(suffix: '.txt') || lp:endsWith(suffix: '.md') || lp:endsWith(suffix: '.log') }, { return 'text/plain; charset=utf-8'; });
		if({ lp:endsWith(suffix: '.svg') }, { return 'image/svg+xml'; });
		if({ lp:endsWith(suffix: '.png') }, { return 'image/png'; });
		if({ lp:endsWith(suffix: '.jpg') || lp:endsWith(suffix: '.jpeg') }, { return 'image/jpeg'; });
		if({ lp:endsWith(suffix: '.gif') }, { return 'image/gif'; });
		if({ lp:endsWith(suffix: '.webp') }, { return 'image/webp'; });
		if({ lp:endsWith(suffix: '.ico') }, { return 'image/x-icon'; });
		return 'application/octet-stream';
	}
}
