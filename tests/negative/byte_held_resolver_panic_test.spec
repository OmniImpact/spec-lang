#! The missing branch is the safe failure path: the resolver gives up
#! for 'phantom' by returning missing() — the runtime-provided default
#! panics with context (Never Null: a member access must yield a
#! value). Compiles fine; panics at runtime with the name in the
#! message.

Class is HeldEntry2{
	namespace: ['test'];

	local String is name;

	Function is init(String is n){
		self:name: n;
	}
}

Class is HeldPanicRegistry{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	held Function of HeldEntry2 is resolveHeld(String is name, Function of HeldEntry2 is missing){
		Conditional:if(check: { name == 'phantom' }, then: {
			return missing();
		});
		return HeldEntry2:init(n: name);
	}
}

Class is HeldResolverPanicTest{
	namespace: ['test'];

	replace Function is init(Map of String to String is args){
		local HeldEntry2 is boom: HeldPanicRegistry:phantom;
		Output:line(text: boom:name);
	}

	replace Array of Array of String is using: [
		['base', 'io', as Output()]
	];
}
