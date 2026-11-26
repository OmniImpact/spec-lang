#! Package suitdemo
#! Suit demo: multi-threaded SIMD grayscale Julia set with WASD/QE navigation and stb_truetype shortcuts HUD.

Class is SuitDemo{
	replace [String] is namespace: ['suitdemo'];

	merge [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'suit', [SuitCanvas, SuitFont, SuitWindow]],
		['base', 'math', Vector],
		['base', 'struct', Map],
		['base', 'sys', [as Cpu(), as Mem(), as Output(), Parallel, Process, as Simd(), as Time()]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Float is centerX: 0.0;
	Float is centerY: 0.0;
	Float is baseSpan: 2.6;
	Float is zoom: 1.0;
	Int is maxIter: 96;

	local Function of Int is colorForIter(Int is iter){
		if({ iter < 0 || iter >= maxIter }, {
			return -16777216;
		});
		local Int is v: (iter * 255) / maxIter;
		return -16777216 | (v << 16) | (v << 8) | v;
	}

	local Function is evaluateRow(Vector is crVec, Float is ci, Int is w, Int is bufPtr, Int is rowOff){
		local Float is jc: -0.7;
		local Float is ji: 0.27015;
		local Int is px: 0;
		if({ hasSimd() && w >= 4 }, {
			local Vector is zr: Vector(length: 4);
			local Vector is zi: Vector(length: 4);
			local Vector is zr2: Vector(length: 4);
			local Vector is zi2: Vector(length: 4);
			local Vector is tmp: Vector(length: 4);
			local Vector is jcVec: Vector(length: 4, initial: -0.7);
			local Vector is jiVec: Vector(length: 4, initial: 0.27015);
			local Int is zrPtr: zr:dataAddr();
			local Int is ziPtr: zi:dataAddr();
			local Int is zr2Ptr: zr2:dataAddr();
			local Int is zi2Ptr: zi2:dataAddr();
			local Int is tmpPtr: tmp:dataAddr();
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

				local Int is i0: -1;
				local Int is i1: -1;
				local Int is i2: -1;
				local Int is i3: -1;
				local Int is active: 4;
				local Int is iter: 0;
				while({ iter < maxIter && active > 0 }, {
					mul4(dst: tmpPtr, a: zrPtr, b: ziPtr);
					scale4(dst: tmpPtr, a: tmpPtr, scalar: 2.0);
					add4(dst: ziPtr, a: tmpPtr, b: jiPtr);

					sub4(dst: tmpPtr, a: zr2Ptr, b: zi2Ptr);
					add4(dst: zrPtr, a: tmpPtr, b: jcPtr);

					mul4(dst: zr2Ptr, a: zrPtr, b: zrPtr);
					mul4(dst: zi2Ptr, a: ziPtr, b: ziPtr);
					add4(dst: tmpPtr, a: zr2Ptr, b: zi2Ptr);

					iter: iter + 1;
					if({ i0 < 0 && loadF64(ptr: tmpPtr, byteOffset: 0) > 4.0 }, {
						i0: iter;
						active: active - 1;
					});
					if({ i1 < 0 && loadF64(ptr: tmpPtr, byteOffset: 8) > 4.0 }, {
						i1: iter;
						active: active - 1;
					});
					if({ i2 < 0 && loadF64(ptr: tmpPtr, byteOffset: 16) > 4.0 }, {
						i2: iter;
						active: active - 1;
					});
					if({ i3 < 0 && loadF64(ptr: tmpPtr, byteOffset: 24) > 4.0 }, {
						i3: iter;
						active: active - 1;
					});
				});

				local Int is outOff: (rowOff + px) * 4;
				storeI32(ptr: bufPtr, byteOffset: outOff, val: colorForIter(iter: i0));
				storeI32(ptr: bufPtr, byteOffset: outOff + 4, val: colorForIter(iter: i1));
				storeI32(ptr: bufPtr, byteOffset: outOff + 8, val: colorForIter(iter: i2));
				storeI32(ptr: bufPtr, byteOffset: outOff + 12, val: colorForIter(iter: i3));
				px: px + 4;
			});

			zr:destroy();
			zi:destroy();
			zr2:destroy();
			zi2:destroy();
			tmp:destroy();
			jcVec:destroy();
			jiVec:destroy();
		});

		while({ px < w }, {
			local Float is zr: crVec:get(index: px);
			local Float is zi: ci;
			local Float is zr2: zr * zr;
			local Float is zi2: zi * zi;
			local Int is iter: 0;
			while({ iter < maxIter && (zr2 + zi2) <= 4.0 }, {
				zi: (2.0 * zr * zi) + ji;
				zr: (zr2 - zi2) + jc;
				zr2: zr * zr;
				zi2: zi * zi;
				iter: iter + 1;
			});
			local Int is c: if({ iter < maxIter }, { colorForIter(iter: iter) }, { -16777216 });
			storeI32(ptr: bufPtr, byteOffset: (rowOff + px) * 4, val: c);
			px: px + 1;
		});
	}

	local Function of Int is renderJulia(SuitCanvas is canvas, SuitFont is font){
		local Int is t0: monotonicMs();
		local Int is w: canvas:width;
		local Int is h: canvas:height;
		if({ w <= 0 || h <= 0 }, { return 0; });

		local Float is spanX: baseSpan / zoom;
		local Float is aspect: (h as Float) / (w as Float);
		local Float is spanY: spanX * aspect;
		local Float is xMin: centerX - (spanX * 0.5);
		local Float is yMin: centerY - (spanY * 0.5);
		local Float is dx: spanX / (w as Float);
		local Float is dy: spanY / (h as Float);

		local Vector is crVec: Vector(length: w);
		local Int is crPtr: crVec:dataAddr();
		local Int is px: 0;
		while({ px < w }, {
			storeF64(ptr: crPtr, byteOffset: px * 8, val: xMin + (((px as Float) + 0.5) * dx));
			px: px + 1;
		});

		local Int is bufPtr: canvas:pixelsAddr();
		local Int is nThreads: Process():threadCount();
		if({ nThreads > h }, { nThreads: h; });
		if({ nThreads < 1 }, { nThreads: 1; });

		if({ nThreads == 1 || (w * h) < 1024 }, {
			local Int is py: 0;
			while({ py < h }, {
				local Float is ci: yMin + (((py as Float) + 0.5) * dy);
				evaluateRow(crVec: crVec, ci: ci, w: w, bufPtr: bufPtr, rowOff: py * w);
				py: py + 1;
			});
		}, {
			Parallel():runScoped(
				threads: nThreads,
				iterations: h,
				worker: local Function of Int(Int is tid, Int is _cnt){
					local Int is py: tid;
					while({ py < h }, {
						local Float is ci: yMin + (((py as Float) + 0.5) * dy);
						evaluateRow(crVec: crVec, ci: ci, w: w, bufPtr: bufPtr, rowOff: py * w);
						py: py + nThreads;
					});
					return 0;
				}
			);
		});

		crVec:destroy();
		local Int is renderMs: monotonicMs() - t0;

		if({ font:isLoaded() }, {
			canvas:fillRect(x: 12, y: 12, w: 540, h: 30, color: -15722972);
			font:drawText(
				canvas: canvas,
				x: 20,
				y: 17,
				text: 'WASD: Pan   Q/E: Zoom   Esc: Quit   (' . (renderMs as String) . ' ms, ' . (nThreads as String) . 'T)',
				size: 18,
				color: -1
			);
		});
		return renderMs;
	}

	local Function of Boolean is handleKey(Int is key, SuitWindow is win){
		local Float is panStep: (baseSpan / zoom) * 0.1;
		return match(when: [
			{ key == 119 }: { centerY: centerY - panStep; true },
			{ key == 115 }: { centerY: centerY + panStep; true },
			{ key == 97 }:  { centerX: centerX - panStep; true },
			{ key == 100 }: { centerX: centerX + panStep; true },
			{ key == 113 }: { zoom: zoom / 1.25; true },
			{ key == 101 }: { zoom: zoom * 1.25; true },
			{ key == 27 }:  { win:close(); false },
			else: { false }
		]);
	}

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():loadFromBundle(bundlePath: 'cli.json', fallbackPath: 'examples/suitdemo/cli.json');
		if({ !cli:parse(rawArgs: Process():rawArgs()) }, {
			if({ cli:helpRequested || cli:versionRequested }, { return; });
			Process():exit(status: 1);
		});
		local Int is durationMs: cli:getInt(name: 'duration-ms', default: 0);
		local SuitWindow is win: SuitWindow(title: 'Suit Demo', width: 800, height: 600, decorated: true);
		if({ !win:open() }, {
			line(text: 'SuitDemo failed to open window: ' . win:lastError());
			return;
		});

		local Int is curW: win:width();
		local Int is curH: win:height();
		if({ curW <= 0 }, { curW: 800; });
		if({ curH <= 0 }, { curH: 600; });

		local SuitCanvas is canvas: SuitCanvas(width: curW, height: curH);
		local SuitFont is font: SuitFont();
		if({ !font:loadSystemFont() }, {
			line(text: 'SuitDemo font warning: ' . font:lastError());
		});

		local Boolean is dirty: true;
		local Int is startMs: monotonicMs();
		while({ win:poll() }, {
			local Int is ww: win:width();
			local Int is wh: win:height();
			if({ ww > 0 && wh > 0 && (ww != canvas:width || wh != canvas:height) }, {
				canvas:resize(width: ww, height: wh);
				dirty: true;
			});

			local Int is k: win:nextKey();
			while({ k != 0 }, {
				if({ handleKey(key: k, win: win) }, {
					dirty: true;
				});
				k: win:nextKey();
			});

			if({ dirty && win:isOpen() }, {
				local Int is ms: renderJulia(canvas: canvas, font: font);
				win:present(canvas: canvas);
				dirty: false;
				if({ durationMs > 0 }, {
					line(text: 'Rendered frame in ' . (ms as String) . ' ms');
				});
			});

			if({ durationMs > 0 && (monotonicMs() - startMs) >= durationMs }, {
				win:close();
			});
		});

		font:close();
		canvas:dispose();
	}
}
