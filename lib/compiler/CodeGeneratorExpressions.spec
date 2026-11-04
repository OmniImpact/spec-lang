#! Package compiler
#! Expression-level C generation: literals, calls, closures, tagged-enum constructors, and generic casts.
#! Group fragment merged into CodeGenerator at load time (see Loader).

## Expression-level C generation: literals, calls, closures, tagged-enum constructors, and generic casts.
Class is CodeGeneratorExpressions{

	## Load-time grouping: members merge into CodeGenerator.
	local Array of String is group: [CodeGenerator];

	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:Parameter,
		base:reflect:Member,
		base:reflect:ClassInfo,
		base:meta:*
	];

	Function of String is generateExpression(Expression is expr){
		local String is kind: expr:getKind();

		when (kind) {
			is "ARRAY": {
				local String is res: "({ SpecArray* _arr = spec_array_new();";
				expr:arrayItems:each(action: local Function(Expression is item){
					local String is itemC: self:generateExpression(expr: item);
					res: res . " spec_array_add(_arr, (void*)(" . itemC . "));";
				});
				res: res . " _arr; })";
				return res;
			}
			is "MAP": {
				local String is res: "({ SpecMap* _map = spec_map_new();";
				local Int is idx: 0;
				expr:mapKeys:each(action: local Function(Expression is kExpr){
					local Expression is vExpr: expr:mapValues:get(index: idx);
					local String is kC: self:generateExpression(expr: kExpr);
					local String is vC: self:generateExpression(expr: vExpr);
					if (self:isStringExpr(expr: vExpr)) {
						res: res . " spec_map_set(_map, " . kC . ", " . vC . ");";
					} else {
						res: res . " spec_map_set_any(_map, " . kC . ", (void*)(intptr_t)(" . vC . "));";
					}
					idx: idx + 1;
				});
				res: res . " _map; })";
				return res;
			}
			is "STRING": {
				return "\"" . self:escapeString(s: expr:stringValue) . "\"";
			}
			is "NUMBER": {
				if (expr:stringValue != "") {
					return expr:stringValue;
				}
				return "0";
			}
			is "FLOAT": {
				if (expr:stringValue != "") {
					return expr:stringValue;
				}
				return "0.0";
			}
			is "BOOL": {
				return if (expr:boolValue) "true" else "false";
			}
			is "IDENT": {
				local String is name: expr:stringValue;
				if (name == "self" || name == "true" || name == "false") {
					return name;
				}
				if (self:allEnumVariants:has(key: name)) {
					local String is enumName: self:allEnumVariants:getString(key: name, default: "");
					if (self:allTaggedEnums:has(key: enumName)) {
						return enumName . "_" . self:cIdent(name: name) . "_ctor()";
					}
					return enumName . "_" . self:cIdent(name: name);
				}
				if (self:localVars:has(key: name)) {
					return self:cIdent(name: name);
				}
				if (self:fieldTypes:has(key: name)) {
					return "self->" . self:cIdent(name: name);
				}
				return self:cIdent(name: name);
			}
			is "PATH": {
				local Array of String is segs: expr:pathSegments;
				if (segs:length() == 1) {
					return segs:get(index: 0);
				}
				if (segs:length() >= 2) {
					local String is root: segs:get(index: 0);
					if (self:allEnumNames:has(key: root)) {
						if (self:allTaggedEnums:has(key: root)) {
							return root . "_" . self:cIdent(name: segs:get(index: 1)) . "_ctor()";
						}
						return root . "_" . self:cIdent(name: segs:get(index: 1));
					}
					local String is rootC: self:cIdent(name: root);
					if (!self:localVars:has(key: root) && self:fieldTypes:has(key: root)) {
						rootC: "self->" . rootC;
					}
					local PathChainLoop is pathLoop: PathChainLoop:init(segs: segs, rootC: rootC, utils: self:utils);
					While:run(loop: pathLoop);
					local String is resC: pathLoop:res;
					if (root != "self") {
						local String is resolvedT: expr:getResolvedType();
						local String is rootT: self:localVars:getString(key: root, default: "");
						if (rootT:contains(needle: ":") && !rootT:startsWith(prefix: "Array:") && !rootT:startsWith(prefix: "Map:") && resolvedT != "" && resolvedT != "Any") {
							local String is castT: self:cTypeFor(typeName: resolvedT);
							resC: "((" . castT . ")(intptr_t)(" . resC . "))";
						}
					}
					return resC;
				}
				return "";
			}
			is "BINARY": {
				local String is op: expr:binaryOp;
				when (op) {
					is ".": {
						local String is leftC: self:generateExpression(expr: expr:leftExpr);
						local String is rightC: self:generateExpression(expr: expr:rightExpr);
						local String is leftWrap: self:wrapToString(expr: expr:leftExpr, exprC: leftC);
						local String is rightWrap: self:wrapToString(expr: expr:rightExpr, exprC: rightC);
						return "spec_str_concat(" . leftWrap . ", " . rightWrap . ")";
					}
					is "is", "==": {
						local String is leftC: self:generateExpression(expr: expr:leftExpr);
						local String is rightC: self:generateExpression(expr: expr:rightExpr);
						if (self:isStringExpr(expr: expr:leftExpr) || self:isStringExpr(expr: expr:rightExpr)) {
							return "spec_str_equals(" . leftC . ", " . rightC . ")";
						}
						return "((" . leftC . ") == (" . rightC . "))";
					}
					is "!=": {
						local String is leftC: self:generateExpression(expr: expr:leftExpr);
						local String is rightC: self:generateExpression(expr: expr:rightExpr);
						if (self:isStringExpr(expr: expr:leftExpr) || self:isStringExpr(expr: expr:rightExpr)) {
							return "(!spec_str_equals(" . leftC . ", " . rightC . "))";
						}
						return "((" . leftC . ") != (" . rightC . "))";
					}
					is "<", "<=", ">", ">=", "+", "-", "*", "/", "%", "&&", "||", "&", "|", "^", "<<", ">>": {
						local String is leftC: self:generateExpression(expr: expr:leftExpr);
						local String is rightC: self:generateExpression(expr: expr:rightExpr);
						return "((" . leftC . ") " . op . " (" . rightC . "))";
					}
					else: {
						return "0";
					}
				}
			}
			is "INDEX": {
				local String is targetC: self:generateExpression(expr: expr:leftExpr);
				local String is indexC: self:generateExpression(expr: expr:rightExpr);
				local String is targetType: self:inferTargetType(expr: expr:leftExpr);
				if (targetType:startsWith(prefix: "Map:") || targetType == "Map") {
					local String is valType: "String";
					if (targetType:startsWith(prefix: "Map:")) {
						local String is afterMap: targetType:substring(start: 4, end: targetType:length());
						local Int is colonIdx: afterMap:indexOf(needle: ":", default: -1);
						if (colonIdx >= 0 && colonIdx + 1 < afterMap:length()) {
							valType: afterMap:substring(start: colonIdx + 1, end: afterMap:length());
						}
					}
					if (valType == "String" || valType == "string") {
						return "spec_map_get_string(" . targetC . ", " . indexC . ", \"\")";
					}
					if (valType == "Int" || valType == "int") {
						return "spec_map_get_int(" . targetC . ", " . indexC . ", 0)";
					}
					if (valType == "Float" || valType == "float") {
						return "spec_map_get_float(" . targetC . ", " . indexC . ", 0.0)";
					}
					if (valType == "Boolean" || valType == "bool") {
						return "spec_map_get_bool(" . targetC . ", " . indexC . ", false)";
					}
					local String is valCType: self:cTypeFor(typeName: valType);
					return "((" . valCType . ")(intptr_t)spec_map_get(" . targetC . ", " . indexC . ", NULL))";
				}
				if (targetType == "Array:String" || targetType == "Array of String") {
					return "((const char*)spec_array_get(" . targetC . ", (size_t)(" . indexC . ")))";
				}
				if (targetType:startsWith(prefix: "Array:") && targetType:length() > 6) {
					local String is elemT: targetType:substring(start: 6, end: targetType:length());
					local String is elemCType: self:cTypeFor(typeName: elemT);
					return "((" . elemCType . ")(intptr_t)spec_array_get(" . targetC . ", (size_t)(" . indexC . ")))";
				}
				return "((long long)(intptr_t)spec_array_get(" . targetC . ", (size_t)(" . indexC . ")))";
			}
			is "CAST": {
				local String is innerC: self:generateExpression(expr: expr:leftExpr);
				local String is target: expr:stringValue;
				local String is srcT: self:inferTargetType(expr: expr:leftExpr);
				local String is digitsC: "0";
				if (expr:castArgs:length() > 0) {
					digitsC: self:generateExpression(expr: expr:castArgs:get(index: 0));
				}
				when (target) {
					is "Hex": {
						if (srcT == "String" || srcT == "string") {
							return "spec_parse_base(" . innerC . ", 16, 0)";
						}
						return "spec_int_to_base(" . innerC . ", 16, " . digitsC . ")";
					}
					is "Bin": {
						if (srcT == "String" || srcT == "string") {
							return "spec_parse_base(" . innerC . ", 2, 0)";
						}
						return "spec_int_to_base(" . innerC . ", 2, " . digitsC . ")";
					}
					is "Oct": {
						if (srcT == "String" || srcT == "string") {
							return "spec_parse_base(" . innerC . ", 8, 0)";
						}
						return "spec_int_to_base(" . innerC . ", 8, " . digitsC . ")";
					}
					is "Any": {
						return innerC;
					}
					is "Int", "int": {
						if (srcT == "String" || srcT == "string") {
							return "spec_parse_base(" . innerC . ", 10, 0)";
						}
						if (srcT == "Float" || srcT == "float") {
							return "((long long)(" . innerC . "))";
						}
						return innerC;
					}
					is "Float", "float": {
						return "((double)(" . innerC . "))";
					}
					is "String", "string": {
						if (srcT == "Int" || srcT == "int") {
							return "spec_to_string_int(" . innerC . ")";
						}
						if (srcT == "Float" || srcT == "float") {
							return "spec_to_string_float(" . innerC . ")";
						}
						if (srcT == "Boolean" || srcT == "bool") {
							return "spec_to_string_bool(" . innerC . ")";
						}
						if (self:allClassNames:has(key: srcT) && !self:allEnumNames:has(key: srcT) && !self:utils:isBuiltinClass(name: srcT)) {
							return "spec_type_name(" . innerC . ")";
						}
						return innerC;
					}
					else: {
						if (self:allClassNames:has(key: target) && !self:allEnumNames:has(key: target) && !self:isBuiltinClass(name: target)) {
							return "((" . target . "*)spec_cast_check(" . innerC . ", \"" . target . "\"))";
						}
						return innerC;
					}
				}
			}
			is "UNARY": {
				local String is innerC: self:generateExpression(expr: expr:unaryExpr);
				return "(" . expr:unaryOp . "(" . innerC . "))";
			}
			is "CALL": {
				local String is targetC: self:generateExpression(expr: expr:methodTarget);

				local String is targetType: self:inferTargetType(expr: expr:methodTarget);
				local String is fieldKey: targetC;
				if (targetC:startsWith(prefix: "self->")) {
					fieldKey: targetC:substring(start: 6, end: targetC:length());
				}
				if (targetType == "") {
					targetType: self:localVars:getString(key: fieldKey, default: "");
				}
				if (targetType == "") {
					targetType: self:fieldTypes:getString(key: fieldKey, default: "");
				}

				local String is builtinC: self:builtins:generateBuiltinCall(expr: expr, targetC: targetC, targetType: targetType, cg: self);
				if (builtinC != "") {
					return builtinC;
				}

				# Direct invocation of a Function variable or field: fnVar(arg1, arg2)
				if (targetC == "self" && (self:localVars:has(key: expr:methodName) || self:fieldTypes:has(key: expr:methodName))) {
					local String is fnVarT: self:localVars:getString(key: expr:methodName, default: self:fieldTypes:getString(key: expr:methodName, default: ""));
					if (fnVarT:startsWith(prefix: "Function")) {
						local String is fnPtrC: if (self:localVars:has(key: expr:methodName)) self:cIdent(name: expr:methodName) else "self->" . self:cIdent(name: expr:methodName);
						local String is retTName: if (fnVarT:startsWith(prefix: "Function:") && fnVarT:length() > 9) fnVarT:substring(start: 9, end: fnVarT:length()) else "Void";
						local String is retCType: self:cTypeFor(typeName: retTName);
						local String is pTypesC: "void*";
						local String is cArgsC: "_cls->env";
						expr:methodArgs:each(action: local Function(NamedArg is arg){
							local String is aValC: self:generateExpression(expr: arg:getValue());
							local String is aT: self:inferTargetType(expr: arg:getValue());
							local String is aCType: self:cTypeFor(typeName: aT);
							pTypesC: pTypesC . ", " . aCType;
							cArgsC: cArgsC . ", " . aValC;
						});
						return "({ SpecClosure* _cls = (SpecClosure*)(" . fnPtrC . "); if (!_cls || !_cls->fn) spec_panic(\"Invocation of null Function\"); ((" . retCType . " (*)(" . pTypesC . "))_cls->fn)(" . cArgsC . "); })";
					}
				}

				# Tagged enum variant constructor invocation: EnumName:Variant(...) or Variant(...)
				if (self:allEnumVariants:has(key: expr:methodName) && (self:allTaggedEnums:has(key: targetC) || targetC == "self")) {
					local String is eName: self:allEnumVariants:getString(key: expr:methodName, default: "");
					if (self:allTaggedEnums:has(key: eName)) {
						local Member is vMem: self:lookupEnumVariant(enumName: eName, variantName: expr:methodName);
						local Array of Parameter is vParams: vMem:getParameters();
						local String is vArgsC: "";
						local Int is pIdx: 0;
						vParams:each(action: local Function(Parameter is p){
							if (pIdx > 0) { vArgsC: vArgsC . ", "; }
							local String is pName: p:getName();
							local Boolean is matched: false;
							local String is argC: "0";
							expr:methodArgs:each(action: local Function(NamedArg is a){
								if (!matched && a:getName() == pName && pName != "") {
									argC: self:generateExpression(expr: a:getValue());
									matched: true;
								}
							});
							if (!matched && pIdx < expr:methodArgs:length()) {
								local NamedArg is posArg: expr:methodArgs:get(index: pIdx);
								argC: self:generateExpression(expr: posArg:getValue());
								matched: true;
							}
							vArgsC: vArgsC . argC;
							pIdx: pIdx + 1;
						});
						return eName . "_" . self:cIdent(name: expr:methodName) . "(" . vArgsC . ")";
					}
				}

				# ClassInfo constructor or static method invocation: ClassName:init(...) or ClassName:method(...)
				if (self:allClassNames:has(key: targetC) && !self:allEnumNames:has(key: targetC)) {
					local String is argsJoined: self:formatCallArguments(className: targetC, methodName: expr:methodName, args: expr:methodArgs);
					if (expr:methodName == "init") {
						# The declaring class may be an ancestor; dispatch to it.
						local String is initCls: self:findMethodImplementingClass(className: targetC, methodName: "init", paramCount: -1);
						if (initCls == "" || initCls == targetC) {
							return "({ " . targetC . "* _inst = " . targetC . "_new(); " . targetC . "_init(_inst" . argsJoined . "); _inst; })";
						}
						local String is initArgs: self:formatCallArguments(className: initCls, methodName: "init", args: expr:methodArgs);
						return "({ " . targetC . "* _inst = " . targetC . "_new(); " . initCls . "_init((" . initCls . "*)_inst" . initArgs . "); _inst; })";
					}
					local Member is mDef: self:lookupMethodMember(className: targetC, methodName: expr:methodName);
					if (mDef:getKind() == "METHOD") {
						local String is mRetType: self:resolveReturnType(t: mDef:getType());
						if (mRetType != "" && mRetType != "Void" && mRetType != "void") {
							return targetC . "_" . expr:methodName . "(NULL" . argsJoined . ")";
						}
					}
					return "({ " . targetC . "* _inst = " . targetC . "_new(); " . targetC . "_" . expr:methodName . "(_inst" . argsJoined . "); _inst; })";
				}

				# Instance method invocation
				local String is objType: targetType;
				if (objType == "") {
					objType: self:localVars:getString(key: targetC, default: "");
				}
				if (objType == "") {
					objType: self:fieldTypes:getString(key: targetC, default: "");
				}
				if (objType == "" || objType == "Any" || targetC == "self") {
					objType: self:currentClassName;
				}
				local String is fullObjType: objType;

				# Dynamic dispatch on the root type: an Any-typed receiver invokes
				# through its own vtable (root-contract members and any virtual
				# method), instead of being retyped to the enclosing class.
				if (objType == "Any" && self:methodSlots:has(key: expr:methodName)) {
					local Member is anyM: self:lookupMethodMember(className: "Any", methodName: expr:methodName);
					if (anyM:getKind() == "METHOD") {
						local String is slotC: self:methodSlots:getString(key: expr:methodName, default: "0");
						local String is retT: self:resolveReturnType(t: anyM:getType());
						local String is argsC: "";
						expr:methodArgs:each(action: local Function(NamedArg is arg){
							argsC: argsC . ", " . self:generateExpression(expr: arg:getValue());
						});
						if (retT == "void") {
							return "((void (*)(Any*))((Any*)" . targetC . ")->_vtable[" . slotC . "])((Any*)" . targetC . argsC . ")";
						}
						return "((" . retT . " (*)(Any*))((Any*)" . targetC . ")->_vtable[" . slotC . "])((Any*)" . targetC . argsC . ")";
					}
				}

				if (objType:startsWith(prefix: "Array:")) {
					objType: "Array";
				} else if (objType:startsWith(prefix: "Map:")) {
					objType: "Map";
				} else if (objType:contains(needle: ":")) {
					local Array of String is parts: objType:split(delimiter: ":");
					objType: parts:get(index: 0);
				}
				local String is argsC: self:formatCallArguments(className: fullObjType, methodName: expr:methodName, args: expr:methodArgs);
				local String is callStr: "";
				if (self:overriddenMethods:has(key: expr:methodName) && self:allClassNames:has(key: objType) && !self:allEnumNames:has(key: objType) && !self:isBuiltinClass(name: objType) && self:methodSlots:has(key: expr:methodName)) {
					# Virtual dispatch through the receiver's vtable slot.
					local Member is vm: self:lookupMethodMember(className: objType, methodName: expr:methodName);
					if (vm:getKind() == "METHOD") {
						local String is retT: self:resolveReturnType(t: vm:getType());
						local String is sigC: objType . "*";
						vm:getParameters():each(action: local Function(Parameter is p){
							sigC: sigC . ", " . self:cTypeFor(typeName: p:getType():getName());
						});
						local String is slotC: self:methodSlots:getString(key: expr:methodName, default: "0");
						if (targetC == "self") {
							callStr: "(((" . retT . " (*)(" . sigC . "))self->_vtable[" . slotC . "]))((" . objType . "*)self" . argsC . ")";
						} else {
							callStr: "({ " . objType . "* _recv = (" . objType . "*)(" . targetC . "); (((" . retT . " (*)(" . sigC . "))_recv->_vtable[" . slotC . "]))((" . objType . "*)_recv" . argsC . "); })";
						}
					}
				}
				if (callStr == "") {
					local String is dispatchCls: self:findMethodImplementingClass(className: objType, methodName: expr:methodName, paramCount: -1);
					local String is targetExprC: targetC;
					if (dispatchCls != "" && dispatchCls != objType) {
						objType: dispatchCls;
						targetExprC: "((" . dispatchCls . "*)" . targetC . ")";
					}
					callStr: objType . "_" . expr:methodName . "(" . targetExprC . argsC . ") /* inst:" . objType . ":" . expr:methodName . " */";
				}
				local Member is targetM: self:lookupMethodMember(className: objType, methodName: expr:methodName);
				local ClassInfo is targetCls: self:findClass(name: objType);
				if (targetM:getKind() == "METHOD" && targetCls:getTypeParams():length() > 0) {
					local String is rawRet: self:formatTypeString(t: targetM:getType());
					if (targetCls:getTypeParams():indexOf(search: rawRet, default: -1) >= 0) {
						local String is resolvedRet: expr:getResolvedType();
						if (resolvedRet != "" && resolvedRet != "Any") {
							local String is castCType: self:cTypeFor(typeName: resolvedRet);
							callStr: "((" . castCType . ")(intptr_t)(" . callStr . "))";
						}
					}
				}
				return callStr;
			}
			is "IF_ELSE": {
				local String is condC: self:generateExpression(expr: expr:condExpr);
				local String is thenC: self:generateExpression(expr: expr:thenExpr);
				local String is elseC: self:generateExpression(expr: expr:elseExpr);
				return "((" . condC . ") ? (" . thenC . ") : (" . elseC . "))";
			}
			is "WHEN": {
				local String is subjC: self:generateExpression(expr: expr:whenSubject);
				local String is chain: "0";
				expr:whenArms:each(action: local Function(WhenArm is arm){
					if (arm:isElse && arm:hasValueExpr) {
						chain: self:generateExpression(expr: arm:valueExpr);
					}
				});
				expr:whenArms:each(action: local Function(WhenArm is arm){
					if (!arm:isElse && arm:hasValueExpr) {
						local String is bindsC: self:generateWhenBindings(subjC: subjC, arm: arm);
						local String is armVal: self:generateExpression(expr: arm:valueExpr);
						if (bindsC != "") {
							armVal: "({ " . bindsC . " " . armVal . "; })";
						}
						local String is condOr: "";
						arm:conditions:each(action: local Function(Expression is c){
							local String is cmp: self:generateWhenCondition(subjExpr: expr:whenSubject, subjC: subjC, c: c);
							if (condOr == "") {
								condOr: cmp;
							} else {
								condOr: condOr . " || " . cmp;
							}
						});
						chain: "((" . condOr . ") ? (" . armVal . ") : (" . chain . "))";
					}
				});
				return chain;
			}
			is "ANON_FN": {
				self:anonCounter: self:anonCounter + 1;
				local Int is id: self:anonCounter;
				local String is fnName: "_anon_fn_" . id;
				local String is retC: self:cTypeFor(typeName: expr:anonReturnType:getName());

				local Map of String to String is savedVars: Map:init();
				local Array of String is outerKeys: self:localVars:keys();
				outerKeys:each(action: local Function(String is k){
					savedVars:set(key: k, value: self:localVars:getString(key: k, default: ""));
				});

				local Map of String to String is savedScopeVars: Map:init();
				local Array of String is outerScopeKeys: self:localScopeVars:keys();
				outerScopeKeys:each(action: local Function(String is k){
					savedScopeVars:set(key: k, value: self:localScopeVars:getString(key: k, default: ""));
				});
				self:localScopeVars: Map:init();

				local String is paramsC: "void* _env_ptr";
				local Array of String is paramNames: [];
				expr:anonParams:each(action: local Function(Parameter is p){
					paramNames:add(item: p:getName());
					self:localVars:set(key: p:getName(), value: self:formatVarTypeString(t: p:getType()));
					paramsC: paramsC . ", " . self:cTypeFor(typeName: p:getType():getName()) . " " . self:cIdent(name: p:getName());
				});

				local String is savedRetVar: self:inlineReturnVar;
				local String is savedRetLbl: self:inlineReturnLabel;
				self:inlineReturnVar: "";
				self:inlineReturnLabel: "";
				local String is bodyC: "";
				expr:anonBody:each(action: local Function(Statement is s){
					bodyC: bodyC . self:generateStatement(stmt: s);
				});
				self:inlineReturnVar: savedRetVar;
				self:inlineReturnLabel: savedRetLbl;
				self:localVars: savedVars;
				self:localScopeVars: savedScopeVars;

				local String is envName: "_Env_anon_" . id;
				local String is destroyEnvName: "_destroy_env_anon_" . id;

				local String is capFieldDecls: "";
				local String is capFieldBinds: "";
				local String is capAssigns: "";
				local String is capReleases: "";
				local Boolean is hasCaptures: false;

				if (self:inMethod && self:currentClassName != "" && !self:isBuiltinClass(name: self:currentClassName) && !self:allEnumNames:has(key: self:currentClassName) && bodyC:contains(needle: "self")) {
					hasCaptures: true;
					capFieldDecls: capFieldDecls . "    " . self:currentClassName . "* self;\n";
					capFieldBinds: capFieldBinds . "    " . self:currentClassName . "* self = _env->self;\n    (void)self;\n";
					capAssigns: capAssigns . "    _env->self = (" . self:currentClassName . "*)spec_retain((void*)self);\n";
					capReleases: capReleases . "    if (_env->self) spec_release((void*)_env->self);\n";
				}

				outerKeys:each(action: local Function(String is k){
					if (paramNames:indexOf(search: k, default: -1) < 0) {
						local String is cVar: self:cIdent(name: k);
						if (bodyC:contains(needle: cVar)) {
							local String is vType: savedVars:getString(key: k, default: "");
							local String is vCType: self:cTypeFor(typeName: vType);
							if (vCType != "void" && vCType != "") {
								hasCaptures: true;
								capFieldDecls: capFieldDecls . "    " . vCType . " " . cVar . ";\n";
								capFieldBinds: capFieldBinds . "    " . vCType . " " . cVar . " = _env->" . cVar . ";\n    (void)" . cVar . ";\n";
								local Boolean is isArcVar: (self:allClassNames:has(key: vType) && !self:allEnumNames:has(key: vType)) || self:allTaggedEnums:has(key: vType) || vType:startsWith(prefix: "Array") || vType:startsWith(prefix: "Map") || vType:startsWith(prefix: "Function") || vType == "LoopControl";
								if (isArcVar) {
									capAssigns: capAssigns . "    _env->" . cVar . " = (" . vCType . ")spec_retain((void*)" . cVar . ");\n";
									capReleases: capReleases . "    if (_env->" . cVar . ") spec_release((void*)_env->" . cVar . ");\n";
								} else if (vType == "String" || vType == "string") {
									capAssigns: capAssigns . "    _env->" . cVar . " = spec_str_clone_if_buffered(" . cVar . ");\n";
								} else {
									capAssigns: capAssigns . "    _env->" . cVar . " = " . cVar . ";\n";
								}
							}
						}
					}
				});

				if (hasCaptures) {
					local String is envStruct: "typedef struct {\n" . capFieldDecls . "} " . envName . ";\n\n";
					local String is destroyEnv: "static void " . destroyEnvName . "(void* _env_ptr) {\n    if (!_env_ptr) return;\n    " . envName . "* _env = (" . envName . "*)_env_ptr;\n" . capReleases . "    free(_env);\n}\n\n";
					local String is bindsC: "    " . envName . "* _env = (" . envName . "*)_env_ptr;\n" . capFieldBinds;
					self:helperFunctions: self:helperFunctions . envStruct . destroyEnv . "static " . retC . " " . fnName . "(" . paramsC . ") {\n" . bindsC . bodyC . "}\n\n";
					return "({ " . envName . "* _env = (" . envName . "*)calloc(1, sizeof(" . envName . "));\n" . capAssigns . "    spec_closure_new((void*)" . fnName . ", (void*)_env, " . destroyEnvName . "); })";
				} else {
					self:helperFunctions: self:helperFunctions . "static " . retC . " " . fnName . "(" . paramsC . ") {\n    (void)_env_ptr;\n" . bodyC . "}\n\n";
					return "spec_closure_new((void*)" . fnName . ", NULL, NULL)";
				}
			}
			else: {
				return "0";
			}
		}
	}

	## Resolves a simple local variable or `self` field expression to its C identifier without side effects.
	##
	## @param expr: Target [Expression] node.
	## @return: C lvalue string if simple variable/field, or empty string otherwise.
	local Function of String is tryGenerateTargetOnly(Expression is expr){
		if (expr:getKind() == "IDENT") {
			if (self:localVars:has(key: expr:stringValue)) {
				return self:cIdent(name: expr:stringValue);
			}
			if (self:inMethod && self:fieldTypes:has(key: expr:stringValue)) {
				return "self->" . self:cIdent(name: expr:stringValue);
			}
			return self:cIdent(name: expr:stringValue);
		}
		if (expr:getKind() == "PATH" && expr:pathSegments:length() == 2 && expr:pathSegments:get(index: 0) == "self") {
			return "self->" . self:cIdent(name: expr:pathSegments:get(index: 1));
		}
		return "";
	}

	## Optimizes left-recursive string concatenation chains (`s: s . a . b`) into amortized O(1) `spec_str_append` calls.
	##
	## @param expr: Right-hand side assignment [Expression].
	## @param targetC: Generated C lvalue of the assignment target.
	## @return: `spec_str_append` call chain string if optimizable, or empty string otherwise.
	local Function of String is tryGenerateAppendChain(Expression is expr, String is targetC){
		if (targetC == "") {
			return "";
		}
		if (expr:getKind() == "BINARY" && expr:binaryOp == ".") {
			local String is leftTarget: self:tryGenerateTargetOnly(expr: expr:leftExpr);
			if (leftTarget == targetC) {
				local String is rhsC: self:wrapToString(expr: expr:rightExpr, exprC: self:generateExpression(expr: expr:rightExpr));
				if (rhsC:contains(needle: targetC)) {
					return "";
				}
				return "spec_str_append(" . targetC . ", " . rhsC . ")";
			}
			local String is innerChain: self:tryGenerateAppendChain(expr: expr:leftExpr, targetC: targetC);
			if (innerChain != "") {
				local String is rhsC: self:wrapToString(expr: expr:rightExpr, exprC: self:generateExpression(expr: expr:rightExpr));
				if (rhsC:contains(needle: targetC)) {
					return "";
				}
				return "spec_str_append(" . innerChain . ", " . rhsC . ")";
			}
		}
		return "";
	}

	## Generates C code for a statement node.
	##
	## @param stmt: [Statement] AST node.
	## @return: C statement code block.
}
