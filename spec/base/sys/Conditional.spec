#! Package base:sys
#! The conditional wrapper: every conditional shape composed from the
#! floor's single primitive — `else` is just `not if` (FUNCTIONS.md
#! Part II).

Class is Conditional{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Conditional]
	];

	## Runs [then] when [check] holds. The floor primitive.
	##
	## @param check: The condition.
	## @param then: The closure to run when the condition holds.
	Function is branch(Function of Boolean is check, Function is then){
		base:sysinternal:Conditional:branch(check: check, then: then);
	}

	## Runs [then] or [else] — composed as two floor calls: the second
	## guards on `!check`.
	##
	## @param check: The condition.
	## @param then: The closure for the true case.
	## @param otherwise: The closure for the false case.
	Function is branch(Function of Boolean is check, Function is then, Function is otherwise){
		self:branch(check: check, then: then);
		self:branch(check: { return !check(); }, then: otherwise);
	}

	## Runs [then] or [else], then [finally] either way.
	##
	## @param check: The condition.
	## @param then: The closure for the true case.
	## @param otherwise: The closure for the false case.
	## @param finally: Runs after whichever branch ran.
	Function is branch(Function of Boolean is check, Function is then, Function is otherwise, Function is finally){
		self:branch(check: check, then: then);
		self:branch(check: { return !check(); }, then: otherwise);
		finally();
	}
}
