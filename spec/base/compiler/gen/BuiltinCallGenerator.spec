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
		if (fCls:name != clsName) {
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
			} else if (expr:methodTarget:kind == ExpressionKind:CALL) {
				local Expression is qInner: expr:methodTarget;
				if (qInner:methodTarget:kind == ExpressionKind:PATH) {
					qCls: qInner:methodName;
				}
			}
			local ClassInfo is qc: cg:findClass(name: qCls);
			if (qCls != '' && qc:name == qCls && cg:isSysinternalClass(name: qCls)) {
				floorCls: qCls;
			}
		}
		if (floorCls != '') {
			local String is bound: self:bindFloorCall(clsName: floorCls, expr: expr, cg: cg);
			if (bound != '') {
				return bound;
			}
		}

		# Reflection:class()/method() — compile-time source identity.
		if (targetC == 'Reflection' && expr:methodName == 'class' && expr:argCount() == 0) {
			return 'spec_string_intern("' . cg:currentClassName . '")';
		}
		if (targetC == 'Reflection' && expr:methodName == 'method' && expr:argCount() == 0) {
			return 'spec_string_intern("' . cg:currentMethodName . '")';
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
			local Expression is a0: self:argValue(expr: expr, index: 0);
			local Expression is a1: self:argValue(expr: expr, index: 1);
			local Expression is evalExpr: a0;
			local Expression is iterExpr: a1;
			if (evalExpr:kind == ExpressionKind:ANON_FN && iterExpr:kind == ExpressionKind:ANON_FN) {
				local String is evalC: cg:generateExpression(expr: evalExpr);
				local String is iterC: cg:generateExpression(expr: iterExpr);
				return '({ SpecClosure* _ec = (SpecClosure*)(' . evalC . '); SpecClosure* _ic = (SpecClosure*)(' . iterC . '); while (_ec && _ic) { bool _v = ((bool (*)(void*))_ec->fn)(_ec->env); if (!_v) break; ((bool (*)(void*))_ic->fn)(_ic->env); } })';
			}
		}

		# Input:prompt.
		if (targetC == 'Input' && expr:methodName == 'prompt' && expr:argCount() > 0) {
			local Expression is msgArg: self:argValue(expr: expr, index: 0);
			local String is msgC: cg:generateExpression(expr: msgArg);
			return 'spec_input_prompt(' . msgC . ')';
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
				local Expression is pArg: self:argValue(expr: expr, index: 0);
				local String is pC: cg:generateExpression(expr: pArg);
				return 'spec_file_read(' . pC . ')';
			}
			if (expr:methodName == 'write') {
				local String is argsCs: '';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (argsCs != '') { argsCs: argsCs . ', '; }
					argsCs: argsCs . cg:generateExpression(expr: arg:value);
				});
				return 'spec_file_write(' . argsCs . ')';
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
		if (targetType:startsWith(prefix: 'Array') || targetType:startsWith(prefix: 'List') || targetType == 'Map' || targetType:startsWith(prefix: 'Map:')) {
			local String is arrC: self:bindContainerCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			if (arrC != '') {
				return arrC;
			}
		}

		# Map literal-constructor + concrete getters.
		if (targetC == 'Map' || targetType == 'Map' || targetType:startsWith(prefix: 'Map:')) {
			local String is mapC: self:bindMapCall(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			if (mapC != '') {
				return mapC;
			}
		}

		# Array higher-order methods (each/filter/count/any/map/fold/join).
		if (targetType:startsWith(prefix: 'Array') && (targetC == 'self' || self:policy:isTransparent(c: cg:findClass(name: targetType)))) {
			local String is hoC: self:bindArrayHigherOrder(expr: expr, targetC: targetC, targetType: targetType, cg: cg);
			if (hoC != '') {
				return hoC;
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
		# Array methods (SpecArray*).
		if (targetType:startsWith(prefix: 'Array') && !targetType:startsWith(prefix: 'Array of String')) {
			when (m) {
				is 'length': { return 'spec_array_length(' . targetC . ')'; }
				is 'get': { return '((long long)(intptr_t)spec_array_get(' . targetC . ', (size_t)(' . a0 . ')))'; }
				is 'pop': { return '((long long)(intptr_t)spec_array_pop(' . targetC . ', ' . a0 . '))'; }
				is 'set': { return 'spec_array_set(' . targetC . ', ' . a0 . ', (void*)(intptr_t)(' . a1 . '))'; }
				is 'clear': { return 'spec_array_clear(' . targetC . ')'; }
				else: {}
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
			return 'spec_map_set(' . targetC . ', ' . a0 . ', ' . a1 . ')';
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
		return '';
	}

	## Binds Array higher-order methods (each/filter/count/any/map/fold/join)
	## — the callback-taking surface.
	##
	## @param expr: CALL expression.
	## @param targetC: Target C.
	## @param targetType: Target type name.
	## @param cg: The code generator.
	## @return: C call, or ''.
	Function of String is bindArrayHigherOrder(Expression is expr, String is targetC, String is targetType, CodeGenerator is cg){
		local String is m: expr:methodName;
		if (expr:argCount() == 0) {
			return '';
		}
		local String is fnC: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
		when (m) {
			is 'each': {
				if (expr:argCount() < 2) {
					return '';
				}
				return 'spec_array_each(' . targetC . ', (void (*)(void*))(' . fnC . '))';
			}
			is 'filter': {
				return 'spec_array_filter(' . targetC . ', (bool (*)(void*))(' . fnC . '))';
			}
			is 'count': {
				return 'spec_array_count(' . targetC . ', (bool (*)(void*))(' . fnC . '))';
			}
			is 'any': {
				return 'spec_array_any(' . targetC . ', (bool (*)(void*))(' . fnC . '))';
			}
			is 'map': {
				return 'spec_array_map(' . targetC . ', (void* (*)(void*))(' . fnC . '))';
			}
			is 'fold': {
				local String is initC: '';
				if (expr:argCount() > 0) {
					initC: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
				}
				local String is accFnC: '';
				if (expr:argCount() > 1) {
					accFnC: cg:generateExpression(expr: self:argValue(expr: expr, index: 1));
				}
				return 'spec_array_fold(' . targetC . ', ' . initC . ', ' . accFnC . ')';
			}
			is 'join': {
				local String is sepC: 'spec_string_intern("")';
				if (expr:argCount() > 0) {
					sepC: cg:generateExpression(expr: self:argValue(expr: expr, index: 0));
				}
				return 'spec_array_join(' . targetC . ', ' . sepC . ')';
			}
			else: { return ''; }
		}
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
