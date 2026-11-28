#! Package base:math:crypto
#! Base64 and PEM block decoder for X.509 certificates and PKCS#8 Ed25519 private keys.

Class is Pem{
	replace [String] is namespace: ['base', 'math', 'crypto'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Function of Int is b64Val(Int is ch){
		if({ ch >= 65 && ch <= 90 }, { return ch - 65; });
		if({ ch >= 97 && ch <= 122 }, { return ch - 97 + 26; });
		if({ ch >= 48 && ch <= 57 }, { return ch - 48 + 52; });
		if({ ch == 43 }, { return 62; });
		if({ ch == 47 }, { return 63; });
		return -1;
	}

	## Encodes raw bytes (`0..255`) into standard Base64 text.
	Function of String is base64Encode(Array of Int is data){
		local String is alpha: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
		local String is out: '';
		local Int is n: data:length();
		local Int is i: 0;
		while({ i < n }, {
			local Int is b0: data:get(index: i, default: 0) & 255;
			local Boolean is has1: (i + 1) < n;
			local Boolean is has2: (i + 2) < n;
			local Int is b1: if({ has1 }, { data:get(index: i + 1, default: 0) & 255 }, { 0 });
			local Int is b2: if({ has2 }, { data:get(index: i + 2, default: 0) & 255 }, { 0 });
			local Int is triple: (b0 << 16) | (b1 << 8) | b2;
			local Int is c0: (triple >> 18) & 63;
			local Int is c1: (triple >> 12) & 63;
			local Int is c2: (triple >> 6) & 63;
			local Int is c3: triple & 63;
			out: out . alpha:substring(start: c0, end: c0 + 1) . alpha:substring(start: c1, end: c1 + 1);
			out: out . if({ has1 }, { alpha:substring(start: c2, end: c2 + 1) }, { '=' });
			out: out . if({ has2 }, { alpha:substring(start: c3, end: c3 + 1) }, { '=' });
			i: i + 3;
		});
		return out;
	}

	## Decodes standard Base64 text (ignoring whitespace) into raw byte values (`0..255`).
	Function of Array of Int is base64Decode(String is text){
		local Array of Int is out: Array();
		local Int is n: text:byteLength();
		local Int is acc: 0;
		local Int is bits: 0;
		local Int is i: 0;
		while({ i < n }, {
			local Int is ch: text:byteAt(index: i, default: 0);
			if({ ch == 61 }, {
				i: n;
			}, {
				local Int is v: :b64Val(ch: ch);
				if({ v >= 0 }, {
					acc: (acc << 6) | v;
					bits: bits + 6;
					if({ bits >= 8 }, {
						bits: bits - 8;
						out:add(item: (acc >> bits) & 255);
					});
				});
				i: i + 1;
			});
		});
		return out;
	}

	## Extracts all PEM blocks matching `-----BEGIN [label]-----` ... `-----END [label]-----`
	## and returns each block's decoded DER bytes.
	Function of Array of Array of Int is decodeBlocks(String is pemText, String is label){
		local Array of Array of Int is blocks: Array();
		local String is beginMark: '-----BEGIN ' . label . '-----';
		local String is endMark: '-----END ' . label . '-----';
		local Int is pos: 0;
		local Int is n: pemText:length();
		while({ pos < n }, {
			local Int is bIdx: pemText:indexOfFrom(search: beginMark, from: pos, default: -1);
			if({ bIdx < 0 }, { return blocks; });
			local Int is bodyStart: bIdx + beginMark:length();
			local Int is eIdx: pemText:indexOfFrom(search: endMark, from: bodyStart, default: -1);
			if({ eIdx < 0 }, { return blocks; });
			local String is b64: pemText:substring(start: bodyStart, end: eIdx);
			blocks:add(item: :base64Decode(text: b64));
			pos: eIdx + endMark:length();
		});
		return blocks;
	}

	## Extracts a 32-byte Ed25519 private key seed from a PKCS#8 DER or PEM key
	## (OID 1.3.101.112 -> ends with 0x04 0x20 <32-byte seed>). Returns empty Array on error.
	Function of Array of Int is extractEd25519Seed(Array of Int is der){
		local Int is n: der:length();
		if({ n == 32 }, { return der; });
		if({ n < 34 }, { return Array(); });
		# Scan for inner OCTET STRING header 0x04 0x20 followed by 32 bytes at the end
		local Int is start: n - 34;
		if({ der:get(index: start, default: 0) == 4 && der:get(index: start + 1, default: 0) == 32 }, {
			local Array of Int is seed: Array();
			local Int is i: 0;
			while({ i < 32 }, {
				seed:add(item: der:get(index: start + 2 + i, default: 0) & 255);
				i: i + 1;
			});
			return seed;
		});
		return Array();
	}
}
