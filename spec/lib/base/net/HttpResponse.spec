#! Package base:net
#! HTTP/1.1 response container holding status code, status text, headers, and body.

Class is HttpResponse{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'struct', Map]
	];

	Int is status: 0;
	String is statusText: '';
	Map of String to String is headers: Map:init();
	String is body: '';

	replace Function is init(Int is status: 0, String is statusText: '', String is body: ''){
		:status: status;
		:statusText: statusText;
		:headers: Map:init();
		:body: body;
	}

	## Looks up a response header case-insensitively.
	Function of String is header(String is name, String is default: ''){
		return :headers:getString(key: name:toLower(), default: default);
	}

	Function of Boolean is isOk(){
		return :status >= 200 && :status < 300;
	}

	Function of Boolean is isRedirect(){
		return :status == 301 || :status == 302 || :status == 303 || :status == 307 || :status == 308;
	}
}
