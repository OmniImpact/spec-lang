#! Package compiler
#! Pure Spec compiler implementation: BuiltinCallGenerator for standard library and runtime intrinsic calls.

## Translates standard library and runtime builtin method calls into C11 runtime functions.
Class is BuiltinCallGenerator{

	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:meta:*,
		base:reflect:ClassInfo,
		base:reflect:Member,
		base:reflect:Parameter,
		compiler:CBackendUtils,
		compiler:CodeGenerator
	];

	local CBackendUtils is utils;
	local Map of String to String is allEnumNames: Map:init();

	replace Function is init(){
		self:utils: CBackendUtils:init();
		self:allEnumNames: Map:init();
	}

	Function is setEnumNames(Map of String to String is names){
		self:allEnumNames: names;
	}

	## Generates C code for a standard library or runtime intrinsic call.
	##
	## @param expr: AST [Expression] node of kind CALL.
	## @param targetC: Generated C expression for method target.
	## @param targetType: Inferred type name of method target.
	## @param cg: Reference to parent [CodeGenerator].
	## @return: C code string if builtin call, or empty string if not a builtin.
	Function of String is generateBuiltinCall(Expression is expr, String is targetC, String is targetType, CodeGenerator is cg){
	# error:line - diagnostics written to stderr
	if ((targetC == 'error' || targetC == 'Error') && expr:methodName == 'line' && expr:methodArgs:length() > 0) {
		local NamedArg is errArg: expr:methodArgs:get(index: 0);
		local String is errValC: cg:generateExpression(expr: errArg:getValue());
		local String is errStrC: cg:wrapToString(expr: errArg:getValue(), exprC: errValC);
		return 'spec_error_line(' . errStrC . ')';
	}

	# Generic String direct dispatch: when the String class carries a compiled
	# body for the method, emit a direct call to it; body-less declarations fall
	# through to the runtime interceptions below. Arguments bind positionally in
	# declaration order first, then by name, with declaration-side defaults
	# filling the gaps.
	if (targetType == 'String' || targetType == 'string') {
		local ClassInfo is strCls: cg:findClassForCall(name: 'String');
		if (strCls:getName() == 'String') {
			local Member is foundM;
			local Boolean is hasM: false;
			strCls:getMembers():each(action: local Function(Member is m){
				if (!hasM && m:getKind() == 'METHOD' && m:getName() == expr:methodName) {
					hasM: true;
					foundM: m;
				}
			});
			if (hasM && foundM:getBody():length() > 0) {
				local String is argCs: '';
				local Boolean is argsOk: true;
				local Int is posIdx: 0;
				foundM:getParameters():each(action: local Function(Parameter is p){
					if (argsOk) {
						local Boolean is got: false;
						if (posIdx < expr:methodArgs:length() && expr:methodArgs:get(index: posIdx):getName() == '') {
							argCs: argCs . ', ' . cg:generateExpression(expr: expr:methodArgs:get(index: posIdx):getValue());
							posIdx: posIdx + 1;
							got: true;
						}
						if (!got) {
							expr:methodArgs:each(action: local Function(NamedArg is a){
								if (!got && a:getName() == p:getName()) {
									got: true;
									argCs: argCs . ', ' . cg:generateExpression(expr: a:getValue());
								}
							});
						}
						if (!got && p:getHasDefault()) {
							argCs: argCs . ', ' . cg:generateExpression(expr: p:getDefaultExpr());
							got: true;
						}
						if (!got) {
							argsOk: false;
						}
					}
				});
				if (argsOk) {
					return 'String_' . expr:methodName . '(' . targetC . argCs . ')';
				}
			}
		}
	}

		# Type name introspection on class instances
		if (expr:methodName == 'typeName' && targetType != '' && !self:utils:isBuiltinClass(name: targetType) && !self:allEnumNames:has(key: targetType)) {
			return 'spec_type_name(' . targetC . ')';
		}

		# Integer base conversion
		if (expr:methodName == 'toBase' && (targetType == 'Int' || targetType == 'int')) {
			local String is baseC: '10';
			local String is digitsC: '0';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:getName() == 'base') { baseC: cg:generateExpression(expr: arg:getValue()); }
				if (arg:getName() == 'digits') { digitsC: cg:generateExpression(expr: arg:getValue()); }
			});
			return 'spec_int_to_base(' . targetC . ', ' . baseC . ', ' . digitsC . ')';
		}
		if (expr:methodName == 'parseInt' && (targetType == 'String' || targetType == 'string')) {
			local String is baseC: '10';
			local String is defC: '0';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:getName() == 'base') { baseC: cg:generateExpression(expr: arg:getValue()); }
				if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
			});
			return 'spec_parse_base(' . targetC . ', ' . baseC . ', ' . defC . ')';
		}

		# Parallel fan-out execution
		if (targetC == 'Parallel' && expr:methodName == 'run' && expr:methodArgs:length() >= 3) {
			local String is threadsC: '1';
			local String is iterC: '0';
			local String is workerC: 'NULL';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:getName() == 'threads') { threadsC: cg:generateExpression(expr: arg:getValue()); }
				if (arg:getName() == 'iterations') { iterC: cg:generateExpression(expr: arg:getValue()); }
				if (arg:getName() == 'worker') { workerC: cg:generateExpression(expr: arg:getValue()); }
			});
			return 'spec_parallel_run(' . threadsC . ', ' . iterC . ', (void*)(' . workerC . '))';
		}

		# Ansi terminal metrics (runtime ioctls; Ansi is otherwise pure Spec)
		if (targetC == 'Ansi' && expr:methodName == 'terminalWidth') {
			return 'spec_term_width()';
		}
		if (targetC == 'Ansi' && expr:methodName == 'terminalHeight') {
			return 'spec_term_height()';
		}

		# Output:line and Output:print / Output:write
		if ((targetC == 'output' || targetC == 'Output') && expr:methodName == 'line' && expr:methodArgs:length() > 0) {
			local NamedArg is firstArg: expr:methodArgs:get(index: 0);
			local String is valC: cg:generateExpression(expr: firstArg:getValue());
			local String is strC: cg:wrapToString(expr: firstArg:getValue(), exprC: valC);
			return "printf(\"%s\\n\", spec_buf_to_cstring((SpecBuf*)(" . strC . ")))";
		}
		if ((targetC == 'output' || targetC == 'Output') && (expr:methodName == 'print' || expr:methodName == 'write') && expr:methodArgs:length() > 0) {
			local NamedArg is firstArg: expr:methodArgs:get(index: 0);
			local String is valC: cg:generateExpression(expr: firstArg:getValue());
			local String is strC: cg:wrapToString(expr: firstArg:getValue(), exprC: valC);
			return '({ printf("%s", spec_buf_to_cstring((SpecBuf*)(' . strC . '))); fflush(stdout); })';
		}

		# String:fromCharCode
		if (targetC == 'String' && expr:methodName == 'fromCharCode' && expr:methodArgs:length() > 0) {
			local NamedArg is codeArg: expr:methodArgs:get(index: 0);
			local String is codeC: cg:generateExpression(expr: codeArg:getValue());
			return 'spec_string_from_char_code(' . codeC . ')';
		}

		# Intrinsic loop runner: While:run(loop, control)
		if (targetC == 'While' && expr:methodName == 'run' && expr:methodArgs:length() > 0) {
			local NamedArg is loopArg: expr:methodArgs:get(index: 0);
			local Expression is loopVal: loopArg:getValue();
			local String is loopC: cg:generateExpressionInner(expr: loopVal);
			local String is loopClass: cg:inferTargetType(expr: loopVal);
			if (loopClass == '' && loopVal:getKind() == 'CALL') {
				local Expression is mt: loopVal:methodTarget;
				loopClass: cg:generateExpression(expr: mt);
			}
			local String is ctrlC: 'NULL';
			if (expr:methodArgs:length() > 1) {
				local NamedArg is ctrlArg: expr:methodArgs:get(index: 1);
				ctrlC: cg:generateExpression(expr: ctrlArg:getValue());
			}
			local String is freeLoopC: '';
		if (loopVal:getKind() == 'CALL' && loopVal:methodName == 'init') {
			freeLoopC: ' spec_release(_lp);';
		}
			return '({ void* _lp = (void*)(' . loopC . '); SpecLoopControl* _ctrl = (SpecLoopControl*)(' . ctrlC . '); while (' . loopClass . '_evaluate((void*)_lp)) { if (!' . loopClass . '_iteration((void*)_lp, _ctrl) || (_ctrl && _ctrl->stopped)) break; } if (_ctrl && _ctrl->on_complete) { _ctrl->on_complete(_ctrl->callback, _ctrl); }' . freeLoopC . ' })';
		}

		# Lightweight predicate loop: While:condition(evaluate, iteration)
		if (targetC == 'While' && expr:methodName == 'condition' && expr:methodArgs:length() >= 2) {
			local NamedArg is a0: expr:methodArgs:get(index: 0);
			local NamedArg is a1: expr:methodArgs:get(index: 1);
			local Expression is evalExpr: a0:getValue();
			local Expression is iterExpr: a1:getValue();
			if (evalExpr:getKind() == 'ANON_FN' && iterExpr:getKind() == 'ANON_FN') {
				return cg:generateInlineWhileCondition(evalExpr: evalExpr, iterExpr: iterExpr);
			}
			local String is evalC: cg:generateExpression(expr: evalExpr);
			local String is iterC: cg:generateExpression(expr: iterExpr);
			return '({ bool (*_ev)(void) = (bool (*)(void))(' . evalC . '); void (*_it)(void) = (void (*)(void))(' . iterC . '); while (_ev && _ev()) { if (_it) _it(); } })';
		}

		# Input static methods
		if (targetC == 'Input' && expr:methodName == 'prompt' && expr:methodArgs:length() > 0) {
			local NamedArg is promptArg: expr:methodArgs:get(index: 0);
			local Expression is promptVal: promptArg:getValue();
			local String is handlerC: cg:generateExpression(expr: promptVal);
			local String is handlerClass: cg:inferTargetType(expr: promptVal);
			if (handlerClass == '' && promptVal:getKind() == 'CALL') {
				local Expression is mt: promptVal:methodTarget;
				handlerClass: cg:generateExpression(expr: mt);
			}
			return "({ char* _line = NULL; size_t _line_cap = 0; char* _res = \"\"; ssize_t _n = getline(&_line, &_line_cap, stdin); if (_n >= 0) { if (_n > 0 && _line[_n - 1] == '\\n') _line[_n - 1] = '\\0'; _res = strdup(_line); } free(_line); " . handlerClass . '_onInput((void*)(' . handlerC . '), spec_string_from_chars(_res)); })';
		}

		# LoopControl methods
		if (targetC == 'LoopControl' && expr:methodName == 'init') {
			if (expr:methodArgs:length() == 0) {
				return 'LoopControl_new()';
			}
			local NamedArg is cbArg: expr:methodArgs:get(index: 0);
			local Expression is cbVal: cbArg:getValue();
			local String is cbC: cg:generateExpression(expr: cbVal);
			local String is cbClass: cg:inferTargetType(expr: cbVal);
			if (cbClass == '' && cbVal:getKind() == 'CALL') {
				local Expression is mt: cbVal:methodTarget;
				cbClass: cg:generateExpression(expr: mt);
			}
			return '({ SpecLoopControl* _c = LoopControl_new(); _c->callback = (void*)(' . cbC . '); _c->on_complete = (void (*)(void*, struct SpecLoopControl*))' . cbClass . '_onComplete; _c; })';
		}
		if (expr:methodName == 'stop') {
			return 'LoopControl_stop(' . targetC . ')';
		}

		# Process static methods
		if (targetC == 'Process') {
			if (expr:methodName == 'execute') {
				local String is cmdC: 'spec_string_intern("")';
				local String is argsC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'command') { cmdC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'args') { argsC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_process_execute(' . cmdC . ', ' . argsC . ')';
			}
			if (expr:methodName == 'sleep') {
				local String is msC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'milliseconds') { msC: cg:generateExpression(expr: arg:getValue()); }
				});
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
			if (expr:methodName == 'atomicAdd') {
				local String is slotC: '0';
				local String is valC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'slot') { slotC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'value') { valC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_atomic_add(' . slotC . ', ' . valC . ')';
			}
			if (expr:methodName == 'atomicPut') {
				local String is slotC: '0';
				local String is valC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'slot') { slotC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'value') { valC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_atomic_put(' . slotC . ', ' . valC . ')';
			}
			if (expr:methodName == 'atomicGet') {
				local String is slotC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'slot') { slotC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_atomic_get(' . slotC . ')';
			}
			if (expr:methodName == 'exit') {
				local String is codeC: '0';
				if (expr:methodArgs:length() > 0) {
					local NamedArg is codeArg: expr:methodArgs:get(index: 0);
					codeC: cg:generateExpression(expr: codeArg:getValue());
				}
				return 'exit((int)(' . codeC . '))';
			}
		}

		# File static methods
		if (targetC == 'File') {
			if (expr:methodName == 'exists') {
				local String is pathC: 'spec_string_intern("")';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'path') { pathC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_file_exists(' . pathC . ')';
			}
			if (expr:methodName == 'remove') {
				local String is pathC: 'spec_string_intern("")';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'path') { pathC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_file_remove(' . pathC . ')';
			}
			if (expr:methodName == 'read') {
				local String is pathC: 'spec_string_intern("")';
				local String is defC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'path') { pathC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'onSuccess') { onSuccC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'onError') { onErrC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_file_read(' . pathC . ', ' . defC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			}
			if (expr:methodName == 'readAsync') {
				local String is pathC: 'spec_string_intern("")';
				local String is defC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'path') { pathC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'onSuccess') { onSuccC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'onError') { onErrC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_file_read_async(' . pathC . ', ' . defC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			}
			if (expr:methodName == 'write') {
				local String is pathC: 'spec_string_intern("")';
				local String is contentC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'path') { pathC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'content') { contentC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'onSuccess') { onSuccC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'onError') { onErrC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_file_write(' . pathC . ', ' . contentC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			}
			if (expr:methodName == 'writeAsync') {
				local String is pathC: 'spec_string_intern("")';
				local String is contentC: 'spec_string_intern("")';
				local String is onSuccC: 'NULL';
				local String is onErrC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'path') { pathC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'content') { contentC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'onSuccess') { onSuccC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'onError') { onErrC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_file_write_async(' . pathC . ', ' . contentC . ', (SpecClosure*)(' . onSuccC . '), (SpecClosure*)(' . onErrC . '))';
			}
		}

		# Math static methods
		if (targetC == 'Math' || targetC == 'math') {
			if (expr:methodName == 'round') {
				local String is valC: '0.0';
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					valC: cg:generateExpression(expr: a0:getValue());
				}
				return 'spec_math_round(' . valC . ')';
			}
			if (expr:methodName == 'floor') {
				local String is valC: '0.0';
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					valC: cg:generateExpression(expr: a0:getValue());
				}
				return 'spec_math_floor(' . valC . ')';
			}
			if (expr:methodName == 'ceil' || expr:methodName == 'ceiling') {
				local String is valC: '0.0';
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					valC: cg:generateExpression(expr: a0:getValue());
				}
				return 'spec_math_ceil(' . valC . ')';
			}
			if (expr:methodName == 'abs') {
				local String is valC: '0.0';
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					valC: cg:generateExpression(expr: a0:getValue());
				}
				return 'spec_math_abs(' . valC . ')';
			}
			if (expr:methodName == 'min') {
				local String is aC: '0.0';
				local String is bC: '0.0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'a') { aC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'b') { bC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_math_min(' . aC . ', ' . bC . ')';
			}
			if (expr:methodName == 'max') {
				local String is aC: '0.0';
				local String is bC: '0.0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'a') { aC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'b') { bC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_math_max(' . aC . ', ' . bC . ')';
			}
			if (expr:methodName == 'clamp') {
				local String is vC: '0.0';
				local String is loC: '0.0';
				local String is hiC: '1.0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'value') { vC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'min' || arg:getName() == 'lo') { loC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'max' || arg:getName() == 'hi') { hiC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_math_clamp(' . vC . ', ' . loC . ', ' . hiC . ')';
			}
			if (expr:methodName == 'fastRandom') {
				return 'spec_fast_random()';
			}
			if (expr:methodName == 'toInt') {
				local String is valC: '0';
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					valC: cg:generateExpression(expr: a0:getValue());
				}
				return '((long long)(' . valC . '))';
			}
			if (expr:methodName == 'random') {
				local String is minC: '0.0';
				local String is maxC: '1.0';
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					minC: cg:generateExpression(expr: a0:getValue());
				}
				if (expr:methodArgs:length() > 1) {
					local NamedArg is a1: expr:methodArgs:get(index: 1);
					maxC: cg:generateExpression(expr: a1:getValue());
				}
				return 'spec_math_random(' . minC . ', ' . maxC . ')';
			}
			if (expr:methodName == 'sqrt' || expr:methodName == 'sin' || expr:methodName == 'cos' || expr:methodName == 'tan' || expr:methodName == 'log' || expr:methodName == 'log2' || expr:methodName == 'toFloat') {
				local String is valC: '0.0';
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					valC: cg:generateExpression(expr: a0:getValue());
				}
				if (expr:methodName == 'toFloat') {
					return 'spec_math_to_float(' . valC . ')';
				}
				return 'spec_math_' . expr:methodName . '(' . valC . ')';
			}
			if (expr:methodName == 'pow' || expr:methodName == 'atan2') {
				local String is aC: '0.0';
				local String is bC: '0.0';
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					aC: cg:generateExpression(expr: a0:getValue());
				}
				if (expr:methodArgs:length() > 1) {
					local NamedArg is a1: expr:methodArgs:get(index: 1);
					bC: cg:generateExpression(expr: a1:getValue());
				}
				return 'spec_math_' . expr:methodName . '(' . aC . ', ' . bC . ')';
			}
		}

		# List methods ([Byte] byte-buffer shape; other shapes below)
		if (targetType == 'List:Byte' || targetType == 'List of Byte') {
			local String is errC: 'spec_noop_closure()';
			if (expr:methodName == 'get' || expr:methodName == 'pop' || expr:methodName == 'set') {
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'error') {
						errC: cg:generateExpression(expr: arg:getValue());
					}
				});
			}
			if (expr:methodName == 'push') {
				local String is itemC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					itemC: cg:generateExpression(expr: arg:getValue());
				});
				return 'spec_bytebuffer_push(' . targetC . ', (long long)(' . itemC . '))';
			}
			if (expr:methodName == 'appendString') {
				local String is sC: 'spec_string_intern("")';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					sC: cg:generateExpression(expr: arg:getValue());
				});
				return 'spec_bytebuffer_append_string(' . targetC . ', spec_buf_to_cstring((SpecBuf*)(' . sC . ')))';
			}
			if (expr:methodName == 'get') {
				local String is idxC: '0';
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'index') { idxC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: '(long long)(' . cg:generateExpression(expr: arg:getValue()) . ')'; }
				});
				return 'spec_bytebuffer_get(' . targetC . ', ' . idxC . ', ' . defC . ', ' . errC . ')';
			}
			if (expr:methodName == 'set') {
				local String is idxC: '0';
				local String is itemC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'index') { idxC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'item' || arg:getName() == 'value') { itemC: '(long long)(' . cg:generateExpression(expr: arg:getValue()) . ')'; }
				});
				return 'spec_bytebuffer_set(' . targetC . ', ' . idxC . ', ' . itemC . ', ' . errC . ')';
			}
			if (expr:methodName == 'pop') {
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'default') { defC: '(long long)(' . cg:generateExpression(expr: arg:getValue()) . ')'; }
				});
				return 'spec_bytebuffer_pop(' . targetC . ', ' . defC . ', ' . errC . ')';
			}
			if (expr:methodName == 'length') {
				return 'spec_bytebuffer_length(' . targetC . ')';
			}
			if (expr:methodName == 'clear') {
				return 'spec_bytebuffer_clear(' . targetC . ')';
			}
			if (expr:methodName == 'toString') {
				return 'spec_bytebuffer_to_string(' . targetC . ')';
			}
		}

		# List methods (pointer-vector shapes)
		if (targetType:startsWith(prefix: 'List')) {
			local String is listElem: '';
			if (targetType:startsWith(prefix: 'List of ') && targetType:length() > 7) {
				listElem: targetType:substring(start: 7, end: targetType:length());
			} else if (targetType:startsWith(prefix: 'List:') && targetType:length() > 5) {
				listElem: targetType:substring(start: 5, end: targetType:length());
			}
			local String is elemKind: cg:containerElemKind(containerType: targetType);
			local String is itemPre: '(void*)(intptr_t)(';
			local String is itemPost: ')';
			local String is resCast: '(long long)(intptr_t)';
			if (elemKind == 'string') {
				itemPre: '(void*)(';
				resCast: '(String)';
			} else if (elemKind == 'object') {
				itemPre: '(void*)(';
				resCast: '(' . cg:cTypeFor(typeName: listElem) . ')(intptr_t)';
			}
			local String is errC: 'spec_noop_closure()';
			if (expr:methodName == 'get' || expr:methodName == 'pop' || expr:methodName == 'set') {
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'error') {
						errC: cg:generateExpression(expr: arg:getValue());
					}
				});
			}
			if (expr:methodName == 'push') {
				local String is itemC: '0';
				local Expression is itemExpr;
				local Boolean is savedArgV: cg:argMode;
				cg:setArgMode(m: false);
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					itemC: cg:generateExpression(expr: arg:getValue());
					itemExpr: arg:getValue();
				});
				cg:setArgMode(m: savedArgV);
				return 'spec_vec_push(' . targetC . ', ' . itemPre . itemC . itemPost . ')';
			}
			if (expr:methodName == 'get') {
				local String is idxC: '0';
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'index') { idxC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return resCast . 'spec_vec_get(' . targetC . ', ' . idxC . ', ' . itemPre . defC . itemPost . ', ' . errC . ')';
			}
			if (expr:methodName == 'set') {
				local String is idxC: '0';
				local String is itemC: '0';
				local Expression is itemExpr;
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'index') { idxC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'item' || arg:getName() == 'value') {
						local Boolean is savedArgS: cg:argMode;
						cg:setArgMode(m: false);
						itemC: cg:generateExpression(expr: arg:getValue());
						cg:setArgMode(m: savedArgS);
						itemExpr: arg:getValue();
					}
				});
				return 'spec_vec_set(' . targetC . ', ' . idxC . ', ' . itemPre . itemC . itemPost . ', ' . errC . ')';
			}
			if (expr:methodName == 'pop') {
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return resCast . 'spec_vec_pop(' . targetC . ', ' . itemPre . defC . itemPost . ', ' . errC . ')';
			}
			if (expr:methodName == 'length') {
				return 'spec_vec_length(' . targetC . ')';
			}
			if (expr:methodName == 'clear') {
				return 'spec_vec_clear(' . targetC . ')';
			}
		}

		# Map methods
		local Boolean is isMap: targetC == 'Map' || targetType == 'Map' || targetType:startsWith(prefix: 'Map:') ||
			((targetType == '' || targetType == 'Any') && (
				(expr:methodName == 'set' && !targetType:startsWith(prefix: 'Array')) || expr:methodName == 'getString' || expr:methodName == 'getInt' ||
				expr:methodName == 'getFloat' || expr:methodName == 'getBool' || expr:methodName == 'has' || expr:methodName == 'keys'
			));

		if (isMap) {
			if (expr:methodName == 'init') {
				if (cg:containerElemIsArc(containerType: targetType)) {
					return 'spec_map_new_object()';
				}
				return 'spec_map_new()';
			}
			if (expr:methodName == 'set') {
				local String is keyC: 'spec_string_intern("")';
				local String is valC: 'spec_string_intern("")';
				local Boolean is valIsStr: true;
				local Expression is valExpr;
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'key') { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'value') {
						local Boolean is savedArgM: cg:argMode;
						cg:setArgMode(m: false);
						valC: cg:generateExpression(expr: arg:getValue());
						cg:setArgMode(m: savedArgM);
						valIsStr: cg:isStringExpr(expr: arg:getValue());
						valExpr: arg:getValue();
					}
				});
				if (targetType:contains(needle: 'String:String') || targetType:contains(needle: 'to String') || valIsStr) {
					return 'spec_map_set(' . targetC . ', ' . keyC . ', ' . valC . ')';
				}
				return 'spec_map_set_any(' . targetC . ', ' . keyC . ', (void*)(intptr_t)(' . valC . '))';
			}
			if (expr:methodName == 'getString') {
				local String is keyC: 'spec_string_intern("")';
				local String is defC: 'spec_string_intern("")';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'key') { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_map_get_string(' . targetC . ', ' . keyC . ', ' . defC . ')';
			}
			if (expr:methodName == 'getInt') {
				local String is keyC: 'spec_string_intern("")';
				local String is defC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'key') { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_map_get_int(' . targetC . ', ' . keyC . ', ' . defC . ')';
			}
			if (expr:methodName == 'getFloat') {
				local String is keyC: 'spec_string_intern("")';
				local String is defC: '0.0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'key') { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_map_get_float(' . targetC . ', ' . keyC . ', ' . defC . ')';
			}
			if (expr:methodName == 'getBool') {
				local String is keyC: 'spec_string_intern("")';
				local String is defC: 'false';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'key') { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_map_get_bool(' . targetC . ', ' . keyC . ', ' . defC . ')';
			}
			if (expr:methodName == 'get') {
				local String is keyC: 'spec_string_intern("")';
				local String is defC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'key') { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_map_get(' . targetC . ', ' . keyC . ', (void*)(intptr_t)(' . defC . '))';
			}
			if (expr:methodName == 'has') {
				local String is keyC: 'spec_string_intern("")';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'key') { keyC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_map_has(' . targetC . ', ' . keyC . ')';
			}
			if (expr:methodName == 'remove') {
				local String is keyC: 'spec_string_intern("")';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'key') { keyC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_map_remove(' . targetC . ', ' . keyC . ')';
			}
			if (expr:methodName == 'keys') {
				return 'spec_map_keys(' . targetC . ')';
			}
			if (expr:methodName == 'length') {
				return '(long long)spec_map_length(' . targetC . ')';
			}
			if (expr:methodName == 'each') {
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					local Expression is fnExpr: a0:getValue();
					if (fnExpr:getKind() == 'ANON_FN') {
						return cg:generateInlineMapEach(targetC: targetC, fnExpr: fnExpr);
					}
				}
			}
		}

		# Array methods
		local Boolean is isArr: targetC == 'Array' || targetType == 'Array' || targetType:startsWith(prefix: 'Array') ||
			((targetType == '' || targetType == 'Any') && (
				expr:methodName == 'get' || expr:methodName == 'add' || expr:methodName == 'set' || expr:methodName == 'pop' ||
				expr:methodName == 'removeAt' || expr:methodName == 'slice' || expr:methodName == 'clear' || expr:methodName == 'join' ||
				expr:methodName == 'each' || expr:methodName == 'filter' || expr:methodName == 'count' || expr:methodName == 'any' ||
				expr:methodName == 'map' || expr:methodName == 'fold' ||
				(expr:methodName == 'length' && targetType != 'String' && targetType != 'string' && targetC != 'Map' && targetType != 'Map' && !targetType:startsWith(prefix: 'Map:'))
			));

		if (isArr) {
			if (expr:methodName == 'get') {
				local String is idxC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'index') { idxC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_array_get(' . targetC . ', ' . idxC . ')';
			}
			if (expr:methodName == 'set') {
				local String is idxC: '0';
				local String is itemC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'index') { idxC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'item' || arg:getName() == 'value') { itemC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_array_set(' . targetC . ', ' . idxC . ', (void*)(intptr_t)(' . itemC . '))';
			}
			if (expr:methodName == 'add') {
				local String is itemC: 'NULL';
				local Expression is itemExpr;
				if (expr:methodArgs:length() > 0) {
					local NamedArg is firstArg: expr:methodArgs:get(index: 0);
					local Expression is valExpr: firstArg:getValue();
					if (valExpr:getKind() == 'ARRAY') {
						cg:setContainerHint(t: targetType);
						itemC: cg:generateExpression(expr: valExpr);
						return 'spec_array_add_array(' . targetC . ', ' . itemC . ')';
					}
					local Boolean is savedArgA: cg:argMode;
					cg:setArgMode(m: false);
					itemC: cg:generateExpression(expr: valExpr);
					cg:setArgMode(m: savedArgA);
					itemExpr: valExpr;
				}
				local String is elemKindA: cg:containerElemKind(containerType: targetType);
				local String is addFn: 'spec_array_add';
				if (elemKindA == 'object' || elemKindA == 'string') {
					addFn: 'spec_array_add_object';
				}
				return addFn . '(' . targetC . ', (void*)(' . itemC . '))';
			}
			if (expr:methodName == 'length') {
				return 'spec_array_length(' . targetC . ')';
			}
			if (expr:methodName == 'pop') {
				local String is defC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'default') {
						local String is rawDefC: cg:generateExpression(expr: arg:getValue());
						if (targetType:startsWith(prefix: 'Array:String')) {
							defC: rawDefC;
						} else {
							defC: '(void*)(intptr_t)(' . rawDefC . ')';
						}
					}
				});
				return 'spec_array_pop(' . targetC . ', ' . defC . ')';
			}
			if (expr:methodName == 'removeAt') {
				local String is idxC: '0';
				local String is defC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'index') { idxC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: '(void*)(intptr_t)(' . cg:generateExpression(expr: arg:getValue()) . ')'; }
				});
				return 'spec_array_remove_at(' . targetC . ', ' . idxC . ', ' . defC . ')';
			}
			if (expr:methodName == 'isEmpty') {
				return '(long long)(spec_array_length(' . targetC . ') == 0)';
			}
			if (expr:methodName == 'slice') {
				local String is startC: '0';
				local String is endC: '0';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'start') { startC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'end') { endC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_array_slice(' . targetC . ', ' . startC . ', ' . endC . ')';
			}
			if (expr:methodName == 'clear') {
				return 'spec_array_clear(' . targetC . ')';
			}
			if (expr:methodName == 'indexOf') {
				local String is searchC: '""';
				local String is defC: '-1';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'search' || arg:getName() == 'needle') { searchC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == 'default') { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_array_index_of_str(' . targetC . ', ' . searchC . ', ' . defC . ')';
			}
			if (expr:methodName == 'each') {
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					local Expression is fnExpr: a0:getValue();
					if (fnExpr:getKind() == 'ANON_FN') {
						return cg:generateInlineArrayOp(mode: 'each', targetC: targetC, fnExpr: fnExpr);
					}
				}
				local String is fnC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'action') { fnC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_array_each(' . targetC . ', (void (*)(void*))(' . fnC . '))';
			}
			if (expr:methodName == 'filter') {
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					local Expression is fnExpr: a0:getValue();
					if (fnExpr:getKind() == 'ANON_FN') {
						return cg:generateInlineArrayOp(mode: 'filter', targetC: targetC, fnExpr: fnExpr);
					}
				}
				local String is fnC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'predicate') { fnC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_array_filter(' . targetC . ', (bool (*)(void*))(' . fnC . '))';
			}
			if (expr:methodName == 'count') {
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					local Expression is fnExpr: a0:getValue();
					if (fnExpr:getKind() == 'ANON_FN') {
						return cg:generateInlineArrayOp(mode: 'count', targetC: targetC, fnExpr: fnExpr);
					}
				}
				local String is fnC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'predicate') { fnC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_array_count(' . targetC . ', (bool (*)(void*))(' . fnC . '))';
			}
			if (expr:methodName == 'any') {
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					local Expression is fnExpr: a0:getValue();
					if (fnExpr:getKind() == 'ANON_FN') {
						return cg:generateInlineArrayOp(mode: 'any', targetC: targetC, fnExpr: fnExpr);
					}
				}
				local String is fnC: 'NULL';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'predicate') { fnC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_array_any(' . targetC . ', (bool (*)(void*))(' . fnC . '))';
			}
			if (expr:methodName == 'map') {
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					local Expression is fnExpr: a0:getValue();
					if (fnExpr:getKind() == 'ANON_FN') {
						return cg:generateInlineArrayOp(mode: 'map', targetC: targetC, fnExpr: fnExpr);
					}
				}
			}
			if (expr:methodName == 'fold') {
				if (expr:methodArgs:length() >= 2) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					local NamedArg is a1: expr:methodArgs:get(index: 1);
					local Expression is fnExpr: a1:getValue();
					if (fnExpr:getKind() == 'ANON_FN') {
						return cg:generateInlineArrayFold(targetC: targetC, initExpr: a0:getValue(), fnExpr: fnExpr);
					}
				}
			}
			if (expr:methodName == 'join') {
				local String is sepC: '""';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == 'separator' || sepC == '""') { sepC: cg:generateExpression(expr: arg:getValue()); }
				});
				return 'spec_array_join(' . targetC . ', ' . sepC . ')';
			}
		}

		# Buf floor primitives (body-less, bound to the C runtime)
		if (targetC == 'Buf' && expr:methodName == 'bufLength' && expr:methodArgs:length() > 0) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			return 'spec_buf_length(' . cg:generateExpression(expr: bArg:getValue()) . ')';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufGetByte' && expr:methodArgs:length() > 2) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			local NamedArg is idxArg: expr:methodArgs:get(index: 1);
			local NamedArg is defArg: expr:methodArgs:get(index: 2);
			return 'spec_buf_get_byte(' . cg:generateExpression(expr: bArg:getValue()) . ', ' .
				cg:generateExpression(expr: idxArg:getValue()) . ', ' .
				cg:generateExpression(expr: defArg:getValue()) . ', (SpecClosure*)NULL)';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufCopy' && expr:methodArgs:length() > 0) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			return 'spec_string_copy(' . cg:generateExpression(expr: bArg:getValue()) . ')';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufSubstring' && expr:methodArgs:length() > 2) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			local NamedArg is startArg: expr:methodArgs:get(index: 1);
			local NamedArg is endArg: expr:methodArgs:get(index: 2);
			return 'spec_string_substring(' . cg:generateExpression(expr: bArg:getValue()) . ', ' .
				cg:generateExpression(expr: startArg:getValue()) . ', ' .
				cg:generateExpression(expr: endArg:getValue()) . ')';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufIndexOf' && expr:methodArgs:length() > 2) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			local NamedArg is needleArg: expr:methodArgs:get(index: 1);
			local NamedArg is defArg: expr:methodArgs:get(index: 2);
			return 'spec_string_index_of(' . cg:generateExpression(expr: bArg:getValue()) . ', ' .
				cg:generateExpression(expr: needleArg:getValue()) . ', ' .
				cg:generateExpression(expr: defArg:getValue()) . ')';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufReplace' && expr:methodArgs:length() > 2) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			local NamedArg is searchArg: expr:methodArgs:get(index: 1);
			local NamedArg is replArg: expr:methodArgs:get(index: 2);
			return 'spec_string_replace_all(' . cg:generateExpression(expr: bArg:getValue()) . ', ' .
				cg:generateExpression(expr: searchArg:getValue()) . ', ' .
				cg:generateExpression(expr: replArg:getValue()) . ')';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufTrim' && expr:methodArgs:length() > 0) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			return 'spec_string_trim(' . cg:generateExpression(expr: bArg:getValue()) . ')';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufIsDigit' && expr:methodArgs:length() > 0) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			return 'spec_string_is_digit(' . cg:generateExpression(expr: bArg:getValue()) . ')';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufIsAlpha' && expr:methodArgs:length() > 0) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			return 'spec_string_is_alpha(' . cg:generateExpression(expr: bArg:getValue()) . ')';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufIsWhitespace' && expr:methodArgs:length() > 0) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			return 'spec_string_is_whitespace(' . cg:generateExpression(expr: bArg:getValue()) . ')';
		}
		if (targetC == 'Buf' && expr:methodName == 'bufCountLeading' && expr:methodArgs:length() > 1) {
			local NamedArg is bArg: expr:methodArgs:get(index: 0);
			local NamedArg is searchArg: expr:methodArgs:get(index: 1);
			return 'spec_string_count_leading(' . cg:generateExpression(expr: bArg:getValue()) . ', ' .
				cg:generateExpression(expr: searchArg:getValue()) . ')';
		}

		# String methods
		if (expr:methodName == 'length' && (targetType == 'String' || targetType == 'string')) {
			return 'spec_string_length(' . targetC . ')';
		}
		if (expr:methodName == 'split') {
			local String is delimC: '""';
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:getName() == 'delimiter' || delimC == '""') { delimC: cg:generateExpression(expr: arg:getValue()); }
			});
			return 'spec_string_split(' . targetC . ', ' . delimC . ')';
		}
		if (expr:methodName == 'lines') {
			return 'spec_string_lines(' . targetC . ')';
		}

		# Enum methods
		if (self:allEnumNames:has(key: targetC) && expr:methodName == 'values') {
			return targetC . '_values()';
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

}
