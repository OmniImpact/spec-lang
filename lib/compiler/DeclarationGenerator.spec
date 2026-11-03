#! Package compiler
#! Pure Spec compiler implementation: DeclarationGenerator for C11 enums, structs, and forward declarations.

## Emits C11 enum definitions, forward declarations, and struct layouts from AST Class descriptors.
class DeclarationGenerator{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:Class,
		base:reflect:Member,
		base:reflect:Parameter,
		compiler:CBackendUtils
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

	replace local Function of String is cTypeFor(String is typeName){
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

	replace local Function of String is resolveReturnType(Type is t){
		if (t:getName() == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:cTypeFor(typeName: ret:getName());
			}
			return "void";
		}
		return self:cTypeFor(typeName: t:getName());
	}

	class HasFieldLoop extends Loop{
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

	replace local Function is collectStructFields(Class is c, Array of Class is allClasses, Array of Member is acc){
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
			allClasses:each(action: local Function(Class is cand){
				if (cand:getName() == baseName) {
					self:collectStructFields(c: cand, allClasses: allClasses, acc: acc);
				}
			});
		});
	}

	replace local Function of String is generateEnums(Array of Class is classes){
		local String is out: "/* Enum Definitions */\n";

		classes:each(action: local Function(Class is c){
			if (c:getBaseClass() == "Enum") {
				local String is name: c:getName();
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
					out: out . "    return (long long)self;\n}\n\n";
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
		});

		return out;
	}

	replace local Function of String is generateForwardDeclarations(Array of Class is classes){
		local String is out: "/* Forward Declarations */\n";

		classes:each(action: local Function(Class is c){
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

		classes:each(action: local Function(Class is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != "Enum") {
				c:getMembers():each(action: local Function(Member is m){
					when (m:getMemberKind()) {
						is METHOD: {
							if (m:getBody():length() > 0 || m:getName() == "init") {
								local String is retType: self:resolveReturnType(t: m:getType());
								if (retType == "void") {
									if (m:getName() == "evaluate" || m:getName() == "iteration") {
										retType: "bool";
									}
									if (m:getName() == "drawCard" || m:getName() == "handValue") {
										retType: "long long";
									}
								}
								out: out . retType . " " . c:getName() . "_" . m:getName() . "(" . c:getName() . "* self";
								m:getParameters():each(action: local Function(Parameter is p){
									out: out . ", " . self:cTypeFor(typeName: p:getType():getName()) . " " . self:cIdent(name: p:getName());
								});
								out: out . ");\n";
							}
						}
						else: {}
					}
				});
			}
		});
		out: out . "\n";
		return out;
	}

	replace local Function of String is generateStructs(Array of Class is classes){
		local String is out: "/* Struct Layouts */\n";

		classes:each(action: local Function(Class is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != "Enum") {
				out: out . "struct " . c:getName() . " {\n";
				local Array of Member is allFields: [];
				self:collectStructFields(c: c, allClasses: classes, acc: allFields);
				allFields:each(action: local Function(Member is m){
					out: out . "    " . self:cTypeFor(typeName: m:getType():getName()) . " " . self:cIdent(name: m:getName()) . ";\n";
				});
				out: out . "};\n\n";
			}
		});
		return out;
	}

}
