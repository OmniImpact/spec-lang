#! Package base:scrap
#! Shared dropdown placement helper computing smart up/down and left/right window-clamped bounds.

Class is DropdownPopup{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', Rect]
	];

	held DropdownPopup is shared: DropdownPopup();

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
