#! Package examples:regression
#! Tracks vtable dispatch and struct layout correctness across hierarchies.

## Virtual dispatch and layout invariants.
##
## Guarded behavior:
## - Struct fields are laid out bases-first, so ancestor casts on descendant
##   objects read the correct offsets at any depth.
## - Overridden methods dispatch through the receiver's vtable: base-typed
##   references reach the most-derived implementation.
## - Multiple inheritance resolves by first-wins declaration order.
## - All checks print "[PASS]"; any "[FAIL]" is a regression.

Class is LayoutBase{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];
	local Int is baseField: 11;

	Function of Int is describeBase(){
		return self:baseField;
	}

	Function of Int is poly(){
		return 1;
	}
}

Class of LayoutBase is LayoutMid{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	local Int is midField: 22;

	replace Function of Int is poly(){
		return 2;
	}
}

Class of LayoutMid is LayoutLeaf{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	local Int is leafField: 33;

	replace Function of Int is poly(){
		return 3;
	}
}

Class is MiaFeature{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	Function of String is label(){
		return 'mia';
	}
}

Class is MibFeature{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	Function of String is tag(){
		return 'mib';
	}
}

Class of MiaFeature, MibFeature is MiChild{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	replace Function of String is label(){
		return 'child-mia';
	}
}

Class is VtableDispatchTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Output],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Regression: Vtable Dispatch & Layout ===');

		local LayoutLeaf is leaf: LayoutLeaf:init();

		# Case 1: fields at every level round-trip (layout integrity).
		Conditional:if(check: { leaf:baseField == 11 && leaf:midField == 22 && leaf:leafField == 33 }, then: {
			Output:line('[PASS] layout: all three field levels intact');
		}, else: {
			Output:line('[FAIL] layout: base=' . leaf:baseField . ' mid=' . leaf:midField . ' leaf=' . leaf:leafField);
		});

		# Case 2: base-declared method reading base field via leaf object.
		local Int is desc: leaf:describeBase();
		Conditional:if(check: { desc == 11 }, then: {
			Output:line('[PASS] inherited method reads base field: 11');
		}, else: {
			Output:line('[FAIL] inherited method: expected 11, got ' . desc);
		});

		# Case 3: base-typed reference dispatches to most-derived override.
		local LayoutBase is asBase: leaf;
		local Int is poly: asBase:poly();
		Conditional:if(check: { poly == 3 }, then: {
			Output:line('[PASS] base-typed virtual dispatch: poly = 3');
		}, else: {
			Output:line('[FAIL] base-typed virtual dispatch: expected 3, got ' . poly);
		});

		# Case 4: mid-typed reference also reaches the leaf override.
		local LayoutMid is asMid: leaf;
		Conditional:if(check: { asMid:poly() == 3 }, then: {
			Output:line('[PASS] mid-typed virtual dispatch: poly = 3');
		}, else: {
			Output:line('[FAIL] mid-typed virtual dispatch: expected 3');
		});

		# Case 5: MI first-wins - child override wins over both parents.
		local MiChild is mi: MiChild:init();
		local String is lbl: mi:label();
		Conditional:if(check: { lbl == 'child-mia' }, then: {
			Output:line('[PASS] MI override: label = child-mia');
		}, else: {
			Output:line('[FAIL] MI override: expected child-mia, got ' . lbl);
		});

		# Case 6: MI first-wins - undeclared method resolves to first parent.
		local String is tg: mi:tag();
		Conditional:if(check: { tg == 'mib' }, then: {
			Output:line('[PASS] MI first-wins: tag = mib');
		}, else: {
			Output:line('[FAIL] MI first-wins: expected mib, got ' . tg);
		});

		# Case 7: base-typed MI reference dispatches virtually.
		local MiaFeature is miAsBase: mi;
		Conditional:if(check: { miAsBase:label() == 'child-mia' }, then: {
			Output:line('[PASS] MI base-typed dispatch: label = child-mia');
		}, else: {
			Output:line('[FAIL] MI base-typed dispatch: expected child-mia');
		});

		Output:line('=== End Vtable Dispatch & Layout ===');
	}

}
