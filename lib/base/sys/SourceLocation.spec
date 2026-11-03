class SourceLocation{

	local String is file: "";
	local Int is line: 1;
	local Int is col: 1;

	replace local Function is init(String is file, Int is line, Int is col){
		self:file: file;
		self:line: line;
		self:col: col;
	}

	replace local Function of String is getFile(){
		return self:file;
	}

	replace local Function of Int is getLine(){
		return self:line;
	}

	replace local Function of Int is getCol(){
		return self:col;
	}

	replace local Function of String is toString(){
		if (self:file:length() > 0) {
			return self:file . ":" . self:line . ":" . self:col;
		}
		return self:line . ":" . self:col;
	}

}
