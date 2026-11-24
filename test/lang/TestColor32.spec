#! specunit: suite

Class of SpecUnitTest is TestColor32{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'struct', List],
		['base', 'theo', [Color32, TheoBuffer, TheoCell]]
	];

	Function is testPackUnpackAndAvg4(){
		local Int is c: Color32:pack(r: 100, g: 150, b: 200);
		Assert:areEqualInt(100, Color32:red(color: c));
		Assert:areEqualInt(150, Color32:green(color: c));
		Assert:areEqualInt(200, Color32:blue(color: c));
		Assert:areEqualInt(255, Color32:alpha(color: c));

		local Int is c2: Color32:pack(r: 200, g: 50, b: 100);
		local Int is avg: Color32:avg4(c00: c, c10: c2, c01: c, c11: c2);
		Assert:areEqualInt(150, Color32:red(color: avg));
		Assert:areEqualInt(100, Color32:green(color: avg));
		Assert:areEqualInt(150, Color32:blue(color: avg));
	}

	Function is testByteListRgbAndU32(){
		local List of Byte is buf: List(byteMode: true);
		buf:pushRgb(r: 12, g: 34, b: 56);
		Assert:areEqualInt(3, buf:length());
		buf:pushU32LE(v: 305419896);
		Assert:areEqualInt(305419896, buf:readU32LE(offset: 3));
		buf:setU32LE(offset: 3, v: 42);
		Assert:areEqualInt(42, buf:readU32LE(offset: 3));
	}

	Function is testTheoBufferSetCellRgb(){
		local TheoBuffer is buf: TheoBuffer(width: 4, height: 2);
		local Int is fg: Color32:pack(r: 10, g: 20, b: 30);
		local Int is bg: Color32:pack(r: 40, g: 50, b: 60);
		buf:setCellRgb(x: 1, y: 1, ch: '▀', fgRgb: fg, bgRgb: bg);
		local TheoCell is cell: buf:cellAt(x: 1, y: 1);
		Assert:areEqualString('▀', cell:ch);
		Assert:areEqualInt(2, cell:fg:kind);
		Assert:areEqualInt(10, cell:fg:c1);
		Assert:areEqualInt(20, cell:fg:c2);
		Assert:areEqualInt(30, cell:fg:c3);
		Assert:areEqualInt(40, cell:bg:c1);
		Assert:areEqualInt(50, cell:bg:c2);
		Assert:areEqualInt(60, cell:bg:c3);
	}
}
