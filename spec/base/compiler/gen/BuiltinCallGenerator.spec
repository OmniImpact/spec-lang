#! Package base:compiler:gen
#! Translates standard-library and runtime builtin method calls into C11
#! runtime functions.
##
## TRANSITIONAL (TRANSITION.md section 3): this class is the fossil's
## interception surface, ported. Every branch here dies when the floor
## classes are reimplemented in Spec over the sysinternal primitives. The
## sysinternal namespace-binding block at the top is the replacement
## mechanism, already live.

Class is BuiltinCallGenerator{
	namespace: ['base', 'compiler', 'gen'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'ast', Type],
		['spec', 'base', 'compiler', 'ast', Primitive],
		['spec', 'base', 'compiler', 'ast', Expression],
		['spec', 'base', 'compiler', 'ast', ExpressionKind],
		['spec', 'base', 'compiler', 'ast', NamedArg],
		['spec', 'base', 'compiler', 'ast', Parameter],
		['spec', 'base', 'compiler', 'ast', Member],
		['spec', 'base', 'compiler', 'ast', MemberKind],
		['spec', 'base', 'compiler', 'ast', ClassInfo],
		['spec', 'base', 'compiler', WellKnown],
		['spec', 'base', 'compiler', 'gen', CBackendUtils],
		['spec', 'base', 'compiler', 'gen', EmissionPolicy],
		['lib', 'base', 'struct', Array],
		['lib', 'base', 'struct', Map],
		['lib', 'base', 'iterator']
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
		if (fCls:name == '') {
			return '';
		}
		local Member is foundM;
		local Boolean is hasM: false;
		fCls:members:each(action: local Function(Member is m){
			if (!hasM && m:kind == MemberKind:METHOD && m:name == expr:methodName) {
				hasM: true;
				foundM: m;
			}
		});
		if (!hasM) {
			return '';
		}
		local Array of String is argList: [];
		local Boolean is argsOk: true;
		local Int is posIdx: 0;
		foundM:params:each(action: local Function(Parameter is p){
			if (argsOk) {
				local Boolean is got: false;
				local Expression is posArg: expr:argValue(index: posIdx);
				if (posIdx < expr:argCount() && expr:argName(index: posIdx) == '') {
					argList:add(item: cg:generateExpression(expr: posArg));
					posIdx: posIdx + 1;
					got: true;
				}
				if (!got) {
					expr:methodArgs:each(action: local Function(NamedArg is a){
						if (!got && a:name == p:name) {
							got: true;
							argList:add(item: cg:generateExpression(expr: a:value));
						}
					});
				}
				if (!got && p:hasDefault) {
					got: true;
					argList:add(item: cg:generateExpression(expr: p:defaultExpr));
				}
				if (!got) {
					argsOk: false;
				}
			}
		});
		if (!argsOk) {
			return '';
		}
		local String is argCs: '';
		argList:each(action: local Function(String is a){
			if (argCs == '') {
				argCs: a;
			} else {
				argCs: argCs . ', ' . a;
			}
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
	## @param targetType: Inferred type of the target.
	## @param cg: The code generator.
	## @return: C call string, or '' when not builtin.
	Function of String is generateBuiltinCall(Expression is expr, String is targetC, String is targetType, CodeGenerator is cg){
		# error:line - diagnostics to stderr
		if ((targetC == 'error' || targetC == 'Error') && expr:methodName == 'line' && expr:argCount() > 0) {
			local Expression is errArg: self:argValue(expr: expr, index: 0);
			local String is errValC: cg:generateExpression(expr: errArg);
			local String is errStrC: cg:wrapToString(expr: errArg, exprC: errValC);
			return 'spec_error_line(' . errStrC . ')';
		}

		# Reflection:class()/method() — compile-time source identity,
		# injected at the call site. Matches the bare usage form AND the
		# qualified floor chain (the base:sys wrapper delegates by chain;
		# user code hits the bare interception first).
		local Boolean is isReflTarget: targetC == 'Reflection';
		if (!isReflTarget && expr:methodTarget:kind == ExpressionKind:PATH) {
			local String is rJoined: '';
			expr:methodTarget:pathSegments:each(action: local Function(String is seg){
				if (rJoined == '') {
					rJoined: seg;
				} else {
					rJoined: rJoined . ':' . seg;
				}
			});
			if (rJoined:endsWith(suffix: ':sysinternal:Reflection')) {
				isReflTarget: true;
			}
		}
		if (isReflTarget && expr:methodName == 'class' && expr:argCount() == 0) {
			return 'spec_string_intern("' . cg:currentClassName . '")';
		}
		if (isReflTarget && expr:methodName == 'method' && expr:argCount() == 0) {
			return 'spec_string_intern("' . cg:currentMethodName . '")';
		}

		# Namespace-driven sysinternal floor binding: a call on a class whose
		# namespace ends with `sysinternal` compiles to spec_<snake(method)>.
		local String is floorCls: '';
		local ClassInfo is tc: cg:findClass(name: targetC);
		if (targetC != '' && tc:name == targetC && cg:isSysinternalClass(name: targetC)) {
			floorCls: targetC;
		} else {
			local String is qCls: '';
			if (expr:methodTarget:kind == ExpressionKind:PATH) {
				local Array of String is qSegs: expr:methodTarget:pathSegments;
				qCls: qSegs:get(index: qSegs:length() - 1);
				# Qualified chains ('base:sysinternal:Buf') resolve by full
				# namespace path so the floor never collides with its
				# same-name base:sys wrapper.
				local String is qJoined: '';
				qSegs:each(action: local Function(String is seg){
					if (qJoined == '') {
						qJoined: seg;
					} else {
						qJoined: qJoined . ':' . seg;
					}
				});
				if (qJoined:contains(needle: ':sysinternal:')) {
					qCls: qJoined;
				}
			} else if (expr:methodTarget:kind == ExpressionKind:CALL) {
				local Expression is qInner: expr:methodTarget;
				if (qInner:methodTarget:kind == ExpressionKind:PATH) {
					qCls: qInner:methodName;
				}
			}
			local ClassInfo is qc: cg:findClass(name: qCls);
			if (qCls != '' && qc:name != '' && (qc:name == qCls || (qc:namespaceJoined() . ':' . qc:name) == qCls) && cg:isSysinternalClass(name: qCls)) {
				floorCls: qCls;
			}
		}
		if (floorCls != '') {
			local String is bound: self:bindFloorCall(clsName: floorCls, expr: expr, cg: cg);
			if (bound != '') {
				return bound;
			}
		}

		# String:newline() — the newline constant.
		if (targetC == 'String' && expr:methodName == 'newline' && expr:argCount() == 0) {
			return 'spec_string_intern("\\n")';
		}

		# Type name introspection on class instances.
		if (expr:methodName == 'typeName' && targetType != '' && !self:policy:isTransparent(c: cg:findClass(name: targetType)) && !self:allEnumNames:has(key: targetType)) {
			return 'spec_type_name(' . targetC . ')';
		}

		# Int toBase conversion.
		if (expr:methodName == 'toBase' && (targetType == Primitive:INT:value())) {
			local String is baseC: '10';
			local String is digitsC: '0';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:name == 'base') { baseC: cg:generateExpression(expr: arg:value); }
				if (arg:name == 'digits') { digitsC: cg:generateExpression(expr: arg:value); }
			});
			return 'spec_int_to_base(' . targetC . ', ' . baseC . ', ' . digitsC . ')';
		}

		# Parallel fan-out execution.
		if (targetC == 'Parallel' && expr:methodName == 'run' && expr:argCount() >= 3) {
			local String is threadsC: '1';
			local String is iterC: '0';
			local String is workerC: 'NULL';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:name == 'threads') { threadsC: cg:generateExpression(expr: arg:value); }
				if (arg:name == 'iterations') { iterC: cg:generateExpression(expr: arg:value); }
				if (arg:name == 'worker') { workerC: cg:generateExpression(expr: arg:value); }
			});
			return 'spec_parallel_run(' . threadsC . ', ' . iterC . ', (void*)(' . workerC . '))';
		}

		# Ansi terminal metrics.
		if (targetC == 'Ansi' && expr:methodName == 'terminalWidth') {
			return 'spec_term_width()';
		}
		if (targetC == 'Ansi' && expr:methodName == 'terminalHeight') {
			return 'spec_term_height()';
		}

		# Output:line and Output:print/write.
		if ((targetC == 'output' || targetC == 'Output') && expr:methodName == 'line' && expr:argCount() > 0) {
			local Expression is firstArg: self:argValue(expr: expr, index: 0);
			local String is valC: cg:generateExpression(expr: firstArg);
			local String is strC: cg:wrapToString(expr: firstArg, exprC: valC);
			return 'printf("%s\\n", spec_buf_to_cstring((SpecBuf*)(' . strC . ')))';
		}
		if ((targetC == 'output' || targetC == 'Output') && (expr:methodName == 'print' || expr:methodName == 'write') && expr:argCount() > 0) {
			local Expression is firstArg: self:argValue(expr: expr, index: 0);
			local String is valC: cg:generateExpression(expr: firstArg);
			local String is strC: cg:wrapToString(expr: firstArg, exprC: valC);
			return '({ printf("%s", spec_buf_to_cstring((SpecBuf*)(' . strC . '))); fflush(stdout); })';
		}

		# String:fromCharCode.
		if (targetC == 'String' && expr:methodName == 'fromCharCode' && expr:argCount() > 0) {
			local Expression is codeArg: self:argValue(expr: expr, index: 0);
			local String is codeC: cg:generateExpression(expr: codeArg);
			return 'spec_string_from_char_code(' . codeC . ')';
		}

		# While:run / While:condition — the loop runners.
		if (targetC == 'While' && expr:methodName == 'run' && expr:argCount() > 0) {
			local Expression is loopVal: self:argValue(expr: expr, index: 0);
			local String is loopC: cg:generateExpressionInner(expr: loopVal);
			local String is loopClass: cg:inferTargetType(expr: loopVal);
			if (loopClass == '' && loopVal:kind == ExpressionKind:CALL) {
				local Expression is mt: loopVal:methodTarget;
				loopClass: cg:generateExpression(expr: mt);
			}
			local String is ctrlC: 'NULL';
			if (expr:argCount() > 1) {
				local Expression is ctrlArg: self:argValue(expr: expr, index: 1);
				ctrlC: cg:generateExpression(expr: ctrlArg);
			}
			local String is freeLoopC: '';
			if (loopVal:kind == ExpressionKind:CALL && loopVal:methodName == 'init') {
				freeLoopC: ' spec_release(_lp);';
			}
			return '({ void* _lp = (void*)(' . loopC . '); SpecLoopControl* _ctrl = (SpecLoopControl*)(' . ctrlC . '); while (' . loopClass . '_evaluate((void*)_lp)) { if (!' . loopClass . '_iteration((void*)_lp, _ctrl) || (_ctrl && _ctrl->stopped)) break; } if (_ctrl && _ctrl->on_complete) { _ctrl->on_complete(_ctrl->callback, _ctrl); }' . freeLoopC . ' })';
		}
		if (targetC == 'While' && expr:methodName == 'condition' && expr:argCount() >= 2) {
			local Expression is evalExpr: self:argValue(expr: expr, index: 0);
			local Expression is iterExpr: self:argValue(expr: expr, index: 1);
			if (evalExpr:kind == ExpressionKind:ANON_FN && iterExpr:kind == ExpressionKind:ANON_FN) {
				return cg:generateInlineWhileCondition(evalExpr: evalExpr, iterExpr: iterExpr);
			}
		}

		# LoopControl methods: transparent runtime-managed objects — the
		# constructor wires the optional completion callback directly.
		if (targetC == 'LoopControl' && expr:methodName == 'init') {
			if (expr:argCount() == 0) {
				return 'LoopControl_new()';
			}
			local NamedArg is cbArg: expr:methodArgs:get(index: 0);
			local Expression is cbVal: cbArg:value;
			local String is cbC: cg:generateExpression(expr: cbVal);
			local String is cbClass: cg:inferTargetType(expr: cbVal);
			if (cbClass == '' && cbVal:kind == ExpressionKind:CALL) {
				local Expression is mt: cbVal:methodTarget;
				cbClass: cg:generateExpression(expr: mt);
			}
			return '({ SpecLoopControl* _c = LoopControl_new(); _c->callback = (void*)(' . cbC . '); _c->on_complete = (void (*)(void*, struct SpecLoopControl*))' . cbClass . '_onComplete; _c; })';
		}
		if (expr:methodName == 'stop' && (targetC == 'LoopControl' || targetType == 'LoopControl')) {
			return 'LoopControl_stop(' . targetC . ')';
		}

		# Input:prompt — inline getline driving the handler's onInput.
		if (targetC == 'Input' && expr:methodName == 'prompt' && expr:argCount() > 0) {
			local Expression is handlerExpr: self:argValue(expr: expr, index: 0);
			local String is handlerC: cg:generateExpression(expr: handlerExpr);
			local String is handlerClass: cg:inferTargetType(expr: handlerExpr);
			if (handlerClass == '' && handlerExpr:kind == ExpressionKind:CALL) {
				local Expression is mt: handlerExpr:methodTarget;
				handlerClass: cg:generateExpression(expr: mt);
			}
			return "({ char* _line = NULL; size_t _line_cap = 0; char* _res = \"\"; ssize_t _n = getline(&_line, &_line_cap, stdin); if (_n >= 0) { if (_n > 0 && _line[_n - 1] == '\\n') _line[_n - 1] = '\\0'; _res = strdup(_line); } free(_line); " . handlerClass . '_onInput((void*)(' . handlerC . '), spec_string_from_chars(_res)); })';
		}

		# Process methods.
		if (targetC == 'Process') {
			if (expr:methodName == 'execute') {
				local String is cmdC: '0';
				local Array of String is argList: [];
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					argList:add(item: cg:generateExpression(expr: arg:value));
				});
				argList:each(action: local Function(String is a){
					if (cmdC == '0') { cmdC: a; } else { cmdC: cmdC . ', ' . a; }
				});
				return 'spec_process_execute(' . cmdC . ')';
			}
			if (expr:methodName == 'sleep') {
				local Expression is msArg: self:argValue(expr: expr, index: 0);
				local String is msC: cg:generateExpression(expr: msArg);
				return 'spec_process_sleep(' . msC . ')';
			}
			if (expr:methodName == 'getPid') {
				return 'spec_process_get_pid()';
			}
			if (expr:methodName == 'clockMs') {
				return 'spec_clock_ms()';
			}
			if (expr:methodName == 'peakMemoryKb') {
				return 'spec_mem_peak_kb()';
			}
			if (expr:methodName == 'threadCount') {
				return 'spec_thread_count()';
			}
			if (expr:methodName == 'exit') {
				local Expression is codeArg: self:argValue(expr: expr, index: 0);
				local String is codeC: cg:generateExpression(expr: codeArg);
				return 'exit(' . codeC . ')';
			}
		}

		# File methods.
		if (targetC == 'File') {
			if (expr:methodName == 'exists') {
				local Expression is pArg: self:argValue(expr: expr, index: 0);
				local String is pC: cg:generateExpression(expr: pArg);
				return 'spec_file_exists(' . pC . ')';
			}
			if (expr:methodName == 'read') {
				local String is pathC: 'spec_string_intern("")';
				local String is defC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'path') { pathC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'default') { defC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'onSuccess') { onSuccC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'onError') { onErrC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_file_read(' . pathC . ', ' . defC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			}
			if (expr:methodName == 'write') {
				local String is pathC: 'spec_string_intern("")';
				local String is contentC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'path') { pathC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'content') { contentC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'onSuccess') { onSuccC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'onError') { onErrC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_file_write(' . pathC . ', ' . contentC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			}
			if (expr:methodName == 'remove') {
				local Expression is pArg: self:argValue(expr: expr, index: 0);
				local String is pC: cg:generateExpression(expr: pArg);
				return 'spec_file_remove(' . pC . ')';
			}
		}

		# Math functions.
		if (targetC == 'Math' || targetC == 'math') {
			local String is m: expr:methodName;
			local String is a0: '0.0';
			if (expr:argCount() > 0) {
				a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
			}
			# Single-operand functions.
			when (m) {
				is 'round': { return 'spec_math_round(' . a0 . ')'; }
				is 'floor': { return 'spec_math_floor(' . a0 . ')'; }
				is 'ceil', 'ceiling': { return 'spec_math_ceil(' . a0 . ')'; }
				is 'abs': { return 'spec_math_abs(' . a0 . ')'; }
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
			if (expr:argCount() > 1) {
				a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
			}
			if (m == 'min') {
				return 'spec_math_min(' . a0 . ', ' . a1 . ')';
			}
			if (m == 'max') {
				return 'spec_math_max(' . a0 . ', ' . a1 . ')';
			}
			if (m == 'pow') {
				return 'spec_math_pow(' . a0 . ', ' . a1 . ')';
			}
			if (m == 'atan2') {
				return 'spec_math_atan2(' . a0 . ', ' . a1 . ')';
			}
			if (m == 'random') {
				return 'spec_math_random(' . a0 . ', ' . a1 . ')';
			}
			if (m == 'clamp') {
				local String is vC: '0.0';
				local String is loC: '0.0';
				local String is hiC: '1.0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'value') { vC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'min' || arg:name == 'lo') { loC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'max' || arg:name == 'hi') { hiC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_math_clamp(' . vC . ', ' . loC . ', ' . hiC . ')';
			}
			if (m == 'toInt' || m == 'toFloat') {
				return a0;
			}
		}

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
		if (isArr) {
			local String is arrC: self:bindContainerCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			if (arrC != '') {
				return arrC;
			}
		}

		# Map literal-constructor + concrete getters + inline each.
		if (targetC == 'Map' || targetType == 'Map' || targetType:startsWith(prefix: 'Map:')) {
			local String is mapC: self:bindMapCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			if (mapC != '') {
				return mapC;
			}
		}

		# String instance methods: direct dispatch to compiled bodies.
		if (targetType == 'String') {
			local String is ddC: self:bindStringDirect(expr: expr, targetC: targetC, cg: cg);
			if (ddC != '') {
				return ddC;
			}
		}

		# Enum values()/of()/name()/value()/ordinal().
		if (self:allEnumNames:has(key: targetC) && expr:methodName == 'values') {
			return targetC . '_values()';
		}
		if (self:allEnumNames:has(key: targetC) && expr:methodName == 'of' && expr:argCount() > 0) {
			local Expression is vArg: self:argValue(expr: expr, index: 0);
			return targetC . '_of(' . cg:generateExpression(expr: vArg) . ')';
		}
		if (self:allEnumNames:has(key: targetType)) {
			if (expr:methodName == 'name') {
				return targetType . '_name(' . targetC . ')';
			}
			if (expr:methodName == 'value') {
				return targetType . '_value(' . targetC . ')';
			}
			if (expr:methodName == 'ordinal') {
				return targetType . '_ordinal(' . targetC . ')';
			}
		}

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
		if (expr:argCount() > 0) {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		}
		local String is a1: '';
		if (expr:argCount() > 1) {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		}
		# Array methods (SpecArray*). Named-arg extraction per the fossil.
		if (targetType:startsWith(prefix: 'Array')) {
			if (m == 'get') {
				local String is idxC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'index') { idxC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_array_get(' . targetC . ', ' . idxC . ')';
			}
			if (m == 'set') {
				local String is idxC: '0';
				local String is itemC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'index') { idxC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'item' || arg:name == 'value') { itemC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_array_set(' . targetC . ', ' . idxC . ', (void*)(intptr_t)(' . itemC . '))';
			}
			if (m == 'add') {
				local String is itemC: 'NULL';
				if (expr:argCount() > 0) {
					local Expression is valExpr: self:argValue(expr: expr, index: 0);
					if (valExpr:kind == ExpressionKind:ARRAY) {
						cg:setContainerHint(t: targetType);
						itemC: cg:generateExpression(expr: valExpr);
						return 'spec_array_add_array(' . targetC . ', ' . itemC . ')';
					}
					local Boolean is savedArgMode: cg:argMode;
					cg:setArgMode(m: false);
					itemC: cg:generateExpression(expr: valExpr);
					cg:setArgMode(m: savedArgMode);
				}
				local String is elemKindA: cg:containerElemKind(containerType: targetType);
				local String is addFn: 'spec_array_add';
				if (elemKindA == 'object') {
					addFn: 'spec_array_add_object';
				}
				return addFn . '(' . targetC . ', (void*)(' . itemC . '))';
			}
			if (m == 'length') {
				return 'spec_array_length(' . targetC . ')';
			}
			if (m == 'pop') {
				local String is defC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'default') {
						local String is rawDefC: cg:generateExpression(expr: arg:value);
						if (targetType:startsWith(prefix: 'Array:String')) {
							defC: rawDefC;
						} else {
							defC: '(void*)(intptr_t)(' . rawDefC . ')';
						}
					}
				});
				return 'spec_array_pop(' . targetC . ', ' . defC . ')';
			}
			if (m == 'removeAt') {
				local String is idxC: '0';
				local String is defC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'index') { idxC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'default') { defC: '(void*)(intptr_t)(' . cg:generateExpression(expr: arg:value) . ')'; }
				});
				return 'spec_array_remove_at(' . targetC . ', ' . idxC . ', ' . defC . ')';
			}
			if (m == 'isEmpty') {
				return '(long long)(spec_array_length(' . targetC . ') == 0)';
			}
			if (m == 'slice') {
				local String is startC: '0';
				local String is endC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'start') { startC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'end') { endC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_array_slice(' . targetC . ', ' . startC . ', ' . endC . ')';
			}
			if (m == 'clear') {
				return 'spec_array_clear(' . targetC . ')';
			}
			if (m == 'indexOf') {
				local String is searchC: '""';
				local String is defC: '-1';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'search' || arg:name == 'needle') { searchC: cg:generateExpression(expr: arg:value); }
					if (arg:name == 'default') { defC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_array_index_of_str(' . targetC . ', ' . searchC . ', ' . defC . ')';
			}
			# Higher-order: anon functions inline as loops; values as callbacks.
			if (m == 'each') {
				if (expr:argCount() > 0) {
					local Expression is fnExpr: self:argValue(expr: expr, index: 0);
					if (fnExpr:kind == ExpressionKind:ANON_FN) {
						return cg:generateInlineArrayOp(mode: 'each', targetC: targetC, fnExpr: fnExpr);
					}
				}
				local String is fnC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'action') { fnC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_array_each(' . targetC . ', (void (*)(void*))(' . fnC . '))';
			}
			if (m == 'filter') {
				if (expr:argCount() > 0) {
					local Expression is fnExpr: self:argValue(expr: expr, index: 0);
					if (fnExpr:kind == ExpressionKind:ANON_FN) {
						return cg:generateInlineArrayOp(mode: 'filter', targetC: targetC, fnExpr: fnExpr);
					}
				}
				local String is fnC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'predicate') { fnC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_array_filter(' . targetC . ', (bool (*)(void*))(' . fnC . '))';
			}
			if (m == 'count') {
				if (expr:argCount() > 0) {
					local Expression is fnExpr: self:argValue(expr: expr, index: 0);
					if (fnExpr:kind == ExpressionKind:ANON_FN) {
						return cg:generateInlineArrayOp(mode: 'count', targetC: targetC, fnExpr: fnExpr);
					}
				}
				local String is fnC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'predicate') { fnC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_array_count(' . targetC . ', (bool (*)(void*))(' . fnC . '))';
			}
			if (m == 'any') {
				if (expr:argCount() > 0) {
					local Expression is fnExpr: self:argValue(expr: expr, index: 0);
					if (fnExpr:kind == ExpressionKind:ANON_FN) {
						return cg:generateInlineArrayOp(mode: 'any', targetC: targetC, fnExpr: fnExpr);
					}
				}
				local String is fnC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'predicate') { fnC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_array_any(' . targetC . ', (bool (*)(void*))(' . fnC . '))';
			}
			if (m == 'map') {
				if (expr:argCount() > 0) {
					local Expression is fnExpr: self:argValue(expr: expr, index: 0);
					if (fnExpr:kind == ExpressionKind:ANON_FN) {
						return cg:generateInlineArrayOp(mode: 'map', targetC: targetC, fnExpr: fnExpr);
					}
				}
			}
			if (m == 'fold') {
				if (expr:argCount() >= 2) {
					local Expression is initExpr: self:argValue(expr: expr, index: 0);
					local Expression is fnExpr: self:argValue(expr: expr, index: 1);
					if (fnExpr:kind == ExpressionKind:ANON_FN) {
						return cg:generateInlineArrayFold(targetC: targetC, initExpr: initExpr, fnExpr: fnExpr);
					}
				}
			}
			if (m == 'join') {
				local String is sepC: '""';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'separator' || sepC == '""') { sepC: cg:generateExpression(expr: arg:value); }
				});
				return 'spec_array_join(' . targetC . ', ' . sepC . ')';
			}
		}
		# List methods (SpecVec*/SpecByteBuffer*).
		if (targetType:startsWith(prefix: 'List')) {
			local Boolean is byteBuf: targetType == 'List:Byte' || targetType == 'List of Byte';
			when (m) {
				is 'push': {
					if (byteBuf) {
						return 'spec_bytebuffer_push(' . targetC . ', ' . a0 . ')';
					}
					return 'spec_vec_push(' . targetC . ', ' . a0 . ')';
				}
				is 'appendString': { return 'spec_bytebuffer_append_string(' . targetC . ', ' . a0 . ')'; }
				is 'get': { return 'spec_buf_get_byte(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
				is 'pop': { return 'spec_buf_pop_byte(' . targetC . ', ' . a0 . ')'; }
				is 'length': { return 'spec_vec_length(' . targetC . ')'; }
				is 'clear': { return 'spec_vec_clear(' . targetC . ')'; }
				else: {}
			}
		}
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
		if (expr:argCount() > 0) {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		}
		local String is a1: '';
		if (expr:argCount() > 1) {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		}
		if (m == 'init') {
			return 'spec_map_new()';
		}
		if (m == 'set') {
			# String values store directly; everything else boxes into the
			# any-slot via spec_map_set_any.
			local String is keyC: 'spec_string_intern("")';
			local String is valC: 'spec_string_intern("")';
			local Boolean is valIsStr: true;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:name == 'key') { keyC: cg:generateExpression(expr: arg:value); }
				if (arg:name == 'value') {
					local Boolean is savedArgMode: cg:argMode;
					cg:setArgMode(m: false);
					valC: cg:generateExpression(expr: arg:value);
					cg:setArgMode(m: savedArgMode);
					valIsStr: cg:isStringExpr(expr: arg:value, exprC: valC);
				}
			});
			if (targetType:contains(needle: 'String:String') || targetType:contains(needle: 'to String') || valIsStr) {
				return 'spec_map_set(' . targetC . ', ' . keyC . ', ' . valC . ')';
			}
			return 'spec_map_set_any(' . targetC . ', ' . keyC . ', (void*)(intptr_t)(' . valC . '))';
		}
		if (m == 'getString') {
			return 'spec_map_get_string(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		}
		if (m == 'getInt') {
			return 'spec_map_get_int(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		}
		if (m == 'getFloat') {
			return 'spec_map_get_float(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		}
		if (m == 'getBool') {
			return 'spec_map_get_bool(' . targetC . ', ' . a0 . ', ' . a1 . ')';
		}
		if (m == 'has') {
			return 'spec_map_has(' . targetC . ', ' . a0 . ')';
		}
		if (m == 'remove') {
			return 'spec_map_remove(' . targetC . ', ' . a0 . ')';
		}
		if (m == 'keys') {
			return 'spec_map_keys(' . targetC . ')';
		}
		if (m == 'length') {
			return '(long long)spec_map_length(' . targetC . ')';
		}
		if (m == 'each') {
			if (expr:argCount() > 0) {
				local Expression is fnExpr: self:argValue(expr: expr, index: 0);
				if (fnExpr:kind == ExpressionKind:ANON_FN) {
					return cg:generateInlineMapEach(targetC: targetC, fnExpr: fnExpr);
				}
			}
		}
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
		if (expr:argCount() > 0) {
			a0: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		}
		local String is a1: '';
		if (expr:argCount() > 1) {
			a1: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
		}
		when (m) {
			is 'length': { return 'spec_string_length(' . targetC . ')'; }
			is 'charAt': { return 'spec_string_char_at(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
			is 'substring': { return 'spec_string_substring(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
			is 'indexOf': { return 'spec_string_index_of(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
			is 'trim': { return 'spec_string_trim(' . targetC . ')'; }
			is 'isDigit': { return 'spec_string_is_digit(' . targetC . ')'; }
			is 'isAlpha': { return 'spec_string_is_alpha(' . targetC . ')'; }
			is 'isWhitespace': { return 'spec_string_is_whitespace(' . targetC . ')'; }
			is 'countLeading': { return 'spec_string_count_leading(' . targetC . ', ' . a0 . ')'; }
			is 'split': { return 'spec_string_split(' . targetC . ', ' . a0 . ')'; }
			is 'lines': { return 'spec_string_lines(' . targetC . ')'; }
			is 'contains': { return 'spec_string_contains(' . targetC . ', ' . a0 . ')'; }
			is 'startsWith': { return 'spec_string_has_prefix(' . targetC . ', ' . a0 . ')'; }
			is 'endsWith': { return 'spec_string_has_suffix(' . targetC . ', ' . a0 . ')'; }
			is 'replaceAll': { return 'spec_string_replace_all(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
			is 'parseInt': { return 'spec_parse_base(' . targetC . ', ' . a0 . ', ' . a1 . ')'; }
			else: { return ''; }
		}
	}
}
