#! Package base:scrap
#! Animated circular spinner widget supporting indeterminate rotation and determinate progress.

Class of SewNode is Spinner{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Math()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	Float is sizePt: 24.0;
	Boolean is indeterminate: true;
	Float is progress: 0.0;
	String is label: '';

	Int is activeDot: 0;
	Int is accumMs: 0;
	Int is lastTickMs: 0;

	replace Function is init(
		Float is sizePt: 24.0,
		Boolean is indeterminate: true,
		Float is progress: 0.0,
		String is label: '',
		String is tooltip: ''
	){
		:sizePt: sizePt;
		:indeterminate: indeterminate;
		:progress: progress;
		:label: label;
		:tooltip: tooltip;
	}

	Function is setProgress(Float is next){
		local Float is p: next;
		if({ p < 0.0 }, { p: 0.0; });
		if({ p > 1.0 }, { p: 1.0; });
		:progress: p;
		:invalidate();
	}

	replace Function of Boolean is tick(Int is nowMs){
		if({ !indeterminate }, { return false; });
		if({ lastTickMs > 0 }, {
			local Int is dt: nowMs - lastTickMs;
			if({ dt > 0 && dt < 500 }, {
				:accumMs: accumMs + dt;
				if({ accumMs >= 85 }, {
					:accumMs: accumMs - 85;
					:activeDot: (activeDot + 1) % 8;
					:lastTickMs: nowMs;
					:invalidate();
					return true;
				});
			});
		});
		:lastTickMs: nowMs;
		return false;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is sz: activeScale:px(pt: sizePt);
		if({ sz < 14 }, { sz: 14; });
		local Int is w: sz;
		if({ label != '' }, {
			local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt);
			local Int is gap: activeScale:px(pt: activeTheme:paddingSmallPt);
			w: w + gap + (label:length() * fpx * 6) / 10;
		});
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: sz));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is sz: activeScale:px(pt: sizePt);
		if({ sz < 14 }, { sz: 14; });
		local Int is cx: b:x + sz / 2;
		local Int is cy: b:y + b:height / 2;
		local Int is ringR: (sz * 34) / 100;
		if({ ringR < 4 }, { ringR: 4; });
		local Int is dotR: (sz * 10) / 100;
		if({ dotR < 2 }, { dotR: 2; });

		# 8 cardinal/diagonal offsets scaled by 1000: (0,-1000), (707,-707), (1000,0), (707,707), (0,1000), (-707,707), (-1000,0), (-707,-707)
		local Int is diag: (ringR * 707) / 1000;
		local Int is nDots: 8;
		local Int is litCount: if({ indeterminate }, { 3 }, { math:toInt(value: math:round(value: progress * 8.0)) });
		local Int is i: 0;
		while({ i < nDots }, {
			local Int is dx: 0;
			local Int is dy: 0;
			if({ i == 0 }, { dx: 0; dy: 0 - ringR; });
			if({ i == 1 }, { dx: diag; dy: 0 - diag; });
			if({ i == 2 }, { dx: ringR; dy: 0; });
			if({ i == 3 }, { dx: diag; dy: diag; });
			if({ i == 4 }, { dx: 0; dy: ringR; });
			if({ i == 5 }, { dx: 0 - diag; dy: diag; });
			if({ i == 6 }, { dx: 0 - ringR; dy: 0; });
			if({ i == 7 }, { dx: 0 - diag; dy: 0 - diag; });

			local Boolean is lit: false;
			if({ indeterminate }, {
				local Int is dist: (i - activeDot + 8) % 8;
				lit: dist < 3;
			}, {
				lit: i < litCount;
			});
			local Int is col: if({ lit }, { activeTheme:textAccent }, { activeTheme:dividerColorArgb() });
			ctx:fillCircle(cx: cx + dx, cy: cy + dy, r: dotR, color: col);
			i: i + 1;
		});

		if({ label != '' }, {
			local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt);
			local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
			local Int is gap: activeScale:px(pt: activeTheme:paddingSmallPt);
			ctx:drawText(
				x: b:x + sz + gap,
				y: b:y + (b:height - th) / 2,
				text: label,
				color: activeTheme:textSecondary,
				pixelHeight: fpx
			);
		});
	}
}
