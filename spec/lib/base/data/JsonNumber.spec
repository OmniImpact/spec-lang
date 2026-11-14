#! Package base:data
#! Representation of JSON numeric value (integer or float).

Class is JsonNumber{
	namespace: ['base', 'data'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Buf()]
	];

	local String is raw: '0';
	local Boolean is isFloat: false;

	replace Function is init(String is rawText, Boolean is isFloating){
		self:raw: rawText;
		self:isFloat: isFloating;
	}

	replace Function of String is toString(){
		return self:raw;
	}

	Function of Int is toInt(Int is default: 0){
		return self:raw:parseInt(base: 10, default: default);
	}

	Function of Float is toFloat(Float is default: 0.0){
		local String is text: self:raw;
		local Int is len: text:length();
		if({ len == 0 }, {
			return default;
		});
		local Boolean is neg: false;
		local Int is pos: 0;
		if({ Buf:bufGetByte(b: text, idx: 0, def: -1) == 45 }, {
			neg: true;
			pos: 1;
		});
		local Float is intVal: 0.0;
		while({ pos < len && Buf:bufGetByte(b: text, idx: pos, def: -1) >= 48 && Buf:bufGetByte(b: text, idx: pos, def: -1) <= 57 }, {
			intVal: (intVal * 10.0) + ((Buf:bufGetByte(b: text, idx: pos, def: -1) - 48) as Float);
			pos: pos + 1;
		});
		if({ pos < len && Buf:bufGetByte(b: text, idx: pos, def: -1) == 46 }, {
			pos: pos + 1;
			local Float is div: 10.0;
			while({ pos < len && Buf:bufGetByte(b: text, idx: pos, def: -1) >= 48 && Buf:bufGetByte(b: text, idx: pos, def: -1) <= 57 }, {
				intVal: intVal + (((Buf:bufGetByte(b: text, idx: pos, def: -1) - 48) as Float) / div);
				div: div * 10.0;
				pos: pos + 1;
			});
		});
		if({ pos < len && (Buf:bufGetByte(b: text, idx: pos, def: -1) == 101 || Buf:bufGetByte(b: text, idx: pos, def: -1) == 69) }, {
			pos: pos + 1;
			local Boolean is expNeg: false;
			if({ pos < len && Buf:bufGetByte(b: text, idx: pos, def: -1) == 43 }, {
				pos: pos + 1;
			}, {
				if({ pos < len && Buf:bufGetByte(b: text, idx: pos, def: -1) == 45 }, {
					expNeg: true;
					pos: pos + 1;
				});
			});
			local Int is expVal: 0;
			while({ pos < len && Buf:bufGetByte(b: text, idx: pos, def: -1) >= 48 && Buf:bufGetByte(b: text, idx: pos, def: -1) <= 57 }, {
				expVal: (expVal * 10) + (Buf:bufGetByte(b: text, idx: pos, def: -1) - 48);
				pos: pos + 1;
			});
			local Int is ei: 0;
			while({ ei < expVal }, {
				if({ expNeg }, {
					intVal: intVal / 10.0;
				}, {
					intVal: intVal * 10.0;
				});
				ei: ei + 1;
			});
		});
		if({ neg }, {
			return -intVal;
		});
		return intVal;
	}

	Function of Boolean is isFloating(){
		return self:isFloat;
	}
}
