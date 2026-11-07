#! Package base:compiler:checker:loops
#! Finds a class descriptor by name in the flattened program registry.

Class of Loop is ClassSearchLoop{
	namespace: ['base', 'compiler', 'checker', 'loops'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'ast', ClassInfo],
		['lib', 'base', 'iterator']
	];

	local Array of ClassInfo is list;
	local String is target;
	local Int is idx: 0;
	local ClassInfo is res;
	local Boolean is found: false;

	replace Function is init(Array of ClassInfo is list, String is target){
		self:list: list;
		self:target: target;
		self:idx: 0;
		self:found: false;
	}

	replace Function of Boolean is evaluate(){
		return !self:found && self:idx < self:list:length();
	}

	replace Function of Boolean is iteration(LoopControl is c){
		local ClassInfo is cand: self:list:get(index: self:idx);
		self:idx: self:idx + 1;
		if (cand:name == self:target) {
			self:res: cand;
			self:found: true;
			return false;
		}
		# Qualified targets ('base:sysinternal:Buf'): namespace joined with
		# ':' plus the class name must equal the target.
		if (self:target:contains(needle: ':')) {
			local String is candQ: cand:namespaceJoined() . ':' . cand:name;
			if (candQ == self:target) {
				self:res: cand;
				self:found: true;
				return false;
			}
		}
		return true;
	}
}
