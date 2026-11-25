#! Package base:net
#! Contract for dynamic `.spec` pages served by SpecServ.

Class is SpecServePage{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'struct', Map]
	];

	## Initializes the page with decoded URL query ([getArgs]) and form/POST ([postArgs]) parameters.
	replace Function is init(Map of String to String is getArgs: Map:init(), Map of String to String is postArgs: Map:init()){
		return;
	}

	## HTTP status code to return (default 200).
	Function of Int is statusCode(){ 200 }

	## MIME Content-Type header value (default `text/html; charset=utf-8`).
	Function of String is contentType(){ 'text/html; charset=utf-8' }

	## Additional HTTP response headers.
	Function of Map of String to String is headers(){ Map:init() }

	## Response body content.
	Function of String is body(){ '' }
}
