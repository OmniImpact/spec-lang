#! Package base:compiler:checker:loops
#! Finds a method member by name in a member list.
#! PLAN-ENUM Stage 1: with skipHeld set, HELD members are invisible —
#! an instance-method lookup reaches exactly the instance methods.

Class of Loop is MethodSearchLoop{
	namespace: ['base', 'compiler', 'checker', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
	];

	local Array of Member is members;
	local String is methodName;
	local Int is idx: 0;
	local Member is res;
	local Boolean is found: false;

	## When true, held members do not match (instance lookups).
	local Boolean is skipHeld: false;

	replace Function is init(Array of Member is members, String is methodName){
		self:members: members;
		self:methodName: methodName;
		self:idx: 0;
		self:found: false;
		self:skipHeld: false;
	}

	Function is setSkipHeld(Boolean is v){
		self:skipHeld: v;
	}

	replace Function of Boolean is evaluate(){
		return !self:found && self:idx < self:members:length();
	}

	replace Function of Boolean is iteration(LoopControl is c){
		local Member is m: self:members:get(index: self:idx);
		self:idx: self:idx + 1;
		Conditional:if(check: { self:skipHeld && m:hasModifier(kw: Keyword:HELD) }, then: {
			return true;
		});
		Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == self:methodName }, then: {
			self:res: m;
			self:found: true;
			return false;
		});
		return true;
	}
}
