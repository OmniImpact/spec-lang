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
		['base', 'compiler', 'ast', ExpressionKind],
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
		local ClassInfo is fCls: cg:findClass(name: clsName);
		# clsName may be qualified ('base:sysinternal:Buf'); the lookup
		# already resolved it — only absence (empty name) is a miss.
		Conditional:if(check: { fCls:name == '' }, then: {
			return '';
		});
		local Member is foundM;
		local Boolean is hasM: false;
		fCls:members:each(action: local Function(Member is m){
			Conditional:if(check: { !hasM && m:kind == MemberKind:METHOD && m:name == expr:methodName }, then: {
				hasM: true;
				foundM: m;
			});
		});
		Conditional:if(check: { !hasM }, then: {
			return '';
		});
		local Array of String is argList: [];
		local Boolean is argsOk: true;
		local Int is posIdx: 0;
		foundM:params:each(action: local Function(Parameter is p){
			Conditional:if(check: { argsOk }, then: {
				local Boolean is got: false;
				local Expression is posArg: expr:argValue(index: posIdx);
				Conditional:if(check: { posIdx < expr:argCount() && expr:argName(index: posIdx) == '' }, then: {
					argList:add(item: cg:generateExpression(expr: posArg));
					posIdx: posIdx + 1;
					got: true;
				});
				Conditional:if(check: { !got }, then: {
					expr:methodArgs:each(action: local Function(NamedArg is a){
						Conditional:if(check: { !got && a:name == p:name }, then: {
							got: true;
							argList:add(item: cg:generateExpression(expr: a:value));
						});
					});
				});
				Conditional:if(check: { !got && p:hasDefault }, then: {
					got: true;
					argList:add(item: cg:generateExpression(expr: p:defaultExpr));
				});
				Conditional:if(check: { !got }, then: {
					argsOk: false;
				});
			});
		});
		Conditional:if(check: { !argsOk }, then: {
			return '';
		});
		local String is argCs: '';
		argList:each(action: local Function(String is a){
			Conditional:if(check: { argCs == '' }, then: {
				argCs: a;
			}, else: {
				argCs: argCs . ', ' . a;
			});
		});
		return 'spec_' . self:utils:snakeCase(name: expr:methodName) . '(' . argCs . ')';
	}

	## Safely extracts a call argument's value expression, avoiding the
	## call-result field-access limitation.
	##
	## @param expr: The CALL expression.
	## @param index: The argument index.
	## @return: The value expression.
	Function of Expression is argValue(Expression is expr, Int is index){
		local NamedArg is arg: expr:methodArgs:get(index: index);
		return arg:value;
	}

	## Translates a builtin call into C; '' when not a builtin.
	##
	## @param expr: CALL expression node.
	## @param targetC: Generated C for the method target.
	## True when the first argument of a builtin math call is Int-typed
	## (§I.4: selects the integer overload's floor).
	##
	## @param expr: The call expression.
	## @param cg: The code generator.
	## @return: true when the first argument is Int.
	Function of Boolean is absArgIsInt(Expression is expr, CodeGenerator is cg){
		Conditional:if(check: { expr:argCount() == 0 }, then: {
			return false;
		});
		local Expression is a0: expr:argValue(index: 0);
		return cg:inferTargetType(expr: a0) == 'Int';
	}

	## @param targetType: Inferred type of the target.
	## @param cg: The code generator.
	## @return: C call string, or '' when not builtin.
	Function of String is generateBuiltinCall(Expression is expr, String is targetC, String is targetType, CodeGenerator is cg){
		# Reflection:class()/method() — compile-time source identity,
		# injected at the call site. Matches the bare usage form AND the
		# qualified floor chain (the base:sys wrapper delegates by chain;
		# user code hits the bare interception first).
		local Boolean is isReflTarget: targetC == 'Reflection';
		Conditional:if(check: { !isReflTarget && expr:methodTarget:kind == ExpressionKind:PATH }, then: {
			local String is rJoined: '';
			expr:methodTarget:pathSegments:each(action: local Function(String is seg){
				Conditional:if(check: { rJoined == '' }, then: {
					rJoined: seg;
				}, else: {
					rJoined: rJoined . ':' . seg;
				});
			});
			Conditional:if(check: { rJoined:endsWith(suffix: ':sysinternal:Reflection') }, then: {
				isReflTarget: true;
			});
		});
		Conditional:if(check: { isReflTarget && expr:methodName == 'class' && expr:argCount() == 0 }, then: {
			return 'spec_string_intern("' . cg:currentClassName . '")';
		});
		Conditional:if(check: { isReflTarget && expr:methodName == 'method' && expr:argCount() == 0 }, then: {
			return 'spec_string_intern("' . cg:currentMethodName . '")';
		});

		# Namespace-driven sysinternal floor binding: a call on a class whose
		# namespace ends with `sysinternal` compiles to spec_<snake(method)>.
		local String is floorCls: '';
		local ClassInfo is tc: cg:findClass(name: targetC);
		Conditional:if(check: { targetC != '' && tc:name == targetC && cg:isSysinternalClass(name: targetC) }, then: {
			floorCls: targetC;
		}, else: {
			local String is qCls: '';
			Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:PATH }, then: {
				local Array of String is qSegs: expr:methodTarget:pathSegments;
				qCls: qSegs:get(index: qSegs:length() - 1);
				# Qualified chains ('base:sysinternal:Buf') resolve by full
				# namespace path so the floor never collides with its
				# same-name base:sys wrapper.
				local String is qJoined: '';
				qSegs:each(action: local Function(String is seg){
					Conditional:if(check: { qJoined == '' }, then: {
						qJoined: seg;
					}, else: {
						qJoined: qJoined . ':' . seg;
					});
				});
				Conditional:if(check: { qJoined:contains(needle: ':sysinternal:') }, then: {
					qCls: qJoined;
				});
			}, else: {
				Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:CALL }, then: {
					local Expression is qInner: expr:methodTarget;
					Conditional:if(check: { qInner:methodTarget:kind == ExpressionKind:PATH }, then: {
						qCls: qInner:methodName;
					});
				});
			});
			local ClassInfo is qc: cg:findClass(name: qCls);
			Conditional:if(check: { qCls != '' && qc:name != '' && (qc:name == qCls || (qc:namespaceJoined() . ':' . qc:name) == qCls) && cg:isSysinternalClass(name: qCls) }, then: {
				floorCls: qCls;
			});
		});
		Conditional:if(check: { floorCls != '' }, then: {
			local String is bound: self:bindFloorCall(clsName: floorCls, expr: expr, cg: cg);
			Conditional:if(check: { bound != '' }, then: {
				return bound;
			});
		});

		# String:newline() — the newline constant.
		Conditional:if(check: { targetC == 'String' && expr:methodName == 'newline' && expr:argCount() == 0 }, then: {
			return 'spec_string_intern("\\n")';
		});

		# Type name introspection on class instances.
		Conditional:if(check: { expr:methodName == 'typeName' && targetType != '' && !self:policy:isTransparent(c: cg:findClass(name: targetType)) }, then: {
			return 'spec_type_name(' . targetC . ')';
		});

		# Int toBase conversion.
		Conditional:if(check: { expr:methodName == 'toBase' && (targetType == Primitive:INT:value()) }, then: {
			local String is baseC: '10';
			local String is digitsC: '0';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:if(check: { arg:name == 'base' }, then: {
 baseC: cg:generateExpression(expr: arg:value);
				});
				Conditional:if(check: { arg:name == 'digits' }, then: {
 digitsC: cg:generateExpression(expr: arg:value);
				});
			});
			return 'spec_int_to_base(' . targetC . ', ' . baseC . ', ' . digitsC . ')';
		});

		# Parallel fan-out execution.
		Conditional:if(check: { targetC == 'Parallel' && expr:methodName == 'run' && expr:argCount() >= 3 }, then: {
			local String is threadsC: '1';
			local String is iterC: '0';
			local String is workerC: 'NULL';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:if(check: { arg:name == 'threads' }, then: {
 threadsC: cg:generateExpression(expr: arg:value);
				});
				Conditional:if(check: { arg:name == 'iterations' }, then: {
 iterC: cg:generateExpression(expr: arg:value);
				});
				Conditional:if(check: { arg:name == 'worker' }, then: {
 workerC: cg:generateExpression(expr: arg:value);
				});
			});
			return 'spec_parallel_run(' . threadsC . ', ' . iterC . ', (void*)(' . workerC . '))';
		});

		# String:fromCharCode.
		Conditional:if(check: { targetC == 'String' && expr:methodName == 'fromCharCode' && expr:argCount() > 0 }, then: {
			local Expression is codeArg: self:argValue(expr: expr, index: 0);
			local String is codeC: cg:generateExpression(expr: codeArg);
			return 'spec_string_from_char_code(' . codeC . ')';
		});

		# The loop runners — While (the legacy spelling, bridged) and
		# Loops (§the control-flow provider).
		Conditional:if(check: { (targetC == 'Loops' || expr:bareProvider == 'Loops') && expr:methodName == 'run' && expr:argCount() > 0 }, then: {
			local Expression is loopVal: self:argValue(expr: expr, index: 0);
			local String is loopC: cg:generateExpressionInner(expr: loopVal);
			local String is loopClass: cg:inferTargetType(expr: loopVal);
			Conditional:if(check: { loopClass == '' && loopVal:kind == ExpressionKind:CALL }, then: {
				local Expression is mt: loopVal:methodTarget;
				loopClass: cg:generateExpression(expr: mt);
			});
			# the loop-class symbol qualifies for
			# nested classes — resolve the class and derive the qualified base.
			local ClassInfo is loopCls: cg:findClass(name: loopClass);
			Conditional:if(check: { loopCls:name != '' }, then: {
				loopClass: cg:utils:cIdent(name: loopCls:qualifiedName());
			});
			local String is ctrlC: 'NULL';
			Conditional:if(check: { expr:argCount() > 1 }, then: {
				local Expression is ctrlArg: self:argValue(expr: expr, index: 1);
				ctrlC: cg:generateExpression(expr: ctrlArg);
			});
			local String is freeLoopC: '';
			Conditional:if(check: { loopVal:kind == ExpressionKind:CALL && loopVal:methodName == 'init' }, then: {
				freeLoopC: ' spec_release(_lp);';
			});
			# The protocol inline needs the loop's static class for the
			# direct evaluate/iteration calls; an unresolved receiver (a
			# Loop held as Any) falls through to the runtime run body.
			Conditional:if(check: { loopClass != '' }, then: {
				return '({ void* _lp = (void*)(' . loopC . '); SpecLoopControl* _ctrl = (SpecLoopControl*)(' . ctrlC . '); while (' . loopClass . '_evaluate((void*)_lp)) { if (!' . loopClass . '_iteration((void*)_lp, _ctrl) || (_ctrl && _ctrl->stopped)) break; } if (_ctrl && _ctrl->on_complete) { _ctrl->on_complete(_ctrl->callback, _ctrl); }' . freeLoopC . ' })';
			});
		});
		# Loops:repeat(count:, worker:) — the counting loop, inlined.
		Conditional:if(check: { (targetC == 'Loops' || expr:bareProvider == 'Loops') && expr:methodName == 'repeat' && expr:argCount() == 2 }, then: {
			local Expression is repCountExpr;
			local Expression is repWorkerExpr;
			local Boolean is repHasCount: false;
			local Boolean is repHasWorker: false;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:if(check: { arg:name == 'count' }, then: {
					repCountExpr: arg:value;
					repHasCount: true;
				}, else: {
					Conditional:if(check: { arg:name == 'worker' }, then: {
						repWorkerExpr: arg:value;
						repHasWorker: true;
					});
				});
			});
			Conditional:if(check: { !repHasCount && expr:argCount() == 2 }, then: {
				repCountExpr: self:argValue(expr: expr, index: 0);
				repHasCount: true;
			});
			Conditional:if(check: { !repHasWorker && expr:argCount() == 2 }, then: {
				repWorkerExpr: self:argValue(expr: expr, index: 1);
				repHasWorker: true;
			});
			Conditional:if(check: { repHasCount && repHasWorker && repWorkerExpr:kind == ExpressionKind:ANON_FN }, then: {
				return cg:generateInlineRepeat(countExpr: repCountExpr, workerExpr: repWorkerExpr);
			});
		});
		Conditional:if(check: { (targetC == 'Loops' || expr:bareProvider == 'Loops') && (expr:methodName == 'while' || expr:methodName == 'condition' || expr:methodName == 'until' || expr:methodName == 'loop' || expr:methodName == 'init') }, then: {
			local Expression is varsExpr;
			local Expression is evalExpr;
			local Expression is iterExpr;
			local Boolean is hasVars: false;
			local Boolean is hasEval: false;
			local Boolean is hasIter: false;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:if(check: { arg:name == 'evaluate' }, then: {
					evalExpr: arg:value;
					hasEval: true;
				}, else: {
					Conditional:if(check: { arg:name == 'iterate' || arg:name == 'iteration' }, then: {
						iterExpr: arg:value;
						hasIter: true;
					}, else: {
						Conditional:if(check: { arg:name == 'vars' || arg:name == 'state' }, then: {
							varsExpr: arg:value;
							hasVars: true;
						});
					});
				});
			});
			Conditional:if(check: { !hasEval }, then: {
				Conditional:if(check: { expr:argCount() >= 3 }, then: {
					evalExpr: self:argValue(expr: expr, index: 1);
					hasEval: true;
				}, else: {
					Conditional:if(check: { expr:argCount() >= 2 }, then: {
						evalExpr: self:argValue(expr: expr, index: 0);
						hasEval: true;
					});
				});
			});
			Conditional:if(check: { !hasIter }, then: {
				Conditional:if(check: { expr:argCount() >= 3 }, then: {
					iterExpr: self:argValue(expr: expr, index: 2);
					hasIter: true;
				}, else: {
					Conditional:if(check: { expr:argCount() >= 2 }, then: {
						iterExpr: self:argValue(expr: expr, index: 1);
						hasIter: true;
					});
				});
			});
			Conditional:if(check: { !hasVars && expr:argCount() >= 3 }, then: {
				varsExpr: self:argValue(expr: expr, index: 0);
				hasVars: true;
			});
			Conditional:if(check: { hasEval && hasIter && evalExpr:kind == ExpressionKind:ANON_FN && iterExpr:kind == ExpressionKind:ANON_FN }, then: {
				local Array of Parameter is loopVars: [];
				Conditional:if(check: { hasVars && varsExpr:anonParams:length() > 0 }, then: {
					loopVars: varsExpr:anonParams;
				});
				# until is the do-while — the body runs once first.
				Conditional:if(check: { expr:methodName == 'until' }, then: {
					return cg:generateInlineUntil(evalExpr: evalExpr, iterExpr: iterExpr);
				});
				return cg:generateInlineWhileLoop(loopVars: loopVars, evalExpr: evalExpr, iterExpr: iterExpr);
			});
		});

		# LoopControl methods: transparent runtime-managed objects — the
		# constructor wires the optional completion callback directly.
		Conditional:if(check: { targetC == 'LoopControl' && expr:methodName == 'init' }, then: {
			Conditional:if(check: { expr:argCount() == 0 }, then: {
				return 'LoopControl_new()';
			});
			local NamedArg is cbArg: expr:methodArgs:get(index: 0);
			local Expression is cbVal: cbArg:value;
			local String is cbC: cg:generateExpression(expr: cbVal);
			local String is cbClass: cg:inferTargetType(expr: cbVal);
			Conditional:if(check: { cbClass == '' && cbVal:kind == ExpressionKind:CALL }, then: {
				local Expression is mt: cbVal:methodTarget;
				cbClass: cg:generateExpression(expr: mt);
			});
			# the callback-class symbol qualifies
			# for nested classes.
			local ClassInfo is cbCls: cg:findClass(name: cbClass);
			Conditional:if(check: { cbCls:name != '' }, then: {
				cbClass: cg:utils:cIdent(name: cbCls:qualifiedName());
			});
			return '({ SpecLoopControl* _c = LoopControl_new(); _c->callback = (void*)(' . cbC . '); _c->on_complete = (void (*)(void*, struct SpecLoopControl*))' . cbClass . '_onComplete; _c; })';
		});
		Conditional:if(check: { expr:methodName == 'stop' && (targetC == 'LoopControl' || targetType == 'LoopControl') }, then: {
			return 'LoopControl_stop(' . targetC . ')';
		});
		# LoopControl:isStopped — the halt query the runtime run()
		# composes from (the compile-time inlines read the C struct
		# directly; the wrapper needs the public surface). Null-safe:
		# an omitted control drives without a halt query.
		Conditional:if(check: { expr:methodName == 'isStopped' && (targetC == 'LoopControl' || targetType == 'LoopControl') }, then: {
			return '({ SpecLoopControl* _lc = (SpecLoopControl*)(' . targetC . '); _lc ? (bool)_lc->stopped : false; })';
		});
		# LoopControl:complete — fires the completion callback the
		# runtime run() owes after the loop ends (the inline protocol's
		# on_complete tail). No callback registered: nothing fires.
		Conditional:if(check: { expr:methodName == 'complete' && (targetC == 'LoopControl' || targetType == 'LoopControl') }, then: {
			return '({ SpecLoopControl* _lc = (SpecLoopControl*)(' . targetC . '); if (_lc && _lc->on_complete) { _lc->on_complete(_lc->callback, _lc); } })';
		});

		# Math functions.
		Conditional:if(check: { targetC == 'Math' }, then: {
			local String is m: expr:methodName;
			local String is a0: '0.0';
			Conditional:if(check: { expr:argCount() > 0 }, then: {
				a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
			});
			# Single-operand functions: the match yields the C call; the
			# empty else lets the two-operand section run.
			local String is oneC: match(on: m, when: [
				'round': { 'spec_math_round(' . a0 . ')' },
				'floor': { 'spec_math_floor(' . a0 . ')' },
				['ceil', 'ceiling']: { 'spec_math_ceil(' . a0 . ')' },
				'abs': {
					# §I.4: type-distinct overloads — the Int
					# overload routes to the integer floor.
					local String is absC: 'spec_math_abs(' . a0 . ')';
					Conditional:if(check: { self:absArgIsInt(expr: expr, cg: cg) }, then: {
						absC: 'spec_math_abs_int(' . a0 . ')';
					});
					absC
				},
				'sqrt': { 'spec_math_sqrt(' . a0 . ')' },
				'sin': { 'spec_math_sin(' . a0 . ')' },
				'cos': { 'spec_math_cos(' . a0 . ')' },
				'tan': { 'spec_math_tan(' . a0 . ')' },
				'log': { 'spec_math_log(' . a0 . ')' },
				'log2': { 'spec_math_log2(' . a0 . ')' },
				'fastRandom': { 'spec_fast_random()' },
				else: { '' }
			]);
			Conditional:if(check: { oneC != '' }, then: {
				return oneC;
			});
			# Two-operand functions: a + b, or named value/min/max.
			local String is a1: '0.0';
			Conditional:if(check: { expr:argCount() > 1 }, then: {
				a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
			});
			Conditional:if(check: { m == 'min' }, then: {
				return 'spec_math_min(' . a0 . ', ' . a1 . ')';
			});
			Conditional:if(check: { m == 'max' }, then: {
				return 'spec_math_max(' . a0 . ', ' . a1 . ')';
			});
			Conditional:if(check: { m == 'pow' }, then: {
				return 'spec_math_pow(' . a0 . ', ' . a1 . ')';
			});
			Conditional:if(check: { m == 'atan2' }, then: {
				return 'spec_math_atan2(' . a0 . ', ' . a1 . ')';
			});
			Conditional:if(check: { m == 'random' }, then: {
				return 'spec_math_random(' . a0 . ', ' . a1 . ')';
			});
			Conditional:if(check: { m == 'clamp' }, then: {
				local String is vC: '0.0';
				local String is loC: '0.0';
				local String is hiC: '1.0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'value' }, then: {
 vC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'min' || arg:name == 'lo' }, then: {
 loC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'max' || arg:name == 'hi' }, then: {
 hiC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_math_clamp(' . vC . ', ' . loC . ', ' . hiC . ')';
			});
			Conditional:if(check: { m == 'toInt' }, then: {
				return '((long long)(' . a0 . '))';
			});
			Conditional:if(check: { m == 'toFloat' }, then: {
				return '((double)(' . a0 . '))';
			});
		});

		# Array/List/Map method bindings (runtime-managed; spec_* calls).
		# Entry is by method name on any Array-typed target — no transparency
		# check: registered locals must bind without a registry lookup.
		local Boolean is isArr: targetC == 'Array' || targetType == 'Array' || targetType:startsWith(prefix: 'Array') ||
			targetType:startsWith(prefix: 'List') ||
			((targetType == '' || targetType == Primitive:ANY:value()) && (
				expr:methodName == 'get' || expr:methodName == 'add' || expr:methodName == 'set' || expr:methodName == 'pop' ||
				expr:methodName == 'removeAt' || expr:methodName == 'slice' || expr:methodName == 'clear' || expr:methodName == 'join' ||
				expr:methodName == 'each' || expr:methodName == 'filter' || expr:methodName == 'count' || expr:methodName == 'any' ||
				expr:methodName == 'map' || expr:methodName == 'fold' ||
				(expr:methodName == 'length' && targetType != 'String' && targetC != 'Map' && !targetType:startsWith(prefix: 'Map:'))
			));
		Conditional:if(check: { isArr }, then: {
			local String is arrC: self:bindContainerCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			Conditional:if(check: { arrC != '' }, then: {
				return arrC;
			});
		});

		# Map literal-constructor + concrete getters + inline each.
		Conditional:if(check: { targetC == 'Map' || targetType == 'Map' || targetType:startsWith(prefix: 'Map:') }, then: {
			local String is mapC: self:bindMapCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			Conditional:if(check: { mapC != '' }, then: {
				return mapC;
			});
		});

		# String instance methods: direct dispatch to compiled bodies.
		Conditional:if(check: { targetType == 'String' }, then: {
			local String is ddC: self:bindStringDirect(expr: expr, targetC: targetC, cg: cg);
			Conditional:if(check: { ddC != '' }, then: {
				return ddC;
			});
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
		local String is m: expr:methodName;
		local String is a0: '';
		Conditional:if(check: { expr:argCount() > 0 }, then: {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		});
		local String is a1: '';
		Conditional:if(check: { expr:argCount() > 1 }, then: {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		});
		# Array methods (SpecArray*). Named-arg extraction.
		Conditional:if(check: { targetType:startsWith(prefix: 'Array') }, then: {
			Conditional:if(check: { m == 'get' }, then: {
				local String is idxC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_array_get(' . targetC . ', ' . idxC . ')';
			});
			Conditional:if(check: { m == 'set' }, then: {
				local String is idxC: '0';
				local String is itemC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'item' || arg:name == 'value' }, then: {
 itemC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_array_set(' . targetC . ', ' . idxC . ', (void*)(intptr_t)(' . itemC . '))';
			});
			Conditional:if(check: { m == 'add' }, then: {
				local String is itemC: 'NULL';
				local Boolean is itemClaims: false;
				Conditional:if(check: { expr:argCount() > 0 }, then: {
					local Expression is valExpr: self:argValue(expr: expr, index: 0);
					Conditional:if(check: { valExpr:kind == ExpressionKind:ARRAY }, then: {
						cg:setContainerHint(t: targetType);
						itemC: cg:generateExpression(expr: valExpr);
						return 'spec_array_add_array(' . targetC . ', ' . itemC . ')';
					});
					itemClaims: cg:yieldsClaim(expr: valExpr) && !(valExpr:kind == ExpressionKind:CALL && (valExpr:methodName == 'get' || valExpr:methodName == 'getString'));
					local Boolean is savedArgMode: cg:argMode;
					cg:setArgMode(m: false);
					itemC: cg:generateExpression(expr: valExpr);
					cg:setArgMode(m: savedArgMode);
				});
				local String is elemKindA: cg:containerElemKind(containerType: targetType);
				local String is addFn: 'spec_array_add';
				Conditional:if(check: { elemKindA == 'object' }, then: {
					addFn: Conditional:if(check: { itemClaims }, then: { 'spec_array_add_owned' }, else: { 'spec_array_add_object' });
				});
				return addFn . '(' . targetC . ', (void*)(' . itemC . '))';
			});
			Conditional:if(check: { m == 'length' }, then: {
				return 'spec_array_length(' . targetC . ')';
			});
			Conditional:if(check: { m == 'pop' }, then: {
				local String is defC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'default' }, then: {
						local String is rawDefC: cg:generateExpression(expr: arg:value);
						Conditional:if(check: { targetType:startsWith(prefix: 'Array:String') }, then: {
							defC: rawDefC;
						}, else: {
							defC: '(void*)(intptr_t)(' . rawDefC . ')';
						});
					});
				});
				return 'spec_array_pop(' . targetC . ', ' . defC . ')';
			});
			Conditional:if(check: { m == 'removeAt' }, then: {
				local String is idxC: '0';
				local String is defC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'default' }, then: {
 defC: '(void*)(intptr_t)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_array_remove_at(' . targetC . ', ' . idxC . ', ' . defC . ')';
			});
			Conditional:if(check: { m == 'isEmpty' }, then: {
				return '(long long)(spec_array_length(' . targetC . ') == 0)';
			});
			Conditional:if(check: { m == 'slice' }, then: {
				local String is startC: '0';
				local String is endC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'start' }, then: {
 startC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'end' }, then: {
 endC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'Array_slice(' . targetC . ', ' . startC . ', ' . endC . ')';
			});
			Conditional:if(check: { m == 'clear' }, then: {
				return 'spec_array_clear(' . targetC . ')';
			});
			Conditional:if(check: { m == 'indexOf' }, then: {
				local String is searchC: '""';
				local String is defC: '-1';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'search' || arg:name == 'needle' }, then: {
 searchC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'Array_indexOf(' . targetC . ', ' . searchC . ', ' . defC . ')';
			});
			# Higher-order: anon functions inline as loops; values as callbacks.
			Conditional:if(check: { m == 'each' }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'each', targetC: targetC, fnExpr: fnExpr);
			});
			Conditional:if(check: { m == 'filter' }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'filter', targetC: targetC, fnExpr: fnExpr);
			});
			Conditional:if(check: { m == 'count' }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'count', targetC: targetC, fnExpr: fnExpr);
			});
			Conditional:if(check: { m == 'any' }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'any', targetC: targetC, fnExpr: fnExpr);
			});
			Conditional:if(check: { m == 'map' }, then: {
				Conditional:if(check: { expr:argCount() > 0 }, then: {
					local Expression is fnExpr: self:argValue(expr: expr, index: 0);
					Conditional:if(check: { fnExpr:kind == ExpressionKind:ANON_FN }, then: {
						return cg:generateInlineArrayOp(mode: 'map', targetC: targetC, fnExpr: fnExpr);
					});
				});
			});
			Conditional:if(check: { m == 'fold' }, then: {
				Conditional:if(check: { expr:argCount() >= 2 }, then: {
					local Expression is initExpr: self:argValue(expr: expr, index: 0);
					local Expression is fnExpr: self:argValue(expr: expr, index: 1);
					Conditional:if(check: { fnExpr:kind == ExpressionKind:ANON_FN }, then: {
						return cg:generateInlineArrayFold(targetC: targetC, initExpr: initExpr, fnExpr: fnExpr);
					});
				});
			});
			Conditional:if(check: { m == 'join' }, then: {
				local String is sepC: '""';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'separator' || sepC == '""' }, then: {
 sepC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'Array_join(' . targetC . ', ' . sepC . ')';
			});
		});
		# List methods ([Byte] byte-buffer shape; pointer-vector shapes below).
		Conditional:if(check: { targetType == 'List:Byte' || targetType == 'List of Byte' }, then: {
			local String is errC: 'spec_noop_closure()';
			Conditional:if(check: { m == 'get' || m == 'pop' || m == 'set' }, then: {
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'error' }, then: {
						errC: cg:generateExpression(expr: arg:value);
					});
				});
			});
			Conditional:if(check: { m == 'push' }, then: {
				local String is itemC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					itemC: cg:generateExpression(expr: arg:value);
				});
				return 'spec_bytebuffer_push(' . targetC . ', (long long)(' . itemC . '))';
			});
			Conditional:if(check: { m == 'appendString' }, then: {
				local String is sC: 'spec_string_intern("")';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					sC: cg:generateExpression(expr: arg:value);
				});
				return 'spec_bytebuffer_append_string(' . targetC . ', spec_buf_to_cstring((SpecBuf*)(' . sC . ')))';
			});
			Conditional:if(check: { m == 'get' }, then: {
				local String is idxC: '0';
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'default' }, then: {
 defC: '(long long)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_bytebuffer_get(' . targetC . ', ' . idxC . ', ' . defC . ', ' . errC . ')';
			});
			Conditional:if(check: { m == 'set' }, then: {
				local String is idxC: '0';
				local String is itemC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'item' || arg:name == 'value' }, then: {
 itemC: '(long long)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_bytebuffer_set(' . targetC . ', ' . idxC . ', ' . itemC . ', ' . errC . ')';
			});
			Conditional:if(check: { m == 'pop' }, then: {
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'default' }, then: {
 defC: '(long long)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_bytebuffer_pop(' . targetC . ', ' . defC . ', ' . errC . ')';
			});
			Conditional:if(check: { m == 'length' }, then: {
				return 'spec_bytebuffer_length(' . targetC . ')';
			});
			Conditional:if(check: { m == 'clear' }, then: {
				return 'spec_bytebuffer_clear(' . targetC . ')';
			});
			Conditional:if(check: { m == 'toString' }, then: {
				return 'spec_bytebuffer_to_string(' . targetC . ')';
			});
		});

		# List methods (pointer-vector shapes, element-kind casts).
		Conditional:if(check: { targetType:startsWith(prefix: 'List') }, then: {
			local String is listElem: '';
			Conditional:if(check: { targetType:startsWith(prefix: 'List of ') && targetType:length() > 7 }, then: {
				listElem: targetType:substring(start: 7, end: targetType:length());
			}, else: {
				Conditional:if(check: { targetType:startsWith(prefix: 'List:') && targetType:length() > 5 }, then: {
					listElem: targetType:substring(start: 5, end: targetType:length());
				});
			});
			local String is elemKind: cg:containerElemKind(containerType: targetType);
			local String is itemPre: '(void*)(intptr_t)(';
			local String is itemPost: ')';
			local String is resCast: '(long long)(intptr_t)';
			Conditional:if(check: { elemKind == 'string' }, then: {
				itemPre: '(void*)(';
				resCast: '(String)';
			}, else: {
				Conditional:if(check: { elemKind == 'object' }, then: {
					itemPre: '(void*)(';
					resCast: '(' . cg:cTypeFor(typeName: listElem) . ')(intptr_t)';
				});
			});
			local String is errC: 'spec_noop_closure()';
			Conditional:if(check: { m == 'get' || m == 'pop' || m == 'set' }, then: {
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'error' }, then: {
						errC: cg:generateExpression(expr: arg:value);
					});
				});
			});
			Conditional:if(check: { m == 'push' }, then: {
				local String is itemC: '0';
				local Boolean is savedArgV: cg:argMode;
				cg:setArgMode(m: false);
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					itemC: cg:generateExpression(expr: arg:value);
				});
				cg:setArgMode(m: savedArgV);
				return 'spec_vec_push(' . targetC . ', ' . itemPre . itemC . itemPost . ')';
			});
			Conditional:if(check: { m == 'get' }, then: {
				local String is idxC: '0';
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
				});
				return resCast . 'spec_vec_get(' . targetC . ', ' . idxC . ', ' . itemPre . defC . itemPost . ', ' . errC . ')';
			});
			Conditional:if(check: { m == 'set' }, then: {
				local String is idxC: '0';
				local String is itemC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'item' || arg:name == 'value' }, then: {
						local Boolean is savedArgS: cg:argMode;
						cg:setArgMode(m: false);
						itemC: cg:generateExpression(expr: arg:value);
						cg:setArgMode(m: savedArgS);
					});
				});
				return 'spec_vec_set(' . targetC . ', ' . idxC . ', ' . itemPre . itemC . itemPost . ', ' . errC . ')';
			});
			Conditional:if(check: { m == 'pop' }, then: {
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
				});
				return resCast . 'spec_vec_pop(' . targetC . ', ' . itemPre . defC . itemPost . ', ' . errC . ')';
			});
			Conditional:if(check: { m == 'length' }, then: {
				return 'spec_vec_length(' . targetC . ')';
			});
			Conditional:if(check: { m == 'clear' }, then: {
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
		local String is m: expr:methodName;
		local String is a0: '';
		Conditional:if(check: { expr:argCount() > 0 }, then: {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		});
		local String is a1: '';
		Conditional:if(check: { expr:argCount() > 1 }, then: {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		});
		Conditional:if(check: { m == 'init' }, then: {
			return 'spec_map_new()';
		});
		Conditional:if(check: { m == 'set' }, then: {
			# String values store directly via spec_xstrdup (so the SpecBuf*
			# argument stays in argMode: true to be claimed in the pool);
			# everything else boxes into the any-slot via spec_map_set_any.
			local String is keyC: 'spec_string_intern("")';
			local String is valC: 'spec_string_intern("")';
			local Boolean is isStrMap: targetType:contains(needle: 'String:String') || targetType:contains(needle: 'to String');
			local Boolean is valIsStr: true;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:if(check: { arg:name == 'key' }, then: {
 keyC: cg:generateExpression(expr: arg:value);
				});
				Conditional:if(check: { arg:name == 'value' }, then: {
					valIsStr: isStrMap || cg:inferTargetType(expr: arg:value) == 'String' || arg:value:kind == ExpressionKind:STRING || (arg:value:kind == ExpressionKind:BINARY && arg:value:str == '.');
					local Boolean is savedArgMode: cg:argMode;
					Conditional:if(check: { !valIsStr }, then: {
						cg:setArgMode(m: false);
					});
					valC: cg:generateExpression(expr: arg:value);
					cg:setArgMode(m: savedArgMode);
					valIsStr: valIsStr || cg:isStringExpr(expr: arg:value, exprC: valC);
				});
			});
			Conditional:if(check: { isStrMap || valIsStr }, then: {
				return 'spec_map_set(' . targetC . ', ' . keyC . ', ' . valC . ')';
			});
			return 'spec_map_set_any(' . targetC . ', ' . keyC . ', (void*)(intptr_t)(' . valC . '))';
		});
		Conditional:if(check: { m == 'get' }, then: {
			return 'spec_map_get(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		Conditional:if(check: { m == 'getString' }, then: {
			return '(String)spec_map_get(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		Conditional:if(check: { m == 'getInt' }, then: {
			return 'Map_getInt(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		Conditional:if(check: { m == 'getFloat' }, then: {
			return '((double)spec_map_get(' . targetC . ', ' . a0 . ', (void*)0))';
		});
		Conditional:if(check: { m == 'getBool' }, then: {
			return 'Map_getBool(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		Conditional:if(check: { m == 'has' }, then: {
			return 'spec_map_has(' . targetC . ', ' . a0 . ')';
		});
		Conditional:if(check: { m == 'remove' }, then: {
			return 'spec_map_remove(' . targetC . ', ' . a0 . ')';
		});
		Conditional:if(check: { m == 'keys' }, then: {
			return 'spec_map_keys(' . targetC . ')';
		});
		Conditional:if(check: { m == 'length' }, then: {
			return '(long long)spec_map_length(' . targetC . ')';
		});
		Conditional:if(check: { m == 'each' }, then: {
			Conditional:if(check: { expr:argCount() > 0 }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				Conditional:if(check: { fnExpr:kind == ExpressionKind:ANON_FN }, then: {
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
		local String is m: expr:methodName;
		local String is a0: '';
		Conditional:if(check: { expr:argCount() > 0 }, then: {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		});
		local String is a1: '';
		Conditional:if(check: { expr:argCount() > 1 }, then: {
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
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { arg:name == 'base' }, then: {
 baseC: cg:generateExpression(expr: arg:value);
					});
					Conditional:if(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
				});
				'String_parseInt(' . targetC . ', ' . baseC . ', ' . defC . ')'
			},
			else: { '' }
		]);
	}
}
