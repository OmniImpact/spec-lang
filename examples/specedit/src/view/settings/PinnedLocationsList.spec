#! Package specedit:view:settings
#! Interactive pinned-locations list with drag-and-drop gripper handles and remove buttons.

Class of SewNode is PinnedLocationsList{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', DrawContext],
		['specedit', 'viewmodel', SettingsViewModel]
	];

	SettingsViewModel is vm: SettingsViewModel();
	Int is hoverRow: -1;
	Int is hoverRemoveRow: -1;
	Int is dragFromIdx: -1;
	Int is dragToIdx: -1;

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is rowHeightPx(){
		local Int is h: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0) + activeTheme:paddingPt * 1.75);
		return if({ h < 24 }, { 24 }, { h });
	}

	local Function of Int is rowIndexAt(Int is y){
		local Rect is b: bounds();
		local Int is count: vm:pinned:paths:length();
		if({ y < b:y || count <= 0 }, { return -1; });
		local Int is rh: :rowHeightPx();
		local Int is idx: (y - b:y) / rh;
		if({ idx < 0 || idx >= count }, { return -1; });
		return idx;
	}

	local Function of Rect is removeBtnRect(Rect is b, Int is rowIdx){
		local Int is rh: :rowHeightPx();
		local Int is ry: b:y + rowIdx * rh;
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt * 0.5);
		local Int is btnW: activeScale:px(pt: 68.0);
		local Int is btnH: rh - pad;
		if({ btnH < 16 }, { btnH: 16; });
		local Int is bx: b:x + b:width - btnW - pad;
		local Int is by: ry + (rh - btnH) / 2;
		return Rect(x: bx, y: by, width: btnW, height: btnH);
	}

	local Function of Boolean is inRect(Rect is r, Int is x, Int is y){
		return x >= r:x && x < r:x + r:width && y >= r:y && y < r:y + r:height;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is count: vm:pinned:paths:length();
		local Int is rh: :rowHeightPx();
		local Int is totalH: if({ count > 0 }, { count * rh }, { rh });
		desiredSize: Size(width: c:clampW(w: c:maxW), height: c:clampH(h: totalH));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is count: vm:pinned:paths:length();
		local Int is fpx: :fontPx();
		local Int is th: DrawContext:measureHeight(pixelHeight: fpx);
		local Int is linePx: activeTheme:linePx(scaleFactor: activeScale:factor);
		local Int is bw: activeTheme:borderPx(scaleFactor: activeScale:factor);

		if({ count == 0 }, {
			ctx:drawText(x: b:x, y: b:y + (b:height - th) / 2, text: 'No pinned locations.', color: activeTheme:textMuted, pixelHeight: fpx);
			return;
		});

		local Int is rh: :rowHeightPx();
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is dotSz: linePx + 1;
		local Int is dotGap: dotSz + activeScale:px(pt: 2.0);
		local Int is gripW: dotGap * 2 + pad;

		local Int is i: 0;
		while({ i < count }, {
			local Int is ry: b:y + i * rh;
			local Boolean is isDragged: (i == dragFromIdx);
			if({ isDragged }, {
				ctx:fillRect(x: b:x, y: ry, w: b:width, h: rh, color: activeTheme:activeBg);
			}, {
			if({ i == hoverRow }, {
				ctx:fillRect(x: b:x, y: ry, w: b:width, h: rh, color: activeTheme:hoverBg);
			}); });

			## Draw 6-dot gripper handle on the left
			local Int is gx: b:x + pad / 2;
			local Int is gy: ry + (rh - dotGap * 2 - dotSz) / 2;
			local Int is gCol: if({ isDragged || i == hoverRow }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			local Int is r: 0;
			while({ r < 3 }, {
				local Int is cIdx: 0;
				while({ cIdx < 2 }, {
					ctx:fillRect(x: gx + cIdx * dotGap, y: gy + r * dotGap, w: dotSz, h: dotSz, color: gCol);
					cIdx: cIdx + 1;
				});
				r: r + 1;
			});

			## Label: Name (Path)
			local Boolean is canRemove: !vm:pinned:isDefaultAt(index: i);
			local Rect is btnR: :removeBtnRect(b: b, rowIdx: i);
			local String is nm: vm:pinned:names:get(index: i);
			local String is pp: vm:pinned:paths:get(index: i);
			local Int is tx: b:x + gripW;
			local Int is maxTextW: if({ canRemove }, { btnR:x - tx - pad }, { (b:x + b:width) - tx - pad });
			if({ maxTextW > 20 }, {
				ctx:setClip(x: tx, y: ry, w: maxTextW, h: rh);
				ctx:drawText(x: tx, y: ry + (rh - th) / 2, text: nm . '  (' . pp . ')', color: activeTheme:textPrimary, pixelHeight: fpx);
				ctx:clearClip();
			});

			## Remove button (only for user-pinned locations)
			if({ canRemove }, {
				local Boolean is remHov: (i == hoverRemoveRow);
				local Int is btnBg: if({ remHov }, { activeTheme:hoverBg }, { activeTheme:panelBg });
				ctx:fillRect(x: btnR:x, y: btnR:y, w: btnR:width, h: btnR:height, color: btnBg);
				if({ bw > 0 }, {
					ctx:strokeRect(x: btnR:x, y: btnR:y, w: btnR:width, h: btnR:height, color: activeTheme:buttonBorder, thickness: bw);
				});
				local Int is rw: DrawContext:measureWidth(text: 'Remove', pixelHeight: fpx);
				ctx:drawText(
					x: btnR:x + (btnR:width - rw) / 2,
					y: btnR:y + (btnR:height - th) / 2,
					text: 'Remove',
					color: activeTheme:textPrimary,
					pixelHeight: fpx
				);
			});

			if({ i + 1 < count && linePx > 0 }, {
				ctx:fillRect(x: b:x, y: ry + rh - linePx, w: b:width, h: linePx, color: activeTheme:toolbarBorder);
			});
			i: i + 1;
		});

		## Insertion indicator when dragging to reorder
		if({ dragFromIdx >= 0 && dragToIdx >= 0 && dragToIdx != dragFromIdx }, {
			local Int is lineY: b:y + dragToIdx * rh;
			if({ dragToIdx > dragFromIdx }, { lineY: lineY + rh - linePx * 2; });
			ctx:fillRect(x: b:x, y: lineY, w: b:width, h: linePx * 2, color: activeTheme:textAccent);
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Rect is b: bounds();
		local Int is nextRow: :rowIndexAt(y: y);
		if({ !:inRect(r: b, x: x, y: y) }, { nextRow: -1; });
		local Int is nextRem: -1;
		if({ nextRow >= 0 && !vm:pinned:isDefaultAt(index: nextRow) }, {
			if({ :inRect(r: :removeBtnRect(b: b, rowIdx: nextRow), x: x, y: y) }, {
				nextRem: nextRow;
			});
		});
		if({ nextRow != hoverRow || nextRem != hoverRemoveRow }, {
			:hoverRow: nextRow;
			:hoverRemoveRow: nextRem;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function is clearHover(){
		if({ hoverRow != -1 || hoverRemoveRow != -1 }, {
			:hoverRow: -1;
			:hoverRemoveRow: -1;
			invalidate();
		});
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods){
		local Rect is b: bounds();
		local Int is idx: :rowIndexAt(y: y);
		if({ dragFromIdx < 0 }, {
			local Boolean is overRemove: idx >= 0 && !vm:pinned:isDefaultAt(index: idx) && :inRect(r: :removeBtnRect(b: b, rowIdx: idx), x: x, y: y);
			if({ idx >= 0 && !overRemove }, {
				:dragFromIdx: idx;
				:dragToIdx: idx;
				invalidate();
				return true;
			});
			return false;
		});
		if({ idx >= 0 && idx != dragToIdx }, {
			:dragToIdx: idx;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragFromIdx >= 0 }, {
			local Int is fromIdx: dragFromIdx;
			local Int is toIdx: dragToIdx;
			:dragFromIdx: -1;
			:dragToIdx: -1;
			if({ toIdx >= 0 && toIdx != fromIdx }, {
				vm:movePinned(fromIdx: fromIdx, toIdx: toIdx);
			}, {
				invalidate();
			});
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods){
		local Rect is b: bounds();
		local Int is idx: :rowIndexAt(y: y);
		if({ idx >= 0 && !vm:pinned:isDefaultAt(index: idx) && :inRect(r: :removeBtnRect(b: b, rowIdx: idx), x: x, y: y) }, {
			vm:removePinned(index: idx);
			return true;
		});
		return false;
	}
}