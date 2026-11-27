#! specunit: suite

Class of SpecUnitTest is TestDestroyAndMemLoad{
	replace [String] is namespace: ['test', 'lang', 'destroy_chain'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', as Mem()],
		['base', 'sys', Parallel],
		['base', 'struct', Array],
		['test', 'lang', 'destroy_chain', [DestroyBase, DestroyChild]]
	];

	held Array of Int is sharedNums: Array([10, 20, 30, 40]);

	local Function is createAndDropChild(){
		local DestroyChild is c: DestroyChild();
		return;
	}

	Function is testDestroyChainsChildToParent(){
		DestroyBase:log:clear();
		:createAndDropChild();
		Assert:areEqualInt(2, DestroyBase:log:length());
		Assert:areEqualString('child', DestroyBase:log:get(index: 0));
		Assert:areEqualString('base', DestroyBase:log:get(index: 1));
	}

	Function is testMemLoadU32AndLoadS32(){
		local Int is buf: Mem:alloc(bytes: 8);
		Mem:storeI32(ptr: buf, byteOffset: 0, val: 255 << 24);
		Assert:areEqualInt(4278190080, Mem:loadU32(ptr: buf, byteOffset: 0));
		Assert:areEqualInt(-16777216, Mem:loadS32(ptr: buf, byteOffset: 0));
		Mem:free(ptr: buf);
	}

	Function is testImmortalHeldContainerParallelReads(){
		local Int is outBuf: Mem:alloc(bytes: 4 * 8);
		Parallel():runScoped(
			threads: 4,
			iterations: 4,
			worker: local Function of Int(Int is tid, Int is _cnt){
				local Int is sum: 0;
				local Int is i: 0;
				while({ i < 1000 }, {
					sum: sum + TestDestroyAndMemLoad:sharedNums:get(index: i % 4);
					i: i + 1;
				});
				Mem:storeI64(ptr: outBuf, byteOffset: tid * 8, val: sum);
				return 0;
			}
		);
		Assert:areEqualInt(25000, Mem:loadI64(ptr: outBuf, byteOffset: 0));
		Assert:areEqualInt(25000, Mem:loadI64(ptr: outBuf, byteOffset: 24));
		Mem:free(ptr: outBuf);
	}
}
