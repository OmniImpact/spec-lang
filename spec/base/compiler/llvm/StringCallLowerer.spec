#! Package base:compiler:llvm
#! Lowers String runtime method calls (length, contains, substring) to Spec IR.

Class of CallLowerer is StringCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'StringCallLowerer';
	}

	replace Function of Int is order(){
		return 20;
	}

	local Function of Boolean is isSysBufTarget(CallData is call){
		if({ call:bareProvider:endsWith(suffix: ':sysinternal:Buf') }, { return true; });
		local Boolean is ok: false;
		match(on: call:target, when: [
			Expression:Path: local Function(Array of String is segs){
				local Int is n: segs:length();
				if({ n >= 2 && segs:get(index: n - 1, default: '') == 'Buf' && segs:get(index: n - 2, default: '') == 'sysinternal' }, {
					ok: true;
				});
			}
		], default: {});
		return ok;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		local Boolean is isBuf: self:isSysBufTarget(call: call);
		local Boolean is isStrIdent: false;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tn){
				if({ tn == 'String' }, { isStrIdent: true; });
			}
		], default: {});
		if({ isBuf }, {
			if({ nm == 'init' || nm == 'bufLength' || nm == 'bufGetByte' || nm == 'bufCountByte' || nm == 'bufAppendBuf' || nm == 'intern' || nm == 'stringCopy' || nm == 'stringIndexOf' || nm == 'stringIndexOfFrom' || nm == 'stringSubstring' }, { return true; });
			return false;
		});
		if({ isStrIdent && nm == 'fromCharCode' && call:args:length() >= 1 }, { return true; });
		if({ isStrIdent && nm == 'newline' && call:args:length() == 0 }, { return true; });
		if({ nm == 'toBase' && call:target:resolvedType == 'Int' }, { return true; });
		if({ call:target:resolvedType != 'String' }, { return false; });
		local Int is argc: call:args:length();
		if({ nm == 'length' && argc == 0 }, { return true; });
		if({ nm == 'indexOf' && argc >= 1 }, { return true; });
		if({ nm == 'substring' && argc >= 2 }, { return true; });
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		local Boolean is isBuf: self:isSysBufTarget(call: call);
		if({ nm == 'newline' }, {
			local Int is sidNl: b:mod:internStringLiteral(value: "\n");
			local String is dstNl: b:nextTmp();
			b:emit(inst: IrInst:ConstString(dst: dstNl, strId: sidNl));
			return dstNl;
		});
		if({ nm == 'toBase' && call:target:resolvedType == 'Int' }, {
			local String is iv: b:lowerExpr(expr: call:target);
			local String is baseV: '10';
			local String is digV: '0';
			if({ call:args:length() >= 1 }, {
				local NamedArg is na0: call:args:get(index: 0);
				if({ na0:name == 'digits' }, { digV: b:lowerExpr(expr: na0:value); }, { baseV: b:lowerExpr(expr: na0:value); });
			});
			if({ call:args:length() >= 2 }, {
				local NamedArg is na1: call:args:get(index: 1);
				if({ na1:name == 'base' }, { baseV: b:lowerExpr(expr: na1:value); }, { digV: b:lowerExpr(expr: na1:value); });
			});
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_int_to_base', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [iv, baseV, digV]));
			b:emitClaimPool(val: dst);
			return dst;
		});
		if({ isBuf }, {
			if({ nm == 'init' }, { return 'null'; });
			local NamedArg is ba0: call:args:get(index: 0);
			local String is bufArg: b:lowerExpr(expr: ba0:value);
			if({ nm == 'bufLength' }, {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_buf_length', argTypes: [IrType:Ptr], args: [bufArg]));
				return dst;
			});
			if({ nm == 'stringCopy' }, {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_copy', argTypes: [IrType:Ptr], args: [bufArg]));
				b:emitClaimPool(val: dst);
				return dst;
			});
			if({ nm == 'intern' }, {
				local String is cstr: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: cstr, hasDst: true, retType: IrType:Ptr, callee: 'spec_buf_to_cstring', argTypes: [IrType:Ptr], args: [bufArg]));
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_intern', argTypes: [IrType:Ptr], args: [cstr]));
				return dst;
			});
			if({ nm == 'bufAppendBuf' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local String is srcArg: b:lowerExpr(expr: ba1:value);
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_buf_append_buf', argTypes: [IrType:Ptr, IrType:Ptr], args: [bufArg, srcArg]));
				return '0';
			});
			if({ nm == 'bufCountByte' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local String is byteArg: b:lowerExpr(expr: ba1:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_buf_count_byte', argTypes: [IrType:Ptr, IrType:I64], args: [bufArg, byteArg]));
				return dst;
			});
			if({ nm == 'bufGetByte' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local NamedArg is ba2: call:args:get(index: 2);
				local String is idxArg: b:lowerExpr(expr: ba1:value);
				local String is defArg: b:lowerExpr(expr: ba2:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_buf_get_byte', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [bufArg, idxArg, defArg]));
				return dst;
			});
			if({ nm == 'stringIndexOf' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local NamedArg is ba2: call:args:get(index: 2);
				local String is ndlArg: b:lowerExpr(expr: ba1:value);
				local String is defArg: b:lowerExpr(expr: ba2:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_index_of', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: [bufArg, ndlArg, defArg]));
				return dst;
			});
			if({ nm == 'stringIndexOfFrom' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local NamedArg is ba2: call:args:get(index: 2);
				local NamedArg is ba3: call:args:get(index: 3);
				local String is ndlArg: b:lowerExpr(expr: ba1:value);
				local String is fromArg: b:lowerExpr(expr: ba2:value);
				local String is defArg: b:lowerExpr(expr: ba3:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_index_of_from', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:I64], args: [bufArg, ndlArg, fromArg, defArg]));
				return dst;
			});
			if({ nm == 'stringSubstring' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local NamedArg is ba2: call:args:get(index: 2);
				local String is stArg: b:lowerExpr(expr: ba1:value);
				local String is enArg: b:lowerExpr(expr: ba2:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_substring', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [bufArg, stArg, enArg]));
				b:emitClaimPool(val: dst);
				return dst;
			});
		});
		if({ nm == 'fromCharCode' }, {
			local NamedArg is na0: call:args:get(index: 0);
			local String is codeVal: b:lowerExpr(expr: na0:value);
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_from_char_code', argTypes: [IrType:I64], args: [codeVal]));
			b:emitClaimPool(val: dst);
			return dst;
		});
		local String is sRecv: b:lowerExpr(expr: call:target);
		local String is res: '0';
		match(on: call:name, when: [
			'length': {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_length', argTypes: [IrType:Ptr], args: [sRecv]));
				res: dst;
			},
			'indexOf': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is needle: b:lowerExpr(expr: na0:value);
				local String is defVal: '-1';
				if({ call:args:length() >= 2 }, {
					local NamedArg is na1: call:args:get(index: 1);
					defVal: b:lowerExpr(expr: na1:value);
				});
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_index_of', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: [sRecv, needle, defVal]));
				res: dst;
			},
			'substring': {
				local NamedArg is na0: call:args:get(index: 0);
				local NamedArg is na1: call:args:get(index: 1);
				local String is st: b:lowerExpr(expr: na0:value);
				local String is en: b:lowerExpr(expr: na1:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_substring', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [sRecv, st, en]));
				b:emitClaimPool(val: dst);
				res: dst;
			}
		]);
		return res;
	}
}
