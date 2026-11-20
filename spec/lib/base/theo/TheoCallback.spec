#! Package base:theo
#! Concrete callback wrapper stored in [Array]s without triggering bare `Function` type ambiguity.

Class is TheoCallback{
	namespace: ['base', 'theo'];

	Function is cb;

	replace Function is init(Function is fn){
		:cb: fn;
	}

	Function is call(){
		local Function is f: cb;
		f();
	}

	Function is callStr(String is s){
		local Function is f: cb;
		f(s);
	}

	Function is callAny(Any is v){
		local Function is f: cb;
		f(v);
	}
}
