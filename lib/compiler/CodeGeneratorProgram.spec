#! Package compiler
#! Statement, method, entry-point, and whole-program C generation.
#! Group fragment merged into CodeGenerator at load time (see Loader).

## Statement, method, entry-point, and whole-program C generation.
Class is CodeGeneratorProgram{

	## Load-time grouping: members merge into CodeGenerator.
	replace local Array of String is group: [CodeGenerator];

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:Parameter,
		base:reflect:Member,
		base:reflect:ClassInfo,
		base:meta:*
	];

	replace local Function of String is generateStatement(Statement is stmt){
		local String is kind: stmt:getKind();

		when (kind) {
			is "VAR_DECL": {
				self:localVars:set(key: stmt:varName, value: self:formatVarTypeString(t: stmt:varType));
				local String is vTypeName: stmt:varType:getName();
				local String is cType: self:cTypeFor(typeName: vTypeName);
				local String is varName: self:cIdent(name: stmt:varName);
				if (stmt:hasInit) {
					local String is initC: self:generateExpression(expr: stmt:initExpr);
					if (cType:length() > 0 && cType:charAt(index: cType:length() - 1) == "*" && cType != "const char*" && cType != "SpecArray*" && cType != "SpecMap*") {
						initC: "(" . cType . ")(" . initC . ")";
					}
					if (cType == "const char*") {
						initC: "spec_str_clone_if_buffered(" . initC . ")";
					}
					return "    " . cType . " " . varName . " = " . initC . ";\n";
				}
				if (vTypeName == "String" || vTypeName == "string") {
					return "    " . cType . " " . varName . " = \"\";\n";
				}
				if (vTypeName == "Array") {
					return "    " . cType . " " . varName . " = spec_array_new();\n";
				}
				if (vTypeName == "Map") {
					return "    " . cType . " " . varName . " = spec_map_new();\n";
				}
				return "    " . cType . " " . varName . " = 0;\n";
			}
			is "ASSIGN": {
				if (stmt:assignTarget:getKind() == "INDEX") {
					local String is containerC: self:generateExpression(expr: stmt:assignTarget:leftExpr);
					local String is idxC: self:generateExpression(expr: stmt:assignTarget:rightExpr);
					local String is valC: self:generateExpression(expr: stmt:assignValue);
					local String is containerType: self:inferTargetType(expr: stmt:assignTarget:leftExpr);
					if (containerType:startsWith(prefix: "Map:") || containerType == "Map") {
						if (self:isStringExpr(expr: stmt:assignValue)) {
							return "    spec_map_set(" . containerC . ", " . idxC . ", " . valC . ");\n";
						}
						return "    spec_map_set_any(" . containerC . ", " . idxC . ", (void*)(intptr_t)(" . valC . "));\n";
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
						return "    " . self:inlineReturnVar . " = " . retC . "; goto " . self:inlineReturnLabel . ";\n";
					}
					return "    goto " . self:inlineReturnLabel . ";\n";
				}
				if (stmt:hasReturnExpr) {
					local String is retC: self:generateExpression(expr: stmt:returnExpr);
					local ClassInfo is curCls: self:findClass(name: self:currentClassName);
					if (curCls:getTypeParams():indexOf(search: self:currentMethodReturnType, default: -1) >= 0) {
						retC: "(void*)(intptr_t)(" . retC . ")";
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
	replace local Function of String is generateMethod(ClassInfo is classDef, Member is method){
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

		if (method:getName() != "init") {
			local Int is paramCount: method:getParameters():length();
			self:programClasses:each(action: local Function(ClassInfo is subCls){
				if (subCls:getName() != classDef:getName() && self:isSubclassOf(subName: subCls:getName(), baseName: classDef:getName())) {
					local MethodMemberLoop is trampMl: MethodMemberLoop:init(members: subCls:getMembers(), methodName: method:getName());
					While:run(loop: trampMl);
					local Boolean is isMergeOverride: false;
					if (trampMl:found) {
						isMergeOverride: trampMl:res:getModifiers():indexOf(search: "merge", default: -1) >= 0;
					}
					local String is implCls: "";
					if (!isMergeOverride) {
						implCls: self:findMethodImplementingClass(className: subCls:getName(), methodName: method:getName(), paramCount: paramCount);
						if (implCls != "") {
							# A merge implementation must never be entered via base-typed
							# dispatch: its forward calls back into this base method.
							local Member is implM: self:lookupMethodMember(className: implCls, methodName: method:getName());
							if (implM:getName() != "" && implM:getModifiers():indexOf(search: "merge", default: -1) >= 0) {
								implCls: "";
							}
						}
					}
					if (implCls != "" && implCls != classDef:getName()) {
						out: out . "    if (self && self->_type_name && strcmp(self->_type_name, \"" . subCls:getName() . "\") == 0) {\n";
						if (retType == "void") {
							out: out . "        " . implCls . "_" . method:getName() . "((" . implCls . "*)self" . callArgs . ");\n        return;\n";
						} else {
							out: out . "        return " . implCls . "_" . method:getName() . "((" . implCls . "*)self" . callArgs . ");\n";
						}
						out: out . "    }\n";
					}
				}
			});
		}

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
	replace local Function of String is generateMain(String is entryClass){
		local String is m: "/* Application Entry Point */\n";
		m: m . "int main(int argc, char** argv) {\n";
		m: m . "    srand((unsigned int)time(NULL));\n";
		m: m . "    SpecMap* args = spec_map_new();\n";
		m: m . "    for (int i = 1; i < argc; i++) {\n";
		m: m . "        if (strncmp(argv[i], \"--\", 2) == 0) {\n";
		m: m . "            const char* key = argv[i] + 2;\n";
		m: m . "            const char* val = \"true\";\n";
		m: m . "            if (i + 1 < argc && argv[i + 1][0] != '-') {\n";
		m: m . "                val = argv[++i];\n";
		m: m . "            }\n";
		m: m . "            spec_map_set(args, key, val);\n";
		m: m . "        } else if (argv[i][0] == '-' && argv[i][1] != '\\0') {\n";
		m: m . "            const char* key = argv[i] + 1;\n";
		m: m . "            const char* val = \"true\";\n";
		m: m . "            if (i + 1 < argc && argv[i + 1][0] != '-') {\n";
		m: m . "                val = argv[++i];\n";
		m: m . "            }\n";
		m: m . "            spec_map_set(args, key, val);\n";
		m: m . "        }\n";
		m: m . "    }\n";
		m: m . "    " . entryClass . "* app = " . entryClass . "_new();\n";
		m: m . "    " . entryClass . "_init(app, args);\n";
		m: m . "    spec_drain_async_tasks();\n";
		m: m . "    return 0;\n";
		m: m . "}\n";
		return m;
	}

	replace local Function is collectClassesFromStatement(Statement is stmt, Array of ClassInfo is acc){
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

	replace local Function is collectClasses(ClassInfo is c, Array of ClassInfo is acc){
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
	replace local Function of String is generateProgram(ProgramNode is program, String is entryClass){
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

		local String is enums: self:declGen:generateEnums(classes: flattenedClasses);
		local String is decls: self:declGen:generateForwardDeclarations(classes: flattenedClasses);
		local String is structs: self:declGen:generateStructs(classes: flattenedClasses);
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
			}
		});

		local String is mainFn: self:generateMain(entryClass: entryClass);

		local String is cSource: "";
		cSource: cSource . self:generatePrelude();
		cSource: cSource . enums;
		cSource: cSource . decls;
		cSource: cSource . structs;
		cSource: cSource . self:helperFunctions;
		cSource: cSource . ctors;
		cSource: cSource . methods;
		cSource: cSource . mainFn;
		return cSource;
	}

}
