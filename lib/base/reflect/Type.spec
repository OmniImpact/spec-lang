#! Package base:reflect
#! Provides runtime type information and structural reflection.

## Represents a primitive or parameterized type descriptor in the Spec type system.
Class is Type{

	replace local Array of String is using: [
		base:struct:Array
	];

	## Base type identifier (e.g. "Int", "String", "Function", "Array").
	local String is name: "";

	## Generic type arguments (e.g. `[String]` in `Array of String`).
	local Array of Type is params: [];

	## Initializes a simple type descriptor without generic parameters.
	##
	## @param name: Base type name.
	replace local Function is init(String is name){
		self:name: name;
		self:params: [];
	}

	## Initializes a parameterized generic type descriptor.
	##
	## @param name: Base type name.
	## @param params: Generic type arguments.
	local Function is withParams(String is name, Array of Type is params){
		self:name: name;
		self:params: params;
	}

	## Returns the base type name.
	##
	## @return: Name string.
	local Function of String is getName(){
		return self:name;
	}

	## Returns generic parameter types.
	##
	## @return: Array of parameter [Type] descriptors.
	local Function of Array of Type is getParams(){
		return self:params;
	}

	## Indicates whether this type has generic parameters.
	##
	## @return: `true` if parameterized, `false` otherwise.
	local Function of Boolean is isGeneric(){
		return self:params:length() > 0;
	}

	## Formats the type into canonical Spec syntax (e.g. "Array of String", "Map of String to Int").
	##
	## @return: Canonical type string.
	replace local Function of String is toString(){
		if (self:params:length() == 0) {
			return self:name;
		}
		if (self:params:length() == 1) {
			local Type is p0: self:params:get(index: 0);
			return self:name . " of " . p0:toString();
		}
		local Type is first: self:params:get(index: 0);
		local Type is second: self:params:get(index: 1);
		return self:name . " of " . first:toString() . " to " . second:toString();
	}

}
