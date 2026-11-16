#! Package base:sys
#! Public wrapper over the base:sysinternal:Mem LLVM intrinsic floor.
##
## Provides raw heap allocation, typed byte-offset loads and stores,
## pointer/address conversions, and atomic operations for runtime and
## container implementations in pure Spec.

Class is Mem{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Mem]
	];

	Function of Int is alloc(Int is bytes){
		return base:sysinternal:Mem:alloc(bytes: bytes);
	}

	Function of Int is realloc(Int is ptr, Int is bytes){
		return base:sysinternal:Mem:realloc(ptr: ptr, bytes: bytes);
	}

	Function is free(Int is ptr){
		base:sysinternal:Mem:free(ptr: ptr);
	}

	Function is copy(Int is dst, Int is src, Int is bytes){
		base:sysinternal:Mem:copy(dst: dst, src: src, bytes: bytes);
	}

	Function is move(Int is dst, Int is src, Int is bytes){
		base:sysinternal:Mem:move(dst: dst, src: src, bytes: bytes);
	}

	Function is set(Int is dst, Int is byteVal, Int is bytes){
		base:sysinternal:Mem:set(dst: dst, byteVal: byteVal, bytes: bytes);
	}

	Function of Int is cmp(Int is a, Int is b, Int is bytes){
		return base:sysinternal:Mem:cmp(a: a, b: b, bytes: bytes);
	}

	Function of Int is cstrLen(Int is cstrAddr){
		return base:sysinternal:Mem:cstrLen(cstrAddr: cstrAddr);
	}

	Function of Int is loadI64(Int is ptr, Int is byteOffset){
		return base:sysinternal:Mem:loadI64(ptr: ptr, byteOffset: byteOffset);
	}

	Function is storeI64(Int is ptr, Int is byteOffset, Int is val){
		base:sysinternal:Mem:storeI64(ptr: ptr, byteOffset: byteOffset, val: val);
	}

	Function of Int is loadI32(Int is ptr, Int is byteOffset){
		return base:sysinternal:Mem:loadI32(ptr: ptr, byteOffset: byteOffset);
	}

	Function is storeI32(Int is ptr, Int is byteOffset, Int is val){
		base:sysinternal:Mem:storeI32(ptr: ptr, byteOffset: byteOffset, val: val);
	}

	Function of Int is loadByte(Int is ptr, Int is byteOffset){
		return base:sysinternal:Mem:loadByte(ptr: ptr, byteOffset: byteOffset);
	}

	Function is storeByte(Int is ptr, Int is byteOffset, Int is val){
		base:sysinternal:Mem:storeByte(ptr: ptr, byteOffset: byteOffset, val: val);
	}

	Function of Any is loadPtr(Int is ptr, Int is byteOffset){
		return base:sysinternal:Mem:loadPtr(ptr: ptr, byteOffset: byteOffset);
	}

	Function is storePtr(Int is ptr, Int is byteOffset, Any is val){
		base:sysinternal:Mem:storePtr(ptr: ptr, byteOffset: byteOffset, val: val);
	}

	Function of Float is loadF64(Int is ptr, Int is byteOffset){
		return base:sysinternal:Mem:loadF64(ptr: ptr, byteOffset: byteOffset);
	}

	Function is storeF64(Int is ptr, Int is byteOffset, Float is val){
		base:sysinternal:Mem:storeF64(ptr: ptr, byteOffset: byteOffset, val: val);
	}

	Function of Int is objToAddr(Any is obj){
		return base:sysinternal:Mem:objToAddr(obj: obj);
	}

	Function of Any is addrToObj(Int is addr){
		return base:sysinternal:Mem:addrToObj(addr: addr);
	}

	Function of Int is retainAddr(Int is objAddr){
		return base:sysinternal:Mem:retainAddr(objAddr: objAddr);
	}

	Function is releaseAddr(Int is objAddr){
		base:sysinternal:Mem:releaseAddr(objAddr: objAddr);
	}

	Function of Int is claimPoolAddr(Int is objAddr){
		return base:sysinternal:Mem:claimPoolAddr(objAddr: objAddr);
	}

	Function of String is strFromBytes(Int is srcAddr, Int is len){
		return base:sysinternal:Mem:strFromBytes(srcAddr: srcAddr, len: len);
	}

	Function of String is internStr(String is s){
		return base:sysinternal:Mem:internStr(s: s);
	}

	Function is panic(String is msg){
		base:sysinternal:Mem:panic(msg: msg);
	}

	Function of Int is floatToBits(Float is val){
		return base:sysinternal:Mem:floatToBits(val: val);
	}

	Function of Float is bitsToFloat(Int is bits){
		return base:sysinternal:Mem:bitsToFloat(bits: bits);
	}

	Function of Int is atomicLoadI32(Int is addr){
		return base:sysinternal:Mem:atomicLoadI32(addr: addr);
	}

	Function is atomicStoreI32(Int is addr, Int is val){
		base:sysinternal:Mem:atomicStoreI32(addr: addr, val: val);
	}

	Function of Int is atomicAddI32(Int is addr, Int is delta){
		return base:sysinternal:Mem:atomicAddI32(addr: addr, delta: delta);
	}

	Function of Int is atomicSubI32(Int is addr, Int is delta){
		return base:sysinternal:Mem:atomicSubI32(addr: addr, delta: delta);
	}

	Function of Int is atomicLoadI64(Int is addr){
		return base:sysinternal:Mem:atomicLoadI64(addr: addr);
	}

	Function is atomicStoreI64(Int is addr, Int is val){
		base:sysinternal:Mem:atomicStoreI64(addr: addr, val: val);
	}

	Function of Int is atomicAddI64(Int is addr, Int is delta){
		return base:sysinternal:Mem:atomicAddI64(addr: addr, delta: delta);
	}

	Function of Boolean is atomicCasI64(Int is addr, Int is expected, Int is desired){
		return base:sysinternal:Mem:atomicCasI64(addr: addr, expected: expected, desired: desired);
	}

	Function is callDestroy(Int is fnPtr, Int is objPtr){
		base:sysinternal:Mem:callDestroy(fnPtr: fnPtr, objPtr: objPtr);
	}
}
