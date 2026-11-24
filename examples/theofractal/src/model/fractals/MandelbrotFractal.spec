#! Package theofractal:model:fractals
#! Mandelbrot set fractal implementation.

Class of EscapeFractal is MandelbrotFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [EscapeFractal, FractalViewport]],
		['theofractal', 'util', FractalStrings],
		['base', 'math', [as Math(), Vector]],
		['base', 'sys', [as Cpu(), as Simd(), as Mem()]]
	];

	replace Function of String is name(){ FractalStrings:OPT_MANDELBROT }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: -0.5, centerY: 0.0, baseSpan: 2.6, zoom: 1.0)
	}

	replace Function of Float is evaluatePoint(Float is cr, Float is ci, Int is maxIter){
		local Float is q: ((cr - 0.25) * (cr - 0.25)) + (ci * ci);
		if({ (q * (q + (cr - 0.25))) <= (0.25 * ci * ci) }, { return -1.0; });
		if({ ((cr + 1.0) * (cr + 1.0)) + (ci * ci) <= 0.0625 }, { return -1.0; });
		local Float is zr: 0.0;
		local Float is zi: 0.0;
		local Float is zr2: 0.0;
		local Float is zi2: 0.0;
		local Int is iter: 0;
		while({ (iter < maxIter) && ((zr2 + zi2) <= 16.0) }, {
			zi: (2.0 * zr * zi) + ci;
			zr: (zr2 - zi2) + cr;
			zr2: zr * zr;
			zi2: zi * zi;
			iter: iter + 1;
		});
		if({ iter >= maxIter }, { return -1.0; });
		return smoothEscapeValue(iter: iter, mag2: zr2 + zi2);
	}

	local Function of Boolean is inMainBulb(Float is cr, Float is ci){
		local Float is dx: cr - 0.25;
		local Float is ci2: ci * ci;
		local Float is q: (dx * dx) + ci2;
		if({ (q * (q + dx)) <= (0.25 * ci2) }, { return true; });
		local Float is bx: cr + 1.0;
		return ((bx * bx) + ci2) <= 0.0625;
	}

	local Function of Float is shadeLane(Int is escIter, Int is maxIter, Float is mag2){
		if({ escIter < 0 || escIter >= maxIter }, { return -1.0; });
		return 0.5 - 0.5 * cos(value: smoothEscapeValue(iter: escIter, mag2: mag2) * 0.25);
	}

	## Evaluates 4 pixels per step using portable `<4 x double>` LLVM SIMD when available.
	replace Function is evaluateRow(Vector is crVec, Float is ci, Int is w, Int is maxIter, Vector is outBuf, Int is rowOff){
		local Int is px: 0;
		if({ hasSimd() && w >= 4 }, {
			local Vector is zr: Vector(length: 4);
			local Vector is zi: Vector(length: 4);
			local Vector is zr2: Vector(length: 4);
			local Vector is zi2: Vector(length: 4);
			local Vector is tmp: Vector(length: 4);
			local Vector is ciVec: Vector(length: 4, initial: ci);
			local Int is zrPtr: zr:dataAddr();
			local Int is ziPtr: zi:dataAddr();
			local Int is zr2Ptr: zr2:dataAddr();
			local Int is zi2Ptr: zi2:dataAddr();
			local Int is tmpPtr: tmp:dataAddr();
			local Int is ciPtr: ciVec:dataAddr();
			local Int is crBase: crVec:dataAddr();

			while({ px + 4 <= w }, {
				local Int is crPtr: crBase + px * 8;
				local Boolean is b0: inMainBulb(cr: loadF64(ptr: crPtr, byteOffset: 0), ci: ci);
				local Boolean is b1: inMainBulb(cr: loadF64(ptr: crPtr, byteOffset: 8), ci: ci);
				local Boolean is b2: inMainBulb(cr: loadF64(ptr: crPtr, byteOffset: 16), ci: ci);
				local Boolean is b3: inMainBulb(cr: loadF64(ptr: crPtr, byteOffset: 24), ci: ci);

				if({ b0 && b1 && b2 && b3 }, {
					outBuf:set(index: rowOff + px, value: -1.0);
					outBuf:set(index: rowOff + px + 1, value: -1.0);
					outBuf:set(index: rowOff + px + 2, value: -1.0);
					outBuf:set(index: rowOff + px + 3, value: -1.0);
				}, {
					fill4(dst: zrPtr, val: 0.0);
					fill4(dst: ziPtr, val: 0.0);
					fill4(dst: zr2Ptr, val: 0.0);
					fill4(dst: zi2Ptr, val: 0.0);

					local Int is i0: if({ b0 }, { maxIter }, { -1 });
					local Int is i1: if({ b1 }, { maxIter }, { -1 });
					local Int is i2: if({ b2 }, { maxIter }, { -1 });
					local Int is i3: if({ b3 }, { maxIter }, { -1 });
					local Float is m0: 0.0;
					local Float is m1: 0.0;
					local Float is m2: 0.0;
					local Float is m3: 0.0;
					local Int is active: 0;
					if({ i0 < 0 }, { active: active + 1; });
					if({ i1 < 0 }, { active: active + 1; });
					if({ i2 < 0 }, { active: active + 1; });
					if({ i3 < 0 }, { active: active + 1; });

					local Int is iter: 0;
					while({ iter < maxIter && active > 0 }, {
						mul4(dst: tmpPtr, a: zrPtr, b: ziPtr);
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
							if({ v0 > 16.0 }, { i0: iter; m0: v0; active: active - 1; });
						});
						if({ i1 < 0 }, {
							local Float is v1: loadF64(ptr: tmpPtr, byteOffset: 8);
							if({ v1 > 16.0 }, { i1: iter; m1: v1; active: active - 1; });
						});
						if({ i2 < 0 }, {
							local Float is v2: loadF64(ptr: tmpPtr, byteOffset: 16);
							if({ v2 > 16.0 }, { i2: iter; m2: v2; active: active - 1; });
						});
						if({ i3 < 0 }, {
							local Float is v3: loadF64(ptr: tmpPtr, byteOffset: 24);
							if({ v3 > 16.0 }, { i3: iter; m3: v3; active: active - 1; });
						});
					});

					outBuf:set(index: rowOff + px, value: shadeLane(escIter: i0, maxIter: maxIter, mag2: m0));
					outBuf:set(index: rowOff + px + 1, value: shadeLane(escIter: i1, maxIter: maxIter, mag2: m1));
					outBuf:set(index: rowOff + px + 2, value: shadeLane(escIter: i2, maxIter: maxIter, mag2: m2));
					outBuf:set(index: rowOff + px + 3, value: shadeLane(escIter: i3, maxIter: maxIter, mag2: m3));
				});
				px: px + 4;
			});

			zr:destroy();
			zi:destroy();
			zr2:destroy();
			zi2:destroy();
			tmp:destroy();
			ciVec:destroy();
		});

		while({ px < w }, {
			local Float is mu: evaluatePoint(cr: crVec:get(index: px), ci: ci, maxIter: maxIter);
			if({ mu < 0.0 }, {
				outBuf:set(index: rowOff + px, value: -1.0);
			}, {
				outBuf:set(index: rowOff + px, value: 0.5 - 0.5 * cos(value: mu * 0.25));
			});
			px: px + 1;
		});
	}
}
