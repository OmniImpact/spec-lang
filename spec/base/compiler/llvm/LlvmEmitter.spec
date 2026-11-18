#! Package base:compiler:llvm
#! Emits target-agnostic LLVM IR (.ll text with opaque ptr) from an IrModule.

Class is LlvmEmitter{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'compiler', 'ir', IrParam],
		['base', 'compiler', 'ir', IrStruct],
		['base', 'compiler', 'ir', IrFunction],
		['base', 'compiler', 'ir', IrModule],
		['base', 'compiler', 'llvm', LlvmRuntimePrelude],
		['base', 'compiler', 'llvm', LlvmStructLayout],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Buf()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Boolean is debugMode: false;
	Array of String is dbgNodes: [];
	Map of String to Int is dbgFileIds: Map:init();
	Map of String to Int is dbgLocIds: Map:init();
	Int is dbgUnitId: 0;
	Int is dbgEmptyId: 1;
	Int is dbgSubTypeId: 2;

	replace Function is init(){
	}

	Function of String is llvmType(IrType is ty){
		return match(on: ty, when: [
			IrType:Void: { 'void' },
			IrType:I1: { 'i1' },
			IrType:I64: { 'i64' },
			IrType:F64: { 'double' },
			IrType:Ptr: { 'ptr' }
		]);
	}

	local Function of String is emitExternalSpecDecls(IrModule is mod){
		local Map of String to Boolean is known: Map:init();
		local Array of String is preludeSyms: [
			'spec_rt_alloc', 'spec_rt_retain', 'spec_rt_release',
			'spec_pool_frame', 'spec_pool_release_to', 'spec_claim_pool',
			'spec_rt_closure_new', 'spec_rt_box_new', 'spec_rt_box_get', 'spec_rt_box_set',
			'spec_loop_control_is_stopped', 'spec_loop_control_complete', 'spec_loop_control_with_callback',
			'spec_string_intern', 'spec_to_string_float', 'spec_to_string_bool',
			'spec_panic', 'spec_panic_byte_range', 'spec_panic_cast',
			'spec_buf_destroy', 'spec_buf_to_cstring', 'spec_string_copy', 'spec_string_concat', 'spec_type_name',
			'spec_math_log', 'spec_math_log2', 'spec_math_log10', 'spec_fast_random_seed', 'spec_math_random',
			'spec_time_monotonic_ns', 'spec_atomic_add', 'spec_atomic_put', 'spec_atomic_get',
			'spec_cli_args_map', 'spec_process_raw_args'
		];
		local Int is pi: 0;
		while({ pi < preludeSyms:length() }, {
			known:set(key: preludeSyms:get(index: pi, default: ''), value: true);
			pi++;
		});
		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn0: mod:functions:get(index: fi);
			known:set(key: fn0:name, value: true);
			fi++;
		});
		local String is out: '';
		fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: fi);
			local Int is bi: 0;
			while({ bi < fn:blocks:length() }, {
				local IrBlock is blk: fn:blocks:get(index: bi);
				local Int is ii: 0;
				while({ ii < blk:insts:length() }, {
					match(on: blk:insts:get(index: ii), when: [
						IrInst:IrCall: local Function(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
							if({ callee:startsWith(prefix: 'spec_') && !known:has(key: callee) }, {
								known:set(key: callee, value: true);
								local String is sig: '';
								local Int is ai: 0;
								while({ ai < argTypes:length() }, {
									if({ ai > 0 }, { sig: sig . ', '; });
									sig: sig . self:llvmType(ty: argTypes:get(index: ai));
									ai++;
								});
								out: out . 'declare ' . self:llvmType(ty: retType) . ' @' . callee . '(' . sig . ")\n";
							});
						}
					], default: {});
					ii++;
				});
				bi++;
			});
			fi++;
		});
		return out;
	}

	Function of String is emitModule(IrModule is mod){
		local LlvmRuntimePrelude is prelude: LlvmRuntimePrelude:init();
		local String is out: ```
; Spec LLVM IR
{{prelude:emitAll()}}
{{self:emitExternalSpecDecls(mod: mod)}}
```;

		# Module globals (held fields, etc.)
		local Int is gi: 0;
		while({ gi < mod:globalNames:length() }, {
			local String is gn: mod:globalNames:get(index: gi, default: '');
			local IrType is gt: mod:globalTypes:get(index: gi);
			local String is giv: mod:globalInits:get(index: gi, default: 'zeroinitializer');
			out: out . '@' . gn . ' = internal global ' . self:llvmType(ty: gt) . ' ' . giv . "\n";
			gi++;
		});
		if({ mod:globalNames:length() > 0 }, { out: out . "\n"; });

		# Struct types, vtables, and reflection metadata
		local LlvmStructLayout is methodMetaLayout: LlvmStructLayout:methodMeta();
		local LlvmStructLayout is classMetaLayout: LlvmStructLayout:classMeta();
		local LlvmStructLayout is heldEntryLayout: LlvmStructLayout:heldEntry();
		local String is methodMetaType: methodMetaLayout:llvmType();
		local String is heldEntryType: heldEntryLayout:llvmType();
		local Array of String is classMetaRefs: [];
		local Array of String is heldEntryItems: [];
		local Int is si: 0;
		while({ si < mod:structs:length() }, {
			local IrStruct is st: mod:structs:get(index: si);
			local String is fieldsStr: '';
			local Int is fi: 0;
			while({ fi < st:fieldTypes:length() }, {
				if({ fi > 0 }, { fieldsStr: fieldsStr . ', '; });
				fieldsStr: fieldsStr . self:llvmType(ty: st:fieldTypes:get(index: fi));
				fi++;
			});
			out: out . '%struct.' . st:name . ' = type { ' . fieldsStr . " }\n";
			local String is qn: if({ st:qualifiedName != '' }, { st:qualifiedName }, { st:name });
			out: out . self:emitCStrGlobal(sym: '@.typename.' . st:name, val: qn);
			local Int is vtLen: st:vtableFns:length();
			if({ vtLen > 0 }, {
				local String is vtItems: '';
				local Int is vi: 0;
				while({ vi < vtLen }, {
					if({ vi > 0 }, { vtItems: vtItems . ', '; });
					local String is vfn: st:vtableFns:get(index: vi, default: 'null');
					if({ vfn == 'null' }, {
						vtItems: vtItems . 'ptr null';
					}, {
						vtItems: vtItems . 'ptr @' . vfn;
					});
					vi++;
				});
				out: out . '@.vtable.' . st:name . ' = constant [' . (vtLen as String) . ' x ptr] [' . vtItems . "]\n";
			}, {
				out: out . '@.vtable.' . st:name . " = constant [1 x ptr] zeroinitializer\n";
			});

			# Reflection metadata for this struct
			out: out . self:emitCStrGlobal(sym: '@.src.' . st:name, val: st:sourceFileBase);
			local String is basesRef: 'null';
			if({ st:baseNames:length() > 0 }, {
				local String is bItems: '';
				local Int is bi: 0;
				while({ bi < st:baseNames:length() }, {
					local String is bn: st:baseNames:get(index: bi, default: '');
					local String is bSym: '@.bname.' . st:name . '.' . (bi as String);
					out: out . self:emitCStrGlobal(sym: bSym, val: bn);
					if({ bi > 0 }, { bItems: bItems . ', '; });
					bItems: bItems . 'ptr ' . bSym;
					bi++;
				});
				out: out . '@.bases.' . st:name . ' = private constant [' . (st:baseNames:length() as String) . ' x ptr] [' . bItems . "]\n";
				basesRef: '@.bases.' . st:name;
			});

			local String is methodsRef: 'null';
			if({ st:metaMethodNames:length() > 0 }, {
				local String is mItems: '';
				local Int is mi: 0;
				while({ mi < st:metaMethodNames:length() }, {
					local String is mn: st:metaMethodNames:get(index: mi, default: '');
					local String is mSym: '@.mname.' . st:name . '.' . (mi as String);
					out: out . self:emitCStrGlobal(sym: mSym, val: mn);
					local String is mfn: st:metaMethodFns:get(index: mi, default: 'null');
					local String is mfnRef: if({ mfn == 'null' }, { 'null' }, { '@' . mfn });
					local Int is mfl: st:metaMethodFlags:get(index: mi, default: 0);
					local Int is mln: st:metaMethodLines:get(index: mi, default: 0);
					if({ mi > 0 }, { mItems: mItems . ', '; });
					mItems: mItems . methodMetaLayout:formatConst(values: [mSym, mfnRef, mfl as String, mln as String]);
					mi++;
				});
				out: out . '@.methods.' . st:name . ' = private constant [' . (st:metaMethodNames:length() as String) . ' x ' . methodMetaType . '] [' . mItems . "]\n";
				methodsRef: '@.methods.' . st:name;
			});

			local String is ctorPtr: if({ st:constructFn == 'null' }, { 'null' }, { '@' . st:constructFn });
			out: out . '@.meta.' . st:name . ' = private constant ' . classMetaLayout:formatConst(values: ['@.typename.' . st:name, '@.src.' . st:name, basesRef, st:baseNames:length() as String, ctorPtr, methodsRef, st:metaMethodNames:length() as String]) . "\n";
			classMetaRefs:add(item: 'ptr @.meta.' . st:name);

			if({ st:heldNames:length() > 0 }, {
				local String is hnItems: '';
				local String is hgItems: '';
				local Int is hi: 0;
				while({ hi < st:heldNames:length() }, {
					local String is hn: st:heldNames:get(index: hi, default: '');
					local String is hSym: '@.hname.' . st:name . '.' . (hi as String);
					out: out . self:emitCStrGlobal(sym: hSym, val: hn);
					local String is hg: st:heldGetters:get(index: hi, default: 'null');
					local String is hgPtr: if({ hg == 'null' }, { 'null' }, { '@' . hg });
					if({ hi > 0 }, {
						hnItems: hnItems . ', ';
						hgItems: hgItems . ', ';
					});
					hnItems: hnItems . 'ptr ' . hSym;
					hgItems: hgItems . 'ptr ' . hgPtr;
					hi++;
				});
				out: out . '@.held_names.' . st:name . ' = private constant [' . (st:heldNames:length() as String) . ' x ptr] [' . hnItems . "]\n";
				out: out . '@.held_getters.' . st:name . ' = private constant [' . (st:heldGetters:length() as String) . ' x ptr] [' . hgItems . "]\n";
				heldEntryItems:add(item: heldEntryLayout:formatConst(values: ['@.typename.' . st:name, '@.held_names.' . st:name, st:heldNames:length() as String, '@.held_getters.' . st:name]));
			});
			si++;
		});
		if({ mod:structs:length() > 0 }, { out: out . "\n"; });

		# Global class and held registries
		local Int is cmCount: classMetaRefs:length();
		if({ cmCount > 0 }, {
			local String is cmList: '';
			local Int is ci: 0;
			while({ ci < cmCount }, {
				if({ ci > 0 }, { cmList: cmList . ', '; });
				cmList: cmList . classMetaRefs:get(index: ci, default: 'ptr null');
				ci++;
			});
			out: out . '@spec_class_registry = constant [' . (cmCount as String) . ' x ptr] [' . cmList . "]\n";
		}, {
			out: out . "@spec_class_registry = constant [1 x ptr] zeroinitializer\n";
		});
		out: out . 'define i32 @spec_class_registry_count() {' . "\n  ret i32 " . (cmCount as String) . "\n}\n";

		heldEntryItems:add(item: heldEntryType . ' zeroinitializer');
		local String is heList: '';
		local Int is hei: 0;
		while({ hei < heldEntryItems:length() }, {
			if({ hei > 0 }, { heList: heList . ', '; });
			heList: heList . heldEntryItems:get(index: hei, default: '');
			hei++;
		});
		out: out . '@spec_held_registry = constant [' . (heldEntryItems:length() as String) . ' x ' . heldEntryType . '] [' . heList . "]\n\n";

		# String literal globals (null-terminated)
		local Int is li: 0;
		while({ li < mod:stringLiterals:length() }, {
			local String is raw: mod:stringLiterals:get(index: li, default: '');
			local Int is byteLen: raw:length() + 1;
			local String is esc: self:escapeLlvmBytes(s: raw);
			out: out . '@.str.' . (li as String) . ' = private unnamed_addr constant [' . (byteLen as String) . ' x i8] c"' . esc . "\\00\"\n";
			out: out . '@.str.cache.' . (li as String) . " = internal global ptr null, align 8\n";
			li++;
		});
		if({ mod:stringLiterals:length() > 0 }, { out: out . "\n"; });

		# Functions
		if({ self:debugMode }, {
			self:dbgNodes: [];
			self:dbgFileIds: Map:init();
			self:dbgLocIds: Map:init();
			# !0 = DICompileUnit, !1 = !{}, !2 = DISubroutineType
			self:dbgNodes:add(item: '');
			self:dbgNodes:add(item: '!1 = !{}');
			self:dbgNodes:add(item: '!2 = !DISubroutineType(types: !1)');
		});
		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			out: out . self:emitFunction(fn: mod:functions:get(index: fi)) . "\n";
			fi++;
		});
		if({ self:debugMode }, {
			out: out . self:emitDebugMetadata();
		});
		return out;
	}

	local Function of Int is internDebugFile(String is path){
		local String is norm: if({ path != '' }, { path }, { '<spec>' });
		if({ self:dbgFileIds:has(key: norm) }, {
			return self:dbgFileIds:get(key: norm, default: 0);
		});
		local Int is lastSlash: -1;
		local Int is n: Buf:bufLength(b: norm);
		local Int is idx: 0;
		while({ idx < n }, {
			if({ Buf:bufGetByte(b: norm, idx: idx, def: 0) == 47 }, {
				lastSlash: idx;
			});
			idx++;
		});
		local String is dir: '.';
		local String is file: norm;
		if({ lastSlash >= 0 }, {
			dir: if({ lastSlash == 0 }, { '/' }, { Buf:stringSubstring(b: norm, start: 0, end: lastSlash) });
			file: Buf:stringSubstring(b: norm, start: lastSlash + 1, end: n);
		});
		local Int is id: self:dbgNodes:length();
		self:dbgNodes:add(item: '!' . (id as String) . ' = !DIFile(filename: "' . self:escapeDebugStr(s: file) . '", directory: "' . self:escapeDebugStr(s: dir) . '")');
		self:dbgFileIds:set(key: norm, value: id);
		return id;
	}

	local Function of Int is internDebugLoc(Int is spId, Int is line){
		local Int is effLine: if({ line > 0 }, { line }, { 1 });
		local String is key: (spId as String) . ':' . (effLine as String);
		if({ self:dbgLocIds:has(key: key) }, {
			return self:dbgLocIds:get(key: key, default: 0);
		});
		local Int is id: self:dbgNodes:length();
		self:dbgNodes:add(item: '!' . (id as String) . ' = !DILocation(line: ' . (effLine as String) . ', column: 1, scope: !' . (spId as String) . ')');
		self:dbgLocIds:set(key: key, value: id);
		return id;
	}

	local Function of String is escapeDebugStr(String is s){
		local String is res: '';
		local Int is len: Buf:bufLength(b: s);
		local Int is i: 0;
		while({ i < len }, {
			local Int is b: Buf:bufGetByte(b: s, idx: i, def: 0);
			if({ b == 34 }, {
				res: res . '\\"';
			}, {
				if({ b == 92 }, {
					res: res . '\\\\';
				}, {
					res: res . Buf:stringSubstring(b: s, start: i, end: i + 1);
				});
			});
			i++;
		});
		return res;
	}

	local Function of String is appendDbgToInst(String is ir, Int is locId){
		local String is suffix: ', !dbg !' . (locId as String);
		local Array of String is parts: ir:split(delimiter: "\n");
		if({ parts:length() <= 1 }, {
			return ir . suffix;
		});
		local String is out: '';
		local Int is pi: 0;
		while({ pi < parts:length() }, {
			if({ pi > 0 }, { out: out . "\n"; });
			out: out . parts:get(index: pi, default: '') . suffix;
			pi++;
		});
		return out;
	}

	local Function of String is emitDebugMetadata(){
		local Int is cuFileId: 0;
		if({ self:dbgNodes:length() <= 3 }, {
			cuFileId: self:internDebugFile(path: 'main.spec');
		}, {
			cuFileId: 3;
		});
		local Int is dwarfVerId: self:dbgNodes:length();
		self:dbgNodes:add(item: '!' . (dwarfVerId as String) . ' = !{i32 7, !"Dwarf Version", i32 5}');
		local Int is dbgVerId: self:dbgNodes:length();
		self:dbgNodes:add(item: '!' . (dbgVerId as String) . ' = !{i32 2, !"Debug Info Version", i32 3}');
		self:dbgNodes:set(index: 0, value: '!0 = distinct !DICompileUnit(language: DW_LANG_C99, file: !' . (cuFileId as String) . ', producer: "spec", isOptimized: false, runtimeVersion: 0, emissionKind: LineTablesOnly, enums: !1, splitDebugInlining: false, nameTableKind: None)');

		local String is out: "!llvm.dbg.cu = !{!0}\n";
		out: out . '!llvm.module.flags = !{!' . (dwarfVerId as String) . ', !' . (dbgVerId as String) . "}\n\n";
		local Int is ni: 0;
		while({ ni < self:dbgNodes:length() }, {
			out: out . self:dbgNodes:get(index: ni, default: '') . "\n";
			ni++;
		});
		return out;
	}

	local Function of String is emitCStrGlobal(String is sym, String is val){
		local Int is byteLen: val:length() + 1;
		local String is esc: self:escapeLlvmBytes(s: val);
		return sym . ' = private unnamed_addr constant [' . (byteLen as String) . ' x i8] c"' . esc . "\\00\"\n";
	}

	local Function of String is escapeLlvmBytes(String is s){
		local String is hex: '0123456789ABCDEF';
		local String is res: '';
		local Int is len: Buf:bufLength(b: s);
		local Int is i: 0;
		while({ i < len }, {
			local Int is b: Buf:bufGetByte(b: s, idx: i, def: 0);
			if({ b < 32 || b >= 127 || b == 34 || b == 92 }, {
				local Int is hi: (b >> 4) & 15;
				local Int is lo: b & 15;
				res: res . '\\' . Buf:stringSubstring(b: hex, start: hi, end: hi + 1) . Buf:stringSubstring(b: hex, start: lo, end: lo + 1);
			}, {
				res: res . Buf:stringSubstring(b: s, start: i, end: i + 1);
			});
			i++;
		});
		return res;
	}

	local Function of String is emitFunction(IrFunction is fn){
		local String is retStr: self:llvmType(ty: fn:retType);
		local String is paramsStr: '';
		local Int is pi: 0;
		while({ pi < fn:params:length() }, {
			if({ pi > 0 }, { paramsStr: paramsStr . ', '; });
			local IrParam is p: fn:params:get(index: pi);
			paramsStr: paramsStr . self:llvmType(ty: p:ty) . ' ' . p:name;
			pi++;
		});

		if({ fn:isExternal }, {
			return 'declare ' . retStr . ' @' . fn:name . '(' . paramsStr . ")\n";
		});

		local String is inlineAttr: '';
		if({ fn:alwaysInline && !self:debugMode }, {
			inlineAttr: ' alwaysinline';
		});

		local Int is spId: -1;
		local String is spAttr: '';
		if({ self:debugMode && fn:sourceFile != '' }, {
			local Int is fileId: self:internDebugFile(path: fn:sourceFile);
			local Int is fnLine: if({ fn:line > 0 }, { fn:line }, { 1 });
			spId: self:dbgNodes:length();
			self:dbgNodes:add(item: '!' . (spId as String) . ' = distinct !DISubprogram(name: "' . self:escapeDebugStr(s: fn:name) . '", scope: !' . (fileId as String) . ', file: !' . (fileId as String) . ', line: ' . (fnLine as String) . ', type: !2, scopeLine: ' . (fnLine as String) . ', spFlags: DISPFlagDefinition, unit: !0)');
			spAttr: ' !dbg !' . (spId as String);
		});

		local String is out: 'define ' . retStr . ' @' . fn:name . '(' . paramsStr . ')' . inlineAttr . spAttr . " {\n";
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			out: out . blk:label . ":\n";
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local String is instStr: self:emitInst(inst: blk:insts:get(index: ii));
				if({ spId >= 0 }, {
					local Int is ln: blk:instLines:get(index: ii, default: 0);
					if({ ln <= 0 }, { ln: fn:line; });
					local Int is locId: self:internDebugLoc(spId: spId, line: ln);
					instStr: self:appendDbgToInst(ir: instStr, locId: locId);
				});
				out: out . '  ' . instStr . "\n";
				ii++;
			});
			bi++;
		});
		out: out . "}\n";
		return out;
	}

	local Function of String is emitInst(IrInst is inst){
		return match(on: inst, when: [
			IrInst:ConstInt: local Function of String(String is dst, Int is value){
				return dst . ' = add i64 0, ' . (value as String);
			},
			IrInst:ConstFloat: local Function of String(String is dst, String is text){
				return dst . ' = fadd double 0.0, ' . text;
			},
			IrInst:ConstBool: local Function of String(String is dst, Boolean is value){
				if({ value }, { return dst . ' = add i1 0, 1'; });
				return dst . ' = add i1 0, 0';
			},
			IrInst:ConstString: local Function of String(String is dst, Int is strId){
				local String is idStr: strId as String;
				return dst . ' = call ptr @__spec_intern_cached(ptr @.str.' . idStr . ', ptr @.str.cache.' . idStr . ')';
			},
			IrInst:Alloca: local Function of String(String is slot, IrType is ty){
				return slot . ' = alloca ' . self:llvmType(ty: ty);
			},
			IrInst:Load: local Function of String(String is dst, String is slot, IrType is ty){
				local String is t: self:llvmType(ty: ty);
				return dst . ' = load ' . t . ', ptr ' . slot;
			},
			IrInst:Store: local Function of String(String is slot, String is val, IrType is ty){
				local String is t: self:llvmType(ty: ty);
				return 'store ' . t . ' ' . val . ', ptr ' . slot;
			},
			IrInst:BinOp: local Function of String(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
				local String is t: self:llvmType(ty: ty);
				local String is llvmOp: self:llvmBinOp(op: op, ty: ty);
				return dst . ' = ' . llvmOp . ' ' . t . ' ' . lhs . ', ' . rhs;
			},
			IrInst:UnaryOp: local Function of String(String is dst, String is op, String is operand, IrType is ty){
				if({ op == '-' }, {
					if({ ty == IrType:F64 }, { return dst . ' = fneg double ' . operand; });
					return dst . ' = sub i64 0, ' . operand;
				});
				if({ op == '!' }, {
					return dst . ' = xor i1 ' . operand . ', 1';
				});
				if({ op == '~' }, {
					return dst . ' = xor i64 ' . operand . ', -1';
				});
				return dst . ' = add i64 0, ' . operand;
			},
			IrInst:Cmp: local Function of String(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
				local String is t: self:llvmType(ty: ty);
				if({ ty == IrType:F64 }, {
					local String is fpred: 'oeq';
					if({ op == '!=' }, { fpred: 'one'; });
					if({ op == '<' }, { fpred: 'olt'; });
					if({ op == '<=' }, { fpred: 'ole'; });
					if({ op == '>' }, { fpred: 'ogt'; });
					if({ op == '>=' }, { fpred: 'oge'; });
					return dst . ' = fcmp ' . fpred . ' double ' . lhs . ', ' . rhs;
				});
				local String is ipred: 'eq';
				if({ op == '!=' }, { ipred: 'ne'; });
				if({ op == '<' }, { ipred: 'slt'; });
				if({ op == '<=' }, { ipred: 'sle'; });
				if({ op == '>' }, { ipred: 'sgt'; });
				if({ op == '>=' }, { ipred: 'sge'; });
				return dst . ' = icmp ' . ipred . ' ' . t . ' ' . lhs . ', ' . rhs;
			},
			IrInst:IrCall: local Function of String(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
				local String is argsStr: '';
				local Int is ai: 0;
				while({ ai < args:length() }, {
					if({ ai > 0 }, { argsStr: argsStr . ', '; });
					argsStr: argsStr . self:llvmType(ty: argTypes:get(index: ai)) . ' ' . args:get(index: ai, default: '');
					ai++;
				});
				local String is rt: self:llvmType(ty: retType);
				if({ hasDst }, {
					return dst . ' = call ' . rt . ' @' . callee . '(' . argsStr . ')';
				});
				return 'call ' . rt . ' @' . callee . '(' . argsStr . ')';
			},
			IrInst:IndirectCall: local Function of String(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, Array of IrType is argTypes, Array of String is args){
				local String is argsStr: '';
				local Int is ai: 0;
				while({ ai < args:length() }, {
					if({ ai > 0 }, { argsStr: argsStr . ', '; });
					argsStr: argsStr . self:llvmType(ty: argTypes:get(index: ai)) . ' ' . args:get(index: ai, default: '');
					ai++;
				});
				local String is rt: self:llvmType(ty: retType);
				if({ hasDst }, {
					return dst . ' = call ' . rt . ' ' . fnPtr . '(' . argsStr . ')';
				});
				return 'call ' . rt . ' ' . fnPtr . '(' . argsStr . ')';
			},
			IrInst:GlobalAddr: local Function of String(String is dst, String is globalName){
				return dst . ' = getelementptr i8, ptr @' . globalName . ', i64 0';
			},
			IrInst:AllocObj: local Function of String(String is dst, String is structName, String is destroyFn){
				local LlvmStructLayout is hdr: LlvmStructLayout:objHeader();
				local String is tnIdx: hdr:fieldIndex(name: 'type_name') as String;
				local String is vtIdx: hdr:fieldIndex(name: 'vtable') as String;
				local String is szPtr: dst . '_szp';
				local String is szVal: dst . '_sz';
				local String is tnPtr: dst . '_tnp';
				local String is vtPtr: dst . '_vtp';
				return szPtr . ' = getelementptr %struct.' . structName . ", ptr null, i32 1\n  "
					. szVal . ' = ptrtoint ptr ' . szPtr . " to i64\n  "
					. dst . ' = call ptr @spec_rt_alloc(i64 ' . szVal . ', ptr ' . destroyFn . ")\n  "
					. tnPtr . ' = getelementptr inbounds %struct.' . structName . ', ptr ' . dst . ', i32 0, i32 ' . tnIdx . "\n  "
					. 'store ptr @.typename.' . structName . ', ptr ' . tnPtr . "\n  "
					. vtPtr . ' = getelementptr inbounds %struct.' . structName . ', ptr ' . dst . ', i32 0, i32 ' . vtIdx . "\n  "
					. 'store ptr @.vtable.' . structName . ', ptr ' . vtPtr;
			},
			IrInst:FieldPtr: local Function of String(String is dst, String is objPtr, String is structName, Int is fieldIndex){
				return dst . ' = getelementptr inbounds %struct.' . structName . ', ptr ' . objPtr . ', i32 0, i32 ' . (fieldIndex as String);
			},
			IrInst:PtrElem: local Function of String(String is dst, String is basePtr, Int is index){
				return dst . ' = getelementptr ptr, ptr ' . basePtr . ', i64 ' . (index as String);
			},
			IrInst:IrCast: local Function of String(String is dst, String is val, IrType is fromType, IrType is toType){
				if({ fromType == IrType:I64 && toType == IrType:F64 }, { return dst . ' = sitofp i64 ' . val . ' to double'; });
				if({ fromType == IrType:F64 && toType == IrType:I64 }, { return dst . ' = fptosi double ' . val . ' to i64'; });
				if({ (fromType == IrType:I64 || fromType == IrType:I1) && toType == IrType:Ptr }, {
					return dst . ' = inttoptr ' . self:llvmType(ty: fromType) . ' ' . val . ' to ptr';
				});
				if({ fromType == IrType:Ptr && (toType == IrType:I64 || toType == IrType:I1) }, {
					return dst . ' = ptrtoint ptr ' . val . ' to ' . self:llvmType(ty: toType);
				});
				if({ fromType == IrType:F64 && toType == IrType:Ptr }, {
					local String is bits: dst . '_bits';
					return bits . " = bitcast double " . val . " to i64\n  "
						. dst . ' = inttoptr i64 ' . bits . ' to ptr';
				});
				if({ fromType == IrType:Ptr && toType == IrType:F64 }, {
					local String is bits: dst . '_bits';
					return bits . " = ptrtoint ptr " . val . " to i64\n  "
						. dst . ' = bitcast i64 ' . bits . ' to double';
				});
				if({ fromType == IrType:I1 && toType == IrType:I64 }, { return dst . ' = zext i1 ' . val . ' to i64'; });
				if({ fromType == IrType:I64 && toType == IrType:I1 }, { return dst . ' = icmp ne i64 ' . val . ', 0'; });
				return dst . ' = bitcast ' . self:llvmType(ty: fromType) . ' ' . val . ' to ' . self:llvmType(ty: toType);
			},
			IrInst:Retain: local Function of String(String is val){
				return 'call ptr @spec_rt_retain(ptr ' . val . ')';
			},
			IrInst:Release: local Function of String(String is val){
				return 'call void @spec_rt_release(ptr ' . val . ')';
			},
			IrInst:Ret: local Function of String(Boolean is hasVal, String is val, IrType is ty){
				if({ hasVal }, {
					return 'ret ' . self:llvmType(ty: ty) . ' ' . val;
				});
				return 'ret void';
			},
			IrInst:Br: local Function of String(String is target){
				return 'br label %' . target;
			},
			IrInst:CondBr: local Function of String(String is cond, String is thenLabel, String is elseLabel){
				return 'br i1 ' . cond . ', label %' . thenLabel . ', label %' . elseLabel;
			}
		]);
	}

	local Function of String is llvmBinOp(String is op, IrType is ty){
		if({ ty == IrType:F64 }, {
			if({ op == '+' }, { return 'fadd'; });
			if({ op == '-' }, { return 'fsub'; });
			if({ op == '*' }, { return 'fmul'; });
			if({ op == '/' }, { return 'fdiv'; });
			return 'fadd';
		});
		if({ op == '+' }, { return 'add'; });
		if({ op == '-' }, { return 'sub'; });
		if({ op == '*' }, { return 'mul'; });
		if({ op == '/' }, { return 'sdiv'; });
		if({ op == '%' }, { return 'srem'; });
		if({ op == '&' || op == '&&' }, { return 'and'; });
		if({ op == '|' || op == '||' }, { return 'or'; });
		if({ op == '^' }, { return 'xor'; });
		if({ op == '<<' }, { return 'shl'; });
		if({ op == '>>' }, { return 'ashr'; });
		return 'add';
	}
}
