#! specunit: suite

Class of SpecUnitTest is TestMold3D{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', as Mem()],
		['base', 'sys', as Process()],
		['base', 'math', as Math()],
		['base', 'mold', [Mat4, SphereMesh, SpirvBuilder]]
	];

	Function is testSphereMeshAccessorsAndDispose(){
		local SphereMesh is s: SphereMesh(radius: 0.5);
		Assert:isTrue(s:vertexAddr() != 0);
		Assert:isTrue(s:vertexBytes() > 0);
		Assert:isTrue(s:indexAddr() != 0);
		Assert:isTrue(s:indexCount() > 0);
		s:dispose();
		Assert:areEqualInt(0, s:vertexAddr());
		Assert:areEqualInt(0, s:indexAddr());
	}

	Function is testSpirvBuilderConstants(){
		Assert:areEqualInt(119734787, SpirvBuilder:MAGIC);
		Assert:areEqualInt(65536, SpirvBuilder:VERSION_1_0);
		Assert:areEqualInt(17, SpirvBuilder:OP_CAPABILITY);

		local SpirvBuilder is sb: SpirvBuilder();
		sb:emitOp(op: SpirvBuilder:OP_DECORATE, args: Array([10, 30, 0]));
		Assert:areEqualInt(4, sb:words:length());
		Assert:areEqualInt((4 * 65536) + 71, sb:words:get(index: 0));
		Assert:areEqualInt(10, sb:words:get(index: 1));
	}

	Function is testMat4ColumnMajorMulAndAliasing(){
		local Mat4 is ops: Mat4();
		local Mat4 is t: ops:translate(tx: 2.0, ty: 3.0, tz: 4.0);
		local Mat4 is rz: ops:rotateZ(rad: Math:pi() * 0.5);

		# Column-major T * Rz: translation column (col=3) stays (2, 3, 4, 1),
		# upper-left 2x2 is [[0, -1], [1, 0]]
		local Mat4 is prod: t:mul(other: rz);
		Assert:areClose(0.0, prod:get(col: 0, row: 0), 0.0001);
		Assert:areClose(1.0, prod:get(col: 0, row: 1), 0.0001);
		Assert:areClose(-1.0, prod:get(col: 1, row: 0), 0.0001);
		Assert:areClose(0.0, prod:get(col: 1, row: 1), 0.0001);
		Assert:areClose(2.0, prod:get(col: 3, row: 0), 0.0001);
		Assert:areClose(3.0, prod:get(col: 3, row: 1), 0.0001);
		Assert:areClose(4.0, prod:get(col: 3, row: 2), 0.0001);
		Assert:areClose(1.0, prod:get(col: 3, row: 3), 0.0001);

		# Aliasing safety: mulInto(other, out: this) and mulInto(other, out: other)
		local Mat4 is aCopy: ops:translate(tx: 2.0, ty: 3.0, tz: 4.0);
		aCopy:mulInto(other: rz, out: aCopy);
		Assert:areClose(prod:get(col: 0, row: 1), aCopy:get(col: 0, row: 1), 0.0001);
		Assert:areClose(prod:get(col: 1, row: 0), aCopy:get(col: 1, row: 0), 0.0001);
		Assert:areClose(prod:get(col: 3, row: 0), aCopy:get(col: 3, row: 0), 0.0001);

		local Mat4 is bCopy: ops:rotateZ(rad: Math:pi() * 0.5);
		t:mulInto(other: bCopy, out: bCopy);
		Assert:areClose(prod:get(col: 0, row: 1), bCopy:get(col: 0, row: 1), 0.0001);
		Assert:areClose(prod:get(col: 3, row: 2), bCopy:get(col: 3, row: 2), 0.0001);

		# packF32 writes 64 bytes of f32; col=3, row=0 (index 12) is 2.0f -> 0x40000000 = 1073741824
		local Int is buf: Mem:alloc(bytes: 64);
		prod:packF32(dstAddr: buf);
		Assert:areEqualInt(1073741824, Mem:loadI32(ptr: buf, byteOffset: 12 * 4));
		Mem:free(ptr: buf);
	}

	local Function of Float is stepMat4Mul(Mat4 is a, Mat4 is b){
		local Mat4 is tmp: a:mul(other: b);
		return tmp:get(col: 0, row: 0);
	}

	Function is testMat4NoMemoryLeak(){
		local Mat4 is ops: Mat4();
		local Mat4 is a: ops:rotateX(rad: 0.3);
		local Mat4 is b: ops:rotateY(rad: 0.7);
		local Float is acc: 0.0;
		# Warm up allocator/heap
		local Int is w: 0;
		while({ w < 2000 }, {
			acc: acc + :stepMat4Mul(a: a, b: b);
			w: w + 1;
		});
		local Int is rssBefore: Process:peakMemoryKb();
		# 30,000 Mat4 allocations across frames (~3.8 MB if destroy() leaked)
		local Int is i: 0;
		while({ i < 30000 }, {
			acc: acc + :stepMat4Mul(a: a, b: b);
			i: i + 1;
		});
		local Int is rssAfter: Process:peakMemoryKb();
		Assert:isTrue(acc > 0.0);
		Assert:isTrue(rssAfter - rssBefore < 1024);
	}
}
