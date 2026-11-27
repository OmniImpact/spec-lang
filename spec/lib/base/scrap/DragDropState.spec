#! Package base:scrap
#! Shared mouse-follow and draggable/droppable coordination state rendered above the widget tree.

Class is DragDropState{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', Scale],
		['base', 'fabric', Color],
		['base', 'fabric', Theme],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext]
	];

	held DragDropState is shared: DragDropState();

	Boolean is active: false;
	String is payload: '';
	String is label: '';
	Int is ptrX: -1;
	Int is ptrY: -1;
	Boolean is dropAccepted: false;
	Function is activeDropHandler: local Function(String is _payload){};

	Function is beginDrag(String is payload, String is label, Int is x, Int is y){
		:active: true;
		:payload: payload;
		:label: label;
		:ptrX: x;
		:ptrY: y;
		:dropAccepted: false;
		:activeDropHandler: local Function(String is _payload){};
	}

	Function is setDropTarget(Boolean is accepted, Function is handler){
		:dropAccepted: accepted;
		:activeDropHandler: handler;
	}

	Function is updatePointer(Int is x, Int is y){
		:ptrX: x;
		:ptrY: y;
		:dropAccepted: false;
		:activeDropHandler: local Function(String is _payload){};
	}

	Function is finishDrag(){
		if({ active && dropAccepted }, {
			local Function is cb: activeDropHandler;
			cb(payload);
		});
		:active: false;
		:payload: '';
		:label: '';
		:dropAccepted: false;
		:activeDropHandler: local Function(String is _payload){};
	}

	Function is paintOverlay(DrawContext is ctx, Theme is theme, Scale is scale, Int is winW, Int is winH){
		if({ !active || label == '' || ptrX < 0 || ptrY < 0 }, { return; });
		local Int is fpx: scale:px(pt: theme:scaledTextPt(defaultPt: 13.0));
		if({ fpx < 10 }, { fpx: 10; });
		local Int is padX: scale:px(pt: theme:paddingLargePt);
		local Int is padY: scale:px(pt: theme:paddingSmallPt);
		local Int is tw: ctx:measureTextWidth(text: label, pixelHeight: fpx);
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is bw: tw + padX * 2;
		local Int is bh: th + padY * 2;
		local Int is gx: ptrX + scale:px(pt: 12.0);
		local Int is gy: ptrY + scale:px(pt: 12.0);
		if({ winW > 0 && gx + bw > winW - 2 }, { gx: winW - bw - 2; });
		if({ winH > 0 && gy + bh > winH - 2 }, { gy: winH - bh - 2; });
		if({ gx < 2 }, { gx: 2; });
		if({ gy < 2 }, { gy: 2; });
		local Int is btnPx: theme:buttonBorderPx(scaleFactor: scale:factor);
		local Int is radPx: scale:px(pt: theme:buttonCornerRadiusPt);
		local Int is borderCol: if({ dropAccepted }, { theme:positive:toArgb() }, { theme:textAccent });
		ctx:drawStyledBoxFill(
			x: gx, y: gy, w: bw, h: bh,
			fill: theme:resolveButtonFill(enabled: true, selected: true, hovered: false),
			borderColor: borderCol, thickness: if({ btnPx > 0 }, { btnPx }, { 1 }),
			radius: radPx, style: theme:buttonBorderStyle
		);
		ctx:drawText(x: gx + padX, y: gy + padY, text: label, color: theme:textPrimary, pixelHeight: fpx);
	}
}
