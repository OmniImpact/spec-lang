#! Package base:compress
#! IEEE 802.3 CRC-32 (Gzip/PNG/ZIP) and Adler-32 (Zlib) checksums.

Class is Crc32{
	replace [String] is namespace: ['base', 'compress'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Computes the IEEE 802.3 CRC-32 checksum over byte array [data] (`0..255`).
	Function of Int is crc32(Array of Int is data){
		local Int is crc: 4294967295;
		local Int is n: data:length();
		local Int is i: 0;
		while({ i < n }, {
			crc: (crc ^ (data:get(index: i, default: 0) & 255)) & 4294967295;
			local Int is b: 0;
			while({ b < 8 }, {
				if({ (crc & 1) != 0 }, {
					crc: ((crc >> 1) ^ 3988292384) & 4294967295;
				}, {
					crc: (crc >> 1) & 4294967295;
				});
				b: b + 1;
			});
			i: i + 1;
		});
		return (crc ^ 4294967295) & 4294967295;
	}

	## Computes the RFC 1950 Adler-32 checksum over byte array [data] (`0..255`).
	Function of Int is adler32(Array of Int is data){
		local Int is a: 1;
		local Int is b: 0;
		local Int is n: data:length();
		local Int is i: 0;
		while({ i < n }, {
			a: (a + (data:get(index: i, default: 0) & 255)) % 65521;
			b: (b + a) % 65521;
			i: i + 1;
		});
		return ((b << 16) | a) & 4294967295;
	}
}
