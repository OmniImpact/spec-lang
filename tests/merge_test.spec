#! Package examples:regression
#! Tracks the `merge` modifier: data-structure-aware field overriding.

## Merge: children fold array fields onto their parent's values.
##
## Guarded behavior:
## - `merge` satisfies the override requirement like `replace`.
## - Array literals fold: parent items first, then child items.
## - `merge` on `using` composes with import loading.
## - All four checks print "[PASS]"; any "[FAIL]" is a regression.

Class is MergeBase{

	## No ancestor declares `using`, so this merge stands alone as a fresh array.
	merge local Array of String is using: [base:io:Output];

	local Array of String is tags: ["core"];

	replace local Function of Int is baseValue(){
		return 10;
	}
}

Class is MergeChild extends MergeBase{

	## Folds onto MergeBase's using: Output + Array both load.
	merge local Array of String is using: [base:struct:Array];

	## Folds onto ["core"]: result is ["core", "extended"].
	merge local Array of String is tags: ["extended"];

	replace local Function of Int is baseValue(){
		return 20;
	}
}

Class is MergeTest{

	replace local Function is init(Map of String to String is args){
		output:line("=== Regression: Merge Modifier ===");

		local MergeChild is child: MergeChild:init();

		# Case 1: merged array contains parent item first.
		local String is first: child:tags:get(index: 0);
		if (first == "core") {
			output:line("[PASS] merge fold order: tags[0] = core");
		} else {
			output:line("[FAIL] merge fold order: expected core, got " . first);
		}

		# Case 2: merged array appends child item.
		local String is second: child:tags:get(index: 1);
		if (second == "extended") {
			output:line("[PASS] merge fold append: tags[1] = extended");
		} else {
			output:line("[FAIL] merge fold append: expected extended, got " . second);
		}

		# Case 3: merged length is parent + child.
		local Int is count: child:tags:length();
		if (count == 2) {
			output:line("[PASS] merge fold length: tags length = 2");
		} else {
			output:line("[FAIL] merge fold length: expected 2, got " . count);
		}

		# Case 4: `merge` did not disturb normal override semantics.
		local Int is value: child:baseValue();
		if (value == 20) {
			output:line("[PASS] replace alongside merge: baseValue = 20");
		} else {
			output:line("[FAIL] replace alongside merge: expected 20, got " . value);
		}

		output:line("=== End Merge Modifier Regression ===");
	}

}
