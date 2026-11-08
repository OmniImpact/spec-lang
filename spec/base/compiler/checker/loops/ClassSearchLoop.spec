#! Package base:compiler:checker:loops
#! Finds a class descriptor by name in the flattened program registry.

Class of Loop is ClassSearchLoop{
	namespace: ['base', 'compiler', 'checker', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
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
		Conditional:if(check: { cand:name == self:target }, then: {
			self:res: cand;
			self:found: true;
			return false;
		});
		# Qualified targets ('base:sysinternal:Buf'): namespace joined with
		# ':' plus the class name must equal the target.
		Conditional:if(check: { self:target:contains(needle: ':') }, then: {
			local String is candQ: cand:namespaceJoined() . ':' . cand:name;
			Conditional:if(check: { candQ == self:target }, then: {
				self:res: cand;
				self:found: true;
				return false;
			});
		});
		return true;
	}
}
