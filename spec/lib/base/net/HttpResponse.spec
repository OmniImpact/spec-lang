#! Package base:net
#! Minimal HTTP response container holding status code and response body.

Class is HttpResponse{
	namespace: ['base', 'net'];

	Int is status: 0;
	String is body: '';

	replace Function is init(Int is status: 0, String is body: ''){
		:status: status;
		:body: body;
	}

	Function of Boolean is isOk(){
		return :status >= 200 && :status < 300;
	}
}
