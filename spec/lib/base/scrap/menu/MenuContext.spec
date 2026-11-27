#! Package base:scrap
#! Floating right-click context menu overlay backed by `MenuItemConfig` items.

Class of SewNode is MenuContext{
	replace [String] is namespace: ['base', 'scrap', 'menu'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'fabric', 'svg', SvgRenderer],
		['base', 'scrap', 'menu', MenuItemConfig]
	];

	Boolean is isOpen: false;
	Int is posX: 0;
	Int is posY: 0;
	Int is hoverIdx: -1;
	Array of MenuItemConfig is items: Array();
	String is radioOffIconSvg: '';
	String is radioOnIconSvg: '';
	String is checkboxOnIconSvg: '';

	replace Function is init(
		String is radioOffIconSvg: '',
		String is radioOnIconSvg: '',
		String is checkboxOnIconSvg: ''
	){
		isOpen: false;
		posX: 0;
		posY: 0;
		hoverIdx: -1;
		items: Array();
		:radioOffIconSvg: radioOffIconSvg;
		:radioOnIconSvg: radioOnIconSvg;
		:checkboxOnIconSvg: checkboxOnIconSvg;
	}

	## Opens the context menu at ([x], [y]) with [items] and invalidates.
	Function is open(Int is x, Int is y, Array of MenuItemConfig is items){
		:posX: x;
		:posY: y;
		:items: items;
		:hoverIdx: -1;
		:isOpen: items:length() > 0;
		invalidate();
	}

	## Closes the context menu and invalidates.
	Function is close(){
		if({ !isOpen }, { return; });
		isOpen: false;
		hoverIdx: -1;
		invalidate();
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 15.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is itemHeightPx(){
		local Int is h: activeScale:px(pt: activeTheme:menuItemHeightPt);
		return if({ h < 16 }, { 16 }, { h });
	}

	local Function of Boolean is hasIndicators(){
		local Int is i: 0;
		while({ i < items:length() }, {
			local MenuItemConfig is it: items:get(index: i);
			if({ it:iconSvg != '' || it:checked || it:kind == 'radio' || it:kind == 'toggle' }, { return true; });
			i: i + 1;
		});
		return false;
	}

	local Function of Int is menuWidthPx(){
		local Int is fpx: :fontPx();
		local Int is padX: activeScale:px(pt: activeTheme:paddingMediumPt);
		local Int is indW: if({ :hasIndicators() }, { activeScale:px(pt: activeTheme:iconSizePt + activeTheme:paddingPt) }, { 0 });
		local Int is minW: activeScale:px(pt: activeTheme:buttonMinWidthPt * 2.0);
		local Int is maxW: minW;
		local Int is i: 0;
		while({ i < items:length() }, {
			local Int is tw: DrawContext:measureWidth(text: items:get(index: i):label, pixelHeight: fpx) + padX * 2 + indW;
			if({ tw > maxW }, { maxW: tw; });
			i: i + 1;
		});
		return maxW;
	}

	local Function of Int is clampedX(Int is viewW, Int is mw){
		local Int is x: posX;
		if({ x + mw > viewW }, { x: viewW - mw - 2; });
		if({ x < 2 }, { x: 2; });
		return x;
	}

	local Function of Int is clampedY(Int is viewH, Int is mh){
		local Int is y: posY;
		if({ y + mh > viewH }, { y: viewH - mh - 2; });
		if({ y < 2 }, { y: 2; });
		return y;
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		return isOpen && !pointerTransparent;
	}

	replace Function is clearHover(){
		if({ hoverIdx >= 0 }, {
			hoverIdx: -1;
			invalidate();
		});
	}

	Function of Boolean is handlePointerMove(Int is x, Int is y, Int is viewW, Int is viewH){
		if({ !isOpen }, { return false; });
		local Int is mw: :menuWidthPx();
		local Int is ih: :itemHeightPx();
		local Int is mh: items:length() * ih;
		local Int is mx: :clampedX(viewW: viewW, mw: mw);
		local Int is my: :clampedY(viewH: viewH, mh: mh);
		local Int is nextHover: -1;
		if({ x >= mx && x < mx + mw && y >= my && y < my + mh && ih > 0 }, {
			nextHover: (y - my) / ih;
		});
		if({ nextHover != hoverIdx }, {
			hoverIdx: nextHover;
			return true;
		});
		return false;
	}

	Function of Boolean is handlePointerClick(Int is x, Int is y, Int is viewW, Int is viewH){
		if({ !isOpen }, { return false; });
		local Int is mw: :menuWidthPx();
		local Int is ih: :itemHeightPx();
		local Int is mh: items:length() * ih;
		local Int is mx: :clampedX(viewW: viewW, mw: mw);
		local Int is my: :clampedY(viewH: viewH, mh: mh);
		if({ x >= mx && x < mx + mw && y >= my && y < my + mh && ih > 0 }, {
			local Int is idx: (y - my) / ih;
			if({ idx >= 0 && idx < items:length() }, {
				local MenuItemConfig is item: items:get(index: idx);
				if({ !item:enabled }, { return true; });
				:close();
				local Function is cb: item:onClick;
				cb();
				return true;
			});
		});
		:close();
		return true;
	}

	replace Function is paint(DrawContext is ctx){
		if({ !isOpen || items:length() == 0 }, { return; });
		local Int is viewW: ctx:canvas:width;
		local Int is viewH: ctx:canvas:height;
		local Int is mw: :menuWidthPx();
		local Int is ih: :itemHeightPx();
		local Int is mh: items:length() * ih;
		local Int is mx: :clampedX(viewW: viewW, mw: mw);
		local Int is my: :clampedY(viewH: viewH, mh: mh);

		local Int is linePx: activeTheme:borderPx(scaleFactor: activeScale:factor);
		ctx:fillRect(x: mx, y: my, w: mw, h: mh, color: activeTheme:menuBg);
		if({ linePx > 0 }, {
			ctx:strokeRect(x: mx, y: my, w: mw, h: mh, color: activeTheme:menuBorder, thickness: linePx);
		});

		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is padX: activeScale:px(pt: activeTheme:paddingMediumPt);
		local Boolean is hasInd: :hasIndicators();
		local Int is indW: if({ hasInd }, { activeScale:px(pt: activeTheme:iconSizePt + activeTheme:paddingPt) }, { 0 });
		local Int is iconSz: activeScale:px(pt: 12.0);
		if({ iconSz < 10 }, { iconSz: 10; });
		local Int is i: 0;
		while({ i < items:length() }, {
			local MenuItemConfig is item: items:get(index: i);
			local Int is iy: my + i * ih;
			if({ hoverIdx == i && item:enabled }, {
				ctx:fillRect(x: mx + 1, y: iy + 1, w: mw - 2, h: ih - 2, color: activeTheme:hoverBg);
			});
			local Int is ty: iy + (ih - th) / 2;
			local Int is txtColor: if({ item:enabled }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			if({ hasInd }, {
				local Int is icoY: iy + (ih - iconSz) / 2;
				if({ item:iconSvg != '' }, {
					SvgRenderer:shared:draw(ctx: ctx, svgSrc: item:iconSvg, x: mx + padX, y: icoY, widthPx: iconSz, heightPx: iconSz, tintColor: txtColor, useTint: true);
				}, {
					if({ item:kind == 'radio' }, {
						local String is rSvg: if({ item:checked }, { radioOnIconSvg }, { radioOffIconSvg });
						if({ rSvg != '' }, {
							SvgRenderer:shared:draw(ctx: ctx, svgSrc: rSvg, x: mx + padX, y: icoY, widthPx: iconSz, heightPx: iconSz, tintColor: txtColor, useTint: true);
						});
					}, {
						if({ item:kind == 'toggle' && item:checked && checkboxOnIconSvg != '' }, {
							SvgRenderer:shared:draw(ctx: ctx, svgSrc: checkboxOnIconSvg, x: mx + padX, y: icoY, widthPx: iconSz, heightPx: iconSz, tintColor: txtColor, useTint: true);
						});
					});
				});
			});
			ctx:drawText(x: mx + padX + indW, y: ty, text: item:label, color: txtColor, pixelHeight: fpx);
			i: i + 1;
		});
	}
}
