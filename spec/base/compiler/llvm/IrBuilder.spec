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
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', CallLowererRegistry],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	IrModule is mod: IrModule:init();
	Int is tmpCounter: 0;
	Int is lblCounter: 0;
	Int is anonCounter: 0;
	String is currentClass: '';
	Int is currentLine: 0;
	IrFunction is curFn: IrFunction:init();
	IrBlock is curBlk: IrBlock:init();
	Boolean is blkTerminated: false;
	Map of String to String is localSlots: Map:init();
	Map of String to IrType is localTypes: Map:init();
	Array of String is ownedSlots: [];
	Array of CallLowerer is callLowerers: [];
	Map of String to ClassInfo is clsMap: Map:init();
	Map of String to String is heldFields: Map:init();
	Map of String to String is heldFieldTypes: Map:init();
	Map of String to Boolean is heldMethods: Map:init();

	replace Function is init(){
		self:callLowerers: CallLowererRegistry:init():loadAll();
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
			self:curBlk:appendAt(inst: inst, line: self:currentLine);
		});
	}

	Function is terminate(IrInst is inst){
		if({ !self:blkTerminated }, {
			self:curBlk:appendAt(inst: inst, line: self:currentLine);
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

	local Function of String is cStructName(String is qname){
		return qname:replaceAll(target: ':', replacement: '_');
	}

	local Function is addInheritedFields(IrStruct is st, ClassInfo is cls, Map of String to ClassInfo is clsMap, Map of String to Boolean is seenFields){
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			if({ clsMap:has(key: bname) }, {
				local ClassInfo is bcls: clsMap:get(key: bname, default: cls);
				self:addInheritedFields(st: st, cls: bcls, clsMap: clsMap, seenFields: seenFields);
			});
			bi++;
		});
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:FIELD && m:name != 'using' && !m:hasModifier(kw: Keyword:HELD) && !seenFields:has(key: m:name) }, {
				seenFields:set(key: m:name, value: true);
				local IrType is fty: self:irTypeFor(specType: m:memberType:name);
				if({ fty == IrType:Void }, { fty: IrType:Ptr; });
				st:addField(name: m:name, ty: fty);
			});
			mi++;
		});
	}

	local Function is buildVtable(IrStruct is st, ClassInfo is cls, Map of String to ClassInfo is clsMap){
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			if({ clsMap:has(key: bname) }, {
				local ClassInfo is bcls: clsMap:get(key: bname, default: cls);
				self:buildVtable(st: st, cls: bcls, clsMap: clsMap);
			});
			bi++;
		});
		local String is sname: self:cStructName(qname: cls:qualifiedName());
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:METHOD && m:name != 'init' && m:name != 'destroy' && !m:hasModifier(kw: Keyword:HELD) }, {
				local String is fnName: 'null';
				if({ m:body:length() > 0 }, {
					fnName: sname . '_' . m:name;
				});
				st:setVtableMethod(mname: m:name, fnName: fnName);
			});
			mi++;
		});
	}

	local Function is collectAllClasses(ClassInfo is cls, Array of ClassInfo is out){
		out:add(item: cls);
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:CLASS }, {
				self:collectAllClasses(cls: m:nestedClass, out: out);
			});
			mi++;
		});
	}

	Function of IrModule is buildProgram(ProgramNode is program, String is entryClass){
		self:mod: IrModule:init();
		self:mod:entryFunction: entryClass;

		local Array of ClassInfo is allClasses: [];
		local Int is pci: 0;
		while({ pci < program:classes:length() }, {
			local ClassInfo is pc0: program:classes:get(index: pci);
			if({ !self:isStdlibClass(cls: pc0) }, {
				self:collectAllClasses(cls: pc0, out: allClasses);
			});
			pci++;
		});

		local Map of String to ClassInfo is clsMap: Map:init();
		local Int is ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is c0: allClasses:get(index: ci);
			clsMap:set(key: c0:qualifiedName(), value: c0);
			if({ c0:outerName == '' }, {
				clsMap:set(key: c0:name, value: c0);
			});
			ci++;
		});
		self:clsMap: clsMap;
		self:heldFields: Map:init();
		self:heldFieldTypes: Map:init();
		self:heldMethods: Map:init();

		# 1. Register structs for user classes (deduplicated by name, with inherited fields)
		local Map of String to Boolean is seenStructs: Map:init();
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			local String is sname: self:cStructName(qname: cls:qualifiedName());
			if({ !seenStructs:has(key: sname) }, {
				seenStructs:set(key: sname, value: true);
				local IrStruct is st: IrStruct:init(name: sname);
				st:qualifiedName: cls:qualifiedName();
				if({ cls:sourceFile != '' }, {
					local Array of String is srcSegs: cls:sourceFile:split(delimiter: '/');
					if({ srcSegs:length() > 0 }, {
						st:sourceFileBase: srcSegs:get(index: srcSegs:length() - 1, default: '');
					});
				});
				local Int is bni: 0;
				while({ bni < cls:baseClasses:length() }, {
					st:baseNames:add(item: cls:baseClasses:get(index: bni, default: ''));
					bni++;
				});
				# Header layout: _type_name (Ptr), _vtable (Ptr)
				st:addField(name: '_type_name', ty: IrType:Ptr);
				st:addField(name: '_vtable', ty: IrType:Ptr);
				local Map of String to Boolean is seenFields: Map:init();
				self:addInheritedFields(st: st, cls: cls, clsMap: clsMap, seenFields: seenFields);
				self:buildVtable(st: st, cls: cls, clsMap: clsMap);
				self:registerClassMetaAndHeld(st: st, cls: cls, sname: sname);
				self:mod:addStruct(s: st);
			});
			ci++;
		});

		# 2. Lower methods, construct helpers, and held field __ensure accessors
		local Map of String to Boolean is seenFns: Map:init();
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			local String is sname: self:cStructName(qname: cls:qualifiedName());
			self:currentClass: sname;
			local Int is mi: 0;
			while({ mi < cls:members:length() }, {
				local Member is m: cls:members:get(index: mi);
				if({ m:kind == MemberKind:FIELD && m:hasModifier(kw: Keyword:HELD) }, {
					local String is ensureFn: sname . '_' . m:name . '__ensure';
					if({ !seenFns:has(key: ensureFn) }, {
						seenFns:set(key: ensureFn, value: true);
						self:buildHeldEnsure(sname: sname, m: m);
					});
				});
				if({ m:kind == MemberKind:METHOD }, {
					local String is fnName: sname . '_' . m:name;
					if({ !seenFns:has(key: fnName) }, {
						seenFns:set(key: fnName, value: true);
						self:buildMethod(cls: cls, m: m);
					});
				});
				mi++;
			});
			local IrStruct is st2: self:mod:findStruct(name: sname);
			if({ st2:constructFn != 'null' && !seenFns:has(key: st2:constructFn) }, {
				seenFns:set(key: st2:constructFn, value: true);
				self:buildConstructHelper(cls: cls, sname: sname, ctorFn: st2:constructFn);
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

	local Function is emitFieldDefaults(ClassInfo is cls, Map of String to Boolean is seen){
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			if({ self:clsMap:has(key: bname) }, {
				local ClassInfo is bcls: self:clsMap:get(key: bname, default: cls);
				self:emitFieldDefaults(cls: bcls, seen: seen);
			});
			bi++;
		});
		local IrStruct is st: self:mod:findStruct(name: self:currentClass);
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:FIELD && m:name != 'using' && !m:hasModifier(kw: Keyword:HELD) && m:hasInit && !seen:has(key: m:name) }, {
				seen:set(key: m:name, value: true);
				local Int is fidx: st:fieldIndex(name: m:name);
				if({ fidx >= 0 }, {
					local IrType is fty: st:fieldTypes:get(index: fidx);
					local String is val: self:lowerExpr(expr: m:initExpr);
					local String is ptr: self:nextTmp();
					self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: '%self', structName: self:currentClass, fieldIndex: fidx));
					self:emit(inst: IrInst:Store(slot: ptr, val: val, ty: fty));
				});
			});
			mi++;
		});
	}

	local Function is registerClassMetaAndHeld(IrStruct is st, ClassInfo is cls, String is sname){
		local Boolean is hasInitMember: false;
		local Boolean is hasZeroArgInit: false;
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:FIELD && m:hasModifier(kw: Keyword:HELD) }, {
				local IrType is hty: self:irTypeFor(specType: m:memberType:name);
				if({ hty == IrType:Void }, { hty: IrType:Ptr; });
				local String is valGlob: '.held_val.' . sname . '.' . m:name;
				local String is initGlob: '.held_init.' . sname . '.' . m:name;
				self:mod:addGlobal(name: valGlob, ty: hty, initVal: 'zeroinitializer');
				self:mod:addGlobal(name: initGlob, ty: IrType:I1, initVal: 'false');
				self:heldFields:set(key: sname . ':' . m:name, value: sname);
				self:heldFields:set(key: cls:name . ':' . m:name, value: sname);
				self:heldFieldTypes:set(key: sname . ':' . m:name, value: m:memberType:name);
				st:heldNames:add(item: m:name);
				st:heldGetters:add(item: sname . '_' . m:name . '__ensure');
			});
			if({ m:kind == MemberKind:METHOD }, {
				if({ m:hasModifier(kw: Keyword:HELD) }, {
					self:heldMethods:set(key: sname . '_' . m:name, value: true);
					st:heldNames:add(item: m:name);
					st:heldGetters:add(item: 'null');
				}, {
					if({ m:name == 'init' }, {
						hasInitMember: true;
						if({ m:params:length() == 0 }, { hasZeroArgInit: true; });
					});
					local Int is flags: 0;
					if({ m:memberType:name == 'Void' }, { flags: flags + 1; });
					if({ m:params:length() == 0 }, { flags: flags + 2; });
					if({ m:memberType:name == 'Function' && m:memberType:params:length() == 0 }, { flags: flags + 4; });
					st:metaMethodNames:add(item: m:name);
					if({ m:body:length() > 0 }, {
						st:metaMethodFns:add(item: sname . '_' . m:name);
					}, {
						st:metaMethodFns:add(item: 'null');
					});
					st:metaMethodFlags:add(item: flags);
					st:metaMethodLines:add(item: m:line);
				});
			});
			mi++;
		});
		if({ !hasInitMember || hasZeroArgInit }, {
			st:constructFn: sname . '__spec_construct';
		});
	}

	local Function is buildConstructHelper(ClassInfo is cls, String is sname, String is ctorFn){
		local IrFunction is fn: IrFunction:init(name: ctorFn, retType: IrType:Ptr);
		local IrBlock is entry: fn:addBlock(label: 'entry');
		self:curFn: fn;
		self:switchBlock(blk: entry);
		self:tmpCounter: 0;
		local String is obj: self:nextTmp();
		self:emit(inst: IrInst:AllocObj(dst: obj, structName: sname, destroyFn: 'null'));
		local Boolean is hasZeroInit: false;
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:METHOD && m:name == 'init' && m:params:length() == 0 }, {
				hasZeroInit: true;
			});
			mi++;
		});
		if({ hasZeroInit }, {
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: sname . '_init', argTypes: [IrType:Ptr], args: [obj]));
		});
		self:terminate(inst: IrInst:Ret(hasVal: true, val: obj, ty: IrType:Ptr));
		self:mod:addFunction(fn: fn);
	}

	local Function is buildHeldEnsure(String is sname, Member is m){
		local IrType is hty: self:irTypeFor(specType: m:memberType:name);
		if({ hty == IrType:Void }, { hty: IrType:Ptr; });
		local String is fnName: sname . '_' . m:name . '__ensure';
		local IrFunction is fn: IrFunction:init(name: fnName, retType: hty);
		local IrBlock is entry: fn:addBlock(label: 'entry');
		self:curFn: fn;
		self:switchBlock(blk: entry);
		self:tmpCounter: 0;
		self:lblCounter: 0;
		self:localSlots: Map:init();
		self:localTypes: Map:init();
		self:ownedSlots: [];

		local String is valGlob: '@.held_val.' . sname . '.' . m:name;
		local String is initGlob: '@.held_init.' . sname . '.' . m:name;
		local String is isInit: self:nextTmp();
		self:emit(inst: IrInst:Load(dst: isInit, slot: initGlob, ty: IrType:I1));

		local String is initLbl: self:nextLabel(prefix: 'held_init');
		local String is doneLbl: self:nextLabel(prefix: 'held_done');
		self:terminate(inst: IrInst:CondBr(cond: isInit, thenLabel: doneLbl, elseLabel: initLbl));

		local IrBlock is initBlk: fn:addBlock(label: initLbl);
		self:switchBlock(blk: initBlk);
		local String is trueTmp: self:nextTmp();
		self:emit(inst: IrInst:ConstBool(dst: trueTmp, value: true));
		self:emit(inst: IrInst:Store(slot: initGlob, val: trueTmp, ty: IrType:I1));
		if({ m:hasInit }, {
			local String is iv: self:lowerExpr(expr: m:initExpr);
			if({ iv == '' }, { iv: self:emitDefaultVal(ty: hty); });
			self:emit(inst: IrInst:Store(slot: valGlob, val: iv, ty: hty));
		});
		self:terminate(inst: IrInst:Br(target: doneLbl));

		local IrBlock is doneBlk: fn:addBlock(label: doneLbl);
		self:switchBlock(blk: doneBlk);
		local String is res: self:nextTmp();
		self:emit(inst: IrInst:Load(dst: res, slot: valGlob, ty: hty));
		self:terminate(inst: IrInst:Ret(hasVal: true, val: res, ty: hty));
		self:mod:addFunction(fn: fn);
	}

	local Function is buildMethod(ClassInfo is cls, Member is m){
		local IrType is retTy: self:methodReturnType(mt: m:memberType);
		local String is fnName: self:cStructName(qname: cls:qualifiedName()) . '_' . m:name;
		local Boolean is isHeldMethod: m:hasModifier(kw: Keyword:HELD);
		local IrFunction is fn: IrFunction:init(name: fnName, retType: retTy);
		fn:sourceFile: cls:sourceFile;
		fn:line: m:line;
		self:currentLine: m:line;
		if({ !isHeldMethod }, {
			fn:addParam(name: '%self', ty: IrType:Ptr);
		});
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
		self:ownedSlots: [];

		if({ !isHeldMethod }, {
			# Bind 'self' into stack slot
			self:localSlots:set(key: 'self', value: '%self_slot');
			self:localTypes:set(key: 'self', value: IrType:Ptr);
			self:emit(inst: IrInst:Alloca(slot: '%self_slot', ty: IrType:Ptr));
			self:emit(inst: IrInst:Store(slot: '%self_slot', val: '%self', ty: IrType:Ptr));
		});

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

		if({ m:name == 'init' }, {
			self:emitFieldDefaults(cls: cls, seen: Map:init());
		});

		self:lowerStmts(stmts: m:body);

		if({ !self:blkTerminated }, {
			self:emitReleaseOwnedLocals();
			if({ retTy == IrType:Void }, {
				self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
			}, {
				local String is defVal: self:emitDefaultVal(ty: retTy);
				self:terminate(inst: IrInst:Ret(hasVal: true, val: defVal, ty: retTy));
			});
		});

		self:mod:addFunction(fn: fn);
	}

	local Function is emitReleaseOwnedLocals(){
		local Int is oi: 0;
		while({ oi < self:ownedSlots:length() }, {
			local String is oslot: self:ownedSlots:get(index: oi, default: '');
			local String is oval: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: oval, slot: oslot, ty: IrType:Ptr));
			self:emit(inst: IrInst:Release(val: oval));
			oi++;
		});
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

	Function is lowerStmts(Array of Statement is stmts){
		local Int is i: 0;
		while({ i < stmts:length() && !self:blkTerminated }, {
			self:lowerStmt(stmt: stmts:get(index: i));
			i++;
		});
	}

	local Function is lowerStmt(Statement is stmt){
		local Int is prevLine: self:currentLine;
		if({ stmt:line > 0 }, { self:currentLine: stmt:line; });
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
					if({ vty == IrType:Ptr }, {
						local Boolean is needsRetain: match(on: initExpr, when: [
							Expression:Ident: local Function of Boolean(String is _n){ return true; },
							Expression:FieldAccess: local Function of Boolean(Expression is _t, String is _f){ return true; },
							Expression:Index: local Function of Boolean(Expression is _t, Expression is _i){ return true; }
						], default: { return false; });
						if({ needsRetain }, {
							self:emit(inst: IrInst:Retain(val: val));
						});
					});
					self:emit(inst: IrInst:Store(slot: slot, val: val, ty: vty));
				}, {
					local String is defVal: self:emitDefaultVal(ty: vty);
					self:emit(inst: IrInst:Store(slot: slot, val: defVal, ty: vty));
				});
				if({ vty == IrType:Ptr }, {
					self:ownedSlots:add(item: slot);
				});
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				local String is val: self:lowerExpr(expr: assignValue);
				match(on: assignTarget, when: [
					Expression:Ident: local Function(String is name){
						if({ self:localSlots:has(key: name) }, {
							local String is slot: self:localSlots:get(key: name, default: '');
							local IrType is ty: self:localTypes:get(key: name, default: IrType:I64);
							if({ ty == IrType:Ptr }, {
								self:emit(inst: IrInst:Retain(val: val));
								local String is oldVal: self:nextTmp();
								self:emit(inst: IrInst:Load(dst: oldVal, slot: slot, ty: IrType:Ptr));
								self:emit(inst: IrInst:Release(val: oldVal));
							});
							self:emit(inst: IrInst:Store(slot: slot, val: val, ty: ty));
						}, {
							local String is hk: self:currentClass . ':' . name;
							if({ self:heldFields:has(key: hk) }, {
								local String is owner: self:heldFields:get(key: hk, default: '');
								local IrType is hty: self:irTypeFor(specType: self:heldFieldTypes:get(key: owner . ':' . name, default: ''));
								if({ hty == IrType:Void }, { hty: IrType:Ptr; });
								local String is trueTmp: self:nextTmp();
								self:emit(inst: IrInst:ConstBool(dst: trueTmp, value: true));
								self:emit(inst: IrInst:Store(slot: '@.held_init.' . owner . '.' . name, val: trueTmp, ty: IrType:I1));
								self:emit(inst: IrInst:Store(slot: '@.held_val.' . owner . '.' . name, val: val, ty: hty));
							});
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
					},
					Expression:Path: local Function(Array of String is segments){
						if({ segments:length() >= 2 }, {
							local String is seg0: segments:get(index: 0, default: '');
							if({ self:localSlots:has(key: seg0) }, {
								local String is slot: self:localSlots:get(key: seg0, default: '');
								local IrType is sty: self:localTypes:get(key: seg0, default: IrType:Ptr);
								local String is obj: self:nextTmp();
								self:emit(inst: IrInst:Load(dst: obj, slot: slot, ty: sty));
								local String is sname: self:currentClass;
								if({ seg0 != 'self' }, { sname: self:cStructName(qname: seg0); });
								local String is fname: segments:get(index: segments:length() - 1, default: '');
								local IrStruct is st: self:mod:findStruct(name: sname);
								local Int is fidx: st:fieldIndex(name: fname);
								if({ fidx >= 0 }, {
									local IrType is fty: st:fieldTypes:get(index: fidx);
									local String is ptr: self:nextTmp();
									self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: sname, fieldIndex: fidx));
									self:emit(inst: IrInst:Store(slot: ptr, val: val, ty: fty));
								});
							}, {
								local String is seg1: segments:get(index: 1, default: '');
								local String is hk: seg0 . ':' . seg1;
								if({ segments:length() == 2 && self:heldFields:has(key: hk) }, {
									local String is owner: self:heldFields:get(key: hk, default: '');
									local IrType is hty: self:irTypeFor(specType: self:heldFieldTypes:get(key: owner . ':' . seg1, default: ''));
									if({ hty == IrType:Void }, { hty: IrType:Ptr; });
									local String is trueTmp: self:nextTmp();
									self:emit(inst: IrInst:ConstBool(dst: trueTmp, value: true));
									self:emit(inst: IrInst:Store(slot: '@.held_init.' . owner . '.' . seg1, val: trueTmp, ty: IrType:I1));
									self:emit(inst: IrInst:Store(slot: '@.held_val.' . owner . '.' . seg1, val: val, ty: hty));
								});
							});
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
					if({ val == '0' && self:curFn:retType == IrType:Ptr }, {
						val: 'null';
					});
					if({ self:curFn:retType == IrType:Ptr && val != 'null' }, {
						self:emit(inst: IrInst:Retain(val: val));
					});
					self:emitReleaseOwnedLocals();
					self:terminate(inst: IrInst:Ret(hasVal: true, val: val, ty: self:curFn:retType));
				}, {
					self:emitReleaseOwnedLocals();
					self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
				});
			},
			Statement:Expr: local Function(Expression is exprStmt){
				local String is _u0: self:lowerExpr(expr: exprStmt);
			}
		], default: {});
		self:currentLine: prevLine;
	}

	Function of String is lowerExpr(Expression is expr){
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
				local String is hk: self:currentClass . ':' . name;
				if({ self:heldFields:has(key: hk) }, {
					local String is owner: self:heldFields:get(key: hk, default: '');
					local IrType is hty: self:irTypeFor(specType: self:heldFieldTypes:get(key: owner . ':' . name, default: ''));
					if({ hty == IrType:Void }, { hty: IrType:Ptr; });
					local String is dst: self:nextTmp();
					self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: hty, callee: owner . '_' . name . '__ensure', argTypes: [], args: []));
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
					if({ cmpTy == IrType:Ptr && (op == '==' || op == '!=') }, {
						local Array of IrType is sT: [IrType:Ptr, IrType:Ptr];
						local Array of String is sV: [l, r];
						if({ op == '==' }, {
							self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I1, callee: 'spec_string_equals', argTypes: sT, args: sV));
							return dst;
						}, {
							local String is eqTmp: self:nextTmp();
							self:emit(inst: IrInst:IrCall(dst: eqTmp, hasDst: true, retType: IrType:I1, callee: 'spec_string_equals', argTypes: sT, args: sV));
							self:emit(inst: IrInst:UnaryOp(dst: dst, op: '!', operand: eqTmp, ty: IrType:I1));
							return dst;
						});
					});
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
			Expression:Path: local Function(Array of String is segments){
				if({ segments:length() >= 2 }, {
					local String is seg0: segments:get(index: 0, default: '');
					if({ self:localSlots:has(key: seg0) }, {
						local String is slot: self:localSlots:get(key: seg0, default: '');
						local IrType is sty: self:localTypes:get(key: seg0, default: IrType:Ptr);
						local String is obj: self:nextTmp();
						self:emit(inst: IrInst:Load(dst: obj, slot: slot, ty: sty));
						local String is sname: self:currentClass;
						local String is fname: segments:get(index: segments:length() - 1, default: '');
						local IrStruct is st: self:mod:findStruct(name: sname);
						local Int is fidx: st:fieldIndex(name: fname);
						if({ fidx >= 0 }, {
							local IrType is fty: st:fieldTypes:get(index: fidx);
							local String is ptr: self:nextTmp();
							local String is dst: self:nextTmp();
							self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: sname, fieldIndex: fidx));
							self:emit(inst: IrInst:Load(dst: dst, slot: ptr, ty: fty));
							return dst;
						});
					}, {
						local String is seg1: segments:get(index: 1, default: '');
						local String is hk: seg0 . ':' . seg1;
						if({ segments:length() == 2 && self:heldFields:has(key: hk) }, {
							local String is owner: self:heldFields:get(key: hk, default: '');
							local IrType is hty: self:irTypeFor(specType: self:heldFieldTypes:get(key: owner . ':' . seg1, default: ''));
							if({ hty == IrType:Void }, { hty: IrType:Ptr; });
							local String is dst: self:nextTmp();
							self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: hty, callee: owner . '_' . seg1 . '__ensure', argTypes: [], args: []));
							return dst;
						});
					});
				});
				if({ self:irTypeFor(specType: expr:resolvedType) == IrType:Ptr }, {
					return 'null';
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
			Expression:ArrayLit: local Function(Array of Expression is items){
				local String is arr: self:nextTmp();
				local Array of IrType is emptyT: [];
				local Array of String is emptyV: [];
				local Boolean is isObjArr: false;
				if({ items:length() > 0 }, {
					local Expression is firstItem: items:get(index: 0);
					if({ self:irTypeFor(specType: firstItem:resolvedType) == IrType:Ptr }, { isObjArr: true; });
				});
				if({ isObjArr }, {
					self:emit(inst: IrInst:IrCall(dst: arr, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_new_object', argTypes: emptyT, args: emptyV));
				}, {
					self:emit(inst: IrInst:IrCall(dst: arr, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_new', argTypes: emptyT, args: emptyV));
				});
				local Int is ii: 0;
				while({ ii < items:length() }, {
					local Expression is it: items:get(index: ii);
					local String is iv: self:lowerExpr(expr: it);
					local IrType is ity: self:irTypeFor(specType: it:resolvedType);
					local String is ip: iv;
					if({ ity == IrType:Void }, {
						ip: 'null';
					}, {
						if({ ity != IrType:Ptr }, {
							ip: self:nextTmp();
							self:emit(inst: IrInst:IrCast(dst: ip, val: iv, fromType: ity, toType: IrType:Ptr));
						});
					});
					local Array of IrType is addT: [IrType:Ptr, IrType:Ptr];
					local Array of String is addV: [arr, ip];
					self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_add', argTypes: addT, args: addV));
					ii++;
				});
				return arr;
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				local String is mp: self:nextTmp();
				local Array of IrType is emptyT: [];
				local Array of String is emptyV: [];
				self:emit(inst: IrInst:IrCall(dst: mp, hasDst: true, retType: IrType:Ptr, callee: 'spec_map_new', argTypes: emptyT, args: emptyV));
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					local Expression is ke: keys:get(index: mi);
					local Expression is ve: values:get(index: mi);
					local String is kv: self:lowerExpr(expr: ke);
					local String is vv: self:lowerExpr(expr: ve);
					local IrType is vty: self:irTypeFor(specType: ve:resolvedType);
					local String is vp: vv;
					if({ vty != IrType:Ptr }, {
						vp: self:nextTmp();
						self:emit(inst: IrInst:IrCast(dst: vp, val: vv, fromType: vty, toType: IrType:Ptr));
					});
					local Array of IrType is setT: [IrType:Ptr, IrType:Ptr, IrType:Ptr];
					local Array of String is setV: [mp, kv, vp];
					self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_map_set', argTypes: setT, args: setV));
					mi++;
				});
				return mp;
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				local String is tv: self:lowerExpr(expr: target);
				local String is iv: self:lowerExpr(expr: index);
				local String is raw: self:nextTmp();
				local Array of IrType is gT: [IrType:Ptr, IrType:I64];
				local Array of String is gV: [tv, iv];
				self:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_get', argTypes: gT, args: gV));
				local IrType is rty: self:irTypeFor(specType: expr:resolvedType);
				if({ rty != IrType:Ptr && rty != IrType:Void }, {
					local String is casted: self:nextTmp();
					self:emit(inst: IrInst:IrCast(dst: casted, val: raw, fromType: IrType:Ptr, toType: rty));
					return casted;
				});
				return raw;
			},
			Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
				return self:lowerAnonFn(returnType: returnType, params: params, body: body);
			},
			Expression:Call: local Function(CallData is call){
				return self:lowerCall(expr: expr, call: call);
			}
		], default: {
			if({ self:irTypeFor(specType: expr:resolvedType) == IrType:Ptr }, {
				return 'null';
			});
			return '0';
		});
	}

	local Function is collectFreeInStmts(Array of Statement is stmts, Map of String to Boolean is bound, Map of String to String is outerSlots, Map of String to Boolean is seen, Array of String is out){
		local Int is i: 0;
		while({ i < stmts:length() }, {
			local Statement is st: stmts:get(index: i);
			match(on: st, when: [
				Statement:VarDecl: local Function(Array of String is _m, Type is _t, String is varName, Expression is initExpr, Boolean is hasInit){
					if({ hasInit }, {
						self:collectFreeInExpr(expr: initExpr, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					});
					bound:set(key: varName, value: true);
				},
				Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
					self:collectFreeInExpr(expr: assignTarget, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					self:collectFreeInExpr(expr: assignValue, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				},
				Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
					if({ hasReturnExpr }, {
						self:collectFreeInExpr(expr: returnExpr, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					});
				},
				Statement:Expr: local Function(Expression is exprStmt){
					self:collectFreeInExpr(expr: exprStmt, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				}
			], default: {});
			i++;
		});
	}

	local Function is collectFreeInExpr(Expression is expr, Map of String to Boolean is bound, Map of String to String is outerSlots, Map of String to Boolean is seen, Array of String is out){
		match(on: expr, when: [
			Expression:Ident: local Function(String is name){
				if({ !bound:has(key: name) && outerSlots:has(key: name) && !seen:has(key: name) }, {
					seen:set(key: name, value: true);
					out:add(item: name);
				});
			},
			Expression:Unary: local Function(String is _op, Expression is operand){
				self:collectFreeInExpr(expr: operand, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
			},
			Expression:Binary: local Function(String is _op, Expression is left, Expression is right){
				self:collectFreeInExpr(expr: left, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				self:collectFreeInExpr(expr: right, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
			},
			Expression:Cast: local Function(Expression is inner, String is _t, Array of Expression is args){
				self:collectFreeInExpr(expr: inner, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				local Int is ai: 0;
				while({ ai < args:length() }, {
					self:collectFreeInExpr(expr: args:get(index: ai), bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					ai++;
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is _f){
				self:collectFreeInExpr(expr: target, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				self:collectFreeInExpr(expr: target, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				self:collectFreeInExpr(expr: index, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				local Int is ii: 0;
				while({ ii < items:length() }, {
					self:collectFreeInExpr(expr: items:get(index: ii), bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					ii++;
				});
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					self:collectFreeInExpr(expr: keys:get(index: mi), bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					self:collectFreeInExpr(expr: values:get(index: mi), bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					mi++;
				});
			},
			Expression:Call: local Function(CallData is call){
				self:collectFreeInExpr(expr: call:target, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				local Int is ci: 0;
				while({ ci < call:args:length() }, {
					local NamedArg is na: call:args:get(index: ci);
					self:collectFreeInExpr(expr: na:value, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					ci++;
				});
			},
			Expression:AnonFn: local Function(Type is _rt, Array of Parameter is subParams, Array of Statement is subBody){
				local Map of String to Boolean is subBound: Map:init();
				local Array of String is bKeys: bound:keys();
				local Int is bi: 0;
				while({ bi < bKeys:length() }, {
					subBound:set(key: bKeys:get(index: bi, default: ''), value: true);
					bi++;
				});
				local Int is pi: 0;
				while({ pi < subParams:length() }, {
					local Parameter is sp: subParams:get(index: pi);
					subBound:set(key: sp:name, value: true);
					pi++;
				});
				self:collectFreeInStmts(stmts: subBody, bound: subBound, outerSlots: outerSlots, seen: seen, out: out);
			}
		], default: {});
	}

	local Function of String is lowerAnonFn(Type is returnType, Array of Parameter is params, Array of Statement is body){
		self:anonCounter: self:anonCounter + 1;
		local Int is anonId: self:anonCounter;
		local String is fnName: '__anon_' . (anonId as String);
		local IrType is retTy: self:irTypeFor(specType: returnType:name);
		if({ returnType:name == 'Function' }, {
			if({ returnType:params:length() > 0 }, {
				local Type is rt: returnType:params:get(index: 0);
				retTy: self:irTypeFor(specType: rt:name);
			}, {
				retTy: IrType:Void;
			});
		});

		# Collect free variables captured from enclosing function
		local Map of String to Boolean is bound: Map:init();
		local Int is bpi: 0;
		while({ bpi < params:length() }, {
			local Parameter is bp: params:get(index: bpi);
			bound:set(key: bp:name, value: true);
			bpi++;
		});
		local Map of String to Boolean is seenCap: Map:init();
		local Array of String is captures: [];
		self:collectFreeInStmts(stmts: body, bound: bound, outerSlots: self:localSlots, seen: seenCap, out: captures);

		local String is envStructName: '__env_' . (anonId as String);
		if({ captures:length() > 0 }, {
			local IrStruct is envSt: IrStruct:init(name: envStructName);
			envSt:addField(name: '_type_name', ty: IrType:Ptr);
			envSt:addField(name: '_vtable', ty: IrType:Ptr);
			local Int is ci: 0;
			while({ ci < captures:length() }, {
				local String is cname: captures:get(index: ci, default: '');
				local IrType is cty: self:localTypes:get(key: cname, default: IrType:I64);
				envSt:addField(name: cname, ty: cty);
				ci++;
			});
			self:mod:addStruct(s: envSt);
		});

		# Save outer method builder state
		local IrFunction is savedFn: self:curFn;
		local IrBlock is savedBlk: self:curBlk;
		local Boolean is savedTerm: self:blkTerminated;
		local Int is savedTmp: self:tmpCounter;
		local Int is savedLbl: self:lblCounter;
		local Map of String to String is savedSlots: self:localSlots;
		local Map of String to IrType is savedTypes: self:localTypes;
		local Array of String is savedOwned: self:ownedSlots;

		local IrFunction is fn: IrFunction:init(name: fnName, retType: retTy);
		fn:sourceFile: savedFn:sourceFile;
		fn:line: self:currentLine;
		fn:addParam(name: '%env', ty: IrType:Ptr);
		local Int is pi: 0;
		while({ pi < params:length() }, {
			local Parameter is p: params:get(index: pi);
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
		self:ownedSlots: [];

		# Unpack captured variables from %env into local slots
		local Int is uci: 0;
		while({ uci < captures:length() }, {
			local String is cname: captures:get(index: uci, default: '');
			local IrType is cty: savedTypes:get(key: cname, default: IrType:I64);
			local String is fPtr: self:nextTmp();
			self:emit(inst: IrInst:FieldPtr(dst: fPtr, objPtr: '%env', structName: envStructName, fieldIndex: uci + 2));
			local String is loaded: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: loaded, slot: fPtr, ty: cty));
			local String is capSlot: '%cap_' . cname;
			self:localSlots:set(key: cname, value: capSlot);
			self:localTypes:set(key: cname, value: cty);
			self:emit(inst: IrInst:Alloca(slot: capSlot, ty: cty));
			if({ cty == IrType:Ptr }, {
				self:emit(inst: IrInst:Retain(val: loaded));
				self:ownedSlots:add(item: capSlot);
			});
			self:emit(inst: IrInst:Store(slot: capSlot, val: loaded, ty: cty));
			uci++;
		});

		pi: 0;
		while({ pi < params:length() }, {
			local Parameter is p: params:get(index: pi);
			local IrType is pty: self:irTypeFor(specType: p:paramType:name);
			local String is slot: '%slot_' . p:name;
			self:localSlots:set(key: p:name, value: slot);
			self:localTypes:set(key: p:name, value: pty);
			self:emit(inst: IrInst:Alloca(slot: slot, ty: pty));
			self:emit(inst: IrInst:Store(slot: slot, val: '%p_' . p:name, ty: pty));
			pi++;
		});

		self:lowerStmts(stmts: body);
		if({ !self:blkTerminated }, {
			self:emitReleaseOwnedLocals();
			if({ retTy == IrType:Void }, {
				self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
			}, {
				local String is defVal: self:emitDefaultVal(ty: retTy);
				self:terminate(inst: IrInst:Ret(hasVal: true, val: defVal, ty: retTy));
			});
		});
		self:mod:addFunction(fn: fn);

		# Emit env destructor if captures exist
		local String is destroyName: envStructName . '_destroy';
		if({ captures:length() > 0 }, {
			local IrFunction is dFn: IrFunction:init(name: destroyName, retType: IrType:Void);
			dFn:sourceFile: savedFn:sourceFile;
			dFn:line: self:currentLine;
			dFn:addParam(name: '%env', ty: IrType:Ptr);
			local IrBlock is dEntry: dFn:addBlock(label: 'entry');
			self:curFn: dFn;
			self:switchBlock(blk: dEntry);
			self:tmpCounter: 0;
			local Int is dci: 0;
			while({ dci < captures:length() }, {
				local String is cname: captures:get(index: dci, default: '');
				local IrType is cty: savedTypes:get(key: cname, default: IrType:I64);
				if({ cty == IrType:Ptr }, {
					local String is dfPtr: self:nextTmp();
					self:emit(inst: IrInst:FieldPtr(dst: dfPtr, objPtr: '%env', structName: envStructName, fieldIndex: dci + 2));
					local String is dVal: self:nextTmp();
					self:emit(inst: IrInst:Load(dst: dVal, slot: dfPtr, ty: IrType:Ptr));
					self:emit(inst: IrInst:Release(val: dVal));
				});
				dci++;
			});
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_rt_release', argTypes: [IrType:Ptr], args: ['%env']));
			self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
			self:mod:addFunction(fn: dFn);
		});

		# Restore outer method builder state
		self:curFn: savedFn;
		self:curBlk: savedBlk;
		self:blkTerminated: savedTerm;
		self:tmpCounter: savedTmp;
		self:lblCounter: savedLbl;
		self:localSlots: savedSlots;
		self:localTypes: savedTypes;
		self:ownedSlots: savedOwned;

		# Allocate and populate %env in outer function if captures exist
		local String is envVal: 'null';
		local String is destroyPtr: 'null';
		if({ captures:length() > 0 }, {
			envVal: self:nextTmp();
			self:emit(inst: IrInst:AllocObj(dst: envVal, structName: envStructName, destroyFn: 'null'));
			local Int is oci: 0;
			while({ oci < captures:length() }, {
				local String is cname: captures:get(index: oci, default: '');
				local String is oSlot: self:localSlots:get(key: cname, default: '');
				local IrType is oTy: self:localTypes:get(key: cname, default: IrType:I64);
				local String is oVal: self:nextTmp();
				self:emit(inst: IrInst:Load(dst: oVal, slot: oSlot, ty: oTy));
				if({ oTy == IrType:Ptr }, {
					self:emit(inst: IrInst:Retain(val: oVal));
				});
				local String is dstPtr: self:nextTmp();
				self:emit(inst: IrInst:FieldPtr(dst: dstPtr, objPtr: envVal, structName: envStructName, fieldIndex: oci + 2));
				self:emit(inst: IrInst:Store(slot: dstPtr, val: oVal, ty: oTy));
				oci++;
			});
			destroyPtr: self:nextTmp();
			self:emit(inst: IrInst:GlobalAddr(dst: destroyPtr, globalName: destroyName));
		});

		local String is fnPtr: self:nextTmp();
		self:emit(inst: IrInst:GlobalAddr(dst: fnPtr, globalName: fnName));
		local String is clsTmp: self:nextTmp();
		local Array of IrType is cT: [IrType:Ptr, IrType:Ptr, IrType:Ptr];
		local Array of String is cV: [fnPtr, envVal, destroyPtr];
		self:emit(inst: IrInst:IrCall(dst: clsTmp, hasDst: true, retType: IrType:Ptr, callee: 'spec_rt_closure_new', argTypes: cT, args: cV));
		return clsTmp;
	}

	local Function of String is lowerCall(Expression is expr, CallData is call){
		local String is nm: call:name;

		# Pluggable call lowerers (control flow, String, Array, Map, etc.)
		local Int is cli: 0;
		local Boolean is handled: false;
		local String is loweredRes: '0';
		while({ cli < self:callLowerers:length() && !handled }, {
			local CallLowerer is cl: self:callLowerers:get(index: cli);
			if({ cl:matches(b: self, expr: expr, call: call) }, {
				loweredRes: cl:lower(b: self, expr: expr, call: call);
				handled: true;
			});
			cli++;
		});
		if({ handled }, { return loweredRes; });

		# Closure local variable call: fn(...)
		if({ self:localSlots:has(key: nm) && self:localTypes:get(key: nm, default: IrType:I64) == IrType:Ptr }, {
			local String is cSlot: self:localSlots:get(key: nm, default: '');
			local String is cObj: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: cObj, slot: cSlot, ty: IrType:Ptr));
			local String is fnPtrAddr: self:nextTmp();
			self:emit(inst: IrInst:FieldPtr(dst: fnPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 0));
			local String is fnPtrVal: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: fnPtrVal, slot: fnPtrAddr, ty: IrType:Ptr));
			local String is envPtrAddr: self:nextTmp();
			self:emit(inst: IrInst:FieldPtr(dst: envPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 1));
			local String is envVal: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: envVal, slot: envPtrAddr, ty: IrType:Ptr));
			local IrType is cRetTy: self:irTypeFor(specType: expr:resolvedType);
			local Array of IrType is cArgT: [IrType:Ptr];
			local Array of String is cArgV: [envVal];
			local Int is cai: 0;
			while({ cai < call:args:length() }, {
				local NamedArg is cna: call:args:get(index: cai);
				local Expression is cav: cna:value;
				local IrType is caty: self:irTypeFor(specType: cav:resolvedType);
				if({ caty == IrType:Void }, { caty: IrType:I64; });
				cArgT:add(item: caty);
				cArgV:add(item: self:lowerExpr(expr: cav));
				cai++;
			});
			local Boolean is cHasDst: cRetTy != IrType:Void;
			local String is cDst: '';
			if({ cHasDst }, { cDst: self:nextTmp(); });
			self:emit(inst: IrInst:IndirectCall(dst: cDst, hasDst: cHasDst, retType: cRetTy, fnPtr: fnPtrVal, argTypes: cArgT, args: cArgV));
			return cDst;
		});

		local String is recvType: call:target:resolvedType;

		# Method / constructor call
		local IrType is retTy: self:irTypeFor(specType: expr:resolvedType);
		local Array of IrType is argTypes: [];
		local Array of String is argVals: [];

		local String is calleeName: match(on: call:target, when: [
			Expression:Ident: local Function of String(String is tname){
				if({ tname != 'self' && self:localSlots:has(key: tname) && recvType != '' }, {
					return recvType . '_' . nm;
				});
				if({ tname != 'self' && !self:localSlots:has(key: tname) }, {
					return self:cStructName(qname: tname) . '_' . nm;
				});
				return self:currentClass . '_' . nm;
			},
			Expression:Path: local Function of String(Array of String is segs){
				if({ segs:length() == 2 && self:heldFields:has(key: segs:get(index: 0, default: '') . ':' . segs:get(index: 1, default: '')) }, {
					if({ recvType != '' }, { return self:cStructName(qname: recvType) . '_' . nm; });
				});
				if({ segs:length() > 0 }, {
					return segs:get(index: segs:length() - 1, default: '') . '_' . nm;
				});
				return self:currentClass . '_' . nm;
			}
		], default: {
			if({ recvType != '' }, { return recvType . '_' . nm; });
			return self:currentClass . '_' . nm;
		});
		# Receiver: self or local variable, else static class Path (or held field receiver)
		local Boolean is hasRecv: match(on: call:target, when: [
			Expression:Ident: local Function of Boolean(String is tname){
				if({ tname == 'self' || self:localSlots:has(key: tname) }, {
					argTypes:add(item: IrType:Ptr);
					argVals:add(item: self:lowerExpr(expr: call:target));
					return true;
				});
				return false;
			},
			Expression:Path: local Function of Boolean(Array of String is segs){
				if({ segs:length() == 2 && self:heldFields:has(key: segs:get(index: 0, default: '') . ':' . segs:get(index: 1, default: '')) }, {
					argTypes:add(item: IrType:Ptr);
					argVals:add(item: self:lowerExpr(expr: call:target));
					return true;
				});
				return false;
			}
		], default: {
			argTypes:add(item: IrType:Ptr);
			argVals:add(item: self:lowerExpr(expr: call:target));
			return true;
		});

		if({ !hasRecv }, {
			local String is pathCName: '';
			local String is pathWithNm: '';
			match(on: call:target, when: [
				Expression:Ident: local Function(String is tname){
					if({ tname != 'self' && !self:localSlots:has(key: tname) }, {
						pathCName: tname;
						pathWithNm: tname . '_' . nm;
					});
				},
				Expression:Path: local Function(Array of String is segs){
					local Int is si: 0;
					while({ si < segs:length() }, {
						if({ si > 0 }, { pathCName: pathCName . '_'; });
						pathCName: pathCName . segs:get(index: si, default: '');
						si++;
					});
					if({ pathCName != '' }, { pathWithNm: pathCName . '_' . nm; });
				}
			], default: {});
			local Boolean is isVariantCtor: (pathWithNm != '') && (self:mod:findStruct(name: pathWithNm):name != '');
			if({ nm == 'init' || isVariantCtor }, {
				# Constructor: ClassName_new + ClassName_init
				local String is clsName: self:currentClass;
				if({ isVariantCtor }, {
					clsName: pathWithNm;
				}, {
					if({ pathCName != '' }, { clsName: pathCName; });
				});
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
		});

		if({ call:bareProvider != '' }, {
			local String is provStruct: self:cStructName(qname: call:bareProvider);
			if({ self:mod:findStruct(name: provStruct):name != '' }, {
				local String is provObj: self:nextTmp();
				self:emit(inst: IrInst:AllocObj(dst: provObj, structName: provStruct, destroyFn: 'null'));
				self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: provStruct . '_init', argTypes: [IrType:Ptr], args: [provObj]));
				argTypes: [IrType:Ptr];
				argVals: [provObj];
				hasRecv: true;
				recvType: call:bareProvider;
				calleeName: provStruct . '_' . nm;
			});
		});

		if({ !hasRecv && !self:heldMethods:has(key: calleeName) }, {
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

		local Int is vslot: -1;
		local String is recvStruct: self:currentClass;
		if({ hasRecv && nm != 'init' && nm != 'destroy' }, {
			if({ recvType != '' }, {
				recvStruct: self:cStructName(qname: recvType);
			});
			local IrStruct is rst: self:mod:findStruct(name: recvStruct);
			vslot: rst:vtableSlot(mname: nm);
		});
		if({ vslot >= 0 }, {
			local String is recvPtr: argVals:get(index: 0, default: 'null');
			local String is vtPtrAddr: self:nextTmp();
			self:emit(inst: IrInst:FieldPtr(dst: vtPtrAddr, objPtr: recvPtr, structName: recvStruct, fieldIndex: 1));
			local String is vtBase: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: vtBase, slot: vtPtrAddr, ty: IrType:Ptr));
			local String is slotPtr: self:nextTmp();
			self:emit(inst: IrInst:PtrElem(dst: slotPtr, basePtr: vtBase, index: vslot));
			local String is fnPtr: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: fnPtr, slot: slotPtr, ty: IrType:Ptr));
			self:emit(inst: IrInst:IndirectCall(dst: dst, hasDst: hasDst, retType: retTy, fnPtr: fnPtr, argTypes: argTypes, args: argVals));
		}, {
			self:emit(inst: IrInst:IrCall(dst: dst, hasDst: hasDst, retType: retTy, callee: calleeName, argTypes: argTypes, args: argVals));
		});
		return dst;
	}
}
