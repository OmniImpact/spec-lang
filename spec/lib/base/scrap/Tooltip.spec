#! Package base:scrap
#! Shared 80%-opaque tooltip renderer for `Dialog` and `ToolkitContainer` overlays.

Class is Tooltip{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', Scale],
		['base', 'fabric', Color],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	held Tooltip is shared: Tooltip();

	Function is paint(
		DrawContext is ctx,
		Theme is theme,
		Scale is scale,
		String is text,
		Int is ptrX,
		Int is ptrY,
		Int is winW,
		Int is winH
	){
		if({ text == '' || winW <= 0 || winH <= 0 }, { return; });
		local Int is fpx: scale:px(pt: theme:scaledTextPt(defaultPt: 13.0));
		if({ fpx < 10 }, { fpx: 10; });
		local Int is padX: scale:px(pt: theme:paddingPt);
		local Int is padY: scale:px(pt: theme:paddingSmallPt);
		if({ padX < 4 }, { padX: 4; });
		if({ padY < 2 }, { padY: 2; });
		local Int is tw: ctx:measureTextWidth(text: text, pixelHeight: fpx);
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is boxW: tw + padX * 2;
		local Int is boxH: th + padY * 2;
		local Int is tx: ptrX + scale:px(pt: 12.0);
		local Int is ty: ptrY + scale:px(pt: 18.0);
		if({ tx + boxW > winW - 2 }, { tx: winW - boxW - 2; });
		if({ ty + boxH > winH - 2 }, { ty: ptrY - boxH - scale:px(pt: 6.0); });
		if({ tx < 2 }, { tx: 2; });
		if({ ty < 2 }, { ty: 2; });
		local Int is bg: Color:fromArgb(argb: theme:menuBg):withAlphaByte(a: 204):toArgb();
		local Int is border: Color:fromArgb(argb: theme:panelBorder):withAlphaByte(a: 204):toArgb();
		local Int is bw: theme:borderPx(scaleFactor: scale:factor);
		ctx:fillRect(x: tx, y: ty, w: boxW, h: boxH, color: bg);
		if({ bw > 0 }, {
			ctx:strokeRect(x: tx, y: ty, w: boxW, h: boxH, color: border, thickness: bw);
		});
		ctx:drawText(x: tx + padX, y: ty + padY, text: text, color: theme:textPrimary, pixelHeight: fpx);
	}
}
