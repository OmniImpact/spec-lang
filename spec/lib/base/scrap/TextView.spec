#! Package base:scrap
#! Multi-line reactive document text view (`SewNode`) for `ScrollView`.

Class of SewNode is TextView{
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
		['base', 'fabric', DrawContext]
	];

	TextEmitter is text: TextEmitter(initial: '');
	Float is padPt: 12.0;
	Float is lineGapPt: 4.0;
	Array of String is lines: Array();
	String is cachedRaw: '';

	replace Function is init(
		TextEmitter is text: TextEmitter(initial: ''),
		Float is padPt: 12.0,
		Float is lineGapPt: 4.0
	){
		:text: text;
		:padPt: padPt;
		:lineGapPt: lineGapPt;
		:lines: Array();
		:cachedRaw: '';
		:rebuildLines(raw: text:current());
		signalBag:track(
			slot: 'text',
			emitter: text,
			collector: text:collect(onEmit: local Function(String is next){
				:rebuildLines(raw: next);
				invalidate();
			})
		);
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: 18.0);
		return if({ px < 12 }, { 12 }, { px });
	}

	local Function is rebuildLines(String is raw){
		cachedRaw: raw;
		lines: Array();
		local Int is len: raw:length();
		if({ len == 0 }, { return; });
		local Int is start: 0;
		local Int is i: 0;
		while({ i < len }, {
			local Int is ch: raw:byteAt(index: i);
			if({ ch == 10 }, {
				local Int is endIdx: i;
				if({ endIdx > start && raw:byteAt(index: endIdx - 1) == 13 }, {
					endIdx: endIdx - 1;
				});
				lines:add(item: raw:substring(start: start, end: endIdx));
				start: i + 1;
			});
			i: i + 1;
		});
		if({ start <= len }, {
			local Int is endIdx: len;
			if({ endIdx > start && raw:byteAt(index: endIdx - 1) == 13 }, {
				endIdx: endIdx - 1;
			});
			lines:add(item: raw:substring(start: start, end: endIdx));
		});
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is gapPx: activeScale:px(pt: lineGapPt);
		local Int is padPx: activeScale:px(pt: padPt);
		local Int is rowH: fpx + gapPx;
		local Int is totalH: padPx * 2 + lines:length() * rowH;
		desiredSize: Size(width: c:maxW, height: totalH);
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		local Int is fpx: :fontPx();
		local Int is gapPx: activeScale:px(pt: lineGapPt);
		local Int is padPx: activeScale:px(pt: padPt);
		local Int is rowH: fpx + gapPx;
		local Int is count: lines:length();
		if({ count == 0 || rowH <= 0 }, { return; });

		local Int is minY: if({ ctx:hasClip }, { ctx:clipY }, { 0 });
		local Int is maxY: if({ ctx:hasClip }, { ctx:clipY + ctx:clipH }, { b:y + b:height });

		local Int is firstIdx: (minY - (b:y + padPx)) / rowH;
		if({ firstIdx < 0 }, { firstIdx: 0; });
		local Int is lastIdx: ((maxY - (b:y + padPx)) / rowH) + 1;
		if({ lastIdx >= count }, { lastIdx: count - 1; });

		local Int is i: firstIdx;
		while({ i <= lastIdx }, {
			local Int is ly: b:y + padPx + i * rowH;
			if({ ly >= minY && (ly + fpx) <= maxY }, {
				local String is lineStr: lines:get(index: i);
				if({ lineStr != '' }, {
					ctx:drawText(
						x: b:x + padPx,
						y: ly,
						text: lineStr,
						color: activeTheme:textPrimary,
						pixelHeight: fpx
					);
				});
			});
			i: i + 1;
		});
	}
}
