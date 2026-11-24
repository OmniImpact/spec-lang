#! SpecUnit suite for base:sys:Mem / base:sysinternal:Mem LLVM intrinsics.

Class of SpecUnitTest is TestMem{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Mem()]
	];

	Function is testAllocLoadsStoresAndFree(){
		local Int is buf: Mem:alloc(bytes: 64);
		Assert:isTrue(buf != 0);

		# Zero-initialized by calloc
		Assert:areEqualInt(0, Mem:loadI64(ptr: buf, byteOffset: 0));
		Assert:areEqualInt(0, Mem:loadI32(ptr: buf, byteOffset: 8));
		Assert:areEqualInt(0, Mem:loadByte(ptr: buf, byteOffset: 16));

		# Store/load I64, I32, Byte, F64
		Mem:storeI64(ptr: buf, byteOffset: 0, val: 1234567890123);
		Mem:storeI32(ptr: buf, byteOffset: 8, val: 424242);
		Mem:storeByte(ptr: buf, byteOffset: 12, val: 251);
		Mem:storeF64(ptr: buf, byteOffset: 16, val: 3.14159);

		Assert:areEqualInt(1234567890123, Mem:loadI64(ptr: buf, byteOffset: 0));
		Assert:areEqualInt(424242, Mem:loadI32(ptr: buf, byteOffset: 8));
		Assert:areEqualInt(251, Mem:loadByte(ptr: buf, byteOffset: 12));
		Assert:isTrue(Mem:loadF64(ptr: buf, byteOffset: 16) > 3.14 && Mem:loadF64(ptr: buf, byteOffset: 16) < 3.15);

		# Realloc preserves prefix
		local Int is buf2: Mem:realloc(ptr: buf, bytes: 128);
		Assert:areEqualInt(1234567890123, Mem:loadI64(ptr: buf2, byteOffset: 0));
		Assert:areEqualInt(424242, Mem:loadI32(ptr: buf2, byteOffset: 8));
		Assert:areEqualInt(251, Mem:loadByte(ptr: buf2, byteOffset: 12));

		Mem:free(ptr: buf2);
	}

	Function is testCopyMoveSetCmpAndCstrLen(){
		local Int is a: Mem:alloc(bytes: 16);
		local Int is b: Mem:alloc(bytes: 16);

		Mem:storeByte(ptr: a, byteOffset: 0, val: 65);
		Mem:storeByte(ptr: a, byteOffset: 1, val: 66);
		Mem:storeByte(ptr: a, byteOffset: 2, val: 67);
		Mem:storeByte(ptr: a, byteOffset: 3, val: 0);

		Assert:areEqualInt(3, Mem:cstrLen(cstrAddr: a));
		Mem:copy(dst: b, src: a, bytes: 4);
		Assert:areEqualInt(0, Mem:cmp(a: a, b: b, bytes: 3));

		Mem:storeByte(ptr: b, byteOffset: 2, val: 68);
		Assert:isTrue(Mem:cmp(a: a, b: b, bytes: 3) < 0);
		Assert:isTrue(Mem:cmp(a: b, b: a, bytes: 3) > 0);

		# Overlapping move
		Mem:move(dst: a + 1, src: a, bytes: 3);
		Assert:areEqualInt(65, Mem:loadByte(ptr: a, byteOffset: 0));
		Assert:areEqualInt(65, Mem:loadByte(ptr: a, byteOffset: 1));
		Assert:areEqualInt(66, Mem:loadByte(ptr: a, byteOffset: 2));
		Assert:areEqualInt(67, Mem:loadByte(ptr: a, byteOffset: 3));

		Mem:set(dst: a, byteVal: 9, bytes: 8);
		Assert:areEqualInt(9, Mem:loadByte(ptr: a, byteOffset: 0));
		Assert:areEqualInt(9, Mem:loadByte(ptr: a, byteOffset: 7));

		Mem:free(ptr: a);
		Mem:free(ptr: b);
	}

	Function is testAtomicsAndBitcasts(){
		local Int is cell: Mem:alloc(bytes: 16);

		# 32-bit atomics
		Mem:atomicStoreI32(addr: cell, val: 10);
		Assert:areEqualInt(10, Mem:atomicLoadI32(addr: cell));
		Assert:areEqualInt(10, Mem:atomicAddI32(addr: cell, delta: 5));
		Assert:areEqualInt(15, Mem:atomicLoadI32(addr: cell));
		Assert:areEqualInt(15, Mem:atomicSubI32(addr: cell, delta: 3));
		Assert:areEqualInt(12, Mem:atomicLoadI32(addr: cell));

		# 64-bit atomics + CAS
		local Int is cell64: cell + 8;
		Mem:atomicStoreI64(addr: cell64, val: 100);
		Assert:areEqualInt(100, Mem:atomicLoadI64(addr: cell64));
		Assert:isFalse(Mem:atomicCasI64(addr: cell64, expected: 99, desired: 200));
		Assert:areEqualInt(100, Mem:atomicLoadI64(addr: cell64));
		Assert:isTrue(Mem:atomicCasI64(addr: cell64, expected: 100, desired: 200));
		Assert:areEqualInt(200, Mem:atomicLoadI64(addr: cell64));
		Assert:areEqualInt(200, Mem:atomicAddI64(addr: cell64, delta: 50));
		Assert:areEqualInt(250, Mem:atomicLoadI64(addr: cell64));

		# Float bitcast round-trip
		local Int is bits: Mem:floatToBits(val: 2.5);
		Assert:isTrue(Mem:bitsToFloat(bits: bits) == 2.5);

		# Object address round-trip
		local String is s: 'hello';
		local Int is addr: Mem:objToAddr(obj: s);
		Assert:isTrue(addr != 0);
		local String is s2: Mem:addrToObj(addr: addr) as String;
		Assert:areEqualString('hello', s2);

		Mem:free(ptr: cell);
	}
}
