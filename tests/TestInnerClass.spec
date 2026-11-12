#! SpecUnit sweep (from inner_class_test.spec): Part IV IV.2/IV.3 —
#! inner classes inherit their enclosing class — the members (the
#! parent's methods and fields through the MI link) and the imports
#! (the outer's as-imports synthesize onto the inner, so the inherited
#! functions dispatch on the inner). The inner's OWN additional imports
#! scope to it alone.
#!
#! Conversion note: the old inners declared empty `replace Function is
#! init(){}` bodies; through the enclosing link the SpecUnitTest base
#! now contributes both init signatures, so the replaces are dropped —
#! the inners inherit the base's empty no-arg init, which is the same
#! construction protocol.

Class of SpecUnitTest is TestInnerClass{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()]
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
	}

	## The shadowing rule: the inner's own member wins silently over the
	## same-named parent member (the closer scope).
	Function of Int is shadowed(){
		return 1;
	}

	## The inner-of-inner chain: the qualified identity is three-deep and
	## the member walk goes all the way out (Mid and TestInnerClass both
	## serve members to Deep).
	Class is Mid{
		Function of Int is midValue(){
			return 20;
		}

		## Shadows both Mid's and TestInnerClass's same-named member.
		Function of Int is shadowed(){
			return 3;
		}

		Class is Deep{
			Function of Int is all(){
				return self:doubled(5) + self:midValue() + self:shadowed();
			}

			Function of Int is shadowPick(){
				return self:shadowed();
			}
		}
	}

	## 1. The parent's method through the link.
	Function is testParentMethodThroughLink(){
		local Helper is h: Helper:init();
		Assert:areEqualInt(42, h:viaParent(21));
	}

	## 2. The parent's field on the inner's own instance.
	Function is testParentFieldOnInnerInstance(){
		local Helper is h: Helper:init();
		local Int is fieldVal: h:parentFieldTimes(3);
		Assert:areEqualInt(3, fieldVal);
	}

	## 3. The outer's as-import (Conditional) bare inside the inner.
	Function is testInheritedImportBareInInner(){
		local Helper is h: Helper:init();
		Assert:areEqualString('yes', h:pick(true));
		Assert:areEqualString('no', h:pick(false));
	}

	## 4. The inner's OWN additional import (base:math on MathUser).
	Function is testOwnImportScopesToInner(){
		local MathUser is mu: MathUser:init();
		Assert:areClose(4.0, mu:halved(8.0), 0.0001);
	}

	## 5. The shadowing rule: the inner's own member wins; the inners
	## without their own shadowed() walk out to the enclosing one.
	Function is testShadowingRule(){
		local Helper is h: Helper:init();
		local MathUser is mu: MathUser:init();
		Assert:areEqualInt(1, h:shadowed());
		Assert:areEqualInt(1, mu:shadowed());
	}

	## 6. The inner-of-inner chain: the three-deep qualified reference
	## resolves, the member walk goes all the way out, and the deepest
	## shadow wins.
	Function is testInnerOfInnerChain(){
		local TestInnerClass:Mid:Deep is d: TestInnerClass:Mid:Deep:init();
		Assert:areEqualInt(33, d:all());
		Assert:areEqualInt(3, d:shadowPick());
	}
}
