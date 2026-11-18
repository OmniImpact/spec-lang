#! Package base:data
#! Representation of JSON boolean value.

Class is JsonBool{
	namespace: ['base', 'data'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	local Boolean is val: false;

	replace Function is init(Boolean is value){
		:val: value;
	}

	Function of Boolean is value(){
		return :val;
	}

	replace Function of String is toString(){
		return if({ :val }, { 'true' }, { 'false' });
	}
}
