#! Package base:sysinternal
#! Pure-Spec unmanaged floor for the thread-local deferred-release claim pool.
##
## TLS slots in @_spec_tls_i64:
##   slot 3: pool_stack (i64 address of i64[] object address buffer)
##   slot 4: pool_top   (i64 current stack depth)
##   slot 5: pool_cap   (i64 allocated slot capacity)

Class is Pool{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Loops()],
		['base', 'sysinternal', as Arc()]
	];

	Function of Int is poolFrame(){
		return Mem:tlsGetI64(slot: 4);
	}

	Function is poolReleaseTo(Int is mark){
		while({ Mem:tlsGetI64(slot: 4) > mark }, {
			local Int is ntop: Mem:tlsGetI64(slot: 4) - 1;
			Mem:tlsSetI64(slot: 4, val: ntop);
			local Int is stk: Mem:tlsGetI64(slot: 3);
			local Int is obj: Mem:loadI64(ptr: stk, byteOffset: ntop * 8);
			if({ obj != 0 }, {
				Mem:releaseAddr(objAddr: obj);
			});
		});
	}

	## Drains the current frame's pool down to [mark], preserving [keepAddr]
	## into the caller's frame pool when [keepAddr] was claimed in this frame.
	## Safe for `Any` returns that may hold non-pointer values (which are never
	## present in the pool).
	Function is releaseToTransferring(Int is mark, Int is keepAddr){
		local Int is count: Mem:tlsGetI64(slot: 4);
		local Int is stk: Mem:tlsGetI64(slot: 3);
		local Boolean is found: false;
		if({ keepAddr != 0 && stk != 0 && mark < count }, {
			local Int is i: count - 1;
			while({ i >= mark && !found }, {
				if({ Mem:loadI64(ptr: stk, byteOffset: i * 8) == keepAddr }, {
					Mem:storeI64(ptr: stk, byteOffset: i * 8, val: 0);
					found: true;
				});
				i: i - 1;
			});
		});
		:poolReleaseTo(mark: mark);
		if({ found }, {
			:claimPool(objAddr: keepAddr);
		});
	}

	## Removes the TOPMOST pool entry matching [objAddr] WITHOUT releasing
	## it — the ownership transfer for a RETURNED claimed object. Without
	## this, a function returning a claimed allocation leaves its entry on
	## the stack; the frame-exit drain then releases the object the caller
	## now owns, and the caller's own release double-frees it.
	##
	## @param objAddr: The returned object's address.
	Function is unclaimAddr(Int is objAddr){
		if({ objAddr == 0 }, { return; });
		local Int is top: Mem:tlsGetI64(slot: 4);
		if({ top == 0 }, { return; });
		local Int is stk: Mem:tlsGetI64(slot: 3);
		if({ stk == 0 }, { return; });
		local Int is idx: top - 1;
		while({ idx >= 0 }, {
			local Int is entry: Mem:loadI64(ptr: stk, byteOffset: idx * 8);
			if({ entry == objAddr }, {
				local Int is shift: idx;
				while({ shift < top - 1 }, {
					local Int is nxt: Mem:loadI64(ptr: stk, byteOffset: (shift + 1) * 8);
					Mem:storeI64(ptr: stk, byteOffset: shift * 8, val: nxt);
					shift: shift + 1;
				});
				Mem:tlsSetI64(slot: 4, val: top - 1);
				return;
			});
			idx: idx - 1;
		});
	}

	Function of Int is claimPool(Int is objAddr){
		if({ objAddr == 0 }, { return 0; });
		# Autorelease ownership: claimPool ADOPTS an existing +1 reference
		# (from Arc:allocObj, container retain+claim, or return transfer) into
		# the current frame's pool. The frame drain releases it exactly once.
		local Int is top: Mem:tlsGetI64(slot: 4);
		local Int is cap: Mem:tlsGetI64(slot: 5);
		if({ top == cap }, {
			local Int is ncap: if({ cap == 0 }, { 8 }, { cap * 2 });
			local Int is ostk: Mem:tlsGetI64(slot: 3);
			local Int is nstk: Mem:realloc(ptr: ostk, bytes: ncap * 8);
			Mem:tlsSetI64(slot: 3, val: nstk);
			Mem:tlsSetI64(slot: 5, val: ncap);
		});
		local Int is stk: Mem:tlsGetI64(slot: 3);
		Mem:storeI64(ptr: stk, byteOffset: top * 8, val: objAddr);
		Mem:tlsSetI64(slot: 4, val: top + 1);
		return objAddr;
	}

	Function of Boolean is pushErrorHandler(Int is objAddr){
		if({ objAddr == 0 }, { return false; });
		local Int is top: Mem:tlsGetI64(slot: 7);
		local Int is stk: Mem:tlsGetI64(slot: 6);
		if({ top > 0 && stk != 0 && Mem:loadI64(ptr: stk, byteOffset: (top - 1) * 8) == objAddr }, {
			return false;
		});
		local Int is cap: Mem:tlsGetI64(slot: 8);
		if({ top == cap }, {
			local Int is ncap: if({ cap == 0 }, { 8 }, { cap * 2 });
			local Int is nstk: Mem:realloc(ptr: stk, bytes: ncap * 8);
			Mem:tlsSetI64(slot: 6, val: nstk);
			Mem:tlsSetI64(slot: 8, val: ncap);
			stk: nstk;
		});
		Mem:storeI64(ptr: stk, byteOffset: top * 8, val: objAddr);
		Mem:tlsSetI64(slot: 7, val: top + 1);
		return true;
	}

	Function is popErrorHandler(Boolean is pushed){
		if({ pushed }, {
			local Int is top: Mem:tlsGetI64(slot: 7);
			if({ top > 0 }, {
				Mem:tlsSetI64(slot: 7, val: top - 1);
			});
		});
	}

	Function is raisePendingError(Int is errAddr){
		if({ errAddr == 0 }, { return; });
		Mem:retainAddr(objAddr: errAddr);
		local Int is prev: Mem:tlsGetI64(slot: 15);
		if({ prev != 0 }, {
			Mem:releaseAddr(objAddr: prev);
		});
		Mem:tlsSetI64(slot: 15, val: errAddr);
	}

	Function of Int is takePendingError(){
		local Int is cur: Mem:tlsGetI64(slot: 15);
		Mem:tlsSetI64(slot: 15, val: 0);
		return cur;
	}

	Function is finishErrorHandler(Int is errAddr, Boolean is handled){
		if({ !handled && Mem:tlsGetI64(slot: 15) == 0 }, {
			:raisePendingError(errAddr: errAddr);
		});
		if({ errAddr != 0 }, {
			Mem:releaseAddr(objAddr: errAddr);
		});
	}

	local Function is invokeFrameRecorder(Function is cb, Any is errObj, String is clsName, String is methodName, String is file, Int is line){
		cb(errObj, clsName, methodName, file, line);
	}

	local Function is invokePanicRunner(Function is cb, Any is errObj){
		cb(errObj);
	}

	Function is recordPendingFrame(String is clsName, String is methodName, String is file, Int is line){
		local Int is errAddr: Mem:tlsGetI64(slot: 15);
		if({ errAddr == 0 }, { return; });
		local Int is cbAddr: Mem:loadI64(ptr: errAddr, byteOffset: 16);
		if({ cbAddr == 0 }, { return; });
		Mem:tlsSetI64(slot: 15, val: 0);
		:invokeFrameRecorder(cb: Mem:addrToObj(addr: cbAddr), errObj: Mem:addrToObj(addr: errAddr), clsName: clsName, methodName: methodName, file: file, line: line);
		Mem:tlsSetI64(slot: 15, val: errAddr);
	}

	Function is panicPending(){
		local Int is errAddr: Mem:tlsGetI64(slot: 15);
		if({ errAddr == 0 }, { return; });
		local Int is cbAddr: Mem:loadI64(ptr: errAddr, byteOffset: 24);
		if({ cbAddr == 0 }, { return; });
		Mem:tlsSetI64(slot: 15, val: 0);
		:invokePanicRunner(cb: Mem:addrToObj(addr: cbAddr), errObj: Mem:addrToObj(addr: errAddr));
	}

	Function of Int is callCatching(Function is action){
		local Int is addr: Mem:objToAddr(obj: action);
		if({ addr != 0 && Mem:loadI64(ptr: addr, byteOffset: 0) != 0 }, {
			action();
		});
		local Int is errAddr: Mem:tlsGetI64(slot: 15);
		if({ errAddr != 0 }, {
			Mem:tlsSetI64(slot: 15, val: 0);
		});
		return errAddr;
	}

	Function is threadCleanup(){
		local Int is pend: Mem:tlsGetI64(slot: 15);
		if({ pend != 0 }, {
			Mem:tlsSetI64(slot: 15, val: 0);
			Mem:releaseAddr(objAddr: pend);
		});
		local Int is hstk: Mem:tlsGetI64(slot: 6);
		if({ hstk != 0 }, {
			Mem:free(ptr: hstk);
			Mem:tlsSetI64(slot: 6, val: 0);
			Mem:tlsSetI64(slot: 7, val: 0);
			Mem:tlsSetI64(slot: 8, val: 0);
		});
		local Int is stk: Mem:tlsGetI64(slot: 3);
		if({ stk != 0 }, {
			:poolReleaseTo(mark: 0);
			Mem:free(ptr: stk);
			Mem:tlsSetI64(slot: 3, val: 0);
			Mem:tlsSetI64(slot: 4, val: 0);
			Mem:tlsSetI64(slot: 5, val: 0);
		});
		Arc:threadCleanup();
	}
}
