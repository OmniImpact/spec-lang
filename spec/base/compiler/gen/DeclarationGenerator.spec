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
		['base', 'sys', as Conditional()],
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
		['base', 'iterator'],
		['base', 'iterator', as While()]
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
		Conditional:if(check: { typeParams:indexOf(search: typeName, default: -1) >= 0 }, then: {
			return 'void*';
		});
		local String is base: typeName;
		Conditional:if(check: { base:contains(needle: ':') }, then: {
			local Array of String is parts: base:split(delimiter: ':');
			base: parts:get(index: 0);
		});
		# Enum types pass by value in prototypes, matching the definitions
		# the method emitter produces (tagged unions are pointers).
		Conditional:if(check: { self:allEnumNames:has(key: base) && !self:allTaggedEnums:has(key: base) }, then: {
			return base;
		});
		return self:utils:cTypeFor(typeName: typeName);
	}

	## Resolves the C return type of a method inside a generic class.
	##
	## @param t: Declared type descriptor.
	## @param typeParams: The class's generic parameter names.
	## @return: C return type string.
	Function of String is resolveReturnTypeForClass(Type is t, Array of String is typeParams){
		Conditional:if(check: { Primitive:of(t:name) == Primitive:FUNCTION }, then: {
			Conditional:if(check: { t:params:length() > 0 }, then: {
				local Type is ret: t:params:get(index: 0);
				return self:cTypeForClass(typeName: ret:name, typeParams: typeParams);
			});
			return 'void';
		});
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
		local Array of Member is ignoredOuter: [];
		self:collectStructFieldsSplit(c: c, allClasses: allClasses, acc: acc, outerAcc: ignoredOuter, fromOuterLink: false);
	}

	## FUNCTIONS.md Part IV IV.2: the struct-field collection with the
	## outer-link split — the fields reached through the OUTER chain (the
	## inner-class link) accumulate into [outerAcc]; the declared-of
	## lattice and the class's own fields into [acc]. The construction
	## expressions run for [acc] only; [outerAcc] zero-inits.
	##
	## @param c: The class.
	## @param allClasses: The full program classes (base lookup).
	## @param acc: The declared-of + own field list.
	## @param outerAcc: The outer-link field list.
	## @param fromOuterLink: True when [c] was reached through the outer chain.
	Function is collectStructFieldsSplit(ClassInfo is c, Array of ClassInfo is allClasses, Array of Member is acc, Array of Member is outerAcc, Boolean is fromOuterLink){
		local Array of Member is target: acc;
		Conditional:if(check: { fromOuterLink }, then: {
			target: outerAcc;
		});
		c:baseClasses:each(action: local Function(String is baseName){
			# FUNCTIONS.md Part IV IV.2: the base is the outer-link relation
			# when its name appears in this class's outer chain.
			local Boolean is baseIsOuter: c:outerName != '' && (c:outerName == baseName || c:outerName:contains(needle: ':' . baseName));
			allClasses:each(action: local Function(ClassInfo is cand){
				Conditional:if(check: { cand:name == baseName }, then: {
					self:collectStructFieldsSplit(c: cand, allClasses: allClasses, acc: acc, outerAcc: outerAcc, fromOuterLink: baseIsOuter);
				});
			});
		});
		c:members:each(action: local Function(Member is m){
			when (m:kind) {
				is MemberKind:FIELD: {
					# Declarative metadata (namespace/using/castable)
					# never becomes a struct field.
					Conditional:if(check: { m:name != MetadataField:USING:value() && m:name != MetadataField:NAMESPACE:value() &&
						m:name != MetadataField:CASTABLE:value() }, then: {
						local Int is existing: self:fieldIndexNamed(list: target, name: m:name);
						Conditional:if(check: { existing >= 0 }, then: {
							target:set(index: existing, item: m);
						}, else: {
							target:add(item: m);
						});
					});
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
			Conditional:if(check: { c:baseClass == self:names:enumHeader() }, then: {
				local String is name: c:name;
				# The namespace declaration is metadata inside the body —
				# filter it out of the variant surface once, up front.
				local Array of Member is variants: [];
				c:members:each(action: local Function(Member is m){
					Conditional:if(check: { !(m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) }, then: {
						variants:add(item: m);
					});
				});
				Conditional:if(check: { self:allTaggedEnums:has(key: name) }, then: {
					out: out . "typedef enum {\n";
					local Int is tIdx: 0;
					variants:each(action: local Function(Member is m){
						out: out . '    ' . name . '_TAG_' . self:utils:cIdent(name: m:name) . ' = ' . tIdx . ",\n";
						tIdx: tIdx + 1;
					});
					out: out . '} ' . name . "_Tag;\n";
					out: out . 'typedef struct ' . name . ' ' . name . ";\n\n";
				}, else: {
					out: out . "typedef enum {\n";
					local Int is idx: 0;
					variants:each(action: local Function(Member is m){
						out: out . '    ' . name . '_' . self:utils:cIdent(name: m:name) . ' = ' . idx . ",\n";
						idx: idx + 1;
					});
					out: out . '} ' . name . ";\n\n";

					out: out . 'static __attribute__((unused)) const char* ' . name . "_names[] = {\n";
					variants:each(action: local Function(Member is m){
						out: out . '    "' . m:name . "\",\n";
					});
					out: out . "};\n\n";

					out: out . 'static const ' . name . ' ' . name . "_all_values[] = {\n";
					variants:each(action: local Function(Member is m){
						out: out . '    ' . name . '_' . self:utils:cIdent(name: m:name) . ",\n";
					});
					out: out . "};\n\n";

					out: out . 'static inline String ' . name . '_name(' . name . " self) {\n";
					out: out . "    (void)self;\n";
					out: out . "    switch (self) {\n";
					variants:each(action: local Function(Member is m){
						out: out . '        case ' . name . '_' . self:utils:cIdent(name: m:name) . ': return spec_string_intern("' . m:name . '");' . "\n";
					});
					out: out . "        default: return spec_string_intern(\"UNKNOWN\");\n";
					out: out . "    }\n}\n\n";

					local Boolean is isStrBacked: false;
					variants:each(action: local Function(Member is m){
						Conditional:if(check: { m:memberType:name == Primitive:STRING:value() }, then: {
							isStrBacked: true;
						});
					});

					Conditional:if(check: { isStrBacked }, then: {
						out: out . self:emitStringBacking(name: name, cls: c);
					}, else: {
						out: out . self:emitIntBacking(name: name, cls: c);
					});

					out: out . 'static inline long long ' . name . '_ordinal(' . name . " self) {\n";
					out: out . "    (void)self;\n";
					out: out . "    switch (self) {\n";
					local Int is ordIdx: 0;
					variants:each(action: local Function(Member is m){
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
				});
			});
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
		# Metadata (the namespace declaration) is not a variant.
		local Array of Member is variants: [];
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { !(m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) }, then: {
				variants:add(item: m);
			});
		});
		out: out . 'static inline String ' . name . '_value(' . name . " self) {\n";
		out: out . "    (void)self;\n";
					out: out . "    switch (self) {\n";
		variants:each(action: local Function(Member is m){
			out: out . '        case ' . name . '_' . self:utils:cIdent(name: m:name) . ': return spec_string_intern("' . self:variantTag(m: m) . '");' . "\n";
		});
		out: out . "        default: return spec_string_intern(\"\");\n";
		out: out . "    }\n}\n\n";

		local String is emptyVariant: '';
		out: out . 'static inline ' . name . ' ' . name . '_of(String v) {' . "\n";
		variants:each(action: local Function(Member is m){
			local String is valStr: self:variantTag(m: m);
			Conditional:if(check: { valStr == '' }, then: {
				emptyVariant: m:name;
			});
			out: out . '    if (spec_string_equals(v, spec_string_intern("' . valStr . '"))) return ' . name . '_' . self:utils:cIdent(name: m:name) . ";\n";
		});
		Conditional:if(check: { emptyVariant != '' }, then: {
			out: out . '    return ' . name . '_' . self:utils:cIdent(name: emptyVariant) . ";\n";
		}, else: {
			out: out . '    return (' . name . ")-1;\n";
		});
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
		# Metadata (the namespace declaration) is not a variant.
		local Array of Member is variants: [];
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { !(m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) }, then: {
				variants:add(item: m);
			});
		});
		out: out . 'static inline long long ' . name . '_value(' . name . " self) {\n";
		out: out . "    (void)self;\n";
					out: out . "    switch (self) {\n";
		local Int is vIdx: 0;
		variants:each(action: local Function(Member is m){
			local String is valNum: '' . vIdx;
			Conditional:if(check: { m:hasInit }, then: {
				local Expression is initE: m:initExpr;
				Conditional:if(check: { initE:kind == ExpressionKind:NUMBER && initE:stringValue != '' }, then: {
					valNum: initE:stringValue;
				}, else: {
					Conditional:if(check: { initE:kind == ExpressionKind:UNARY && initE:unaryOp == '-' && initE:unaryExpr:kind == ExpressionKind:NUMBER }, then: {
						valNum: '-' . initE:unaryExpr:stringValue;
					});
				});
			});
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
		Conditional:if(check: { m:hasInit }, then: {
			local Expression is initE: m:initExpr;
			Conditional:if(check: { initE:kind == ExpressionKind:STRING }, then: {
				return initE:stringValue;
			});
		});
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
				Conditional:if(check: { !self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader() }, then: {
					local String is cSym: self:utils:cIdent(name: c:qualifiedName());
					# FUNCTIONS.md Part IV IV.2c: for nested classes the typedef
					# ALIASES the bare name to the qualified struct — but only
					# when the bare name is unique. Two same-named inner
					# classes under different outers cannot share one C
					# typedef; their references spell the qualified form.
					Conditional:if(check: { c:outerName != '' }, then: {
						local Int is bareCount: 0;
						classes:each(action: local Function(ClassInfo is oc){
							Conditional:if(check: { oc:name == c:name }, then: {
								bareCount: bareCount + 1;
							});
						});
						out: out . 'typedef struct ' . cSym . ' ' . cSym . ";\n";
						Conditional:if(check: { bareCount == 1 }, then: {
							out: out . 'typedef struct ' . cSym . ' ' . c:name . ";\n";
						});
					}, else: {
						out: out . 'typedef struct ' . cSym . ' ' . cSym . ";\n";
					});
				out: out . cSym . '* ' . cSym . "_new(void);\n";
				out: out . 'void ' . cSym . "_destroy(void* self);\n";
				Conditional:if(check: { !self:hasFieldNamed(list: c:members, name: 'init') }, then: {
					out: out . 'void ' . cSym . '_init(' . cSym . "* self);\n";
				});
			});
		});
		out: out . "\n";

		classes:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { self:policy:emitsPrototypes(c: c) && c:baseClass != self:names:enumHeader() }, then: {
				local Array of String is tps: c:typeParams;
				c:members:each(action: local Function(Member is m){
					when (m:kind) {
						is MemberKind:METHOD: {
							Conditional:if(check: { !self:policy:isTransparent(c: c) || m:body:length() > 0 }, then: {
								local String is retType: self:resolveReturnTypeForClass(t: m:memberType, typeParams: tps);
								Conditional:if(check: { retType == 'void' }, then: {
									Conditional:if(check: { m:name == ContractMethod:EVALUATE:value() || m:name == ContractMethod:ITERATION:value() }, then: {
										retType: 'bool';
									});
								});
								local Int is ovIdx: 0;
								local Int is ovHit: 0;
								c:members:each(action: local Function(Member is g){
									Conditional:if(check: { g:kind == MemberKind:METHOD && g:name == m:name }, then: {
										Conditional:if(check: { g == m }, then: {
											ovHit: ovIdx;
										});
										ovIdx: ovIdx + 1;
									});
								});
								local String is symName: self:utils:cIdent(name: c:qualifiedName()) . '_' . m:name;
								Conditional:if(check: { ovHit > 0 }, then: {
									symName: symName . '_' . (ovHit + 1) . '';
								});
								out: out . retType . ' ' . symName . '(' . self:cTypeForClass(typeName: c:qualifiedName(), typeParams: tps) . ' self';
								m:params:each(action: local Function(Parameter is p){
									out: out . ', ' . self:cTypeForClass(typeName: p:paramType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: p:name);
								});
								out: out . ");\n";
							});
						}
						else: {}
					}
				});
			});
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
			Conditional:if(check: { !self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader() }, then: {
				local Array of String is tps: c:typeParams;
				local String is cSym: self:utils:cIdent(name: c:qualifiedName());
				out: out . 'struct ' . cSym . " {\n";
				out: out . "    const char* _type_name;\n";
				out: out . "    void** _vtable;\n";
				local Array of Member is allFields: [];
				local Array of Member is outerFields: [];
				self:collectStructFieldsSplit(c: c, allClasses: classes, acc: allFields, outerAcc: outerFields, fromOuterLink: false);
				allFields:each(action: local Function(Member is m){
					out: out . '    ' . self:cTypeForClass(typeName: m:memberType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: m:name) . ";\n";
				});
				outerFields:each(action: local Function(Member is m){
					out: out . '    ' . self:cTypeForClass(typeName: m:memberType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: m:name) . ";\n";
				});
				out: out . "};\n\n";
				}, else: {
					Conditional:if(check: { c:baseClass == self:names:enumHeader() && self:allTaggedEnums:has(key: c:name) }, then: {
						out: out . self:emitTaggedEnumStruct(name: c:qualifiedName(), cls: c);
					});
			});
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
		# Metadata (the namespace declaration) is not a variant.
		local Array of Member is variants: [];
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { !(m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) }, then: {
				variants:add(item: m);
			});
		});
		out: out . 'struct ' . name . " {\n";
		out: out . '    ' . name . "_Tag _tag;\n";
		out: out . "    const char* _variant_name;\n";
		variants:each(action: local Function(Member is m){
			local String is vName: self:utils:cIdent(name: m:name);
			m:params:each(action: local Function(Parameter is p){
				out: out . '    ' . self:utils:cTypeFor(typeName: p:paramType:name) . ' ' . vName . '_' . self:utils:cIdent(name: p:name) . ";\n";
			});
		});
		out: out . "};\n\n";

		variants:each(action: local Function(Member is m){
			local String is vName: self:utils:cIdent(name: m:name);
			Conditional:if(check: { m:params:length() == 0 }, then: {
				out: out . 'static inline ' . name . '* ' . name . '_' . vName . "_ctor(void) {\n";
				out: out . '    ' . name . '* _e = (' . name . '*)spec_alloc(sizeof(' . name . "), NULL);\n";
				out: out . '    _e->_tag = ' . name . '_TAG_' . vName . ";\n";
				out: out . '    _e->_variant_name = "' . m:name . "\";\n";
				out: out . "    return _e;\n}\n\n";
			}, else: {
				out: out . 'static inline ' . name . '* ' . name . '_' . vName . '(';
				local Boolean is firstP: true;
				m:params:each(action: local Function(Parameter is p){
					Conditional:if(check: { !firstP }, then: {
 out: out . ', ';
					});
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
			});
		});

		out: out . 'static inline String ' . name . '_name(' . name . "* self) {\n";
		out: out . "    return self ? spec_string_from_chars(self->_variant_name) : spec_string_intern(\"UNKNOWN\");\n}\n\n";
		out: out . 'static inline long long ' . name . '_ordinal(' . name . "* self) {\n";
		out: out . "    return self ? (long long)self->_tag : -1;\n}\n\n";
		return out;
	}

	## True when [list] has a member with the name (scan state).
	Class of Loop is HasFieldLoop{

		replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
		];
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
			Conditional:if(check: { m:name == self:name }, then: {
				self:found: true;
				return false;
			});
			return true;
		}
	}

	## Walks a field accumulator tracking a name's index.
	Class of Loop is FieldIndexLoop{

		replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
		];
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
			Conditional:if(check: { m:name == self:name }, then: {
				self:res: self:idx;
			});
			self:idx: self:idx + 1;
			return true;
		}
	}
}
