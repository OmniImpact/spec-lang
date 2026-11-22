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
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Process()],
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
			'spec_pool_frame', 'spec_pool_release_to', 'spec_pool_release_to_transfer', 'spec_claim_pool',
			'spec_rt_closure_new', 'spec_rt_box_new', 'spec_rt_box_get', 'spec_rt_box_set',
			'spec_string_intern', 'spec_to_string_float', 'spec_to_string_bool',
			'spec_panic', 'spec_panic_byte_range', 'spec_panic_cast',
			'spec_buf_destroy', 'spec_buf_to_cstring', 'spec_string_copy', 'spec_string_concat', 'spec_type_name',
			'spec_math_log', 'spec_math_log2', 'spec_math_log10', 'spec_fast_random_seed', 'spec_math_random',
			'spec_time_monotonic_ns', 'spec_atomic_add', 'spec_atomic_put', 'spec_atomic_get',
			'spec_process_raw_args', 'spec_pal_random_bytes'
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
									sig: sig . :llvmType(ty: argTypes:get(index: ai));
									ai++;
								});
								out: out . 'declare ' . :llvmType(ty: retType) . ' @' . callee . '(' . sig . ")\n";
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

	local Function of String is emitModuleHeader(IrModule is mod){
		local LlvmRuntimePrelude is prelude: LlvmRuntimePrelude:init();
		local String is out: ```
; Spec LLVM IR
{{prelude:emitAll()}}
{{:emitExternalSpecDecls(mod: mod)}}
```;

		# Module globals (held fields, etc.)
		local Int is gi: 0;
		while({ gi < mod:globalNames:length() }, {
			local String is gn: mod:globalNames:get(index: gi, default: '');
			local IrType is gt: mod:globalTypes:get(index: gi);
			local String is giv: mod:globalInits:get(index: gi, default: 'zeroinitializer');
			out: out . '@' . gn . ' = internal global ' . :llvmType(ty: gt) . ' ' . giv . "\n";
			gi++;
		});
		if({ mod:globalNames:length() > 0 }, { out: out . "\n"; });

		# Struct types, vtables, and reflection metadata
		local LlvmStructLayout is methodMetaLayout: LlvmStructLayout:methodMeta();
		local LlvmStructLayout is fieldMetaLayout: LlvmStructLayout:fieldMeta();
		local LlvmStructLayout is classMetaLayout: LlvmStructLayout:classMeta();
		local LlvmStructLayout is heldEntryLayout: LlvmStructLayout:heldEntry();
		local String is methodMetaType: methodMetaLayout:llvmType();
		local String is fieldMetaType: fieldMetaLayout:llvmType();
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
				fieldsStr: fieldsStr . :llvmType(ty: st:fieldTypes:get(index: fi));
				fi++;
			});
			out: out . '%struct.' . st:name . ' = type { ' . fieldsStr . " }\n";
			local String is qn: if({ st:qualifiedName != '' }, { st:qualifiedName }, { st:name });
			out: out . :emitCStrGlobal(sym: '@.typename.' . st:name, val: qn);
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
			out: out . :emitCStrGlobal(sym: '@.src.' . st:name, val: st:sourceFileBase);
			local String is basesRef: 'null';
			if({ st:baseNames:length() > 0 }, {
				local String is bItems: '';
				local Int is bi: 0;
				while({ bi < st:baseNames:length() }, {
					local String is bn: st:baseNames:get(index: bi, default: '');
					local String is bSym: '@.bname.' . st:name . '.' . (bi as String);
					out: out . :emitCStrGlobal(sym: bSym, val: bn);
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
					out: out . :emitCStrGlobal(sym: mSym, val: mn);
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

			local String is fieldsRef: 'null';
			if({ st:metaFieldNames:length() > 0 }, {
				local String is mfItems: '';
				local Int is mfi: 0;
				while({ mfi < st:metaFieldNames:length() }, {
					local String is mfnm: st:metaFieldNames:get(index: mfi, default: '');
					local String is mfty: st:metaFieldTypes:get(index: mfi, default: '');
					local Int is mfidx: st:metaFieldIndices:get(index: mfi, default: 0);
					local Int is mffl: st:metaFieldFlags:get(index: mfi, default: 0);
					local String is fnSym: '@.fname.' . st:name . '.' . (mfi as String);
					local String is ftSym: '@.ftype.' . st:name . '.' . (mfi as String);
					out: out . :emitCStrGlobal(sym: fnSym, val: mfnm);
					out: out . :emitCStrGlobal(sym: ftSym, val: mfty);
					local String is offExpr: 'ptrtoint (ptr getelementptr (%struct.' . st:name . ', ptr null, i32 0, i32 ' . (mfidx as String) . ') to i32)';
					if({ mfi > 0 }, { mfItems: mfItems . ', '; });
					mfItems: mfItems . fieldMetaLayout:formatConst(values: [fnSym, ftSym, offExpr, mffl as String]);
					mfi++;
				});
				out: out . '@.fields.' . st:name . ' = private constant [' . (st:metaFieldNames:length() as String) . ' x ' . fieldMetaType . '] [' . mfItems . "]\n";
				fieldsRef: '@.fields.' . st:name;
			});

			local String is ctorPtr: if({ st:constructFn == 'null' }, { 'null' }, { '@' . st:constructFn });
			out: out . '@.meta.' . st:name . ' = private constant ' . classMetaLayout:formatConst(values: ['@.typename.' . st:name, '@.src.' . st:name, basesRef, st:baseNames:length() as String, ctorPtr, methodsRef, st:metaMethodNames:length() as String, fieldsRef, st:metaFieldNames:length() as String]) . "\n";
			classMetaRefs:add(item: 'ptr @.meta.' . st:name);

			if({ st:heldNames:length() > 0 }, {
				local String is hnItems: '';
				local String is hgItems: '';
				local Int is hi: 0;
				while({ hi < st:heldNames:length() }, {
					local String is hn: st:heldNames:get(index: hi, default: '');
					local String is hSym: '@.hname.' . st:name . '.' . (hi as String);
					out: out . :emitCStrGlobal(sym: hSym, val: hn);
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
			local String is esc: :escapeLlvmBytes(s: raw);
			out: out . '@.str.' . (li as String) . ' = private unnamed_addr constant [' . (byteLen as String) . ' x i8] c"' . esc . "\\00\"\n";
			out: out . '@.str.cache.' . (li as String) . " = internal global ptr null, align 8\n";
			li++;
		});
		if({ mod:stringLiterals:length() > 0 }, { out: out . "\n"; });
		return out;
	}

	local Function of String is emitShardHeader(IrModule is mod, Boolean is isPrimary){
		local LlvmRuntimePrelude is prelude: LlvmRuntimePrelude:init();
		local String is out: ```
; Spec LLVM IR (shard)
{{prelude:emitAllForShard(isPrimary: isPrimary)}}
{{:emitExternalSpecDecls(mod: mod)}}
```;
		if({ isPrimary }, {
			local Int is gi: 0;
			while({ gi < mod:globalNames:length() }, {
				local String is gn: mod:globalNames:get(index: gi, default: '');
				local IrType is gt: mod:globalTypes:get(index: gi);
				local String is giv: mod:globalInits:get(index: gi, default: 'zeroinitializer');
				out: out . '@' . gn . ' = hidden global ' . :llvmType(ty: gt) . ' ' . giv . "\n";
				gi++;
			});
			if({ mod:globalNames:length() > 0 }, { out: out . "\n"; });

			local LlvmStructLayout is methodMetaLayout: LlvmStructLayout:methodMeta();
			local LlvmStructLayout is fieldMetaLayout: LlvmStructLayout:fieldMeta();
			local LlvmStructLayout is classMetaLayout: LlvmStructLayout:classMeta();
			local LlvmStructLayout is heldEntryLayout: LlvmStructLayout:heldEntry();
			local String is methodMetaType: methodMetaLayout:llvmType();
			local String is fieldMetaType: fieldMetaLayout:llvmType();
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
					fieldsStr: fieldsStr . :llvmType(ty: st:fieldTypes:get(index: fi));
					fi++;
				});
				out: out . '%struct.' . st:name . ' = type { ' . fieldsStr . " }\n";
				local String is qn: if({ st:qualifiedName != '' }, { st:qualifiedName }, { st:name });
				local Int is qnByteLen: qn:length() + 1;
				out: out . '@.typename.' . st:name . ' = hidden unnamed_addr constant [' . (qnByteLen as String) . ' x i8] c"' . :escapeLlvmBytes(s: qn) . "\\00\"\n";
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
					out: out . '@.vtable.' . st:name . ' = hidden constant [' . (vtLen as String) . ' x ptr] [' . vtItems . "]\n";
				}, {
					out: out . '@.vtable.' . st:name . " = hidden constant [1 x ptr] zeroinitializer\n";
				});

				out: out . :emitCStrGlobal(sym: '@.src.' . st:name, val: st:sourceFileBase);
				local String is basesRef: 'null';
				if({ st:baseNames:length() > 0 }, {
					local String is bItems: '';
					local Int is bi: 0;
					while({ bi < st:baseNames:length() }, {
						local String is bn: st:baseNames:get(index: bi, default: '');
						local String is bSym: '@.bname.' . st:name . '.' . (bi as String);
						out: out . :emitCStrGlobal(sym: bSym, val: bn);
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
						out: out . :emitCStrGlobal(sym: mSym, val: mn);
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

				local String is fieldsRef: 'null';
				if({ st:metaFieldNames:length() > 0 }, {
					local String is mfItems: '';
					local Int is mfi: 0;
					while({ mfi < st:metaFieldNames:length() }, {
						local String is mfnm: st:metaFieldNames:get(index: mfi, default: '');
						local String is mfty: st:metaFieldTypes:get(index: mfi, default: '');
						local Int is mfidx: st:metaFieldIndices:get(index: mfi, default: 0);
						local Int is mffl: st:metaFieldFlags:get(index: mfi, default: 0);
						local String is fnSym: '@.fname.' . st:name . '.' . (mfi as String);
						local String is ftSym: '@.ftype.' . st:name . '.' . (mfi as String);
						out: out . :emitCStrGlobal(sym: fnSym, val: mfnm);
						out: out . :emitCStrGlobal(sym: ftSym, val: mfty);
						local String is offExpr: 'ptrtoint (ptr getelementptr (%struct.' . st:name . ', ptr null, i32 0, i32 ' . (mfidx as String) . ') to i32)';
						if({ mfi > 0 }, { mfItems: mfItems . ', '; });
						mfItems: mfItems . fieldMetaLayout:formatConst(values: [fnSym, ftSym, offExpr, mffl as String]);
						mfi++;
					});
					out: out . '@.fields.' . st:name . ' = private constant [' . (st:metaFieldNames:length() as String) . ' x ' . fieldMetaType . '] [' . mfItems . "]\n";
					fieldsRef: '@.fields.' . st:name;
				});

				local String is ctorPtr: if({ st:constructFn == 'null' }, { 'null' }, { '@' . st:constructFn });
				out: out . '@.meta.' . st:name . ' = private constant ' . classMetaLayout:formatConst(values: ['@.typename.' . st:name, '@.src.' . st:name, basesRef, st:baseNames:length() as String, ctorPtr, methodsRef, st:metaMethodNames:length() as String, fieldsRef, st:metaFieldNames:length() as String]) . "\n";
				classMetaRefs:add(item: 'ptr @.meta.' . st:name);

				if({ st:heldNames:length() > 0 }, {
					local String is hnItems: '';
					local String is hgItems: '';
					local Int is hi: 0;
					while({ hi < st:heldNames:length() }, {
						local String is hn: st:heldNames:get(index: hi, default: '');
						local String is hSym: '@.hname.' . st:name . '.' . (hi as String);
						out: out . :emitCStrGlobal(sym: hSym, val: hn);
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

			local Int is li: 0;
			while({ li < mod:stringLiterals:length() }, {
				local String is raw: mod:stringLiterals:get(index: li, default: '');
				local Int is byteLen: raw:length() + 1;
				local String is esc: :escapeLlvmBytes(s: raw);
				out: out . '@.str.' . (li as String) . ' = hidden unnamed_addr constant [' . (byteLen as String) . ' x i8] c"' . esc . "\\00\"\n";
				out: out . '@.str.cache.' . (li as String) . " = hidden global ptr null, align 8\n";
				li++;
			});
			if({ mod:stringLiterals:length() > 0 }, { out: out . "\n"; });
			return out;
		});

		# Non-primary shard: external declarations for shared globals, struct types, and strings.
		local Int is egi: 0;
		while({ egi < mod:globalNames:length() }, {
			local String is egn: mod:globalNames:get(index: egi, default: '');
			local IrType is egt: mod:globalTypes:get(index: egi);
			out: out . '@' . egn . ' = external hidden global ' . :llvmType(ty: egt) . "\n";
			egi++;
		});
		local Int is esi: 0;
		while({ esi < mod:structs:length() }, {
			local IrStruct is est: mod:structs:get(index: esi);
			local String is eFields: '';
			local Int is efi: 0;
			while({ efi < est:fieldTypes:length() }, {
				if({ efi > 0 }, { eFields: eFields . ', '; });
				eFields: eFields . :llvmType(ty: est:fieldTypes:get(index: efi));
				efi++;
			});
			out: out . '%struct.' . est:name . ' = type { ' . eFields . " }\n";
			out: out . '@.typename.' . est:name . " = external hidden unnamed_addr constant i8\n";
			out: out . '@.vtable.' . est:name . " = external hidden constant i8\n";
			esi++;
		});
		out: out . "@spec_class_registry = external constant i8\n";
		out: out . "@spec_held_registry = external constant i8\n";
		out: out . "declare i32 @spec_class_registry_count()\n";
		local Int is eli: 0;
		while({ eli < mod:stringLiterals:length() }, {
			out: out . '@.str.' . (eli as String) . " = external hidden unnamed_addr constant i8\n";
			out: out . '@.str.cache.' . (eli as String) . " = external hidden global ptr\n";
			eli++;
		});
		out: out . "\n";
		return out;
	}

	local Function of String is emitFunctionDecl(IrFunction is fn){
		local String is retStr: :llvmType(ty: fn:retType);
		local String is paramsStr: '';
		local Int is pi: 0;
		while({ pi < fn:params:length() }, {
			if({ pi > 0 }, { paramsStr: paramsStr . ', '; });
			local IrParam is p: fn:params:get(index: pi);
			paramsStr: paramsStr . :llvmType(ty: p:ty) . ' ' . p:name;
			pi++;
		});
		return 'declare ' . retStr . ' @' . fn:name . '(' . paramsStr . ")\n";
	}

	## Emits [mod] split across [shards] independent LLVM IR translation units
	## for parallel clang -c compilation. Functions are LPT-balanced by
	## instruction count across shards; shard 0 owns shared globals/metadata.
	Function of Array of String is emitShardsScoped(IrModule is mod, ThreadScope is scope, Int is shards: 1){
		local Int is nFn: mod:functions:length();
		if({ shards <= 1 || nFn <= 1 }, {
			return [:emitModule(mod: mod)];
		});
		local Int is nShards: if({ shards < nFn }, { shards }, { nFn });
		Process:arrayFreeze(a: mod:functions);

		# Compute instruction weight per function and build declare prototypes.
		local Array of Int is weights: [];
		local Array of String is fnDecls: [];
		local Array of Int is sortedIdx: [];
		local Int is i: 0;
		while({ i < nFn }, {
			local IrFunction is f0: mod:functions:get(index: i);
			local Int is w0: 1;
			local Int is bi0: 0;
			while({ bi0 < f0:blocks:length() }, {
				w0: w0 + f0:blocks:get(index: bi0):insts:length();
				bi0++;
			});
			weights:add(item: w0);
			fnDecls:add(item: :emitFunctionDecl(fn: f0));
			sortedIdx:add(item: i);
			i++;
		});
		Process:arrayFreeze(a: fnDecls);

		# Insertion sort function indices by weight descending (LPT).
		local Int is si: 1;
		while({ si < nFn }, {
			local Int is keyIdx: sortedIdx:get(index: si);
			local Int is keyW: weights:get(index: keyIdx);
			local Int is sj: si - 1;
			while({ sj >= 0 && weights:get(index: sortedIdx:get(index: sj)) < keyW }, {
				sortedIdx:set(index: sj + 1, item: sortedIdx:get(index: sj));
				sj: sj - 1;
			});
			sortedIdx:set(index: sj + 1, item: keyIdx);
			si++;
		});

		local Array of Array of Int is buckets: [];
		local Array of Int is bucketWeights: [];
		local Int is b0: 0;
		while({ b0 < nShards }, {
			buckets:add(item: []);
			bucketWeights:add(item: 0);
			b0++;
		});
		local Array of Int is ownerShard: [];
		local Int is oi: 0;
		while({ oi < nFn }, {
			ownerShard:add(item: 0);
			oi++;
		});
		local Int is pi: 0;
		while({ pi < nFn }, {
			local Int is fi: sortedIdx:get(index: pi);
			local Int is fw: weights:get(index: fi);
			local Int is bestB: 0;
			local Int is bestL: bucketWeights:get(index: 0);
			local Int is bi: 1;
			while({ bi < nShards }, {
				local Int is curL: bucketWeights:get(index: bi);
				if({ curL < bestL }, {
					bestL: curL;
					bestB: bi;
				});
				bi++;
			});
			buckets:get(index: bestB):add(item: fi);
			bucketWeights:set(index: bestB, item: bestL + fw);
			ownerShard:set(index: fi, item: bestB);
			pi++;
		});
		Process:arrayFreeze(a: ownerShard);

		# Pre-compute the shared non-primary header once (identical for shards 1..N-1).
		local String is primaryHdr: :emitShardHeader(mod: mod, isPrimary: true);
		local String is secondaryHdr: :emitShardHeader(mod: mod, isPrimary: false);
		local Boolean is dbgFlag: :debugMode;

		local Array of Task of String is shardTasks: [];
		local Int is s: 0;
		while({ s < nShards }, {
			local Int is myShard: s;
			local Array of Int is myFns: buckets:get(index: s);
			local String is myHdr: if({ myShard == 0 }, { primaryHdr }, { secondaryHdr });
			local Task of String is stTask: scope:spawn(task: local Function of String(){
				local LlvmEmitter is wEm: LlvmEmitter:init();
				wEm:debugMode: dbgFlag;
				if({ dbgFlag }, {
					wEm:dbgNodes: [];
					wEm:dbgFileIds: Map:init();
					wEm:dbgLocIds: Map:init();
					wEm:dbgNodes:add(item: '');
					wEm:dbgNodes:add(item: '!1 = !{}');
					wEm:dbgNodes:add(item: '!2 = !DISubroutineType(types: !1)');
				});
				local String is out: myHdr;
				local Int is di: 0;
				while({ di < nFn }, {
					if({ ownerShard:get(index: di) != myShard }, {
						out: out . fnDecls:get(index: di, default: '');
					});
					di++;
				});
				out: out . "\n";
				local Int is k: 0;
				while({ k < myFns:length() }, {
					out: out . wEm:emitFunction(fn: mod:functions:get(index: myFns:get(index: k))) . "\n";
					k++;
				});
				if({ dbgFlag }, {
					out: out . wEm:emitDebugMetadata();
				});
				return out;
			});
			shardTasks:add(item: stTask);
			s++;
		});

		local Array of String is results: [];
		local Int is ri: 0;
		while({ ri < shardTasks:length() }, {
			results:add(item: shardTasks:get(index: ri):await());
			ri++;
		});
		return results;
	}

	Function of String is emitModule(IrModule is mod){
		local String is out: :emitModuleHeader(mod: mod);

		# Functions
		if({ :debugMode }, {
			:dbgNodes: [];
			:dbgFileIds: Map:init();
			:dbgLocIds: Map:init();
			# !0 = DICompileUnit, !1 = !{}, !2 = DISubroutineType
			:dbgNodes:add(item: '');
			:dbgNodes:add(item: '!1 = !{}');
			:dbgNodes:add(item: '!2 = !DISubroutineType(types: !1)');
		});
		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			out: out . :emitFunction(fn: mod:functions:get(index: fi)) . "\n";
			fi++;
		});
		if({ :debugMode }, {
			out: out . :emitDebugMetadata();
		});
		return out;
	}

	## Emits an [IrModule] to LLVM IR text, parallelizing per-function emission
	## across [threads] tasks inside [scope] when debug metadata is disabled.
	Function of String is emitModuleScoped(IrModule is mod, ThreadScope is scope, Int is threads: 1){
		if({ :debugMode || threads <= 1 || mod:functions:length() <= 1 }, {
			return :emitModule(mod: mod);
		});
		Process:arrayFreeze(a: mod:functions);
		local Int is nFn: mod:functions:length();
		local Int is nWorkers: if({ threads < nFn }, { threads }, { nFn });
		local Int is baseCount: nFn / nWorkers;
		local Int is rem: nFn % nWorkers;
		local Array of Task of String is workerTasks: [];
		local Int is curStart: 0;
		local Int is w: 0;
		while({ w < nWorkers }, {
			local Int is cnt: baseCount + if({ w < rem }, { 1 }, { 0 });
			local Int is sIdx: curStart;
			local Int is eIdx: curStart + cnt;
			curStart: eIdx;
			local Task of String is wt: scope:spawn(task: local Function of String(){
				local String is chunk: '';
				local Int is k: sIdx;
				while({ k < eIdx }, {
					chunk: chunk . :emitFunction(fn: mod:functions:get(index: k)) . "\n";
					k++;
				});
				return chunk;
			});
			workerTasks:add(item: wt);
			w++;
		});

		# Emit module header, structs, vtables, registries, and string literals on the calling thread
		local String is out: :emitModuleHeader(mod: mod);

		local Int is wi: 0;
		while({ wi < workerTasks:length() }, {
			local Task of String is t: workerTasks:get(index: wi);
			out: out . t:await();
			wi++;
		});
		return out;
	}

	local Function of Int is internDebugFile(String is path){
		local String is norm: if({ path != '' }, { path }, { '<spec>' });
		if({ :dbgFileIds:has(key: norm) }, {
			return :dbgFileIds:get(key: norm, default: 0);
		});
		local Int is lastSlash: -1;
		local Int is n: norm:length();
		local Int is idx: 0;
		while({ idx < n }, {
			if({ norm:byteAt(index: idx, default: 0) == 47 }, {
				lastSlash: idx;
			});
			idx++;
		});
		local String is dir: '.';
		local String is file: norm;
		if({ lastSlash >= 0 }, {
			dir: if({ lastSlash == 0 }, { '/' }, { norm:substring(start: 0, end: lastSlash) });
			file: norm:substring(start: lastSlash + 1, end: n);
		});
		local Int is id: :dbgNodes:length();
		:dbgNodes:add(item: '!' . (id as String) . ' = !DIFile(filename: "' . :escapeDebugStr(s: file) . '", directory: "' . :escapeDebugStr(s: dir) . '")');
		:dbgFileIds:set(key: norm, value: id);
		return id;
	}

	local Function of Int is internDebugLoc(Int is spId, Int is line){
		local Int is effLine: if({ line > 0 }, { line }, { 1 });
		local String is key: (spId as String) . ':' . (effLine as String);
		if({ :dbgLocIds:has(key: key) }, {
			return :dbgLocIds:get(key: key, default: 0);
		});
		local Int is id: :dbgNodes:length();
		:dbgNodes:add(item: '!' . (id as String) . ' = !DILocation(line: ' . (effLine as String) . ', column: 1, scope: !' . (spId as String) . ')');
		:dbgLocIds:set(key: key, value: id);
		return id;
	}

	local Function of String is escapeDebugStr(String is s){
		local String is res: '';
		local Int is len: s:length();
		local Int is i: 0;
		while({ i < len }, {
			local Int is b: s:byteAt(index: i, default: 0);
			if({ b == 34 }, {
				res: res . '\\"';
			}, {
				if({ b == 92 }, {
					res: res . '\\\\';
				}, {
					res: res . s:substring(start: i, end: i + 1);
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
		if({ :dbgNodes:length() <= 3 }, {
			cuFileId: :internDebugFile(path: 'main.spec');
		}, {
			cuFileId: 3;
		});
		local Int is dwarfVerId: :dbgNodes:length();
		:dbgNodes:add(item: '!' . (dwarfVerId as String) . ' = !{i32 7, !"Dwarf Version", i32 5}');
		local Int is dbgVerId: :dbgNodes:length();
		:dbgNodes:add(item: '!' . (dbgVerId as String) . ' = !{i32 2, !"Debug Info Version", i32 3}');
		:dbgNodes:set(index: 0, item: '!0 = distinct !DICompileUnit(language: DW_LANG_C99, file: !' . (cuFileId as String) . ', producer: "spec", isOptimized: false, runtimeVersion: 0, emissionKind: LineTablesOnly, enums: !1, splitDebugInlining: false, nameTableKind: None)');

		local String is out: "!llvm.dbg.cu = !{!0}\n";
		out: out . '!llvm.module.flags = !{!' . (dwarfVerId as String) . ', !' . (dbgVerId as String) . "}\n\n";
		local Int is ni: 0;
		while({ ni < :dbgNodes:length() }, {
			out: out . :dbgNodes:get(index: ni, default: '') . "\n";
			ni++;
		});
		return out;
	}

	local Function of String is emitCStrGlobal(String is sym, String is val){
		local Int is byteLen: val:length() + 1;
		local String is esc: :escapeLlvmBytes(s: val);
		return sym . ' = private unnamed_addr constant [' . (byteLen as String) . ' x i8] c"' . esc . "\\00\"\n";
	}

	local Function of String is escapeLlvmBytes(Str is s){
		local Str is hex: '0123456789ABCDEF';
		local String is res: '';
		local Int is len: s:length();
		local Int is i: 0;
		while({ i < len }, {
			local Int is b: s:byteAt(index: i, default: 0);
			if({ b < 32 || b >= 127 || b == 34 || b == 92 }, {
				local Int is hi: (b >> 4) & 15;
				local Int is lo: b & 15;
				res: res . '\\' . hex:substring(start: hi, end: hi + 1) . hex:substring(start: lo, end: lo + 1);
			}, {
				res: res . s:substring(start: i, end: i + 1);
			});
			i++;
		});
		return res;
	}

	local Function of String is emitFunction(IrFunction is fn){
		local String is retStr: :llvmType(ty: fn:retType);
		local String is paramsStr: '';
		local Int is pi: 0;
		while({ pi < fn:params:length() }, {
			if({ pi > 0 }, { paramsStr: paramsStr . ', '; });
			local IrParam is p: fn:params:get(index: pi);
			paramsStr: paramsStr . :llvmType(ty: p:ty) . ' ' . p:name;
			pi++;
		});

		if({ fn:isExternal }, {
			return 'declare ' . retStr . ' @' . fn:name . '(' . paramsStr . ")\n";
		});

		local String is inlineAttr: '';
		if({ fn:alwaysInline && !:debugMode }, {
			inlineAttr: ' alwaysinline';
		});

		local Int is spId: -1;
		local String is spAttr: '';
		if({ :debugMode && fn:sourceFile != '' }, {
			local Int is fileId: :internDebugFile(path: fn:sourceFile);
			local Int is fnLine: if({ fn:line > 0 }, { fn:line }, { 1 });
			spId: :dbgNodes:length();
			:dbgNodes:add(item: '!' . (spId as String) . ' = distinct !DISubprogram(name: "' . :escapeDebugStr(s: fn:name) . '", scope: !' . (fileId as String) . ', file: !' . (fileId as String) . ', line: ' . (fnLine as String) . ', type: !2, scopeLine: ' . (fnLine as String) . ', spFlags: DISPFlagDefinition, unit: !0)');
			spAttr: ' !dbg !' . (spId as String);
		});

		local String is out: 'define ' . retStr . ' @' . fn:name . '(' . paramsStr . ')' . inlineAttr . spAttr . " {\n";
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			out: out . blk:label . ":\n";
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local String is instStr: :emitInst(inst: blk:insts:get(index: ii));
				if({ spId >= 0 }, {
					local Int is ln: blk:instLines:get(index: ii, default: 0);
					if({ ln <= 0 }, { ln: fn:line; });
					local Int is locId: :internDebugLoc(spId: spId, line: ln);
					instStr: :appendDbgToInst(ir: instStr, locId: locId);
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
				return slot . ' = alloca ' . :llvmType(ty: ty);
			},
			IrInst:Load: local Function of String(String is dst, String is slot, IrType is ty){
				local String is t: :llvmType(ty: ty);
				return dst . ' = load ' . t . ', ptr ' . slot;
			},
			IrInst:Store: local Function of String(String is slot, String is val, IrType is ty){
				local String is t: :llvmType(ty: ty);
				return 'store ' . t . ' ' . val . ', ptr ' . slot;
			},
			IrInst:BinOp: local Function of String(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
				local String is t: :llvmType(ty: ty);
				local String is llvmOp: :llvmBinOp(op: op, ty: ty);
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
				local String is t: :llvmType(ty: ty);
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
				if({ op == 'u<' }, { ipred: 'ult'; });
				if({ op == 'u<=' }, { ipred: 'ule'; });
				if({ op == 'u>' }, { ipred: 'ugt'; });
				if({ op == 'u>=' }, { ipred: 'uge'; });
				return dst . ' = icmp ' . ipred . ' ' . t . ' ' . lhs . ', ' . rhs;
			},
			IrInst:IrCall: local Function of String(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
				local String is argsStr: '';
				local Int is ai: 0;
				while({ ai < args:length() }, {
					if({ ai > 0 }, { argsStr: argsStr . ', '; });
					argsStr: argsStr . :llvmType(ty: argTypes:get(index: ai)) . ' ' . args:get(index: ai, default: '');
					ai++;
				});
				local String is rt: :llvmType(ty: retType);
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
					argsStr: argsStr . :llvmType(ty: argTypes:get(index: ai)) . ' ' . args:get(index: ai, default: '');
					ai++;
				});
				local String is rt: :llvmType(ty: retType);
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
					return dst . ' = inttoptr ' . :llvmType(ty: fromType) . ' ' . val . ' to ptr';
				});
				if({ fromType == IrType:Ptr && (toType == IrType:I64 || toType == IrType:I1) }, {
					return dst . ' = ptrtoint ptr ' . val . ' to ' . :llvmType(ty: toType);
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
				return dst . ' = bitcast ' . :llvmType(ty: fromType) . ' ' . val . ' to ' . :llvmType(ty: toType);
			},
			IrInst:Retain: local Function of String(String is val){
				return 'call ptr @spec_rt_retain(ptr ' . val . ')';
			},
			IrInst:Release: local Function of String(String is val){
				return 'call void @spec_rt_release(ptr ' . val . ')';
			},
			IrInst:Ret: local Function of String(Boolean is hasVal, String is val, IrType is ty){
				if({ hasVal }, {
					return 'ret ' . :llvmType(ty: ty) . ' ' . val;
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
		if({ op == 'u/' }, { return 'udiv'; });
		if({ op == 'u%' }, { return 'urem'; });
		if({ op == '&' || op == '&&' }, { return 'and'; });
		if({ op == '|' || op == '||' }, { return 'or'; });
		if({ op == '^' }, { return 'xor'; });
		if({ op == '<<' }, { return 'shl'; });
		if({ op == '>>' }, { return 'ashr'; });
		if({ op == '>>>' }, { return 'lshr'; });
		return 'add';
	}
}
