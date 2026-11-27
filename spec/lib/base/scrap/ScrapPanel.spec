#! Package base:scrap
#! Simple filled rectangular surface widget participating in Sew layout and Theme propagation.

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
	Float is heightPt: 0.0;

	replace Function is init(Int is bgColor: 0, Boolean is useThemeBg: true, Float is heightPt: 0.0){
		:bgColor: bgColor;
		:useThemeBg: useThemeBg;
		:heightPt: heightPt;
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		if({ useThemeBg }, {
			:bgColor: theme:windowBg;
		});
	}

	replace Function of Size is measure(Constraints is c){
		local Int is h: if({ heightPt > 0.0 }, {
			c:clampH(h: activeScale:px(pt: heightPt))
		}, {
			if({ c:maxH >= 100000 }, { activeScale:px(pt: activeTheme:panelMinSizePt) }, { c:maxH })
		});
		desiredSize: Size(width: c:maxW, height: h);
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: bgColor);
	}
}
