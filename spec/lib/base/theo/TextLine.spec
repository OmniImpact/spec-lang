#! Package base:theo
#! Single-line text widget accepting either a static [String] or dynamic [TextEmitter].

Class of Widget is TextLine{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', Widget],
		['base', 'theo', TheoColor],
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'signal', TextEmitter],
		['base', 'signal', TextCollector],
		['base', 'sys', as Conditional()]
	];

	String is textValue: '';
	TheoColor is color: TheoColor:none();
	Boolean is bold: false;
	Array of TextEmitter is boundEmitters: [];
	Array of TextCollector is boundCollectors: [];

	replace Function is init(Any is value: '', TheoColor is color: TheoColor:none(), Boolean is bold: false){
		:color: color;
		:bold: bold;
		:boundEmitters: [];
		:boundCollectors: [];
		if({ value:typeName() == 'TextEmitter' }, {
			local TextEmitter is em: value as TextEmitter;
			:textValue: em:current();
			:boundEmitters: [em];
			local TextCollector is col: em:collect(onEmit: local Function(String is next){
				:textValue: next;
				invalidate();
			});
			:boundCollectors: [col];
		}, {
			:textValue: value as String;
		});
	}

	replace Function of Int is measureWidth(Int is maxW){
		local Int is len: textValue:length();
		if({ len > maxW }, { return maxW; });
		return len;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		return 1;
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		buf:drawText(x: boxX, y: boxY, text: textValue, fg: color, bold: bold);
	}

	replace Function is dispose(){
		if({ boundEmitters:length() > 0 && boundCollectors:length() > 0 }, {
			boundEmitters:get(index: 0):detach(collector: boundCollectors:get(index: 0));
			:boundEmitters: [];
			:boundCollectors: [];
		});
	}
}
