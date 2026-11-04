#! Package compiler
#! Statement, method, entry-point, and whole-program C generation.
#! Group fragment merged into CodeGenerator at load time (see Loader).

## Statement, method, entry-point, and whole-program C generation.
Class is CodeGeneratorProgram{

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

	local Function of String is generateStatement(Statement is stmt){
		local String is kind: stmt:getKind();

		when (kind) {
			is "VAR_DECL": {
				self:localVars:set(key: stmt:varName, value: self:formatVarTypeString(t: stmt:varType));
				self:localScopeVars:set(key: stmt:varName, value: stmt:varType:getName());
				local String is vTypeName: stmt:varType:getName();
				local String is cType: self:cTypeFor(typeName: vTypeName);
				local String is varName: self:cIdent(name: stmt:varName);
				local Boolean is isArcVar: self:isArcType(typeName: vTypeName);
				local String is autoPrefix: if (isArcVar) "SPEC_AUTO " else "";
				if (stmt:hasInit) {
					local String is initC: self:generateExpression(expr: stmt:initExpr);
					if (cType:length() > 0 && cType:charAt(index: cType:length() - 1) == "*" && cType != "const char*" && cType != "SpecArray*" && cType != "SpecMap*") {
						initC: "(" . cType . ")(" . initC . ")";
					}
					if (cType == "const char*") {
						initC: "spec_str_clone_if_buffered(" . initC . ")";
					}
					if (isArcVar && !self:isFreshAllocExpr(expr: stmt:initExpr)) {
						initC: "(" . cType . ")spec_retain((void*)(" . initC . "))";
					}
					return "    " . autoPrefix . cType . " " . varName . " = " . initC . ";\n";
				}
				if (vTypeName == "String" || vTypeName == "string") {
					return "    " . cType . " " . varName . " = \"\";\n";
				}
				if (vTypeName == "Array") {
					return "    " . autoPrefix . cType . " " . varName . " = spec_array_new();\n";
				}
				if (vTypeName == "Map") {
					return "    " . autoPrefix . cType . " " . varName . " = spec_map_new();\n";
				}
				return "    " . autoPrefix . cType . " " . varName . " = 0;\n";
			}
			is "ASSIGN": {
				if (stmt:assignTarget:getKind() == "INDEX") {
					local String is containerC: self:generateExpression(expr: stmt:assignTarget:leftExpr);
					local String is idxC: self:generateExpression(expr: stmt:assignTarget:rightExpr);
					local String is valC: self:generateExpression(expr: stmt:assignValue);
					local String is containerType: self:inferTargetType(expr: stmt:assignTarget:leftExpr);
					if (containerType:startsWith(prefix: "Map:") || containerType == "Map") {
						if (containerType:contains(needle: "String:String") || containerType:contains(needle: "to String") || self:isStringExpr(expr: stmt:assignValue)) {
							return "    spec_map_set(" . containerC . ", " . idxC . ", " . valC . ");\n";
						}
						local String is mapValType: self:inferTargetType(expr: stmt:assignValue);
						if (self:isArcType(typeName: mapValType)) {
							valC: "(void*)spec_retain((void*)(" . valC . "))";
						}
						return "    spec_map_set_any(" . containerC . ", " . idxC . ", (void*)(intptr_t)(" . valC . "));\n";
					}
					local String is arrValType: self:inferTargetType(expr: stmt:assignValue);
					if (self:isArcType(typeName: arrValType)) {
						valC: "(void*)spec_retain((void*)(" . valC . "))";
					}
					return "    spec_array_set(" . containerC . ", " . idxC . ", (void*)(intptr_t)(" . valC . "));\n";
				}
				local String is targetC: self:generateExpression(expr: stmt:assignTarget);
				local String is appendC: self:tryGenerateAppendChain(expr: stmt:assignValue, targetC: targetC);
				if (appendC != "") {
					return "    " . targetC . " = " . appendC . ";\n";
				}
				local String is valC: self:generateExpression(expr: stmt:assignValue);
				local String is lhsType: self:inferTargetType(expr: stmt:assignTarget);
				local ClassInfo is curCls: self:findClass(name: self:currentClassName);
				if (curCls:getTypeParams():indexOf(search: lhsType, default: -1) >= 0) {
					valC: "(void*)(intptr_t)(" . valC . ")";
				} else if (lhsType == "String" || lhsType == "string") {
					valC: "spec_str_clone_if_buffered(" . valC . ")";
				}
				local Boolean is isArcLhs: self:isArcType(typeName: lhsType);
				if (isArcLhs) {
					if (self:isFreshAllocExpr(expr: stmt:assignValue)) {
						return "    spec_assign_transfer((void**)&" . targetC . ", (void*)(" . valC . "));\n";
					}
					return "    spec_assign((void**)&" . targetC . ", (void*)(" . valC . "));\n";
				}
				return "    " . targetC . " = " . valC . ";\n";
			}
			is "IF": {
				local String is condC: self:generateExpression(expr: stmt:ifCondition);
				local String is out: "    if (" . condC . ") {\n";
				stmt:thenBranch:each(action: local Function(Statement is s){
					out: out . "    " . self:generateStatement(stmt: s);
				});
				if (stmt:hasElse) {
					out: out . "    } else {\n";
					stmt:elseBranch:each(action: local Function(Statement is s){
						out: out . "    " . self:generateStatement(stmt: s);
					});
				}
				out: out . "    }\n";
				return out;
			}
			is "FORWARD": {
				# Merge-forward: delegate to the nearest parent implementation.
				local ClassInfo is fwdCls: self:findClass(name: self:currentClassName);
				local String is dispatchCls: "";
				fwdCls:getBaseClasses():each(action: local Function(String is baseName){
					if (dispatchCls == "") {
						local String is implCls: self:findMethodImplementingClass(className: baseName, methodName: self:currentMethodName, paramCount: -1);
						if (implCls != "") {
							dispatchCls: implCls;
						}
					}
				});
				if (dispatchCls == "") {
					return "";
				}
				local Member is superM: self:lookupMethodMember(className: dispatchCls, methodName: self:currentMethodName);
				local String is argsC: self:formatCallArguments(className: dispatchCls, methodName: self:currentMethodName, args: stmt:getForwardArgs());
				local String is callC: dispatchCls . "_" . self:currentMethodName . "((" . dispatchCls . "*)self" . argsC . ")";
				local String is superRet: self:resolveReturnType(t: superM:getType());
				if (superRet != "void") {
					return "    return " . callC . ";\n";
				}
				return "    " . callC . ";\n";
			}
			is "RETURN": {
				if (self:inlineReturnLabel != "") {
					if (stmt:hasReturnExpr && self:inlineReturnVar != "") {
						local String is retC: self:generateExpression(expr: stmt:returnExpr);
						return "    " . self:inlineReturnVar . " = " . retC . "; break;\n";
					}
					return "    break;\n";
				}
				if (stmt:hasReturnExpr) {
					local String is retC: self:generateExpression(expr: stmt:returnExpr);
					local ClassInfo is curCls: self:findClass(name: self:currentClassName);
					if (curCls:getTypeParams():indexOf(search: self:currentMethodReturnType, default: -1) >= 0) {
						retC: "(void*)(intptr_t)(" . retC . ")";
					} else if (self:isArcType(typeName: self:currentMethodReturnType)) {
						if (!self:isFreshAllocExpr(expr: stmt:returnExpr)) {
							retC: "(" . self:cTypeFor(typeName: self:currentMethodReturnType) . ")spec_retain((void*)(" . retC . "))";
						}
					}
					return "    return " . retC . ";\n";
				}
				return "    return;\n";
			}
			is "WHEN": {
				local String is subjC: self:generateExpression(expr: stmt:whenSubject);
				local String is out: "";
				local Boolean is first: true;
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					local String is bindsC: "";
					if (arm:isElse) {
						out: out . "    } else {\n";
					} else {
						local String is condOr: "";
						arm:conditions:each(action: local Function(Expression is c){
							local String is cmp: self:generateWhenCondition(subjExpr: stmt:whenSubject, subjC: subjC, c: c);
							if (condOr == "") {
								condOr: cmp;
							} else {
								condOr: condOr . " || " . cmp;
							}
						});
						bindsC: self:generateWhenBindings(subjC: subjC, arm: arm);
						if (first) {
							out: out . "    if (" . condOr . ") {\n";
							first: false;
						} else {
							out: out . "    } else if (" . condOr . ") {\n";
						}
						out: out . bindsC;
					}
					arm:body:each(action: local Function(Statement is s){
						out: out . "    " . self:generateStatement(stmt: s);
					});
				});
				out: out . "    }\n";
				return out;
			}
			is "EXPR": {
				local String is exprC: self:generateExpression(expr: stmt:exprStmt);
				return "    " . exprC . ";\n";
			}
			is "CLASS": {
				return "";
			}
			else: {
				return "";
			}
		}
	}

	## Generates C code for a method definition.
	##
	## @param classDef: Enclosing [ClassInfo] definition.
	## @param method: Method [Member] descriptor.
	## @return: C method implementation string.
	local Function of String is generateMethod(ClassInfo is classDef, Member is method){
		self:inMethod: true;
		self:currentMethodName: method:getName();
		self:currentMethodReturnType: self:formatTypeString(t: method:getType());
		local String is retType: self:resolveReturnType(t: method:getType());
		if (retType == "void") {
			if (method:getName() == "evaluate" || method:getName() == "iteration") {
				retType: "bool";
			}
		}

		self:localVars: Map:init();
		self:localScopeVars: Map:init();
		method:getParameters():each(action: local Function(Parameter is p){
			self:localVars:set(key: p:getName(), value: self:formatVarTypeString(t: p:getType()));
		});

		local String is out: retType . " " . classDef:getName() . "_" . method:getName() . "(" . classDef:getName() . "* self";
		local String is callArgs: "";
		method:getParameters():each(action: local Function(Parameter is p){
			out: out . ", " . self:cTypeFor(typeName: p:getType():getName()) . " " . self:cIdent(name: p:getName());
			callArgs: callArgs . ", " . self:cIdent(name: p:getName());
		});
		out: out . ") {\n";

		method:getBody():each(action: local Function(Statement is stmt){
			out: out . self:generateStatement(stmt: stmt);
		});

		if (method:getBody():length() == 0 && retType != "void") {
			if (retType == "const char*") {
				out: out . "    return \"\";\n";
			} else {
				out: out . "    return 0;\n";
			}
		}

		out: out . "}\n\n";
		self:inMethod: false;
		return out;
	}

	## Generates the C `main` function entry point.
	##
	## @param entryClass: Application entry point class name.
	## @return: C main function text.
	local Function of String is generateMain(String is entryClass){
		local String is m: "/* Application Entry Point */\n";
		m: m . "int main(int argc, char** argv) {\n";
		m: m . "#if defined(SPEC_GC_BOEHM)\n";
		m: m . "    GC_init();\n";
		m: m . "#endif\n";
		m: m . "    srand((unsigned int)time(NULL));\n";
		m: m . "    SPEC_AUTO SpecMap* args = spec_map_new();\n";
		m: m . "    for (int i = 1; i < argc; i++) {\n";
		m: m . "        if (strncmp(argv[i], \"--\", 2) == 0) {\n";
		m: m . "            const char* eq = strchr(argv[i] + 2, '=');\n";
		m: m . "            if (eq) {\n";
		m: m . "                int klen = (int)(eq - (argv[i] + 2));\n";
		m: m . "                char kbuf[128];\n";
		m: m . "                if (klen >= 128) klen = 127;\n";
		m: m . "                strncpy(kbuf, argv[i] + 2, klen);\n";
		m: m . "                kbuf[klen] = '\\0';\n";
		m: m . "                spec_map_set(args, kbuf, eq + 1);\n";
		m: m . "            } else {\n";
		m: m . "                const char* key = argv[i] + 2;\n";
		m: m . "                const char* val = \"true\";\n";
		m: m . "                if (i + 1 < argc && argv[i + 1][0] != '-') {\n";
		m: m . "                    val = argv[++i];\n";
		m: m . "                }\n";
		m: m . "                spec_map_set(args, key, val);\n";
		m: m . "            }\n";
		m: m . "        } else if (argv[i][0] == '-' && argv[i][1] != '\\0') {\n";
		m: m . "            const char* eq = strchr(argv[i] + 1, '=');\n";
		m: m . "            if (eq) {\n";
		m: m . "                int klen = (int)(eq - (argv[i] + 1));\n";
		m: m . "                char kbuf[128];\n";
		m: m . "                if (klen >= 128) klen = 127;\n";
		m: m . "                strncpy(kbuf, argv[i] + 1, klen);\n";
		m: m . "                kbuf[klen] = '\\0';\n";
		m: m . "                spec_map_set(args, kbuf, eq + 1);\n";
		m: m . "            } else {\n";
		m: m . "                const char* key = argv[i] + 1;\n";
		m: m . "                const char* val = \"true\";\n";
		m: m . "                if (i + 1 < argc && argv[i + 1][0] != '-') {\n";
		m: m . "                    val = argv[++i];\n";
		m: m . "                }\n";
		m: m . "                spec_map_set(args, key, val);\n";
		m: m . "            }\n";
		m: m . "        }\n";
		m: m . "    }\n";
		m: m . "    SPEC_AUTO " . entryClass . "* app = " . entryClass . "_new();\n";
		m: m . "    " . entryClass . "_init(app, args);\n";
		m: m . "    spec_drain_async_tasks();\n";
		m: m . "    return 0;\n";
		m: m . "}\n";
		return m;
	}

	local Function is collectClassesFromStatement(Statement is stmt, Array of ClassInfo is acc){
		when (stmt:getKind()) {
			is "CLASS": {
				self:collectClasses(c: stmt:nestedClass, acc: acc);
			}
			is "IF": {
				stmt:thenBranch:each(action: local Function(Statement is s){
					self:collectClassesFromStatement(stmt: s, acc: acc);
				});
				if (stmt:hasElse) {
					stmt:elseBranch:each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
					});
				}
			}
			is "WHEN": {
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					arm:body:each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
					});
				});
			}
			else: {}
		}
	}

	local Function is collectClasses(ClassInfo is c, Array of ClassInfo is acc){
		acc:add(item: c);
		c:getMembers():each(action: local Function(Member is m){
			when (m:getMemberKind()) {
				is CLASS: {
					self:collectClasses(c: m:getNestedClass(), acc: acc);
				}
				is METHOD: {
					m:getBody():each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
					});
				}
				else: {}
			}
		});
	}

	## Translates a complete parsed program AST into a standalone C11 translation unit.
	##
	## @param program: Parsed [ProgramNode] AST.
	## @param entryClass: Application entry point class name.
	## @return: Complete C11 source code string.
	Function of String is generateProgram(ProgramNode is program, String is entryClass){
		local Array of ClassInfo is flattenedClasses: [];
		program:getClasses():each(action: local Function(ClassInfo is c){
			self:collectClasses(c: c, acc: flattenedClasses);
		});
		self:programClasses: flattenedClasses;

		self:allClassNames: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();
		self:allTaggedEnums: Map:init();
		flattenedClasses:each(action: local Function(ClassInfo is c){
			self:allClassNames:set(key: c:getName(), value: "true");
			c:getMembers():each(action: local Function(Member is m){
				if (m:getName() == "toString" && !self:classesWithToString:has(key: c:getName())) {
					self:classesWithToString:set(key: c:getName(), value: "true");
				}
			});
			if (c:getBaseClass() == "Enum") {
				self:allEnumNames:set(key: c:getName(), value: "true");
				c:getMembers():each(action: local Function(Member is m){
					self:allEnumVariants:set(key: m:getName(), value: c:getName());
					if (m:getParameters():length() > 0) {
						self:allTaggedEnums:set(key: c:getName(), value: "true");
					}
					if (m:getType():getName() == "String" || m:getType():getName() == "string") {
						self:allStringBackedEnums:set(key: c:getName(), value: "true");
					}
				});
			}
		});

		self:declGen:setEnumNames(names: self:allEnumNames);
		self:declGen:setTaggedEnums(names: self:allTaggedEnums);
		self:builtins:setEnumNames(names: self:allEnumNames);

		# Virtual slot assignment: method-name slots in deterministic
		# first-seen order; names declared by 2+ classes dispatch virtually.
		self:methodSlots: Map:init();
		self:overriddenMethods: Map:init();
		self:classesWithToString: Map:init();
		self:methodSlotCount: 0;
		self:slotNames: [];
		flattenedClasses:each(action: local Function(ClassInfo is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != "Enum") {
				c:getMembers():each(action: local Function(Member is m){
					if (m:getKind() == "METHOD") {
						if (self:methodSlots:has(key: m:getName())) {
							self:overriddenMethods:set(key: m:getName(), value: "true");
						} else {
							self:methodSlots:set(key: m:getName(), value: "" . self:methodSlotCount);
							self:slotNames:add(item: m:getName());
							self:methodSlotCount: self:methodSlotCount + 1;
						}
					}
				});
			}
		});

		local String is enums: self:declGen:generateEnums(classes: flattenedClasses);
		local String is decls: self:declGen:generateForwardDeclarations(classes: flattenedClasses);
		local String is structs: self:declGen:generateStructs(classes: flattenedClasses);
		local String is vt: self:generateVTables(classes: flattenedClasses);
		local String is ctors: self:generateConstructors(classes: flattenedClasses);

		local String is methods: "";
		flattenedClasses:each(action: local Function(ClassInfo is c){
			if (!self:isBuiltinClass(name: c:getName())) {
				self:currentClassName: c:getName();
				self:fieldTypes: Map:init();
				local Array of Member is allFields: [];
				self:declGen:collectStructFields(c: c, allClasses: flattenedClasses, acc: allFields);
				allFields:each(action: local Function(Member is m){
					self:fieldTypes:set(key: m:getName(), value: self:formatVarTypeString(t: m:getType()));
				});

				local Boolean is hasInit: false;
				c:getMembers():each(action: local Function(Member is m){
					when (m:getMemberKind()) {
						is METHOD: {
							if (m:getName() == "init") { hasInit: true; }
							methods: methods . self:generateMethod(classDef: c, method: m);
						}
						else: {}
					}
				});
				if (!hasInit && c:getBaseClass() != "Enum") {
					methods: methods . "void " . c:getName() . "_init(" . c:getName() . "* self) {\n    /* default initializer */\n}\n\n";
				}

				# Default toString for classes without a user definition, so that
				# concatenation and String casts render the class name, not a pointer.
				local Boolean is hasToString: false;
				c:getMembers():each(action: local Function(Member is m){
					if (m:getName() == "toString") {
						hasToString: true;
					}
				});
				if (!hasToString && c:getBaseClass() != "Enum") {
					local String is cn: c:getName();
					methods: methods . "const char* " . cn . "_toString(" . cn . "* self);\n";
					methods: methods . "const char* " . cn . "_toString(" . cn . "* self) {\n";
					methods: methods . "    if (!self) { return \"\"; }\n";
					methods: methods . "    return \"" . cn . "\";\n}\n\n";
				}
			}
		});

		local String is mainFn: self:generateMain(entryClass: entryClass);

		local String is cSource: "";
		cSource: cSource . self:generatePrelude();
		cSource: cSource . enums;
		cSource: cSource . decls;
		cSource: cSource . structs;
		cSource: cSource . vt;
		cSource: cSource . self:generateTypeHierarchy(classes: flattenedClasses);
		cSource: cSource . self:helperFunctions;
		cSource: cSource . ctors;
		cSource: cSource . methods;
		cSource: cSource . mainFn;
		return cSource;
	}

	local Function is collectAncestors(ClassInfo is c, Array of ClassInfo is allClasses, Array of String is acc){
		c:getBaseClasses():each(action: local Function(String is baseName){
			if (acc:indexOf(search: baseName, default: -1) < 0) {
				acc:add(item: baseName);
				allClasses:each(action: local Function(ClassInfo is cand){
					if (cand:getName() == baseName) {
						self:collectAncestors(c: cand, allClasses: allClasses, acc: acc);
					}
				});
			}
		});
	}

	local Function of String is generateTypeHierarchy(Array of ClassInfo is classes){
		local String is out: "/* RTTI Class Hierarchy */\n";
		out: out . "static bool spec_is_subclass_of(const char* actual, const char* target) {\n";
		out: out . "    if (!actual || !target) return false;\n";
		out: out . "    if (strcmp(actual, target) == 0) return true;\n";
		out: out . "    if (strcmp(target, \"Any\") == 0 || strcmp(target, \"Stringable\") == 0) return true;\n";
		classes:each(action: local Function(ClassInfo is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != "Enum") {
				local Array of String is ancestors: [];
				self:collectAncestors(c: c, allClasses: classes, acc: ancestors);
				if (ancestors:length() > 0) {
					out: out . "    if (strcmp(actual, \"" . c:getName() . "\") == 0) {\n";
					out: out . "        return ";
					local Boolean is firstA: true;
					ancestors:each(action: local Function(String is aName){
						if (!firstA) { out: out . " || "; }
						out: out . "(strcmp(target, \"" . aName . "\") == 0)";
						firstA: false;
					});
					out: out . ";\n    }\n";
				}
			}
		});
		out: out . "    return false;\n";
		out: out . "}\n\n";
		return out;
	}

	## Emits per-class virtual method tables.
	##
	## One table per class with one slot per virtual method name; each entry is
	## resolved by first-wins depth-first search (own concrete declaration
	## wins, else nearest ancestor). Merge overrides occupy their slot: their
	## forwards call the parent directly, so virtual entry cannot recurse.
	## Abstract slots resolve to NULL (concrete classes are checker-enforced
	## to implement them before instantiation).
	##
	## @param classes: Flattened [ClassInfo] list.
	## @return: C source defining every class vtable.
	local Function of String is generateVTables(Array of ClassInfo is classes){
		local String is out: "/* Virtual Method Tables */\n";
		if (self:methodSlotCount == 0) {
			return out;
		}
		classes:each(action: local Function(ClassInfo is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != "Enum") {
				out: out . "static void* " . c:getName() . "_vtable[" . self:methodSlotCount . "] = {\n";
				local Int is slot: 0;
				While:condition(
					evaluate: local Function of Boolean(){
						return slot < self:methodSlotCount;
					},
					iteration: local Function of Boolean(){
						local String is mName: self:slotNames:get(index: slot);
						local String is implCls: self:findMethodImplementingClass(className: c:getName(), methodName: mName, paramCount: -1);
						if (slot > 0) {
							out: out . ",\n";
						}
						if (implCls == "") {
							out: out . "    (void*)0";
						} else {
							out: out . "    (void*)" . implCls . "_" . mName;
						}
						slot: slot + 1;
						return true;
					}
				);
				out: out . "\n};\n\n";
			}
		});
		return out;
	}

}
