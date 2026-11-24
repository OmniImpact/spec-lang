#! Package theofractal:model
#! Shared base class for smooth escape-time complex-plane fractals (Mandelbrot, Julia, Burning Ship).

Class of Fractal is EscapeFractal{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalViewport]],
		['base', 'math', [as Math(), Vector]],
		['base', 'sys', [as Conditional(), as Loops(), Parallel, Process]],
		['base', 'sys', 'thread', ThreadScope]
	];

	## Override to evaluate smooth escape count at `(cr, ci)` up to [maxIter], or `-1.0` if interior.
	Function of Float is evaluatePoint(Float is cr, Float is ci, Int is maxIter){ -1.0 }

	## Computes smooth continuous escape value from escape iteration [iter] and squared magnitude [mag2].
	Function of Float is smoothEscapeValue(Int is iter, Float is mag2){
		local Float is mag: sqrt(value: mag2);
		local Float is logMag: log(value: mag);
		local Float is nu: if({ logMag > 0.0 }, { log2(value: logMag) }, { 0.0 });
		return (toFloat(value: iter) + 1.0) - nu;
	}

	## Evaluates one horizontal scanline at imaginary coordinate [ci] into [outBuf] starting at [rowOff].
	Function is evaluateRow(Vector is crVec, Float is ci, Int is w, Int is maxIter, Vector is outBuf, Int is rowOff){
		local Int is px: 0;
		while({ px < w }, {
			local Float is cr: crVec:get(index: px);
			local Float is mu: evaluatePoint(cr: cr, ci: ci, maxIter: maxIter);
			if({ mu < 0.0 }, {
				outBuf:set(index: rowOff + px, value: -1.0);
			}, {
				outBuf:set(index: rowOff + px, value: 0.5 - 0.5 * cos(value: mu * 0.25));
			});
			px: px + 1;
		});
	}

	replace Function of [Float] is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		local [Float] is grid: [];
		if({ w <= 0 || h <= 0 }, { return grid; });

		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is yMin: viewport:centerY - spanY * 0.5;
		local Float is zoomBoost: if({ viewport:zoom > 1.0 }, { log2(value: viewport:zoom) * 16.0 }, { 0.0 });
		local Int is maxIter: 80 + toInt(value: zoomBoost);
		if({ maxIter > 220 }, { maxIter: 220; });

		# Precompute row x-coordinates using SIMD-accelerated Vector operations
		local Vector is idxVec: Vector(length: w);
		local Int is ix: 0;
		while({ ix < w }, {
			idxVec:set(index: ix, value: toFloat(value: ix) + 0.5);
			ix: ix + 1;
		});
		local Vector is scaledX: Vector(length: w);
		idxVec:scale(factor: spanX / toFloat(value: w), out: scaledX);
		local Vector is xMinVec: Vector(length: w, initial: xMin);
		local Vector is crVec: Vector(length: w);
		scaledX:add(other: xMinVec, out: crVec);
		idxVec:destroy();
		scaledX:destroy();
		xMinVec:destroy();

		local Int is total: w * h;
		local Vector is outBuf: Vector(length: total, initial: -1.0);
		local Int is nThreads: Process():threadCount();
		if({ nThreads > h }, { nThreads: h; });
		if({ nThreads < 1 }, { nThreads: 1; });

		if({ nThreads == 1 || total < 1024 }, {
			local Int is py: 0;
			while({ py < h }, {
				local Float is ci: yMin + ((toFloat(value: py) + 0.5) / toFloat(value: h)) * spanY;
				evaluateRow(crVec: crVec, ci: ci, w: w, maxIter: maxIter, outBuf: outBuf, rowOff: py * w);
				py: py + 1;
			});
		}, {
			ThreadScope:open(
				body: local Function(ThreadScope is scope){
					Parallel():run(
						scope: scope,
						threads: nThreads,
						iterations: h,
						worker: local Function of Int(Int is tid, Int is cnt){
							local Int is py: tid;
							while({ py < h }, {
								local Float is ci: yMin + ((toFloat(value: py) + 0.5) / toFloat(value: h)) * spanY;
								evaluateRow(crVec: crVec, ci: ci, w: w, maxIter: maxIter, outBuf: outBuf, rowOff: py * w);
								py: py + nThreads;
							});
							return 0;
						}
					);
				},
				onError: local Function of Boolean(SpecError is _err){ false }
			);
		});

		local Int is k: 0;
		while({ k < total }, {
			grid:push(item: outBuf:get(index: k));
			k: k + 1;
		});
		crVec:destroy();
		outBuf:destroy();
		return grid;
	}
}
