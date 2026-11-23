#! SpecUnit sweep (from merge_test.spec): the `merge` modifier —
#! data-structure-aware field overriding: merge satisfies the override
#! requirement like replace, array literals fold parent-first, and
#! merge-on-using composes with import loading without disturbing
#! normal replace semantics.

Class of SpecUnitTest is TestMerge{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testMergeFoldOrder(){
		# Merged list contains the parent item first.
		local MergeChild is child: MergeChild:init();
		Assert:areEqualString('core', child:tags:get(index: 0, default: ''));
	}

	Function is testMergeFoldAppend(){
		# Merged list appends the child item.
		local MergeChild is child: MergeChild:init();
		Assert:areEqualString('extended', child:tags:get(index: 1, default: ''));
	}

	Function is testMergeFoldLength(){
		# Merged length is parent + child.
		local MergeChild is child: MergeChild:init();
		Assert:areEqualInt(2, child:tags:length());
	}

	Function is testReplaceAlongsideMerge(){
		# `merge` did not disturb normal override semantics.
		local MergeChild is child: MergeChild:init();
		Assert:areEqualInt(20, child:baseValue());
	}

	Function is testMergeInheritsClassControlFlow(){
		# `merge` on `using` inherits `as Conditional()` and `as Loops()` from Class.
		local MergeControlFlow is cf: MergeControlFlow();
		Assert:areEqualInt(6, cf:sumTo(n: 3));
	}
}

Class is MergeBase{

	## No ancestor declares `using`, so this merge stands alone as a fresh array.
	merge Array of Array of String is using: [['base', 'sys', as Output()], ['base', 'sys', as Conditional()]] ;

	List of String is tags: ['core'];

	Function of Int is baseValue(){
		return 10;
	}
}

Class of MergeBase is MergeChild{

	## Folds onto MergeBase's using: Output + Array both load.
	merge Array of Array of String is using: [['base', 'struct', Array], ['base', 'sys', as Output()] ];

	## Folds onto ["core"]: result is ["core", "extended"].
	merge List of String is tags: ['extended'];

	replace Function of Int is baseValue(){
		return 20;
	}
}

Class is MergeControlFlow{
	merge Array of Array of String is using: [];

	Function of Int is sumTo(Int is n){
		local Int is total: 0;
		local Int is i: 1;
		while({ i <= n }, {
			if({ i > 0 }, {
				total: total + i;
			});
			i: i + 1;
		});
		total;
	}
}
