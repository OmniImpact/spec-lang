class Parameter{

	replace local Array of String is using: [
		base:reflect:Type
	];

	local String is name: "";
	local Type is paramType;

	replace local Function is init(String is name, Type is paramType){
		self:name: name;
		self:paramType: paramType;
	}

	replace local Function of String is getName(){
		return self:name;
	}

	replace local Function of Type is getType(){
		return self:paramType;
	}

}
