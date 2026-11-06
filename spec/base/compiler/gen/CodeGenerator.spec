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

	## Sets the declared type for the container literal being generated.
	##
	## @param t: The declared container type.
	Function is setContainerHint(String is t){
		self:containerHint: t;
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
		self:programClasses: classes;
		self:allClassNames: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();
		self:allTaggedEnums: Map:init();
		classes:each(action: local Function(ClassInfo is c){
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
		if (typeName:contains(needle: ':')) {
			local Array of String is parts: typeName:split(delimiter: ':');
			typeName: parts:get(index: 0);
		}
		if (self:allEnumNames:has(key: typeName) && !self:allTaggedEnums:has(key: typeName)) {
			return false;
		}
		if (self:allTaggedEnums:has(key: typeName)) {
			return true;
		}
		if (typeName:startsWith(prefix: 'Array') || typeName:startsWith(prefix: 'Map') || typeName:startsWith(prefix: 'List') || typeName:startsWith(prefix: 'Function') || typeName == 'LoopControl') {
			return true;
		}
		if (self:allClassNames:has(key: typeName)) {
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
			local String is ret: self:lookupMethodReturnType(className: targetType, methodName: expr:methodName);
			if (ret == '' || self:isVoidType(t: ret)) {
				return targetType;
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

	## Decides whether an expression renders as a C string directly (no
	## spec_buf_to_cstring wrap needed).
	##
	## @param expr: The expression node.
	## @param exprC: Its generated C.
	## @return: true when the C is already a C string.
	Function of Boolean is isStringExpr(Expression is expr, String is exprC){
		local ExpressionKind is kind: expr:kind;
		if (kind == ExpressionKind:STRING) {
			return true;
		}
		if (kind == ExpressionKind:IDENT) {
			return false;
		}
		if (kind == ExpressionKind:CALL) {
			# toString-family calls return String (SpecBuf*).
			return false;
		}
		if (exprC:startsWith(prefix: 'spec_string_') || exprC:startsWith(prefix: 'spec_buf_')) {
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
			return true;
		}
	}
}
