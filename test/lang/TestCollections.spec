#! specunit: suite

Class of SpecUnitTest is TestCollections{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', as Mem()],
		['base', 'struct', Array],
		['base', 'struct', HashSet],
		['base', 'struct', Deque],
		['base', 'struct', PriorityQueue],
		['base', 'struct', as Sort()]
	];

	Function is testHashSetOperations(){
		local HashSet of String is a: HashSet();
		Assert:isTrue(a:isEmpty());
		Assert:isTrue(a:add(item: 'alpha'));
		Assert:isTrue(a:add(item: 'beta'));
		Assert:isFalse(a:add(item: 'alpha'));
		Assert:areEqualInt(2, a:length());
		Assert:isTrue(a:has(item: 'beta'));
		Assert:isFalse(a:has(item: 'gamma'));

		local HashSet of String is b: HashSet();
		b:add(item: 'beta');
		b:add(item: 'gamma');

		local HashSet of String is u: a:union(other: b);
		Assert:areEqualInt(3, u:length());
		local HashSet of String is inter: a:intersect(other: b);
		Assert:areEqualInt(1, inter:length());
		Assert:isTrue(inter:has(item: 'beta'));
		local HashSet of String is diff: a:difference(other: b);
		Assert:areEqualInt(1, diff:length());
		Assert:isTrue(diff:has(item: 'alpha'));

		Assert:isTrue(a:remove(item: 'beta'));
		Assert:isFalse(a:remove(item: 'beta'));
		Assert:areEqualInt(1, a:length());

		# Stress rehash (>16 buckets), dynamic non-interned Strings, Int keys, and free-list reuse
		local HashSet of String is ds: HashSet();
		local HashSet of Int is iset: HashSet();
		local Int is i: 0;
		while({ i < 60 }, {
			Assert:isTrue(ds:add(item: 'key_' . (i as String)));
			Assert:isTrue(iset:add(item: i * 13));
			i: i + 1;
		});
		Assert:areEqualInt(60, ds:length());
		Assert:areEqualInt(60, iset:length());
		Assert:isTrue(ds:has(item: 'key_' . (42 as String)));
		Assert:isTrue(iset:has(item: 42 * 13));
		i: 0;
		while({ i < 30 }, {
			Assert:isTrue(ds:remove(item: 'key_' . (i as String)));
			Assert:isTrue(iset:remove(item: i * 13));
			i: i + 1;
		});
		Assert:areEqualInt(30, ds:length());
		Assert:isFalse(ds:has(item: 'key_5'));
		Assert:isTrue(ds:has(item: 'key_55'));
	}

	Function is testDequeWrapAroundAndGrowth(){
		local Deque of Int is dq: Deque();
		Assert:isTrue(dq:isEmpty());

		# Push back & pop front to advance head, then push past initial 16-slot ring capacity
		local Int is i: 0;
		while({ i < 10 }, {
			dq:pushBack(item: i);
			i: i + 1;
		});
		i: 0;
		while({ i < 6 }, {
			Assert:areEqualInt(i, dq:popFront(default: -1));
			i: i + 1;
		});
		# Now head=6, count=4 ([6,7,8,9]). Push 40 more to force wrap-around + multiple doublings
		i: 10;
		while({ i < 50 }, {
			dq:pushBack(item: i);
			i: i + 1;
		});
		Assert:areEqualInt(44, dq:length());
		Assert:areEqualInt(6, dq:peekFront(default: -1));
		Assert:areEqualInt(49, dq:peekBack(default: -1));
		Assert:areEqualInt(20, dq:get(index: 14, default: -1));

		# Test pushFront and popBack
		dq:pushFront(item: 5);
		Assert:areEqualInt(5, dq:peekFront(default: -1));
		Assert:areEqualInt(49, dq:popBack(default: -1));
		Assert:areEqualInt(48, dq:peekBack(default: -1));

		# Verify full sequence order
		local Int is expected: 5;
		while({ !dq:isEmpty() }, {
			Assert:areEqualInt(expected, dq:popFront(default: -1));
			expected: expected + 1;
		});
		Assert:areEqualInt(49, expected);
		Assert:areEqualInt(-1, dq:popFront(default: -1));
	}

	Function is testPriorityQueueMinAndMaxHeap(){
		local PriorityQueue of Int is minPq: PriorityQueue();
		local PriorityQueue of Int is maxPq: PriorityQueue(maxHeap: true);

		local Int is i: 0;
		while({ i < 60 }, {
			local Int is val: (i * 23) % 30;
			minPq:push(item: val);
			maxPq:push(item: val);
			i: i + 1;
		});
		Assert:areEqualInt(60, minPq:length());
		Assert:areEqualInt(0, minPq:peek(default: -1));
		Assert:areEqualInt(29, maxPq:peek(default: -1));

		local Int is prevMin: -1;
		local Int is prevMax: 100;
		while({ !minPq:isEmpty() }, {
			local Int is curMin: minPq:pop(default: -1);
			local Int is curMax: maxPq:pop(default: -1);
			Assert:isTrue(curMin >= prevMin);
			Assert:isTrue(curMax <= prevMax);
			prevMin: curMin;
			prevMax: curMax;
		});
		Assert:areEqualInt(-1, minPq:pop(default: -1));
	}

	Function is testSortFloatsAndMemHasClosure(){
		local Array of Float is xs: Array([3.5, -1.25, 0.0, 2.0, -1.25, 9.75]);
		local Array of Float is asc: Sort:floats(values: xs);
		Assert:areClose(-1.25, asc:get(index: 0, default: 0.0), 0.0001);
		Assert:areClose(-1.25, asc:get(index: 1, default: 0.0), 0.0001);
		Assert:areClose(0.0, asc:get(index: 2, default: 0.0), 0.0001);
		Assert:areClose(2.0, asc:get(index: 3, default: 0.0), 0.0001);
		Assert:areClose(3.5, asc:get(index: 4, default: 0.0), 0.0001);
		Assert:areClose(9.75, asc:get(index: 5, default: 0.0), 0.0001);

		local Array of Float is desc: Sort:floatsDesc(values: xs);
		Assert:areClose(9.75, desc:get(index: 0, default: 0.0), 0.0001);
		Assert:areClose(-1.25, desc:get(index: 5, default: 0.0), 0.0001);

		local Function is validCb: local Function(){};
		Assert:isTrue(Mem:hasClosure(cb: validCb));
	}
}
