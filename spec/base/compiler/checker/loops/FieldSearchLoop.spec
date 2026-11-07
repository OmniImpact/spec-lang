#! Package base:compiler:checker:loops
#! Finds a field member by name in a member list.

Class of Loop is FieldSearchLoop{
	namespace: ['base', 'compiler', 'checker', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'iterator']
	];

	local Array of Member is members;
	local String is fieldName;
	local Int is idx: 0;
	local Member is res;
	local Boolean is found: false;

	replace Function is init(Array of Member is members, String is fieldName){
		self:members: members;
		self:fieldName: fieldName;
		self:idx: 0;
		self:found: false;
	}

	replace Function of Boolean is evaluate(){
		return !self:found && self:idx < self:members:length();
	}

	replace Function of Boolean is iteration(LoopControl is c){
		local Member is m: self:members:get(index: self:idx);
		self:idx: self:idx + 1;
		if (m:kind == MemberKind:FIELD && m:name == self:fieldName) {
			self:res: m;
			self:found: true;
			return false;
		}
		return true;
	}
}
