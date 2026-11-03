#! Package base:reflect
#! Provides runtime type information and structural reflection.

## Describes a named, typed parameter of a method or function signature.
class Parameter{

	replace local Array of String is using: [
		base:reflect:Type
	];

	## Parameter identifier name.
	local String is name: "";

	## Type descriptor of the parameter.
	local Type is paramType;

	## Initializes a parameter descriptor.
	##
	## @param name: Parameter identifier name.
	## @param paramType: [Type] descriptor of the parameter.
	replace local Function is init(String is name, Type is paramType){
		self:name: name;
		self:paramType: paramType;
	}

	## Returns the parameter identifier name.
	##
	## @return: Name string.
	replace local Function of String is getName(){
		return self:name;
	}

	## Returns the type descriptor of this parameter.
	##
	## @return: [Type] instance.
	replace local Function of Type is getType(){
		return self:paramType;
	}

}
