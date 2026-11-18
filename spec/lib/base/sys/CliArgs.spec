#! Package base:sys
#! Command-line argument access and option parsing over raw argc/argv.

Class is CliArgs{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Buf()],
		['base', 'sys', as HashTable()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Function of String is argvAt(Int is argvAddr, Int is idx){
		if({ argvAddr == 0 }, { return ''; });
		local Int is cstr: Mem:loadI64(ptr: argvAddr, byteOffset: idx * 8);
		if({ cstr == 0 }, { return ''; });
		return Mem:strFromBytes(srcAddr: cstr, len: Mem:cstrLen(cstrAddr: cstr));
	}

	local Function is setArg(Any is args, String is key, String is val){
		if({ HashTable:mapHas(m: args, key: key) }, {
			local String is prev: HashTable:mapGet(m: args, key: key, def: '') as String;
			HashTable:mapSet(m: args, key: key, val: Buf:stringConcat(a: Buf:stringConcat(a: prev, b: "\n"), b: val));
		}, {
			HashTable:mapSet(m: args, key: key, val: val);
		});
	}

	## Parses command-line arguments (`argv[1..argc-1]`) into the entry-point
	## `Map of String to String` (supporting `--key=val`, `--key val`, `-k=val`,
	## `-k val`, indexed positionals `'0'`, `'1'`, ..., and newline-joined `''`).
	Function of Any is parseMap(Int is argc, Int is argvAddr){
		local Any is args: HashTable:mapNew();
		local Int is posIdx: 0;
		local Int is i: 1;
		while({ i < argc }, {
			local String is arg: :argvAt(argvAddr: argvAddr, idx: i);
			local Int is alen: Buf:bufLength(b: arg);
			if({ alen >= 2 && Buf:bufGetByte(b: arg, idx: 0, def: 0) == 45 && Buf:bufGetByte(b: arg, idx: 1, def: 0) == 45 }, {
				local String is rest: Buf:stringSubstring(b: arg, start: 2, end: alen);
				local Int is eq: Buf:stringIndexOf(b: rest, needle: '=', def: -1);
				if({ eq >= 0 }, {
					:setArg(args: args, key: Buf:stringSubstring(b: rest, start: 0, end: eq), val: Buf:stringSubstring(b: rest, start: eq + 1, end: Buf:bufLength(b: rest)));
				}, {
					local String is val: 'true';
					if({ i + 1 < argc }, {
						local String is nextArg: :argvAt(argvAddr: argvAddr, idx: i + 1);
						if({ Buf:bufGetByte(b: nextArg, idx: 0, def: 0) != 45 }, {
							i: i + 1;
							val: nextArg;
						});
					});
					:setArg(args: args, key: rest, val: val);
				});
			}, {
				if({ alen >= 2 && Buf:bufGetByte(b: arg, idx: 0, def: 0) == 45 }, {
					local String is rest: Buf:stringSubstring(b: arg, start: 1, end: alen);
					local Int is eq: Buf:stringIndexOf(b: rest, needle: '=', def: -1);
					if({ eq >= 0 }, {
						:setArg(args: args, key: Buf:stringSubstring(b: rest, start: 0, end: eq), val: Buf:stringSubstring(b: rest, start: eq + 1, end: Buf:bufLength(b: rest)));
					}, {
						local String is val: 'true';
						if({ i + 1 < argc }, {
							local String is nextArg: :argvAt(argvAddr: argvAddr, idx: i + 1);
							if({ Buf:bufGetByte(b: nextArg, idx: 0, def: 0) != 45 }, {
								i: i + 1;
								val: nextArg;
							});
						});
						:setArg(args: args, key: rest, val: val);
					});
				}, {
					:setArg(args: args, key: Buf:intToString(v: posIdx), val: arg);
					posIdx: posIdx + 1;
					:setArg(args: args, key: '', val: arg);
				});
			});
			i: i + 1;
		});
		return args;
	}

	## Returns `argv[1..argc-1]` as an `Array of String` in CLI order.
	Function of Array of String is rawArgs(Int is argc, Int is argvAddr){
		local Array of String is out: [];
		local Int is i: 1;
		while({ i < argc }, {
			out:add(item: :argvAt(argvAddr: argvAddr, idx: i));
			i: i + 1;
		});
		return out;
	}
}
