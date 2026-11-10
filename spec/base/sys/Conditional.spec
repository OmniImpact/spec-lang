#! Package base:sys
#! The conditional wrapper: every conditional shape composed from the
#! floor's single primitive — `else` is just `not if`.

Class is Conditional{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Conditional]
	];

	## Runs [then] when [check] holds. The floor primitive.
	##
	## @param check: The condition.
	## @param then: The closure to run when the condition holds.
	Function is if(Function of Boolean is check, Function is then){
		base:sysinternal:Conditional:branch(check: check, then: then);
	}

	## Runs [then] or [else] — composed as two floor calls: the second
	## guards on `!check`.
	##
	## @param check: The condition.
	## @param then: The closure for the true case.
	## @param else: The closure for the false case.
	Function is if(Function of Boolean is check, Function is then, Function is else){
		self:if(check: check, then: then);
		self:if(check: { return !check(); }, then: else);
	}

	## Runs [then] or [else], then [finally] either way.
	##
	## @param check: The condition.
	## @param then: The closure for the true case.
	## @param else: The closure for the false case.
	## @param finally: Runs after whichever branch ran.
	Function is if(Function of Boolean is check, Function is then, Function is else, Function is finally){
		self:if(check: check, then: then);
		self:if(check: { return !check(); }, then: else);
		finally();
	}

	## Dispatches [on] over the arm table [when] — the match construct.
	## Runtime-managed: intercepted by the compiler — the arm table
	## resolves against the subject's class's held members at compile
	## time and inlines into a comparison chain — so no body is emitted.
	## The arm table is a map literal whose keys are held-member
	## references (an array key matches several), `else` names the
	## fallback arm, and the closures are the arm bodies (a closure's
	## last expression is the arm's value).
	##
	## @param on: The subject value.
	## @param when: The arm table.
	Function is match(Any is on, Map of Any to Any is when){
	}
}
