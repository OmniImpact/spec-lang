#! Package base:sysinternal
#! Pure-Spec unmanaged floor for the 64 KiB aligned fixed-size-class slab allocator.
##
## Size classes (total slot bytes, up to 4 KiB; > 4 KiB uses OS VM directly):
##   class 0:   32B   class 5:  272B
##   class 1:   48B   class 6:  512B
##   class 2:   64B   class 7: 1024B
##   class 3:   80B   class 8: 2048B
##   class 4:  144B   class 9: 4096B
##
## Slab header (96 bytes at offset 0 of each 64 KiB aligned slab):
##   offset  0: slotSize   (i64)
##   offset  8: classIdx   (i64)
##   offset 16: ownerState (atomic i64: ThreadState addr, or 0 if orphaned)
##   offset 24: liveCount  (atomic i64)
##   offset 32: bumpOff    (i64: next uncarved offset in [96..65536])
##   offset 40: localFree  (i64: head of singly-linked local freelist)
##   offset 48: remoteFree (atomic i64: head of lock-free CAS remote freelist)
##   offset 56: nextSlab   (i64: next slab in partial/spare list)
##   offset 64: prevSlab   (i64: prev slab in partial list)
##   offset 72: inPartial  (i64: 1 if linked in partial list, 0 otherwise)
##   offset 80: isFresh    (i64: 1 if freshly mmap'd / zeroed by OS, 0 if reused)
##
## ThreadState layout (240 bytes = 10 classes * 24 bytes in 4096B VM page, TLS slot 14):
##   class base +  0: active  (i64: current active slab)
##   class base +  8: partial (i64: doubly-linked list head of other slabs)
##   class base + 16: spare   (i64: singly-linked list of empty cached slabs)

Class is Slab{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Loops()]
	];

	Function of Int is classForSize(Int is totalBytes){
		if({ totalBytes <= 80 }, {
			if({ totalBytes <= 32 }, { return 0; });
			return (totalBytes - 17) >> 4;
		});
		if({ totalBytes <= 144 }, { return 4; });
		if({ totalBytes <= 272 }, { return 5; });
		if({ totalBytes <= 512 }, { return 6; });
		if({ totalBytes <= 1024 }, { return 7; });
		if({ totalBytes <= 2048 }, { return 8; });
		if({ totalBytes <= 4096 }, { return 9; });
		return -1;
	}

	Function of Int is slotSizeForClass(Int is cls){
		if({ cls == 0 }, { return 32; });
		if({ cls == 1 }, { return 48; });
		if({ cls == 2 }, { return 64; });
		if({ cls == 3 }, { return 80; });
		if({ cls == 4 }, { return 144; });
		if({ cls == 5 }, { return 272; });
		if({ cls == 6 }, { return 512; });
		if({ cls == 7 }, { return 1024; });
		if({ cls == 8 }, { return 2048; });
		return 4096;
	}

	Function of Int is getThreadState(){
		local Int is st: Mem:tlsGetI64(slot: 14);
		if({ st == 0 }, {
			st: base:sysinternal:Mem:vmAlloc(bytes: 4096);
			Mem:tlsSetI64(slot: 14, val: st);
		});
		return st;
	}

	Function of Int is drainRemote(Int is slab){
		local Int is rf: Mem:atomicLoadI64(addr: slab + 48);
		while({ rf != 0 }, {
			if({ Mem:atomicCasI64(addr: slab + 48, expected: rf, desired: 0) }, {
				return rf;
			});
			rf: Mem:atomicLoadI64(addr: slab + 48);
		});
		return 0;
	}

	Function is linkPartial(Int is base, Int is slab){
		local Int is head: Mem:loadI64(ptr: base, byteOffset: 8);
		Mem:storeI64(ptr: slab, byteOffset: 56, val: head);
		Mem:storeI64(ptr: slab, byteOffset: 64, val: 0);
		if({ head != 0 }, {
			Mem:storeI64(ptr: head, byteOffset: 64, val: slab);
		});
		Mem:storeI64(ptr: base, byteOffset: 8, val: slab);
		Mem:storeI64(ptr: slab, byteOffset: 72, val: 1);
	}

	Function is unlinkPartial(Int is base, Int is slab){
		if({ Mem:loadI64(ptr: slab, byteOffset: 72) == 0 }, { return; });
		local Int is nxt: Mem:loadI64(ptr: slab, byteOffset: 56);
		local Int is prv: Mem:loadI64(ptr: slab, byteOffset: 64);
		if({ prv != 0 }, {
			Mem:storeI64(ptr: prv, byteOffset: 56, val: nxt);
		}, {
			Mem:storeI64(ptr: base, byteOffset: 8, val: nxt);
		});
		if({ nxt != 0 }, {
			Mem:storeI64(ptr: nxt, byteOffset: 64, val: prv);
		});
		Mem:storeI64(ptr: slab, byteOffset: 56, val: 0);
		Mem:storeI64(ptr: slab, byteOffset: 64, val: 0);
		Mem:storeI64(ptr: slab, byteOffset: 72, val: 0);
	}

	Function is incLive(Int is slab){
		if({ base:sysinternal:Mem:isMultithreaded() }, {
			Mem:atomicAddI64(addr: slab + 24, delta: 1);
		}, {
			Mem:storeI64(ptr: slab, byteOffset: 24, val: Mem:loadI64(ptr: slab, byteOffset: 24) + 1);
		});
	}

	Function of Int is tryAllocFromSlab(Int is slab, Int is slotSize){
		local Int is lf: Mem:loadI64(ptr: slab, byteOffset: 40);
		if({ lf != 0 }, {
			local Int is next: Mem:loadI64(ptr: lf, byteOffset: 0);
			Mem:storeI64(ptr: slab, byteOffset: 40, val: next);
			:incLive(slab: slab);
			Mem:set(dst: lf, byteVal: 0, bytes: slotSize);
			return lf;
		});
		local Int is bump: Mem:loadI64(ptr: slab, byteOffset: 32);
		if({ bump + slotSize <= 65536 }, {
			local Int is slot: slab + bump;
			Mem:storeI64(ptr: slab, byteOffset: 32, val: bump + slotSize);
			:incLive(slab: slab);
			if({ Mem:loadI64(ptr: slab, byteOffset: 80) == 0 }, {
				Mem:set(dst: slot, byteVal: 0, bytes: slotSize);
			});
			return slot;
		});
		local Int is rf: :drainRemote(slab: slab);
		if({ rf != 0 }, {
			local Int is rnext: Mem:loadI64(ptr: rf, byteOffset: 0);
			Mem:storeI64(ptr: slab, byteOffset: 40, val: rnext);
			:incLive(slab: slab);
			Mem:set(dst: rf, byteVal: 0, bytes: slotSize);
			return rf;
		});
		return 0;
	}

	Function of Int is allocSlow(Int is state, Int is cls, Int is slotSize){
		local Int is base: state + (cls * 24);
		local Int is cur: Mem:loadI64(ptr: base, byteOffset: 8);
		while({ cur != 0 }, {
			local Int is nxt: Mem:loadI64(ptr: cur, byteOffset: 56);
			local Int is slot: :tryAllocFromSlab(slab: cur, slotSize: slotSize);
			if({ slot != 0 }, {
				:unlinkPartial(base: base, slab: cur);
				Mem:storeI64(ptr: base, byteOffset: 0, val: cur);
				return slot;
			});
			if({ Mem:atomicLoadI64(addr: cur + 24) == 1 }, {
				:unlinkPartial(base: base, slab: cur);
				local Int is oldSp: Mem:loadI64(ptr: base, byteOffset: 16);
				Mem:storeI64(ptr: cur, byteOffset: 56, val: oldSp);
				Mem:storeI64(ptr: base, byteOffset: 16, val: cur);
			});
			cur: nxt;
		});

		local Int is sp: Mem:loadI64(ptr: base, byteOffset: 16);
		if({ sp != 0 }, {
			local Int is nextSp: Mem:loadI64(ptr: sp, byteOffset: 56);
			Mem:storeI64(ptr: sp, byteOffset: 56, val: 0);
			Mem:storeI64(ptr: base, byteOffset: 16, val: nextSp);
			Mem:storeI64(ptr: sp, byteOffset: 32, val: 96 + slotSize);
			Mem:storeI64(ptr: sp, byteOffset: 40, val: 0);
			Mem:atomicStoreI64(addr: sp + 48, val: 0);
			Mem:storeI64(ptr: sp, byteOffset: 80, val: 0);
			Mem:atomicStoreI64(addr: sp + 24, val: 2);
			Mem:storeI64(ptr: base, byteOffset: 0, val: sp);
			local Int is spSlot: sp + 96;
			Mem:set(dst: spSlot, byteVal: 0, bytes: slotSize);
			return spSlot;
		});

		local Int is ns: base:sysinternal:Mem:slabAlloc();
		Mem:storeI64(ptr: ns, byteOffset: 0, val: slotSize);
		Mem:storeI64(ptr: ns, byteOffset: 8, val: cls);
		Mem:atomicStoreI64(addr: ns + 16, val: state);
		Mem:atomicStoreI64(addr: ns + 24, val: 2);
		Mem:storeI64(ptr: ns, byteOffset: 32, val: 96 + slotSize);
		Mem:storeI64(ptr: ns, byteOffset: 80, val: 1);
		Mem:storeI64(ptr: base, byteOffset: 0, val: ns);
		return ns + 96;
	}

	Function of Int is allocSlot(Int is cls){
		local Int is state: Mem:tlsGetI64(slot: 14);
		if({ state == 0 }, {
			state: :getThreadState();
		});
		local Int is slotSize: :slotSizeForClass(cls: cls);
		local Int is base: state + (cls * 24);
		local Int is s: Mem:loadI64(ptr: base, byteOffset: 0);
		if({ s != 0 }, {
			local Int is lf: Mem:loadI64(ptr: s, byteOffset: 40);
			if({ lf != 0 }, {
				# Freelist-integrity guard: the head must point inside this
				# slab. A foreign head means a prior corruption — panic at
				# the fault site instead of dereferencing a wild pointer.
				if({ lf < s + 96 || lf >= s + 65536 }, {
					Mem:panic(msg: 'slab: allocSlot freelist head outside its slab');
				});
				local Int is next: Mem:loadI64(ptr: lf, byteOffset: 0);
				Mem:storeI64(ptr: s, byteOffset: 40, val: next);
				if({ base:sysinternal:Mem:isMultithreaded() }, {
					Mem:atomicAddI64(addr: s + 24, delta: 1);
				}, {
					Mem:storeI64(ptr: s, byteOffset: 24, val: Mem:loadI64(ptr: s, byteOffset: 24) + 1);
				});
				Mem:set(dst: lf, byteVal: 0, bytes: slotSize);
				return lf;
			});
			local Int is bump: Mem:loadI64(ptr: s, byteOffset: 32);
			if({ bump + slotSize <= 65536 }, {
				local Int is slot: s + bump;
				Mem:storeI64(ptr: s, byteOffset: 32, val: bump + slotSize);
				if({ base:sysinternal:Mem:isMultithreaded() }, {
					Mem:atomicAddI64(addr: s + 24, delta: 1);
				}, {
					Mem:storeI64(ptr: s, byteOffset: 24, val: Mem:loadI64(ptr: s, byteOffset: 24) + 1);
				});
				if({ Mem:loadI64(ptr: s, byteOffset: 80) == 0 }, {
					Mem:set(dst: slot, byteVal: 0, bytes: slotSize);
				});
				return slot;
			});
			local Int is rf: :drainRemote(slab: s);
			if({ rf != 0 }, {
				local Int is rnext: Mem:loadI64(ptr: rf, byteOffset: 0);
				Mem:storeI64(ptr: s, byteOffset: 40, val: rnext);
				if({ base:sysinternal:Mem:isMultithreaded() }, {
					Mem:atomicAddI64(addr: s + 24, delta: 1);
				}, {
					Mem:storeI64(ptr: s, byteOffset: 24, val: Mem:loadI64(ptr: s, byteOffset: 24) + 1);
				});
				Mem:set(dst: rf, byteVal: 0, bytes: slotSize);
				return rf;
			});
			:linkPartial(base: base, slab: s);
			Mem:storeI64(ptr: base, byteOffset: 0, val: 0);
		});
		return :allocSlow(state: state, cls: cls, slotSize: slotSize);
	}

	Function is freeSlot(Int is slotAddr){
		local Int is s: slotAddr & (-65536);
		# Freelist-integrity guards: a slot must lie inside its 64 KiB slab,
		# past the 96-byte header, and a slot already carrying the freed
		# marker is a DOUBLE FREE (its dead destroyFn/kind field holds the
		# marker). Both conditions otherwise poison the freelist silently
		# and surface later as wild-pointer faults far from the cause —
		# panic here instead, where the freeing stack is attributable.
		if({ slotAddr < s + 96 || slotAddr >= s + 65536 }, {
			Mem:panic(msg: 'slab: freeSlot slot outside its slab');
		});
		if({ Mem:loadI64(ptr: slotAddr, byteOffset: 8) == 73083690742142 }, {
			Mem:panic(msg: 'slab: double free of already-freed slot');
		});
		Mem:storeI64(ptr: slotAddr, byteOffset: 8, val: 73083690742142);
		local Int is myState: Mem:tlsGetI64(slot: 14);
		local Boolean is mt: base:sysinternal:Mem:isMultithreaded();
		local Int is owner: if({ mt }, { Mem:atomicLoadI64(addr: s + 16) }, { Mem:loadI64(ptr: s, byteOffset: 16) });
		if({ myState != 0 && owner == myState }, {
			local Int is oldLf: Mem:loadI64(ptr: s, byteOffset: 40);
			Mem:storeI64(ptr: slotAddr, byteOffset: 0, val: oldLf);
			Mem:storeI64(ptr: s, byteOffset: 40, val: slotAddr);
			local Int is oldLive: 0;
			if({ mt }, {
				oldLive: Mem:atomicAddI64(addr: s + 24, delta: -1);
			}, {
				oldLive: Mem:loadI64(ptr: s, byteOffset: 24);
				Mem:storeI64(ptr: s, byteOffset: 24, val: oldLive - 1);
			});
			if({ oldLive == 2 }, {
				local Int is cls: Mem:loadI64(ptr: s, byteOffset: 8);
				local Int is base: myState + (cls * 24);
				if({ s == Mem:loadI64(ptr: base, byteOffset: 0) }, {
					Mem:storeI64(ptr: s, byteOffset: 32, val: 96);
					Mem:storeI64(ptr: s, byteOffset: 40, val: 0);
					Mem:atomicStoreI64(addr: s + 48, val: 0);
					Mem:storeI64(ptr: s, byteOffset: 80, val: 0);
					return;
				});
				:unlinkPartial(base: base, slab: s);
				local Int is oldSp2: Mem:loadI64(ptr: base, byteOffset: 16);
				Mem:storeI64(ptr: s, byteOffset: 56, val: oldSp2);
				Mem:storeI64(ptr: base, byteOffset: 16, val: s);
			});
			return;
		});

		local Boolean is pushed: false;
		while({ !pushed }, {
			local Int is oldRf: Mem:atomicLoadI64(addr: s + 48);
			Mem:storeI64(ptr: slotAddr, byteOffset: 0, val: oldRf);
			pushed: Mem:atomicCasI64(addr: s + 48, expected: oldRf, desired: slotAddr);
		});
		local Int is oldLiveR: Mem:atomicAddI64(addr: s + 24, delta: -1);
		if({ oldLiveR == 1 }, {
			base:sysinternal:Mem:slabFree(ptr: s);
		});
	}

	Function is orphanOrFree(Int is slab, Int is state){
		if({ slab == 0 }, { return; });
		Mem:atomicCasI64(addr: slab + 16, expected: state, desired: 0);
		local Int is oldLive: Mem:atomicAddI64(addr: slab + 24, delta: -1);
		if({ oldLive == 1 }, {
			base:sysinternal:Mem:slabFree(ptr: slab);
		});
	}

	Function is threadCleanup(){
		local Int is myState: Mem:tlsGetI64(slot: 14);
		if({ myState == 0 }, { return; });
		Mem:tlsSetI64(slot: 14, val: 0);
		local Int is c: 0;
		while({ c < 10 }, {
			local Int is base: myState + (c * 24);
			local Int is act: Mem:loadI64(ptr: base, byteOffset: 0);
			if({ act != 0 }, {
				:orphanOrFree(slab: act, state: myState);
			});
			local Int is sp: Mem:loadI64(ptr: base, byteOffset: 16);
			while({ sp != 0 }, {
				local Int is spNxt: Mem:loadI64(ptr: sp, byteOffset: 56);
				base:sysinternal:Mem:slabFree(ptr: sp);
				sp: spNxt;
			});
			local Int is cur: Mem:loadI64(ptr: base, byteOffset: 8);
			while({ cur != 0 }, {
				local Int is nxt: Mem:loadI64(ptr: cur, byteOffset: 56);
				:orphanOrFree(slab: cur, state: myState);
				cur: nxt;
			});
			c: c + 1;
		});
		base:sysinternal:Mem:vmFree(ptr: myState, bytes: 4096);
	}
}
