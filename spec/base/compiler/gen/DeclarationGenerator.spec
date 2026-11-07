#! Package base:compiler:gen
#! Emits C declarations: enums (with value/of helpers), forward
#! declarations, struct layouts, and method prototypes.
##
## Emission transparency is decided by [EmissionPolicy]: runtime-managed
## classes get no struct or vtable; their instances live in the C runtime.
## Declarative metadata members (namespace/using/group/castable) are
#! loader directives and never become struct fields.

Class is DeclarationGenerator{
	namespace: ['base', 'compiler', 'gen'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', MetadataField],
		['base', 'compiler', 'ast', ContractMethod],
		['base', 'compiler', WellKnown],
		['base', 'compiler', 'gen', CBackendUtils],
		['base', 'compiler', 'gen', EmissionPolicy],
		['base', 'iterator']
	];

	## Enum name -> "true" (string-backed enums included).
	local Map of String to String is allEnumNames: Map:init();

	## Tagged-union enum names -> "true".
	local Map of String to String is allTaggedEnums: Map:init();

	## Well-known names.
	local WellKnown is names: WellKnown:init();

	## Backend utilities.
	local CBackendUtils is utils: CBackendUtils:init();

	## Emission transparency decisions.
	local EmissionPolicy is policy: EmissionPolicy:init();

	replace Function is init(){
		self:allEnumNames: Map:init();
		self:allTaggedEnums: Map:init();
	}

	## Receives the enum registries gathered by the checker.
	##
	## @param names: All enum names.
	Function is setEnumNames(Map of String to String is names){
		self:allEnumNames: names;
	}

	## Receives the tagged-enum registry.
	##
	## @param names: Tagged enum names.
	Function is setTaggedEnums(Map of String to String is names){
		self:allTaggedEnums: names;
	}

	## Maps a type name to its C type, grounding the class's own generic
	## parameters to void*.
	##
	## @param typeName: Type name.
	## @param typeParams: The class's generic parameter names.
	## @return: C type string.
	Function of String is cTypeForClass(String is typeName, Array of String is typeParams){
		if (typeParams:indexOf(search: typeName, default: -1) >= 0) {
			return 'void*';
		}
		local String is base: typeName;
		if (base:contains(needle: ':')) {
			local Array of String is parts: base:split(delimiter: ':');
			base: parts:get(index: 0);
		}
		# Enum types pass by value in prototypes, matching the definitions
		# the method emitter produces (tagged unions are pointers).
		if (self:allEnumNames:has(key: base) && !self:allTaggedEnums:has(key: base)) {
			return base;
		}
		return self:utils:cTypeFor(typeName: typeName);
	}

	## Resolves the C return type of a method inside a generic class.
	##
	## @param t: Declared type descriptor.
	## @param typeParams: The class's generic parameter names.
	## @return: C return type string.
	Function of String is resolveReturnTypeForClass(Type is t, Array of String is typeParams){
		if (Primitive:of(t:name) == Primitive:FUNCTION) {
			if (t:params:length() > 0) {
				local Type is ret: t:params:get(index: 0);
				return self:cTypeForClass(typeName: ret:name, typeParams: typeParams);
			}
			return 'void';
		}
		return self:cTypeForClass(typeName: t:name, typeParams: typeParams);
	}

	## True when [list] carries a member named [name].
	##
	## @param list: Members to scan.
	## @param name: Member name.
	## @return: true when present.
	Function of Boolean is hasFieldNamed(Array of Member is list, String is name){
		local HasFieldLoop is loop: HasFieldLoop:init(list: list, name: name);
		While:run(loop: loop);
		return loop:found;
	}

	## Collects a class's struct fields: base fields first (ancestor casts
	## stay offset-correct), most-derived declaration winning on redeclare.
	## Metadata members never become fields.
	##
	## @param c: The class.
	## @param allClasses: The full program classes (base lookup).
	## @param acc: Output field list.
	Function is collectStructFields(ClassInfo is c, Array of ClassInfo is allClasses, Array of Member is acc){
		c:baseClasses:each(action: local Function(String is baseName){
			allClasses:each(action: local Function(ClassInfo is cand){
				if (cand:name == baseName) {
					self:collectStructFields(c: cand, allClasses: allClasses, acc: acc);
				}
			});
		});
		c:members:each(action: local Function(Member is m){
			when (m:kind) {
				is MemberKind:FIELD: {
					# Declarative metadata (namespace/using/group/castable)
					# never becomes a struct field.
					if (m:name != MetadataField:USING:value() && m:name != MetadataField:NAMESPACE:value() &&
						m:name != MetadataField:GROUP:value() && m:name != MetadataField:CASTABLE:value()) {
						local Int is existing: self:fieldIndexNamed(list: acc, name: m:name);
						if (existing >= 0) {
							acc:set(index: existing, item: m);
						} else {
							acc:add(item: m);
						}
					}
				}
				else: {}
			}
		});
	}

	## Finds a field's index in an accumulator by name.
	##
	## @param list: Accumulated fields.
	## @param name: Field name.
	## @return: The index, or -1.
	Function of Int is fieldIndexNamed(Array of Member is list, String is name){
		local FieldIndexLoop is loop: FieldIndexLoop:init(list: list, name: name);
		While:run(loop: loop);
		return loop:res;
	}

	## Emits the C enum definitions for every enum in the program:
	## tagged-union enums get tag structs and variant constructors;
	## plain enums get names/value/ordinal/values tables plus value() and
	## of() lookups for string-backed variants.
	##
	## @param classes: Program classes.
	## @return: C source text.
	Function of String is generateEnums(Array of ClassInfo is classes){
		local String is out: "/* Enum Definitions */\n";

		classes:each(action: local Function(ClassInfo is c){
			if (c:baseClass == self:names:enumHeader()) {
				local String is name: c:name;
				if (self:allTaggedEnums:has(key: name)) {
					out: out . "typedef enum {\n";
					local Int is tIdx: 0;
					c:members:each(action: local Function(Member is m){
						out: out . '    ' . name . '_TAG_' . self:utils:cIdent(name: m:name) . ' = ' . tIdx . ",\n";
						tIdx: tIdx + 1;
					});
					out: out . '} ' . name . "_Tag;\n";
					out: out . 'typedef struct ' . name . ' ' . name . ";\n\n";
				} else {
					out: out . "typedef enum {\n";
					local Int is idx: 0;
					c:members:each(action: local Function(Member is m){
						out: out . '    ' . name . '_' . self:utils:cIdent(name: m:name) . ' = ' . idx . ",\n";
						idx: idx + 1;
					});
					out: out . '} ' . name . ";\n\n";

					out: out . 'static const char* ' . name . "_names[] = {\n";
					c:members:each(action: local Function(Member is m){
						out: out . '    "' . m:name . "\",\n";
					});
					out: out . "};\n\n";

					out: out . 'static const ' . name . ' ' . name . "_all_values[] = {\n";
					c:members:each(action: local Function(Member is m){
						out: out . '    ' . name . '_' . self:utils:cIdent(name: m:name) . ",\n";
					});
					out: out . "};\n\n";

					out: out . 'static inline String ' . name . '_name(' . name . " self) {\n";
					out: out . "    switch (self) {\n";
					c:members:each(action: local Function(Member is m){
						out: out . '        case ' . name . '_' . self:utils:cIdent(name: m:name) . ': return spec_string_intern("' . m:name . '");' . "\n";
					});
					out: out . "        default: return spec_string_intern(\"UNKNOWN\");\n";
					out: out . "    }\n}\n\n";

					local Boolean is isStrBacked: false;
					c:members:each(action: local Function(Member is m){
						if (m:memberType:name == Primitive:STRING:value()) {
							isStrBacked: true;
						}
					});

					if (isStrBacked) {
						out: out . self:emitStringBacking(name: name, cls: c);
					} else {
						out: out . self:emitIntBacking(name: name, cls: c);
					}

					out: out . 'static inline long long ' . name . '_ordinal(' . name . " self) {\n";
					out: out . "    switch (self) {\n";
					local Int is ordIdx: 0;
					c:members:each(action: local Function(Member is m){
						out: out . '        case ' . name . '_' . self:utils:cIdent(name: m:name) . ': return ' . ordIdx . ";\n";
						ordIdx: ordIdx + 1;
					});
					out: out . "        default: return -1;\n";
					out: out . "    }\n}\n\n";

					out: out . 'static inline SpecArray* ' . name . "_values(void) {\n";
					out: out . "    SpecArray* arr = spec_array_new();\n";
					out: out . '    for (size_t i = 0; i < ' . idx . "; i++) {\n";
					out: out . '        spec_array_add(arr, (void*)(intptr_t)' . name . "_all_values[i]);\n";
					out: out . "    }\n    return arr;\n}\n\n";
				}
			}
		});

		return out;
	}

	## Emits the string-backed helpers: value() (variant -> tag) and of()
	## (tag -> variant; no match yields the empty-tag variant, else -1).
	##
	## @param name: Enum name.
	## @param cls: The enum class.
	## @return: C source text.
	Function of String is emitStringBacking(String is name, ClassInfo is cls){
		local String is out: '';
		out: out . 'static inline String ' . name . '_value(' . name . " self) {\n";
		out: out . "    switch (self) {\n";
		cls:members:each(action: local Function(Member is m){
			out: out . '        case ' . name . '_' . self:utils:cIdent(name: m:name) . ': return spec_string_intern("' . self:variantTag(m: m) . '");' . "\n";
		});
		out: out . "        default: return spec_string_intern(\"\");\n";
		out: out . "    }\n}\n\n";

		local String is emptyVariant: '';
		out: out . 'static inline ' . name . ' ' . name . '_of(String v) {' . "\n";
		cls:members:each(action: local Function(Member is m){
			local String is valStr: self:variantTag(m: m);
			if (valStr == '') {
				emptyVariant: m:name;
			}
			out: out . '    if (spec_string_equals(v, spec_string_intern("' . valStr . '"))) return ' . name . '_' . self:utils:cIdent(name: m:name) . ";\n";
		});
		if (emptyVariant != '') {
			out: out . '    return ' . name . '_' . self:utils:cIdent(name: emptyVariant) . ";\n";
		} else {
			out: out . '    return (' . name . ")-1;\n";
		}
		out: out . "}\n\n";
		return out;
	}

	## Emits the integer-backed helper: value() (variant -> declared or
	## ordinal integer).
	##
	## @param name: Enum name.
	## @param cls: The enum class.
	## @return: C source text.
	Function of String is emitIntBacking(String is name, ClassInfo is cls){
		local String is out: '';
		out: out . 'static inline long long ' . name . '_value(' . name . " self) {\n";
		out: out . "    switch (self) {\n";
		local Int is vIdx: 0;
		cls:members:each(action: local Function(Member is m){
			local String is valNum: '' . vIdx;
			if (m:hasInit) {
				local Expression is initE: m:initExpr;
				if (initE:kind == ExpressionKind:NUMBER && initE:stringValue != '') {
					valNum: initE:stringValue;
				} else if (initE:kind == ExpressionKind:UNARY && initE:unaryOp == '-' && initE:unaryExpr:kind == ExpressionKind:NUMBER) {
					valNum: '-' . initE:unaryExpr:stringValue;
				}
			}
			out: out . '        case ' . name . '_' . self:utils:cIdent(name: m:name) . ': return ' . valNum . "LL;\n";
			vIdx: vIdx + 1;
		});
		out: out . "        default: return 0LL;\n";
		out: out . "    }\n}\n\n";
		return out;
	}

	## Resolves a variant's string tag: the declared `: 'tag'` value, or the
	## variant name when untagged.
	##
	## @param m: The variant member.
	## @return: The tag string.
	Function of String is variantTag(Member is m){
		if (m:hasInit) {
			local Expression is initE: m:initExpr;
			if (initE:kind == ExpressionKind:STRING) {
				return initE:stringValue;
			}
		}
		return m:name;
	}

	## Emits forward declarations (typedefs, constructors, destructors) for
	## every emission-visible class.
	##
	## @param classes: Program classes.
	## @return: C source text.
	Function of String is generateForwardDeclarations(Array of ClassInfo is classes){
		local String is out: "/* Forward Declarations */\n";

		classes:each(action: local Function(ClassInfo is c){
			if (!self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader()) {
				out: out . 'typedef struct ' . c:name . ' ' . c:name . ";\n";
				out: out . c:name . '* ' . c:name . "_new(void);\n";
				out: out . 'void ' . c:name . "_destroy(void* self);\n";
				if (!self:hasFieldNamed(list: c:members, name: 'init')) {
					out: out . 'void ' . c:name . '_init(' . c:name . "* self);\n";
				}
			}
		});
		out: out . "\n";

		classes:each(action: local Function(ClassInfo is c){
			if (self:policy:emitsPrototypes(c: c) && c:baseClass != self:names:enumHeader()) {
				local Array of String is tps: c:typeParams;
				c:members:each(action: local Function(Member is m){
					when (m:kind) {
						is MemberKind:METHOD: {
							local String is retType: self:resolveReturnTypeForClass(t: m:memberType, typeParams: tps);
							if (retType == 'void') {
								if (m:name == ContractMethod:EVALUATE:value() || m:name == ContractMethod:ITERATION:value()) {
									retType: 'bool';
								}
							}
							out: out . retType . ' ' . c:name . '_' . m:name . '(' . self:cTypeForClass(typeName: c:name, typeParams: tps) . ' self';
							m:params:each(action: local Function(Parameter is p){
								out: out . ', ' . self:cTypeForClass(typeName: p:paramType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: p:name);
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

	## Emits struct layouts for emission-visible classes and tagged-union
	## variant structs with constructors for tagged enums.
	##
	## @param classes: Program classes.
	## @return: C source text.
	Function of String is generateStructs(Array of ClassInfo is classes){
		local String is out: "/* Struct Layouts */\n";

		classes:each(action: local Function(ClassInfo is c){
			if (!self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader()) {
				local Array of String is tps: c:typeParams;
				out: out . 'struct ' . c:name . " {\n";
				out: out . "    const char* _type_name;\n";
				out: out . "    void** _vtable;\n";
				local Array of Member is allFields: [];
				self:collectStructFields(c: c, allClasses: classes, acc: allFields);
				allFields:each(action: local Function(Member is m){
					out: out . '    ' . self:cTypeForClass(typeName: m:memberType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: m:name) . ";\n";
				});
				out: out . "};\n\n";
			} else if (c:baseClass == self:names:enumHeader() && self:allTaggedEnums:has(key: c:name)) {
				out: out . self:emitTaggedEnumStruct(name: c:name, cls: c);
			}
		});
		return out;
	}

	## Emits a tagged enum's struct, variant constructors, and accessors.
	##
	## @param name: Enum name.
	## @param cls: The enum class.
	## @return: C source text.
	Function of String is emitTaggedEnumStruct(String is name, ClassInfo is cls){
		local String is out: '';
		out: out . 'struct ' . name . " {\n";
		out: out . '    ' . name . "_Tag _tag;\n";
		out: out . "    const char* _variant_name;\n";
		cls:members:each(action: local Function(Member is m){
			local String is vName: self:utils:cIdent(name: m:name);
			m:params:each(action: local Function(Parameter is p){
				out: out . '    ' . self:utils:cTypeFor(typeName: p:paramType:name) . ' ' . vName . '_' . self:utils:cIdent(name: p:name) . ";\n";
			});
		});
		out: out . "};\n\n";

		cls:members:each(action: local Function(Member is m){
			local String is vName: self:utils:cIdent(name: m:name);
			if (m:params:length() == 0) {
				out: out . 'static inline ' . name . '* ' . name . '_' . vName . "_ctor(void) {\n";
				out: out . '    ' . name . '* _e = (' . name . '*)spec_alloc(sizeof(' . name . "), NULL);\n";
				out: out . '    _e->_tag = ' . name . '_TAG_' . vName . ";\n";
				out: out . '    _e->_variant_name = "' . m:name . "\";\n";
				out: out . "    return _e;\n}\n\n";
			} else {
				out: out . 'static inline ' . name . '* ' . name . '_' . vName . '(';
				local Boolean is firstP: true;
				m:params:each(action: local Function(Parameter is p){
					if (!firstP) { out: out . ', '; }
					out: out . self:utils:cTypeFor(typeName: p:paramType:name) . ' ' . self:utils:cIdent(name: p:name);
					firstP: false;
				});
				out: out . ") {\n";
				out: out . '    ' . name . '* _e = (' . name . '*)spec_alloc(sizeof(' . name . "), NULL);\n";
				out: out . '    _e->_tag = ' . name . '_TAG_' . vName . ";\n";
				out: out . '    _e->_variant_name = "' . m:name . "\";\n";
				m:params:each(action: local Function(Parameter is p){
					out: out . '    _e->' . vName . '_' . self:utils:cIdent(name: p:name) . ' = ' . self:utils:cIdent(name: p:name) . ";\n";
				});
				out: out . "    return _e;\n}\n\n";
			}
		});

		out: out . 'static inline String ' . name . '_name(' . name . "* self) {\n";
		out: out . "    return self ? spec_string_from_chars(self->_variant_name) : spec_string_intern(\"UNKNOWN\");\n}\n\n";
		out: out . 'static inline long long ' . name . '_ordinal(' . name . "* self) {\n";
		out: out . "    return self ? (long long)self->_tag : -1;\n}\n\n";
		return out;
	}

	## True when [list] has a member with the name (scan state).
	Class of Loop is HasFieldLoop{
		local Array of Member is list;
		local String is name;
		local Int is idx: 0;
		local Boolean is found: false;

		replace Function is init(Array of Member is list, String is name){
			self:list: list;
			self:name: name;
			self:idx: 0;
			self:found: false;
		}

		replace Function of Boolean is evaluate(){
			return !self:found && self:idx < self:list:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:list:get(index: self:idx);
			self:idx: self:idx + 1;
			if (m:name == self:name) {
				self:found: true;
				return false;
			}
			return true;
		}
	}

	## Walks a field accumulator tracking a name's index.
	Class of Loop is FieldIndexLoop{
		local Array of Member is list;
		local String is name;
		local Int is idx: 0;
		local Int is res: -1;

		replace Function is init(Array of Member is list, String is name){
			self:list: list;
			self:name: name;
			self:idx: 0;
			self:res: -1;
		}

		replace Function of Boolean is evaluate(){
			return self:res < 0 && self:idx < self:list:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:list:get(index: self:idx);
			if (m:name == self:name) {
				self:res: self:idx;
			}
			self:idx: self:idx + 1;
			return true;
		}
	}
}
