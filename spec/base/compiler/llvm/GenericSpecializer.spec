#! Package base:compiler:llvm
#! Monomorphizes generic classes (`Class is C of T`, `Class is P of A to B`) and
#! generic methods into distinct concrete specializations per used type argument.

Class is GenericSpecializer{
	replace [String] is namespace: ['base', 'compiler', 'llvm'];

	replace [[String]] is using: [
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', SemType],
		['base', 'compiler', 'checker', as SemTypes()],
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
	local Map of String to SemType is semTypeCache: Map:init();

	local Function of SemType is cachedNamedSemType(String is name){
		if({ name == '' }, { return SemTypes:EMPTY; });
		local SemType is hit: :semTypeCache:get(key: name, default: SemTypes:EMPTY);
		if({ !hit:isEmpty() }, { return hit; });
		local SemType is st: SemTypes:named(name: name);
		:semTypeCache:set(key: name, value: st);
		return st;
	}

	local Function of SemType is cachedSemType(Type is t){
		if({ t:name == '' }, { return SemTypes:EMPTY; });
		if({ t:params:length() == 0 }, {
			return :cachedNamedSemType(name: t:name);
		});
		return SemTypes:fromAstType(t: t);
	}

	local Function of Type is makeType(String is name, [Type] is params){
		local Type is t: Type(name: name);
		t:params: params;
		return t;
	}

	local Function of Type is cloneType(Type is t){
		local [Type] is cps: [];
		times(count: t:params:length(), worker: local Function(Int is i){
			cps:push(item: :cloneType(t: t:params:get(index: i)));
		});
		return :makeType(name: t:name, params: cps);
	}

	local Function of String is typeToSymbolSegment(Type is t){
		local String is out: t:name;
		times(count: t:params:length(), worker: local Function(Int is i){
			out: out . '_' . :typeToSymbolSegment(t: t:params:get(index: i));
		});
		return out;
	}

	local Function of String is typeToResolvedStr(Type is t){
		if({ t:params:length() == 0 }, {
			return t:name;
		});
		local String is out: t:name;
		times(count: t:params:length(), worker: local Function(Int is i){
			out: out . ':' . :typeToResolvedStr(t: t:params:get(index: i));
		});
		return out;
	}

	local Function of String is specKeyFor(String is baseName, [Type] is typeArgs){
		local String is key: baseName;
		times(count: typeArgs:length(), worker: local Function(Int is i){
			key: key . ':' . :typeToResolvedStr(t: typeArgs:get(index: i));
		});
		return key;
	}

	local Function of String is allocateMangledClassName(String is baseName, [Type] is typeArgs){
		local String is stem: baseName;
		times(count: typeArgs:length(), worker: local Function(Int is i){
			stem: stem . '__' . :typeToSymbolSegment(t: typeArgs:get(index: i));
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
		times(count: t:params:length(), worker: local Function(Int is i){
			newParams:push(item: :transformType(t: t:params:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
		});
		local String is bName: t:name;
		if({ subst:has(key: bName) }, {
			bName: subst:get(key: bName, default: t):name;
		});
		if({ :templates:has(key: bName) }, {
			local ClassInfo is tpl: :templates:get(key: bName, default: ClassInfo(name: '', baseClass: '', members: []));
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

	local Function of Boolean is isConcreteSemType(SemType is st, Map of String to Boolean is tplParams){
		return match(on: st, when: [
			SemType:Empty: { false },
			SemType:Prim: local Function of Boolean(Primitive is kind){ return kind != Primitive:VOID; },
			SemType:StrView: { true },
			SemType:ArrayOf: local Function of Boolean(SemType is elem){
				if({ elem:isEmpty() }, { return true; });
				return :isConcreteSemType(st: elem, tplParams: tplParams);
			},
			SemType:ListOf: local Function of Boolean(SemType is elem){
				if({ elem:isEmpty() }, { return true; });
				return :isConcreteSemType(st: elem, tplParams: tplParams);
			},
			SemType:MapOf: local Function of Boolean(SemType is key, SemType is val){
				if({ key:isEmpty() || val:isEmpty() }, { return true; });
				return :isConcreteSemType(st: key, tplParams: tplParams) && :isConcreteSemType(st: val, tplParams: tplParams);
			},
			SemType:FnOf: local Function of Boolean(SemType is ret){
				if({ ret:isEmpty() || ret:isVoid() }, { return true; });
				return :isConcreteSemType(st: ret, tplParams: tplParams);
			},
			SemType:Named: local Function of Boolean([String] is path, [SemType] is params){
				local String is nm: if({ path:length() == 1 }, { path:get(index: 0) }, { st:baseName() });
				if({ nm == '' || nm == 'Void' || tplParams:has(key: nm) || (!:seenClassNames:has(key: nm) && !:templates:has(key: nm)) }, {
					return false;
				});
				local Int is i: 0;
				while({ i < params:length() }, {
					if({ !:isConcreteSemType(st: params:get(index: i), tplParams: tplParams) }, {
						return false;
					});
					i++;
				});
				return true;
			}
		]);
	}

	## Transforms a [SemType] directly without round-tripping through AST [Type] nodes.
	## Non-template, non-substituted primitives and named classes return [st] unchanged
	## with zero allocations.
	Function of SemType is transformSemType(SemType is st, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		return match(on: st, when: [
			SemType:Empty: { st },
			SemType:Prim: local Function of SemType(Primitive is kind){ return st; },
			SemType:StrView: { st },
			SemType:ArrayOf: local Function of SemType(SemType is elem){
				if({ elem:isEmpty() }, {
					if({ selfTemplateName == 'Array' && selfSpecName != '' }, {
						return :cachedNamedSemType(name: selfSpecName);
					});
					if({ :templates:has(key: 'Array') }, {
						:bareTemplateUsed:set(key: 'Array', value: true);
					});
					return st;
				});
				local SemType is ne: :transformSemType(st: elem, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				if({ :templates:has(key: 'Array') }, {
					local ClassInfo is tpl: :templates:get(key: 'Array', default: ClassInfo(name: '', baseClass: '', members: []));
					if({ tpl:typeParams:length() == 1 && :isConcreteSemType(st: ne, tplParams: tplParams) }, {
						local String is mangled: :ensureSpecialized(baseName: 'Array', typeArgs: [ne:toAstType()]);
						return :cachedNamedSemType(name: mangled);
					});
				});
				return SemType:ArrayOf(elem: ne);
			},
			SemType:ListOf: local Function of SemType(SemType is elem){
				if({ elem:isEmpty() }, {
					if({ selfTemplateName == 'List' && selfSpecName != '' }, {
						return :cachedNamedSemType(name: selfSpecName);
					});
					if({ :templates:has(key: 'List') }, {
						:bareTemplateUsed:set(key: 'List', value: true);
					});
					return st;
				});
				local SemType is ne: :transformSemType(st: elem, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				if({ :templates:has(key: 'List') }, {
					local ClassInfo is tpl: :templates:get(key: 'List', default: ClassInfo(name: '', baseClass: '', members: []));
					if({ tpl:typeParams:length() == 1 }, {
						if({ selfTemplateName == 'Array' }, {
							:bareTemplateUsed:set(key: 'List', value: true);
							return SemTypes:BARE_LIST;
						});
						if({ :isConcreteSemType(st: ne, tplParams: tplParams) }, {
							local String is mangled: :ensureSpecialized(baseName: 'List', typeArgs: [ne:toAstType()]);
							return :cachedNamedSemType(name: mangled);
						});
					});
				});
				return SemType:ListOf(elem: ne);
			},
			SemType:MapOf: local Function of SemType(SemType is key, SemType is val){
				if({ key:isEmpty() || val:isEmpty() }, {
					if({ selfTemplateName == 'Map' && selfSpecName != '' }, {
						return :cachedNamedSemType(name: selfSpecName);
					});
					if({ :templates:has(key: 'Map') }, {
						:bareTemplateUsed:set(key: 'Map', value: true);
					});
					return st;
				});
				local SemType is nk: :transformSemType(st: key, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local SemType is nv: :transformSemType(st: val, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				if({ :templates:has(key: 'Map') }, {
					local ClassInfo is tpl: :templates:get(key: 'Map', default: ClassInfo(name: '', baseClass: '', members: []));
					if({ tpl:typeParams:length() == 2 && :isConcreteSemType(st: nk, tplParams: tplParams) && :isConcreteSemType(st: nv, tplParams: tplParams) }, {
						local String is mangled: :ensureSpecialized(baseName: 'Map', typeArgs: [nk:toAstType(), nv:toAstType()]);
						return :cachedNamedSemType(name: mangled);
					});
				});
				return SemType:MapOf(key: nk, val: nv);
			},
			SemType:FnOf: local Function of SemType(SemType is ret){
				if({ ret:isEmpty() || ret:isVoid() }, { return st; });
				local SemType is nr: :transformSemType(st: ret, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				return SemType:FnOf(ret: nr);
			},
			SemType:Named: local Function of SemType([String] is path, [SemType] is params){
				local String is bName: if({ path:length() == 1 }, { path:get(index: 0) }, { st:baseName() });
				if({ params:length() == 0 }, {
					if({ !subst:has(key: bName) && !:templates:has(key: bName) }, {
						return st;
					});
					if({ subst:has(key: bName) }, {
						local Type is mapped: :cloneType(t: subst:get(key: bName, default: Type:init(name: bName)));
						local Type is tr: :transformType(t: mapped, subst: Map:init(), tplParams: tplParams, selfTemplateName: '', selfSpecName: '');
						return :cachedSemType(t: tr);
					});
					if({ bName == selfTemplateName && selfSpecName != '' }, {
						return :cachedNamedSemType(name: selfSpecName);
					});
					:bareTemplateUsed:set(key: bName, value: true);
					return st;
				});
				local [SemType] is newParams: [];
				times(count: params:length(), worker: local Function(Int is i){
					newParams:push(item: :transformSemType(st: params:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
				});
				local [String] is newPath: path;
				if({ subst:has(key: bName) }, {
					bName: subst:get(key: bName, default: Type:init(name: bName)):name;
					newPath: [bName];
				});
				if({ :templates:has(key: bName) }, {
					local ClassInfo is tpl: :templates:get(key: bName, default: ClassInfo(name: '', baseClass: '', members: []));
					if({ newParams:length() == tpl:typeParams:length() }, {
						local Boolean is allC: true;
						local Int is ci: 0;
						while({ ci < newParams:length() && allC }, {
							if({ !:isConcreteSemType(st: newParams:get(index: ci), tplParams: tplParams) }, {
								allC: false;
							});
							ci++;
						});
						if({ allC }, {
							local [Type] is astArgs: [];
							times(count: newParams:length(), worker: local Function(Int is ai){
								astArgs:push(item: newParams:get(index: ai):toAstType());
							});
							local String is mangled: :ensureSpecialized(baseName: bName, typeArgs: astArgs);
							return :cachedNamedSemType(name: mangled);
						});
					});
				});
				return SemType:Named(path: newPath, params: newParams);
			}
		]);
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
			local ClassInfo is tpl: :templates:get(key: seg, default: ClassInfo(name: '', baseClass: '', members: []));
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
		rangeStep(start: rawParts:length() - 1, end: -1, step: -1, worker: local Function(Int is idx){
			local String is seg: rawParts:get(index: idx, default: '');
			if({ subst:has(key: seg) }, {
				stack:push(item: :cloneType(t: subst:get(key: seg, default: Type(name: seg))));
			}, {
				local Int is arity: :segArity(seg: seg, bareContainers: bareContainers);
				if({ arity > 0 && stack:length() >= arity }, {
					local [Type] is tArgs: [];
					repeat(count: arity, worker: {
						tArgs:push(item: stack:pop());
					});
					stack:push(item: :makeType(name: seg, params: tArgs));
				}, {
					stack:push(item: Type(name: seg));
				});
			});
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
		times(count: stmts:length(), worker: local Function(Int is i){
			out:push(item: :transformStmt(stmt: stmts:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
		});
		return out;
	}

	Function of Statement is transformStmt(Statement is stmt, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		local Int is ln: stmt:line;
		local Statement is res: match(on: stmt, when: [
			Statement:VarDecl: local Function of Statement([String] is mods, Type is vt, String is vn, Expression is ie, Boolean is hi){
				local Type is nvt: :transformType(t: vt, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local Expression is nie: if({ hi }, { :transformExpr(expr: ie, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName) }, { Expression:Unknown });
				# Bare nested-variant construction (`local Maybe2 of String is
				# n: Maybe2:None;`): the init path names the TEMPLATE's
				# variant while the declared type grounds the instantiation —
				# rewrite the head so the emitter constructs the SPEC class's
				# variant (concrete layout, matching typename).
				if({ hi && nvt:name != '' && vt:name != nvt:name }, {
					match(on: nie, when: [
						Expression:Path: local Function([String] is psegs){
							if({ psegs:length() >= 2 && vt:name != '' && psegs:get(index: 0) == vt:name }, {
								local [String] is nsegs: [nvt:name];
								range(start: 1, end: psegs:length(), action: local Function(Int is psi){
									nsegs:push(item: psegs:get(index: psi));
								});
								nie: Expression:Path(segments: nsegs);
								nie:setSemType(st: :cachedSemType(t: nvt));
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
			Statement:Forward: local Function of Statement([NamedArg] is fargs){
				local [NamedArg] is nf: [];
				times(count: fargs:length(), worker: local Function(Int is fi){
					local NamedArg is na: fargs:get(index: fi);
					nf:push(item: NamedArg(name: na:name, value: :transformExpr(expr: na:value, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName)));
				});
				return Statement:Forward(forwardArgs: nf);
			},
			else: { stmt }
		]);
		res:setLine(line: ln);
		return res;
	}

	local Function of Type is inferGenericMethodArgType(Member is gm, String is tpName, [NamedArg] is nargs, Map of String to Type is subst){
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
						local SemType is naSem: na:value:getSemType();
						if({ boundType:name == '' && naSem:hasFunctionReturn() }, {
							boundType: naSem:functionReturn():toAstType();
						});
					});
				});
				local SemType is naSem2: na:value:getSemType();
				if({ p:paramType:name == tpName && !naSem2:isEmpty() && !naSem2:isVoid() }, {
					boundType: naSem2:toAstType();
				});
			});
			pi++;
		});
		return boundType;
	}

	Function of Expression is transformExpr(Expression is expr, Map of String to Type is subst, Map of String to Boolean is tplParams, String is selfTemplateName, String is selfSpecName){
		local Int is ln: expr:line;
		local SemType is newResSem: :transformSemType(st: expr:getSemType(), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
		local Expression is res: match(on: expr, when: [
			Expression:StringLit: local Function of Expression(String is v){ return Expression:StringLit(value: v); },
			Expression:NumberLit: local Function of Expression(Int is v, String is t){ return Expression:NumberLit(value: v, text: t); },
			Expression:FloatLit: local Function of Expression(String is t){ return Expression:FloatLit(text: t); },
			Expression:BoolLit: local Function of Expression(Boolean is v){ return Expression:BoolLit(value: v); },
			Expression:Ident: local Function of Expression(String is name){ return Expression:Ident(name: name); },
			Expression:Path: local Function of Expression([String] is segs){ return Expression:Path(segments: segs); },
			Expression:ArrayLit: local Function of Expression([Expression] is items){
				local [Expression] is nitems: [];
				times(count: items:length(), worker: local Function(Int is i){
					nitems:push(item: :transformExpr(expr: items:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
				});
				return Expression:ArrayLit(items: nitems);
			},
			Expression:MapLit: local Function of Expression([Expression] is keys, [Expression] is vals){
				local [Expression] is nkeys: [];
				local [Expression] is nvals: [];
				times(count: keys:length(), worker: local Function(Int is i){
					nkeys:push(item: :transformExpr(expr: keys:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
					nvals:push(item: :transformExpr(expr: vals:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
				});
				return Expression:MapLit(keys: nkeys, values: nvals);
			},
			Expression:Cast: local Function of Expression(Expression is inner, String is target, [Expression] is args){
				local Expression is ninner: :transformExpr(expr: inner, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local String is ntarget: :transformTypeStr(s: target, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local [Expression] is nargs: [];
				times(count: args:length(), worker: local Function(Int is i){
					nargs:push(item: :transformExpr(expr: args:get(index: i), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
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
				times(count: ps:length(), worker: local Function(Int is pi){
					nps:push(item: :transformParam(p: ps:get(index: pi), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
				});
				local [Statement] is nbd: :transformStmts(stmts: bd, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				return Expression:AnonFn(returnType: nrt, params: nps, body: nbd);
			},
			Expression:Call: local Function of Expression(CallData is call){
				local Expression is ntarget: :transformExpr(expr: call:target, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName);
				local [NamedArg] is nargs: [];
				times(count: call:args:length(), worker: local Function(Int is ai){
					local NamedArg is na: call:args:get(index: ai);
					nargs:push(item: NamedArg(name: na:name, value: :transformExpr(expr: na:value, subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName)));
				});
				match(on: ntarget, when: [
					Expression:Ident: local Function(String is tname){
						if({ :templates:has(key: tname) }, {
							local String is newResBase: newResSem:baseName();
							if({ newResBase:startsWith(prefix: tname . '__') }, {
								ntarget: Expression:Ident(name: newResBase);
								ntarget:setLine(line: ln);
								ntarget:setSemType(st: newResSem);
							}, {
								if({ tname == selfTemplateName && selfSpecName != '' }, {
									local SemType is selfSem: :cachedNamedSemType(name: selfSpecName);
									ntarget: Expression:Ident(name: selfSpecName);
									ntarget:setLine(line: ln);
									ntarget:setSemType(st: selfSem);
									if({ call:name == 'init' }, {
										newResSem: selfSem;
									});
								});
							});
						});
					},
					Expression:Path: local Function([String] is psegs){
						# Nested-shorthand construction (`Box2:Full(...)`) and
						# other Path-target calls: rewrite the head segment to
						# the mangled instantiation the same way the Ident case
						# rewrites a bare template name, so the call resolves
						# against the SPEC class's nested members. The captured
						# ntarget rides the shared frame, as in the Ident case.
						if({ psegs:length() > 0 }, {
							local String is phead: psegs:get(index: 0);
							if({ :templates:has(key: phead) || (phead == selfTemplateName && selfSpecName != '') }, {
								local String is newResBase: newResSem:baseName();
								local String is specHead: '';
								if({ newResBase:startsWith(prefix: phead . '__') }, {
									specHead: newResBase;
								}, {
									if({ phead == selfTemplateName && selfSpecName != '' }, {
										specHead: selfSpecName;
									});
								});
								if({ specHead != '' }, {
									local [String] is nsegs: [specHead];
									range(start: 1, end: psegs:length(), action: local Function(Int is si){
										nsegs:push(item: psegs:get(index: si));
									});
									ntarget: Expression:Path(segments: nsegs);
									ntarget:setLine(line: ln);
									ntarget:setSemType(st: newResSem);
								});
							});
						});
					}
				], default: {});
				local String is callName: call:name;
				local Int is ovIdx: call:overloadIndex;
				local String is recvCls: ntarget:getSemType():toKey();
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
							newResSem: :cachedSemType(t: specRet:params:get(index: 0));
						}, {
							if({ specRet:name != '' }, {
								newResSem: :cachedSemType(t: specRet);
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
		res:setSemType(st: newResSem);
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
			times(count: m:params:length(), worker: local Function(Int is pi){
				nps:push(item: :transformParam(p: m:params:get(index: pi), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
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
			local [Member] is subMembers: [];
			times(count: sub:members:length(), worker: local Function(Int is smi){
				subMembers:push(item: :transformMember(m: sub:members:get(index: smi), subst: subst, tplParams: tplParams, selfTemplateName: selfTemplateName, selfSpecName: selfSpecName));
			});
			local ClassInfo is nsub: ClassInfo(name: sub:name, baseClass: sub:baseClass, members: subMembers);
			nsub:withBaseClasses(name: sub:name, baseClasses: sub:baseClasses, members: subMembers);
			nsub:setLine(line: sub:line);
			nsub:setSourceFile(file: sub:sourceFile);
			nsub:setTypeParams(params: []);
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

	local Function of Boolean is strListHas([String] is xs, String is target){
		local Int is idx: 0;
		while({ idx < xs:length() }, {
			if({ xs:get(index: idx) == target }, { return true; });
			idx++;
		});
		return false;
	}

	local Function is collectUnboundTypeIdents(Type is t, ClassInfo is cls, Array of String is out){
		if({ t:name != '' && t:name != ':field' && !:seenClassNames:has(key: t:name) && !:strListHas(xs: cls:typeParams, target: t:name) && out:indexOf(search: t:name, default: -1) < 0 }, {
			out:add(item: t:name);
		});
		times(count: t:params:length(), worker: local Function(Int is i){
			:collectUnboundTypeIdents(t: t:params:get(index: i), cls: cls, out: out);
		});
	}

	local Function of String is detectMethodTypeParam(Member is m, ClassInfo is cls){
		local Map of String to Int is paramCounts: Map:init();
		times(count: m:params:length(), worker: local Function(Int is pi){
			local Parameter is p: m:params:get(index: pi);
			local Array of String is idents: Array();
			:collectUnboundTypeIdents(t: p:paramType, cls: cls, out: idents);
			times(count: idents:length(), worker: local Function(Int is ii){
				local String is id: idents:get(index: ii, default: '');
				paramCounts:set(key: id, value: paramCounts:get(key: id, default: 0) + 1);
			});
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

	Function is specialize(ProgramNode is program, [ClassInfo] is allClasses){
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
				local [Member] is kept: [];
				times(count: cls:members:length(), worker: local Function(Int is mi){
					local Member is m: cls:members:get(index: mi);
					if({ m:kind == MemberKind:METHOD }, {
						local String is mtp: :detectMethodTypeParam(m: m, cls: cls);
						if({ mtp != '' }, {
							local String is gmKey: cls:name . ':' . m:name;
							:genericMethods:set(key: gmKey, value: m);
							:genericMethodTypeParam:set(key: gmKey, value: mtp);
							:genericMethodOwners:set(key: gmKey, value: cls);
						}, {
							kept:push(item: m);
						});
					}, {
						kept:push(item: m);
					});
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
				local [Member] is newMembers: [];
				times(count: cls:members:length(), worker: local Function(Int is mi){
					newMembers:push(item: :transformMember(m: cls:members:get(index: mi), subst: emptySubst, tplParams: emptyTpl, selfTemplateName: '', selfSpecName: ''));
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
				local ClassInfo is tpl: :templates:get(key: baseName, default: ClassInfo(name: '', baseClass: '', members: []));
				if({ tpl:name != '' }, {
					:curOwnerClassName: mangledName;
					local Map of String to Type is subst: Map:init();
					local Int is ti: 0;
					while({ ti < tpl:typeParams:length() && ti < tArgs:length() }, {
						subst:set(key: tpl:typeParams:get(index: ti), value: tArgs:get(index: ti));
						ti++;
					});
					local [Member] is specMembers: [];
					times(count: tpl:members:length(), worker: local Function(Int is mi){
						specMembers:push(item: :transformMember(m: tpl:members:get(index: mi), subst: subst, tplParams: emptyTpl, selfTemplateName: baseName, selfSpecName: mangledName));
					});
					local ClassInfo is specCls: ClassInfo(name: mangledName, baseClass: tpl:baseClass, members: specMembers);
					specCls:withBaseClasses(name: mangledName, baseClasses: tpl:baseClasses, members: specMembers);
					specCls:setOuter(name: tpl:outerName);
					specCls:setLine(line: tpl:line);
					specCls:setSourceFile(file: tpl:sourceFile);
					specCls:setTypeParams(params: []);
					:specBaseMap:set(key: mangledName, value: baseName);
					:specClassMap:set(key: mangledName, value: specCls);
					:specClassArgsMap:set(key: mangledName, value: tArgs);
					allClasses:push(item: specCls);
					program:classes:push(item: specCls);
					# Nested members of the spec class (enum variants, inner
					# classes) must be visible to emission: the IrBuilder
					# collected the program's own nested classes BEFORE the
					# specializer ran, so flatten the spec clones here —
					# mirroring the Loader's flattening of declared nesting.
					local [ClassInfo] is nestedQueue: [];
					times(count: specCls:members:length(), worker: local Function(Int is nqi){
						local Member is qm: specCls:members:get(index: nqi);
						if({ qm:kind == MemberKind:CLASS }, {
							nestedQueue:push(item: qm:nestedClass);
						});
					});
					while({ nestedQueue:length() > 0 }, {
						local ClassInfo is nq: nestedQueue:pop();
						allClasses:push(item: nq);
						program:classes:push(item: nq);
						times(count: nq:members:length(), worker: local Function(Int is dmi){
							local Member is dm: nq:members:get(index: dmi);
							if({ dm:kind == MemberKind:CLASS }, {
								nestedQueue:push(item: dm:nestedClass);
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
				local ClassInfo is ownerCls: ClassInfo(name: '', baseClass: '', members: []);
				if({ :genericMethods:has(key: gmKey) }, {
					ownerCls: :genericMethodOwners:get(key: gmKey, default: ownerCls);
				}, {
					if({ :specBaseMap:has(key: mOwner) }, {
						local String is bOwner: :specBaseMap:get(key: mOwner, default: '');
						gmKey: bOwner . ':' . mName;
						ownerCls: :specClassMap:get(key: mOwner, default: ownerCls);
						selfTplName: bOwner;
						selfSpName: mOwner;
						local ClassInfo is bTpl: :templates:get(key: bOwner, default: ClassInfo(name: '', baseClass: '', members: []));
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
					ownerCls:members:push(item: specM);
				});
				mwi++;
			});
		});
		:curOwnerClassName: '';
	}
}
