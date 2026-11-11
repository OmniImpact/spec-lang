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
		['base', 'sys', as Buf()],
		['base', 'sys', as Conditional()],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', ClassBindings],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', MetadataField],
		['base', 'compiler', 'ast', ContractMethod],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', WellKnown],
		['base', 'compiler', 'gen', CBackendUtils],
		['base', 'compiler', 'gen', EmissionPolicy],
		['base', 'iterator'],
		['base', 'sys', as Loops()],

	];

	## Well-known names.
	local WellKnown is names: WellKnown:init();

	## The shared floor-class classification (the class-model gate).
	local ClassBindings is bindings: ClassBindings:init();

	## Backend utilities.
	local CBackendUtils is utils: CBackendUtils:init();

	## Emission transparency decisions.
	local EmissionPolicy is policy: EmissionPolicy:init();

	replace Function is init(){
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
		local Boolean is found: false;
		local Int is count: list:length();
		while(
			[Int is idx: 0],
			{ !found && idx < count },
			{
				local Member is m: list:get(index: idx);
				idx++;
				if({ m:name == name }, {
					found: true;
				});
			}
		);
		return found;
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

	## the struct-field collection with the
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
			# the base is the outer-link relation
			# when its name appears in this class's outer chain — unless the
			# base is a class-model enum: the desugared
			# variants INHERIT the base's tag fields, so they stay in acc at
			# the base's offsets (the base-cast reads them).
			local Boolean is baseIsOuter: c:outerName != '' && (c:outerName == baseName || c:outerName:contains(needle: ':' . baseName));
			allClasses:each(action: local Function(ClassInfo is cand){
				Conditional:if(check: { cand:name == baseName }, then: {
					Conditional:if(check: { self:bindings:isClassModelEnum(c: cand) }, then: {
						baseIsOuter: false;
					});
					self:collectStructFieldsSplit(c: cand, allClasses: allClasses, acc: acc, outerAcc: outerAcc, fromOuterLink: baseIsOuter);
				});
			});
		});
		c:members:each(action: local Function(Member is m){
			Conditional:match(on: m:kind, when: [
				MemberKind:FIELD: {
					# Declarative metadata (namespace/using/castable)
					# never becomes a struct field; neither do HELD members
					# — held storage is the file-scope
					# once-guard slot, not a per-instance field.
					Conditional:if(check: { m:name != MetadataField:USING:value() && m:name != MetadataField:NAMESPACE:value() &&
						m:name != MetadataField:CASTABLE:value() && !m:hasModifier(kw: Keyword:HELD) }, then: {
						local Int is existing: self:fieldIndexNamed(list: target, name: m:name);
						Conditional:if(check: { existing >= 0 }, then: {
							target:set(index: existing, item: m);
						}, else: {
							target:add(item: m);
						});
					});
				}
			]);
		});
	}

	## Finds a field's index in an accumulator by name.
	##
	## @param list: Accumulated fields.
	## @param name: Field name.
	## @return: The index, or -1.
	Function of Int is fieldIndexNamed(Array of Member is list, String is name){
		local Int is res: -1;
		local Int is count: list:length();
		while(
			[Int is idx: 0],
			{ res < 0 && idx < count },
			{
				local Member is m: list:get(index: idx);
				if({ m:name == name }, {
					res: idx;
				});
				idx++;
			}
		);
		return res;
	}

	## Emits forward declarations (typedefs, constructors, destructors) for
	## every emission-visible class.
	##
	## @param classes: Program classes.
	## @return: C source text.
	Function of String is generateForwardDeclarations(Array of ClassInfo is classes){
		local String is out: "/* Forward Declarations */\n";

			classes:each(action: local Function(ClassInfo is c){
				Conditional:if(check: { (!self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader()) || self:policy:isClassModelEnum(c: c) }, then: {
					local String is cSym: self:utils:cIdent(name: c:qualifiedName());
					local Array of String is tps: c:typeParams;
					# for nested classes the typedef
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
						Buf:bufAppendBuf(dst: out, src: 'typedef struct ' . cSym . ' ' . cSym . ";\n");
						Conditional:if(check: { bareCount == 1 }, then: {
							Buf:bufAppendBuf(dst: out, src: 'typedef struct ' . cSym . ' ' . c:name . ";\n");
						});
					}, else: {
						Buf:bufAppendBuf(dst: out, src: 'typedef struct ' . cSym . ' ' . cSym . ";\n");
					});
					# Held member prototypes : hoisted here so the
					# anon-fn helper closures (which may read held accessors)
					# precede their definitions.
					c:members:each(action: local Function(Member is m){
						Conditional:if(check: { m:kind == MemberKind:FIELD && m:hasModifier(kw: Keyword:HELD) && m:hasInit }, then: {
							Buf:bufAppendBuf(dst: out, src: self:cTypeForClass(typeName: m:memberType:name, typeParams: tps) . ' ' . cSym . '_' . self:utils:cIdent(name: m:name) . "__ensure(void);\n");
						});
					});
				Buf:bufAppendBuf(dst: out, src: cSym . '* ' . cSym . "_new(void);\n");
				Buf:bufAppendBuf(dst: out, src: 'void ' . cSym . "_destroy(void* self);\n");
				Conditional:if(check: { !self:hasFieldNamed(list: c:members, name: 'init') }, then: {
					Buf:bufAppendBuf(dst: out, src: 'void ' . cSym . '_init(' . cSym . "* self);\n");
				});
			});
		});
		Buf:bufAppendBuf(dst: out, src: "\n");

		classes:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { (self:policy:emitsPrototypes(c: c) && c:baseClass != self:names:enumHeader()) || self:policy:isClassModelEnum(c: c) }, then: {
				local Array of String is tps: c:typeParams;
				c:members:each(action: local Function(Member is m){
					Conditional:match(on: m:kind, when: [
					MemberKind:METHOD: {
						Conditional:if(check: { !self:policy:isTransparent(c: c) || m:body:length() > 0 }, then: {
							local String is retType: self:resolveReturnTypeForClass(t: m:memberType, typeParams: tps);
							Conditional:if(check: { retType == 'void' }, then: {
								Conditional:if(check: { m:name == ContractMethod:EVALUATE:value() || m:name == ContractMethod:ITERATION:value() }, then: {
									retType: 'bool';
								});
							});
							# Held functions: receiver-free
							# prototypes with the _held_ symbol infix.
							Conditional:if(check: { m:hasModifier(kw: Keyword:HELD) }, then: {
								Buf:bufAppendBuf(dst: out, src: retType . ' ' . self:utils:cIdent(name: c:qualifiedName()) . '_held_' . self:utils:cIdent(name: m:name) . '(');
								local Boolean is heldFirst: true;
								m:params:each(action: local Function(Parameter is p){
									Conditional:if(check: { heldFirst }, then: {
										Buf:bufAppendBuf(dst: out, src: self:cTypeForClass(typeName: p:paramType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: p:name));
										heldFirst: false;
									}, else: {
										Buf:bufAppendBuf(dst: out, src: ', ' . self:cTypeForClass(typeName: p:paramType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: p:name));
									});
								});
								Buf:bufAppendBuf(dst: out, src: ");\n");
								return;
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
							Buf:bufAppendBuf(dst: out, src: retType . ' ' . symName . '(' . self:cTypeForClass(typeName: c:qualifiedName(), typeParams: tps) . ' self');
							m:params:each(action: local Function(Parameter is p){
								Buf:bufAppendBuf(dst: out, src: ', ' . self:cTypeForClass(typeName: p:paramType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: p:name));
							});
							Buf:bufAppendBuf(dst: out, src: ");\n");
						});
					}
					]);
				});
			});
		});
		Buf:bufAppendBuf(dst: out, src: "\n");
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
			Conditional:if(check: { (!self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader()) || self:policy:isClassModelEnum(c: c) }, then: {
				local Array of String is tps: c:typeParams;
				local String is cSym: self:utils:cIdent(name: c:qualifiedName());
				Buf:bufAppendBuf(dst: out, src: 'struct ' . cSym . " {\n");
				Buf:bufAppendBuf(dst: out, src: "    const char* _type_name;\n");
				Buf:bufAppendBuf(dst: out, src: "    void** _vtable;\n");
				local Array of Member is allFields: [];
				local Array of Member is outerFields: [];
				self:collectStructFieldsSplit(c: c, allClasses: classes, acc: allFields, outerAcc: outerFields, fromOuterLink: false);
				allFields:each(action: local Function(Member is m){
					Buf:bufAppendBuf(dst: out, src: '    ' . self:cTypeForClass(typeName: m:memberType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: m:name) . ";\n");
				});
				outerFields:each(action: local Function(Member is m){
					Buf:bufAppendBuf(dst: out, src: '    ' . self:cTypeForClass(typeName: m:memberType:name, typeParams: tps) . ' ' . self:utils:cIdent(name: m:name) . ";\n");
				});
				Buf:bufAppendBuf(dst: out, src: "};\n\n");
				});
		});
		return out;
	}
}
