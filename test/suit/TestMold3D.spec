#! specunit: suite

Class of SpecUnitTest is TestMold3D{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'mold', [SphereMesh, SpirvBuilder]]
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
}
