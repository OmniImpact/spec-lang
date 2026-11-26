#! Package base:scrap
#! Composable reactive text widget with word-wrapping, alignment, and theme support.

Class of SewNode is TextScrap{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'signal', TextCollector],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'suit', SuitCanvas]
	];

	TextEmitter is text: TextEmitter(initial: '');
	String is align: 'left';
	Boolean is wrap: false;
	Boolean is muted: false;
	Float is lineGapPt: 6.0;
	Array of String is cachedLines: Array();

	replace Function is init(
		TextEmitter is text: TextEmitter(initial: ''),
		String is align: 'left',
		Boolean is wrap: false,
		Boolean is muted: false,
		Float is lineGapPt: 6.0
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
			collector: TextCollector(onEmit: local Function(String is _v){ invalidate(); })
		);
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: 14.0);
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Array of String is computeLines(String is s, Int is maxW){
		local Array of String is lines: Array();
		if({ s == '' }, { return lines; });
		local Int is fpx: :fontPx();
		local DrawContext is dummy: DrawContext(canvas: SuitCanvas(width: 1, height: 1));
		local Int is fullW: dummy:measureTextWidth(text: s, pixelHeight: fpx);
		if({ !wrap || maxW <= 0 || fullW <= maxW }, {
			dummy:canvas:dispose();
			lines:add(item: s);
			return lines;
		});

		local Int is avgCharW: if({ s:length() > 0 && fullW > 0 }, { fullW / s:length() }, { 8 });
		local Int is maxChars: if({ avgCharW > 0 }, { maxW / avgCharW }, { 40 });
		dummy:canvas:dispose();
		if({ maxChars <= 4 || s:length() <= maxChars }, {
			lines:add(item: s);
			return lines;
		});

		local Int is start: 0;
		local Int is len: s:length();
		while({ start < len }, {
			local Int is rem: len - start;
			if({ rem <= maxChars }, {
				lines:add(item: s:substring(start: start, end: len));
				start: len;
			}, {
				local Int is splitAt: start + maxChars;
				local Int is k: splitAt;
				local Boolean is foundSpace: false;
				while({ k > start && !foundSpace }, {
					if({ s:byteAt(index: k) == 32 }, {
						foundSpace: true;
					}, {
						k: k - 1;
					});
				});
				if({ foundSpace && k > start }, {
					lines:add(item: s:substring(start: start, end: k));
					start: k + 1;
				}, {
					lines:add(item: s:substring(start: start, end: splitAt));
					start: splitAt;
				});
			});
		});
		return lines;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local DrawContext is dummy: DrawContext(canvas: SuitCanvas(width: 1, height: 1));
		local Int is lineH: dummy:measureTextHeight(pixelHeight: fpx);
		local Int is gapPx: activeScale:px(pt: lineGapPt);
		cachedLines: :computeLines(s: text:current(), maxW: c:maxW);

		local Int is maxLineW: 0;
		times(count: cachedLines:length(), worker: local Function(Int is i){
			local Int is w: dummy:measureTextWidth(text: cachedLines:get(index: i), pixelHeight: fpx);
			if({ w > maxLineW }, { maxLineW: w; });
		});
		dummy:canvas:dispose();

		local Int is count: cachedLines:length();
		local Int is totalH: if({ count > 0 }, { count * lineH + (count - 1) * gapPx }, { lineH });
		desiredSize: Size(width: c:clampW(w: maxLineW), height: c:clampH(h: totalH));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is fpx: :fontPx();
		local Int is lineH: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is gapPx: activeScale:px(pt: lineGapPt);
		local Int is color: if({ muted }, { activeTheme:textMuted }, { activeTheme:textPrimary });

		times(count: cachedLines:length(), worker: local Function(Int is i){
			local String is lineStr: cachedLines:get(index: i);
			local Int is lw: ctx:measureTextWidth(text: lineStr, pixelHeight: fpx);
			local Int is lx: b:x;
			if({ align == 'center' }, {
				lx: b:x + (b:width - lw) / 2;
			}, {
				if({ align == 'right' }, {
					lx: b:x + b:width - lw;
				});
			});
			ctx:drawText(x: lx, y: b:y + i * (lineH + gapPx), text: lineStr, color: color, pixelHeight: fpx);
		});
	}
}
