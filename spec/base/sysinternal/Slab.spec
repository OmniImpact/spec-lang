#! Package base:sysinternal
#! Pure-Spec unmanaged floor for the 64 KiB aligned small-object slab allocator.
##
## Size classes (total slot bytes including 16-byte SpecHeader):
##   class 0:  32B (payload   1..16B)
##   class 1:  48B (payload  17..32B)
##   class 2:  64B (payload  33..48B)
##   class 3:  80B (payload  49..64B)
##   class 4: 144B (payload  65..128B)
##   class 5: 272B (payload 129..256B)
##
## Slab header (96 bytes at offset 0 of each 64 KiB aligned slab):
##   offset  0: slotSize   (i64)
##   offset  8: classIdx   (i64)
##   offset 16: ownerState (atomic i64: ThreadState addr, or 0 if orphaned)
##   offset 24: liveCount  (atomic i64)
##   offset 32: bumpOff    (i64: next uncarved offset in [96..65536])
##   offset 40: localFree  (i64: head of singly-linked local freelist)
##   offset 48: remoteFree (atomic i64: head of lock-free CAS remote freelist)
##   offset 56: nextSlab   (i64: next slab in partial list)
##   offset 64: prevSlab   (i64: prev slab in partial list)
##   offset 72: inPartial  (i64: 1 if linked in partial list, 0 otherwise)
##   offset 80: isFresh    (i64: 1 if freshly mmap'd / zeroed by OS, 0 if reused)
##
## ThreadState layout (144 bytes = 6 classes * 24 bytes, stored in TLS slot 14):
##   class base +  0: active  (i64: current active slab)
##   class base +  8: partial (i64: doubly-linked list head of other slabs)
##   class base + 16: spare   (i64: at most 1 cached empty slab)

Class is Slab{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Loops()]
	];

	Function of Int is classForPayload(Int is payloadSize){
		if({ payloadSize <= 64 }, {
			if({ payloadSize <= 1 }, { return 0; });
			return (payloadSize - 1) >> 4;
		});
		if({ payloadSize <= 128 }, { return 4; });
		if({ payloadSize <= 256 }, { return 5; });
		return -1;
	}

	Function of Int is slotSizeForClass(Int is cls){
		if({ cls == 0 }, { return 32; });
		if({ cls == 1 }, { return 48; });
		if({ cls == 2 }, { return 64; });
		if({ cls == 3 }, { return 80; });
		if({ cls == 4 }, { return 144; });
		return 272;
	}

	Function of Int is getThreadState(){
		local Int is st: Mem:tlsGetI64(slot: 14);
		if({ st == 0 }, {
			st: Mem:alloc(bytes: 144);
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
			self:incLive(slab: slab);
			Mem:set(dst: lf + 16, byteVal: 0, bytes: slotSize - 16);
			return lf;
		});
		local Int is bump: Mem:loadI64(ptr: slab, byteOffset: 32);
		if({ bump + slotSize <= 65536 }, {
			local Int is slot: slab + bump;
			Mem:storeI64(ptr: slab, byteOffset: 32, val: bump + slotSize);
			self:incLive(slab: slab);
			if({ Mem:loadI64(ptr: slab, byteOffset: 80) == 0 }, {
				Mem:set(dst: slot + 16, byteVal: 0, bytes: slotSize - 16);
			});
			return slot;
		});
		local Int is rf: self:drainRemote(slab: slab);
		if({ rf != 0 }, {
			local Int is rnext: Mem:loadI64(ptr: rf, byteOffset: 0);
			Mem:storeI64(ptr: slab, byteOffset: 40, val: rnext);
			self:incLive(slab: slab);
			Mem:set(dst: rf + 16, byteVal: 0, bytes: slotSize - 16);
			return rf;
		});
		return 0;
	}

	Function of Int is allocSlow(Int is state, Int is cls, Int is slotSize){
		local Int is base: state + (cls * 24);
		local Int is cur: Mem:loadI64(ptr: base, byteOffset: 8);
		while({ cur != 0 }, {
			local Int is nxt: Mem:loadI64(ptr: cur, byteOffset: 56);
			local Int is slot: self:tryAllocFromSlab(slab: cur, slotSize: slotSize);
			if({ slot != 0 }, {
				self:unlinkPartial(base: base, slab: cur);
				Mem:storeI64(ptr: base, byteOffset: 0, val: cur);
				return slot;
			});
			if({ Mem:atomicLoadI64(addr: cur + 24) == 0 }, {
				self:unlinkPartial(base: base, slab: cur);
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
			Mem:storeI64(ptr: sp, byteOffset: 80, val: 0);
			Mem:atomicAddI64(addr: sp + 24, delta: 1);
			Mem:storeI64(ptr: base, byteOffset: 0, val: sp);
			local Int is spSlot: sp + 96;
			Mem:set(dst: spSlot + 16, byteVal: 0, bytes: slotSize - 16);
			return spSlot;
		});

		local Int is ns: base:sysinternal:Mem:slabAlloc();
		Mem:storeI64(ptr: ns, byteOffset: 0, val: slotSize);
		Mem:storeI64(ptr: ns, byteOffset: 8, val: cls);
		Mem:atomicStoreI64(addr: ns + 16, val: state);
		Mem:atomicStoreI64(addr: ns + 24, val: 1);
		Mem:storeI64(ptr: ns, byteOffset: 32, val: 96 + slotSize);
		Mem:storeI64(ptr: ns, byteOffset: 80, val: 1);
		Mem:storeI64(ptr: base, byteOffset: 0, val: ns);
		return ns + 96;
	}

	Function of Int is allocObj(Int is cls){
		local Int is state: Mem:tlsGetI64(slot: 14);
		if({ state == 0 }, {
			state: self:getThreadState();
		});
		local Int is slotSize: self:slotSizeForClass(cls: cls);
		local Int is base: state + (cls * 24);
		local Int is s: Mem:loadI64(ptr: base, byteOffset: 0);
		if({ s != 0 }, {
			local Int is lf: Mem:loadI64(ptr: s, byteOffset: 40);
			if({ lf != 0 }, {
				local Int is next: Mem:loadI64(ptr: lf, byteOffset: 0);
				Mem:storeI64(ptr: s, byteOffset: 40, val: next);
				if({ base:sysinternal:Mem:isMultithreaded() }, {
					Mem:atomicAddI64(addr: s + 24, delta: 1);
				}, {
					Mem:storeI64(ptr: s, byteOffset: 24, val: Mem:loadI64(ptr: s, byteOffset: 24) + 1);
				});
				Mem:set(dst: lf + 16, byteVal: 0, bytes: slotSize - 16);
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
					Mem:set(dst: slot + 16, byteVal: 0, bytes: slotSize - 16);
				});
				return slot;
			});
			local Int is rf: self:drainRemote(slab: s);
			if({ rf != 0 }, {
				local Int is rnext: Mem:loadI64(ptr: rf, byteOffset: 0);
				Mem:storeI64(ptr: s, byteOffset: 40, val: rnext);
				if({ base:sysinternal:Mem:isMultithreaded() }, {
					Mem:atomicAddI64(addr: s + 24, delta: 1);
				}, {
					Mem:storeI64(ptr: s, byteOffset: 24, val: Mem:loadI64(ptr: s, byteOffset: 24) + 1);
				});
				Mem:set(dst: rf + 16, byteVal: 0, bytes: slotSize - 16);
				return rf;
			});
			self:linkPartial(base: base, slab: s);
			Mem:storeI64(ptr: base, byteOffset: 0, val: 0);
		});
		return self:allocSlow(state: state, cls: cls, slotSize: slotSize);
	}

	Function is freeSlot(Int is hdrAddr){
		local Int is s: hdrAddr & (-65536);
		local Int is myState: Mem:tlsGetI64(slot: 14);
		local Boolean is mt: base:sysinternal:Mem:isMultithreaded();
		local Int is owner: if({ mt }, { Mem:atomicLoadI64(addr: s + 16) }, { Mem:loadI64(ptr: s, byteOffset: 16) });
		if({ myState != 0 && owner == myState }, {
			local Int is oldLf: Mem:loadI64(ptr: s, byteOffset: 40);
			Mem:storeI64(ptr: hdrAddr, byteOffset: 0, val: oldLf);
			Mem:storeI64(ptr: s, byteOffset: 40, val: hdrAddr);
			local Int is oldLive: 0;
			if({ mt }, {
				oldLive: Mem:atomicAddI64(addr: s + 24, delta: -1);
			}, {
				oldLive: Mem:loadI64(ptr: s, byteOffset: 24);
				Mem:storeI64(ptr: s, byteOffset: 24, val: oldLive - 1);
			});
			if({ oldLive == 1 }, {
				local Int is cls: Mem:loadI64(ptr: s, byteOffset: 8);
				local Int is base: myState + (cls * 24);
				if({ s == Mem:loadI64(ptr: base, byteOffset: 0) }, {
					Mem:storeI64(ptr: s, byteOffset: 32, val: 96);
					Mem:storeI64(ptr: s, byteOffset: 40, val: 0);
					Mem:storeI64(ptr: s, byteOffset: 80, val: 0);
					return;
				});
				self:unlinkPartial(base: base, slab: s);
				local Int is oldSp2: Mem:loadI64(ptr: base, byteOffset: 16);
				Mem:storeI64(ptr: s, byteOffset: 56, val: oldSp2);
				Mem:storeI64(ptr: base, byteOffset: 16, val: s);
			});
			return;
		});

		local Boolean is pushed: false;
		while({ !pushed }, {
			local Int is oldRf: Mem:atomicLoadI64(addr: s + 48);
			Mem:storeI64(ptr: hdrAddr, byteOffset: 0, val: oldRf);
			pushed: Mem:atomicCasI64(addr: s + 48, expected: oldRf, desired: hdrAddr);
		});
		local Int is oldLiveR: Mem:atomicAddI64(addr: s + 24, delta: -1);
		if({ oldLiveR == 1 }, {
			local Int is curOwner: Mem:atomicLoadI64(addr: s + 16);
			if({ curOwner == 0 }, {
				base:sysinternal:Mem:slabFree(ptr: s);
			});
		});
	}

	Function is orphanOrFree(Int is slab, Int is state){
		if({ slab == 0 }, { return; });
		Mem:atomicCasI64(addr: slab + 16, expected: state, desired: 0);
		if({ Mem:atomicLoadI64(addr: slab + 24) == 0 }, {
			base:sysinternal:Mem:slabFree(ptr: slab);
		});
	}

	Function is threadCleanup(){
		local Int is myState: Mem:tlsGetI64(slot: 14);
		if({ myState == 0 }, { return; });
		Mem:tlsSetI64(slot: 14, val: 0);
		local Int is c: 0;
		while({ c < 6 }, {
			local Int is base: myState + (c * 24);
			local Int is act: Mem:loadI64(ptr: base, byteOffset: 0);
			if({ act != 0 }, {
				self:orphanOrFree(slab: act, state: myState);
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
				self:orphanOrFree(slab: cur, state: myState);
				cur: nxt;
			});
			c: c + 1;
		});
		Mem:free(ptr: myState);
	}
}
