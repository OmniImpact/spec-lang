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

	## Dispatches an arm table — the match construct. TWO KEY KINDS:
	##
	## - `match(on:, when:)` — the SUBJECT form: the keys are
	##   held-member references (an array key matches several) or
	##   string literals, compared against [on].
	## - `match(when:)` — the PREDICATE form: no subject, the keys are
	##   closures, and the first that holds runs its arm — the else-if
	##   ladder without the pyramid.
	##
	## The literal tables are COMPILE-TIME: the checker resolves the
	## keys (against the subject's class's held members, or as Boolean
	## predicates), types payload arms and checks exhaustiveness, and
	## the backend inlines the table into a comparison chain with zero
	## allocation (TypeChecker.spec: the match recognizer,
	## checkMatchArms, checkPredicateArms; CodeGenerator.spec:
	## generateMatch, generatePredicateMatch). That lowering is the
	## fast path — and the only path that can bind PAYLOAD arms (a
	## payload arm's closure parameters receive the variant's fields)
	## and match identity/array/predicate keys.
	##
	## THIS BODY IS THE RUNTIME PATH for the subject form — the
	## if(...) precedent: the wrapper implements the construct over
	## the floor primitives, and the compiler inlines the literal
	## shape. A table that is NOT a literal at the call site — a Map
	## built with set() — flows here. The runtime surface is
	## STRING-KEYED (the runtime map's keys are strings): the scan
	## walks the key array recursively (state rides the parameters —
	## the runtime closures capture by value, so no dispatch flag can
	## live in a frame), firing the first arm whose key equals a
	## String subject; `else` is the fallback arm, fired when the scan
	## is exhausted. The wrapper's members are self-free (the elided
	## dispatch passes no receiver), so the scan is a held function.
	## The PREDICATE form has no runtime path: a runtime map can
	## neither preserve scan order nor carry closure keys — the
	## checker rejects non-literal predicate tables outright.
	##
	## @param on: The subject value (a String for the runtime path).
	## @param when: The arm table.
	Function is match(Any is on, Map of Any to Any is when){
		Conditional:dispatchScan(when: when, on: on, index: 0);
	}

	## The recursive runtime dispatch scan (held: receiver-free — the
	## elided dispatch passes no receiver). One level per table key:
	## a key matching a String subject fires its arm; the sentinel
	## `else` never matches a value; the exhausted scan fires the
	## fallback arm when the table carries one. The floor's branch is
	## the two-argument primitive — the continue/else pair composes as
	## two branches, the second guarding on the negated condition (the
	## wrapper's own if(...) pattern).
	##
	## @param when: The arm table.
	## @param on: The subject value (a String for the runtime path).
	## @param index: The scan position over the table's key array.
	held Function is dispatchScan(Map of Any to Any is when, Any is on, Int is index){
		local Array of String is ks: when:keys();
		base:sysinternal:Conditional:branch(
			check: { return index < ks:length(); },
			then: {
				local String is k: ks:get(index: index, default: '');
				base:sysinternal:Conditional:branch(
					check: { return k != 'else' && k == on; },
					then: {
						local Function is body: when:get(key: k, default: '') as Function;
						body();
					}
				);
				base:sysinternal:Conditional:branch(
					check: { return !(k != 'else' && k == on); },
					then: {
						Conditional:dispatchScan(when: when, on: on, index: index + 1);
					}
				);
			}
		);
		base:sysinternal:Conditional:branch(
			check: { return index >= ks:length() && when:has(key: 'else'); },
			then: {
				local Function is body: when:get(key: 'else', default: '') as Function;
				body();
			}
		);
	}
}
