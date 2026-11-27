#! Package base:scrap
#! Shared dropdown placement helper computing smart up/down and left/right window-clamped bounds.

Class is DropdownPopup{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', Rect],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext]
	];

	held DropdownPopup is shared: DropdownPopup();

	## Paints a theme-aware dropdown trigger button box (fill, border style, radius, and button shadow).
	Function is paintButtonBox(
		DrawContext is ctx,
		Theme is theme,
		Scale is scale,
		Rect is bounds,
		Boolean is selected: false,
		Boolean is hovered: false,
		Boolean is focused: false
	){
		local Int is btnPx: theme:buttonBorderPx(scaleFactor: scale:factor);
		local Int is radPx: scale:px(pt: theme:buttonCornerRadiusPt);
		local Int is shBlur: scale:px(pt: theme:buttonShadowBlurPt);
		local Int is shOffX: scale:px(pt: theme:buttonShadowOffsetXPt);
		local Int is shOffY: scale:px(pt: theme:buttonShadowOffsetYPt);
		local Int is shCol: if({ shBlur > 0 || shOffX != 0 || shOffY != 0 }, { 1426063360 }, { 0 });
		local FillStyle is fill: theme:resolveButtonFill(
			enabled: true, selected: selected, hovered: hovered, focused: focused
		);
		local Int is borderCol: if({ focused || selected }, { theme:textAccent }, { theme:buttonBorderColorArgb() });
		ctx:drawStyledBoxFill(
			x: bounds:x, y: bounds:y, w: bounds:width, h: bounds:height,
			fill: fill, borderColor: borderCol, thickness: btnPx, radius: radPx,
			style: theme:buttonBorderStyle,
			shadowOffsetX: shOffX, shadowOffsetY: shOffY, shadowBlur: shBlur, shadowColor: shCol
		);
	}

	## Places a popup of ([popupW], [popupH]) near [anchor] inside ([viewW], [viewH]), flipping up or left when needed.
	Function of Rect is placeRect(Rect is anchor, Int is popupW, Int is popupH, Int is viewW, Int is viewH, Int is gapPx: 2){
		local Int is x: anchor:x;
		if({ viewW > 0 && x + popupW > viewW - 2 }, {
			local Int is rightAligned: (anchor:x + anchor:width) - popupW;
			if({ rightAligned >= 2 }, {
				x: rightAligned;
			}, {
				x: viewW - popupW - 2;
			});
		});
		if({ x < 2 }, { x: 2; });

		local Int is y: anchor:y + anchor:height + gapPx;
		if({ viewH > 0 }, {
			local Int is spaceBelow: viewH - (anchor:y + anchor:height + gapPx) - 2;
			local Int is spaceAbove: anchor:y - gapPx - 2;
			if({ popupH > spaceBelow && spaceAbove > spaceBelow }, {
				y: anchor:y - gapPx - popupH;
			});
			if({ y + popupH > viewH - 2 }, {
				y: viewH - popupH - 2;
			});
		});
		if({ y < 2 }, { y: 2; });
		return Rect(x: x, y: y, width: popupW, height: popupH);
	}
}
