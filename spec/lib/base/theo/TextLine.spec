#! Package base:theo
#! Single-line text widget accepting either a static [String] or dynamic [TextEmitter].

Class of Widget is TextLine{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, TheoColor, TheoBuffer, TheoRenderer]],
		['base', 'signal', [TextEmitter, TextCollector]],
		['base', 'sys', as Conditional()]
	];

	String is textValue: '';
	TheoColor is color: TheoColor:none();
	Boolean is bold: false;
	Int is width: 0;

	replace Function is init(String is value: '', TheoColor is color: TheoColor:none(), Boolean is bold: false, Int is width: 0){
		:color: color;
		:bold: bold;
		:width: width;
		:textValue: value;
	}

	replace Function is init(TextEmitter is value, TheoColor is color: TheoColor:none(), Boolean is bold: false, Int is width: 0){
		:color: color;
		:bold: bold;
		:width: width;
		:textValue: value:current();
		trackBinding(slot: 'value', emitter: value, collector: value:collect(onEmit: local Function(String is next){
			:textValue: next;
			invalidate();
		}));
	}

	replace Function of Int is measureWidth(Int is maxW){
		local Int is len: if({ width > 0 }, { width }, { textValue:length() });
		if({ len > maxW }, { return maxW; });
		return len;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ 1 }

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		local TheoColor is effColor: if({ color:isSet() }, { color }, { activeTheme:foreground });
		buf:drawText(x: boxX, y: boxY, text: textValue, fg: effColor, bold: bold);
	}
}
