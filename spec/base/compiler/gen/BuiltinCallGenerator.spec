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
		['base', 'iterator']
,
		['base', 'compiler', 'gen', CodeGenerator],
		['base', 'sys', as Conditional()]
	];

	local CBackendUtils is utils: CBackendUtils:init();
	local EmissionPolicy is policy: EmissionPolicy:init();
	local Map of String to String is allEnumNames: Map:init();

	replace Function is init(){
		self:allEnumNames: Map:init();
	}

	## Receives the enum registry gathered by the checker.
	##
	## @param names: All enum names.
	Function is setEnumNames(Map of String to String is names){
		self:allEnumNames: names;
	}

	## Binds a sysinternal floor call to its C function per the naming
	## convention: spec_ + snake_case(method). Arguments match the declared
	## parameters positionally first, then by name, with declaration-side
	## defaults filling the rest. Returns '' when the method is not a floor
	## declaration, letting the caller fall through.
	Function of String is bindFloorCall(String is clsName, Expression is expr, CodeGenerator is cg){
		local ClassInfo is fCls: cg:findClass(name: clsName);
		# clsName may be qualified ('base:sysinternal:Buf'); the lookup
		# already resolved it — only absence (empty name) is a miss.
		Conditional:branch(check: { fCls:name == '' }, then: {
			return '';
		});
		local Member is foundM;
		local Boolean is hasM: false;
		fCls:members:each(action: local Function(Member is m){
			Conditional:branch(check: { !hasM && m:kind == MemberKind:METHOD && m:name == expr:methodName }, then: {
				hasM: true;
				foundM: m;
			});
		});
		Conditional:branch(check: { !hasM }, then: {
			return '';
		});
		local Array of String is argList: [];
		local Boolean is argsOk: true;
		local Int is posIdx: 0;
		foundM:params:each(action: local Function(Parameter is p){
			Conditional:branch(check: { argsOk }, then: {
				local Boolean is got: false;
				local Expression is posArg: expr:argValue(index: posIdx);
				Conditional:branch(check: { posIdx < expr:argCount() && expr:argName(index: posIdx) == '' }, then: {
					argList:add(item: cg:generateExpression(expr: posArg));
					posIdx: posIdx + 1;
					got: true;
				});
				Conditional:branch(check: { !got }, then: {
					expr:methodArgs:each(action: local Function(NamedArg is a){
						Conditional:branch(check: { !got && a:name == p:name }, then: {
							got: true;
							argList:add(item: cg:generateExpression(expr: a:value));
						});
					});
				});
				Conditional:branch(check: { !got && p:hasDefault }, then: {
					got: true;
					argList:add(item: cg:generateExpression(expr: p:defaultExpr));
				});
				Conditional:branch(check: { !got }, then: {
					argsOk: false;
				});
			});
		});
		Conditional:branch(check: { !argsOk }, then: {
			return '';
		});
		local String is argCs: '';
		argList:each(action: local Function(String is a){
			Conditional:branch(check: { argCs == '' }, then: {
				argCs: a;
			}, otherwise: {
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
	## (FUNCTIONS.md §I.4: selects the integer overload's floor).
	##
	## @param expr: The call expression.
	## @param cg: The code generator.
	## @return: true when the first argument is Int.
	Function of Boolean is absArgIsInt(Expression is expr, CodeGenerator is cg){
		Conditional:branch(check: { expr:argCount() == 0 }, then: {
			return false;
		});
		local Expression is a0: expr:argValue(index: 0);
		return cg:inferTargetType(expr: a0) == 'Int';
	}

	## @param targetType: Inferred type of the target.
	## @param cg: The code generator.
	## @return: C call string, or '' when not builtin.
	Function of String is generateBuiltinCall(Expression is expr, String is targetC, String is targetType, CodeGenerator is cg){
		# Stderr:line - diagnostics to standard error (INSTANCE.md R3:
		# the error:/Error routing fiction is deleted).
		Conditional:branch(check: { targetC == 'Stderr' && expr:methodName == 'line' && expr:argCount() > 0 }, then: {
			local Expression is errArg: self:argValue(expr: expr, index: 0);
			local String is errValC: cg:generateExpression(expr: errArg);
			local String is errStrC: cg:wrapToString(expr: errArg, exprC: errValC);
			return 'spec_error_line(' . errStrC . ')';
		});

		# Reflection:class()/method() — compile-time source identity,
		# injected at the call site. Matches the bare usage form AND the
		# qualified floor chain (the base:sys wrapper delegates by chain;
		# user code hits the bare interception first).
		local Boolean is isReflTarget: targetC == 'Reflection';
		Conditional:branch(check: { !isReflTarget && expr:methodTarget:kind == ExpressionKind:PATH }, then: {
			local String is rJoined: '';
			expr:methodTarget:pathSegments:each(action: local Function(String is seg){
				Conditional:branch(check: { rJoined == '' }, then: {
					rJoined: seg;
				}, otherwise: {
					rJoined: rJoined . ':' . seg;
				});
			});
			Conditional:branch(check: { rJoined:endsWith(suffix: ':sysinternal:Reflection') }, then: {
				isReflTarget: true;
			});
		});
		Conditional:branch(check: { isReflTarget && expr:methodName == 'class' && expr:argCount() == 0 }, then: {
			return 'spec_string_intern("' . cg:currentClassName . '")';
		});
		Conditional:branch(check: { isReflTarget && expr:methodName == 'method' && expr:argCount() == 0 }, then: {
			return 'spec_string_intern("' . cg:currentMethodName . '")';
		});

		# Namespace-driven sysinternal floor binding: a call on a class whose
		# namespace ends with `sysinternal` compiles to spec_<snake(method)>.
		local String is floorCls: '';
		local ClassInfo is tc: cg:findClass(name: targetC);
		Conditional:branch(check: { targetC != '' && tc:name == targetC && cg:isSysinternalClass(name: targetC) }, then: {
			floorCls: targetC;
		}, otherwise: {
			local String is qCls: '';
			Conditional:branch(check: { expr:methodTarget:kind == ExpressionKind:PATH }, then: {
				local Array of String is qSegs: expr:methodTarget:pathSegments;
				qCls: qSegs:get(index: qSegs:length() - 1);
				# Qualified chains ('base:sysinternal:Buf') resolve by full
				# namespace path so the floor never collides with its
				# same-name base:sys wrapper.
				local String is qJoined: '';
				qSegs:each(action: local Function(String is seg){
					Conditional:branch(check: { qJoined == '' }, then: {
						qJoined: seg;
					}, otherwise: {
						qJoined: qJoined . ':' . seg;
					});
				});
				Conditional:branch(check: { qJoined:contains(needle: ':sysinternal:') }, then: {
					qCls: qJoined;
				});
			}, otherwise: {
				Conditional:branch(check: { expr:methodTarget:kind == ExpressionKind:CALL }, then: {
					local Expression is qInner: expr:methodTarget;
					Conditional:branch(check: { qInner:methodTarget:kind == ExpressionKind:PATH }, then: {
						qCls: qInner:methodName;
					});
				});
			});
			local ClassInfo is qc: cg:findClass(name: qCls);
			Conditional:branch(check: { qCls != '' && qc:name != '' && (qc:name == qCls || (qc:namespaceJoined() . ':' . qc:name) == qCls) && cg:isSysinternalClass(name: qCls) }, then: {
				floorCls: qCls;
			});
		});
		Conditional:branch(check: { floorCls != '' }, then: {
			local String is bound: self:bindFloorCall(clsName: floorCls, expr: expr, cg: cg);
			Conditional:branch(check: { bound != '' }, then: {
				return bound;
			});
		});

		# String:newline() — the newline constant.
		Conditional:branch(check: { targetC == 'String' && expr:methodName == 'newline' && expr:argCount() == 0 }, then: {
			return 'spec_string_intern("\\n")';
		});

		# Type name introspection on class instances.
		Conditional:branch(check: { expr:methodName == 'typeName' && targetType != '' && !self:policy:isTransparent(c: cg:findClass(name: targetType)) && !self:allEnumNames:has(key: targetType) }, then: {
			return 'spec_type_name(' . targetC . ')';
		});

		# Int toBase conversion.
		Conditional:branch(check: { expr:methodName == 'toBase' && (targetType == Primitive:INT:value()) }, then: {
			local String is baseC: '10';
			local String is digitsC: '0';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:branch(check: { arg:name == 'base' }, then: {
 baseC: cg:generateExpression(expr: arg:value);
				});
				Conditional:branch(check: { arg:name == 'digits' }, then: {
 digitsC: cg:generateExpression(expr: arg:value);
				});
			});
			return 'spec_int_to_base(' . targetC . ', ' . baseC . ', ' . digitsC . ')';
		});

		# Parallel fan-out execution.
		Conditional:branch(check: { targetC == 'Parallel' && expr:methodName == 'run' && expr:argCount() >= 3 }, then: {
			local String is threadsC: '1';
			local String is iterC: '0';
			local String is workerC: 'NULL';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:branch(check: { arg:name == 'threads' }, then: {
 threadsC: cg:generateExpression(expr: arg:value);
				});
				Conditional:branch(check: { arg:name == 'iterations' }, then: {
 iterC: cg:generateExpression(expr: arg:value);
				});
				Conditional:branch(check: { arg:name == 'worker' }, then: {
 workerC: cg:generateExpression(expr: arg:value);
				});
			});
			return 'spec_parallel_run(' . threadsC . ', ' . iterC . ', (void*)(' . workerC . '))';
		});

		# Ansi terminal metrics.
		Conditional:branch(check: { targetC == 'Ansi' && expr:methodName == 'terminalWidth' }, then: {
			return 'spec_term_width()';
		});
		Conditional:branch(check: { targetC == 'Ansi' && expr:methodName == 'terminalHeight' }, then: {
			return 'spec_term_height()';
		});

		# Output:line and Output:print/write.
		Conditional:branch(check: { (targetC == 'Output') && expr:methodName == 'line' && expr:argCount() > 0 }, then: {
			local Expression is firstArg: self:argValue(expr: expr, index: 0);
			local String is valC: cg:generateExpression(expr: firstArg);
			local String is strC: cg:wrapToString(expr: firstArg, exprC: valC);
			return 'printf("%s\\n", spec_buf_to_cstring((SpecBuf*)(' . strC . ')))';
		});
		Conditional:branch(check: { (targetC == 'Output') && (expr:methodName == 'print' || expr:methodName == 'write') && expr:argCount() > 0 }, then: {
			local Expression is firstArg: self:argValue(expr: expr, index: 0);
			local String is valC: cg:generateExpression(expr: firstArg);
			local String is strC: cg:wrapToString(expr: firstArg, exprC: valC);
			return '({ printf("%s", spec_buf_to_cstring((SpecBuf*)(' . strC . '))); fflush(stdout); })';
		});

		# String:fromCharCode.
		Conditional:branch(check: { targetC == 'String' && expr:methodName == 'fromCharCode' && expr:argCount() > 0 }, then: {
			local Expression is codeArg: self:argValue(expr: expr, index: 0);
			local String is codeC: cg:generateExpression(expr: codeArg);
			return 'spec_string_from_char_code(' . codeC . ')';
		});

		# While:run / While:condition — the loop runners.
		Conditional:branch(check: { targetC == 'While' && expr:methodName == 'run' && expr:argCount() > 0 }, then: {
			local Expression is loopVal: self:argValue(expr: expr, index: 0);
			local String is loopC: cg:generateExpressionInner(expr: loopVal);
			local String is loopClass: cg:inferTargetType(expr: loopVal);
			Conditional:branch(check: { loopClass == '' && loopVal:kind == ExpressionKind:CALL }, then: {
				local Expression is mt: loopVal:methodTarget;
				loopClass: cg:generateExpression(expr: mt);
			});
			local String is ctrlC: 'NULL';
			Conditional:branch(check: { expr:argCount() > 1 }, then: {
				local Expression is ctrlArg: self:argValue(expr: expr, index: 1);
				ctrlC: cg:generateExpression(expr: ctrlArg);
			});
			local String is freeLoopC: '';
			Conditional:branch(check: { loopVal:kind == ExpressionKind:CALL && loopVal:methodName == 'init' }, then: {
				freeLoopC: ' spec_release(_lp);';
			});
			return '({ void* _lp = (void*)(' . loopC . '); SpecLoopControl* _ctrl = (SpecLoopControl*)(' . ctrlC . '); while (' . loopClass . '_evaluate((void*)_lp)) { if (!' . loopClass . '_iteration((void*)_lp, _ctrl) || (_ctrl && _ctrl->stopped)) break; } if (_ctrl && _ctrl->on_complete) { _ctrl->on_complete(_ctrl->callback, _ctrl); }' . freeLoopC . ' })';
		});
		Conditional:branch(check: { targetC == 'While' && (expr:methodName == 'condition' || expr:methodName == 'loop' || expr:methodName == 'init') }, then: {
			local Expression is varsExpr;
			local Expression is evalExpr;
			local Expression is iterExpr;
			local Boolean is hasVars: false;
			local Boolean is hasEval: false;
			local Boolean is hasIter: false;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:branch(check: { arg:name == 'evaluate' }, then: {
					evalExpr: arg:value;
					hasEval: true;
				}, otherwise: {
					Conditional:branch(check: { arg:name == 'iterate' || arg:name == 'iteration' }, then: {
						iterExpr: arg:value;
						hasIter: true;
					}, otherwise: {
						Conditional:branch(check: { arg:name == 'vars' || arg:name == 'state' }, then: {
							varsExpr: arg:value;
							hasVars: true;
						});
					});
				});
			});
			Conditional:branch(check: { !hasEval }, then: {
				Conditional:branch(check: { expr:argCount() >= 3 }, then: {
					evalExpr: self:argValue(expr: expr, index: 1);
					hasEval: true;
				}, otherwise: {
					Conditional:branch(check: { expr:argCount() >= 2 }, then: {
						evalExpr: self:argValue(expr: expr, index: 0);
						hasEval: true;
					});
				});
			});
			Conditional:branch(check: { !hasIter }, then: {
				Conditional:branch(check: { expr:argCount() >= 3 }, then: {
					iterExpr: self:argValue(expr: expr, index: 2);
					hasIter: true;
				}, otherwise: {
					Conditional:branch(check: { expr:argCount() >= 2 }, then: {
						iterExpr: self:argValue(expr: expr, index: 1);
						hasIter: true;
					});
				});
			});
			Conditional:branch(check: { !hasVars && expr:argCount() >= 3 }, then: {
				varsExpr: self:argValue(expr: expr, index: 0);
				hasVars: true;
			});
			Conditional:branch(check: { hasEval && hasIter && evalExpr:kind == ExpressionKind:ANON_FN && iterExpr:kind == ExpressionKind:ANON_FN }, then: {
				local Array of Parameter is loopVars: [];
				Conditional:branch(check: { hasVars && varsExpr:anonParams:length() > 0 }, then: {
					loopVars: varsExpr:anonParams;
				});
				return cg:generateInlineWhileLoop(loopVars: loopVars, evalExpr: evalExpr, iterExpr: iterExpr);
			});
		});

		# LoopControl methods: transparent runtime-managed objects — the
		# constructor wires the optional completion callback directly.
		Conditional:branch(check: { targetC == 'LoopControl' && expr:methodName == 'init' }, then: {
			Conditional:branch(check: { expr:argCount() == 0 }, then: {
				return 'LoopControl_new()';
			});
			local NamedArg is cbArg: expr:methodArgs:get(index: 0);
			local Expression is cbVal: cbArg:value;
			local String is cbC: cg:generateExpression(expr: cbVal);
			local String is cbClass: cg:inferTargetType(expr: cbVal);
			Conditional:branch(check: { cbClass == '' && cbVal:kind == ExpressionKind:CALL }, then: {
				local Expression is mt: cbVal:methodTarget;
				cbClass: cg:generateExpression(expr: mt);
			});
			return '({ SpecLoopControl* _c = LoopControl_new(); _c->callback = (void*)(' . cbC . '); _c->on_complete = (void (*)(void*, struct SpecLoopControl*))' . cbClass . '_onComplete; _c; })';
		});
		Conditional:branch(check: { expr:methodName == 'stop' && (targetC == 'LoopControl' || targetType == 'LoopControl') }, then: {
			return 'LoopControl_stop(' . targetC . ')';
		});

		# Input:prompt — inline getline driving the handler's onInput.
		Conditional:branch(check: { targetC == 'Input' && expr:methodName == 'prompt' && expr:argCount() > 0 }, then: {
			local Expression is handlerExpr: self:argValue(expr: expr, index: 0);
			local String is handlerC: cg:generateExpression(expr: handlerExpr);
			local String is handlerClass: cg:inferTargetType(expr: handlerExpr);
			Conditional:branch(check: { handlerClass == '' && handlerExpr:kind == ExpressionKind:CALL }, then: {
				local Expression is mt: handlerExpr:methodTarget;
				handlerClass: cg:generateExpression(expr: mt);
			});
			return "({ char* _line = NULL; size_t _line_cap = 0; char* _res = \"\"; ssize_t _n = getline(&_line, &_line_cap, stdin); if (_n >= 0) { if (_n > 0 && _line[_n - 1] == '\\n') _line[_n - 1] = '\\0'; _res = strdup(_line); } free(_line); " . handlerClass . '_onInput((void*)(' . handlerC . '), spec_string_from_chars(_res)); })';
		});

		# Process methods.
		Conditional:branch(check: { targetC == 'Process' }, then: {
			Conditional:branch(check: { expr:methodName == 'execute' }, then: {
				local String is cmdC: '0';
				local Array of String is argList: [];
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					argList:add(item: cg:generateExpression(expr: arg:value));
				});
				argList:each(action: local Function(String is a){
					Conditional:branch(check: { cmdC == '0' }, then: {
 cmdC: a;
					}, otherwise: {
 cmdC: cmdC . ', ' . a;
					});
				});
				return 'spec_process_execute(' . cmdC . ')';
			});
			Conditional:branch(check: { expr:methodName == 'sleep' }, then: {
				local Expression is msArg: self:argValue(expr: expr, index: 0);
				local String is msC: cg:generateExpression(expr: msArg);
				return 'spec_process_sleep(' . msC . ')';
			});
			Conditional:branch(check: { expr:methodName == 'getPid' }, then: {
				return 'spec_process_get_pid()';
			});
			Conditional:branch(check: { expr:methodName == 'clockMs' }, then: {
				return 'spec_clock_ms()';
			});
			Conditional:branch(check: { expr:methodName == 'peakMemoryKb' }, then: {
				return 'spec_mem_peak_kb()';
			});
			Conditional:branch(check: { expr:methodName == 'threadCount' }, then: {
				return 'spec_thread_count()';
			});
			Conditional:branch(check: { expr:methodName == 'exit' }, then: {
				local Expression is codeArg: self:argValue(expr: expr, index: 0);
				local String is codeC: cg:generateExpression(expr: codeArg);
				return 'exit(' . codeC . ')';
			});
			Conditional:branch(check: { expr:methodName == 'atomicAdd' || expr:methodName == 'atomicPut' || expr:methodName == 'atomicGet' }, then: {
				local String is argsCs: '';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { argsCs != '' }, then: {
 argsCs: argsCs . ', ';
					});
					argsCs: argsCs . cg:generateExpression(expr: arg:value);
				});
				local String is fn: 'spec_atomic_get';
				Conditional:branch(check: { expr:methodName == 'atomicAdd' }, then: {
 fn: 'spec_atomic_add';
				});
				Conditional:branch(check: { expr:methodName == 'atomicPut' }, then: {
 fn: 'spec_atomic_put';
				});
				return fn . '(' . argsCs . ')';
			});
		});

		# File methods.
		Conditional:branch(check: { targetC == 'File' }, then: {
			Conditional:branch(check: { expr:methodName == 'exists' }, then: {
				local Expression is pArg: self:argValue(expr: expr, index: 0);
				local String is pC: cg:generateExpression(expr: pArg);
				return 'spec_file_exists(' . pC . ')';
			});
			Conditional:branch(check: { expr:methodName == 'read' }, then: {
				local String is pathC: 'spec_string_intern("")';
				local String is defC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'path' }, then: {
 pathC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'onSuccess' }, then: {
 onSuccC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'onError' }, then: {
 onErrC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_file_read(' . pathC . ', ' . defC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			});
			Conditional:branch(check: { expr:methodName == 'readAsync' }, then: {
				local String is pathC: 'spec_string_intern("")';
				local String is defC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'path' }, then: {
 pathC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'onSuccess' }, then: {
 onSuccC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'onError' }, then: {
 onErrC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_file_read_async(' . pathC . ', ' . defC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			});
			Conditional:branch(check: { expr:methodName == 'writeAsync' }, then: {
				local String is pathC: 'spec_string_intern("")';
				local String is contentC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'path' }, then: {
 pathC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'content' }, then: {
 contentC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'onSuccess' }, then: {
 onSuccC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'onError' }, then: {
 onErrC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_file_write_async(' . pathC . ', ' . contentC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			});
			Conditional:branch(check: { expr:methodName == 'write' }, then: {
				local String is pathC: 'spec_string_intern("")';
				local String is contentC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'path' }, then: {
 pathC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'content' }, then: {
 contentC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'onSuccess' }, then: {
 onSuccC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'onError' }, then: {
 onErrC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_file_write(' . pathC . ', ' . contentC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			});
			Conditional:branch(check: { expr:methodName == 'remove' }, then: {
				local Expression is pArg: self:argValue(expr: expr, index: 0);
				local String is pC: cg:generateExpression(expr: pArg);
				return 'spec_file_remove(' . pC . ')';
			});
		});

		# Math functions.
		# Stderr:print.
		Conditional:branch(check: { targetC == 'Stderr' && expr:methodName == 'print' && expr:argCount() > 0 }, then: {
			local Expression is seArg: self:argValue(expr: expr, index: 0);
			local String is seValC: cg:generateExpression(expr: seArg);
			local String is seStrC: cg:wrapToString(expr: seArg, exprC: seValC);
			return '({ fprintf(stderr, "%s", spec_buf_to_cstring((SpecBuf*)(' . seStrC . '))); })';
		});

		# Math functions.
		Conditional:branch(check: { targetC == 'Math' }, then: {
			local String is m: expr:methodName;
			local String is a0: '0.0';
			Conditional:branch(check: { expr:argCount() > 0 }, then: {
				a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
			});
			# Single-operand functions.
			when (m) {
				is 'round': { return 'spec_math_round(' . a0 . ')'; }
				is 'floor': { return 'spec_math_floor(' . a0 . ')'; }
				is 'ceil', 'ceiling': { return 'spec_math_ceil(' . a0 . ')'; }
				is 'abs': {
					# FUNCTIONS.md §I.4: type-distinct overloads — the Int
					# overload routes to the integer floor.
					Conditional:branch(check: { self:absArgIsInt(expr: expr, cg: cg) }, then: {
						return 'spec_math_abs_int(' . a0 . ')';
					});
					return 'spec_math_abs(' . a0 . ')';
				}
				is 'sqrt': { return 'spec_math_sqrt(' . a0 . ')'; }
				is 'sin': { return 'spec_math_sin(' . a0 . ')'; }
				is 'cos': { return 'spec_math_cos(' . a0 . ')'; }
				is 'tan': { return 'spec_math_tan(' . a0 . ')'; }
				is 'log': { return 'spec_math_log(' . a0 . ')'; }
				is 'log2': { return 'spec_math_log2(' . a0 . ')'; }
				is 'fastRandom': { return 'spec_fast_random()'; }
				else: {}
			}
			# Two-operand functions: a + b, or named value/min/max.
			local String is a1: '0.0';
			Conditional:branch(check: { expr:argCount() > 1 }, then: {
				a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
			});
			Conditional:branch(check: { m == 'min' }, then: {
				return 'spec_math_min(' . a0 . ', ' . a1 . ')';
			});
			Conditional:branch(check: { m == 'max' }, then: {
				return 'spec_math_max(' . a0 . ', ' . a1 . ')';
			});
			Conditional:branch(check: { m == 'pow' }, then: {
				return 'spec_math_pow(' . a0 . ', ' . a1 . ')';
			});
			Conditional:branch(check: { m == 'atan2' }, then: {
				return 'spec_math_atan2(' . a0 . ', ' . a1 . ')';
			});
			Conditional:branch(check: { m == 'random' }, then: {
				return 'spec_math_random(' . a0 . ', ' . a1 . ')';
			});
			Conditional:branch(check: { m == 'clamp' }, then: {
				local String is vC: '0.0';
				local String is loC: '0.0';
				local String is hiC: '1.0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'value' }, then: {
 vC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'min' || arg:name == 'lo' }, then: {
 loC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'max' || arg:name == 'hi' }, then: {
 hiC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_math_clamp(' . vC . ', ' . loC . ', ' . hiC . ')';
			});
			Conditional:branch(check: { m == 'toInt' }, then: {
				return '((long long)(' . a0 . '))';
			});
			Conditional:branch(check: { m == 'toFloat' }, then: {
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
		Conditional:branch(check: { isArr }, then: {
			local String is arrC: self:bindContainerCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			Conditional:branch(check: { arrC != '' }, then: {
				return arrC;
			});
		});

		# Map literal-constructor + concrete getters + inline each.
		Conditional:branch(check: { targetC == 'Map' || targetType == 'Map' || targetType:startsWith(prefix: 'Map:') }, then: {
			local String is mapC: self:bindMapCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			Conditional:branch(check: { mapC != '' }, then: {
				return mapC;
			});
		});

		# String instance methods: direct dispatch to compiled bodies.
		Conditional:branch(check: { targetType == 'String' }, then: {
			local String is ddC: self:bindStringDirect(expr: expr, targetC: targetC, cg: cg);
			Conditional:branch(check: { ddC != '' }, then: {
				return ddC;
			});
		});

		# Enum values()/of()/name()/value()/ordinal().
		Conditional:branch(check: { self:allEnumNames:has(key: targetC) && expr:methodName == 'values' }, then: {
			return targetC . '_values()';
		});
		Conditional:branch(check: { self:allEnumNames:has(key: targetC) && expr:methodName == 'of' && expr:argCount() > 0 }, then: {
			local Expression is vArg: self:argValue(expr: expr, index: 0);
			return targetC . '_of(' . cg:generateExpression(expr: vArg) . ')';
		});
		Conditional:branch(check: { self:allEnumNames:has(key: targetType) }, then: {
			Conditional:branch(check: { expr:methodName == 'name' }, then: {
				return targetType . '_name(' . targetC . ')';
			});
			Conditional:branch(check: { expr:methodName == 'value' }, then: {
				return targetType . '_value(' . targetC . ')';
			});
			Conditional:branch(check: { expr:methodName == 'ordinal' }, then: {
				return targetType . '_ordinal(' . targetC . ')';
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
		Conditional:branch(check: { expr:argCount() > 0 }, then: {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		});
		local String is a1: '';
		Conditional:branch(check: { expr:argCount() > 1 }, then: {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		});
		# Array methods (SpecArray*). Named-arg extraction.
		Conditional:branch(check: { targetType:startsWith(prefix: 'Array') }, then: {
			Conditional:branch(check: { m == 'get' }, then: {
				local String is idxC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_array_get(' . targetC . ', ' . idxC . ')';
			});
			Conditional:branch(check: { m == 'set' }, then: {
				local String is idxC: '0';
				local String is itemC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'item' || arg:name == 'value' }, then: {
 itemC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'spec_array_set(' . targetC . ', ' . idxC . ', (void*)(intptr_t)(' . itemC . '))';
			});
			Conditional:branch(check: { m == 'add' }, then: {
				local String is itemC: 'NULL';
				Conditional:branch(check: { expr:argCount() > 0 }, then: {
					local Expression is valExpr: self:argValue(expr: expr, index: 0);
					Conditional:branch(check: { valExpr:kind == ExpressionKind:ARRAY }, then: {
						cg:setContainerHint(t: targetType);
						itemC: cg:generateExpression(expr: valExpr);
						return 'spec_array_add_array(' . targetC . ', ' . itemC . ')';
					});
					local Boolean is savedArgMode: cg:argMode;
					cg:setArgMode(m: false);
					itemC: cg:generateExpression(expr: valExpr);
					cg:setArgMode(m: savedArgMode);
				});
				local String is elemKindA: cg:containerElemKind(containerType: targetType);
				local String is addFn: 'spec_array_add';
				Conditional:branch(check: { elemKindA == 'object' }, then: {
					addFn: 'spec_array_add_object';
				});
				return addFn . '(' . targetC . ', (void*)(' . itemC . '))';
			});
			Conditional:branch(check: { m == 'length' }, then: {
				return 'spec_array_length(' . targetC . ')';
			});
			Conditional:branch(check: { m == 'pop' }, then: {
				local String is defC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'default' }, then: {
						local String is rawDefC: cg:generateExpression(expr: arg:value);
						Conditional:branch(check: { targetType:startsWith(prefix: 'Array:String') }, then: {
							defC: rawDefC;
						}, otherwise: {
							defC: '(void*)(intptr_t)(' . rawDefC . ')';
						});
					});
				});
				return 'spec_array_pop(' . targetC . ', ' . defC . ')';
			});
			Conditional:branch(check: { m == 'removeAt' }, then: {
				local String is idxC: '0';
				local String is defC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'default' }, then: {
 defC: '(void*)(intptr_t)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_array_remove_at(' . targetC . ', ' . idxC . ', ' . defC . ')';
			});
			Conditional:branch(check: { m == 'isEmpty' }, then: {
				return '(long long)(spec_array_length(' . targetC . ') == 0)';
			});
			Conditional:branch(check: { m == 'slice' }, then: {
				local String is startC: '0';
				local String is endC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'start' }, then: {
 startC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'end' }, then: {
 endC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'Array_slice(' . targetC . ', ' . startC . ', ' . endC . ')';
			});
			Conditional:branch(check: { m == 'clear' }, then: {
				return 'spec_array_clear(' . targetC . ')';
			});
			Conditional:branch(check: { m == 'indexOf' }, then: {
				local String is searchC: '""';
				local String is defC: '-1';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'search' || arg:name == 'needle' }, then: {
 searchC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'Array_indexOf(' . targetC . ', ' . searchC . ', ' . defC . ')';
			});
			# Higher-order: anon functions inline as loops; values as callbacks.
			Conditional:branch(check: { m == 'each' }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'each', targetC: targetC, fnExpr: fnExpr);
			});
			Conditional:branch(check: { m == 'filter' }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'filter', targetC: targetC, fnExpr: fnExpr);
			});
			Conditional:branch(check: { m == 'count' }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'count', targetC: targetC, fnExpr: fnExpr);
			});
			Conditional:branch(check: { m == 'any' }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				return cg:generateInlineArrayOp(mode: 'any', targetC: targetC, fnExpr: fnExpr);
			});
			Conditional:branch(check: { m == 'map' }, then: {
				Conditional:branch(check: { expr:argCount() > 0 }, then: {
					local Expression is fnExpr: self:argValue(expr: expr, index: 0);
					Conditional:branch(check: { fnExpr:kind == ExpressionKind:ANON_FN }, then: {
						return cg:generateInlineArrayOp(mode: 'map', targetC: targetC, fnExpr: fnExpr);
					});
				});
			});
			Conditional:branch(check: { m == 'fold' }, then: {
				Conditional:branch(check: { expr:argCount() >= 2 }, then: {
					local Expression is initExpr: self:argValue(expr: expr, index: 0);
					local Expression is fnExpr: self:argValue(expr: expr, index: 1);
					Conditional:branch(check: { fnExpr:kind == ExpressionKind:ANON_FN }, then: {
						return cg:generateInlineArrayFold(targetC: targetC, initExpr: initExpr, fnExpr: fnExpr);
					});
				});
			});
			Conditional:branch(check: { m == 'join' }, then: {
				local String is sepC: '""';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'separator' || sepC == '""' }, then: {
 sepC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'Array_join(' . targetC . ', ' . sepC . ')';
			});
		});
		# List methods ([Byte] byte-buffer shape; pointer-vector shapes below).
		Conditional:branch(check: { targetType == 'List:Byte' || targetType == 'List of Byte' }, then: {
			local String is errC: 'spec_noop_closure()';
			Conditional:branch(check: { m == 'get' || m == 'pop' || m == 'set' }, then: {
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'error' }, then: {
						errC: cg:generateExpression(expr: arg:value);
					});
				});
			});
			Conditional:branch(check: { m == 'push' }, then: {
				local String is itemC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					itemC: cg:generateExpression(expr: arg:value);
				});
				return 'spec_bytebuffer_push(' . targetC . ', (long long)(' . itemC . '))';
			});
			Conditional:branch(check: { m == 'appendString' }, then: {
				local String is sC: 'spec_string_intern("")';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					sC: cg:generateExpression(expr: arg:value);
				});
				return 'spec_bytebuffer_append_string(' . targetC . ', spec_buf_to_cstring((SpecBuf*)(' . sC . ')))';
			});
			Conditional:branch(check: { m == 'get' }, then: {
				local String is idxC: '0';
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'default' }, then: {
 defC: '(long long)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_bytebuffer_get(' . targetC . ', ' . idxC . ', ' . defC . ', ' . errC . ')';
			});
			Conditional:branch(check: { m == 'set' }, then: {
				local String is idxC: '0';
				local String is itemC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'item' || arg:name == 'value' }, then: {
 itemC: '(long long)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_bytebuffer_set(' . targetC . ', ' . idxC . ', ' . itemC . ', ' . errC . ')';
			});
			Conditional:branch(check: { m == 'pop' }, then: {
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'default' }, then: {
 defC: '(long long)(' . cg:generateExpression(expr: arg:value) . ')';
					});
				});
				return 'spec_bytebuffer_pop(' . targetC . ', ' . defC . ', ' . errC . ')';
			});
			Conditional:branch(check: { m == 'length' }, then: {
				return 'spec_bytebuffer_length(' . targetC . ')';
			});
			Conditional:branch(check: { m == 'clear' }, then: {
				return 'spec_bytebuffer_clear(' . targetC . ')';
			});
			Conditional:branch(check: { m == 'toString' }, then: {
				return 'spec_bytebuffer_to_string(' . targetC . ')';
			});
		});

		# List methods (pointer-vector shapes, element-kind casts).
		Conditional:branch(check: { targetType:startsWith(prefix: 'List') }, then: {
			local String is listElem: '';
			Conditional:branch(check: { targetType:startsWith(prefix: 'List of ') && targetType:length() > 7 }, then: {
				listElem: targetType:substring(start: 7, end: targetType:length());
			}, otherwise: {
				Conditional:branch(check: { targetType:startsWith(prefix: 'List:') && targetType:length() > 5 }, then: {
					listElem: targetType:substring(start: 5, end: targetType:length());
				});
			});
			local String is elemKind: cg:containerElemKind(containerType: targetType);
			local String is itemPre: '(void*)(intptr_t)(';
			local String is itemPost: ')';
			local String is resCast: '(long long)(intptr_t)';
			Conditional:branch(check: { elemKind == 'string' }, then: {
				itemPre: '(void*)(';
				resCast: '(String)';
			}, otherwise: {
				Conditional:branch(check: { elemKind == 'object' }, then: {
					itemPre: '(void*)(';
					resCast: '(' . cg:cTypeFor(typeName: listElem) . ')(intptr_t)';
				});
			});
			local String is errC: 'spec_noop_closure()';
			Conditional:branch(check: { m == 'get' || m == 'pop' || m == 'set' }, then: {
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'error' }, then: {
						errC: cg:generateExpression(expr: arg:value);
					});
				});
			});
			Conditional:branch(check: { m == 'push' }, then: {
				local String is itemC: '0';
				local Boolean is savedArgV: cg:argMode;
				cg:setArgMode(m: false);
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					itemC: cg:generateExpression(expr: arg:value);
				});
				cg:setArgMode(m: savedArgV);
				return 'spec_vec_push(' . targetC . ', ' . itemPre . itemC . itemPost . ')';
			});
			Conditional:branch(check: { m == 'get' }, then: {
				local String is idxC: '0';
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
				});
				return resCast . 'spec_vec_get(' . targetC . ', ' . idxC . ', ' . itemPre . defC . itemPost . ', ' . errC . ')';
			});
			Conditional:branch(check: { m == 'set' }, then: {
				local String is idxC: '0';
				local String is itemC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'index' }, then: {
 idxC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'item' || arg:name == 'value' }, then: {
						local Boolean is savedArgS: cg:argMode;
						cg:setArgMode(m: false);
						itemC: cg:generateExpression(expr: arg:value);
						cg:setArgMode(m: savedArgS);
					});
				});
				return 'spec_vec_set(' . targetC . ', ' . idxC . ', ' . itemPre . itemC . itemPost . ', ' . errC . ')';
			});
			Conditional:branch(check: { m == 'pop' }, then: {
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
				});
				return resCast . 'spec_vec_pop(' . targetC . ', ' . itemPre . defC . itemPost . ', ' . errC . ')';
			});
			Conditional:branch(check: { m == 'length' }, then: {
				return 'spec_vec_length(' . targetC . ')';
			});
			Conditional:branch(check: { m == 'clear' }, then: {
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
		Conditional:branch(check: { expr:argCount() > 0 }, then: {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		});
		local String is a1: '';
		Conditional:branch(check: { expr:argCount() > 1 }, then: {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		});
		Conditional:branch(check: { m == 'init' }, then: {
			return 'spec_map_new()';
		});
		Conditional:branch(check: { m == 'set' }, then: {
			# String values store directly; everything else boxes into the
			# any-slot via spec_map_set_any.
			local String is keyC: 'spec_string_intern("")';
			local String is valC: 'spec_string_intern("")';
			local Boolean is valIsStr: true;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:branch(check: { arg:name == 'key' }, then: {
 keyC: cg:generateExpression(expr: arg:value);
				});
				Conditional:branch(check: { arg:name == 'value' }, then: {
					local Boolean is savedArgMode: cg:argMode;
					cg:setArgMode(m: false);
					valC: cg:generateExpression(expr: arg:value);
					cg:setArgMode(m: savedArgMode);
					valIsStr: cg:isStringExpr(expr: arg:value, exprC: valC);
				});
			});
			Conditional:branch(check: { targetType:contains(needle: 'String:String') || targetType:contains(needle: 'to String') || valIsStr }, then: {
				return 'spec_map_set(' . targetC . ', ' . keyC . ', ' . valC . ')';
			});
			return 'spec_map_set_any(' . targetC . ', ' . keyC . ', (void*)(intptr_t)(' . valC . '))';
		});
		Conditional:branch(check: { m == 'get' }, then: {
			return 'spec_map_get(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		Conditional:branch(check: { m == 'getString' }, then: {
			return '(String)spec_map_get(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		Conditional:branch(check: { m == 'getInt' }, then: {
			return 'Map_getInt(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		Conditional:branch(check: { m == 'getFloat' }, then: {
			return '((double)spec_map_get(' . targetC . ', ' . a0 . ', (void*)0))';
		});
		Conditional:branch(check: { m == 'getBool' }, then: {
			return 'Map_getBool(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		});
		Conditional:branch(check: { m == 'has' }, then: {
			return 'spec_map_has(' . targetC . ', ' . a0 . ')';
		});
		Conditional:branch(check: { m == 'remove' }, then: {
			return 'spec_map_remove(' . targetC . ', ' . a0 . ')';
		});
		Conditional:branch(check: { m == 'keys' }, then: {
			return 'spec_map_keys(' . targetC . ')';
		});
		Conditional:branch(check: { m == 'length' }, then: {
			return '(long long)spec_map_length(' . targetC . ')';
		});
		Conditional:branch(check: { m == 'each' }, then: {
			Conditional:branch(check: { expr:argCount() > 0 }, then: {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				Conditional:branch(check: { fnExpr:kind == ExpressionKind:ANON_FN }, then: {
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
		Conditional:branch(check: { expr:argCount() > 0 }, then: {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		});
		local String is a1: '';
		Conditional:branch(check: { expr:argCount() > 1 }, then: {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		});
		when (m) {
			is 'length': { return 'spec_string_length(' . targetC . ')'; }
			is 'charAt': { return 'String_charAt(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
			is 'substring': { return 'spec_string_substring(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
			is 'indexOf': { return 'spec_string_index_of(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
			is 'trim': { return 'String_trim(' . targetC . ')'; }
			is 'isDigit': { return 'String_isDigit(' . targetC . ')'; }
			is 'isAlpha': { return 'String_isAlpha(' . targetC . ')'; }
			is 'isWhitespace': { return 'String_isWhitespace(' . targetC . ')'; }
			is 'countLeading': { return 'String_countLeading(' . targetC . ', ' . a0 . ')'; }
			is 'split': { return 'String_split(' . targetC . ', ' . a0 . ')'; }
			is 'lines': { return 'String_lines(' . targetC . ')'; }
			is 'contains': { return 'String_contains(' . targetC . ', ' . a0 . ')'; }
			is 'startsWith': { return 'String_startsWith(' . targetC . ', ' . a0 . ')'; }
			is 'endsWith': { return 'String_endsWith(' . targetC . ', ' . a0 . ')'; }
			is 'replaceAll': { return 'String_replaceAll(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
			is 'parseInt': {
				local String is baseC: '10';
				local String is defC: '-1';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:branch(check: { arg:name == 'base' }, then: {
 baseC: cg:generateExpression(expr: arg:value);
					});
					Conditional:branch(check: { arg:name == 'default' }, then: {
 defC: cg:generateExpression(expr: arg:value);
					});
				});
				return 'String_parseInt(' . targetC . ', ' . baseC . ', ' . defC . ')';
			}
			else: { return ''; }
		}
	}
}
