#! Package base:net
#! HTTP/1.1 request descriptor with method, URL, headers, body, and options.

Class is HttpRequest{
	namespace: ['base', 'net'];

	replace Array of Array of String is using: [
		['base', 'struct', Map]
	];

	String is method: 'GET';
	String is url: '';
	Map of String to String is headers: Map:init();
	String is body: '';
	Int is timeoutMs: 15000;
	Int is maxRedirects: 5;

	replace Function is init(String is method: 'GET', String is url: '', String is body: '', Int is timeoutMs: 15000, Int is maxRedirects: 5){
		:method: method;
		:url: url;
		:headers: Map:init();
		:body: body;
		:timeoutMs: timeoutMs;
		:maxRedirects: maxRedirects;
	}

	Function of HttpRequest is setHeader(String is name, String is value){
		:headers:set(key: name, value: value);
		return :;
	}

	Function of HttpRequest is withBody(String is body, String is contentType: 'application/json'){
		:body: body;
		:headers:set(key: 'Content-Type', value: contentType);
		return :;
	}

	Function of HttpRequest is withTimeout(Int is timeoutMs){
		:timeoutMs: timeoutMs;
		return :;
	}
}
