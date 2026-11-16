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
		['base', 'compiler', 'llvm', LlvmStructLayout],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

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

	Function of String is emitModule(IrModule is mod){
		local String is out: '''
; Spec LLVM IR (experimental)

declare ptr @spec_rt_alloc(i64, ptr)
declare ptr @spec_rt_retain(ptr)
declare void @spec_rt_release(ptr)
declare i64 @spec_pool_frame()
declare void @spec_pool_release_to(i64)
declare ptr @spec_claim_pool(ptr)
declare ptr @spec_rt_closure_new(ptr, ptr, ptr)
declare ptr @spec_rt_box_new(i64, i1)
declare ptr @spec_string_intern(ptr)
declare ptr @spec_string_concat(ptr, ptr)
declare i1 @spec_string_equals(ptr, ptr)
declare i64 @spec_string_length(ptr)
declare ptr @spec_string_substring(ptr, i64, i64)
declare i64 @spec_string_index_of(ptr, ptr, i64)
declare ptr @spec_to_string_int(i64)
declare ptr @spec_to_string_float(double)
declare ptr @spec_to_string_bool(i1)
declare ptr @spec_int_to_base(i64, i64, i64)
declare ptr @spec_type_name(ptr)
declare void @spec_panic_cast(ptr, ptr)
declare i32 @strcmp(ptr, ptr)
define internal i1 @__spec_cstr_eq(ptr %a, ptr %b) {
  %r = call i32 @strcmp(ptr %a, ptr %b)
  %eq = icmp eq i32 %r, 0
  ret i1 %eq
}
declare void @spec_print(ptr)
declare void @spec_print_line(ptr)
declare void @spec_process_exit(i64)
declare ptr @spec_process_os_name()
declare i64 @spec_process_get_pid()
declare i64 @spec_clock_ms()
declare i1 @spec_file_exists(ptr)
declare i1 @spec_file_remove(ptr)
declare ptr @spec_file_read(ptr, ptr, ptr, ptr)
declare i1 @spec_file_write(ptr, ptr, ptr, ptr)
declare ptr @spec_dir_list_cb(ptr, ptr)
declare ptr @spec_exe_dir()
declare i64 @spec_file_size(ptr)
declare i64 @spec_time_monotonic_ns()
declare i64 @spec_time_monotonic_us()
declare i64 @spec_time_monotonic_ms()
declare i64 @spec_time_epoch_ms()
declare i64 @spec_time_epoch_ns()
declare void @spec_time_sleep_ms(i64)
declare void @spec_time_sleep_us(i64)
declare void @spec_time_sleep_ns(i64)
declare i64 @spec_time_local_offset_sec(i64)
declare double @sqrt(double)
declare double @fma(double, double, double)
declare double @spec_math_sin(double)
declare double @spec_math_cos(double)
declare double @spec_math_tan(double)
declare double @spec_math_atan2(double, double)
declare double @spec_math_log(double)
declare double @spec_math_log2(double)
declare double @spec_math_pow(double, double)
declare double @spec_math_exp(double)
declare double @spec_math_log10(double)
declare double @spec_math_cbrt(double)
declare double @spec_math_asin(double)
declare double @spec_math_acos(double)
declare double @spec_math_atan(double)
declare double @spec_math_random(double, double)
declare ptr @spec_array_new()
declare ptr @spec_array_new_object()
declare void @spec_array_add(ptr, ptr)
declare void @spec_array_add_object(ptr, ptr)
declare i64 @spec_array_length(ptr)
declare ptr @spec_array_get(ptr, i64)
declare void @spec_array_set(ptr, i64, ptr)
declare ptr @spec_map_new()
declare ptr @spec_map_new_object()
declare void @spec_map_set(ptr, ptr, ptr)
declare ptr @spec_map_get(ptr, ptr, ptr)
declare i1 @spec_map_has(ptr, ptr)
declare i64 @spec_map_length(ptr)
%struct.SpecClosure = type { ptr, ptr, ptr }

''';

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
			li++;
		});
		if({ mod:stringLiterals:length() > 0 }, { out: out . "\n"; });

		# Functions
		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			out: out . self:emitFunction(fn: mod:functions:get(index: fi)) . "\n";
			fi++;
		});
		return out;
	}

	local Function of String is emitCStrGlobal(String is sym, String is val){
		local Int is byteLen: val:length() + 1;
		local String is esc: self:escapeLlvmBytes(s: val);
		return sym . ' = private unnamed_addr constant [' . (byteLen as String) . ' x i8] c"' . esc . "\\00\"\n";
	}

	local Function of String is escapeLlvmBytes(String is s){
		local String is res: '';
		local Int is i: 0;
		while({ i < s:length() }, {
			local String is ch: s:charAt(index: i, default: '');
			if({ ch == '\\' }, { res: res . '\\5C'; }, {
				if({ ch == '"' }, { res: res . '\\22'; }, {
					if({ ch == "\n" }, { res: res . '\\0A'; }, {
						if({ ch == "\r" }, { res: res . '\\0D'; }, {
							if({ ch == "\t" }, { res: res . '\\09'; }, {
								res: res . ch;
							});
						});
					});
				});
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

		local String is out: 'define ' . retStr . ' @' . fn:name . '(' . paramsStr . ") {\n";
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			out: out . blk:label . ":\n";
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				out: out . '  ' . self:emitInst(inst: blk:insts:get(index: ii)) . "\n";
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
				return dst . ' = call ptr @spec_string_intern(ptr @.str.' . (strId as String) . ')';
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
