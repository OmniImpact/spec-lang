#! Package base:compiler:checker:loops
#! Checks whether a class member list implements (concretely defines) a
## target abstract member: a method with a body, or an initialized field.

Class of Loop is MemberImplementLoop{
	namespace: ['base', 'compiler', 'checker', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
	];

	local Array of Member is members;
	local Member is target;
	local Int is idx: 0;
	local Boolean is implemented: false;

	replace Function is init(Array of Member is members, Member is target){
		self:members: members;
		self:target: target;
		self:idx: 0;
		self:implemented: false;
	}

	replace Function of Boolean is evaluate(){
		return !self:implemented && self:idx < self:members:length();
	}

	replace Function of Boolean is iteration(LoopControl is c){
		local Member is subM: self:members:get(index: self:idx);
		self:idx: self:idx + 1;
		Conditional:branch(check: { subM:name == self:target:name }, then: {
			Conditional:branch(check: { subM:kind == MemberKind:METHOD && subM:body:length() > 0 }, then: {
				self:implemented: true;
				return false;
			});
			Conditional:branch(check: { subM:kind == MemberKind:FIELD && subM:hasInit }, then: {
				self:implemented: true;
				return false;
			});
		});
		return true;
	}
}
