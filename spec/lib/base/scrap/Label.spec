#! Package base:scrap
#! Text label widget participating in Sew layout and painting via Fabric.

Class of SewNode is Label{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'suit', SuitCanvas]
	];

	String is text: '';
	Theme is theme: Theme();
	Int is padding: 8;
	Int is scale: 2;
	Int is textColor: 0;
	Int is bgColor: 0;
	Int is borderColor: 0;

	replace Function is init(String is text: '', Int is padding: 8, Int is scale: 2){
		:text: text;
		:padding: padding;
		:scale: scale;
		theme: Theme();
		textColor: theme:textAccent;
		bgColor: theme:panelBg;
		borderColor: theme:panelBorder;
	}

	Function is setText(String is text){
		:text: text;
	}

	replace Function of Size is measure(Constraints is c){
		local DrawContext is dummy: DrawContext(canvas: SuitCanvas(width: 1, height: 1));
		local Int is tw: dummy:measureTextWidth(text: text, pixelHeight: scale * 7);
		local Int is th: dummy:measureTextHeight(pixelHeight: scale * 7);
		dummy:canvas:dispose();
		desiredSize: Size(
			width: c:clampW(w: tw + padding * 2),
			height: c:clampH(h: th + padding * 2)
		);
		return desiredSize;
	}

	## Paints the label panel, border, and text into [ctx] at its arranged `bounds()`.
	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: bgColor);
		ctx:strokeRect(x: b:x, y: b:y, w: b:width, h: b:height, color: borderColor);
		ctx:drawText(
			x: b:x + padding,
			y: b:y + padding,
			text: text,
			color: textColor,
			pixelHeight: scale * 7
		);
	}
}
