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
	Map of String to String is lazyLocalStateSlots: Map:init();
	Map of String to Expression is lazyLocalExprs: Map:init();
	Array of String is ownedSlots: [];
	Array of String is scopeVarStack: [];
	Array of String is scopeOldSlotStack: [];
	Array of IrType is scopeOldTypeStack: [];
	Array of Boolean is scopeOldArcStack: [];
	Array of String is scopeOldSpecTypeStack: [];
	Array of Boolean is scopeOldBoxedStack: [];
	Array of String is scopeOldLazyStateStack: [];
	Array of Expression is scopeOldLazyExprStack: [];
	Array of Int is scopeMarkStack: [];
	String is curPoolMark: '';
	Boolean is curFnRetIsArc: false;
	String is curFnErrHandlerCallee: '';
	String is curFnErrPushedSlot: '';
	Boolean is isUnmanagedClass: false;
	String is inlineReturnSlot: '';
	String is inlineReturnEndLbl: '';
	IrType is inlineReturnTy: IrType:Void;
	String is expectedMapKeyType: '';
	String is expectedMapValType: '';
	Expression is currentCallExpr: Expression:Unknown;
	Array of CallLowerer is callLowerers: [];
	Map of String to ClassInfo is clsMap: Map:init();
	Map of String to ClassInfo is sysinternalClasses: Map:init();
	Map of String to String is clsQNameMap: Map:init();
	Map of String to String is methodParamPtrMask: Map:init();
	Map of String to Boolean is methodRetIsPtr: Map:init();
	Map of String to IrType is methodRetTypes: Map:init();
	Map of String to Array of Parameter is methodParams: Map:init();
	Map of String to Boolean is curClassTypeParams: Map:init();
	Map of String to String is heldFields: Map:init();
	Map of String to String is heldFieldTypes: Map:init();
	Map of String to String is lazyFields: Map:init();
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
	Map of String to Boolean is canUnwindCallees: Map:init();
	Map of String to Boolean is canUnwindMethodNames: Map:init();
	String is pathObjPtr: '';
	String is pathStructName: '';
	Int is pathFieldIndex: -1;

	replace Function is init(){
		:callLowerers: CallLowererRegistry:init():loadAll();
	}

	Function of String is nextTmp(){
		:tmpCounter: :tmpCounter + 1;
		return '%t' . (:tmpCounter as String);
	}

	Function of String is nextLabel(String is prefix){
		:lblCounter: :lblCounter + 1;
		return prefix . '_' . (:lblCounter as String);
	}

	Function of IrType is irTypeFor(String is specType){
		if({ specType == 'Int' || specType == 'Byte' }, { return IrType:I64; });
		if({ specType == 'Float' }, { return IrType:F64; });
		if({ specType == 'Boolean' }, { return IrType:I1; });
		if({ specType == 'Void' || specType == '' }, { return IrType:Void; });
		return IrType:Ptr;
	}

	Function of Boolean is isArcSpecType(String is specType){
		if({ :isUnmanagedClass || specType == '' || specType == 'Void' || specType == 'Any' || specType == 'Int' || specType == 'Float' || specType == 'Boolean' || specType == 'Byte' || :curClassTypeParams:has(key: specType) }, {
			return false;
		});
		return true;
	}

	Function of Boolean is hasMethodBodies(ClassInfo is cls){
		local Int is i: 0;
		while({ i < cls:members:length() }, {
			local Member is m: cls:members:get(index: i);
			if({ m:kind == MemberKind:METHOD && m:body:length() > 0 }, {
				return true;
			});
			i++;
		});
		return false;
	}

	Function of String is castIfNeeded(String is val, IrType is fromTy, IrType is toTy){
		if({ fromTy == toTy || fromTy == IrType:Void || toTy == IrType:Void || val == '' }, { return val; });
		local String is dst: :nextTmp();
		:emit(inst: IrInst:IrCast(dst: dst, val: val, fromType: fromTy, toType: toTy));
		return dst;
	}

	Function is emit(IrInst is inst){
		if({ !:blkTerminated }, {
			local Boolean is hoisted: false;
			match(on: inst, when: [
				IrInst:Alloca: local Function(String is slot, IrType is ty){
					if({ :curFn:blocks:length() > 0 }, {
						local IrBlock is entryBlk: :curFn:blocks:get(index: 0);
						if({ :curBlk:label != entryBlk:label }, {
							if({ ty == IrType:Ptr }, {
								entryBlk:prependAt(inst: IrInst:Store(slot: slot, val: 'null', ty: IrType:Ptr), line: :currentLine);
							});
							entryBlk:prependAt(inst: inst, line: :currentLine);
							hoisted: true;
						});
					});
				}
			], default: {});
			if({ !hoisted }, {
				:curBlk:appendAt(inst: inst, line: :currentLine);
			});
		});
	}

	Function is terminate(IrInst is inst){
		if({ !:blkTerminated }, {
			:curBlk:appendAt(inst: inst, line: :currentLine);
			:blkTerminated: true;
		});
	}

	Function is switchBlock(IrBlock is blk){
		:curBlk: blk;
		:blkTerminated: false;
	}

	Function is resetScopes(){
		:scopeVarStack: [];
		:scopeOldSlotStack: [];
		:scopeOldTypeStack: [];
		:scopeOldArcStack: [];
		:scopeOldSpecTypeStack: [];
		:scopeOldBoxedStack: [];
		:scopeOldLazyStateStack: [];
		:scopeOldLazyExprStack: [];
		:scopeMarkStack: [];
		:lazyLocalStateSlots: Map:init();
		:lazyLocalExprs: Map:init();
	}

	Function is pushScope(){
		:scopeMarkStack:add(item: :scopeVarStack:length());
	}

	Function is bindLocal(String is name, String is slot, IrType is ty, Boolean is isArc, String is specType, Boolean is isBoxed){
		if({ :scopeMarkStack:length() > 0 }, {
			:scopeVarStack:add(item: name);
			if({ :localSlots:has(key: name) }, {
				:scopeOldSlotStack:add(item: :localSlots:get(key: name, default: ''));
				:scopeOldTypeStack:add(item: :localTypes:get(key: name, default: IrType:I64));
				:scopeOldArcStack:add(item: :localIsArc:get(key: name, default: false));
				:scopeOldSpecTypeStack:add(item: :localSpecTypes:get(key: name, default: ''));
				:scopeOldBoxedStack:add(item: :boxedLocals:has(key: name));
				:scopeOldLazyStateStack:add(item: :lazyLocalStateSlots:get(key: name, default: ''));
				:scopeOldLazyExprStack:add(item: :lazyLocalExprs:get(key: name, default: Expression:Unknown));
			}, {
				:scopeOldSlotStack:add(item: '');
				:scopeOldTypeStack:add(item: IrType:I64);
				:scopeOldArcStack:add(item: false);
				:scopeOldSpecTypeStack:add(item: '');
				:scopeOldBoxedStack:add(item: false);
				:scopeOldLazyStateStack:add(item: '');
				:scopeOldLazyExprStack:add(item: Expression:Unknown);
			});
		});
		:localSlots:set(key: name, value: slot);
		:localTypes:set(key: name, value: ty);
		:localIsArc:set(key: name, value: isArc);
		:localSpecTypes:set(key: name, value: specType);
		if({ :lazyLocalStateSlots:has(key: name) }, {
			:lazyLocalStateSlots:remove(key: name);
			:lazyLocalExprs:remove(key: name);
		});
		if({ isBoxed }, {
			:boxedLocals:set(key: name, value: true);
		}, {
			if({ :boxedLocals:has(key: name) }, {
				:boxedLocals:remove(key: name);
			});
		});
	}

	Function is popScope(){
		if({ :scopeMarkStack:length() == 0 }, { return; });
		local Int is mark: :scopeMarkStack:pop(default: 0);
		while({ :scopeVarStack:length() > mark }, {
			local String is name: :scopeVarStack:pop(default: '');
			local String is oldSlot: :scopeOldSlotStack:pop(default: '');
			local IrType is oldTy: :scopeOldTypeStack:pop(default: IrType:I64);
			local Boolean is oldArc: :scopeOldArcStack:pop(default: false);
			local String is oldSpec: :scopeOldSpecTypeStack:pop(default: '');
			local Boolean is oldBoxed: :scopeOldBoxedStack:pop(default: false);
			local String is oldLazyState: :scopeOldLazyStateStack:pop(default: '');
			local Expression is oldLazyExpr: :scopeOldLazyExprStack:pop(default: Expression:Unknown);
			if({ oldSlot == '' }, {
				:localSlots:remove(key: name);
				:localTypes:remove(key: name);
				:localIsArc:remove(key: name);
				:localSpecTypes:remove(key: name);
				if({ :boxedLocals:has(key: name) }, {
					:boxedLocals:remove(key: name);
				});
				if({ :lazyLocalStateSlots:has(key: name) }, {
					:lazyLocalStateSlots:remove(key: name);
					:lazyLocalExprs:remove(key: name);
				});
			}, {
				:localSlots:set(key: name, value: oldSlot);
				:localTypes:set(key: name, value: oldTy);
				:localIsArc:set(key: name, value: oldArc);
				:localSpecTypes:set(key: name, value: oldSpec);
				if({ oldBoxed }, {
					:boxedLocals:set(key: name, value: true);
				}, {
					if({ :boxedLocals:has(key: name) }, {
						:boxedLocals:remove(key: name);
					});
				});
				if({ oldLazyState != '' }, {
					:lazyLocalStateSlots:set(key: name, value: oldLazyState);
					:lazyLocalExprs:set(key: name, value: oldLazyExpr);
				}, {
					if({ :lazyLocalStateSlots:has(key: name) }, {
						:lazyLocalStateSlots:remove(key: name);
						:lazyLocalExprs:remove(key: name);
					});
				});
			});
		});
	}

	local Function of Boolean is isStdlibClass(ClassInfo is cls){
		if({ :bindings:isSysinternal(cls: cls) }, {
			return !:hasMethodBodies(cls: cls);
		});
		if({ cls:name == 'List' || cls:name == 'LoopControl' || cls:name == 'LoopCallback' || cls:name == 'Class' || cls:name == 'Function' || cls:name == 'Int' || cls:name == 'Float' || cls:name == 'Boolean' || cls:name == 'Byte' || cls:name == 'Void' || cls:name == 'Any' || cls:name == 'Object' }, { return true; });
		return false;
	}

	Function of String is baseTypeName(String is t){
		local String is res: t;
		local Int is ofIdx: res:indexOf(search: ' of ', default: -1);
		if({ ofIdx > 0 }, {
			res: res:substring(start: 0, end: ofIdx);
		});
		if({ res:contains(needle: ':') && !:clsQNameMap:has(key: res) }, {
			local Int is cIdx: res:indexOf(search: ':', default: -1);
			if({ cIdx > 0 }, {
				local String is cand: res:substring(start: 0, end: cIdx);
				if({ cand == 'Array' || cand == 'Map' || cand == 'List' || :clsQNameMap:has(key: cand) }, {
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
			local ClassInfo is bcls: :resolveBaseClass(cls: cls, bname: bname, clsMap: clsMap);
			if({ bcls:qualifiedName() != cls:qualifiedName() }, {
				:addInheritedFields(st: st, cls: bcls, clsMap: clsMap, seenFields: seenFields);
			});
			bi++;
		});
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:FIELD && m:name != 'using' && m:name != 'namespace' && !m:hasModifier(kw: Keyword:HELD) && !seenFields:has(key: m:name) }, {
				seenFields:set(key: m:name, value: true);
				local IrType is fty: :irTypeFor(specType: m:memberType:name);
				if({ fty == IrType:Void }, { fty: IrType:Ptr; });
				local Boolean is fIsArc: :isArcSpecType(specType: m:memberType:name);
				local Int is bti: 0;
				while({ bti < cls:typeParams:length() }, {
					if({ cls:typeParams:get(index: bti, default: '') == m:memberType:name }, { fIsArc: false; });
					bti++;
				});
				st:addFieldArc(name: m:name, ty: fty, isArc: fIsArc);
				:fieldSpecTypes:set(key: st:name . ':' . m:name, value: m:memberType:name);
				if({ m:hasInit && :isLazyCallExpr(expr: m:initExpr) }, {
					st:addField(name: '_lazy_state_' . m:name, ty: IrType:I64);
					local String is ownerSname: :cStructName(qname: cls:qualifiedName());
					:lazyFields:set(key: st:name . ':' . m:name, value: ownerSname);
					:lazyFields:set(key: cls:name . ':' . m:name, value: ownerSname);
				});
			});
			mi++;
		});
	}

	local Function is buildVtable(IrStruct is st, ClassInfo is cls, Map of String to ClassInfo is clsMap){
		if({ :bindings:isTransparent(c: cls) || :bindings:isSysinternal(cls: cls) }, { return; });
		if({ st:vtableMethodNames:length() == 0 && :globalVtableNames:length() > 0 }, {
			local Int is gi: 0;
			while({ gi < :globalVtableNames:length() }, {
				st:vtableMethodNames:add(item: :globalVtableNames:get(index: gi, default: ''));
				st:vtableFns:add(item: 'null');
				gi++;
			});
		});
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: :resolveBaseClass(cls: cls, bname: bname, clsMap: clsMap);
			if({ bcls:qualifiedName() != cls:qualifiedName() }, {
				:buildVtable(st: st, cls: bcls, clsMap: clsMap);
			});
			bi++;
		});
		local String is sname: :cStructName(qname: cls:qualifiedName());
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
				:collectAllClasses(cls: m:nestedClass, out: out);
			});
			mi++;
		});
	}

	Function of IrModule is buildProgram(ProgramNode is program, String is entryClass){
		:mod: IrModule:init();
		:mod:entryFunction: entryClass;

		:sysinternalClasses: Map:init();
		local Array of ClassInfo is allClasses: [];
		local Int is pci: 0;
		while({ pci < program:classes:length() }, {
			local ClassInfo is pc0: program:classes:get(index: pci);
			if({ :bindings:isSysinternal(cls: pc0) && !:hasMethodBodies(cls: pc0) }, {
				:sysinternalClasses:set(key: pc0:name, value: pc0);
			});
			if({ !:isStdlibClass(cls: pc0) }, {
				:collectAllClasses(cls: pc0, out: allClasses);
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
		:clsMap: clsMap;
		:clsQNameMap: clsQNameMap;
		:methodParamPtrMask: Map:init();
		:methodRetIsPtr: Map:init();
		:methodRetTypes: Map:init();
		:methodParams: Map:init();
		:heldFields: Map:init();
		:heldFieldTypes: Map:init();
		:lazyFields: Map:init();
		:heldMethods: Map:init();
		:globalVtableNames: [];
		:globalVtableMap: Map:init();

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
						if({ !:globalVtableMap:has(key: vk) }, {
							:globalVtableMap:set(key: vk, value: :globalVtableNames:length());
							:globalVtableNames:add(item: vk);
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
			local String is sname: :cStructName(qname: cls:qualifiedName());
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
				:addInheritedFields(st: st, cls: cls, clsMap: clsMap, seenFields: seenFields);
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
							if({ :irTypeFor(specType: mp:paramType:name) == IrType:Ptr }, {
								mask: mask . '1';
							}, {
								mask: mask . '0';
							});
							mpi++;
						});
						:methodParamPtrMask:set(key: mSym, value: mask);
						:methodParams:set(key: mSym, value: mm:params);
						local IrType is mRetTy: :methodReturnType(mt: mm:memberType);
						:methodRetTypes:set(key: mSym, value: mRetTy);
						if({ mRetTy == IrType:Ptr }, {
							:methodRetIsPtr:set(key: mSym, value: true);
						});
					});
					mmi++;
				});
				:buildVtable(st: st, cls: cls, clsMap: clsMap);
				:registerClassMetaAndHeld(st: st, cls: cls, sname: sname);
				:mod:addStruct(s: st);
			});
			ci++;
		});

		# 1b. Inherit held fields from ancestor classes onto subclass prefixes
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			local String is sname: :cStructName(qname: cls:qualifiedName());
			local Map of String to Boolean is hvis: Map:init();
			hvis:set(key: cls:qualifiedName(), value: true);
			:inheritHeldFromAncestors(cls: cls, cur: cls, sname: sname, clsMap: clsMap, hvis: hvis);
			ci++;
		});

		# 2. Lower methods, construct helpers, and held field __ensure accessors
		:computeCanUnwind(allClasses: allClasses);
		local Map of String to Boolean is seenFns: Map:init();
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			local Boolean is isTransCls: :bindings:isTransparent(c: cls);
			local Boolean is isSysCls: :bindings:isSysinternal(cls: cls);
			:isUnmanagedClass: isSysCls;
			local String is sname: :cStructName(qname: cls:qualifiedName());
			:currentClass: sname;
			:curClassTypeParams: Map:init();
			local Int is tpi: 0;
			while({ tpi < cls:typeParams:length() }, {
				:curClassTypeParams:set(key: cls:typeParams:get(index: tpi, default: ''), value: true);
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
						:buildHeldEnsure(sname: sname, m: m);
					});
				});
				if({ m:kind == MemberKind:FIELD && !m:hasModifier(kw: Keyword:HELD) && m:hasInit && :isLazyCallExpr(expr: m:initExpr) }, {
					local String is lazyFn: sname . '_' . m:name . '__lazy_init';
					if({ !seenFns:has(key: lazyFn) }, {
						seenFns:set(key: lazyFn, value: true);
						:buildLazyFieldEnsure(cls: cls, sname: sname, m: m);
					});
				});
				if({ m:kind == MemberKind:METHOD }, {
					local Int is ovIdx: mCounts2:get(key: m:name, default: 0);
					mCounts2:set(key: m:name, value: ovIdx + 1);
					local String is fnName: if({ ovIdx > 0 }, { sname . '_' . m:name . '_' . ((ovIdx + 1) as String) }, { sname . '_' . m:name });
					if({ (!isTransCls || m:body:length() > 0) && !seenFns:has(key: fnName) }, {
						seenFns:set(key: fnName, value: true);
						:buildMethod(cls: cls, m: m, fnName: fnName);
					});
				});
				mi++;
			});
			if({ !isTransCls && !isSysCls }, {
				local String is initFnName: sname . '_init';
				if({ !seenFns:has(key: initFnName) }, {
					seenFns:set(key: initFnName, value: true);
					:buildDefaultInit(cls: cls, sname: sname, initFn: initFnName);
				});
			});
			local IrStruct is st2: :mod:findStruct(name: sname);
			if({ st2:destroyFn != 'null' && !seenFns:has(key: st2:destroyFn) }, {
				seenFns:set(key: st2:destroyFn, value: true);
				:buildDestroyHelper(st: st2, cls: cls, sname: sname, destroyFn: st2:destroyFn);
			});
			if({ st2:constructFn != 'null' && !seenFns:has(key: st2:constructFn) }, {
				seenFns:set(key: st2:constructFn, value: true);
				:buildConstructHelper(cls: cls, sname: sname, ctorFn: st2:constructFn);
			});
			ci++;
		});
		:isUnmanagedClass: false;
		:currentClass: '';
		:currentMethod: '';

		# 3. Emit held resolvers, RTTI hierarchy helpers, and main()
		:buildHeldResolvers();
		:buildRttiHelpers(allClasses: allClasses);
		if({ entryClass != '' }, {
			:buildMainEntry(entryClass: entryClass);
		});

		return :mod;
	}

	local Function is inheritHeldFromAncestors(ClassInfo is cls, ClassInfo is cur, String is sname, Map of String to ClassInfo is clsMap, Map of String to Boolean is hvis){
		local Int is bi: 0;
		while({ bi < cur:baseClasses:length() }, {
			local String is bname: cur:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: :resolveBaseClass(cls: cur, bname: bname, clsMap: clsMap);
			if({ bcls:name != '' && !hvis:has(key: bcls:qualifiedName()) }, {
				hvis:set(key: bcls:qualifiedName(), value: true);
				local String is bsname: :cStructName(qname: bcls:qualifiedName());
				local Int is bmi: 0;
				while({ bmi < bcls:members:length() }, {
					local Member is bm: bcls:members:get(index: bmi);
					if({ bm:kind == MemberKind:FIELD && bm:hasModifier(kw: Keyword:HELD) }, {
						local String is hkS: sname . ':' . bm:name;
						if({ !:heldFields:has(key: hkS) }, {
							local String is owner: :heldFields:get(key: bsname . ':' . bm:name, default: bsname);
							:heldFields:set(key: hkS, value: owner);
							:heldFields:set(key: cls:name . ':' . bm:name, value: owner);
						});
					});
					bmi++;
				});
				:inheritHeldFromAncestors(cls: cls, cur: bcls, sname: sname, clsMap: clsMap, hvis: hvis);
			});
			bi++;
		});
	}

	local Function is emitPoolEnter(){
		if({ :isUnmanagedClass || (:currentClass == 'Vector' && :currentMethod != 'mapKeys') }, {
			:curPoolMark: '';
			return;
		});
		local String is mark: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: mark, hasDst: true, retType: IrType:I64, callee: 'spec_pool_frame', argTypes: [], args: []));
		:curPoolMark: mark;
	}

	local Function is emitPoolExit(){
		if({ :curPoolMark != '' }, {
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_pool_release_to', argTypes: [IrType:I64], args: [:curPoolMark]));
		});
	}

	Function is emitClaimPool(String is val){
		if({ !:isUnmanagedClass && val != '' && val != 'null' }, {
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Ptr, callee: 'spec_claim_pool', argTypes: [IrType:Ptr], args: [val]));
		});
	}

	local Function of String is destroyFnFor(String is structName){
		local IrStruct is st: :mod:findStruct(name: structName);
		if({ st:name != '' && st:destroyFn != 'null' }, {
			return '@' . st:destroyFn;
		});
		return 'null';
	}

	local Function is buildDestroyHelper(IrStruct is st, ClassInfo is cls, String is sname, String is destroyFn){
		local IrFunction is fn: IrFunction:init(name: destroyFn, retType: IrType:Void);
		fn:addParam(name: '%self', ty: IrType:Ptr);
		local IrBlock is entry: fn:addBlock(label: 'entry');
		:curFn: fn;
		:switchBlock(blk: entry);
		:tmpCounter: 0;
		:curPoolMark: '';
		local Int is dmi: 0;
		while({ dmi < cls:members:length() }, {
			local Member is dm: cls:members:get(index: dmi);
			if({ dm:kind == MemberKind:METHOD && dm:name == 'destroy' && dm:params:length() == 0 }, {
				:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: sname . '_destroy', argTypes: [IrType:Ptr], args: ['%self']));
			});
			dmi++;
		});
		local Int is fi: 2;
		while({ fi < st:fieldTypes:length() }, {
			if({ st:fieldIsArc:get(index: fi, default: false) }, {
				local String is fptr: :nextTmp();
				:emit(inst: IrInst:FieldPtr(dst: fptr, objPtr: '%self', structName: st:name, fieldIndex: fi));
				local String is fval: :nextTmp();
				:emit(inst: IrInst:Load(dst: fval, slot: fptr, ty: IrType:Ptr));
				:emit(inst: IrInst:Release(val: fval));
				:emit(inst: IrInst:Store(slot: fptr, val: 'null', ty: IrType:Ptr));
			});
			fi++;
		});
		:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
		:mod:addFunction(fn: fn);
	}

	local Function is buildMainEntry(String is entryClass){
		local IrFunction is mainFn: IrFunction:init(name: 'main', retType: IrType:I64);
		mainFn:addParam(name: '%argc', ty: IrType:I64);
		mainFn:addParam(name: '%argv', ty: IrType:Ptr);
		local IrBlock is entry: mainFn:addBlock(label: 'entry');
		:curFn: mainFn;
		:switchBlock(blk: entry);
		:tmpCounter: 0;
		:emitPoolEnter();

		local String is argsMap: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: argsMap, hasDst: true, retType: IrType:Ptr, callee: 'spec_cli_args_map', argTypes: [IrType:I64, IrType:Ptr], args: ['%argc', '%argv']));

		# Allocate entry object and call the resolved entry init
		local String is obj: :nextTmp();
		:emit(inst: IrInst:AllocObj(dst: obj, structName: entryClass, destroyFn: :destroyFnFor(structName: entryClass)));
		local String is initOwner: entryClass;
		if({ :entryInitOwner != '' }, {
			initOwner: :cStructName(qname: :clsQNameMap:get(key: :entryInitOwner, default: :entryInitOwner));
		});
		local String is initSuf: if({ :entryInitOverloadIndex > 0 }, { '_' . ((:entryInitOverloadIndex + 1) as String) }, { '' });
		if({ :entryInitTakesMap }, {
			local Array of IrType is initArgTypes: [IrType:Ptr, IrType:Ptr];
			local Array of String is initArgs: [obj, argsMap];
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: initOwner . '_init' . initSuf, argTypes: initArgTypes, args: initArgs));
		}, {
			local Array of IrType is initArgTypes: [IrType:Ptr];
			local Array of String is initArgs: [obj];
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: initOwner . '_init' . initSuf, argTypes: initArgTypes, args: initArgs));
		});
		:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_drain_async_tasks', argTypes: [], args: []));
		if({ :clsQNameMap:has(key: 'Pool') }, {
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Pool_panicPending', argTypes: [IrType:Ptr], args: ['null']));
		});
		:emitPoolExit();
		:emit(inst: IrInst:Release(val: argsMap));
		:emit(inst: IrInst:Release(val: obj));
		:curPoolMark: '';
		local String is zero: :nextTmp();
		:emit(inst: IrInst:ConstInt(dst: zero, value: 0));
		:terminate(inst: IrInst:Ret(hasVal: true, val: zero, ty: IrType:I64));
		:mod:addFunction(fn: mainFn);
	}

	local Function is collectAncestors(ClassInfo is cls, Map of String to Boolean is seen, Array of String is out){
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bn: cls:baseClasses:get(index: bi, default: '');
			if({ bn != '' && !seen:has(key: bn) }, {
				seen:set(key: bn, value: true);
				out:add(item: bn);
				if({ :clsMap:has(key: bn) }, {
					local ClassInfo is bcls: :clsMap:get(key: bn, default: cls);
					:collectAncestors(cls: bcls, seen: seen, out: out);
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
		:curFn: subFn;
		:switchBlock(blk: entry);
		:tmpCounter: 0;
		:lblCounter: 0;
		:curPoolMark: '';

		local String is aNull: :nextTmp();
		:emit(inst: IrInst:Cmp(dst: aNull, op: '==', lhs: '%actual', rhs: 'null', ty: IrType:Ptr));
		local String is tNull: :nextTmp();
		:emit(inst: IrInst:Cmp(dst: tNull, op: '==', lhs: '%target', rhs: 'null', ty: IrType:Ptr));
		local String is eitherNull: :nextTmp();
		:emit(inst: IrInst:BinOp(dst: eitherNull, op: '|', lhs: aNull, rhs: tNull, ty: IrType:I1));
		local String is retFalseLbl: :nextLabel(prefix: 'rtti_false');
		local String is nonNullLbl: :nextLabel(prefix: 'rtti_nn');
		:terminate(inst: IrInst:CondBr(cond: eitherNull, thenLabel: retFalseLbl, elseLabel: nonNullLbl));

		local IrBlock is nnBlk: subFn:addBlock(label: nonNullLbl);
		:switchBlock(blk: nnBlk);
		local String is retTrueLbl: :nextLabel(prefix: 'rtti_true');
		local String is eqSelf: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: eqSelf, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%actual', '%target']));
		local String is chkAnyLbl: :nextLabel(prefix: 'rtti_any');
		:terminate(inst: IrInst:CondBr(cond: eqSelf, thenLabel: retTrueLbl, elseLabel: chkAnyLbl));

		local IrBlock is anyBlk: subFn:addBlock(label: chkAnyLbl);
		:switchBlock(blk: anyBlk);
		local Int is anyStrId: :mod:internStringLiteral(value: 'Any');
		local String is anyPtr: :nextTmp();
		:emit(inst: IrInst:GlobalAddr(dst: anyPtr, globalName: '.str.' . (anyStrId as String)));
		local String is eqAny: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: eqAny, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%target', anyPtr]));
		local String is chkStrLbl: :nextLabel(prefix: 'rtti_str');
		:terminate(inst: IrInst:CondBr(cond: eqAny, thenLabel: retTrueLbl, elseLabel: chkStrLbl));

		local IrBlock is strBlk: subFn:addBlock(label: chkStrLbl);
		:switchBlock(blk: strBlk);
		local Int is strStrId: :mod:internStringLiteral(value: 'Stringable');
		local String is strPtr: :nextTmp();
		:emit(inst: IrInst:GlobalAddr(dst: strPtr, globalName: '.str.' . (strStrId as String)));
		local String is eqStr: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: eqStr, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%target', strPtr]));
		local String is nextChkLbl: :nextLabel(prefix: 'rtti_cls');
		:terminate(inst: IrInst:CondBr(cond: eqStr, thenLabel: retTrueLbl, elseLabel: nextChkLbl));

		local IrBlock is curChkBlk: subFn:addBlock(label: nextChkLbl);
		:switchBlock(blk: curChkBlk);
		local Int is ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			if({ !:isStdlibClass(cls: cls) || cls:baseClasses:length() > 0 }, {
				local Array of String is ancs: [];
				:collectAncestors(cls: cls, seen: Map:init(), out: ancs);
				if({ ancs:length() > 0 }, {
					local Int is qnId: :mod:internStringLiteral(value: cls:qualifiedName());
					local String is qnPtr: :nextTmp();
					:emit(inst: IrInst:GlobalAddr(dst: qnPtr, globalName: '.str.' . (qnId as String)));
					local String is eqCls: :nextTmp();
					:emit(inst: IrInst:IrCall(dst: eqCls, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%actual', qnPtr]));
					local String is matchClsLbl: :nextLabel(prefix: 'rtti_m');
					local String is skipClsLbl: :nextLabel(prefix: 'rtti_n');
					:terminate(inst: IrInst:CondBr(cond: eqCls, thenLabel: matchClsLbl, elseLabel: skipClsLbl));

					local IrBlock is mBlk: subFn:addBlock(label: matchClsLbl);
					:switchBlock(blk: mBlk);
					local Int is ai: 0;
					while({ ai < ancs:length() }, {
						local String is aname: ancs:get(index: ai, default: '');
						local Int is aId: :mod:internStringLiteral(value: aname);
						local String is aPtr: :nextTmp();
						:emit(inst: IrInst:GlobalAddr(dst: aPtr, globalName: '.str.' . (aId as String)));
						local String is eqAnc: :nextTmp();
						:emit(inst: IrInst:IrCall(dst: eqAnc, hasDst: true, retType: IrType:I1, callee: '__spec_cstr_eq', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%target', aPtr]));
						local String is nextAncLbl: :nextLabel(prefix: 'rtti_a');
						:terminate(inst: IrInst:CondBr(cond: eqAnc, thenLabel: retTrueLbl, elseLabel: nextAncLbl));
						local IrBlock is aBlk: subFn:addBlock(label: nextAncLbl);
						:switchBlock(blk: aBlk);
						ai++;
					});
					:terminate(inst: IrInst:Br(target: retFalseLbl));

					curChkBlk: subFn:addBlock(label: skipClsLbl);
					:switchBlock(blk: curChkBlk);
				});
			});
			ci++;
		});
		:terminate(inst: IrInst:Br(target: retFalseLbl));

		local IrBlock is trueBlk: subFn:addBlock(label: retTrueLbl);
		:switchBlock(blk: trueBlk);
		local String is tVal: :nextTmp();
		:emit(inst: IrInst:ConstBool(dst: tVal, value: true));
		:terminate(inst: IrInst:Ret(hasVal: true, val: tVal, ty: IrType:I1));

		local IrBlock is falseBlk: subFn:addBlock(label: retFalseLbl);
		:switchBlock(blk: falseBlk);
		local String is fVal: :nextTmp();
		:emit(inst: IrInst:ConstBool(dst: fVal, value: false));
		:terminate(inst: IrInst:Ret(hasVal: true, val: fVal, ty: IrType:I1));
		:mod:addFunction(fn: subFn);

		# spec_cast_check(ptr %obj, ptr %target) -> ptr
		local IrFunction is ccFn: IrFunction:init(name: 'spec_cast_check', retType: IrType:Ptr);
		ccFn:addParam(name: '%obj', ty: IrType:Ptr);
		ccFn:addParam(name: '%target', ty: IrType:Ptr);
		local IrBlock is ccEntry: ccFn:addBlock(label: 'entry');
		:curFn: ccFn;
		:switchBlock(blk: ccEntry);
		:tmpCounter: 0;
		:lblCounter: 0;
		local String is isNull: :nextTmp();
		:emit(inst: IrInst:Cmp(dst: isNull, op: '==', lhs: '%obj', rhs: 'null', ty: IrType:Ptr));
		local String is ccNullLbl: :nextLabel(prefix: 'cc_null');
		local String is ccChkLbl: :nextLabel(prefix: 'cc_chk');
		:terminate(inst: IrInst:CondBr(cond: isNull, thenLabel: ccNullLbl, elseLabel: ccChkLbl));

		local IrBlock is ccNullBlk: ccFn:addBlock(label: ccNullLbl);
		:switchBlock(blk: ccNullBlk);
		:terminate(inst: IrInst:Ret(hasVal: true, val: 'null', ty: IrType:Ptr));

		local IrBlock is ccChkBlk: ccFn:addBlock(label: ccChkLbl);
		:switchBlock(blk: ccChkBlk);
		local String is actualType: :nextTmp();
		:emit(inst: IrInst:Load(dst: actualType, slot: '%obj', ty: IrType:Ptr));
		local String is ok: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: ok, hasDst: true, retType: IrType:I1, callee: 'spec_is_subclass_of', argTypes: [IrType:Ptr, IrType:Ptr], args: [actualType, '%target']));
		local String is ccOkLbl: :nextLabel(prefix: 'cc_ok');
		local String is ccFailLbl: :nextLabel(prefix: 'cc_fail');
		:terminate(inst: IrInst:CondBr(cond: ok, thenLabel: ccOkLbl, elseLabel: ccFailLbl));

		local IrBlock is ccFailBlk: ccFn:addBlock(label: ccFailLbl);
		:switchBlock(blk: ccFailBlk);
		:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_panic_cast', argTypes: [IrType:Ptr, IrType:Ptr], args: [actualType, '%target']));
		:terminate(inst: IrInst:Ret(hasVal: true, val: '%obj', ty: IrType:Ptr));

		local IrBlock is ccOkBlk: ccFn:addBlock(label: ccOkLbl);
		:switchBlock(blk: ccOkBlk);
		:terminate(inst: IrInst:Ret(hasVal: true, val: '%obj', ty: IrType:Ptr));
		:mod:addFunction(fn: ccFn);
	}

	Function of String is methodReturnSpecType(Type is mt){
		if({ mt:name == 'Function' }, {
			if({ mt:params:length() > 0 }, {
				local Type is rt: mt:params:get(index: 0);
				return rt:name;
			});
			return 'Void';
		});
		return mt:name;
	}

	Function of IrType is methodReturnType(Type is mt){
		if({ mt:name == 'Function' }, {
			if({ mt:params:length() > 0 }, {
				local Type is rt: mt:params:get(index: 0);
				return :irTypeFor(specType: rt:name);
			});
			return IrType:Void;
		});
		return :irTypeFor(specType: mt:name);
	}

	local Function is emitFieldDefaults(ClassInfo is cls, Map of String to Boolean is seen){
		local String is clsKey: '@cls:' . cls:qualifiedName();
		if({ seen:has(key: clsKey) }, { return; });
		seen:set(key: clsKey, value: true);
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local Boolean is isEnclosing: cls:outerName != '' && (cls:outerName == bname || cls:outerName:endsWith(suffix: ':' . bname));
			if({ :clsMap:has(key: bname) }, {
				local ClassInfo is bcls: :clsMap:get(key: bname, default: cls);
				local Boolean is bIsEnum: false;
				local Int is ebi: 0;
				while({ ebi < bcls:baseClasses:length() }, {
					if({ bcls:baseClasses:get(index: ebi, default: '') == 'Enum' }, { bIsEnum: true; });
					ebi++;
				});
				if({ !isEnclosing || bIsEnum }, {
					:emitFieldDefaults(cls: bcls, seen: seen);
				});
			});
			bi++;
		});
		local IrStruct is st: :mod:findStruct(name: :currentClass);
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:FIELD && m:name != 'using' && m:name != 'namespace' && !m:hasModifier(kw: Keyword:HELD) && m:hasInit && !:isLazyCallExpr(expr: m:initExpr) }, {
				local Int is fidx: st:fieldIndex(name: m:name);
				if({ fidx >= 0 }, {
					local IrType is fty: st:fieldTypes:get(index: fidx);
					local String is ptr: :nextTmp();
					:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: '%self', structName: :currentClass, fieldIndex: fidx));
					local String is prevMapK: :expectedMapKeyType;
					local String is prevMapV: :expectedMapValType;
					if({ m:memberType:name == 'Map' && m:memberType:params:length() >= 1 }, {
						local Type is mkp0: m:memberType:params:get(index: 0);
						:expectedMapKeyType: mkp0:name;
						if({ m:memberType:params:length() >= 2 }, {
							local Type is mkp1: m:memberType:params:get(index: 1);
							:expectedMapValType: mkp1:name;
						});
					});
					local String is val: :lowerExpr(expr: m:initExpr);
					:expectedMapKeyType: prevMapK;
					:expectedMapValType: prevMapV;
					local IrType is vty: :irTypeFor(specType: m:initExpr:resolvedType);
					val: :castIfNeeded(val: val, fromTy: vty, toTy: fty);
					if({ st:fieldIsArc:get(index: fidx, default: false) }, {
						if({ val != '' && val != 'null' }, {
							:emit(inst: IrInst:Retain(val: val));
						});
						if({ seen:has(key: m:name) }, {
							local String is oldF: :nextTmp();
							:emit(inst: IrInst:Load(dst: oldF, slot: ptr, ty: IrType:Ptr));
							:emit(inst: IrInst:Release(val: oldF));
						});
					});
					seen:set(key: m:name, value: true);
					:emit(inst: IrInst:Store(slot: ptr, val: val, ty: fty));
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
				local IrType is hty: :irTypeFor(specType: m:memberType:name);
				if({ hty == IrType:Void }, { hty: IrType:Ptr; });
				local String is valGlob: '.held_val.' . sname . '.' . m:name;
				local String is initGlob: '.held_init.' . sname . '.' . m:name;
				:mod:addGlobal(name: valGlob, ty: hty, initVal: 'zeroinitializer');
				:mod:addGlobal(name: initGlob, ty: IrType:I1, initVal: 'false');
				:heldFields:set(key: sname . ':' . m:name, value: sname);
				:heldFields:set(key: cls:name . ':' . m:name, value: sname);
				:heldFieldTypes:set(key: sname . ':' . m:name, value: m:memberType:name);
				st:heldNames:add(item: m:name);
				st:heldGetters:add(item: sname . '_' . m:name . '__ensure');
			});
			if({ m:kind == MemberKind:METHOD }, {
				if({ m:hasModifier(kw: Keyword:HELD) }, {
					:heldMethods:set(key: sname . '_' . m:name, value: true);
					if({ m:name == 'resolveHeld' }, {
						:heldResolvers:set(key: sname, value: sname);
						:heldResolvers:set(key: cls:name, value: sname);
						:heldResolverRetTypes:set(key: sname, value: :methodReturnSpecType(mt: m:memberType));
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
					if({ :bindings:isTransparent(c: cls) && m:body:length() == 0 }, {
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
		if({ (!hasInitMember || hasZeroArgInit) && !:bindings:isTransparent(c: cls) && !:bindings:isSysinternal(cls: cls) && cls:baseClass != 'Enum' }, {
			st:constructFn: sname . '__spec_construct';
		});
	}

	local Function is buildConstructHelper(ClassInfo is cls, String is sname, String is ctorFn){
		local IrFunction is fn: IrFunction:init(name: ctorFn, retType: IrType:Ptr);
		local IrBlock is entry: fn:addBlock(label: 'entry');
		:curFn: fn;
		:switchBlock(blk: entry);
		:tmpCounter: 0;
		local String is obj: :nextTmp();
		:emit(inst: IrInst:AllocObj(dst: obj, structName: sname, destroyFn: :destroyFnFor(structName: sname)));
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
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: sname . '_init', argTypes: [IrType:Ptr], args: [obj]));
		});
		:terminate(inst: IrInst:Ret(hasVal: true, val: obj, ty: IrType:Ptr));
		:mod:addFunction(fn: fn);
	}

	local Function is buildDefaultInit(ClassInfo is cls, String is sname, String is initFn){
		local IrFunction is fn: IrFunction:init(name: initFn, retType: IrType:Void);
		fn:addParam(name: '%self', ty: IrType:Ptr);
		local IrBlock is entry: fn:addBlock(label: 'entry');
		:curFn: fn;
		:switchBlock(blk: entry);
		:tmpCounter: 0;
		:localSlots: Map:init();
		:localTypes: Map:init();
		:localIsArc: Map:init();
		:localSpecTypes: Map:init();
		:boxedLocals: Map:init();
		:capturedNames: Map:init();
		:ownedSlots: [];
		:curPoolMark: '';
		:emitFieldDefaults(cls: cls, seen: Map:init());
		:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
		:mod:addFunction(fn: fn);
	}

	local Function is buildHeldEnsure(String is sname, Member is m){
		local IrType is hty: :irTypeFor(specType: m:memberType:name);
		if({ hty == IrType:Void }, { hty: IrType:Ptr; });
		local String is fnName: sname . '_' . m:name . '__ensure';
		local IrFunction is fn: IrFunction:init(name: fnName, retType: hty);
		local IrBlock is entry: fn:addBlock(label: 'entry');
		:curFn: fn;
		:switchBlock(blk: entry);
		:tmpCounter: 0;
		:lblCounter: 0;
		:localSlots: Map:init();
		:localTypes: Map:init();
		:localIsArc: Map:init();
		:localSpecTypes: Map:init();
		:boxedLocals: Map:init();
		:capturedNames: Map:init();
		:ownedSlots: [];
		:curFnRetIsArc: :isArcSpecType(specType: :methodReturnSpecType(mt: m:memberType));
		:emitPoolEnter();

		local String is valGlob: '@.held_val.' . sname . '.' . m:name;
		local String is initGlob: '@.held_init.' . sname . '.' . m:name;
		local String is isInit: :nextTmp();
		:emit(inst: IrInst:Load(dst: isInit, slot: initGlob, ty: IrType:I1));

		local String is initLbl: :nextLabel(prefix: 'held_init');
		local String is doneLbl: :nextLabel(prefix: 'held_done');
		:terminate(inst: IrInst:CondBr(cond: isInit, thenLabel: doneLbl, elseLabel: initLbl));

		local IrBlock is initBlk: fn:addBlock(label: initLbl);
		:switchBlock(blk: initBlk);
		local String is trueTmp: :nextTmp();
		:emit(inst: IrInst:ConstBool(dst: trueTmp, value: true));
		:emit(inst: IrInst:Store(slot: initGlob, val: trueTmp, ty: IrType:I1));
		if({ m:hasInit }, {
			local String is prevMapK: :expectedMapKeyType;
			local String is prevMapV: :expectedMapValType;
			if({ m:memberType:name == 'Map' && m:memberType:params:length() >= 1 }, {
				local Type is kp: m:memberType:params:get(index: 0);
				:expectedMapKeyType: kp:name;
				if({ m:memberType:params:length() >= 2 }, {
					local Type is vp: m:memberType:params:get(index: 1);
					:expectedMapValType: vp:name;
				});
			});
			local String is iv: :lowerExpr(expr: m:initExpr);
			:expectedMapKeyType: prevMapK;
			:expectedMapValType: prevMapV;
			if({ iv == '' }, { iv: :emitDefaultVal(ty: hty); });
			if({ hty == IrType:Ptr && iv != 'null' }, {
				:emit(inst: IrInst:Retain(val: iv));
			});
			:emit(inst: IrInst:Store(slot: valGlob, val: iv, ty: hty));
		});
		:terminate(inst: IrInst:Br(target: doneLbl));

		local IrBlock is doneBlk: fn:addBlock(label: doneLbl);
		:switchBlock(blk: doneBlk);
		local String is res: :nextTmp();
		:emit(inst: IrInst:Load(dst: res, slot: valGlob, ty: hty));
		if({ hty == IrType:Ptr }, {
			:emit(inst: IrInst:Retain(val: res));
		});
		:emitPoolExit();
		:curPoolMark: '';
		:terminate(inst: IrInst:Ret(hasVal: true, val: res, ty: hty));
		:mod:addFunction(fn: fn);
	}

	local Function is buildLazyFieldEnsure(ClassInfo is cls, String is sname, Member is m){
		local IrStruct is st: :mod:findStruct(name: sname);
		local Int is valIdx: st:fieldIndex(name: m:name);
		local Int is stateIdx: st:fieldIndex(name: '_lazy_state_' . m:name);
		if({ valIdx < 0 || stateIdx < 0 }, { return; });
		local IrType is fty: st:fieldTypes:get(index: valIdx);
		local Boolean is fIsArc: st:fieldIsArc:get(index: valIdx, default: false);
		local String is fnName: sname . '_' . m:name . '__lazy_init';
		local IrFunction is fn: IrFunction:init(name: fnName, retType: fty);
		fn:sourceFile: cls:sourceFile;
		fn:line: m:line;
		:currentLine: m:line;
		:currentMethod: m:name . '__lazy_init';
		fn:addParam(name: '%self', ty: IrType:Ptr);

		local IrBlock is entry: fn:addBlock(label: 'entry');
		:curFn: fn;
		:switchBlock(blk: entry);
		:tmpCounter: 0;
		:lblCounter: 0;
		:localSlots: Map:init();
		:localTypes: Map:init();
		:localIsArc: Map:init();
		:localSpecTypes: Map:init();
		:boxedLocals: Map:init();
		:capturedNames: Map:init();
		:ownedSlots: [];
		:resetScopes();

		local Map of String to Boolean is decls: Map:init();
		:collectDeclNamesInExpr(expr: m:initExpr, decls: decls);
		:collectAllAnonCapturesInExpr(expr: m:initExpr, decls: decls, out: :capturedNames);
		:curFnRetIsArc: false;
		:emitPoolEnter();

		:localSlots:set(key: ':', value: '%self_slot');
		:localTypes:set(key: ':', value: IrType:Ptr);
		:localIsArc:set(key: ':', value: !:isUnmanagedClass);
		:localSpecTypes:set(key: ':', value: sname);
		:emit(inst: IrInst:Alloca(slot: '%self_slot', ty: IrType:Ptr));
		:emit(inst: IrInst:Store(slot: '%self_slot', val: '%self', ty: IrType:Ptr));

		local String is valPtr: :nextTmp();
		:emit(inst: IrInst:FieldPtr(dst: valPtr, objPtr: '%self', structName: sname, fieldIndex: valIdx));
		local String is statePtr: :nextTmp();
		:emit(inst: IrInst:FieldPtr(dst: statePtr, objPtr: '%self', structName: sname, fieldIndex: stateIdx));
		local String is stateAddr: :nextTmp();
		:emit(inst: IrInst:IrCast(dst: stateAddr, val: statePtr, fromType: IrType:Ptr, toType: IrType:I64));

		local String is zeroVal: :nextTmp();
		:emit(inst: IrInst:ConstInt(dst: zeroVal, value: 0));
		local String is oneVal: :nextTmp();
		:emit(inst: IrInst:ConstInt(dst: oneVal, value: 1));
		local String is twoVal: :nextTmp();
		:emit(inst: IrInst:ConstInt(dst: twoVal, value: 2));

		local String is wonCas: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: wonCas, hasDst: true, retType: IrType:I1, callee: '__spec_mem_atomic_cas_i64', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [stateAddr, zeroVal, oneVal]));

		local String is evalLbl: :nextLabel(prefix: 'lazy_eval');
		local String is waitLbl: :nextLabel(prefix: 'lazy_wait');
		local String is doneLbl: :nextLabel(prefix: 'lazy_done');
		:terminate(inst: IrInst:CondBr(cond: wonCas, thenLabel: evalLbl, elseLabel: waitLbl));

		local IrBlock is evalBlk: fn:addBlock(label: evalLbl);
		:switchBlock(blk: evalBlk);
		local String is prevMapK: :expectedMapKeyType;
		local String is prevMapV: :expectedMapValType;
		if({ m:memberType:name == 'Map' && m:memberType:params:length() >= 1 }, {
			local Type is mkp0: m:memberType:params:get(index: 0);
			:expectedMapKeyType: mkp0:name;
			if({ m:memberType:params:length() >= 2 }, {
				local Type is mkp1: m:memberType:params:get(index: 1);
				:expectedMapValType: mkp1:name;
			});
		});
		local String is iv: :lowerLazyBodyVal(blkExpr: :getLazyBodyExpr(expr: m:initExpr), expectedTy: fty);
		:expectedMapKeyType: prevMapK;
		:expectedMapValType: prevMapV;
		if({ iv == '' }, { iv: :emitDefaultVal(ty: fty); });
		if({ fIsArc && iv != '' && iv != 'null' }, {
			:emit(inst: IrInst:Retain(val: iv));
		});
		:emit(inst: IrInst:Store(slot: valPtr, val: iv, ty: fty));
		:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: '__spec_mem_atomic_store_i64', argTypes: [IrType:I64, IrType:I64], args: [stateAddr, twoVal]));
		:terminate(inst: IrInst:Br(target: doneLbl));

		local IrBlock is waitBlk: fn:addBlock(label: waitLbl);
		:switchBlock(blk: waitBlk);
		local String is curState: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: curState, hasDst: true, retType: IrType:I64, callee: '__spec_mem_atomic_load_i64', argTypes: [IrType:I64], args: [stateAddr]));
		local String is isDone: :nextTmp();
		:emit(inst: IrInst:Cmp(dst: isDone, op: '==', lhs: curState, rhs: twoVal, ty: IrType:I64));
		:terminate(inst: IrInst:CondBr(cond: isDone, thenLabel: doneLbl, elseLabel: waitLbl));

		local IrBlock is doneBlk: fn:addBlock(label: doneLbl);
		:switchBlock(blk: doneBlk);
		local String is res: :nextTmp();
		:emit(inst: IrInst:Load(dst: res, slot: valPtr, ty: fty));
		:emitReleaseOwnedLocals();
		:emitPoolExit();
		:curPoolMark: '';
		:terminate(inst: IrInst:Ret(hasVal: true, val: res, ty: fty));
		:mod:addFunction(fn: fn);
	}

	local Function of String is findParentMethodImpl(String is clsName, String is methodName, String is suffix){
		if({ !:clsMap:has(key: clsName) }, { return ''; });
		local ClassInfo is cls: :clsMap:get(key: clsName, default: ClassInfo:init(name: '', baseClass: '', members: []));
		local String is found: '';
		local Int is bi: 0;
		while({ found == '' && bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: :resolveBaseClass(cls: cls, bname: bname, clsMap: :clsMap);
			if({ bcls:qualifiedName() != cls:qualifiedName() }, {
				local Int is mi: 0;
				while({ found == '' && mi < bcls:members:length() }, {
					local Member is m: bcls:members:get(index: mi);
					if({ m:kind == MemberKind:METHOD && m:name == methodName && !m:hasModifier(kw: Keyword:HELD) }, {
						found: :cStructName(qname: bcls:qualifiedName()) . '_' . methodName . suffix;
					});
					mi++;
				});
				if({ found == '' }, {
					found: :findParentMethodImpl(clsName: bcls:qualifiedName(), methodName: methodName, suffix: suffix);
				});
			});
			bi++;
		});
		return found;
	}

	local Function of String is findHeldResolver(String is clsName){
		local String is qn: '' . clsName;
		if({ :clsQNameMap:has(key: clsName) }, {
			qn: :clsQNameMap:get(key: clsName, default: '');
		});
		local String is sn: :cStructName(qname: qn);
		if({ :heldResolvers:has(key: sn) }, {
			return :heldResolvers:get(key: sn, default: '');
		});
		if({ !:clsMap:has(key: qn) }, { return ''; });
		local ClassInfo is cls: :clsMap:get(key: qn, default: ClassInfo:init(name: '', baseClass: '', members: []));
		local String is found: '';
		local Int is bi: 0;
		while({ found == '' && bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: :resolveBaseClass(cls: cls, bname: bname, clsMap: :clsMap);
			if({ bcls:qualifiedName() != cls:qualifiedName() }, {
				found: :findHeldResolver(clsName: bcls:qualifiedName());
			});
			bi++;
		});
		return found;
	}

	local Function is buildHeldResolvers(){
		local Array of String is rKeys: :heldResolverRetTypes:keys();
		local Int is ri: 0;
		while({ ri < rKeys:length() }, {
			local String is rSym: rKeys:get(index: ri, default: '');
			local String is retSpec: :heldResolverRetTypes:get(key: rSym, default: '');
			local IrType is resTy: :irTypeFor(specType: retSpec);
			if({ resTy == IrType:Void }, { resTy: IrType:Ptr; });
			local Boolean is resArc: :isArcSpecType(specType: retSpec);

			# 1. Missing callback: static void* missing(void* env)
			local IrFunction is missFn: IrFunction:init(name: rSym . '_held_missing_fn', retType: resTy);
			missFn:addParam(name: '%env', ty: IrType:Ptr);
			local IrBlock is mEntry: missFn:addBlock(label: 'entry');
			:curFn: missFn;
			:switchBlock(blk: mEntry);
			:tmpCounter: 0;
			:lblCounter: 0;
			:curPoolMark: '';
			local Int is pPreId: :mod:internStringLiteral(value: "No held member '");
			local String is pPre: :nextTmp();
			:emit(inst: IrInst:ConstString(dst: pPre, strId: pPreId));
			local String is pMid: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: pMid, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [pPre, '%env']));
			local Int is pSufId: :mod:internStringLiteral(value: "' on " . rSym);
			local String is pSuf: :nextTmp();
			:emit(inst: IrInst:ConstString(dst: pSuf, strId: pSufId));
			local String is pMsg: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: pMsg, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [pMid, pSuf]));
			local String is pCstr: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: pCstr, hasDst: true, retType: IrType:Ptr, callee: 'spec_buf_to_cstring', argTypes: [IrType:Ptr], args: [pMsg]));
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_panic', argTypes: [IrType:Ptr], args: [pCstr]));
			local String is mDef: :emitDefaultVal(ty: resTy);
			:terminate(inst: IrInst:Ret(hasVal: true, val: mDef, ty: resTy));
			:mod:addFunction(fn: missFn);

			# 2. Cache global + resolver wrapper: rSym_held_resolve(ptr %p_name)
			local String is cacheGlob: '.held_cache.' . rSym;
			:mod:addGlobal(name: cacheGlob, ty: IrType:Ptr, initVal: 'null');
			local IrFunction is fn: IrFunction:init(name: rSym . '_held_resolve', retType: resTy);
			fn:addParam(name: '%p_name', ty: IrType:Ptr);
			local IrBlock is entry: fn:addBlock(label: 'entry');
			:curFn: fn;
			:switchBlock(blk: entry);
			:tmpCounter: 0;
			:lblCounter: 0;
			:localSlots: Map:init();
			:localTypes: Map:init();
			:localIsArc: Map:init();
			:localSpecTypes: Map:init();
			:boxedLocals: Map:init();
			:capturedNames: Map:init();
			:ownedSlots: [];
			:curFnRetIsArc: resArc;
			:emitPoolEnter();

			local String is cache0: :nextTmp();
			:emit(inst: IrInst:Load(dst: cache0, slot: '@' . cacheGlob, ty: IrType:Ptr));
			local String is needInit: :nextTmp();
			:emit(inst: IrInst:Cmp(dst: needInit, op: '==', lhs: cache0, rhs: 'null', ty: IrType:Ptr));
			local String is mkLbl: :nextLabel(prefix: 'hcache_mk');
			local String is chkLbl: :nextLabel(prefix: 'hcache_chk');
			:terminate(inst: IrInst:CondBr(cond: needInit, thenLabel: mkLbl, elseLabel: chkLbl));

			local IrBlock is mkBlk: fn:addBlock(label: mkLbl);
			:switchBlock(blk: mkBlk);
			local String is kk: :nextTmp();
			:emit(inst: IrInst:ConstInt(dst: kk, value: 0));
			local String is vk: :nextTmp();
			local Int is vkVal: 0;
			if({ resArc }, { vkVal: 1; });
			:emit(inst: IrInst:ConstInt(dst: vk, value: vkVal));
			local String is newMap: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: newMap, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewTyped', argTypes: [IrType:I64, IrType:I64], args: [kk, vk]));
			:emit(inst: IrInst:Store(slot: '@' . cacheGlob, val: newMap, ty: IrType:Ptr));
			:terminate(inst: IrInst:Br(target: chkLbl));

			local IrBlock is chkBlk: fn:addBlock(label: chkLbl);
			:switchBlock(blk: chkBlk);
			local String is cache1: :nextTmp();
			:emit(inst: IrInst:Load(dst: cache1, slot: '@' . cacheGlob, ty: IrType:Ptr));
			local String is hasKey: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: hasKey, hasDst: true, retType: IrType:I1, callee: 'HashTable_mapHas', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', cache1, '%p_name']));
			local String is hitLbl: :nextLabel(prefix: 'hcache_hit');
			local String is missLbl: :nextLabel(prefix: 'hcache_miss');
			:terminate(inst: IrInst:CondBr(cond: hasKey, thenLabel: hitLbl, elseLabel: missLbl));

			local IrBlock is hitBlk: fn:addBlock(label: hitLbl);
			:switchBlock(blk: hitBlk);
			local String is hitRaw: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: hitRaw, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapGet', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', cache1, '%p_name', 'null']));
			local String is hitVal: :castIfNeeded(val: hitRaw, fromTy: IrType:Ptr, toTy: resTy);
			if({ resArc && hitVal != 'null' }, { :emit(inst: IrInst:Retain(val: hitVal)); });
			:emitPoolExit();
			:terminate(inst: IrInst:Ret(hasVal: true, val: hitVal, ty: resTy));

			local IrBlock is missBlk: fn:addBlock(label: missLbl);
			:switchBlock(blk: missBlk);
			local String is missFnPtr: :nextTmp();
			:emit(inst: IrInst:GlobalAddr(dst: missFnPtr, globalName: rSym . '_held_missing_fn'));
			local String is clos: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: clos, hasDst: true, retType: IrType:Ptr, callee: 'spec_rt_closure_new', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [missFnPtr, '%p_name', 'null']));
			:emitClaimPool(val: clos);
			local String is resolved: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: resolved, hasDst: true, retType: resTy, callee: rSym . '_resolveHeld', argTypes: [IrType:Ptr, IrType:Ptr], args: ['%p_name', clos]));
			local String is setRaw: :castIfNeeded(val: resolved, fromTy: resTy, toTy: IrType:Ptr);
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'HashTable_mapSetAny', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', cache1, '%p_name', setRaw]));
			if({ resArc && resolved != 'null' }, { :emit(inst: IrInst:Retain(val: resolved)); });
			:emitPoolExit();
			:curPoolMark: '';
			:terminate(inst: IrInst:Ret(hasVal: true, val: resolved, ty: resTy));
			:mod:addFunction(fn: fn);
			ri++;
		});
	}

	Function of Boolean is isLazyCallExpr(Expression is expr){
		local Boolean is res: false;
		match(on: expr, when: [
			Expression:Call: local Function(CallData is call){
				if({ call:args:length() >= 1 }, {
					if({ call:name == 'lazy' && (call:bareProvider == 'Lazy' || call:bareProvider:endsWith(suffix: ':Lazy') || call:target:resolvedType == 'Lazy' || call:isBareCall) }, {
						res: true;
					});
					if({ call:name == 'eval' }, {
						match(on: call:target, when: [
							Expression:Path: local Function(Array of String is segs){
								local Int is n: segs:length();
								if({ n >= 2 && segs:get(index: n - 1, default: '') == 'Lazy' && segs:get(index: n - 2, default: '') == 'sysinternal' }, {
									res: true;
								});
							}
						], default: {});
					});
				});
			}
		], default: {});
		return res;
	}

	Function of Expression is getLazyBodyExpr(Expression is expr){
		return match(on: expr, when: [
			Expression:Call: local Function of Expression(CallData is call){
				if({ call:args:length() > 0 }, {
					return call:args:get(index: 0):value;
				});
				return Expression:Unknown;
			},
			else: { Expression:Unknown }
		]);
	}

	Function of String is lowerLazyBodyVal(Expression is blkExpr, IrType is expectedTy){
		local IrType is resTy: expectedTy;
		if({ resTy == IrType:Void }, { resTy: IrType:Ptr; });
		local String is _rtmp: :nextTmp();
		local String is resSlot: '%lazy_res_' . (:tmpCounter as String);
		:emit(inst: IrInst:Alloca(slot: resSlot, ty: resTy));
		local String is defVal: :emitDefaultVal(ty: resTy);
		:emit(inst: IrInst:Store(slot: resSlot, val: defVal, ty: resTy));
		local String is endLbl: :nextLabel(prefix: 'lazy_body_end');

		local String is prevRetSlot: :inlineReturnSlot;
		local String is prevRetEnd: :inlineReturnEndLbl;
		local IrType is prevRetTy: :inlineReturnTy;
		:inlineReturnSlot: resSlot;
		:inlineReturnEndLbl: endLbl;
		:inlineReturnTy: resTy;

		match(on: blkExpr, when: [
			Expression:AnonFn: local Function(Type is _rt, Array of Parameter is _ps, Array of Statement is bd){
				:pushScope();
				local Int is lastIdx: bd:length() - 1;
				local Int is i: 0;
				while({ i < lastIdx && !:blkTerminated }, {
					:lowerStmt(stmt: bd:get(index: i));
					i++;
				});
				if({ lastIdx >= 0 && !:blkTerminated }, {
					local Statement is lastStmt: bd:get(index: lastIdx);
					match(on: lastStmt, when: [
						Statement:Expr: local Function(Expression is es){
							local IrType is ety: :irTypeFor(specType: es:resolvedType);
							local String is ev: :lowerExpr(expr: es);
							ev: :castIfNeeded(val: ev, fromTy: ety, toTy: resTy);
							if({ ev != '' }, {
								:emit(inst: IrInst:Store(slot: resSlot, val: ev, ty: resTy));
							});
						},
						Statement:Return: local Function(Expression is re, Boolean is hr){
							if({ hr }, {
								local IrType is rty: :irTypeFor(specType: re:resolvedType);
								local String is rv: :lowerExpr(expr: re);
								rv: :castIfNeeded(val: rv, fromTy: rty, toTy: resTy);
								if({ rv != '' }, {
									:emit(inst: IrInst:Store(slot: resSlot, val: rv, ty: resTy));
								});
							});
						}
					], default: {
						:lowerStmt(stmt: lastStmt);
					});
				});
				:popScope();
			}
		], default: {
			local String is cObj: :lowerExpr(expr: blkExpr);
			local String is fnPtrAddr: :nextTmp();
			:emit(inst: IrInst:FieldPtr(dst: fnPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 0));
			local String is fnPtrVal: :nextTmp();
			:emit(inst: IrInst:Load(dst: fnPtrVal, slot: fnPtrAddr, ty: IrType:Ptr));
			local String is envPtrAddr: :nextTmp();
			:emit(inst: IrInst:FieldPtr(dst: envPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 1));
			local String is envVal: :nextTmp();
			:emit(inst: IrInst:Load(dst: envVal, slot: envPtrAddr, ty: IrType:Ptr));
			local String is callDst: :nextTmp();
			:emit(inst: IrInst:IndirectCall(dst: callDst, hasDst: true, retType: resTy, fnPtr: fnPtrVal, argTypes: [IrType:Ptr], args: [envVal]));
			:emit(inst: IrInst:Store(slot: resSlot, val: callDst, ty: resTy));
		});

		:inlineReturnSlot: prevRetSlot;
		:inlineReturnEndLbl: prevRetEnd;
		:inlineReturnTy: prevRetTy;

		if({ !:blkTerminated }, {
			:terminate(inst: IrInst:Br(target: endLbl));
		});
		local IrBlock is endBlk: :curFn:addBlock(label: endLbl);
		:switchBlock(blk: endBlk);
		local String is finalVal: :nextTmp();
		:emit(inst: IrInst:Load(dst: finalVal, slot: resSlot, ty: resTy));
		return finalVal;
	}

	local Function of String is emitLoadField(String is objPtr, String is sname, IrStruct is st, Int is fidx, String is fieldName){
		local IrType is fty: st:fieldTypes:get(index: fidx);
		local Int is stateIdx: st:fieldIndex(name: '_lazy_state_' . fieldName);
		if({ stateIdx >= 0 && :lazyFields:has(key: sname . ':' . fieldName) }, {
			local String is ownerSname: :lazyFields:get(key: sname . ':' . fieldName, default: sname);
			local String is statePtr: :nextTmp();
			:emit(inst: IrInst:FieldPtr(dst: statePtr, objPtr: objPtr, structName: sname, fieldIndex: stateIdx));
			local String is stateAddr: :nextTmp();
			:emit(inst: IrInst:IrCast(dst: stateAddr, val: statePtr, fromType: IrType:Ptr, toType: IrType:I64));
			local String is stVal: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: stVal, hasDst: true, retType: IrType:I64, callee: '__spec_mem_atomic_load_i64', argTypes: [IrType:I64], args: [stateAddr]));
			local String is twoV: :nextTmp();
			:emit(inst: IrInst:ConstInt(dst: twoV, value: 2));
			local String is isReady: :nextTmp();
			:emit(inst: IrInst:Cmp(dst: isReady, op: '==', lhs: stVal, rhs: twoV, ty: IrType:I64));

			local String is _rtmp: :nextTmp();
			local String is resSlot: '%lazy_fld_' . (:tmpCounter as String);
			:emit(inst: IrInst:Alloca(slot: resSlot, ty: fty));
			local String is fastLbl: :nextLabel(prefix: 'lazy_fast');
			local String is slowLbl: :nextLabel(prefix: 'lazy_slow');
			local String is endLbl: :nextLabel(prefix: 'lazy_end');
			:terminate(inst: IrInst:CondBr(cond: isReady, thenLabel: fastLbl, elseLabel: slowLbl));

			local IrBlock is fastBlk: :curFn:addBlock(label: fastLbl);
			:switchBlock(blk: fastBlk);
			local String is fptr: :nextTmp();
			local String is fval: :nextTmp();
			:emit(inst: IrInst:FieldPtr(dst: fptr, objPtr: objPtr, structName: sname, fieldIndex: fidx));
			:emit(inst: IrInst:Load(dst: fval, slot: fptr, ty: fty));
			:emit(inst: IrInst:Store(slot: resSlot, val: fval, ty: fty));
			:terminate(inst: IrInst:Br(target: endLbl));

			local IrBlock is slowBlk: :curFn:addBlock(label: slowLbl);
			:switchBlock(blk: slowBlk);
			local String is sval: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: sval, hasDst: true, retType: fty, callee: ownerSname . '_' . fieldName . '__lazy_init', argTypes: [IrType:Ptr], args: [objPtr]));
			:emit(inst: IrInst:Store(slot: resSlot, val: sval, ty: fty));
			:terminate(inst: IrInst:Br(target: endLbl));

			local IrBlock is endBlk: :curFn:addBlock(label: endLbl);
			:switchBlock(blk: endBlk);
			local String is finalVal: :nextTmp();
			:emit(inst: IrInst:Load(dst: finalVal, slot: resSlot, ty: fty));
			return finalVal;
		});
		local String is ptr: :nextTmp();
		local String is dst: :nextTmp();
		:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: objPtr, structName: sname, fieldIndex: fidx));
		:emit(inst: IrInst:Load(dst: dst, slot: ptr, ty: fty));
		return dst;
	}

	local Function is emitMarkLazyFieldDone(String is objPtr, String is sname, IrStruct is st, String is fieldName){
		local Int is stateIdx: st:fieldIndex(name: '_lazy_state_' . fieldName);
		if({ stateIdx >= 0 }, {
			local String is statePtr: :nextTmp();
			:emit(inst: IrInst:FieldPtr(dst: statePtr, objPtr: objPtr, structName: sname, fieldIndex: stateIdx));
			local String is stateAddr: :nextTmp();
			:emit(inst: IrInst:IrCast(dst: stateAddr, val: statePtr, fromType: IrType:Ptr, toType: IrType:I64));
			local String is twoV: :nextTmp();
			:emit(inst: IrInst:ConstInt(dst: twoV, value: 2));
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: '__spec_mem_atomic_store_i64', argTypes: [IrType:I64, IrType:I64], args: [stateAddr, twoV]));
		});
	}

	local Function of String is emitLoadLocal(String is name, IrType is ty){
		if({ :lazyLocalStateSlots:has(key: name) }, {
			local String is stateSlot: :lazyLocalStateSlots:get(key: name, default: '');
			local Expression is lazyExpr: :lazyLocalExprs:get(key: name, default: Expression:Unknown);
			local String is curSt: :nextTmp();
			:emit(inst: IrInst:Load(dst: curSt, slot: stateSlot, ty: IrType:I64));
			local String is twoV: :nextTmp();
			:emit(inst: IrInst:ConstInt(dst: twoV, value: 2));
			local String is isDone: :nextTmp();
			:emit(inst: IrInst:Cmp(dst: isDone, op: '==', lhs: curSt, rhs: twoV, ty: IrType:I64));

			local String is initLbl: :nextLabel(prefix: 'lazy_loc_init');
			local String is doneLbl: :nextLabel(prefix: 'lazy_loc_done');
			:terminate(inst: IrInst:CondBr(cond: isDone, thenLabel: doneLbl, elseLabel: initLbl));

			local IrBlock is initBlk: :curFn:addBlock(label: initLbl);
			:switchBlock(blk: initBlk);
			:lazyLocalStateSlots:remove(key: name);
			local Boolean is isArc: :localIsArc:get(key: name, default: false);
			local String is specT: :localSpecTypes:get(key: name, default: '');
			local String is prevMapK: :expectedMapKeyType;
			local String is prevMapV: :expectedMapValType;
			:setMapHintsFromTypeStr(t: specT);
			local String is initVal: :lowerLazyBodyVal(blkExpr: lazyExpr, expectedTy: ty);
			:expectedMapKeyType: prevMapK;
			:expectedMapValType: prevMapV;
			if({ initVal == '' }, { initVal: :emitDefaultVal(ty: ty); });
			:emitStoreLocal(name: name, val: initVal, ty: ty, isArc: isArc);
			:emit(inst: IrInst:Store(slot: stateSlot, val: twoV, ty: IrType:I64));
			:lazyLocalStateSlots:set(key: name, value: stateSlot);
			:terminate(inst: IrInst:Br(target: doneLbl));

			local IrBlock is doneBlk: :curFn:addBlock(label: doneLbl);
			:switchBlock(blk: doneBlk);
		});
		local String is slot: :localSlots:get(key: name, default: '');
		if({ :boxedLocals:has(key: name) }, {
			local String is boxPtr: :nextTmp();
			:emit(inst: IrInst:Load(dst: boxPtr, slot: slot, ty: IrType:Ptr));
			local String is raw: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'spec_rt_box_get', argTypes: [IrType:Ptr], args: [boxPtr]));
			if({ ty == IrType:Ptr }, { return raw; });
			local String is dst: :nextTmp();
			:emit(inst: IrInst:IrCast(dst: dst, val: raw, fromType: IrType:Ptr, toType: ty));
			return dst;
		});
		local String is dst: :nextTmp();
		:emit(inst: IrInst:Load(dst: dst, slot: slot, ty: ty));
		return dst;
	}

	local Function is emitStoreLocal(String is name, String is val, IrType is ty, Boolean is isArc){
		if({ :lazyLocalStateSlots:has(key: name) }, {
			local String is stSlot: :lazyLocalStateSlots:get(key: name, default: '');
			local String is twoV: :nextTmp();
			:emit(inst: IrInst:ConstInt(dst: twoV, value: 2));
			:emit(inst: IrInst:Store(slot: stSlot, val: twoV, ty: IrType:I64));
		});
		local String is slot: :localSlots:get(key: name, default: '');
		if({ :boxedLocals:has(key: name) }, {
			local String is boxPtr: :nextTmp();
			:emit(inst: IrInst:Load(dst: boxPtr, slot: slot, ty: IrType:Ptr));
			local String is vPtr: val;
			if({ ty != IrType:Ptr }, {
				vPtr: :nextTmp();
				:emit(inst: IrInst:IrCast(dst: vPtr, val: val, fromType: ty, toType: IrType:Ptr));
			});
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_rt_box_set', argTypes: [IrType:Ptr, IrType:Ptr], args: [boxPtr, vPtr]));
			return;
		});
		if({ isArc }, {
			if({ val != '' && val != 'null' }, {
				:emit(inst: IrInst:Retain(val: val));
			});
			local String is oldVal: :nextTmp();
			:emit(inst: IrInst:Load(dst: oldVal, slot: slot, ty: IrType:Ptr));
			:emit(inst: IrInst:Release(val: oldVal));
		});
		:emit(inst: IrInst:Store(slot: slot, val: val, ty: ty));
	}

	Function of String is emitNewBox(String is initVal, IrType is ty, Boolean is isArc){
		local String is valI64: initVal;
		if({ ty == IrType:F64 }, {
			local String is pTmp: :nextTmp();
			:emit(inst: IrInst:IrCast(dst: pTmp, val: initVal, fromType: IrType:F64, toType: IrType:Ptr));
			valI64: :nextTmp();
			:emit(inst: IrInst:IrCast(dst: valI64, val: pTmp, fromType: IrType:Ptr, toType: IrType:I64));
		}, {
			if({ ty != IrType:I64 }, {
				valI64: :nextTmp();
				:emit(inst: IrInst:IrCast(dst: valI64, val: initVal, fromType: ty, toType: IrType:I64));
			});
		});
		local String is arcConst: :nextTmp();
		:emit(inst: IrInst:ConstBool(dst: arcConst, value: isArc));
		local String is boxPtr: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: boxPtr, hasDst: true, retType: IrType:Ptr, callee: 'spec_rt_box_new', argTypes: [IrType:I64, IrType:I1], args: [valI64, arcConst]));
		return boxPtr;
	}

	local Function is collectDeclNamesInStmts(Array of Statement is stmts, Map of String to Boolean is decls){
		local Int is i: 0;
		while({ i < stmts:length() }, {
			local Statement is st: stmts:get(index: i);
			match(on: st, when: [
				Statement:VarDecl: local Function(Array of String is _m, Type is _t, String is varName, Expression is initExpr, Boolean is hasInit){
					decls:set(key: varName, value: true);
					if({ hasInit }, { :collectDeclNamesInExpr(expr: initExpr, decls: decls); });
				},
				Statement:Assign: local Function(Expression is t, Expression is v){
					:collectDeclNamesInExpr(expr: t, decls: decls);
					:collectDeclNamesInExpr(expr: v, decls: decls);
				},
				Statement:Expr: local Function(Expression is e){
					:collectDeclNamesInExpr(expr: e, decls: decls);
				},
				Statement:Return: local Function(Expression is e, Boolean is hr){
					if({ hr }, { :collectDeclNamesInExpr(expr: e, decls: decls); });
				}
			], default: {});
			i++;
		});
	}

	local Function is collectDeclNamesInExpr(Expression is expr, Map of String to Boolean is decls){
		match(on: expr, when: [
			Expression:Unary: local Function(String is _op, Expression is operand){
				:collectDeclNamesInExpr(expr: operand, decls: decls);
			},
			Expression:Binary: local Function(String is _op, Expression is left, Expression is right){
				:collectDeclNamesInExpr(expr: left, decls: decls);
				:collectDeclNamesInExpr(expr: right, decls: decls);
			},
			Expression:Cast: local Function(Expression is inner, String is _t, Array of Expression is args){
				:collectDeclNamesInExpr(expr: inner, decls: decls);
				local Int is ai: 0;
				while({ ai < args:length() }, {
					:collectDeclNamesInExpr(expr: args:get(index: ai), decls: decls);
					ai++;
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is _f){
				:collectDeclNamesInExpr(expr: target, decls: decls);
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				:collectDeclNamesInExpr(expr: target, decls: decls);
				:collectDeclNamesInExpr(expr: index, decls: decls);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				local Int is ii: 0;
				while({ ii < items:length() }, {
					:collectDeclNamesInExpr(expr: items:get(index: ii), decls: decls);
					ii++;
				});
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					:collectDeclNamesInExpr(expr: keys:get(index: mi), decls: decls);
					:collectDeclNamesInExpr(expr: values:get(index: mi), decls: decls);
					mi++;
				});
			},
			Expression:Call: local Function(CallData is call){
				:collectDeclNamesInExpr(expr: call:target, decls: decls);
				local Int is ci: 0;
				while({ ci < call:args:length() }, {
					local NamedArg is na: call:args:get(index: ci);
					:collectDeclNamesInExpr(expr: na:value, decls: decls);
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
				:collectDeclNamesInStmts(stmts: subBody, decls: decls);
			}
		], default: {});
	}

	local Function is collectAllAnonCapturesInStmts(Array of Statement is stmts, Map of String to Boolean is decls, Map of String to Boolean is out){
		local Int is i: 0;
		while({ i < stmts:length() }, {
			local Statement is st: stmts:get(index: i);
			match(on: st, when: [
				Statement:VarDecl: local Function(Array of String is _m, Type is _t, String is _vn, Expression is initExpr, Boolean is hasInit){
					if({ hasInit }, { :collectAllAnonCapturesInExpr(expr: initExpr, decls: decls, out: out); });
				},
				Statement:Assign: local Function(Expression is t, Expression is v){
					:collectAllAnonCapturesInExpr(expr: t, decls: decls, out: out);
					:collectAllAnonCapturesInExpr(expr: v, decls: decls, out: out);
				},
				Statement:Expr: local Function(Expression is e){
					:collectAllAnonCapturesInExpr(expr: e, decls: decls, out: out);
				},
				Statement:Return: local Function(Expression is e, Boolean is hr){
					if({ hr }, { :collectAllAnonCapturesInExpr(expr: e, decls: decls, out: out); });
				}
			], default: {});
			i++;
		});
	}

	local Function is collectAllAnonCapturesInExpr(Expression is expr, Map of String to Boolean is decls, Map of String to Boolean is out){
		match(on: expr, when: [
			Expression:Unary: local Function(String is _op, Expression is operand){
				:collectAllAnonCapturesInExpr(expr: operand, decls: decls, out: out);
			},
			Expression:Binary: local Function(String is _op, Expression is left, Expression is right){
				:collectAllAnonCapturesInExpr(expr: left, decls: decls, out: out);
				:collectAllAnonCapturesInExpr(expr: right, decls: decls, out: out);
			},
			Expression:Cast: local Function(Expression is inner, String is _t, Array of Expression is args){
				:collectAllAnonCapturesInExpr(expr: inner, decls: decls, out: out);
				local Int is ai: 0;
				while({ ai < args:length() }, {
					:collectAllAnonCapturesInExpr(expr: args:get(index: ai), decls: decls, out: out);
					ai++;
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is _f){
				:collectAllAnonCapturesInExpr(expr: target, decls: decls, out: out);
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				:collectAllAnonCapturesInExpr(expr: target, decls: decls, out: out);
				:collectAllAnonCapturesInExpr(expr: index, decls: decls, out: out);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				local Int is ii: 0;
				while({ ii < items:length() }, {
					:collectAllAnonCapturesInExpr(expr: items:get(index: ii), decls: decls, out: out);
					ii++;
				});
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					:collectAllAnonCapturesInExpr(expr: keys:get(index: mi), decls: decls, out: out);
					:collectAllAnonCapturesInExpr(expr: values:get(index: mi), decls: decls, out: out);
					mi++;
				});
			},
			Expression:Call: local Function(CallData is call){
				:collectAllAnonCapturesInExpr(expr: call:target, decls: decls, out: out);
				local String is cnm: call:name;
				local Boolean is isInlineCf: cnm == 'if' || cnm == 'branch' || cnm == 'while' || cnm == 'repeat' || cnm == 'until' || cnm == 'loop' || cnm == 'match' || cnm == 'lazy' || cnm == 'eval';
				local Int is ci: 0;
				while({ ci < call:args:length() }, {
					local NamedArg is na: call:args:get(index: ci);
					if({ isInlineCf }, {
						local Boolean is handledInl: false;
						match(on: na:value, when: [
							Expression:AnonFn: local Function(Type is _rt, Array of Parameter is _sp, Array of Statement is subBody){
								handledInl: true;
								:collectAllAnonCapturesInStmts(stmts: subBody, decls: decls, out: out);
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
												:collectAllAnonCapturesInStmts(stmts: kBody, decls: decls, out: out);
											}
										], default: {
											:collectAllAnonCapturesInExpr(expr: mk, decls: decls, out: out);
										});
										match(on: mv, when: [
											Expression:AnonFn: local Function(Type is _vrt, Array of Parameter is _vsp, Array of Statement is vBody){
												:collectAllAnonCapturesInStmts(stmts: vBody, decls: decls, out: out);
											}
										], default: {
											:collectAllAnonCapturesInExpr(expr: mv, decls: decls, out: out);
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
															:collectAllAnonCapturesInStmts(stmts: pBody, decls: decls, out: out);
														}
													], default: {
														:collectAllAnonCapturesInExpr(expr: pItem, decls: decls, out: out);
													});
													pi++;
												});
											}
										], default: {
											:collectAllAnonCapturesInExpr(expr: bItem, decls: decls, out: out);
										});
										bi++;
									});
								});
							}
						], default: {});
						if({ !handledInl }, {
							:collectAllAnonCapturesInExpr(expr: na:value, decls: decls, out: out);
						});
					}, {
						:collectAllAnonCapturesInExpr(expr: na:value, decls: decls, out: out);
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
				:collectFreeInStmts(stmts: subBody, bound: subBound, outerSlots: decls, seen: seen, out: caps);
				local Int is ci: 0;
				while({ ci < caps:length() }, {
					local String is cname: caps:get(index: ci, default: '');
					if({ cname != ':' }, {
						out:set(key: cname, value: true);
					});
					ci++;
				});
			}
		], default: {});
	}

	local Function of String is structNameForLocal(String is name){
		if({ name == ':' }, { return :currentClass; });
		local String is st: :baseTypeName(t: '' . :localSpecTypes:get(key: name, default: ''));
		if({ st != '' }, {
			local String is qn: st;
			if({ :clsQNameMap:has(key: st) }, { qn: '' . :clsQNameMap:get(key: st, default: ''); });
			local String is cs: :cStructName(qname: qn);
			if({ :mod:findStruct(name: cs):name != '' }, { return cs; });
		});
		return :currentClass;
	}

	local Function of Int is resolvePathField(Array of String is segments){
		:pathObjPtr: '';
		:pathStructName: '';
		:pathFieldIndex: -1;
		if({ segments:length() < 2 }, { return -1; });
		local String is seg0: segments:get(index: 0, default: '');
		local String is obj: '';
		local String is sname: '';
		local Int is segIdx: 1;
		if({ :localSlots:has(key: seg0) }, {
			local IrType is sty: :localTypes:get(key: seg0, default: IrType:Ptr);
			obj: :emitLoadLocal(name: seg0, ty: sty);
			sname: :structNameForLocal(name: seg0);
		}, {
			local String is selfHk: :currentClass . ':' . seg0;
			if({ :heldFields:has(key: selfHk) }, {
				local String is owner0: :heldFields:get(key: selfHk, default: '');
				local String is hSpec0: :heldFieldTypes:get(key: owner0 . ':' . seg0, default: '');
				local IrType is hty0: :irTypeFor(specType: hSpec0);
				if({ hty0 == IrType:Void }, { hty0: IrType:Ptr; });
				obj: :nextTmp();
				:emit(inst: IrInst:IrCall(dst: obj, hasDst: true, retType: hty0, callee: owner0 . '_' . seg0 . '__ensure', argTypes: [], args: []));
				if({ hty0 == IrType:Ptr }, { :emitClaimPool(val: obj); });
				local String is hqn0: '' . hSpec0;
				if({ :clsQNameMap:has(key: hSpec0) }, {
					hqn0: :clsQNameMap:get(key: hSpec0, default: '');
				});
				sname: :cStructName(qname: hqn0);
			}, {
				if({ segments:length() >= 3 }, {
					local String is seg1: segments:get(index: 1, default: '');
					local String is hk: seg0 . ':' . seg1;
					if({ :heldFields:has(key: hk) }, {
						local String is owner1: :heldFields:get(key: hk, default: '');
						local String is hSpec1: :heldFieldTypes:get(key: owner1 . ':' . seg1, default: '');
						local IrType is hty1: :irTypeFor(specType: hSpec1);
						if({ hty1 == IrType:Void }, { hty1: IrType:Ptr; });
						obj: :nextTmp();
						:emit(inst: IrInst:IrCall(dst: obj, hasDst: true, retType: hty1, callee: owner1 . '_' . seg1 . '__ensure', argTypes: [], args: []));
						if({ hty1 == IrType:Ptr }, { :emitClaimPool(val: obj); });
						local String is hqn1: '' . hSpec1;
						if({ :clsQNameMap:has(key: hSpec1) }, {
							hqn1: :clsQNameMap:get(key: hSpec1, default: '');
						});
						sname: :cStructName(qname: hqn1);
						segIdx: 2;
					});
				});
			});
		});
		if({ obj == '' && :localSlots:has(key: ':') }, {
			local IrStruct is selfSt: :mod:findStruct(name: :currentClass);
			if({ selfSt:fieldIndex(name: seg0) >= 0 }, {
				obj: :emitLoadLocal(name: ':', ty: IrType:Ptr);
				sname: :currentClass;
				segIdx: 0;
			});
		});
		if({ obj == '' || sname == '' }, { return -1; });
		local Boolean is ok: true;
		while({ ok && segIdx < segments:length() - 1 }, {
			local String is seg: segments:get(index: segIdx, default: '');
			local IrStruct is curSt: :mod:findStruct(name: sname);
			local Int is fidx: curSt:fieldIndex(name: seg);
			if({ fidx < 0 }, {
				ok: false;
			}, {
				local String is nextObj: :emitLoadField(objPtr: obj, sname: sname, st: curSt, fidx: fidx, fieldName: seg);
				obj: nextObj;
				local String is fSpec: :baseTypeName(t: :fieldSpecTypes:get(key: sname . ':' . seg, default: ''));
				local String is fqn: '' . fSpec;
				if({ :clsQNameMap:has(key: fSpec) }, {
					fqn: :clsQNameMap:get(key: fSpec, default: '');
				});
				sname: :cStructName(qname: fqn);
				if({ sname == '' || :mod:findStruct(name: sname):name == '' }, {
					ok: false;
				});
			});
			segIdx++;
		});
		if({ !ok }, { return -1; });
		local String is fname: segments:get(index: segments:length() - 1, default: '');
		local IrStruct is finalSt: :mod:findStruct(name: sname);
		local Int is finalIdx: finalSt:fieldIndex(name: fname);
		if({ finalIdx < 0 }, { return -1; });
		:pathObjPtr: obj;
		:pathStructName: sname;
		:pathFieldIndex: finalIdx;
		return finalIdx;
	}

	local Function of String is structNameForExpr(Expression is expr){
		local String is rt: :baseTypeName(t: expr:resolvedType);
		if({ rt != '' }, {
			local String is qn: rt;
			if({ :clsQNameMap:has(key: rt) }, { qn: '' . :clsQNameMap:get(key: rt, default: ''); });
			local String is cs: :cStructName(qname: qn);
			if({ :mod:findStruct(name: cs):name != '' }, { return cs; });
		});
		return :currentClass;
	}

	local Function is buildMethod(ClassInfo is cls, Member is m, String is fnName){
		local IrType is retTy: :methodReturnType(mt: m:memberType);
		local Boolean is isHeldMethod: m:hasModifier(kw: Keyword:HELD);
		local IrFunction is fn: IrFunction:init(name: fnName, retType: retTy);
		fn:sourceFile: cls:sourceFile;
		fn:line: m:line;
		:currentLine: m:line;
		:currentMethod: m:name;
		if({ !isHeldMethod }, {
			fn:addParam(name: '%self', ty: IrType:Ptr);
		});
		local Int is pi: 0;
		while({ pi < m:params:length() }, {
			local Parameter is p: m:params:get(index: pi);
			fn:addParam(name: '%p_' . p:name, ty: :irTypeFor(specType: p:paramType:name));
			pi++;
		});

		local IrBlock is entry: fn:addBlock(label: 'entry');
		:curFn: fn;
		:switchBlock(blk: entry);
		:tmpCounter: 0;
		:lblCounter: 0;
		:localSlots: Map:init();
		:localTypes: Map:init();
		:localIsArc: Map:init();
		:localSpecTypes: Map:init();
		:boxedLocals: Map:init();
		:capturedNames: Map:init();
		:ownedSlots: [];
		:resetScopes();

		local Map of String to Boolean is decls: Map:init();
		local Int is dpi: 0;
		while({ dpi < m:params:length() }, {
			local Parameter is dp: m:params:get(index: dpi);
			decls:set(key: dp:name, value: true);
			dpi++;
		});
		:collectDeclNamesInStmts(stmts: m:body, decls: decls);
		:collectAllAnonCapturesInStmts(stmts: m:body, decls: decls, out: :capturedNames);
		:curFnRetIsArc: :isArcSpecType(specType: :methodReturnSpecType(mt: m:memberType));
		:curFnErrHandlerCallee: '';
		:curFnErrPushedSlot: '';
		:emitPoolEnter();

		if({ !isHeldMethod }, {
			# Bind ':' receiver into stack slot
			:localSlots:set(key: ':', value: '%self_slot');
			:localTypes:set(key: ':', value: IrType:Ptr);
			:localIsArc:set(key: ':', value: !:isUnmanagedClass);
			:localSpecTypes:set(key: ':', value: :currentClass);
			:emit(inst: IrInst:Alloca(slot: '%self_slot', ty: IrType:Ptr));
			:emit(inst: IrInst:Store(slot: '%self_slot', val: '%self', ty: IrType:Ptr));
			if({ !:isUnmanagedClass && :clsQNameMap:has(key: 'Pool') && m:name != 'SpecErrorHandler' && m:name != 'destroy' }, {
				local String is errCallee: :findCustomErrorHandlerCallee(clsName: cls:qualifiedName());
				if({ errCallee != '' }, {
					:curFnErrHandlerCallee: errCallee;
					:curFnErrPushedSlot: '%err_pushed_slot';
					:emit(inst: IrInst:Alloca(slot: '%err_pushed_slot', ty: IrType:I1));
					local String is selfAddr: :nextTmp();
					:emit(inst: IrInst:IrCast(dst: selfAddr, val: '%self', fromType: IrType:Ptr, toType: IrType:I64));
					local String is pushedVal: :nextTmp();
					:emit(inst: IrInst:IrCall(dst: pushedVal, hasDst: true, retType: IrType:I1, callee: 'Pool_pushErrorHandler', argTypes: [IrType:Ptr, IrType:I64], args: ['null', selfAddr]));
					:emit(inst: IrInst:Store(slot: '%err_pushed_slot', val: pushedVal, ty: IrType:I1));
				});
			});
		});

		pi: 0;
		while({ pi < m:params:length() }, {
			local Parameter is p: m:params:get(index: pi);
			local IrType is pty: :irTypeFor(specType: p:paramType:name);
			local Boolean is pArc: :isArcSpecType(specType: p:paramType:name);
			local String is slot: '%slot_' . p:name;
			:localSlots:set(key: p:name, value: slot);
			:localTypes:set(key: p:name, value: pty);
			:localIsArc:set(key: p:name, value: pArc);
			:localSpecTypes:set(key: p:name, value: p:paramType:name);
			if({ :capturedNames:has(key: p:name) }, {
				:boxedLocals:set(key: p:name, value: true);
				:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
				if({ pArc }, {
					:emit(inst: IrInst:Retain(val: '%p_' . p:name));
				});
				local String is boxPtr: :emitNewBox(initVal: '%p_' . p:name, ty: pty, isArc: pArc);
				:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
				:ownedSlots:add(item: slot);
			}, {
				:emit(inst: IrInst:Alloca(slot: slot, ty: pty));
				:emit(inst: IrInst:Store(slot: slot, val: '%p_' . p:name, ty: pty));
			});
			pi++;
		});

		if({ m:name == 'init' }, {
			:emitFieldDefaults(cls: cls, seen: Map:init());
		});

		:lowerStmts(stmts: m:body);

		if({ !:blkTerminated }, {
			:emitReleaseOwnedLocals();
			:emitPoolExit();
			if({ retTy == IrType:Void }, {
				:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
			}, {
				local String is defVal: :emitDefaultVal(ty: retTy);
				:terminate(inst: IrInst:Ret(hasVal: true, val: defVal, ty: retTy));
			});
		});
		:curPoolMark: '';
		:curFnErrHandlerCallee: '';
		:curFnErrPushedSlot: '';

		:mod:addFunction(fn: fn);
	}

	local Function of String is findCustomErrorHandlerCallee(String is clsName){
		return :findCustomErrorHandlerWalk(clsName: clsName, visited: Map:init());
	}

	local Function of String is findCustomErrorHandlerWalk(String is clsName, Map of String to Boolean is visited){
		if({ clsName == '' || clsName == 'Class' || clsName == 'Stringable' || clsName == 'Loadable' || clsName == 'Any' || clsName == 'Enum' }, {
			return '';
		});
		local String is qn: clsName;
		if({ :clsQNameMap:has(key: clsName) }, {
			qn: '' . :clsQNameMap:get(key: clsName, default: '');
		});
		if({ visited:has(key: qn) || !:clsMap:has(key: qn) }, {
			return '';
		});
		visited:set(key: qn, value: true);
		local ClassInfo is cls: :clsMap:get(key: qn, default: ClassInfo:init(name: '', baseClass: '', members: []));
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:METHOD && m:name == 'SpecErrorHandler' && !m:hasModifier(kw: Keyword:HELD) }, {
				return :cStructName(qname: cls:qualifiedName()) . '_SpecErrorHandler';
			});
			mi++;
		});
		local Int is bi: 0;
		while({ bi < cls:baseClasses:length() }, {
			local String is bname: cls:baseClasses:get(index: bi, default: '');
			local ClassInfo is bcls: :resolveBaseClass(cls: cls, bname: bname, clsMap: :clsMap);
			if({ bcls:qualifiedName() != cls:qualifiedName() }, {
				local String is found: :findCustomErrorHandlerWalk(clsName: bcls:qualifiedName(), visited: visited);
				if({ found != '' }, {
					return found;
				});
			});
			bi++;
		});
		return '';
	}

	local Function of String is emitConstStrVal(String is value){
		local String is dst: :nextTmp();
		local Int is sid: :mod:internStringLiteral(value: value);
		:emit(inst: IrInst:ConstString(dst: dst, strId: sid));
		return dst;
	}

	local Function is collectCallsInStmts(Array of Statement is stmts, Map of String to Boolean is fnVars, Array of String is outCalls){
		local Int is i: 0;
		while({ i < stmts:length() }, {
			local Statement is st: stmts:get(index: i);
			match(on: st, when: [
				Statement:VarDecl: local Function(Array of String is _m, Type is vt, String is vn, Expression is ie, Boolean is hi){
					if({ vt:name:startsWith(prefix: 'Function') }, {
						fnVars:set(key: vn, value: true);
					});
					if({ hi }, {
						:collectCallsInExpr(expr: ie, fnVars: fnVars, outCalls: outCalls);
					});
				},
				Statement:Assign: local Function(Expression is at, Expression is av){
					:collectCallsInExpr(expr: at, fnVars: fnVars, outCalls: outCalls);
					:collectCallsInExpr(expr: av, fnVars: fnVars, outCalls: outCalls);
				},
				Statement:Return: local Function(Expression is re, Boolean is hr){
					if({ hr }, {
						:collectCallsInExpr(expr: re, fnVars: fnVars, outCalls: outCalls);
					});
				},
				Statement:Expr: local Function(Expression is es){
					:collectCallsInExpr(expr: es, fnVars: fnVars, outCalls: outCalls);
				}
			], default: {});
			i++;
		});
	}

	local Function is collectCallsInExpr(Expression is expr, Map of String to Boolean is fnVars, Array of String is outCalls){
		match(on: expr, when: [
			Expression:Unary: local Function(String is _op, Expression is opnd){
				:collectCallsInExpr(expr: opnd, fnVars: fnVars, outCalls: outCalls);
			},
			Expression:Binary: local Function(String is _op, Expression is l, Expression is r){
				:collectCallsInExpr(expr: l, fnVars: fnVars, outCalls: outCalls);
				:collectCallsInExpr(expr: r, fnVars: fnVars, outCalls: outCalls);
			},
			Expression:Cast: local Function(Expression is inner, String is _t, Array of Expression is args){
				:collectCallsInExpr(expr: inner, fnVars: fnVars, outCalls: outCalls);
				local Int is ai: 0;
				while({ ai < args:length() }, {
					:collectCallsInExpr(expr: args:get(index: ai), fnVars: fnVars, outCalls: outCalls);
					ai++;
				});
			},
			Expression:FieldAccess: local Function(Expression is t, String is _f){
				:collectCallsInExpr(expr: t, fnVars: fnVars, outCalls: outCalls);
			},
			Expression:Index: local Function(Expression is t, Expression is idx){
				:collectCallsInExpr(expr: t, fnVars: fnVars, outCalls: outCalls);
				:collectCallsInExpr(expr: idx, fnVars: fnVars, outCalls: outCalls);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				local Int is ii: 0;
				while({ ii < items:length() }, {
					:collectCallsInExpr(expr: items:get(index: ii), fnVars: fnVars, outCalls: outCalls);
					ii++;
				});
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is vals){
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					:collectCallsInExpr(expr: keys:get(index: mi), fnVars: fnVars, outCalls: outCalls);
					:collectCallsInExpr(expr: vals:get(index: mi), fnVars: fnVars, outCalls: outCalls);
					mi++;
				});
			},
			Expression:AnonFn: local Function(Type is _rt, Array of Parameter is subParams, Array of Statement is subBody){
				local Int is pi: 0;
				while({ pi < subParams:length() }, {
					local Parameter is sp: subParams:get(index: pi);
					if({ sp:paramType:name:startsWith(prefix: 'Function') }, {
						fnVars:set(key: sp:name, value: true);
					});
					pi++;
				});
				:collectCallsInStmts(stmts: subBody, fnVars: fnVars, outCalls: outCalls);
			},
			Expression:Call: local Function(CallData is call){
				local String is cnm: call:name;
				if({ cnm == 'callCatching' }, {
					return;
				});
				if({ cnm == 'raiseError' || cnm == 'raisePendingError' || cnm == 'raisePendingErrorAddr' || cnm == 'invokeVoid' || cnm == 'invoke_void' }, {
					outCalls:add(item: '__UNWIND_SEED__');
				});
				if({ call:isBareCall && fnVars:has(key: cnm) }, {
					outCalls:add(item: '__UNWIND_SEED__');
				});
				if({ cnm == 'init' }, {
					match(on: call:target, when: [
						Expression:Ident: local Function(String is tname){
							if({ tname != ':' && tname != '' }, {
								outCalls:add(item: tname . '_init');
							});
						}
					], default: {});
				}, {
					if({ cnm != 'if' && cnm != 'while' && cnm != 'until' && cnm != 'repeat' && cnm != 'match' && cnm != 'branch' && cnm != 'lazy' && cnm != 'eval' && cnm != 'get' && cnm != 'set' && cnm != 'add' && cnm != 'length' && cnm != 'has' && cnm != 'toString' && cnm != 'destroy' }, {
						outCalls:add(item: cnm);
					});
				});
				:collectCallsInExpr(expr: call:target, fnVars: fnVars, outCalls: outCalls);
				local Int is cai: 0;
				while({ cai < call:args:length() }, {
					local NamedArg is cna: call:args:get(index: cai);
					:collectCallsInExpr(expr: cna:value, fnVars: fnVars, outCalls: outCalls);
					cai++;
				});
			}
		], default: {});
	}

	local Function is computeCanUnwind(Array of ClassInfo is allClasses){
		:canUnwindCallees: Map:init();
		:canUnwindMethodNames: Map:init();
		local Array of String is methodSyms: [];
		local Array of String is methodBareNames: [];
		local Array of Int is methodCallStarts: [];
		local Array of Int is methodCallEnds: [];
		local Array of String is flatCalls: [];

		local Int is ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			if({ !:bindings:isSysinternal(cls: cls) }, {
				local String is sname: :cStructName(qname: cls:qualifiedName());
				local Map of String to Int is mCounts: Map:init();
				local Int is mi: 0;
				while({ mi < cls:members:length() }, {
					local Member is m: cls:members:get(index: mi);
					if({ m:kind == MemberKind:METHOD && m:body:length() > 0 && m:name != 'destroy' }, {
						local Int is ovIdx: mCounts:get(key: m:name, default: 0);
						mCounts:set(key: m:name, value: ovIdx + 1);
						local String is fnSym: if({ ovIdx > 0 }, { sname . '_' . m:name . '_' . ((ovIdx + 1) as String) }, { sname . '_' . m:name });
						local Map of String to Boolean is fnVars: Map:init();
						local Int is pi: 0;
						while({ pi < m:params:length() }, {
							local Parameter is p: m:params:get(index: pi);
							if({ p:paramType:name:startsWith(prefix: 'Function') }, {
								fnVars:set(key: p:name, value: true);
							});
							pi++;
						});
						local Int is startIdx: flatCalls:length();
						:collectCallsInStmts(stmts: m:body, fnVars: fnVars, outCalls: flatCalls);
						local Int is endIdx: flatCalls:length();
						local Boolean is hasSeed: false;
						local Int is ki: startIdx;
						while({ ki < endIdx }, {
							if({ flatCalls:get(index: ki, default: '') == '__UNWIND_SEED__' }, {
								hasSeed: true;
							});
							ki++;
						});
						if({ hasSeed }, {
							:canUnwindCallees:set(key: fnSym, value: true);
							if({ m:name != 'init' }, {
								:canUnwindMethodNames:set(key: m:name, value: true);
							});
						}, {
							methodSyms:add(item: fnSym);
							methodBareNames:add(item: m:name);
							methodCallStarts:add(item: startIdx);
							methodCallEnds:add(item: endIdx);
						});
					});
					mi++;
				});
			});
			ci++;
		});

		local Boolean is changed: true;
		while({ changed }, {
			changed: false;
			local Int is idx: 0;
			while({ idx < methodSyms:length() }, {
				local String is sym: methodSyms:get(index: idx, default: '');
				if({ !:canUnwindCallees:has(key: sym) }, {
					local Int is sIdx: methodCallStarts:get(index: idx, default: 0);
					local Int is eIdx: methodCallEnds:get(index: idx, default: 0);
					local Boolean is hits: false;
					local Int is ki: sIdx;
					while({ ki < eIdx && !hits }, {
						local String is c: flatCalls:get(index: ki, default: '');
						if({ :canUnwindCallees:has(key: c) || :canUnwindMethodNames:has(key: c) }, {
							hits: true;
						});
						ki++;
					});
					if({ hits }, {
						:canUnwindCallees:set(key: sym, value: true);
						local String is bname: methodBareNames:get(index: idx, default: '');
						if({ bname != 'init' }, {
							:canUnwindMethodNames:set(key: bname, value: true);
						});
						changed: true;
					});
				});
				idx++;
			});
		});
	}

	local Function of Boolean is shouldEmitUnwindCheck(String is callee){
		if({ :isUnmanagedClass }, { return false; });
		if({ !:clsQNameMap:has(key: 'Pool') }, { return false; });
		if({ :currentMethod == 'destroy' || :currentMethod:endsWith(suffix: '__ensure') || :currentMethod:endsWith(suffix: '__lazy_init') }, {
			return false;
		});
		if({ callee == '__indirect__' }, {
			return true;
		});
		if({ :canUnwindCallees:has(key: callee) }, {
			return true;
		});
		local Int is uIdx: callee:indexOf(search: '_', default: -1);
		if({ uIdx > 0 }, {
			local String is cPref: callee:substring(start: 0, end: uIdx);
			local String is mPart: callee:substring(start: uIdx + 1, end: callee:length());
			if({ :sysinternalClasses:has(key: cPref) || cPref == 'Arc' || cPref == 'Slab' || cPref == 'Heap' || cPref == 'Pool' || cPref == 'Arena' || cPref == 'Intern' }, {
				return false;
			});
			if({ mPart != 'init' && :canUnwindMethodNames:has(key: mPart) }, {
				return true;
			});
		});
		return false;
	}

	Function is emitUnwindCurrentFrame(Boolean is recordFrame){
		if({ recordFrame && :clsQNameMap:has(key: 'Pool') }, {
			local String is cStr: :emitConstStrVal(value: :currentClass);
			local String is mStr: :emitConstStrVal(value: :currentMethod);
			local String is fStr: :emitConstStrVal(value: :curFn:sourceFile);
			local String is lVal: :nextTmp();
			:emit(inst: IrInst:ConstInt(dst: lVal, value: :currentLine));
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Pool_recordPendingFrame', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:I64], args: ['null', cStr, mStr, fStr, lVal]));
		});
		if({ :curFnErrHandlerCallee != '' && :curFnErrPushedSlot != '' }, {
			local String is pushedVal: :nextTmp();
			:emit(inst: IrInst:Load(dst: pushedVal, slot: :curFnErrPushedSlot, ty: IrType:I1));
			local String is handleLbl: :nextLabel(prefix: 'err_handle');
			local String is exitLbl: :nextLabel(prefix: 'err_exit');
			:terminate(inst: IrInst:CondBr(cond: pushedVal, thenLabel: handleLbl, elseLabel: exitLbl));

			local IrBlock is handleBlk: :curFn:addBlock(label: handleLbl);
			:switchBlock(blk: handleBlk);
			local String is trueB: :nextTmp();
			:emit(inst: IrInst:ConstBool(dst: trueB, value: true));
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Pool_popErrorHandler', argTypes: [IrType:Ptr, IrType:I1], args: ['null', trueB]));
			local String is falseB: :nextTmp();
			:emit(inst: IrInst:ConstBool(dst: falseB, value: false));
			:emit(inst: IrInst:Store(slot: :curFnErrPushedSlot, val: falseB, ty: IrType:I1));

			local String is errAddr: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: errAddr, hasDst: true, retType: IrType:I64, callee: 'Pool_takePendingError', argTypes: [IrType:Ptr], args: ['null']));
			local String is errPtr: :nextTmp();
			:emit(inst: IrInst:IrCast(dst: errPtr, val: errAddr, fromType: IrType:I64, toType: IrType:Ptr));
			local String is selfVal: :emitLoadLocal(name: ':', ty: IrType:Ptr);
			local IrStruct is curSt: :mod:findStruct(name: :currentClass);
			local Int is ehSlot: curSt:vtableSlot(mname: 'SpecErrorHandler');
			if({ ehSlot >= 0 }, {
				local String is vtPtrAddr: :nextTmp();
				:emit(inst: IrInst:FieldPtr(dst: vtPtrAddr, objPtr: selfVal, structName: :currentClass, fieldIndex: 1));
				local String is vtBase: :nextTmp();
				:emit(inst: IrInst:Load(dst: vtBase, slot: vtPtrAddr, ty: IrType:Ptr));
				local String is slotPtr: :nextTmp();
				:emit(inst: IrInst:PtrElem(dst: slotPtr, basePtr: vtBase, index: ehSlot));
				local String is fnPtr: :nextTmp();
				:emit(inst: IrInst:Load(dst: fnPtr, slot: slotPtr, ty: IrType:Ptr));
				:emit(inst: IrInst:IndirectCall(dst: '', hasDst: false, retType: IrType:Void, fnPtr: fnPtr, argTypes: [IrType:Ptr, IrType:Ptr], args: [selfVal, errPtr]));
			}, {
				:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: :curFnErrHandlerCallee, argTypes: [IrType:Ptr, IrType:Ptr], args: [selfVal, errPtr]));
			});
			:emit(inst: IrInst:Release(val: errPtr));
			:terminate(inst: IrInst:Br(target: exitLbl));

			local IrBlock is exitBlk: :curFn:addBlock(label: exitLbl);
			:switchBlock(blk: exitBlk);
		});
		:emitReleaseOwnedLocals();
		:emitPoolExit();
		if({ :curFn:retType == IrType:Void }, {
			:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
		}, {
			local String is defVal: :emitDefaultVal(ty: :curFn:retType);
			:terminate(inst: IrInst:Ret(hasVal: true, val: defVal, ty: :curFn:retType));
		});
	}

	Function is emitCheckUnwindAfterCall(String is callee){
		if({ !:shouldEmitUnwindCheck(callee: callee) }, { return; });
		local String is fifteenVal: :nextTmp();
		:emit(inst: IrInst:ConstInt(dst: fifteenVal, value: 15));
		local String is pendAddr: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: pendAddr, hasDst: true, retType: IrType:I64, callee: '__spec_mem_tls_get_i64', argTypes: [IrType:I64], args: [fifteenVal]));
		local String is zeroAddr: :nextTmp();
		:emit(inst: IrInst:ConstInt(dst: zeroAddr, value: 0));
		local String is hasPend: :nextTmp();
		:emit(inst: IrInst:Cmp(dst: hasPend, op: '!=', lhs: pendAddr, rhs: zeroAddr, ty: IrType:I64));
		local String is unwindLbl: :nextLabel(prefix: 'err_unwind');
		local String is contLbl: :nextLabel(prefix: 'err_cont');
		:terminate(inst: IrInst:CondBr(cond: hasPend, thenLabel: unwindLbl, elseLabel: contLbl));

		local IrBlock is unwindBlk: :curFn:addBlock(label: unwindLbl);
		:switchBlock(blk: unwindBlk);
		:emitUnwindCurrentFrame(recordFrame: true);

		local IrBlock is contBlk: :curFn:addBlock(label: contLbl);
		:switchBlock(blk: contBlk);
	}

	local Function is emitReleaseOwnedLocals(){
		if({ :curFnErrPushedSlot != '' }, {
			local String is pushedNow: :nextTmp();
			:emit(inst: IrInst:Load(dst: pushedNow, slot: :curFnErrPushedSlot, ty: IrType:I1));
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Pool_popErrorHandler', argTypes: [IrType:Ptr, IrType:I1], args: ['null', pushedNow]));
			local String is falseVal: :nextTmp();
			:emit(inst: IrInst:ConstBool(dst: falseVal, value: false));
			:emit(inst: IrInst:Store(slot: :curFnErrPushedSlot, val: falseVal, ty: IrType:I1));
		});
		local Int is oi: 0;
		while({ oi < :ownedSlots:length() }, {
			local String is oslot: :ownedSlots:get(index: oi, default: '');
			local String is oval: :nextTmp();
			:emit(inst: IrInst:Load(dst: oval, slot: oslot, ty: IrType:Ptr));
			:emit(inst: IrInst:Release(val: oval));
			oi++;
		});
	}

	Function of String is emitDefaultVal(IrType is ty){
		local String is tmp: :nextTmp();
		if({ ty == IrType:I64 }, {
			:emit(inst: IrInst:ConstInt(dst: tmp, value: 0));
			return tmp;
		});
		if({ ty == IrType:F64 }, {
			:emit(inst: IrInst:ConstFloat(dst: tmp, text: '0.0'));
			return tmp;
		});
		if({ ty == IrType:I1 }, {
			:emit(inst: IrInst:ConstBool(dst: tmp, value: false));
			return tmp;
		});
		return 'null';
	}

	Function is lowerStmts(Array of Statement is stmts){
		local Int is i: 0;
		while({ i < stmts:length() && !:blkTerminated }, {
			:lowerStmt(stmt: stmts:get(index: i));
			i++;
		});
	}

	Function is lowerStmt(Statement is stmt){
		local Int is prevLine: :currentLine;
		if({ stmt:line > 0 }, { :currentLine: stmt:line; });
		match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				local IrType is vty: :irTypeFor(specType: varType:name);
				local Boolean is vIsArc: :isArcSpecType(specType: varType:name);
				local String is slot: '%var_' . varName . '_' . (:nextTmp());
				# Clean '%' from slot suffix so LLVM identifier is valid
				slot: '%var_' . varName . '_' . (:tmpCounter as String);
				local Boolean is isBoxed: :capturedNames:has(key: varName);
				:bindLocal(name: varName, slot: slot, ty: vty, isArc: vIsArc, specType: varType:name, isBoxed: isBoxed);
				local Boolean is declInEntry: :curBlk:label == 'entry';
				if({ isBoxed }, {
					:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
				}, {
					:emit(inst: IrInst:Alloca(slot: slot, ty: vty));
				});
				if({ hasInit }, {
					if({ :isLazyCallExpr(expr: initExpr) }, {
						local String is _stmp: :nextTmp();
						local String is stateSlot: '%lazy_state_' . varName . '_' . (:tmpCounter as String);
						:emit(inst: IrInst:Alloca(slot: stateSlot, ty: IrType:I64));
						local String is zeroState: :nextTmp();
						:emit(inst: IrInst:ConstInt(dst: zeroState, value: 0));
						:emit(inst: IrInst:Store(slot: stateSlot, val: zeroState, ty: IrType:I64));
						:lazyLocalStateSlots:set(key: varName, value: stateSlot);
						:lazyLocalExprs:set(key: varName, value: :getLazyBodyExpr(expr: initExpr));
						local String is lDefVal: :emitDefaultVal(ty: vty);
						if({ (vIsArc || isBoxed) && !declInEntry }, {
							local String is prevLazyVal: :nextTmp();
							:emit(inst: IrInst:Load(dst: prevLazyVal, slot: slot, ty: IrType:Ptr));
							:emit(inst: IrInst:Release(val: prevLazyVal));
						});
						if({ isBoxed }, {
							local String is lBoxPtr: :emitNewBox(initVal: lDefVal, ty: vty, isArc: vIsArc);
							:emit(inst: IrInst:Store(slot: slot, val: lBoxPtr, ty: IrType:Ptr));
						}, {
							:emit(inst: IrInst:Store(slot: slot, val: lDefVal, ty: vty));
						});
					}, {
						local String is prevMapK: :expectedMapKeyType;
						local String is prevMapV: :expectedMapValType;
						if({ varType:name == 'Map' && varType:params:length() >= 1 }, {
							local Type is mkp0: varType:params:get(index: 0);
							:expectedMapKeyType: mkp0:name;
							if({ varType:params:length() >= 2 }, {
								local Type is mkp1: varType:params:get(index: 1);
								:expectedMapValType: mkp1:name;
							});
						});
						local String is val: :lowerExpr(expr: initExpr);
						:expectedMapKeyType: prevMapK;
						:expectedMapValType: prevMapV;
						local IrType is initTy: :irTypeFor(specType: initExpr:resolvedType);
						val: :castIfNeeded(val: val, fromTy: initTy, toTy: vty);
						if({ val == '' }, { val: :emitDefaultVal(ty: vty); });
						local Boolean is isStrLitInit: false;
						match(on: initExpr, when: [
							Expression:StringLit: local Function(String is sv){ isStrLitInit: true; }
						], default: {});
						local Boolean is strCopyOwned: false;
						if({ varType:name == 'String' && isStrLitInit && val != '' && val != 'null' }, {
							local String is strCopy: :nextTmp();
							:emit(inst: IrInst:IrCall(dst: strCopy, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_copy', argTypes: [IrType:Ptr], args: [val]));
							if({ isBoxed }, {
								:emitClaimPool(val: strCopy);
							}, {
								strCopyOwned: true;
							});
							val: strCopy;
						});
						if({ vIsArc && !strCopyOwned && val != '' && val != 'null' }, {
							:emit(inst: IrInst:Retain(val: val));
						});
						if({ (vIsArc || isBoxed) && !declInEntry }, {
							local String is prevSlotVal: :nextTmp();
							:emit(inst: IrInst:Load(dst: prevSlotVal, slot: slot, ty: IrType:Ptr));
							:emit(inst: IrInst:Release(val: prevSlotVal));
						});
						if({ isBoxed }, {
							local String is boxPtr: :emitNewBox(initVal: val, ty: vty, isArc: vIsArc);
							:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
						}, {
							:emit(inst: IrInst:Store(slot: slot, val: val, ty: vty));
						});
					});
				}, {
					local String is defVal: :emitDefaultVal(ty: vty);
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
						defVal: :nextTmp();
						:emit(inst: IrInst:IrCall(dst: defVal, hasDst: true, retType: IrType:Ptr, callee: 'Vector_byteBufNew', argTypes: [], args: []));
						:emitClaimPool(val: defVal);
						:emit(inst: IrInst:Retain(val: defVal));
					}, {
						if({ varType:name == 'List' || varType:name:startsWith(prefix: 'List of ') || varType:name:startsWith(prefix: 'List:') }, {
							local String is vecCtor: 'Vector_vecNewObject';
							if({ listElem != '' && !:isArcSpecType(specType: listElem) }, {
								vecCtor: 'Vector_vecNew';
							});
							defVal: :nextTmp();
							:emit(inst: IrInst:IrCall(dst: defVal, hasDst: true, retType: IrType:Ptr, callee: vecCtor, argTypes: [], args: []));
							:emitClaimPool(val: defVal);
							:emit(inst: IrInst:Retain(val: defVal));
						});
					});
					if({ (vIsArc || isBoxed) && !declInEntry }, {
						local String is prevSlotVal2: :nextTmp();
						:emit(inst: IrInst:Load(dst: prevSlotVal2, slot: slot, ty: IrType:Ptr));
						:emit(inst: IrInst:Release(val: prevSlotVal2));
					});
					if({ isBoxed }, {
						local String is boxPtr: :emitNewBox(initVal: defVal, ty: vty, isArc: vIsArc);
						:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
					}, {
						:emit(inst: IrInst:Store(slot: slot, val: defVal, ty: vty));
					});
				});
				if({ vIsArc || isBoxed }, {
					:ownedSlots:add(item: slot);
				});
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				if({ :tryLowerAppendChain(assignTarget: assignTarget, assignValue: assignValue) }, {
					:currentLine: prevLine;
					return;
				});
				local String is prevMapK: :expectedMapKeyType;
				local String is prevMapV: :expectedMapValType;
				:setAssignTargetMapHints(assignTarget: assignTarget);
				local String is val: :lowerExpr(expr: assignValue);
				:expectedMapKeyType: prevMapK;
				:expectedMapValType: prevMapV;
				local IrType is valTy: :irTypeFor(specType: assignValue:resolvedType);
				match(on: assignTarget, when: [
					Expression:Ident: local Function(String is name){
						if({ :localSlots:has(key: name) }, {
							local IrType is ty: :localTypes:get(key: name, default: IrType:I64);
							local Boolean is isArc: :localIsArc:get(key: name, default: false);
							local String is cval: :castIfNeeded(val: val, fromTy: valTy, toTy: ty);
							local Boolean is isStrLitAsgn: false;
							match(on: assignValue, when: [
								Expression:StringLit: local Function(String is _sv){ isStrLitAsgn: true; }
							], default: {});
							if({ isStrLitAsgn && !:boxedLocals:has(key: name) && (:localSpecTypes:get(key: name, default: '') == 'String' || :localSpecTypes:get(key: name, default: '') == 'Str') && cval != '' && cval != 'null' }, {
								if({ :lazyLocalStateSlots:has(key: name) }, {
									local String is stSlot: :lazyLocalStateSlots:get(key: name, default: '');
									local String is twoV: :nextTmp();
									:emit(inst: IrInst:ConstInt(dst: twoV, value: 2));
									:emit(inst: IrInst:Store(slot: stSlot, val: twoV, ty: IrType:I64));
								});
								local String is slot: :localSlots:get(key: name, default: '');
								local String is strCopy: :nextTmp();
								:emit(inst: IrInst:IrCall(dst: strCopy, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_copy', argTypes: [IrType:Ptr], args: [cval]));
								local String is oldVal: :nextTmp();
								:emit(inst: IrInst:Load(dst: oldVal, slot: slot, ty: IrType:Ptr));
								:emit(inst: IrInst:Release(val: oldVal));
								:emit(inst: IrInst:Store(slot: slot, val: strCopy, ty: IrType:Ptr));
							}, {
								:emitStoreLocal(name: name, val: cval, ty: ty, isArc: isArc);
							});
						}, {
							local String is hk: :currentClass . ':' . name;
							if({ :heldFields:has(key: hk) }, {
								local String is owner: :heldFields:get(key: hk, default: '');
								local IrType is hty: :irTypeFor(specType: :heldFieldTypes:get(key: owner . ':' . name, default: ''));
								if({ hty == IrType:Void }, { hty: IrType:Ptr; });
								local String is trueTmp: :nextTmp();
								:emit(inst: IrInst:ConstBool(dst: trueTmp, value: true));
								:emit(inst: IrInst:Store(slot: '@.held_init.' . owner . '.' . name, val: trueTmp, ty: IrType:I1));
								:emit(inst: IrInst:Store(slot: '@.held_val.' . owner . '.' . name, val: val, ty: hty));
							}, {
								if({ :localSlots:has(key: ':') }, {
									local IrStruct is selfSt: :mod:findStruct(name: :currentClass);
									local Int is sfidx: selfSt:fieldIndex(name: name);
									if({ sfidx >= 0 }, {
										local String is selfObj: :emitLoadLocal(name: ':', ty: IrType:Ptr);
										local IrType is sfty: selfSt:fieldTypes:get(index: sfidx);
										local Boolean is sfIsArc: selfSt:fieldIsArc:get(index: sfidx, default: false);
										local String is scval: :castIfNeeded(val: val, fromTy: valTy, toTy: sfty);
										local String is sptr: :nextTmp();
										:emit(inst: IrInst:FieldPtr(dst: sptr, objPtr: selfObj, structName: :currentClass, fieldIndex: sfidx));
										if({ sfIsArc }, {
											if({ scval != '' && scval != 'null' }, {
												:emit(inst: IrInst:Retain(val: scval));
											});
											local String is oldSfVal: :nextTmp();
											:emit(inst: IrInst:Load(dst: oldSfVal, slot: sptr, ty: IrType:Ptr));
											:emit(inst: IrInst:Release(val: oldSfVal));
										});
										:emit(inst: IrInst:Store(slot: sptr, val: scval, ty: sfty));
										:emitMarkLazyFieldDone(objPtr: selfObj, sname: :currentClass, st: selfSt, fieldName: name);
									});
								});
							});
						});
					},
					Expression:FieldAccess: local Function(Expression is target, String is fieldName){
						local String is obj: :lowerExpr(expr: target);
						local String is sname: :structNameForExpr(expr: target);
						local IrStruct is st: :mod:findStruct(name: sname);
						local Int is fidx: st:fieldIndex(name: fieldName);
						if({ fidx >= 0 }, {
							local IrType is fty: st:fieldTypes:get(index: fidx);
							local Boolean is fIsArc: st:fieldIsArc:get(index: fidx, default: false);
							local String is cval: :castIfNeeded(val: val, fromTy: valTy, toTy: fty);
							local String is ptr: :nextTmp();
							:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: sname, fieldIndex: fidx));
							if({ fIsArc }, {
								if({ cval != '' && cval != 'null' }, {
									:emit(inst: IrInst:Retain(val: cval));
								});
								local String is oldFVal: :nextTmp();
								:emit(inst: IrInst:Load(dst: oldFVal, slot: ptr, ty: IrType:Ptr));
								:emit(inst: IrInst:Release(val: oldFVal));
							});
							:emit(inst: IrInst:Store(slot: ptr, val: cval, ty: fty));
							:emitMarkLazyFieldDone(objPtr: obj, sname: sname, st: st, fieldName: fieldName);
						});
					},
					Expression:Path: local Function(Array of String is segments){
						if({ segments:length() >= 2 }, {
							local String is seg0: segments:get(index: 0, default: '');
							local String is seg1: segments:get(index: 1, default: '');
							if({ segments:length() == 2 && !:localSlots:has(key: seg0) && :heldFields:has(key: seg0 . ':' . seg1) }, {
								local String is owner: :heldFields:get(key: seg0 . ':' . seg1, default: '');
								local IrType is hty: :irTypeFor(specType: :heldFieldTypes:get(key: owner . ':' . seg1, default: ''));
								if({ hty == IrType:Void }, { hty: IrType:Ptr; });
								local String is trueTmp: :nextTmp();
								:emit(inst: IrInst:ConstBool(dst: trueTmp, value: true));
								:emit(inst: IrInst:Store(slot: '@.held_init.' . owner . '.' . seg1, val: trueTmp, ty: IrType:I1));
								:emit(inst: IrInst:Store(slot: '@.held_val.' . owner . '.' . seg1, val: val, ty: hty));
							}, {
								local Int is fidx: :resolvePathField(segments: segments);
								if({ fidx >= 0 }, {
									local String is obj: :pathObjPtr;
									local String is sname: :pathStructName;
									local IrStruct is st: :mod:findStruct(name: sname);
									local IrType is fty: st:fieldTypes:get(index: fidx);
									local Boolean is fIsArc: st:fieldIsArc:get(index: fidx, default: false);
									local String is cval: :castIfNeeded(val: val, fromTy: valTy, toTy: fty);
									local String is ptr: :nextTmp();
									:emit(inst: IrInst:FieldPtr(dst: ptr, objPtr: obj, structName: sname, fieldIndex: fidx));
									if({ fIsArc }, {
										if({ cval != '' && cval != 'null' }, {
											:emit(inst: IrInst:Retain(val: cval));
										});
										local String is oldPVal: :nextTmp();
										:emit(inst: IrInst:Load(dst: oldPVal, slot: ptr, ty: IrType:Ptr));
										:emit(inst: IrInst:Release(val: oldPVal));
									});
									:emit(inst: IrInst:Store(slot: ptr, val: cval, ty: fty));
									:emitMarkLazyFieldDone(objPtr: obj, sname: sname, st: st, fieldName: segments:get(index: segments:length() - 1, default: ''));
								});
							});
						});
					},
					Expression:Index: local Function(Expression is target, Expression is index){
						local String is tv: :lowerExpr(expr: target);
						local String is iv: :lowerExpr(expr: index);
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
							local String is kp: :castIfNeeded(val: iv, fromTy: :irTypeFor(specType: kSpec), toTy: kArgTy);
							local String is vp: :castIfNeeded(val: val, fromTy: valTy, toTy: IrType:Ptr);
							local String is setCallee: 'HashTable_mapSet' . kSuf . 'Any';
							if({ assignValue:resolvedType == 'String' }, {
								setCallee: 'HashTable_mapSet' . kSuf;
							});
							:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: setCallee, argTypes: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr], args: ['null', tv, kp, vp]));
						}, {
							local String is idxV: :castIfNeeded(val: iv, fromTy: :irTypeFor(specType: index:resolvedType), toTy: IrType:I64);
							local String is vp: :castIfNeeded(val: val, fromTy: valTy, toTy: IrType:Ptr);
							:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecSetAt', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:Ptr], args: ['null', tv, idxV, vp]));
						});
					}
				], default: {});
			},
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ :inlineReturnEndLbl != '' }, {
					if({ hasReturnExpr && :inlineReturnSlot != '' }, {
						local String is ival: :lowerExpr(expr: returnExpr);
						local IrType is ivalTy: :irTypeFor(specType: returnExpr:resolvedType);
						ival: :castIfNeeded(val: ival, fromTy: ivalTy, toTy: :inlineReturnTy);
						:emit(inst: IrInst:Store(slot: :inlineReturnSlot, val: ival, ty: :inlineReturnTy));
					});
					:terminate(inst: IrInst:Br(target: :inlineReturnEndLbl));
					return;
				});
				if({ hasReturnExpr && :curFn:retType != IrType:Void }, {
					local String is val: :lowerExpr(expr: returnExpr);
					local IrType is valTy: :irTypeFor(specType: returnExpr:resolvedType);
					val: :castIfNeeded(val: val, fromTy: valTy, toTy: :curFn:retType);
					if({ val == '' }, {
						val: :emitDefaultVal(ty: :curFn:retType);
					});
					if({ val == '0' && :curFn:retType == IrType:Ptr }, {
						val: 'null';
					});
					local Boolean is retExprIsArc: :isArcSpecType(specType: returnExpr:resolvedType);
					if({ (:curFnRetIsArc || retExprIsArc) && :curFn:retType == IrType:Ptr && val != 'null' }, {
						:emit(inst: IrInst:Retain(val: val));
					});
					:emitReleaseOwnedLocals();
					:emitPoolExit();
					if({ :curFnRetIsArc && :curFn:retType == IrType:Ptr && val != 'null' }, {
						:emitClaimPool(val: val);
					});
					:terminate(inst: IrInst:Ret(hasVal: true, val: val, ty: :curFn:retType));
				}, {
					if({ hasReturnExpr }, {
						local String is _unusedRet: :lowerExpr(expr: returnExpr);
					});
					:emitReleaseOwnedLocals();
					:emitPoolExit();
					:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
				});
			},
			Statement:Forward: local Function(Array of NamedArg is args){
				local String is parentFn: :findParentMethodImpl(clsName: :currentClass, methodName: :currentMethod, suffix: '');
				if({ parentFn != '' }, {
					local Array of IrType is fArgT: [IrType:Ptr];
					local Array of String is fArgV: [:emitLoadLocal(name: ':', ty: IrType:Ptr)];
					:lowerCallArgs(fnKey: parentFn, callArgs: args, argTypes: fArgT, argVals: fArgV);
					local IrType is fRetTy: :methodRetTypes:get(key: parentFn, default: IrType:Void);
					local Boolean is fHasDst: fRetTy != IrType:Void;
					local String is fDst: '';
					if({ fHasDst }, { fDst: :nextTmp(); });
					:emit(inst: IrInst:IrCall(dst: fDst, hasDst: fHasDst, retType: fRetTy, callee: parentFn, argTypes: fArgT, args: fArgV));
					if({ fHasDst }, {
						if({ :curFnRetIsArc && fRetTy == IrType:Ptr && fDst != 'null' }, {
							:emit(inst: IrInst:Retain(val: fDst));
						});
						:emitReleaseOwnedLocals();
						:emitPoolExit();
						if({ :curFnRetIsArc && fRetTy == IrType:Ptr && fDst != 'null' }, {
							:emitClaimPool(val: fDst);
						});
						:terminate(inst: IrInst:Ret(hasVal: true, val: fDst, ty: fRetTy));
					}, {
						:emitReleaseOwnedLocals();
						:emitPoolExit();
						:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
					});
				});
			},
			Statement:Expr: local Function(Expression is exprStmt){
				local String is _u0: :lowerExpr(expr: exprStmt);
			}
		], default: {});
		:currentLine: prevLine;
	}

	local Function is setMapHintsFromTypeStr(String is t){
		local Int is toIdx: t:indexOf(search: ' to ', default: -1);
		if({ t:startsWith(prefix: 'Map of ') && toIdx > 7 }, {
			:expectedMapKeyType: t:substring(start: 7, end: toIdx);
			:expectedMapValType: t:substring(start: toIdx + 4, end: t:length());
			return;
		});
		if({ t:startsWith(prefix: 'Map:') }, {
			local String is afterMap: t:substring(start: 4, end: t:length());
			local Int is cIdx: afterMap:indexOf(search: ':', default: -1);
			if({ cIdx > 0 }, {
				:expectedMapKeyType: afterMap:substring(start: 0, end: cIdx);
				:expectedMapValType: afterMap:substring(start: cIdx + 1, end: afterMap:length());
			});
		});
	}

	local Function is setAssignTargetMapHints(Expression is assignTarget){
		if({ assignTarget:resolvedType != '' && assignTarget:resolvedType != 'Map' }, {
			:setMapHintsFromTypeStr(t: assignTarget:resolvedType);
			if({ :expectedMapKeyType != '' }, { return; });
		});
		match(on: assignTarget, when: [
			Expression:Ident: local Function(String is name){
				if({ :localSpecTypes:has(key: name) }, {
					:setMapHintsFromTypeStr(t: :localSpecTypes:get(key: name, default: ''));
				}, {
					if({ :fieldSpecTypes:has(key: :currentClass . ':' . name) }, {
						:setMapHintsFromTypeStr(t: :fieldSpecTypes:get(key: :currentClass . ':' . name, default: ''));
					});
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				local String is sname: :structNameForExpr(expr: target);
				if({ :fieldSpecTypes:has(key: sname . ':' . fieldName) }, {
					:setMapHintsFromTypeStr(t: :fieldSpecTypes:get(key: sname . ':' . fieldName, default: ''));
				});
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() == 2 && segs:get(index: 0, default: '') == ':' }, {
					local String is fn: segs:get(index: 1, default: '');
					if({ :fieldSpecTypes:has(key: :currentClass . ':' . fn) }, {
						:setMapHintsFromTypeStr(t: :fieldSpecTypes:get(key: :currentClass . ':' . fn, default: ''));
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
				if({ :collectAppendChainRhs(expr: left, targetName: targetName, rhsOut: rhsOut) }, {
					rhsOut:add(item: right);
					return true;
				});
				return false;
			},
			else: { false }
		]);
	}

	local Function of String is lowerConcatRight(Expression is right){
		local String is r: :lowerExpr(expr: right);
		local IrType is rTy: :irTypeFor(specType: right:resolvedType);
		if({ rTy == IrType:I64 }, {
			local String is rsI: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: rsI, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToString', argTypes: [IrType:Ptr, IrType:I64], args: ['null', r]));
			return rsI;
		});
		if({ rTy == IrType:F64 }, {
			local String is rsF: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: rsF, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_float', argTypes: [IrType:F64], args: [r]));
			:emitClaimPool(val: rsF);
			return rsF;
		});
		if({ rTy == IrType:I1 }, {
			local String is rsB: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: rsB, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_bool', argTypes: [IrType:I1], args: [r]));
			:emitClaimPool(val: rsB);
			return rsB;
		});
		if({ rTy == IrType:Ptr && right:resolvedType != 'String' && right:resolvedType != 'Str' && (:clsMap:has(key: right:resolvedType) || right:resolvedType == 'Any') }, {
			return :emitObjectToString(objVal: r, specType: right:resolvedType);
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
						ls: :lowerConcatChainNoClaim(expr: left);
					}, {
						local String is l: :lowerExpr(expr: left);
						local IrType is lTy: :irTypeFor(specType: left:resolvedType);
						if({ lTy == IrType:I64 }, {
							ls: :nextTmp();
							:emit(inst: IrInst:IrCall(dst: ls, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToString', argTypes: [IrType:Ptr, IrType:I64], args: ['null', l]));
						}, {
							if({ lTy == IrType:F64 }, {
								ls: :nextTmp();
								:emit(inst: IrInst:IrCall(dst: ls, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_float', argTypes: [IrType:F64], args: [l]));
								:emitClaimPool(val: ls);
							}, {
								if({ lTy == IrType:I1 }, {
									ls: :nextTmp();
									:emit(inst: IrInst:IrCall(dst: ls, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_bool', argTypes: [IrType:I1], args: [l]));
									:emitClaimPool(val: ls);
								}, {
									ls: l;
								});
							});
						});
					});
					local String is rs: :lowerConcatRight(right: right);
					local String is dst: :nextTmp();
					:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'String_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [ls, rs]));
					return dst;
				});
				return :lowerExpr(expr: expr);
			},
			else: { :lowerExpr(expr: expr) }
		]);
	}

	local Function of Boolean is tryLowerAppendChain(Expression is assignTarget, Expression is assignValue){
		local String is targetName: match(on: assignTarget, when: [
			Expression:Ident: local Function of String(String is nm){ return nm; },
			else: { '' }
		]);
		if({ targetName == '' || !:localSlots:has(key: targetName) || :boxedLocals:has(key: targetName) || :lazyLocalStateSlots:has(key: targetName) }, {
			return false;
		});
		if({ :localSpecTypes:get(key: targetName, default: '') != 'String' && :localSpecTypes:get(key: targetName, default: '') != 'Str' }, {
			return false;
		});
		local Array of Expression is rhsList: [];
		if({ !:collectAppendChainRhs(expr: assignValue, targetName: targetName, rhsOut: rhsList) || rhsList:length() == 0 }, {
			return false;
		});
		local String is slot: :localSlots:get(key: targetName, default: '');
		local String is curVal: :nextTmp();
		:emit(inst: IrInst:Load(dst: curVal, slot: slot, ty: IrType:Ptr));
		local Int is ri: 0;
		while({ ri < rhsList:length() }, {
			local String is rs: :lowerConcatRight(right: rhsList:get(index: ri));
			local String is nextVal: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: nextVal, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [curVal, rs]));
			curVal: nextVal;
			ri++;
		});
		:emit(inst: IrInst:Store(slot: slot, val: curVal, ty: IrType:Ptr));
		return true;
	}

	local Function of String is lowerIncDec(String is op, Expression is operand, IrType is ty){
		local String is localName: '';
		local String is slot: '';
		local IrType is slotTy: ty;
		local String is fldObj: '';
		local String is fldSname: '';
		local IrStruct is fldSt: IrStruct:init();
		local Int is fldIdx: -1;
		local String is fldName: '';
		match(on: operand, when: [
			Expression:Ident: local Function(String is name){
				if({ :localSlots:has(key: name) }, {
					slot: :localSlots:get(key: name, default: '');
					slotTy: :localTypes:get(key: name, default: ty);
					localName: name;
				}, {
					if({ :localSlots:has(key: ':') }, {
						local IrStruct is selfSt: :mod:findStruct(name: :currentClass);
						local Int is sfidx: selfSt:fieldIndex(name: name);
						if({ sfidx >= 0 }, {
							local String is selfObj: :emitLoadLocal(name: ':', ty: IrType:Ptr);
							slotTy: selfSt:fieldTypes:get(index: sfidx);
							slot: :nextTmp();
							:emit(inst: IrInst:FieldPtr(dst: slot, objPtr: selfObj, structName: :currentClass, fieldIndex: sfidx));
							fldObj: selfObj;
							fldSname: :currentClass;
							fldSt: selfSt;
							fldIdx: sfidx;
							fldName: name;
						});
					});
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				local String is obj: :lowerExpr(expr: target);
				local String is sname: :structNameForExpr(expr: target);
				local IrStruct is st: :mod:findStruct(name: sname);
				local Int is fidx: st:fieldIndex(name: fieldName);
				if({ fidx >= 0 }, {
					slotTy: st:fieldTypes:get(index: fidx);
					slot: :nextTmp();
					:emit(inst: IrInst:FieldPtr(dst: slot, objPtr: obj, structName: sname, fieldIndex: fidx));
					fldObj: obj;
					fldSname: sname;
					fldSt: st;
					fldIdx: fidx;
					fldName: fieldName;
				});
			},
			Expression:Path: local Function(Array of String is segments){
				local Int is fidx: :resolvePathField(segments: segments);
				if({ fidx >= 0 }, {
					local String is obj: :pathObjPtr;
					local String is sname: :pathStructName;
					local IrStruct is st: :mod:findStruct(name: sname);
					slotTy: st:fieldTypes:get(index: fidx);
					slot: :nextTmp();
					:emit(inst: IrInst:FieldPtr(dst: slot, objPtr: obj, structName: sname, fieldIndex: fidx));
					fldObj: obj;
					fldSname: sname;
					fldSt: st;
					fldIdx: fidx;
					fldName: segments:get(index: segments:length() - 1, default: '');
				});
			}
		], default: {});
		if({ slot == '' && localName == '' }, {
			return :emitDefaultVal(ty: ty);
		});
		local String is oldVal: '';
		if({ localName != '' }, {
			oldVal: :emitLoadLocal(name: localName, ty: slotTy);
		}, {
			if({ fldIdx >= 0 }, {
				oldVal: :emitLoadField(objPtr: fldObj, sname: fldSname, st: fldSt, fidx: fldIdx, fieldName: fldName);
			}, {
				oldVal: :nextTmp();
				:emit(inst: IrInst:Load(dst: oldVal, slot: slot, ty: slotTy));
			});
		});
		local String is one: :nextTmp();
		if({ slotTy == IrType:F64 }, {
			:emit(inst: IrInst:ConstFloat(dst: one, text: '1.0'));
		}, {
			:emit(inst: IrInst:ConstInt(dst: one, value: 1));
		});
		local String is binOp: if({ op == 'post++' || op == '++' }, { '+' }, { '-' });
		local String is newVal: :nextTmp();
		:emit(inst: IrInst:BinOp(dst: newVal, op: binOp, lhs: oldVal, rhs: one, ty: slotTy));
		if({ localName != '' }, {
			:emitStoreLocal(name: localName, val: newVal, ty: slotTy, isArc: false);
		}, {
			:emit(inst: IrInst:Store(slot: slot, val: newVal, ty: slotTy));
			if({ fldIdx >= 0 }, {
				:emitMarkLazyFieldDone(objPtr: fldObj, sname: fldSname, st: fldSt, fieldName: fldName);
			});
		});
		if({ op == 'post++' || op == 'post--' }, {
			return oldVal;
		});
		return newVal;
	}

	local Function of String is emitObjectToString(String is objVal, String is specType){
		if({ specType != '' && specType != 'Any' }, {
			local String is sname: :cStructName(qname: specType);
			local IrStruct is st: :mod:findStruct(name: sname);
			local Int is tsSlot: st:vtableSlot(mname: 'toString');
			if({ tsSlot >= 0 }, {
				local String is vtPtrAddr: :nextTmp();
				:emit(inst: IrInst:FieldPtr(dst: vtPtrAddr, objPtr: objVal, structName: sname, fieldIndex: 1));
				local String is vtBase: :nextTmp();
				:emit(inst: IrInst:Load(dst: vtBase, slot: vtPtrAddr, ty: IrType:Ptr));
				local String is slotPtr: :nextTmp();
				:emit(inst: IrInst:PtrElem(dst: slotPtr, basePtr: vtBase, index: tsSlot));
				local String is fnPtr: :nextTmp();
				:emit(inst: IrInst:Load(dst: fnPtr, slot: slotPtr, ty: IrType:Ptr));
				local String is hasTs: :nextTmp();
				:emit(inst: IrInst:Cmp(dst: hasTs, op: '!=', lhs: fnPtr, rhs: 'null', ty: IrType:Ptr));
				local String is tsResSlot: :nextTmp();
				:emit(inst: IrInst:Alloca(slot: tsResSlot, ty: IrType:Ptr));
				local String is tsCallLbl: :nextLabel(prefix: 'ts_call');
				local String is tsFallbackLbl: :nextLabel(prefix: 'ts_fb');
				local String is tsEndLbl: :nextLabel(prefix: 'ts_end');
				:terminate(inst: IrInst:CondBr(cond: hasTs, thenLabel: tsCallLbl, elseLabel: tsFallbackLbl));
				local IrBlock is tsCallBlk: :curFn:addBlock(label: tsCallLbl);
				:switchBlock(blk: tsCallBlk);
				local String is tsDst: :nextTmp();
				:emit(inst: IrInst:IndirectCall(dst: tsDst, hasDst: true, retType: IrType:Ptr, fnPtr: fnPtr, argTypes: [IrType:Ptr], args: [objVal]));
				:emitClaimPool(val: tsDst);
				:emit(inst: IrInst:Store(slot: tsResSlot, val: tsDst, ty: IrType:Ptr));
				:terminate(inst: IrInst:Br(target: tsEndLbl));
				local IrBlock is tsFbBlk: :curFn:addBlock(label: tsFallbackLbl);
				:switchBlock(blk: tsFbBlk);
				local String is fbTn: :nextTmp();
				:emit(inst: IrInst:IrCall(dst: fbTn, hasDst: true, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: [IrType:Ptr], args: [objVal]));
				:emit(inst: IrInst:Store(slot: tsResSlot, val: fbTn, ty: IrType:Ptr));
				:terminate(inst: IrInst:Br(target: tsEndLbl));
				local IrBlock is tsEndBlk: :curFn:addBlock(label: tsEndLbl);
				:switchBlock(blk: tsEndBlk);
				local String is tsFinal: :nextTmp();
				:emit(inst: IrInst:Load(dst: tsFinal, slot: tsResSlot, ty: IrType:Ptr));
				return tsFinal;
			});
		});
		local String is tnDst: :nextTmp();
		:emit(inst: IrInst:IrCall(dst: tnDst, hasDst: true, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: [IrType:Ptr], args: [objVal]));
		if({ specType == 'Any' }, {
			local String is strLit: :nextTmp();
			:emit(inst: IrInst:ConstString(dst: strLit, strId: :mod:internStringLiteral(value: 'String')));
			local String is isStr: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: isStr, hasDst: true, retType: IrType:I1, callee: 'Buf_stringEquals', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', tnDst, strLit]));
			local String is outSlot: '%any_ts_' . (:nextTmp());
			outSlot: '%any_ts_' . (:tmpCounter as String);
			:emit(inst: IrInst:Alloca(slot: outSlot, ty: IrType:Ptr));
			local String is sLbl: :nextLabel(prefix: 'any_ts_s');
			local String is oLbl: :nextLabel(prefix: 'any_ts_o');
			local String is eLbl: :nextLabel(prefix: 'any_ts_e');
			:terminate(inst: IrInst:CondBr(cond: isStr, thenLabel: sLbl, elseLabel: oLbl));
			local IrBlock is sBlk: :curFn:addBlock(label: sLbl);
			:switchBlock(blk: sBlk);
			:emit(inst: IrInst:Store(slot: outSlot, val: objVal, ty: IrType:Ptr));
			:terminate(inst: IrInst:Br(target: eLbl));
			local IrBlock is oBlk: :curFn:addBlock(label: oLbl);
			:switchBlock(blk: oBlk);
			:emit(inst: IrInst:Store(slot: outSlot, val: tnDst, ty: IrType:Ptr));
			:terminate(inst: IrInst:Br(target: eLbl));
			local IrBlock is eBlk: :curFn:addBlock(label: eLbl);
			:switchBlock(blk: eBlk);
			local String is finalAny: :nextTmp();
			:emit(inst: IrInst:Load(dst: finalAny, slot: outSlot, ty: IrType:Ptr));
			return finalAny;
		});
		return tnDst;
	}

	Function of String is lowerExpr(Expression is expr){
		return match(on: expr, when: [
			Expression:NumberLit: local Function(Int is value, String is text){
				local Int is v: value;
				if({ text != '' }, { v: text as Int; });
				local String is dst: :nextTmp();
				:emit(inst: IrInst:ConstInt(dst: dst, value: v));
				return dst;
			},
			Expression:FloatLit: local Function(String is text){
				local String is dst: :nextTmp();
				:emit(inst: IrInst:ConstFloat(dst: dst, text: text));
				return dst;
			},
			Expression:BoolLit: local Function(Boolean is value){
				local String is dst: :nextTmp();
				:emit(inst: IrInst:ConstBool(dst: dst, value: value));
				return dst;
			},
			Expression:StringLit: local Function(String is value){
				local Int is sid: :mod:internStringLiteral(value: value);
				local String is dst: :nextTmp();
				:emit(inst: IrInst:ConstString(dst: dst, strId: sid));
				return dst;
			},
			Expression:Ident: local Function(String is name){
				if({ :localSlots:has(key: name) }, {
					local IrType is ty: :localTypes:get(key: name, default: IrType:I64);
					return :emitLoadLocal(name: name, ty: ty);
				});
				local String is hk: :currentClass . ':' . name;
				if({ :heldFields:has(key: hk) }, {
					local String is owner: :heldFields:get(key: hk, default: '');
					local IrType is hty: :irTypeFor(specType: :heldFieldTypes:get(key: owner . ':' . name, default: ''));
					if({ hty == IrType:Void }, { hty: IrType:Ptr; });
					local String is dst: :nextTmp();
					:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: hty, callee: owner . '_' . name . '__ensure', argTypes: [], args: []));
					if({ hty == IrType:Ptr }, { :emitClaimPool(val: dst); });
					return dst;
				});
				if({ :localSlots:has(key: ':') }, {
					local IrStruct is selfSt: :mod:findStruct(name: :currentClass);
					local Int is sfidx: selfSt:fieldIndex(name: name);
					if({ sfidx >= 0 }, {
						local String is selfObj: :emitLoadLocal(name: ':', ty: IrType:Ptr);
						return :emitLoadField(objPtr: selfObj, sname: :currentClass, st: selfSt, fidx: sfidx, fieldName: name);
					});
				});
				return '0';
			},
			Expression:Unary: local Function(String is op, Expression is operand){
				local IrType is ty: :irTypeFor(specType: expr:resolvedType);
				if({ ty == IrType:Void }, { ty: IrType:I64; });
				if({ op == 'post++' || op == 'post--' || op == '++' || op == '--' }, {
					return :lowerIncDec(op: op, operand: operand, ty: ty);
				});
				local String is v: :lowerExpr(expr: operand);
				local String is dst: :nextTmp();
				:emit(inst: IrInst:UnaryOp(dst: dst, op: op, operand: v, ty: ty));
				return dst;
			},
			Expression:Binary: local Function(String is op, Expression is left, Expression is right){
				if({ op == '&&' || op == '||' }, {
					local String is resSlot: :nextTmp();
					:emit(inst: IrInst:Alloca(slot: resSlot, ty: IrType:I1));
					local String is lVal: :lowerExpr(expr: left);
					local IrType is lTy: :irTypeFor(specType: left:resolvedType);
					if({ lTy != IrType:I1 && lTy != IrType:Void }, {
						lVal: :castIfNeeded(val: lVal, fromTy: lTy, toTy: IrType:I1);
					});
					:emit(inst: IrInst:Store(slot: resSlot, val: lVal, ty: IrType:I1));
					local String is rhsLbl: :nextLabel(prefix: 'sc_rhs');
					local String is endLbl: :nextLabel(prefix: 'sc_end');
					if({ op == '&&' }, {
						:terminate(inst: IrInst:CondBr(cond: lVal, thenLabel: rhsLbl, elseLabel: endLbl));
					}, {
						:terminate(inst: IrInst:CondBr(cond: lVal, thenLabel: endLbl, elseLabel: rhsLbl));
					});
					local IrBlock is rhsBlk: :curFn:addBlock(label: rhsLbl);
					:switchBlock(blk: rhsBlk);
					local String is rVal: :lowerExpr(expr: right);
					local IrType is rTy: :irTypeFor(specType: right:resolvedType);
					if({ rTy != IrType:I1 && rTy != IrType:Void }, {
						rVal: :castIfNeeded(val: rVal, fromTy: rTy, toTy: IrType:I1);
					});
					:emit(inst: IrInst:Store(slot: resSlot, val: rVal, ty: IrType:I1));
					:terminate(inst: IrInst:Br(target: endLbl));
					local IrBlock is endBlk: :curFn:addBlock(label: endLbl);
					:switchBlock(blk: endBlk);
					local String is scDst: :nextTmp();
					:emit(inst: IrInst:Load(dst: scDst, slot: resSlot, ty: IrType:I1));
					return scDst;
				});
				if({ op == '.' }, {
					local String is catDst: :lowerConcatChainNoClaim(expr: expr);
					return catDst;
				});
				local String is l: :lowerExpr(expr: left);
				local String is r: :lowerExpr(expr: right);
				local String is dst: :nextTmp();
				if({ op == '==' || op == '!=' || op == '<' || op == '<=' || op == '>' || op == '>=' }, {
					local IrType is cmpTy: :irTypeFor(specType: left:resolvedType);
					if({ cmpTy == IrType:Void }, { cmpTy: IrType:I64; });
					local Boolean is isStrCmp: cmpTy == IrType:Ptr && (left:resolvedType == 'String' || right:resolvedType == 'String' || left:resolvedType == 'Str' || right:resolvedType == 'Str');
					if({ isStrCmp && (op == '==' || op == '!=') }, {
						local Array of IrType is sT: [IrType:Ptr, IrType:Ptr, IrType:Ptr];
						local Array of String is sV: ['null', l, r];
						if({ op == '==' }, {
							:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I1, callee: 'Buf_stringEquals', argTypes: sT, args: sV));
							return dst;
						}, {
							local String is eqTmp: :nextTmp();
							:emit(inst: IrInst:IrCall(dst: eqTmp, hasDst: true, retType: IrType:I1, callee: 'Buf_stringEquals', argTypes: sT, args: sV));
							:emit(inst: IrInst:UnaryOp(dst: dst, op: '!', operand: eqTmp, ty: IrType:I1));
							return dst;
						});
					});
					if({ isStrCmp && (op == '<' || op == '<=' || op == '>' || op == '>=') }, {
						local String is cmpRes: :nextTmp();
						:emit(inst: IrInst:IrCall(dst: cmpRes, hasDst: true, retType: IrType:I64, callee: 'Buf_stringCompare', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', l, r]));
						local String is zeroV: :nextTmp();
						:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
						:emit(inst: IrInst:Cmp(dst: dst, op: op, lhs: cmpRes, rhs: zeroV, ty: IrType:I64));
						return dst;
					});
					if({ cmpTy == IrType:Ptr }, {
						if({ l == '0' }, { l: 'null'; });
						if({ r == '0' }, { r: 'null'; });
					});
					:emit(inst: IrInst:Cmp(dst: dst, op: op, lhs: l, rhs: r, ty: cmpTy));
					return dst;
				});
				local IrType is ty: :irTypeFor(specType: expr:resolvedType);
				if({ ty == IrType:Void }, { ty: IrType:I64; });
				:emit(inst: IrInst:BinOp(dst: dst, op: op, lhs: l, rhs: r, ty: ty));
				return dst;
			},
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				local String is obj: :lowerExpr(expr: target);
				local String is sname: :structNameForExpr(expr: target);
				local IrStruct is st: :mod:findStruct(name: sname);
				local Int is fidx: st:fieldIndex(name: fieldName);
				if({ fidx >= 0 }, {
					return :emitLoadField(objPtr: obj, sname: sname, st: st, fidx: fidx, fieldName: fieldName);
				});
				return '0';
			},
			Expression:Path: local Function(Array of String is segments){
				if({ segments:length() >= 2 }, {
					local String is seg0: segments:get(index: 0, default: '');
					local String is seg1: segments:get(index: 1, default: '');
					local String is hk: seg0 . ':' . seg1;
					if({ segments:length() == 2 && !:localSlots:has(key: seg0) && :heldFields:has(key: hk) }, {
						local String is owner: :heldFields:get(key: hk, default: '');
						local IrType is hty: :irTypeFor(specType: :heldFieldTypes:get(key: owner . ':' . seg1, default: ''));
						if({ hty == IrType:Void }, { hty: IrType:Ptr; });
						local String is dst: :nextTmp();
						:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: hty, callee: owner . '_' . seg1 . '__ensure', argTypes: [], args: []));
						if({ hty == IrType:Ptr }, { :emitClaimPool(val: dst); });
						return dst;
					});
					local String is varStruct: seg0 . '_' . seg1;
					if({ segments:length() == 2 && !:localSlots:has(key: seg0) && :mod:findStruct(name: varStruct):name != '' }, {
						local String is vdst: :nextTmp();
						:emit(inst: IrInst:AllocObj(dst: vdst, structName: varStruct, destroyFn: :destroyFnFor(structName: varStruct)));
						:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: varStruct . '_init', argTypes: [IrType:Ptr], args: [vdst]));
						:emitClaimPool(val: vdst);
						return vdst;
					});
					if({ segments:length() == 2 && !:localSlots:has(key: seg0) }, {
						local String is rSym: :findHeldResolver(clsName: seg0);
						if({ rSym != '' }, {
							local Int is rSid: :mod:internStringLiteral(value: seg1);
							local String is rNameStr: :nextTmp();
							:emit(inst: IrInst:ConstString(dst: rNameStr, strId: rSid));
							local String is rSpec: :heldResolverRetTypes:get(key: rSym, default: '');
							local IrType is rTy: :irTypeFor(specType: rSpec);
							if({ rTy == IrType:Void }, { rTy: IrType:Ptr; });
							local String is rDst: :nextTmp();
							:emit(inst: IrInst:IrCall(dst: rDst, hasDst: true, retType: rTy, callee: rSym . '_held_resolve', argTypes: [IrType:Ptr], args: [rNameStr]));
							if({ rTy == IrType:Ptr }, { :emitClaimPool(val: rDst); });
							return rDst;
						});
					});
					local Int is fidx: :resolvePathField(segments: segments);
					if({ fidx >= 0 }, {
						local String is obj: :pathObjPtr;
						local String is sname: :pathStructName;
						local IrStruct is st: :mod:findStruct(name: sname);
						return :emitLoadField(objPtr: obj, sname: sname, st: st, fidx: fidx, fieldName: segments:get(index: segments:length() - 1, default: ''));
					});
				});
				if({ :irTypeFor(specType: expr:resolvedType) == IrType:Ptr }, {
					return 'null';
				});
				return '0';
			},
			Expression:Cast: local Function(Expression is inner, String is target, Array of Expression is args){
				local String is v: :lowerExpr(expr: inner);
				local IrType is fromTy: :irTypeFor(specType: inner:resolvedType);
				if({ target == 'Hex' || target == 'Bin' || target == 'Oct' }, {
					local Int is base: 16;
					if({ target == 'Bin' }, { base: 2; });
					if({ target == 'Oct' }, { base: 8; });
					local String is baseVal: :nextTmp();
					:emit(inst: IrInst:ConstInt(dst: baseVal, value: base));
					if({ fromTy == IrType:Ptr }, {
						local String is defVal: :nextTmp();
						:emit(inst: IrInst:ConstInt(dst: defVal, value: 0));
						local String is dstP: :nextTmp();
						:emit(inst: IrInst:IrCall(dst: dstP, hasDst: true, retType: IrType:I64, callee: 'Str_parseInt', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [v, baseVal, defVal]));
						return dstP;
					});
					local String is digitsVal: '';
					if({ args:length() > 0 }, {
						digitsVal: :lowerExpr(expr: args:get(index: 0));
					}, {
						digitsVal: :nextTmp();
						:emit(inst: IrInst:ConstInt(dst: digitsVal, value: 0));
					});
					local String is dstB: :nextTmp();
					:emit(inst: IrInst:IrCall(dst: dstB, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToBase', argTypes: [IrType:Ptr, IrType:I64, IrType:I64, IrType:I64], args: ['null', v, baseVal, digitsVal]));
					return dstB;
				});
				local IrType is toTy: :irTypeFor(specType: target);
				if({ target == 'Byte' && inner:resolvedType != 'Byte' }, {
					local String is bv: :castIfNeeded(val: v, fromTy: fromTy, toTy: IrType:I64);
					local String is dstByte: :nextTmp();
					:emit(inst: IrInst:IrCall(dst: dstByte, hasDst: true, retType: IrType:I64, callee: '__spec_check_byte', argTypes: [IrType:I64], args: [bv]));
					return dstByte;
				});
				if({ (inner:resolvedType == 'String' || inner:resolvedType == 'Str') && target == 'Int' }, {
					local String is base10: :nextTmp();
					:emit(inst: IrInst:ConstInt(dst: base10, value: 10));
					local String is def0: :nextTmp();
					:emit(inst: IrInst:ConstInt(dst: def0, value: 0));
					local String is dstI: :nextTmp();
					:emit(inst: IrInst:IrCall(dst: dstI, hasDst: true, retType: IrType:I64, callee: 'Str_parseInt', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [v, base10, def0]));
					return dstI;
				});
				if({ (target == 'String' || target == 'Str') && fromTy != IrType:Ptr }, {
					local String is dstS: :nextTmp();
					if({ fromTy == IrType:F64 }, {
						:emit(inst: IrInst:IrCall(dst: dstS, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_float', argTypes: [IrType:F64], args: [v]));
						return dstS;
					});
					if({ fromTy == IrType:I1 }, {
						:emit(inst: IrInst:IrCall(dst: dstS, hasDst: true, retType: IrType:Ptr, callee: 'spec_to_string_bool', argTypes: [IrType:I1], args: [v]));
						return dstS;
					});
					:emit(inst: IrInst:IrCall(dst: dstS, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToString', argTypes: [IrType:Ptr, IrType:I64], args: ['null', v]));
					return dstS;
				});
				if({ fromTy == toTy }, {
					if({ fromTy == IrType:Ptr && (target == 'String' || target == 'Str') && inner:resolvedType != 'String' && inner:resolvedType != 'Str' && (:clsMap:has(key: inner:resolvedType) || inner:resolvedType == 'Any') }, {
						return :emitObjectToString(objVal: v, specType: inner:resolvedType);
					});
					if({ fromTy == IrType:Ptr && target != 'Any' && target != '' && target != 'String' && target != 'Str' && target != 'Buf' && target != 'Array' && target != 'Map' && !target:startsWith(prefix: 'Array of ') && !target:startsWith(prefix: 'Map of ') && :clsQNameMap:has(key: target) }, {
						local String is tQName: :clsQNameMap:get(key: target, default: '');
						local Int is tStrId: :mod:internStringLiteral(value: tQName);
						local String is tPtr: :nextTmp();
						:emit(inst: IrInst:GlobalAddr(dst: tPtr, globalName: '.str.' . (tStrId as String)));
						local String is ccDst: :nextTmp();
						:emit(inst: IrInst:IrCall(dst: ccDst, hasDst: true, retType: IrType:Ptr, callee: 'spec_cast_check', argTypes: [IrType:Ptr, IrType:Ptr], args: [v, tPtr]));
						return ccDst;
					});
					return v;
				});
				local String is dst: :nextTmp();
				:emit(inst: IrInst:IrCast(dst: dst, val: v, fromType: fromTy, toType: toTy));
				return dst;
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				local String is arr: :nextTmp();
				local Array of IrType is emptyT: [];
				local Array of String is emptyV: [];
				local Boolean is isObjArr: false;
				if({ items:length() > 0 }, {
					local Expression is firstItem: items:get(index: 0);
					if({ :irTypeFor(specType: firstItem:resolvedType) == IrType:Ptr }, { isObjArr: true; });
				});
				if({ isObjArr }, {
					:emit(inst: IrInst:IrCall(dst: arr, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecNewObject', argTypes: emptyT, args: emptyV));
				}, {
					:emit(inst: IrInst:IrCall(dst: arr, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecNew', argTypes: emptyT, args: emptyV));
				});
				local Int is ii: 0;
				while({ ii < items:length() }, {
					local Expression is it: items:get(index: ii);
					local String is iv: :lowerExpr(expr: it);
					local IrType is ity: :irTypeFor(specType: it:resolvedType);
					local String is ip: iv;
					if({ ity == IrType:Void }, {
						ip: 'null';
					}, {
						if({ ity != IrType:Ptr }, {
							ip: :nextTmp();
							:emit(inst: IrInst:IrCast(dst: ip, val: iv, fromType: ity, toType: IrType:Ptr));
						});
					});
					local Array of IrType is addT: [IrType:Ptr, IrType:Ptr, IrType:Ptr];
					local Array of String is addV: ['null', arr, ip];
					:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecAdd', argTypes: addT, args: addV));
					ii++;
				});
				:emitClaimPool(val: arr);
				return arr;
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				local String is mp: :nextTmp();
				local Int is mapKk: 0;
				local Int is mapVk: 0;
				local String is resTy: expr:resolvedType;
				if({ keys:length() > 0 }, {
					local Expression is k0: keys:get(index: 0);
					if({ k0:resolvedType == 'Int' || k0:resolvedType == 'Boolean' }, { mapKk: 1; });
					if({ k0:resolvedType == 'Float' }, { mapKk: 2; });
					if({ mapKk == 0 && k0:resolvedType != 'String' && k0:resolvedType != 'Any' }, { mapKk: 3; });
				}, {
					if({ resTy:startsWith(prefix: 'Map of Int to ') || resTy:startsWith(prefix: 'Map:Int:') || resTy:startsWith(prefix: 'Map of Boolean to ') || resTy:startsWith(prefix: 'Map:Boolean:') }, { mapKk: 1; });
					if({ resTy:startsWith(prefix: 'Map of Float to ') || resTy:startsWith(prefix: 'Map:Float:') }, { mapKk: 2; });
					if({ mapKk == 0 && resTy != 'Map' && resTy != '' && !resTy:startsWith(prefix: 'Map of String to ') && !resTy:startsWith(prefix: 'Map:String:') && !resTy:startsWith(prefix: 'Map of Any to ') && !resTy:startsWith(prefix: 'Map:Any:') }, { mapKk: 3; });
					if({ mapKk == 0 && (resTy == 'Map' || resTy == '') && :expectedMapKeyType != '' }, {
						local String is ek: :expectedMapKeyType;
						if({ ek == 'Int' || ek == 'Boolean' }, { mapKk: 1; });
						if({ ek == 'Float' }, { mapKk: 2; });
						if({ mapKk == 0 && ek != 'String' && ek != 'Any' }, { mapKk: 3; });
					});
				});
				if({ values:length() > 0 }, {
					local Expression is v0: values:get(index: 0);
					if({ :isArcSpecType(specType: v0:resolvedType) }, { mapVk: 1; });
				}, {
					local Int is toIdx: resTy:indexOf(search: ' to ', default: -1);
					if({ toIdx >= 0 }, {
						local String is vSpec: resTy:substring(start: toIdx + 4, end: resTy:length());
						if({ :isArcSpecType(specType: vSpec) }, { mapVk: 1; });
					}, {
						if({ resTy:startsWith(prefix: 'Map:') }, {
							local String is afterMap: resTy:substring(start: 4, end: resTy:length());
							local Int is cIdx: afterMap:indexOf(search: ':', default: -1);
							if({ cIdx >= 0 }, {
								local String is vSpec2: afterMap:substring(start: cIdx + 1, end: afterMap:length());
								if({ :isArcSpecType(specType: vSpec2) }, { mapVk: 1; });
							});
						}, {
							if({ (resTy == 'Map' || resTy == '') && :expectedMapValType != '' }, {
								if({ :isArcSpecType(specType: :expectedMapValType) }, { mapVk: 1; });
							});
						});
					});
				});
				if({ mapKk != 0 || mapVk != 0 }, {
					if({ mapKk == 0 && mapVk == 1 }, {
						local Array of IrType is emptyT: [];
						local Array of String is emptyV: [];
						:emit(inst: IrInst:IrCall(dst: mp, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewObject', argTypes: emptyT, args: emptyV));
					}, {
						local String is mkkV: :nextTmp();
						:emit(inst: IrInst:ConstInt(dst: mkkV, value: mapKk));
						local String is mvkV: :nextTmp();
						:emit(inst: IrInst:ConstInt(dst: mvkV, value: mapVk));
						:emit(inst: IrInst:IrCall(dst: mp, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewTyped', argTypes: [IrType:I64, IrType:I64], args: [mkkV, mvkV]));
					});
				}, {
					local Array of IrType is emptyT: [];
					local Array of String is emptyV: [];
					:emit(inst: IrInst:IrCall(dst: mp, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNew', argTypes: emptyT, args: emptyV));
				});
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					local Expression is ke: keys:get(index: mi);
					local Expression is ve: values:get(index: mi);
					local String is kv: :lowerExpr(expr: ke);
					local IrType is kty: :irTypeFor(specType: ke:resolvedType);
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
					kv: :castIfNeeded(val: kv, fromTy: kty, toTy: kArgTy);
					local String is vv: :lowerExpr(expr: ve);
					local IrType is vty: :irTypeFor(specType: ve:resolvedType);
					local String is vp: vv;
					if({ vty != IrType:Ptr }, {
						vp: :nextTmp();
						:emit(inst: IrInst:IrCast(dst: vp, val: vv, fromType: vty, toType: IrType:Ptr));
					});
					local Array of IrType is setT: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr];
					local Array of String is setV: ['null', mp, kv, vp];
					local String is setCallee: 'HashTable_mapSet' . kSuf . 'Any';
					if({ ve:resolvedType == 'String' }, {
						setCallee: 'HashTable_mapSet' . kSuf;
					});
					:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: setCallee, argTypes: setT, args: setV));
					mi++;
				});
				:emitClaimPool(val: mp);
				return mp;
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				local String is tv: :lowerExpr(expr: target);
				local String is iv: :lowerExpr(expr: index);
				local String is raw: :nextTmp();
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
					local String is kp: :castIfNeeded(val: iv, fromTy: :irTypeFor(specType: kSpec), toTy: kArgTy);
					local String is mDef: 'null';
					if({ expr:resolvedType == 'String' || expr:resolvedType == '' }, {
						mDef: :nextTmp();
						local Int is esid: :mod:internStringLiteral(value: '');
						:emit(inst: IrInst:ConstString(dst: mDef, strId: esid));
					});
					:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapGet' . kSuf, argTypes: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr], args: ['null', tv, kp, mDef]));
				}, {
					local Array of IrType is gT: [IrType:Ptr, IrType:Ptr, IrType:I64];
					local Array of String is gV: ['null', tv, iv];
					:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecGetChecked', argTypes: gT, args: gV));
				});
				local IrType is rty: :irTypeFor(specType: expr:resolvedType);
				if({ rty != IrType:Ptr && rty != IrType:Void }, {
					local String is casted: :nextTmp();
					:emit(inst: IrInst:IrCast(dst: casted, val: raw, fromType: IrType:Ptr, toType: rty));
					return casted;
				});
				return raw;
			},
			Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
				return :lowerAnonFn(returnType: returnType, params: params, body: body);
			},
			Expression:Call: local Function(CallData is call){
				return :lowerCall(expr: expr, call: call);
			}
		], default: {
			if({ :irTypeFor(specType: expr:resolvedType) == IrType:Ptr }, {
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
						:collectFreeInExpr(expr: initExpr, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					});
					bound:set(key: varName, value: true);
				},
				Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
					:collectFreeInExpr(expr: assignTarget, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					:collectFreeInExpr(expr: assignValue, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				},
				Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
					if({ hasReturnExpr }, {
						:collectFreeInExpr(expr: returnExpr, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					});
				},
				Statement:Expr: local Function(Expression is exprStmt){
					:collectFreeInExpr(expr: exprStmt, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
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
						if({ outerSlots:has(key: ':') && !seen:has(key: ':') && :mod:findStruct(name: :currentClass):fieldIndex(name: name) >= 0 }, {
							seen:set(key: ':', value: true);
							out:add(item: ':');
						});
					});
				});
			},
			Expression:Unary: local Function(String is _op, Expression is operand){
				:collectFreeInExpr(expr: operand, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
			},
			Expression:Binary: local Function(String is _op, Expression is left, Expression is right){
				:collectFreeInExpr(expr: left, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				:collectFreeInExpr(expr: right, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
			},
			Expression:Cast: local Function(Expression is inner, String is _t, Array of Expression is args){
				:collectFreeInExpr(expr: inner, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				local Int is ai: 0;
				while({ ai < args:length() }, {
					:collectFreeInExpr(expr: args:get(index: ai), bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					ai++;
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is _f){
				:collectFreeInExpr(expr: target, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
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
							if({ outerSlots:has(key: ':') && !seen:has(key: ':') && :mod:findStruct(name: :currentClass):fieldIndex(name: seg0) >= 0 }, {
								seen:set(key: ':', value: true);
								out:add(item: ':');
							});
						});
					});
				});
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				:collectFreeInExpr(expr: target, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				:collectFreeInExpr(expr: index, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				local Int is ii: 0;
				while({ ii < items:length() }, {
					:collectFreeInExpr(expr: items:get(index: ii), bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					ii++;
				});
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				local Int is mi: 0;
				while({ mi < keys:length() }, {
					:collectFreeInExpr(expr: keys:get(index: mi), bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					:collectFreeInExpr(expr: values:get(index: mi), bound: bound, outerSlots: outerSlots, seen: seen, out: out);
					mi++;
				});
			},
			Expression:Call: local Function(CallData is call){
				if({ call:isBareCall && !bound:has(key: call:name) && outerSlots:has(key: call:name) && !seen:has(key: call:name) }, {
					seen:set(key: call:name, value: true);
					out:add(item: call:name);
				});
				:collectFreeInExpr(expr: call:target, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
				local Int is ci: 0;
				while({ ci < call:args:length() }, {
					local NamedArg is na: call:args:get(index: ci);
					:collectFreeInExpr(expr: na:value, bound: bound, outerSlots: outerSlots, seen: seen, out: out);
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
				:collectFreeInStmts(stmts: subBody, bound: subBound, outerSlots: outerSlots, seen: seen, out: out);
			}
		], default: {});
	}

	local Function of String is lowerAnonFn(Type is returnType, Array of Parameter is params, Array of Statement is body){
		:anonCounter: :anonCounter + 1;
		local Int is anonId: :anonCounter;
		local String is fnName: '__anon_' . (anonId as String);
		local IrType is retTy: :irTypeFor(specType: returnType:name);
		local String is retSpecType: returnType:name;
		if({ returnType:name == 'Function' }, {
			if({ returnType:params:length() > 0 }, {
				local Type is rt: returnType:params:get(index: 0);
				retTy: :irTypeFor(specType: rt:name);
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
		:collectFreeInStmts(stmts: body, bound: bound, outerSlots: :localSlots, seen: seenCap, out: captures);

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
			:mod:addStruct(s: envSt);
		});

		# Save outer method builder state
		local IrFunction is savedFn: :curFn;
		local IrBlock is savedBlk: :curBlk;
		local Boolean is savedTerm: :blkTerminated;
		local Int is savedTmp: :tmpCounter;
		local Int is savedLbl: :lblCounter;
		local Map of String to String is savedSlots: :localSlots;
		local Map of String to IrType is savedTypes: :localTypes;
		local Map of String to Boolean is savedIsArc: :localIsArc;
		local Map of String to String is savedSpecTypes: :localSpecTypes;
		local Map of String to Boolean is savedBoxed: :boxedLocals;
		local Map of String to Boolean is savedCaptured: :capturedNames;
		local Map of String to String is savedLazyStateSlots: :lazyLocalStateSlots;
		local Map of String to Expression is savedLazyExprs: :lazyLocalExprs;
		local Array of String is savedOwned: :ownedSlots;
		local Array of String is savedScopeVars: :scopeVarStack;
		local Array of String is savedScopeOldSlots: :scopeOldSlotStack;
		local Array of IrType is savedScopeOldTypes: :scopeOldTypeStack;
		local Array of Boolean is savedScopeOldArcs: :scopeOldArcStack;
		local Array of String is savedScopeOldSpecs: :scopeOldSpecTypeStack;
		local Array of Boolean is savedScopeOldBoxed: :scopeOldBoxedStack;
		local Array of String is savedScopeOldLazyStates: :scopeOldLazyStateStack;
		local Array of Expression is savedScopeOldLazyExprs: :scopeOldLazyExprStack;
		local Array of Int is savedScopeMarks: :scopeMarkStack;
		local String is savedPoolMark: :curPoolMark;
		local Boolean is savedRetIsArc: :curFnRetIsArc;
		local String is savedErrCallee: :curFnErrHandlerCallee;
		local String is savedErrSlot: :curFnErrPushedSlot;
		:curFnErrHandlerCallee: '';
		:curFnErrPushedSlot: '';

		local IrFunction is fn: IrFunction:init(name: fnName, retType: retTy);
		fn:sourceFile: savedFn:sourceFile;
		fn:line: :currentLine;
		fn:addParam(name: '%env', ty: IrType:Ptr);
		local Int is pi: 0;
		while({ pi < params:length() }, {
			local Parameter is p: params:get(index: pi);
			fn:addParam(name: '%p_' . p:name, ty: :irTypeFor(specType: p:paramType:name));
			pi++;
		});

		local IrBlock is entry: fn:addBlock(label: 'entry');
		:curFn: fn;
		:switchBlock(blk: entry);
		:tmpCounter: 0;
		:lblCounter: 0;
		:localSlots: Map:init();
		:localTypes: Map:init();
		:localIsArc: Map:init();
		:localSpecTypes: Map:init();
		:boxedLocals: Map:init();
		:capturedNames: Map:init();
		:ownedSlots: [];
		:resetScopes();

		local Map of String to Boolean is decls: Map:init();
		local Int is dpi: 0;
		while({ dpi < params:length() }, {
			local Parameter is dp: params:get(index: dpi);
			decls:set(key: dp:name, value: true);
			dpi++;
		});
		:collectDeclNamesInStmts(stmts: body, decls: decls);
		:collectAllAnonCapturesInStmts(stmts: body, decls: decls, out: :capturedNames);
		:curFnRetIsArc: :isArcSpecType(specType: retSpecType);
		:emitPoolEnter();

		# Unpack captured variables from %env into local slots
		local Int is uci: 0;
		while({ uci < captures:length() }, {
			local String is cname: captures:get(index: uci, default: '');
			local IrType is cty: savedTypes:get(key: cname, default: IrType:I64);
			local Boolean is cArc: savedIsArc:get(key: cname, default: false);
			local String is fPtr: :nextTmp();
			:emit(inst: IrInst:FieldPtr(dst: fPtr, objPtr: '%env', structName: envStructName, fieldIndex: uci + 2));
			local String is loaded: :nextTmp();
			:emit(inst: IrInst:Load(dst: loaded, slot: fPtr, ty: IrType:Ptr));
			:localTypes:set(key: cname, value: cty);
			:localIsArc:set(key: cname, value: cArc);
			:localSpecTypes:set(key: cname, value: savedSpecTypes:get(key: cname, default: ''));
			if({ cname == ':' }, {
				local String is capSlot: '%cap__recv';
				:localSlots:set(key: cname, value: capSlot);
				:emit(inst: IrInst:Alloca(slot: capSlot, ty: cty));
				if({ cArc }, {
					:emit(inst: IrInst:Retain(val: loaded));
					:ownedSlots:add(item: capSlot);
				});
				:emit(inst: IrInst:Store(slot: capSlot, val: loaded, ty: cty));
			}, {
				if({ savedBoxed:has(key: cname) }, {
					local String is capSlot: '%cap_' . cname;
					:localSlots:set(key: cname, value: capSlot);
					:boxedLocals:set(key: cname, value: true);
					:emit(inst: IrInst:Alloca(slot: capSlot, ty: IrType:Ptr));
					:emit(inst: IrInst:Store(slot: capSlot, val: loaded, ty: IrType:Ptr));
				}, {
					:localSlots:set(key: cname, value: loaded);
				});
			});
			uci++;
		});

		pi: 0;
		while({ pi < params:length() }, {
			local Parameter is p: params:get(index: pi);
			local IrType is pty: :irTypeFor(specType: p:paramType:name);
			local Boolean is pArc: :isArcSpecType(specType: p:paramType:name);
			local String is slot: '%slot_' . p:name;
			:localSlots:set(key: p:name, value: slot);
			:localTypes:set(key: p:name, value: pty);
			:localIsArc:set(key: p:name, value: pArc);
			:localSpecTypes:set(key: p:name, value: p:paramType:name);
			if({ :capturedNames:has(key: p:name) }, {
				:boxedLocals:set(key: p:name, value: true);
				:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
				if({ pArc }, {
					:emit(inst: IrInst:Retain(val: '%p_' . p:name));
				});
				local String is boxPtr: :emitNewBox(initVal: '%p_' . p:name, ty: pty, isArc: pArc);
				:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
				:ownedSlots:add(item: slot);
			}, {
				:emit(inst: IrInst:Alloca(slot: slot, ty: pty));
				:emit(inst: IrInst:Store(slot: slot, val: '%p_' . p:name, ty: pty));
			});
			pi++;
		});

		:lowerStmts(stmts: body);
		if({ !:blkTerminated }, {
			:emitReleaseOwnedLocals();
			:emitPoolExit();
			if({ retTy == IrType:Void }, {
				:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
			}, {
				local String is defVal: :emitDefaultVal(ty: retTy);
				:terminate(inst: IrInst:Ret(hasVal: true, val: defVal, ty: retTy));
			});
		});
		:curPoolMark: '';
		:mod:addFunction(fn: fn);

		# Emit env destructor if captures exist
		local String is destroyName: envStructName . '_destroy';
		if({ captures:length() > 0 }, {
			local IrFunction is dFn: IrFunction:init(name: destroyName, retType: IrType:Void);
			dFn:sourceFile: savedFn:sourceFile;
			dFn:line: :currentLine;
			dFn:addParam(name: '%env', ty: IrType:Ptr);
			local IrBlock is dEntry: dFn:addBlock(label: 'entry');
			:curFn: dFn;
			:switchBlock(blk: dEntry);
			:tmpCounter: 0;
			local Int is dci: 0;
			while({ dci < captures:length() }, {
				local String is cname: captures:get(index: dci, default: '');
				local Boolean is cArc: savedIsArc:get(key: cname, default: false);
				if({ (cname == ':' && cArc) || savedBoxed:has(key: cname) }, {
					local String is dfPtr: :nextTmp();
					:emit(inst: IrInst:FieldPtr(dst: dfPtr, objPtr: '%env', structName: envStructName, fieldIndex: dci + 2));
					local String is dVal: :nextTmp();
					:emit(inst: IrInst:Load(dst: dVal, slot: dfPtr, ty: IrType:Ptr));
					:emit(inst: IrInst:Release(val: dVal));
				});
				dci++;
			});
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_rt_release', argTypes: [IrType:Ptr], args: ['%env']));
			:terminate(inst: IrInst:Ret(hasVal: false, val: '', ty: IrType:Void));
			:mod:addFunction(fn: dFn);
		});

		# Restore outer method builder state
		:curFn: savedFn;
		:curBlk: savedBlk;
		:blkTerminated: savedTerm;
		:tmpCounter: savedTmp;
		:lblCounter: savedLbl;
		:localSlots: savedSlots;
		:localTypes: savedTypes;
		:localIsArc: savedIsArc;
		:localSpecTypes: savedSpecTypes;
		:boxedLocals: savedBoxed;
		:capturedNames: savedCaptured;
		:lazyLocalStateSlots: savedLazyStateSlots;
		:lazyLocalExprs: savedLazyExprs;
		:ownedSlots: savedOwned;
		:scopeVarStack: savedScopeVars;
		:scopeOldSlotStack: savedScopeOldSlots;
		:scopeOldTypeStack: savedScopeOldTypes;
		:scopeOldArcStack: savedScopeOldArcs;
		:scopeOldSpecTypeStack: savedScopeOldSpecs;
		:scopeOldBoxedStack: savedScopeOldBoxed;
		:scopeOldLazyStateStack: savedScopeOldLazyStates;
		:scopeOldLazyExprStack: savedScopeOldLazyExprs;
		:scopeMarkStack: savedScopeMarks;
		:curPoolMark: savedPoolMark;
		:curFnRetIsArc: savedRetIsArc;
		:curFnErrHandlerCallee: savedErrCallee;
		:curFnErrPushedSlot: savedErrSlot;

		# Allocate and populate %env in outer function if captures exist
		local String is envVal: 'null';
		local String is destroyPtr: 'null';
		if({ captures:length() > 0 }, {
			envVal: :nextTmp();
			:emit(inst: IrInst:AllocObj(dst: envVal, structName: envStructName, destroyFn: 'null'));
			local Int is oci: 0;
			while({ oci < captures:length() }, {
				local String is cname: captures:get(index: oci, default: '');
				local String is oSlot: :localSlots:get(key: cname, default: '');
				local IrType is oTy: :localTypes:get(key: cname, default: IrType:I64);
				local Boolean is oArc: :localIsArc:get(key: cname, default: false);
				if({ :lazyLocalStateSlots:has(key: cname) }, {
					local String is _ensuredLazy: :emitLoadLocal(name: cname, ty: oTy);
				});
				local String is dstPtr: :nextTmp();
				:emit(inst: IrInst:FieldPtr(dst: dstPtr, objPtr: envVal, structName: envStructName, fieldIndex: oci + 2));
				if({ cname == ':' || :boxedLocals:has(key: cname) }, {
					local String is oVal: :nextTmp();
					local IrType is loadTy: if({ cname == ':' }, { oTy }, { IrType:Ptr });
					:emit(inst: IrInst:Load(dst: oVal, slot: oSlot, ty: loadTy));
					if({ oArc || :boxedLocals:has(key: cname) }, {
						:emit(inst: IrInst:Retain(val: oVal));
					});
					:emit(inst: IrInst:Store(slot: dstPtr, val: oVal, ty: IrType:Ptr));
				}, {
					:emit(inst: IrInst:Store(slot: dstPtr, val: oSlot, ty: IrType:Ptr));
				});
				oci++;
			});
			destroyPtr: :nextTmp();
			:emit(inst: IrInst:GlobalAddr(dst: destroyPtr, globalName: destroyName));
		});

		local String is fnPtr: :nextTmp();
		:emit(inst: IrInst:GlobalAddr(dst: fnPtr, globalName: fnName));
		local String is clsTmp: :nextTmp();
		local Array of IrType is cT: [IrType:Ptr, IrType:Ptr, IrType:Ptr];
		local Array of String is cV: [fnPtr, envVal, destroyPtr];
		:emit(inst: IrInst:IrCall(dst: clsTmp, hasDst: true, retType: IrType:Ptr, callee: 'spec_rt_closure_new', argTypes: cT, args: cV));
		:emitClaimPool(val: clsTmp);
		return clsTmp;
	}

	local Function of String is lowerCall(Expression is expr, CallData is call){
		local String is nm: call:name;

		if({ nm == 'toBase' && call:target:resolvedType == 'Int' }, {
			local String is iv: :lowerExpr(expr: call:target);
			local String is baseV: '10';
			local String is digV: '0';
			if({ call:args:length() >= 1 }, {
				local NamedArg is na0: call:args:get(index: 0);
				if({ na0:name == 'digits' }, { digV: :lowerExpr(expr: na0:value); }, { baseV: :lowerExpr(expr: na0:value); });
			});
			if({ call:args:length() >= 2 }, {
				local NamedArg is na1: call:args:get(index: 1);
				if({ na1:name == 'base' }, { baseV: :lowerExpr(expr: na1:value); }, { digV: :lowerExpr(expr: na1:value); });
			});
			local String is dst: :nextTmp();
			:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'Buf_intToBase', argTypes: [IrType:Ptr, IrType:I64, IrType:I64, IrType:I64], args: ['null', iv, baseV, digV]));
			return dst;
		});

		if({ :isLazyCallExpr(expr: expr) }, {
			local IrType is lTy: :irTypeFor(specType: expr:resolvedType);
			return :lowerLazyBodyVal(blkExpr: :getLazyBodyExpr(expr: expr), expectedTy: lTy);
		});

		if({ nm == 'raiseError' && call:args:length() == 1 && :clsQNameMap:has(key: 'Pool') }, {
			local NamedArg is rArg0: call:args:get(index: 0);
			local String is errObj: :lowerExpr(expr: rArg0:value);
			local String is errAddr: :nextTmp();
			:emit(inst: IrInst:IrCast(dst: errAddr, val: errObj, fromType: IrType:Ptr, toType: IrType:I64));
			:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Pool_raisePendingError', argTypes: [IrType:Ptr, IrType:I64], args: ['null', errAddr]));
			:emitUnwindCurrentFrame(recordFrame: false);
			return '0';
		});

		# Pluggable call lowerers (control flow, String, Array, Map, etc.)
		local Int is cli: 0;
		local Boolean is handled: false;
		local String is loweredRes: '0';
		while({ cli < :callLowerers:length() && !handled }, {
			local CallLowerer is cl: :callLowerers:get(index: cli);
			if({ cl:matches(b: :, expr: expr, call: call) }, {
				loweredRes: cl:lower(b: :, expr: expr, call: call);
				handled: true;
			});
			cli++;
		});
		if({ handled }, { return loweredRes; });

		# Closure local variable call: fn(...)
		if({ call:isBareCall && :localSlots:has(key: nm) && :localTypes:get(key: nm, default: IrType:I64) == IrType:Ptr }, {
			local String is cObj: :emitLoadLocal(name: nm, ty: IrType:Ptr);
			local String is fnPtrAddr: :nextTmp();
			:emit(inst: IrInst:FieldPtr(dst: fnPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 0));
			local String is fnPtrVal: :nextTmp();
			:emit(inst: IrInst:Load(dst: fnPtrVal, slot: fnPtrAddr, ty: IrType:Ptr));
			local String is envPtrAddr: :nextTmp();
			:emit(inst: IrInst:FieldPtr(dst: envPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 1));
			local String is envVal: :nextTmp();
			:emit(inst: IrInst:Load(dst: envVal, slot: envPtrAddr, ty: IrType:Ptr));
			local IrType is cRetTy: :irTypeFor(specType: expr:resolvedType);
			local Array of IrType is cArgT: [IrType:Ptr];
			local Array of String is cArgV: [envVal];
			local Int is cai: 0;
			while({ cai < call:args:length() }, {
				local NamedArg is cna: call:args:get(index: cai);
				local Expression is cav: cna:value;
				local IrType is caty: :irTypeFor(specType: cav:resolvedType);
				if({ caty == IrType:Void }, { caty: IrType:I64; });
				cArgT:add(item: caty);
				cArgV:add(item: :lowerExpr(expr: cav));
				cai++;
			});
			local Boolean is cHasDst: cRetTy != IrType:Void;
			local String is cDst: '';
			if({ cHasDst }, { cDst: :nextTmp(); });
			:emit(inst: IrInst:IndirectCall(dst: cDst, hasDst: cHasDst, retType: cRetTy, fnPtr: fnPtrVal, argTypes: cArgT, args: cArgV));
			:emitCheckUnwindAfterCall(callee: '__indirect__');
			return cDst;
		});

		local String is recvType: :baseTypeName(t: call:target:resolvedType);

		# Method / constructor call
		local IrType is retTy: :irTypeFor(specType: expr:resolvedType);
		local Array of IrType is argTypes: [];
		local Array of String is argVals: [];

		local String is calleeName: match(on: call:target, when: [
			Expression:Ident: local Function of String(String is tname){
				if({ tname != ':' && :localSlots:has(key: tname) && recvType != '' }, {
					return :cStructName(qname: recvType) . '_' . nm;
				});
				if({ tname != ':' && !:localSlots:has(key: tname) && :localSlots:has(key: ':') && :mod:findStruct(name: :currentClass):fieldIndex(name: tname) >= 0 && recvType != '' }, {
					return :cStructName(qname: recvType) . '_' . nm;
				});
				if({ tname != ':' && !:localSlots:has(key: tname) }, {
					return :cStructName(qname: tname) . '_' . nm;
				});
				return :currentClass . '_' . nm;
			},
			Expression:Path: local Function of String(Array of String is segs){
				if({ segs:length() >= 2 && (segs:get(index: 0, default: '') == ':' || :localSlots:has(key: segs:get(index: 0, default: '')) || :heldFields:has(key: :currentClass . ':' . segs:get(index: 0, default: '')) || :heldFields:has(key: segs:get(index: 0, default: '') . ':' . segs:get(index: 1, default: '')) || (:localSlots:has(key: ':') && :mod:findStruct(name: :currentClass):fieldIndex(name: segs:get(index: 0, default: '')) >= 0)) }, {
					if({ recvType != '' }, { return :cStructName(qname: recvType) . '_' . nm; });
				});
				if({ segs:length() > 0 }, {
					return segs:get(index: segs:length() - 1, default: '') . '_' . nm;
				});
				return :currentClass . '_' . nm;
			}
		], default: {
			if({ recvType != '' }, { return :cStructName(qname: recvType) . '_' . nm; });
			return :currentClass . '_' . nm;
		});
		# Receiver: ':' or local variable, else static class Path (or held field receiver)
		local Boolean is hasRecv: match(on: call:target, when: [
			Expression:Ident: local Function of Boolean(String is tname){
				if({ tname == ':' || :localSlots:has(key: tname) || (:localSlots:has(key: ':') && :mod:findStruct(name: :currentClass):fieldIndex(name: tname) >= 0) }, {
					argTypes:add(item: IrType:Ptr);
					argVals:add(item: :lowerExpr(expr: call:target));
					return true;
				});
				return false;
			},
			Expression:Path: local Function of Boolean(Array of String is segs){
				if({ segs:length() >= 2 && (segs:get(index: 0, default: '') == ':' || :localSlots:has(key: segs:get(index: 0, default: '')) || :heldFields:has(key: :currentClass . ':' . segs:get(index: 0, default: '')) || :heldFields:has(key: segs:get(index: 0, default: '') . ':' . segs:get(index: 1, default: '')) || (:localSlots:has(key: ':') && :mod:findStruct(name: :currentClass):fieldIndex(name: segs:get(index: 0, default: '')) >= 0)) }, {
					argTypes:add(item: IrType:Ptr);
					argVals:add(item: :lowerExpr(expr: call:target));
					return true;
				});
				return false;
			}
		], default: {
			argTypes:add(item: IrType:Ptr);
			argVals:add(item: :lowerExpr(expr: call:target));
			return true;
		});

		local String is staticTargetName: '';
		if({ !hasRecv }, {
			local String is pathCName: '';
			local String is pathWithNm: '';
			match(on: call:target, when: [
				Expression:Ident: local Function(String is tname){
					if({ tname != ':' && !:localSlots:has(key: tname) }, {
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
			local Boolean is isVariantCtor: (pathWithNm != '') && (:mod:findStruct(name: pathWithNm):name != '');
			if({ nm == 'init' || isVariantCtor }, {
				# Constructor: ClassName_new + ClassName_init
				local String is clsName: :currentClass;
				if({ isVariantCtor }, {
					clsName: pathWithNm;
				}, {
					if({ pathCName != '' }, { clsName: pathCName; });
				});
				if({ :mod:findStruct(name: clsName):name == '' }, {
					local String is resCName: :cStructName(qname: expr:resolvedType);
					if({ resCName != '' && :mod:findStruct(name: resCName):name != '' }, {
						clsName: resCName;
					}, {
						if({ :currentClass != '' && :mod:findStruct(name: :currentClass . '_' . clsName):name != '' }, {
							clsName: :currentClass . '_' . clsName;
						});
					});
				});
				local String is obj: :nextTmp();
				:emit(inst: IrInst:AllocObj(dst: obj, structName: clsName, destroyFn: :destroyFnFor(structName: clsName)));
				argTypes:add(item: IrType:Ptr);
				argVals:add(item: obj);
				local String is ctorSuf: '';
				if({ call:overloadIndex > 0 }, {
					ctorSuf: '_' . ((call:overloadIndex + 1) as String);
				});
				local String is ctorKey: clsName . '_init' . ctorSuf;
				if({ !:methodParams:has(key: ctorKey) }, {
					local String is qLookup: clsName;
					if({ expr:resolvedType != '' && :clsMap:has(key: expr:resolvedType) }, {
						qLookup: expr:resolvedType;
					});
					local String is parentInit: :findParentMethodImpl(clsName: qLookup, methodName: 'init', suffix: ctorSuf);
					if({ parentInit != '' }, {
						if({ call:args:length() == 0 && :mod:findStruct(name: clsName):name != '' }, {
							:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: clsName . '_init', argTypes: [IrType:Ptr], args: [obj]));
						});
						ctorKey: parentInit;
					}, {
						if({ call:args:length() == 0 && :mod:findStruct(name: clsName):name != '' }, {
							ctorKey: clsName . '_init';
						});
					});
				});
				local Expression is prevCtorCallExpr: :currentCallExpr;
				:currentCallExpr: expr;
				:lowerCallArgs(fnKey: ctorKey, callArgs: call:args, argTypes: argTypes, argVals: argVals);
				:currentCallExpr: prevCtorCallExpr;
				:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: ctorKey, argTypes: argTypes, args: argVals));
				:emitCheckUnwindAfterCall(callee: ctorKey);
				:emitClaimPool(val: obj);
				return obj;
			});
		});

		if({ call:bareProvider != '' }, {
			local String is provStruct: :cStructName(qname: call:bareProvider);
			if({ :mod:findStruct(name: provStruct):name != '' }, {
				local String is provObj: :emitImportFieldOrAlloc(provStruct: provStruct, rawName: call:bareProvider);
				argTypes: [IrType:Ptr];
				argVals: [provObj];
				hasRecv: true;
				recvType: call:bareProvider;
				calleeName: provStruct . '_' . nm;
			});
		});

		if({ !hasRecv && !:heldMethods:has(key: calleeName) }, {
			local String is provStruct: '';
			if({ staticTargetName != '' }, {
				provStruct: :cStructName(qname: staticTargetName);
				if({ :mod:findStruct(name: provStruct):name == '' && :clsQNameMap:has(key: staticTargetName) }, {
					provStruct: :cStructName(qname: :clsQNameMap:get(key: staticTargetName, default: staticTargetName));
				});
			});
			if({ provStruct != '' && :mod:findStruct(name: provStruct):name != '' }, {
				local String is provObj: :emitImportFieldOrAlloc(provStruct: provStruct, rawName: staticTargetName);
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
		local String is recvStruct: :currentClass;
		local String is ovSuf: if({ call:overloadIndex > 0 }, { '_' . ((call:overloadIndex + 1) as String) }, { '' });
		if({ !hasRecv && staticTargetName != '' && !:heldMethods:has(key: calleeName) && !:methodParams:has(key: dirCallee) }, {
			local String is stStruct: :cStructName(qname: staticTargetName);
			if({ :mod:findStruct(name: stStruct):name == '' && :clsQNameMap:has(key: staticTargetName) }, {
				stStruct: :cStructName(qname: :clsQNameMap:get(key: staticTargetName, default: staticTargetName));
			});
			local String is parentStFn: :findParentMethodImpl(clsName: stStruct, methodName: nm, suffix: ovSuf);
			if({ parentStFn != 'null' && parentStFn != '' }, {
				dirCallee: parentStFn;
			});
		});
		if({ hasRecv && nm != 'init' && nm != 'destroy' && !:heldMethods:has(key: calleeName) }, {
			local Boolean is isSelfTarget: false;
			match(on: call:target, when: [
				Expression:Ident: local Function(String is tname){
					if({ tname == ':' }, { isSelfTarget: true; });
				}
			], default: {});
			if({ (!isSelfTarget || call:bareProvider != '') && recvType != '' }, {
				recvStruct: :cStructName(qname: recvType);
				if({ :mod:findStruct(name: recvStruct):name == '' && :clsQNameMap:has(key: recvType) }, {
					recvStruct: :cStructName(qname: :clsQNameMap:get(key: recvType, default: recvType));
				});
			});
			if({ recvStruct != 'String' && recvStruct != 'Str' && recvStruct != 'Array' && recvStruct != 'Map' && recvStruct != 'Math' && recvStruct != 'List' }, {
				local IrStruct is rst: :mod:findStruct(name: recvStruct);
				local String is vkey: if({ call:overloadIndex > 0 }, { nm . '_' . ((call:overloadIndex + 1) as String) }, { nm });
				vslot: rst:vtableSlot(mname: vkey);
				if({ vslot >= 0 }, {
					local String is vtFn: rst:vtableFns:get(index: vslot, default: calleeName);
					if({ vtFn != '' && vtFn != 'null' }, {
						dirCallee: vtFn;
					});
				});
			}, {
				if({ !:methodParams:has(key: dirCallee) }, {
					local String is parentFn: :findParentMethodImpl(clsName: recvStruct, methodName: nm, suffix: ovSuf);
					if({ parentFn != 'null' && parentFn != '' }, {
						dirCallee: parentFn;
					});
				});
			});
		});

		local Expression is prevCallExpr: :currentCallExpr;
		:currentCallExpr: expr;
		:lowerCallArgs(fnKey: dirCallee, callArgs: call:args, argTypes: argTypes, argVals: argVals);
		:currentCallExpr: prevCallExpr;

		local IrType is callRetTy: retTy;
		if({ :methodRetTypes:has(key: dirCallee) }, {
			callRetTy: :methodRetTypes:get(key: dirCallee, default: retTy);
		});
		local Boolean is hasDst: callRetTy != IrType:Void;
		local String is dst: '';
		if({ hasDst }, { dst: :nextTmp(); });

		if({ vslot >= 0 }, {
			local String is recvPtr: argVals:get(index: 0, default: 'null');
			if({ recvPtr == 'null' }, {
				:emit(inst: IrInst:IrCall(dst: dst, hasDst: hasDst, retType: callRetTy, callee: dirCallee, argTypes: argTypes, args: argVals));
				:emitCheckUnwindAfterCall(callee: dirCallee);
			}, {
				local String is resSlot: '';
				if({ hasDst }, {
					resSlot: :nextTmp();
					:emit(inst: IrInst:Alloca(slot: resSlot, ty: callRetTy));
				});
				local String is isNonNull: :nextTmp();
				:emit(inst: IrInst:Cmp(dst: isNonNull, op: '!=', lhs: recvPtr, rhs: 'null', ty: IrType:Ptr));
				local String is vtLbl: :nextLabel(prefix: 'vt_call');
				local String is dirLbl: :nextLabel(prefix: 'dir_call');
				local String is endLbl: :nextLabel(prefix: 'vt_end');
				:terminate(inst: IrInst:CondBr(cond: isNonNull, thenLabel: vtLbl, elseLabel: dirLbl));

				local IrBlock is vtBlk: :curFn:addBlock(label: vtLbl);
				:switchBlock(blk: vtBlk);
				local String is vtPtrAddr: :nextTmp();
				:emit(inst: IrInst:FieldPtr(dst: vtPtrAddr, objPtr: recvPtr, structName: recvStruct, fieldIndex: 1));
				local String is vtBase: :nextTmp();
				:emit(inst: IrInst:Load(dst: vtBase, slot: vtPtrAddr, ty: IrType:Ptr));
				local String is slotPtr: :nextTmp();
				:emit(inst: IrInst:PtrElem(dst: slotPtr, basePtr: vtBase, index: vslot));
				local String is fnPtr: :nextTmp();
				:emit(inst: IrInst:Load(dst: fnPtr, slot: slotPtr, ty: IrType:Ptr));
				local String is vtDst: '';
				if({ hasDst }, { vtDst: :nextTmp(); });
				:emit(inst: IrInst:IndirectCall(dst: vtDst, hasDst: hasDst, retType: callRetTy, fnPtr: fnPtr, argTypes: argTypes, args: argVals));
				if({ hasDst }, {
					:emit(inst: IrInst:Store(slot: resSlot, val: vtDst, ty: callRetTy));
				});
				:terminate(inst: IrInst:Br(target: endLbl));

				local IrBlock is dirBlk: :curFn:addBlock(label: dirLbl);
				:switchBlock(blk: dirBlk);
				local String is dirDst: '';
				if({ hasDst }, { dirDst: :nextTmp(); });
				:emit(inst: IrInst:IrCall(dst: dirDst, hasDst: hasDst, retType: callRetTy, callee: dirCallee, argTypes: argTypes, args: argVals));
				if({ hasDst }, {
					:emit(inst: IrInst:Store(slot: resSlot, val: dirDst, ty: callRetTy));
				});
				:terminate(inst: IrInst:Br(target: endLbl));

				local IrBlock is endBlk: :curFn:addBlock(label: endLbl);
				:switchBlock(blk: endBlk);
				if({ hasDst }, {
					:emit(inst: IrInst:Load(dst: dst, slot: resSlot, ty: callRetTy));
				});
				:emitCheckUnwindAfterCall(callee: dirCallee);
			});
		}, {
			:emit(inst: IrInst:IrCall(dst: dst, hasDst: hasDst, retType: callRetTy, callee: dirCallee, argTypes: argTypes, args: argVals));
			:emitCheckUnwindAfterCall(callee: dirCallee);
		});
		if({ callRetTy != retTy && hasDst }, {
			dst: :castIfNeeded(val: dst, fromTy: callRetTy, toTy: retTy);
		});
		return dst;
	}

	local Function of String is emitImportFieldOrAlloc(String is provStruct, String is rawName){
		if({ :mod:findStruct(name: provStruct):fieldNames:length() <= 2 }, {
			return 'null';
		});
		if({ :clsMap:has(key: provStruct) && :bindings:isTransparent(c: :clsMap:get(key: provStruct, default: ClassInfo:init(name: '', baseClass: '', members: []))) }, {
			return 'null';
		});
		if({ :currentClass != '' && :localSlots:has(key: ':') }, {
			local IrStruct is curSt: :mod:findStruct(name: :currentClass);
			local Int is impIdx: curSt:fieldIndex(name: '_import_' . provStruct);
			if({ impIdx < 0 && rawName != '' }, {
				impIdx: curSt:fieldIndex(name: '_import_' . rawName);
			});
			if({ impIdx >= 0 }, {
				local String is selfPtr: :emitLoadLocal(name: ':', ty: IrType:Ptr);
				local String is fPtr: :nextTmp();
				:emit(inst: IrInst:FieldPtr(dst: fPtr, objPtr: selfPtr, structName: :currentClass, fieldIndex: impIdx));
				local String is fVal: :nextTmp();
				:emit(inst: IrInst:Load(dst: fVal, slot: fPtr, ty: IrType:Ptr));
				return fVal;
			});
		});
		local String is provObj: :nextTmp();
		:emit(inst: IrInst:AllocObj(dst: provObj, structName: provStruct, destroyFn: :destroyFnFor(structName: provStruct)));
		:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: provStruct . '_init', argTypes: [IrType:Ptr], args: [provObj]));
		:emitClaimPool(val: provObj);
		return provObj;
	}

	local Function is lowerCallArgs(String is fnKey, Array of NamedArg is callArgs, Array of IrType is argTypes, Array of String is argVals){
		local Expression is callExprForDefaults: :currentCallExpr;
		if({ !:methodParams:has(key: fnKey) }, {
			local Int is ai: 0;
			local String is calleeMask: :methodParamPtrMask:get(key: fnKey, default: '');
			while({ ai < callArgs:length() }, {
				local NamedArg is na2: callArgs:get(index: ai);
				local Expression is av: na2:value;
				local IrType is aty: :irTypeFor(specType: av:resolvedType);
				if({ aty == IrType:Void }, { aty: IrType:I64; });
				local String is aval: :lowerExpr(expr: av);
				if({ ai < calleeMask:length() && calleeMask:charAt(index: ai, default: '0') == '1' }, {
					if({ aty != IrType:Ptr }, {
						aval: :castIfNeeded(val: aval, fromTy: aty, toTy: IrType:Ptr);
						aty: IrType:Ptr;
					});
				});
				argTypes:add(item: aty);
				argVals:add(item: aval);
				ai++;
			});
			return;
		});
		local Array of Parameter is params: :methodParams:get(key: fnKey, default: []);
		local Int is pi: 0;
		while({ pi < params:length() }, {
			local Parameter is p: params:get(index: pi);
			local IrType is pty: :irTypeFor(specType: p:paramType:name);
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
				aty: :irTypeFor(specType: av:resolvedType);
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
				aval: :lowerExpr(expr: av);
			}, {
				if({ p:hasDefault }, {
					:currentCallExpr: callExprForDefaults;
					aty: :irTypeFor(specType: p:defaultExpr:resolvedType);
					if({ aty == IrType:Void }, { aty: IrType:I64; });
					aval: :lowerExpr(expr: p:defaultExpr);
				}, {
					aval: :emitDefaultVal(ty: pty);
					aty: pty;
				});
			});
			if({ aty != pty }, {
				aval: :castIfNeeded(val: aval, fromTy: aty, toTy: pty);
			});
			argTypes:add(item: pty);
			argVals:add(item: aval);
			pi++;
		});
	}
}
