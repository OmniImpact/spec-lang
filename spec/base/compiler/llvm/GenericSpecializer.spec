#! Package base:compiler:llvm
#! Monomorphizes generic classes (`Class is C of T`, `Class is P of A to B`) and
#! generic methods into distinct concrete specializations per used type argument.

Class is GenericSpecializer{
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
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	ClassBindings is bindings: ClassBindings:init();
	Map of String to ClassInfo is templates: Map:init();
	Map of String to Boolean is seenClassNames: Map:init();
	Map of String to String is specKeyToMangled: Map:init();
	Map of String to String is specBaseMap: Map:init();
	Map of String to ClassInfo is specClassMap: Map:init();
	Map of String to Array of Type is specClassArgsMap: Map:init();
	Array of String is pendingBaseNames: [];
	Array of Array of Type is pendingTypeArgs: [];
	Array of String is pendingMangledNames: [];

	Map of String to Member is genericMethods: Map:init();
	Map of String to String is genericMethodTypeParam: Map:init();
	Map of String to ClassInfo is genericMethodOwners: Map:init();
	Map of String to String is specMethodKeyToName: Map:init();
	Array of String is pendingMethodOwners: [];
	Array of String is pendingMethodNames: [];
	Array of Type is pendingMethodArgTypes: [];
	Array of String is pendingMethodMangled: [];
	String is curOwnerClassName: '';

	local Function of Type is makeType(String is name, Array of Type is params){
		local Type is t: Type:init(name: name);
		t:params: params;
		return t;
	}

	local Function of Type is cloneType(Type is t){
		local Array of Type is cps: [];
		local Int is i: 0;
		while({ i < t:params:length() }, {
			cps:add(item: :cloneType(t: t:params:get(index: i)));
			i++;
		});
		return :makeType(name: t:name, params: cps);
	}

	local Function of String is typeToSymbolSegment(Type is t){
		local String is out: t:name;
		local Int is i: 0;
		while({ i < t:params:length() }, {
			out: out . '_' . :typeToSymbolSegment(t: t:params:get(index: i));
			i++;
		});
		return out;
	}

	local Function of String is typeToResolvedStr(Type is t){
		if({ t:params:length() == 0 }, {
			return t:name;
		});
		local String is out: t:name;
		local Int is i: 0;
		while({ i < t:params:length() }, {
			out: out . ':' . :typeToResolvedStr(t: t:params:get(index: i));
			i++;
		});
		return out;
	}

	local Function of String is specKeyFor(String is baseName, Array of Type is typeArgs){
		local String is key: baseName;
		local Int is i: 0;
		while({ i < typeArgs:length() }, {
			key: key . ':' . :typeToResolvedStr(t: typeArgs:get(index: i));
			i++;
		});
		return key;
	}

	local Function of String is allocateMangledClassName(String is baseName, Array of Type is typeArgs){
		local String is stem: baseName;
		local Int is i: 0;
		while({ i < typeArgs:length() }, {
			stem: stem . '__' . :typeToSymbolSegment(t: typeArgs:get(index: i));
			i++;
		});
		local String is cand: stem;
		local Int is suffix: 1;
		while({ :seenClassNames:has(key: cand) }, {
			cand: stem . '_' . (suffix as String);
			suffix: suffix + 1;
		});
		:seenClassNames:set(key: cand, value: true);
		return cand;
	}

	local Function of Boolean is isConcreteType(Type is t, Map of String to Boolean is tplParams){
		if({ t:name == '' || t:name == 'Any' || t:name == 'Void' || tplParams:has(key: t:name) }, {
			return false;
		});
		local Int is i: 0;
		while({ i < t:params:length() }, {
			if({ !:isConcreteType(t: t:params:get(index: i), tplParams: tplParams) }, {
				return false;
			});
			i++;
		});
		return true;
	}

	local Function of Boolean is areAllConcreteTypes(Array of Type is types, Map of String to Boolean is tplParams){
		local Int is i: 0;
		while({ i < types:length() }, {
			if({ !:isConcreteType(t: types:get(index: i), tplParams: tplParams) }, {
				return false;
			});
			i++;
		});
		return true;
	}

	local Function of String is ensureSpecialized(String is baseName, Array of Type is typeArgs){
		local String is key: :specKeyFor(baseName: baseName, typeArgs: typeArgs);
		if({ :specKeyToMangled:has(key: key) }, {
			return :specKeyToMangled:get(key: key, default: baseName);
		});
		local String is mangled: :allocateMangledClassName(baseName: baseName, typeArgs: typeArgs);
		:specKeyToMangled:set(key: key, value: mangled);
		:specBaseMap:set(key: mangled, value: baseName);
		:specClassArgsMap:set(key: mangled, value: typeArgs);
		:pendingBaseNames:add(item: baseName);
		:pendingTypeArgs:add(item: typeArgs);
		:pendingMangledNames:add(item: mangled);
		return mangled;
	}

	local Function of String is ensureSpecializedMethod(String is ownerClassName, String is methodName, Type is argType){
		local String is key: ownerClassName . ':' . methodName . ':' . :typeToResolvedStr(t: argType);
		if({ :specMethodKeyToName:has(key: key) }, {
			return :specMethodKeyToName:get(key: key, default: methodName);
		});
		local String is mangled: methodName . '__' . :typeToSymbolSegment(t: argType);
		:specMethodKeyToName:set(key: key, value: mangled);
		:pendingMethodOwners:add(item: ownerClassName);
		:pendingMethodNames:add(item: methodName);
		:pendingMethodArgTypes:add(item: :cloneType(t: argType));
		:pendingMethodMangled:add(item: mangled);
		return mangled;
	}

	## Transforms a structured [Type] AST node directly over its [params] array.
	Function of Type is transformType(Type is t, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		if({ t:name == '' }, { return Type:init(name: ''); });
		if({ subst:has(key: t:name) && t:params:length() == 0 }, {
			local Type is mapped: :cloneType(t: subst:get(key: t:name, default: t));
			return :transformType(t: mapped, subst: Map:init(), tplParams: tplParams, selfTemplateName: '', selfSpecName: '');
		});
		local Array of Type is newParams: [];
		local Int is i: 0;
		while({ i < t:params:length() }, {
			newParams:add(item: :transformType(t: t:params:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
			i++;
		});
		local String is bName: t:name;
		if({ subst:has(key: bName) }, {
			bName: subst:get(key: bName, default: t):name;
		});
		if({ :templates:has(key: bName) }, {
			local ClassInfo is tpl: :templates:get(key: bName, default: ClassInfo:init(name: '', baseClass: '', members: []));
			if({ newParams:length() == tpl:typeParams:length() && newParams:length() > 0 }, {
				if({ :areAllConcreteTypes(types: newParams, tplParams: tplParams) }, {
					local String is mangled: :ensureSpecialized(baseName: bName, typeArgs: newParams);
					return Type:init(name: mangled);
				});
			});
			if({ bName == selfTemplateName && selfSpecName != '' && newParams:length() == 0 }, {
				return Type:init(name: selfSpecName);
			});
		});
		return :makeType(name: bName, params: newParams);
	}

	## Converts a checker resolvedType tag into a structured [Type] tree, transforms it,
	## and formats the resulting [Type].
	local Function of Type is resolvedStrToType(String is s, Map of String to Type is subst){
		if({ s == '' }, { return Type:init(name: ''); });
		if({ subst:has(key: s) }, {
			return :cloneType(t: subst:get(key: s, default: Type:init(name: s)));
		});
		local String is norm: s:replaceAll(target: ' of ', replacement: ':'):replaceAll(target: ' to ', replacement: ':');
		local Array of String is rawParts: norm:split(delimiter: ':');
		local Array of Type is stack: [];
		local Int is idx: rawParts:length() - 1;
		while({ idx >= 0 }, {
			local String is seg: rawParts:get(index: idx, default: '');
			if({ subst:has(key: seg) }, {
				stack:add(item: :cloneType(t: subst:get(key: seg, default: Type:init(name: seg))));
			}, {
				local Int is arity: 0;
				if({ :templates:has(key: seg) }, {
					local ClassInfo is tpl: :templates:get(key: seg, default: ClassInfo:init(name: '', baseClass: '', members: []));
					arity: tpl:typeParams:length();
				}, {
					if({ seg == 'Array' || seg == 'List' || seg == 'Function' }, {
						arity: 1;
					});
					if({ seg == 'Map' }, {
						arity: 2;
					});
				});
				if({ arity > 0 && stack:length() >= arity }, {
					local Array of Type is tArgs: [];
					local Int is ki: 0;
					while({ ki < arity }, {
						tArgs:add(item: stack:pop(default: Type:init(name: '')));
						ki++;
					});
					stack:add(item: :makeType(name: seg, params: tArgs));
				}, {
					stack:add(item: Type:init(name: seg));
				});
			});
			idx: idx - 1;
		});
		if({ stack:length() > 0 }, {
			return stack:get(index: stack:length() - 1);
		});
		return Type:init(name: s);
	}

	Function of String is transformTypeStr(String is s, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		if({ s == '' }, { return ''; });
		local Type is parsed: :resolvedStrToType(s: s, subst: subst);
		local Type is specT: :transformType(t: parsed, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
		return :typeToResolvedStr(t: specT);
	}

	Function of Parameter is transformParam(Parameter is p, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		local Type is newPT: :transformType(t: p:paramType, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
		local Parameter is np: Parameter:init(name: p:name, paramType: newPT);
		np:isVariadic: p:isVariadic;
		if({ p:hasDefault }, {
			np:setDefault(expr: :transformExpr(expr: p:defaultExpr, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
		});
		return np;
	}

	Function of Array of Statement is transformStmts(Array of Statement is stmts, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		local Array of Statement is out: [];
		local Int is i: 0;
		while({ i < stmts:length() }, {
			out:add(item: :transformStmt(stmt: stmts:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
			i++;
		});
		return out;
	}

	Function of Statement is transformStmt(Statement is stmt, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		local Int is ln: stmt:line;
		local Statement is res: match(on: stmt, when: [
			Statement:VarDecl: local Function of Statement(Array of String is mods, Type is vt, String is vn, Expression is ie, Boolean is hi){
				local Type is nvt: :transformType(t: vt, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local Expression is nie: if({ hi }, { :transformExpr(expr: ie, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName) }, { Expression:Unknown });
				return Statement:VarDecl(modifiers: mods, varType: nvt, varName: vn, initExpr: nie, hasInit: hi);
			},
			Statement:Assign: local Function of Statement(Expression is at, Expression is av){
				return Statement:Assign(
					assignTarget: :transformExpr(expr: at, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName),
					assignValue: :transformExpr(expr: av, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName)
				);
			},
			Statement:Return: local Function of Statement(Expression is re, Boolean is hr){
				local Expression is nre: if({ hr }, { :transformExpr(expr: re, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName) }, { Expression:Unknown });
				return Statement:Return(returnExpr: nre, hasReturnExpr: hr);
			},
			Statement:Expr: local Function of Statement(Expression is es){
				return Statement:Expr(exprStmt: :transformExpr(expr: es, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
			},
			Statement:Forward: local Function of Statement(Array of NamedArg is fargs){
				local Array of NamedArg is nf: [];
				local Int is fi: 0;
				while({ fi < fargs:length() }, {
					local NamedArg is na: fargs:get(index: fi);
					nf:add(item: NamedArg:init(name: na:name, value: :transformExpr(expr: na:value, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName)));
					fi++;
				});
				return Statement:Forward(forwardArgs: nf);
			},
			else: { stmt }
		]);
		res:setLine(line: ln);
		return res;
	}

	local Function of Type is inferGenericMethodArgType(Member is gm, String is tpName, Array of NamedArg is nargs, Map of String to Type is subst){
		local Type is boundType: Type:init(name: '');
		local Int is pi: 0;
		while({ pi < gm:params:length() && boundType:name == '' }, {
			local Parameter is p: gm:params:get(index: pi);
			if({ pi < nargs:length() }, {
				local NamedArg is na: nargs:get(index: pi);
				if({ p:paramType:name == 'Function' && p:paramType:params:length() > 0 }, {
					local Type is pRet: p:paramType:params:get(index: 0);
					if({ pRet:name == tpName }, {
						match(on: na:value, when: [
							Expression:AnonFn: local Function(Type is fnRet, Array of Parameter is _ps, Array of Statement is _bd){
								if({ fnRet:name == 'Function' && fnRet:params:length() > 0 }, {
									boundType: fnRet:params:get(index: 0);
								}, {
									if({ fnRet:name != '' && fnRet:name != 'Void' && fnRet:name != 'Function' }, {
										boundType: fnRet;
									});
								});
							}
						], default: {});
						local Type is naNode: na:value:getResolvedTypeNode();
						if({ boundType:name == '' && naNode:name == 'Function' && naNode:params:length() > 0 }, {
							local Type is rNode: naNode:params:get(index: 0);
							if({ rNode:name != '' && rNode:name != 'Void' }, {
								boundType: :cloneType(t: rNode);
							});
						});
						if({ boundType:name == '' && na:value:resolvedType:startsWith(prefix: 'Function:') }, {
							local String is rSub: na:value:resolvedType:substring(start: 9, end: na:value:resolvedType:length());
							if({ rSub != '' && rSub != 'Void' }, {
								boundType: :resolvedStrToType(s: rSub, subst: subst);
							});
						});
					});
				});
				if({ p:paramType:name == tpName && na:value:resolvedType != '' && na:value:resolvedType != 'Void' }, {
					local Type is naNode2: na:value:getResolvedTypeNode();
					if({ naNode2:name != '' }, {
						boundType: :cloneType(t: naNode2);
					}, {
						boundType: :resolvedStrToType(s: na:value:resolvedType, subst: subst);
					});
				});
			});
			pi++;
		});
		return boundType;
	}

	Function of Expression is transformExpr(Expression is expr, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		local Int is ln: expr:line;
		local Type is exprNode: expr:getResolvedTypeNode();
		local Type is baseResNode: if({ exprNode:name != '' }, { exprNode }, { :resolvedStrToType(s: expr:resolvedType, subst: subst) });
		local Type is newResNode: :transformType(t: baseResNode, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
		local String is newResT: :typeToResolvedStr(t: newResNode);
		local Expression is res: match(on: expr, when: [
			Expression:StringLit: local Function of Expression(String is v){ return Expression:StringLit(value: v); },
			Expression:NumberLit: local Function of Expression(Int is v, String is t){ return Expression:NumberLit(value: v, text: t); },
			Expression:FloatLit: local Function of Expression(String is t){ return Expression:FloatLit(text: t); },
			Expression:BoolLit: local Function of Expression(Boolean is v){ return Expression:BoolLit(value: v); },
			Expression:Ident: local Function of Expression(String is name){ return Expression:Ident(name: name); },
			Expression:Path: local Function of Expression(Array of String is segs){ return Expression:Path(segments: segs); },
			Expression:ArrayLit: local Function of Expression(Array of Expression is items){
				local Array of Expression is nitems: [];
				local Int is i: 0;
				while({ i < items:length() }, {
					nitems:add(item: :transformExpr(expr: items:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
					i++;
				});
				return Expression:ArrayLit(items: nitems);
			},
			Expression:MapLit: local Function of Expression(Array of Expression is keys, Array of Expression is vals){
				local Array of Expression is nkeys: [];
				local Array of Expression is nvals: [];
				local Int is i: 0;
				while({ i < keys:length() }, {
					nkeys:add(item: :transformExpr(expr: keys:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
					nvals:add(item: :transformExpr(expr: vals:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
					i++;
				});
				return Expression:MapLit(keys: nkeys, values: nvals);
			},
			Expression:Cast: local Function of Expression(Expression is inner, String is target, Array of Expression is args){
				local Expression is ninner: :transformExpr(expr: inner, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local String is ntarget: :transformTypeStr(s: target, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local Array of Expression is nargs: [];
				local Int is i: 0;
				while({ i < args:length() }, {
					nargs:add(item: :transformExpr(expr: args:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
					i++;
				});
				return Expression:Cast(inner: ninner, target: ntarget, args: nargs);
			},
			Expression:FieldAccess: local Function of Expression(Expression is target, String is fname){
				return Expression:FieldAccess(
					target: :transformExpr(expr: target, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName),
					fieldName: fname
				);
			},
			Expression:Index: local Function of Expression(Expression is target, Expression is idx){
				return Expression:Index(
					target: :transformExpr(expr: target, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName),
					index: :transformExpr(expr: idx, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName)
				);
			},
			Expression:Binary: local Function of Expression(String is op, Expression is l, Expression is r){
				return Expression:Binary(
					op: op,
					left: :transformExpr(expr: l, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName),
					right: :transformExpr(expr: r, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName)
				);
			},
			Expression:Unary: local Function of Expression(String is op, Expression is opnd){
				return Expression:Unary(
					op: op,
					operand: :transformExpr(expr: opnd, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName)
				);
			},
			Expression:AnonFn: local Function of Expression(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				local Type is nrt: :transformType(t: rt, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local Array of Parameter is nps: [];
				local Int is pi: 0;
				while({ pi < ps:length() }, {
					nps:add(item: :transformParam(p: ps:get(index: pi), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
					pi++;
				});
				local Array of Statement is nbd: :transformStmts(stmts: bd, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				return Expression:AnonFn(returnType: nrt, params: nps, body: nbd);
			},
			Expression:Call: local Function of Expression(CallData is call){
				local Expression is ntarget: :transformExpr(expr: call:target, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local Array of NamedArg is nargs: [];
				local Int is ai: 0;
				while({ ai < call:args:length() }, {
					local NamedArg is na: call:args:get(index: ai);
					nargs:add(item: NamedArg:init(name: na:name, value: :transformExpr(expr: na:value, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName)));
					ai++;
				});
				match(on: ntarget, when: [
					Expression:Ident: local Function(String is tname){
						if({ :templates:has(key: tname) }, {
							if({ newResT:startsWith(prefix: tname . '__') }, {
								ntarget: Expression:Ident(name: newResT);
								ntarget:setLine(line: ln);
								ntarget:setResolvedType(t: newResT);
							}, {
								if({ tname == selfTemplateName && selfSpecName != '' }, {
									ntarget: Expression:Ident(name: selfSpecName);
									ntarget:setLine(line: ln);
									ntarget:setResolvedType(t: selfSpecName);
									if({ call:name == 'init' }, {
										newResT: selfSpecName;
									});
								});
							});
						});
					}
				], default: {});
				local String is callName: call:name;
				local Int is ovIdx: call:overloadIndex;
				local String is recvCls: ntarget:resolvedType;
				if({ recvCls == '' || recvCls == ':' }, {
					recvCls: :curOwnerClassName;
				});
				local String is gmKey: recvCls . ':' . callName;
				if({ !:genericMethods:has(key: gmKey) && :genericMethods:has(key: gmKey . 'Typed') }, {
					gmKey: gmKey . 'Typed';
				});
				if({ !:genericMethods:has(key: gmKey) && :specBaseMap:has(key: recvCls) }, {
					local String is baseRecv: :specBaseMap:get(key: recvCls, default: '');
					if({ :genericMethods:has(key: baseRecv . ':' . callName) }, {
						gmKey: baseRecv . ':' . callName;
					}, {
						if({ :genericMethods:has(key: baseRecv . ':' . callName . 'Typed') }, {
							gmKey: baseRecv . ':' . callName . 'Typed';
						});
					});
				});
				if({ :genericMethods:has(key: gmKey) }, {
					local Member is gm: :genericMethods:get(key: gmKey, default: Member:init(kind: MemberKind:METHOD));
					local String is tpName: :genericMethodTypeParam:get(key: gmKey, default: '');
					local Type is boundType: :inferGenericMethodArgType(gm: gm, tpName: tpName, nargs: nargs, subst: subst);
					if({ boundType:name != '' && :isConcreteType(t: boundType, tplParams: tplParams) }, {
						local Type is specBound: :transformType(t: boundType, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
						callName: :ensureSpecializedMethod(ownerClassName: recvCls, methodName: gm:name, argType: specBound);
						local Map of String to Type is retSubst: Map:init();
						retSubst:set(key: tpName, value: specBound);
						local Type is specRet: :transformType(t: gm:memberType, subst: retSubst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
						if({ specRet:name == 'Function' && specRet:params:length() > 0 }, {
							newResT: :typeToResolvedStr(t: specRet:params:get(index: 0));
						}, {
							if({ specRet:name != '' }, {
								newResT: :typeToResolvedStr(t: specRet);
							});
						});
						ovIdx: 0;
					}, {
						ovIdx: 0;
					});
				});
				local CallData is ncall: CallData:init(target: ntarget, name: callName, args: nargs);
				ncall:bareProvider: call:bareProvider;
				ncall:isBareCall: call:isBareCall;
				ncall:scopedRemainder: call:scopedRemainder;
				ncall:overloadIndex: ovIdx;
				return Expression:Call(call: ncall);
			},
			else: { expr }
		]);
		res:setLine(line: ln);
		res:setResolvedTypeNode(tn: :resolvedStrToType(s: newResT, subst: Map:init()), t: newResT);
		return res;
	}

	Function of Member is transformMember(Member is m, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		if({ m:name == 'using' || m:name == 'namespace' }, {
			return m;
		});
		local Member is nm: Member:init(kind: m:kind);
		nm:setLine(line: m:line);
		nm:setSourceFile(file: m:sourceFile);
		nm:name: m:name;
		nm:modifiers: m:modifiers;
		if({ m:kind == MemberKind:FIELD }, {
			nm:memberType: :transformType(t: m:memberType, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
			nm:hasInit: m:hasInit;
			if({ m:hasInit }, {
				nm:initExpr: :transformExpr(expr: m:initExpr, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
			});
			return nm;
		});
		if({ m:kind == MemberKind:METHOD }, {
			nm:memberType: :transformType(t: m:memberType, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
			local Array of Parameter is nps: [];
			local Int is pi: 0;
			while({ pi < m:params:length() }, {
				nps:add(item: :transformParam(p: m:params:get(index: pi), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
				pi++;
			});
			nm:params: nps;
			nm:body: :transformStmts(stmts: m:body, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
			return nm;
		});
		return m;
	}

	local Function is collectUnboundTypeIdents(Type is t, ClassInfo is cls, Array of String is out){
		if({ t:name != '' && t:name != ':field' && !:seenClassNames:has(key: t:name) && cls:typeParams:indexOf(search: t:name, default: -1) < 0 && out:indexOf(search: t:name, default: -1) < 0 }, {
			out:add(item: t:name);
		});
		local Int is i: 0;
		while({ i < t:params:length() }, {
			:collectUnboundTypeIdents(t: t:params:get(index: i), cls: cls, out: out);
			i++;
		});
	}

	local Function of String is detectMethodTypeParam(Member is m, ClassInfo is cls){
		local Map of String to Int is paramCounts: Map:init();
		local Int is pi: 0;
		while({ pi < m:params:length() }, {
			local Parameter is p: m:params:get(index: pi);
			local Array of String is idents: [];
			:collectUnboundTypeIdents(t: p:paramType, cls: cls, out: idents);
			local Int is ii: 0;
			while({ ii < idents:length() }, {
				local String is id: idents:get(index: ii, default: '');
				paramCounts:set(key: id, value: paramCounts:get(key: id, default: 0) + 1);
				ii++;
			});
			pi++;
		});
		local Array of String is retIdents: [];
		:collectUnboundTypeIdents(t: m:memberType, cls: cls, out: retIdents);
		local Array of String is pKeys: paramCounts:keys();
		local Int is ki: 0;
		while({ ki < pKeys:length() }, {
			local String is id: pKeys:get(index: ki, default: '');
			local Int is cnt: paramCounts:get(key: id, default: 0);
			if({ cnt >= 2 || retIdents:indexOf(search: id, default: -1) >= 0 }, {
				return id;
			});
			ki++;
		});
		return '';
	}

	Function is specialize(ProgramNode is program, Array of ClassInfo is allClasses){
		:templates: Map:init();
		:seenClassNames: Map:init();
		:specKeyToMangled: Map:init();
		:pendingBaseNames: [];
		:pendingTypeArgs: [];
		:pendingMangledNames: [];
		:genericMethods: Map:init();
		:genericMethodTypeParam: Map:init();
		:genericMethodOwners: Map:init();
		:specMethodKeyToName: Map:init();
		:pendingMethodOwners: [];
		:pendingMethodNames: [];
		:pendingMethodArgTypes: [];
		:pendingMethodMangled: [];

		:seenClassNames:set(key: 'Int', value: true);
		:seenClassNames:set(key: 'Float', value: true);
		:seenClassNames:set(key: 'Boolean', value: true);
		:seenClassNames:set(key: 'String', value: true);
		:seenClassNames:set(key: 'Str', value: true);
		:seenClassNames:set(key: 'Byte', value: true);
		:seenClassNames:set(key: 'Void', value: true);
		:seenClassNames:set(key: 'Any', value: true);
		:seenClassNames:set(key: 'Function', value: true);
		:seenClassNames:set(key: 'Array', value: true);
		:seenClassNames:set(key: 'List', value: true);
		:seenClassNames:set(key: 'Map', value: true);
		:seenClassNames:set(key: 'Class', value: true);
		:seenClassNames:set(key: 'Enum', value: true);
		:seenClassNames:set(key: 'Stringable', value: true);
		:seenClassNames:set(key: 'Loadable', value: true);

		local Int is ci: 0;
		while({ ci < program:classes:length() }, {
			local ClassInfo is pcls: program:classes:get(index: ci);
			:seenClassNames:set(key: pcls:name, value: true);
			:seenClassNames:set(key: pcls:qualifiedName(), value: true);
			ci++;
		});
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			:seenClassNames:set(key: cls:name, value: true);
			:seenClassNames:set(key: cls:qualifiedName(), value: true);
			if({ cls:typeParams:length() > 0 && !:bindings:isTransparent(c: cls) && !:bindings:isSysinternal(cls: cls) }, {
				:templates:set(key: cls:name, value: cls);
			});
			ci++;
		});

		# Discover method-level generic templates and strip the unspecialized template overloads
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			if({ !:bindings:isTransparent(c: cls) && !:bindings:isSysinternal(cls: cls) }, {
				local Array of Member is kept: [];
				local Int is mi: 0;
				while({ mi < cls:members:length() }, {
					local Member is m: cls:members:get(index: mi);
					if({ m:kind == MemberKind:METHOD }, {
						local String is mtp: :detectMethodTypeParam(m: m, cls: cls);
						if({ mtp != '' }, {
							local String is gmKey: cls:name . ':' . m:name;
							:genericMethods:set(key: gmKey, value: m);
							:genericMethodTypeParam:set(key: gmKey, value: mtp);
							:genericMethodOwners:set(key: gmKey, value: cls);
						}, {
							kept:add(item: m);
						});
					}, {
						kept:add(item: m);
					});
					mi++;
				});
				cls:members: kept;
			});
			ci++;
		});

		if({ :templates:keys():length() == 0 && :genericMethods:keys():length() == 0 }, {
			return;
		});

		# 1. Transform all non-template classes in place, discovering concrete generic instantiations
		local Map of String to Type is emptySubst: Map:init();
		local Map of String to Boolean is emptyTpl: Map:init();
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			if({ cls:typeParams:length() == 0 && !:bindings:isSysinternal(cls: cls) }, {
				:curOwnerClassName: cls:name;
				local Array of Member is newMembers: [];
				local Int is mi: 0;
				while({ mi < cls:members:length() }, {
					newMembers:add(item: :transformMember(m: cls:members:get(index: mi), subst: emptySubst, tplParams: emptyTpl, selfTemplateName: '', selfSpecName: ''));
					mi++;
				});
				cls:members: newMembers;
			});
			ci++;
		});

		# 2. Drain worklists of concrete generic class and method specializations transitively
		local Int is wi: 0;
		local Int is mwi: 0;
		while({ wi < :pendingMangledNames:length() || mwi < :pendingMethodMangled:length() }, {
			while({ wi < :pendingMangledNames:length() }, {
				local String is baseName: :pendingBaseNames:get(index: wi, default: '');
				local Array of Type is tArgs: :pendingTypeArgs:get(index: wi);
				local String is mangledName: :pendingMangledNames:get(index: wi, default: '');
				local ClassInfo is tpl: :templates:get(key: baseName, default: ClassInfo:init(name: '', baseClass: '', members: []));
				if({ tpl:name != '' }, {
					:curOwnerClassName: mangledName;
					local Map of String to Type is subst: Map:init();
					local Int is ti: 0;
					while({ ti < tpl:typeParams:length() && ti < tArgs:length() }, {
						subst:set(key: tpl:typeParams:get(index: ti, default: ''), value: tArgs:get(index: ti));
						ti++;
					});
					local Array of Member is specMembers: [];
					local Int is mi: 0;
					while({ mi < tpl:members:length() }, {
						specMembers:add(item: :transformMember(m: tpl:members:get(index: mi), subst: subst, tplParams: emptyTpl, selfTemplateName: baseName, selfSpecName: mangledName));
						mi++;
					});
					local ClassInfo is specCls: ClassInfo:init(name: mangledName, baseClass: tpl:baseClass, members: specMembers);
					specCls:withBaseClasses(name: mangledName, baseClasses: tpl:baseClasses, members: specMembers);
					specCls:setOuter(name: tpl:outerName);
					specCls:setLine(line: tpl:line);
					specCls:setSourceFile(file: tpl:sourceFile);
					specCls:setTypeParams(params: []);
					:specBaseMap:set(key: mangledName, value: baseName);
					:specClassMap:set(key: mangledName, value: specCls);
					:specClassArgsMap:set(key: mangledName, value: tArgs);
					allClasses:add(item: specCls);
					program:classes:add(item: specCls);
				});
				wi++;
			});
			while({ mwi < :pendingMethodMangled:length() }, {
				local String is mOwner: :pendingMethodOwners:get(index: mwi, default: '');
				local String is mName: :pendingMethodNames:get(index: mwi, default: '');
				local Type is mArgType: :pendingMethodArgTypes:get(index: mwi);
				local String is mMangled: :pendingMethodMangled:get(index: mwi, default: '');
				local String is gmKey: mOwner . ':' . mName;
				local String is selfTplName: '';
				local String is selfSpName: '';
				local Map of String to Type is mSubst: Map:init();
				local ClassInfo is ownerCls: ClassInfo:init(name: '', baseClass: '', members: []);
				if({ :genericMethods:has(key: gmKey) }, {
					ownerCls: :genericMethodOwners:get(key: gmKey, default: ownerCls);
				}, {
					if({ :specBaseMap:has(key: mOwner) }, {
						local String is bOwner: :specBaseMap:get(key: mOwner, default: '');
						gmKey: bOwner . ':' . mName;
						ownerCls: :specClassMap:get(key: mOwner, default: ownerCls);
						selfTplName: bOwner;
						selfSpName: mOwner;
						local ClassInfo is bTpl: :templates:get(key: bOwner, default: ClassInfo:init(name: '', baseClass: '', members: []));
						local Array of Type is bArgs: :specClassArgsMap:get(key: mOwner, default: []);
						local Int is bti: 0;
						while({ bti < bTpl:typeParams:length() && bti < bArgs:length() }, {
							mSubst:set(key: bTpl:typeParams:get(index: bti, default: ''), value: bArgs:get(index: bti));
							bti++;
						});
					});
				});
				local Member is gm: :genericMethods:get(key: gmKey, default: Member:init(kind: MemberKind:METHOD));
				local String is tpName: :genericMethodTypeParam:get(key: gmKey, default: '');
				if({ gm:name != '' && ownerCls:name != '' }, {
					:curOwnerClassName: ownerCls:name;
					mSubst:set(key: tpName, value: mArgType);
					local Member is specM: :transformMember(m: gm, subst: mSubst, tplParams: emptyTpl, selfTemplateName: selfTplName, selfSpecName: selfSpName);
					specM:name: mMangled;
					ownerCls:members:add(item: specM);
				});
				mwi++;
			});
		});
		:curOwnerClassName: '';
	}
}
