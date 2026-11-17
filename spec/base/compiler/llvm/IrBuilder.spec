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
		['base', 'compiler', 'ast', ClassBindings],
		['base', 'compiler', 'lexer', Keyword],
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
	String is currentMethod: '';
	Int is currentLine: 0;
	IrFunction is curFn: IrFunction:init();
	IrBlock is curBlk: IrBlock:init();
	Boolean is blkTerminated: false;
	Map of String to String is localSlots: Map:init();
	Map of String to IrType is localTypes: Map:init();
	Map of String to Boolean is localIsArc: Map:init();
	Map of String to String is localSpecTypes: Map:init();
	Map of String to Boolean is boxedLocals: Map:init();
	Map of String to Boolean is capturedNames: Map:init();
	Array of String is ownedSlots: [];
	Array of String is scopeVarStack: [];
	Array of String is scopeOldSlotStack: [];
	Array of IrType is scopeOldTypeStack: [];
	Array of Boolean is scopeOldArcStack: [];
	Array of String is scopeOldSpecTypeStack: [];
	Array of Boolean is scopeOldBoxedStack: [];
	Array of Int is scopeMarkStack: [];
	String is curPoolMark: '';
	Boolean is curFnRetIsArc: false;
	String is inlineReturnSlot: '';
	String is inlineReturnEndLbl: '';
	IrType is inlineReturnTy: IrType:Void;
	String is expectedMapKeyType: '';
	String is expectedMapValType: '';
	Array of CallLowerer is callLowerers: [];
	Map of String to ClassInfo is clsMap: Map:init();
	Map of String to String is clsQNameMap: Map:init();
	Map of String to String is methodParamPtrMask: Map:init();
	Map of String to Boolean is methodRetIsPtr: Map:init();
	Map of String to IrType is methodRetTypes: Map:init();
	Map of String to Array of Parameter is methodParams: Map:init();
	Map of String to Boolean is curClassTypeParams: Map:init();
	Map of String to String is heldFields: Map:init();
	Map of String to String is heldFieldTypes: Map:init();
	Map of String to Boolean is heldMethods: Map:init();
	Map of String to String is heldResolvers: Map:init();
	Map of String to String is heldResolverRetTypes: Map:init();
	ClassBindings is bindings: ClassBindings:init();
	String is entryInitOwner: '';
	Int is entryInitOverloadIndex: 0;
	Boolean is entryInitTakesMap: false;
	Array of String is globalVtableNames: [];
	Map of String to Int is globalVtableMap: Map:init();
	Map of String to String is fieldSpecTypes: Map:init();
	String is pathObjPtr: '';
	String is pathStructName: '';
	Int is pathFieldIndex: -1;

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
		if({ specType == 'Int' || specType == 'Byte' }, { return IrType:I64; });
		if({ specType == 'Float' }, { return IrType:F64; });
		if({ specType == 'Boolean' }, { return IrType:I1; });
		if({ specType == 'Void' || specType == '' }, { return IrType:Void; });
		return IrType:Ptr;
	}

	Function of Boolean is isArcSpecType(String is specType){
		if({ specType == '' || specType == 'Void' || specType == 'Any' || specType == 'Int' || specType == 'Float' || specType == 'Boolean' || specType == 'Byte' || self:curClassTypeParams:has(key: specType) }, {
			return false;
		});
		return true;
	}

	Function of String is castIfNeeded(String is val, IrType is fromTy, IrType is toTy){
		if({ fromTy == toTy || fromTy == IrType:Void || toTy == IrType:Void || val == '' }, { return val; });
		local String is dst: self:nextTmp();
		self:emit(inst: IrInst:IrCast(dst: dst, val: val, fromType: fromTy, toType: toTy));
		return dst;
	}

	Function is emit(IrInst is inst){
		if({ !self:blkTerminated }, {
			local Boolean is hoisted: false;
			match(on: inst, when: [
				IrInst:Alloca: local Function(String is slot, IrType is ty){
					if({ self:curFn:blocks:length() > 0 }, {
						local IrBlock is entryBlk: self:curFn:blocks:get(index: 0);
						if({ self:curBlk:label != entryBlk:label }, {
							if({ ty == IrType:Ptr }, {
								entryBlk:prependAt(inst: IrInst:Store(slot: slot, val: 'null', ty: IrType:Ptr), line: self:currentLine);
							});
							entryBlk:prependAt(inst: inst, line: self:currentLine);
							hoisted: true;
						});
					});
				}
			], default: {});
			if({ !hoisted }, {
				self:curBlk:appendAt(inst: inst, line: self:currentLine);
			});
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

	Function is resetScopes(){
		self:scopeVarStack: [];
		self:scopeOldSlotStack: [];
		self:scopeOldTypeStack: [];
		self:scopeOldArcStack: [];
		self:scopeOldSpecTypeStack: [];
		self:scopeOldBoxedStack: [];
		self:scopeMarkStack: [];
	}

	Function is pushScope(){
		self:scopeMarkStack:add(item: self:scopeVarStack:length());
	}

	Function is bindLocal(String is name, String is slot, IrType is ty, Boolean is isArc, String is specType, Boolean is isBoxed){
		if({ self:scopeMarkStack:length() > 0 }, {
			self:scopeVarStack:add(item: name);
			if({ self:localSlots:has(key: name) }, {
				self:scopeOldSlotStack:add(item: self:localSlots:get(key: name, default: ''));
				self:scopeOldTypeStack:add(item: self:localTypes:get(key: name, default: IrType:I64));
				self:scopeOldArcStack:add(item: self:localIsArc:get(key: name, default: false));
				self:scopeOldSpecTypeStack:add(item: self:localSpecTypes:get(key: name, default: ''));
				self:scopeOldBoxedStack:add(item: self:boxedLocals:has(key: name));
			}, {
				self:scopeOldSlotStack:add(item: '');
				self:scopeOldTypeStack:add(item: IrType:I64);
				self:scopeOldArcStack:add(item: false);
				self:scopeOldSpecTypeStack:add(item: '');
				self:scopeOldBoxedStack:add(item: false);
			});
		});
		self:localSlots:set(key: name, value: slot);
		self:localTypes:set(key: name, value: ty);
		self:localIsArc:set(key: name, value: isArc);
		self:localSpecTypes:set(key: name, value: specType);
		if({ isBoxed }, {
			self:boxedLocals:set(key: name, value: true);
		}, {
			if({ self:boxedLocals:has(key: name) }, {
				self:boxedLocals:remove(key: name);
			});
		});
	}

	Function is popScope(){
		if({ self:scopeMarkStack:length() == 0 }, { return; });
		local Int is mark: self:scopeMarkStack:pop(default: 0);
		while({ self:scopeVarStack:length() > mark }, {
			local String is name: self:scopeVarStack:pop(default: '');
			local String is oldSlot: self:scopeOldSlotStack:pop(default: '');
			local IrType is oldTy: self:scopeOldTypeStack:pop(default: IrType:I64);
			local Boolean is oldArc: self:scopeOldArcStack:pop(default: false);
			local String is oldSpec: self:scopeOldSpecTypeStack:pop(default: '');
			local Boolean is oldBoxed: self:scopeOldBoxedStack:pop(default: false);
			if({ oldSlot == '' }, {
				self:localSlots:remove(key: name);
				self:localTypes:remove(key: name);
				self:localIsArc:remove(key: name);
				self:localSpecTypes:remove(key: name);
				if({ self:boxedLocals:has(key: name) }, {
					self:boxedLocals:remove(key: name);
				});
			}, {
				self:localSlots:set(key: name, value: oldSlot);
				self:localTypes:set(key: name, value: oldTy);
				self:localIsArc:set(key: name, value: oldArc);
				self:localSpecTypes:set(key: name, value: oldSpec);
				if({ oldBoxed }, {
					self:boxedLocals:set(key: name, value: true);
				}, {
					if({ self:boxedLocals:has(key: name) }, {
						self:boxedLocals:remove(key: name);
					});
				});
			});
		});
	}

	local Function of Boolean is isStdlibClass(ClassInfo is cls){
		if({ self:bindings:isSysinternal(cls: cls) }, { return true; });
		if({ cls:name == 'List' || cls:name == 'LoopControl' || cls:name == 'LoopCallback' || cls:name == 'Parallel' || cls:name == 'Class' || cls:name == 'Function' || cls:name == 'Int' || cls:name == 'Float' || cls:name == 'Boolean' || cls:name == 'Byte' || cls:name == 'Void' || cls:name == 'Any' || cls:name == 'Object' }, { return true; });
		return false;
	}

	Function of String is baseTypeName(String is t){
		local String is res: t;
		local Int is ofIdx: res:indexOf(search: ' of ', default: -1);
		if({ ofIdx > 0 }, {
			res: res:substring(start: 0, end: ofIdx);
		});
		if({ res:contains(needle: ':') && !self:clsQNameMap:has(key: res) }, {
			local Int is cIdx: res:indexOf(search: ':', default: -1);
			if({ cIdx > 0 }, {
				local String is cand: res:substring(start: 0, end: cIdx);
				if({ cand == 'Array' || cand == 'Map' || cand == 'List' || self:clsQNameMap:has(key: cand) }, {
					res: cand;
				});
			});
		});
		return res;
	}

	Function of String is cStructName(String is qname){
		return qname:replaceAll(target: ':', replacement: '_');
	}

	local Function of ClassInfo is resolveBaseClass(ClassInfo is cls, String is bname, Map of String to ClassInfo is clsMap){
		if({ clsMap:has(key: bname) }, {
			return clsMap:get(key: bname, default: cls);
		});
		if({ cls:outerName != '' }, {
			if({ (cls:outerName == bname || cls:outerName:endsWith(suffix: ':' . bname)) && clsMap:has(key: cls:outerName) }, {
				return clsMap:get(key: cls:outerName, default: cls);
			});
			local String is sib: cls:outerName . ':' . bname;
			if({ clsMap:has(key: sib) }, {
				return clsMap:get(key: sib, default: cls);
			});
		});
		return cls;
	}

	local Function is addInheritedFields(IrStruct is st, ClassInfo is cls, Map of String to ClassInfo is clsMap, Map of String to Boolean is seenFields){
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: self:resolveBaseClass(cls: cls, bname: bname, clsMap: clsMap);
			if({ bcls:qualifiedName() != cls:qualifiedName() }, {
				self:addInheritedFields(st: st, cls: bcls, clsMap: clsMap, seenFields: seenFields);
			});
			bi++;
		});
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:FIELD && m:name != 'using' && m:name != 'namespace' && !m:hasModifier(kw: Keyword:HELD) && !seenFields:has(key: m:name) }, {
				seenFields:set(key: m:name, value: true);
				local IrType is fty: self:irTypeFor(specType: m:memberType:name);
				if({ fty == IrType:Void }, { fty: IrType:Ptr; });
				local Boolean is fIsArc: self:isArcSpecType(specType: m:memberType:name);
				local Int is bti: 0;
				while({ bti < cls:typeParams:length() }, {
					if({ cls:typeParams:get(index: bti, default: '') == m:memberType:name }, { fIsArc: false; });
					bti++;
				});
				st:addFieldArc(name: m:name, ty: fty, isArc: fIsArc);
				self:fieldSpecTypes:set(key: st:name . ':' . m:name, value: m:memberType:name);
			});
			mi++;
		});
	}

	local Function is buildVtable(IrStruct is st, ClassInfo is cls, Map of String to ClassInfo is clsMap){
		if({ self:bindings:isTransparent(c: cls) }, { return; });
		if({ st:vtableMethodNames:length() == 0 && self:globalVtableNames:length() > 0 }, {
			local Int is gi: 0;
			while({ gi < self:globalVtableNames:length() }, {
				st:vtableMethodNames:add(item: self:globalVtableNames:get(index: gi, default: ''));
				st:vtableFns:add(item: 'null');
				gi++;
			});
		});
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: self:resolveBaseClass(cls: cls, bname: bname, clsMap: clsMap);
			if({ bcls:qualifiedName() != cls:qualifiedName() }, {
				self:buildVtable(st: st, cls: bcls, clsMap: clsMap);
			});
			bi++;
		});
		local String is sname: self:cStructName(qname: cls:qualifiedName());
		local Map of String to Int is mCounts: Map:init();
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:METHOD }, {
				local Int is ovIdx: mCounts:get(key: m:name, default: 0);
				mCounts:set(key: m:name, value: ovIdx + 1);
				if({ m:name != 'init' && m:name != 'destroy' && !m:hasModifier(kw: Keyword:HELD) }, {
					local String is vkey: if({ ovIdx > 0 }, { m:name . '_' . ((ovIdx + 1) as String) }, { m:name });
					local String is fnSym: sname . '_' . vkey;
					st:setVtableMethod(mname: vkey, fnName: fnSym);
				});
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
		local Map of String to String is clsQNameMap: Map:init();
		local Int is ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is c0: allClasses:get(index: ci);
			clsMap:set(key: c0:qualifiedName(), value: c0);
			clsQNameMap:set(key: c0:qualifiedName(), value: c0:qualifiedName());
			if({ c0:outerName == '' }, {
				clsMap:set(key: c0:name, value: c0);
				clsQNameMap:set(key: c0:name, value: c0:qualifiedName());
			});
			ci++;
		});
		self:clsMap: clsMap;
		self:clsQNameMap: clsQNameMap;
		self:methodParamPtrMask: Map:init();
		self:methodRetIsPtr: Map:init();
		self:methodRetTypes: Map:init();
		self:methodParams: Map:init();
		self:heldFields: Map:init();
		self:heldFieldTypes: Map:init();
		self:heldMethods: Map:init();
		self:globalVtableNames: [];
		self:globalVtableMap: Map:init();

		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is vc: allClasses:get(index: ci);
			local Map of String to Int is vmCounts: Map:init();
			local Int is vmi: 0;
			while({ vmi < vc:members:length() }, {
				local Member is vm: vc:members:get(index: vmi);
				if({ vm:kind == MemberKind:METHOD }, {
					local Int is vOv: vmCounts:get(key: vm:name, default: 0);
					vmCounts:set(key: vm:name, value: vOv + 1);
					if({ vm:name != 'init' && vm:name != 'destroy' && !vm:hasModifier(kw: Keyword:HELD) }, {
						local String is vk: if({ vOv > 0 }, { vm:name . '_' . ((vOv + 1) as String) }, { vm:name });
						if({ !self:globalVtableMap:has(key: vk) }, {
							self:globalVtableMap:set(key: vk, value: self:globalVtableNames:length());
							self:globalVtableNames:add(item: vk);
						});
					});
				});
				vmi++;
			});
			ci++;
		});

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
				local Boolean is hasArcField: false;
				local Int is dfi: 2;
				while({ dfi < st:fieldTypes:length() }, {
					if({ st:fieldIsArc:get(index: dfi, default: false) }, {
						hasArcField: true;
					});
					dfi++;
				});
				local Boolean is hasUserDestroy: false;
				local Int is dmi: 0;
				while({ dmi < cls:members:length() }, {
					local Member is dm: cls:members:get(index: dmi);
					if({ dm:kind == MemberKind:METHOD && dm:name == 'destroy' && dm:params:length() == 0 }, {
						hasUserDestroy: true;
					});
					dmi++;
				});
				if({ hasArcField || hasUserDestroy }, {
					st:destroyFn: sname . '__destroy';
				});
				local Map of String to Int is mCounts: Map:init();
				local Int is mmi: 0;
				while({ mmi < cls:members:length() }, {
					local Member is mm: cls:members:get(index: mmi);
					if({ mm:kind == MemberKind:METHOD }, {
						local Int is ovIdx: mCounts:get(key: mm:name, default: 0);
						mCounts:set(key: mm:name, value: ovIdx + 1);
						local String is mSym: if({ ovIdx > 0 }, { sname . '_' . mm:name . '_' . ((ovIdx + 1) as String) }, { sname . '_' . mm:name });
						local String is mask: '';
						local Int is mpi: 0;
						while({ mpi < mm:params:length() }, {
							local Parameter is mp: mm:params:get(index: mpi);
							if({ self:irTypeFor(specType: mp:paramType:name) == IrType:Ptr }, {
								mask: mask . '1';
							}, {
								mask: mask . '0';
							});
							mpi++;
						});
						self:methodParamPtrMask:set(key: mSym, value: mask);
						self:methodParams:set(key: mSym, value: mm:params);
						local IrType is mRetTy: self:methodReturnType(mt: mm:memberType);
						self:methodRetTypes:set(key: mSym, value: mRetTy);
						if({ mRetTy == IrType:Ptr }, {
							self:methodRetIsPtr:set(key: mSym, value: true);
						});
					});
					mmi++;
				});
				self:buildVtable(st: st, cls: cls, clsMap: clsMap);
				self:registerClassMetaAndHeld(st: st, cls: cls, sname: sname);
				self:mod:addStruct(s: st);
			});
			ci++;
		});

		# 1b. Inherit held fields from ancestor classes onto subclass prefixes
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			local String is sname: self:cStructName(qname: cls:qualifiedName());
			local Map of String to Boolean is hvis: Map:init();
			hvis:set(key: cls:qualifiedName(), value: true);
			self:inheritHeldFromAncestors(cls: cls, cur: cls, sname: sname, clsMap: clsMap, hvis: hvis);
			ci++;
		});

		# 2. Lower methods, construct helpers, and held field __ensure accessors
		local Map of String to Boolean is seenFns: Map:init();
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			local Boolean is isTransCls: self:bindings:isTransparent(c: cls);
			local String is sname: self:cStructName(qname: cls:qualifiedName());
			self:currentClass: sname;
			self:curClassTypeParams: Map:init();
			local Int is tpi: 0;
			while({ tpi < cls:typeParams:length() }, {
				self:curClassTypeParams:set(key: cls:typeParams:get(index: tpi, default: ''), value: true);
				tpi++;
			});
			local Map of String to Int is mCounts2: Map:init();
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
					local Int is ovIdx: mCounts2:get(key: m:name, default: 0);
					mCounts2:set(key: m:name, value: ovIdx + 1);
					local String is fnName: if({ ovIdx > 0 }, { sname . '_' . m:name . '_' . ((ovIdx + 1) as String) }, { sname . '_' . m:name });
					if({ (!isTransCls || m:body:length() > 0) && !seenFns:has(key: fnName) }, {
						seenFns:set(key: fnName, value: true);
						self:buildMethod(cls: cls, m: m, fnName: fnName);
					});
				});
				mi++;
			});
			if({ !isTransCls }, {
				local String is initFnName: sname . '_init';
				if({ !seenFns:has(key: initFnName) }, {
					seenFns:set(key: initFnName, value: true);
					self:buildDefaultInit(cls: cls, sname: sname, initFn: initFnName);
				});
			});
			local IrStruct is st2: self:mod:findStruct(name: sname);
			if({ st2:destroyFn != 'null' && !seenFns:has(key: st2:destroyFn) }, {
				seenFns:set(key: st2:destroyFn, value: true);
				self:buildDestroyHelper(st: st2, cls: cls, sname: sname, destroyFn: st2:destroyFn);
			});
			if({ st2:constructFn != 'null' && !seenFns:has(key: st2:constructFn) }, {
				seenFns:set(key: st2:constructFn, value: true);
				self:buildConstructHelper(cls: cls, sname: sname, ctorFn: st2:constructFn);
			});
			ci++;
		});
		self:currentClass: '';
		self:currentMethod: '';

		# 3. Emit held resolvers, RTTI hierarchy helpers, and main()
		self:buildHeldResolvers();
		self:buildRttiHelpers(allClasses: allClasses);
		if({ entryClass != '' }, {
			self:buildMainEntry(entryClass: entryClass);
		});

		return self:mod;
	}

	local Function is inheritHeldFromAncestors(ClassInfo is cls, ClassInfo is cur, String is sname, Map of String to ClassInfo is clsMap, Map of String to Boolean is hvis){
		local Int is bi: 0;
		while({ bi < cur:baseClasses:length() }, {
			local String is bname: cur:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: self:resolveBaseClass(cls: cur, bname: bname, clsMap: clsMap);
			if({ bcls:name != '' && !hvis:has(key: bcls:qualifiedName()) }, {
				hvis:set(key: bcls:qualifiedName(), value: true);
				local String is bsname: self:cStructName(qname: bcls:qualifiedName());
				local Int is bmi: 0;
				while({ bmi < bcls:members:length() }, {
					local Member is bm: bcls:members:get(index: bmi);
					if({ bm:kind == MemberKind:FIELD && bm:hasModifier(kw: Keyword:HELD) }, {
						local String is hkS: sname . ':' . bm:name;
						if({ !self:heldFields:has(key: hkS) }, {
							local String is owner: self:heldFields:get(key: bsname . ':' . bm:name, default: bsname);
							self:heldFields:set(key: hkS, value: owner);
							self:heldFields:set(key: cls:name . ':' . bm:name, value: owner);
						});
					});
					bmi++;
				});
				self:inheritHeldFromAncestors(cls: cls, cur: bcls, sname: sname, clsMap: clsMap, hvis: hvis);
			});
			bi++;
		});
	}

	local Function is emitPoolEnter(){
		if({ self:currentClass == 'Vector' && self:currentMethod != 'mapKeys' }, {
			self:curPoolMark: '';
			return;
		});
		local String is mark: self:nextTmp();
		self:emit(inst: IrInst:IrCall(dst: mark, hasDst: true, retType: IrType:I64, callee: 'spec_pool_frame', argTypes: [], args: []));
		self:curPoolMark: mark;
	}

	local Function is emitPoolExit(){
		if({ self:curPoolMark != '' }, {
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_pool_release_to', argTypes: [IrType:I64], args: [self:curPoolMark]));
		});
	}

	Function is emitClaimPool(String is val){
		if({ val != '' && val != 'null' }, {
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Ptr, callee: 'spec_claim_pool', argTypes: [IrType:Ptr], args: [val]));
		});
	}

	local Function of String is destroyFnFor(String is structName){
		local IrStruct is st: self:mod:findStruct(name: structName);
		if({ st:name != '' && st:destroyFn != 'null' }, {
			return '@' . st:destroyFn;
		});
		return 'null';
	}

	local Function is buildDestroyHelper(IrStruct is st, ClassInfo is cls, String is sname, String is destroyFn){
		local IrFunction is fn: IrFunction:init(name: destroyFn, retType: IrType:Void);
		fn:addParam(name: '%self', ty: IrType:Ptr);
		local IrBlock is entry: fn:addBlock(label: 'entry');
		self:curFn: fn;
		self:switchBlock(blk: entry);
		self:tmpCounter: 0;
		self:curPoolMark: '';
		local Int is dmi: 0;
		while({ dmi < cls:members:length() }, {
			local Member is dm: cls:members:get(index: dmi);
			if({ dm:kind == MemberKind:METHOD && dm:name == 'destroy' && dm:params:length() == 0 }, {
				self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: sname . '_destroy', argTypes: [IrType:Ptr], args: ['%self']));
			});
			dmi++;
		});
		local Int is fi: 2;
		while({ fi < st:fieldTypes:length() }, {
			if({ st:fieldIsArc:get(index: fi, default: false) }, {
				local String is fptr: self:nextTmp();
				self:emit(inst: IrInst:FieldPtr(dst: fptr, objPtr: '%self', structName: st:name, fieldIndex: fi));
				local String is fval: self:nextTmp();
				self:emit(inst: IrInst:Load(dst: fval, slot: fptr, ty: IrType:Ptr));
				self:emit(inst: IrInst:Release(val: fval));
				self:emit(inst: IrInst:Store(slot: fptr, val: 'null', ty: IrType:Ptr));
			});
			fi++;
		});
		self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
		self:mod:addFunction(fn: fn);
	}

	local Function is buildMainEntry(String is entryClass){
		local IrFunction is mainFn: IrFunction:init(name: 'main', retType: IrType:I64);
		mainFn:addParam(name: '%argc', ty: IrType:I64);
		mainFn:addParam(name: '%argv', ty: IrType:Ptr);
		local IrBlock is entry: mainFn:addBlock(label: 'entry');
		self:curFn: mainFn;
		self:switchBlock(blk: entry);
		self:tmpCounter: 0;
		self:emitPoolEnter();

		local String is argsMap: self:nextTmp();
		self:emit(inst: IrInst:IrCall(dst: argsMap, hasDst: true, retType: IrType:Ptr, callee: 'spec_cli_args_map', argTypes: [IrType:I64, IrType:Ptr], args: ['%argc', '%argv']));

		# Allocate entry object and call the resolved entry init
		local String is obj: self:nextTmp();
		self:emit(inst: IrInst:AllocObj(dst: obj, structName: entryClass, destroyFn: self:destroyFnFor(structName: entryClass)));
		local String is initOwner: entryClass;
		if({ self:entryInitOwner != '' }, {
			initOwner: self:cStructName(qname: self:clsQNameMap:get(key: self:entryInitOwner, default: self:entryInitOwner));
		});
		local String is initSuf: if({ self:entryInitOverloadIndex > 0 }, { '_' . ((self:entryInitOverloadIndex + 1) as String) }, { '' });
		if({ self:entryInitTakesMap }, {
			local Array of IrType is initArgTypes: [IrType:Ptr, IrType:Ptr];
			local Array of String is initArgs: [obj, argsMap];
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: initOwner . '_init' . initSuf, argTypes: initArgTypes, args: initArgs));
		}, {
			local Array of IrType is initArgTypes: [IrType:Ptr];
			local Array of String is initArgs: [obj];
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: initOwner . '_init' . initSuf, argTypes: initArgTypes, args: initArgs));
		});
		self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_drain_async_tasks', argTypes: [], args: []));
		self:emitPoolExit();
		self:emit(inst: IrInst:Release(val: argsMap));
		self:emit(inst: IrInst:Release(val: obj));
		self:curPoolMark: '';
		local String is zero: self:nextTmp();
		self:emit(inst: IrInst:ConstInt(dst: zero, value: 0));
		self:terminate(inst: IrInst:Ret(hasVal: true, val: zero, ty: IrType:I64));
		self:mod:addFunction(fn: mainFn);
	}

	local Function is collectAncestors(ClassInfo is cls, Map of String to Boolean is seen, Array of String is out){
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bn: cls:baseClasses:get(index: bi, default: '');
			if({ bn != '' && !seen:has(key: bn) }, {
				seen:set(key: bn, value: true);
				out:add(item: bn);
				if({ self:clsMap:has(key: bn) }, {
					local ClassInfo is bcls: self:clsMap:get(key: bn, default: cls);
					self:collectAncestors(cls: bcls, seen: seen, out: out);
				});
			});
			bi++;
		});
	}

	local Function is buildRttiHelpers(Array of ClassInfo is allClasses){
		# spec_is_subclass_of(ptr %actual, ptr %target) -> i1
		local IrFunction is subFn: IrFunction:init(name: 'spec_is_subclass_of', retType: IrType:I1);
		subFn:addParam(name: '%actual', ty: IrType:Ptr);
		subFn:addParam(name: '%target', ty: IrType:Ptr);
		local IrBlock is entry: subFn:addBlock(label: 'entry');
		self:curFn: subFn;
		self:switchBlock(blk: entry);
		self:tmpCounter: 0;
		self:lblCounter: 0;
		self:curPoolMark: '';

		local String is aNull: self:nextTmp();
		self:emit(inst: IrInst:Cmp(dst: aNull, op: '==', lhs: '%actual', rhs: 'null', ty: IrType:Ptr));
		local String is tNull: self:nextTmp();
		self:emit(inst: IrInst:Cmp(dst: tNull, op: '==', lhs: '%target', rhs: 'null', ty: IrType:Ptr));
		local String is eitherNull: self:nextTmp();
		self:emit(inst: IrInst:BinOp(dst: eitherNull, op: '|', lhs: aNull, rhs: tNull, ty: IrType:I1));
		local String is retFalseLbl: self:nextLabel(prefix: 'rtti_false');
		local String is nonNullLbl: self:nextLabel(prefix: 'rtti_nn');
		self:terminate(inst: IrInst:CondBr(cond: eitherNull, thenLabel: retFalseLbl, elseLabel: nonNullLbl));

		local IrBlock is nnBlk: subFn:addBlock(label: nonNullLbl);
		self:switchBlock(blk: nnBlk);
		local String is retTrueLbl: self:nextLabel(prefix: 'rtti_true');
		local String is eqSelf: self:nextTmp();
		self:emit(inst: IrInst:IrCall(dst: eqSelf, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%actual', '%target']));
		local String is chkAnyLbl: self:nextLabel(prefix: 'rtti_any');
		self:terminate(inst: IrInst:CondBr(cond: eqSelf, thenLabel: retTrueLbl, elseLabel: chkAnyLbl));

		local IrBlock is anyBlk: subFn:addBlock(label: chkAnyLbl);
		self:switchBlock(blk: anyBlk);
		local Int is anyStrId: self:mod:internStringLiteral(value: 'Any');
		local String is anyPtr: self:nextTmp();
		self:emit(inst: IrInst:GlobalAddr(dst: anyPtr, globalName: '.str.' . (anyStrId as String)));
		local String is eqAny: self:nextTmp();
		self:emit(inst: IrInst:IrCall(dst: eqAny, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%target', anyPtr]));
		local String is chkStrLbl: self:nextLabel(prefix: 'rtti_str');
		self:terminate(inst: IrInst:CondBr(cond: eqAny, thenLabel: retTrueLbl, elseLabel: chkStrLbl));

		local IrBlock is strBlk: subFn:addBlock(label: chkStrLbl);
		self:switchBlock(blk: strBlk);
		local Int is strStrId: self:mod:internStringLiteral(value: 'Stringable');
		local String is strPtr: self:nextTmp();
		self:emit(inst: IrInst:GlobalAddr(dst: strPtr, globalName: '.str.' . (strStrId as String)));
		local String is eqStr: self:nextTmp();
		self:emit(inst: IrInst:IrCall(dst: eqStr, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%target', strPtr]));
		local String is nextChkLbl: self:nextLabel(prefix: 'rtti_cls');
		self:terminate(inst: IrInst:CondBr(cond: eqStr, thenLabel: retTrueLbl, elseLabel: nextChkLbl));

		local IrBlock is curChkBlk: subFn:addBlock(label: nextChkLbl);
		self:switchBlock(blk: curChkBlk);
		local Int is ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			if({ !self:isStdlibClass(cls: cls) || cls:baseClasses:length() > 0 }, {
				local Array of String is ancs: [];
				self:collectAncestors(cls: cls, seen: Map:init(), out: ancs);
				if({ ancs:length() > 0 }, {
					local Int is qnId: self:mod:internStringLiteral(value: cls:qualifiedName());
					local String is qnPtr: self:nextTmp();
					self:emit(inst: IrInst:GlobalAddr(dst: qnPtr, globalName: '.str.' . (qnId as String)));
					local String is eqCls: self:nextTmp();
					self:emit(inst: IrInst:IrCall(dst: eqCls, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%actual', qnPtr]));
					local String is matchClsLbl: self:nextLabel(prefix: 'rtti_m');
					local String is skipClsLbl: self:nextLabel(prefix: 'rtti_n');
					self:terminate(inst: IrInst:CondBr(cond: eqCls, thenLabel: matchClsLbl, elseLabel: skipClsLbl));

					local IrBlock is mBlk: subFn:addBlock(label: matchClsLbl);
					self:switchBlock(blk: mBlk);
					local Int is ai: 0;
					while({ ai < ancs:length() }, {
						local String is aname: ancs:get(index: ai, default: '');
						local Int is aId: self:mod:internStringLiteral(value: aname);
						local String is aPtr: self:nextTmp();
						self:emit(inst: IrInst:GlobalAddr(dst: aPtr, globalName: '.str.' . (aId as String)));
						local String is eqAnc: self:nextTmp();
						self:emit(inst: IrInst:IrCall(dst: eqAnc, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%target', aPtr]));
						local String is nextAncLbl: self:nextLabel(prefix: 'rtti_a');
						self:terminate(inst: IrInst:CondBr(cond: eqAnc, thenLabel: retTrueLbl, elseLabel: nextAncLbl));
						local IrBlock is aBlk: subFn:addBlock(label: nextAncLbl);
						self:switchBlock(blk: aBlk);
						ai++;
					});
					self:terminate(inst: IrInst:Br(target: retFalseLbl));

					curChkBlk: subFn:addBlock(label: skipClsLbl);
					self:switchBlock(blk: curChkBlk);
				});
			});
			ci++;
		});
		self:terminate(inst: IrInst:Br(target: retFalseLbl));

		local IrBlock is trueBlk: subFn:addBlock(label: retTrueLbl);
		self:switchBlock(blk: trueBlk);
		local String is tVal: self:nextTmp();
		self:emit(inst: IrInst:ConstBool(dst: tVal, value: true));
		self:terminate(inst: IrInst:Ret(hasVal: true, val: tVal, ty: IrType:I1));

		local IrBlock is falseBlk: subFn:addBlock(label: retFalseLbl);
		self:switchBlock(blk: falseBlk);
		local String is fVal: self:nextTmp();
		self:emit(inst: IrInst:ConstBool(dst: fVal, value: false));
		self:terminate(inst: IrInst:Ret(hasVal: true, val: fVal, ty: IrType:I1));
		self:mod:addFunction(fn: subFn);

		# spec_cast_check(ptr %obj, ptr %target) -> ptr
		local IrFunction is ccFn: IrFunction:init(name: 'spec_cast_check', retType: IrType:Ptr);
		ccFn:addParam(name: '%obj', ty: IrType:Ptr);
		ccFn:addParam(name: '%target', ty: IrType:Ptr);
		local IrBlock is ccEntry: ccFn:addBlock(label: 'entry');
		self:curFn: ccFn;
		self:switchBlock(blk: ccEntry);
		self:tmpCounter: 0;
		self:lblCounter: 0;
		local String is isNull: self:nextTmp();
		self:emit(inst: IrInst:Cmp(dst: isNull, op: '==', lhs: '%obj', rhs: 'null', ty: IrType:Ptr));
		local String is ccNullLbl: self:nextLabel(prefix: 'cc_null');
		local String is ccChkLbl: self:nextLabel(prefix: 'cc_chk');
		self:terminate(inst: IrInst:CondBr(cond: isNull, thenLabel: ccNullLbl, elseLabel: ccChkLbl));

		local IrBlock is ccNullBlk: ccFn:addBlock(label: ccNullLbl);
		self:switchBlock(blk: ccNullBlk);
		self:terminate(inst: IrInst:Ret(hasVal: true, val: 'null', ty: IrType:Ptr));

		local IrBlock is ccChkBlk: ccFn:addBlock(label: ccChkLbl);
		self:switchBlock(blk: ccChkBlk);
		local String is actualType: self:nextTmp();
		self:emit(inst: IrInst:Load(dst: actualType, slot: '%obj', ty: IrType:Ptr));
		local String is ok: self:nextTmp();
		self:emit(inst: IrInst:IrCall(dst: ok, hasDst: true, retType: IrType:I1, callee: 'spec_is_subclass_of', argTypes: [IrType:Ptr, IrType:Ptr], args: [actualType, '%target']));
		local String is ccOkLbl: self:nextLabel(prefix: 'cc_ok');
		local String is ccFailLbl: self:nextLabel(prefix: 'cc_fail');
		self:terminate(inst: IrInst:CondBr(cond: ok, thenLabel: ccOkLbl, elseLabel: ccFailLbl));

		local IrBlock is ccFailBlk: ccFn:addBlock(label: ccFailLbl);
		self:switchBlock(blk: ccFailBlk);
		self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_panic_cast', argTypes: [IrType:Ptr, IrType:Ptr], args: [actualType, '%target']));
		self:terminate(inst: IrInst:Ret(hasVal: true, val: '%obj', ty: IrType:Ptr));

		local IrBlock is ccOkBlk: ccFn:addBlock(label: ccOkLbl);
		self:switchBlock(blk: ccOkBlk);
		self:terminate(inst: IrInst:Ret(hasVal: true, val: '%obj', ty: IrType:Ptr));
		self:mod:addFunction(fn: ccFn);
	}

	local Function of String is methodReturnSpecType(Type is mt){
		if({ mt:name == 'Function' }, {
			if({ mt:params:length() > 0 }, {
				local Type is rt: mt:params:get(index: 0);
				return rt:name;
			});
			return 'Void';
		});
		return mt:name;
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
		local String is clsKey: '@cls:' . cls:qualifiedName();
		if({ seen:has(key: clsKey) }, { return; });
		seen:set(key: clsKey, value: true);
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local Boolean is isEnclosing: cls:outerName != '' && (cls:outerName == bname || cls:outerName:endsWith(suffix: ':' . bname));
			if({ self:clsMap:has(key: bname) }, {
				local ClassInfo is bcls: self:clsMap:get(key: bname, default: cls);
				local Boolean is bIsEnum: false;
				local Int is ebi: 0;
				while({ ebi < bcls:baseClasses:length() }, {
					if({ bcls:baseClasses:get(index: ebi, default: '') == 'Enum' }, { bIsEnum: true; });
					ebi++;
				});
				if({ !isEnclosing || bIsEnum }, {
					self:emitFieldDefaults(cls: bcls, seen: seen);
				});
			});
			bi++;
		});
		local IrStruct is st: self:mod:findStruct(name: self:currentClass);
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:FIELD && m:name != 'using' && m:name != 'namespace' && !m:hasModifier(kw: Keyword:HELD) && m:hasInit }, {
				local Int is fidx: st:fieldIndex(name: m:name);
				if({ fidx >= 0 }, {
					local IrType is fty: st:fieldTypes:get(index: fidx);
					local String is ptr: self:nextTmp();
					self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: '%self', structName: self:currentClass, fieldIndex: fidx));
					local String is prevMapK: self:expectedMapKeyType;
					local String is prevMapV: self:expectedMapValType;
					if({ m:memberType:name == 'Map' && m:memberType:params:length() >= 1 }, {
						local Type is mkp0: m:memberType:params:get(index: 0);
						self:expectedMapKeyType: mkp0:name;
						if({ m:memberType:params:length() >= 2 }, {
							local Type is mkp1: m:memberType:params:get(index: 1);
							self:expectedMapValType: mkp1:name;
						});
					});
					local String is val: self:lowerExpr(expr: m:initExpr);
					self:expectedMapKeyType: prevMapK;
					self:expectedMapValType: prevMapV;
					local IrType is vty: self:irTypeFor(specType: m:initExpr:resolvedType);
					val: self:castIfNeeded(val: val, fromTy: vty, toTy: fty);
					if({ st:fieldIsArc:get(index: fidx, default: false) }, {
						if({ val != '' && val != 'null' }, {
							self:emit(inst: IrInst:Retain(val: val));
						});
						if({ seen:has(key: m:name) }, {
							local String is oldF: self:nextTmp();
							self:emit(inst: IrInst:Load(dst: oldF, slot: ptr, ty: IrType:Ptr));
							self:emit(inst: IrInst:Release(val: oldF));
						});
					});
					seen:set(key: m:name, value: true);
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
					if({ m:name == 'resolveHeld' }, {
						self:heldResolvers:set(key: sname, value: sname);
						self:heldResolvers:set(key: cls:name, value: sname);
						self:heldResolverRetTypes:set(key: sname, value: self:methodReturnSpecType(mt: m:memberType));
					});
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
					if({ self:bindings:isTransparent(c: cls) && m:body:length() == 0 }, {
						st:metaMethodFns:add(item: 'null');
					}, {
						st:metaMethodFns:add(item: sname . '_' . m:name);
					});
					st:metaMethodFlags:add(item: flags);
					st:metaMethodLines:add(item: m:line);
				});
			});
			mi++;
		});
		if({ (!hasInitMember || hasZeroArgInit) && !self:bindings:isTransparent(c: cls) && cls:baseClass != 'Enum' }, {
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
		self:emit(inst: IrInst:AllocObj(dst: obj, structName: sname, destroyFn: self:destroyFnFor(structName: sname)));
		local Boolean is hasZeroInit: false;
		local Boolean is hasAnyInit: false;
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:METHOD && m:name == 'init' }, {
				hasAnyInit: true;
				if({ m:params:length() == 0 }, {
					hasZeroInit: true;
				});
			});
			mi++;
		});
		if({ hasZeroInit || !hasAnyInit }, {
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: sname . '_init', argTypes: [IrType:Ptr], args: [obj]));
		});
		self:terminate(inst: IrInst:Ret(hasVal: true, val: obj, ty: IrType:Ptr));
		self:mod:addFunction(fn: fn);
	}

	local Function is buildDefaultInit(ClassInfo is cls, String is sname, String is initFn){
		local IrFunction is fn: IrFunction:init(name: initFn, retType: IrType:Void);
		fn:addParam(name: '%self', ty: IrType:Ptr);
		local IrBlock is entry: fn:addBlock(label: 'entry');
		self:curFn: fn;
		self:switchBlock(blk: entry);
		self:tmpCounter: 0;
		self:localSlots: Map:init();
		self:localTypes: Map:init();
		self:localIsArc: Map:init();
		self:localSpecTypes: Map:init();
		self:boxedLocals: Map:init();
		self:capturedNames: Map:init();
		self:ownedSlots: [];
		self:curPoolMark: '';
		self:emitFieldDefaults(cls: cls, seen: Map:init());
		self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
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
		self:localIsArc: Map:init();
		self:localSpecTypes: Map:init();
		self:boxedLocals: Map:init();
		self:capturedNames: Map:init();
		self:ownedSlots: [];
		self:curFnRetIsArc: self:isArcSpecType(specType: self:methodReturnSpecType(mt: m:memberType));
		self:emitPoolEnter();

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
			if({ hty == IrType:Ptr && iv != 'null' }, {
				self:emit(inst: IrInst:Retain(val: iv));
			});
			self:emit(inst: IrInst:Store(slot: valGlob, val: iv, ty: hty));
		});
		self:terminate(inst: IrInst:Br(target: doneLbl));

		local IrBlock is doneBlk: fn:addBlock(label: doneLbl);
		self:switchBlock(blk: doneBlk);
		local String is res: self:nextTmp();
		self:emit(inst: IrInst:Load(dst: res, slot: valGlob, ty: hty));
		if({ hty == IrType:Ptr }, {
			self:emit(inst: IrInst:Retain(val: res));
		});
		self:emitPoolExit();
		self:curPoolMark: '';
		self:terminate(inst: IrInst:Ret(hasVal: true, val: res, ty: hty));
		self:mod:addFunction(fn: fn);
	}

	local Function of String is findParentMethodImpl(String is clsName, String is methodName, String is suffix){
		if({ !self:clsMap:has(key: clsName) }, { return ''; });
		local ClassInfo is cls: self:clsMap:get(key: clsName, default: ClassInfo:init(name: '', baseClass: '', members: []));
		local String is found: '';
		local Int is bi: 0;
		while({ found == '' && bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: self:resolveBaseClass(cls: cls, bname: bname, clsMap: self:clsMap);
			if({ bcls:qualifiedName() != cls:qualifiedName() }, {
				local Int is mi: 0;
				while({ found == '' && mi < bcls:members:length() }, {
					local Member is m: bcls:members:get(index: mi);
					if({ m:kind == MemberKind:METHOD && m:name == methodName && !m:hasModifier(kw: Keyword:HELD) }, {
						found: self:cStructName(qname: bcls:qualifiedName()) . '_' . methodName . suffix;
					});
					mi++;
				});
				if({ found == '' }, {
					found: self:findParentMethodImpl(clsName: bcls:qualifiedName(), methodName: methodName, suffix: suffix);
				});
			});
			bi++;
		});
		return found;
	}

	local Function of String is findHeldResolver(String is clsName){
		local String is qn: '' . clsName;
		if({ self:clsQNameMap:has(key: clsName) }, {
			qn: self:clsQNameMap:get(key: clsName, default: '');
		});
		local String is sn: self:cStructName(qname: qn);
		if({ self:heldResolvers:has(key: sn) }, {
			return self:heldResolvers:get(key: sn, default: '');
		});
		if({ !self:clsMap:has(key: qn) }, { return ''; });
		local ClassInfo is cls: self:clsMap:get(key: qn, default: ClassInfo:init(name: '', baseClass: '', members: []));
		local String is found: '';
		local Int is bi: 0;
		while({ found == '' && bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: self:resolveBaseClass(cls: cls, bname: bname, clsMap: self:clsMap);
			if({ bcls:qualifiedName() != cls:qualifiedName() }, {
				found: self:findHeldResolver(clsName: bcls:qualifiedName());
			});
			bi++;
		});
		return found;
	}

	local Function is buildHeldResolvers(){
		local Array of String is rKeys: self:heldResolverRetTypes:keys();
		local Int is ri: 0;
		while({ ri < rKeys:length() }, {
			local String is rSym: rKeys:get(index: ri, default: '');
			local String is retSpec: self:heldResolverRetTypes:get(key: rSym, default: '');
			local IrType is resTy: self:irTypeFor(specType: retSpec);
			if({ resTy == IrType:Void }, { resTy: IrType:Ptr; });
			local Boolean is resArc: self:isArcSpecType(specType: retSpec);

			# 1. Missing callback: static void* missing(void* env)
			local IrFunction is missFn: IrFunction:init(name: rSym . '_held_missing_fn', retType: resTy);
			missFn:addParam(name: '%env', ty: IrType:Ptr);
			local IrBlock is mEntry: missFn:addBlock(label: 'entry');
			self:curFn: missFn;
			self:switchBlock(blk: mEntry);
			self:tmpCounter: 0;
			self:lblCounter: 0;
			self:curPoolMark: '';
			local Int is pPreId: self:mod:internStringLiteral(value: "No held member '");
			local String is pPre: self:nextTmp();
			self:emit(inst: IrInst:ConstString(dst: pPre, strId: pPreId));
			local String is pMid: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: pMid, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [pPre, '%env']));
			local Int is pSufId: self:mod:internStringLiteral(value: "' on " . rSym);
			local String is pSuf: self:nextTmp();
			self:emit(inst: IrInst:ConstString(dst: pSuf, strId: pSufId));
			local String is pMsg: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: pMsg, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [pMid, pSuf]));
			local String is pCstr: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: pCstr, hasDst: true, retType: IrType:Ptr, callee: 'spec_buf_to_cstring', argTypes: [IrType:Ptr], args: [pMsg]));
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_panic', argTypes: [IrType:Ptr], args: [pCstr]));
			local String is mDef: self:emitDefaultVal(ty: resTy);
			self:terminate(inst: IrInst:Ret(hasVal: true, val: mDef, ty: resTy));
			self:mod:addFunction(fn: missFn);

			# 2. Cache global + resolver wrapper: rSym_held_resolve(ptr %p_name)
			local String is cacheGlob: '.held_cache.' . rSym;
			self:mod:addGlobal(name: cacheGlob, ty: IrType:Ptr, initVal: 'null');
			local IrFunction is fn: IrFunction:init(name: rSym . '_held_resolve', retType: resTy);
			fn:addParam(name: '%p_name', ty: IrType:Ptr);
			local IrBlock is entry: fn:addBlock(label: 'entry');
			self:curFn: fn;
			self:switchBlock(blk: entry);
			self:tmpCounter: 0;
			self:lblCounter: 0;
			self:localSlots: Map:init();
			self:localTypes: Map:init();
			self:localIsArc: Map:init();
			self:localSpecTypes: Map:init();
			self:boxedLocals: Map:init();
			self:capturedNames: Map:init();
			self:ownedSlots: [];
			self:curFnRetIsArc: resArc;
			self:emitPoolEnter();

			local String is cache0: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: cache0, slot: '@' . cacheGlob, ty: IrType:Ptr));
			local String is needInit: self:nextTmp();
			self:emit(inst: IrInst:Cmp(dst: needInit, op: '==', lhs: cache0, rhs: 'null', ty: IrType:Ptr));
			local String is mkLbl: self:nextLabel(prefix: 'hcache_mk');
			local String is chkLbl: self:nextLabel(prefix: 'hcache_chk');
			self:terminate(inst: IrInst:CondBr(cond: needInit, thenLabel: mkLbl, elseLabel: chkLbl));

			local IrBlock is mkBlk: fn:addBlock(label: mkLbl);
			self:switchBlock(blk: mkBlk);
			local String is kk: self:nextTmp();
			self:emit(inst: IrInst:ConstInt(dst: kk, value: 0));
			local String is vk: self:nextTmp();
			local Int is vkVal: 0;
			if({ resArc }, { vkVal: 1; });
			self:emit(inst: IrInst:ConstInt(dst: vk, value: vkVal));
			local String is newMap: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: newMap, hasDst: true, retType: IrType:Ptr, callee: 'spec_map_new_typed', argTypes: [IrType:I64, IrType:I64], args: [kk, vk]));
			self:emit(inst: IrInst:Store(slot: '@' . cacheGlob, val: newMap, ty: IrType:Ptr));
			self:terminate(inst: IrInst:Br(target: chkLbl));

			local IrBlock is chkBlk: fn:addBlock(label: chkLbl);
			self:switchBlock(blk: chkBlk);
			local String is cache1: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: cache1, slot: '@' . cacheGlob, ty: IrType:Ptr));
			local String is hasKey: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: hasKey, hasDst: true, retType: IrType:I1, callee: 'HashTable_mapHas', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', cache1, '%p_name']));
			local String is hitLbl: self:nextLabel(prefix: 'hcache_hit');
			local String is missLbl: self:nextLabel(prefix: 'hcache_miss');
			self:terminate(inst: IrInst:CondBr(cond: hasKey, thenLabel: hitLbl, elseLabel: missLbl));

			local IrBlock is hitBlk: fn:addBlock(label: hitLbl);
			self:switchBlock(blk: hitBlk);
			local String is hitRaw: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: hitRaw, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapGet', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', cache1, '%p_name', 'null']));
			local String is hitVal: self:castIfNeeded(val: hitRaw, fromTy: IrType:Ptr, toTy: resTy);
			if({ resArc && hitVal != 'null' }, { self:emit(inst: IrInst:Retain(val: hitVal)); });
			self:emitPoolExit();
			self:terminate(inst: IrInst:Ret(hasVal: true, val: hitVal, ty: resTy));

			local IrBlock is missBlk: fn:addBlock(label: missLbl);
			self:switchBlock(blk: missBlk);
			local String is missFnPtr: self:nextTmp();
			self:emit(inst: IrInst:GlobalAddr(dst: missFnPtr, globalName: rSym . '_held_missing_fn'));
			local String is clos: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: clos, hasDst: true, retType: IrType:Ptr, callee: 'spec_rt_closure_new', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [missFnPtr, '%p_name', 'null']));
			self:emitClaimPool(val: clos);
			local String is resolved: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: resolved, hasDst: true, retType: resTy, callee: rSym . '_resolveHeld', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%p_name', clos]));
			local String is setRaw: self:castIfNeeded(val: resolved, fromTy: resTy, toTy: IrType:Ptr);
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'HashTable_mapSetAny', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', cache1, '%p_name', setRaw]));
			if({ resArc && resolved != 'null' }, { self:emit(inst: IrInst:Retain(val: resolved)); });
			self:emitPoolExit();
			self:curPoolMark: '';
			self:terminate(inst: IrInst:Ret(hasVal: true, val: resolved, ty: resTy));
			self:mod:addFunction(fn: fn);
			ri++;
		});
	}

	local Function of String is emitLoadLocal(String is name, IrType is ty){
		local String is slot: self:localSlots:get(key: name, default: '');
		if({ self:boxedLocals:has(key: name) }, {
			local String is boxPtr: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: boxPtr, slot: slot, ty: IrType:Ptr));
			local String is raw: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'spec_rt_box_get', argTypes: [IrType:Ptr], args: [boxPtr]));
			if({ ty == IrType:Ptr }, { return raw; });
			local String is dst: self:nextTmp();
			self:emit(inst: IrInst:IrCast(dst: dst, val: raw, fromType: IrType:Ptr, toType: ty));
			return dst;
		});
		local String is dst: self:nextTmp();
		self:emit(inst: IrInst:Load(dst: dst, slot: slot, ty: ty));
		return dst;
	}

	local Function is emitStoreLocal(String is name, String is val, IrType is ty, Boolean is isArc){
		local String is slot: self:localSlots:get(key: name, default: '');
		if({ self:boxedLocals:has(key: name) }, {
			local String is boxPtr: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: boxPtr, slot: slot, ty: IrType:Ptr));
			local String is vPtr: val;
			if({ ty != IrType:Ptr }, {
				vPtr: self:nextTmp();
				self:emit(inst: IrInst:IrCast(dst: vPtr, val: val, fromType: ty, toType: IrType:Ptr));
			});
			self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_rt_box_set', argTypes: [IrType:Ptr, IrType:Ptr], args: [boxPtr, vPtr]));
			return;
		});
		if({ isArc }, {
			if({ val != '' && val != 'null' }, {
				self:emit(inst: IrInst:Retain(val: val));
			});
			local String is oldVal: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: oldVal, slot: slot, ty: IrType:Ptr));
			self:emit(inst: IrInst:Release(val: oldVal));
		});
		self:emit(inst: IrInst:Store(slot: slot, val: val, ty: ty));
	}

	Function of String is emitNewBox(String is initVal, IrType is ty, Boolean is isArc){
		local String is valI64: initVal;
		if({ ty == IrType:F64 }, {
			local String is pTmp: self:nextTmp();
			self:emit(inst: IrInst:IrCast(dst: pTmp, val: initVal, fromType: IrType:F64, toType: IrType:Ptr));
			valI64: self:nextTmp();
			self:emit(inst: IrInst:IrCast(dst: valI64, val: pTmp, fromType: IrType:Ptr, toType: IrType:I64));
		}, {
			if({ ty != IrType:I64 }, {
				valI64: self:nextTmp();
				self:emit(inst: IrInst:IrCast(dst: valI64, val: initVal, fromType: ty, toType: IrType:I64));
			});
		});
		local String is arcConst: self:nextTmp();
		self:emit(inst: IrInst:ConstBool(dst: arcConst, value: isArc));
		local String is boxPtr: self:nextTmp();
		self:emit(inst: IrInst:IrCall(dst: boxPtr, hasDst: true, retType: IrType:Ptr, callee: 'spec_rt_box_new', argTypes: [IrType:I64, IrType:I1], args: [valI64, arcConst]));
		return boxPtr;
	}

	local Function is collectDeclNamesInStmts(Array of Statement is stmts, Map of String to Boolean is decls){
		local Int is i: 0;
		while({ i < stmts:length() }, {
			local Statement is st: stmts:get(index: i);
			match(on: st, when: [
				Statement:VarDecl: local Function(Array of String is _m, Type is _t, String is varName, Expression is initExpr, Boolean is hasInit){
					decls:set(key: varName, value: true);
					if({ hasInit }, { self:collectDeclNamesInExpr(expr: initExpr, decls: decls); });
				},
				Statement:Assign: local Function(Expression is t, Expression is v){
					self:collectDeclNamesInExpr(expr: t, decls: decls);
					self:collectDeclNamesInExpr(expr: v, decls: decls);
				},
				Statement:Expr: local Function(Expression is e){
					self:collectDeclNamesInExpr(expr: e, decls: decls);
				},
				Statement:Return: local Function(Expression is e, Boolean is hr){
					if({ hr }, { self:collectDeclNamesInExpr(expr: e, decls: decls); });
				}
			], default: {});
			i++;
		});
	}

	local Function is collectDeclNamesInExpr(Expression is expr, Map of String to Boolean is decls){
		match(on: expr, when: [
			Expression:Unary: local Function(String is _op, Expression is operand){
				self:collectDeclNamesInExpr(expr: operand, decls: decls);
			},
			Expression:Binary: local Function(String is _op, Expression is left, Expression is right){
				self:collectDeclNamesInExpr(expr: left, decls: decls);
				self:collectDeclNamesInExpr(expr: right, decls: decls);
			},
			Expression:Cast: local Function(Expression is inner, String is _t, Array of Expression is args){
				self:collectDeclNamesInExpr(expr: inner, decls: decls);
				local Int is ai: 0;
				while({ ai < args:length() }, {
					self:collectDeclNamesInExpr(expr: args:get(index: ai), decls: decls);
					ai++;
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is _f){
				self:collectDeclNamesInExpr(expr: target, decls: decls);
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				self:collectDeclNamesInExpr(expr: target, decls: decls);
				self:collectDeclNamesInExpr(expr: index, decls: decls);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				local Int is ii: 0;
				while({ ii < items:length() }, {
					self:collectDeclNamesInExpr(expr: items:get(index: ii), decls: decls);
					ii++;
				});
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					self:collectDeclNamesInExpr(expr: keys:get(index: mi), decls: decls);
					self:collectDeclNamesInExpr(expr: values:get(index: mi), decls: decls);
					mi++;
				});
			},
			Expression:Call: local Function(CallData is call){
				self:collectDeclNamesInExpr(expr: call:target, decls: decls);
				local Int is ci: 0;
				while({ ci < call:args:length() }, {
					local NamedArg is na: call:args:get(index: ci);
					self:collectDeclNamesInExpr(expr: na:value, decls: decls);
					ci++;
				});
			},
			Expression:AnonFn: local Function(Type is _rt, Array of Parameter is subParams, Array of Statement is subBody){
				local Int is pi: 0;
				while({ pi < subParams:length() }, {
					local Parameter is sp: subParams:get(index: pi);
					decls:set(key: sp:name, value: true);
					pi++;
				});
				self:collectDeclNamesInStmts(stmts: subBody, decls: decls);
			}
		], default: {});
	}

	local Function is collectAllAnonCapturesInStmts(Array of Statement is stmts, Map of String to Boolean is decls, Map of String to Boolean is out){
		local Int is i: 0;
		while({ i < stmts:length() }, {
			local Statement is st: stmts:get(index: i);
			match(on: st, when: [
				Statement:VarDecl: local Function(Array of String is _m, Type is _t, String is _vn, Expression is initExpr, Boolean is hasInit){
					if({ hasInit }, { self:collectAllAnonCapturesInExpr(expr: initExpr, decls: decls, out: out); });
				},
				Statement:Assign: local Function(Expression is t, Expression is v){
					self:collectAllAnonCapturesInExpr(expr: t, decls: decls, out: out);
					self:collectAllAnonCapturesInExpr(expr: v, decls: decls, out: out);
				},
				Statement:Expr: local Function(Expression is e){
					self:collectAllAnonCapturesInExpr(expr: e, decls: decls, out: out);
				},
				Statement:Return: local Function(Expression is e, Boolean is hr){
					if({ hr }, { self:collectAllAnonCapturesInExpr(expr: e, decls: decls, out: out); });
				}
			], default: {});
			i++;
		});
	}

	local Function is collectAllAnonCapturesInExpr(Expression is expr, Map of String to Boolean is decls, Map of String to Boolean is out){
		match(on: expr, when: [
			Expression:Unary: local Function(String is _op, Expression is operand){
				self:collectAllAnonCapturesInExpr(expr: operand, decls: decls, out: out);
			},
			Expression:Binary: local Function(String is _op, Expression is left, Expression is right){
				self:collectAllAnonCapturesInExpr(expr: left, decls: decls, out: out);
				self:collectAllAnonCapturesInExpr(expr: right, decls: decls, out: out);
			},
			Expression:Cast: local Function(Expression is inner, String is _t, Array of Expression is args){
				self:collectAllAnonCapturesInExpr(expr: inner, decls: decls, out: out);
				local Int is ai: 0;
				while({ ai < args:length() }, {
					self:collectAllAnonCapturesInExpr(expr: args:get(index: ai), decls: decls, out: out);
					ai++;
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is _f){
				self:collectAllAnonCapturesInExpr(expr: target, decls: decls, out: out);
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				self:collectAllAnonCapturesInExpr(expr: target, decls: decls, out: out);
				self:collectAllAnonCapturesInExpr(expr: index, decls: decls, out: out);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				local Int is ii: 0;
				while({ ii < items:length() }, {
					self:collectAllAnonCapturesInExpr(expr: items:get(index: ii), decls: decls, out: out);
					ii++;
				});
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					self:collectAllAnonCapturesInExpr(expr: keys:get(index: mi), decls: decls, out: out);
					self:collectAllAnonCapturesInExpr(expr: values:get(index: mi), decls: decls, out: out);
					mi++;
				});
			},
			Expression:Call: local Function(CallData is call){
				self:collectAllAnonCapturesInExpr(expr: call:target, decls: decls, out: out);
				local String is cnm: call:name;
				local Boolean is isInlineCf: cnm == 'if' || cnm == 'branch' || cnm == 'while' || cnm == 'repeat' || cnm == 'until' || cnm == 'loop' || cnm == 'match';
				local Int is ci: 0;
				while({ ci < call:args:length() }, {
					local NamedArg is na: call:args:get(index: ci);
					if({ isInlineCf }, {
						local Boolean is handledInl: false;
						match(on: na:value, when: [
							Expression:AnonFn: local Function(Type is _rt, Array of Parameter is _sp, Array of Statement is subBody){
								handledInl: true;
								self:collectAllAnonCapturesInStmts(stmts: subBody, decls: decls, out: out);
							},
							Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
								if({ cnm == 'match' }, {
									handledInl: true;
									local Int is mi: 0;
									while({ mi < keys:length() }, {
										local Expression is mk: keys:get(index: mi);
										local Expression is mv: values:get(index: mi);
										match(on: mk, when: [
											Expression:AnonFn: local Function(Type is _krt, Array of Parameter is _ksp, Array of Statement is kBody){
												self:collectAllAnonCapturesInStmts(stmts: kBody, decls: decls, out: out);
											}
										], default: {
											self:collectAllAnonCapturesInExpr(expr: mk, decls: decls, out: out);
										});
										match(on: mv, when: [
											Expression:AnonFn: local Function(Type is _vrt, Array of Parameter is _vsp, Array of Statement is vBody){
												self:collectAllAnonCapturesInStmts(stmts: vBody, decls: decls, out: out);
											}
										], default: {
											self:collectAllAnonCapturesInExpr(expr: mv, decls: decls, out: out);
										});
										mi++;
									});
								});
							},
							Expression:ArrayLit: local Function(Array of Expression is items){
								if({ cnm == 'branch' }, {
									handledInl: true;
									local Int is bi: 0;
									while({ bi < items:length() }, {
										local Expression is bItem: items:get(index: bi);
										match(on: bItem, when: [
											Expression:ArrayLit: local Function(Array of Expression is pair){
												local Int is pi: 0;
												while({ pi < pair:length() }, {
													local Expression is pItem: pair:get(index: pi);
													match(on: pItem, when: [
														Expression:AnonFn: local Function(Type is _prt, Array of Parameter is _psp, Array of Statement is pBody){
															self:collectAllAnonCapturesInStmts(stmts: pBody, decls: decls, out: out);
														}
													], default: {
														self:collectAllAnonCapturesInExpr(expr: pItem, decls: decls, out: out);
													});
													pi++;
												});
											}
										], default: {
											self:collectAllAnonCapturesInExpr(expr: bItem, decls: decls, out: out);
										});
										bi++;
									});
								});
							}
						], default: {});
						if({ !handledInl }, {
							self:collectAllAnonCapturesInExpr(expr: na:value, decls: decls, out: out);
						});
					}, {
						self:collectAllAnonCapturesInExpr(expr: na:value, decls: decls, out: out);
					});
					ci++;
				});
			},
			Expression:AnonFn: local Function(Type is _rt, Array of Parameter is subParams, Array of Statement is subBody){
				local Map of String to Boolean is subBound: Map:init();
				local Int is pi: 0;
				while({ pi < subParams:length() }, {
					local Parameter is sp: subParams:get(index: pi);
					subBound:set(key: sp:name, value: true);
					pi++;
				});
				local Map of String to Boolean is seen: Map:init();
				local Array of String is caps: [];
				self:collectFreeInStmts(stmts: subBody, bound: subBound, outerSlots: decls, seen: seen, out: caps);
				local Int is ci: 0;
				while({ ci < caps:length() }, {
					local String is cname: caps:get(index: ci, default: '');
					if({ cname != 'self' }, {
						out:set(key: cname, value: true);
					});
					ci++;
				});
			}
		], default: {});
	}

	local Function of String is structNameForLocal(String is name){
		if({ name == 'self' }, { return self:currentClass; });
		local String is st: self:baseTypeName(t: '' . self:localSpecTypes:get(key: name, default: ''));
		if({ st != '' }, {
			local String is qn: st;
			if({ self:clsQNameMap:has(key: st) }, { qn: '' . self:clsQNameMap:get(key: st, default: ''); });
			local String is cs: self:cStructName(qname: qn);
			if({ self:mod:findStruct(name: cs):name != '' }, { return cs; });
		});
		return self:currentClass;
	}

	local Function of Int is resolvePathField(Array of String is segments){
		self:pathObjPtr: '';
		self:pathStructName: '';
		self:pathFieldIndex: -1;
		if({ segments:length() < 2 }, { return -1; });
		local String is seg0: segments:get(index: 0, default: '');
		local String is obj: '';
		local String is sname: '';
		local Int is segIdx: 1;
		if({ self:localSlots:has(key: seg0) }, {
			local IrType is sty: self:localTypes:get(key: seg0, default: IrType:Ptr);
			obj: self:emitLoadLocal(name: seg0, ty: sty);
			sname: self:structNameForLocal(name: seg0);
		}, {
			local String is selfHk: self:currentClass . ':' . seg0;
			if({ self:heldFields:has(key: selfHk) }, {
				local String is owner0: self:heldFields:get(key: selfHk, default: '');
				local String is hSpec0: self:heldFieldTypes:get(key: owner0 . ':' . seg0, default: '');
				local IrType is hty0: self:irTypeFor(specType: hSpec0);
				if({ hty0 == IrType:Void }, { hty0: IrType:Ptr; });
				obj: self:nextTmp();
				self:emit(inst: IrInst:IrCall(dst: obj, hasDst: true, retType: hty0, callee: owner0 . '_' . seg0 . '__ensure', argTypes: [], args: []));
				if({ hty0 == IrType:Ptr }, { self:emitClaimPool(val: obj); });
				local String is hqn0: '' . hSpec0;
				if({ self:clsQNameMap:has(key: hSpec0) }, {
					hqn0: self:clsQNameMap:get(key: hSpec0, default: '');
				});
				sname: self:cStructName(qname: hqn0);
			}, {
				if({ segments:length() >= 3 }, {
					local String is seg1: segments:get(index: 1, default: '');
					local String is hk: seg0 . ':' . seg1;
					if({ self:heldFields:has(key: hk) }, {
						local String is owner1: self:heldFields:get(key: hk, default: '');
						local String is hSpec1: self:heldFieldTypes:get(key: owner1 . ':' . seg1, default: '');
						local IrType is hty1: self:irTypeFor(specType: hSpec1);
						if({ hty1 == IrType:Void }, { hty1: IrType:Ptr; });
						obj: self:nextTmp();
						self:emit(inst: IrInst:IrCall(dst: obj, hasDst: true, retType: hty1, callee: owner1 . '_' . seg1 . '__ensure', argTypes: [], args: []));
						if({ hty1 == IrType:Ptr }, { self:emitClaimPool(val: obj); });
						local String is hqn1: '' . hSpec1;
						if({ self:clsQNameMap:has(key: hSpec1) }, {
							hqn1: self:clsQNameMap:get(key: hSpec1, default: '');
						});
						sname: self:cStructName(qname: hqn1);
						segIdx: 2;
					});
				});
			});
		});
		if({ obj == '' && self:localSlots:has(key: 'self') }, {
			local IrStruct is selfSt: self:mod:findStruct(name: self:currentClass);
			if({ selfSt:fieldIndex(name: seg0) >= 0 }, {
				obj: self:emitLoadLocal(name: 'self', ty: IrType:Ptr);
				sname: self:currentClass;
				segIdx: 0;
			});
		});
		if({ obj == '' || sname == '' }, { return -1; });
		local Boolean is ok: true;
		while({ ok && segIdx < segments:length() - 1 }, {
			local String is seg: segments:get(index: segIdx, default: '');
			local IrStruct is curSt: self:mod:findStruct(name: sname);
			local Int is fidx: curSt:fieldIndex(name: seg);
			if({ fidx < 0 }, {
				ok: false;
			}, {
				local IrType is fty: curSt:fieldTypes:get(index: fidx);
				local String is ptr: self:nextTmp();
				local String is nextObj: self:nextTmp();
				self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: sname, fieldIndex: fidx));
				self:emit(inst: IrInst:Load(dst: nextObj, slot: ptr, ty: fty));
				obj: nextObj;
				local String is fSpec: self:baseTypeName(t: self:fieldSpecTypes:get(key: sname . ':' . seg, default: ''));
				local String is fqn: '' . fSpec;
				if({ self:clsQNameMap:has(key: fSpec) }, {
					fqn: self:clsQNameMap:get(key: fSpec, default: '');
				});
				sname: self:cStructName(qname: fqn);
				if({ sname == '' || self:mod:findStruct(name: sname):name == '' }, {
					ok: false;
				});
			});
			segIdx++;
		});
		if({ !ok }, { return -1; });
		local String is fname: segments:get(index: segments:length() - 1, default: '');
		local IrStruct is finalSt: self:mod:findStruct(name: sname);
		local Int is finalIdx: finalSt:fieldIndex(name: fname);
		if({ finalIdx < 0 }, { return -1; });
		self:pathObjPtr: obj;
		self:pathStructName: sname;
		self:pathFieldIndex: finalIdx;
		return finalIdx;
	}

	local Function of String is structNameForExpr(Expression is expr){
		local String is rt: self:baseTypeName(t: expr:resolvedType);
		if({ rt != '' }, {
			local String is qn: rt;
			if({ self:clsQNameMap:has(key: rt) }, { qn: '' . self:clsQNameMap:get(key: rt, default: ''); });
			local String is cs: self:cStructName(qname: qn);
			if({ self:mod:findStruct(name: cs):name != '' }, { return cs; });
		});
		return self:currentClass;
	}

	local Function is buildMethod(ClassInfo is cls, Member is m, String is fnName){
		local IrType is retTy: self:methodReturnType(mt: m:memberType);
		local Boolean is isHeldMethod: m:hasModifier(kw: Keyword:HELD);
		local IrFunction is fn: IrFunction:init(name: fnName, retType: retTy);
		fn:sourceFile: cls:sourceFile;
		fn:line: m:line;
		self:currentLine: m:line;
		self:currentMethod: m:name;
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
		self:localIsArc: Map:init();
		self:localSpecTypes: Map:init();
		self:boxedLocals: Map:init();
		self:capturedNames: Map:init();
		self:ownedSlots: [];
		self:resetScopes();

		local Map of String to Boolean is decls: Map:init();
		local Int is dpi: 0;
		while({ dpi < m:params:length() }, {
			local Parameter is dp: m:params:get(index: dpi);
			decls:set(key: dp:name, value: true);
			dpi++;
		});
		self:collectDeclNamesInStmts(stmts: m:body, decls: decls);
		self:collectAllAnonCapturesInStmts(stmts: m:body, decls: decls, out: self:capturedNames);
		self:curFnRetIsArc: self:isArcSpecType(specType: self:methodReturnSpecType(mt: m:memberType));
		self:emitPoolEnter();

		if({ !isHeldMethod }, {
			# Bind 'self' into stack slot
			self:localSlots:set(key: 'self', value: '%self_slot');
			self:localTypes:set(key: 'self', value: IrType:Ptr);
			self:localIsArc:set(key: 'self', value: true);
			self:localSpecTypes:set(key: 'self', value: self:currentClass);
			self:emit(inst: IrInst:Alloca(slot: '%self_slot', ty: IrType:Ptr));
			self:emit(inst: IrInst:Store(slot: '%self_slot', val: '%self', ty: IrType:Ptr));
		});

		pi: 0;
		while({ pi < m:params:length() }, {
			local Parameter is p: m:params:get(index: pi);
			local IrType is pty: self:irTypeFor(specType: p:paramType:name);
			local Boolean is pArc: self:isArcSpecType(specType: p:paramType:name);
			local String is slot: '%slot_' . p:name;
			self:localSlots:set(key: p:name, value: slot);
			self:localTypes:set(key: p:name, value: pty);
			self:localIsArc:set(key: p:name, value: pArc);
			self:localSpecTypes:set(key: p:name, value: p:paramType:name);
			if({ self:capturedNames:has(key: p:name) }, {
				self:boxedLocals:set(key: p:name, value: true);
				self:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
				if({ pArc }, {
					self:emit(inst: IrInst:Retain(val: '%p_' . p:name));
				});
				local String is boxPtr: self:emitNewBox(initVal: '%p_' . p:name, ty: pty, isArc: pArc);
				self:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
				self:ownedSlots:add(item: slot);
			}, {
				self:emit(inst: IrInst:Alloca(slot: slot, ty: pty));
				self:emit(inst: IrInst:Store(slot: slot, val: '%p_' . p:name, ty: pty));
			});
			pi++;
		});

		if({ m:name == 'init' }, {
			self:emitFieldDefaults(cls: cls, seen: Map:init());
		});

		self:lowerStmts(stmts: m:body);

		if({ !self:blkTerminated }, {
			self:emitReleaseOwnedLocals();
			self:emitPoolExit();
			if({ retTy == IrType:Void }, {
				self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
			}, {
				local String is defVal: self:emitDefaultVal(ty: retTy);
				self:terminate(inst: IrInst:Ret(hasVal: true, val: defVal, ty: retTy));
			});
		});
		self:curPoolMark: '';

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

	Function of String is emitDefaultVal(IrType is ty){
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

	Function is lowerStmt(Statement is stmt){
		local Int is prevLine: self:currentLine;
		if({ stmt:line > 0 }, { self:currentLine: stmt:line; });
		match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				local IrType is vty: self:irTypeFor(specType: varType:name);
				local Boolean is vIsArc: self:isArcSpecType(specType: varType:name);
				local String is slot: '%var_' . varName . '_' . (self:nextTmp());
				# Clean '%' from slot suffix so LLVM identifier is valid
				slot: '%var_' . varName . '_' . (self:tmpCounter as String);
				local Boolean is isBoxed: self:capturedNames:has(key: varName);
				self:bindLocal(name: varName, slot: slot, ty: vty, isArc: vIsArc, specType: varType:name, isBoxed: isBoxed);
				local Boolean is declInEntry: self:curBlk:label == 'entry';
				if({ isBoxed }, {
					self:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
				}, {
					self:emit(inst: IrInst:Alloca(slot: slot, ty: vty));
				});
				if({ hasInit }, {
					local String is prevMapK: self:expectedMapKeyType;
					local String is prevMapV: self:expectedMapValType;
					if({ varType:name == 'Map' && varType:params:length() >= 1 }, {
						local Type is mkp0: varType:params:get(index: 0);
						self:expectedMapKeyType: mkp0:name;
						if({ varType:params:length() >= 2 }, {
							local Type is mkp1: varType:params:get(index: 1);
							self:expectedMapValType: mkp1:name;
						});
					});
					local String is val: self:lowerExpr(expr: initExpr);
					self:expectedMapKeyType: prevMapK;
					self:expectedMapValType: prevMapV;
					local IrType is initTy: self:irTypeFor(specType: initExpr:resolvedType);
					val: self:castIfNeeded(val: val, fromTy: initTy, toTy: vty);
					if({ val == '' }, { val: self:emitDefaultVal(ty: vty); });
					local Boolean is isStrLitInit: false;
					match(on: initExpr, when: [
						Expression:StringLit: local Function(String is sv){ isStrLitInit: true; }
					], default: {});
					local Boolean is strCopyOwned: false;
					if({ varType:name == 'String' && isStrLitInit && val != '' && val != 'null' }, {
						local String is strCopy: self:nextTmp();
						self:emit(inst: IrInst:IrCall(dst: strCopy, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_copy', argTypes: [IrType:Ptr], args: [val]));
						if({ isBoxed }, {
							self:emitClaimPool(val: strCopy);
						}, {
							strCopyOwned: true;
						});
						val: strCopy;
					});
					if({ vIsArc && !strCopyOwned && val != '' && val != 'null' }, {
						self:emit(inst: IrInst:Retain(val: val));
					});
					if({ (vIsArc || isBoxed) && !declInEntry }, {
						local String is prevSlotVal: self:nextTmp();
						self:emit(inst: IrInst:Load(dst: prevSlotVal, slot: slot, ty: IrType:Ptr));
						self:emit(inst: IrInst:Release(val: prevSlotVal));
					});
					if({ isBoxed }, {
						local String is boxPtr: self:emitNewBox(initVal: val, ty: vty, isArc: vIsArc);
						self:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
					}, {
						self:emit(inst: IrInst:Store(slot: slot, val: val, ty: vty));
					});
				}, {
					local String is defVal: self:emitDefaultVal(ty: vty);
					local String is listElem: '';
					if({ varType:params:length() > 0 }, {
						local Type is lp0: varType:params:get(index: 0);
						listElem: lp0:name;
					}, {
						if({ varType:name:startsWith(prefix: 'List of ') && varType:name:length() > 8 }, {
							listElem: varType:name:substring(start: 8, end: varType:name:length());
						}, {
							if({ varType:name:startsWith(prefix: 'List:') && varType:name:length() > 5 }, {
								listElem: varType:name:substring(start: 5, end: varType:name:length());
							});
						});
					});
					local Boolean is isByteListVar: varType:name == 'List of Byte' || varType:name == 'List:Byte' || (varType:name == 'List' && listElem == 'Byte');
					if({ isByteListVar }, {
						defVal: self:nextTmp();
						self:emit(inst: IrInst:IrCall(dst: defVal, hasDst: true, retType: IrType:Ptr, callee: 'spec_bytebuffer_new', argTypes: [], args: []));
						self:emitClaimPool(val: defVal);
						self:emit(inst: IrInst:Retain(val: defVal));
					}, {
						if({ varType:name == 'List' || varType:name:startsWith(prefix: 'List of ') || varType:name:startsWith(prefix: 'List:') }, {
							local String is vecCtor: 'spec_array_new_object';
							if({ listElem != '' && !self:isArcSpecType(specType: listElem) }, {
								vecCtor: 'spec_array_new';
							});
							defVal: self:nextTmp();
							self:emit(inst: IrInst:IrCall(dst: defVal, hasDst: true, retType: IrType:Ptr, callee: vecCtor, argTypes: [], args: []));
							self:emitClaimPool(val: defVal);
							self:emit(inst: IrInst:Retain(val: defVal));
						});
					});
					if({ (vIsArc || isBoxed) && !declInEntry }, {
						local String is prevSlotVal2: self:nextTmp();
						self:emit(inst: IrInst:Load(dst: prevSlotVal2, slot: slot, ty: IrType:Ptr));
						self:emit(inst: IrInst:Release(val: prevSlotVal2));
					});
					if({ isBoxed }, {
						local String is boxPtr: self:emitNewBox(initVal: defVal, ty: vty, isArc: vIsArc);
						self:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
					}, {
						self:emit(inst: IrInst:Store(slot: slot, val: defVal, ty: vty));
					});
				});
				if({ vIsArc || isBoxed }, {
					self:ownedSlots:add(item: slot);
				});
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				if({ self:tryLowerAppendChain(assignTarget: assignTarget, assignValue: assignValue) }, {
					self:currentLine: prevLine;
					return;
				});
				local String is prevMapK: self:expectedMapKeyType;
				local String is prevMapV: self:expectedMapValType;
				self:setAssignTargetMapHints(assignTarget: assignTarget);
				local String is val: self:lowerExpr(expr: assignValue);
				self:expectedMapKeyType: prevMapK;
				self:expectedMapValType: prevMapV;
				local IrType is valTy: self:irTypeFor(specType: assignValue:resolvedType);
				match(on: assignTarget, when: [
					Expression:Ident: local Function(String is name){
						if({ self:localSlots:has(key: name) }, {
							local IrType is ty: self:localTypes:get(key: name, default: IrType:I64);
							local Boolean is isArc: self:localIsArc:get(key: name, default: false);
							local String is cval: self:castIfNeeded(val: val, fromTy: valTy, toTy: ty);
							local Boolean is isStrLitAsgn: false;
							match(on: assignValue, when: [
								Expression:StringLit: local Function(String is _sv){ isStrLitAsgn: true; }
							], default: {});
							if({ isStrLitAsgn && !self:boxedLocals:has(key: name) && self:localSpecTypes:get(key: name, default: '') == 'String' && cval != '' && cval != 'null' }, {
								local String is slot: self:localSlots:get(key: name, default: '');
								local String is strCopy: self:nextTmp();
								self:emit(inst: IrInst:IrCall(dst: strCopy, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_copy', argTypes: [IrType:Ptr], args: [cval]));
								local String is oldVal: self:nextTmp();
								self:emit(inst: IrInst:Load(dst: oldVal, slot: slot, ty: IrType:Ptr));
								self:emit(inst: IrInst:Release(val: oldVal));
								self:emit(inst: IrInst:Store(slot: slot, val: strCopy, ty: IrType:Ptr));
							}, {
								self:emitStoreLocal(name: name, val: cval, ty: ty, isArc: isArc);
							});
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
							}, {
								if({ self:localSlots:has(key: 'self') }, {
									local IrStruct is selfSt: self:mod:findStruct(name: self:currentClass);
									local Int is sfidx: selfSt:fieldIndex(name: name);
									if({ sfidx >= 0 }, {
										local String is selfObj: self:emitLoadLocal(name: 'self', ty: IrType:Ptr);
										local IrType is sfty: selfSt:fieldTypes:get(index: sfidx);
										local Boolean is sfIsArc: selfSt:fieldIsArc:get(index: sfidx, default: false);
										local String is scval: self:castIfNeeded(val: val, fromTy: valTy, toTy: sfty);
										local String is sptr: self:nextTmp();
										self:emit(inst: IrInst:FieldPtr(dst: sptr, objPtr: selfObj, structName: self:currentClass, fieldIndex: sfidx));
										if({ sfIsArc }, {
											if({ scval != '' && scval != 'null' }, {
												self:emit(inst: IrInst:Retain(val: scval));
											});
											local String is oldSfVal: self:nextTmp();
											self:emit(inst: IrInst:Load(dst: oldSfVal, slot: sptr, ty: IrType:Ptr));
											self:emit(inst: IrInst:Release(val: oldSfVal));
										});
										self:emit(inst: IrInst:Store(slot: sptr, val: scval, ty: sfty));
									});
								});
							});
						});
					},
					Expression:FieldAccess: local Function(Expression is target, String is fieldName){
						local String is obj: self:lowerExpr(expr: target);
						local String is sname: self:structNameForExpr(expr: target);
						local IrStruct is st: self:mod:findStruct(name: sname);
						local Int is fidx: st:fieldIndex(name: fieldName);
						if({ fidx >= 0 }, {
							local IrType is fty: st:fieldTypes:get(index: fidx);
							local Boolean is fIsArc: st:fieldIsArc:get(index: fidx, default: false);
							local String is cval: self:castIfNeeded(val: val, fromTy: valTy, toTy: fty);
							local String is ptr: self:nextTmp();
							self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: sname, fieldIndex: fidx));
							if({ fIsArc }, {
								if({ cval != '' && cval != 'null' }, {
									self:emit(inst: IrInst:Retain(val: cval));
								});
								local String is oldFVal: self:nextTmp();
								self:emit(inst: IrInst:Load(dst: oldFVal, slot: ptr, ty: IrType:Ptr));
								self:emit(inst: IrInst:Release(val: oldFVal));
							});
							self:emit(inst: IrInst:Store(slot: ptr, val: cval, ty: fty));
						});
					},
					Expression:Path: local Function(Array of String is segments){
						if({ segments:length() >= 2 }, {
							local String is seg0: segments:get(index: 0, default: '');
							local String is seg1: segments:get(index: 1, default: '');
							if({ segments:length() == 2 && !self:localSlots:has(key: seg0) && self:heldFields:has(key: seg0 . ':' . seg1) }, {
								local String is owner: self:heldFields:get(key: seg0 . ':' . seg1, default: '');
								local IrType is hty: self:irTypeFor(specType: self:heldFieldTypes:get(key: owner . ':' . seg1, default: ''));
								if({ hty == IrType:Void }, { hty: IrType:Ptr; });
								local String is trueTmp: self:nextTmp();
								self:emit(inst: IrInst:ConstBool(dst: trueTmp, value: true));
								self:emit(inst: IrInst:Store(slot: '@.held_init.' . owner . '.' . seg1, val: trueTmp, ty: IrType:I1));
								self:emit(inst: IrInst:Store(slot: '@.held_val.' . owner . '.' . seg1, val: val, ty: hty));
							}, {
								local Int is fidx: self:resolvePathField(segments: segments);
								if({ fidx >= 0 }, {
									local String is obj: self:pathObjPtr;
									local String is sname: self:pathStructName;
									local IrStruct is st: self:mod:findStruct(name: sname);
									local IrType is fty: st:fieldTypes:get(index: fidx);
									local Boolean is fIsArc: st:fieldIsArc:get(index: fidx, default: false);
									local String is cval: self:castIfNeeded(val: val, fromTy: valTy, toTy: fty);
									local String is ptr: self:nextTmp();
									self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: sname, fieldIndex: fidx));
									if({ fIsArc }, {
										if({ cval != '' && cval != 'null' }, {
											self:emit(inst: IrInst:Retain(val: cval));
										});
										local String is oldPVal: self:nextTmp();
										self:emit(inst: IrInst:Load(dst: oldPVal, slot: ptr, ty: IrType:Ptr));
										self:emit(inst: IrInst:Release(val: oldPVal));
									});
									self:emit(inst: IrInst:Store(slot: ptr, val: cval, ty: fty));
								});
							});
						});
					},
					Expression:Index: local Function(Expression is target, Expression is index){
						local String is tv: self:lowerExpr(expr: target);
						local String is iv: self:lowerExpr(expr: index);
						local String is tType: target:resolvedType;
						if({ tType == 'Map' || tType:startsWith(prefix: 'Map:') || tType:startsWith(prefix: 'Map of ') }, {
							local String is kSpec: index:resolvedType;
							local String is kSuf: '';
							local IrType is kArgTy: IrType:Ptr;
							if({ kSpec == 'Int' || kSpec == 'Boolean' || tType:startsWith(prefix: 'Map of Int to ') || tType:startsWith(prefix: 'Map:Int:') || tType:startsWith(prefix: 'Map of Boolean to ') || tType:startsWith(prefix: 'Map:Boolean:') }, {
								kSuf: 'Int';
								kArgTy: IrType:I64;
							}, {
								if({ kSpec == 'Float' || tType:startsWith(prefix: 'Map of Float to ') || tType:startsWith(prefix: 'Map:Float:') }, {
									kSuf: 'Flt';
									kArgTy: IrType:F64;
								}, {
									if({ kSpec != 'String' && kSpec != 'Any' && tType != 'Map' && !tType:startsWith(prefix: 'Map of String to ') && !tType:startsWith(prefix: 'Map:String:') && !tType:startsWith(prefix: 'Map of Any to ') }, {
										kSuf: 'Obj';
									});
								});
							});
							local String is kp: self:castIfNeeded(val: iv, fromTy: self:irTypeFor(specType: kSpec), toTy: kArgTy);
							local String is vp: self:castIfNeeded(val: val, fromTy: valTy, toTy: IrType:Ptr);
							local String is setCallee: 'HashTable_mapSet' . kSuf . 'Any';
							if({ assignValue:resolvedType == 'String' }, {
								setCallee: 'HashTable_mapSet' . kSuf;
							});
							self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: setCallee, argTypes: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr], args: ['null', tv, kp, vp]));
						}, {
							local String is idxV: self:castIfNeeded(val: iv, fromTy: self:irTypeFor(specType: index:resolvedType), toTy: IrType:I64);
							local String is vp: self:castIfNeeded(val: val, fromTy: valTy, toTy: IrType:Ptr);
							self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecSetAt', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:Ptr], args: ['null', tv, idxV, vp]));
						});
					}
				], default: {});
			},
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ self:inlineReturnEndLbl != '' }, {
					if({ hasReturnExpr && self:inlineReturnSlot != '' }, {
						local String is ival: self:lowerExpr(expr: returnExpr);
						local IrType is ivalTy: self:irTypeFor(specType: returnExpr:resolvedType);
						ival: self:castIfNeeded(val: ival, fromTy: ivalTy, toTy: self:inlineReturnTy);
						self:emit(inst: IrInst:Store(slot: self:inlineReturnSlot, val: ival, ty: self:inlineReturnTy));
					});
					self:terminate(inst: IrInst:Br(target: self:inlineReturnEndLbl));
					return;
				});
				if({ hasReturnExpr && self:curFn:retType != IrType:Void }, {
					local String is val: self:lowerExpr(expr: returnExpr);
					local IrType is valTy: self:irTypeFor(specType: returnExpr:resolvedType);
					val: self:castIfNeeded(val: val, fromTy: valTy, toTy: self:curFn:retType);
					if({ val == '' }, {
						val: self:emitDefaultVal(ty: self:curFn:retType);
					});
					if({ val == '0' && self:curFn:retType == IrType:Ptr }, {
						val: 'null';
					});
					local Boolean is retExprIsArc: self:isArcSpecType(specType: returnExpr:resolvedType);
					if({ (self:curFnRetIsArc || retExprIsArc) && self:curFn:retType == IrType:Ptr && val != 'null' }, {
						self:emit(inst: IrInst:Retain(val: val));
					});
					self:emitReleaseOwnedLocals();
					self:emitPoolExit();
					if({ self:curFnRetIsArc && self:curFn:retType == IrType:Ptr && val != 'null' }, {
						self:emitClaimPool(val: val);
					});
					self:terminate(inst: IrInst:Ret(hasVal: true, val: val, ty: self:curFn:retType));
				}, {
					if({ hasReturnExpr }, {
						local String is _unusedRet: self:lowerExpr(expr: returnExpr);
					});
					self:emitReleaseOwnedLocals();
					self:emitPoolExit();
					self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
				});
			},
			Statement:Forward: local Function(Array of NamedArg is args){
				local String is parentFn: self:findParentMethodImpl(clsName: self:currentClass, methodName: self:currentMethod, suffix: '');
				if({ parentFn != '' }, {
					local Array of IrType is fArgT: [IrType:Ptr];
					local Array of String is fArgV: [self:emitLoadLocal(name: 'self', ty: IrType:Ptr)];
					self:lowerCallArgs(fnKey: parentFn, callArgs: args, argTypes: fArgT, argVals: fArgV);
					local IrType is fRetTy: self:methodRetTypes:get(key: parentFn, default: IrType:Void);
					local Boolean is fHasDst: fRetTy != IrType:Void;
					local String is fDst: '';
					if({ fHasDst }, { fDst: self:nextTmp(); });
					self:emit(inst: IrInst:IrCall(dst: fDst, hasDst: fHasDst, retType: fRetTy, callee: parentFn, argTypes: fArgT, args: fArgV));
					if({ fHasDst }, {
						if({ self:curFnRetIsArc && fRetTy == IrType:Ptr && fDst != 'null' }, {
							self:emit(inst: IrInst:Retain(val: fDst));
						});
						self:emitReleaseOwnedLocals();
						self:emitPoolExit();
						if({ self:curFnRetIsArc && fRetTy == IrType:Ptr && fDst != 'null' }, {
							self:emitClaimPool(val: fDst);
						});
						self:terminate(inst: IrInst:Ret(hasVal: true, val: fDst, ty: fRetTy));
					}, {
						self:emitReleaseOwnedLocals();
						self:emitPoolExit();
						self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
					});
				});
			},
			Statement:Expr: local Function(Expression is exprStmt){
				local String is _u0: self:lowerExpr(expr: exprStmt);
			}
		], default: {});
		self:currentLine: prevLine;
	}

	local Function is setMapHintsFromTypeStr(String is t){
		local Int is toIdx: t:indexOf(search: ' to ', default: -1);
		if({ t:startsWith(prefix: 'Map of ') && toIdx > 7 }, {
			self:expectedMapKeyType: t:substring(start: 7, end: toIdx);
			self:expectedMapValType: t:substring(start: toIdx + 4, end: t:length());
			return;
		});
		if({ t:startsWith(prefix: 'Map:') }, {
			local String is afterMap: t:substring(start: 4, end: t:length());
			local Int is cIdx: afterMap:indexOf(search: ':', default: -1);
			if({ cIdx > 0 }, {
				self:expectedMapKeyType: afterMap:substring(start: 0, end: cIdx);
				self:expectedMapValType: afterMap:substring(start: cIdx + 1, end: afterMap:length());
			});
		});
	}

	local Function is setAssignTargetMapHints(Expression is assignTarget){
		if({ assignTarget:resolvedType != '' && assignTarget:resolvedType != 'Map' }, {
			self:setMapHintsFromTypeStr(t: assignTarget:resolvedType);
			if({ self:expectedMapKeyType != '' }, { return; });
		});
		match(on: assignTarget, when: [
			Expression:Ident: local Function(String is name){
				if({ self:localSpecTypes:has(key: name) }, {
					self:setMapHintsFromTypeStr(t: self:localSpecTypes:get(key: name, default: ''));
				}, {
					if({ self:fieldSpecTypes:has(key: self:currentClass . ':' . name) }, {
						self:setMapHintsFromTypeStr(t: self:fieldSpecTypes:get(key: self:currentClass . ':' . name, default: ''));
					});
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				local String is sname: self:structNameForExpr(expr: target);
				if({ self:fieldSpecTypes:has(key: sname . ':' . fieldName) }, {
					self:setMapHintsFromTypeStr(t: self:fieldSpecTypes:get(key: sname . ':' . fieldName, default: ''));
				});
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() == 2 && segs:get(index: 0, default: '') == 'self' }, {
					local String is fn: segs:get(index: 1, default: '');
					if({ self:fieldSpecTypes:has(key: self:currentClass . ':' . fn) }, {
						self:setMapHintsFromTypeStr(t: self:fieldSpecTypes:get(key: self:currentClass . ':' . fn, default: ''));
					});
				});
			}
		], default: {});
	}

	local Function of Boolean is collectAppendChainRhs(Expression is expr, String is targetName, Array of Expression is rhsOut){
		return match(on: expr, when: [
			Expression:Binary: local Function of Boolean(String is op, Expression is left, Expression is right){
				if({ op != '.' }, { return false; });
				local Boolean is leftIsTarget: match(on: left, when: [
					Expression:Ident: local Function of Boolean(String is nm){ return nm == targetName; },
					else: { false }
				]);
				if({ leftIsTarget }, {
					rhsOut:add(item: right);
					return true;
				});
				if({ self:collectAppendChainRhs(expr: left, targetName: targetName, rhsOut: rhsOut) }, {
					rhsOut:add(item: right);
					return true;
				});
				return false;
			},
			else: { false }
		]);
	}

	local Function of String is lowerConcatRight(Expression is right){
		local String is r: self:lowerExpr(expr: right);
		local IrType is rTy: self:irTypeFor(specType: right:resolvedType);
		if({ rTy == IrType:I64 }, {
			local String is rsI: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: rsI, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToString', argTypes: [IrType:Ptr, IrType:I64], args: ['null', r]));
			return rsI;
		});
		if({ rTy == IrType:F64 }, {
			local String is rsF: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: rsF, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_float', argTypes: [IrType:F64], args: [r]));
			self:emitClaimPool(val: rsF);
			return rsF;
		});
		if({ rTy == IrType:I1 }, {
			local String is rsB: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: rsB, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_bool', argTypes: [IrType:I1], args: [r]));
			self:emitClaimPool(val: rsB);
			return rsB;
		});
		if({ rTy == IrType:Ptr && right:resolvedType != 'String' && (self:clsMap:has(key: right:resolvedType) || right:resolvedType == 'Any') }, {
			return self:emitObjectToString(objVal: r, specType: right:resolvedType);
		});
		return r;
	}

	local Function of String is lowerConcatChainNoClaim(Expression is expr){
		return match(on: expr, when: [
			Expression:Binary: local Function of String(String is op, Expression is left, Expression is right){
				if({ op == '.' }, {
					local Boolean is leftIsDot: match(on: left, when: [
						Expression:Binary: local Function of Boolean(String is lop, Expression is _ll, Expression is _lr){ return lop == '.'; },
						else: { false }
					]);
					local String is ls: '';
					if({ leftIsDot }, {
						ls: self:lowerConcatChainNoClaim(expr: left);
					}, {
						local String is l: self:lowerExpr(expr: left);
						local IrType is lTy: self:irTypeFor(specType: left:resolvedType);
						if({ lTy == IrType:I64 }, {
							ls: self:nextTmp();
							self:emit(inst: IrInst:IrCall(dst: ls, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToString', argTypes: [IrType:Ptr, IrType:I64], args: ['null', l]));
							self:emit(inst: IrInst:Retain(val: ls));
						}, {
							if({ lTy == IrType:F64 }, {
								ls: self:nextTmp();
								self:emit(inst: IrInst:IrCall(dst: ls, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_float', argTypes: [IrType:F64], args: [l]));
							}, {
								if({ lTy == IrType:I1 }, {
									ls: self:nextTmp();
									self:emit(inst: IrInst:IrCall(dst: ls, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_bool', argTypes: [IrType:I1], args: [l]));
								}, {
									ls: l;
									self:emit(inst: IrInst:Retain(val: ls));
								});
							});
						});
					});
					local String is rs: self:lowerConcatRight(right: right);
					local String is dst: self:nextTmp();
					self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [ls, rs]));
					return dst;
				});
				return self:lowerExpr(expr: expr);
			},
			else: { self:lowerExpr(expr: expr) }
		]);
	}

	local Function of Boolean is tryLowerAppendChain(Expression is assignTarget, Expression is assignValue){
		local String is targetName: match(on: assignTarget, when: [
			Expression:Ident: local Function of String(String is nm){ return nm; },
			else: { '' }
		]);
		if({ targetName == '' || !self:localSlots:has(key: targetName) || self:boxedLocals:has(key: targetName) }, {
			return false;
		});
		if({ self:localSpecTypes:get(key: targetName, default: '') != 'String' }, {
			return false;
		});
		local Array of Expression is rhsList: [];
		if({ !self:collectAppendChainRhs(expr: assignValue, targetName: targetName, rhsOut: rhsList) || rhsList:length() == 0 }, {
			return false;
		});
		local String is slot: self:localSlots:get(key: targetName, default: '');
		local String is curVal: self:nextTmp();
		self:emit(inst: IrInst:Load(dst: curVal, slot: slot, ty: IrType:Ptr));
		local Int is ri: 0;
		while({ ri < rhsList:length() }, {
			local String is rs: self:lowerConcatRight(right: rhsList:get(index: ri));
			local String is nextVal: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: nextVal, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [curVal, rs]));
			curVal: nextVal;
			ri++;
		});
		self:emit(inst: IrInst:Store(slot: slot, val: curVal, ty: IrType:Ptr));
		return true;
	}

	local Function of String is lowerIncDec(String is op, Expression is operand, IrType is ty){
		local String is boxedName: '';
		local String is slot: '';
		local IrType is slotTy: ty;
		match(on: operand, when: [
			Expression:Ident: local Function(String is name){
				if({ self:localSlots:has(key: name) }, {
					slot: self:localSlots:get(key: name, default: '');
					slotTy: self:localTypes:get(key: name, default: ty);
					if({ self:boxedLocals:has(key: name) }, {
						boxedName: name;
					});
				}, {
					if({ self:localSlots:has(key: 'self') }, {
						local IrStruct is selfSt: self:mod:findStruct(name: self:currentClass);
						local Int is sfidx: selfSt:fieldIndex(name: name);
						if({ sfidx >= 0 }, {
							local String is selfObj: self:emitLoadLocal(name: 'self', ty: IrType:Ptr);
							slotTy: selfSt:fieldTypes:get(index: sfidx);
							slot: self:nextTmp();
							self:emit(inst: IrInst:FieldPtr(dst: slot, objPtr: selfObj, structName: self:currentClass, fieldIndex: sfidx));
						});
					});
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				local String is obj: self:lowerExpr(expr: target);
				local String is sname: self:structNameForExpr(expr: target);
				local IrStruct is st: self:mod:findStruct(name: sname);
				local Int is fidx: st:fieldIndex(name: fieldName);
				if({ fidx >= 0 }, {
					slotTy: st:fieldTypes:get(index: fidx);
					slot: self:nextTmp();
					self:emit(inst: IrInst:FieldPtr(dst: slot, objPtr: obj, structName: sname, fieldIndex: fidx));
				});
			},
			Expression:Path: local Function(Array of String is segments){
				local Int is fidx: self:resolvePathField(segments: segments);
				if({ fidx >= 0 }, {
					local String is obj: self:pathObjPtr;
					local String is sname: self:pathStructName;
					local IrStruct is st: self:mod:findStruct(name: sname);
					slotTy: st:fieldTypes:get(index: fidx);
					slot: self:nextTmp();
					self:emit(inst: IrInst:FieldPtr(dst: slot, objPtr: obj, structName: sname, fieldIndex: fidx));
				});
			}
		], default: {});
		if({ slot == '' && boxedName == '' }, {
			return self:emitDefaultVal(ty: ty);
		});
		local String is oldVal: '';
		if({ boxedName != '' }, {
			oldVal: self:emitLoadLocal(name: boxedName, ty: slotTy);
		}, {
			oldVal: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: oldVal, slot: slot, ty: slotTy));
		});
		local String is one: self:nextTmp();
		if({ slotTy == IrType:F64 }, {
			self:emit(inst: IrInst:ConstFloat(dst: one, text: '1.0'));
		}, {
			self:emit(inst: IrInst:ConstInt(dst: one, value: 1));
		});
		local String is binOp: if({ op == 'post++' || op == '++' }, { '+' }, { '-' });
		local String is newVal: self:nextTmp();
		self:emit(inst: IrInst:BinOp(dst: newVal, op: binOp, lhs: oldVal, rhs: one, ty: slotTy));
		if({ boxedName != '' }, {
			self:emitStoreLocal(name: boxedName, val: newVal, ty: slotTy, isArc: false);
		}, {
			self:emit(inst: IrInst:Store(slot: slot, val: newVal, ty: slotTy));
		});
		if({ op == 'post++' || op == 'post--' }, {
			return oldVal;
		});
		return newVal;
	}

	local Function of String is emitObjectToString(String is objVal, String is specType){
		if({ specType != '' && specType != 'Any' }, {
			local String is sname: self:cStructName(qname: specType);
			local IrStruct is st: self:mod:findStruct(name: sname);
			local Int is tsSlot: st:vtableSlot(mname: 'toString');
			if({ tsSlot >= 0 }, {
				local String is vtPtrAddr: self:nextTmp();
				self:emit(inst: IrInst:FieldPtr(dst: vtPtrAddr, objPtr: objVal, structName: sname, fieldIndex: 1));
				local String is vtBase: self:nextTmp();
				self:emit(inst: IrInst:Load(dst: vtBase, slot: vtPtrAddr, ty: IrType:Ptr));
				local String is slotPtr: self:nextTmp();
				self:emit(inst: IrInst:PtrElem(dst: slotPtr, basePtr: vtBase, index: tsSlot));
				local String is fnPtr: self:nextTmp();
				self:emit(inst: IrInst:Load(dst: fnPtr, slot: slotPtr, ty: IrType:Ptr));
				local String is hasTs: self:nextTmp();
				self:emit(inst: IrInst:Cmp(dst: hasTs, op: '!=', lhs: fnPtr, rhs: 'null', ty: IrType:Ptr));
				local String is tsResSlot: self:nextTmp();
				self:emit(inst: IrInst:Alloca(slot: tsResSlot, ty: IrType:Ptr));
				local String is tsCallLbl: self:nextLabel(prefix: 'ts_call');
				local String is tsFallbackLbl: self:nextLabel(prefix: 'ts_fb');
				local String is tsEndLbl: self:nextLabel(prefix: 'ts_end');
				self:terminate(inst: IrInst:CondBr(cond: hasTs, thenLabel: tsCallLbl, elseLabel: tsFallbackLbl));
				local IrBlock is tsCallBlk: self:curFn:addBlock(label: tsCallLbl);
				self:switchBlock(blk: tsCallBlk);
				local String is tsDst: self:nextTmp();
				self:emit(inst: IrInst:IndirectCall(dst: tsDst, hasDst: true, retType: IrType:Ptr, fnPtr: fnPtr, argTypes: [IrType:Ptr], args: [objVal]));
				self:emitClaimPool(val: tsDst);
				self:emit(inst: IrInst:Store(slot: tsResSlot, val: tsDst, ty: IrType:Ptr));
				self:terminate(inst: IrInst:Br(target: tsEndLbl));
				local IrBlock is tsFbBlk: self:curFn:addBlock(label: tsFallbackLbl);
				self:switchBlock(blk: tsFbBlk);
				local String is fbTn: self:nextTmp();
				self:emit(inst: IrInst:IrCall(dst: fbTn, hasDst: true, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: [IrType:Ptr], args: [objVal]));
				self:emit(inst: IrInst:Store(slot: tsResSlot, val: fbTn, ty: IrType:Ptr));
				self:terminate(inst: IrInst:Br(target: tsEndLbl));
				local IrBlock is tsEndBlk: self:curFn:addBlock(label: tsEndLbl);
				self:switchBlock(blk: tsEndBlk);
				local String is tsFinal: self:nextTmp();
				self:emit(inst: IrInst:Load(dst: tsFinal, slot: tsResSlot, ty: IrType:Ptr));
				return tsFinal;
			});
		});
		local String is tnDst: self:nextTmp();
		self:emit(inst: IrInst:IrCall(dst: tnDst, hasDst: true, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: [IrType:Ptr], args: [objVal]));
		if({ specType == 'Any' }, {
			local String is strLit: self:nextTmp();
			self:emit(inst: IrInst:ConstString(dst: strLit, strId: self:mod:internStringLiteral(value: 'String')));
			local String is isStr: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: isStr, hasDst: true, retType: IrType:I1, callee: 'Buf_stringEquals', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', tnDst, strLit]));
			local String is outSlot: '%any_ts_' . (self:nextTmp());
			outSlot: '%any_ts_' . (self:tmpCounter as String);
			self:emit(inst: IrInst:Alloca(slot: outSlot, ty: IrType:Ptr));
			local String is sLbl: self:nextLabel(prefix: 'any_ts_s');
			local String is oLbl: self:nextLabel(prefix: 'any_ts_o');
			local String is eLbl: self:nextLabel(prefix: 'any_ts_e');
			self:terminate(inst: IrInst:CondBr(cond: isStr, thenLabel: sLbl, elseLabel: oLbl));
			local IrBlock is sBlk: self:curFn:addBlock(label: sLbl);
			self:switchBlock(blk: sBlk);
			self:emit(inst: IrInst:Store(slot: outSlot, val: objVal, ty: IrType:Ptr));
			self:terminate(inst: IrInst:Br(target: eLbl));
			local IrBlock is oBlk: self:curFn:addBlock(label: oLbl);
			self:switchBlock(blk: oBlk);
			self:emit(inst: IrInst:Store(slot: outSlot, val: tnDst, ty: IrType:Ptr));
			self:terminate(inst: IrInst:Br(target: eLbl));
			local IrBlock is eBlk: self:curFn:addBlock(label: eLbl);
			self:switchBlock(blk: eBlk);
			local String is finalAny: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: finalAny, slot: outSlot, ty: IrType:Ptr));
			return finalAny;
		});
		return tnDst;
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
					local IrType is ty: self:localTypes:get(key: name, default: IrType:I64);
					return self:emitLoadLocal(name: name, ty: ty);
				});
				local String is hk: self:currentClass . ':' . name;
				if({ self:heldFields:has(key: hk) }, {
					local String is owner: self:heldFields:get(key: hk, default: '');
					local IrType is hty: self:irTypeFor(specType: self:heldFieldTypes:get(key: owner . ':' . name, default: ''));
					if({ hty == IrType:Void }, { hty: IrType:Ptr; });
					local String is dst: self:nextTmp();
					self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: hty, callee: owner . '_' . name . '__ensure', argTypes: [], args: []));
					if({ hty == IrType:Ptr }, { self:emitClaimPool(val: dst); });
					return dst;
				});
				if({ self:localSlots:has(key: 'self') }, {
					local IrStruct is selfSt: self:mod:findStruct(name: self:currentClass);
					local Int is sfidx: selfSt:fieldIndex(name: name);
					if({ sfidx >= 0 }, {
						local String is selfObj: self:emitLoadLocal(name: 'self', ty: IrType:Ptr);
						local IrType is sfty: selfSt:fieldTypes:get(index: sfidx);
						local String is sptr: self:nextTmp();
						local String is sdst: self:nextTmp();
						self:emit(inst: IrInst:FieldPtr(dst: sptr, objPtr: selfObj, structName: self:currentClass, fieldIndex: sfidx));
						self:emit(inst: IrInst:Load(dst: sdst, slot: sptr, ty: sfty));
						return sdst;
					});
				});
				return '0';
			},
			Expression:Unary: local Function(String is op, Expression is operand){
				local IrType is ty: self:irTypeFor(specType: expr:resolvedType);
				if({ ty == IrType:Void }, { ty: IrType:I64; });
				if({ op == 'post++' || op == 'post--' || op == '++' || op == '--' }, {
					return self:lowerIncDec(op: op, operand: operand, ty: ty);
				});
				local String is v: self:lowerExpr(expr: operand);
				local String is dst: self:nextTmp();
				self:emit(inst: IrInst:UnaryOp(dst: dst, op: op, operand: v, ty: ty));
				return dst;
			},
			Expression:Binary: local Function(String is op, Expression is left, Expression is right){
				if({ op == '&&' || op == '||' }, {
					local String is resSlot: self:nextTmp();
					self:emit(inst: IrInst:Alloca(slot: resSlot, ty: IrType:I1));
					local String is lVal: self:lowerExpr(expr: left);
					local IrType is lTy: self:irTypeFor(specType: left:resolvedType);
					if({ lTy != IrType:I1 && lTy != IrType:Void }, {
						lVal: self:castIfNeeded(val: lVal, fromTy: lTy, toTy: IrType:I1);
					});
					self:emit(inst: IrInst:Store(slot: resSlot, val: lVal, ty: IrType:I1));
					local String is rhsLbl: self:nextLabel(prefix: 'sc_rhs');
					local String is endLbl: self:nextLabel(prefix: 'sc_end');
					if({ op == '&&' }, {
						self:terminate(inst: IrInst:CondBr(cond: lVal, thenLabel: rhsLbl, elseLabel: endLbl));
					}, {
						self:terminate(inst: IrInst:CondBr(cond: lVal, thenLabel: endLbl, elseLabel: rhsLbl));
					});
					local IrBlock is rhsBlk: self:curFn:addBlock(label: rhsLbl);
					self:switchBlock(blk: rhsBlk);
					local String is rVal: self:lowerExpr(expr: right);
					local IrType is rTy: self:irTypeFor(specType: right:resolvedType);
					if({ rTy != IrType:I1 && rTy != IrType:Void }, {
						rVal: self:castIfNeeded(val: rVal, fromTy: rTy, toTy: IrType:I1);
					});
					self:emit(inst: IrInst:Store(slot: resSlot, val: rVal, ty: IrType:I1));
					self:terminate(inst: IrInst:Br(target: endLbl));
					local IrBlock is endBlk: self:curFn:addBlock(label: endLbl);
					self:switchBlock(blk: endBlk);
					local String is scDst: self:nextTmp();
					self:emit(inst: IrInst:Load(dst: scDst, slot: resSlot, ty: IrType:I1));
					return scDst;
				});
				if({ op == '.' }, {
					local String is catDst: self:lowerConcatChainNoClaim(expr: expr);
					self:emitClaimPool(val: catDst);
					return catDst;
				});
				local String is l: self:lowerExpr(expr: left);
				local String is r: self:lowerExpr(expr: right);
				local String is dst: self:nextTmp();
				if({ op == '==' || op == '!=' || op == '<' || op == '<=' || op == '>' || op == '>=' }, {
					local IrType is cmpTy: self:irTypeFor(specType: left:resolvedType);
					if({ cmpTy == IrType:Void }, { cmpTy: IrType:I64; });
					local Boolean is isStrCmp: cmpTy == IrType:Ptr && (left:resolvedType == 'String' || right:resolvedType == 'String');
					if({ isStrCmp && (op == '==' || op == '!=') }, {
						local Array of IrType is sT: [IrType:Ptr, IrType:Ptr, IrType:Ptr];
						local Array of String is sV: ['null', l, r];
						if({ op == '==' }, {
							self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I1, callee: 'Buf_stringEquals', argTypes: sT, args: sV));
							return dst;
						}, {
							local String is eqTmp: self:nextTmp();
							self:emit(inst: IrInst:IrCall(dst: eqTmp, hasDst: true, retType: IrType:I1, callee: 'Buf_stringEquals', argTypes: sT, args: sV));
							self:emit(inst: IrInst:UnaryOp(dst: dst, op: '!', operand: eqTmp, ty: IrType:I1));
							return dst;
						});
					});
					if({ isStrCmp && (op == '<' || op == '<=' || op == '>' || op == '>=') }, {
						local String is cmpRes: self:nextTmp();
						self:emit(inst: IrInst:IrCall(dst: cmpRes, hasDst: true, retType: IrType:I64, callee: 'spec_string_compare', argTypes: [IrType:Ptr, IrType:Ptr], args: [l, r]));
						local String is zeroV: self:nextTmp();
						self:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
						self:emit(inst: IrInst:Cmp(dst: dst, op: op, lhs: cmpRes, rhs: zeroV, ty: IrType:I64));
						return dst;
					});
					if({ cmpTy == IrType:Ptr }, {
						if({ l == '0' }, { l: 'null'; });
						if({ r == '0' }, { r: 'null'; });
					});
					self:emit(inst: IrInst:Cmp(dst: dst, op: op, lhs: l, rhs: r, ty: cmpTy));
					return dst;
				});
				local IrType is ty: self:irTypeFor(specType: expr:resolvedType);
				if({ ty == IrType:Void }, { ty: IrType:I64; });
				self:emit(inst: IrInst:BinOp(dst: dst, op: op, lhs: l, rhs: r, ty: ty));
				return dst;
			},
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				local String is obj: self:lowerExpr(expr: target);
				local String is sname: self:structNameForExpr(expr: target);
				local IrStruct is st: self:mod:findStruct(name: sname);
				local Int is fidx: st:fieldIndex(name: fieldName);
				if({ fidx >= 0 }, {
					local IrType is fty: st:fieldTypes:get(index: fidx);
					local String is ptr: self:nextTmp();
					local String is dst: self:nextTmp();
					self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: sname, fieldIndex: fidx));
					self:emit(inst: IrInst:Load(dst: dst, slot: ptr, ty: fty));
					return dst;
				});
				return '0';
			},
			Expression:Path: local Function(Array of String is segments){
				if({ segments:length() >= 2 }, {
					local String is seg0: segments:get(index: 0, default: '');
					local String is seg1: segments:get(index: 1, default: '');
					local String is hk: seg0 . ':' . seg1;
					if({ segments:length() == 2 && !self:localSlots:has(key: seg0) && self:heldFields:has(key: hk) }, {
						local String is owner: self:heldFields:get(key: hk, default: '');
						local IrType is hty: self:irTypeFor(specType: self:heldFieldTypes:get(key: owner . ':' . seg1, default: ''));
						if({ hty == IrType:Void }, { hty: IrType:Ptr; });
						local String is dst: self:nextTmp();
						self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: hty, callee: owner . '_' . seg1 . '__ensure', argTypes: [], args: []));
						if({ hty == IrType:Ptr }, { self:emitClaimPool(val: dst); });
						return dst;
					});
					local String is varStruct: seg0 . '_' . seg1;
					if({ segments:length() == 2 && !self:localSlots:has(key: seg0) && self:mod:findStruct(name: varStruct):name != '' }, {
						local String is vdst: self:nextTmp();
						self:emit(inst: IrInst:AllocObj(dst: vdst, structName: varStruct, destroyFn: self:destroyFnFor(structName: varStruct)));
						self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: varStruct . '_init', argTypes: [IrType:Ptr], args: [vdst]));
						self:emitClaimPool(val: vdst);
						return vdst;
					});
					if({ segments:length() == 2 && !self:localSlots:has(key: seg0) }, {
						local String is rSym: self:findHeldResolver(clsName: seg0);
						if({ rSym != '' }, {
							local Int is rSid: self:mod:internStringLiteral(value: seg1);
							local String is rNameStr: self:nextTmp();
							self:emit(inst: IrInst:ConstString(dst: rNameStr, strId: rSid));
							local String is rSpec: self:heldResolverRetTypes:get(key: rSym, default: '');
							local IrType is rTy: self:irTypeFor(specType: rSpec);
							if({ rTy == IrType:Void }, { rTy: IrType:Ptr; });
							local String is rDst: self:nextTmp();
							self:emit(inst: IrInst:IrCall(dst: rDst, hasDst: true, retType: rTy, callee: rSym . '_held_resolve', argTypes: [IrType:Ptr], args: [rNameStr]));
							if({ rTy == IrType:Ptr }, { self:emitClaimPool(val: rDst); });
							return rDst;
						});
					});
					local Int is fidx: self:resolvePathField(segments: segments);
					if({ fidx >= 0 }, {
						local String is obj: self:pathObjPtr;
						local String is sname: self:pathStructName;
						local IrStruct is st: self:mod:findStruct(name: sname);
						local IrType is fty: st:fieldTypes:get(index: fidx);
						local String is ptr: self:nextTmp();
						local String is dst: self:nextTmp();
						self:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: sname, fieldIndex: fidx));
						self:emit(inst: IrInst:Load(dst: dst, slot: ptr, ty: fty));
						return dst;
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
				if({ target == 'Hex' || target == 'Bin' || target == 'Oct' }, {
					local Int is base: 16;
					if({ target == 'Bin' }, { base: 2; });
					if({ target == 'Oct' }, { base: 8; });
					local String is baseVal: self:nextTmp();
					self:emit(inst: IrInst:ConstInt(dst: baseVal, value: base));
					if({ fromTy == IrType:Ptr }, {
						local String is defVal: self:nextTmp();
						self:emit(inst: IrInst:ConstInt(dst: defVal, value: 0));
						local String is dstP: self:nextTmp();
						self:emit(inst: IrInst:IrCall(dst: dstP, hasDst: true, retType: IrType:I64, callee: 'String_parseInt', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [v, baseVal, defVal]));
						return dstP;
					});
					local String is digitsVal: '';
					if({ args:length() > 0 }, {
						digitsVal: self:lowerExpr(expr: args:get(index: 0));
					}, {
						digitsVal: self:nextTmp();
						self:emit(inst: IrInst:ConstInt(dst: digitsVal, value: 0));
					});
					local String is dstB: self:nextTmp();
					self:emit(inst: IrInst:IrCall(dst: dstB, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToBase', argTypes: [IrType:Ptr, IrType:I64, IrType:I64, IrType:I64], args: ['null', v, baseVal, digitsVal]));
					return dstB;
				});
				local IrType is toTy: self:irTypeFor(specType: target);
				if({ target == 'Byte' && inner:resolvedType != 'Byte' }, {
					local String is bv: self:castIfNeeded(val: v, fromTy: fromTy, toTy: IrType:I64);
					local String is dstByte: self:nextTmp();
					self:emit(inst: IrInst:IrCall(dst: dstByte, hasDst: true, retType: IrType:I64, callee: '__spec_check_byte', argTypes: [IrType:I64], args: [bv]));
					return dstByte;
				});
				if({ inner:resolvedType == 'String' && target == 'Int' }, {
					local String is base10: self:nextTmp();
					self:emit(inst: IrInst:ConstInt(dst: base10, value: 10));
					local String is def0: self:nextTmp();
					self:emit(inst: IrInst:ConstInt(dst: def0, value: 0));
					local String is dstI: self:nextTmp();
					self:emit(inst: IrInst:IrCall(dst: dstI, hasDst: true, retType: IrType:I64, callee: 'String_parseInt', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [v, base10, def0]));
					return dstI;
				});
				if({ target == 'String' && fromTy != IrType:Ptr }, {
					local String is dstS: self:nextTmp();
					if({ fromTy == IrType:F64 }, {
						self:emit(inst: IrInst:IrCall(dst: dstS, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_float', argTypes: [IrType:F64], args: [v]));
						return dstS;
					});
					if({ fromTy == IrType:I1 }, {
						self:emit(inst: IrInst:IrCall(dst: dstS, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_bool', argTypes: [IrType:I1], args: [v]));
						return dstS;
					});
					self:emit(inst: IrInst:IrCall(dst: dstS, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToString', argTypes: [IrType:Ptr, IrType:I64], args: ['null', v]));
					return dstS;
				});
				if({ fromTy == toTy }, {
					if({ fromTy == IrType:Ptr && target == 'String' && inner:resolvedType != 'String' && (self:clsMap:has(key: inner:resolvedType) || inner:resolvedType == 'Any') }, {
						return self:emitObjectToString(objVal: v, specType: inner:resolvedType);
					});
					if({ fromTy == IrType:Ptr && target != 'Any' && target != '' && target != 'String' && target != 'Array' && target != 'Map' && !target:startsWith(prefix: 'Array of ') && !target:startsWith(prefix: 'Map of ') && self:clsQNameMap:has(key: target) }, {
						local String is tQName: self:clsQNameMap:get(key: target, default: '');
						local Int is tStrId: self:mod:internStringLiteral(value: tQName);
						local String is tPtr: self:nextTmp();
						self:emit(inst: IrInst:GlobalAddr(dst: tPtr, globalName: '.str.' . (tStrId as String)));
						local String is ccDst: self:nextTmp();
						self:emit(inst: IrInst:IrCall(dst: ccDst, hasDst: true, retType: IrType:Ptr, callee: 'spec_cast_check', argTypes: [IrType:Ptr, IrType:Ptr], args: [v, tPtr]));
						return ccDst;
					});
					return v;
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
					local Array of IrType is addT: [IrType:Ptr, IrType:Ptr, IrType:Ptr];
					local Array of String is addV: ['null', arr, ip];
					self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecAdd', argTypes: addT, args: addV));
					ii++;
				});
				self:emitClaimPool(val: arr);
				return arr;
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				local String is mp: self:nextTmp();
				local Int is mapKk: 0;
				if({ keys:length() > 0 }, {
					local Expression is k0: keys:get(index: 0);
					if({ k0:resolvedType == 'Int' || k0:resolvedType == 'Boolean' }, { mapKk: 1; });
					if({ k0:resolvedType == 'Float' }, { mapKk: 2; });
					if({ mapKk == 0 && k0:resolvedType != 'String' && k0:resolvedType != 'Any' }, { mapKk: 3; });
				});
				if({ mapKk != 0 }, {
					local String is mkkV: self:nextTmp();
					self:emit(inst: IrInst:ConstInt(dst: mkkV, value: mapKk));
					local String is mvkV: self:nextTmp();
					self:emit(inst: IrInst:ConstInt(dst: mvkV, value: 0));
					self:emit(inst: IrInst:IrCall(dst: mp, hasDst: true, retType: IrType:Ptr, callee: 'spec_map_new_typed', argTypes: [IrType:I64, IrType:I64], args: [mkkV, mvkV]));
				}, {
					local Array of IrType is emptyT: [];
					local Array of String is emptyV: [];
					self:emit(inst: IrInst:IrCall(dst: mp, hasDst: true, retType: IrType:Ptr, callee: 'spec_map_new', argTypes: emptyT, args: emptyV));
				});
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					local Expression is ke: keys:get(index: mi);
					local Expression is ve: values:get(index: mi);
					local String is kv: self:lowerExpr(expr: ke);
					local IrType is kty: self:irTypeFor(specType: ke:resolvedType);
					local String is kSuf: '';
					local IrType is kArgTy: IrType:Ptr;
					if({ ke:resolvedType == 'Int' || ke:resolvedType == 'Boolean' }, {
						kSuf: 'Int';
						kArgTy: IrType:I64;
					}, {
						if({ ke:resolvedType == 'Float' }, {
							kSuf: 'Flt';
							kArgTy: IrType:F64;
						}, {
							if({ ke:resolvedType != 'String' && ke:resolvedType != 'Any' }, {
								kSuf: 'Obj';
							});
						});
					});
					kv: self:castIfNeeded(val: kv, fromTy: kty, toTy: kArgTy);
					local String is vv: self:lowerExpr(expr: ve);
					local IrType is vty: self:irTypeFor(specType: ve:resolvedType);
					local String is vp: vv;
					if({ vty != IrType:Ptr }, {
						vp: self:nextTmp();
						self:emit(inst: IrInst:IrCast(dst: vp, val: vv, fromType: vty, toType: IrType:Ptr));
					});
					local Array of IrType is setT: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr];
					local Array of String is setV: ['null', mp, kv, vp];
					local String is setCallee: 'HashTable_mapSet' . kSuf . 'Any';
					if({ ve:resolvedType == 'String' }, {
						setCallee: 'HashTable_mapSet' . kSuf;
					});
					self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: setCallee, argTypes: setT, args: setV));
					mi++;
				});
				self:emitClaimPool(val: mp);
				return mp;
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				local String is tv: self:lowerExpr(expr: target);
				local String is iv: self:lowerExpr(expr: index);
				local String is raw: self:nextTmp();
				if({ target:resolvedType == 'Map' || target:resolvedType:startsWith(prefix: 'Map:') || target:resolvedType:startsWith(prefix: 'Map of ') }, {
					local String is kSpec: index:resolvedType;
					local String is tType: target:resolvedType;
					local String is kSuf: '';
					local IrType is kArgTy: IrType:Ptr;
					if({ kSpec == 'Int' || kSpec == 'Boolean' || tType:startsWith(prefix: 'Map of Int to ') || tType:startsWith(prefix: 'Map:Int:') || tType:startsWith(prefix: 'Map of Boolean to ') || tType:startsWith(prefix: 'Map:Boolean:') }, {
						kSuf: 'Int';
						kArgTy: IrType:I64;
					}, {
						if({ kSpec == 'Float' || tType:startsWith(prefix: 'Map of Float to ') || tType:startsWith(prefix: 'Map:Float:') }, {
							kSuf: 'Flt';
							kArgTy: IrType:F64;
						}, {
							if({ kSpec != 'String' && kSpec != 'Any' && tType != 'Map' && !tType:startsWith(prefix: 'Map of String to ') && !tType:startsWith(prefix: 'Map:String:') && !tType:startsWith(prefix: 'Map of Any to ') }, {
								kSuf: 'Obj';
							});
						});
					});
					local String is kp: self:castIfNeeded(val: iv, fromTy: self:irTypeFor(specType: kSpec), toTy: kArgTy);
					local String is mDef: 'null';
					if({ expr:resolvedType == 'String' || expr:resolvedType == '' }, {
						mDef: self:nextTmp();
						local Int is esid: self:mod:internStringLiteral(value: '');
						self:emit(inst: IrInst:ConstString(dst: mDef, strId: esid));
					});
					self:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapGet' . kSuf, argTypes: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr], args: ['null', tv, kp, mDef]));
				}, {
					local Array of IrType is gT: [IrType:Ptr, IrType:Ptr, IrType:I64];
					local Array of String is gV: ['null', tv, iv];
					self:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecGetChecked', argTypes: gT, args: gV));
				});
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
				if({ !bound:has(key: name) }, {
					if({ outerSlots:has(key: name) }, {
						if({ !seen:has(key: name) }, {
							seen:set(key: name, value: true);
							out:add(item: name);
						});
					}, {
						if({ outerSlots:has(key: 'self') && !seen:has(key: 'self') && self:mod:findStruct(name: self:currentClass):fieldIndex(name: name) >= 0 }, {
							seen:set(key: 'self', value: true);
							out:add(item: 'self');
						});
					});
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
			Expression:Path: local Function(Array of String is segments){
				if({ segments:length() > 0 }, {
					local String is seg0: segments:get(index: 0, default: '');
					if({ !bound:has(key: seg0) }, {
						if({ outerSlots:has(key: seg0) }, {
							if({ !seen:has(key: seg0) }, {
								seen:set(key: seg0, value: true);
								out:add(item: seg0);
							});
						}, {
							if({ outerSlots:has(key: 'self') && !seen:has(key: 'self') && self:mod:findStruct(name: self:currentClass):fieldIndex(name: seg0) >= 0 }, {
								seen:set(key: 'self', value: true);
								out:add(item: 'self');
							});
						});
					});
				});
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
				local Boolean is isBareCall: match(on: call:target, when: [
					Expression:Ident: local Function of Boolean(String is tname){ return tname == 'self'; },
					Expression:Unknown: local Function of Boolean(){ return true; },
					else: { false }
				]);
				if({ isBareCall && !bound:has(key: call:name) && outerSlots:has(key: call:name) && !seen:has(key: call:name) }, {
					seen:set(key: call:name, value: true);
					out:add(item: call:name);
				});
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
		local String is retSpecType: returnType:name;
		if({ returnType:name == 'Function' }, {
			if({ returnType:params:length() > 0 }, {
				local Type is rt: returnType:params:get(index: 0);
				retTy: self:irTypeFor(specType: rt:name);
				retSpecType: rt:name;
			}, {
				retTy: IrType:Void;
				retSpecType: '';
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
				envSt:addField(name: cname, ty: IrType:Ptr);
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
		local Map of String to Boolean is savedIsArc: self:localIsArc;
		local Map of String to String is savedSpecTypes: self:localSpecTypes;
		local Map of String to Boolean is savedBoxed: self:boxedLocals;
		local Map of String to Boolean is savedCaptured: self:capturedNames;
		local Array of String is savedOwned: self:ownedSlots;
		local Array of String is savedScopeVars: self:scopeVarStack;
		local Array of String is savedScopeOldSlots: self:scopeOldSlotStack;
		local Array of IrType is savedScopeOldTypes: self:scopeOldTypeStack;
		local Array of Boolean is savedScopeOldArcs: self:scopeOldArcStack;
		local Array of String is savedScopeOldSpecs: self:scopeOldSpecTypeStack;
		local Array of Boolean is savedScopeOldBoxed: self:scopeOldBoxedStack;
		local Array of Int is savedScopeMarks: self:scopeMarkStack;
		local String is savedPoolMark: self:curPoolMark;
		local Boolean is savedRetIsArc: self:curFnRetIsArc;

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
		self:localIsArc: Map:init();
		self:localSpecTypes: Map:init();
		self:boxedLocals: Map:init();
		self:capturedNames: Map:init();
		self:ownedSlots: [];
		self:resetScopes();

		local Map of String to Boolean is decls: Map:init();
		local Int is dpi: 0;
		while({ dpi < params:length() }, {
			local Parameter is dp: params:get(index: dpi);
			decls:set(key: dp:name, value: true);
			dpi++;
		});
		self:collectDeclNamesInStmts(stmts: body, decls: decls);
		self:collectAllAnonCapturesInStmts(stmts: body, decls: decls, out: self:capturedNames);
		self:curFnRetIsArc: self:isArcSpecType(specType: retSpecType);
		self:emitPoolEnter();

		# Unpack captured variables from %env into local slots
		local Int is uci: 0;
		while({ uci < captures:length() }, {
			local String is cname: captures:get(index: uci, default: '');
			local IrType is cty: savedTypes:get(key: cname, default: IrType:I64);
			local Boolean is cArc: savedIsArc:get(key: cname, default: false);
			local String is fPtr: self:nextTmp();
			self:emit(inst: IrInst:FieldPtr(dst: fPtr, objPtr: '%env', structName: envStructName, fieldIndex: uci + 2));
			local String is loaded: self:nextTmp();
			self:emit(inst: IrInst:Load(dst: loaded, slot: fPtr, ty: IrType:Ptr));
			self:localTypes:set(key: cname, value: cty);
			self:localIsArc:set(key: cname, value: cArc);
			self:localSpecTypes:set(key: cname, value: savedSpecTypes:get(key: cname, default: ''));
			if({ cname == 'self' }, {
				local String is capSlot: '%cap_' . cname;
				self:localSlots:set(key: cname, value: capSlot);
				self:emit(inst: IrInst:Alloca(slot: capSlot, ty: cty));
				if({ cArc }, {
					self:emit(inst: IrInst:Retain(val: loaded));
					self:ownedSlots:add(item: capSlot);
				});
				self:emit(inst: IrInst:Store(slot: capSlot, val: loaded, ty: cty));
			}, {
				if({ savedBoxed:has(key: cname) }, {
					local String is capSlot: '%cap_' . cname;
					self:localSlots:set(key: cname, value: capSlot);
					self:boxedLocals:set(key: cname, value: true);
					self:emit(inst: IrInst:Alloca(slot: capSlot, ty: IrType:Ptr));
					self:emit(inst: IrInst:Store(slot: capSlot, val: loaded, ty: IrType:Ptr));
				}, {
					self:localSlots:set(key: cname, value: loaded);
				});
			});
			uci++;
		});

		pi: 0;
		while({ pi < params:length() }, {
			local Parameter is p: params:get(index: pi);
			local IrType is pty: self:irTypeFor(specType: p:paramType:name);
			local Boolean is pArc: self:isArcSpecType(specType: p:paramType:name);
			local String is slot: '%slot_' . p:name;
			self:localSlots:set(key: p:name, value: slot);
			self:localTypes:set(key: p:name, value: pty);
			self:localIsArc:set(key: p:name, value: pArc);
			self:localSpecTypes:set(key: p:name, value: p:paramType:name);
			if({ self:capturedNames:has(key: p:name) }, {
				self:boxedLocals:set(key: p:name, value: true);
				self:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
				if({ pArc }, {
					self:emit(inst: IrInst:Retain(val: '%p_' . p:name));
				});
				local String is boxPtr: self:emitNewBox(initVal: '%p_' . p:name, ty: pty, isArc: pArc);
				self:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
				self:ownedSlots:add(item: slot);
			}, {
				self:emit(inst: IrInst:Alloca(slot: slot, ty: pty));
				self:emit(inst: IrInst:Store(slot: slot, val: '%p_' . p:name, ty: pty));
			});
			pi++;
		});

		self:lowerStmts(stmts: body);
		if({ !self:blkTerminated }, {
			self:emitReleaseOwnedLocals();
			self:emitPoolExit();
			if({ retTy == IrType:Void }, {
				self:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
			}, {
				local String is defVal: self:emitDefaultVal(ty: retTy);
				self:terminate(inst: IrInst:Ret(hasVal: true, val: defVal, ty: retTy));
			});
		});
		self:curPoolMark: '';
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
				local Boolean is cArc: savedIsArc:get(key: cname, default: false);
				if({ (cname == 'self' && cArc) || savedBoxed:has(key: cname) }, {
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
		self:localIsArc: savedIsArc;
		self:localSpecTypes: savedSpecTypes;
		self:boxedLocals: savedBoxed;
		self:capturedNames: savedCaptured;
		self:ownedSlots: savedOwned;
		self:scopeVarStack: savedScopeVars;
		self:scopeOldSlotStack: savedScopeOldSlots;
		self:scopeOldTypeStack: savedScopeOldTypes;
		self:scopeOldArcStack: savedScopeOldArcs;
		self:scopeOldSpecTypeStack: savedScopeOldSpecs;
		self:scopeOldBoxedStack: savedScopeOldBoxed;
		self:scopeMarkStack: savedScopeMarks;
		self:curPoolMark: savedPoolMark;
		self:curFnRetIsArc: savedRetIsArc;

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
				local Boolean is oArc: self:localIsArc:get(key: cname, default: false);
				local String is dstPtr: self:nextTmp();
				self:emit(inst: IrInst:FieldPtr(dst: dstPtr, objPtr: envVal, structName: envStructName, fieldIndex: oci + 2));
				if({ cname == 'self' || self:boxedLocals:has(key: cname) }, {
					local String is oVal: self:nextTmp();
					local IrType is loadTy: if({ cname == 'self' }, { oTy }, { IrType:Ptr });
					self:emit(inst: IrInst:Load(dst: oVal, slot: oSlot, ty: loadTy));
					if({ oArc || self:boxedLocals:has(key: cname) }, {
						self:emit(inst: IrInst:Retain(val: oVal));
					});
					self:emit(inst: IrInst:Store(slot: dstPtr, val: oVal, ty: IrType:Ptr));
				}, {
					self:emit(inst: IrInst:Store(slot: dstPtr, val: oSlot, ty: IrType:Ptr));
				});
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
		self:emitClaimPool(val: clsTmp);
		return clsTmp;
	}

	local Function of String is lowerCall(Expression is expr, CallData is call){
		local String is nm: call:name;

		if({ nm == 'toBase' && call:target:resolvedType == 'Int' }, {
			local String is iv: self:lowerExpr(expr: call:target);
			local String is baseV: '10';
			local String is digV: '0';
			if({ call:args:length() >= 1 }, {
				local NamedArg is na0: call:args:get(index: 0);
				if({ na0:name == 'digits' }, { digV: self:lowerExpr(expr: na0:value); }, { baseV: self:lowerExpr(expr: na0:value); });
			});
			if({ call:args:length() >= 2 }, {
				local NamedArg is na1: call:args:get(index: 1);
				if({ na1:name == 'base' }, { baseV: self:lowerExpr(expr: na1:value); }, { digV: self:lowerExpr(expr: na1:value); });
			});
			local String is dst: self:nextTmp();
			self:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToBase', argTypes: [IrType:Ptr, IrType:I64, IrType:I64, IrType:I64], args: ['null', iv, baseV, digV]));
			return dst;
		});

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
		local Boolean is isBareTarget: match(on: call:target, when: [
			Expression:Ident: local Function of Boolean(String is tname){ return tname == 'self'; },
			Expression:Unknown: local Function of Boolean(){ return true; }
		], default: { false });
		if({ isBareTarget && self:localSlots:has(key: nm) && self:localTypes:get(key: nm, default: IrType:I64) == IrType:Ptr }, {
			local String is cObj: self:emitLoadLocal(name: nm, ty: IrType:Ptr);
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

		local String is recvType: self:baseTypeName(t: call:target:resolvedType);

		# Method / constructor call
		local IrType is retTy: self:irTypeFor(specType: expr:resolvedType);
		local Array of IrType is argTypes: [];
		local Array of String is argVals: [];

		local String is calleeName: match(on: call:target, when: [
			Expression:Ident: local Function of String(String is tname){
				if({ tname != 'self' && self:localSlots:has(key: tname) && recvType != '' }, {
					return self:cStructName(qname: recvType) . '_' . nm;
				});
				if({ tname != 'self' && !self:localSlots:has(key: tname) && self:localSlots:has(key: 'self') && self:mod:findStruct(name: self:currentClass):fieldIndex(name: tname) >= 0 && recvType != '' }, {
					return self:cStructName(qname: recvType) . '_' . nm;
				});
				if({ tname != 'self' && !self:localSlots:has(key: tname) }, {
					return self:cStructName(qname: tname) . '_' . nm;
				});
				return self:currentClass . '_' . nm;
			},
			Expression:Path: local Function of String(Array of String is segs){
				if({ segs:length() >= 2 && (segs:get(index: 0, default: '') == 'self' || self:localSlots:has(key: segs:get(index: 0, default: '')) || self:heldFields:has(key: self:currentClass . ':' . segs:get(index: 0, default: '')) || self:heldFields:has(key: segs:get(index: 0, default: '') . ':' . segs:get(index: 1, default: '')) || (self:localSlots:has(key: 'self') && self:mod:findStruct(name: self:currentClass):fieldIndex(name: segs:get(index: 0, default: '')) >= 0)) }, {
					if({ recvType != '' }, { return self:cStructName(qname: recvType) . '_' . nm; });
				});
				if({ segs:length() > 0 }, {
					return segs:get(index: segs:length() - 1, default: '') . '_' . nm;
				});
				return self:currentClass . '_' . nm;
			}
		], default: {
			if({ recvType != '' }, { return self:cStructName(qname: recvType) . '_' . nm; });
			return self:currentClass . '_' . nm;
		});
		# Receiver: self or local variable, else static class Path (or held field receiver)
		local Boolean is hasRecv: match(on: call:target, when: [
			Expression:Ident: local Function of Boolean(String is tname){
				if({ tname == 'self' || self:localSlots:has(key: tname) || (self:localSlots:has(key: 'self') && self:mod:findStruct(name: self:currentClass):fieldIndex(name: tname) >= 0) }, {
					argTypes:add(item: IrType:Ptr);
					argVals:add(item: self:lowerExpr(expr: call:target));
					return true;
				});
				return false;
			},
			Expression:Path: local Function of Boolean(Array of String is segs){
				if({ segs:length() >= 2 && (segs:get(index: 0, default: '') == 'self' || self:localSlots:has(key: segs:get(index: 0, default: '')) || self:heldFields:has(key: self:currentClass . ':' . segs:get(index: 0, default: '')) || self:heldFields:has(key: segs:get(index: 0, default: '') . ':' . segs:get(index: 1, default: '')) || (self:localSlots:has(key: 'self') && self:mod:findStruct(name: self:currentClass):fieldIndex(name: segs:get(index: 0, default: '')) >= 0)) }, {
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

		local String is staticTargetName: '';
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
			staticTargetName: pathCName;
			local Boolean is isVariantCtor: (pathWithNm != '') && (self:mod:findStruct(name: pathWithNm):name != '');
			if({ nm == 'init' || isVariantCtor }, {
				# Constructor: ClassName_new + ClassName_init
				local String is clsName: self:currentClass;
				if({ isVariantCtor }, {
					clsName: pathWithNm;
				}, {
					if({ pathCName != '' }, { clsName: pathCName; });
				});
				if({ self:mod:findStruct(name: clsName):name == '' }, {
					local String is resCName: self:cStructName(qname: expr:resolvedType);
					if({ resCName != '' && self:mod:findStruct(name: resCName):name != '' }, {
						clsName: resCName;
					}, {
						if({ self:currentClass != '' && self:mod:findStruct(name: self:currentClass . '_' . clsName):name != '' }, {
							clsName: self:currentClass . '_' . clsName;
						});
					});
				});
				local String is obj: self:nextTmp();
				self:emit(inst: IrInst:AllocObj(dst: obj, structName: clsName, destroyFn: self:destroyFnFor(structName: clsName)));
				argTypes:add(item: IrType:Ptr);
				argVals:add(item: obj);
				local String is ctorSuf: '';
				if({ call:overloadIndex > 0 }, {
					ctorSuf: '_' . ((call:overloadIndex + 1) as String);
				});
				local String is ctorKey: clsName . '_init' . ctorSuf;
				if({ !self:methodParams:has(key: ctorKey) }, {
					local String is qLookup: clsName;
					if({ expr:resolvedType != '' && self:clsMap:has(key: expr:resolvedType) }, {
						qLookup: expr:resolvedType;
					});
					local String is parentInit: self:findParentMethodImpl(clsName: qLookup, methodName: 'init', suffix: ctorSuf);
					if({ parentInit != '' }, {
						if({ call:args:length() == 0 && self:mod:findStruct(name: clsName):name != '' }, {
							self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: clsName . '_init', argTypes: [IrType:Ptr], args: [obj]));
						});
						ctorKey: parentInit;
					}, {
						if({ call:args:length() == 0 && self:mod:findStruct(name: clsName):name != '' }, {
							ctorKey: clsName . '_init';
						});
					});
				});
				self:lowerCallArgs(fnKey: ctorKey, callArgs: call:args, argTypes: argTypes, argVals: argVals);
				self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: ctorKey, argTypes: argTypes, args: argVals));
				self:emitClaimPool(val: obj);
				return obj;
			});
		});

		if({ call:bareProvider != '' }, {
			local String is provStruct: self:cStructName(qname: call:bareProvider);
			if({ self:mod:findStruct(name: provStruct):name != '' }, {
				local String is provObj: self:emitImportFieldOrAlloc(provStruct: provStruct, rawName: call:bareProvider);
				argTypes: [IrType:Ptr];
				argVals: [provObj];
				hasRecv: true;
				recvType: call:bareProvider;
				calleeName: provStruct . '_' . nm;
			});
		});

		if({ !hasRecv && !self:heldMethods:has(key: calleeName) }, {
			local String is provStruct: '';
			if({ staticTargetName != '' }, {
				provStruct: self:cStructName(qname: staticTargetName);
				if({ self:mod:findStruct(name: provStruct):name == '' && self:clsQNameMap:has(key: staticTargetName) }, {
					provStruct: self:cStructName(qname: self:clsQNameMap:get(key: staticTargetName, default: staticTargetName));
				});
			});
			if({ provStruct != '' && self:mod:findStruct(name: provStruct):name != '' }, {
				local String is provObj: self:emitImportFieldOrAlloc(provStruct: provStruct, rawName: staticTargetName);
				argTypes:add(item: IrType:Ptr);
				argVals:add(item: provObj);
			}, {
				argTypes:add(item: IrType:Ptr);
				argVals:add(item: 'null');
			});
		});

		if({ call:overloadIndex > 0 }, {
			calleeName: calleeName . '_' . ((call:overloadIndex + 1) as String);
		});
		local Int is vslot: -1;
		local String is dirCallee: calleeName;
		local String is recvStruct: self:currentClass;
		if({ hasRecv && nm != 'init' && nm != 'destroy' && !self:heldMethods:has(key: calleeName) }, {
			local Boolean is isSelfTarget: false;
			match(on: call:target, when: [
				Expression:Ident: local Function(String is tname){
					if({ tname == 'self' }, { isSelfTarget: true; });
				}
			], default: {});
			if({ (!isSelfTarget || call:bareProvider != '') && recvType != '' }, {
				recvStruct: self:cStructName(qname: recvType);
				if({ self:mod:findStruct(name: recvStruct):name == '' && self:clsQNameMap:has(key: recvType) }, {
					recvStruct: self:cStructName(qname: self:clsQNameMap:get(key: recvType, default: recvType));
				});
			});
			if({ recvStruct != 'String' && recvStruct != 'Array' && recvStruct != 'Map' && recvStruct != 'Math' && recvStruct != 'List' }, {
				local IrStruct is rst: self:mod:findStruct(name: recvStruct);
				local String is vkey: if({ call:overloadIndex > 0 }, { nm . '_' . ((call:overloadIndex + 1) as String) }, { nm });
				vslot: rst:vtableSlot(mname: vkey);
				if({ vslot >= 0 }, {
					local String is vtFn: rst:vtableFns:get(index: vslot, default: calleeName);
					if({ vtFn != '' && vtFn != 'null' }, {
						dirCallee: vtFn;
					});
				});
			});
		});

		self:lowerCallArgs(fnKey: dirCallee, callArgs: call:args, argTypes: argTypes, argVals: argVals);

		local IrType is callRetTy: retTy;
		if({ self:methodRetTypes:has(key: dirCallee) }, {
			callRetTy: self:methodRetTypes:get(key: dirCallee, default: retTy);
		});
		local Boolean is hasDst: callRetTy != IrType:Void;
		local String is dst: '';
		if({ hasDst }, { dst: self:nextTmp(); });

		if({ vslot >= 0 }, {
			local String is recvPtr: argVals:get(index: 0, default: 'null');
			if({ recvPtr == 'null' }, {
				self:emit(inst: IrInst:IrCall(dst: dst, hasDst: hasDst, retType: callRetTy, callee: dirCallee, argTypes: argTypes, args: argVals));
			}, {
				local String is resSlot: '';
				if({ hasDst }, {
					resSlot: self:nextTmp();
					self:emit(inst: IrInst:Alloca(slot: resSlot, ty: callRetTy));
				});
				local String is isNonNull: self:nextTmp();
				self:emit(inst: IrInst:Cmp(dst: isNonNull, op: '!=', lhs: recvPtr, rhs: 'null', ty: IrType:Ptr));
				local String is vtLbl: self:nextLabel(prefix: 'vt_call');
				local String is dirLbl: self:nextLabel(prefix: 'dir_call');
				local String is endLbl: self:nextLabel(prefix: 'vt_end');
				self:terminate(inst: IrInst:CondBr(cond: isNonNull, thenLabel: vtLbl, elseLabel: dirLbl));

				local IrBlock is vtBlk: self:curFn:addBlock(label: vtLbl);
				self:switchBlock(blk: vtBlk);
				local String is vtPtrAddr: self:nextTmp();
				self:emit(inst: IrInst:FieldPtr(dst: vtPtrAddr, objPtr: recvPtr, structName: recvStruct, fieldIndex: 1));
				local String is vtBase: self:nextTmp();
				self:emit(inst: IrInst:Load(dst: vtBase, slot: vtPtrAddr, ty: IrType:Ptr));
				local String is slotPtr: self:nextTmp();
				self:emit(inst: IrInst:PtrElem(dst: slotPtr, basePtr: vtBase, index: vslot));
				local String is fnPtr: self:nextTmp();
				self:emit(inst: IrInst:Load(dst: fnPtr, slot: slotPtr, ty: IrType:Ptr));
				local String is vtDst: '';
				if({ hasDst }, { vtDst: self:nextTmp(); });
				self:emit(inst: IrInst:IndirectCall(dst: vtDst, hasDst: hasDst, retType: callRetTy, fnPtr: fnPtr, argTypes: argTypes, args: argVals));
				if({ hasDst }, {
					self:emit(inst: IrInst:Store(slot: resSlot, val: vtDst, ty: callRetTy));
				});
				self:terminate(inst: IrInst:Br(target: endLbl));

				local IrBlock is dirBlk: self:curFn:addBlock(label: dirLbl);
				self:switchBlock(blk: dirBlk);
				local String is dirDst: '';
				if({ hasDst }, { dirDst: self:nextTmp(); });
				self:emit(inst: IrInst:IrCall(dst: dirDst, hasDst: hasDst, retType: callRetTy, callee: dirCallee, argTypes: argTypes, args: argVals));
				if({ hasDst }, {
					self:emit(inst: IrInst:Store(slot: resSlot, val: dirDst, ty: callRetTy));
				});
				self:terminate(inst: IrInst:Br(target: endLbl));

				local IrBlock is endBlk: self:curFn:addBlock(label: endLbl);
				self:switchBlock(blk: endBlk);
				if({ hasDst }, {
					self:emit(inst: IrInst:Load(dst: dst, slot: resSlot, ty: callRetTy));
				});
			});
		}, {
			self:emit(inst: IrInst:IrCall(dst: dst, hasDst: hasDst, retType: callRetTy, callee: calleeName, argTypes: argTypes, args: argVals));
		});
		if({ callRetTy != retTy && hasDst }, {
			dst: self:castIfNeeded(val: dst, fromTy: callRetTy, toTy: retTy);
		});
		return dst;
	}

	local Function of String is emitImportFieldOrAlloc(String is provStruct, String is rawName){
		if({ provStruct == 'Math' || provStruct == 'String' || provStruct == 'Array' || provStruct == 'Map' || provStruct == 'Vector' || provStruct == 'HashTable' || provStruct == 'Buf' || provStruct == 'Mem' || provStruct == 'Introspection' }, {
			return 'null';
		});
		if({ self:currentClass != '' && self:localSlots:has(key: 'self') }, {
			local IrStruct is curSt: self:mod:findStruct(name: self:currentClass);
			local Int is impIdx: curSt:fieldIndex(name: '_import_' . provStruct);
			if({ impIdx < 0 && rawName != '' }, {
				impIdx: curSt:fieldIndex(name: '_import_' . rawName);
			});
			if({ impIdx >= 0 }, {
				local String is selfPtr: self:emitLoadLocal(name: 'self', ty: IrType:Ptr);
				local String is fPtr: self:nextTmp();
				self:emit(inst: IrInst:FieldPtr(dst: fPtr, objPtr: selfPtr, structName: self:currentClass, fieldIndex: impIdx));
				local String is fVal: self:nextTmp();
				self:emit(inst: IrInst:Load(dst: fVal, slot: fPtr, ty: IrType:Ptr));
				return fVal;
			});
		});
		local String is provObj: self:nextTmp();
		self:emit(inst: IrInst:AllocObj(dst: provObj, structName: provStruct, destroyFn: self:destroyFnFor(structName: provStruct)));
		self:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: provStruct . '_init', argTypes: [IrType:Ptr], args: [provObj]));
		self:emitClaimPool(val: provObj);
		return provObj;
	}

	local Function is lowerCallArgs(String is fnKey, Array of NamedArg is callArgs, Array of IrType is argTypes, Array of String is argVals){
		if({ !self:methodParams:has(key: fnKey) }, {
			local Int is ai: 0;
			local String is calleeMask: self:methodParamPtrMask:get(key: fnKey, default: '');
			while({ ai < callArgs:length() }, {
				local NamedArg is na2: callArgs:get(index: ai);
				local Expression is av: na2:value;
				local IrType is aty: self:irTypeFor(specType: av:resolvedType);
				if({ aty == IrType:Void }, { aty: IrType:I64; });
				local String is aval: self:lowerExpr(expr: av);
				if({ ai < calleeMask:length() && calleeMask:charAt(index: ai, default: '0') == '1' }, {
					if({ aty != IrType:Ptr }, {
						aval: self:castIfNeeded(val: aval, fromTy: aty, toTy: IrType:Ptr);
						aty: IrType:Ptr;
					});
				});
				argTypes:add(item: aty);
				argVals:add(item: aval);
				ai++;
			});
			return;
		});
		local Array of Parameter is params: self:methodParams:get(key: fnKey, default: []);
		local Int is pi: 0;
		while({ pi < params:length() }, {
			local Parameter is p: params:get(index: pi);
			local IrType is pty: self:irTypeFor(specType: p:paramType:name);
			if({ pty == IrType:Void }, { pty: IrType:Ptr; });
			local Boolean is found: false;
			local Int is ai: 0;
			local NamedArg is matched;
			while({ ai < callArgs:length() && !found }, {
				local NamedArg is na: callArgs:get(index: ai);
				if({ na:name == p:name || (na:name == '' && ai == pi) }, {
					matched: na;
					found: true;
				});
				ai++;
			});
			if({ !found && pi < callArgs:length() }, {
				local NamedArg is posNa: callArgs:get(index: pi);
				local Boolean is matchesOtherParam: false;
				if({ posNa:name != '' }, {
					local Int is opi: 0;
					while({ opi < params:length() && !matchesOtherParam }, {
						local Parameter is opP: params:get(index: opi);
						if({ opP:name == posNa:name }, { matchesOtherParam: true; });
						opi++;
					});
				});
				if({ !matchesOtherParam }, {
					matched: posNa;
					found: true;
				});
			});
			local String is aval: '';
			local IrType is aty: pty;
			if({ found }, {
				local Expression is av: matched:value;
				aty: self:irTypeFor(specType: av:resolvedType);
				if({ aty == IrType:Void }, {
					aty: match(on: av, when: [
						Expression:StringLit: local Function of IrType(String is s){ return IrType:Ptr; },
						Expression:ArrayLit: local Function of IrType(Array of Expression is items){ return IrType:Ptr; },
						Expression:MapLit: local Function of IrType(Array of Expression is keys, Array of Expression is vals){ return IrType:Ptr; },
						Expression:AnonFn: local Function of IrType(Type is retT, Array of Parameter is ps, Array of Statement is bs){ return IrType:Ptr; },
						Expression:FloatLit: local Function of IrType(String is t){ return IrType:F64; },
						Expression:BoolLit: local Function of IrType(Boolean is b){ return IrType:I1; },
						Expression:NumberLit: local Function of IrType(Int is i, String is t){ return IrType:I64; },
						else: { pty }
					]);
				});
				aval: self:lowerExpr(expr: av);
			}, {
				if({ p:hasDefault }, {
					aty: self:irTypeFor(specType: p:defaultExpr:resolvedType);
					if({ aty == IrType:Void }, { aty: IrType:I64; });
					aval: self:lowerExpr(expr: p:defaultExpr);
				}, {
					aval: self:emitDefaultVal(ty: pty);
					aty: pty;
				});
			});
			if({ aty != pty }, {
				aval: self:castIfNeeded(val: aval, fromTy: aty, toTy: pty);
			});
			argTypes:add(item: pty);
			argVals:add(item: aval);
			pi++;
		});
	}
}
