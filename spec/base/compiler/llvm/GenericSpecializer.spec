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
	## Templates whose BARE name appears in any emitted type spelling —
	## a receiver, a parameter, a field, a local. Their template copy is
	## still live code (no instantiation exists to serve those sites).
	Map of String to Boolean is bareTemplateUsed: Map:init();
	Map of String to ClassInfo is specClassMap: Map:init();
	Map of String to [Type] is specClassArgsMap: Map();
	Array of String is pendingBaseNames: Array();
	[[Type]] is pendingTypeArgs: [];
	Array of String is pendingMangledNames: Array();

	Map of String to Member is genericMethods: Map:init();
	Map of String to String is genericMethodTypeParam: Map:init();
	Map of String to ClassInfo is genericMethodOwners: Map:init();
	Map of String to String is specMethodKeyToName: Map:init();
	Array of String is pendingMethodOwners: Array();
	Array of String is pendingMethodNames: Array();
	[Type] is pendingMethodArgTypes: [];
	Array of String is pendingMethodMangled: Array();
	String is curOwnerClassName: '';

	local Function of Type is makeType(String is name, [Type] is params){
		local Type is t: Type(name: name);
		t:params: params;
		return t;
	}

	local Function of Type is cloneType(Type is t){
		local [Type] is cps: [];
		local Int is i: 0;
		while({ i < t:params:length() }, {
			cps:push(item: :cloneType(t: t:params:get(index: i)));
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

	local Function of String is specKeyFor(String is baseName, [Type] is typeArgs){
		local String is key: baseName;
		local Int is i: 0;
		while({ i < typeArgs:length() }, {
			key: key . ':' . :typeToResolvedStr(t: typeArgs:get(index: i));
			i++;
		});
		return key;
	}

	local Function of String is allocateMangledClassName(String is baseName, [Type] is typeArgs){
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

	## Any is concrete: it is the lowest-level bare Object, and every
	## type — Function, Class, containers — is implemented on top of
	## it. A bare object derived of Any is valid, so `Map of String
	## to Any` instantiates exactly as any typed argument does.
	local Function of Boolean is isConcreteType(Type is t, Map of String to Boolean is tplParams){
		if({ t:name == '' || t:name == 'Void' || tplParams:has(key: t:name) || (!:seenClassNames:has(key: t:name) && !:templates:has(key: t:name)) }, {
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

	local Function of Boolean is areAllConcreteTypes([Type] is types, Map of String to Boolean is tplParams){
		local Int is i: 0;
		while({ i < types:length() }, {
			if({ !:isConcreteType(t: types:get(index: i), tplParams: tplParams) }, {
				return false;
			});
			i++;
		});
		return true;
	}

	local Function of String is ensureSpecialized(String is baseName, [Type] is typeArgs){
		local String is key: :specKeyFor(baseName: baseName, typeArgs: typeArgs);
		if({ :specKeyToMangled:has(key: key) }, {
			return :specKeyToMangled:get(key: key, default: baseName);
		});
		local String is mangled: :allocateMangledClassName(baseName: baseName, typeArgs: typeArgs);
		:specKeyToMangled:set(key: key, value: mangled);
		:specBaseMap:set(key: mangled, value: baseName);
		:specClassArgsMap:set(key: mangled, value: typeArgs);
		:pendingBaseNames:add(item: baseName);
		:pendingTypeArgs:push(item: typeArgs);
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
		:pendingMethodArgTypes:push(item: :cloneType(t: argType));
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
		local [Type] is newParams: [];
		local Int is i: 0;
		while({ i < t:params:length() }, {
			newParams:push(item: :transformType(t: t:params:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
			i++;
		});
		local String is bName: t:name;
		if({ subst:has(key: bName) }, {
			bName: subst:get(key: bName, default: t):name;
		});
		if({ :templates:has(key: bName) }, {
			local ClassInfo is tpl: :templates:get(key: bName, default: ClassInfo:init(name: '', baseClass: '', members: Array()));
			if({ newParams:length() == tpl:typeParams:length() && newParams:length() > 0 }, {
				if({ bName == 'List' && selfTemplateName == 'Array' }, {
					:bareTemplateUsed:set(key: 'List', value: true);
					return Type:init(name: 'List');
				});
				if({ :areAllConcreteTypes(types: newParams, tplParams: tplParams) }, {
					local String is mangled: :ensureSpecialized(baseName: bName, typeArgs: newParams);
					return Type:init(name: mangled);
				});
			});
			if({ bName == selfTemplateName && selfSpecName != '' && newParams:length() == 0 }, {
				return Type:init(name: selfSpecName);
			});
			if({ newParams:length() == 0 }, {
				:bareTemplateUsed:set(key: bName, value: true);
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
		local String is norm: s:replaceAll(search: ' of ', replacement: ':'):replaceAll(search: ' to ', replacement: ':');
		local Array of String is rawParts: norm:split(delimiter: ':');
		# Greedy pass first; on an ill-formed outer type (an arity-1
		# container absorbing a sibling argument of the outer generic),
		# retry with the hardcoded containers parsed bare. Mirrors the
		# checker's rebuildTypeNode repair.
		local Type is parsedT: :rebuildResolvedType(rawParts: rawParts, subst: subst, bareContainers: false);
		if({ parsedT:name == '' }, {
			parsedT: :rebuildResolvedType(rawParts: rawParts, subst: subst, bareContainers: true);
		});
		if({ parsedT:name != '' }, {
			return parsedT;
		});
		return Type:init(name: s);
	}

	local Function of Int is segArity(String is seg, Boolean is bareContainers){
		if({ :templates:has(key: seg) }, {
			local ClassInfo is tpl: :templates:get(key: seg, default: ClassInfo:init(name: '', baseClass: '', members: Array()));
			return tpl:typeParams:length();
		});
		if({ seg == 'Array' || seg == 'List' || seg == 'Function' }, {
			return if({ bareContainers }, { 0 }, { 1 });
		});
		if({ seg == 'Map' }, {
			return 2;
		});
		return 0;
	}

	local Function of Type is rebuildResolvedType(Array of String is rawParts, Map of String to Type is subst, Boolean is bareContainers){
		local [Type] is stack: [];
		local Int is idx: rawParts:length() - 1;
		while({ idx >= 0 }, {
			local String is seg: rawParts:get(index: idx, default: '');
			if({ subst:has(key: seg) }, {
				stack:push(item: :cloneType(t: subst:get(key: seg, default: Type(name: seg))));
			}, {
				local Int is arity: :segArity(seg: seg, bareContainers: bareContainers);
				if({ arity > 0 && stack:length() >= arity }, {
					local [Type] is tArgs: [];
					local Int is ki: 0;
					while({ ki < arity }, {
						tArgs:push(item: stack:pop());
						ki++;
					});
					stack:push(item: :makeType(name: seg, params: tArgs));
				}, {
					stack:push(item: Type(name: seg));
				});
			});
			idx: idx - 1;
		});
		if({ stack:length() == 0 }, {
			return Type:init(name: '');
		});
		local Type is top: stack:get(index: stack:length() - 1);
		local Int is topArity: :segArity(seg: top:name, bareContainers: bareContainers);
		if({ topArity > 0 && top:params:length() != topArity }, {
			return Type:init(name: '');
		});
		return top;
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

	Function of [Statement] is transformStmts([Statement] is stmts, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		local [Statement] is out: [];
		local Int is i: 0;
		while({ i < stmts:length() }, {
			out:push(item: :transformStmt(stmt: stmts:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
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
				# Bare nested-variant construction (`local Maybe2 of String is
				# n: Maybe2:None;`): the init path names the TEMPLATE's
				# variant while the declared type grounds the instantiation —
				# rewrite the head so the emitter constructs the SPEC class's
				# variant (concrete layout, matching typename).
				if({ hi && nvt:name != '' && vt:name != nvt:name }, {
					match(on: nie, when: [
						Expression:Path: local Function(Array of String is psegs){
							if({ psegs:length() >= 2 && vt:name != '' && psegs:get(index: 0) == vt:name }, {
								local Array of String is nsegs: Array([nvt:name]);
								local Int is psi: 1;
								while({ psi < psegs:length() }, {
									nsegs:add(item: psegs:get(index: psi));
									psi++;
								});
								nie: Expression:Path(segments: nsegs);
								nie:setResolvedTypeNode(tn: nvt, t: nvt:name);
							});
						}
					], default: {});
				});
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
				local Array of NamedArg is nf: Array();
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
							Expression:AnonFn: local Function(Type is fnRet, [Parameter] is _ps, [Statement] is _bd){
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
						if({ boundType:name == '' && naNode:isFunction() }, {
							local Type is rNode: naNode:functionReturn();
							if({ !rNode:isEmpty() && !rNode:isVoid() }, {
								boundType: :cloneType(t: rNode);
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
				local Array of Expression is nitems: Array();
				local Int is i: 0;
				while({ i < items:length() }, {
					nitems:add(item: :transformExpr(expr: items:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
					i++;
				});
				return Expression:ArrayLit(items: nitems);
			},
			Expression:MapLit: local Function of Expression(Array of Expression is keys, Array of Expression is vals){
				local Array of Expression is nkeys: Array();
				local Array of Expression is nvals: Array();
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
				local Array of Expression is nargs: Array();
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
			Expression:AnonFn: local Function of Expression(Type is rt, [Parameter] is ps, [Statement] is bd){
				local Type is nrt: :transformType(t: rt, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local [Parameter] is nps: [];
				local Int is pi: 0;
				while({ pi < ps:length() }, {
					nps:push(item: :transformParam(p: ps:get(index: pi), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
					pi++;
				});
				local [Statement] is nbd: :transformStmts(stmts: bd, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				return Expression:AnonFn(returnType: nrt, params: nps, body: nbd);
			},
			Expression:Call: local Function of Expression(CallData is call){
				local Expression is ntarget: :transformExpr(expr: call:target, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local Array of NamedArg is nargs: Array();
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
								ntarget:setResolvedTypeNode(tn: Type:init(name: newResT), t: newResT);
							}, {
								if({ tname == selfTemplateName && selfSpecName != '' }, {
									ntarget: Expression:Ident(name: selfSpecName);
									ntarget:setLine(line: ln);
									ntarget:setResolvedTypeNode(tn: Type:init(name: selfSpecName), t: selfSpecName);
									if({ call:name == 'init' }, {
										newResT: selfSpecName;
										newResNode: Type:init(name: selfSpecName);
									});
								});
							});
						});
					},
					Expression:Path: local Function(Array of String is psegs){
						# Nested-shorthand construction (`Box2:Full(...)`) and
						# other Path-target calls: rewrite the head segment to
						# the mangled instantiation the same way the Ident case
						# rewrites a bare template name, so the call resolves
						# against the SPEC class's nested members. The captured
						# ntarget rides the shared frame, as in the Ident case.
						if({ psegs:length() > 0 }, {
							local String is phead: psegs:get(index: 0);
							if({ :templates:has(key: phead) || (phead == selfTemplateName && selfSpecName != '') }, {
								local String is specHead: '';
								if({ newResT:startsWith(prefix: phead . '__') }, {
									specHead: newResT;
								}, {
									if({ phead == selfTemplateName && selfSpecName != '' }, {
										specHead: selfSpecName;
									});
								});
								if({ specHead != '' }, {
									local Array of String is nsegs: Array([specHead]);
									local Int is si: 1;
									while({ si < psegs:length() }, {
										nsegs:add(item: psegs:get(index: si));
										si++;
									});
									ntarget: Expression:Path(segments: nsegs);
									ntarget:setLine(line: ln);
									ntarget:setResolvedTypeNode(tn: newResNode, t: newResT);
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
							newResNode: specRet:params:get(index: 0);
							newResT: :typeToResolvedStr(t: newResNode);
						}, {
							if({ specRet:name != '' }, {
								newResNode: specRet;
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
		# The transformed node rides alongside its string: an override arm
		# (method return, self-init rename) sets it directly, so the tail
		# re-parse only runs for paths that never had a node.
		if({ newResNode:name != '' }, {
			res:setResolvedTypeNode(tn: newResNode, t: newResT);
		}, {
			res:setResolvedTypeNode(tn: :resolvedStrToType(s: newResT, subst: Map:init()), t: newResT);
		});
		return res;
	}

	Function of Member is transformMember(Member is m, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		if({ m:name == 'using' || m:name == 'namespace' || m:name == 'castable' }, {
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
			local [Parameter] is nps: [];
			local Int is pi: 0;
			while({ pi < m:params:length() }, {
				nps:push(item: :transformParam(p: m:params:get(index: pi), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
				pi++;
			});
			nm:params: nps;
			nm:body: :transformStmts(stmts: m:body, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
			return nm;
		});
		if({ m:kind == MemberKind:CLASS }, {
			# Generic templates: descend into nested classes (enum variants,
			# inner classes) so the specialization carries CONCRETE members.
			# The template's own nested shape stays unspecialized — only the
			# mangled instantiation gets the substituted clone.
			local ClassInfo is sub: m:nestedClass;
			if({ sub:name == '' }, {
				return m;
			});
			local Array of Member is subMembers: Array();
			local Int is smi: 0;
			while({ smi < sub:members:length() }, {
				subMembers:add(item: :transformMember(m: sub:members:get(index: smi), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
				smi++;
			});
			local ClassInfo is nsub: ClassInfo:init(name: sub:name, baseClass: sub:baseClass, members: subMembers);
			nsub:withBaseClasses(name: sub:name, baseClasses: sub:baseClasses, members: subMembers);
			nsub:setLine(line: sub:line);
			nsub:setSourceFile(file: sub:sourceFile);
			nsub:setTypeParams(params: Array());
			if({ selfSpecName != '' }, {
				nsub:setOuter(name: selfSpecName);
			}, {
				nsub:setOuter(name: sub:outerName);
			});
			local Member is nest: Member:init(kind: MemberKind:CLASS);
			nest:setLine(line: m:line);
			nest:setSourceFile(file: m:sourceFile);
			nest:name: m:name;
			nest:modifiers: m:modifiers;
			nest:nestedClass: nsub;
			nest:line: m:line;
			return nest;
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
			local Array of String is idents: Array();
			:collectUnboundTypeIdents(t: p:paramType, cls: cls, out: idents);
			local Int is ii: 0;
			while({ ii < idents:length() }, {
				local String is id: idents:get(index: ii, default: '');
				paramCounts:set(key: id, value: paramCounts:get(key: id, default: 0) + 1);
				ii++;
			});
			pi++;
		});
		local Array of String is retIdents: Array();
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
		:pendingBaseNames: Array();
		:pendingTypeArgs: [];
		:pendingMangledNames: Array();
		:genericMethods: Map:init();
		:genericMethodTypeParam: Map:init();
		:genericMethodOwners: Map:init();
		:specMethodKeyToName: Map:init();
		:pendingMethodOwners: Array();
		:pendingMethodNames: Array();
		:pendingMethodArgTypes: [];
		:pendingMethodMangled: Array();

		:seenClassNames:set(key: 'Int', value: true);
		:seenClassNames:set(key: 'Int8', value: true);
		:seenClassNames:set(key: 'Int16', value: true);
		:seenClassNames:set(key: 'Int32', value: true);
		:seenClassNames:set(key: 'Int128', value: true);
		:seenClassNames:set(key: 'ISize', value: true);
		:seenClassNames:set(key: 'Float', value: true);
		:seenClassNames:set(key: 'Float32', value: true);
		:seenClassNames:set(key: 'Boolean', value: true);
		:seenClassNames:set(key: 'String', value: true);
		:seenClassNames:set(key: 'Str', value: true);
		:seenClassNames:set(key: 'Byte', value: true);
		:seenClassNames:set(key: 'UInt8', value: true);
		:seenClassNames:set(key: 'UInt16', value: true);
		:seenClassNames:set(key: 'UInt32', value: true);
		:seenClassNames:set(key: 'UInt64', value: true);
		:seenClassNames:set(key: 'UInt128', value: true);
		:seenClassNames:set(key: 'USize', value: true);
		:seenClassNames:set(key: 'Rune', value: true);
		:seenClassNames:set(key: 'RawPtr', value: true);
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
			if({ cls:typeParams:length() > 0 && !:bindings:isSysinternal(cls: cls) }, {
				:templates:set(key: cls:name, value: cls);
			});
			ci++;
		});

		# Discover method-level generic templates and strip the unspecialized template overloads
		ci: 0;
		while({ ci < allClasses:length() }, {
			local ClassInfo is cls: allClasses:get(index: ci);
			if({ !:bindings:isSysinternal(cls: cls) }, {
				local Array of Member is kept: Array();
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
				local Array of Member is newMembers: Array();
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
				local [Type] is tArgs: :pendingTypeArgs:get(index: wi);
				local String is mangledName: :pendingMangledNames:get(index: wi, default: '');
				local ClassInfo is tpl: :templates:get(key: baseName, default: ClassInfo:init(name: '', baseClass: '', members: Array()));
				if({ tpl:name != '' }, {
					:curOwnerClassName: mangledName;
					local Map of String to Type is subst: Map:init();
					local Int is ti: 0;
					while({ ti < tpl:typeParams:length() && ti < tArgs:length() }, {
						subst:set(key: tpl:typeParams:get(index: ti, default: ''), value: tArgs:get(index: ti));
						ti++;
					});
					local Array of Member is specMembers: Array();
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
					specCls:setTypeParams(params: Array());
					:specBaseMap:set(key: mangledName, value: baseName);
					:specClassMap:set(key: mangledName, value: specCls);
					:specClassArgsMap:set(key: mangledName, value: tArgs);
					allClasses:add(item: specCls);
					program:classes:add(item: specCls);
					# Nested members of the spec class (enum variants, inner
					# classes) must be visible to emission: the IrBuilder
					# collected the program's own nested classes BEFORE the
					# specializer ran, so flatten the spec clones here —
					# mirroring the Loader's flattening of declared nesting.
					local Array of ClassInfo is nestedQueue: Array();
					local Int is nqi: 0;
					while({ nqi < specCls:members:length() }, {
						local Member is qm: specCls:members:get(index: nqi);
						if({ qm:kind == MemberKind:CLASS }, {
							nestedQueue:add(item: qm:nestedClass);
						});
						nqi++;
					});
					while({ nestedQueue:length() > 0 }, {
						local ClassInfo is nq: nestedQueue:pop(default: ClassInfo:init(name: '', baseClass: '', members: Array()));
						allClasses:add(item: nq);
						program:classes:add(item: nq);
						nq:members:each(action: local Function(Member is dm){
							if({ dm:kind == MemberKind:CLASS }, {
								nestedQueue:add(item: dm:nestedClass);
							});
						});
					});
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
				local ClassInfo is ownerCls: ClassInfo:init(name: '', baseClass: '', members: Array());
				if({ :genericMethods:has(key: gmKey) }, {
					ownerCls: :genericMethodOwners:get(key: gmKey, default: ownerCls);
				}, {
					if({ :specBaseMap:has(key: mOwner) }, {
						local String is bOwner: :specBaseMap:get(key: mOwner, default: '');
						gmKey: bOwner . ':' . mName;
						ownerCls: :specClassMap:get(key: mOwner, default: ownerCls);
						selfTplName: bOwner;
						selfSpName: mOwner;
						local ClassInfo is bTpl: :templates:get(key: bOwner, default: ClassInfo:init(name: '', baseClass: '', members: Array()));
						local [Type] is emptyTypes: [];
						local [Type] is bArgs: :specClassArgsMap:get(key: mOwner, default: emptyTypes);
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
