#! Package base:compiler:llvm
#! Lowers a type-checked Spec ProgramNode AST into backend-agnostic Spec IR.

Class is IrBuilder{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'compiler', 'ir', IrFunction],
		['base', 'compiler', 'ir', IrStruct],
		['base', 'compiler', 'ir', IrModule],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	IrModule is mod: IrModule:init();
	Int is tmpCounter: 0;
	Int is lblCounter: 0;
	String is currentClass: '';
	IrFunction is curFn: IrFunction:init();
	IrBlock is curBlk: IrBlock:init();
	Boolean is blkTerminated: false;
	Map of String to String is localSlots: Map:init();
	Map of String to IrType is localTypes: Map:init();

	replace Function is init(){
	}

	Function of String is nextTmp(){
		self:tmpCounter: self:tmpCounter + 1;
		return '%t' . (self:tmpCounter as String);
	}

	Function of String is nextLabel(String is prefix){
		self:lblCounter: self:lblCounter + 1;
		return prefix . '_' . (self:lblCounter as String);
	}

	Function of IrType is irTypeFor(String is specType){
		if({ specType == 'Int' }, { return IrType:I64; });
		if({ specType == 'Float' }, { return IrType:F64; });
		if({ specType == 'Boolean' }, { return IrType:I1; });
		if({ specType == 'Void' || specType == '' }, { return IrType:Void; });
		return IrType:Ptr;
	}

	Function is emit(IrInst is inst){
		if({ !self:blkTerminated }, {
			self:curBlk:append(inst: inst);
		});
	}

	Function is terminate(IrInst is inst){
		if({ !self:blkTerminated }, {
			self:curBlk:append(inst: inst);
			self:blkTerminated: true;
		});
	}

	Function is switchBlock(IrBlock is blk){
		self:curBlk: blk;
		self:blkTerminated: false;
	}

	local Function of Boolean is isStdlibClass(ClassInfo is cls){
		local String is sf: cls:sourceFile;
		if({ sf:startsWith(prefix: 'spec/lib/') || sf:startsWith(prefix: 'spec/base/') }, { return true; });
		if({ sf:contains(needle: '/spec/lib/') || sf:contains(needle: '/spec/base/') }, { return true; });
		if({ sf:startsWith(prefix: 'spec\\lib\\') || sf:startsWith(prefix: 'spec\\base\\') }, { return true; });
		if({ sf:contains(needle: '\\spec\\lib\\') || sf:contains(needle: '\\spec\\base\\') }, { return true; });
		return false;
	}

	Function of IrModule is buildProgram(ProgramNode is program, String is entryClass){
		self:mod: IrModule:init();
		self:mod:entryFunction: entryClass;

		# 1. Register structs for user classes (deduplicated by name)
		local Map of String to Boolean is seenStructs: Map:init();
		local Int is ci: 0;
		while({ ci < program:classes:length() }, {
			local ClassInfo is cls: program:classes:get(index: ci);
			if({ !self:isStdlibClass(cls: cls) && !seenStructs:has(key: cls:name) }, {
				seenStructs:set(key: cls:name, value: true);
				local IrStruct is st: IrStruct:init(name: cls:name);
				# Header layout: _type_name (Ptr), _vtable (Ptr)
				st:addField(name: '_type_name', ty: IrType:Ptr);
				st:addField(name: '_vtable', ty: IrType:Ptr);
				local Int is mi: 0;
				while({ mi < cls:members:length() }, {
					local Member is m: cls:members:get(index: mi);
					if({ m:kind == MemberKind:FIELD }, {
						local IrType is fty: self:irTypeFor(specType: m:memberType:name);
						if({ fty == IrType:Void }, { fty: IrType:Ptr; });
						st:addField(name: m:name, ty: fty);
					});
					mi++;
				});
				self:mod:addStruct(s: st);
			});
			ci++;
		});

		# 2. Lower methods for each class (deduplicated by mangled name)
		local Map of String to Boolean is seenFns: Map:init();
		ci: 0;
		while({ ci < program:classes:length() }, {
			local ClassInfo is cls: program:classes:get(index: ci);
			if({ !self:isStdlibClass(cls: cls) }, {
				self:currentClass: cls:name;
				local Int is mi: 0;
				while({ mi < cls:members:length() }, {
					local Member is m: cls:members:get(index: mi);
					if({ m:kind == MemberKind:METHOD }, {
						local String is fnName: cls:name . '_' . m:name;
						if({ !seenFns:has(key: fnName) }, {
							seenFns:set(key: fnName, value: true);
							self:buildMethod(cls: cls, m: m);
						});
					});
					mi++;
				});
			});
			ci++;
		});

		# 3. Emit C main() entry shim if entryClass is non-empty
		if({ entryClass != '' }, {
			self:buildMainEntry(entryClass: entryClass);
		});

		return self:mod;
	}

	local Function is buildMainEntry(String is entryClass){
		local IrFunction is mainFn: IrFunction:init(name: 'main', retType: IrType:I64);
		mainFn:addParam(name: '%argc', ty: IrType:I64);
		mainFn:addParam(name: '%argv', ty: IrType:Ptr);
		local IrBlock is entry: mainFn:addBlock(label: 'entry');
		self:curFn: mainFn;
		self:switchBlock(blk: entry);

		# Allocate entry object (64 bytes minimum for SpecHeader + fields) and call Entry_init(obj, null)
		local String is obj: self:nextTmp();
		self:emit(inst: IrInst:AllocObj(dst: obj, structName: entryClass, destroyFn: 'null'));
		local Array of IrType is initArgTypes: [IrType:Ptr, IrType:Ptr];
		local Array of String is initArgs: [obj, 'null'];
		self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: entryClass . '_init', argTypes: initArgTypes, args: initArgs));
		local String is zero: self:nextTmp();
		self:emit(inst: IrInst:ConstInt(dst: zero, value: 0));
		self:terminate(inst: IrInst:Ret(hasVal: true, val: zero, ty: IrType:I64));
		self:mod:addFunction(fn: mainFn);
	}

	local Function of IrType is methodReturnType(Type is mt){
		if({ mt:name == 'Function' }, {
			if({ mt:params:length() > 0 }, {
				local Type is rt: mt:params:get(index: 0);
				return self:irTypeFor(specType: rt:name);
			});
			return IrType:Void;
		});
		return self:irTypeFor(specType: mt:name);
	}

	local Function is buildMethod(ClassInfo is cls, Member is m){
		local IrType is retTy: self:methodReturnType(mt: m:memberType);
		local String is fnName: cls:name . '_' . m:name;
		local IrFunction is fn: IrFunction:init(name: fnName, retType: retTy);
		fn:addParam(name: '%self', ty: IrType:Ptr);
		local Int is pi: 0;
		while({ pi < m:params:length() }, {
			local Parameter is p: m:params:get(index: pi);
			fn:addParam(name: '%p_' . p:name, ty: self:irTypeFor(specType: p:paramType:name));
			pi++;
		});

		local IrBlock is entry: fn:addBlock(label: 'entry');
		self:curFn: fn;
		self:switchBlock(blk: entry);
		self:tmpCounter: 0;
		self:lblCounter: 0;
		self:localSlots: Map:init();
		self:localTypes: Map:init();

		# Bind 'self' and params into stack slots
		self:localSlots:set(key: 'self', value: '%self_slot');
		self:localTypes:set(key: 'self', value: IrType:Ptr);
		self:emit(inst: IrInst:Alloca(slot: '%self_slot', ty: IrType:Ptr));
		self:emit(inst: IrInst:Store(slot: '%self_slot', val: '%self', ty: IrType:Ptr));

		pi: 0;
		while({ pi < m:params:length() }, {
			local Parameter is p: m:params:get(index: pi);
			local IrType is pty: self:irTypeFor(specType: p:paramType:name);
			local String is slot: '%slot_' . p:name;
			self:localSlots:set(key: p:name, value: slot);
			self:localTypes:set(key: p:name, value: pty);
			self:emit(inst: IrInst:Alloca(slot: slot, ty: pty));
			self:emit(inst: IrInst:Store(slot: slot, val: '%p_' . p:name, ty: pty));
			pi++;
		});

		self:lowerStmts(stmts: m:body);

		if({ !self:blkTerminated }, {
			if({ retTy == IrType:Void }, {
				self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
			}, {
				local String is defVal: self:emitDefaultVal(ty: retTy);
				self:terminate(inst: IrInst:Ret(hasVal: true, val: defVal, ty: retTy));
			});
		});

		self:mod:addFunction(fn: fn);
	}

	local Function of String is emitDefaultVal(IrType is ty){
		local String is tmp: self:nextTmp();
		if({ ty == IrType:I64 }, {
			self:emit(inst: IrInst:ConstInt(dst: tmp, value: 0));
			return tmp;
		});
		if({ ty == IrType:F64 }, {
			self:emit(inst: IrInst:ConstFloat(dst: tmp, text: '0.0'));
			return tmp;
		});
		if({ ty == IrType:I1 }, {
			self:emit(inst: IrInst:ConstBool(dst: tmp, value: false));
			return tmp;
		});
		return 'null';
	}

	local Function is lowerStmts(Array of Statement is stmts){
		local Int is i: 0;
		while({ i < stmts:length() && !self:blkTerminated }, {
			self:lowerStmt(stmt: stmts:get(index: i));
			i++;
		});
	}

	local Function is lowerStmt(Statement is stmt){
		match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				local IrType is vty: self:irTypeFor(specType: varType:name);
				local String is slot: '%var_' . varName . '_' . (self:nextTmp());
				# Clean '%' from slot suffix so LLVM identifier is valid
				slot: '%var_' . varName . '_' . (self:tmpCounter as String);
				self:localSlots:set(key: varName, value: slot);
				self:localTypes:set(key: varName, value: vty);
				self:emit(inst: IrInst:Alloca(slot: slot, ty: vty));
				if({ hasInit }, {
					local String is val: self:lowerExpr(expr: initExpr);
					self:emit(inst: IrInst:Store(slot: slot, val: val, ty: vty));
				}, {
					local String is defVal: self:emitDefaultVal(ty: vty);
					self:emit(inst: IrInst:Store(slot: slot, val: defVal, ty: vty));
				});
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				local String is val: self:lowerExpr(expr: assignValue);
				match(on: assignTarget, when: [
					Expression:Ident: local Function(String is name){
						if({ self:localSlots:has(key: name) }, {
							local String is slot: self:localSlots:get(key: name, default: '');
							local IrType is ty: self:localTypes:get(key: name, default: IrType:I64);
							self:emit(inst: IrInst:Store(slot: slot, val: val, ty: ty));
						});
					},
					Expression:FieldAccess: local Function(Expression is target, String is fieldName){
						local String is obj: self:lowerExpr(expr: target);
						local IrStruct is st: self:mod:findStruct(name: self:currentClass);
						local Int is fidx: st:fieldIndex(name: fieldName);
						if({ fidx >= 0 }, {
							local IrType is fty: st:fieldTypes:get(index: fidx);
							local String is ptr: self:nextTmp();
							self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: self:currentClass, fieldIndex: fidx));
							self:emit(inst: IrInst:Store(slot: ptr, val: val, ty: fty));
						});
					}
				], default: {});
			},
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ hasReturnExpr }, {
					local String is val: self:lowerExpr(expr: returnExpr);
					if({ val == '' && self:curFn:retType != IrType:Void }, {
						val: self:emitDefaultVal(ty: self:curFn:retType);
					});
					self:terminate(inst: IrInst:Ret(hasVal: true, val: val, ty: self:curFn:retType));
				}, {
					self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
				});
			},
			Statement:Expr: local Function(Expression is exprStmt){
				local String is _u0: self:lowerExpr(expr: exprStmt);
			}
		], default: {});
	}

	local Function of String is lowerExpr(Expression is expr){
		return match(on: expr, when: [
			Expression:NumberLit: local Function(Int is value, String is text){
				local Int is v: value;
				if({ text != '' }, { v: text as Int; });
				local String is dst: self:nextTmp();
				self:emit(inst: IrInst:ConstInt(dst: dst, value: v));
				return dst;
			},
			Expression:FloatLit: local Function(String is text){
				local String is dst: self:nextTmp();
				self:emit(inst: IrInst:ConstFloat(dst: dst, text: text));
				return dst;
			},
			Expression:BoolLit: local Function(Boolean is value){
				local String is dst: self:nextTmp();
				self:emit(inst: IrInst:ConstBool(dst: dst, value: value));
				return dst;
			},
			Expression:StringLit: local Function(String is value){
				local Int is sid: self:mod:internStringLiteral(value: value);
				local String is dst: self:nextTmp();
				self:emit(inst: IrInst:ConstString(dst: dst, strId: sid));
				return dst;
			},
			Expression:Ident: local Function(String is name){
				if({ self:localSlots:has(key: name) }, {
					local String is slot: self:localSlots:get(key: name, default: '');
					local IrType is ty: self:localTypes:get(key: name, default: IrType:I64);
					local String is dst: self:nextTmp();
					self:emit(inst: IrInst:Load(dst: dst, slot: slot, ty: ty));
					return dst;
				});
				return '0';
			},
			Expression:Unary: local Function(String is op, Expression is operand){
				local String is v: self:lowerExpr(expr: operand);
				local String is dst: self:nextTmp();
				local IrType is ty: self:irTypeFor(specType: expr:resolvedType);
				if({ ty == IrType:Void }, { ty: IrType:I64; });
				self:emit(inst: IrInst:UnaryOp(dst: dst, op: op, operand: v, ty: ty));
				return dst;
			},
			Expression:Binary: local Function(String is op, Expression is left, Expression is right){
				local String is l: self:lowerExpr(expr: left);
				local String is r: self:lowerExpr(expr: right);
				local String is dst: self:nextTmp();
				if({ op == '==' || op == '!=' || op == '<' || op == '<=' || op == '>' || op == '>=' }, {
					local IrType is cmpTy: self:irTypeFor(specType: left:resolvedType);
					if({ cmpTy == IrType:Void }, { cmpTy: IrType:I64; });
					self:emit(inst: IrInst:Cmp(dst: dst, op: op, lhs: l, rhs: r, ty: cmpTy));
					return dst;
				});
				if({ op == '.' }, {
					local Array of IrType is cTypes: [IrType:Ptr, IrType:Ptr];
					local Array of String is cArgs: [l, r];
					self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: cTypes, args: cArgs));
					return dst;
				});
				local IrType is ty: self:irTypeFor(specType: expr:resolvedType);
				if({ ty == IrType:Void }, { ty: IrType:I64; });
				self:emit(inst: IrInst:BinOp(dst: dst, op: op, lhs: l, rhs: r, ty: ty));
				return dst;
			},
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				local String is obj: self:lowerExpr(expr: target);
				local IrStruct is st: self:mod:findStruct(name: self:currentClass);
				local Int is fidx: st:fieldIndex(name: fieldName);
				if({ fidx >= 0 }, {
					local IrType is fty: st:fieldTypes:get(index: fidx);
					local String is ptr: self:nextTmp();
					local String is dst: self:nextTmp();
					self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: self:currentClass, fieldIndex: fidx));
					self:emit(inst: IrInst:Load(dst: dst, slot: ptr, ty: fty));
					return dst;
				});
				return '0';
			},
			Expression:Cast: local Function(Expression is inner, String is target, Array of Expression is args){
				local String is v: self:lowerExpr(expr: inner);
				local IrType is fromTy: self:irTypeFor(specType: inner:resolvedType);
				local IrType is toTy: self:irTypeFor(specType: target);
				if({ fromTy == toTy }, { return v; });
				if({ fromTy == IrType:I64 && toTy == IrType:Ptr }, {
					local String is dst: self:nextTmp();
					local Array of IrType is aT: [IrType:I64];
					local Array of String is aV: [v];
					self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_int', argTypes: aT, args: aV));
					return dst;
				});
				local String is dst: self:nextTmp();
				self:emit(inst: IrInst:IrCast(dst: dst, val: v, fromType: fromTy, toType: toTy));
				return dst;
			},
			Expression:Call: local Function(CallData is call){
				return self:lowerCall(expr: expr, call: call);
			}
		], default: {
			return '0';
		});
	}

	local Function of String is lowerCall(Expression is expr, CallData is call){
		local String is nm: call:name;
		if({ nm == 'if' && call:args:length() >= 2 }, {
			return self:lowerIfCall(expr: expr, call: call);
		});
		if({ nm == 'while' && call:args:length() >= 2 }, {
			self:lowerWhileCall(call: call);
			return '0';
		});
		if({ nm == 'line' && call:args:length() >= 1 }, {
			local NamedArg is lineArg: call:args:get(index: 0);
			local String is txt: self:lowerExpr(expr: lineArg:value);
			local Array of IrType is aT: [IrType:Ptr];
			local Array of String is aV: [txt];
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_print_line', argTypes: aT, args: aV));
			return '0';
		});

		# Method / constructor call
		local IrType is retTy: self:irTypeFor(specType: expr:resolvedType);
		local Array of IrType is argTypes: [];
		local Array of String is argVals: [];

		local String is calleeName: self:currentClass . '_' . nm;
		# Receiver: self if Ident('self'), or static class Path
		local Boolean is hasRecv: true;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tname){
				if({ tname == 'self' }, {
					argTypes:add(item: IrType:Ptr);
					argVals:add(item: self:lowerExpr(expr: call:target));
				}, {
					hasRecv: false;
				});
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 }, {
					calleeName: segs:get(index: segs:length() - 1, default: '') . '_' . nm;
				});
				hasRecv: false;
			}
		], default: {
			argTypes:add(item: IrType:Ptr);
			argVals:add(item: self:lowerExpr(expr: call:target));
		});

		if({ !hasRecv && nm == 'init' }, {
			# Constructor: ClassName_new + ClassName_init
			local String is clsName: self:currentClass;
			match(on: call:target, when: [
				Expression:Path: local Function(Array of String is segs){
					if({ segs:length() > 0 }, { clsName: segs:get(index: segs:length() - 1, default: ''); });
				}
			], default: {});
			local String is obj: self:nextTmp();
			self:emit(inst: IrInst:AllocObj(dst: obj, structName: clsName, destroyFn: 'null'));
			argTypes:add(item: IrType:Ptr);
			argVals:add(item: obj);
			local Int is ai: 0;
			while({ ai < call:args:length() }, {
				local NamedArg is na: call:args:get(index: ai);
				local Expression is av: na:value;
				argTypes:add(item: self:irTypeFor(specType: av:resolvedType));
				argVals:add(item: self:lowerExpr(expr: av));
				ai++;
			});
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: clsName . '_init', argTypes: argTypes, args: argVals));
			return obj;
		});

		if({ !hasRecv }, {
			argTypes:add(item: IrType:Ptr);
			argVals:add(item: 'null');
		});

		local Int is ai: 0;
		while({ ai < call:args:length() }, {
			local NamedArg is na2: call:args:get(index: ai);
			local Expression is av: na2:value;
			local IrType is aty: self:irTypeFor(specType: av:resolvedType);
			if({ aty == IrType:Void }, { aty: IrType:I64; });
			argTypes:add(item: aty);
			argVals:add(item: self:lowerExpr(expr: av));
			ai++;
		});

		local Boolean is hasDst: retTy != IrType:Void;
		local String is dst: '';
		if({ hasDst }, { dst: self:nextTmp(); });
		self:emit(inst: IrInst:IrCall(dst: dst, hasDst: hasDst, retType: retTy, callee: calleeName, argTypes: argTypes, args: argVals));
		return dst;
	}

	local Function of String is lowerIfCall(Expression is expr, CallData is call){
		local NamedArg is condNa: call:args:get(index: 0);
		local NamedArg is thenNa: call:args:get(index: 1);
		local Expression is condExpr: condNa:value;
		local Expression is thenExpr: thenNa:value;
		local Boolean is hasElse: call:args:length() >= 3;

		# Unwrap AnonFn cond: { cond }
		local String is condVal: '0';
		match(on: condExpr, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				if({ bd:length() > 0 }, {
					local Statement is bs: bd:get(index: 0);
					match(on: bs, when: [
						Statement:Return: local Function(Expression is re, Boolean is hr){
							if({ hr }, { condVal: self:lowerExpr(expr: re); });
						},
						Statement:Expr: local Function(Expression is es){
							condVal: self:lowerExpr(expr: es);
						}
					], default: {});
				});
			}
		], default: {
			condVal: self:lowerExpr(expr: condExpr);
		});

		local String is thenLbl: self:nextLabel(prefix: 'if_then');
		local String is elseLbl: self:nextLabel(prefix: 'if_else');
		local String is endLbl: self:nextLabel(prefix: 'if_end');
		if({ !hasElse }, { elseLbl: endLbl; });

		self:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: thenLbl, elseLabel: elseLbl));

		local IrBlock is thenBlk: self:curFn:addBlock(label: thenLbl);
		self:switchBlock(blk: thenBlk);
		match(on: thenExpr, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				self:lowerStmts(stmts: bd);
			}
		], default: { local String is _u1: self:lowerExpr(expr: thenExpr); });
		if({ !self:blkTerminated }, {
			self:terminate(inst: IrInst:Br(target: endLbl));
		});

		if({ hasElse }, {
			local NamedArg is elseNa: call:args:get(index: 2);
			local Expression is elseExpr: elseNa:value;
			local IrBlock is elseBlk: self:curFn:addBlock(label: elseLbl);
			self:switchBlock(blk: elseBlk);
			match(on: elseExpr, when: [
				Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
					self:lowerStmts(stmts: bd);
				}
			], default: { local String is _u2: self:lowerExpr(expr: elseExpr); });
			if({ !self:blkTerminated }, {
				self:terminate(inst: IrInst:Br(target: endLbl));
			});
		});

		local IrBlock is endBlk: self:curFn:addBlock(label: endLbl);
		self:switchBlock(blk: endBlk);
		return '0';
	}

	local Function is lowerWhileCall(CallData is call){
		local NamedArg is condNa: call:args:get(index: 0);
		local NamedArg is bodyNa: call:args:get(index: 1);
		local Expression is condExpr: condNa:value;
		local Expression is bodyExpr: bodyNa:value;

		local String is hdrLbl: self:nextLabel(prefix: 'while_hdr');
		local String is bodyLbl: self:nextLabel(prefix: 'while_body');
		local String is endLbl: self:nextLabel(prefix: 'while_end');

		self:terminate(inst: IrInst:Br(target: hdrLbl));

		local IrBlock is hdrBlk: self:curFn:addBlock(label: hdrLbl);
		self:switchBlock(blk: hdrBlk);
		local String is condVal: '0';
		match(on: condExpr, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				if({ bd:length() > 0 }, {
					local Statement is bs: bd:get(index: 0);
					match(on: bs, when: [
						Statement:Return: local Function(Expression is re, Boolean is hr){
							if({ hr }, { condVal: self:lowerExpr(expr: re); });
						},
						Statement:Expr: local Function(Expression is es){
							condVal: self:lowerExpr(expr: es);
						}
					], default: {});
				});
			}
		], default: { condVal: self:lowerExpr(expr: condExpr); });
		self:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: bodyLbl, elseLabel: endLbl));

		local IrBlock is bodyBlk: self:curFn:addBlock(label: bodyLbl);
		self:switchBlock(blk: bodyBlk);
		match(on: bodyExpr, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				self:lowerStmts(stmts: bd);
			}
		], default: { local String is _u3: self:lowerExpr(expr: bodyExpr); });
		if({ !self:blkTerminated }, {
			self:terminate(inst: IrInst:Br(target: hdrLbl));
		});

		local IrBlock is endBlk: self:curFn:addBlock(label: endLbl);
		self:switchBlock(blk: endBlk);
	}
}
