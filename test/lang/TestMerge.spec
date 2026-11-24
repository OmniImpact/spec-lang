#! SpecUnit sweep (from merge_test.spec): the `merge` modifier —
#! data-structure-aware field overriding: merge satisfies the override
#! requirement like replace, array literals fold parent-first, and
#! merge-on-using composes with import loading without disturbing
#! normal replace semantics.

Class of SpecUnitTest is TestMerge{

	replace [[String]] is using: [
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

	Function is testMergeArrayField(){
		local MergeChild is child: MergeChild:init();
		Assert:areEqualInt(3, child:items:length());
		Assert:areEqualString('a', child:items[0]);
		Assert:areEqualString('b', child:items[1]);
		Assert:areEqualString('c', child:items[2]);
	}

	Function is testMergeMapField(){
		local MergeChild is child: MergeChild:init();
		Assert:areEqualInt(3, child:scores:length());
		Assert:areEqualInt(1, child:scores:get(key: 'a', default: 0));
		Assert:areEqualInt(20, child:scores:get(key: 'b', default: 0));
		Assert:areEqualInt(3, child:scores:get(key: 'c', default: 0));
	}

	Function is testMergeCustomMergeable(){
		local MergeChild is child: MergeChild:init();
		Assert:areEqualString('prod.example.com', child:cfg:host);
		Assert:areEqualInt(60, child:cfg:timeout);
	}

	Function is testMergeMultiLevel(){
		local MergeGrandChild is gc: MergeGrandChild:init();
		Assert:areEqualInt(3, gc:tags:length());
		Assert:areEqualString('core', gc:tags:get(index: 0, default: ''));
		Assert:areEqualString('extended', gc:tags:get(index: 1, default: ''));
		Assert:areEqualString('leaf', gc:tags:get(index: 2, default: ''));
		Assert:areEqualInt(4, gc:items:length());
		Assert:areEqualString('d', gc:items[3]);
		Assert:areEqualInt(99, gc:scores:get(key: 'b', default: 0));
		Assert:areEqualString('leaf.example.com', gc:cfg:host);
		Assert:areEqualInt(60, gc:cfg:timeout);
	}
}

Class of Mergeable is MergeableConfig{
	String is host: '';
	Int is timeout: 0;

	replace Function is init(String is host: '', Int is timeout: 0){
		:host: host;
		:timeout: timeout;
	}

	replace Function is merge(MergeableConfig is other){
		if({ other:host != '' }, {
			:host: other:host;
		});
		if({ other:timeout > 0 }, {
			:timeout: other:timeout;
		});
	}
}

Class is MergeBase{

	## No ancestor declares `using`, so this merge stands alone as a fresh array.
	merge [[String]] is using: [['base', 'sys', as Output()], ['base', 'sys', as Conditional()]] ;

	List of String is tags: ['core'];
	Array of String is items: Array(['a', 'b']);
	Map of String to Int is scores: ['a': 1, 'b': 2];
	MergeableConfig is cfg: MergeableConfig(host: 'prod.example.com', timeout: 30);

	Function of Int is baseValue(){
		return 10;
	}
}

Class of MergeBase is MergeChild{

	## Folds onto MergeBase's using: Output + Array both load.
	merge [[String]] is using: [['base', 'struct', Array], ['base', 'sys', as Output()] ];

	## Merges onto ["core"]: result is ["core", "extended"].
	merge List of String is tags: ['extended'];
	merge Array of String is items: Array(['c']);
	merge Map of String to Int is scores: ['b': 20, 'c': 3];
	merge MergeableConfig is cfg: MergeableConfig(timeout: 60);

	replace Function of Int is baseValue(){
		return 20;
	}
}

Class of MergeChild is MergeGrandChild{
	merge List of String is tags: ['leaf'];
	merge Array of String is items: Array(['d']);
	merge Map of String to Int is scores: ['b': 99];
	merge MergeableConfig is cfg: MergeableConfig(host: 'leaf.example.com');
}

Class is MergeControlFlow{
	merge [[String]] is using: [];

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
