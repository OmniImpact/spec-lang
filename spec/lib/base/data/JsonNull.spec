#! Package base:data
#! Representation of JSON null value.

Class is JsonNull{
	replace [String] is namespace: ['base', 'data'];

	## Returns string representation 'null'.
	replace Function of String is toString(){
		return 'null';
	}
}
