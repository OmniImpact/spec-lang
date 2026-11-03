class StackFrame{

	replace local Array of String is using: [
		base:sys:SourceLocation
	];

	local SourceLocation is location;
	local String is className: "";
	local String is methodName: "";

	replace local Function is init(SourceLocation is location, String is className, String is methodName){
		self:location: location;
		self:className: className;
		self:methodName: methodName;
	}

	replace local Function of SourceLocation is getLocation(){
		return self:location;
	}

	replace local Function of String is getClassName(){
		return self:className;
	}

	replace local Function of String is getMethodName(){
		return self:methodName;
	}

	replace local Function of String is toString(){
		local String is locStr: "";
		if (self:location:getLine() > 0) {
			locStr: " (" . self:location:toString() . ")";
		}
		if (self:className:length() > 0) {
			return self:className . ":" . self:methodName . locStr;
		}
		return self:methodName . locStr;
	}

}
