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
		local String is out: "; Spec LLVM IR (experimental)\n\n";

		# Runtime declarations and empty reflection registry stubs for spec_runtime.o
		out: out . "declare ptr @spec_rt_alloc(i64, ptr)\n";
		out: out . "declare ptr @spec_rt_retain(ptr)\n";
		out: out . "declare void @spec_rt_release(ptr)\n";
		out: out . "declare ptr @spec_rt_closure_new(ptr, ptr, ptr)\n";
		out: out . "declare ptr @spec_rt_box_new(i64, i1)\n";
		out: out . "declare ptr @spec_string_intern(ptr)\n";
		out: out . "declare ptr @spec_string_concat(ptr, ptr)\n";
		out: out . "declare i1 @spec_string_equals(ptr, ptr)\n";
		out: out . "declare i64 @spec_string_length(ptr)\n";
		out: out . "declare ptr @spec_string_substring(ptr, i64, i64)\n";
		out: out . "declare i64 @spec_string_index_of(ptr, ptr, i64)\n";
		out: out . "declare ptr @spec_to_string_int(i64)\n";
		out: out . "declare void @spec_print_line(ptr)\n";
		out: out . "declare void @spec_process_exit(i64)\n";
		out: out . "declare ptr @spec_array_new()\n";
		out: out . "declare ptr @spec_array_new_object()\n";
		out: out . "declare void @spec_array_add(ptr, ptr)\n";
		out: out . "declare void @spec_array_add_object(ptr, ptr)\n";
		out: out . "declare i64 @spec_array_length(ptr)\n";
		out: out . "declare ptr @spec_array_get(ptr, i64)\n";
		out: out . "declare void @spec_array_set(ptr, i64, ptr)\n";
		out: out . "declare ptr @spec_map_new()\n";
		out: out . "declare ptr @spec_map_new_object()\n";
		out: out . "declare void @spec_map_set(ptr, ptr, ptr)\n";
		out: out . "declare ptr @spec_map_get(ptr, ptr, ptr)\n";
		out: out . "declare i1 @spec_map_has(ptr, ptr)\n";
		out: out . "declare i64 @spec_map_length(ptr)\n";
		out: out . "%struct.SpecClosure = type { ptr, ptr, ptr }\n";
		out: out . "@spec_class_registry = constant [1 x ptr] zeroinitializer\n";
		out: out . "@spec_held_registry = constant [1 x { ptr, ptr, i32, ptr }] zeroinitializer\n";
		out: out . "define i32 @spec_class_registry_count() {\n  ret i32 0\n}\n\n";

		# Struct types
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
			local Int is tnLen: st:name:length() + 1;
			local String is tnEsc: self:escapeLlvmBytes(s: st:name);
			out: out . '@.typename.' . st:name . ' = private unnamed_addr constant [' . (tnLen as String) . ' x i8] c"' . tnEsc . "\\00\"\n";
			si++;
		});
		if({ mod:structs:length() > 0 }, { out: out . "\n"; });

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
				local String is szPtr: dst . '_szp';
				local String is szVal: dst . '_sz';
				local String is tnPtr: dst . '_tnp';
				return szPtr . ' = getelementptr %struct.' . structName . ", ptr null, i32 1\n  "
					. szVal . ' = ptrtoint ptr ' . szPtr . " to i64\n  "
					. dst . ' = call ptr @spec_rt_alloc(i64 ' . szVal . ', ptr ' . destroyFn . ")\n  "
					. tnPtr . ' = getelementptr inbounds %struct.' . structName . ', ptr ' . dst . ", i32 0, i32 0\n  "
					. 'store ptr @.typename.' . structName . ', ptr ' . tnPtr;
			},
			IrInst:FieldPtr: local Function of String(String is dst, String is objPtr, String is structName, Int is fieldIndex){
				return dst . ' = getelementptr inbounds %struct.' . structName . ', ptr ' . objPtr . ', i32 0, i32 ' . (fieldIndex as String);
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
