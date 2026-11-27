#! Package base:scrap
#! Mouse-follow container primitive (`SewNode`) that tracks pointer position inside its bounds and paints an optional follower badge.

Class of SingleChildNode is MouseFollow{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', SingleChildNode],
		['base', 'sew', Rect],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext]
	];

	String is badgeText: '';
	Boolean is showCrosshair: false;
	Function is onFollow: local Function(Int is _x, Int is _y){};

	Boolean is inside: false;
	Int is followX: -1;
	Int is followY: -1;

	replace Function is init(
		SewNode is child: SewNode(),
		String is badgeText: '',
		Boolean is showCrosshair: false,
		Function is onFollow: local Function(Int is _x, Int is _y){}
	){
		:child: child;
		:badgeText: badgeText;
		:showCrosshair: showCrosshair;
		:onFollow: onFollow;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		child:paint(ctx: ctx);
		if({ inside && followX >= b:x && followY >= b:y }, {
			if({ showCrosshair }, {
				local Int is linePx: activeTheme:linePx(scaleFactor: activeScale:factor);
				ctx:fillRect(x: followX, y: b:y, w: linePx, h: b:height, color: activeTheme:accentSubtle(alpha: 0.45));
				ctx:fillRect(x: b:x, y: followY, w: b:width, h: linePx, color: activeTheme:accentSubtle(alpha: 0.45));
			});
			if({ badgeText != '' }, {
				local Int is fpx: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 12.0));
				if({ fpx < 10 }, { fpx: 10; });
				local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
				local Int is padY: activeScale:px(pt: activeTheme:paddingSmallPt);
				local Int is tw: ctx:measureTextWidth(text: badgeText, pixelHeight: fpx);
				local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
				local Int is bw: tw + padX * 2;
				local Int is bh: th + padY * 2;
				local Int is bx: followX + activeScale:px(pt: 10.0);
				local Int is by: followY + activeScale:px(pt: 12.0);
				if({ bx + bw > b:x + b:width - 2 }, { bx: b:x + b:width - bw - 2; });
				if({ by + bh > b:y + b:height - 2 }, { by: followY - bh - activeScale:px(pt: 6.0); });
				if({ bx < b:x + 2 }, { bx: b:x + 2; });
				if({ by < b:y + 2 }, { by: b:y + 2; });
				local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
				local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
				ctx:drawStyledBoxFill(
					x: bx, y: by, w: bw, h: bh,
					fill: activeTheme:resolveButtonFill(enabled: true, selected: false, hovered: false),
					borderColor: activeTheme:panelBorderColorArgb(), thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
				);
				ctx:drawText(x: bx + padX, y: by + padY, text: badgeText, color: activeTheme:textPrimary, pixelHeight: fpx);
			});
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is over: :containsPoint(x: x, y: y);
		local Boolean is childChanged: child:onPointerMove(x: x, y: y);
		if({ over }, {
			local Boolean is moved: (!inside) || (followX != x) || (followY != y);
			:inside: true;
			:followX: x;
			:followY: y;
			if({ moved }, {
				local Function is cb: onFollow;
				cb(x - bounds():x, y - bounds():y);
				invalidate();
				return true;
			});
			return childChanged;
		});
		if({ inside }, {
			:inside: false;
			invalidate();
			return true;
		});
		return childChanged;
	}

	replace Function is clearHover(){
		if({ inside }, {
			:inside: false;
			invalidate();
		});
		child:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return child:onPointerClickMod(x: x, y: y, mods: mods);
	}
}
