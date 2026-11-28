#! Package base:compress
#! RFC 1952 Gzip and RFC 1950 Zlib compression/decompression wrappers over `Deflate` and `Crc32`.

Class is Gzip{
	replace [String] is namespace: ['base', 'compress'];

	replace [[String]] is using: [
		['base', 'compress', as Crc32()],
		['base', 'compress', Deflate],
		['base', 'struct', Array],
		['base', 'struct', List],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Array of Int is strToBytes(String is text){
		local Array of Int is out: Array();
		local Int is i: 0;
		while({ i < text:byteLength() }, {
			out:add(item: text:byteAt(index: i, default: 0));
			i: i + 1;
		});
		return out;
	}

	local Function of String is bytesToStr(Array of Int is bytes){
		local [Byte] is b;
		local Int is i: 0;
		while({ i < bytes:length() }, {
			b:push((bytes:get(index: i, default: 0) & 255) as Byte);
			i: i + 1;
		});
		return b:toString();
	}

	## Compresses [data] into RFC 1952 Gzip format (compatible with `gzip`, `zlib`, browsers).
	Function of Array of Int is compress(Array of Int is data){
		local Deflate is def: Deflate:init();
		local Array of Int is body: def:compress(data: data);
		local Int is crc: Crc32:crc32(data: data);
		local Int is isize: data:length() & 4294967295;
		local Array of Int is out: Array([31, 139, 8, 0, 0, 0, 0, 0, 0, 255]);
		local Int is i: 0;
		while({ i < body:length() }, { out:add(item: body:get(index: i, default: 0)); i: i + 1; });
		out:add(item: crc & 255);
		out:add(item: (crc >> 8) & 255);
		out:add(item: (crc >> 16) & 255);
		out:add(item: (crc >> 24) & 255);
		out:add(item: isize & 255);
		out:add(item: (isize >> 8) & 255);
		out:add(item: (isize >> 16) & 255);
		out:add(item: (isize >> 24) & 255);
		return out;
	}

	## Decompresses an RFC 1952 Gzip stream [data]; returns empty Array on invalid header/CRC.
	Function of Array of Int is decompress(Array of Int is data){
		local Int is n: data:length();
		if({ n < 18 || data:get(index: 0, default: 0) != 31 || data:get(index: 1, default: 0) != 139 || data:get(index: 2, default: 0) != 8 }, {
			return Array();
		});
		local Int is flg: data:get(index: 3, default: 0);
		local Int is pos: 10;
		if({ (flg & 4) != 0 && pos + 2 <= n }, {
			local Int is xlen: data:get(index: pos, default: 0) | (data:get(index: pos + 1, default: 0) << 8);
			pos: pos + 2 + xlen;
		});
		if({ (flg & 8) != 0 }, {
			while({ pos < n && data:get(index: pos, default: 0) != 0 }, { pos: pos + 1; });
			pos: pos + 1;
		});
		if({ (flg & 16) != 0 }, {
			while({ pos < n && data:get(index: pos, default: 0) != 0 }, { pos: pos + 1; });
			pos: pos + 1;
		});
		if({ (flg & 2) != 0 }, { pos: pos + 2; });
		if({ pos > n - 8 }, { return Array(); });

		local Array of Int is deflatePayload: Array();
		local Int is i: pos;
		while({ i < n - 8 }, {
			deflatePayload:add(item: data:get(index: i, default: 0));
			i: i + 1;
		});
		local Deflate is def: Deflate:init();
		local Array of Int is plain: def:decompress(data: deflatePayload);

		local Int is wantCrc: data:get(index: n - 8, default: 0) | (data:get(index: n - 7, default: 0) << 8) | (data:get(index: n - 6, default: 0) << 16) | (data:get(index: n - 5, default: 0) << 24);
		if({ Crc32:crc32(data: plain) != wantCrc }, { return Array(); });
		return plain;
	}

	## Compresses [data] into RFC 1950 Zlib format (`0x78 0x9C` + DEFLATE + Adler-32).
	Function of Array of Int is zlibCompress(Array of Int is data){
		local Deflate is def: Deflate:init();
		local Array of Int is body: def:compress(data: data);
		local Int is adler: Crc32:adler32(data: data);
		local Array of Int is out: Array([120, 156]);
		local Int is i: 0;
		while({ i < body:length() }, { out:add(item: body:get(index: i, default: 0)); i: i + 1; });
		out:add(item: (adler >> 24) & 255);
		out:add(item: (adler >> 16) & 255);
		out:add(item: (adler >> 8) & 255);
		out:add(item: adler & 255);
		return out;
	}

	## Decompresses an RFC 1950 Zlib stream [data]; returns empty Array on invalid header/Adler-32.
	Function of Array of Int is zlibDecompress(Array of Int is data){
		local Int is n: data:length();
		if({ n < 6 }, { return Array(); });
		local Int is cmf: data:get(index: 0, default: 0);
		local Int is flg: data:get(index: 1, default: 0);
		if({ (cmf & 15) != 8 || (((cmf << 8) | flg) % 31) != 0 }, { return Array(); });
		local Int is start: if({ (flg & 32) != 0 }, { 6 }, { 2 });
		if({ start > n - 4 }, { return Array(); });
		local Array of Int is payload: Array();
		local Int is i: start;
		while({ i < n - 4 }, { payload:add(item: data:get(index: i, default: 0)); i: i + 1; });
		local Deflate is def: Deflate:init();
		local Array of Int is plain: def:decompress(data: payload);
		local Int is wantAdler: (data:get(index: n - 4, default: 0) << 24) | (data:get(index: n - 3, default: 0) << 16) | (data:get(index: n - 2, default: 0) << 8) | data:get(index: n - 1, default: 0);
		if({ Crc32:adler32(data: plain) != wantAdler }, { return Array(); });
		return plain;
	}

	Function of Array of Int is compressString(String is text){
		return :compress(data: :strToBytes(text: text));
	}

	Function of String is decompressString(Array of Int is data){
		return :bytesToStr(bytes: :decompress(data: data));
	}
}
