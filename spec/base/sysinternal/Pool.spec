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

	Function of Int is claimPool(Int is objAddr){
		if({ objAddr == 0 }, { return 0; });
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

	Function is threadCleanup(){
		local Int is stk: Mem:tlsGetI64(slot: 3);
		if({ stk != 0 }, {
			self:poolReleaseTo(mark: 0);
			Mem:free(ptr: stk);
			Mem:tlsSetI64(slot: 3, val: 0);
			Mem:tlsSetI64(slot: 4, val: 0);
			Mem:tlsSetI64(slot: 5, val: 0);
		});
		Arc:threadCleanup();
	}
}
