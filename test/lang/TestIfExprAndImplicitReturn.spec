#! specunit: suite

Class of SpecUnitTest is TestIfExprAndImplicitReturn{
	replace [String] is namespace: ['test', 'lang'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'math', Vector],
		['base', 'sys', as Mem()]
	];

	local Function of Float is acceptFloat(Float is v){
		v * 2.0
	}

	local Function of Int is parenImplicitSingle(Int is color){ (color >> 16) & 255 }

	local Function of Int is parenImplicitMulti(Int is color){
		local Int is shifted: color;
		(shifted >> 8) & 255
	}

	Function is testIfAsCallArgument(){
		local Vector is vec: Vector(length: 4);
		local Float is x: -3.5;
		vec:set(index: 0, value: if({ x < 0.0 }, { -x }, { x }));
		vec:set(index: 1, value: if({ x > 0.0 }, { 1.0 }, { 2.5 }));
		Assert:isTrue(vec:get(index: 0) == 3.5);
		Assert:isTrue(vec:get(index: 1) == 2.5);

		local Int is ptr: vec:dataAddr();
		storeF64(ptr: ptr, byteOffset: 16, val: if({ x < 0.0 }, { -x }, { x }));
		Assert:isTrue(vec:get(index: 2) == 3.5);

		Assert:isTrue(acceptFloat(v: if({ x < 0.0 }, { 4.0 }, { 1.0 })) == 8.0);
		vec:destroy();
	}

	Function is testIfInBinaryExpr(){
		local Float is a: 1.5 + if({ 2 > 1 }, { 2.5 }, { 0.0 });
		local Float is b: if({ 1 > 2 }, { 10.0 }, { 3.0 }) + 4.0;
		Assert:isTrue(a == 4.0);
		Assert:isTrue(b == 7.0);
	}

	Function is testParenAndMultiLineImplicitReturn(){
		local Int is rgb: (255 << 24) | (180 << 16) | (90 << 8) | 45;
		Assert:isTrue(parenImplicitSingle(color: rgb) == 180);
		Assert:isTrue(parenImplicitMulti(color: rgb) == 90);
	}
}
