#! Package base:data
#! Representation of JSON null value.

Class is JsonNull{
	namespace: ['base', 'data'];

	## Returns string representation 'null'.
	replace Function of String is toString(){
		return 'null';
	}
}
