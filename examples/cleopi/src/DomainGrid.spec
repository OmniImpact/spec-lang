#! Unit-circle ASCII visualization with live colored worker position markers.

## Renders rows of the `[-1, 1] x [-1, 1]` unit-circle domain and overlays active worker markers.
Class is DomainGrid{
	merge [[String]] is using: [
		['base', 'sys', as Ansi()],
		['base', 'math', as Math()],
		[PiStats],
		[PiTelemetry]
	];

	Int is width: 44;
	Int is height: 20;
	local PiStats is stats: PiStats();

	replace Function is init(Int is width: 44, Int is height: 20){
		:width: width;
		:height: height;
	}

	## Returns the thread index occupying `(col, row)`, or `-1` if none.
	Function of Int is markerAt(Int is col, Int is row, Int is threads, PiTelemetry is telemetry){
		local Int is i: 0;
		while({ i < threads }, {
			local Int is gx: (telemetry:workerX(threadIndex: i) * width) / 1000;
			local Int is gy: (telemetry:workerY(threadIndex: i) * height) / 1000;
			if({ gx == col && gy == row }, { return i; });
			i: i + 1;
		});
		return -1;
	}

	## Renders a single [row] of the unit circle with live worker markers from [telemetry].
	Function of String is renderRow(Int is row, Int is threads, PiTelemetry is telemetry){
		local String is buf: '';
		local Int is col: 0;
		while({ col < width }, {
			local Float is cx: ((toFloat(value: col) + 0.5) / toFloat(value: width)) * 2.0 - 1.0;
			local Float is cy: ((toFloat(value: row) + 0.5) / toFloat(value: height)) * 2.0 - 1.0;
			local Float is dist: sqrt(value: cx * cx + cy * cy);
			local Int is marker: markerAt(col: col, row: row, threads: threads, telemetry: telemetry);
			match(when: [
				{ marker >= 0 }: { buf: buf . color256(code: stats:threadColor(index: marker), text: '●'); },
				{ dist <= 1.0 }: { buf: buf . color256(code: 24, text: '·'); },
				else:            { buf: "{{buf}} "; }
			]);
			col: col + 1;
		});
		return buf;
	}
}
