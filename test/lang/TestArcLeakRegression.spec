#! specunit: suite
#! Leak regression tests for frame-pool ARC ownership:
#! 1. Deterministic slab slot-reuse checks across helper frames, field
#!    overwrites, containers, closures, and Json parsing.
#! 2. High-iteration churn RSS bound check (Linux /proc/self/statm) to
#!    catch silent leaks across strings, arrays, maps, boxes, and closures.

Class of SpecUnitTest is TestArcLeakRegression{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as File()],
		['base', 'data', as Json()],
		['base', 'struct', Array],
		['base', 'struct', Map]
	];

	local Function of Int is readRssPages(){
		local String is statm: fileRead(path: '/proc/self/statm', default: '');
		if({ statm == '' }, { return -1; });
		local Array of String is parts: statm:trim():split(delimiter: ' ');
		if({ parts:length() < 2 }, { return -1; });
		return parts:get(index: 1, default: '0'):parseInt(base: 10, default: -1);
	}

	local Function of Int is churnOneNode(){
		local LeakNode is n: LeakNode:init(tag: 'probe');
		return Mem:objToAddr(obj: n);
	}

	local Function of Int is churnContainersAndClosures(Int is seed){
		local Array of String is arr: [];
		arr:add(item: 'k_' . (seed as String));
		arr:add(item: 'v_' . ((seed + 1) as String));
		local Map of String to String is mp: Map:init();
		mp:set(key: arr:get(index: 0, default: ''), value: arr:get(index: 1, default: ''));
		local Int is boxed: seed;
		local Function of Int is fn: local Function of Int(){
			boxed: boxed + 1;
			return boxed;
		};
		local Int is res: fn();
		local Any is parsed: Json:parse(text: '{"a":[1,2,"three"],"b":true}');
		local Map is obj: parsed as Map;
		if({ obj:has(key: 'a') }, {
			return res;
		});
		return 0;
	}

	local Function is overwriteHolderField(LeakHolder is h, Int is idx){
		h:node: LeakNode:init(tag: 'item_' . (idx as String));
	}

	## A single-object allocation that does not escape its frame must be freed
	## on return so the slab LIFO freelist hands back the exact same slot.
	Function is testSlabSlotReusedAcrossFrames(){
		# Warm up the size class so we are not hitting the bump pointer.
		local Int is warm: :churnOneNode();
		local Int is a1: :churnOneNode();
		local Int is a2: :churnOneNode();
		Assert:isTrue(a1 != 0);
		Assert:areEqualInt(a1, a2);
	}

	## Overwriting a heap field in a helper frame must release the old object
	## deterministically: its slab slot carries the freed marker immediately
	## after the helper returns, and the surviving field value holds exactly
	## one reference (its own).
	##
	## Slot identity is deliberately NOT asserted here: same-size-class raw
	## traffic (HashTable's 32-byte entries land in the same 48-byte class as
	## a small object) legally consumes the freed slot between iterations,
	## so distinct addresses prove nothing about ownership. The freed marker
	## in the slab header is checked before any interposing allocation can
	## reclaim the slot, so a leaked (pinned) old node fails this test.
	Function is testFieldOverwriteFreesOldObject(){
		local LeakNode is k1: LeakNode:init(tag: 'k1');
		local LeakNode is k2: LeakNode:init(tag: 'k2');
		local LeakNode is k3: LeakNode:init(tag: 'k3');
		local LeakHolder is holder: LeakHolder:init(node: LeakNode:init(tag: 'init'));
		# The map stays in the loop to preserve the interposing-allocation
		# environment and keep the raw-Int-key map path exercised (the
		# retained raw keys once pinned these very nodes).
		local Map of Int to Boolean is seen: Map:init();
		local Int is prev: 0;
		local Int is freedCount: 0;
		local Int is i: 0;
		while({ i < 50 }, {
			:overwriteHolderField(h: holder, idx: i);
			if({ prev != 0 }, {
				if({ Mem:loadI64(ptr: prev - 8, byteOffset: 0) == 73083690742142 }, {
					freedCount: freedCount + 1;
				});
			});
			prev: Mem:objToAddr(obj: holder:node);
			seen:set(key: prev, value: true);
			i++;
		});
		# 49 overwritten predecessors must all have been released.
		Assert:areEqualInt(49, freedCount);
		# The survivor holds exactly one reference: the field's own.
		Assert:areEqualInt(1, Mem:loadI32(ptr: prev - 16, byteOffset: 0));
	}

	## High-iteration churn across strings, arrays, maps, closures, boxed
	## locals, and Json:parse must not grow RSS unboundedly.
	Function is testHighIterationChurnBoundedRss(){
		local Int is i: 0;
		local Int is acc: 0;
		while({ i < 2000 }, {
			acc: acc + :churnContainersAndClosures(seed: i);
			i++;
		});
		local Int is rssBefore: :readRssPages();
		i: 0;
		while({ i < 40000 }, {
			acc: acc + :churnContainersAndClosures(seed: i);
			i++;
		});
		local Int is rssAfter: :readRssPages();
		Assert:isTrue(acc > 0);
		if({ rssBefore >= 0 && rssAfter >= 0 }, {
			local Int is deltaPages: rssAfter - rssBefore;
			# 40,000 iterations of strings + arrays + maps + closures + JSON
			# would leak tens of thousands of pages if pools or containers leaked.
			# Allow at most 2048 pages (~8 MB) of slab/allocator headroom.
			Assert:isTrue(deltaPages < 2048);
		});
	}
}

Class is LeakNode{
	String is tag: '';

	replace Function is init(String is tag){
		:tag: tag;
	}
}

Class is LeakHolder{
	LeakNode is node;

	replace Function is init(LeakNode is node){
		:node: node;
	}
}
