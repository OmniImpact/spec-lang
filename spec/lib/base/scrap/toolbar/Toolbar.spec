#! Package base:scrap
#! Resolution-independent toolbar widget built over `Bar` with dropdown menus and sub-menus.

Class of SewNode is Toolbar{
	replace [String] is namespace: ['base', 'scrap', 'toolbar'];

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
		['base', 'scrap', Bar],
		['base', 'fabric', 'svg', SvgRenderer],
		['base', 'scrap', 'toolbar', ToolbarConfig],
		['base', 'scrap', 'menu', MenuConfig],
		['base', 'scrap', 'menu', MenuItemConfig]
	];

	Bar is bar: Bar(borderSide: 'bottom');
	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	ToolbarConfig is config: ToolbarConfig();
	Int is openMenuIdx: -1;
	Int is hoverMenuIdx: -1;
	Int is hoverItemIdx: -1;
	Int is openSubMenuIdx: -1;
	Int is hoverSubItemIdx: -1;
	Function is onMenuOpen: local Function(MenuConfig is menu){};

	replace Function is init(
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0),
		ToolbarConfig is config: ToolbarConfig(),
		Function is onMenuOpen: local Function(MenuConfig is menu){}
	){
		:theme: theme;
		:scale: scale;
		:config: config;
		:onMenuOpen: onMenuOpen;
		:bar: Bar(heightPt: config:heightPt, borderSide: 'bottom', theme: theme, scale: scale);
		openMenuIdx: -1;
		hoverMenuIdx: -1;
		hoverItemIdx: -1;
		openSubMenuIdx: -1;
		hoverSubItemIdx: -1;
	}

	Function is setConfig(ToolbarConfig is config){
		:config: config;
		bar:setHeightPt(heightPt: config:heightPt);
		openMenuIdx: -1;
		hoverMenuIdx: -1;
		hoverItemIdx: -1;
		openSubMenuIdx: -1;
		hoverSubItemIdx: -1;
		invalidate();
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		:theme: theme;
		bar:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:scale: scale;
		bar:setScale(scale: scale);
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		bar:arrange(bounds: bounds);
	}

	local Function of Int is fontPx(){
		local Int is px: scale:px(pt: 18.0);
		return if({ px < 12 }, { 12 }, { px });
	}

	local Function of Int is menuButtonWidthPx(MenuConfig is menu){
		local Int is tw: DrawContext:measureWidth(text: menu:label, pixelHeight: :fontPx());
		return tw + scale:px(pt: 22.0);
	}

	local Function of Int is menuButtonX(Int is idx){
		local Rect is b: bounds();
		local Int is x: b:x + scale:px(pt: 4.0);
		times(count: idx, worker: local Function(Int is i){
			local MenuConfig is m: config:menus:get(index: i);
			if({ m:visible }, {
				x: x + :menuButtonWidthPx(menu: m);
			});
		});
		return x;
	}

	local Function of Int is dropdownWidthPx(){
		return scale:px(pt: 150.0);
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
	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Int is prevMenu: hoverMenuIdx;
		local Int is prevItem: hoverItemIdx;
		local Int is prevSubOpen: openSubMenuIdx;
		local Int is prevSubHover: hoverSubItemIdx;
		hoverMenuIdx: -1;
		hoverItemIdx: -1;
		hoverSubItemIdx: -1;

		local Rect is b: bounds();
		if({ y >= b:y && y < b:y + b:height }, {
			times(count: config:menus:length(), worker: local Function(Int is i){
				local MenuConfig is m: config:menus:get(index: i);
				if({ m:visible }, {
					local Int is bx: :menuButtonX(idx: i);
					local Int is bw: :menuButtonWidthPx(menu: m);
					if({ x >= bx && x < bx + bw }, {
						hoverMenuIdx: i;
					});
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

			if({ openSubMenuIdx >= 0 && openSubMenuIdx < om:items:length() }, {
				local MenuItemConfig is parentItem: om:items:get(index: openSubMenuIdx);
				if({ parentItem:subItems:length() > 0 }, {
					local Int is sdx: dx + dw;
					local Int is sdy: dy + openSubMenuIdx * ih;
					local Int is sdh: parentItem:subItems:length() * ih;
					if({ x >= sdx && x < sdx + dw && y >= sdy && y < sdy + sdh }, {
						hoverSubItemIdx: (y - sdy) / ih;
						hoverItemIdx: openSubMenuIdx;
					});
				});
			});

			if({ hoverSubItemIdx < 0 && x >= dx && x < dx + dw && y >= dy && y < dy + dh }, {
				local Int is idx: (y - dy) / ih;
				hoverItemIdx: idx;
				if({ idx >= 0 && idx < om:items:length() }, {
					local MenuItemConfig is item: om:items:get(index: idx);
					if({ item:enabled && item:subItems:length() > 0 }, {
						openSubMenuIdx: idx;
					}, {
						openSubMenuIdx: -1;
					});
				});
			});
		});

		return prevMenu != hoverMenuIdx || prevItem != hoverItemIdx || prevSubOpen != openSubMenuIdx || prevSubHover != hoverSubItemIdx;
	}

	## Handles a left-click at ([x], [y]); returns `true` if visual state changed.
	Function of Boolean is onPointerClick(Int is x, Int is y){
		local Rect is b: bounds();
		local Boolean is handled: false;

		if({ y >= b:y && y < b:y + b:height }, {
			times(count: config:menus:length(), worker: local Function(Int is i){
				local MenuConfig is m: config:menus:get(index: i);
				if({ m:visible }, {
					local Int is bx: :menuButtonX(idx: i);
					local Int is bw: :menuButtonWidthPx(menu: m);
					if({ x >= bx && x < bx + bw }, {
						if({ openMenuIdx == i }, {
							openMenuIdx: -1;
							openSubMenuIdx: -1;
						}, {
							openMenuIdx: i;
							openSubMenuIdx: -1;
							local Function is ocb: onMenuOpen;
							ocb(m);
						});
						handled: true;
					});
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

			if({ openSubMenuIdx >= 0 && openSubMenuIdx < om:items:length() }, {
				local MenuItemConfig is parentItem: om:items:get(index: openSubMenuIdx);
				if({ parentItem:subItems:length() > 0 }, {
					local Int is sdx: dx + dw;
					local Int is sdy: dy + openSubMenuIdx * ih;
					local Int is sdh: parentItem:subItems:length() * ih;
					if({ x >= sdx && x < sdx + dw && y >= sdy && y < sdy + sdh }, {
						local Int is subIdx: (y - sdy) / ih;
						if({ subIdx >= 0 && subIdx < parentItem:subItems:length() }, {
							local MenuItemConfig is subItem: parentItem:subItems:get(index: subIdx);
							if({ !subItem:enabled }, { return true; });
							openMenuIdx: -1;
							openSubMenuIdx: -1;
							local Function is scb: subItem:onClick;
							scb();
							return true;
						});
					});
				});
			});

			if({ x >= dx && x < dx + dw && y >= dy && y < dy + dh }, {
				local Int is itemIdx: (y - dy) / ih;
				if({ itemIdx >= 0 && itemIdx < om:items:length() }, {
					local MenuItemConfig is item: om:items:get(index: itemIdx);
					if({ !item:enabled }, { return true; });
					if({ item:subItems:length() > 0 }, {
						openSubMenuIdx: itemIdx;
						return true;
					});
					openMenuIdx: -1;
					openSubMenuIdx: -1;
					local Function is cb: item:onClick;
					cb();
					return true;
				});
			});
			openMenuIdx: -1;
			openSubMenuIdx: -1;
			return true;
		});

		return false;
	}

	## Paints the underlying `Bar` overlaid with menu trigger buttons.
	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		bar:paint(ctx: ctx);
		local Int is borderH: if({ scale:px(pt: 1.0) < 1 }, { 1 }, { scale:px(pt: 1.0) });
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is textY: b:y + (b:height - th) / 2;
		local Int is padX: scale:px(pt: 11.0);

		times(count: config:menus:length(), worker: local Function(Int is i){
			local MenuConfig is m: config:menus:get(index: i);
			if({ m:visible }, {
				local Int is bx: :menuButtonX(idx: i);
				local Int is bw: :menuButtonWidthPx(menu: m);
				if({ openMenuIdx == i }, {
					ctx:fillRect(x: bx, y: b:y, w: bw, h: b:height - borderH, color: theme:activeBg);
				}, {
					if({ hoverMenuIdx == i }, {
						ctx:fillRect(x: bx, y: b:y, w: bw, h: b:height - borderH, color: theme:hoverBg);
					});
				});
				ctx:drawText(x: bx + padX, y: textY, text: m:label, color: theme:textPrimary, pixelHeight: fpx);
			});
		});
	}

	local Function of Boolean is listHasIndicators(Array of MenuItemConfig is list){
		local Int is i: 0;
		while({ i < list:length() }, {
			local MenuItemConfig is it: list:get(index: i);
			if({ it:kind == 'radio' || it:kind == 'toggle' || it:checked || it:iconSvg != '' }, {
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	local Function is paintMenuItem(
		DrawContext is ctx,
		MenuItemConfig is item,
		Int is x,
		Int is y,
		Int is w,
		Int is h,
		Int is fpx,
		Int is th,
		Int is padX,
		Boolean is hovered,
		Boolean is reserveInd
	){
		if({ hovered && item:enabled }, {
			ctx:fillRect(x: x + 1, y: y + 1, w: w - 2, h: h - 2, color: theme:hoverBg);
		});
		local Int is fgCol: if({ item:enabled }, { theme:textPrimary }, { theme:textMuted });
		local Int is indW: if({ reserveInd }, { scale:px(pt: 18.0) }, { 0 });
		local Int is cy: y + h / 2;
		local Int is iconSz: scale:px(pt: 12.0);
		if({ iconSz < 10 }, { iconSz: 10; });
		local Int is iy: cy - iconSz / 2;
		if({ item:kind == 'radio' }, {
			local String is rSvg: if({ item:checked }, { config:radioOnIconSvg }, { config:radioOffIconSvg });
			if({ rSvg != '' }, {
				SvgRenderer:shared:draw(ctx: ctx, svgSrc: rSvg, x: x + padX, y: iy, widthPx: iconSz, heightPx: iconSz, tintColor: fgCol, useTint: true);
			});
		}, {
			if({ item:kind == 'toggle' }, {
				local String is cSvg: if({ item:checked }, { config:checkboxOnIconSvg }, { config:checkboxOffIconSvg });
				if({ cSvg != '' }, {
					SvgRenderer:shared:draw(ctx: ctx, svgSrc: cSvg, x: x + padX, y: iy, widthPx: iconSz, heightPx: iconSz, tintColor: fgCol, useTint: true);
				});
			}, {
				if({ item:iconSvg != '' }, {
					SvgRenderer:shared:draw(ctx: ctx, svgSrc: item:iconSvg, x: x + padX, y: iy, widthPx: iconSz, heightPx: iconSz, tintColor: fgCol, useTint: true);
				});
			});
		});
		local Int is ty: y + (h - th) / 2;
		ctx:drawText(x: x + padX + indW, y: ty, text: item:label, color: fgCol, pixelHeight: fpx);
	}

	## Paints the open dropdown menu popup (and any open sub-menu) above the body layer.
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

		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is padX: scale:px(pt: 12.0);
		local Boolean is mainInd: :listHasIndicators(list: om:items);

		times(count: count, worker: local Function(Int is i){
			local MenuItemConfig is item: om:items:get(index: i);
			local Int is iy: dy + i * ih;
			:paintMenuItem(
				ctx: ctx,
				item: item,
				x: dx,
				y: iy,
				w: dw,
				h: ih,
				fpx: fpx,
				th: th,
				padX: padX,
				hovered: (hoverItemIdx == i || openSubMenuIdx == i),
				reserveInd: mainInd
			);
			if({ item:subItems:length() > 0 }, {
				local Int is ty: iy + (ih - th) / 2;
				local Int is aw: ctx:measureTextWidth(text: '...', pixelHeight: fpx);
				ctx:drawText(x: dx + dw - padX - aw, y: ty, text: '...', color: theme:textMuted, pixelHeight: fpx);
			});
		});

		if({ openSubMenuIdx >= 0 && openSubMenuIdx < count }, {
			local MenuItemConfig is parentItem: om:items:get(index: openSubMenuIdx);
			local Int is scount: parentItem:subItems:length();
			if({ scount > 0 }, {
				local Int is sdx: dx + dw;
				local Int is sdy: dy + openSubMenuIdx * ih;
				local Int is sdh: scount * ih;
				ctx:fillRect(x: sdx, y: sdy, w: dw, h: sdh, color: theme:menuBg);
				ctx:strokeRect(x: sdx, y: sdy, w: dw, h: sdh, color: theme:menuBorder);
				local Boolean is subInd: :listHasIndicators(list: parentItem:subItems);
				times(count: scount, worker: local Function(Int is j){
					local MenuItemConfig is sub: parentItem:subItems:get(index: j);
					local Int is siy: sdy + j * ih;
					:paintMenuItem(
						ctx: ctx,
						item: sub,
						x: sdx,
						y: siy,
						w: dw,
						h: ih,
						fpx: fpx,
						th: th,
						padX: padX,
						hovered: (hoverSubItemIdx == j),
						reserveInd: subInd
					);
				});
			});
		});
	}
}
