class Type{

	replace local Array of String is using: [
		base:struct:Array
	];

	local String is name: "";
	local Array of Type is params: [];

	replace local Function is init(String is name){
		self:name: name;
		self:params: [];
	}

	replace local Function is withParams(String is name, Array of Type is params){
		self:name: name;
		self:params: params;
	}

	replace local Function of String is getName(){
		return self:name;
	}

	replace local Function of Array of Type is getParams(){
		return self:params;
	}

	replace local Function of Boolean is isGeneric(){
		return self:params:length() > 0;
	}

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
