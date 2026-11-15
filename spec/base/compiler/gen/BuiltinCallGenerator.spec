#! Package base:compiler:gen
#! Translates standard-library and runtime builtin method calls into C11
#! runtime functions.
##
## The interception surface for the runtime-managed packages: this class is the
## interception surface, ported. Every branch here dies when the floor
## classes are reimplemented in Spec over the sysinternal primitives. The
## sysinternal namespace-binding block at the top is the replacement
## mechanism, already live.

Class is BuiltinCallGenerator{
	namespace: ['base', 'compiler', 'gen'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', WellKnown],
		['base', 'compiler', 'gen', CBackendUtils],
		['base', 'compiler', 'gen', EmissionPolicy],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'compiler', 'gen', CodeGenerator],
		['base', 'sys', as Conditional()]
	];

	local CBackendUtils is utils: CBackendUtils:init();
	local EmissionPolicy is policy: EmissionPolicy:init();

	## Binds a sysinternal floor call to its C function per the naming
	## convention: spec_ + snake_case(method). Arguments match the declared
	## parameters positionally first, then by name, with declaration-side
	## defaults filling the rest. Returns '' when the method is not a floor
	## declaration, letting the caller fall through.
	Function of String is bindFloorCall(String is clsName, Expression is expr, CodeGenerator is cg){
		local CallData is cd: match(on: expr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: { CallData:init(target: Expression:Unknown, name: '', args: []) }
		]);
		local ClassInfo is fCls: cg:findClass(name: clsName);
		# clsName may be qualified ('base:sysinternal:Buf'); the lookup
		# already resolved it — only absence (empty name) is a miss.
		if({ fCls:name == '' }, {
			return '';
		});
		local Member is foundM;
		local Boolean is hasM: false;
		fCls:members:each(action: local Function(Member is m){
			if({ !hasM && m:kind == MemberKind:METHOD && m:name == cd:name }, {
				hasM: true;
				foundM: m;
			});
		});
		if({ !hasM }, {
			return '';
		});
		local Array of String is argList: [];
		local Boolean is argsOk: true;
		local Int is posIdx: 0;
		foundM:params:each(action: local Function(Parameter is p){
			if({ argsOk }, {
				local Boolean is got: false;
				local Expression is posArg: expr:argValue(index: posIdx);
				if({ posIdx < expr:argCount() && expr:argName(index: posIdx) == '' }, {
					argList:add(item: cg:generateExpression(expr: posArg));
					posIdx: posIdx + 1;
					got: true;
				});
				if({ !got }, {
					cd:args:each(action: local Function(NamedArg is a){
						if({ !got && a:name == p:name }, {
							got: true;
							argList:add(item: cg:generateExpression(expr: a:value));
						});
					});
				});
				if({ !got && p:hasDefault }, {
					got: true;
					argList:add(item: cg:generateExpression(expr: p:defaultExpr));
				});
				if({ !got }, {
					argsOk: false;
				});
			});
		});
		if({ !argsOk }, {
			return '';
		});
		local String is argCs: '';
		argList:each(action: local Function(String is a){
			if({ argCs == '' }, {
				argCs: a;
			}, {
				argCs: argCs . ', ' . a;
			});
		});
		return 'spec_' . self:utils:snakeCase(name: cd:name) . '(' . argCs . ')';
	}

	## Safely extracts a call argument's value expression, avoiding the
	## call-result field-access limitation.
	##
	## @param expr: The CALL expression.
	## @param index: The argument index.
	## @return: The value expression.
	Function of Expression is argValue(Expression is expr, Int is index){
		return expr:argValue(index: index);
	}

	## Extracts CallData from a Call expression (or an empty dummy when not Call).
	Function of CallData is extractCall(Expression is expr){
		return match(on: expr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: { CallData:init(target: Expression:Unknown, name: '', args: []) }
		]);
	}

	## @param targetType: Inferred type of the target.
	## @param cg: The code generator.
	## @return: C call string, or '' when not builtin.
	Function of String is generateBuiltinCall(Expression is expr, String is targetC, String is targetType, CodeGenerator is cg){
		local CallData is cd: self:extractCall(expr: expr);
		# Reflection:class()/method() — compile-time source identity,
		# injected at the call site. Matches the bare usage form AND the
		# qualified floor chain (the base:sys wrapper delegates by chain;
		# user code hits the bare interception first).
		local Boolean is isReflTarget: targetC == 'Reflection';
		if({ !isReflTarget }, {
			match(on: cd:target, when: [
				Expression:Path: local Function(Array of String is segments){
					local String is rJoined: '';
					segments:each(action: local Function(String is seg){
						if({ rJoined == '' }, {
							rJoined: seg;
						}, {
							rJoined: rJoined . ':' . seg;
						});
					});
					if({ rJoined:endsWith(suffix: ':sysinternal:Reflection') }, {
						isReflTarget: true;
					});
				}
			]);
		});
		if({ isReflTarget && cd:name == 'class' && expr:argCount() == 0 }, {
			return 'spec_string_intern("' . cg:currentClassName . '")';
		});
		if({ isReflTarget && cd:name == 'method' && expr:argCount() == 0 }, {
			return 'spec_string_intern("' . cg:currentMethodName . '")';
		});

		# Namespace-driven sysinternal floor binding: a call on a class whose
		# namespace ends with `sysinternal` compiles to spec_<snake(method)>.
		local String is floorCls: '';
		local ClassInfo is tc: cg:findClass(name: targetC);
		if({ targetC != '' && tc:name == targetC && cg:isSysinternalClass(name: targetC) }, {
			floorCls: targetC;
		}, {
			local String is qCls: '';
			match(on: cd:target, when: [
				Expression:Path: local Function(Array of String is qSegs){
					qCls: qSegs:get(index: qSegs:length() - 1);
					# Qualified chains ('base:sysinternal:Buf') resolve by full
					# namespace path so the floor never collides with its
					# same-name base:sys wrapper.
					local String is qJoined: '';
					qSegs:each(action: local Function(String is seg){
						if({ qJoined == '' }, {
							qJoined: seg;
						}, {
							qJoined: qJoined . ':' . seg;
						});
					});
					if({ qJoined:contains(needle: ':sysinternal:') }, {
						qCls: qJoined;
					});
				},
				Expression:Call: local Function(CallData is qInner){
					match(on: qInner:target, when: [
						Expression:Path: local Function(Array of String is segments){
							qCls: qInner:name;
						}
					]);
				}
			]);
			local ClassInfo is qc: cg:findClass(name: qCls);
			if({ qCls != '' && qc:name != '' && (qc:name == qCls || (qc:namespaceJoined() . ':' . qc:name) == qCls) && cg:isSysinternalClass(name: qCls) }, {
				floorCls: qCls;
			});
		});
		if({ floorCls != '' }, {
			local String is bound: self:bindFloorCall(clsName: floorCls, expr: expr, cg: cg);
			if({ bound != '' }, {
				return bound;
			});
		});

		# String:newline() — the newline constant.
		if({ targetC == 'String' && cd:name == 'newline' && expr:argCount() == 0 }, {
			return 'spec_string_intern("\\n")';
		});

		# Type name introspection on class instances.
		if({ cd:name == 'typeName' && targetType != '' && !self:policy:isTransparent(c: cg:findClass(name: targetType)) }, {
			return 'spec_type_name(' . targetC . ')';
		});

		# Int toBase conversion.
		if({ cd:name == 'toBase' && (targetType == Primitive:INT:value()) }, {
			local String is baseC: '10';
			local String is digitsC: '0';
			cd:args:each(action: local Function(NamedArg is arg){
				if({ arg:name == 'base' }, {
					baseC: cg:generateExpression(expr: arg:value);
				});
				if({ arg:name == 'digits' }, {
					digitsC: cg:generateExpression(expr: arg:value);
				});
			});
			return 'spec_int_to_base(' . targetC . ', ' . baseC . ', ' . digitsC . ')';
		});

		# Parallel fan-out execution and synchronization.
		if({ targetC == 'Parallel' && cd:name == 'sync' && expr:argCount() >= 1 }, {
			local String is actionC: 'NULL';
			cd:args:each(action: local Function(NamedArg is arg){
				if({ arg:name == 'action' }, {
					actionC: cg:generateExpression(expr: arg:value);
				});
			});
			return 'spec_parallel_sync((void*)(' . actionC . '))';
		});
		if({ targetC == 'Parallel' && cd:name == 'syncWith' && expr:argCount() >= 2 }, {
			local String is lockC: '0';
			local String is actionC: 'NULL';
			cd:args:each(action: local Function(NamedArg is arg){
				if({ arg:name == 'lock' }, {
					lockC: cg:generateExpression(expr: arg:value);
				});
				if({ arg:name == 'action' }, {
					actionC: cg:generateExpression(expr: arg:value);
				});
			});
			return 'spec_parallel_sync_with(' . lockC . ', (void*)(' . actionC . '))';
		});
		if({ targetC == 'Parallel' && cd:name == 'run' && expr:argCount() >= 3 }, {
			local String is threadsC: '1';
			local String is iterC: '0';
			local String is workerC: 'NULL';
			cd:args:each(action: local Function(NamedArg is arg){
				if({ arg:name == 'threads' }, {
					threadsC: cg:generateExpression(expr: arg:value);
				});
				if({ arg:name == 'iterations' }, {
					iterC: cg:generateExpression(expr: arg:value);
				});
				if({ arg:name == 'worker' }, {
					workerC: cg:generateExpression(expr: arg:value);
				});
			});
			return 'spec_parallel_run(' . threadsC . ', ' . iterC . ', (void*)(' . workerC . '))';
		});

		# String:fromCharCode.
		if({ targetC == 'String' && cd:name == 'fromCharCode' && expr:argCount() > 0 }, {
			local Expression is codeArg: self:argValue(expr: expr, index: 0);
			local String is codeC: cg:generateExpression(expr: codeArg);
			return 'spec_string_from_char_code(' . codeC . ')';
		});

		# The loop runners — While (the legacy spelling, bridged) and
		# Loops (§the control-flow provider).
		if({ (targetC == 'Loops' || cd:bareProvider == 'Loops') && cd:name == 'run' && expr:argCount() > 0 }, {
			local Expression is loopVal: self:argValue(expr: expr, index: 0);
			local String is loopC: cg:generateExpressionInner(expr: loopVal);
			local String is loopClass: cg:inferTargetType(expr: loopVal);
			local String is freeLoopC: '';
			match(on: loopVal, when: [
				Expression:Call: local Function(CallData is lvCall){
					if({ loopClass == '' }, {
						loopClass: cg:generateExpression(expr: lvCall:target);
					});
					if({ lvCall:name == 'init' }, {
						freeLoopC: ' spec_release(_lp);';
					});
				}
			]);
			# the loop-class symbol qualifies for
			# nested classes — resolve the class and derive the qualified base.
			local ClassInfo is loopCls: cg:findClass(name: loopClass);
			if({ loopCls:name != '' }, {
				loopClass: cg:utils:cIdent(name: loopCls:qualifiedName());
			});
			local String is ctrlC: 'NULL';
			if({ expr:argCount() > 1 }, {
				local Expression is ctrlArg: self:argValue(expr: expr, index: 1);
				ctrlC: cg:generateExpression(expr: ctrlArg);
			});
			# The protocol inline needs the loop's static class for the
			# direct evaluate/iteration calls; an unresolved receiver (a
			# Loop held as Any) falls through to the runtime run body.
			if({ loopClass != '' }, {
				return '({ void* _lp = (void*)(' . loopC . '); SpecLoopControl* _ctrl = (SpecLoopControl*)(' . ctrlC . '); while (' . loopClass . '_evaluate((void*)_lp)) { if (!' . loopClass . '_iteration((void*)_lp, _ctrl) || (_ctrl && _ctrl->stopped)) break; } if (_ctrl && _ctrl->on_complete) { _ctrl->on_complete(_ctrl->callback, _ctrl); }' . freeLoopC . ' })';
			});
		});
		# Loops:repeat(count:, worker:) — the counting loop, inlined.
		if({ (targetC == 'Loops' || cd:bareProvider == 'Loops') && cd:name == 'repeat' && expr:argCount() == 2 }, {
			local Expression is repCountExpr;
			local Expression is repWorkerExpr;
			local Boolean is repHasCount: false;
			local Boolean is repHasWorker: false;
			cd:args:each(action: local Function(NamedArg is arg){
				if({ arg:name == 'count' }, {
					repCountExpr: arg:value;
					repHasCount: true;
				}, {
					if({ arg:name == 'worker' }, {
						repWorkerExpr: arg:value;
						repHasWorker: true;
					});
				});
			});
			if({ !repHasCount && expr:argCount() == 2 }, {
				repCountExpr: self:argValue(expr: expr, index: 0);
				repHasCount: true;
			});
			if({ !repHasWorker && expr:argCount() == 2 }, {
				repWorkerExpr: self:argValue(expr: expr, index: 1);
				repHasWorker: true;
			});
			if({ repHasCount && repHasWorker }, {
				local Boolean is workerIsAnon: match(on: repWorkerExpr, when: [
					Expression:AnonFn: local Function of Boolean(Type is returnType, Array of Parameter is params, Array of Statement is body){ return true; },
					else: { false }
				]);
				if({ workerIsAnon }, {
					return cg:generateInlineRepeat(countExpr: repCountExpr, workerExpr: repWorkerExpr);
				});
			});
		});
		if({ (targetC == 'Loops' || cd:bareProvider == 'Loops') && (cd:name == 'while' || cd:name == 'condition' || cd:name == 'until' || cd:name == 'loop' || cd:name == 'init') }, {
			local Expression is varsExpr;
			local Expression is evalExpr;
			local Expression is iterExpr;
			local Boolean is hasVars: false;
			local Boolean is hasEval: false;
			local Boolean is hasIter: false;
			cd:args:each(action: local Function(NamedArg is arg){
				if({ arg:name == 'evaluate' }, {
					evalExpr: arg:value;
					hasEval: true;
				}, {
					if({ arg:name == 'iterate' || arg:name == 'iteration' }, {
						iterExpr: arg:value;
						hasIter: true;
					}, {
						if({ arg:name == 'vars' || arg:name == 'state' }, {
							varsExpr: arg:value;
							hasVars: true;
						});
					});
				});
			});
			if({ !hasEval }, {
				if({ expr:argCount() >= 3 }, {
					evalExpr: self:argValue(expr: expr, index: 1);
					hasEval: true;
				}, {
					if({ expr:argCount() >= 2 }, {
						evalExpr: self:argValue(expr: expr, index: 0);
						hasEval: true;
					});
				});
			});
			if({ !hasIter }, {
				if({ expr:argCount() >= 3 }, {
					iterExpr: self:argValue(expr: expr, index: 2);
					hasIter: true;
				}, {
					if({ expr:argCount() >= 2 }, {
						iterExpr: self:argValue(expr: expr, index: 1);
						hasIter: true;
					});
				});
			});
			if({ !hasVars && expr:argCount() >= 3 }, {
				varsExpr: self:argValue(expr: expr, index: 0);
				hasVars: true;
			});
			if({ hasEval && hasIter }, {
				local Boolean is evalIsAnon: match(on: evalExpr, when: [
					Expression:AnonFn: local Function of Boolean(Type is returnType, Array of Parameter is params, Array of Statement is body){ return true; },
					else: { false }
				]);
				local Boolean is iterIsAnon: match(on: iterExpr, when: [
					Expression:AnonFn: local Function of Boolean(Type is returnType, Array of Parameter is params, Array of Statement is body){ return true; },
					else: { false }
				]);
				if({ evalIsAnon && iterIsAnon }, {
					local Array of Parameter is loopVars: [];
					if({ hasVars }, {
						match(on: varsExpr, when: [
							Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
								if({ params:length() > 0 }, {
									loopVars: params;
								});
							}
						]);
					});
					# until is the do-while — the body runs once first.
					if({ cd:name == 'until' }, {
						return cg:generateInlineUntil(evalExpr: evalExpr, iterExpr: iterExpr);
					});
					return cg:generateInlineWhileLoop(loopVars: loopVars, evalExpr: evalExpr, iterExpr: iterExpr);
				});
			});
		});

		# LoopControl methods: transparent runtime-managed objects — the
		# constructor wires the optional completion callback directly.
		if({ targetC == 'LoopControl' && cd:name == 'init' }, {
			if({ expr:argCount() == 0 }, {
				return 'LoopControl_new()';
			});
			local NamedArg is cbArg: cd:args:get(index: 0);
			local Expression is cbVal: cbArg:value;
			local String is cbC: cg:generateExpression(expr: cbVal);
			local String is cbClass: cg:inferTargetType(expr: cbVal);
			if({ cbClass == '' }, {
				match(on: cbVal, when: [
					Expression:Call: local Function(CallData is cbCall){
						cbClass: cg:generateExpression(expr: cbCall:target);
					}
				]);
			});
			# the callback-class symbol qualifies
			# for nested classes.
			local ClassInfo is cbCls: cg:findClass(name: cbClass);
			if({ cbCls:name != '' }, {
				cbClass: cg:utils:cIdent(name: cbCls:qualifiedName());
			});
			return '({ SpecLoopControl* _c = LoopControl_new(); _c->callback = (void*)(' . cbC . '); _c->on_complete = (void (*)(void*, struct SpecLoopControl*))' . cbClass . '_onComplete; _c; })';
		});
		if({ cd:name == 'stop' && (targetC == 'LoopControl' || targetType == 'LoopControl') }, {
			return 'LoopControl_stop(' . targetC . ')';
		});
		# LoopControl:isStopped — the halt query the runtime run()
		# composes from (the compile-time inlines read the C struct
		# directly; the wrapper needs the public surface). Null-safe:
		# an omitted control drives without a halt query.
		if({ cd:name == 'isStopped' && (targetC == 'LoopControl' || targetType == 'LoopControl') }, {
			return '({ SpecLoopControl* _lc = (SpecLoopControl*)(' . targetC . '); _lc ? (bool)_lc->stopped : false; })';
		});
		# LoopControl:complete — fires the completion callback the
		# runtime run() owes after the loop ends (the inline protocol's
		# on_complete tail). No callback registered: nothing fires.
		if({ cd:name == 'complete' && (targetC == 'LoopControl' || targetType == 'LoopControl') }, {
			return '({ SpecLoopControl* _lc = (SpecLoopControl*)(' . targetC . '); if (_lc && _lc->on_complete) { _lc->on_complete(_lc->callback, _lc); } })';
		});

		# Math functions (libm / C-cast floor only).
		if({ targetC == 'Math' || targetType == 'Math' }, {
			local String is m: cd:name;
			local String is a0: '0.0';
			if({ expr:argCount() > 0 }, {
				a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
			});
			# Single-operand functions: the match yields the C call; the
			# empty else lets the two-operand section run.
			local String is oneC: match(on: m, when: [
				'sqrt': { 'spec_math_sqrt(' . a0 . ')' },
				'sin': { 'spec_math_sin(' . a0 . ')' },
				'cos': { 'spec_math_cos(' . a0 . ')' },
				'tan': { 'spec_math_tan(' . a0 . ')' },
				'log': { 'spec_math_log(' . a0 . ')' },
				'log2': { 'spec_math_log2(' . a0 . ')' },
				'fastRandom': { 'spec_fast_random()' },
				else: { '' }
			]);
			if({ oneC != '' }, {
				return oneC;
			});
			# Two-operand floor functions.
			local String is a1: '0.0';
			if({ expr:argCount() > 1 }, {
				a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
			});
			if({ m == 'pow' }, {
				return 'spec_math_pow(' . a0 . ', ' . a1 . ')';
			});
			if({ m == 'atan2' }, {
				return 'spec_math_atan2(' . a0 . ', ' . a1 . ')';
			});
			if({ m == 'toInt' }, {
				return '((long long)(' . a0 . '))';
			});
			if({ m == 'toFloat' }, {
				return '((double)(' . a0 . '))';
			});
		});

		# Array/List/Map method bindings (runtime-managed; spec_* calls).
		# Entry is by method name on any Array-typed target — no transparency
		# check: registered locals must bind without a registry lookup.
		local Boolean is isArr: targetC == 'Array' || targetType == 'Array' || targetType:startsWith(prefix: 'Array') ||
			targetType:startsWith(prefix: 'List') ||
			((targetType == '' || targetType == Primitive:ANY:value()) && (
				cd:name == 'get' || cd:name == 'add' || cd:name == 'set' || cd:name == 'pop' ||
				cd:name == 'removeAt' || cd:name == 'slice' || cd:name == 'clear' || cd:name == 'join' ||
				cd:name == 'each' || cd:name == 'filter' || cd:name == 'count' || cd:name == 'any' ||
				cd:name == 'map' || cd:name == 'fold' ||
				(cd:name == 'length' && targetType != 'String' && targetC != 'Map' && !targetType:startsWith(prefix: 'Map:'))
			));
		if({ isArr }, {
			local String is arrC: self:bindContainerCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			if({ arrC != '' }, {
				return arrC;
			});
		});

		# Map literal-constructor + concrete getters + inline each.
		if({ targetC == 'Map' || targetType == 'Map' || targetType:startsWith(prefix: 'Map:') }, {
			local String is mapC: self:bindMapCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			if({ mapC != '' }, {
				return mapC;
			});
		});

		# String instance methods: direct dispatch to compiled bodies.
		if({ targetType == 'String' }, {
			local String is ddC: self:bindStringDirect(expr: expr, targetC: targetC, cg: cg);
			if({ ddC != '' }, {
				return ddC;
			});
		});

		return '';
	}

	## The result cast for an Array element read (get/pop): value-typed
	## elements (Int/Boolean/Float) ride the pointer slot and must be
	## cast back out — List emission does the same via its resCast.
	## Class, ARC, and String elements flow as pointers and cast to
	## nothing, the implicit shape every existing read relies on.
	##
	## @param containerType: The Array's static type name.
	## @param cg: The code generator (element-type lookup).
	## @return: A C cast prefix ('' when none is needed).
	Function of String is arrayElemResCast(String is containerType, CodeGenerator is cg){
		local String is elem: cg:elemOfType(t: containerType);
		if({ elem == 'Int' || elem == 'Boolean' || elem == 'Float' }, {
			return '(long long)(intptr_t)';
		});
		return '';
	}

	## Binds Array/List element and query methods to their spec_* C
	## functions. Transitional: dies when containers are Spec classes.
	##
	## @param expr: CALL expression.
	## @param targetC: Target C.
	## @param targetType: Target type name.
	## @param cg: The code generator.
	## @return: C call, or ''.
	Function of String is bindContainerCall(Expression is expr, String is targetC, String is targetType, CodeGenerator is cg){
		local CallData is cd: self:extractCall(expr: expr);
		local String is m: cd:name;
		local String is a0: '';
		if({ expr:argCount() > 0 }, {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		});
		local String is a1: '';
		if({ expr:argCount() > 1 }, {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		});
		# Array methods (SpecArray*). Named-arg extraction.
		if({ targetType:startsWith(prefix: 'Array') }, {
			if({ m == 'get' }, {
				local String is idxC: '0';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'index' }, {
						idxC: cg:generateExpression(expr: arg:value);
					});
				});
				return self:arrayElemResCast(containerType: targetType, cg: cg) . 'spec_array_get(' . targetC . ', ' . idxC . ')';
			});
			if({ m == 'set' }, {
				local String is idxC: '0';
				local String is itemC: 'NULL';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'index' }, {
						idxC: cg:generateExpression(expr: arg:value);
					});
					if({ arg:name == 'item' || arg:name == 'value' }, {
						itemC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_array_set(' . targetC . ', ' . idxC . ', (void*)(intptr_t)(' . itemC . '))';
			});
			if({ m == 'add' }, {
				local String is itemC: 'NULL';
				local Boolean is itemClaims: false;
				if({ expr:argCount() > 0 }, {
					local Expression is valExpr: self:argValue(expr: expr, index: 0);
					local Boolean is valIsArray: match(on: valExpr, when: [
						Expression:ArrayLit: local Function of Boolean(Array of Expression is items){ return true; },
						else: { false }
					]);
					if({ valIsArray }, {
						cg:setContainerHint(t: targetType);
						itemC: cg:generateExpression(expr: valExpr);
						return 'spec_array_add_array(' . targetC . ', ' . itemC . ')';
					});
					local Boolean is valIsGetCall: match(on: valExpr, when: [
						Expression:Call: local Function of Boolean(CallData is vc){
							return vc:name == 'get' || vc:name == 'getString';
						},
						else: { false }
					]);
					itemClaims: cg:yieldsClaim(expr: valExpr) && !valIsGetCall;
					local Boolean is savedArgMode: cg:argMode;
					cg:setArgMode(m: false);
					itemC: cg:generateExpression(expr: valExpr);
					cg:setArgMode(m: savedArgMode);
				});
				local String is elemKindA: cg:containerElemKind(containerType: targetType);
				local String is addFn: 'spec_array_add';
				if({ elemKindA == 'object' }, {
					addFn: if({ itemClaims }, { 'spec_array_add_owned' }, { 'spec_array_add_object' });
				});
				return addFn . '(' . targetC . ', (void*)(' . itemC . '))';
			});
			if({ m == 'length' }, {
				return 'spec_array_length(' . targetC . ')';
			});
			if({ m == 'pop' }, {
				local String is defC: 'NULL';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'default' }, {
						local String is rawDefC: cg:generateExpression(expr: arg:value);
						if({ targetType:startsWith(prefix: 'Array:String') }, {
							defC: rawDefC;
						}, {
							defC: '(void*)(intptr_t)(' . rawDefC . ')';
						});
					});
				});
				return self:arrayElemResCast(containerType: targetType, cg: cg) . 'spec_array_pop(' . targetC . ', ' . defC . ')';
			});
			if({ m == 'removeAt' }, {
				local String is idxC: '0';
				local String is defC: 'NULL';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'index' }, {
						idxC: cg:generateExpression(expr: arg:value);
					});
					if({ arg:name == 'default' }, {
						defC: '(void*)(intptr_t)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_array_remove_at(' . targetC . ', ' . idxC . ', ' . defC . ')';
			});
			if({ m == 'isEmpty' }, {
				return '(long long)(spec_array_length(' . targetC . ') == 0)';
			});
			if({ m == 'slice' }, {
				local String is startC: '0';
				local String is endC: '0';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'start' }, {
						startC: cg:generateExpression(expr: arg:value);
					});
					if({ arg:name == 'end' }, {
						endC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'Array_slice(' . targetC . ', ' . startC . ', ' . endC . ')';
			});
			if({ m == 'clear' }, {
				return 'spec_array_clear(' . targetC . ')';
			});
			if({ m == 'indexOf' }, {
				local String is searchC: '""';
				local String is defC: '-1';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'search' || arg:name == 'needle' }, {
						searchC: cg:generateExpression(expr: arg:value);
					});
					if({ arg:name == 'default' }, {
						defC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'Array_indexOf(' . targetC . ', ' . searchC . ', ' . defC . ')';
			});
			# Higher-order: anon functions inline as loops; values as callbacks.
			if({ m == 'each' }, {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'each', targetC: targetC, fnExpr: fnExpr);
			});
			if({ m == 'filter' }, {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'filter', targetC: targetC, fnExpr: fnExpr);
			});
			if({ m == 'count' }, {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'count', targetC: targetC, fnExpr: fnExpr);
			});
			if({ m == 'any' }, {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'any', targetC: targetC, fnExpr: fnExpr);
			});
			if({ m == 'map' }, {
				if({ expr:argCount() > 0 }, {
					local Expression is fnExpr: self:argValue(expr: expr, index: 0);
					local Boolean is isAnon: match(on: fnExpr, when: [
						Expression:AnonFn: local Function of Boolean(Type is returnType, Array of Parameter is params, Array of Statement is body){ return true; },
						else: { false }
					]);
					if({ isAnon }, {
						return cg:generateInlineArrayOp(mode: 'map', targetC: targetC, fnExpr: fnExpr);
					});
				});
			});
			if({ m == 'fold' }, {
				if({ expr:argCount() >= 2 }, {
					local Expression is initExpr: self:argValue(expr: expr, index: 0);
					local Expression is fnExpr: self:argValue(expr: expr, index: 1);
					local Boolean is isAnon: match(on: fnExpr, when: [
						Expression:AnonFn: local Function of Boolean(Type is returnType, Array of Parameter is params, Array of Statement is body){ return true; },
						else: { false }
					]);
					if({ isAnon }, {
						return cg:generateInlineArrayFold(targetC: targetC, initExpr: initExpr, fnExpr: fnExpr);
					});
				});
			});
			if({ m == 'join' }, {
				local String is sepC: '""';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'separator' || sepC == '""' }, {
						sepC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'Array_join(' . targetC . ', ' . sepC . ')';
			});
		});
		# List methods ([Byte] byte-buffer shape; pointer-vector shapes below).
		if({ targetType == 'List:Byte' || targetType == 'List of Byte' }, {
			local String is errC: 'spec_noop_closure()';
			if({ m == 'get' || m == 'pop' || m == 'set' }, {
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'error' }, {
						errC: cg:generateExpression(expr: arg:value);
					});
				});
			});
			if({ m == 'push' }, {
				local String is itemC: '0';
				cd:args:each(action: local Function(NamedArg is arg){
					itemC: cg:generateExpression(expr: arg:value);
				});
				return 'spec_bytebuffer_push(' . targetC . ', (long long)(' . itemC . '))';
			});
			if({ m == 'appendString' }, {
				local String is sC: 'spec_string_intern("")';
				cd:args:each(action: local Function(NamedArg is arg){
					sC: cg:generateExpression(expr: arg:value);
				});
				return 'spec_bytebuffer_append_string(' . targetC . ', spec_buf_to_cstring((SpecBuf*)(' . sC . ')))';
			});
			if({ m == 'get' }, {
				local String is idxC: '0';
				local String is defC: '0';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'index' }, {
						idxC: cg:generateExpression(expr: arg:value);
					});
					if({ arg:name == 'default' }, {
						defC: '(long long)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_bytebuffer_get(' . targetC . ', ' . idxC . ', ' . defC . ', ' . errC . ')';
			});
			if({ m == 'set' }, {
				local String is idxC: '0';
				local String is itemC: '0';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'index' }, {
						idxC: cg:generateExpression(expr: arg:value);
					});
					if({ arg:name == 'item' || arg:name == 'value' }, {
						itemC: '(long long)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_bytebuffer_set(' . targetC . ', ' . idxC . ', ' . itemC . ', ' . errC . ')';
			});
			if({ m == 'pop' }, {
				local String is defC: '0';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'default' }, {
						defC: '(long long)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_bytebuffer_pop(' . targetC . ', ' . defC . ', ' . errC . ')';
			});
			if({ m == 'length' }, {
				return 'spec_bytebuffer_length(' . targetC . ')';
			});
			if({ m == 'clear' }, {
				return 'spec_bytebuffer_clear(' . targetC . ')';
			});
			if({ m == 'toString' }, {
				return 'spec_bytebuffer_to_string(' . targetC . ')';
			});
		});

		# List methods (pointer-vector shapes, element-kind casts).
		if({ targetType:startsWith(prefix: 'List') }, {
			local String is listElem: '';
			if({ targetType:startsWith(prefix: 'List of ') && targetType:length() > 7 }, {
				listElem: targetType:substring(start: 7, end: targetType:length());
			}, {
				if({ targetType:startsWith(prefix: 'List:') && targetType:length() > 5 }, {
					listElem: targetType:substring(start: 5, end: targetType:length());
				});
			});
			local String is elemKind: cg:containerElemKind(containerType: targetType);
			local String is itemPre: '(void*)(intptr_t)(';
			local String is itemPost: ')';
			local String is resCast: '(long long)(intptr_t)';
			if({ elemKind == 'string' }, {
				itemPre: '(void*)(';
				resCast: '(String)';
			}, {
				if({ elemKind == 'object' }, {
					itemPre: '(void*)(';
					resCast: '(' . cg:cTypeFor(typeName: listElem) . ')(intptr_t)';
				});
			});
			local String is errC: 'spec_noop_closure()';
			if({ m == 'get' || m == 'pop' || m == 'set' }, {
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'error' }, {
						errC: cg:generateExpression(expr: arg:value);
					});
				});
			});
			if({ m == 'push' }, {
				local String is itemC: '0';
				local Boolean is savedArgV: cg:argMode;
				cg:setArgMode(m: false);
				cd:args:each(action: local Function(NamedArg is arg){
					itemC: cg:generateExpression(expr: arg:value);
				});
				cg:setArgMode(m: savedArgV);
				return 'spec_vec_push(' . targetC . ', ' . itemPre . itemC . itemPost . ')';
			});
			if({ m == 'get' }, {
				local String is idxC: '0';
				local String is defC: '0';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'index' }, {
						idxC: cg:generateExpression(expr: arg:value);
					});
					if({ arg:name == 'default' }, {
						defC: cg:generateExpression(expr: arg:value);
					});
				});
				return resCast . 'spec_vec_get(' . targetC . ', ' . idxC . ', ' . itemPre . defC . itemPost . ', ' . errC . ')';
			});
			if({ m == 'set' }, {
				local String is idxC: '0';
				local String is itemC: '0';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'index' }, {
						idxC: cg:generateExpression(expr: arg:value);
					});
					if({ arg:name == 'item' || arg:name == 'value' }, {
						local Boolean is savedArgS: cg:argMode;
						cg:setArgMode(m: false);
						itemC: cg:generateExpression(expr: arg:value);
						cg:setArgMode(m: savedArgS);
					});
				});
				return 'spec_vec_set(' . targetC . ', ' . idxC . ', ' . itemPre . itemC . itemPost . ', ' . errC . ')';
			});
			if({ m == 'pop' }, {
				local String is defC: '0';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'default' }, {
						defC: cg:generateExpression(expr: arg:value);
					});
				});
				return resCast . 'spec_vec_pop(' . targetC . ', ' . itemPre . defC . itemPost . ', ' . errC . ')';
			});
			if({ m == 'length' }, {
				return 'spec_vec_length(' . targetC . ')';
			});
			if({ m == 'clear' }, {
				return 'spec_vec_clear(' . targetC . ')';
			});
		});
		return '';
	}

	## Binds Map construction and concrete getters.
	##
	## @param expr: CALL expression.
	## @param targetC: Target C.
	## @param targetType: Target type name.
	## @param cg: The code generator.
	## @return: C call, or ''.
	Function of String is bindMapCall(Expression is expr, String is targetC, String is targetType, CodeGenerator is cg){
		local CallData is cd: self:extractCall(expr: expr);
		local String is m: cd:name;
		local String is a0: '';
		if({ expr:argCount() > 0 }, {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		});
		local String is a1: '';
		if({ expr:argCount() > 1 }, {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		});
		if({ m == 'init' }, {
			return 'spec_map_new()';
		});
		if({ m == 'set' }, {
			# String values store directly via spec_xstrdup (so the SpecBuf*
			# argument stays in argMode: true to be claimed in the pool);
			# everything else boxes into the any-slot via spec_map_set_any.
			local String is keyC: 'spec_string_intern("")';
			local String is valC: 'spec_string_intern("")';
			local Boolean is isStrMap: targetType:contains(needle: 'String:String') || targetType:contains(needle: 'to String');
			local Boolean is valIsStr: true;
			cd:args:each(action: local Function(NamedArg is arg){
				if({ arg:name == 'key' }, {
					keyC: cg:generateExpression(expr: arg:value);
				});
				if({ arg:name == 'value' }, {
					local Boolean is argIsStrLitOrConcat: match(on: arg:value, when: [
						Expression:StringLit: local Function of Boolean(String is value){ return true; },
						Expression:Binary: local Function of Boolean(String is op, Expression is left, Expression is right){ return op == '.'; },
						else: { false }
					]);
					valIsStr: isStrMap || cg:inferTargetType(expr: arg:value) == 'String' || argIsStrLitOrConcat;
					local Boolean is savedArgMode: cg:argMode;
					if({ !valIsStr }, {
						cg:setArgMode(m: false);
					});
					valC: cg:generateExpression(expr: arg:value);
					cg:setArgMode(m: savedArgMode);
					valIsStr: valIsStr || cg:isStringExpr(expr: arg:value, exprC: valC);
				});
			});
			if({ isStrMap || valIsStr }, {
				return 'spec_map_set(' . targetC . ', ' . keyC . ', ' . valC . ')';
			});
			return 'spec_map_set_any(' . targetC . ', ' . keyC . ', (void*)(intptr_t)(' . valC . '))';
		});
		if({ m == 'get' }, {
			return 'spec_map_get(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		if({ m == 'getString' }, {
			return '(String)spec_map_get(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		if({ m == 'getInt' }, {
			return 'Map_getInt(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		if({ m == 'getFloat' }, {
			return '((double)spec_map_get(' . targetC . ', ' . a0 . ', (void*)0))';
		});
		if({ m == 'getBool' }, {
			return 'Map_getBool(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		if({ m == 'has' }, {
			return 'spec_map_has(' . targetC . ', ' . a0 . ')';
		});
		if({ m == 'remove' }, {
			return 'spec_map_remove(' . targetC . ', ' . a0 . ')';
		});
		if({ m == 'keys' }, {
			return 'spec_map_keys(' . targetC . ')';
		});
		if({ m == 'length' }, {
			return '(long long)spec_map_length(' . targetC . ')';
		});
		if({ m == 'each' }, {
			if({ expr:argCount() > 0 }, {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				local Boolean is isAnon: match(on: fnExpr, when: [
					Expression:AnonFn: local Function of Boolean(Type is returnType, Array of Parameter is params, Array of Statement is body){ return true; },
					else: { false }
				]);
				if({ isAnon }, {
					return cg:generateInlineMapEach(targetC: targetC, fnExpr: fnExpr);
				});
			});
		});
		return '';
	}

	## Binds String instance methods via direct dispatch to the compiled
	## bodies (prototypes are emitted for String). Unresolved methods fall
	## through to spec_string_* interception.
	##
	## @param expr: CALL expression.
	## @param targetC: Target C.
	## @param cg: The code generator.
	## @return: C call, or ''.
	Function of String is bindStringDirect(Expression is expr, String is targetC, CodeGenerator is cg){
		local CallData is cd: self:extractCall(expr: expr);
		local String is m: cd:name;
		local String is a0: '';
		if({ expr:argCount() > 0 }, {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		});
		local String is a1: '';
		if({ expr:argCount() > 1 }, {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		});
		return match(on: m, when: [
			'length': { 'spec_string_length(' . targetC . ')' },
			'charAt': { 'String_charAt(' . targetC . ', ' . a0 . ', ' . a1 . ')' },
			'substring': { 'spec_string_substring(' . targetC . ', ' . a0 . ', ' . a1 . ')' },
			'indexOf': { 'spec_string_index_of(' . targetC . ', ' . a0 . ', ' . a1 . ')' },
			'trim': { 'String_trim(' . targetC . ')' },
			'isDigit': { 'String_isDigit(' . targetC . ')' },
			'isAlpha': { 'String_isAlpha(' . targetC . ')' },
			'isWhitespace': { 'String_isWhitespace(' . targetC . ')' },
			'countLeading': { 'String_countLeading(' . targetC . ', ' . a0 . ')' },
			'split': { 'String_split(' . targetC . ', ' . a0 . ')' },
			'lines': { 'String_lines(' . targetC . ')' },
			'contains': { 'String_contains(' . targetC . ', ' . a0 . ')' },
			'startsWith': { 'String_startsWith(' . targetC . ', ' . a0 . ')' },
			'endsWith': { 'String_endsWith(' . targetC . ', ' . a0 . ')' },
			'replaceAll': { 'String_replaceAll(' . targetC . ', ' . a0 . ', ' . a1 . ')' },
			'parseInt': {
				local String is baseC: '10';
				local String is defC: '-1';
				cd:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'base' }, {
						baseC: cg:generateExpression(expr: arg:value);
					});
					if({ arg:name == 'default' }, {
						defC: cg:generateExpression(expr: arg:value);
					});
				});
				'String_parseInt(' . targetC . ', ' . baseC . ', ' . defC . ')'
			},
			else: { '' }
		]);
	}
}
