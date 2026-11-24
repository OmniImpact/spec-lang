#! Package base:sys
#! Reads and packs binary asset bundles appended to Spec executables by `specbuild`.

Class is Bundle{
	replace [String] is namespace: ['base', 'sys'];

	merge [[String]] is using: [
		['base', 'struct', [Array, List, Map]],
		['base', 'sys', [as Dir(), as File()]]
	];

	local String is MAGIC: 'SPECBNDL';
	local Map of String to String is entries: Map();
	local Array of String is entryKeys: Array();
	local Boolean is loaded: false;

	replace Function is init(Boolean is autoLoad: true){
		if({ autoLoad }, {
			local String is exe: exePath();
			if({ exe != '' }, {
				loadFromFile(path: exe);
			});
		});
	}

	local Function of String is normalizeKey(String is rawPath){
		local String is p: rawPath:replaceAll(search: '\\', replacement: '/');
		while({ p:startsWith(prefix: './') }, {
			p: p:substring(start: 2, end: p:byteLength());
		});
		while({ p:startsWith(prefix: '/') }, {
			p: p:substring(start: 1, end: p:byteLength());
		});
		return p;
	}

	local Function is pushU32LE(List of Byte is buf, Int is val){
		local Int is v: val;
		local Int is i: 0;
		while({ i < 4 }, {
			buf:push(item: (v % 256) as Byte);
			v: v / 256;
			i: i + 1;
		});
	}

	local Function is pushU64LE(List of Byte is buf, Int is val){
		local Int is v: val;
		local Int is i: 0;
		while({ i < 8 }, {
			buf:push(item: (v % 256) as Byte);
			v: v / 256;
			i: i + 1;
		});
	}

	local Function of Int is readU32LE(String is raw, Int is offset){
		local Int is b0: raw:byteAt(index: offset, default: 0);
		local Int is b1: raw:byteAt(index: offset + 1, default: 0);
		local Int is b2: raw:byteAt(index: offset + 2, default: 0);
		local Int is b3: raw:byteAt(index: offset + 3, default: 0);
		return b0 + (b1 * 256) + (b2 * 65536) + (b3 * 16777216);
	}

	local Function of Int is readU64LE(String is raw, Int is offset){
		local Int is total: 0;
		local Int is mul: 1;
		local Int is i: 0;
		while({ i < 8 }, {
			local Int is b: raw:byteAt(index: offset + i, default: 0);
			total: total + (b * mul);
			mul: mul * 256;
			i: i + 1;
		});
		return total;
	}

	## Encodes [destPaths] and [payloads] into a binary bundle blob with the `SPECBNDL` trailer.
	Function of String is pack(Array of String is destPaths, Array of String is payloads){
		local List of Byte is body: List(byteMode: true);
		local Int is count: destPaths:length();
		if({ payloads:length() < count }, { count: payloads:length(); });
		pushU32LE(buf: body, val: count);
		local Int is i: 0;
		while({ i < count }, {
			local String is key: normalizeKey(rawPath: destPaths:get(index: i));
			local String is data: payloads:get(index: i);
			pushU32LE(buf: body, val: key:byteLength());
			body:appendString(value: key);
			pushU64LE(buf: body, val: data:byteLength());
			body:appendString(value: data);
			i: i + 1;
		});
		local String is bodyStr: body:toString();
		local List of Byte is out: List(byteMode: true);
		out:appendString(value: bodyStr);
		pushU64LE(buf: out, val: bodyStr:byteLength());
		out:appendString(value: MAGIC);
		return out:toString();
	}

	## Parses a bundle trailer and entry table from [raw] bytes; returns true if a valid bundle was found.
	Function of Boolean is loadFromBytes(String is raw){
		entries: Map();
		entryKeys: Array();
		loaded: false;
		local Int is totalLen: raw:byteLength();
		if({ totalLen < 16 }, { return false; });
		if({ raw:substring(start: totalLen - 8, end: totalLen) != MAGIC }, { return false; });

		local Int is bundleLen: readU64LE(raw: raw, offset: totalLen - 16);
		if({ bundleLen < 4 || bundleLen > totalLen - 16 }, { return false; });
		local Int is pos: totalLen - 16 - bundleLen;
		local Int is endPos: totalLen - 16;

		local Int is count: readU32LE(raw: raw, offset: pos);
		pos: pos + 4;
		local Int is i: 0;
		while({ i < count }, {
			if({ pos + 4 > endPos }, { return false; });
			local Int is keyLen: readU32LE(raw: raw, offset: pos);
			pos: pos + 4;
			if({ keyLen < 0 || pos + keyLen + 8 > endPos }, { return false; });
			local String is key: normalizeKey(rawPath: raw:substring(start: pos, end: pos + keyLen));
			pos: pos + keyLen;
			local Int is dataLen: readU64LE(raw: raw, offset: pos);
			pos: pos + 8;
			if({ dataLen < 0 || pos + dataLen > endPos }, { return false; });
			local String is data: raw:substring(start: pos, end: pos + dataLen);
			pos: pos + dataLen;
			entries:set(key: key, value: data);
			entryKeys:add(item: key);
			i: i + 1;
		});
		loaded: true;
		return true;
	}

	## Loads an appended bundle from the file at [path].
	Function of Boolean is loadFromFile(String is path){
		local String is raw: fileRead(path: path, default: '');
		if({ raw == '' }, { return false; });
		return loadFromBytes(raw: raw);
	}

	## Returns true when a valid bundle was loaded.
	Function of Boolean is isBundled(){ loaded }

	## Returns true if [path] exists in the loaded bundle.
	Function of Boolean is has(String is path){
		if({ !loaded }, { return false; });
		return entries:has(key: normalizeKey(rawPath: path));
	}

	## Reads the bundled text/bytes at [path], or returns [default] if missing.
	Function of String is readText(String is path, String is default: ''){
		if({ !loaded }, { return default; });
		local String is key: normalizeKey(rawPath: path);
		if({ !entries:has(key: key) }, { return default; });
		return entries:getString(key: key, default: default);
	}

	## Lists all bundled paths matching [prefix].
	Function of Array of String is list(String is prefix: ''){
		local Array of String is out: Array();
		if({ !loaded }, { return out; });
		local String is normPrefix: normalizeKey(rawPath: prefix);
		local Int is i: 0;
		while({ i < entryKeys:length() }, {
			local String is k: entryKeys:get(index: i);
			if({ normPrefix == '' || k:startsWith(prefix: normPrefix) }, {
				out:add(item: k);
			});
			i: i + 1;
		});
		return out;
	}
}
