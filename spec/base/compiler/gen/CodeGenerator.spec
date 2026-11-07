#! Package base:compiler:gen
#! The C11 code generator: shared state, ownership policy, symbol lookups,
#! target-type inference, and the ownership-claim policy.
##
## The emission layers (expressions, statements, program assembly) are
## ported onto this class in G6 increments; everything they reference
## through `self` — the program registries, virtual-slot tables, method
## scope maps, and the claim/ARC policy — lives here.

Class is CodeGenerator{
	namespace: ['base', 'compiler', 'gen'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'ast', Type],
		['spec', 'base', 'compiler', 'ast', Primitive],
		['spec', 'base', 'compiler', 'ast', Expression],
		['spec', 'base', 'compiler', 'ast', ExpressionKind],
		['spec', 'base', 'compiler', 'ast', Statement],
		['spec', 'base', 'compiler', 'ast', Parameter],
		['spec', 'base', 'compiler', 'ast', Member],
		['spec', 'base', 'compiler', 'ast', MemberKind],
		['spec', 'base', 'compiler', 'ast', ClassInfo],
		['spec', 'base', 'compiler', 'ast', NamedArg],
		['spec', 'base', 'compiler', 'ast', WhenArm],
		['spec', 'base', 'compiler', 'ast', ProgramNode],
		['spec', 'base', 'compiler', WellKnown],
		['spec', 'base', 'compiler', 'gen', CBackendUtils],
		['spec', 'base', 'compiler', 'gen', EmissionPolicy],
		['spec', 'base', 'compiler', 'gen', DeclarationGenerator],
		['spec', 'base', 'compiler', 'gen', BuiltinCallGenerator],
		['spec', 'base', 'compiler', 'gen', RuntimePrelude],
		['lib', 'base', 'struct', Array],
		['lib', 'base', 'struct', Map],
		['lib', 'base', 'iterator']
	];

	## Backend utilities.
	local CBackendUtils is utils: CBackendUtils:init();

	## Declaration emitter (enums, structs, prototypes).
	local DeclarationGenerator is declGen: DeclarationGenerator:init();

	## Emission transparency decisions.
	local EmissionPolicy is policy: EmissionPolicy:init();

	## Well-known names.
	local WellKnown is names: WellKnown:init();

	## Builtin call translator (floor-class spec_* bindings).
	local BuiltinCallGenerator is builtins: BuiltinCallGenerator:init();

	## Class currently being generated.
	local String is currentClassName: '';

	## Return type name of the method currently being generated.
	local String is currentMethodReturnType: '';

	## Name of the method currently being generated.
	local String is currentMethodName: '';

	## Virtual method slots: method name -> decimal slot index.
	local Map of String to String is methodSlots: Map:init();

	## Method names declared by more than one class (dispatch virtually).
	local Map of String to String is overriddenMethods: Map:init();

	## Total virtual slot count.
	local Int is methodSlotCount: 0;

	## Slot index -> method name (parallel to [methodSlots]).
	local Array of String is slotNames: [];

	## Classes declaring an explicit toString.
	local Map of String to String is classesWithToString: Map:init();

	## Local variables in the current method scope: name -> type name.
	local Map of String to String is localVars: Map:init();

	## Struct fields of the current class: name -> type name.
	local Map of String to String is fieldTypes: Map:init();

	## All classes in the program (nested included).
	local Array of ClassInfo is programClasses: [];

	## Registry of class names.
	local Map of String to String is allClassNames: Map:init();

	## Registry of enum type names.
	local Map of String to String is allEnumNames: Map:init();

	## Enum variant name -> parent enum name.
	local Map of String to String is allEnumVariants: Map:init();

	## String-backed enum names.
	local Map of String to String is allStringBackedEnums: Map:init();

	## Tagged-union enum names.
	local Map of String to String is allTaggedEnums: Map:init();

	## True while generating inside a method body.
	local Boolean is inMethod: false;

	## Forward-declaration buffer for anonymous static functions.
	local String is helperFunctions: '';

	## Unique-name counter for anonymous functions.
	local Int is anonCounter: 0;

	## Active inline-return variable (closure inlining).
	local String is inlineReturnVar: '';

	## Active inline-return label (closure inlining).
	local String is inlineReturnLabel: '';

	## Locals declared in the current scope (SPEC_AUTO injection).
	local Map of String to String is localScopeVars: Map:init();

	## Parameters of the method being generated: names are borrow targets —
	## assignment to them must not release the caller's argument.
	local Map of String to String is currentParams: Map:init();

	## True when the current inline-return target is ARC-managed
	## (reassignment goes through spec_assign).
	local Boolean is inlineReturnArc: false;

	## True in read positions (arguments, conditions, operands): claim-
	## yielding subexpressions go to the runtime claim pool. False in
	## consumption positions (initializers, returns, container stores).
	local Boolean is argMode: true;

	## GC mode: '' (default ARC) or 'boehm'.
	local String is gcMode: '';

	## Declared-type context for the container literal being generated
	## (selects spec_array_new_string vs _object vs _bytebuffer).
	local String is containerHint: '';

	replace Function is init(){
		self:methodSlots: Map:init();
		self:overriddenMethods: Map:init();
		self:classesWithToString: Map:init();
		self:localVars: Map:init();
		self:fieldTypes: Map:init();
		self:programClasses: [];
		self:allClassNames: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();
		self:allTaggedEnums: Map:init();
		self:inMethod: false;
		self:helperFunctions: '';
		self:anonCounter: 0;
		self:inlineReturnVar: '';
		self:inlineReturnLabel: '';
		self:localScopeVars: Map:init();
		self:gcMode: '';
	}

	## Sets the GC mode and informs the prelude emitter.
	##
	## @param mode: '' (ARC) or 'boehm'.
	Function is setGcMode(String is mode){
		self:gcMode: mode;
	}

	## Sets the claim-pool mode: true in read positions, false in
	## consumption positions (initializers, container stores).
	##
	## @param m: The new mode.
	Function is setArgMode(Boolean is m){
		self:argMode: m;
	}

	## Sets the declared type for the container literal being generated.
	##
	## @param t: The declared container type.
	Function is setContainerHint(String is t){
		self:containerHint: t;
	}


	## Emits the C runtime prelude (static heredoc text).
	##
	## @return: The C runtime source.
	Function of String is generatePrelude(){
		local RuntimePrelude is rp: RuntimePrelude:init();
		return rp:emitRuntime();
	}

	## Assigns virtual method slots in deterministic first-seen order.
	## Names declared by two or more classes dispatch virtually; single-
	## declaration names dispatch directly.
	##
	## @param classes: The flattened program classes.
	Function is assignVirtualSlots(Array of ClassInfo is classes){
		self:methodSlots: Map:init();
		self:overriddenMethods: Map:init();
		self:methodSlotCount: 0;
		self:slotNames: [];
		classes:each(action: local Function(ClassInfo is c){
			if (!self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader()) {
				c:members:each(action: local Function(Member is m){
					if (m:kind == MemberKind:METHOD) {
						if (self:methodSlots:has(key: m:name)) {
							self:overriddenMethods:set(key: m:name, value: 'true');
						} else {
							self:methodSlots:set(key: m:name, value: '' . self:methodSlotCount);
							self:slotNames:add(item: m:name);
							self:methodSlotCount: self:methodSlotCount + 1;
						}
					}
				});
			}
		});
	}

	## Records the program registries from the checker's flatten pass.
	##
	## @param classes: The flattened program classes.
	Function is registerProgram(Array of ClassInfo is classes){
		# Flatten nested classes into the registries: the driver hands over
		# the loaded set, and nested classes are first-class citizens for
		# lookups (static calls on them dispatch by name).
		local Array of ClassInfo is flattened: [];
		classes:each(action: local Function(ClassInfo is c){
			self:collectClasses(c: c, acc: flattened);
		});
		self:programClasses: flattened;
		self:allClassNames: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();
		self:allTaggedEnums: Map:init();
		flattened:each(action: local Function(ClassInfo is c){
			self:allClassNames:set(key: c:name, value: 'true');
			if (c:baseClass == self:names:enumHeader()) {
				self:allEnumNames:set(key: c:name, value: 'true');
				c:members:each(action: local Function(Member is m){
					self:allEnumVariants:set(key: m:name, value: c:name);
					if (m:memberType:name == Primitive:STRING:value()) {
						self:allStringBackedEnums:set(key: c:name, value: 'true');
					}
				});
			}
		});
	}

	## True when the type name is ARC-managed (ownership transfers at
	## assignments and calls).
	##
	## @param typeName: Type name.
	## @return: true when ARC-managed.
	Function of Boolean is isArcType(String is typeName){
		if (typeName == '') {
			return false;
		}
		# String is primitive-spelled but ARC-managed; test it first.
		if (typeName == 'String') {
			return true;
		}
		if (self:isPrimitiveName(t: typeName)) {
			return false;
		}
		# Base-name extraction goes through a local: parameters are borrows,
		# and reassigning one would release the caller's argument.
		local String is baseName: typeName;
		if (baseName:contains(needle: ':')) {
			local Array of String is parts: baseName:split(delimiter: ':');
			baseName: parts:get(index: 0);
		}
		if (self:allEnumNames:has(key: baseName) && !self:allTaggedEnums:has(key: baseName)) {
			return false;
		}
		if (self:allTaggedEnums:has(key: baseName)) {
			return true;
		}
		if (baseName:startsWith(prefix: 'Array') || baseName:startsWith(prefix: 'Map') || baseName:startsWith(prefix: 'List') || baseName:startsWith(prefix: 'Function') || baseName == 'LoopControl') {
			return true;
		}
		if (self:allClassNames:has(key: baseName)) {
			return true;
		}
		return false;
	}

	## True when the name is a primitive spelling (canonical or alias).
	##
	## @param t: Type name.
	## @return: true per the [Primitive] vocabulary.
	Function of Boolean is isPrimitiveName(String is t){
		return Primitive:of(t) != Primitive:NONE;
	}

	## Classifies a container's element ownership from a canonical container
	## type string: "object" (ARC-managed, String included), "byte" (compact
	## byte buffer), or "none" (primitives, Any, unknown — never owned).
	##
	## @param containerType: Canonical container type name.
	## @return: The ownership kind.
	Function of String is containerElemKind(String is containerType){
		local String is elem: self:elemOfType(t: containerType);
		if (elem == '') {
			return 'none';
		}
		if (elem == Primitive:ANY:value()) {
			return 'none';
		}
		if (elem == 'Byte') {
			return 'byte';
		}
		if (self:isArcType(typeName: elem)) {
			return 'object';
		}
		return 'none';
	}

	## Extracts a container's element/value type from either spelling
	## ('Array of X' / 'Array:X', 'Map of K to V' / 'Map:K:V').
	##
	## @param t: Container type name.
	## @return: The element/value type name, or ''.
	Function of String is elemOfType(String is t){
		if (t:startsWith(prefix: 'Array of ')) {
			return t:substring(start: 9, end: t:length());
		}
		if (t:startsWith(prefix: 'Array:')) {
			return t:substring(start: 6, end: t:length());
		}
		if (t:startsWith(prefix: 'List of ')) {
			return t:substring(start: 8, end: t:length());
		}
		if (t:startsWith(prefix: 'List:')) {
			return t:substring(start: 5, end: t:length());
		}
		if (t:startsWith(prefix: 'Map of ')) {
			local String is rest: t:substring(start: 7, end: t:length());
			local Int is toIdx: rest:indexOf(search: ' to ', default: -1);
			if (toIdx >= 0) {
				return rest:substring(start: toIdx + 4, end: rest:length());
			}
			return '';
		}
		if (t:startsWith(prefix: 'Map:')) {
			local String is rest: t:substring(start: 4, end: t:length());
			local Int is colonIdx: rest:indexOf(search: ':', default: -1);
			if (colonIdx >= 0) {
				return rest:substring(start: colonIdx + 1, end: rest:length());
			}
			return '';
		}
		return '';
	}

	## True when a container's element/value is ARC-managed.
	##
	## @param containerType: Canonical container type name.
	## @return: true when element-owned.
	Function of Boolean is containerElemIsArc(String is containerType){
		local String is k: self:containerElemKind(containerType: containerType);
		return k == 'object';
	}

	## Generates the per-type constructor call for a typed assignment:
	## primitives are casts, String wraps into a managed value, containers
	## and ARC types retain unless the producer transferred a claim.
	##
	## @param typeName: The assignment's declared type name.
	## @param valueC: The generated value expression.
	## @param expr: The value expression node.
	## @param cType: The C type of the assignment.
	## @return: The constructor C expression.
	Function of String is generateTypedConstructor(String is typeName, String is valueC, String is cType, Boolean is claims){
		if (typeName == 'String') {
			if (claims) {
				return valueC;
			}
			return 'spec_construct_string(' . valueC . ')';
		}
		if (typeName == 'Byte') {
			return 'spec_construct_byte((long long)(' . valueC . '))';
		}
		if (typeName == Primitive:INT:value() || typeName == 'Float' || typeName == 'Boolean') {
			return valueC;
		}
		if (self:isArcType(typeName: typeName)) {
			if (claims) {
				return '(' . cType . ')((' . valueC . '))';
			}
			return '(' . cType . ')spec_retain((void*)(' . valueC . '))';
		}
		return valueC;
	}

	## True when the type name is one of the two void spellings.
	##
	## @param t: Type name.
	## @return: true for 'void' and 'Void'.
	Function of Boolean is isVoidType(String is t){
		return t == self:names:voidName() || t == self:names:voidMemberType();
	}

	## Maps a type name to its C type, grounding the enclosing class's
	## generic parameters and resolving enums/containers.
	##
	## @param typeName: Type name.
	## @return: C type string.
	Function of String is cTypeFor(String is typeName){
		local ClassInfo is curCls: self:findClass(name: self:currentClassName);
		if (curCls:typeParams:indexOf(search: typeName, default: -1) >= 0) {
			return 'void*';
		}
		local String is containerC: self:utils:cTypeFor(typeName: typeName);
		if (containerC:startsWith(prefix: 'Spec')) {
			return containerC;
		}
		local String is base: typeName;
		if (base:contains(needle: ':')) {
			local Array of String is parts: base:split(delimiter: ':');
			base: parts:get(index: 0);
		}
		if (self:allTaggedEnums:has(key: base)) {
			return base . '*';
		}
		if (self:allEnumNames:has(key: base)) {
			return base;
		}
		return containerC;
	}

	## Resolves a method's return type to its C type: enum returns pass by
	## value (the registry-aware cTypeFor), Function types unwrap to their
	## return type's C type.
	##
	## @param t: Type descriptor.
	## @return: C type string.
	Function of String is resolveReturnType(Type is t){
		if (Primitive:of(t:name) == Primitive:FUNCTION) {
			if (t:params:length() > 0) {
				local Type is ret: t:params:get(index: 0);
				return self:cTypeFor(typeName: ret:name);
			}
			return 'void';
		}
		return self:cTypeFor(typeName: t:name);
	}

	## Formats a [Type] descriptor into the internal colon form.
	##
	## @param t: Type descriptor.
	## @return: Type name string.
	Function of String is formatTypeString(Type is t){
		local String is baseName: t:name;
		if (Primitive:of(baseName) == Primitive:FUNCTION) {
			if (t:params:length() > 0) {
				local Type is ret: t:params:get(index: 0);
				return self:formatTypeString(t: ret);
			}
			return 'void';
		}
		if (t:params:length() == 1) {
			local Type is p0: t:params:get(index: 0);
			return baseName . ':' . self:formatTypeString(t: p0);
		}
		if (t:params:length() >= 2) {
			local Type is p0: t:params:get(index: 0);
			local Type is p1: t:params:get(index: 1);
			return baseName . ':' . self:formatTypeString(t: p0) . ':' . self:formatTypeString(t: p1);
		}
		return baseName;
	}

	## Substitutes a class's generic parameters in a member type name.
	##
	## @param rawType: Declared type name.
	## @param cls: The declaring class.
	## @param typeArgs: The concrete type arguments.
	## @return: The substituted type name.
	Function of String is substituteTypeParam(String is rawType, ClassInfo is cls, Array of String is typeArgs){
		local Array of String is tps: cls:typeParams;
		if (tps:length() == 0 || typeArgs:length() == 0) {
			return rawType;
		}
		local Int is idx: tps:indexOf(search: rawType, default: -1);
		if (idx >= 0 && idx < typeArgs:length()) {
			return typeArgs:get(index: idx);
		}
		if (rawType:startsWith(prefix: 'Array:') && rawType:length() > 6) {
			local String is elem: rawType:substring(start: 6, end: rawType:length());
			local Int is eIdx: tps:indexOf(search: elem, default: -1);
			if (eIdx >= 0 && eIdx < typeArgs:length()) {
				return 'Array:' . typeArgs:get(index: eIdx);
			}
		}
		return rawType;
	}

	## Finds a class descriptor by name.
	##
	## @param name: Target class name.
	## @return: The descriptor, or an unnamed one when absent.
	Function of ClassInfo is findClass(String is name){
		local GenClassSearchLoop is s: GenClassSearchLoop:init(list: self:programClasses, target: name);
		While:run(loop: s);
		if (s:found) {
			return s:res;
		}
		return ClassInfo:init(name: '', baseClass: '', members: []);
	}

	## Looks up a field's static type on a class and its ancestors.
	##
	## @param className: Starting class name.
	## @param fieldName: Field name.
	## @return: The field type name, or ''.
	Function of String is lookupFieldType(String is className, String is fieldName){
		if (className == '' || className == Primitive:ANY:value()) {
			return '';
		}
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:name == '') {
			return '';
		}
		local FieldMemberLoop is fl: FieldMemberLoop:init(members: cls:members, fieldName: fieldName);
		While:run(loop: fl);
		if (fl:found) {
			local String is rawT: self:formatTypeString(t: fl:res:memberType);
			return self:substituteTypeParam(rawType: rawT, cls: cls, typeArgs: typeArgs);
		}
		local String is inherited: '';
		cls:baseClasses:each(action: local Function(String is baseName){
			if (inherited == '') {
				inherited: self:lookupFieldType(className: baseName, fieldName: fieldName);
			}
		});
		return inherited;
	}

	## Looks up a method's return type on a class and its ancestors.
	##
	## @param className: Starting class name.
	## @param methodName: Method name.
	## @return: The return type name, or ''.
	Function of String is lookupMethodReturnType(String is className, String is methodName){
		if (className == '' || className == Primitive:ANY:value()) {
			return '';
		}
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
		if (methodName == 'init' && self:allClassNames:has(key: baseClassName) && !self:allEnumNames:has(key: baseClassName)) {
			return className;
		}
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:name == '') {
			return '';
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:members, methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			local String is rawT: self:formatTypeString(t: ml:res:memberType);
			return self:substituteTypeParam(rawType: rawT, cls: cls, typeArgs: typeArgs);
		}
		local String is inherited: '';
		cls:baseClasses:each(action: local Function(String is baseName){
			if (inherited == '') {
				inherited: self:lookupMethodReturnType(className: baseName, methodName: methodName);
			}
		});
		return inherited;
	}

	## Looks up an enum variant member.
	##
	## @param enumName: Parent enum name.
	## @param variantName: Variant name.
	## @return: The variant member, or an empty-named one.
	Function of Member is lookupEnumVariant(String is enumName, String is variantName){
		local ClassInfo is cls: self:findClass(name: enumName);
		local FieldMemberLoop is fl: FieldMemberLoop:init(members: cls:members, fieldName: variantName);
		While:run(loop: fl);
		if (fl:found) {
			return fl:res;
		}
		return Member:init(kind: MemberKind:FIELD);
	}

	## Finds the class whose declaration implements a method for a receiver
	## of [className] (ancestor overrides).
	##
	## @param className: Receiver class name.
	## @param methodName: Method name.
	## @param paramCount: Expected parameter count (-1 = any).
	## @return: The implementing class name, or ''.
	Function of String is findMethodImplementingClass(String is className, String is methodName, Int is paramCount){
		if (className == '' || className == Primitive:ANY:value()) {
			return '';
		}
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:name == '') {
			return '';
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:members, methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			if (paramCount < 0 || ml:res:params:length() == paramCount) {
				return baseClassName;
			}
		}
		local String is inherited: '';
		cls:baseClasses:each(action: local Function(String is baseName){
			if (inherited == '') {
				inherited: self:findMethodImplementingClass(className: baseName, methodName: methodName, paramCount: paramCount);
			}
		});
		return inherited;
	}

	## Looks up a method member on a class or its ancestors.
	##
	## @param className: Starting class name.
	## @param methodName: Method name.
	## @return: The member, or an empty-named one.
	Function of Member is lookupMethodMember(String is className, String is methodName){
		if (className == '' || className == Primitive:ANY:value()) {
			return Member:init(kind: MemberKind:FIELD);
		}
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:name == '') {
			return Member:init(kind: MemberKind:FIELD);
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:members, methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			return ml:res;
		}
		local Member is inherited: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			if (inherited:name == '') {
				inherited: self:lookupMethodMember(className: baseName, methodName: methodName);
			}
		});
		return inherited;
	}

	## True when [subName] inherits from [baseName] (transitively).
	##
	## @param subName: Candidate subtype.
	## @param baseName: Candidate base type.
	## @return: Subclass relationship.
	Function of Boolean is isSubclassOf(String is subName, String is baseName){
		if (subName == '' || baseName == '') {
			return false;
		}
		if (subName == baseName) {
			return true;
		}
		local ClassInfo is subCls: self:findClass(name: subName);
		if (subCls:name == '') {
			return false;
		}
		local Boolean is matched: false;
		subCls:baseClasses:each(action: local Function(String is pName){
			if (pName == baseName || self:isSubclassOf(subName: pName, baseName: baseName)) {
				matched: true;
			}
		});
		return matched;
	}

	## Infers the static type name of an expression for the BACKEND:
	## locals and fields from scope maps, paths chained through field
	## types, calls through method return types, literals directly.
	##
	## @param expr: The expression node.
	## @return: The inferred type name ('' when unknown).
	Function of String is inferTargetType(Expression is expr){
		local ExpressionKind is kind: expr:kind;
		if (kind == ExpressionKind:IDENT) {
			local String is name: expr:stringValue;
			if (name == self:names:selfIdent()) {
				return self:currentClassName;
			}
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
		if (kind == ExpressionKind:PATH) {
			local Array of String is segs: expr:pathSegments;
			if (segs:length() == 0) {
				return '';
			}
			local String is root: segs:get(index: 0);
			local String is rootType: '';
			if (root == self:names:selfIdent()) {
				rootType: self:currentClassName;
			} else if (self:localVars:has(key: root)) {
				rootType: self:localVars:getString(key: root, default: '');
			} else if (self:fieldTypes:has(key: root)) {
				rootType: self:fieldTypes:getString(key: root, default: '');
			} else if (self:allEnumNames:has(key: root)) {
				return root;
			} else if (self:allClassNames:has(key: root)) {
				return root;
			}
			if (rootType == '') {
				return rootType;
			}
			local Int is idx: 1;
			While:condition(
				evaluate: local Function of Boolean(){
					return rootType != '' && idx < segs:length();
				},
				iteration: local Function of Boolean(){
					rootType: self:lookupFieldType(className: rootType, fieldName: segs:get(index: idx));
					idx: idx + 1;
					return true;
				}
			);
			return rootType;
		}
		if (kind == ExpressionKind:CALL) {
			local String is targetType: self:inferTargetType(expr: expr:methodTarget);
			if (targetType == self:names:selfIdent() || targetType == '') {
				targetType: self:currentClassName;
			}
			if (targetType:contains(needle: ':')) {
				local Array of String is parts: targetType:split(delimiter: ':');
				targetType: parts:get(index: 0);
			}
			# Container element extraction: Array of X:get/pop/removeAt -> X.
			if (targetType:startsWith(prefix: 'Array:') && (expr:methodName == 'get' || expr:methodName == 'pop' || expr:methodName == 'removeAt')) {
				return targetType:substring(start: 6, end: targetType:length());
			}
			# Enum contract methods have fixed return types.
			if (self:allEnumNames:has(key: targetType)) {
				if (expr:methodName == 'name') { return 'String'; }
				if (expr:methodName == 'ordinal') { return Primitive:INT:value(); }
				if (expr:methodName == 'values') { return 'Array:' . targetType; }
				if (expr:methodName == 'value') {
					if (self:allStringBackedEnums:has(key: targetType)) {
						return 'String';
					}
					return Primitive:INT:value();
				}
			}
			local String is ret: self:lookupMethodReturnType(className: targetType, methodName: expr:methodName);
			if (ret == '' || self:isVoidType(t: ret)) {
				return '';
			}
			return ret;
		}
		if (kind == ExpressionKind:FIELD_ACCESS) {
			local String is leftT: self:inferTargetType(expr: expr:leftExpr);
			if (leftT == '' || leftT == Primitive:ANY:value()) {
				return '';
			}
			return self:lookupFieldType(className: leftT, fieldName: expr:stringValue);
		}
		if (kind == ExpressionKind:STRING) {
			return 'String';
		}
		if (kind == ExpressionKind:NUMBER) {
			return Primitive:INT:value();
		}
		if (kind == ExpressionKind:FLOAT) {
			return 'Float';
		}
		if (kind == ExpressionKind:BOOL) {
			return 'Boolean';
		}
		if (kind == ExpressionKind:ARRAY) {
			return 'Array';
		}
		if (kind == ExpressionKind:MAP) {
			return 'Map';
		}
		if (kind == ExpressionKind:BINARY && expr:binaryOp == '.') {
			# String concatenation chains produce a String.
			return 'String';
		}
		if (kind == ExpressionKind:CAST) {
			return expr:castTarget;
		}
		if (kind == ExpressionKind:ANON_FN) {
			local String is anonRet: expr:anonReturnType:name;
			if (anonRet != '' && !self:isVoidType(t: anonRet)) {
				return 'Function:' . self:formatTypeString(t: expr:anonReturnType);
			}
			return 'Function';
		}
		return '';
	}

	## Determines whether evaluating [expr] yields a transferred ownership
	## claim: constructors, user-class method calls, concat chains, ARC-typed
	## literals, and fresh-returning floor methods hand one claim to the
	## caller. Borrowing expressions (locals, fields, container getters,
	## primitives) do not.
	##
	## @param expr: The expression node.
	## @return: true when ownership transfers.
	Function of Boolean is yieldsClaim(Expression is expr){
		local ExpressionKind is kind: expr:kind;
		if (kind == ExpressionKind:ARRAY || kind == ExpressionKind:MAP) {
			return true;
		}
		if (kind == ExpressionKind:BINARY) {
			return expr:binaryOp == '.';
		}
		if (kind == ExpressionKind:CALL) {
			local String is resT: self:inferTargetType(expr: expr);
			if (!self:isArcType(typeName: resT)) {
				return false;
			}
			local String is targetT0: self:inferTargetType(expr: expr:methodTarget);
			local String is targetT: targetT0;
			if (targetT:contains(needle: ':')) {
				local Array of String is parts0: targetT:split(delimiter: ':');
				targetT: parts0:get(index: 0);
			}
			if (self:allClassNames:has(key: targetT) && !self:allEnumNames:has(key: targetT)) {
				local String is mRet: self:lookupMethodReturnType(className: targetT, methodName: expr:methodName);
				if (mRet == '' || self:isVoidType(t: mRet)) {
					return false;
				}
				if (mRet == targetT && expr:methodName != 'init' && expr:methodName != targetT && !self:policy:isTransparent(c: self:findClass(name: targetT))) {
					return false;
				}
			}
			if (self:policy:isTransparent(c: self:findClass(name: targetT)) || targetT == 'List' || targetT == 'String') {
				if (expr:methodName == 'get') {
					return targetT:startsWith(prefix: 'Map');
				}
				when (expr:methodName) {
					is 'pop', 'removeAt', 'substring', 'trim', 'replace', 'join', 'split', 'lines', 'keys',
					'getString', 'read', 'fromCharCode', 'toString', 'map', 'filter', 'slice', 'charAt': {
						return true;
					}
					else: {
						return false;
					}
				}
			}
			return true;
		}
		return false;
	}

	## True when the expression is a constructor call whose produced value
	## is provably fresh (the creator abandons the initial ref).
	##
	## @param expr: The expression node.
	## @return: true when fresh.
	Function of Boolean is isFreshConstructorCall(Expression is expr){
		if (expr:kind != ExpressionKind:CALL) {
			return false;
		}
		local String is m: expr:methodName;
		if (!(m == 'init' || m == 'new')) {
			return false;
		}
		local String is targetT: self:inferTargetType(expr: expr:methodTarget);
		return self:allClassNames:has(key: targetT);
	}

	## Decides whether an expression's value is a Spec String (SpecBuf*):
	## inference first (String-typed calls, fields, concat chains), then the
	## literal kinds. Equality on such values must compare CONTENT, not
	## pointers.
	##
	## @param expr: The expression node.
	## @param exprC: Its generated C.
	## @return: true when the C is already a Spec String.
	Function of Boolean is isStringExpr(Expression is expr, String is exprC){
		local String is resolved: self:inferTargetType(expr: expr);
		if (resolved == 'String' || resolved == 'string') {
			return true;
		}
		local ExpressionKind is kind: expr:kind;
		if (kind == ExpressionKind:STRING) {
			return true;
		}
		if (kind == ExpressionKind:BINARY && expr:binaryOp == '.') {
			return true;
		}
		return false;
	}

	## Wraps an expression's C into a String (SpecBuf*) for contexts that
	## need one (concat, Output, error messages): string literals intern,
	## Strings pass through, everything else converts via the value's type.
	##
	## @param expr: The expression node.
	## @param exprC: Its generated C.
	## @return: C producing a String.
	Function of String is wrapToString(Expression is expr, String is exprC){
		local ExpressionKind is kind: expr:kind;
		if (kind == ExpressionKind:STRING) {
			return 'spec_string_intern("' . self:utils:escapeString(s: expr:stringValue) . '")';
		}
		if (kind == ExpressionKind:NUMBER) {
			return 'spec_to_string_int(' . exprC . ')';
		}
		if (kind == ExpressionKind:FLOAT) {
			return 'spec_to_string_float(' . exprC . ')';
		}
		if (kind == ExpressionKind:BOOL) {
			return 'spec_to_string_bool(' . exprC . ')';
		}
		if (kind == ExpressionKind:BINARY) {
			local String is op: expr:binaryOp;
			if (op == '+' || op == '-' || op == '*' || op == '/' || op == '%' || op == '&' || op == '|' || op == '^' || op == '<<' || op == '>>') {
				return 'spec_to_string_int(' . exprC . ')';
			}
			if (op == '==' || op == '!=' || op == '<' || op == '<=' || op == '>' || op == '>=' || op == '&&' || op == '||') {
				return 'spec_to_string_bool(' . exprC . ')';
			}
			return exprC;
		}
		if (kind == ExpressionKind:UNARY) {
			if (expr:unaryOp == '!') {
				return 'spec_to_string_bool(' . exprC . ')';
			}
			return 'spec_to_string_int(' . exprC . ')';
		}
		local String is t: self:inferTargetType(expr: expr);
		if (t == 'String') {
			return exprC;
		}
		if (t == Primitive:INT:value()) {
			return 'spec_to_string_int(' . exprC . ')';
		}
		if (t == 'Float') {
			return 'spec_to_string_float(' . exprC . ')';
		}
		if (t == 'Boolean') {
			return 'spec_to_string_bool(' . exprC . ')';
		}
		if (t != '' && t != Primitive:ANY:value() && self:allClassNames:has(key: t) && !self:policy:isTransparent(c: self:findClass(name: t))) {
			return 'spec_type_name(' . exprC . ') /* wrap:' . t . ' */';
		}
		return exprC;
	}

	## Safely extracts a call argument's value expression.
	##
	## @param expr: The CALL expression.
	## @param index: The argument index.
	## @return: The value expression.
	Function of Expression is argValue(Expression is expr, Int is index){
		local NamedArg is arg: expr:methodArgs:get(index: index);
		return arg:value;
	}

	## Generates C for an expression, wrapping claim-yielding results
	## for read positions (the claim pool takes ownership).
	##
	## @param expr: The expression node.
	## @return: C expression string.
	Function of String is generateExpression(Expression is expr){
		local String is c: self:generateExpressionInner(expr: expr);
		local ExpressionKind is kind: expr:kind;
		local Boolean is claim: false;
		if (kind == ExpressionKind:CALL) {
			claim: self:yieldsClaim(expr: expr);
		} else if (kind == ExpressionKind:BINARY) {
			claim: expr:binaryOp == '.';
		} else if (kind == ExpressionKind:ARRAY || kind == ExpressionKind:MAP) {
			claim: true;
		} else if (kind == ExpressionKind:INDEX) {
			local String is tgt: self:inferTargetType(expr: expr:leftExpr);
			claim: (tgt:startsWith(prefix: 'Map') && self:inferTargetType(expr: expr) == 'String');
		}
		if (claim) {
			if (self:argMode) {
				local String is resT: self:inferTargetType(expr: expr);
				local String is resC: self:cTypeFor(typeName: resT);
				return '((' . resC . ')spec_claim_pool((void*)(' . c . ')))';
			}
		}
		return c;
	}

	## Generates C for an expression without the claim wrapper.
	##
	## @param expr: The expression node.
	## @return: C expression string.
	Function of String is generateExpressionInner(Expression is expr){
		local ExpressionKind is kind: expr:kind;

		when (kind) {
			is ExpressionKind:ARRAY: {
				return self:emitArrayLiteral(expr: expr);
			}
			is ExpressionKind:MAP: {
				return self:emitMapLiteral(expr: expr);
			}
			is ExpressionKind:STRING: {
				# Raw strings collapse into STRING upstream; one intern path.
				return 'spec_string_intern("' . self:utils:escapeString(s: expr:stringValue) . '")';
			}
			is ExpressionKind:NUMBER: {
				if (expr:stringValue != '') {
					return expr:stringValue;
				}
				return '0';
			}
			is ExpressionKind:FLOAT: {
				if (expr:stringValue != '') {
					return expr:stringValue;
				}
				return '0.0';
			}
			is ExpressionKind:BOOL: {
				return if (expr:boolValue) 'true' else 'false';
			}
			is ExpressionKind:IDENT: {
				return self:emitIdent(expr: expr);
			}
			is ExpressionKind:PATH: {
				return self:emitPath(expr: expr);
			}
			is ExpressionKind:BINARY: {
				return self:emitBinary(expr: expr);
			}
			is ExpressionKind:INDEX: {
				return self:emitIndex(expr: expr);
			}
			is ExpressionKind:CAST: {
				return self:emitCast(expr: expr);
			}
			is ExpressionKind:UNARY: {
				local String is innerC: self:generateExpression(expr: expr:unaryExpr);
				return '(' . expr:unaryOp . '(' . innerC . '))';
			}
			is ExpressionKind:CALL: {
				return self:emitCall(expr: expr);
			}
			is ExpressionKind:FIELD_ACCESS: {
				local String is leftC: self:generateExpression(expr: expr:leftExpr);
				return '(' . leftC . ')->' . self:utils:cIdent(name: expr:stringValue);
			}
			is ExpressionKind:IF_ELSE: {
				local String is condC: self:generateExpression(expr: expr:condExpr);
				local String is thenC: self:generateExpression(expr: expr:thenExpr);
				local String is elseC: self:generateExpression(expr: expr:elseExpr);
				return '((' . condC . ') ? (' . thenC . ') : (' . elseC . '))';
			}
			is ExpressionKind:WHEN: {
				return self:emitWhenExpression(expr: expr);
			}
			is ExpressionKind:ANON_FN: {
				return self:emitAnonFn(expr: expr);
			}
			else: {
				return '0';
			}
		}
	}

	## Emits an array/list literal from the container hint or the first
	## element's inferred type.
	##
	## @param expr: The ARRAY expression.
	## @return: C compound-literal allocation.
	Function of String is emitArrayLiteral(Expression is expr){
		local Boolean is listHint: self:containerHint:startsWith(prefix: 'List');
		local String is addFn: if (listHint) 'spec_vec_push' else 'spec_array_add';
		local String is newCall: 'spec_array_new()';
		if (self:containerHint != '') {
			local String is hintKind: self:containerElemKind(containerType: self:containerHint);
			if (hintKind == 'byte') {
				newCall: 'spec_bytebuffer_new()';
			} else if (hintKind == 'object') {
				newCall: if (listHint) 'spec_vec_new_object()' else 'spec_array_new_object()';
			} else if (hintKind == 'string') {
				newCall: if (listHint) 'spec_vec_new_string()' else 'spec_array_new_string()';
			} else if (listHint) {
				newCall: 'spec_vec_new()';
			}
			self:containerHint: '';
		} else if (expr:arrayItems:length() > 0) {
			local String is elemT: self:inferTargetType(expr: expr:arrayItems:get(index: 0));
			if (self:isArcType(typeName: elemT)) {
				newCall: 'spec_array_new_object()';
			} else if (elemT == 'String') {
				newCall: 'spec_array_new_string()';
			}
		}
		local String is arrCType: if (listHint) 'SpecVec*' else 'SpecArray*';
		local String is res: '({ ' . arrCType . ' _arr = ' . newCall . ';';
		local Boolean is savedArg: self:argMode;
		self:argMode: false;
		expr:arrayItems:each(action: local Function(Expression is item){
			local String is itemC: self:generateExpression(expr: item);
			res: res . ' ' . addFn . '(_arr, (void*)(' . itemC . '));';
		});
		self:argMode: savedArg;
		res: res . ' _arr; })';
		return res;
	}

	## Emits a map literal from the container hint or the first value's
	## inferred type.
	##
	## @param expr: The MAP expression.
	## @return: C compound-literal allocation.
	Function of String is emitMapLiteral(Expression is expr){
		local String is newCall: 'spec_map_new()';
		if (self:containerHint != '') {
			if (self:containerElemIsArc(containerType: self:containerHint)) {
				newCall: 'spec_map_new_object()';
			}
			self:containerHint: '';
		} else if (expr:mapValues:length() > 0) {
			local String is valT: self:inferTargetType(expr: expr:mapValues:get(index: 0));
			if (self:isArcType(typeName: valT)) {
				newCall: 'spec_map_new_object()';
			}
		}
		local String is res: '({ SpecMap* _map = ' . newCall . ';';
		local Int is idx: 0;
		local Boolean is savedArgM: self:argMode;
		self:argMode: false;
		expr:mapKeys:each(action: local Function(Expression is kExpr){
			local Expression is vExpr: expr:mapValues:get(index: idx);
			local String is kC: self:generateExpression(expr: kExpr);
			local String is vC: self:generateExpression(expr: vExpr);
			if (self:isStringExpr(expr: vExpr, exprC: vC)) {
				res: res . ' spec_map_set(_map, ' . kC . ', ' . vC . ');';
			} else {
				local String is setFn: if (self:yieldsClaim(expr: vExpr)) 'spec_map_set_any_transfer' else 'spec_map_set_any';
				res: res . ' ' . setFn . '(_map, ' . kC . ', (void*)(intptr_t)(' . vC . '));';
			}
			idx: idx + 1;
		});
		self:argMode: savedArgM;
		res: res . ' _map; })';
		return res;
	}

	## Emits an identifier reference: self, enum variants, locals, fields.
	##
	## @param expr: The IDENT expression.
	## @return: C identifier expression.
	Function of String is emitIdent(Expression is expr){
		local String is name: expr:stringValue;
		if (name == self:names:selfIdent() || name == 'true' || name == 'false') {
			return name;
		}
		if (self:allEnumVariants:has(key: name)) {
			local String is enumName: self:allEnumVariants:getString(key: name, default: '');
			if (self:allTaggedEnums:has(key: enumName)) {
				return enumName . '_' . self:utils:cIdent(name: name) . '_ctor()';
			}
			return enumName . '_' . self:utils:cIdent(name: name);
		}
		if (self:localVars:has(key: name)) {
			return self:utils:cIdent(name: name);
		}
		if (self:fieldTypes:has(key: name)) {
			return 'self->' . self:utils:cIdent(name: name);
		}
		return self:utils:cIdent(name: name);
	}

	## Emits a colon-path reference: enum variants, chained field access.
	##
	## @param expr: The PATH expression.
	## @return: C expression.
	Function of String is emitPath(Expression is expr){
		local Array of String is segs: expr:pathSegments;
		if (segs:length() == 1) {
			return segs:get(index: 0);
		}
		if (segs:length() >= 2) {
			local String is root: segs:get(index: 0);
			if (self:allEnumNames:has(key: root)) {
				if (self:allTaggedEnums:has(key: root)) {
					return root . '_' . self:utils:cIdent(name: segs:get(index: 1)) . '_ctor()';
				}
				return root . '_' . self:utils:cIdent(name: segs:get(index: 1));
			}
			local String is rootC: self:utils:cIdent(name: root);
			if (!self:localVars:has(key: root) && self:fieldTypes:has(key: root)) {
				rootC: 'self->' . rootC;
			}
			local Int is idx: 1;
			local String is resC: rootC;
			While:condition(
				evaluate: local Function of Boolean(){
					return idx < segs:length();
				},
				iteration: local Function of Boolean(){
					resC: resC . '->' . self:utils:cIdent(name: segs:get(index: idx));
					idx: idx + 1;
					return true;
				}
			);
			if (root != self:names:selfIdent()) {
				local String is resolvedT: expr:resolvedType;
				local String is rootT: self:localVars:getString(key: root, default: '');
				if (rootT:contains(needle: ':') && !rootT:startsWith(prefix: 'Array:') && !rootT:startsWith(prefix: 'Map:') && resolvedT != '' && resolvedT != Primitive:ANY:value()) {
					local String is castT: self:cTypeFor(typeName: resolvedT);
					resC: '((' . castT . ')(intptr_t)(' . resC . '))';
				}
			}
			return resC;
		}
		return '';
	}

	## Emits a binary operation: concat, equality, arithmetic, bitwise.
	##
	## @param expr: The BINARY expression.
	## @return: C expression.
	Function of String is emitBinary(Expression is expr){
		local String is op: expr:binaryOp;
		when (op) {
			is '.': {
				local String is leftC: self:generateExpressionInner(expr: expr:leftExpr);
				local ExpressionKind is leftKind: expr:leftExpr:kind;
				local String is leftT: self:inferTargetType(expr: expr:leftExpr);
				local Boolean is leftPrim: leftT == Primitive:INT:value() || leftT == 'Byte' || leftT == 'Float' || leftT == 'Boolean';
				local Boolean is leftClaimKind: leftKind == ExpressionKind:CALL || leftKind == ExpressionKind:BINARY || leftKind == ExpressionKind:ARRAY || leftKind == ExpressionKind:MAP;
				local Boolean is leftArc: self:isArcType(typeName: leftT);
				local String is leftClaim: leftC;
				if (!leftPrim) {
					if (leftClaimKind) {
						leftClaim: leftC;
					} else if (leftArc) {
						leftClaim: '(void*)spec_retain((void*)(' . leftC . '))';
					} else {
						leftClaim: 'spec_string_from_chars(' . leftC . ')';
					}
				}
				local String is leftWrap: if (leftPrim) self:wrapToString(expr: expr:leftExpr, exprC: leftClaim) else leftClaim;
				local Boolean is savedArgR: self:argMode;
				self:argMode: true;
				local String is rightC: self:generateExpression(expr: expr:rightExpr);
				self:argMode: savedArgR;
				local String is rightWrap: self:wrapToString(expr: expr:rightExpr, exprC: rightC);
				return 'spec_string_concat(' . leftWrap . ', ' . rightWrap . ')';
			}
			is 'is', '==': {
				local String is leftC: self:generateExpression(expr: expr:leftExpr);
				local String is rightC: self:generateExpression(expr: expr:rightExpr);
				if (self:isStringExpr(expr: expr:leftExpr, exprC: leftC) || self:isStringExpr(expr: expr:rightExpr, exprC: rightC)) {
					return 'spec_string_equals(' . leftC . ', ' . rightC . ')';
				}
				return '((' . leftC . ') == (' . rightC . '))';
			}
			is '!=': {
				local String is leftC: self:generateExpression(expr: expr:leftExpr);
				local String is rightC: self:generateExpression(expr: expr:rightExpr);
				if (self:isStringExpr(expr: expr:leftExpr, exprC: leftC) || self:isStringExpr(expr: expr:rightExpr, exprC: rightC)) {
					return '(!spec_string_equals(' . leftC . ', ' . rightC . '))';
				}
				return '((' . leftC . ') != (' . rightC . '))';
			}
			is '<', '<=', '>', '>=', '+', '-', '*', '/', '%', '&&', '||', '&', '|', '^', '<<', '>>': {
				local String is leftC: self:generateExpression(expr: expr:leftExpr);
				local String is rightC: self:generateExpression(expr: expr:rightExpr);
				return '((' . leftC . ') ' . op . ' (' . rightC . '))';
			}
			else: {
				return '0';
			}
		}
	}

	## Emits an index expression: Map lookups and Array/List element access.
	##
	## @param expr: The INDEX expression.
	## @return: C expression.
	Function of String is emitIndex(Expression is expr){
		local String is targetC: self:generateExpression(expr: expr:leftExpr);
		local String is indexC: self:generateExpression(expr: expr:rightExpr);
		local String is targetType: self:inferTargetType(expr: expr:leftExpr);
		if (targetType:startsWith(prefix: 'Map:') || targetType == 'Map') {
			local String is valType: 'String';
			if (targetType:startsWith(prefix: 'Map:')) {
				valType: self:elemOfType(t: targetType);
			}
			if (valType == 'String') {
				return 'spec_map_get_string(' . targetC . ', ' . indexC . ', spec_string_intern(""))';
			}
			if (valType == Primitive:INT:value()) {
				return 'spec_map_get_int(' . targetC . ', ' . indexC . ', 0)';
			}
			if (valType == 'Float') {
				return 'spec_map_get_float(' . targetC . ', ' . indexC . ', 0.0)';
			}
			if (valType == 'Boolean') {
				return 'spec_map_get_bool(' . targetC . ', ' . indexC . ', false)';
			}
			local String is valCType: self:cTypeFor(typeName: valType);
			return '((' . valCType . ')(intptr_t)spec_map_get(' . targetC . ', ' . indexC . ', NULL))';
		}
		local String is elemT: self:elemOfType(t: targetType);
		if (elemT != '') {
			local String is elemCType: self:cTypeFor(typeName: elemT);
			return '((' . elemCType . ')(intptr_t)spec_array_get(' . targetC . ', (size_t)(' . indexC . ')))';
		}
		return '((long long)(intptr_t)spec_array_get(' . targetC . ', (size_t)(' . indexC . ')))';
	}

	## Emits a type cast: format casts, primitive conversions, class upcasts.
	##
	## @param expr: The CAST expression.
	## @return: C expression.
	Function of String is emitCast(Expression is expr){
		local String is innerC: self:generateExpression(expr: expr:leftExpr);
		local String is target: expr:castTarget;
		local String is srcT: self:inferTargetType(expr: expr:leftExpr);
		local String is digitsC: '0';
		if (expr:castArgs:length() > 0) {
			digitsC: self:generateExpression(expr: expr:castArgs:get(index: 0));
		}
		when (target) {
			is 'Hex': {
				if (srcT == 'String') {
					return 'spec_parse_base(' . innerC . ', 16, 0)';
				}
				return 'spec_int_to_base(' . innerC . ', 16, ' . digitsC . ')';
			}
			is 'Bin': {
				if (srcT == 'String') {
					return 'spec_parse_base(' . innerC . ', 2, 0)';
				}
				return 'spec_int_to_base(' . innerC . ', 2, ' . digitsC . ')';
			}
			is 'Oct': {
				if (srcT == 'String') {
					return 'spec_parse_base(' . innerC . ', 8, 0)';
				}
				return 'spec_int_to_base(' . innerC . ', 8, ' . digitsC . ')';
			}
			is 'Any': {
				return innerC;
			}
			is 'Int': {
				if (srcT == 'String') {
					return 'spec_parse_base(' . innerC . ', 10, 0)';
				}
				if (srcT == 'Float' || srcT == 'Byte') {
					return '((long long)(' . innerC . '))';
				}
				return innerC;
			}
			is 'Float': {
				return '((double)(' . innerC . '))';
			}
			is 'Byte': {
				if (srcT == 'Byte') {
					return innerC;
				}
				return '({ long long _bv = (long long)(' . innerC . '); if (_bv < 0 || _bv > 255) { spec_panic_byte_range(_bv); } ((unsigned char)_bv); })';
			}
			is 'String': {
				if (srcT == Primitive:INT:value()) {
					return 'spec_to_string_int(' . innerC . ')';
				}
				if (srcT == 'Float') {
					return 'spec_to_string_float(' . innerC . ')';
				}
				if (srcT == 'Boolean') {
					return 'spec_to_string_bool(' . innerC . ')';
				}
				if (self:allClassNames:has(key: srcT) && !self:allEnumNames:has(key: srcT) && !self:policy:isTransparent(c: self:findClass(name: srcT))) {
					return 'spec_type_name(' . innerC . ')';
				}
				# Unknown or computed sources (arithmetic binaries, calls with
				# unresolved types) route through the string-wrap policy.
				return self:wrapToString(expr: expr:leftExpr, exprC: innerC);
			}
			else: {
				if (self:allClassNames:has(key: target) && !self:allEnumNames:has(key: target) && !self:policy:isTransparent(c: self:findClass(name: target))) {
					return '((' . target . '*)spec_cast_check(' . innerC . ', "' . target . '"))';
				}
				return innerC;
			}
		}
	}

	## Emits a CALL expression: builtins, constructors, tagged variant
	## constructors, virtual dispatch, direct dispatch.
	##
	## @param expr: The CALL expression.
	## @return: C expression.
	Function of String is emitCall(Expression is expr){
		local String is targetC: self:generateExpression(expr: expr:methodTarget);
		local String is targetType: self:inferTargetType(expr: expr:methodTarget);
		local String is fieldKey: targetC;
		if (targetC:startsWith(prefix: 'self->')) {
			fieldKey: targetC:substring(start: 6, end: targetC:length());
		}
		if (targetType == '') {
			targetType: self:localVars:getString(key: fieldKey, default: '');
		}
		if (targetType == '') {
			targetType: self:fieldTypes:getString(key: fieldKey, default: '');
		}

		local String is builtinC: self:builtins:generateBuiltinCall(expr: expr, targetC: targetC, targetType: targetType, cg: self);
		if (builtinC != '') {
			return builtinC;
		}

		# Function variable or field invocation: fnVar(args).
		if (targetC == self:names:selfIdent() && (self:localVars:has(key: expr:methodName) || self:fieldTypes:has(key: expr:methodName))) {
			local String is fnVarT: self:localVars:getString(key: expr:methodName, default: self:fieldTypes:getString(key: expr:methodName, default: ''));
			if (fnVarT:startsWith(prefix: 'Function')) {
				local String is fnPtrC: if (self:localVars:has(key: expr:methodName)) self:utils:cIdent(name: expr:methodName) else 'self->' . self:utils:cIdent(name: expr:methodName);
				local String is retTName: if (fnVarT:startsWith(prefix: 'Function:') && fnVarT:length() > 9) fnVarT:substring(start: 9, end: fnVarT:length()) else 'Void';
				local String is retCType: self:cTypeFor(typeName: retTName);
				local String is pTypesC: 'void*';
				local String is cArgsC: '_cls->env';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					local String is aValC: self:generateExpression(expr: arg:value);
					local String is aT: self:inferTargetType(expr: arg:value);
					local String is aCType: self:cTypeFor(typeName: aT);
					pTypesC: pTypesC . ', ' . aCType;
					cArgsC: cArgsC . ', ' . aValC;
				});
				return '({ SpecClosure* _cls = (SpecClosure*)(' . fnPtrC . '); if (!_cls || !_cls->fn) spec_panic("Invocation of null Function"); ((' . retCType . ' (*)(' . pTypesC . '))_cls->fn)(' . cArgsC . '); })';
			}
		}

		# Tagged enum variant constructor.
		if (self:allEnumVariants:has(key: expr:methodName) && (self:allTaggedEnums:has(key: targetC) || targetC == self:names:selfIdent())) {
			local String is eName: self:allEnumVariants:getString(key: expr:methodName, default: '');
			if (self:allTaggedEnums:has(key: eName)) {
				local Member is vMem: self:lookupEnumVariant(enumName: eName, variantName: expr:methodName);
				local Array of Parameter is vParams: vMem:params;
				local String is vArgsC: '';
				local Int is pIdx: 0;
				vParams:each(action: local Function(Parameter is p){
					if (pIdx > 0) { vArgsC: vArgsC . ', '; }
					local String is pName: p:name;
					local Boolean is matched: false;
					local String is argC: '0';
					expr:methodArgs:each(action: local Function(NamedArg is a){
						if (!matched && a:name == pName && pName != '') {
							argC: self:generateExpression(expr: a:value);
							matched: true;
						}
					});
					if (!matched && pIdx < expr:argCount()) {
						local Expression is posArg: self:argValue(expr: expr, index: pIdx);
						argC: self:generateExpression(expr: posArg);
						matched: true;
					}
					vArgsC: vArgsC . argC;
					pIdx: pIdx + 1;
				});
				return eName . '_' . self:utils:cIdent(name: expr:methodName) . '(' . vArgsC . ')';
			}
		}

		# Constructor or static invocation: ClassName:init(...)/ClassName:method(...).
		if (self:allClassNames:has(key: targetC) && !self:allEnumNames:has(key: targetC)) {
			local String is argsJoined: self:formatCallArguments(className: targetC, methodName: expr:methodName, args: expr:methodArgs);
			if (expr:methodName == 'init') {
				local String is initCls: self:findMethodImplementingClass(className: targetC, methodName: 'init', paramCount: -1);
				if (initCls == '' || initCls == targetC) {
					return '({ ' . targetC . '* _inst = ' . targetC . '_new(); ' . targetC . '_init(_inst' . argsJoined . '); _inst; })';
				}
				local String is initArgs: self:formatCallArguments(className: initCls, methodName: 'init', args: expr:methodArgs);
				return '({ ' . targetC . '* _inst = ' . targetC . '_new(); ' . initCls . '_init((' . initCls . '*)_inst' . initArgs . '); _inst; })';
			}
			local Member is mDef: self:lookupMethodMember(className: targetC, methodName: expr:methodName);
			if (mDef:kind == MemberKind:METHOD) {
				local String is mRetType: self:resolveReturnType(t: mDef:memberType);
				if (mRetType != '' && mRetType != 'Void' && mRetType != 'void') {
					return targetC . '_' . expr:methodName . '(NULL' . argsJoined . ')';
				}
			}
			return '({ ' . targetC . '* _inst = ' . targetC . '_new(); ' . targetC . '_' . expr:methodName . '(_inst' . argsJoined . '); _inst; })';
		}

		# Instance method invocation.
		local String is objType: targetType;
		if (objType == '') {
			objType: self:localVars:getString(key: targetC, default: '');
		}
		if (objType == '') {
			objType: self:fieldTypes:getString(key: targetC, default: '');
		}
		if (objType == '' || objType == Primitive:ANY:value() || targetC == self:names:selfIdent()) {
			objType: self:currentClassName;
		}
		local String is fullObjType: objType;

		# Any-typed receiver dispatches through its own vtable.
		if (objType == Primitive:ANY:value() && self:methodSlots:has(key: expr:methodName)) {
			local Member is anyM: self:lookupMethodMember(className: 'Any', methodName: expr:methodName);
			if (anyM:kind == MemberKind:METHOD) {
				local String is slotC: self:methodSlots:getString(key: expr:methodName, default: '0');
				local String is retT: self:resolveReturnType(t: anyM:memberType);
				local String is argsC: '';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					argsC: argsC . ', ' . self:generateExpression(expr: arg:value);
				});
				if (retT == 'void') {
					return '((void (*)(Any*))((Any*)' . targetC . ')->_vtable[' . slotC . '])((Any*)' . targetC . argsC . ')';
				}
				return '((' . retT . ' (*)(Any*))((Any*)' . targetC . ')->_vtable[' . slotC . '])((Any*)' . targetC . argsC . ')';
			}
		}

		if (objType:startsWith(prefix: 'Array:')) {
			objType: 'Array';
		} else if (objType:startsWith(prefix: 'Map:')) {
			objType: 'Map';
		} else if (objType:contains(needle: ':')) {
			local Array of String is parts: objType:split(delimiter: ':');
			objType: parts:get(index: 0);
		}
		local String is argsC: self:formatCallArguments(className: fullObjType, methodName: expr:methodName, args: expr:methodArgs);
		local String is callStr: '';
		if (self:overriddenMethods:has(key: expr:methodName) && self:allClassNames:has(key: objType) && !self:allEnumNames:has(key: objType) && !self:policy:isTransparent(c: self:findClass(name: objType)) && self:methodSlots:has(key: expr:methodName)) {
			local Member is vm: self:lookupMethodMember(className: objType, methodName: expr:methodName);
			if (vm:kind == MemberKind:METHOD) {
				local String is retT: self:resolveReturnType(t: vm:memberType);
				local String is sigC: objType . '*';
				vm:params:each(action: local Function(Parameter is p){
					sigC: sigC . ', ' . self:cTypeFor(typeName: p:paramType:name);
				});
				local String is slotC: self:methodSlots:getString(key: expr:methodName, default: '0');
				if (targetC == self:names:selfIdent()) {
					callStr: '(((' . retT . ' (*)(' . sigC . '))self->_vtable[' . slotC . ']))((' . objType . '*)self' . argsC . ')';
				} else {
					callStr: '({ ' . objType . '* _recv = (' . objType . '*)(' . targetC . '); (((' . retT . ' (*)(' . sigC . '))_recv->_vtable[' . slotC . ']))((' . objType . '*)_recv' . argsC . '); })';
				}
			}
		}
		if (callStr == '') {
			local String is dispatchCls: self:findMethodImplementingClass(className: objType, methodName: expr:methodName, paramCount: -1);
			local String is targetExprC: targetC;
			if (dispatchCls != '' && dispatchCls != objType) {
				objType: dispatchCls;
				targetExprC: '((' . dispatchCls . '*)' . targetC . ')';
			}
			callStr: objType . '_' . expr:methodName . '(' . targetExprC . argsC . ') /* inst:' . objType . ':' . expr:methodName . ' */';
		}
		local Member is targetM: self:lookupMethodMember(className: objType, methodName: expr:methodName);
		local ClassInfo is targetCls: self:findClass(name: objType);
		if (targetM:kind == MemberKind:METHOD && targetCls:typeParams:length() > 0) {
			local String is rawRet: self:formatTypeString(t: targetM:memberType);
			if (targetCls:typeParams:indexOf(search: rawRet, default: -1) >= 0) {
				local String is resolvedRet: expr:resolvedType;
				if (resolvedRet != '' && resolvedRet != Primitive:ANY:value()) {
					local String is castCType: self:cTypeFor(typeName: resolvedRet);
					callStr: '((' . castCType . ')(intptr_t)(' . callStr . '))';
				}
			}
		}
		return callStr;
	}

	## Emits a `when` expression as a nested ternary chain.
	##
	## @param expr: The WHEN expression.
	## @return: C expression.
	Function of String is emitWhenExpression(Expression is expr){
		local String is subjC: self:generateExpression(expr: expr:whenSubject);
		local String is chain: '0';
		expr:whenArms:each(action: local Function(WhenArm is arm){
			if (arm:isElse && arm:hasValueExpr) {
				chain: self:generateExpression(expr: arm:valueExpr);
			}
		});
		expr:whenArms:each(action: local Function(WhenArm is arm){
			if (!arm:isElse && arm:hasValueExpr) {
				local String is bindsC: self:generateWhenBindings(subjC: subjC, arm: arm);
				local String is armVal: self:generateExpression(expr: arm:valueExpr);
				if (bindsC != '') {
					armVal: '({ ' . bindsC . ' ' . armVal . '; })';
				}
				local String is condOr: '';
				arm:conditions:each(action: local Function(Expression is c){
					local String is cmp: self:generateWhenCondition(subjExpr: expr:whenSubject, subjC: subjC, c: c);
					if (condOr == '') {
						condOr: cmp;
					} else {
						condOr: condOr . ' || ' . cmp;
					}
				});
				chain: '((' . condOr . ') ? (' . armVal . ') : (' . chain . '))';
			}
		});
		return chain;
	}

	## Emits an anonymous function as a static C function + closure.
	##
	## @param expr: The ANON_FN expression.
	## @return: C closure-construction expression.
	Function of String is emitAnonFn(Expression is expr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is fnName: '_anon_fn_' . id;
		local String is retC: self:cTypeFor(typeName: expr:anonReturnType:name);

		local Map of String to String is savedVars: Map:init();
		local Array of String is outerKeys: self:localVars:keys();
		outerKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
		});
		local Map of String to String is savedScopeVars: Map:init();
		local Array of String is outerScopeKeys: self:localScopeVars:keys();
		outerScopeKeys:each(action: local Function(String is k){
			savedScopeVars:set(key: k, value: self:localScopeVars:getString(key: k, default: ''));
		});
		self:localScopeVars: Map:init();

		local String is paramsC: 'void* _env_ptr';
		local Array of String is paramNames: [];
		expr:anonParams:each(action: local Function(Parameter is p){
			paramNames:add(item: p:name);
			self:localVars:set(key: p:name, value: self:formatTypeString(t: p:paramType));
			local String is pCType: self:cTypeFor(typeName: p:paramType:name);
			paramsC: paramsC . ', ' . pCType . ' ' . self:utils:cIdent(name: p:name);
		});

		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;
		self:inlineReturnVar: '';
		self:inlineReturnLabel: '';
		local String is bodyC: '';
		expr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});
		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;
		self:localVars: savedVars;
		self:localScopeVars: savedScopeVars;

		local String is envName: '_Env_anon_' . id;
		local String is destroyEnvName: '_destroy_env_anon_' . id;
		local String is capFieldDecls: '';
		local String is capFieldBinds: '';
		local String is capAssigns: '';
		local String is capReleases: '';
		local Boolean is hasCaptures: false;

		if (self:inMethod && self:currentClassName != '' && !self:policy:isTransparent(c: self:findClass(name: self:currentClassName)) && !self:allEnumNames:has(key: self:currentClassName) && bodyC:contains(needle: 'self')) {
			hasCaptures: true;
			capFieldDecls: capFieldDecls . '    ' . self:currentClassName . "* self;\n";
			capFieldBinds: capFieldBinds . '    ' . self:currentClassName . "* self = _env->self;\n    (void)self;\n";
			capAssigns: capAssigns . '    _env->self = (' . self:currentClassName . "*)spec_retain((void*)self);\n";
			capReleases: capReleases . "    if (_env->self) spec_release((void*)_env->self);\n";
		}

		# Names the body redeclares shadow the outer scope — they are NOT
		# captures; binding them from the env would redeclare the local.
		local Map of String to String is bodyLocals: Map:init();
		expr:anonBody:each(action: local Function(Statement is s){
			if (s:kind == StatementKind:VAR_DECL) {
				bodyLocals:set(key: s:varName, value: 'true');
			}
		});

		outerKeys:each(action: local Function(String is k){
			if (paramNames:indexOf(search: k, default: -1) < 0 && !bodyLocals:has(key: k)) {
				local String is cVar: self:utils:cIdent(name: k);
				if (bodyC:contains(needle: cVar)) {
					local String is vType: savedVars:getString(key: k, default: '');
					local String is vCType: self:cTypeFor(typeName: vType);
					if (vCType != 'void' && vCType != '') {
						hasCaptures: true;
						capFieldDecls: capFieldDecls . '    ' . vCType . ' ' . cVar . ";\n";
						capFieldBinds: capFieldBinds . '    ' . vCType . ' ' . cVar . ' = _env->' . cVar . ";\n    (void)" . cVar . ";\n";
						if (self:isArcType(typeName: vType)) {
							capAssigns: capAssigns . '    _env->' . cVar . ' = (' . vCType . ')spec_retain((void*)' . cVar . ");\n";
							capReleases: capReleases . '    if (_env->' . cVar . ') spec_release((void*)_env->' . cVar . ");\n";
						} else {
							capAssigns: capAssigns . '    _env->' . cVar . ' = ' . cVar . ";\n";
						}
					}
				}
			}
		});

		if (hasCaptures) {
			local String is envStruct: "typedef struct {\n" . capFieldDecls . '} ' . envName . ";\n\n";
			local String is destroyEnv: 'static void ' . destroyEnvName . "(void* _env_ptr) {\n    if (!_env_ptr) return;\n    " . envName . '* _env = (' . envName . "*)_env_ptr;\n" . capReleases . "    free(_env);\n}\n\n";
			local String is bindsC: '    ' . envName . '* _env = (' . envName . "*)_env_ptr;\n" . capFieldBinds;
			self:helperFunctions: self:helperFunctions . envStruct . destroyEnv . 'static ' . retC . ' ' . fnName . '(' . paramsC . ") {\n" . bindsC . bodyC . "}\n\n";
			return '({ ' . envName . '* _env = (' . envName . '*)calloc(1, sizeof(' . envName . "));\n" . capAssigns . '    spec_closure_new((void*)' . fnName . ', (void*)_env, ' . destroyEnvName . '); })';
		} else {
			self:helperFunctions: self:helperFunctions . 'static ' . retC . ' ' . fnName . '(' . paramsC . ") {\n    (void)_env_ptr;\n" . bodyC . "}\n\n";
			return 'spec_closure_new((void*)' . fnName . ', NULL, NULL)';
		}
	}

	## Formats call arguments: matched by parameter name, positional
	## fallback, declaration-side defaults.
	##
	## @param className: The receiver class name.
	## @param methodName: The method name.
	## @param args: The call arguments.
	## @return: Comma-joined C arguments (no receiver).
	Function of String is formatCallArguments(String is className, String is methodName, Array of NamedArg is args){
		local Member is m: self:lookupMethodMember(className: className, methodName: methodName);
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		local Array of String is tps: cls:typeParams;
		if (m:kind == MemberKind:METHOD) {
			local Array of Parameter is params: m:params;
			if (params:length() > 0) {
				local String is joined: '';
				local Int is pIdx: 0;
				params:each(action: local Function(Parameter is p){
					local String is pName: p:name;
					local Boolean is matched: false;
					local String is argC: '0';
					args:each(action: local Function(NamedArg is a){
						if (!matched && a:name == pName && pName != '') {
							argC: self:generateExpression(expr: a:value);
							matched: true;
						}
					});
					if (!matched && pIdx < args:length()) {
						local NamedArg is posArg: args:get(index: pIdx);
						if (posArg:name == '') {
							argC: self:generateExpression(expr: posArg:value);
							matched: true;
						}
					}
					if (!matched && p:hasDefault) {
						argC: self:generateExpression(expr: p:defaultExpr);
						matched: true;
					}
					# Ground the enclosing class's generic parameters to void*.
					if (tps:indexOf(search: p:paramType:name, default: -1) >= 0) {
						argC: '(void*)(intptr_t)(' . argC . ')';
					}
					joined: joined . ', ' . argC;
					pIdx: pIdx + 1;
				});
				return joined;
			}
		}
		local String is joined: '';
		args:each(action: local Function(NamedArg is a){
			joined: joined . ', ' . self:generateExpression(expr: a:value);
		});
		return joined;
	}

	## Emits scope-end releases for the ARC-typed locals directly declared
	## in a statement list. Locals own their references (typed constructors
	## retain borrows, spec_assign retains, containers retain elements), so
	## releasing at block end is safe; claims pool only fresh temporaries.
	##
	## @param stmts: The block's statement list.
	## @return: Release lines, or '' when nothing needs release.
	Function of String is scopeReleases(Array of Statement is stmts){
		local String is out: '';
		stmts:each(action: local Function(Statement is stmt){
			if (stmt:kind == StatementKind:VAR_DECL) {
				local String is typeName: self:formatTypeString(t: stmt:varType);
				if (self:isArcType(typeName: typeName)) {
					local String is varC: self:utils:cIdent(name: stmt:varName);
					out: out . '    if (' . varC . ') { spec_release((void*)' . varC . '); ' . varC . " = NULL; }\n";
				}
			}
		});
		return out;
	}

	## Generates the when-condition comparison for one arm condition.
	##
	## @param subjExpr: The when subject expression.
	## @param subjC: The subject's C.
	## @param c: The condition expression.
	## @return: C boolean expression.
	Function of String is generateWhenCondition(Expression is subjExpr, String is subjC, Expression is c){
		if (c:kind == ExpressionKind:CALL && self:allEnumVariants:has(key: c:methodName)) {
			local String is eName: self:allEnumVariants:getString(key: c:methodName, default: '');
			if (self:allTaggedEnums:has(key: eName)) {
				return '((' . subjC . ') && (' . subjC . ')->_tag == ' . eName . '_TAG_' . self:utils:cIdent(name: c:methodName) . ')';
			}
		}
		if (c:kind == ExpressionKind:IDENT && self:allEnumVariants:has(key: c:stringValue)) {
			local String is eName: self:allEnumVariants:getString(key: c:stringValue, default: '');
			if (self:allTaggedEnums:has(key: eName)) {
				return '((' . subjC . ') && (' . subjC . ')->_tag == ' . eName . '_TAG_' . self:utils:cIdent(name: c:stringValue) . ')';
			}
		}
		if (c:kind == ExpressionKind:PATH && c:pathSegments:length() >= 2 && self:allTaggedEnums:has(key: c:pathSegments:get(index: 0))) {
			local String is eName: c:pathSegments:get(index: 0);
			local String is vName: c:pathSegments:get(index: 1);
			return '((' . subjC . ') && (' . subjC . ')->_tag == ' . eName . '_TAG_' . self:utils:cIdent(name: vName) . ')';
		}
		local String is cVal: self:generateExpression(expr: c);
		if (self:isStringExpr(expr: subjExpr, exprC: subjC)) {
			return 'spec_string_equals(' . subjC . ', ' . cVal . ')';
		}
		return '((' . subjC . ') == (' . cVal . '))';
	}

	## Generates variable bindings for tagged-variant pattern payloads.
	##
	## @param subjC: The subject's C.
	## @param arm: The when arm.
	## @return: C variable declarations.
	Function of String is generateWhenBindings(String is subjC, WhenArm is arm){
		local String is binds: '';
		arm:conditions:each(action: local Function(Expression is c){
			if (c:kind == ExpressionKind:CALL && self:allEnumVariants:has(key: c:methodName)) {
				local String is eName: self:allEnumVariants:getString(key: c:methodName, default: '');
				if (self:allTaggedEnums:has(key: eName)) {
					local Member is vMem: self:lookupEnumVariant(enumName: eName, variantName: c:methodName);
					local String is vNameC: self:utils:cIdent(name: c:methodName);
					local Int is idx: 0;
					c:methodArgs:each(action: local Function(NamedArg is arg){
						if (idx < vMem:params:length()) {
							local Expression is av: arg:value;
							if (av:kind == ExpressionKind:IDENT) {
								local Parameter is pDef: vMem:params:get(index: idx);
								local String is bindName: av:stringValue;
								self:localVars:set(key: bindName, value: self:formatTypeString(t: pDef:paramType));
								local String is pCType: self:cTypeFor(typeName: pDef:paramType:name);
								binds: binds . '        ' . pCType . ' ' . self:utils:cIdent(name: bindName) . ' = (' . subjC . ')->' . vNameC . '_' . self:utils:cIdent(name: pDef:name) . ";\n";
							}
						}
						idx: idx + 1;
					});
				}
			}
		});
		return binds;
	}

	## Resolves a simple local or self-field target to its C lvalue.
	##
	## @param expr: The target expression.
	## @return: C lvalue string, or '' when complex.
	Function of String is tryGenerateTargetOnly(Expression is expr){
		if (expr:kind == ExpressionKind:IDENT) {
			if (self:localVars:has(key: expr:stringValue)) {
				return self:utils:cIdent(name: expr:stringValue);
			}
			if (self:inMethod && self:fieldTypes:has(key: expr:stringValue)) {
				return 'self->' . self:utils:cIdent(name: expr:stringValue);
			}
			return self:utils:cIdent(name: expr:stringValue);
		}
		if (expr:kind == ExpressionKind:PATH && expr:pathSegments:length() == 2 && expr:pathSegments:get(index: 0) == self:names:selfIdent()) {
			return 'self->' . self:utils:cIdent(name: expr:pathSegments:get(index: 1));
		}
		return '';
	}

	## Optimizes left-recursive concat chains into spec_string_append.
	##
	## @param expr: The right-hand side expression.
	## @param targetC: The target lvalue C.
	## @return: Append-chain C, or '' when not optimizable.
	Function of String is tryGenerateAppendChain(Expression is expr, String is targetC){
		if (targetC == '') {
			return '';
		}
		if (expr:kind == ExpressionKind:BINARY && expr:binaryOp == '.') {
			local String is leftTarget: self:tryGenerateTargetOnly(expr: expr:leftExpr);
			if (leftTarget == targetC) {
				local String is rhsC: self:wrapToString(expr: expr:rightExpr, exprC: self:generateExpression(expr: expr:rightExpr));
				if (rhsC:contains(needle: targetC)) {
					return '';
				}
				return 'spec_string_concat(' . targetC . ', ' . rhsC . ')';
			}
			local String is innerChain: self:tryGenerateAppendChain(expr: expr:leftExpr, targetC: targetC);
			if (innerChain != '') {
				local String is rhsC: self:wrapToString(expr: expr:rightExpr, exprC: self:generateExpression(expr: expr:rightExpr));
				if (rhsC:contains(needle: targetC)) {
					return '';
				}
				return 'spec_string_concat(' . innerChain . ', ' . rhsC . ')';
			}
		}
		return '';
	}

	## Generates C for a statement node.
	##
	## @param stmt: The statement node.
	## @return: C statement code.
	Function of String is generateStatement(Statement is stmt){
		if (stmt:line > 0) {
			self:currentLineHack(stmt: stmt);
		}
		local StatementKind is kind: stmt:kind;

		when (kind) {
			is StatementKind:VAR_DECL: {
				return self:emitVarDecl(stmt: stmt);
			}
			is StatementKind:ASSIGN: {
				return self:emitAssign(stmt: stmt);
			}
			is StatementKind:IF: {
				local String is condC: self:generateExpression(expr: stmt:ifCondition);
				local String is out: '    if (' . condC . ") {\n";
				stmt:thenBranch:each(action: local Function(Statement is s){
					out: out . '    ' . self:generateStatement(stmt: s);
				});
				out: out . self:scopeReleases(stmts: stmt:thenBranch);
				if (stmt:hasElse) {
					out: out . "    } else {\n";
					stmt:elseBranch:each(action: local Function(Statement is s){
						out: out . '    ' . self:generateStatement(stmt: s);
					});
					out: out . self:scopeReleases(stmts: stmt:elseBranch);
				}
				out: out . "    }\n";
				return out;
			}
			is StatementKind:FORWARD: {
				return self:emitForward(stmt: stmt);
			}
			is StatementKind:RETURN: {
				return self:emitReturn(stmt: stmt);
			}
			is StatementKind:WHEN: {
				return self:emitWhenStatement(stmt: stmt);
			}
			is StatementKind:EXPR: {
				# Claim-yielding results go to the pool (released on
				# eviction). A CALL that yields no claim but returns an
				# ARC type is the blanket-RETURN-retain case: the callee
				# retained its result for this caller and nobody consumes
				# it, so the statement releases it. Everything else
				# (idents, fields) is a borrow — leave it alone.
				local String is exprC: self:generateExpression(expr: stmt:exprStmt);
				local String is resT: self:inferTargetType(expr: stmt:exprStmt);
				if (stmt:exprStmt:kind == ExpressionKind:CALL && !self:yieldsClaim(expr: stmt:exprStmt) && self:isArcType(typeName: resT)) {
					return '    spec_release((void*)(' . exprC . "));\n";
				}
				return '    ' . exprC . ";\n";
			}
			is StatementKind:CLASS: {
				return '';
			}
			else: {
				return '';
			}
		}
	}

	## Compatibility: the fossil tracked currentLine but the codegen does not
	## need it (diagnostics come from the checker).
	Function is currentLineHack(Statement is stmt){
	}

	## Emits a variable declaration with the typed constructor.
	##
	## @param stmt: The VAR_DECL statement.
	## @return: C declaration.
	Function of String is emitVarDecl(Statement is stmt){
		self:localVars:set(key: stmt:varName, value: self:formatTypeString(t: stmt:varType));
		self:localScopeVars:set(key: stmt:varName, value: stmt:varType:name);
		local String is vTypeName: stmt:varType:name;
		local String is cType: '';
		if (vTypeName == 'List') {
			cType: self:cTypeFor(typeName: self:formatTypeString(t: stmt:varType));
		} else {
			cType: self:cTypeFor(typeName: vTypeName);
		}
		local String is varName: self:utils:cIdent(name: stmt:varName);
		local Boolean is isArcVar: self:isArcType(typeName: vTypeName);
		local String is autoPrefix: if (isArcVar) 'SPEC_AUTO ' else '';
		if (stmt:hasInit) {
			local ExpressionKind is initKind: stmt:initExpr:kind;
			if (initKind == ExpressionKind:ARRAY || initKind == ExpressionKind:MAP) {
				self:setContainerHint(t: self:formatTypeString(t: stmt:varType));
			}
			local Boolean is savedArg: self:argMode;
			self:argMode: false;
			local String is initC: self:generateExpression(expr: stmt:initExpr);
			self:argMode: savedArg;
			self:setContainerHint(t: '');
			local Boolean is claims: self:yieldsClaim(expr: stmt:initExpr);
			initC: self:generateTypedConstructor(typeName: vTypeName, valueC: initC, cType: cType, claims: claims);
			return '    ' . autoPrefix . cType . ' ' . varName . ' = ' . initC . ";\n";
		}
		if (vTypeName == 'String') {
			return '    ' . cType . ' ' . varName . " = \"\";\n";
		}
		if (vTypeName == 'Array') {
			local String is elemKind: self:containerElemKind(containerType: self:formatTypeString(t: stmt:varType));
			local String is newCall: 'spec_array_new()';
			if (elemKind == 'object') {
				newCall: 'spec_array_new_object()';
			} else if (elemKind == 'string') {
				newCall: 'spec_array_new_string()';
			}
			return '    ' . autoPrefix . cType . ' ' . varName . ' = ' . newCall . ";\n";
		}
		if (vTypeName == 'List') {
			local String is fullT: self:formatTypeString(t: stmt:varType);
			local String is elemKind: self:containerElemKind(containerType: fullT);
			local String is newCall: 'spec_vec_new()';
			if (elemKind == 'byte') {
				newCall: 'spec_bytebuffer_new()';
			} else if (elemKind == 'string') {
				newCall: 'spec_vec_new_string()';
			} else if (elemKind == 'object') {
				newCall: 'spec_vec_new_object()';
			}
			return '    ' . autoPrefix . cType . ' ' . varName . ' = ' . newCall . ";\n";
		}
		if (vTypeName == 'Map') {
			local String is newCall: 'spec_map_new()';
			if (self:containerElemIsArc(containerType: self:formatTypeString(t: stmt:varType))) {
				newCall: 'spec_map_new_object()';
			}
			return '    ' . autoPrefix . cType . ' ' . varName . ' = ' . newCall . ";\n";
		}
		return '    ' . autoPrefix . cType . ' ' . varName . " = 0;\n";
	}

	## Emits an assignment: container stores, concat-chain optimization,
	## ARC spec_assign.
	##
	## @param stmt: The ASSIGN statement.
	## @return: C assignment.
	Function of String is emitAssign(Statement is stmt){
		if (stmt:assignTarget:kind == ExpressionKind:INDEX) {
			local String is containerC: self:generateExpression(expr: stmt:assignTarget:leftExpr);
			local String is idxC: self:generateExpression(expr: stmt:assignTarget:rightExpr);
			local String is containerType: self:inferTargetType(expr: stmt:assignTarget:leftExpr);
			local Boolean is savedArgIx: self:argMode;
			self:argMode: false;
			local String is valC: self:generateExpression(expr: stmt:assignValue);
			self:argMode: savedArgIx;
			if (containerType:startsWith(prefix: 'Map:') || containerType == 'Map') {
				if (containerType:contains(needle: 'String:String') || containerType:contains(needle: 'to String') || self:isStringExpr(expr: stmt:assignValue, exprC: valC)) {
					return '    spec_map_set(' . containerC . ', ' . idxC . ', ' . valC . ");\n";
				}
				return '    spec_map_set_any(' . containerC . ', ' . idxC . ', (void*)(intptr_t)(' . valC . "));\n";
			}
			return '    spec_array_set(' . containerC . ', ' . idxC . ', (void*)(intptr_t)(' . valC . "));\n";
		}
		local String is targetC: self:generateExpression(expr: stmt:assignTarget);
		local String is appendC: self:tryGenerateAppendChain(expr: stmt:assignValue, targetC: targetC);
		if (appendC != '') {
			return '    ' . targetC . ' = ' . appendC . ";\n";
		}
		local String is lhsType: self:inferTargetType(expr: stmt:assignTarget);
		local ExpressionKind is valKind: stmt:assignValue:kind;
		if ((valKind == ExpressionKind:ARRAY || valKind == ExpressionKind:MAP) && (lhsType:startsWith(prefix: 'Array') || lhsType:startsWith(prefix: 'Map') || lhsType:startsWith(prefix: 'List'))) {
			self:setContainerHint(t: lhsType);
		}
		local Boolean is savedArg: self:argMode;
		self:argMode: false;
		local String is valC: self:generateExpression(expr: stmt:assignValue);
		self:argMode: savedArg;
		local ClassInfo is curCls: self:findClass(name: self:currentClassName);
		if (curCls:typeParams:indexOf(search: lhsType, default: -1) >= 0) {
			valC: '(void*)(intptr_t)(' . valC . ')';
		}
		local Boolean is isArcLhs: self:isArcType(typeName: lhsType);
		if (isArcLhs) {
			# Parameters are borrows: overwriting one retains the new value
			# but must not release the caller's argument.
			if (stmt:assignTarget:kind == ExpressionKind:IDENT && self:currentParams:has(key: stmt:assignTarget:stringValue)) {
				return '    spec_retain((void*)(' . valC . ')); ' . targetC . ' = ' . valC . ";\n";
			}
			return '    spec_assign((void**)&' . targetC . ', (void*)(' . valC . "));\n";
		}
		return '    ' . targetC . ' = ' . valC . ";\n";
	}

	## Emits a merge-forward delegation to the nearest parent implementation.
	##
	## @param stmt: The FORWARD statement.
	## @return: C delegation call.
	Function of String is emitForward(Statement is stmt){
		local ClassInfo is fwdCls: self:findClass(name: self:currentClassName);
		local String is dispatchCls: '';
		fwdCls:baseClasses:each(action: local Function(String is baseName){
			if (dispatchCls == '') {
				local String is implCls: self:findMethodImplementingClass(className: baseName, methodName: self:currentMethodName, paramCount: -1);
				if (implCls != '') {
					dispatchCls: implCls;
				}
			}
		});
		if (dispatchCls == '') {
			return '';
		}
		local Member is superM: self:lookupMethodMember(className: dispatchCls, methodName: self:currentMethodName);
		local String is argsC: self:formatCallArguments(className: dispatchCls, methodName: self:currentMethodName, args: stmt:forwardArgs);
		local String is callC: dispatchCls . '_' . self:currentMethodName . '((' . dispatchCls . '*)self' . argsC . ')';
		local String is superRet: self:resolveReturnType(t: superM:memberType);
		if (superRet != 'void') {
			return '    return ' . callC . ";\n";
		}
		return '    ' . callC . ";\n";
	}

	## Emits a return with ARC ownership transfer.
	##
	## @param stmt: The RETURN statement.
	## @return: C return.
	Function of String is emitReturn(Statement is stmt){
		if (self:inlineReturnLabel != '') {
			if (stmt:hasReturnExpr && self:inlineReturnVar != '') {
				local String is retC: self:generateExpression(expr: stmt:returnExpr);
				return '    ' . self:inlineReturnVar . ' = ' . retC . "; break;\n";
			}
			return "    break;\n";
		}
		if (stmt:hasReturnExpr) {
			local ExpressionKind is retKind: stmt:returnExpr:kind;
			if ((retKind == ExpressionKind:ARRAY || retKind == ExpressionKind:MAP) && (self:currentMethodReturnType:startsWith(prefix: 'Array') || self:currentMethodReturnType:startsWith(prefix: 'Map'))) {
				self:setContainerHint(t: self:currentMethodReturnType);
			}
			local Boolean is savedArg: self:argMode;
			self:argMode: false;
			local String is retC: self:generateExpression(expr: stmt:returnExpr);
			self:argMode: savedArg;
			local ClassInfo is curCls: self:findClass(name: self:currentClassName);
			if (curCls:typeParams:indexOf(search: self:currentMethodReturnType, default: -1) >= 0) {
				retC: '(void*)(intptr_t)(' . retC . ')';
			} else if (self:isArcType(typeName: self:currentMethodReturnType)) {
				local Boolean is ownedLocal: retKind == ExpressionKind:IDENT && self:localScopeVars:has(key: stmt:returnExpr:stringValue);
				if (ownedLocal) {
					local String is identC: self:utils:cIdent(name: stmt:returnExpr:stringValue);
					local String is rtC: self:cTypeFor(typeName: self:currentMethodReturnType);
					retC: '(' . rtC . ')({ ' . rtC . ' _ret_val = ' . identC . '; ' . identC . " = NULL; _ret_val; })";
				} else if (self:isFreshConstructorCall(expr: stmt:returnExpr)) {
					retC: '(' . self:cTypeFor(typeName: self:currentMethodReturnType) . ')(' . retC . ')';
				} else {
					retC: '(' . self:cTypeFor(typeName: self:currentMethodReturnType) . ')spec_retain((void*)(' . retC . '))';
				}
			}
			return '    return ' . retC . ";\n";
		}
		return "    return;\n";
	}

	## Emits a when statement as an if/else-if chain.
	##
	## @param stmt: The WHEN statement.
	## @return: C if/else chain.
	Function of String is emitWhenStatement(Statement is stmt){
		local String is subjC: self:generateExpression(expr: stmt:whenSubject);
		local String is out: '';
		local Boolean is first: true;
		stmt:whenArms:each(action: local Function(WhenArm is arm){
			if (arm:isElse) {
				out: out . "    } else {\n";
			} else {
				local String is condOr: '';
				arm:conditions:each(action: local Function(Expression is c){
					local String is cmp: self:generateWhenCondition(subjExpr: stmt:whenSubject, subjC: subjC, c: c);
					if (condOr == '') {
						condOr: cmp;
					} else {
						condOr: condOr . ' || ' . cmp;
					}
				});
				local String is bindsC: self:generateWhenBindings(subjC: subjC, arm: arm);
				if (first) {
					out: out . '    if (' . condOr . ") {\n";
					first: false;
				} else {
					out: out . '    } else if (' . condOr . ") {\n";
				}
				out: out . bindsC;
			}
			arm:body:each(action: local Function(Statement is s){
				out: out . '    ' . self:generateStatement(stmt: s);
			});
			out: out . self:scopeReleases(stmts: arm:body);
		});
		out: out . "    }\n";
		return out;
	}

	## Generates a C method implementation.
	##
	## @param classDef: The enclosing class.
	## @param method: The method member.
	## @return: C method implementation.
	## True when the class's namespace ends with sysinternal — the
	## structural C-floor annotation (TRANSITION.md section 1).
	##
	## @param name: Class name.
	## @return: true when the class is a floor binding.
	Function of Boolean is isSysinternalClass(String is name){
		local ClassInfo is c: self:findClass(name: name);
		if (c:name == '') {
			return false;
		}
		return self:policy:isSysinternal(cls: c);
	}

	Function of String is generateMethod(ClassInfo is classDef, Member is method){
		self:inMethod: true;
		self:currentMethodName: method:name;
		self:currentMethodReturnType: self:formatTypeString(t: method:memberType);
		local String is retType: self:resolveReturnType(t: method:memberType);
		if (retType == 'void') {
			if (method:name == ContractMethod:EVALUATE:value() || method:name == ContractMethod:ITERATION:value()) {
				retType: 'bool';
			}
		}

		self:localVars: Map:init();
		self:localScopeVars: Map:init();
		self:currentParams: Map:init();
		method:params:each(action: local Function(Parameter is p){
			self:localVars:set(key: p:name, value: self:formatTypeString(t: p:paramType));
			self:currentParams:set(key: p:name, value: 'true');
		});

		local String is selfCType: self:cTypeFor(typeName: classDef:name);
		local String is out: retType . ' ' . classDef:name . '_' . method:name . '(' . selfCType . ' self';
		method:params:each(action: local Function(Parameter is p){
			out: out . ', ' . self:cTypeFor(typeName: p:paramType:name) . ' ' . self:utils:cIdent(name: p:name);
		});
		out: out . ") {\n";

		method:body:each(action: local Function(Statement is stmt){
			out: out . self:generateStatement(stmt: stmt);
		});

		if (method:body:length() == 0 && retType != 'void') {
			out: out . "    return 0;\n";
		}

		# Scope-end releases: drop the refs this method's locals own.
		out: out . self:scopeReleases(stmts: method:body);
		out: out . "}\n\n";
		self:inMethod: false;
		return out;
	}

	## Generates the C main entry point with argv->Map parsing.
	##
	## @param entryClass: The entry class name.
	## @return: C main function.
	Function of String is generateMain(String is entryClass){
		local String is m: "/* Application Entry Point */\n";
		m: m . "int main(int argc, char** argv) {\n";
		m: m . "#if defined(SPEC_GC_BOEHM)\n    GC_init();\n#endif\n";
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
		m: m . "                kbuf[klen] = 0;\n";
		m: m . "                spec_map_set(args, spec_string_from_chars(kbuf), spec_string_from_chars(eq + 1));\n";
		m: m . "            } else {\n";
		m: m . "                const char* key = argv[i] + 2;\n";
		m: m . "                const char* val = \"true\";\n";
		m: m . "                if (i + 1 < argc && argv[i + 1][0] != '-') {\n";
		m: m . "                    val = argv[++i];\n";
		m: m . "                }\n";
		m: m . "                spec_map_set(args, spec_string_from_chars(key), spec_string_from_chars(val));\n";
		m: m . "            }\n";
		m: m . "        } else if (argv[i][0] == '-' && argv[i][1] != 0) {\n";
		m: m . "            const char* eq = strchr(argv[i] + 1, '=');\n";
		m: m . "            if (eq) {\n";
		m: m . "                int klen = (int)(eq - (argv[i] + 1));\n";
		m: m . "                char kbuf[128];\n";
		m: m . "                if (klen >= 128) klen = 127;\n";
		m: m . "                strncpy(kbuf, argv[i] + 1, klen);\n";
		m: m . "                kbuf[klen] = 0;\n";
		m: m . "                spec_map_set(args, spec_string_from_chars(kbuf), spec_string_from_chars(eq + 1));\n";
		m: m . "            } else {\n";
		m: m . "                const char* key = argv[i] + 1;\n";
		m: m . "                const char* val = \"true\";\n";
		m: m . "                if (i + 1 < argc && argv[i + 1][0] != '-') {\n";
		m: m . "                    val = argv[++i];\n";
		m: m . "                }\n";
		m: m . "                spec_map_set(args, spec_string_from_chars(key), spec_string_from_chars(val));\n";
		m: m . "            }\n";
		m: m . "        }\n";
		m: m . "    }\n";
		m: m . '    SPEC_AUTO ' . entryClass . '* app = ' . entryClass . "_new();\n";
		m: m . '    ' . entryClass . "_init(app, args);\n";
		m: m . "    spec_drain_async_tasks();\n";
		m: m . "    return 0;\n";
		m: m . "}\n";
		return m;
	}

	## Collects nested classes from a statement tree.
	Function is collectClassesFromStatement(Statement is stmt, Array of ClassInfo is acc){
		when (stmt:kind) {
			is StatementKind:CLASS: {
				self:collectClasses(c: stmt:nestedClass, acc: acc);
			}
			is StatementKind:IF: {
				stmt:thenBranch:each(action: local Function(Statement is s){
					self:collectClassesFromStatement(stmt: s, acc: acc);
				});
				if (stmt:hasElse) {
					stmt:elseBranch:each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
					});
				}
			}
			is StatementKind:WHEN: {
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					arm:body:each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
					});
				});
			}
			else: {}
		}
	}

	## Collects a class and all nested definitions.
	Function is collectClasses(ClassInfo is c, Array of ClassInfo is acc){
		acc:add(item: c);
		c:members:each(action: local Function(Member is m){
			when (m:kind) {
				is MemberKind:CLASS: {
					self:collectClasses(c: m:nestedClass, acc: acc);
				}
				is MemberKind:METHOD: {
					m:body:each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
					});
				}
				else: {}
			}
		});
	}

	## Translates a complete parsed program into a standalone C11 file.
	##
	## @param program: The parsed program.
	## @param entryClass: The entry-point class name.
	## @return: Complete C11 source.
	Function of String is generateProgram(ProgramNode is program, String is entryClass){
		local Array of ClassInfo is flattenedClasses: [];
		program:classes:each(action: local Function(ClassInfo is c){
			self:collectClasses(c: c, acc: flattenedClasses);
		});
		# registerProgram was called with the FULL class set (source + preloaded)
		# by the driver; this method's emission loop iterates only the source
		# program's classes.
		self:assignVirtualSlots(classes: flattenedClasses);
		self:declGen:setEnumNames(names: self:allEnumNames);
		self:declGen:setTaggedEnums(names: self:allTaggedEnums);
		self:builtins:setEnumNames(names: self:allEnumNames);

		local String is enums: self:declGen:generateEnums(classes: flattenedClasses);
		local String is decls: self:declGen:generateForwardDeclarations(classes: flattenedClasses);
		local String is structs: self:declGen:generateStructs(classes: flattenedClasses);
		local String is vt: self:generateVTables(classes: flattenedClasses);
		local String is ctors: self:generateConstructors(classes: flattenedClasses);

		local String is methods: '';
		flattenedClasses:each(action: local Function(ClassInfo is c){
			if (!self:policy:isTransparent(c: c) || c:name == 'String') {
				self:currentClassName: c:name;
				self:fieldTypes: Map:init();
				local Array of Member is allFields: [];
				self:declGen:collectStructFields(c: c, allClasses: flattenedClasses, acc: allFields);
				allFields:each(action: local Function(Member is m){
					self:fieldTypes:set(key: m:name, value: self:formatTypeString(t: m:memberType));
				});

				local Boolean is hasInit: false;
				c:members:each(action: local Function(Member is m){
					when (m:kind) {
						is MemberKind:METHOD: {
							if (m:name == 'init') { hasInit: true; }
							methods: methods . self:generateMethod(classDef: c, method: m);
						}
						else: {}
					}
				});
				if (!hasInit && c:baseClass != self:names:enumHeader()) {
					methods: methods . 'void ' . c:name . '_init(' . c:name . "* self) {\n    /* default initializer */\n}\n\n";
				}

				local Boolean is hasToString: false;
				c:members:each(action: local Function(Member is m){
					if (m:name == 'toString') { hasToString: true; }
				});
				if (!hasToString && c:baseClass != self:names:enumHeader()) {
					local String is cn: c:name;
					methods: methods . 'String ' . cn . '_toString(' . cn . "* self) {\n";
					methods: methods . "    if (!self) { return spec_string_intern(\"\"); }\n";
					methods: methods . '    return spec_string_intern("' . cn . '");' . "\n}\n\n";
				}
			}
		});

		local String is mainFn: self:generateMain(entryClass: entryClass);

		local String is cSource: '';
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

	## Collects all ancestor class names transitively.
	Function is collectAncestors(ClassInfo is c, Array of ClassInfo is allClasses, Array of String is acc){
		c:baseClasses:each(action: local Function(String is baseName){
			if (acc:indexOf(search: baseName, default: -1) < 0) {
				acc:add(item: baseName);
				allClasses:each(action: local Function(ClassInfo is cand){
					if (cand:name == baseName) {
						self:collectAncestors(c: cand, allClasses: allClasses, acc: acc);
					}
				});
			}
		});
	}

	## Emits the RTTI class-hierarchy function.
	##
	## @param classes: Program classes.
	## @return: C source text.
	Function of String is generateTypeHierarchy(Array of ClassInfo is classes){
		local String is out: "/* RTTI Class Hierarchy */\n";
		out: out . "static bool spec_is_subclass_of(const char* actual, const char* target) {\n";
		out: out . "    if (!actual || !target) return false;\n";
		out: out . "    if (strcmp(actual, target) == 0) return true;\n";
		out: out . "    if (strcmp(target, \"Any\") == 0 || strcmp(target, \"Stringable\") == 0) return true;\n";
		classes:each(action: local Function(ClassInfo is c){
			if (!self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader()) {
				local Array of String is ancestors: [];
				self:collectAncestors(c: c, allClasses: classes, acc: ancestors);
				if (ancestors:length() > 0) {
					out: out . '    if (strcmp(actual, "' . c:name . "\") == 0) {\n";
					out: out . '        return ';
					local Boolean is firstA: true;
					ancestors:each(action: local Function(String is aName){
						if (!firstA) { out: out . ' || '; }
						out: out . '(strcmp(target, "' . aName . '") == 0)';
						firstA: false;
					});
					out: out . ";\n    }\n";
				}
			}
		});
		out: out . "    return false;\n}\n\n";
		return out;
	}

	## Emits virtual method tables for emission-visible classes.
	##
	## @param classes: Program classes.
	## @return: C source text.
	Function of String is generateVTables(Array of ClassInfo is classes){
		local String is out: "/* Virtual Method Tables */\n";
		if (self:methodSlotCount == 0) {
			return out;
		}
		classes:each(action: local Function(ClassInfo is c){
			if (!self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader()) {
				out: out . 'static void* ' . c:name . '_vtable[' . self:methodSlotCount . "] = {\n";
				local Int is slot: 0;
				While:condition(
					evaluate: local Function of Boolean(){
						return slot < self:methodSlotCount;
					},
					iteration: local Function of Boolean(){
						local String is mName: self:slotNames:get(index: slot);
						local String is implCls: self:findMethodImplementingClass(className: c:name, methodName: mName, paramCount: -1);
						if (slot > 0) {
							out: out . ",\n";
						}
						if (implCls == '') {
							out: out . '    (void*)0';
						} else {
							out: out . '    (void*)' . implCls . '_' . mName;
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

	## Emits constructors: destroy (ARC release per field) and new (alloc +
	## vtable + field initializers).
	##
	## @param classes: Program classes.
	## @return: C source text.
	Function of String is generateConstructors(Array of ClassInfo is classes){
		local String is out: "/* Constructor Implementations */\n";

		classes:each(action: local Function(ClassInfo is c){
			if (!self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader()) {
				self:currentClassName: c:name;
				self:fieldTypes: Map:init();
				local Array of Member is allFields: [];
				self:declGen:collectStructFields(c: c, allClasses: classes, acc: allFields);
				allFields:each(action: local Function(Member is f){
					self:fieldTypes:set(key: f:name, value: self:formatTypeString(t: f:memberType));
				});

				out: out . 'void ' . c:name . "_destroy(void* self_ptr) {\n";
				out: out . '    ' . c:name . '* self = (' . c:name . "*)self_ptr;\n";
				out: out . "    if (!self) return;\n";
				allFields:each(action: local Function(Member is m){
					local String is ft: m:memberType:name;
					if (self:isArcType(typeName: ft)) {
						out: out . '    if (self->' . self:utils:cIdent(name: m:name) . ') { spec_release((void*)self->' . self:utils:cIdent(name: m:name) . '); self->' . self:utils:cIdent(name: m:name) . " = NULL; }\n";
					}
				});
				out: out . "}\n\n";

				out: out . c:name . '* ' . c:name . "_new(void) {\n";
				out: out . '    ' . c:name . '* self = (' . c:name . '*)spec_alloc(sizeof(' . c:name . '), ' . c:name . "_destroy);\n";
				out: out . '    self->_type_name = "' . c:name . "\";\n";
				if (self:methodSlotCount > 0) {
					out: out . '    self->_vtable = ' . c:name . "_vtable;\n";
				}
				allFields:each(action: local Function(Member is m){
					if (m:hasInit) {
						local Boolean is savedArgFi: self:argMode;
						self:argMode: false;
						local String is fieldInitC: self:generateExpression(expr: m:initExpr);
						self:argMode: savedArgFi;
						local String is ftn: m:memberType:name;
						if (self:isArcType(typeName: ftn)) {
							fieldInitC: '(' . self:cTypeFor(typeName: ftn) . ')spec_retain((void*)(' . fieldInitC . '))';
						}
						out: out . '    self->' . self:utils:cIdent(name: m:name) . ' = ' . fieldInitC . ";\n";
					}
				});
				out: out . "    return self;\n}\n\n";
			}
		});
		return out;
	}
	## Inlines an anonymous-function callback over an Array as a C loop
	## (each/filter/count/any/map). The fossil inlined these to give the
	## body direct access to enclosing locals; the port keeps that.
	##
	## @param mode: each | filter | count | any | map.
	## @param targetC: Generated C for the array.
	## @param fnExpr: The ANON_FN argument.
	## @return: C statement expression, or '0'.
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
			self:localVars:set(key: p:name, value: self:formatTypeString(t: p:paramType));
			local String is pCType: self:cTypeFor(typeName: p:paramType:name);
			local String is pRaw: '(' . pCType . ')(intptr_t)_a_' . id . '->items[_i_' . id . ']';
			paramDecl: '        ' . pCType . ' ' . self:utils:cIdent(name: p:name) . ' = ' . pRaw . ";\n";
		}

		local String is bodyC: '';
		fnExpr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});
		bodyC: bodyC . self:scopeReleases(stmts: fnExpr:anonBody);

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
				local Parameter is p0: fnExpr:anonParams:get(index: 0);
				local String is pName: p0:paramType:name;
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
			local String is retCType: self:cTypeFor(typeName: fnExpr:anonReturnType:name);
			if (retCType == 'void') { retCType: 'void*'; }
			self:inlineReturnArc: retCType:charAt(index: retCType:length() - 1, default: '') == '*';
			local String is outNewC: 'spec_array_new()';
			if (self:isArcType(typeName: fnExpr:anonReturnType:name)) {
				outNewC: 'spec_array_new_object()';
			} else if (fnExpr:anonReturnType:name == 'String') {
				outNewC: 'spec_array_new_string()';
			}
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; SpecArray* ' . outVar . ' = ' . outNewC . '; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . '        ' . retCType . ' ' . predVar . " = 0;\n        do {\n" . bodyC . "        } while (0);\n        spec_array_add(" . outVar . ', (void*)(intptr_t)(' . predVar . "));\n    } } " . outVar . '; })';
			return out;
		}
		return '0';
	}

	## Inlines a fold over an Array: accumulator threading with the anon
	## function's body as the loop body. Params: (acc, item).
	##
	## @param targetC: Generated C for the array.
	## @param initExpr: The initial accumulator expression.
	## @param fnExpr: The ANON_FN argument.
	## @return: C statement expression.
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
		local String is arrVar: '_a_' . id;
		local String is idxVar: '_i_' . id;

		local String is initC: self:generateExpression(expr: initExpr);
		local String is accTypeName: self:inferTargetType(expr: initExpr);
		if (accTypeName == '' && fnExpr:anonReturnType:name != 'Void' && fnExpr:anonReturnType:name != 'void') {
			accTypeName: fnExpr:anonReturnType:name;
		}
		local String is accCType: self:cTypeFor(typeName: accTypeName);
		if (accCType == 'void') { accCType: 'long long'; }

		self:inlineReturnVar: accVar;
		self:inlineReturnLabel: 'break';
		local Boolean is savedArc: self:inlineReturnArc;
		self:inlineReturnArc: accCType:charAt(index: accCType:length() - 1, default: '') == '*';

		local String is paramDecl: '';
		if (fnExpr:anonParams:length() >= 1) {
			local Parameter is p0: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p0:name, value: accTypeName);
			paramDecl: paramDecl . '        ' . accCType . ' ' . self:utils:cIdent(name: p0:name) . ' = ' . accVar . ";\n";
		}
		if (fnExpr:anonParams:length() >= 2) {
			local Parameter is p1: fnExpr:anonParams:get(index: 1);
			self:localVars:set(key: p1:name, value: self:formatTypeString(t: p1:paramType));
			local String is p1CType: self:cTypeFor(typeName: p1:paramType:name);
			local String is p1Raw: '(' . p1CType . ')(intptr_t)' . arrVar . '->items[' . idxVar . ']';
			paramDecl: paramDecl . '        ' . p1CType . ' ' . self:utils:cIdent(name: p1:name) . ' = ' . p1Raw . ";\n";
		}

		local String is bodyC: '';
		fnExpr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});
		bodyC: bodyC . self:scopeReleases(stmts: fnExpr:anonBody);

		self:localVars: savedVars;
		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;
		self:inlineReturnArc: savedArc;

		local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; ' . accCType . ' ' . accVar . ' = ' . initC . '; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
		out: out . paramDecl . "        do {\n" . bodyC . "        } while (0);\n    } } " . accVar . '; })';
		return out;
	}

	## Inlines a Map:each iteration: key/value unpacked per bucket entry.
	##
	## @param targetC: Generated C for the map.
	## @param fnExpr: The ANON_FN argument (key, value).
	## @return: C statement expression.
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
			self:localVars:set(key: p0:name, value: 'String');
			paramDecl: paramDecl . '            String ' . self:utils:cIdent(name: p0:name) . ' = spec_string_from_chars(' . eVar . "->key);\n";
		}
		if (fnExpr:anonParams:length() >= 2) {
			local Parameter is p1: fnExpr:anonParams:get(index: 1);
			self:localVars:set(key: p1:name, value: self:formatTypeString(t: p1:paramType));
			local String is p1CType: self:cTypeFor(typeName: p1:paramType:name);
			local String is p1Raw: '(' . p1CType . ')(intptr_t)' . eVar . '->value';
			if (p1:paramType:name == 'String') {
				p1Raw: 'spec_string_from_chars((const char*)' . eVar . '->value)';
			}
			paramDecl: paramDecl . '            ' . p1CType . ' ' . self:utils:cIdent(name: p1:name) . ' = ' . p1Raw . ";\n";
		}

		local String is bodyC: '';
		fnExpr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});
		bodyC: bodyC . self:scopeReleases(stmts: fnExpr:anonBody);

		self:localVars: savedVars;
		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is out: '({ SpecMap* ' . mapVar . ' = ' . targetC . '; if (' . mapVar . ') { for (size_t ' . bVar . ' = 0; ' . bVar . ' < SPEC_MAP_BUCKETS; ' . bVar . '++) { for (SpecMapEntry* ' . eVar . ' = ' . mapVar . '->buckets[' . bVar . ']; ' . eVar . '; ' . eVar . ' = ' . eVar . "->next) {\n";
		out: out . paramDecl . "            do {\n" . bodyC . "            } while (0);\n        } } } })";
		return out;
	}

	## Inlines a While:condition predicate loop: evaluate/iteration anon
	## function bodies become the loop's condition and step.
	##
	## @param evalExpr: The evaluate ANON_FN.
	## @param iterExpr: The iteration ANON_FN.
	## @return: C statement expression.
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
		evalBodyC: evalBodyC . self:scopeReleases(stmts: evalExpr:anonBody);

		self:inlineReturnVar: '';
		self:inlineReturnLabel: 'break';
		local String is iterBodyC: '';
		iterExpr:anonBody:each(action: local Function(Statement is s){
			iterBodyC: iterBodyC . self:generateStatement(stmt: s);
		});
		iterBodyC: iterBodyC . self:scopeReleases(stmts: iterExpr:anonBody);

		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is out: "({ while (1) {\n        bool " . evVar . " = false;\n        do {\n" . evalBodyC . "        } while (0);\n        if (!" . evVar . ") break;\n        do {\n" . iterBodyC . "        } while (0);\n    } })";
		return out;
	}

	## Scans a member list for a field by name.
	Class of Loop is FieldMemberLoop{
		local Array of Member is members;
		local String is fieldName;
		local Int is idx: 0;
		local Member is res;
		local Boolean is found: false;

		replace Function is init(Array of Member is members, String is fieldName){
			self:members: members;
			self:fieldName: fieldName;
			self:idx: 0;
			self:found: false;
		}

		replace Function of Boolean is evaluate(){
			return !self:found && self:idx < self:members:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (m:kind == MemberKind:FIELD && m:name == self:fieldName) {
				self:res: m;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	## Scans a member list for a method by name.
	Class of Loop is MethodMemberLoop{
		local Array of Member is members;
		local String is methodName;
		local Int is idx: 0;
		local Member is res;
		local Boolean is found: false;

		replace Function is init(Array of Member is members, String is methodName){
			self:members: members;
			self:methodName: methodName;
			self:idx: 0;
			self:found: false;
		}

		replace Function of Boolean is evaluate(){
			return !self:found && self:idx < self:members:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (m:kind == MemberKind:METHOD && m:name == self:methodName) {
				self:res: m;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	## Scans the program registry for a class by name.
	Class of Loop is GenClassSearchLoop{
		local Array of ClassInfo is list;
		local String is target;
		local Int is idx: 0;
		local ClassInfo is res;
		local Boolean is found: false;

		replace Function is init(Array of ClassInfo is list, String is target){
			self:list: list;
			self:target: target;
			self:idx: 0;
			self:found: false;
		}

		replace Function of Boolean is evaluate(){
			return !self:found && self:idx < self:list:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			local ClassInfo is cand: self:list:get(index: self:idx);
			self:idx: self:idx + 1;
			if (cand:name == self:target) {
				self:res: cand;
				self:found: true;
				return false;
			}
			# Qualified targets ('base:sysinternal:Buf'): namespace joined
			# with ':' plus the class name must equal the target.
			if (self:target:contains(needle: ':')) {
				local String is candQ: cand:namespaceJoined() . ':' . cand:name;
				if (candQ == self:target) {
					self:res: cand;
					self:found: true;
					return false;
				}
			}
			return true;
		}
	}
}
