#! Package base:sysinternal
#! Low-level memory, pointer, and atomic intrinsics lowered directly to LLVM IR.
##
## Body-less declarations bound to LLVM IR memory and atomic instructions by
## MemCallLowerer. Only base:sys:Mem may call this class directly (enforced by
## the type checker's sysinternal rule).

Class is Mem{
	namespace: ['base', 'sysinternal'];

	Function of Int is alloc(Int is bytes);
	Function of Int is realloc(Int is ptr, Int is bytes);
	Function is free(Int is ptr);
	Function of Int is slabAlloc();
	Function is slabFree(Int is ptr);
	Function of Int is vmAlloc(Int is bytes);
	Function is vmFree(Int is ptr, Int is bytes);
	Function of Int is vmRealloc(Int is ptr, Int is oldBytes, Int is newBytes);
	Function is copy(Int is dst, Int is src, Int is bytes);
	Function is move(Int is dst, Int is src, Int is bytes);
	Function is set(Int is dst, Int is byteVal, Int is bytes);
	Function of Int is cmp(Int is a, Int is b, Int is bytes);
	Function of Int is cstrLen(Int is cstrAddr);

	Function of Int is loadI64(Int is ptr, Int is byteOffset);
	Function is storeI64(Int is ptr, Int is byteOffset, Int is val);
	Function of Int is loadI32(Int is ptr, Int is byteOffset);
	Function is storeI32(Int is ptr, Int is byteOffset, Int is val);
	Function of Int is loadByte(Int is ptr, Int is byteOffset);
	Function is storeByte(Int is ptr, Int is byteOffset, Int is val);
	Function of Any is loadPtr(Int is ptr, Int is byteOffset);
	Function is storePtr(Int is ptr, Int is byteOffset, Any is val);
	Function of Float is loadF64(Int is ptr, Int is byteOffset);
	Function is storeF64(Int is ptr, Int is byteOffset, Float is val);

	Function of Int is objToAddr(Any is obj);
	Function of Any is addrToObj(Int is addr);
	Function of Int is retainAddr(Int is objAddr);
	Function is releaseAddr(Int is objAddr);
	Function of Int is claimPoolAddr(Int is objAddr);
	Function of String is strFromBytes(Int is srcAddr, Int is len);
	Function of String is internStr(String is s);
	Function is panic(String is msg);
	Function of Int is floatToBits(Float is val);
	Function of Float is bitsToFloat(Int is bits);

	Function of Int is atomicLoadI32(Int is addr);
	Function is atomicStoreI32(Int is addr, Int is val);
	Function of Int is atomicAddI32(Int is addr, Int is delta);
	Function of Int is atomicSubI32(Int is addr, Int is delta);
	Function of Int is atomicLoadI64(Int is addr);
	Function is atomicStoreI64(Int is addr, Int is val);
	Function of Int is atomicAddI64(Int is addr, Int is delta);
	Function of Boolean is atomicCasI64(Int is addr, Int is expected, Int is desired);

	Function is callDestroy(Int is fnPtr, Int is objPtr);
	Function of Any is callConstruct(Int is fnAddr);
	Function of Int is classRegistryAddr();
	Function of Int is classRegistryCount();
	Function of Int is heldRegistryAddr();
	Function of String is cstrToStr(Int is cstrAddr);
	Function of String is typeNameOf(Any is obj);
	Function of Int is tlsGetI64(Int is slot);
	Function is tlsSetI64(Int is slot, Int is val);
	Function of Boolean is isMultithreaded();
}
