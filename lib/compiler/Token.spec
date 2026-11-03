class Token{

	replace local Array of String is using: [
		base:sys:SourceLocation
	];

	local String is kind: "";
	local String is value: "";
	local SourceLocation is location;

	replace local Function is init(String is kind, String is value, Int is line, Int is col){
		self:kind: kind;
		self:value: value;
		self:location: SourceLocation:init(file: "", line: line, col: col);
	}

	replace local Function is withLocation(String is kind, String is value, SourceLocation is location){
		self:kind: kind;
		self:value: value;
		self:location: location;
	}

	replace local Function of String is getKind(){
		return self:kind;
	}

	replace local Function of String is getValue(){
		return self:value;
	}

	replace local Function of Int is getLine(){
		return self:location:getLine();
	}

	replace local Function of Int is getCol(){
		return self:location:getCol();
	}

	replace local Function of SourceLocation is getLocation(){
		return self:location;
	}

}
