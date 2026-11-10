#! N30 (PLAN-ENUM Stage 1): the held strictness walls.
#! - assignment through the class-name prefix (held is read-only)
#! - held combined with replace (single-copy cannot be overridden)
#! - self inside a held initializer (no instance exists)
#! - same-class held reference in a held initializer (once-guard deadlock)
#! - held member reached through an instance receiver (strict resolution)
#! - held local reached from an unrelated class (visibility)

Class is N30HeldWalls{
	namespace: ['test'];

	held String is label: 'wall';
	held local Int is hidden: 1;
	held String is fromSelf: self:label;

	replace Function is init(){
		# 1. held members are read-only.
		N30HeldWalls:label: 'mutated';
	}
}

Class of N30HeldWalls is N30HeldWallsChild{
	namespace: ['test'];

	# 2. held members are single-copy: they cannot be overridden.
	held replace String is label: 'sub';
}

Class is N30HeldCycle{
	namespace: ['test'];

	# 4. a held initializer referencing a held member of the same class
	#    would deadlock the once-guards.
	held String is a: N30HeldCycle:b . '!';
	held String is b: 'seed';
}

Class is N30HeldNoInit{
	namespace: ['test'];

	# 7. held fields construct lazily from their initializer: without
	#    one there is nothing to construct.
	held Int is noInit;
}

Class is N30HeldProbe{
	namespace: ['test'];

	replace Function is init(N30HeldWalls is w){
		# 5. strict resolution: an instance reference reaches exactly
		#    the instance members.
		Output:line(text: w:label);
		# 6. held local: invisible outside the declaring class.
		Output:line(text: (N30HeldWalls:hidden as String));
	}

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
}
