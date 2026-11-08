#! FUNCTIONS.md Part IV IV.2/IV.3: inner classes inherit their enclosing
#! class — the members (the parent's methods and fields through the MI
#! link) and the imports (the outer's as-imports synthesize onto the
#! inner, so the inherited functions dispatch on the inner). The inner's
#! OWN additional imports scope to it alone.

Class is InnerClassTest{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	## The parent's member: the inner calls it through the link.
	Function of Int is doubled(Int is n){
		return n * 2;
	}

	## The parent's field: the inner reads and writes its own copy
	## (public members follow the parent link; `local` stays sealed).
	Int is shared: 7;

	## The inner class: no using of its own — everything comes from the
	## enclosing class.
	Class is Helper{
		Function of Int is viaParent(Int is n){
			return self:doubled(n);
		}

		Function of Int is parentFieldTimes(Int is n){
			# the inherited field starts empty on the inner's instances; the
			# inner's methods set what they need.
			self:shared: self:shared + n;
			return self:shared;
		}

		## The construction protocol is the inner's own (the parent's init
		## is the driver entry, not the inner's); the members come through
		## the link.
		replace Function is init(){
		}

		## The outer's as-import (Conditional) used bare inside the inner:
		## the inherited synthesis carries it.
		Function of String is pick(Boolean is flag){
			return Conditional:if(check: { flag }, then: { 'yes' }, else: { 'no' });
		}
	}

	## A second inner declaring its OWN additional import: scopes to it
	## and its contents only.
	Class is MathUser{
		replace Array of Array of String is using: [
			['base', 'math', as Math()]
		];

		Function of Float is halved(Float is x){
			return Math:floor(value: x) / 2.0;
		}

		replace Function is init(){
		}
	}

	replace Function is init(Map of String to String is args){
		Output:line('=== Inner Classes ===');
		local Int is pass: 0;
		local Int is fail: 0;

		local Helper is h: Helper:init();
		local MathUser is mu: MathUser:init();

		# 1. The parent's method through the link.
		Conditional:if(check: { h:viaParent(21) == 42 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] parent method: ' . (h:viaParent(21) as String));
		});

		# 2. The parent's field on the inner's own instance.
		Conditional:if(check: { h:parentFieldTimes(3) == 3 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] parent field: ' . (h:parentFieldTimes(3) as String));
		});

		# 3. The outer's as-import (Conditional) bare inside the inner.
		Conditional:if(check: { h:pick(true) == 'yes' && h:pick(false) == 'no' }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] inherited import: ' . h:pick(true));
		});

		# 4. The inner's OWN additional import.
		Conditional:if(check: { mu:halved(8.0) == 4.0 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			Output:line('[FAIL] own import: ' . (mu:halved(8.0) as String));
		});

		Conditional:if(check: { fail == 0 }, then: {
			Output:line('[PASS] inner classes: ' . (pass as String) . ' checks');
		}, else: {
			Output:line('[FAIL] inner classes: ' . (fail as String) . ' failures');
		});
	}
}
