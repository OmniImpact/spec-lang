#! Package theofractal:model:fractals
#! Julia set fractal implementation (`c = -0.7 + 0.27015i`).

Class of EscapeFractal is JuliaFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [EscapeFractal, FractalViewport]],
		['theofractal', 'util', FractalStrings],
		['base', 'math', [as Math(), Vector]],
		['base', 'sys', [as Cpu(), as Simd(), as Mem()]]
	];

	replace Function of String is name(){ FractalStrings:OPT_JULIA }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: 0.0, centerY: 0.0, baseSpan: 2.6, zoom: 1.0)
	}

	replace Function of Float is evaluatePoint(Float is cr, Float is ci, Int is maxIter){
		local Float is jc: -0.7;
		local Float is ji: 0.27015;
		local Float is zr: cr;
		local Float is zi: ci;
		local Float is zr2: zr * zr;
		local Float is zi2: zi * zi;
		local Int is iter: 0;
		while({ (iter < maxIter) && ((zr2 + zi2) <= 256.0) }, {
			zi: (2.0 * zr * zi) + ji;
			zr: (zr2 - zi2) + jc;
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

	## Evaluates 4 pixels per step using portable `<4 x double>` LLVM SIMD when available, with DE derivative tracking.
	replace Function is evaluateRow(Vector is crVec, Float is ci, Int is w, Int is maxIter, Float is pixelSpan, Vector is outBuf, Vector is deBuf, Int is rowOff){
		local Int is px: 0;
		if({ hasSimd() && w >= 4 }, {
			local Vector is zr: Vector(length: 4);
			local Vector is zi: Vector(length: 4);
			local Vector is zr2: Vector(length: 4);
			local Vector is zi2: Vector(length: 4);
			local Vector is dzr: Vector(length: 4);
			local Vector is dzi: Vector(length: 4);
			local Vector is tmp: Vector(length: 4);
			local Vector is tmp2: Vector(length: 4);
			local Vector is tmp3: Vector(length: 4);
			local Vector is jcVec: Vector(length: 4, initial: -0.7);
			local Vector is jiVec: Vector(length: 4, initial: 0.27015);
			local Int is zrPtr: zr:dataAddr();
			local Int is ziPtr: zi:dataAddr();
			local Int is zr2Ptr: zr2:dataAddr();
			local Int is zi2Ptr: zi2:dataAddr();
			local Int is dzrPtr: dzr:dataAddr();
			local Int is dziPtr: dzi:dataAddr();
			local Int is tmpPtr: tmp:dataAddr();
			local Int is tmp2Ptr: tmp2:dataAddr();
			local Int is tmp3Ptr: tmp3:dataAddr();
			local Int is jcPtr: jcVec:dataAddr();
			local Int is jiPtr: jiVec:dataAddr();
			local Int is crBase: crVec:dataAddr();

			while({ px + 4 <= w }, {
				local Int is crPtr: crBase + px * 8;
				storeF64(ptr: zrPtr, byteOffset: 0, val: loadF64(ptr: crPtr, byteOffset: 0));
				storeF64(ptr: zrPtr, byteOffset: 8, val: loadF64(ptr: crPtr, byteOffset: 8));
				storeF64(ptr: zrPtr, byteOffset: 16, val: loadF64(ptr: crPtr, byteOffset: 16));
				storeF64(ptr: zrPtr, byteOffset: 24, val: loadF64(ptr: crPtr, byteOffset: 24));
				fill4(dst: ziPtr, val: ci);
				mul4(dst: zr2Ptr, a: zrPtr, b: zrPtr);
				mul4(dst: zi2Ptr, a: ziPtr, b: ziPtr);
				fill4(dst: dzrPtr, val: 1.0);
				fill4(dst: dziPtr, val: 0.0);

				local Int is i0: -1;
				local Int is i1: -1;
				local Int is i2: -1;
				local Int is i3: -1;
				local Float is m0: 0.0;
				local Float is m1: 0.0;
				local Float is m2: 0.0;
				local Float is m3: 0.0;
				local Float is d0: 0.0;
				local Float is d1: 0.0;
				local Float is d2: 0.0;
				local Float is d3: 0.0;
				local Int is active: 4;
				local Int is iter: 0;
				while({ iter < maxIter && active > 0 }, {
					# Update derivative dz = 2*z*dz in 4-wide SIMD
					mul4(dst: tmpPtr, a: zrPtr, b: dzrPtr);
					mul4(dst: tmp2Ptr, a: ziPtr, b: dziPtr);
					sub4(dst: tmp3Ptr, a: tmpPtr, b: tmp2Ptr);
					mul4(dst: tmpPtr, a: zrPtr, b: dziPtr);
					mul4(dst: tmp2Ptr, a: ziPtr, b: dzrPtr);
					add4(dst: tmpPtr, a: tmpPtr, b: tmp2Ptr);
					scale4(dst: dzrPtr, a: tmp3Ptr, scalar: 2.0);
					scale4(dst: dziPtr, a: tmpPtr, scalar: 2.0);

					mul4(dst: tmpPtr, a: zrPtr, b: ziPtr);
					axpy4(dst: ziPtr, a: tmpPtr, scalar: 2.0, c: jiPtr);

					sub4(dst: tmpPtr, a: zr2Ptr, b: zi2Ptr);
					add4(dst: zrPtr, a: tmpPtr, b: jcPtr);

					mul4(dst: zr2Ptr, a: zrPtr, b: zrPtr);
					mul4(dst: zi2Ptr, a: ziPtr, b: ziPtr);
					add4(dst: tmpPtr, a: zr2Ptr, b: zi2Ptr);

					iter: iter + 1;
					if({ i0 < 0 }, {
						local Float is v0: loadF64(ptr: tmpPtr, byteOffset: 0);
						if({ v0 > 256.0 }, {
							local Float is r0: loadF64(ptr: dzrPtr, byteOffset: 0);
							local Float is j0: loadF64(ptr: dziPtr, byteOffset: 0);
							i0: iter; m0: v0; d0: r0 * r0 + j0 * j0; active: active - 1;
						});
					});
					if({ i1 < 0 }, {
						local Float is v1: loadF64(ptr: tmpPtr, byteOffset: 8);
						if({ v1 > 256.0 }, {
							local Float is r1: loadF64(ptr: dzrPtr, byteOffset: 8);
							local Float is j1: loadF64(ptr: dziPtr, byteOffset: 8);
							i1: iter; m1: v1; d1: r1 * r1 + j1 * j1; active: active - 1;
						});
					});
					if({ i2 < 0 }, {
						local Float is v2: loadF64(ptr: tmpPtr, byteOffset: 16);
						if({ v2 > 256.0 }, {
							local Float is r2: loadF64(ptr: dzrPtr, byteOffset: 16);
							local Float is j2: loadF64(ptr: dziPtr, byteOffset: 16);
							i2: iter; m2: v2; d2: r2 * r2 + j2 * j2; active: active - 1;
						});
					});
					if({ i3 < 0 }, {
						local Float is v3: loadF64(ptr: tmpPtr, byteOffset: 24);
						if({ v3 > 256.0 }, {
							local Float is r3: loadF64(ptr: dzrPtr, byteOffset: 24);
							local Float is j3: loadF64(ptr: dziPtr, byteOffset: 24);
							i3: iter; m3: v3; d3: r3 * r3 + j3 * j3; active: active - 1;
						});
					});
				});

				outBuf:set(index: rowOff + px, value: rawLane(escIter: i0, maxIter: maxIter, mag2: m0));
				outBuf:set(index: rowOff + px + 1, value: rawLane(escIter: i1, maxIter: maxIter, mag2: m1));
				outBuf:set(index: rowOff + px + 2, value: rawLane(escIter: i2, maxIter: maxIter, mag2: m2));
				outBuf:set(index: rowOff + px + 3, value: rawLane(escIter: i3, maxIter: maxIter, mag2: m3));
				if({ i0 >= 0 && i0 < maxIter }, { deBuf:set(index: rowOff + px, value: deEdgeGlow(mag2: m0, dz2: d0, pixelSpan: pixelSpan)); });
				if({ i1 >= 0 && i1 < maxIter }, { deBuf:set(index: rowOff + px + 1, value: deEdgeGlow(mag2: m1, dz2: d1, pixelSpan: pixelSpan)); });
				if({ i2 >= 0 && i2 < maxIter }, { deBuf:set(index: rowOff + px + 2, value: deEdgeGlow(mag2: m2, dz2: d2, pixelSpan: pixelSpan)); });
				if({ i3 >= 0 && i3 < maxIter }, { deBuf:set(index: rowOff + px + 3, value: deEdgeGlow(mag2: m3, dz2: d3, pixelSpan: pixelSpan)); });
				px: px + 4;
			});

			zr:destroy();
			zi:destroy();
			zr2:destroy();
			zi2:destroy();
			dzr:destroy();
			dzi:destroy();
			tmp:destroy();
			jcVec:destroy();
			jiVec:destroy();
		});

		while({ px < w }, {
			local Float is mu: evaluatePoint(cr: crVec:get(index: px), ci: ci, maxIter: maxIter);
			outBuf:set(index: rowOff + px, value: if({ mu < 0.0 }, { -1.0 }, { mu }));
			px: px + 1;
		});
	}
}
