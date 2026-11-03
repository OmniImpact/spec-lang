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
	local Int is baseField: 11;

	local Function of Int is describeBase(){
		return self:baseField;
	}

	local Function of Int is poly(){
		return 1;
	}
}

Class is LayoutMid extends LayoutBase{
	local Int is midField: 22;

	replace local Function of Int is poly(){
		return 2;
	}
}

Class is LayoutLeaf extends LayoutMid{
	local Int is leafField: 33;

	replace local Function of Int is poly(){
		return 3;
	}
}

Class is MiaFeature{
	local Function of String is label(){
		return "mia";
	}
}

Class is MibFeature{
	local Function of String is tag(){
		return "mib";
	}
}

Class is MiChild extends MiaFeature, MibFeature{
	replace local Function of String is label(){
		return "child-mia";
	}
}

Class is VtableDispatchTest{

	replace local Array of String is using: [
		base:io:Output
	];

	replace local Function is init(Map of String to String is args){
		output:line("=== Regression: Vtable Dispatch & Layout ===");

		local LayoutLeaf is leaf: LayoutLeaf:init();

		# Case 1: fields at every level round-trip (layout integrity).
		if (leaf:baseField == 11 && leaf:midField == 22 && leaf:leafField == 33) {
			output:line("[PASS] layout: all three field levels intact");
		} else {
			output:line("[FAIL] layout: base=" . leaf:baseField . " mid=" . leaf:midField . " leaf=" . leaf:leafField);
		}

		# Case 2: base-declared method reading base field via leaf object.
		local Int is desc: leaf:describeBase();
		if (desc == 11) {
			output:line("[PASS] inherited method reads base field: 11");
		} else {
			output:line("[FAIL] inherited method: expected 11, got " . desc);
		}

		# Case 3: base-typed reference dispatches to most-derived override.
		local LayoutBase is asBase: leaf;
		local Int is poly: asBase:poly();
		if (poly == 3) {
			output:line("[PASS] base-typed virtual dispatch: poly = 3");
		} else {
			output:line("[FAIL] base-typed virtual dispatch: expected 3, got " . poly);
		}

		# Case 4: mid-typed reference also reaches the leaf override.
		local LayoutMid is asMid: leaf;
		if (asMid:poly() == 3) {
			output:line("[PASS] mid-typed virtual dispatch: poly = 3");
		} else {
			output:line("[FAIL] mid-typed virtual dispatch: expected 3");
		}

		# Case 5: MI first-wins - child override wins over both parents.
		local MiChild is mi: MiChild:init();
		local String is lbl: mi:label();
		if (lbl == "child-mia") {
			output:line("[PASS] MI override: label = child-mia");
		} else {
			output:line("[FAIL] MI override: expected child-mia, got " . lbl);
		}

		# Case 6: MI first-wins - undeclared method resolves to first parent.
		local String is tg: mi:tag();
		if (tg == "mib") {
			output:line("[PASS] MI first-wins: tag = mib");
		} else {
			output:line("[FAIL] MI first-wins: expected mib, got " . tg);
		}

		# Case 7: base-typed MI reference dispatches virtually.
		local MiaFeature is miAsBase: mi;
		if (miAsBase:label() == "child-mia") {
			output:line("[PASS] MI base-typed dispatch: label = child-mia");
		} else {
			output:line("[FAIL] MI base-typed dispatch: expected child-mia");
		}

		output:line("=== End Vtable Dispatch & Layout ===");
	}

}
