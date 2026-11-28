#! specunit: suite

Class of SpecUnitTest is TestTrees{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'struct', Array],
		['base', 'struct', TreeMap],
		['base', 'struct', TreeSet],
		['base', 'struct', TreeNode],
		['base', 'struct', Tree]
	];

	Function is testTreeMapInsertSearchRemoveAndGrowth(){
		local TreeMap of Int to String is tm: TreeMap();
		Assert:isTrue(tm:isEmpty());

		# Insert 80 keys in pseudo-shuffled order to stress RB rotations and pool growth (>16)
		local Int is i: 0;
		while({ i < 80 }, {
			local Int is k: (i * 37) % 80;
			tm:set(key: k, value: 'v' . (k as String));
			i: i + 1;
		});
		Assert:areEqualInt(80, tm:length());
		Assert:areEqualInt(0, tm:minKey(default: -1));
		Assert:areEqualInt(79, tm:maxKey(default: -1));
		Assert:areEqualString('v42', tm:get(key: 42, default: ''));

		# Overwrite existing key
		tm:set(key: 42, value: 'updated');
		Assert:areEqualInt(80, tm:length());
		Assert:areEqualString('updated', tm:get(key: 42, default: ''));

		# Floor / ceiling
		Assert:areEqualInt(42, tm:floorKey(key: 42, default: -1));
		Assert:areEqualInt(42, tm:ceilingKey(key: 42, default: -1));

		# Remove half the keys
		i: 0;
		while({ i < 80 }, {
			Assert:isTrue(tm:remove(key: i));
			i: i + 2;
		});
		Assert:areEqualInt(40, tm:length());
		Assert:isFalse(tm:has(key: 0));
		Assert:isTrue(tm:has(key: 1));
		Assert:areEqualInt(1, tm:minKey(default: -1));
		Assert:areEqualInt(79, tm:maxKey(default: -1));
		Assert:areEqualInt(41, tm:floorKey(key: 42, default: -1));
		Assert:areEqualInt(43, tm:ceilingKey(key: 42, default: -1));

		# Verify in-order keys are strictly ascending
		local Array of Int is ks: tm:keys();
		Assert:areEqualInt(40, ks:length());
		i: 1;
		while({ i < ks:length() }, {
			Assert:isTrue(ks:get(index: i - 1, default: 0) < ks:get(index: i, default: 0));
			i: i + 1;
		});
	}

	Function is testTreeSetAndSetAlgebra(){
		local TreeSet of String is a: TreeSet();
		Assert:isTrue(a:add(item: 'banana'));
		Assert:isTrue(a:add(item: 'apple'));
		Assert:isFalse(a:add(item: 'apple'));
		Assert:isTrue(a:add(item: 'cherry'));

		Assert:areEqualString('apple', a:min(default: ''));
		Assert:areEqualString('cherry', a:max(default: ''));

		local TreeSet of String is b: TreeSet();
		b:add(item: 'banana');
		b:add(item: 'date');

		local TreeSet of String is u: a:union(other: b);
		Assert:areEqualInt(4, u:length());
		local TreeSet of String is inter: a:intersect(other: b);
		Assert:areEqualInt(1, inter:length());
		Assert:isTrue(inter:has(item: 'banana'));
		local TreeSet of String is diff: a:difference(other: b);
		Assert:areEqualInt(2, diff:length());
		Assert:isTrue(diff:has(item: 'apple'));
		Assert:isTrue(diff:has(item: 'cherry'));
	}

	Function is testTreeAndTreeNode(){
		local Tree of String is t: Tree(rootValue: 'root');
		local TreeNode of String is root: t:getRoot(default: TreeNode(value: ''));
		local TreeNode of String is c1: TreeNode(value: 'c1');
		local TreeNode of String is c2: TreeNode(value: 'c2');
		local TreeNode of String is g1: TreeNode(value: 'g1');

		Assert:isTrue(root:addChild(child: c1));
		Assert:isTrue(root:addChild(child: c2));
		Assert:isTrue(c1:addChild(child: g1));

		# Cycle guard: g1 cannot add root or itself as a child
		Assert:isFalse(g1:addChild(child: root));
		Assert:isFalse(g1:addChild(child: g1));

		Assert:areEqualInt(4, t:size());
		Assert:areEqualInt(3, t:height());

		local Array of String is pre: t:toArrayPreOrder();
		Assert:areEqualString('root', pre:get(index: 0, default: ''));
		Assert:areEqualString('c1', pre:get(index: 1, default: ''));
		Assert:areEqualString('g1', pre:get(index: 2, default: ''));
		Assert:areEqualString('c2', pre:get(index: 3, default: ''));

		local Array of String is bfs: t:toArrayBreadthFirst();
		Assert:areEqualString('root', bfs:get(index: 0, default: ''));
		Assert:areEqualString('c1', bfs:get(index: 1, default: ''));
		Assert:areEqualString('c2', bfs:get(index: 2, default: ''));
		Assert:areEqualString('g1', bfs:get(index: 3, default: ''));

		# Reparent g1 under c2
		Assert:isTrue(c2:addChild(child: g1));
		Assert:areEqualInt(0, c1:childCount());
		Assert:areEqualInt(1, c2:childCount());
		Assert:areEqualInt(4, t:size());
	}
}
