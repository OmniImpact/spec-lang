#! specunit: suite

Class of SpecUnitTest is TestCompression{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'struct', Array],
		['base', 'compress', as Crc32()],
		['base', 'compress', as Gzip()]
	];

	Function is testCrc32AndAdler32Vectors(){
		# Standard CRC-32("123456789") = 0xCBF43926 = 3421780262
		local Array of Int is digits: Array([49, 50, 51, 52, 53, 54, 55, 56, 57]);
		Assert:areEqualInt(3421780262, Crc32:crc32(data: digits));

		# Standard Adler-32("Wikipedia") = 0x11E60398 = 300286872
		local Array of Int is wiki: Array([87, 105, 107, 105, 112, 101, 100, 105, 97]);
		Assert:areEqualInt(300286872, Crc32:adler32(data: wiki));
	}

	Function is testGzipAndZlibRoundTripAndCompression(){
		local String is text: 'The quick brown fox jumps over the lazy dog. ';
		local String is big: '';
		local Int is i: 0;
		while({ i < 20 }, {
			big: big . text;
			i: i + 1;
		});
		local Array of Int is gz: Gzip:compressString(text: big);
		# 900 bytes of repetitive text must compress well below 200 bytes
		Assert:isTrue(gz:length() < 200);
		Assert:areEqualString(big, Gzip:decompressString(data: gz));

		# Zlib round-trip
		local Array of Int is raw: Array();
		i: 0;
		while({ i < big:byteLength() }, { raw:add(item: big:byteAt(index: i, default: 0)); i: i + 1; });
		local Array of Int is zl: Gzip:zlibCompress(data: raw);
		Assert:isTrue(zl:length() < 190);
		local Array of Int is zlPlain: Gzip:zlibDecompress(data: zl);
		Assert:areEqualInt(raw:length(), zlPlain:length());
		Assert:areEqualInt(raw:get(index: 0, default: 0), zlPlain:get(index: 0, default: 0));
		Assert:areEqualInt(raw:get(index: raw:length() - 1, default: 0), zlPlain:get(index: zlPlain:length() - 1, default: 0));

		# Empty round-trip
		local Array of Int is gzEmpty: Gzip:compressString(text: '');
		Assert:areEqualString('', Gzip:decompressString(data: gzEmpty));
	}

	Function is testExternalDynamicHuffmanGzipInterop(){
		# External Python gzip.compress(..., compresslevel=9) vector using BTYPE=10 (Dynamic Huffman)
		local Array of Int is extGz: Array([
			31, 139, 8, 0, 0, 0, 0, 0, 2, 255, 237, 78, 91, 10, 195, 48, 12, 187, 138, 118, 131, 61, 187, 237, 56, 106, 27, 18, 179, 184, 49, 109,
			2, 163, 167, 159, 3, 251, 217, 29, 246, 33, 97, 33, 89, 136, 217, 18, 49, 134, 74, 68, 170, 18, 115, 200, 126, 7, 219, 36, 151, 5, 123, 55,
			58, 106, 234, 44, 197, 233, 69, 51, 34, 83, 199, 153, 208, 134, 165, 225, 45, 40, 42, 211, 234, 31, 38, 88, 83, 193, 38, 209, 203, 42, 27, 218,
			183, 202, 146, 96, 114, 184, 244, 112, 136, 196, 241, 116, 190, 92, 111, 195, 253, 241, 60, 128, 255, 29, 63, 59, 62, 48, 70, 241, 84, 152, 1, 0, 0
		]);
		local String is unit: 'alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega 0123456789! ';
		local String is expected: unit . unit . unit;
		Assert:areEqualString(expected, Gzip:decompressString(data: extGz));
	}
}
