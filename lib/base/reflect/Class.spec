class Class{

	replace local Array of String is using: [
		base:struct:Array,
		base:reflect:Member
	];

	local String is name: "";
	local String is baseClass: "";
	local Array of Member is members: [];

	replace local Function is init(String is name, String is baseClass, Array of Member is members){
		self:name: name;
		self:baseClass: baseClass;
		self:members: members;
	}

	replace local Function of String is getName(){
		return self:name;
	}

	replace local Function of String is getBaseClass(){
		return self:baseClass;
	}

	replace local Function of Array of Member is getMembers(){
		return self:members;
	}

}
