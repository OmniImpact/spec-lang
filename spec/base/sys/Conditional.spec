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
	##
	## THE CONTRACT, IN THIS FILE: the arm table is a map literal whose
	## keys are held-member references of the subject's class (an array
	## key matches several), `else` names the fallback arm, and the
	## values are the arm bodies — a closure whose last expression is
	## the arm's value. A payload arm's closure parameters bind the
	## variant's payload fields, in declaration order.
	##
	## THE IMPLEMENTATION IS COMPILE-TIME, and this body is therefore
	## never emitted: the checker recognizes the call
	## (TypeChecker.spec — the match recognizer and checkMatchArms:
	## key resolution against the subject class's held members, payload
	## typing from the variant's init parameters, exhaustiveness for
	## value-form subjects over Enum-rooted classes) and the backend
	## lowers the table (CodeGenerator.spec — generateMatch: the arm
	## closures inline as statement blocks, the keys compile to
	## identity compares for class-typed held members, string equality
	## for literal keys, == for numeric subjects, the else arm as the
	## chain's tail). Nothing runs at runtime except the chosen arm —
	## there is no table object and no dispatch loop to hide here.
	##
	## @param on: The subject value.
	## @param when: The arm table.
	Function is match(Any is on, Map of Any to Any is when){
	}
}
