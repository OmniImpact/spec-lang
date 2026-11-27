#! Package base:scrap
#! Simple filled rectangular surface widget participating in Sew layout, Theme propagation, and optional custom [onPaint].

Class of SewNode is ScrapPanel{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	Int is bgColor: -1;
	Boolean is useThemeBg: true;
	Float is minWidthPt: 0.0;
	Float is minHeightPt: 0.0;
	Float is heightPt: 0.0;
	Function is onPaint: local Function(DrawContext is _ctx, Int is _x, Int is _y, Int is _w, Int is _h){};

	replace Function is init(
		Int is bgColor: 0,
		Boolean is useThemeBg: true,
		Float is minWidthPt: 0.0,
		Float is minHeightPt: 0.0,
		Float is heightPt: 0.0,
		Function is onPaint: local Function(DrawContext is _ctx, Int is _x, Int is _y, Int is _w, Int is _h){}
	){
		:bgColor: bgColor;
		:useThemeBg: useThemeBg;
		:minWidthPt: minWidthPt;
		:minHeightPt: minHeightPt;
		:heightPt: heightPt;
		:onPaint: onPaint;
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		if({ useThemeBg }, {
			:bgColor: theme:windowBg;
		});
	}

	replace Function of Size is measure(Constraints is c){
		local Int is minW: activeScale:px(pt: minWidthPt);
		local Int is w: if({ c:maxW >= 100000 }, { minW }, { c:maxW });
		if({ minW > w }, { w: minW; });
		local Int is minH: activeScale:px(pt: minHeightPt);
		local Int is h: if({ heightPt > 0.0 }, {
			c:clampH(h: activeScale:px(pt: heightPt))
		}, {
			if({ minH > 0 }, { c:clampH(h: minH) }, {
				if({ c:maxH >= 100000 }, { activeScale:px(pt: activeTheme:panelMinSizePt) }, { c:maxH })
			})
		});
		desiredSize: Size(width: c:clampW(w: w), height: h);
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: bgColor);
		local Function is cb: onPaint;
		cb(ctx, b:x, b:y, b:width, b:height);
	}
}
