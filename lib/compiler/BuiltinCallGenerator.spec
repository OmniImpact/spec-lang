#! Package compiler
#! Pure Spec compiler implementation: BuiltinCallGenerator for standard library and runtime intrinsic calls.

## Translates standard library and runtime builtin method calls into C11 runtime functions.
class BuiltinCallGenerator{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:meta:*,
		compiler:CBackendUtils,
		compiler:CodeGenerator
	];

	local CBackendUtils is utils;
	local Map of String to String is allEnumNames: Map:init();

	replace local Function is init(){
		self:utils: CBackendUtils:init();
		self:allEnumNames: Map:init();
	}

	replace local Function is setEnumNames(Map of String to String is names){
		self:allEnumNames: names;
	}

	## Generates C code for a standard library or runtime intrinsic call.
	##
	## @param expr: AST [Expression] node of kind CALL.
	## @param targetC: Generated C expression for method target.
	## @param targetType: Inferred type name of method target.
	## @param cg: Reference to parent [CodeGenerator].
	## @return: C code string if builtin call, or empty string if not a builtin.
	replace local Function of String is generateBuiltinCall(Expression is expr, String is targetC, String is targetType, CodeGenerator is cg){
		# Output:line
		if (expr:methodName == "line" && expr:methodArgs:length() > 0) {
			local NamedArg is firstArg: expr:methodArgs:get(index: 0);
			local String is valC: cg:generateExpression(expr: firstArg:getValue());
			local String is strC: cg:wrapToString(expr: firstArg:getValue(), exprC: valC);
			return "printf(\"%s\\n\", " . strC . ")";
		}

		# Intrinsic loop runner: While:run(loop, control)
		if (targetC == "While" && expr:methodName == "run" && expr:methodArgs:length() > 0) {
			local NamedArg is loopArg: expr:methodArgs:get(index: 0);
			local Expression is loopVal: loopArg:getValue();
			local String is loopC: cg:generateExpression(expr: loopVal);
			local String is loopClass: cg:inferTargetType(expr: loopVal);
			if (loopClass == "" && loopVal:getKind() == "CALL") {
				local Expression is mt: loopVal:methodTarget;
				loopClass: cg:generateExpression(expr: mt);
			}
			local String is ctrlC: "NULL";
			if (expr:methodArgs:length() > 1) {
				local NamedArg is ctrlArg: expr:methodArgs:get(index: 1);
				ctrlC: cg:generateExpression(expr: ctrlArg:getValue());
			}
			return "({ void* _lp = (void*)(" . loopC . "); SpecLoopControl* _ctrl = (SpecLoopControl*)(" . ctrlC . "); while (" . loopClass . "_evaluate((void*)_lp)) { if (!" . loopClass . "_iteration((void*)_lp, _ctrl) || (_ctrl && _ctrl->stopped)) break; } if (_ctrl && _ctrl->on_complete) { _ctrl->on_complete(_ctrl->callback, _ctrl); } })";
		}

		# Input static methods
		if (targetC == "Input" && expr:methodName == "prompt" && expr:methodArgs:length() > 0) {
			local NamedArg is promptArg: expr:methodArgs:get(index: 0);
			local Expression is promptVal: promptArg:getValue();
			local String is handlerC: cg:generateExpression(expr: promptVal);
			local String is handlerClass: cg:inferTargetType(expr: promptVal);
			if (handlerClass == "" && promptVal:getKind() == "CALL") {
				local Expression is mt: promptVal:methodTarget;
				handlerClass: cg:generateExpression(expr: mt);
			}
			return "({ char _buf[256]; char* _res = \"s\"; if (fgets(_buf, sizeof(_buf), stdin)) { size_t _len = strlen(_buf); if (_len > 0 && _buf[_len - 1] == '\\n') _buf[_len - 1] = '\\0'; _res = strdup(_buf); } " . handlerClass . "_onInput((void*)(" . handlerC . "), _res); })";
		}

		# LoopControl methods
		if (targetC == "LoopControl" && expr:methodName == "init") {
			if (expr:methodArgs:length() == 0) {
				return "LoopControl_new()";
			}
			local NamedArg is cbArg: expr:methodArgs:get(index: 0);
			local Expression is cbVal: cbArg:getValue();
			local String is cbC: cg:generateExpression(expr: cbVal);
			local String is cbClass: cg:inferTargetType(expr: cbVal);
			if (cbClass == "" && cbVal:getKind() == "CALL") {
				local Expression is mt: cbVal:methodTarget;
				cbClass: cg:generateExpression(expr: mt);
			}
			return "({ SpecLoopControl* _c = LoopControl_new(); _c->callback = (void*)(" . cbC . "); _c->on_complete = (void (*)(void*, struct SpecLoopControl*))" . cbClass . "_onComplete; _c; })";
		}
		if (expr:methodName == "stop") {
			return "LoopControl_stop(" . targetC . ")";
		}

		# Process static methods
		if (targetC == "Process") {
			if (expr:methodName == "execute") {
				local String is cmdC: "\"\"";
				local String is argsC: "NULL";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "command") { cmdC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "args") { argsC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_process_execute(" . cmdC . ", " . argsC . ")";
			}
			if (expr:methodName == "sleep") {
				local String is msC: "0";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "milliseconds") { msC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_process_sleep(" . msC . ")";
			}
		}

		# File static methods
		if (targetC == "File") {
			if (expr:methodName == "exists") {
				local String is pathC: "\"\"";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "path") { pathC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_file_exists(" . pathC . ")";
			}
			if (expr:methodName == "read") {
				local String is pathC: "\"\"";
				local String is defC: "\"\"";
				local String is onSuccC: "NULL";
				local String is onErrC: "NULL";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "path") { pathC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "default") { defC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "onSuccess") { onSuccC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "onError") { onErrC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_file_read(" . pathC . ", " . defC . ", (void (*)(const char*))(" . onSuccC . "), (void (*)(const char*))(" . onErrC . "))";
			}
			if (expr:methodName == "readAsync") {
				local String is pathC: "\"\"";
				local String is defC: "\"\"";
				local String is onSuccC: "NULL";
				local String is onErrC: "NULL";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "path") { pathC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "default") { defC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "onSuccess") { onSuccC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "onError") { onErrC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_file_read_async(" . pathC . ", " . defC . ", (void (*)(const char*))(" . onSuccC . "), (void (*)(const char*))(" . onErrC . "))";
			}
			if (expr:methodName == "write") {
				local String is pathC: "\"\"";
				local String is contentC: "\"\"";
				local String is onSuccC: "NULL";
				local String is onErrC: "NULL";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "path") { pathC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "content") { contentC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "onSuccess") { onSuccC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "onError") { onErrC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_file_write(" . pathC . ", " . contentC . ", (void (*)(long long))(" . onSuccC . "), (void (*)(const char*))(" . onErrC . "))";
			}
			if (expr:methodName == "writeAsync") {
				local String is pathC: "\"\"";
				local String is contentC: "\"\"";
				local String is onSuccC: "NULL";
				local String is onErrC: "NULL";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "path") { pathC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "content") { contentC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "onSuccess") { onSuccC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "onError") { onErrC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_file_write_async(" . pathC . ", " . contentC . ", (void (*)(long long))(" . onSuccC . "), (void (*)(const char*))(" . onErrC . "))";
			}
		}

		# Math static methods
		if (targetC == "Math" || targetC == "math") {
			if (expr:methodName == "round") {
				local String is valC: "0.0";
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					valC: cg:generateExpression(expr: a0:getValue());
				}
				return "spec_math_round(" . valC . ")";
			}
			if (expr:methodName == "floor") {
				local String is valC: "0.0";
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					valC: cg:generateExpression(expr: a0:getValue());
				}
				return "spec_math_floor(" . valC . ")";
			}
			if (expr:methodName == "ceil" || expr:methodName == "ceiling") {
				local String is valC: "0.0";
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					valC: cg:generateExpression(expr: a0:getValue());
				}
				return "spec_math_ceil(" . valC . ")";
			}
			if (expr:methodName == "random") {
				local String is minC: "0.0";
				local String is maxC: "1.0";
				if (expr:methodArgs:length() > 0) {
					local NamedArg is a0: expr:methodArgs:get(index: 0);
					minC: cg:generateExpression(expr: a0:getValue());
				}
				if (expr:methodArgs:length() > 1) {
					local NamedArg is a1: expr:methodArgs:get(index: 1);
					maxC: cg:generateExpression(expr: a1:getValue());
				}
				return "spec_math_random(" . minC . ", " . maxC . ")";
			}
		}

		# Map methods
		if (targetC == "Map" || expr:methodName == "set" || expr:methodName == "getString" || expr:methodName == "has" || expr:methodName == "keys") {
			if (expr:methodName == "init") {
				return "spec_map_new()";
			}
			if (expr:methodName == "set") {
				local String is keyC: "\"\"";
				local String is valC: "\"\"";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "key") { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "value") { valC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_map_set(" . targetC . ", " . keyC . ", " . valC . ")";
			}
			if (expr:methodName == "getString") {
				local String is keyC: "\"\"";
				local String is defC: "\"\"";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "key") { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "default") { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_map_get_string(" . targetC . ", " . keyC . ", " . defC . ")";
			}
			if (expr:methodName == "getInt") {
				local String is keyC: "\"\"";
				local String is defC: "0";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "key") { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "default") { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_map_get_int(" . targetC . ", " . keyC . ", " . defC . ")";
			}
			if (expr:methodName == "getFloat") {
				local String is keyC: "\"\"";
				local String is defC: "0.0";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "key") { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "default") { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_map_get_float(" . targetC . ", " . keyC . ", " . defC . ")";
			}
			if (expr:methodName == "getBool") {
				local String is keyC: "\"\"";
				local String is defC: "false";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "key") { keyC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "default") { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_map_get_bool(" . targetC . ", " . keyC . ", " . defC . ")";
			}
			if (expr:methodName == "get") {
				local String is keyC: "\"\"";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "key") { keyC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_map_get(" . targetC . ", " . keyC . ")";
			}
			if (expr:methodName == "has") {
				local String is keyC: "\"\"";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "key") { keyC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_map_has(" . targetC . ", " . keyC . ")";
			}
			if (expr:methodName == "remove") {
				local String is keyC: "\"\"";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "key") { keyC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_map_remove(" . targetC . ", " . keyC . ")";
			}
			if (expr:methodName == "keys") {
				return "spec_map_keys(" . targetC . ")";
			}
			if (expr:methodName == "length") {
				return "(long long)spec_map_length(" . targetC . ")";
			}
		}

		# Array methods
		local Boolean is isArr: targetC == "Array" || targetType == "Array" || targetType:startsWith(prefix: "Array") ||
			expr:methodName == "get" || expr:methodName == "add" || expr:methodName == "pop" ||
			expr:methodName == "removeAt" || expr:methodName == "slice" || expr:methodName == "clear" ||
			expr:methodName == "each" || expr:methodName == "filter" || expr:methodName == "count" || expr:methodName == "any" ||
			(expr:methodName == "length" && targetType != "String" && targetType != "string" && targetC != "Map" && targetType != "Map");

		if (isArr) {
			if (expr:methodName == "get") {
				local String is idxC: "0";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "index") { idxC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_array_get(" . targetC . ", " . idxC . ")";
			}
			if (expr:methodName == "add") {
				local String is itemC: "NULL";
				if (expr:methodArgs:length() > 0) {
					local NamedArg is firstArg: expr:methodArgs:get(index: 0);
					local Expression is valExpr: firstArg:getValue();
					itemC: cg:generateExpression(expr: valExpr);
					if (valExpr:getKind() == "ARRAY") {
						return "spec_array_add_array(" . targetC . ", " . itemC . ")";
					}
				}
				return "spec_array_add(" . targetC . ", (void*)(" . itemC . "))";
			}
			if (expr:methodName == "length") {
				return "spec_array_length(" . targetC . ")";
			}
			if (expr:methodName == "pop") {
				return "spec_array_pop(" . targetC . ", NULL)";
			}
			if (expr:methodName == "removeAt") {
				local String is idxC: "0";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "index") { idxC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_array_remove_at(" . targetC . ", " . idxC . ")";
			}
			if (expr:methodName == "slice") {
				local String is startC: "0";
				local String is endC: "0";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "start") { startC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "end") { endC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_array_slice(" . targetC . ", " . startC . ", " . endC . ")";
			}
			if (expr:methodName == "clear") {
				return "spec_array_clear(" . targetC . ")";
			}
			if (expr:methodName == "indexOf") {
				local String is searchC: "\"\"";
				local String is defC: "-1";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "search") { searchC: cg:generateExpression(expr: arg:getValue()); }
					if (arg:getName() == "default") { defC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_array_index_of_str(" . targetC . ", " . searchC . ", " . defC . ")";
			}
			if (expr:methodName == "each") {
				local String is fnC: "NULL";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "action") { fnC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_array_each(" . targetC . ", (void (*)(void*))(" . fnC . "))";
			}
			if (expr:methodName == "filter") {
				local String is fnC: "NULL";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "predicate") { fnC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_array_filter(" . targetC . ", (bool (*)(void*))(" . fnC . "))";
			}
			if (expr:methodName == "count") {
				local String is fnC: "NULL";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "predicate") { fnC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_array_count(" . targetC . ", (bool (*)(void*))(" . fnC . "))";
			}
			if (expr:methodName == "any") {
				local String is fnC: "NULL";
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:getName() == "predicate") { fnC: cg:generateExpression(expr: arg:getValue()); }
				});
				return "spec_array_any(" . targetC . ", (bool (*)(void*))(" . fnC . "))";
			}
		}

		# String methods
		if (expr:methodName == "length" && (targetType == "String" || targetType == "string")) {
			return "(long long)strlen(" . targetC . ")";
		}
		if (expr:methodName == "charAt") {
			local String is idxC: "0";
			local String is defC: "\"\"";
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:getName() == "index") { idxC: cg:generateExpression(expr: arg:getValue()); }
				if (arg:getName() == "default") { defC: cg:generateExpression(expr: arg:getValue()); }
			});
			return "spec_str_char_at(" . targetC . ", " . idxC . ", " . defC . ")";
		}
		if (expr:methodName == "substring") {
			local String is startC: "0";
			local String is endC: "0";
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:getName() == "start") { startC: cg:generateExpression(expr: arg:getValue()); }
				if (arg:getName() == "end") { endC: cg:generateExpression(expr: arg:getValue()); }
			});
			return "spec_str_substring(" . targetC . ", " . startC . ", " . endC . ")";
		}
		if (expr:methodName == "startsWith") {
			local String is pfxC: "\"\"";
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:getName() == "prefix") { pfxC: cg:generateExpression(expr: arg:getValue()); }
			});
			return "spec_str_starts_with(" . targetC . ", " . pfxC . ")";
		}
		if (expr:methodName == "trim") {
			return "spec_str_trim(" . targetC . ")";
		}
		if (expr:methodName == "isDigit") {
			return "spec_str_is_digit(" . targetC . ")";
		}
		if (expr:methodName == "isAlpha") {
			return "spec_str_is_alpha(" . targetC . ")";
		}
		if (expr:methodName == "isWhitespace") {
			return "spec_str_is_whitespace(" . targetC . ")";
		}
		if (expr:methodName == "lines") {
			return "spec_str_lines(" . targetC . ")";
		}
		if (expr:methodName == "countLeading") {
			local String is searchC: "\"\"";
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:getName() == "search") { searchC: cg:generateExpression(expr: arg:getValue()); }
			});
			return "spec_str_count_leading(" . targetC . ", " . searchC . ")";
		}
		if (expr:methodName == "indexOf") {
			local String is needleC: "\"\"";
			local String is defC: "-1";
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:getName() == "needle") { needleC: cg:generateExpression(expr: arg:getValue()); }
				if (arg:getName() == "default") { defC: cg:generateExpression(expr: arg:getValue()); }
			});
			return "spec_str_index_of(" . targetC . ", " . needleC . ", " . defC . ")";
		}

		# Enum methods
		if (self:allEnumNames:has(key: targetC) && expr:methodName == "values") {
			return targetC . "_values()";
		}
		if (self:allEnumNames:has(key: targetType)) {
			if (expr:methodName == "name") {
				return targetType . "_name(" . targetC . ")";
			}
			if (expr:methodName == "value") {
				return targetType . "_value(" . targetC . ")";
			}
			if (expr:methodName == "ordinal") {
				return targetType . "_ordinal(" . targetC . ")";
			}
		}

		return "";
	}

}
