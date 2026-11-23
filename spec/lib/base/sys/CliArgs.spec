#! Package base:sys
#! Command-line argument access and option parsing over raw argc/argv.

Class is CliArgs{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Constructs the CLI args map from the raw argc/argv that the entry
	## template stored in TLS slots 12/13. Pure Spec: reads the raw
	## values, iterates the C-string array, and delegates to the existing
	## parse logic. This replaces the prelude's spec_cli_args_map
	## C-to-Spec map-construction call.
	Function of Any is fromGlobals(){
		local Int is argc: Mem:tlsGetI64(slot: 12);
		local Int is av: Mem:tlsGetI64(slot: 13);
		return :parseMap(argc: argc, argvAddr: av);
	}

	local Function of String is argvAt(Int is argvAddr, Int is idx){
		if({ argvAddr == 0 }, { return ''; });
		local Int is cstr: Mem:loadI64(ptr: argvAddr, byteOffset: idx * 8);
		if({ cstr == 0 }, { return ''; });
		return Mem:strFromBytes(srcAddr: cstr, len: Mem:cstrLen(cstrAddr: cstr));
	}

	local Function is setArg(Map of String to String is args, String is key, String is val){
		if({ args:has(key: key) }, {
			local String is prev: args:get(key: key, default: '');
			args:set(key: key, value: prev . "\n" . val);
		}, {
			args:set(key: key, value: val);
		});
	}

	## Parses command-line arguments (`argv[1..argc-1]`) into the entry-point
	## `Map of String to String` (supporting `--key=val`, `--key val`, `-k=val`,
	## `-k val`, indexed positionals `'0'`, `'1'`, ..., and newline-joined `''`).
	Function of Any is parseMap(Int is argc, Int is argvAddr){
		local Map of String to String is args: Map:init();
		local Int is posIdx: 0;
		local Int is i: 1;
		while({ i < argc }, {
			local String is arg: :argvAt(argvAddr: argvAddr, idx: i);
			local Int is alen: arg:length();
			if({ alen >= 2 && arg:byteAt(index: 0, default: 0) == 45 && arg:byteAt(index: 1, default: 0) == 45 }, {
				local String is rest: arg:substring(start: 2, end: alen);
				local Int is eq: rest:indexOf(search: '=', default: -1);
				if({ eq >= 0 }, {
					:setArg(args: args, key: rest:substring(start: 0, end: eq), val: rest:substring(start: eq + 1, end: rest:length()));
				}, {
					local String is val: 'true';
					if({ i + 1 < argc }, {
						local String is nextArg: :argvAt(argvAddr: argvAddr, idx: i + 1);
						if({ nextArg:byteAt(index: 0, default: 0) != 45 }, {
							i: i + 1;
							val: nextArg;
						});
					});
					:setArg(args: args, key: rest, val: val);
				});
			}, {
				if({ alen >= 2 && arg:byteAt(index: 0, default: 0) == 45 }, {
					local String is rest: arg:substring(start: 1, end: alen);
					local Int is eq: rest:indexOf(search: '=', default: -1);
					if({ eq >= 0 }, {
						:setArg(args: args, key: rest:substring(start: 0, end: eq), val: rest:substring(start: eq + 1, end: rest:length()));
					}, {
						local String is val: 'true';
						if({ i + 1 < argc }, {
							local String is nextArg: :argvAt(argvAddr: argvAddr, idx: i + 1);
							if({ nextArg:byteAt(index: 0, default: 0) != 45 }, {
								i: i + 1;
								val: nextArg;
							});
						});
						:setArg(args: args, key: rest, val: val);
					});
				}, {
					:setArg(args: args, key: posIdx as String, val: arg);
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
		local Array of String is out: Array();
		local Int is i: 1;
		while({ i < argc }, {
			out:add(item: :argvAt(argvAddr: argvAddr, idx: i));
			i: i + 1;
		});
		return out;
	}
}
