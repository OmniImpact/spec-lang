class Token{

	local String is kind: "";
	local String is value: "";
	local Int is line: 1;
	local Int is col: 1;

	replace local Function is init(String is kind, String is value, Int is line, Int is col){
		self:kind: kind;
		self:value: value;
		self:line: line;
		self:col: col;
	}

	replace local Function of String is getKind(){
		return self:kind;
	}

	replace local Function of String is getValue(){
		return self:value;
	}

	replace local Function of Int is getLine(){
		return self:line;
	}

	replace local Function of Int is getCol(){
		return self:col;
	}

}
