#! Package theofractal:model:fractals
#! Burning Ship fractal implementation.

Class of EscapeFractal is BurningShipFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [EscapeFractal, FractalViewport]],
		['theofractal', 'util', FractalStrings],
		['base', 'math', [as Math(), Vector]],
		['base', 'sys', [as Cpu(), as Simd(), as Mem()]]
	];

	replace Function of String is name(){ FractalStrings:OPT_BURNING_SHIP }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: -0.45, centerY: -0.55, baseSpan: 2.8, zoom: 1.0)
	}

	replace Function of Float is evaluatePoint(Float is cr, Float is ci, Int is maxIter){
		local Float is zr: 0.0;
		local Float is zi: 0.0;
		local Float is zr2: 0.0;
		local Float is zi2: 0.0;
		local Int is iter: 0;
		while({ (iter < maxIter) && ((zr2 + zi2) <= 256.0) }, {
			local Float is azr: if({ zr < 0.0 }, { -zr }, { zr });
			local Float is azi: if({ zi < 0.0 }, { -zi }, { zi });
			zi: (2.0 * azr * azi) + ci;
			zr: (zr2 - zi2) + cr;
			zr2: zr * zr;
			zi2: zi * zi;
			iter: iter + 1;
		});
		if({ iter >= maxIter }, { return -1.0; });
		return smoothEscapeValue(iter: iter, mag2: zr2 + zi2);
	}

	local Function of Float is rawLane(Int is escIter, Int is maxIter, Float is mag2){
		if({ escIter < 0 || escIter >= maxIter }, { return -1.0; });
		return smoothEscapeValue(iter: escIter, mag2: mag2);
	}

	local Function is abs4(Int is dstPtr, Int is srcPtr){
		storeF64(ptr: dstPtr, byteOffset: 0, val: abs(value: loadF64(ptr: srcPtr, byteOffset: 0)));
		storeF64(ptr: dstPtr, byteOffset: 8, val: abs(value: loadF64(ptr: srcPtr, byteOffset: 8)));
		storeF64(ptr: dstPtr, byteOffset: 16, val: abs(value: loadF64(ptr: srcPtr, byteOffset: 16)));
		storeF64(ptr: dstPtr, byteOffset: 24, val: abs(value: loadF64(ptr: srcPtr, byteOffset: 24)));
	}

	## Evaluates 4 pixels per step using portable `<4 x double>` LLVM SIMD when available.
	replace Function is evaluateRow(Vector is crVec, Float is ci, Int is w, Int is maxIter, Float is pixelSpan, Vector is outBuf, Vector is deBuf, Int is rowOff){
		local Int is px: 0;
		if({ hasSimd() && w >= 4 }, {
			local Vector is zr: Vector(length: 4);
			local Vector is zi: Vector(length: 4);
			local Vector is zr2: Vector(length: 4);
			local Vector is zi2: Vector(length: 4);
			local Vector is azr: Vector(length: 4);
			local Vector is azi: Vector(length: 4);
			local Vector is tmp: Vector(length: 4);
			local Vector is ciVec: Vector(length: 4, initial: ci);
			local Int is zrPtr: zr:dataAddr();
			local Int is ziPtr: zi:dataAddr();
			local Int is zr2Ptr: zr2:dataAddr();
			local Int is zi2Ptr: zi2:dataAddr();
			local Int is azrPtr: azr:dataAddr();
			local Int is aziPtr: azi:dataAddr();
			local Int is tmpPtr: tmp:dataAddr();
			local Int is ciPtr: ciVec:dataAddr();
			local Int is crBase: crVec:dataAddr();

			while({ px + 4 <= w }, {
				local Int is crPtr: crBase + px * 8;
				fill4(dst: zrPtr, val: 0.0);
				fill4(dst: ziPtr, val: 0.0);
				fill4(dst: zr2Ptr, val: 0.0);
				fill4(dst: zi2Ptr, val: 0.0);

				local Int is i0: -1;
				local Int is i1: -1;
				local Int is i2: -1;
				local Int is i3: -1;
				local Float is m0: 0.0;
				local Float is m1: 0.0;
				local Float is m2: 0.0;
				local Float is m3: 0.0;
				local Int is active: 4;
				local Int is iter: 0;
				while({ iter < maxIter && active > 0 }, {
					abs4(dstPtr: azrPtr, srcPtr: zrPtr);
					abs4(dstPtr: aziPtr, srcPtr: ziPtr);
					mul4(dst: tmpPtr, a: azrPtr, b: aziPtr);
					scale4(dst: tmpPtr, a: tmpPtr, scalar: 2.0);
					add4(dst: ziPtr, a: tmpPtr, b: ciPtr);

					sub4(dst: tmpPtr, a: zr2Ptr, b: zi2Ptr);
					add4(dst: zrPtr, a: tmpPtr, b: crPtr);

					mul4(dst: zr2Ptr, a: zrPtr, b: zrPtr);
					mul4(dst: zi2Ptr, a: ziPtr, b: ziPtr);
					add4(dst: tmpPtr, a: zr2Ptr, b: zi2Ptr);

					iter: iter + 1;
					if({ i0 < 0 }, {
						local Float is v0: loadF64(ptr: tmpPtr, byteOffset: 0);
						if({ v0 > 256.0 }, { i0: iter; m0: v0; active: active - 1; });
					});
					if({ i1 < 0 }, {
						local Float is v1: loadF64(ptr: tmpPtr, byteOffset: 8);
						if({ v1 > 256.0 }, { i1: iter; m1: v1; active: active - 1; });
					});
					if({ i2 < 0 }, {
						local Float is v2: loadF64(ptr: tmpPtr, byteOffset: 16);
						if({ v2 > 256.0 }, { i2: iter; m2: v2; active: active - 1; });
					});
					if({ i3 < 0 }, {
						local Float is v3: loadF64(ptr: tmpPtr, byteOffset: 24);
						if({ v3 > 256.0 }, { i3: iter; m3: v3; active: active - 1; });
					});
				});

				outBuf:set(index: rowOff + px, value: rawLane(escIter: i0, maxIter: maxIter, mag2: m0));
				outBuf:set(index: rowOff + px + 1, value: rawLane(escIter: i1, maxIter: maxIter, mag2: m1));
				outBuf:set(index: rowOff + px + 2, value: rawLane(escIter: i2, maxIter: maxIter, mag2: m2));
				outBuf:set(index: rowOff + px + 3, value: rawLane(escIter: i3, maxIter: maxIter, mag2: m3));
				px: px + 4;
			});

			zr:destroy();
			zi:destroy();
			zr2:destroy();
			zi2:destroy();
			azr:destroy();
			azi:destroy();
			tmp:destroy();
			ciVec:destroy();
		});

		while({ px < w }, {
			local Float is mu: evaluatePoint(cr: crVec:get(index: px), ci: ci, maxIter: maxIter);
			if({ mu < 0.0 }, {
				outBuf:set(index: rowOff + px, value: -1.0);
			}, {
				outBuf:set(index: rowOff + px, value: mu);
			});
			px: px + 1;
		});
	}
}
