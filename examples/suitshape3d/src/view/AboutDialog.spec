#! Package suitshape3d:view
#! App-specific About dialog built on `base:scrap:Dialog` showing centered version & description.

Class is AboutDialog{
	replace [String] is namespace: ['suitshape3d', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', Dialog],
		['suitshape3d', 'viewmodel', Shape3DViewModel]
	];

	local Function of Array of String is wrapText(String is s, Int is maxChars){
		local Array of String is lines: Array();
		if({ s == '' }, { return lines; });
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

	Function of Dialog is build(Shape3DViewModel is vm){
		return Dialog(
			title: 'About SuitShape3D',
			open: vm:aboutOpen,
			widthPt: 480.0,
			heightPt: 180.0,
			onPaint: local Function(DrawContext is ctx, Int is w, Int is h, Theme is theme, Scale is scale){
				local Int is ts: if({ scale:px(pt: 2.0) < 1 }, { 1 }, { scale:px(pt: 2.0) });
				local Int is lineH: ctx:measureTextHeight(scale: ts) + scale:px(pt: 8.0);
				local Int is charW: 6 * ts;
				local Int is maxChars: if({ charW > 0 }, { (w - scale:px(pt: 32.0)) / charW }, { 40 });

				local String is ver: vm:versionText:current();
				local Array of String is descLines: :wrapText(s: vm:descriptionText:current(), maxChars: maxChars);
				local Int is totalLines: 1 + descLines:length();
				local Int is blockH: totalLines * lineH;
				local Int is startY: (h - blockH) / 2;

				local Int is vw: ctx:measureTextWidth(text: ver, scale: ts);
				ctx:drawText(x: (w - vw) / 2, y: startY, text: ver, color: theme:textPrimary, scale: ts);

				times(count: descLines:length(), worker: local Function(Int is i){
					local String is dl: descLines:get(index: i);
					local Int is dw: ctx:measureTextWidth(text: dl, scale: ts);
					ctx:drawText(
						x: (w - dw) / 2,
						y: startY + (i + 1) * lineH,
						text: dl,
						color: theme:textMuted,
						scale: ts
					);
				});
			}
		);
	}
}
