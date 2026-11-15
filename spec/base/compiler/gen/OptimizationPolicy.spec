#! Package base:compiler:gen
#! Structural, AST-based optimization predicates for the C11 code generator.
##
## Every optimization here must be purely structural (derived from AST shape
## and resolved types, never from hardcoded class or method names) and
## read-only so parallel code generation remains deterministic and race-free.

Class is OptimizationPolicy{
	namespace: ['base', 'compiler', 'gen'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## True when [typeName] is a stack-only scalar primitive (or Void) that
	## never allocates into or claims from the thread-local ARC claim pool.
	## Empty/unresolved type names return false (conservative).
	Function of Boolean is isPrimitiveScalarType(String is typeName){
		return typeName == 'Int' || typeName == 'Float' || typeName == 'Boolean' || typeName == 'Byte' || typeName == 'Void';
	}

	## True when any parameter in [params] has a non-primitive type.
	Function of Boolean is paramsNeedPoolFrame(Array of Parameter is params){
		local Boolean is needed: false;
		params:each(action: local Function(Parameter is p){
			if({ !needed && !self:isPrimitiveScalarType(typeName: p:paramType:name) }, {
				needed: true;
			});
		});
		return needed;
	}

	## True when [m] (method) requires a SPEC_POOL_AUTO claim-pool frame.
	## Pure-primitive methods with no managed locals, calls, or allocations
	## do not touch the claim pool and can safely omit SPEC_POOL_AUTO.
	Function of Boolean is methodNeedsPoolFrame(Member is m){
		if({ self:paramsNeedPoolFrame(params: m:params) }, {
			return true;
		});
		return self:stmtsNeedPoolFrame(stmts: m:body);
	}

	## True when any statement in [stmts] may allocate or claim into the
	## current scope's ARC claim pool.
	Function of Boolean is stmtsNeedPoolFrame(Array of Statement is stmts){
		local Boolean is needed: false;
		stmts:each(action: local Function(Statement is s){
			if({ !needed && self:stmtNeedsPoolFrame(stmt: s) }, {
				needed: true;
			});
		});
		return needed;
	}

	## True when [stmt] may allocate or claim into the current scope's ARC
	## claim pool.
	Function of Boolean is stmtNeedsPoolFrame(Statement is stmt){
		return match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				if({ !self:isPrimitiveScalarType(typeName: varType:name) }, {
					return true;
				});
				if({ hasInit }, {
					return self:exprNeedsPoolFrame(expr: initExpr);
				});
				return false;
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				return self:exprNeedsPoolFrame(expr: assignTarget) || self:exprNeedsPoolFrame(expr: assignValue);
			},
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ hasReturnExpr }, {
					return self:exprNeedsPoolFrame(expr: returnExpr);
				});
				return false;
			},
			Statement:Expr: local Function(Expression is exprStmt){
				return self:exprNeedsPoolFrame(expr: exprStmt);
			},
			else: { true }
		]);
	}

	## True when [call] is a control-flow call whose AnonFn arguments are
	## inlined into the enclosing C scope rather than heap-allocated.
	Function of Boolean is isInlinedControlFlowCall(CallData is call){
		local String is name: call:name;
		return name == 'if' || name == 'match' || name == 'while' || name == 'until' || name == 'repeat';
	}

	## True when [expr] may allocate or claim into the current scope's ARC
	## claim pool.
	Function of Boolean is exprNeedsPoolFrame(Expression is expr){
		return match(on: expr, when: [
			Expression:NumberLit: local Function(Int is value, String is text){ return false; },
			Expression:FloatLit: local Function(String is text){ return false; },
			Expression:BoolLit: local Function(Boolean is value){ return false; },
			Expression:Ident: local Function(String is name){ return false; },
			Expression:Path: local Function(Array of String is segments){ return false; },
			Expression:Unary: local Function(String is op, Expression is operand){
				return self:exprNeedsPoolFrame(expr: operand);
			},
			Expression:Binary: local Function(String is op, Expression is left, Expression is right){
				if({ !self:isPrimitiveScalarType(typeName: expr:resolvedType) }, {
					return true;
				});
				return self:exprNeedsPoolFrame(expr: left) || self:exprNeedsPoolFrame(expr: right);
			},
			Expression:Cast: local Function(Expression is inner, String is target, Array of Expression is args){
				if({ !self:isPrimitiveScalarType(typeName: target) }, {
					return true;
				});
				if({ self:exprNeedsPoolFrame(expr: inner) }, {
					return true;
				});
				local Boolean is needed: false;
				args:each(action: local Function(Expression is a){
					if({ !needed && self:exprNeedsPoolFrame(expr: a) }, {
						needed: true;
					});
				});
				return needed;
			},
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				return self:exprNeedsPoolFrame(expr: target);
			},
			Expression:Call: local Function(CallData is call){
				if({ !self:isPrimitiveScalarType(typeName: expr:resolvedType) }, {
					return true;
				});
				local Boolean is targetIsStaticPath: match(on: call:target, when: [
					Expression:Path: local Function(Array of String is segments){ return true; },
					Expression:Call: local Function(CallData is qInner){
						if({ qInner:args:length() != 0 }, {
							return false;
						});
						return match(on: qInner:target, when: [
							Expression:Path: local Function(Array of String is segments){ return true; },
							else: { false }
						]);
					},
					else: { false }
				]);
				if({ !targetIsStaticPath && self:exprNeedsPoolFrame(expr: call:target) }, {
					return true;
				});
				local Boolean is inlinedCf: self:isInlinedControlFlowCall(call: call);
				local Boolean is needed: false;
				call:args:each(action: local Function(NamedArg is arg){
					if({ !needed }, {
						local Expression is val: arg:value;
						if({ inlinedCf }, {
							match(on: val, when: [
								Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
									if({ self:paramsNeedPoolFrame(params: params) || self:stmtsNeedPoolFrame(stmts: body) }, {
										needed: true;
									});
								},
								else: {
									if({ self:exprNeedsPoolFrame(expr: val) }, {
										needed: true;
									});
								}
							]);
						}, {
							if({ self:exprNeedsPoolFrame(expr: val) }, {
								needed: true;
							});
						});
					});
				});
				return needed;
			},
			else: { true }
		]);
	}

	## True when [expr] is a side-effect-free leaf expression (literal,
	## identifier, or namespace path) that can be safely dropped or reordered.
	Function of Boolean is isPureArgExpr(Expression is expr){
		return match(on: expr, when: [
			Expression:NumberLit: local Function(Int is value, String is text){ return true; },
			Expression:FloatLit: local Function(String is text){ return true; },
			Expression:BoolLit: local Function(Boolean is value){ return true; },
			Expression:StringLit: local Function(String is value){ return true; },
			Expression:Ident: local Function(String is name){ return true; },
			Expression:Path: local Function(Array of String is segments){ return true; },
			else: { false }
		]);
	}

	## True when [expr] is a literal constant.
	Function of Boolean is isLiteralExpr(Expression is expr){
		return match(on: expr, when: [
			Expression:NumberLit: local Function(Int is value, String is text){ return true; },
			Expression:FloatLit: local Function(String is text){ return true; },
			Expression:BoolLit: local Function(Boolean is value){ return true; },
			Expression:StringLit: local Function(String is value){ return true; },
			else: { false }
		]);
	}

	## True when [expr] is a static class/namespace target (Path, known class Ident,
	## or qualified Class reference parsed as a zero-arg Call on a Path).
	Function of Boolean is isStaticNamespaceTarget(Expression is expr, Map of String to String is allClassNames, Map of String to String is paramSet){
		return match(on: expr, when: [
			Expression:Path: local Function(Array of String is segments){
				if({ segments:length() < 2 }, {
					return false;
				});
				local String is firstSeg: segments:get(index: 0);
				if({ firstSeg == 'self' || paramSet:has(key: firstSeg) }, {
					return false;
				});
				local String is lastSeg: segments:get(index: segments:length() - 1);
				return allClassNames:has(key: lastSeg);
			},
			Expression:Ident: local Function(String is name){
				return name != 'self' && !paramSet:has(key: name) && allClassNames:has(key: name);
			},
			Expression:Call: local Function(CallData is qInner){
				if({ qInner:args:length() != 0 }, {
					return false;
				});
				return match(on: qInner:target, when: [
					Expression:Path: local Function(Array of String is segments){
						if({ segments:length() < 1 }, {
							return false;
						});
						local String is firstSeg: segments:get(index: 0);
						if({ firstSeg == 'self' || paramSet:has(key: firstSeg) }, {
							return false;
						});
						return allClassNames:has(key: qInner:name);
					},
					else: { false }
				]);
			},
			else: { false }
		]);
	}

	## Returns the Spec return type name of a method's [Type] descriptor
	## (unwrapping `Function of R` -> `R`, and bare `Function` -> `'Void'`).
	Function of String is methodReturnTypeName(Type is t){
		if({ t:name == 'Function' }, {
			if({ t:params:length() > 0 }, {
				local Type is ret: t:params:get(index: 0);
				if({ ret:name == 'Function' }, {
					return 'Function';
				});
				return ret:name;
			});
			return 'Void';
		});
		return t:name;
	}

	## Extracts the single forwarded Call expression from [m] if [m] is a
	## structural forwarding wrapper, or Expression:Unknown otherwise.
	Function of Expression is forwardingBodyCall(Member is m, Map of String to String is allClassNames){
		if({ m:kind != MemberKind:METHOD || m:hasModifier(kw: Keyword:HELD) || m:name == 'init' }, {
			return Expression:Unknown;
		});
		local String is retTypeName: self:methodReturnTypeName(t: m:memberType);
		if({ !self:isPrimitiveScalarType(typeName: retTypeName) }, {
			return Expression:Unknown;
		});
		if({ m:body:length() != 1 }, {
			return Expression:Unknown;
		});
		local Statement is firstStmt: m:body:get(index: 0);
		local Expression is bodyExpr: match(on: firstStmt, when: [
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ hasReturnExpr }, {
					return returnExpr;
				});
				return Expression:Unknown;
			},
			Statement:Expr: local Function(Expression is exprStmt){
				if({ retTypeName == 'Void' }, {
					return exprStmt;
				});
				return Expression:Unknown;
			},
			else: { Expression:Unknown }
		]);
		local Boolean is okCall: match(on: bodyExpr, when: [
			Expression:Call: local Function(CallData is innerCall){
				if({ self:isInlinedControlFlowCall(call: innerCall) || innerCall:name == 'init' }, {
					return false;
				});
				local Map of String to String is paramSet: Map:init();
				m:params:each(action: local Function(Parameter is p){
					paramSet:set(key: p:name, value: '1');
				});
				if({ !self:isStaticNamespaceTarget(expr: innerCall:target, allClassNames: allClassNames, paramSet: paramSet) }, {
					return false;
				});
				local Map of String to String is seenParams: Map:init();
				local Boolean is argsOk: true;
				innerCall:args:each(action: local Function(NamedArg is ia){
					if({ argsOk }, {
						local Expression is val: ia:value;
						match(on: val, when: [
							Expression:Ident: local Function(String is idName){
								if({ !paramSet:has(key: idName) || seenParams:has(key: idName) }, {
									argsOk: false;
								}, {
									seenParams:set(key: idName, value: '1');
								});
							},
							else: {
								if({ !self:isLiteralExpr(expr: val) }, {
									argsOk: false;
								});
							}
						]);
					});
				});
				return argsOk;
			},
			else: { false }
		]);
		if({ okCall }, {
			return bodyExpr;
		});
		return Expression:Unknown;
	}

	## If [bodyExpr] is a pre-extracted forwarding-wrapper Call for [m] and
	## [outerCall] can be safely unwrapped into [bodyExpr] with caller arguments
	## substituted, returns the unwrapped Call expression; otherwise returns Expression:Unknown.
	Function of Expression is tryUnwrapForwardingCall(Member is m, Expression is bodyExpr, CallData is outerCall, String is resolvedType){
		local Boolean is hasBody: match(on: bodyExpr, when: [
			Expression:Call: local Function(CallData is c){ return true; },
			else: { false }
		]);
		if({ !hasBody }, {
			return Expression:Unknown;
		});
		local CallData is innerCall: match(on: bodyExpr, when: [
			Expression:Call: local Function(CallData is c){ return c; },
			else: { CallData:init(target: Expression:Unknown, name: '', args: []) }
		]);
		# Map each parameter of [m] to the caller's argument expression.
		local Map of String to Expression is paramMap: Map:init();
		local Int is posIdx: 0;
		local Boolean is argsOk: true;
		m:params:each(action: local Function(Parameter is p){
			if({ argsOk }, {
				local Boolean is got: false;
				if({ posIdx < outerCall:args:length() }, {
					local NamedArg is posNa: outerCall:args:get(index: posIdx);
					if({ posNa:name == '' }, {
						paramMap:set(key: p:name, value: posNa:value);
						posIdx: posIdx + 1;
						got: true;
					});
				});
				if({ !got }, {
					outerCall:args:each(action: local Function(NamedArg is oa){
						if({ !got && oa:name == p:name }, {
							paramMap:set(key: p:name, value: oa:value);
							got: true;
						});
					});
				});
				if({ !got && p:hasDefault }, {
					paramMap:set(key: p:name, value: p:defaultExpr);
					got: true;
				});
				if({ !got }, {
					argsOk: false;
				});
			});
		});
		if({ !argsOk }, {
			return Expression:Unknown;
		});
		# Ensure any parameter of [m] not forwarded to [innerCall] has a pure
		# caller argument so no side effect is dropped.
		local Map of String to String is usedSet: Map:init();
		local Array of NamedArg is newArgs: [];
		innerCall:args:each(action: local Function(NamedArg is ia){
			local Expression is val: ia:value;
			match(on: val, when: [
				Expression:Ident: local Function(String is idName){
					usedSet:set(key: idName, value: '1');
					local Expression is mapped: paramMap:get(key: idName, default: Expression:Unknown);
					newArgs:add(item: NamedArg:init(name: ia:name, value: mapped));
				},
				else: {
					newArgs:add(item: ia);
				}
			]);
		});
		m:params:each(action: local Function(Parameter is p){
			if({ argsOk && !usedSet:has(key: p:name) }, {
				local Expression is unusedArg: paramMap:get(key: p:name, default: Expression:Unknown);
				if({ !self:isPureArgExpr(expr: unusedArg) }, {
					argsOk: false;
				});
			});
		});
		if({ !argsOk }, {
			return Expression:Unknown;
		});
		local CallData is newCd: CallData:init(target: innerCall:target, name: innerCall:name, args: newArgs);
		newCd:bareProvider: innerCall:bareProvider;
		newCd:overloadIndex: innerCall:overloadIndex;
		local Expression is res: Expression:Call(call: newCd);
		res:setResolvedType(t: resolvedType);
		return res;
	}

	## True when [m] on [c] is a small, non-generic, pure-primitive leaf method
	## that can be safely emitted as `static inline` in C11.
	## Both DeclarationGenerator (prototype) and CodeGenerator (definition)
	## use this exact predicate so C linkage always matches.
	Function of Boolean is isStaticInlineLeaf(ClassInfo is c, Member is m){
		return noneOf(checks: [
			m:kind != MemberKind:METHOD,
			m:hasModifier(kw: Keyword:HELD),
			m:name == 'init',
			m:name == 'destroy',
			c:typeParams:length() > 0,
			m:body:length() == 0,
			m:body:length() > 12,
			!self:isPrimitiveScalarType(typeName: self:methodReturnTypeName(t: m:memberType)),
			self:methodNeedsPoolFrame(m: m)
		]);
	}

	## True when [expr] contains any non-call-target reference to [identName]
	## or any call to [forbidCallName].
	Function of Boolean is exprUsesIdentOutsideCallTarget(Expression is expr, String is identName, String is forbidCallName){
		return match(on: expr, when: [
			Expression:Ident: local Function of Boolean(String is name){
				return name == identName;
			},
			Expression:Unary: local Function of Boolean(String is op, Expression is operand){
				return self:exprUsesIdentOutsideCallTarget(expr: operand, identName: identName, forbidCallName: forbidCallName);
			},
			Expression:Binary: local Function of Boolean(String is op, Expression is left, Expression is right){
				return self:exprUsesIdentOutsideCallTarget(expr: left, identName: identName, forbidCallName: forbidCallName)
					|| self:exprUsesIdentOutsideCallTarget(expr: right, identName: identName, forbidCallName: forbidCallName);
			},
			Expression:Cast: local Function of Boolean(Expression is inner, String is target, Array of Expression is args){
				return self:exprUsesIdentOutsideCallTarget(expr: inner, identName: identName, forbidCallName: forbidCallName);
			},
			Expression:Index: local Function of Boolean(Expression is target, Expression is index){
				return self:exprUsesIdentOutsideCallTarget(expr: target, identName: identName, forbidCallName: forbidCallName)
					|| self:exprUsesIdentOutsideCallTarget(expr: index, identName: identName, forbidCallName: forbidCallName);
			},
			Expression:FieldAccess: local Function of Boolean(Expression is target, String is fieldName){
				return self:exprUsesIdentOutsideCallTarget(expr: target, identName: identName, forbidCallName: forbidCallName);
			},
			Expression:Call: local Function of Boolean(CallData is cd){
				if({ forbidCallName != '' && cd:name == forbidCallName }, {
					return true;
				});
				local Boolean is targetBad: false;
				local Boolean is targetIsThisFn: false;
				match(on: cd:target, when: [
					Expression:Ident: local Function(String is n){
						if({ n == identName }, {
							targetIsThisFn: true;
						});
					}
				], default: {});
				if({ !targetIsThisFn }, {
					if({ self:exprUsesIdentOutsideCallTarget(expr: cd:target, identName: identName, forbidCallName: forbidCallName) }, {
						targetBad: true;
					});
				});
				if({ targetBad }, {
					return true;
				});
				local Boolean is argBad: false;
				cd:args:each(action: local Function(NamedArg is a){
					if({ !argBad && self:exprUsesIdentOutsideCallTarget(expr: a:value, identName: identName, forbidCallName: forbidCallName) }, {
						argBad: true;
					});
				});
				return argBad;
			},
			Expression:AnonFn: local Function of Boolean(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				return self:stmtsUseIdentOutsideCallTarget(stmts: bd, identName: identName, forbidCallName: forbidCallName);
			},
			Expression:ArrayLit: local Function of Boolean(Array of Expression is items){
				local Boolean is bad: false;
				items:each(action: local Function(Expression is it){
					if({ !bad && self:exprUsesIdentOutsideCallTarget(expr: it, identName: identName, forbidCallName: forbidCallName) }, {
						bad: true;
					});
				});
				return bad;
			},
			Expression:MapLit: local Function of Boolean(Array of Expression is ks, Array of Expression is vs){
				local Boolean is bad: false;
				ks:each(action: local Function(Expression is k){
					if({ !bad && self:exprUsesIdentOutsideCallTarget(expr: k, identName: identName, forbidCallName: forbidCallName) }, {
						bad: true;
					});
				});
				vs:each(action: local Function(Expression is v){
					if({ !bad && self:exprUsesIdentOutsideCallTarget(expr: v, identName: identName, forbidCallName: forbidCallName) }, {
						bad: true;
					});
				});
				return bad;
			},
			else: { false }
		]);
	}

	Function of Boolean is stmtsUseIdentOutsideCallTarget(Array of Statement is stmts, String is identName, String is forbidCallName){
		local Boolean is bad: false;
		stmts:each(action: local Function(Statement is s){
			if({ !bad }, {
				match(on: s, when: [
					Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
						if({ hasInit && self:exprUsesIdentOutsideCallTarget(expr: initExpr, identName: identName, forbidCallName: forbidCallName) }, {
							bad: true;
						});
					},
					Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
						if({ self:exprUsesIdentOutsideCallTarget(expr: assignTarget, identName: identName, forbidCallName: forbidCallName)
							|| self:exprUsesIdentOutsideCallTarget(expr: assignValue, identName: identName, forbidCallName: forbidCallName) }, {
							bad: true;
						});
					},
					Statement:Expr: local Function(Expression is exprStmt){
						if({ self:exprUsesIdentOutsideCallTarget(expr: exprStmt, identName: identName, forbidCallName: forbidCallName) }, {
							bad: true;
						});
					},
					Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
						if({ hasReturnExpr && self:exprUsesIdentOutsideCallTarget(expr: returnExpr, identName: identName, forbidCallName: forbidCallName) }, {
							bad: true;
						});
					},
					else: { bad: true; }
				]);
			});
		});
		return bad;
	}

	## True when [m] on [c] called with [call] can be structurally inlined
	## with its literal AnonFn arguments expanded directly at the call site.
	Function of Boolean is isInlineableAnonMethod(ClassInfo is c, Member is m, CallData is call){
		if({ m:kind != MemberKind:METHOD || m:hasModifier(kw: Keyword:HELD) || m:name == 'init' || m:name == 'destroy' }, {
			return false;
		});
		if({ c:typeParams:length() > 0 || m:body:length() == 0 || m:body:length() > 10 }, {
			return false;
		});
		if({ self:stmtsUseIdentOutsideCallTarget(stmts: m:body, identName: 'self', forbidCallName: m:name) }, {
			return false;
		});

		local Int is fnParamCount: 0;
		local Boolean is paramsOk: true;
		local Array of String is nonFnNames: [];
		local Array of Expression is anonArgs: [];

		local Int is pi: 0;
		m:params:each(action: local Function(Parameter is p){
			if({ paramsOk }, {
				local String is pt: p:paramType:name;
				if({ pt == 'Function' || pt:startsWith(prefix: 'Function:') }, {
					fnParamCount: fnParamCount + 1;
					local Expression is argVal: Expression:Unknown;
					local Boolean is foundArg: false;
					call:args:each(action: local Function(NamedArg is a){
						if({ !foundArg && a:name == p:name && p:name != '' }, {
							argVal: a:value;
							foundArg: true;
						});
					});
					if({ !foundArg && pi < call:args:length() }, {
						local NamedArg is posArg: call:args:get(index: pi);
						if({ posArg:name == '' || posArg:name == p:name }, {
							argVal: posArg:value;
							foundArg: true;
						});
					});
					local Boolean is isAnon: false;
					if({ foundArg }, {
						match(on: argVal, when: [
							Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
								isAnon: true;
								anonArgs:add(item: argVal);
							}
						], default: {});
					});
					if({ !isAnon }, {
						paramsOk: false;
					});
					if({ self:stmtsUseIdentOutsideCallTarget(stmts: m:body, identName: p:name, forbidCallName: '') }, {
						paramsOk: false;
					});
				}, {
					nonFnNames:add(item: p:name);
				});
			});
			pi: pi + 1;
		});

		if({ !paramsOk || fnParamCount == 0 }, {
			return false;
		});

		# Collect local VarDecl names inside m:body; ensure none shadow names in anonArgs.
		m:body:each(action: local Function(Statement is s){
			match(on: s, when: [
				Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
					nonFnNames:add(item: varName);
				}
			], default: {});
		});

		local Boolean is shadowRisk: false;
		anonArgs:each(action: local Function(Expression is anon){
			if({ !shadowRisk }, {
				match(on: anon, when: [
					Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
						nonFnNames:each(action: local Function(String is localNm){
							if({ !shadowRisk && self:stmtsUseIdentOutsideCallTarget(stmts: bd, identName: localNm, forbidCallName: localNm) }, {
								shadowRisk: true;
							});
						});
					}
				], default: {});
			});
		});
		return !shadowRisk;
	}

}
