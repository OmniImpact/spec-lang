#! Package compiler
#! Pure Spec compiler implementation: DeclarationGenerator for C11 enums, structs, and forward declarations.

## Emits C11 enum definitions, forward declarations, and struct layouts from AST ClassInfo descriptors.
Class is DeclarationGenerator{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:ClassInfo,
		base:reflect:Member,
		base:reflect:Parameter,
		compiler:CBackendUtils
	];

	local CBackendUtils is utils;
	local Map of String to String is allEnumNames: Map:init();
	local Map of String to String is allTaggedEnums: Map:init();

	replace local Function is init(){
		self:utils: CBackendUtils:init();
		self:allEnumNames: Map:init();
		self:allTaggedEnums: Map:init();
	}

	replace local Function is setEnumNames(Map of String to String is names){
		self:allEnumNames: names;
	}

	replace local Function is setTaggedEnums(Map of String to String is names){
		self:allTaggedEnums: names;
	}

	replace local Function of String is cTypeFor(String is typeName){
		if (self:allTaggedEnums:has(key: typeName)) {
			return typeName . "*";
		}
		if (self:allEnumNames:has(key: typeName)) {
			return typeName;
		}
		return self:utils:cTypeFor(typeName: typeName);
	}

	replace local Function of String is cIdent(String is name){
		return self:utils:cIdent(name: name);
	}

	replace local Function of Boolean is isBuiltinClass(String is name){
		return self:utils:isBuiltinClass(name: name);
	}

	replace local Function of String is cTypeForClass(String is typeName, Array of String is typeParams){
		if (typeParams:indexOf(search: typeName, default: -1) >= 0) {
			return "void*";
		}
		return self:cTypeFor(typeName: typeName);
	}

	replace local Function of String is resolveReturnTypeForClass(Type is t, Array of String is typeParams){
		if (t:getName() == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:cTypeForClass(typeName: ret:getName(), typeParams: typeParams);
			}
			return "void";
		}
		return self:cTypeForClass(typeName: t:getName(), typeParams: typeParams);
	}

	Class is HasFieldLoop extends Loop{
		local Array of Member is list;
		local String is name: "";
		local Int is idx: 0;
		local Boolean is found: false;

		replace local Function is init(Array of Member is list, String is name){
			self:list: list;
			self:name: name;
			self:idx: 0;
			self:found: false;
		}

		replace local Function of Boolean is evaluate(){
			return !self:found && self:idx < self:list:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			local Member is item: self:list:get(index: self:idx);
			self:idx: self:idx + 1;
			if (item:getName() == self:name) {
				self:found: true;
			}
			return true;
		}
	}

	replace local Function of Boolean is hasFieldNamed(Array of Member is list, String is name){
		local HasFieldLoop is loopInst: HasFieldLoop:init(list: list, name: name);
		While:run(loop: loopInst);
		return loopInst:found;
	}

	replace local Function is collectStructFields(ClassInfo is c, Array of ClassInfo is allClasses, Array of Member is acc){
		c:getMembers():each(action: local Function(Member is m){
			when (m:getMemberKind()) {
				is FIELD: {
					if (m:getName() != "using" && !self:hasFieldNamed(list: acc, name: m:getName())) {
						acc:add(item: m);
					}
				}
				else: {}
			}
		});
		c:getBaseClasses():each(action: local Function(String is baseName){
			allClasses:each(action: local Function(ClassInfo is cand){
				if (cand:getName() == baseName) {
					self:collectStructFields(c: cand, allClasses: allClasses, acc: acc);
				}
			});
		});
	}

	replace local Function of String is generateEnums(Array of ClassInfo is classes){
		local String is out: "/* Enum Definitions */\n";

		classes:each(action: local Function(ClassInfo is c){
			if (c:getBaseClass() == "Enum") {
				local String is name: c:getName();
				if (self:allTaggedEnums:has(key: name)) {
					out: out . "typedef enum {\n";
					local Int is tIdx: 0;
					c:getMembers():each(action: local Function(Member is m){
						local String is vName: self:cIdent(name: m:getName());
						out: out . "    " . name . "_TAG_" . vName . " = " . tIdx . ",\n";
						tIdx: tIdx + 1;
					});
					out: out . "} " . name . "_Tag;\n";
					out: out . "typedef struct " . name . " " . name . ";\n\n";
				} else {
					out: out . "typedef enum {\n";
					local Int is idx: 0;
					c:getMembers():each(action: local Function(Member is m){
						local String is vName: self:cIdent(name: m:getName());
						out: out . "    " . name . "_" . vName . " = " . idx . ",\n";
						idx: idx + 1;
					});
					out: out . "} " . name . ";\n\n";

					out: out . "static const char* " . name . "_names[] = {\n";
					c:getMembers():each(action: local Function(Member is m){
						out: out . "    \"" . m:getName() . "\",\n";
					});
					out: out . "};\n\n";

					out: out . "static const " . name . " " . name . "_all_values[] = {\n";
					c:getMembers():each(action: local Function(Member is m){
						out: out . "    " . name . "_" . self:cIdent(name: m:getName()) . ",\n";
					});
					out: out . "};\n\n";

					out: out . "static inline const char* " . name . "_name(" . name . " self) {\n";
					out: out . "    switch (self) {\n";
					c:getMembers():each(action: local Function(Member is m){
						out: out . "        case " . name . "_" . self:cIdent(name: m:getName()) . ": return \"" . m:getName() . "\";\n";
					});
					out: out . "        default: return \"UNKNOWN\";\n";
					out: out . "    }\n}\n\n";

					local Boolean is isStrBacked: false;
					c:getMembers():each(action: local Function(Member is m){
						if (m:getType():getName() == "String" || m:getType():getName() == "string") {
							isStrBacked: true;
						}
					});

					if (isStrBacked) {
						out: out . "static inline const char* " . name . "_value(" . name . " self) {\n";
						out: out . "    switch (self) {\n";
						c:getMembers():each(action: local Function(Member is m){
							local String is valStr: m:getName();
							if (m:hasInit) {
								local Expression is initE: m:initExpr;
								if (initE:getKind() == "STRING") {
									valStr: initE:stringValue;
								}
							}
							out: out . "        case " . name . "_" . self:cIdent(name: m:getName()) . ": return \"" . valStr . "\";\n";
						});
						out: out . "        default: return \"\";\n";
						out: out . "    }\n}\n\n";
					} else {
						out: out . "static inline long long " . name . "_value(" . name . " self) {\n";
						out: out . "    switch (self) {\n";
						local Int is vIdx: 0;
						c:getMembers():each(action: local Function(Member is m){
							local String is valNum: "" . vIdx;
							if (m:hasInit) {
								local Expression is initE: m:initExpr;
								if (initE:getKind() == "NUMBER" && initE:stringValue != "") {
									valNum: initE:stringValue;
								} else if (initE:getKind() == "UNARY" && initE:unaryOp == "-" && initE:unaryExpr:getKind() == "NUMBER") {
									valNum: "-" . initE:unaryExpr:stringValue;
								}
							}
							out: out . "        case " . name . "_" . self:cIdent(name: m:getName()) . ": return " . valNum . "LL;\n";
							vIdx: vIdx + 1;
						});
						out: out . "        default: return 0LL;\n";
						out: out . "    }\n}\n\n";
					}

					out: out . "static inline long long " . name . "_ordinal(" . name . " self) {\n";
					out: out . "    switch (self) {\n";
					local Int is ordIdx: 0;
					c:getMembers():each(action: local Function(Member is m){
						out: out . "        case " . name . "_" . self:cIdent(name: m:getName()) . ": return " . ordIdx . ";\n";
						ordIdx: ordIdx + 1;
					});
					out: out . "        default: return -1;\n";
					out: out . "    }\n}\n\n";

					out: out . "static inline SpecArray* " . name . "_values(void) {\n";
					out: out . "    SpecArray* arr = spec_array_new();\n";
					out: out . "    for (size_t i = 0; i < " . idx . "; i++) {\n";
					out: out . "        spec_array_add(arr, (void*)(intptr_t)" . name . "_all_values[i]);\n";
					out: out . "    }\n    return arr;\n}\n\n";
				}
			}
		});

		return out;
	}

	replace local Function of String is generateForwardDeclarations(Array of ClassInfo is classes){
		local String is out: "/* Forward Declarations */\n";

		classes:each(action: local Function(ClassInfo is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != "Enum") {
				out: out . "typedef struct " . c:getName() . " " . c:getName() . ";\n";
				out: out . c:getName() . "* " . c:getName() . "_new(void);\n";
				local Boolean is hasInit: false;
				c:getMembers():each(action: local Function(Member is m){
					if (m:getName() == "init") { hasInit: true; }
				});
				if (!hasInit) {
					out: out . "void " . c:getName() . "_init(" . c:getName() . "* self);\n";
				}
			}
		});
		out: out . "\n";

		classes:each(action: local Function(ClassInfo is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != "Enum") {
				local Array of String is tps: c:getTypeParams();
				c:getMembers():each(action: local Function(Member is m){
					when (m:getMemberKind()) {
						is METHOD: {
							local String is retType: self:resolveReturnTypeForClass(t: m:getType(), typeParams: tps);
							if (retType == "void") {
								if (m:getName() == "evaluate" || m:getName() == "iteration") {
									retType: "bool";
								}
							}
							out: out . retType . " " . c:getName() . "_" . m:getName() . "(" . c:getName() . "* self";
							m:getParameters():each(action: local Function(Parameter is p){
								out: out . ", " . self:cTypeForClass(typeName: p:getType():getName(), typeParams: tps) . " " . self:cIdent(name: p:getName());
							});
							out: out . ");\n";
						}
						else: {}
					}
				});
			}
		});
		out: out . "\n";
		return out;
	}

	replace local Function of String is generateStructs(Array of ClassInfo is classes){
		local String is out: "/* Struct Layouts */\n";

		classes:each(action: local Function(ClassInfo is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != "Enum") {
				local Array of String is tps: c:getTypeParams();
				out: out . "struct " . c:getName() . " {\n";
				out: out . "    const char* _type_name;\n";
				local Array of Member is allFields: [];
				self:collectStructFields(c: c, allClasses: classes, acc: allFields);
				allFields:each(action: local Function(Member is m){
					out: out . "    " . self:cTypeForClass(typeName: m:getType():getName(), typeParams: tps) . " " . self:cIdent(name: m:getName()) . ";\n";
				});
				out: out . "};\n\n";
			} else if (c:getBaseClass() == "Enum" && self:allTaggedEnums:has(key: c:getName())) {
				local String is name: c:getName();
				out: out . "struct " . name . " {\n";
				out: out . "    " . name . "_Tag _tag;\n";
				out: out . "    const char* _variant_name;\n";
				c:getMembers():each(action: local Function(Member is m){
					local String is vName: self:cIdent(name: m:getName());
					m:getParameters():each(action: local Function(Parameter is p){
						out: out . "    " . self:cTypeFor(typeName: p:getType():getName()) . " " . vName . "_" . self:cIdent(name: p:getName()) . ";\n";
					});
				});
				out: out . "};\n\n";

				c:getMembers():each(action: local Function(Member is m){
					local String is vName: self:cIdent(name: m:getName());
					if (m:getParameters():length() == 0) {
						out: out . "static inline " . name . "* " . name . "_" . vName . "_ctor(void) {\n";
						out: out . "    " . name . "* _e = (" . name . "*)calloc(1, sizeof(" . name . "));\n";
						out: out . "    _e->_tag = " . name . "_TAG_" . vName . ";\n";
						out: out . "    _e->_variant_name = \"" . m:getName() . "\";\n";
						out: out . "    return _e;\n}\n\n";
					} else {
						out: out . "static inline " . name . "* " . name . "_" . vName . "(";
						local Boolean is firstP: true;
						m:getParameters():each(action: local Function(Parameter is p){
							if (!firstP) { out: out . ", "; }
							out: out . self:cTypeFor(typeName: p:getType():getName()) . " " . self:cIdent(name: p:getName());
							firstP: false;
						});
						out: out . ") {\n";
						out: out . "    " . name . "* _e = (" . name . "*)calloc(1, sizeof(" . name . "));\n";
						out: out . "    _e->_tag = " . name . "_TAG_" . vName . ";\n";
						out: out . "    _e->_variant_name = \"" . m:getName() . "\";\n";
						m:getParameters():each(action: local Function(Parameter is p){
							out: out . "    _e->" . vName . "_" . self:cIdent(name: p:getName()) . " = " . self:cIdent(name: p:getName()) . ";\n";
						});
						out: out . "    return _e;\n}\n\n";
					}
				});

				out: out . "static inline const char* " . name . "_name(" . name . "* self) {\n";
				out: out . "    return self ? self->_variant_name : \"UNKNOWN\";\n}\n\n";
				out: out . "static inline long long " . name . "_ordinal(" . name . "* self) {\n";
				out: out . "    return self ? (long long)self->_tag : -1;\n}\n\n";
			}
		});
		return out;
	}

}
