#! Package theofractal:model
#! Shared base class for smooth escape-time complex-plane fractals (Mandelbrot, Julia, Burning Ship).

Class of Fractal is EscapeFractal{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalViewport]],
		['base', 'math', [as Math(), Vector]],
		['base', 'sys', [as Conditional(), as Loops(), Parallel, Process]]
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

	## Evaluates one horizontal scanline at imaginary coordinate [ci] into raw escape buffer [outBuf] and optional DE glow [deBuf].
	Function is evaluateRow(Vector is crVec, Float is ci, Int is w, Int is maxIter, Float is pixelSpan, Vector is outBuf, Vector is deBuf, Int is rowOff){
		local Int is px: 0;
		while({ px < w }, {
			local Float is cr: crVec:get(index: px);
			local Float is mu: evaluatePoint(cr: cr, ci: ci, maxIter: maxIter);
			outBuf:set(index: rowOff + px, value: if({ mu < 0.0 }, { -1.0 }, { mu }));
			px: px + 1;
		});
	}

	## Computes smooth [0.0, 1.0] Distance-Estimation edge coverage from escape [mag2], |dz|^2 [dz2], and [pixelSpan].
	Function of Float is deEdgeGlow(Float is mag2, Float is dz2, Float is pixelSpan){
		if({ dz2 <= 0.0 || mag2 <= 1.0 || pixelSpan <= 0.0 }, { return 0.0; });
		local Float is mag: sqrt(value: mag2);
		local Float is dzMag: sqrt(value: dz2);
		local Float is dist: (mag * log(value: mag)) / dzMag;
		local Float is norm: dist / pixelSpan;
		if({ norm > 8.0 }, { return 0.0; });
		return exp(value: -norm);
	}

	local Function of [Float] is normalizeEscapeGrid(Vector is outBuf, Vector is deBuf, Int is total){
		local [Float] is grid: [];
		if({ total <= 0 }, { return grid; });

		local Float is minLog: 1000000.0;
		local Float is maxLog: -1.0;
		local Int is escaped: 0;
		local Int is i: 0;
		while({ i < total }, {
			local Float is mu: outBuf:get(index: i);
			if({ mu >= 0.0 }, {
				local Float is lm: log(value: 1.0 + mu);
				if({ lm < minLog }, { minLog: lm; });
				if({ lm > maxLog }, { maxLog: lm; });
				escaped: escaped + 1;
			});
			i: i + 1;
		});

		if({ escaped <= 0 }, {
			local Int is k0: 0;
			while({ k0 < total }, {
				grid:push(item: -1.0);
				k0: k0 + 1;
			});
			return grid;
		});

		local Float is logRange: maxLog - minLog;
		if({ logRange < 0.000001 }, { logRange: 1.0; });

		local Int is bins: 256;
		local [Int] is hist: [];
		local Int is bi: 0;
		while({ bi < bins }, {
			hist:push(item: 0);
			bi: bi + 1;
		});

		i: 0;
		while({ i < total }, {
			local Float is mu2: outBuf:get(index: i);
			if({ mu2 >= 0.0 }, {
				local Float is u: (log(value: 1.0 + mu2) - minLog) / logRange;
				local Int is b: toInt(value: u * 255.0);
				if({ b < 0 }, { b: 0; });
				if({ b > 255 }, { b: 255; });
				hist:set(index: b, item: hist:get(index: b) + 1);
			});
			i: i + 1;
		});

		local [Float] is cdf: [];
		local Int is running: 0;
		local Float is denom: toFloat(value: escaped);
		bi: 0;
		while({ bi < bins }, {
			cdf:push(item: toFloat(value: running) / denom);
			running: running + hist:get(index: bi);
			bi: bi + 1;
		});

		i: 0;
		while({ i < total }, {
			local Float is mu3: outBuf:get(index: i);
			if({ mu3 < 0.0 }, {
				grid:push(item: -1.0);
			}, {
				local Float is logT: (log(value: 1.0 + mu3) - minLog) / logRange;
				if({ logT < 0.0 }, { logT: 0.0; });
				if({ logT > 1.0 }, { logT: 1.0; });
				local Int is b2: toInt(value: logT * 255.0);
				if({ b2 < 0 }, { b2: 0; });
				if({ b2 > 255 }, { b2: 255; });
				local Float is histT: cdf:get(index: b2);
				local Float is baseT: 0.45 * logT + 0.55 * histT;
				local Float is dg: deBuf:get(index: i);
				local Float is val: baseT + (1.0 - baseT) * dg * 0.45;
				if({ val > 1.0 }, { val: 1.0; });
				grid:push(item: val);
			});
			i: i + 1;
		});
		return grid;
	}

	replace Function of [Float] is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		if({ w <= 0 || h <= 0 }, { return []; });

		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is pixelSpan: spanX / toFloat(value: w);
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is yMin: viewport:centerY - spanY * 0.5;
		local Float is zoomBoost: if({ viewport:zoom > 1.0 }, { log2(value: viewport:zoom) * 40.0 }, { 0.0 });
		local Int is maxIter: 100 + toInt(value: zoomBoost);
		if({ maxIter > 2400 }, { maxIter: 2400; });

		# Precompute row x-coordinates using SIMD-accelerated Vector operations
		local Vector is idxVec: Vector(length: w);
		local Int is ix: 0;
		while({ ix < w }, {
			idxVec:set(index: ix, value: toFloat(value: ix) + 0.5);
			ix: ix + 1;
		});
		local Vector is scaledX: Vector(length: w);
		idxVec:scale(factor: pixelSpan, out: scaledX);
		local Vector is xMinVec: Vector(length: w, initial: xMin);
		local Vector is crVec: Vector(length: w);
		scaledX:add(other: xMinVec, out: crVec);
		idxVec:destroy();
		scaledX:destroy();
		xMinVec:destroy();

		local Int is total: w * h;
		local Vector is outBuf: Vector(length: total, initial: -1.0);
		local Vector is deBuf: Vector(length: total, initial: 0.0);
		local Int is nThreads: Process():threadCount();
		if({ nThreads > h }, { nThreads: h; });
		if({ nThreads < 1 }, { nThreads: 1; });

		if({ nThreads == 1 || total < 1024 }, {
			local Int is py: 0;
			while({ py < h }, {
				local Float is ci: yMin + ((toFloat(value: py) + 0.5) / toFloat(value: h)) * spanY;
				evaluateRow(crVec: crVec, ci: ci, w: w, maxIter: maxIter, pixelSpan: pixelSpan, outBuf: outBuf, deBuf: deBuf, rowOff: py * w);
				py: py + 1;
			});
		}, {
			Parallel():runScoped(
				threads: nThreads,
				iterations: h,
				worker: local Function of Int(Int is tid, Int is cnt){
					local Int is py: tid;
					while({ py < h }, {
						local Float is ci: yMin + ((toFloat(value: py) + 0.5) / toFloat(value: h)) * spanY;
						evaluateRow(crVec: crVec, ci: ci, w: w, maxIter: maxIter, pixelSpan: pixelSpan, outBuf: outBuf, deBuf: deBuf, rowOff: py * w);
						py: py + nThreads;
					});
					return 0;
				}
			);
		});

		local [Float] is grid: normalizeEscapeGrid(outBuf: outBuf, deBuf: deBuf, total: total);
		crVec:destroy();
		outBuf:destroy();
		deBuf:destroy();
		return grid;
	}
}
