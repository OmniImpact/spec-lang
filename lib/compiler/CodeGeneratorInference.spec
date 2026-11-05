#! Package compiler
#! Target type inference, string wrapping, subclass checks, constructor generation, and inlined higher-order collection operations.
#! Group fragment merged into CodeGenerator at load time (see Loader).

## Target type inference, string wrapping, subclass checks, constructor generation, and inlined higher-order collection operations.
Class is CodeGeneratorInference{

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

	Class of Loop is PathTypeResolveLoop{
		local CodeGenerator is cg;
		local Array of String is segs;
		local Int is idx: 1;
		local String is currType: '';

		replace Function is init(CodeGenerator is cg, Array of String is segs, String is rootType){
			self:cg: cg;
			self:segs: segs;
			self:currType: rootType;
			self:idx: 1;
		}

		replace Function of Boolean is evaluate(){
			return self:currType != '' && self:idx < self:segs:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			local String is seg: self:segs:get(index: self:idx);
			self:idx: self:idx + 1;
			if (self:cg:allEnumNames:has(key: self:currType)) {
				return true;
			}
			self:currType: self:cg:lookupFieldType(className: self:currType, fieldName: seg);
			return true;
		}
	}

	## Infers the target type of an expression for method dispatch and type conversion.
	Function of String is inferTargetType(Expression is expr){
		local String is resolved: expr:getResolvedType();
		if (resolved != '' && resolved != 'Any') {
			return resolved;
		}

		local String is kind: expr:getKind();
		if (kind == 'STRING') { return 'String'; }
		if (kind == 'NUMBER') { return 'Int'; }
		if (kind == 'FLOAT') { return 'Float'; }
		if (kind == 'BOOL') { return 'Boolean'; }

		if (kind == 'IDENT') {
			local String is name: expr:stringValue;
			if (name == 'self') { return self:currentClassName; }
			if (self:localVars:has(key: name)) {
				return self:localVars:getString(key: name, default: '');
			}
			if (self:fieldTypes:has(key: name)) {
				return self:fieldTypes:getString(key: name, default: '');
			}
			if (self:allEnumVariants:has(key: name)) {
				return self:allEnumVariants:getString(key: name, default: '');
			}
			if (self:allClassNames:has(key: name)) {
				return name;
			}
			return '';
		}
		if (kind == 'PATH') {
			local Array of String is segs: expr:pathSegments;
			if (segs:length() > 0) {
				local String is root: segs:get(index: 0);
				local String is rootType: '';
				if (root == 'self') {
					rootType: self:currentClassName;
				} else if (self:localVars:has(key: root)) {
					rootType: self:localVars:getString(key: root, default: '');
				} else if (self:fieldTypes:has(key: root)) {
					rootType: self:fieldTypes:getString(key: root, default: '');
				} else if (self:allEnumNames:has(key: root) || self:allClassNames:has(key: root)) {
					rootType: root;
				}
				local PathTypeResolveLoop is pLoop: PathTypeResolveLoop:init(cg: self, segs: segs, rootType: rootType);
				While:run(loop: pLoop);
				return pLoop:currType;
			}
			return '';
		}
		if (kind == 'CALL') {
			local String is tgtType: self:inferTargetType(expr: expr:methodTarget);
			if (tgtType == '' || tgtType == 'self') {
				tgtType: self:currentClassName;
			}
			local String is m: expr:methodName;
			if (tgtType:startsWith(prefix: 'Array:') && (m == 'get' || m == 'pop' || m == 'removeAt')) {
				return tgtType:substring(start: 6, end: tgtType:length());
			}
			if (self:allEnumNames:has(key: tgtType)) {
				if (m == 'name') { return 'String'; }
				if (m == 'ordinal') { return 'Int'; }
				if (m == 'values') { return 'Array:' . tgtType; }
				if (m == 'value') {
					return if (self:allStringBackedEnums:has(key: tgtType)) 'String' else 'Int';
				}
			}
			if (tgtType == 'String' && m == 'fromCharCode') {
				return 'String';
			}
			if (tgtType == 'Math' || tgtType == 'math') {
				if (m == 'toInt') { return 'Int'; }
				if (m == 'round' || m == 'floor' || m == 'ceil' || m == 'ceiling' || m == 'random' || m == 'abs' || m == 'min' || m == 'max' || m == 'clamp' || m == 'sqrt' || m == 'sin' || m == 'cos' || m == 'tan' || m == 'atan2' || m == 'log' || m == 'log2' || m == 'pow' || m == 'toFloat') {
					return 'Float';
				}
			}
			local String is methodRet: self:lookupMethodReturnType(className: tgtType, methodName: m);
			if (methodRet != '' && methodRet != 'void') {
				return methodRet;
			}
			return '';
		}
		if (kind == 'INDEX') {
			local String is leftT: self:inferTargetType(expr: expr:leftExpr);
			if (leftT:startsWith(prefix: 'Array:') && leftT:length() > 6) {
				return leftT:substring(start: 6, end: leftT:length());
			}
			return '';
		}
		return '';
	}

	## Wraps non-string expressions with runtime string conversion helpers.
	##
	## @param expr: AST [Expression] node.
	## @param exprC: Generated C expression string.
	## @return: Wrapped C expression string.
	Function of String is wrapToString(Expression is expr, String is exprC){
		local String is resolved: self:inferTargetType(expr: expr);
		when (resolved) {
			is 'Int', 'int': {
				return 'spec_to_string_int(' . exprC . ')';
			}
			is 'Float', 'float': {
				return 'spec_to_string_float(' . exprC . ')';
			}
			is 'Boolean', 'bool': {
				return 'spec_to_string_bool(' . exprC . ')';
			}
			is 'String', 'string': {
				return exprC;
			}
			else: {
				if (self:allEnumNames:has(key: resolved)) {
					return resolved . '_name(' . exprC . ')';
				}
				if (self:allClassNames:has(key: resolved) && !self:isBuiltinClass(name: resolved)) {
					return 'spec_type_name(' . exprC . ') /* wrap:' . resolved . ' */';
				}
			}
		}

		local String is kind: expr:getKind();
		when (kind) {
			is 'NUMBER': {
				return 'spec_to_string_int(' . exprC . ')';
			}
			is 'FLOAT': {
				return 'spec_to_string_float(' . exprC . ')';
			}
			is 'BOOL': {
				return 'spec_to_string_bool(' . exprC . ')';
			}
			is 'BINARY': {
				local String is op: expr:binaryOp;
				if (op == '+' || op == '-' || op == '*' || op == '/' || op == '%' || op == '&' || op == '|' || op == '^' || op == '<<' || op == '>>') {
					return 'spec_to_string_int(' . exprC . ')';
				}
				if (op == '==' || op == '!=' || op == '<' || op == '<=' || op == '>' || op == '>=' || op == '&&' || op == '||') {
					return 'spec_to_string_bool(' . exprC . ')';
				}
				return exprC;
			}
			is 'UNARY': {
				if (expr:unaryOp == '!') {
					return 'spec_to_string_bool(' . exprC . ')';
				}
				return 'spec_to_string_int(' . exprC . ')';
			}
			else: {
				return exprC;
			}
		}
	}

	## Determines whether an expression produces a string value.
	Function of Boolean is isStringExpr(Expression is expr){
		local String is resolved: self:inferTargetType(expr: expr);
		if (resolved == 'String' || resolved == 'string') {
			return true;
		}
		local String is kind: expr:getKind();
		if (kind == 'STRING') {
			return true;
		}
		if (kind == 'BINARY' && expr:binaryOp == '.') {
			return true;
		}
		return false;
	}

	local Function of Boolean is isSubclassOf(String is subName, String is baseName){
		if (subName == '' || baseName == '' || subName == baseName) {
			return false;
		}
		local ClassInfo is subCls: self:findClass(name: subName);
		if (subCls:getName() == '') {
			return false;
		}
		local Boolean is matched: false;
		subCls:getBaseClasses():each(action: local Function(String is parent){
			if (parent == baseName) {
				matched: true;
			} else if (!matched && self:isSubclassOf(subName: parent, baseName: baseName)) {
				matched: true;
			}
		});
		return matched;
	}

	## Emits constructor factory functions for all classes.
	##
	## @param classes: Array of [ClassInfo] definitions.
	## @return: C constructor functions text.
	local Function of String is generateConstructors(Array of ClassInfo is classes){
		local String is out: "/* Constructor Implementations */\n";

		classes:each(action: local Function(ClassInfo is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != 'Enum') {
				self:currentClassName: c:getName();
				self:fieldTypes: Map:init();
				local Array of Member is allFields: [];
				self:declGen:collectStructFields(c: c, allClasses: classes, acc: allFields);
				allFields:each(action: local Function(Member is f){
					self:fieldTypes:set(key: f:getName(), value: self:formatTypeString(t: f:getType()));
				});

				out: out . 'void ' . c:getName() . "_destroy(void* self_ptr) {\n";
				out: out . '    ' . c:getName() . '* self = (' . c:getName() . "*)self_ptr;\n";
				out: out . "    if (!self) return;\n";
				allFields:each(action: local Function(Member is m){
					local String is ft: m:getType():getName();
					if ((self:allClassNames:has(key: ft) && !self:allEnumNames:has(key: ft)) || self:allTaggedEnums:has(key: ft) || ft:startsWith(prefix: 'Array') || ft:startsWith(prefix: 'Map') || ft:startsWith(prefix: 'List') || ft:startsWith(prefix: 'Function') || ft == 'LoopControl' || ft == 'String' || ft == 'string') {
						out: out . '    if (self->' . self:cIdent(name: m:getName()) . ') { spec_release((void*)self->' . self:cIdent(name: m:getName()) . '); self->' . self:cIdent(name: m:getName()) . " = NULL; }\n";
					}
				});
				out: out . "}\n\n";

				out: out . c:getName() . '* ' . c:getName() . "_new(void) {\n";
				out: out . '    ' . c:getName() . '* self = (' . c:getName() . '*)spec_alloc(sizeof(' . c:getName() . '), ' . c:getName() . "_destroy);\n";
				out: out . '    self->_type_name = "' . c:getName() . "\";\n";
				if (self:methodSlotCount > 0) {
					out: out . '    self->_vtable = ' . c:getName() . "_vtable;\n";
				}
				allFields:each(action: local Function(Member is m){
					if (m:hasInit) {
						local Boolean is savedArgFi: self:argMode;
						self:argMode: false;
						local String is fieldInitC: self:generateExpression(expr: m:initExpr);
						self:argMode: savedArgFi;
						local String is ftn: m:getType():getName();
						if (self:isArcType(typeName: ftn)) {
							fieldInitC: '(' . self:cTypeFor(typeName: ftn) . ')spec_retain((void*)(' . fieldInitC . '))';
						}
						out: out . '    self->' . self:cIdent(name: m:getName()) . ' = ' . fieldInitC . ";\n";
					} else {
						local String is ft: m:getType():getName();
						if (ft == 'String' || ft == 'string') {
							out: out . '    self->' . self:cIdent(name: m:getName()) . ' = spec_string_intern("");' . "\n";
						} else if (ft == 'Array') {
							local String is elemKind: self:containerElemKind(containerType: self:formatTypeString(t: m:getType()));
							local String is newCall: 'spec_array_new()';
							if (elemKind == 'object') {
								newCall: 'spec_array_new_object()';
							} else if (elemKind == 'string') {
								newCall: 'spec_array_new_string()';
							}
							out: out . '    self->' . self:cIdent(name: m:getName()) . ' = ' . newCall . ";\n";
						} else if (ft == 'Map') {
							local String is newCall: 'spec_map_new()';
							if (self:containerElemIsArc(containerType: self:formatTypeString(t: m:getType()))) {
								newCall: 'spec_map_new_object()';
							}
							out: out . '    self->' . self:cIdent(name: m:getName()) . ' = ' . newCall . ";\n";
						} else if (ft == 'List') {
							local String is fullT: self:formatTypeString(t: m:getType());
							local String is elemKind: self:containerElemKind(containerType: fullT);
							local String is newCall: 'spec_vec_new()';
							if (elemKind == 'byte') {
								newCall: 'spec_bytebuffer_new()';
							} else if (elemKind == 'string') {
								newCall: 'spec_vec_new_string()';
							} else if (elemKind == 'object') {
								newCall: 'spec_vec_new_object()';
							}
							out: out . '    self->' . self:cIdent(name: m:getName()) . ' = ' . newCall . ";\n";
						}
					}
				});
				out: out . "    return self;\n";
				out: out . "}\n\n";
			}
		});
		return out;
	}

	Function of String is generateInlineArrayOp(String is mode, String is targetC, Expression is fnExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;
		local Boolean is savedArc: self:inlineReturnArc;
		self:inlineReturnLabel: 'break';
		if (mode == 'each') {
			self:inlineReturnVar: '';
		} else {
			self:inlineReturnVar: '_pred_' . id;
		}

		local Map of String to String is savedVars: Map:init();
		local Array of String is outerKeys: self:localVars:keys();
		outerKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
		});

		local String is paramDecl: '';
		if (fnExpr:anonParams:length() > 0) {
			local Parameter is p: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p:getName(), value: self:formatTypeString(t: p:getType()));
			local String is pCType: self:cTypeFor(typeName: p:getType():getName());
			local String is pRaw: '(' . pCType . ')(intptr_t)_a_' . id . '->items[_i_' . id . ']';
			paramDecl: '        ' . pCType . ' ' . self:cIdent(name: p:getName()) . ' = ' . pRaw . ";\n";
		}

		local String is bodyC: '';
		fnExpr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});

		self:localVars: savedVars;
		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;
		self:inlineReturnArc: savedArc;

		local String is arrVar: '_a_' . id;
		local String is idxVar: '_i_' . id;
		local String is predVar: '_pred_' . id;

		if (mode == 'each') {
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . "        do {\n" . bodyC . "        } while (0);\n    } } })";
			return out;
		}
		if (mode == 'filter') {
			local String is outVar: '_out_' . id;
			local String is outNewC: 'spec_array_new()';
			if (fnExpr:anonParams:length() > 0) {
				local String is pName: fnExpr:anonParams:get(index: 0):getType():getName();
				if (self:isArcType(typeName: pName)) {
					outNewC: 'spec_array_new_object()';
				} else if (pName == 'String') {
					outNewC: 'spec_array_new_string()';
				}
			}
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; SpecArray* ' . outVar . ' = ' . outNewC . '; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . '        bool ' . predVar . " = false;\n        do {\n" . bodyC . "        } while (0);\n        if (" . predVar . ') spec_array_add(' . outVar . ', ' . arrVar . '->items[' . idxVar . "]);\n    } } " . outVar . '; })';
			return out;
		}
		if (mode == 'count') {
			local String is cntVar: '_cnt_' . id;
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; long long ' . cntVar . ' = 0; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . '        bool ' . predVar . " = false;\n        do {\n" . bodyC . "        } while (0);\n        if (" . predVar . ') ' . cntVar . "++;\n    } } " . cntVar . '; })';
			return out;
		}
		if (mode == 'any') {
			local String is fndVar: '_fnd_' . id;
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; bool ' . fndVar . ' = false; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . '        bool ' . predVar . " = false;\n        do {\n" . bodyC . "        } while (0);\n        if (" . predVar . ') { ' . fndVar . " = true; break; }\n    } } " . fndVar . '; })';
			return out;
		}
		if (mode == 'map') {
			local String is outVar: '_out_' . id;
			local String is retCType: self:cTypeFor(typeName: fnExpr:anonReturnType:getName());
			if (retCType == 'void') { retCType: 'void*'; }
			self:inlineReturnArc: retCType:charAt(index: retCType:length() - 1) == '*';
			local String is outNewC: 'spec_array_new()';
			if (self:isArcType(typeName: fnExpr:anonReturnType:getName())) {
				outNewC: 'spec_array_new_object()';
			} else if (fnExpr:anonReturnType:getName() == 'String') {
				outNewC: 'spec_array_new_string()';
			}
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; SpecArray* ' . outVar . ' = ' . outNewC . '; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . '        ' . retCType . ' ' . predVar . " = 0;\n        do {\n" . bodyC . "        } while (0);\n        spec_array_add(" . outVar . ', (void*)(intptr_t)(' . predVar . "));\n    } } " . outVar . '; })';
			return out;
		}
		return '0';
	}

	Function of String is generateInlineArrayFold(String is targetC, Expression is initExpr, Expression is fnExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;

		local Map of String to String is savedVars: Map:init();
		local Array of String is outerKeys: self:localVars:keys();
		outerKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
		});

		local String is accVar: '_acc_' . id;
		local String is nextLbl: '_loop_next_' . id;
		local String is arrVar: '_a_' . id;
		local String is idxVar: '_i_' . id;

		local String is initC: self:generateExpression(expr: initExpr);
		local String is accTypeName: self:inferTargetType(expr: initExpr);
		if (accTypeName == '' && fnExpr:anonReturnType:getName() != 'Void' && fnExpr:anonReturnType:getName() != 'void') {
			accTypeName: fnExpr:anonReturnType:getName();
		}
		local String is accCType: self:cTypeFor(typeName: accTypeName);
		if (accCType == 'void') { accCType: 'long long'; }

		self:inlineReturnVar: accVar;
		self:inlineReturnLabel: 'break';
		local Boolean is savedArc2: self:inlineReturnArc;
		self:inlineReturnArc: accCType:charAt(index: accCType:length() - 1) == '*';

		local String is paramDecl: '';
		if (fnExpr:anonParams:length() >= 1) {
			local Parameter is p0: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p0:getName(), value: accTypeName);
			paramDecl: paramDecl . '        ' . accCType . ' ' . self:cIdent(name: p0:getName()) . ' = ' . accVar . ";\n";
		}
		if (fnExpr:anonParams:length() >= 2) {
			local Parameter is p1: fnExpr:anonParams:get(index: 1);
			self:localVars:set(key: p1:getName(), value: self:formatTypeString(t: p1:getType()));
			local String is p1CType: self:cTypeFor(typeName: p1:getType():getName());
			local String is p1Raw: '(' . p1CType . ')(intptr_t)' . arrVar . '->items[' . idxVar . ']';
			paramDecl: paramDecl . '        ' . p1CType . ' ' . self:cIdent(name: p1:getName()) . ' = ' . p1Raw . ";\n";
		}

		local String is bodyC: '';
		fnExpr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});

		self:localVars: savedVars;
		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;
		self:inlineReturnArc: savedArc2;

		local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; ' . accCType . ' ' . accVar . ' = ' . initC . '; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
		out: out . paramDecl . "        do {\n" . bodyC . "        } while (0);\n    } } " . accVar . '; })';
		return out;
	}

	Function of String is generateInlineMapEach(String is targetC, Expression is fnExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;

		local Map of String to String is savedVars: Map:init();
		local Array of String is outerKeys: self:localVars:keys();
		outerKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
		});

		local String is mapVar: '_m_' . id;
		local String is bVar: '_b_' . id;
		local String is eVar: '_e_' . id;

		self:inlineReturnVar: '';
		self:inlineReturnLabel: 'break';

		local String is paramDecl: '';
		if (fnExpr:anonParams:length() >= 1) {
			local Parameter is p0: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p0:getName(), value: 'String');
			paramDecl: paramDecl . '            SpecString ' . self:cIdent(name: p0:getName()) . ' = spec_string_from_chars(' . eVar . "->key);\n";
		}
		if (fnExpr:anonParams:length() >= 2) {
			local Parameter is p1: fnExpr:anonParams:get(index: 1);
			self:localVars:set(key: p1:getName(), value: self:formatTypeString(t: p1:getType()));
			local String is p1CType: self:cTypeFor(typeName: p1:getType():getName());
			local String is p1Raw: '(' . p1CType . ')(intptr_t)' . eVar . '->value';
			if (p1:getType():getName() == 'String') {
				p1Raw: 'spec_string_from_chars((const char*)' . eVar . '->value)';
			}
			paramDecl: paramDecl . '            ' . p1CType . ' ' . self:cIdent(name: p1:getName()) . ' = ' . p1Raw . ";\n";
		}

		local String is bodyC: '';
		fnExpr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});

		self:localVars: savedVars;
		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is out: '({ SpecMap* ' . mapVar . ' = ' . targetC . '; if (' . mapVar . ') { for (size_t ' . bVar . ' = 0; ' . bVar . ' < SPEC_MAP_BUCKETS; ' . bVar . '++) { for (SpecMapEntry* ' . eVar . ' = ' . mapVar . '->buckets[' . bVar . ']; ' . eVar . '; ' . eVar . ' = ' . eVar . "->next) {\n";
		out: out . paramDecl . "            do {\n" . bodyC . "            } while (0);\n        } } } })";
		return out;
	}

	Function of String is generateInlineWhileCondition(Expression is evalExpr, Expression is iterExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;

		local String is evVar: '_ev_' . id;
		self:inlineReturnVar: evVar;
		self:inlineReturnLabel: 'break';
		local String is evalBodyC: '';
		evalExpr:anonBody:each(action: local Function(Statement is s){
			evalBodyC: evalBodyC . self:generateStatement(stmt: s);
		});

		self:inlineReturnVar: '';
		self:inlineReturnLabel: 'break';
		local String is iterBodyC: '';
		iterExpr:anonBody:each(action: local Function(Statement is s){
			iterBodyC: iterBodyC . self:generateStatement(stmt: s);
		});

		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is out: "({ while (1) {\n        bool " . evVar . " = false;\n        do {\n" . evalBodyC . "        } while (0);\n        if (!" . evVar . ") break;\n        do {\n" . iterBodyC . "        } while (0);\n    } })";
		return out;
	}

	Class of Loop is PathChainLoop{
		local Array of String is segs;
		local CBackendUtils is utils;
		local Int is idx: 1;
		local String is res: '';

		replace Function is init(Array of String is segs, String is rootC, CBackendUtils is utils){
			self:segs: segs;
			self:res: rootC;
			self:utils: utils;
			self:idx: 1;
		}

		replace Function of Boolean is evaluate(){
			return self:idx < self:segs:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			self:res: self:res . '->' . self:utils:cIdent(name: self:segs:get(index: self:idx));
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Generates C code for an expression node.
	##
	## @param expr: [Expression] AST node.
	## @return: C expression code string.
}
