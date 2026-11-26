#! Package base:scrap
#! Resolution-independent toolbar widget with dropdown menus (point-based).

Class of SewNode is Toolbar{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'suit', SuitCanvas],
		['base', 'scrap', ToolbarConfig],
		['base', 'scrap', MenuConfig],
		['base', 'scrap', MenuItemConfig]
	];

	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	ToolbarConfig is config: ToolbarConfig();
	Int is openMenuIdx: -1;
	Int is hoverMenuIdx: -1;
	Int is hoverItemIdx: -1;

	replace Function is init(
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0),
		ToolbarConfig is config: ToolbarConfig()
	){
		:theme: theme;
		:scale: scale;
		:config: config;
		openMenuIdx: -1;
		hoverMenuIdx: -1;
		hoverItemIdx: -1;
	}

	Function is setConfig(ToolbarConfig is config){
		:config: config;
		openMenuIdx: -1;
		hoverMenuIdx: -1;
		hoverItemIdx: -1;
	}

	local Function of Int is textScale(){
		local Int is ts: scale:px(pt: 2.0);
		return if({ ts < 1 }, { 1 }, { ts });
	}

	local Function of Int is menuButtonWidthPx(MenuConfig is menu){
		local DrawContext is dummy: DrawContext(canvas: SuitCanvas(width: 1, height: 1));
		local Int is tw: dummy:measureTextWidth(text: menu:label, scale: :textScale());
		dummy:canvas:dispose();
		return tw + scale:px(pt: 20.0);
	}

	local Function of Int is menuButtonX(Int is idx){
		local Rect is b: bounds();
		local Int is x: b:x + scale:px(pt: 4.0);
		times(count: idx, worker: local Function(Int is i){
			local MenuConfig is m: config:menus:get(index: i);
			x: x + :menuButtonWidthPx(menu: m);
		});
		return x;
	}

	local Function of Int is dropdownWidthPx(){
		return scale:px(pt: 120.0);
	}

	local Function of Int is dropdownItemHeightPx(){
		return scale:px(pt: theme:menuItemHeightPt);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is h: scale:px(pt: config:heightPt);
		desiredSize: Size(width: c:clampW(w: c:maxW), height: c:clampH(h: h));
		return desiredSize;
	}

	## Updates hover state; returns `true` if visual state changed.
	Function of Boolean is onPointerMove(Int is x, Int is y){
		local Int is prevMenu: hoverMenuIdx;
		local Int is prevItem: hoverItemIdx;
		hoverMenuIdx: -1;
		hoverItemIdx: -1;

		local Rect is b: bounds();
		if({ y >= b:y && y < b:y + b:height }, {
			times(count: config:menus:length(), worker: local Function(Int is i){
				local MenuConfig is m: config:menus:get(index: i);
				local Int is bx: :menuButtonX(idx: i);
				local Int is bw: :menuButtonWidthPx(menu: m);
				if({ x >= bx && x < bx + bw }, {
					hoverMenuIdx: i;
				});
			});
		});

		if({ openMenuIdx >= 0 && openMenuIdx < config:menus:length() }, {
			local MenuConfig is om: config:menus:get(index: openMenuIdx);
			local Int is dx: :menuButtonX(idx: openMenuIdx);
			local Int is dy: b:y + b:height;
			local Int is dw: :dropdownWidthPx();
			local Int is ih: :dropdownItemHeightPx();
			local Int is dh: om:items:length() * ih;
			if({ x >= dx && x < dx + dw && y >= dy && y < dy + dh }, {
				hoverItemIdx: (y - dy) / ih;
			});
		});

		return prevMenu != hoverMenuIdx || prevItem != hoverItemIdx;
	}

	## Handles a left-click at ([x], [y]); returns `true` if visual state changed.
	Function of Boolean is onPointerClick(Int is x, Int is y){
		local Rect is b: bounds();
		local Boolean is handled: false;

		if({ y >= b:y && y < b:y + b:height }, {
			times(count: config:menus:length(), worker: local Function(Int is i){
				local MenuConfig is m: config:menus:get(index: i);
				local Int is bx: :menuButtonX(idx: i);
				local Int is bw: :menuButtonWidthPx(menu: m);
				if({ x >= bx && x < bx + bw }, {
					if({ openMenuIdx == i }, {
						openMenuIdx: -1;
					}, {
						openMenuIdx: i;
					});
					handled: true;
				});
			});
			if({ handled }, { return true; });
		});

		if({ openMenuIdx >= 0 && openMenuIdx < config:menus:length() }, {
			local MenuConfig is om: config:menus:get(index: openMenuIdx);
			local Int is dx: :menuButtonX(idx: openMenuIdx);
			local Int is dy: b:y + b:height;
			local Int is dw: :dropdownWidthPx();
			local Int is ih: :dropdownItemHeightPx();
			local Int is dh: om:items:length() * ih;
			if({ x >= dx && x < dx + dw && y >= dy && y < dy + dh }, {
				local Int is itemIdx: (y - dy) / ih;
				if({ itemIdx >= 0 && itemIdx < om:items:length() }, {
					local MenuItemConfig is item: om:items:get(index: itemIdx);
					openMenuIdx: -1;
					local Function is cb: item:onClick;
					cb();
					return true;
				});
			});
			openMenuIdx: -1;
			return true;
		});

		return false;
	}

	## Paints the toolbar strip and menu trigger buttons.
	Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: theme:toolbarBg);
		local Int is borderH: if({ scale:px(pt: 1.0) < 1 }, { 1 }, { scale:px(pt: 1.0) });
		ctx:fillRect(x: b:x, y: b:y + b:height - borderH, w: b:width, h: borderH, color: theme:toolbarBorder);

		local Int is ts: :textScale();
		local Int is th: ctx:measureTextHeight(scale: ts);
		local Int is textY: b:y + (b:height - th) / 2;
		local Int is padX: scale:px(pt: 10.0);

		times(count: config:menus:length(), worker: local Function(Int is i){
			local MenuConfig is m: config:menus:get(index: i);
			local Int is bx: :menuButtonX(idx: i);
			local Int is bw: :menuButtonWidthPx(menu: m);
			if({ openMenuIdx == i }, {
				ctx:fillRect(x: bx, y: b:y, w: bw, h: b:height - borderH, color: theme:activeBg);
			}, {
				if({ hoverMenuIdx == i }, {
					ctx:fillRect(x: bx, y: b:y, w: bw, h: b:height - borderH, color: theme:hoverBg);
				});
			});
			ctx:drawText(x: bx + padX, y: textY, text: m:label, color: theme:textPrimary, scale: ts);
		});
	}

	## Paints the open dropdown menu popup above the body layer.
	Function is paintOverlay(DrawContext is ctx){
		if({ openMenuIdx < 0 || openMenuIdx >= config:menus:length() }, { return; });
		local Rect is b: bounds();
		local MenuConfig is om: config:menus:get(index: openMenuIdx);
		local Int is count: om:items:length();
		if({ count <= 0 }, { return; });

		local Int is dx: :menuButtonX(idx: openMenuIdx);
		local Int is dy: b:y + b:height;
		local Int is dw: :dropdownWidthPx();
		local Int is ih: :dropdownItemHeightPx();
		local Int is dh: count * ih;

		ctx:fillRect(x: dx, y: dy, w: dw, h: dh, color: theme:menuBg);
		ctx:strokeRect(x: dx, y: dy, w: dw, h: dh, color: theme:menuBorder);

		local Int is ts: :textScale();
		local Int is th: ctx:measureTextHeight(scale: ts);
		local Int is padX: scale:px(pt: 10.0);

		times(count: count, worker: local Function(Int is i){
			local MenuItemConfig is item: om:items:get(index: i);
			local Int is iy: dy + i * ih;
			if({ hoverItemIdx == i }, {
				ctx:fillRect(x: dx + 1, y: iy + 1, w: dw - 2, h: ih - 2, color: theme:hoverBg);
			});
			local Int is ty: iy + (ih - th) / 2;
			ctx:drawText(x: dx + padX, y: ty, text: item:label, color: theme:textPrimary, scale: ts);
		});
	}
}
