#! specunit: negative
#! expect: must be declared exactly 'held Function of <T> is resolveHeld(String is name, Function of <T> is missing)'
#! expect: The resolution hook cannot resolve through its own class prefix
#! expect: only held members are (§2.3)
#! expect: is read-only: resolution-hook values are cached single copies

#! N32 (PLAN-ENUM Stage 2): the resolution-hook walls.
#! - the contract signature is exact: (String, Function of <T>) returning <T>
#! - the hook cannot resolve through its own class prefix (recursion)
#! - declared instance members keep their rejection (declared wins)
#! - hook-resolved values are cached single copies: read-only

Class is N32BadSig{
	namespace: ['test'];

	# The missing branch must return the same type the resolver
	# searches for — this one returns String.
	held Function of N32Entry is resolveHeld(String is name, Function of String is missing){
		return N32Entry:init(n: name);
	}
}

Class is N32Entry{
	namespace: ['test'];

	local String is name;

	Function is init(String is n){
		self:name: n;
	}
}

Class is N32SelfLoop{
	namespace: ['test'];

	held Function of N32Entry is resolveHeld(String is name, Function of N32Entry is missing){
		# The hook resolving an UNDECLARED name through its own prefix
		# would recurse forever — the checker rejects it.
		return N32SelfLoop:neverDeclared;
	}
}

Class is N32Shadow{
	namespace: ['test'];

	local String is plain: 'instance';

	held Function of N32Entry is resolveHeld(String is name, Function of N32Entry is missing){
		return N32Entry:init(n: name);
	}

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	replace Function is init(){
		# A declared instance member through the prefix stays rejected —
		# the hook never overrides declared resolution.
		Output:line(text: N32Shadow:plain);
	}
}

Class is N32AssignHook{
	namespace: ['test'];

	held Function of N32Entry is resolveHeld(String is name, Function of N32Entry is missing){
		return N32Entry:init(n: name);
	}

	replace Function is init(){
		# Hook values are cached single copies: read-only.
		N32AssignHook:anything: N32Entry:init(n: 'no');
	}
}
