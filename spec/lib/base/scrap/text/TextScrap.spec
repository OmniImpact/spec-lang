#! Package base:scrap
#! Composable reactive text widget with word-wrapping, alignment, and theme support.

Class of SewNode is TextScrap{
	replace [String] is namespace: ['base', 'scrap', 'text'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'signal', TextCollector],
		['base', 'sew', SewNode],
		['base', 'sew', HAlign],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'suit', SuitCanvas]
	];

	TextEmitter is text: TextEmitter(initial: '');
	HAlign is align: HAlign:LEFT;
	Boolean is wrap: false;
	Boolean is muted: false;
	Float is lineGapPt: 0.0;
	Array of String is cachedLines: Array();
	String is lastMeasuredText: '';
	Int is lastMeasuredMaxW: -1;

	replace Function is init(
		TextEmitter is text: TextEmitter(initial: ''),
		HAlign is align: HAlign:LEFT,
		Boolean is wrap: false,
		Boolean is muted: false,
		Float is lineGapPt: 0.0
	){
		:text: text;
		:align: align;
		:wrap: wrap;
		:muted: muted;
		:lineGapPt: lineGapPt;
		:cachedLines: Array();
		signalBag:track(
			slot: 'text',
			emitter: text,
			collector: text:collect(onEmit: local Function(String is _v){ invalidate(); })
		);
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 19.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Array of String is computeLines(String is s, Int is maxW){
		local Array of String is lines: Array();
		if({ s == '' }, { return lines; });
		local Int is fpx: :fontPx();
		local Int is fullW: DrawContext:measureWidth(text: s, pixelHeight: fpx);
		if({ !wrap || maxW <= 0 || fullW <= maxW }, {
			lines:add(item: s);
			return lines;
		});

		local Int is start: 0;
		local Int is len: s:length();
		while({ start < len }, {
			local Int is segEnd: len;
			if({ DrawContext:measureWidth(text: s:substring(start: start, end: len), pixelHeight: fpx) > maxW }, {
				local Int is lo: start + 1;
				local Int is hi: len - 1;
				local Int is maxFit: start + 1;
				while({ lo <= hi }, {
					local Int is mid: lo + (hi - lo) / 2;
					if({ DrawContext:measureWidth(text: s:substring(start: start, end: mid), pixelHeight: fpx) <= maxW }, {
						maxFit: mid;
						lo: mid + 1;
					}, {
						hi: mid - 1;
					});
				});
				segEnd: maxFit;
				if({ segEnd < len }, {
					local Int is si: segEnd - 1;
					local Boolean is foundSpace: false;
					while({ si > start && !foundSpace }, {
						if({ s:byteAt(index: si) == 32 }, {
							segEnd: si + 1;
							foundSpace: true;
						});
						si: si - 1;
					});
				});
				if({ segEnd <= start }, { segEnd: start + 1; });
			});
			local String is part: s:substring(start: start, end: segEnd);
			if({ part:length() > 0 && part:byteAt(index: part:length() - 1) == 32 }, {
				part: part:substring(start: 0, end: part:length() - 1);
			});
			lines:add(item: part);
			start: segEnd;
		});
		return lines;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is lineH: DrawContext:measureHeight(pixelHeight: fpx);
		local Int is gapPx: activeScale:px(pt: if({ lineGapPt > 0.0 }, { lineGapPt }, { activeTheme:lineGapPt * 1.5 }));
		local String is cur: text:current();
		lastMeasuredText: cur;
		lastMeasuredMaxW: c:maxW;
		cachedLines: :computeLines(s: cur, maxW: c:maxW);

		local Int is maxLineW: 0;
		times(count: cachedLines:length(), worker: local Function(Int is i){
			local Int is w: DrawContext:measureWidth(text: cachedLines:get(index: i), pixelHeight: fpx);
			if({ w > maxLineW }, { maxLineW: w; });
		});

		local Int is count: cachedLines:length();
		local Int is totalH: if({ count > 0 }, { count * lineH + (count - 1) * gapPx }, { lineH });
		desiredSize: Size(width: c:clampW(w: maxLineW), height: c:clampH(h: totalH));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local String is cur: text:current();
		if({ cur != lastMeasuredText || (wrap && b:width > 0 && b:width != lastMeasuredMaxW) }, {
			lastMeasuredText: cur;
			lastMeasuredMaxW: b:width;
			cachedLines: :computeLines(s: cur, maxW: b:width);
		});
		local Int is fpx: :fontPx();
		local Int is lineH: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is gapPx: activeScale:px(pt: if({ lineGapPt > 0.0 }, { lineGapPt }, { activeTheme:lineGapPt * 1.5 }));
		local Int is color: if({ muted }, { activeTheme:textMuted }, { activeTheme:textPrimary });

		times(count: cachedLines:length(), worker: local Function(Int is i){
			local String is lineStr: cachedLines:get(index: i);
			local Int is lw: ctx:measureTextWidth(text: lineStr, pixelHeight: fpx);
			local Int is lx: b:x;
			if({ align == HAlign:CENTER }, {
				lx: b:x + (b:width - lw) / 2;
			}, {
				if({ align == HAlign:RIGHT }, {
					lx: b:x + b:width - lw;
				});
			});
			ctx:drawText(x: lx, y: b:y + i * (lineH + gapPx), text: lineStr, color: color, pixelHeight: fpx);
		});
	}
}
