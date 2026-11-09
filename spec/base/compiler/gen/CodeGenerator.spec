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
		['base', 'compiler', 'ast', Type],
		['base', 'sys', as Conditional()],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', WhenArm],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', WellKnown],
		['base', 'compiler', 'checker', 'loops', ClassSearchLoop],
		['base', 'compiler', 'gen', CBackendUtils],
		['base', 'compiler', 'gen', EmissionPolicy],
		['base', 'compiler', 'gen', DeclarationGenerator],
		['base', 'compiler', 'gen', BuiltinCallGenerator],
		['base', 'compiler', 'gen', RuntimePrelude],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'iterator', as Loops()],
		['base', 'sys', as Buf()]
,
		['base', 'compiler', 'ast', StatementKind]
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

	## FUNCTIONS.md Part IV memory discipline: the active method-level
	## cleanup label — returns funnel through it so the scope-end releases
	## run on every exit path, not only the fall-through one.
	local String is cleanupLabel: '';

	## The method's return variable (set when the return type is ARC or a
	## scalar; '' for void methods).
	local String is cleanupRetVar: '';

	## Per-method cleanup-label counter (labels are function-scoped).
	local Int is cleanupCounter: 0;

	## Locals excluded from the scope-end releases — the closure write-backs
	## transfer their ownership to the env, so releasing them here would
	## drop a ref the env owns.
	local Map of String to String is releaseExclusions: Map:init();

	## FUNCTIONS.md Part IV memory discipline: the top-level ARC locals
	## hoisted to zero-initialized declarations for the active funnel — a
	## goto must never jump over an initializer the cleanup releases.
	local Map of String to String is hoistedLocals: Map:init();

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
		self:cleanupLabel: '';
		self:cleanupRetVar: '';
		self:cleanupCounter: 0;
		self:releaseExclusions: Map:init();
		self:hoistedLocals: Map:init();
		self:localScopeVars: Map:init();
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
			Conditional:if(check: { !self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader() }, then: {
				c:members:each(action: local Function(Member is m){
					Conditional:if(check: { m:kind == MemberKind:METHOD }, then: {
						Conditional:if(check: { self:methodSlots:has(key: m:name) }, then: {
							self:overriddenMethods:set(key: m:name, value: 'true');
						}, else: {
							self:methodSlots:set(key: m:name, value: '' . self:methodSlotCount);
							self:slotNames:add(item: m:name);
							self:methodSlotCount: self:methodSlotCount + 1;
						});
					});
				});
			});
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
			# FUNCTIONS.md Part IV IV.2c: the nested classes register under
			# their qualified identity too — and under the C symbol form,
			# so the constructor path recognizes the symbol-spelled targets
			# that emitPath produces.
			Conditional:if(check: { c:outerName != '' }, then: {
				self:allClassNames:set(key: c:qualifiedName(), value: 'true');
				self:allClassNames:set(key: self:utils:cIdent(name: c:qualifiedName()), value: 'true');
			});
			Conditional:if(check: { c:baseClass == self:names:enumHeader() }, then: {
				self:allEnumNames:set(key: c:name, value: 'true');
				c:members:each(action: local Function(Member is m){
					# The namespace declaration is metadata, not a variant.
					Conditional:if(check: { m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, then: {
						return;
					});
					self:allEnumVariants:set(key: m:name, value: c:name);
					# Payload variants make the enum a tagged union.
					Conditional:if(check: { m:params:length() > 0 }, then: {
						self:allTaggedEnums:set(key: c:name, value: 'true');
					});
					Conditional:if(check: { m:memberType:name == Primitive:STRING:value() }, then: {
						self:allStringBackedEnums:set(key: c:name, value: 'true');
					});
				});
			});
		});
	}

	## True when the type name is ARC-managed (ownership transfers at
	## assignments and calls).
	##
	## @param typeName: Type name.
	## @return: true when ARC-managed.
	Function of Boolean is isArcType(String is typeName){
		Conditional:if(check: { typeName == '' }, then: {
			return false;
		});
		# String is primitive-spelled but ARC-managed; test it first.
		Conditional:if(check: { typeName == 'String' }, then: {
			return true;
		});
		Conditional:if(check: { self:isPrimitiveName(t: typeName) }, then: {
			return false;
		});
		# Base-name extraction goes through a local: parameters are borrows,
		# and reassigning one would release the caller's argument.
		local String is baseName: typeName;
		Conditional:if(check: { baseName:contains(needle: ':') }, then: {
			local Array of String is parts: baseName:split(delimiter: ':');
			baseName: parts:get(index: 0);
		});
		Conditional:if(check: { self:allEnumNames:has(key: baseName) && !self:allTaggedEnums:has(key: baseName) }, then: {
			return false;
		});
		Conditional:if(check: { self:allTaggedEnums:has(key: baseName) }, then: {
			return true;
		});
		Conditional:if(check: { baseName:startsWith(prefix: 'Array') || baseName:startsWith(prefix: 'Map') || baseName:startsWith(prefix: 'List') || baseName:startsWith(prefix: 'Function') || baseName == 'LoopControl' }, then: {
			return true;
		});
		Conditional:if(check: { self:allClassNames:has(key: baseName) }, then: {
			return true;
		});
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
		Conditional:if(check: { elem == '' }, then: {
			return 'none';
		});
		Conditional:if(check: { elem == Primitive:ANY:value() }, then: {
			return 'none';
		});
		Conditional:if(check: { elem == 'Byte' }, then: {
			return 'byte';
		});
		Conditional:if(check: { self:isArcType(typeName: elem) }, then: {
			return 'object';
		});
		return 'none';
	}

	## Extracts a container's element/value type from either spelling
	## ('Array of X' / 'Array:X', 'Map of K to V' / 'Map:K:V').
	##
	## @param t: Container type name.
	## @return: The element/value type name, or ''.
	Function of String is elemOfType(String is t){
		Conditional:if(check: { t:startsWith(prefix: 'Array of ') }, then: {
			return t:substring(start: 9, end: t:length());
		});
		Conditional:if(check: { t:startsWith(prefix: 'Array:') }, then: {
			return t:substring(start: 6, end: t:length());
		});
		Conditional:if(check: { t:startsWith(prefix: 'List of ') }, then: {
			return t:substring(start: 8, end: t:length());
		});
		Conditional:if(check: { t:startsWith(prefix: 'List:') }, then: {
			return t:substring(start: 5, end: t:length());
		});
		Conditional:if(check: { t:startsWith(prefix: 'Map of ') }, then: {
			local String is rest: t:substring(start: 7, end: t:length());
			local Int is toIdx: rest:indexOf(search: ' to ', default: -1);
			Conditional:if(check: { toIdx >= 0 }, then: {
				return rest:substring(start: toIdx + 4, end: rest:length());
			});
			return '';
		});
		Conditional:if(check: { t:startsWith(prefix: 'Map:') }, then: {
			local String is rest: t:substring(start: 4, end: t:length());
			local Int is colonIdx: rest:indexOf(search: ':', default: -1);
			Conditional:if(check: { colonIdx >= 0 }, then: {
				return rest:substring(start: colonIdx + 1, end: rest:length());
			});
			return '';
		});
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

	## True when the class currently being generated instance-imports
	## [className] via an as-form using entry (INSTANCE.md §2.1) — its
	## class-name calls dispatch on the owned (elided) instance.
	##
	## @param className: Receiver class name.
	## @return: true when instance-imported by the current class.
	Function of Boolean is isAsImportedReceiver(String is className){
		return self:genImportsAsAnywhere(clsName: self:currentClassName, targetName: className, hops: 0);
	}

	## Recursive import search over the ancestor lattice (the emitted
	## struct flattens ancestors, so the field is reachable from here).
	##
	## @param clsName: Class being visited.
	## @param targetName: The imported class name sought.
	## @param hops: Recursion budget guard.
	## @return: true when found on this class or an ancestor.
	Function of Boolean is genImportsAsAnywhere(String is clsName, String is targetName, Int is hops){
		Conditional:if(check: { clsName == '' || clsName == 'Any' || hops >= 64 }, then: {
			return false;
		});
		local ClassInfo is cls: self:findClass(name: clsName);
		Conditional:if(check: { cls:name == '' }, then: {
			return false;
		});
		Conditional:if(check: { cls:instanceImportsAs(name: targetName) }, then: {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:genImportsAsAnywhere(clsName: baseName, targetName: targetName, hops: hops + 1) }, then: {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## True when [cls] declares real fields (metadata pseudo-members
	## excluded) — field-ful as-imports dispatch through their synthetic
	## hidden field instead of the elided NULL path (INSTANCE.md §2.4).
	##
	## @param cls: The imported class.
	## @return: true when field-ful.
	Function of Boolean is isFieldFulClass(ClassInfo is cls){
		local Boolean is found: false;
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:kind == MemberKind:FIELD && m:name != 'using' && m:name != 'namespace' && m:name != 'castable' }, then: {
				found: true;
			});
		});
		return found;
	}

	## FUNCTIONS.md §I.2: the 0-based overload position of [method]
	## within its class's same-name METHOD group (identity compare).
	##
	## @param classDef: The declaring class.
	## @param method: The member.
	## @return: The overload index.
	Function of Int is overloadIndexOf(ClassInfo is classDef, Member is method){
		local Int is idx: 0;
		local Int is hit: 0;
		classDef:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == method:name }, then: {
				Conditional:if(check: { m == method }, then: {
					hit: idx;
				});
				idx: idx + 1;
			});
		});
		return hit;
	}

	## The C symbol for a method definition or call: Class_method, with a
	## declaration-order suffix for overloads (FUNCTIONS.md §I.4).
	##
	## @param className: The declaring class name.
	## @param methodName: The method name.
	## @param idx: The overload index.
	## @return: The C symbol.
	Function of String is overloadSymbol(String is className, String is methodName, Int is idx){
		# FUNCTIONS.md Part IV IV.2c: the symbol base qualifies for nested
		# classes — the funnel resolves the class and derives the C symbol
		# from the qualified name, so the definitions and the call sites
		# agree.
		local String is symBase: className;
		local ClassInfo is symCls: self:findClass(name: className);
		Conditional:if(check: { symCls:name != '' }, then: {
			symBase: self:utils:cIdent(name: symCls:qualifiedName());
		});
		Conditional:if(check: { idx > 0 }, then: {
			return symBase . '_' . methodName . '_' . (idx + 1) . '';
		});
		return symBase . '_' . methodName;
	}

	## FUNCTIONS.md Part IV IV.2c: the member-lookup root for a (possibly
	## qualified) receiver type — the qualified nested-class reference
	## resolves to the inner class; container forms keep the bare root.
	##
	## @param className: The receiver type string.
	## @return: The class name to start the member walk from.
	Function of String is memberLookupRootGen(String is className){
		local String is root: className:split(delimiter: ':'):get(index: 0);
		Conditional:if(check: { className:contains(needle: ':') }, then: {
			local ClassInfo is qCls: self:findClass(name: className);
			Conditional:if(check: { qCls:name != '' && qCls:qualifiedName() == className }, then: {
				root: className;
			});
		});
		return root;
	}

	## FUNCTIONS.md §I.2: the stamped member for a call — the idx-th
	## same-name METHOD member at the nearest declaring ancestor (all
	## parents walked; idx below zero resolves as the first).
	##
	## @param className: The receiver base class name.
	## @param methodName: The called member's name.
	## @param idx: The stamped overload index.
	## @return: The member, or an empty node when absent.
	Function of Member is lookupOverloadedMemberGen(String is className, String is methodName, Int is idx){
		local Member is none: Member:init(kind: MemberKind:FIELD);
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		self:collectOverloadGroupGen(className: self:memberLookupRootGen(className: className), methodName: methodName, hops: 0, acc: group, ownerAcc: ownerAcc);
		Conditional:if(check: { group:length() == 0 }, then: {
			return none;
		});
		local Int is use: idx;
		Conditional:if(check: { use < 0 }, then: {
			use: 0;
		});
		Conditional:if(check: { use >= group:length() }, then: {
			use: group:length() - 1;
		});
		local Member is cand: group:get(index: use);
		return cand;
	}

	## The name of the class declaring the stamped overload (empty when
	## the name is undeclared).
	##
	## @param className: The receiver base class name.
	## @param methodName: The called member's name.
	## @param idx: The stamped overload index.
	## @return: The declaring class name, or ''.
	Function of String is overloadOwnerNameGen(String is className, String is methodName, Int is idx){
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		self:collectOverloadGroupGen(className: self:memberLookupRootGen(className: className), methodName: methodName, hops: 0, acc: group, ownerAcc: ownerAcc);
		Conditional:if(check: { group:length() == 0 || ownerAcc:length() == 0 }, then: {
			return '';
		});
		local String is owner: ownerAcc:get(index: 0);
		return owner;
	}

	## Recursive overload-group collection (nearest declaring ancestor,
	## all parents walked, first subtree wins).
	##
	## @param className: Class being visited.
	## @param methodName: The member name.
	## @param hops: Recursion budget guard.
	## @param acc: The collected group.
	Function is collectOverloadGroupGen(String is className, String is methodName, Int is hops, Array of Member is acc, Array of String is ownerAcc){
		Conditional:if(check: { ownerAcc:length() > 0 || acc:length() > 0 || className == '' || className == 'Any' || hops >= 64 }, then: {
			return;
		});
		# IV.2c: the qualified nested-class name walks the inner class
		# itself; container forms don't resolve qualified and fall back to
		# the bare root.
		local ClassInfo is cls: self:findClass(name: className);
		Conditional:if(check: { cls:name == '' }, then: {
			cls: self:findClass(name: className:split(delimiter: ':'):get(index: 0));
		});
		Conditional:if(check: { cls:name == '' }, then: {
			return;
		});
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == methodName }, then: {
				acc:add(item: m);
			});
		});
		Conditional:if(check: { acc:length() > 0 }, then: {
			# IV.2c: the owner's qualified identity — the bare name of a
			# nested class is not unique across outers.
			ownerAcc:add(item: cls:qualifiedName());
			return;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			self:collectOverloadGroupGen(className: baseName, methodName: methodName, hops: hops + 1, acc: acc, ownerAcc: ownerAcc);
		});
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
		Conditional:if(check: { typeName == 'String' }, then: {
			Conditional:if(check: { claims }, then: {
				return valueC;
			});
			return 'spec_construct_string(' . valueC . ')';
		});
		Conditional:if(check: { typeName == 'Byte' }, then: {
			return 'spec_construct_byte((long long)(' . valueC . '))';
		});
		Conditional:if(check: { typeName == Primitive:INT:value() || typeName == 'Float' || typeName == 'Boolean' }, then: {
			return valueC;
		});
		Conditional:if(check: { self:isArcType(typeName: typeName) }, then: {
			Conditional:if(check: { claims }, then: {
				return '(' . cType . ')((' . valueC . '))';
			});
			return '(' . cType . ')spec_retain((void*)(' . valueC . '))';
		});
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
		Conditional:if(check: { curCls:typeParams:indexOf(search: typeName, default: -1) >= 0 }, then: {
			return 'void*';
		});
		local String is containerC: self:utils:cTypeFor(typeName: typeName);
		Conditional:if(check: { containerC:startsWith(prefix: 'Spec') }, then: {
			return containerC;
		});
		local String is base: typeName;
		Conditional:if(check: { base:contains(needle: ':') }, then: {
			local Array of String is parts: base:split(delimiter: ':');
			base: parts:get(index: 0);
		});
		Conditional:if(check: { self:allTaggedEnums:has(key: base) }, then: {
			return base . '*';
		});
		Conditional:if(check: { self:allEnumNames:has(key: base) }, then: {
			return base;
		});
		return containerC;
	}

	## Formats a type FOR LOCAL/PARAM REGISTRATION: Function types stay
	## Function-prefixed ('Function:Int') so Function-typed locals dispatch
	## as closures. (Plain formatTypeString unwraps to the return type,
	## which is right for C types but wrong for scope maps.)
	##
	## @param t: Type descriptor.
	## @return: Scope-map type name.
	Function of String is formatVarTypeString(Type is t){
		Conditional:if(check: { Primitive:of(t:name) == Primitive:FUNCTION }, then: {
			Conditional:if(check: { t:params:length() > 0 }, then: {
				local Type is ret: t:params:get(index: 0);
				return 'Function:' . self:formatTypeString(t: ret);
			});
			return 'Function';
		});
		return self:formatTypeString(t: t);
	}

	## Reconstructs a type's full spelling INCLUDING generic arguments:
	## Type(name='Box', params=['Int']) -> 'Box of Int' (the parser stores
	## generics on the params list, and scope maps need the whole form for
	## of-form resolution downstream).
	##
	## @param name: The base type name.
	## @param params: The generic arguments.
	## @return: The full type spelling.
	Function of String is fullTypeSpelling(String is name, Array of Type is params){
		Conditional:if(check: { params:length() == 0 }, then: {
			return name;
		});
		Conditional:if(check: { name == 'Map' && params:length() == 2 }, then: {
			return 'Map of ' . self:formatTypeString(t: params:get(index: 0)) . ' to ' . self:formatTypeString(t: params:get(index: 1));
		});
		local String is out: name;
		params:each(action: local Function(Type is pt){
			out: out . ' of ' . self:formatTypeString(t: pt);
		});
		return out;
	}

	## Resolves a method's return type to its C type: enum returns pass by
	## value (the registry-aware cTypeFor), Function types unwrap to their
	## return type's C type.
	##
	## @param t: Type descriptor.
	## @return: C type string.
	Function of String is resolveReturnType(Type is t){
		Conditional:if(check: { Primitive:of(t:name) == Primitive:FUNCTION }, then: {
			Conditional:if(check: { t:params:length() > 0 }, then: {
				local Type is ret: t:params:get(index: 0);
				return self:cTypeFor(typeName: ret:name);
			});
			return 'void';
		});
		return self:cTypeFor(typeName: t:name);
	}

	## Formats a [Type] descriptor into the internal colon form.
	##
	## @param t: Type descriptor.
	## @return: Type name string.
	Function of String is formatTypeString(Type is t){
		local String is baseName: t:name;
		Conditional:if(check: { Primitive:of(baseName) == Primitive:FUNCTION }, then: {
			Conditional:if(check: { t:params:length() > 0 }, then: {
				local Type is ret: t:params:get(index: 0);
				return self:formatTypeString(t: ret);
			});
			return 'void';
		});
		Conditional:if(check: { t:params:length() == 1 }, then: {
			local Type is p0: t:params:get(index: 0);
			return baseName . ':' . self:formatTypeString(t: p0);
		});
		Conditional:if(check: { t:params:length() >= 2 }, then: {
			local Type is p0: t:params:get(index: 0);
			local Type is p1: t:params:get(index: 1);
			return baseName . ':' . self:formatTypeString(t: p0) . ':' . self:formatTypeString(t: p1);
		});
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
		Conditional:if(check: { tps:length() == 0 || typeArgs:length() == 0 }, then: {
			return rawType;
		});
		local Int is idx: tps:indexOf(search: rawType, default: -1);
		Conditional:if(check: { idx >= 0 && idx < typeArgs:length() }, then: {
			return typeArgs:get(index: idx);
		});
		Conditional:if(check: { rawType:startsWith(prefix: 'Array:') && rawType:length() > 6 }, then: {
			local String is elem: rawType:substring(start: 6, end: rawType:length());
			local Int is eIdx: tps:indexOf(search: elem, default: -1);
			Conditional:if(check: { eIdx >= 0 && eIdx < typeArgs:length() }, then: {
				return 'Array:' . typeArgs:get(index: eIdx);
			});
		});
		return rawType;
	}

	## Finds a class descriptor by name.
	##
	## @param name: Target class name.
	## @return: The descriptor, or an unnamed one when absent.
	Function of ClassInfo is findClass(String is name){
		local ClassSearchLoop is s: ClassSearchLoop:init(list: self:programClasses, target: name);
		Loops:run(loop: s);
		Conditional:if(check: { s:found }, then: {
			return s:res;
		});
		# FUNCTIONS.md Part IV IV.2c: the qualified nested-class reference —
		# 'Outer:Inner' resolves the class whose qualified identity matches.
		Conditional:if(check: { name:contains(needle: ':') }, then: {
			local ClassInfo is qMatch: ClassInfo:init(name: '', baseClass: '', members: []);
			self:programClasses:each(action: local Function(ClassInfo is c){
				Conditional:if(check: { qMatch:name == '' && c:qualifiedName() == name }, then: {
					qMatch: c;
				});
			});
			Conditional:if(check: { qMatch:name != '' }, then: {
				return qMatch;
			});
		});
		return ClassInfo:init(name: '', baseClass: '', members: []);
	}

	## Looks up a field's static type on a class and its ancestors.
	##
	## @param className: Starting class name.
	## @param fieldName: Field name.
	## @return: The field type name, or ''.
	Function of String is lookupFieldType(String is className, String is fieldName){
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return '';
		});
		local String is baseClassName: self:memberLookupRootGen(className: className);
		local Array of String is typeArgs: [];
		# The resolved qualified root absorbs the colon chain (IV.2c); bare
		# colon forms ground their segments as type arguments.
		Conditional:if(check: { baseClassName != className }, then: {
			local Array of String is parts: className:split(delimiter: ':');
			typeArgs: parts:slice(start: 1, end: parts:length());
		});
		# Of-form generic receivers ('Box of Int'): split the base and the
		# type argument so substitution can ground T.
		local Int is ofIdx: className:indexOf(search: ' of ', default: -1);
		Conditional:if(check: { ofIdx > 0 && typeArgs:length() == 0 }, then: {
			baseClassName: className:substring(start: 0, end: ofIdx);
			typeArgs:add(item: className:substring(start: ofIdx + 4, end: className:length()));
		});
		local ClassInfo is cls: self:findClass(name: baseClassName);
		Conditional:if(check: { cls:name == '' }, then: {
			return '';
		});
		local FieldMemberLoop is fl: FieldMemberLoop:init(members: cls:members, fieldName: fieldName);
		Loops:run(loop: fl);
		Conditional:if(check: { fl:found }, then: {
			local String is rawT: self:formatTypeString(t: fl:res:memberType);
			return self:substituteTypeParam(rawType: rawT, cls: cls, typeArgs: typeArgs);
		});
		local String is inherited: '';
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { inherited == '' }, then: {
				inherited: self:lookupFieldType(className: baseName, fieldName: fieldName);
			});
		});
		return inherited;
	}

	## Looks up a method's return type on a class and its ancestors.
	##
	## @param className: Starting class name.
	## @param methodName: Method name.
	## @return: The return type name, or ''.
	Function of String is lookupMethodReturnType(String is className, String is methodName){
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return '';
		});
		local String is baseClassName: self:memberLookupRootGen(className: className);
		local Array of String is typeArgs: [];
		# The resolved qualified root absorbs the colon chain (IV.2c); bare
		# colon forms ground their segments as type arguments.
		Conditional:if(check: { baseClassName != className }, then: {
			local Array of String is parts: className:split(delimiter: ':');
			typeArgs: parts:slice(start: 1, end: parts:length());
		});
		# Of-form generic receivers ('Box of Int'): split the base and the
		# type argument so substitution can ground T.
		local Int is ofIdx: className:indexOf(search: ' of ', default: -1);
		Conditional:if(check: { ofIdx > 0 && typeArgs:length() == 0 }, then: {
			baseClassName: className:substring(start: 0, end: ofIdx);
			typeArgs:add(item: className:substring(start: ofIdx + 4, end: className:length()));
		});
		Conditional:if(check: { methodName == 'init' && self:allClassNames:has(key: baseClassName) && !self:allEnumNames:has(key: baseClassName) }, then: {
			return className;
		});
		# Container element access resolves from the type string directly:
		# the generic machinery substitutes T through the loaded Array
		# declaration, which leaks raw 'T' for of-form receivers.
		Conditional:if(check: { baseClassName == 'Array' || baseClassName == 'List' || baseClassName == 'Map' || baseClassName:startsWith(prefix: 'Array') || baseClassName:startsWith(prefix: 'List') || baseClassName:startsWith(prefix: 'Map') }, then: {
			local Array of String is ctParts: className:split(delimiter: ':');
			local String is elem: '';
			Conditional:if(check: { (baseClassName == 'Array' || baseClassName:startsWith(prefix: 'Array:')) && methodName != 'length' }, then: {
				Conditional:if(check: { ctParts:length() > 1 }, then: {
					elem: ctParts:get(index: 1);
				}, else: {
					Conditional:if(check: { className:startsWith(prefix: 'Array of ') }, then: {
						elem: className:substring(start: 9, end: className:length());
					});
				});
			});
			Conditional:if(check: { baseClassName == 'List' || baseClassName:startsWith(prefix: 'List:') }, then: {
				Conditional:if(check: { ctParts:length() > 1 }, then: {
					elem: ctParts:get(index: 1);
				}, else: {
					Conditional:if(check: { className:startsWith(prefix: 'List of ') }, then: {
						elem: className:substring(start: 8, end: className:length());
					});
				});
			});
			Conditional:if(check: { methodName == 'length' }, then: {
 return Primitive:INT:value();
			});
			Conditional:if(check: { methodName == 'isEmpty' || methodName == 'has' || methodName == 'any' }, then: {
 return Primitive:BOOLEAN:value();
			});
			Conditional:if(check: { methodName == 'count' || methodName == 'indexOf' }, then: {
 return Primitive:INT:value();
			});
			Conditional:if(check: { methodName == 'getString' || methodName == 'join' }, then: {
 return Primitive:STRING:value();
			});
			Conditional:if(check: { methodName == 'getInt' }, then: {
 return Primitive:INT:value();
			});
			Conditional:if(check: { methodName == 'add' || methodName == 'set' || methodName == 'clear' || methodName == 'each' || methodName == 'push' }, then: {
 return 'void';
			});
			Conditional:if(check: { (methodName == 'get' || methodName == 'pop' || methodName == 'removeAt') && elem != '' }, then: {
				return elem;
			});
			Conditional:if(check: { methodName == 'get' && baseClassName == 'Map' }, then: {
				Conditional:if(check: { ctParts:length() > 2 }, then: {
					return ctParts:get(index: 2);
				});
				local String is rest: className;
				Conditional:if(check: { rest:startsWith(prefix: 'Map of ') }, then: {
					rest: rest:substring(start: 7, end: rest:length());
					local Int is toIdx: rest:indexOf(search: ' to ', default: -1);
					Conditional:if(check: { toIdx >= 0 }, then: {
						return rest:substring(start: toIdx + 4, end: rest:length());
					});
				});
			});
		});
		local ClassInfo is cls: self:findClass(name: baseClassName);
		Conditional:if(check: { cls:name == '' }, then: {
			# Unloaded builtin container: resolve from the builtin table so
			# concat wraps know the result type.
			Conditional:if(check: { baseClassName == 'Array' || baseClassName == 'List' || baseClassName == 'Map' || baseClassName:startsWith(prefix: 'Array') || baseClassName:startsWith(prefix: 'List') || baseClassName:startsWith(prefix: 'Map') }, then: {
				Conditional:if(check: { methodName == 'length' }, then: {
 return Primitive:INT:value();
				});
				Conditional:if(check: { methodName == 'isEmpty' || methodName == 'has' || methodName == 'any' }, then: {
 return Primitive:BOOLEAN:value();
				});
				Conditional:if(check: { methodName == 'count' || methodName == 'indexOf' }, then: {
 return Primitive:INT:value();
				});
				Conditional:if(check: { methodName == 'getString' || methodName == 'join' }, then: {
 return Primitive:STRING:value();
				});
				Conditional:if(check: { methodName == 'getInt' }, then: {
 return Primitive:INT:value();
				});
				Conditional:if(check: { methodName == 'add' || methodName == 'set' || methodName == 'clear' || methodName == 'each' || methodName == 'push' }, then: {
 return 'void';
				});
				Conditional:if(check: { methodName == 'get' || methodName == 'pop' || methodName == 'removeAt' }, then: {
					local Array of String is ta: className:split(delimiter: ':');
					Conditional:if(check: { ta:length() > 1 }, then: {
						return ta:get(index: 1);
					});
					local String is cn: className;
					Conditional:if(check: { cn:startsWith(prefix: 'Array of ') }, then: {
						return cn:substring(start: 9, end: cn:length());
					});
					Conditional:if(check: { cn:startsWith(prefix: 'List of ') }, then: {
						return cn:substring(start: 8, end: cn:length());
					});
					Conditional:if(check: { cn:startsWith(prefix: 'Map of ') }, then: {
						local String is rest: cn:substring(start: 7, end: cn:length());
						local Int is toIdx: rest:indexOf(search: ' to ', default: -1);
						Conditional:if(check: { toIdx >= 0 }, then: {
							return rest:substring(start: toIdx + 4, end: rest:length());
						});
					});
				});
			});
			return '';
		});
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:members, methodName: methodName);
		Loops:run(loop: ml);
		Conditional:if(check: { ml:found }, then: {
			local String is rawT: self:formatTypeString(t: ml:res:memberType);
			return self:substituteTypeParam(rawType: rawT, cls: cls, typeArgs: typeArgs);
		});
		local String is inherited: '';
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { inherited == '' }, then: {
				inherited: self:lookupMethodReturnType(className: baseName, methodName: methodName);
			});
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
		Loops:run(loop: fl);
		Conditional:if(check: { fl:found }, then: {
			return fl:res;
		});
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
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return '';
		});
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		# Container element access resolves from the type string directly:
		# the generic machinery substitutes T through the loaded Array
		# declaration, which leaks raw 'T' for of-form receivers.
		Conditional:if(check: { baseClassName == 'Array' || baseClassName == 'List' || baseClassName == 'Map' || baseClassName:startsWith(prefix: 'Array') || baseClassName:startsWith(prefix: 'List') || baseClassName:startsWith(prefix: 'Map') }, then: {
			local Array of String is ctParts: className:split(delimiter: ':');
			local String is elem: '';
			Conditional:if(check: { (baseClassName == 'Array' || baseClassName:startsWith(prefix: 'Array:')) && methodName != 'length' }, then: {
				Conditional:if(check: { ctParts:length() > 1 }, then: {
					elem: ctParts:get(index: 1);
				}, else: {
					Conditional:if(check: { className:startsWith(prefix: 'Array of ') }, then: {
						elem: className:substring(start: 9, end: className:length());
					});
				});
			});
			Conditional:if(check: { baseClassName == 'List' || baseClassName:startsWith(prefix: 'List:') }, then: {
				Conditional:if(check: { ctParts:length() > 1 }, then: {
					elem: ctParts:get(index: 1);
				}, else: {
					Conditional:if(check: { className:startsWith(prefix: 'List of ') }, then: {
						elem: className:substring(start: 8, end: className:length());
					});
				});
			});
			Conditional:if(check: { methodName == 'length' }, then: {
 return Primitive:INT:value();
			});
			Conditional:if(check: { methodName == 'isEmpty' || methodName == 'has' || methodName == 'any' }, then: {
 return Primitive:BOOLEAN:value();
			});
			Conditional:if(check: { methodName == 'count' || methodName == 'indexOf' }, then: {
 return Primitive:INT:value();
			});
			Conditional:if(check: { methodName == 'getString' || methodName == 'join' }, then: {
 return Primitive:STRING:value();
			});
			Conditional:if(check: { methodName == 'getInt' }, then: {
 return Primitive:INT:value();
			});
			Conditional:if(check: { methodName == 'add' || methodName == 'set' || methodName == 'clear' || methodName == 'each' || methodName == 'push' }, then: {
 return 'void';
			});
			Conditional:if(check: { (methodName == 'get' || methodName == 'pop' || methodName == 'removeAt') && elem != '' }, then: {
				return elem;
			});
			Conditional:if(check: { methodName == 'get' && baseClassName == 'Map' }, then: {
				Conditional:if(check: { ctParts:length() > 2 }, then: {
					return ctParts:get(index: 2);
				});
				local String is rest: className;
				Conditional:if(check: { rest:startsWith(prefix: 'Map of ') }, then: {
					rest: rest:substring(start: 7, end: rest:length());
					local Int is toIdx: rest:indexOf(search: ' to ', default: -1);
					Conditional:if(check: { toIdx >= 0 }, then: {
						return rest:substring(start: toIdx + 4, end: rest:length());
					});
				});
			});
		});
		local ClassInfo is cls: self:findClass(name: baseClassName);
		Conditional:if(check: { cls:name == '' }, then: {
			# Unloaded builtin container: resolve from the builtin table so
			# concat wraps know the result type.
			Conditional:if(check: { baseClassName == 'Array' || baseClassName == 'List' || baseClassName == 'Map' || baseClassName:startsWith(prefix: 'Array') || baseClassName:startsWith(prefix: 'List') || baseClassName:startsWith(prefix: 'Map') }, then: {
				Conditional:if(check: { methodName == 'length' }, then: {
 return Primitive:INT:value();
				});
				Conditional:if(check: { methodName == 'isEmpty' || methodName == 'has' || methodName == 'any' }, then: {
 return Primitive:BOOLEAN:value();
				});
				Conditional:if(check: { methodName == 'count' || methodName == 'indexOf' }, then: {
 return Primitive:INT:value();
				});
				Conditional:if(check: { methodName == 'getString' || methodName == 'join' }, then: {
 return Primitive:STRING:value();
				});
				Conditional:if(check: { methodName == 'getInt' }, then: {
 return Primitive:INT:value();
				});
				Conditional:if(check: { methodName == 'add' || methodName == 'set' || methodName == 'clear' || methodName == 'each' || methodName == 'push' }, then: {
 return 'void';
				});
				Conditional:if(check: { methodName == 'get' || methodName == 'pop' || methodName == 'removeAt' }, then: {
					local Array of String is ta: className:split(delimiter: ':');
					Conditional:if(check: { ta:length() > 1 }, then: {
						return ta:get(index: 1);
					});
					local String is cn: className;
					Conditional:if(check: { cn:startsWith(prefix: 'Array of ') }, then: {
						return cn:substring(start: 9, end: cn:length());
					});
					Conditional:if(check: { cn:startsWith(prefix: 'List of ') }, then: {
						return cn:substring(start: 8, end: cn:length());
					});
					Conditional:if(check: { cn:startsWith(prefix: 'Map of ') }, then: {
						local String is rest: cn:substring(start: 7, end: cn:length());
						local Int is toIdx: rest:indexOf(search: ' to ', default: -1);
						Conditional:if(check: { toIdx >= 0 }, then: {
							return rest:substring(start: toIdx + 4, end: rest:length());
						});
					});
				});
			});
			return '';
		});
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:members, methodName: methodName);
		Loops:run(loop: ml);
		Conditional:if(check: { ml:found }, then: {
			Conditional:if(check: { paramCount < 0 || ml:res:params:length() == paramCount }, then: {
				# FUNCTIONS.md Part IV IV.2c: the IMPLEMENTING class's symbol
				# base qualifies for nested classes — the vtable entries and
				# the definitions agree.
				return self:utils:cIdent(name: cls:qualifiedName());
			});
		});
		local String is inherited: '';
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { inherited == '' }, then: {
				inherited: self:findMethodImplementingClass(className: baseName, methodName: methodName, paramCount: paramCount);
			});
		});
		return inherited;
	}

	## Looks up a method member on a class or its ancestors.
	##
	## @param className: Starting class name.
	## @param methodName: Method name.
	## @return: The member, or an empty-named one.
	Function of Member is lookupMethodMember(String is className, String is methodName){
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return Member:init(kind: MemberKind:FIELD);
		});
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		Conditional:if(check: { cls:name == '' }, then: {
			return Member:init(kind: MemberKind:FIELD);
		});
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:members, methodName: methodName);
		Loops:run(loop: ml);
		Conditional:if(check: { ml:found }, then: {
			return ml:res;
		});
		local Member is inherited: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { inherited:name == '' }, then: {
				inherited: self:lookupMethodMember(className: baseName, methodName: methodName);
			});
		});
		return inherited;
	}

	## True when [subName] inherits from [baseName] (transitively).
	##
	## @param subName: Candidate subtype.
	## @param baseName: Candidate base type.
	## @return: Subclass relationship.
	Function of Boolean is isSubclassOf(String is subName, String is baseName){
		Conditional:if(check: { subName == '' || baseName == '' }, then: {
			return false;
		});
		Conditional:if(check: { subName == baseName }, then: {
			return true;
		});
		local ClassInfo is subCls: self:findClass(name: subName);
		Conditional:if(check: { subCls:name == '' }, then: {
			return false;
		});
		local Boolean is matched: false;
		subCls:baseClasses:each(action: local Function(String is pName){
			Conditional:if(check: { pName == baseName || self:isSubclassOf(subName: pName, baseName: baseName) }, then: {
				matched: true;
			});
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
		Conditional:if(check: { kind == ExpressionKind:IDENT }, then: {
			local String is name: expr:stringValue;
			Conditional:if(check: { name == self:names:selfIdent() }, then: {
				return self:currentClassName;
			});
			Conditional:if(check: { self:localVars:has(key: name) }, then: {
				return self:localVars:getString(key: name, default: '');
			});
			Conditional:if(check: { self:fieldTypes:has(key: name) }, then: {
				return self:fieldTypes:getString(key: name, default: '');
			});
			Conditional:if(check: { self:allEnumVariants:has(key: name) }, then: {
				return self:allEnumVariants:getString(key: name, default: '');
			});
			Conditional:if(check: { self:allClassNames:has(key: name) }, then: {
				return name;
			});
			return '';
		});
		Conditional:if(check: { kind == ExpressionKind:PATH }, then: {
			local Array of String is segs: expr:pathSegments;
			Conditional:if(check: { segs:length() == 0 }, then: {
				return '';
			});
			local String is root: segs:get(index: 0);
			local String is rootType: '';
			Conditional:if(check: { root == self:names:selfIdent() }, then: {
				rootType: self:currentClassName;
			}, else: {
				Conditional:if(check: { self:localVars:has(key: root) }, then: {
					rootType: self:localVars:getString(key: root, default: '');
				}, else: {
					Conditional:if(check: { self:fieldTypes:has(key: root) }, then: {
						rootType: self:fieldTypes:getString(key: root, default: '');
					}, else: {
						Conditional:if(check: { self:allEnumNames:has(key: root) }, then: {
							return root;
						}, else: {
							Conditional:if(check: { self:allClassNames:has(key: root) }, then: {
								return root;
							});
						});
					});
				});
			});
			Conditional:if(check: { rootType == '' }, then: {
				return rootType;
			});
			local Int is idx: 1;
			Loops:loop(
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
		});
		Conditional:if(check: { kind == ExpressionKind:CALL }, then: {
			local String is targetType: self:inferTargetType(expr: expr:methodTarget);
			Conditional:if(check: { targetType == self:names:selfIdent() || targetType == '' }, then: {
				targetType: self:currentClassName;
			});
			# INSTANCE.md §2.3: a bare call resolved against the bare scope
			# dispatches on its as-imported provider.
			Conditional:if(check: { expr:bareProvider != '' }, then: {
				targetType: expr:bareProvider;
			});
			# Keep the generic suffix ('Box:Int') for lookup: substitution
			# needs the type arguments to ground T. The split base only
			# feeds the enum-registry checks.
			local String is baseOnly: targetType;
			Conditional:if(check: { targetType:contains(needle: ':') }, then: {
				local Array of String is parts: targetType:split(delimiter: ':');
				baseOnly: parts:get(index: 0);
			});
			Conditional:if(check: { self:allEnumNames:has(key: baseOnly) }, then: {
				targetType: baseOnly;
			});
			# Container element extraction: Array of X:get/pop/removeAt -> X.
			Conditional:if(check: { targetType:startsWith(prefix: 'Array:') && (expr:methodName == 'get' || expr:methodName == 'pop' || expr:methodName == 'removeAt') }, then: {
				return targetType:substring(start: 6, end: targetType:length());
			});
			# Enum contract methods have fixed return types.
			Conditional:if(check: { self:allEnumNames:has(key: targetType) }, then: {
				Conditional:if(check: { expr:methodName == 'name' }, then: {
 return 'String';
				});
				Conditional:if(check: { expr:methodName == 'ordinal' }, then: {
 return Primitive:INT:value();
				});
				Conditional:if(check: { expr:methodName == 'values' }, then: {
 return 'Array:' . targetType;
				});
				Conditional:if(check: { expr:methodName == 'value' }, then: {
					Conditional:if(check: { self:allStringBackedEnums:has(key: targetType) }, then: {
						return 'String';
					});
					return Primitive:INT:value();
				});
			});
			Conditional:if(check: { targetType == Primitive:INT:value() && expr:methodName == 'toBase' }, then: {
				return 'String';
			});
			local String is ret: '';
			Conditional:if(check: { expr:overloadIndex > 0 }, then: {
				# The checker stamped the exact return type for the selected
				# overload (FUNCTIONS.md §I.2); it is the source of truth.
				local String is rt: expr:resolvedType;
				Conditional:if(check: { rt != '' && rt != Primitive:ANY:value() }, then: {
					ret: rt;
				});
			});
			Conditional:if(check: { ret == '' }, then: {
				ret: self:lookupMethodReturnType(className: targetType, methodName: expr:methodName);
			});
			Conditional:if(check: { ret == '' || self:isVoidType(t: ret) }, then: {
				return '';
			});
			return ret;
		});
		Conditional:if(check: { kind == ExpressionKind:FIELD_ACCESS }, then: {
			local String is leftT: self:inferTargetType(expr: expr:leftExpr);
			Conditional:if(check: { leftT == '' || leftT == Primitive:ANY:value() }, then: {
				return '';
			});
			return self:lookupFieldType(className: leftT, fieldName: expr:stringValue);
		});
		Conditional:if(check: { kind == ExpressionKind:INDEX }, then: {
			# Indexing a container yields its element type (both spellings).
			local String is leftT: self:inferTargetType(expr: expr:leftExpr);
			Conditional:if(check: { leftT:startsWith(prefix: 'Array:') && leftT:length() > 6 }, then: {
				return leftT:substring(start: 6, end: leftT:length());
			});
			Conditional:if(check: { leftT:startsWith(prefix: 'Array of ') && leftT:length() > 9 }, then: {
				return leftT:substring(start: 9, end: leftT:length());
			});
			Conditional:if(check: { leftT:startsWith(prefix: 'List of ') && leftT:length() > 8 }, then: {
				return leftT:substring(start: 8, end: leftT:length());
			});
			# Map indexing yields the VALUE type (both spellings).
			Conditional:if(check: { leftT:startsWith(prefix: 'Map of ') && leftT:length() > 7 }, then: {
				local String is kv: leftT:substring(start: 7, end: leftT:length());
				local Int is toIdx: kv:indexOf(search: ' to ', default: -1);
				Conditional:if(check: { toIdx >= 0 }, then: {
					return kv:substring(start: toIdx + 4, end: kv:length());
				});
			});
			Conditional:if(check: { leftT:startsWith(prefix: 'Map:') && leftT:length() > 5 }, then: {
				local String is kv: leftT:substring(start: 5, end: leftT:length());
				local Int is cIdx: kv:indexOf(search: ':', default: -1);
				Conditional:if(check: { cIdx >= 0 }, then: {
					return kv:substring(start: cIdx + 1, end: kv:length());
				});
			});
			return '';
		});
		Conditional:if(check: { kind == ExpressionKind:STRING }, then: {
			return 'String';
		});
		Conditional:if(check: { kind == ExpressionKind:NUMBER }, then: {
			return Primitive:INT:value();
		});
		Conditional:if(check: { kind == ExpressionKind:FLOAT }, then: {
			return 'Float';
		});
		Conditional:if(check: { kind == ExpressionKind:BOOL }, then: {
			return 'Boolean';
		});
		Conditional:if(check: { kind == ExpressionKind:ARRAY }, then: {
			return 'Array';
		});
		Conditional:if(check: { kind == ExpressionKind:MAP }, then: {
			return 'Map';
		});
		Conditional:if(check: { kind == ExpressionKind:BINARY && expr:binaryOp == '.' }, then: {
			# String concatenation chains produce a String.
			return 'String';
		});
		Conditional:if(check: { kind == ExpressionKind:CAST }, then: {
			return expr:castTarget;
		});
		Conditional:if(check: { kind == ExpressionKind:UNARY }, then: {
			Conditional:if(check: { expr:unaryOp == '!' }, then: {
				return 'Boolean';
			});
			return self:inferTargetType(expr: expr:unaryExpr);
		});
		Conditional:if(check: { kind == ExpressionKind:ANON_FN }, then: {
			local String is anonRet: expr:anonReturnType:name;
			Conditional:if(check: { anonRet != '' && !self:isVoidType(t: anonRet) }, then: {
				return 'Function:' . self:formatTypeString(t: expr:anonReturnType);
			});
			return 'Function';
		});
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
		Conditional:if(check: { kind == ExpressionKind:ARRAY || kind == ExpressionKind:MAP }, then: {
			return true;
		});
		Conditional:if(check: { kind == ExpressionKind:BINARY }, then: {
			return expr:binaryOp == '.';
		});
		Conditional:if(check: { kind == ExpressionKind:CALL }, then: {
			local String is resT: self:inferTargetType(expr: expr);
			Conditional:if(check: { !self:isArcType(typeName: resT) }, then: {
				return false;
			});
			local String is targetT0: self:inferTargetType(expr: expr:methodTarget);
			local String is targetT: targetT0;
			Conditional:if(check: { targetT:contains(needle: ':') }, then: {
				local Array of String is parts0: targetT:split(delimiter: ':');
				targetT: parts0:get(index: 0);
			});
			Conditional:if(check: { self:allClassNames:has(key: targetT) && !self:allEnumNames:has(key: targetT) }, then: {
				local String is mRet: self:lookupMethodReturnType(className: targetT, methodName: expr:methodName);
				Conditional:if(check: { mRet == '' || self:isVoidType(t: mRet) }, then: {
					return false;
				});
				Conditional:if(check: { mRet == targetT && expr:methodName != 'init' && expr:methodName != targetT && !self:policy:isTransparent(c: self:findClass(name: targetT)) }, then: {
					return false;
				});
			});
			# Container-typed receivers (incl. of-form spellings) resolve
			# like the transparent classes they are: their element gets are
			# BORROWS, never claims. Without this, the fallback below
			# classified every array element-get as a claim, the typed
			# constructor skipped its retain, and the var-decl's
			# scope-end release underflowed the refcount.
			Conditional:if(check: { self:policy:isTransparent(c: self:findClass(name: targetT)) || targetT == 'List' || targetT == 'String' ||
				targetT:startsWith(prefix: 'Array') || targetT:startsWith(prefix: 'List') || targetT:startsWith(prefix: 'Map') }, then: {
				Conditional:if(check: { expr:methodName == 'get' }, then: {
					return targetT:startsWith(prefix: 'Map');
				});
				when (expr:methodName) {
					is 'pop', 'removeAt', 'substring', 'trim', 'replace', 'join', 'split', 'lines', 'keys',
					'getString', 'read', 'fromCharCode', 'toString', 'map', 'filter', 'slice', 'charAt': {
						return true;
					}
					else: {
						return false;
					}
				}
			});
			return true;
		});
		return false;
	}

	## True when the expression is a constructor call whose produced value
	## is provably fresh (the creator abandons the initial ref).
	##
	## @param expr: The expression node.
	## @return: true when fresh.
	Function of Boolean is isFreshConstructorCall(Expression is expr){
		Conditional:if(check: { expr:kind != ExpressionKind:CALL }, then: {
			return false;
		});
		local String is m: expr:methodName;
		Conditional:if(check: { !(m == 'init' || m == 'new') }, then: {
			return false;
		});
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
		Conditional:if(check: { resolved == 'String' || resolved == 'string' }, then: {
			return true;
		});
		local ExpressionKind is kind: expr:kind;
		Conditional:if(check: { kind == ExpressionKind:STRING }, then: {
			return true;
		});
		Conditional:if(check: { kind == ExpressionKind:BINARY && expr:binaryOp == '.' }, then: {
			return true;
		});
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
		Conditional:if(check: { kind == ExpressionKind:STRING }, then: {
			return 'spec_string_intern("' . self:utils:escapeString(s: expr:stringValue) . '")';
		});
		Conditional:if(check: { kind == ExpressionKind:NUMBER }, then: {
			return 'spec_to_string_int(' . exprC . ')';
		});
		Conditional:if(check: { kind == ExpressionKind:FLOAT }, then: {
			return 'spec_to_string_float(' . exprC . ')';
		});
		Conditional:if(check: { kind == ExpressionKind:BOOL }, then: {
			return 'spec_to_string_bool(' . exprC . ')';
		});
		Conditional:if(check: { kind == ExpressionKind:BINARY }, then: {
			local String is op: expr:binaryOp;
			Conditional:if(check: { op == '+' || op == '-' || op == '*' || op == '/' || op == '%' || op == '&' || op == '|' || op == '^' || op == '<<' || op == '>>' }, then: {
				return 'spec_to_string_int(' . exprC . ')';
			});
			Conditional:if(check: { op == '==' || op == '!=' || op == '<' || op == '<=' || op == '>' || op == '>=' || op == '&&' || op == '||' }, then: {
				return 'spec_to_string_bool(' . exprC . ')';
			});
			return exprC;
		});
		Conditional:if(check: { kind == ExpressionKind:UNARY }, then: {
			Conditional:if(check: { expr:unaryOp == '!' }, then: {
				return 'spec_to_string_bool(' . exprC . ')';
			});
			return 'spec_to_string_int(' . exprC . ')';
		});
		local String is t: self:inferTargetType(expr: expr);
		Conditional:if(check: { t == 'String' }, then: {
			return exprC;
		});
		Conditional:if(check: { t == 'double' || t == 'long long' || t == 'bool' }, then: {
			# C-typed leaks from resolution — map back to Spec spellings.
			Conditional:if(check: { t == 'double' }, then: {
				return 'spec_to_string_float(' . exprC . ')';
			});
			Conditional:if(check: { t == 'bool' }, then: {
				return 'spec_to_string_bool(' . exprC . ')';
			});
			return 'spec_to_string_int(' . exprC . ')';
		});
		Conditional:if(check: { t == Primitive:INT:value() }, then: {
			return 'spec_to_string_int(' . exprC . ')';
		});
		Conditional:if(check: { t == 'Float' }, then: {
			return 'spec_to_string_float(' . exprC . ')';
		});
		Conditional:if(check: { t == 'Boolean' }, then: {
			return 'spec_to_string_bool(' . exprC . ')';
		});
		# Enum values render as their variant name (Color_name(c)).
		Conditional:if(check: { t != '' && self:allEnumNames:has(key: t) && !self:allTaggedEnums:has(key: t) }, then: {
			return t . '_name(' . exprC . ')';
		});
		Conditional:if(check: { t != '' && t != Primitive:ANY:value() && self:allClassNames:has(key: t) && !self:allEnumNames:has(key: t) && !self:policy:isTransparent(c: self:findClass(name: t)) }, then: {
			return 'spec_type_name(' . exprC . ') /* wrap:' . t . ' */';
		});
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
		Conditional:if(check: { kind == ExpressionKind:CALL }, then: {
			claim: self:yieldsClaim(expr: expr);
			Conditional:if(check: { (expr:methodName == 'if' || expr:methodName == 'branch') && expr:argCount() >= 2 && expr:argCount() <= 4 }, then: {
				claim: false;
			});
		}, else: {
			Conditional:if(check: { kind == ExpressionKind:BINARY }, then: {
				claim: expr:binaryOp == '.';
			}, else: {
				Conditional:if(check: { kind == ExpressionKind:ARRAY || kind == ExpressionKind:MAP }, then: {
					claim: true;
				}, else: {
					Conditional:if(check: { kind == ExpressionKind:INDEX }, then: {
						local String is tgt: self:inferTargetType(expr: expr:leftExpr);
						claim: (tgt:startsWith(prefix: 'Map') && self:inferTargetType(expr: expr) == 'String');
					});
				});
			});
		});
		Conditional:if(check: { claim }, then: {
			Conditional:if(check: { self:argMode }, then: {
				local String is resT: self:inferTargetType(expr: expr);
				local String is resC: self:cTypeFor(typeName: resT);
				return '((' . resC . ')spec_claim_pool((void*)(' . c . ')))';
			});
		});
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
				Conditional:if(check: { expr:stringValue != '' }, then: {
					return expr:stringValue;
				});
				return '0';
			}
			is ExpressionKind:FLOAT: {
				Conditional:if(check: { expr:stringValue != '' }, then: {
					return expr:stringValue;
				});
				return '0.0';
			}
			is ExpressionKind:BOOL: {
				return Conditional:if(check: { expr:boolValue }, then: { 'true' }, else: { 'false' });
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
				Conditional:if(check: { expr:unaryOp == 'post++' }, then: {
					return '((' . innerC . ')++)';
				});
				Conditional:if(check: { expr:unaryOp == 'post--' }, then: {
					return '((' . innerC . ')--)';
				});
				Conditional:if(check: { expr:unaryOp == '++' }, then: {
					return '(++(' . innerC . '))';
				});
				Conditional:if(check: { expr:unaryOp == '--' }, then: {
					return '(--(' . innerC . '))';
				});
				return '(' . expr:unaryOp . '(' . innerC . '))';
			}
			is ExpressionKind:CALL: {
				return self:emitCall(expr: expr);
			}
			is ExpressionKind:FIELD_ACCESS: {
				local String is leftC: self:generateExpression(expr: expr:leftExpr);
				return '(' . leftC . ')->' . self:utils:cIdent(name: expr:stringValue);
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
		local String is addFn: Conditional:if(check: { listHint }, then: { 'spec_vec_push' }, else: { 'spec_array_add' });
		local String is newCall: 'spec_array_new()';
		self:containerHint: '';
		Conditional:if(check: { self:containerHint != '' }, then: {
			local String is hintKind: self:containerElemKind(containerType: self:containerHint);
			newCall: Conditional:if(check: { hintKind == 'byte' }, then: { 'spec_bytebuffer_new()' }, else: { Conditional:if(check: { hintKind == 'object' || hintKind == 'string' }, then: { Conditional:if(check: { listHint }, then: { 'spec_vec_new_string()' }, else: { 'spec_vec_new_object()' }) }, else: { Conditional:if(check: { listHint }, then: { 'spec_vec_new()' }, else: { 'spec_array_new_object()' }) }) });
		}, else: {
			Conditional:if(check: { expr:arrayItems:length() > 0 }, then: {
				local String is elemT: self:inferTargetType(expr: expr:arrayItems:get(index: 0));
				newCall: Conditional:if(check: { self:isArcType(typeName: elemT) || elemT == 'String' }, then: { 'spec_array_new_object()' }, else: { 'spec_array_new()' });
			});
		});
		self:containerHint: '';
		self:containerHint: '';
		self:containerHint: '';
		self:containerHint: '';
		self:containerHint: '';
		self:containerHint: '';
		local String is arrCType: Conditional:if(check: { listHint }, then: { 'SpecVec*' }, else: { 'SpecArray*' });
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
		Conditional:if(check: { self:containerHint != '' }, then: {
			Conditional:if(check: { self:containerElemIsArc(containerType: self:containerHint) }, then: {
				newCall: 'spec_map_new_object()';
			});
			self:containerHint: '';
		}, else: {
			Conditional:if(check: { expr:mapValues:length() > 0 }, then: {
				local String is valT: self:inferTargetType(expr: expr:mapValues:get(index: 0));
				Conditional:if(check: { self:isArcType(typeName: valT) }, then: {
					newCall: 'spec_map_new_object()';
				});
			});
		});
		local String is res: '({ SpecMap* _map = ' . newCall . ';';
		local Int is idx: 0;
		local Boolean is savedArgM: self:argMode;
		self:argMode: false;
		expr:mapKeys:each(action: local Function(Expression is kExpr){
			local Expression is vExpr: expr:mapValues:get(index: idx);
			local String is kC: self:generateExpression(expr: kExpr);
			local String is vC: self:generateExpression(expr: vExpr);
			Conditional:if(check: { self:isStringExpr(expr: vExpr, exprC: vC) }, then: {
				res: res . ' spec_map_set(_map, ' . kC . ', ' . vC . ');';
			}, else: {
				local String is setFn: Conditional:if(check: { self:yieldsClaim(expr: vExpr) }, then: { 'spec_map_set_any_transfer' }, else: { 'spec_map_set_any' });
				res: res . ' ' . setFn . '(_map, ' . kC . ', (void*)(intptr_t)(' . vC . '));';
			});
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
		Conditional:if(check: { name == self:names:selfIdent() || name == 'true' || name == 'false' }, then: {
			return name;
		});
		Conditional:if(check: { self:allEnumVariants:has(key: name) }, then: {
			local String is enumName: self:allEnumVariants:getString(key: name, default: '');
			Conditional:if(check: { self:allTaggedEnums:has(key: enumName) }, then: {
				return enumName . '_' . self:utils:cIdent(name: name) . '_ctor()';
			});
			return enumName . '_' . self:utils:cIdent(name: name);
		});
		Conditional:if(check: { self:localVars:has(key: name) }, then: {
			return self:utils:cIdent(name: name);
		});
		Conditional:if(check: { self:fieldTypes:has(key: name) }, then: {
			return 'self->' . self:utils:cIdent(name: name);
		});
		return self:utils:cIdent(name: name);
	}

	## Emits a colon-path reference: enum variants, chained field access.
	##
	## @param expr: The PATH expression.
	## @return: C expression.
	Function of String is emitPath(Expression is expr){
		local Array of String is segs: expr:pathSegments;
		Conditional:if(check: { segs:length() == 1 }, then: {
			return segs:get(index: 0);
		});
	# FUNCTIONS.md Part IV IV.2c: the nested-class chain — 'Outer:Inner'
	# and the inner-of-inner 'Outer:Mid:Deep' — walks CLASS-kind members
	# per segment and resolves to the deepest class's qualified C symbol
	# base.
	Conditional:if(check: { segs:length() >= 2 && !self:allEnumNames:has(key: segs:get(index: 0)) }, then: {
		local String is root: segs:get(index: 0);
		local ClassInfo is chainCls: self:findClass(name: root);
		local Boolean is chainOk: chainCls:name == root;
		local Int is chainIdx: 1;
		Loops:loop(
			evaluate: local Function of Boolean(){ return chainOk && chainIdx < segs:length(); },
			iteration: local Function of Boolean(){
				local String is nextSym: '';
				local ClassInfo is nextCls: ClassInfo:init(name: '', baseClass: '', members: []);
				chainCls:members:each(action: local Function(Member is m){
					Conditional:if(check: { m:kind == MemberKind:CLASS && m:nestedClass:name == segs:get(index: chainIdx) }, then: {
						nextSym: self:utils:cIdent(name: chainCls:qualifiedName() . ':' . segs:get(index: chainIdx));
						nextCls: m:nestedClass;
					});
				});
				Conditional:if(check: { nextSym != '' }, then: {
					chainCls: nextCls;
					chainIdx: chainIdx + 1;
				}, else: {
					chainOk: false;
				});
				return true;
			}
		);
		Conditional:if(check: { chainOk && chainIdx == segs:length() }, then: {
			return self:utils:cIdent(name: chainCls:qualifiedName());
		});
	});
		Conditional:if(check: { segs:length() >= 2 }, then: {
			local String is root: segs:get(index: 0);
			Conditional:if(check: { self:allEnumNames:has(key: root) }, then: {
				Conditional:if(check: { self:allTaggedEnums:has(key: root) }, then: {
					return root . '_' . self:utils:cIdent(name: segs:get(index: 1)) . '_ctor()';
				});
				return root . '_' . self:utils:cIdent(name: segs:get(index: 1));
			});
			local String is rootC: self:utils:cIdent(name: root);
			Conditional:if(check: { !self:localVars:has(key: root) && self:fieldTypes:has(key: root) }, then: {
				rootC: 'self->' . rootC;
			});
			local Int is idx: 1;
			local String is resC: rootC;
			Loops:loop(
				evaluate: local Function of Boolean(){
					return idx < segs:length();
				},
				iteration: local Function of Boolean(){
					resC: resC . '->' . self:utils:cIdent(name: segs:get(index: idx));
					idx: idx + 1;
					return true;
				}
			);
			Conditional:if(check: { root != self:names:selfIdent() }, then: {
				local String is resolvedT: expr:resolvedType;
				local String is rootT: self:localVars:getString(key: root, default: '');
				Conditional:if(check: { rootT:contains(needle: ':') && !rootT:startsWith(prefix: 'Array:') && !rootT:startsWith(prefix: 'Map:') && resolvedT != '' && resolvedT != Primitive:ANY:value() }, then: {
					local String is castT: self:cTypeFor(typeName: resolvedT);
					resC: '((' . castT . ')(intptr_t)(' . resC . '))';
				});
			});
			return resC;
		});
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
				Conditional:if(check: { !leftPrim }, then: {
					Conditional:if(check: { leftClaimKind }, then: {
						leftClaim: leftC;
					}, else: {
						Conditional:if(check: { leftArc }, then: {
							leftClaim: '(void*)spec_retain((void*)(' . leftC . '))';
						}, else: {
							leftClaim: 'spec_string_from_chars(' . leftC . ')';
						});
					});
				});
				local String is leftWrap: Conditional:if(check: { leftPrim }, then: { self:wrapToString(expr: expr:leftExpr, exprC: leftClaim) }, else: { leftClaim });
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
				Conditional:if(check: { self:isStringExpr(expr: expr:leftExpr, exprC: leftC) || self:isStringExpr(expr: expr:rightExpr, exprC: rightC) }, then: {
					return 'spec_string_equals(' . leftC . ', ' . rightC . ')';
				});
				return '((' . leftC . ') == (' . rightC . '))';
			}
			is '!=': {
				local String is leftC: self:generateExpression(expr: expr:leftExpr);
				local String is rightC: self:generateExpression(expr: expr:rightExpr);
				Conditional:if(check: { self:isStringExpr(expr: expr:leftExpr, exprC: leftC) || self:isStringExpr(expr: expr:rightExpr, exprC: rightC) }, then: {
					return '(!spec_string_equals(' . leftC . ', ' . rightC . '))';
				});
				return '((' . leftC . ') != (' . rightC . '))';
			}
			is '<', '<=', '>', '>=': {
				# FUNCTIONS.md hardening (D5): relational operators on String
				# compare lexicographically through the floor — never by
				# pointer.
				local String is leftC: self:generateExpression(expr: expr:leftExpr);
				local String is rightC: self:generateExpression(expr: expr:rightExpr);
				Conditional:if(check: { self:isStringExpr(expr: expr:leftExpr, exprC: leftC) || self:isStringExpr(expr: expr:rightExpr, exprC: rightC) }, then: {
					return '(spec_string_compare(' . leftC . ', ' . rightC . ') ' . op . ' 0)';
				});
				return '((' . leftC . ') ' . op . ' (' . rightC . '))';
			}
			is '+', '-', '*', '/', '%', '&&', '||', '&', '|', '^', '<<', '>>': {
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
		Conditional:if(check: { targetType:startsWith(prefix: 'Map:') || targetType == 'Map' }, then: {
			local String is valType: 'String';
			Conditional:if(check: { targetType:startsWith(prefix: 'Map:') }, then: {
				valType: self:elemOfType(t: targetType);
			});
			Conditional:if(check: { valType == 'String' }, then: {
				return '((String)spec_map_get(' . targetC . ', ' . indexC . ', spec_string_intern("")))';
			});
			Conditional:if(check: { valType == Primitive:INT:value() }, then: {
				return '((long long)(intptr_t)spec_map_get(' . targetC . ', ' . indexC . ', 0))';
			});
			Conditional:if(check: { valType == 'Float' }, then: {
				return '((double)spec_map_get(' . targetC . ', ' . indexC . ', 0))';
			});
			Conditional:if(check: { valType == 'Boolean' }, then: {
				return '((bool)(intptr_t)spec_map_get(' . targetC . ', ' . indexC . ', false))';
			});
			local String is valCType: self:cTypeFor(typeName: valType);
			return '((' . valCType . ')(intptr_t)spec_map_get(' . targetC . ', ' . indexC . ', NULL))';
		});
		local String is elemT: self:elemOfType(t: targetType);
		Conditional:if(check: { elemT != '' }, then: {
			local String is elemCType: self:cTypeFor(typeName: elemT);
			return '((' . elemCType . ')(intptr_t)spec_array_get(' . targetC . ', (size_t)(' . indexC . ')))';
		});
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
		Conditional:if(check: { expr:castArgs:length() > 0 }, then: {
			digitsC: self:generateExpression(expr: expr:castArgs:get(index: 0));
		});
		when (target) {
			is 'Hex': {
				Conditional:if(check: { srcT == 'String' }, then: {
					return 'String_parseInt(' . innerC . ', 16, 0)';
				});
				return 'spec_int_to_base(' . innerC . ', 16, ' . digitsC . ')';
			}
			is 'Bin': {
				Conditional:if(check: { srcT == 'String' }, then: {
					return 'String_parseInt(' . innerC . ', 2, 0)';
				});
				return 'spec_int_to_base(' . innerC . ', 2, ' . digitsC . ')';
			}
			is 'Oct': {
				Conditional:if(check: { srcT == 'String' }, then: {
					return 'String_parseInt(' . innerC . ', 8, 0)';
				});
				return 'spec_int_to_base(' . innerC . ', 8, ' . digitsC . ')';
			}
			is 'Any': {
				return innerC;
			}
			is 'Int': {
				Conditional:if(check: { srcT == 'String' }, then: {
					return 'String_parseInt(' . innerC . ', 10, 0)';
				});
				Conditional:if(check: { srcT == 'Float' || srcT == 'Byte' }, then: {
					return '((long long)(' . innerC . '))';
				});
				return innerC;
			}
			is 'Float': {
				return '((double)(' . innerC . '))';
			}
			is 'Byte': {
				Conditional:if(check: { srcT == 'Byte' }, then: {
					return innerC;
				});
				return '({ long long _bv = (long long)(' . innerC . '); if (_bv < 0 || _bv > 255) { spec_panic_byte_range(_bv); } ((unsigned char)_bv); })';
			}
			is 'String': {
				Conditional:if(check: { srcT == Primitive:INT:value() }, then: {
					return 'spec_to_string_int(' . innerC . ')';
				});
				Conditional:if(check: { srcT == 'Float' }, then: {
					return 'spec_to_string_float(' . innerC . ')';
				});
				Conditional:if(check: { srcT == 'Boolean' }, then: {
					return 'spec_to_string_bool(' . innerC . ')';
				});
				Conditional:if(check: { self:allClassNames:has(key: srcT) && !self:allEnumNames:has(key: srcT) && !self:policy:isTransparent(c: self:findClass(name: srcT)) }, then: {
					return 'spec_type_name(' . innerC . ')';
				});
				# Unknown or computed sources (arithmetic binaries, calls with
				# unresolved types) route through the string-wrap policy.
				return self:wrapToString(expr: expr:leftExpr, exprC: innerC);
			}
			else: {
				Conditional:if(check: { self:allClassNames:has(key: target) && !self:allEnumNames:has(key: target) && !self:policy:isTransparent(c: self:findClass(name: target)) }, then: {
					return '((' . target . '*)spec_cast_check(' . innerC . ', "' . target . '"))';
				});
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
		Conditional:if(check: { targetC:startsWith(prefix: 'self->') }, then: {
			fieldKey: targetC:substring(start: 6, end: targetC:length());
		});
		Conditional:if(check: { targetType == '' }, then: {
			targetType: self:localVars:getString(key: fieldKey, default: '');
		});
		Conditional:if(check: { targetType == '' }, then: {
			targetType: self:fieldTypes:getString(key: fieldKey, default: '');
		});

		local String is builtinC: self:builtins:generateBuiltinCall(expr: expr, targetC: targetC, targetType: targetType, cg: self);
		Conditional:if(check: { builtinC != '' }, then: {
			return builtinC;
		});

		# FUNCTIONS.md Part II: the Conditional inline — statement-form
		# conditionals compile to zero-allocation C if/else (the
		# While:condition precedent). The wrapper's own floor call arrives
		# as a qualified PATH receiver and is excluded, so the fallback
			# stays honest.
			Conditional:if(check: { (expr:methodName == 'if' || expr:methodName == 'branch') && expr:argCount() >= 2 && expr:argCount() <= 4 && ((targetC == 'Conditional' && expr:methodTarget:kind == ExpressionKind:IDENT) || expr:bareProvider == 'Conditional') }, then: {
				local Boolean is shapeOk: expr:argValue(index: 0):kind == ExpressionKind:ANON_FN;
				local Int is bi: 1;
				Loops:loop(
					evaluate: local Function of Boolean(){ return shapeOk && bi < expr:argCount(); },
					iteration: local Function of Boolean(){
						Conditional:if(check: { expr:argValue(index: bi):kind != ExpressionKind:ANON_FN }, then: {
							shapeOk: false;
						});
						bi: bi + 1;
						return true;
					}
				);
				Conditional:if(check: { shapeOk }, then: {
					return self:generateInlineBranch(expr: expr);
				});
			});

		# Function variable or field invocation: fnVar(args).
		Conditional:if(check: { targetC == self:names:selfIdent() && (self:localVars:has(key: expr:methodName) || self:fieldTypes:has(key: expr:methodName)) }, then: {
			local String is fnVarT: self:localVars:getString(key: expr:methodName, default: self:fieldTypes:getString(key: expr:methodName, default: ''));
			Conditional:if(check: { fnVarT:startsWith(prefix: 'Function') }, then: {
				local String is fnPtrC: Conditional:if(check: { self:localVars:has(key: expr:methodName) }, then: { self:utils:cIdent(name: expr:methodName) }, else: { 'self->' . self:utils:cIdent(name: expr:methodName) });
				local String is retTName: Conditional:if(check: { fnVarT:startsWith(prefix: 'Function:') && fnVarT:length() > 9 }, then: { fnVarT:substring(start: 9, end: fnVarT:length()) }, else: { 'Void' });
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
			});
		});

		# Tagged enum variant constructor.
		Conditional:if(check: { self:allEnumVariants:has(key: expr:methodName) && (self:allTaggedEnums:has(key: targetC) || targetC == self:names:selfIdent()) }, then: {
			local String is eName: self:allEnumVariants:getString(key: expr:methodName, default: '');
			# FUNCTIONS.md Part IV IV.2c: the variant symbols qualify for
			# nested tagged enums — the registry lookups stay on the bare
			# name; the C symbol derives from the qualified identity.
			local String is eSym: eName;
			local ClassInfo is eCls: self:findClass(name: eName);
			Conditional:if(check: { eCls:name == eName }, then: {
				eSym: self:utils:cIdent(name: eCls:qualifiedName());
			});
			Conditional:if(check: { self:allTaggedEnums:has(key: eName) }, then: {
				local Member is vMem: self:lookupEnumVariant(enumName: eName, variantName: expr:methodName);
				local Array of Parameter is vParams: vMem:params;
				local String is vArgsC: '';
				local Int is pIdx: 0;
				vParams:each(action: local Function(Parameter is p){
					Conditional:if(check: { pIdx > 0 }, then: {
 vArgsC: vArgsC . ', ';
					});
					local String is pName: p:name;
					local Boolean is matched: false;
					local String is argC: '0';
					expr:methodArgs:each(action: local Function(NamedArg is a){
						Conditional:if(check: { !matched && a:name == pName && pName != '' }, then: {
							argC: self:generateExpression(expr: a:value);
							matched: true;
						});
					});
					Conditional:if(check: { !matched && pIdx < expr:argCount() }, then: {
						local Expression is posArg: self:argValue(expr: expr, index: pIdx);
						argC: self:generateExpression(expr: posArg);
						matched: true;
					});
					vArgsC: vArgsC . argC;
					pIdx: pIdx + 1;
				});
				return eSym . '_' . self:utils:cIdent(name: expr:methodName) . '(' . vArgsC . ')';
			});
		});

		# Constructor or static invocation: ClassName:init(...)/ClassName:method(...).
		Conditional:if(check: { self:allClassNames:has(key: targetC) && !self:allEnumNames:has(key: targetC) }, then: {
			# IV.2c: the C identity of the target — a bare nested-class name
			# has no C type when the bare alias is absent (the bare name is
			# not unique); resolve to the qualified symbol form.
			local String is targetSym: targetC;
			local ClassInfo is tgtCls: self:findClass(name: targetC);
			Conditional:if(check: { tgtCls:name != '' }, then: {
				targetSym: self:utils:cIdent(name: tgtCls:qualifiedName());
			});
			local Member is mDef: self:lookupOverloadedMemberGen(className: targetC, methodName: expr:methodName, idx: expr:overloadIndex);
			local String is ownerName: self:overloadOwnerNameGen(className: targetC, methodName: expr:methodName, idx: expr:overloadIndex);
			local String is symOwner: ownerName;
			Conditional:if(check: { symOwner == '' }, then: {
				symOwner: targetC;
			});
			local String is argsJoined: self:formatCallArgumentsWith(className: targetC, methodName: expr:methodName, idx: expr:overloadIndex, args: expr:methodArgs);
			Conditional:if(check: { expr:methodName == 'init' }, then: {
				# FUNCTIONS.md Part IV IV.2: a qualified inner-class target
				# constructs with its OWN _new/default-_init pair — the
				# enclosing class's entry-point init is not the inner's
				# construction protocol. The gate: the targetC is a registered
				# class identity (the qualified or the symbol form).
				Conditional:if(check: { self:allClassNames:has(key: targetC) && targetC:contains(needle: '_') && self:findClass(name: targetC):name == '' }, then: {
					local String is innerNewSym: targetC;
					local String is innerInitSym: targetC . '_init';
					return '({ ' . targetC . '* _inst = ' . innerNewSym . '_new(); ' . innerInitSym . '(_inst' . argsJoined . '); _inst; })';
				});
				local String is initCls: self:overloadOwnerNameGen(className: targetC, methodName: 'init', idx: expr:overloadIndex);
				local String is symOwnerCls: initCls;
				Conditional:if(check: { symOwnerCls == '' }, then: {
					symOwnerCls: targetC;
				});
			local String is initSymbol: self:overloadSymbol(className: symOwnerCls, methodName: 'init', idx: expr:overloadIndex);
			# FUNCTIONS.md Part IV IV.2c: the _new symbol qualifies like the
			# init symbol — resolve the class's qualified identity.
			local String is newSym: self:utils:cIdent(name: targetC);
			local ClassInfo is newCls: self:findClass(name: targetC);
			Conditional:if(check: { newCls:name == targetC }, then: {
				newSym: self:utils:cIdent(name: newCls:qualifiedName());
			});
			Conditional:if(check: { initCls == '' || initCls == targetC }, then: {
				return '({ ' . targetSym . '* _inst = ' . newSym . '_new(); ' . initSymbol . '(_inst' . argsJoined . '); _inst; })';
			});
			return '({ ' . targetSym . '* _inst = ' . newSym . '_new(); ' . initSymbol . '((' . self:utils:cIdent(name: initCls) . '*)_inst' . argsJoined . '); _inst; })';
		});
			Conditional:if(check: { mDef:kind == MemberKind:METHOD }, then: {
				local String is callSymbol: self:overloadSymbol(className: symOwner, methodName: expr:methodName, idx: expr:overloadIndex);
				Conditional:if(check: { self:isFieldFulClass(cls: self:findClass(name: targetC)) }, then: {
					# Field-ful instance import (INSTANCE.md E1/E2 full
					# form): dispatch through the synthetic hidden field
					# the loader materialized; the field borrows as self.
					return callSymbol . '((' . targetC . '*)(self->' . self:utils:cIdent(name: '_import_' . targetC) . ')' . argsJoined . ')';
				});
				# Elided instance import (INSTANCE.md §2.4): under E5 every
				# non-init class-name call is an instance-imported receiver.
				# The class is field-less, its methods self-free — a direct
				# C call with self ignored, void or not. The old unsound
				# static paths (unguarded NULL self, fresh-instance
				# discard) are deleted (INSTANCE.md E8).
				return callSymbol . '(NULL' . argsJoined . ')';
			});
		});

		# INSTANCE.md §2.3: bare call resolved to an as-imported provider —
		# elided dispatch (v1 providers are field-less, self-free).
		# Runtime-managed providers (Math, Output, Stderr) route through
		# the builtin table under the provider's name first.
		Conditional:if(check: { expr:bareProvider != '' }, then: {
			local String is bpBuiltin: self:builtins:generateBuiltinCall(expr: expr, targetC: expr:bareProvider, targetType: expr:bareProvider, cg: self);
			Conditional:if(check: { bpBuiltin != '' }, then: {
				return bpBuiltin;
			});
			local String is bpArgs: self:formatCallArgumentsWith(className: expr:bareProvider, methodName: expr:methodName, idx: expr:overloadIndex, args: expr:methodArgs);
			local String is bpSymbol: self:overloadSymbol(className: expr:bareProvider, methodName: expr:methodName, idx: expr:overloadIndex);
			Conditional:if(check: { self:isFieldFulClass(cls: self:findClass(name: expr:bareProvider)) }, then: {
				return bpSymbol . '((' . expr:bareProvider . '*)(self->' . self:utils:cIdent(name: '_import_' . expr:bareProvider) . ')' . bpArgs . ')';
			});
			return bpSymbol . '(NULL' . bpArgs . ')';
		});

		# Instance method invocation.
		local String is objType: targetType;
		Conditional:if(check: { objType == '' }, then: {
			objType: self:localVars:getString(key: targetC, default: '');
		});
		Conditional:if(check: { objType == '' }, then: {
			objType: self:fieldTypes:getString(key: targetC, default: '');
		});
		Conditional:if(check: { objType == '' || objType == Primitive:ANY:value() || targetC == self:names:selfIdent() }, then: {
			objType: self:currentClassName;
		});
		local String is fullObjType: objType;

		# Any-typed receiver dispatches through its own vtable.
		Conditional:if(check: { objType == Primitive:ANY:value() && self:methodSlots:has(key: expr:methodName) }, then: {
			local Member is anyM: self:lookupMethodMember(className: 'Any', methodName: expr:methodName);
			Conditional:if(check: { anyM:kind == MemberKind:METHOD }, then: {
				local String is slotC: self:methodSlots:getString(key: expr:methodName, default: '0');
				local String is retT: self:resolveReturnType(t: anyM:memberType);
				local String is argsC: '';
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					argsC: argsC . ', ' . self:generateExpression(expr: arg:value);
				});
				Conditional:if(check: { retT == 'void' }, then: {
					return '((void (*)(Any*))((Any*)' . targetC . ')->_vtable[' . slotC . '])((Any*)' . targetC . argsC . ')';
				});
				return '((' . retT . ' (*)(Any*))((Any*)' . targetC . ')->_vtable[' . slotC . '])((Any*)' . targetC . argsC . ')';
			});
		});

		Conditional:if(check: { objType:startsWith(prefix: 'Array:') }, then: {
			objType: 'Array';
		}, else: {
			Conditional:if(check: { objType:startsWith(prefix: 'Map:') }, then: {
				objType: 'Map';
			}, else: {
				# FUNCTIONS.md Part IV IV.2c: a qualified objType whose root is
				# a registered class is a nested-class reference — the FULL
				# qualified name stays (overloadSymbol qualifies the symbol);
				# only container-prefixed types truncate.
				Conditional:if(check: { objType:contains(needle: ':') && self:findClass(name: objType):name == '' }, then: {
					local Array of String is parts: objType:split(delimiter: ':');
					objType: parts:get(index: 0);
				});
			});
		});
		local String is argsC: self:formatCallArgumentsWith(className: fullObjType, methodName: expr:methodName, idx: expr:overloadIndex, args: expr:methodArgs);
		local String is callStr: '';
		Conditional:if(check: { self:overriddenMethods:has(key: expr:methodName) && self:allClassNames:has(key: objType) && !self:allEnumNames:has(key: objType) && !self:policy:isTransparent(c: self:findClass(name: objType)) && self:methodSlots:has(key: expr:methodName) }, then: {
			local Member is vm: self:lookupMethodMember(className: objType, methodName: expr:methodName);
			Conditional:if(check: { vm:kind == MemberKind:METHOD }, then: {
				local String is retT: self:resolveReturnType(t: vm:memberType);
				# IV.2c: the vtable signature's C types qualify (cIdent maps
				# the qualified identity's colon chain).
				local String is objCType: self:utils:cIdent(name: objType);
				local String is sigC: objCType . '*';
				vm:params:each(action: local Function(Parameter is p){
					sigC: sigC . ', ' . self:cTypeFor(typeName: p:paramType:name);
				});
				local String is slotC: self:methodSlots:getString(key: expr:methodName, default: '0');
				Conditional:if(check: { targetC == self:names:selfIdent() }, then: {
					callStr: '(((' . retT . ' (*)(' . sigC . '))self->_vtable[' . slotC . ']))((' . objCType . '*)self' . argsC . ')';
				}, else: {
					callStr: '({ ' . objCType . '* _recv = (' . objCType . '*)(' . targetC . '); (((' . retT . ' (*)(' . sigC . '))_recv->_vtable[' . slotC . ']))((' . objCType . '*)_recv' . argsC . '); })';
				});
			});
		});
		Conditional:if(check: { callStr == '' }, then: {
			local String is dispatchCls: self:overloadOwnerNameGen(className: objType, methodName: expr:methodName, idx: expr:overloadIndex);
			Conditional:if(check: { dispatchCls == '' }, then: {
				dispatchCls: self:findMethodImplementingClass(className: objType, methodName: expr:methodName, paramCount: -1);
			});
			local String is targetExprC: targetC;
			Conditional:if(check: { dispatchCls != '' && dispatchCls != objType }, then: {
				objType: dispatchCls;
				# IV.2c: the cast's C type derives from the (possibly
				# qualified) owner identity.
				targetExprC: '((' . self:utils:cIdent(name: dispatchCls) . '*)' . targetC . ')';
			});
			callStr: self:overloadSymbol(className: objType, methodName: expr:methodName, idx: expr:overloadIndex) . '(' . targetExprC . argsC . ') /* inst:' . objType . ':' . expr:methodName . ' */';
		});
		local Member is targetM: self:lookupOverloadedMemberGen(className: objType, methodName: expr:methodName, idx: expr:overloadIndex);
		local ClassInfo is targetCls: self:findClass(name: objType);
		Conditional:if(check: { targetM:kind == MemberKind:METHOD && targetCls:typeParams:length() > 0 }, then: {
			local String is rawRet: self:formatTypeString(t: targetM:memberType);
			Conditional:if(check: { targetCls:typeParams:indexOf(search: rawRet, default: -1) >= 0 }, then: {
				local String is resolvedRet: expr:resolvedType;
				Conditional:if(check: { resolvedRet != '' && resolvedRet != Primitive:ANY:value() }, then: {
					local String is castCType: self:cTypeFor(typeName: resolvedRet);
					callStr: '((' . castCType . ')(intptr_t)(' . callStr . '))';
				});
			});
		});
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
			Conditional:if(check: { arm:isElse && arm:hasValueExpr }, then: {
				chain: self:generateExpression(expr: arm:valueExpr);
			});
		});
		expr:whenArms:each(action: local Function(WhenArm is arm){
			Conditional:if(check: { !arm:isElse && arm:hasValueExpr }, then: {
				local String is bindsC: self:generateWhenBindings(subjC: subjC, arm: arm);
				local String is armVal: self:generateExpression(expr: arm:valueExpr);
				Conditional:if(check: { bindsC != '' }, then: {
					armVal: '({ ' . bindsC . ' ' . armVal . '; })';
				});
				local String is condOr: '';
				arm:conditions:each(action: local Function(Expression is c){
					local String is cmp: self:generateWhenCondition(subjExpr: expr:whenSubject, subjC: subjC, c: c);
					Conditional:if(check: { condOr == '' }, then: {
						condOr: cmp;
					}, else: {
						condOr: condOr . ' || ' . cmp;
					});
				});
				chain: '((' . condOr . ') ? (' . armVal . ') : (' . chain . '))';
			});
		});
		return chain;
	}

	## True when any statement in [stmts] (recursively through if/when
	## branches AND the closure arguments of calls the gen inlines —
	## branch calls, While loops, container callbacks) assigns the named
	## local. Fully-materialized nested closures mutate their own env
	## copies, but the over-approximation is harmless (the writeback
	## stores an unchanged value).
	##
	## @param name: The local's Spec name.
	## @param stmts: The statement list to scan.
	## @return: true when the local is assigned.
	Function of Boolean is bodyAssignsLocal(String is name, Array of Statement is stmts){
		local Boolean is found: false;
		stmts:each(action: local Function(Statement is s){
			Conditional:if(check: { found }, then: {
				return;
			});
			Conditional:if(check: { s:kind == StatementKind:ASSIGN && s:assignTarget:kind == ExpressionKind:IDENT && s:assignTarget:stringValue == name }, then: {
				found: true;
			}, else: {
				Conditional:if(check: { s:kind == StatementKind:WHEN }, then: {
					s:whenArms:each(action: local Function(WhenArm is arm){
						Conditional:if(check: { !found && self:bodyAssignsLocal(name: name, stmts: arm:body) }, then: {
							found: true;
						});
					});
				}, else: {
					Conditional:if(check: { s:kind == StatementKind:EXPR }, then: {
						Conditional:if(check: { self:assignsViaCall(name: name, expr: s:exprStmt) }, then: {
							found: true;
						});
					}, else: {
						Conditional:if(check: { s:kind == StatementKind:RETURN && s:hasReturnExpr }, then: {
							Conditional:if(check: { self:assignsViaCall(name: name, expr: s:returnExpr) }, then: {
								found: true;
							});
						});
					});
				});
			});
		});
		return found;
	}

	## Descends into a call expression's ANON_FN arguments (the shapes the
	## gen inlines into this scope).
	Function of Boolean is assignsViaCall(String is name, Expression is expr){
		Conditional:if(check: { expr:kind != ExpressionKind:CALL }, then: {
			return false;
		});
		local Boolean is found: false;
		expr:methodArgs:each(action: local Function(NamedArg is arg){
			Conditional:if(check: { !found && arg:value:kind == ExpressionKind:ANON_FN }, then: {
				Conditional:if(check: { self:bodyAssignsLocal(name: name, stmts: arg:value:anonBody) }, then: {
					found: true;
				});
			});
		});
		return found;
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
			self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
			local String is pCType: self:cTypeFor(typeName: p:paramType:name);
			paramsC: paramsC . ', ' . pCType . ' ' . self:utils:cIdent(name: p:name);
		});

		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;
		self:inlineReturnVar: '';
		self:inlineReturnLabel: '';
		# The closure body is its own C function with its OWN cleanup
		# funnel: its returns release its locals through the label, and the
		# write-backs transfer their locals' ownership to the env (those
		# locals are excluded from the releases). The enclosing method's
		# funnel does not reach into it.
		local String is savedCleanupLabel: self:cleanupLabel;
		local String is savedCleanupRetVar: self:cleanupRetVar;
		local Map of String to String is savedExclusions: self:releaseExclusions;
		self:cleanupLabel: '_cleanup_anon_' . id;
		self:cleanupRetVar: '';
		self:releaseExclusions: Map:init();
		Conditional:if(check: { retC != 'void' }, then: {
			self:cleanupRetVar: '_mret_anon_' . id;
		});
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
		local String is capWritebacks: '';
		local Array of String is writebackNames: [];
		local Boolean is hasCaptures: false;

		Conditional:if(check: { self:inMethod && self:currentClassName != '' && !self:policy:isTransparent(c: self:findClass(name: self:currentClassName)) && !self:allEnumNames:has(key: self:currentClassName) && bodyC:contains(needle: 'self') }, then: {
			hasCaptures: true;
			# IV.2c: the captured self's C type qualifies — the bare name is
			# not a C identity for nested classes.
			local String is selfCapType: self:utils:cIdent(name: self:findClass(name: self:currentClassName):qualifiedName());
			capFieldDecls: capFieldDecls . '    ' . selfCapType . "* self;\n";
			capFieldBinds: capFieldBinds . '    ' . selfCapType . "* self = _env->self;\n    (void)self;\n";
			capAssigns: capAssigns . '    _env->self = (' . selfCapType . "*)spec_retain((void*)self);\n";
			capReleases: capReleases . "    if (_env->self) spec_release((void*)_env->self);\n";
		});

		# Names the body redeclares shadow the outer scope — they are NOT
		# captures; binding them from the env would redeclare the local.
		local Map of String to String is bodyLocals: Map:init();
		expr:anonBody:each(action: local Function(Statement is s){
			Conditional:if(check: { s:kind == StatementKind:VAR_DECL }, then: {
				bodyLocals:set(key: s:varName, value: 'true');
			});
		});

		outerKeys:each(action: local Function(String is k){
			Conditional:if(check: { paramNames:indexOf(search: k, default: -1) < 0 && !bodyLocals:has(key: k) }, then: {
				local String is cVar: self:utils:cIdent(name: k);
				Conditional:if(check: { bodyC:contains(needle: cVar) }, then: {
					local String is vType: savedVars:getString(key: k, default: '');
					local String is vCType: self:cTypeFor(typeName: vType);
					Conditional:if(check: { vCType != 'void' && vCType != '' }, then: {
						hasCaptures: true;
						capFieldDecls: capFieldDecls . '    ' . vCType . ' ' . cVar . ";\n";
						capFieldBinds: capFieldBinds . '    ' . vCType . ' ' . cVar . ' = _env->' . cVar . ";\n    (void)" . cVar . ";\n";
						Conditional:if(check: { self:isArcType(typeName: vType) }, then: {
							capAssigns: capAssigns . '    _env->' . cVar . ' = (' . vCType . ')spec_retain((void*)' . cVar . ");\n";
							capReleases: capReleases . '    if (_env->' . cVar . ') spec_release((void*)_env->' . cVar . ");\n";
						}, else: {
							capAssigns: capAssigns . '    _env->' . cVar . ' = ' . cVar . ";\n";
						});
						# FUNCTIONS.md Part II: the closure body may assign a
						# captured local — write it back at exit or the
						# mutation is lost (the callback ran on a copy).
						Conditional:if(check: { self:bodyAssignsLocal(name: k, stmts: expr:anonBody) && k != 'self' }, then: {
							capWritebacks: capWritebacks . '    _env->' . cVar . ' = ' . cVar . ";\n";
							writebackNames:add(item: k);
					});
				});
			});
		});
		});

		Conditional:if(check: { hasCaptures }, then: {
			local String is envStruct: "typedef struct {\n" . capFieldDecls . '} ' . envName . ";\n\n";
			local String is destroyEnv: 'static __attribute__((unused)) void ' . destroyEnvName . "(void* _env_ptr) {\n    if (!_env_ptr) return;\n    " . envName . '* _env = (' . envName . "*)_env_ptr;\n" . capReleases . "    free(_env);\n}\n\n";
			local String is bindsC: '    ' . envName . '* _env = (' . envName . "*)_env_ptr;\n" . capFieldBinds;
			# The closure's cleanup funnel: the write-back locals transfer
			# their ownership to the env and are excluded from the releases;
			# everything else the body declared releases here, on every
			# return path and on the fall-through.
			writebackNames:each(action: local Function(String is wn){
				self:releaseExclusions:set(key: wn, value: 'true');
			});
			local String is cleanupTail: '    ' . self:cleanupLabel . ": ;\n" . self:scopeReleases(stmts: expr:anonBody) . capWritebacks;
			self:releaseExclusions: savedExclusions;
			Conditional:if(check: { self:cleanupRetVar != '' }, then: {
				cleanupTail: cleanupTail . '    return ' . self:cleanupRetVar . ";\n";
			}, else: {
				cleanupTail: cleanupTail . "    return;\n";
			});
			local String is retDecl: '';
			Conditional:if(check: { self:cleanupRetVar != '' }, then: {
				retDecl: '    ' . retC . ' ' . self:cleanupRetVar . " = 0;\n";
			});
			self:cleanupLabel: savedCleanupLabel;
			self:cleanupRetVar: savedCleanupRetVar;
			self:helperFunctions: self:helperFunctions . envStruct . destroyEnv . 'static __attribute__((unused)) ' . retC . ' ' . fnName . '(' . paramsC . ") {\n" . retDecl . bindsC . bodyC . cleanupTail . "}\n\n";
			return '({ ' . envName . '* _env = (' . envName . '*)calloc(1, sizeof(' . envName . "));\n" . capAssigns . '    spec_closure_new((void*)' . fnName . ', (void*)_env, ' . destroyEnvName . '); })';
		}, else: {
			local String is cleanupTail: '    ' . self:cleanupLabel . ": ;\n" . self:scopeReleases(stmts: expr:anonBody);
			self:releaseExclusions: savedExclusions;
			Conditional:if(check: { self:cleanupRetVar != '' }, then: {
				cleanupTail: cleanupTail . '    return ' . self:cleanupRetVar . ";\n";
			}, else: {
				cleanupTail: cleanupTail . "    return;\n";
			});
			local String is retDecl: '';
			Conditional:if(check: { self:cleanupRetVar != '' }, then: {
				retDecl: '    ' . retC . ' ' . self:cleanupRetVar . " = 0;\n";
			});
			self:cleanupLabel: savedCleanupLabel;
			self:cleanupRetVar: savedCleanupRetVar;
			self:helperFunctions: self:helperFunctions . 'static __attribute__((unused)) ' . retC . ' ' . fnName . '(' . paramsC . ") {\n    (void)_env_ptr;\n" . retDecl . bodyC . cleanupTail . "}\n\n";
			return 'spec_closure_new((void*)' . fnName . ', NULL, NULL)';
		});
	}

	## Formats call arguments: matched by parameter name, positional
	## fallback, declaration-side defaults.
	##
	## @param className: The receiver class name.
	## @param methodName: The method name.
	## @param args: The call arguments.
	## @return: Comma-joined C arguments (no receiver).
	Function of String is formatCallArguments(String is className, String is methodName, Array of NamedArg is args){
		return self:formatCallArgumentsWith(className: className, methodName: methodName, idx: -1, args: args);
	}

	## FUNCTIONS.md §I.2: binds call arguments against the STAMPED
	## overload's parameters (idx below zero resolves as the first —
	## the legacy single-member shape).
	##
	## @param className: The receiver base class name.
	## @param methodName: The called member's name.
	## @param idx: The stamped overload index.
	## @param args: The call's arguments.
	## @return: The C argument list.
	Function of String is formatCallArgumentsWith(String is className, String is methodName, Int is idx, Array of NamedArg is args){
		local Member is m: self:lookupOverloadedMemberGen(className: className, methodName: methodName, idx: idx);
		Conditional:if(check: { m:kind != MemberKind:METHOD }, then: {
			m: self:lookupMethodMember(className: className, methodName: methodName);
		});
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		local Array of String is tps: cls:typeParams;
		Conditional:if(check: { m:kind == MemberKind:METHOD }, then: {
			local Array of Parameter is params: m:params;
			Conditional:if(check: { params:length() > 0 }, then: {
				local String is joined: '';
				local Int is pIdx: 0;
				params:each(action: local Function(Parameter is p){
					local String is pName: p:name;
					local Boolean is matched: false;
					local String is argC: '0';
					args:each(action: local Function(NamedArg is a){
						Conditional:if(check: { !matched && a:name == pName && pName != '' }, then: {
							argC: self:generateExpression(expr: a:value);
							matched: true;
						});
					});
					Conditional:if(check: { !matched && pIdx < args:length() }, then: {
						local NamedArg is posArg: args:get(index: pIdx);
						Conditional:if(check: { posArg:name == '' }, then: {
							argC: self:generateExpression(expr: posArg:value);
							matched: true;
						});
					});
					Conditional:if(check: { !matched && pIdx == params:length() - 1 && args:length() > 0 }, then: {
						local NamedArg is lastArg: args:get(index: args:length() - 1);
						Conditional:if(check: { lastArg:name == '' }, then: {
							argC: self:generateExpression(expr: lastArg:value);
							matched: true;
						});
					});
					Conditional:if(check: { !matched && p:hasDefault }, then: {
						argC: self:generateExpression(expr: p:defaultExpr);
						matched: true;
					});
					# Ground the enclosing class's generic parameters to void*.
					Conditional:if(check: { tps:indexOf(search: p:paramType:name, default: -1) >= 0 }, then: {
						argC: '(void*)(intptr_t)(' . argC . ')';
					});
					joined: joined . ', ' . argC;
					pIdx: pIdx + 1;
				});
				return joined;
			});
		});
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
			Conditional:if(check: { stmt:kind == StatementKind:VAR_DECL }, then: {
				Conditional:if(check: { !self:releaseExclusions:has(key: stmt:varName) }, then: {
					local String is typeName: self:formatTypeString(t: stmt:varType);
					Conditional:if(check: { self:isArcType(typeName: typeName) }, then: {
						local String is varC: self:utils:cIdent(name: stmt:varName);
						out: out . '    if (' . varC . ') { spec_release((void*)' . varC . '); ' . varC . " = NULL; }\n";
					});
				});
			});
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
		Conditional:if(check: { c:kind == ExpressionKind:CALL && self:allEnumVariants:has(key: c:methodName) }, then: {
			local String is eName: self:allEnumVariants:getString(key: c:methodName, default: '');
			Conditional:if(check: { self:allTaggedEnums:has(key: eName) }, then: {
				return '((' . subjC . ') && (' . subjC . ')->_tag == ' . eName . '_TAG_' . self:utils:cIdent(name: c:methodName) . ')';
			});
		});
		Conditional:if(check: { c:kind == ExpressionKind:IDENT && self:allEnumVariants:has(key: c:stringValue) }, then: {
			local String is eName: self:allEnumVariants:getString(key: c:stringValue, default: '');
			Conditional:if(check: { self:allTaggedEnums:has(key: eName) }, then: {
				return '((' . subjC . ') && (' . subjC . ')->_tag == ' . eName . '_TAG_' . self:utils:cIdent(name: c:stringValue) . ')';
			});
		});
		Conditional:if(check: { c:kind == ExpressionKind:PATH && c:pathSegments:length() >= 2 && self:allTaggedEnums:has(key: c:pathSegments:get(index: 0)) }, then: {
			local String is eName: c:pathSegments:get(index: 0);
			local String is vName: c:pathSegments:get(index: 1);
			return '((' . subjC . ') && (' . subjC . ')->_tag == ' . eName . '_TAG_' . self:utils:cIdent(name: vName) . ')';
		});
		local String is cVal: self:generateExpression(expr: c);
		Conditional:if(check: { self:isStringExpr(expr: subjExpr, exprC: subjC) }, then: {
			return 'spec_string_equals(' . subjC . ', ' . cVal . ')';
		});
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
			Conditional:if(check: { c:kind == ExpressionKind:CALL && self:allEnumVariants:has(key: c:methodName) }, then: {
				local String is eName: self:allEnumVariants:getString(key: c:methodName, default: '');
				Conditional:if(check: { self:allTaggedEnums:has(key: eName) }, then: {
					local Member is vMem: self:lookupEnumVariant(enumName: eName, variantName: c:methodName);
					local String is vNameC: self:utils:cIdent(name: c:methodName);
					local Int is idx: 0;
					c:methodArgs:each(action: local Function(NamedArg is arg){
						Conditional:if(check: { idx < vMem:params:length() }, then: {
							local Expression is av: arg:value;
							Conditional:if(check: { av:kind == ExpressionKind:IDENT }, then: {
								local Parameter is pDef: vMem:params:get(index: idx);
								local String is bindName: av:stringValue;
								self:localVars:set(key: bindName, value: self:formatTypeString(t: pDef:paramType));
								local String is pCType: self:cTypeFor(typeName: pDef:paramType:name);
								binds: binds . '        ' . pCType . ' ' . self:utils:cIdent(name: bindName) . ' = (' . subjC . ')->' . vNameC . '_' . self:utils:cIdent(name: pDef:name) . ";\n";
							});
						});
						idx: idx + 1;
					});
				});
			});
		});
		return binds;
	}

	## Resolves a simple local or self-field target to its C lvalue.
	##
	## @param expr: The target expression.
	## @return: C lvalue string, or '' when complex.
	Function of String is tryGenerateTargetOnly(Expression is expr){
		Conditional:if(check: { expr:kind == ExpressionKind:IDENT }, then: {
			Conditional:if(check: { self:localVars:has(key: expr:stringValue) }, then: {
				return self:utils:cIdent(name: expr:stringValue);
			});
			Conditional:if(check: { self:inMethod && self:fieldTypes:has(key: expr:stringValue) }, then: {
				return 'self->' . self:utils:cIdent(name: expr:stringValue);
			});
			return self:utils:cIdent(name: expr:stringValue);
		});
		Conditional:if(check: { expr:kind == ExpressionKind:PATH && expr:pathSegments:length() == 2 && expr:pathSegments:get(index: 0) == self:names:selfIdent() }, then: {
			return 'self->' . self:utils:cIdent(name: expr:pathSegments:get(index: 1));
		});
		return '';
	}

	## Optimizes left-recursive concat chains into spec_string_append.
	##
	## @param expr: The right-hand side expression.
	## @param targetC: The target lvalue C.
	## @return: Append-chain C, or '' when not optimizable.
	Function of String is tryGenerateAppendChain(Expression is expr, String is targetC){
		Conditional:if(check: { targetC == '' }, then: {
			return '';
		});
		Conditional:if(check: { expr:kind == ExpressionKind:BINARY && expr:binaryOp == '.' }, then: {
			local String is leftTarget: self:tryGenerateTargetOnly(expr: expr:leftExpr);
			Conditional:if(check: { leftTarget == targetC }, then: {
				local String is rhsC: self:wrapToString(expr: expr:rightExpr, exprC: self:generateExpression(expr: expr:rightExpr));
				Conditional:if(check: { rhsC:contains(needle: targetC) }, then: {
					return '';
				});
				return 'spec_string_concat(' . targetC . ', ' . rhsC . ')';
			});
			local String is innerChain: self:tryGenerateAppendChain(expr: expr:leftExpr, targetC: targetC);
			Conditional:if(check: { innerChain != '' }, then: {
				local String is rhsC: self:wrapToString(expr: expr:rightExpr, exprC: self:generateExpression(expr: expr:rightExpr));
				Conditional:if(check: { rhsC:contains(needle: targetC) }, then: {
					return '';
				});
				return 'spec_string_concat(' . innerChain . ', ' . rhsC . ')';
			});
		});
		return '';
	}

	## Generates C for a statement node.
	##
	## @param stmt: The statement node.
	## @return: C statement code.
	Function of String is generateStatement(Statement is stmt){
		Conditional:if(check: { stmt:line > 0 }, then: {

		});
		local StatementKind is kind: stmt:kind;

		when (kind) {
			is StatementKind:VAR_DECL: {
				return self:emitVarDecl(stmt: stmt);
			}
			is StatementKind:ASSIGN: {
				return self:emitAssign(stmt: stmt);
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
				Conditional:if(check: { stmt:exprStmt:kind == ExpressionKind:CALL && !self:yieldsClaim(expr: stmt:exprStmt) && self:isArcType(typeName: resT) }, then: {
					return '    spec_release((void*)(' . exprC . "));\n";
				});
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

	## Emits a variable declaration with the typed constructor.
	##
	## @param stmt: The VAR_DECL statement.
	## @return: C declaration.
	Function of String is emitVarDecl(Statement is stmt){
		self:localVars:set(key: stmt:varName, value: self:formatVarTypeString(t: stmt:varType));
		self:localScopeVars:set(key: stmt:varName, value: stmt:varType:name);
		local String is vTypeName: stmt:varType:name;
		local String is cType: '';
		Conditional:if(check: { vTypeName == 'List' }, then: {
			cType: self:cTypeFor(typeName: self:formatTypeString(t: stmt:varType));
		}, else: {
			cType: self:cTypeFor(typeName: vTypeName);
		});
		local String is varName: self:utils:cIdent(name: stmt:varName);
		local Boolean is isArcVar: self:isArcType(typeName: vTypeName);
		local String is autoPrefix: Conditional:if(check: { isArcVar }, then: { 'SPEC_AUTO ' }, else: { '' });
		# FUNCTIONS.md Part IV memory discipline: a hoisted local's
		# declaration lives in the funnel prologue (zero-initialized) — the
		# statement assigns, so a goto can never skip the initializer.
		Conditional:if(check: { self:hoistedLocals:has(key: stmt:varName) }, then: {
			Conditional:if(check: { stmt:hasInit }, then: {
				local ExpressionKind is hInitKind: stmt:initExpr:kind;
				Conditional:if(check: { hInitKind == ExpressionKind:ARRAY || hInitKind == ExpressionKind:MAP }, then: {
					self:setContainerHint(t: self:formatTypeString(t: stmt:varType));
				});
				local Boolean is hSavedArg: self:argMode;
				self:argMode: false;
				local String is hInitC: self:generateExpression(expr: stmt:initExpr);
				self:argMode: hSavedArg;
				self:setContainerHint(t: '');
				local Boolean is hClaims: self:yieldsClaim(expr: stmt:initExpr);
				hInitC: self:generateTypedConstructor(typeName: vTypeName, valueC: hInitC, cType: cType, claims: hClaims);
				return '    ' . varName . ' = ' . hInitC . ";\n";
			});
			Conditional:if(check: { vTypeName == 'String' }, then: {
				return '    ' . varName . " = \"\";\n";
			});
			Conditional:if(check: { vTypeName == 'Array' }, then: {
				local String is hElemKind: self:containerElemKind(containerType: self:formatTypeString(t: stmt:varType));
				local String is hNewCall: 'spec_array_new()';
				Conditional:if(check: { hElemKind == 'object' || hElemKind == 'string' }, then: {
					hNewCall: 'spec_array_new_object()';
				});
				return '    ' . varName . ' = ' . hNewCall . ";\n";
			});
			Conditional:if(check: { vTypeName == 'List' }, then: {
				local String is hFullT: self:formatTypeString(t: stmt:varType);
				local String is hElemKind: self:containerElemKind(containerType: hFullT);
				local String is hNewCall: 'spec_vec_new()';
				Conditional:if(check: { hElemKind == 'byte' }, then: {
					hNewCall: 'spec_bytebuffer_new()';
				}, else: {
					Conditional:if(check: { hElemKind == 'string' }, then: {
						hNewCall: 'spec_vec_new_string()';
					}, else: {
						Conditional:if(check: { hElemKind == 'object' }, then: {
							hNewCall: 'spec_vec_new_object()';
						});
					});
				});
				return '    ' . varName . ' = ' . hNewCall . ";\n";
			});
			Conditional:if(check: { vTypeName == 'Map' }, then: {
				local String is hNewCall: 'spec_map_new()';
				Conditional:if(check: { self:containerElemIsArc(containerType: self:formatTypeString(t: stmt:varType)) }, then: {
					hNewCall: 'spec_map_new_object()';
				});
				return '    ' . varName . ' = ' . hNewCall . ";\n";
			});
			return '';
		});
		Conditional:if(check: { stmt:hasInit }, then: {
			local ExpressionKind is initKind: stmt:initExpr:kind;
			Conditional:if(check: { initKind == ExpressionKind:ARRAY || initKind == ExpressionKind:MAP }, then: {
				self:setContainerHint(t: self:formatTypeString(t: stmt:varType));
			});
			local Boolean is savedArg: self:argMode;
			self:argMode: false;
			local String is initC: self:generateExpression(expr: stmt:initExpr);
			self:argMode: savedArg;
			self:setContainerHint(t: '');
			local Boolean is claims: self:yieldsClaim(expr: stmt:initExpr);
			initC: self:generateTypedConstructor(typeName: vTypeName, valueC: initC, cType: cType, claims: claims);
			return '    ' . autoPrefix . cType . ' ' . varName . ' = ' . initC . ";\n";
		});
		Conditional:if(check: { vTypeName == 'String' }, then: {
			return '    ' . cType . ' ' . varName . " = \"\";\n";
		});
		Conditional:if(check: { vTypeName == 'Array' }, then: {
			local String is elemKind: self:containerElemKind(containerType: self:formatTypeString(t: stmt:varType));
			local String is newCall: 'spec_array_new()';
			Conditional:if(check: { elemKind == 'object' || elemKind == 'string' }, then: {
				newCall: 'spec_array_new_object()';
			});
			return '    ' . autoPrefix . cType . ' ' . varName . ' = ' . newCall . ";\n";
		});
		Conditional:if(check: { vTypeName == 'List' }, then: {
			local String is fullT: self:formatTypeString(t: stmt:varType);
			local String is elemKind: self:containerElemKind(containerType: fullT);
			local String is newCall: 'spec_vec_new()';
			Conditional:if(check: { elemKind == 'byte' }, then: {
				newCall: 'spec_bytebuffer_new()';
			}, else: {
				Conditional:if(check: { elemKind == 'string' }, then: {
					newCall: 'spec_vec_new_string()';
				}, else: {
					Conditional:if(check: { elemKind == 'object' }, then: {
						newCall: 'spec_vec_new_object()';
					});
				});
			});
			return '    ' . autoPrefix . cType . ' ' . varName . ' = ' . newCall . ";\n";
		});
		Conditional:if(check: { vTypeName == 'Map' }, then: {
			local String is newCall: 'spec_map_new()';
			Conditional:if(check: { self:containerElemIsArc(containerType: self:formatTypeString(t: stmt:varType)) }, then: {
				newCall: 'spec_map_new_object()';
			});
			return '    ' . autoPrefix . cType . ' ' . varName . ' = ' . newCall . ";\n";
		});
		return '    ' . autoPrefix . cType . ' ' . varName . " = 0;\n";
	}

	## Emits an assignment: container stores, concat-chain optimization,
	## ARC spec_assign.
	##
	## @param stmt: The ASSIGN statement.
	## @return: C assignment.
	Function of String is emitAssign(Statement is stmt){
		Conditional:if(check: { stmt:assignTarget:kind == ExpressionKind:INDEX }, then: {
			local String is containerC: self:generateExpression(expr: stmt:assignTarget:leftExpr);
			local String is idxC: self:generateExpression(expr: stmt:assignTarget:rightExpr);
			local String is containerType: self:inferTargetType(expr: stmt:assignTarget:leftExpr);
			local Boolean is savedArgIx: self:argMode;
			self:argMode: false;
			local String is valC: self:generateExpression(expr: stmt:assignValue);
			self:argMode: savedArgIx;
			Conditional:if(check: { containerType:startsWith(prefix: 'Map:') || containerType == 'Map' }, then: {
				Conditional:if(check: { containerType:contains(needle: 'String:String') || containerType:contains(needle: 'to String') || self:isStringExpr(expr: stmt:assignValue, exprC: valC) }, then: {
					return '    spec_map_set(' . containerC . ', ' . idxC . ', ' . valC . ");\n";
				});
				return '    spec_map_set_any(' . containerC . ', ' . idxC . ', (void*)(intptr_t)(' . valC . "));\n";
			});
			return '    spec_array_set(' . containerC . ', ' . idxC . ', (void*)(intptr_t)(' . valC . "));\n";
		});
		local String is targetC: self:generateExpression(expr: stmt:assignTarget);
		local String is appendC: self:tryGenerateAppendChain(expr: stmt:assignValue, targetC: targetC);
		Conditional:if(check: { appendC != '' }, then: {
			return '    ' . targetC . ' = ' . appendC . ";\n";
		});
		local String is lhsType: self:inferTargetType(expr: stmt:assignTarget);
		local ExpressionKind is valKind: stmt:assignValue:kind;
		Conditional:if(check: { (valKind == ExpressionKind:ARRAY || valKind == ExpressionKind:MAP) && (lhsType:startsWith(prefix: 'Array') || lhsType:startsWith(prefix: 'Map') || lhsType:startsWith(prefix: 'List')) }, then: {
			self:setContainerHint(t: lhsType);
		});
		local Boolean is savedArg: self:argMode;
		self:argMode: false;
		local String is valC: self:generateExpression(expr: stmt:assignValue);
		self:argMode: savedArg;
		local ClassInfo is curCls: self:findClass(name: self:currentClassName);
		Conditional:if(check: { curCls:typeParams:indexOf(search: lhsType, default: -1) >= 0 }, then: {
			valC: '(void*)(intptr_t)(' . valC . ')';
		});
		local Boolean is isArcLhs: self:isArcType(typeName: lhsType);
		Conditional:if(check: { isArcLhs }, then: {
			# Parameters are borrows: overwriting one retains the new value
			# but must not release the caller's argument.
			Conditional:if(check: { stmt:assignTarget:kind == ExpressionKind:IDENT && self:currentParams:has(key: stmt:assignTarget:stringValue) }, then: {
				return '    spec_retain((void*)(' . valC . ')); ' . targetC . ' = ' . valC . ";\n";
			});
			return '    spec_assign((void**)&' . targetC . ', (void*)(' . valC . "));\n";
		});
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
			Conditional:if(check: { dispatchCls == '' }, then: {
				local String is implCls: self:findMethodImplementingClass(className: baseName, methodName: self:currentMethodName, paramCount: -1);
				Conditional:if(check: { implCls != '' }, then: {
					dispatchCls: implCls;
				});
			});
		});
		Conditional:if(check: { dispatchCls == '' }, then: {
			return '';
		});
		local Member is superM: self:lookupMethodMember(className: dispatchCls, methodName: self:currentMethodName);
		local String is argsC: self:formatCallArguments(className: dispatchCls, methodName: self:currentMethodName, args: stmt:forwardArgs);
		local String is callC: dispatchCls . '_' . self:currentMethodName . '((' . dispatchCls . '*)self' . argsC . ')';
		local String is superRet: self:resolveReturnType(t: superM:memberType);
		Conditional:if(check: { superRet != 'void' }, then: {
			return '    return ' . callC . ";\n";
		});
		return '    ' . callC . ";\n";
	}

	## Emits a return with ARC ownership transfer.
	##
	## @param stmt: The RETURN statement.
	## @return: C return.
	Function of String is emitReturn(Statement is stmt){
		Conditional:if(check: { self:inlineReturnLabel != '' }, then: {
			Conditional:if(check: { stmt:hasReturnExpr && self:inlineReturnVar != '' }, then: {
				local String is retC: self:generateExpression(expr: stmt:returnExpr);
				return '    ' . self:inlineReturnVar . ' = ' . retC . "; break;\n";
			});
			return "    break;\n";
		});
		Conditional:if(check: { stmt:hasReturnExpr }, then: {
			local ExpressionKind is retKind: stmt:returnExpr:kind;
			Conditional:if(check: { (retKind == ExpressionKind:ARRAY || retKind == ExpressionKind:MAP) && (self:currentMethodReturnType:startsWith(prefix: 'Array') || self:currentMethodReturnType:startsWith(prefix: 'Map')) }, then: {
				self:setContainerHint(t: self:currentMethodReturnType);
			});
			local Boolean is savedArg: self:argMode;
			self:argMode: false;
			local String is retC: self:generateExpression(expr: stmt:returnExpr);
			self:argMode: savedArg;
			local ClassInfo is curCls: self:findClass(name: self:currentClassName);
			Conditional:if(check: { curCls:typeParams:indexOf(search: self:currentMethodReturnType, default: -1) >= 0 }, then: {
				retC: '(void*)(intptr_t)(' . retC . ')';
			}, else: {
				Conditional:if(check: { self:isArcType(typeName: self:currentMethodReturnType) }, then: {
					local Boolean is ownedLocal: retKind == ExpressionKind:IDENT && self:localScopeVars:has(key: stmt:returnExpr:stringValue);
					Conditional:if(check: { ownedLocal }, then: {
						local String is identC: self:utils:cIdent(name: stmt:returnExpr:stringValue);
						local String is rtC: self:cTypeFor(typeName: self:currentMethodReturnType);
						retC: '(' . rtC . ')({ ' . rtC . ' _ret_val = ' . identC . '; ' . identC . " = NULL; _ret_val; })";
					}, else: {
						Conditional:if(check: { self:isFreshConstructorCall(expr: stmt:returnExpr) }, then: {
							retC: '(' . self:cTypeFor(typeName: self:currentMethodReturnType) . ')(' . retC . ')';
						}, else: {
							retC: '(' . self:cTypeFor(typeName: self:currentMethodReturnType) . ')spec_retain((void*)(' . retC . '))';
						});
					});
				});
			});
			# FUNCTIONS.md Part IV memory discipline: the return funnels
			# through the method's cleanup label so the scope releases run
			# on this exit path too.
			Conditional:if(check: { self:cleanupLabel != '' }, then: {
				Conditional:if(check: { self:cleanupRetVar != '' }, then: {
					return '    ' . self:cleanupRetVar . ' = ' . retC . ";\n    goto " . self:cleanupLabel . ";\n";
				});
				return '    goto ' . self:cleanupLabel . ";\n";
			});
			return '    return ' . retC . ";\n";
		});
		Conditional:if(check: { self:cleanupLabel != '' }, then: {
			return '    goto ' . self:cleanupLabel . ";\n";
		});
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
			Conditional:if(check: { arm:isElse }, then: {
				out: out . "    } else {\n";
			}, else: {
				local String is condOr: '';
				arm:conditions:each(action: local Function(Expression is c){
					local String is cmp: self:generateWhenCondition(subjExpr: stmt:whenSubject, subjC: subjC, c: c);
					Conditional:if(check: { condOr == '' }, then: {
						condOr: cmp;
					}, else: {
						condOr: condOr . ' || ' . cmp;
					});
				});
				local String is bindsC: self:generateWhenBindings(subjC: subjC, arm: arm);
				Conditional:if(check: { first }, then: {
					out: out . '    if (' . condOr . ") {\n";
					first: false;
				}, else: {
					out: out . '    } else if (' . condOr . ") {\n";
				});
				out: out . bindsC;
			});
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
	## structural C-floor annotation (the namespace is the annotation).
	##
	## @param name: Class name.
	## @return: true when the class is a floor binding.
	Function of Boolean is isSysinternalClass(String is name){
		local ClassInfo is c: self:findClass(name: name);
		Conditional:if(check: { c:name == '' }, then: {
			return false;
		});
		return self:policy:isSysinternal(cls: c);
	}

	Function of String is generateMethod(ClassInfo is classDef, Member is method){
		self:inMethod: true;
		self:currentMethodName: method:name;
		self:currentMethodReturnType: self:formatTypeString(t: method:memberType);
		local String is retType: self:resolveReturnType(t: method:memberType);
		Conditional:if(check: { retType == 'void' }, then: {
			Conditional:if(check: { method:name == ContractMethod:EVALUATE:value() || method:name == ContractMethod:ITERATION:value() }, then: {
				retType: 'bool';
			});
		});

		self:localVars: Map:init();
		self:localScopeVars: Map:init();
		self:currentParams: Map:init();
		method:params:each(action: local Function(Parameter is p){
			self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
			self:currentParams:set(key: p:name, value: 'true');
		});

		# IV.2c: the self parameter's C type qualifies — the bare name is
		# not a C identity for nested classes.
		local String is selfCType: self:cTypeFor(typeName: classDef:qualifiedName());
		# IV.2c: the method's own identity drives its symbol — a bare
		# inner-class name would first-match whichever same-named class
		# registered first; classDef IS the declaring class.
		local String is header: retType . ' ' . self:overloadSymbol(className: classDef:qualifiedName(), methodName: method:name, idx: self:overloadIndexOf(classDef: classDef, method: method)) . '(' . selfCType . ' self';
		method:params:each(action: local Function(Parameter is p){
			header: header . ', ' . self:cTypeFor(typeName: p:paramType:name) . ' ' . self:utils:cIdent(name: p:name);
		});
		header: header . ") {\n";

		# Body first: unused-parameter suppressions need the finished text.
		# The accumulator is a fresh mutable buffer grown IN PLACE — a concat
		# per statement would copy the whole body each time (quadratic).
		local String is bodyC: Buf:stringCopy(b: '');

		# FUNCTIONS.md Part IV memory discipline: the scope-end releases
		# move under a cleanup label and every return funnels through it —
		# a trailing release list is dead code after any return, which
		# leaked every early-returning method's locals. Void methods funnel
		# too: a bare `return` skips the releases just the same.
		self:cleanupCounter: self:cleanupCounter + 1;
		local String is releasesC: self:scopeReleases(stmts: method:body);
		Conditional:if(check: { releasesC:length() > 0 }, then: {
			self:cleanupLabel: '_cleanup_' . (self:cleanupCounter as String);
		});
		Conditional:if(check: { retType != 'void' && self:cleanupLabel != '' }, then: {
			self:cleanupRetVar: '_mret_' . (self:cleanupCounter as String);
		});
		# The funnel's goto must never jump over an initializer a release
		# reads: the top-level ARC locals hoist to zero-initialized
		# declarations in the prologue; their statements assign.
		Conditional:if(check: { self:cleanupLabel != '' }, then: {
			method:body:each(action: local Function(Statement is vs){
				Conditional:if(check: { vs:kind == StatementKind:VAR_DECL && self:isArcType(typeName: vs:varType:name) }, then: {
					local String is hType: '';
					Conditional:if(check: { vs:varType:name == 'List' }, then: {
						hType: self:cTypeFor(typeName: self:formatTypeString(t: vs:varType));
					}, else: {
						hType: self:cTypeFor(typeName: vs:varType:name);
					});
					self:hoistedLocals:set(key: vs:varName, value: hType);
				});
			});
		});

		Conditional:if(check: { self:cleanupRetVar != '' }, then: {
			Buf:bufAppendBuf(dst: bodyC, src: '    ' . retType . ' ' . self:cleanupRetVar . " = 0;\n");
		});
		self:hoistedLocals:each(action: local Function(String is hName){
			local String is hType: self:hoistedLocals:getString(key: hName, default: '');
			Buf:bufAppendBuf(dst: bodyC, src: '    SPEC_AUTO ' . hType . ' ' . self:utils:cIdent(name: hName) . " = 0;\n");
		});
		method:body:each(action: local Function(Statement is stmt){
			local String is stmtC: self:generateStatement(stmt: stmt);
			Buf:bufAppendBuf(dst: bodyC, src: stmtC);
		});

		Conditional:if(check: { method:body:length() == 0 && retType != 'void' }, then: {
			bodyC: bodyC . "    return 0;\n";
		});

		Conditional:if(check: { self:cleanupLabel != '' }, then: {
			# The funnel: releases run on the fall-through too. The return
			# variable is pre-zeroed, so a fall-through on a non-void body
			# behaves like the old trailing form.
			bodyC: bodyC . '    ' . self:cleanupLabel . ": ;\n";
			bodyC: bodyC . releasesC;
			Conditional:if(check: { self:cleanupRetVar != '' }, then: {
				bodyC: bodyC . '    return ' . self:cleanupRetVar . ";\n";
			}, else: {
				bodyC: bodyC . "    return;\n";
			});
			self:cleanupLabel: '';
			self:cleanupRetVar: '';
		}, else: {
			# Bodies without ARC locals keep the plain trailing form.
			bodyC: bodyC . releasesC;
		});

		# Unused-parameter suppressions: the (void) cast is legal on used
		# params too, and substring use-checks false-positive on names
		# appearing inside string literals. Emit for every param always.
		local String is suppressions: "    (void)self;\n";
		method:params:each(action: local Function(Parameter is p){
			suppressions: suppressions . '    (void)' . self:utils:cIdent(name: p:name) . ";\n";
		});

		self:hoistedLocals: Map:init();
		self:inMethod: false;
		return header . suppressions . bodyC . "}\n\n";
	}

	## Generates the C main entry point with argv->Map parsing.
	##
	## @param entryClass: The entry class name.
	## @return: C main function.
	Function of String is generateMain(String is entryClass){
		local String is m: "/* Application Entry Point */\n";
		m: m . "int main(int argc, char** argv) {\n";

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
			Conditional:if(check: { !self:policy:isTransparent(c: c) || c:name == 'String' || c:name == 'Array' || c:name == 'Map' }, then: {
				self:currentClassName: c:name;
				# FUNCTIONS.md Part IV IV.2c: the C symbol base qualifies for
				# nested classes (Outer_Helper); the bare name for top-level.
				local String is cSym: self:utils:cIdent(name: c:qualifiedName());
				self:fieldTypes: Map:init();
				local Array of Member is allFields: [];
				local Array of Member is outerFields: [];
				self:declGen:collectStructFieldsSplit(c: c, allClasses: flattenedClasses, acc: allFields, outerAcc: outerFields, fromOuterLink: false);
				allFields:each(action: local Function(Member is m){
					self:fieldTypes:set(key: m:name, value: self:formatTypeString(t: m:memberType));
				});
				outerFields:each(action: local Function(Member is m){
					self:fieldTypes:set(key: m:name, value: self:formatTypeString(t: m:memberType));
				});

				local Boolean is hasInit: false;
				c:members:each(action: local Function(Member is m){
					when (m:kind) {
						is MemberKind:METHOD: {
							Conditional:if(check: { !self:policy:isTransparent(c: c) || m:body:length() > 0 }, then: {
								Conditional:if(check: { m:name == 'init' }, then: {
 hasInit: true;
								});
								methods: methods . self:generateMethod(classDef: c, method: m);
							});
						}
						else: {}
					}
				});
				Conditional:if(check: { !hasInit && !self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader() }, then: {
					methods: methods . 'void ' . cSym . '_init(' . cSym . "* self) {\n    (void)self;\n}\n\n";
				});

				local Boolean is hasToString: false;
				c:members:each(action: local Function(Member is m){
					Conditional:if(check: { m:name == 'toString' }, then: {
 hasToString: true;
					});
				});
				Conditional:if(check: { !hasToString && !self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader() }, then: {
					# IV.2c: the synthesized contract symbol and self type
					# qualify — the bare name is not a C identity for nested
					# classes.
					methods: methods . 'String ' . cSym . '_toString(' . cSym . "* self) {\n";
					methods: methods . "    if (!self) { return spec_string_intern(\"\"); }\n";
					methods: methods . '    return spec_string_intern("' . c:qualifiedName() . '");' . "\n}\n\n";
				});
			});
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
			Conditional:if(check: { acc:indexOf(search: baseName, default: -1) < 0 }, then: {
				acc:add(item: baseName);
				allClasses:each(action: local Function(ClassInfo is cand){
					Conditional:if(check: { cand:name == baseName }, then: {
						self:collectAncestors(c: cand, allClasses: allClasses, acc: acc);
					});
				});
			});
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
			Conditional:if(check: { !self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader() }, then: {
				local Array of String is ancestors: [];
				self:collectAncestors(c: c, allClasses: classes, acc: ancestors);
				Conditional:if(check: { ancestors:length() > 0 }, then: {
					out: out . '    if (strcmp(actual, "' . c:qualifiedName() . "\") == 0) {\n";
					out: out . '        return ';
					local Boolean is firstA: true;
					ancestors:each(action: local Function(String is aName){
						Conditional:if(check: { !firstA }, then: {
 out: out . ' || ';
						});
						out: out . '(strcmp(target, "' . aName . '") == 0)';
						firstA: false;
					});
					out: out . ";\n    }\n";
				});
			});
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
		Conditional:if(check: { self:methodSlotCount == 0 }, then: {
			return out;
		});
		classes:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { !self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader() }, then: {
				local String is cSym: self:utils:cIdent(name: c:qualifiedName());
				out: out . 'static void* ' . cSym . '_vtable[' . self:methodSlotCount . "] = {\n";
				local Int is slot: 0;
				Loops:loop(
					evaluate: local Function of Boolean(){
						return slot < self:methodSlotCount;
					},
					iteration: local Function of Boolean(){
						local String is mName: self:slotNames:get(index: slot);
						local String is implCls: self:findMethodImplementingClass(className: c:name, methodName: mName, paramCount: -1);
						Conditional:if(check: { slot > 0 }, then: {
							out: out . ",\n";
						});
						Conditional:if(check: { implCls == '' }, then: {
							out: out . '    (void*)0';
						}, else: {
							out: out . '    (void*)' . implCls . '_' . mName;
						});
						slot: slot + 1;
						return true;
					}
				);
				out: out . "\n};\n\n";
			});
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
			Conditional:if(check: { !self:policy:isTransparent(c: c) && c:baseClass != self:names:enumHeader() }, then: {
				self:currentClassName: c:name;
				local String is cSym: self:utils:cIdent(name: c:qualifiedName());
				self:fieldTypes: Map:init();
				local Array of Member is allFields: [];
				local Array of Member is outerFields: [];
				self:declGen:collectStructFieldsSplit(c: c, allClasses: classes, acc: allFields, outerAcc: outerFields, fromOuterLink: false);
				allFields:each(action: local Function(Member is f){
					self:fieldTypes:set(key: f:name, value: self:formatTypeString(t: f:memberType));
				});
				outerFields:each(action: local Function(Member is f){
					self:fieldTypes:set(key: f:name, value: self:formatTypeString(t: f:memberType));
				});

				out: out . 'void ' . cSym . "_destroy(void* self_ptr) {\n";
				out: out . '    ' . cSym . '* self = (' . cSym . "*)self_ptr;\n";
				out: out . "    if (!self) return;\n";
				allFields:each(action: local Function(Member is m){
					local String is ft: m:memberType:name;
					Conditional:if(check: { self:isArcType(typeName: ft) }, then: {
						out: out . '    if (self->' . self:utils:cIdent(name: m:name) . ') { spec_release((void*)self->' . self:utils:cIdent(name: m:name) . '); self->' . self:utils:cIdent(name: m:name) . " = NULL; }\n";
					});
				});
				outerFields:each(action: local Function(Member is m){
					local String is ft: m:memberType:name;
					Conditional:if(check: { self:isArcType(typeName: ft) }, then: {
						out: out . '    if (self->' . self:utils:cIdent(name: m:name) . ') { spec_release((void*)self->' . self:utils:cIdent(name: m:name) . '); self->' . self:utils:cIdent(name: m:name) . " = NULL; }\n";
					});
				});
				out: out . "}\n\n";

				out: out . cSym . '* ' . cSym . "_new(void) {\n";
				# FUNCTIONS.md Part IV memory discipline: every class
				# allocates through ARC — refcounts drive the frees, so the
				# parser's tokens, the loop objects, and every transient
				# reclaim their memory during compilation. The old
				# compiler-phase arena made everything immortal and turned
				# the peak into total allocation volume.
				out: out . '    ' . cSym . '* self = (' . cSym . '*)spec_alloc(sizeof(' . cSym . '), ' . cSym . "_destroy);\n";
				out: out . '    self->_type_name = "' . c:qualifiedName() . "\";\n";
				Conditional:if(check: { self:methodSlotCount > 0 }, then: {
					out: out . '    self->_vtable = ' . cSym . "_vtable;\n";
				});
				# FUNCTIONS.md Part IV IV.2: the construction expressions run for
				# the declared-of + own fields; the OUTER-link fields zero-init
				# (an inner instance starts with an empty parent-part — the
				# enclosing class's containers must not allocate per inner
				# instantiation: the hot-path scan loops).
				allFields:each(action: local Function(Member is m){
					Conditional:if(check: { m:hasInit }, then: {
						local Boolean is savedArgFi: self:argMode;
						self:argMode: false;
						local String is fieldInitC: self:generateExpression(expr: m:initExpr);
						self:argMode: savedArgFi;
						local String is ftn: m:memberType:name;
						Conditional:if(check: { self:isArcType(typeName: ftn) }, then: {
							fieldInitC: '(' . self:cTypeFor(typeName: ftn) . ')spec_retain((void*)(' . fieldInitC . '))';
						});
						out: out . '    self->' . self:utils:cIdent(name: m:name) . ' = ' . fieldInitC . ";\n";
					});
				});
				outerFields:each(action: local Function(Member is m){
					Conditional:if(check: { self:isArcType(typeName: m:memberType:name) }, then: {
						out: out . '    self->' . self:utils:cIdent(name: m:name) . " = NULL;\n";
					}, else: {
						out: out . '    self->' . self:utils:cIdent(name: m:name) . " = 0;\n";
					});
				});
				out: out . "    return self;\n}\n\n";
			});
		});
		return out;
	}
	## Inlines an anonymous-function callback over an Array as a C loop
	## (each/filter/count/any/map). These inline to give the
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
		Conditional:if(check: { mode == 'each' }, then: {
			self:inlineReturnVar: '';
		}, else: {
			self:inlineReturnVar: '_pred_' . id;
		});

		local Map of String to String is savedVars: Map:init();
		local Array of String is outerKeys: self:localVars:keys();
		outerKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
		});

		local String is paramDecl: '';
		Conditional:if(check: { fnExpr:anonParams:length() > 0 }, then: {
			local Parameter is p: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
			local String is pCType: self:cTypeFor(typeName: p:paramType:name);
			local String is pRaw: '(' . pCType . ')(intptr_t)_a_' . id . '->items[_i_' . id . ']';
			paramDecl: '        ' . pCType . ' ' . self:utils:cIdent(name: p:name) . ' = ' . pRaw . ";\n";
		});

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

		Conditional:if(check: { mode == 'each' }, then: {
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . "        do {\n" . bodyC . "        } while (0);\n    } } })";
			return out;
		});
		Conditional:if(check: { mode == 'filter' }, then: {
			local String is outVar: '_out_' . id;
			local String is outNewC: 'spec_array_new()';
			Conditional:if(check: { fnExpr:anonParams:length() > 0 }, then: {
				local Parameter is p0: fnExpr:anonParams:get(index: 0);
				local String is pName: p0:paramType:name;
				Conditional:if(check: { self:isArcType(typeName: pName) || pName == 'String' }, then: {
					outNewC: 'spec_array_new_object()';
				});
			});
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; SpecArray* ' . outVar . ' = ' . outNewC . '; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . '        bool ' . predVar . " = false;\n        do {\n" . bodyC . "        } while (0);\n        if (" . predVar . ') spec_array_add(' . outVar . ', ' . arrVar . '->items[' . idxVar . "]);\n    } } " . outVar . '; })';
			return out;
		});
		Conditional:if(check: { mode == 'count' }, then: {
			local String is cntVar: '_cnt_' . id;
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; long long ' . cntVar . ' = 0; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . '        bool ' . predVar . " = false;\n        do {\n" . bodyC . "        } while (0);\n        if (" . predVar . ') ' . cntVar . "++;\n    } } " . cntVar . '; })';
			return out;
		});
		Conditional:if(check: { mode == 'any' }, then: {
			local String is fndVar: '_fnd_' . id;
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; bool ' . fndVar . ' = false; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . '        bool ' . predVar . " = false;\n        do {\n" . bodyC . "        } while (0);\n        if (" . predVar . ') { ' . fndVar . " = true; break; }\n    } } " . fndVar . '; })';
			return out;
		});
		Conditional:if(check: { mode == 'map' }, then: {
			local String is outVar: '_out_' . id;
			local String is retCType: self:cTypeFor(typeName: fnExpr:anonReturnType:name);
			Conditional:if(check: { retCType == 'void' }, then: {
 retCType: 'void*';
			});
			self:inlineReturnArc: retCType:charAt(index: retCType:length() - 1, default: '') == '*';
			local String is outNewC: 'spec_array_new()';
			Conditional:if(check: { self:isArcType(typeName: fnExpr:anonReturnType:name) || fnExpr:anonReturnType:name == 'String' }, then: {
				outNewC: 'spec_array_new_object()';
			});
			local String is out: '({ SpecArray* ' . arrVar . ' = ' . targetC . '; SpecArray* ' . outVar . ' = ' . outNewC . '; if (' . arrVar . ') { for (size_t ' . idxVar . ' = 0; ' . idxVar . ' < ' . arrVar . '->length; ' . idxVar . "++) {\n";
			out: out . paramDecl . '        ' . retCType . ' ' . predVar . " = 0;\n        do {\n" . bodyC . "        } while (0);\n        spec_array_add(" . outVar . ', (void*)(intptr_t)(' . predVar . "));\n    } } " . outVar . '; })';
			return out;
		});
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
		Conditional:if(check: { accTypeName == '' && fnExpr:anonReturnType:name != 'Void' && fnExpr:anonReturnType:name != 'void' }, then: {
			accTypeName: fnExpr:anonReturnType:name;
		});
		local String is accCType: self:cTypeFor(typeName: accTypeName);
		Conditional:if(check: { accCType == 'void' }, then: {
 accCType: 'long long';
		});

		self:inlineReturnVar: accVar;
		self:inlineReturnLabel: 'break';
		local Boolean is savedArc: self:inlineReturnArc;
		self:inlineReturnArc: accCType:charAt(index: accCType:length() - 1, default: '') == '*';

		local String is paramDecl: '';
		Conditional:if(check: { fnExpr:anonParams:length() >= 1 }, then: {
			local Parameter is p0: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p0:name, value: accTypeName);
			paramDecl: paramDecl . '        ' . accCType . ' ' . self:utils:cIdent(name: p0:name) . ' = ' . accVar . ";\n";
		});
		Conditional:if(check: { fnExpr:anonParams:length() >= 2 }, then: {
			local Parameter is p1: fnExpr:anonParams:get(index: 1);
			self:localVars:set(key: p1:name, value: self:formatTypeString(t: p1:paramType));
			local String is p1CType: self:cTypeFor(typeName: p1:paramType:name);
			local String is p1Raw: '(' . p1CType . ')(intptr_t)' . arrVar . '->items[' . idxVar . ']';
			paramDecl: paramDecl . '        ' . p1CType . ' ' . self:utils:cIdent(name: p1:name) . ' = ' . p1Raw . ";\n";
		});

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
		Conditional:if(check: { fnExpr:anonParams:length() >= 1 }, then: {
			local Parameter is p0: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p0:name, value: 'String');
			paramDecl: paramDecl . '            String ' . self:utils:cIdent(name: p0:name) . ' = spec_string_from_chars(' . eVar . "->key);\n";
		});
		Conditional:if(check: { fnExpr:anonParams:length() >= 2 }, then: {
			local Parameter is p1: fnExpr:anonParams:get(index: 1);
			self:localVars:set(key: p1:name, value: self:formatTypeString(t: p1:paramType));
			local String is p1CType: self:cTypeFor(typeName: p1:paramType:name);
			local String is p1Raw: '(' . p1CType . ')(intptr_t)' . eVar . '->value';
			Conditional:if(check: { p1:paramType:name == 'String' }, then: {
				p1Raw: 'spec_string_from_chars((const char*)' . eVar . '->value)';
			});
			paramDecl: paramDecl . '            ' . p1CType . ' ' . self:utils:cIdent(name: p1:name) . ' = ' . p1Raw . ";\n";
		});

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

	## Inlines a While loop with optional scoped loop variables:
	## loop variables are declared at the block scope, and the evaluate/iteration
	## FUNCTIONS.md Part II: extracts the condition C from a check
	## closure — the body's last expression statement is the condition
	## (the Kotlin convention). Earlier statements, if any, are emitted
		## into a do-block prefix.
	##
	## @param checkAnon: The check closure's ANON_FN.
	## @param prefixOut: Accumulator for any pre-condition statements.
	## @return: The C condition expression.
	Function of String is checkConditionC(Expression is checkAnon, Array of String is prefixOut){
		local Expression is condExpr: Expression:init(kind: ExpressionKind:UNKNOWN);
		local Int is lastExprIdx: -1;
		local Boolean is lastIsReturn: false;
		local Int is si: 0;
		checkAnon:anonBody:each(action: local Function(Statement is st){
			# Both the explicit-terminator form (`expr;`) and the brace
			# shorthand's RETURN-desugared trailing expression carry the
			# condition.
			Conditional:if(check: { st:kind == StatementKind:EXPR }, then: {
				lastExprIdx: si;
				lastIsReturn: false;
			}, else: {
				Conditional:if(check: { st:kind == StatementKind:RETURN && st:hasReturnExpr }, then: {
					lastExprIdx: si;
					lastIsReturn: true;
				});
			});
			si: si + 1;
		});
		Conditional:if(check: { lastExprIdx >= 0 }, then: {
			local Statement is lastStmt: checkAnon:anonBody:get(index: lastExprIdx);
			Conditional:if(check: { lastIsReturn }, then: {
				condExpr: lastStmt:returnExpr;
			}, else: {
				condExpr: lastStmt:exprStmt;
			});
		});
		Conditional:if(check: { lastExprIdx > 0 }, then: {
			local Int is ei: 0;
			checkAnon:anonBody:each(action: local Function(Statement is st){
				Conditional:if(check: { ei < lastExprIdx }, then: {
					prefixOut:add(item: self:generateStatement(stmt: st));
				});
				ei: ei + 1;
			});
		});
		return self:generateExpression(expr: condExpr);
	}

	## FUNCTIONS.md Part II: inlines a Conditional branch call as native
	## C if/else. Branch bodies are inlined into the enclosing function,
	## so a `return` inside a branch returns from the method (guard
	## clauses work). The 2-arg form is the primitive; the 3-arg form is
	## `else` (not-if); the 4-arg form appends `finally`.
	##
	## @param expr: The branch CALL expression.
	## @return: C statement text.
	Function of String is generateInlineBranch(Expression is expr){
		local String is savedVar: self:inlineReturnVar;
		local String is savedLbl: self:inlineReturnLabel;
		local Boolean is savedArg: self:argMode;
		# FUNCTIONS.md Part II: INHERIT the enclosing inline-return
		# context. A branch nested in an inlined loop's iteration keeps the
		# loop's return protocol (`return false` stops the loop); a branch
		# at method level sees the empty context and its returns stay real
		# method returns (guard clauses). Clearing here turned loop-stops
		# into garbage method returns.
		self:argMode: false;
		# FUNCTIONS.md Part II: the value-yielding form — the checker
		# stamped the unified yield type; emit a statement expression.
		local String is resT: expr:resolvedType;
		local Boolean is valueForm: expr:argCount() == 3 && resT != '' && resT != 'void' && resT != 'Void';
		local Array of String is condPrefix: [];
		local String is condC: self:checkConditionC(checkAnon: expr:argValue(index: 0), prefixOut: condPrefix);
		local String is prefixC: '';
		condPrefix:each(action: local Function(String is p){
			prefixC: prefixC . p;
		});
		local String is out: '';
		Conditional:if(check: { valueForm }, then: {
			self:anonCounter: self:anonCounter + 1;
			local String is yieldVar: '_br_' . (self:anonCounter as String);
			local String is yieldCType: self:cTypeFor(typeName: resT);
			local String is thenC: self:inlineBranchBodyYield(anonFn: expr:argValue(index: 1), yieldVar: yieldVar, yieldT: resT);
			local String is elseC: self:inlineBranchBodyYield(anonFn: expr:argValue(index: 2), yieldVar: yieldVar, yieldT: resT);
			out: '({ ' . yieldCType . ' ' . yieldVar . ";\n" . prefixC . "if (" . condC . ") {\n" . thenC . "\t} else {\n" . elseC . "\t}\n" . yieldVar . "; })";
		}, else: {
			local String is thenC: self:inlineBranchBody(anonFn: expr:argValue(index: 1));
			out: prefixC . "if (" . condC . ") {\n" . thenC . "\t}";
			Conditional:if(check: { expr:argCount() >= 3 }, then: {
				local String is elseC: self:inlineBranchBody(anonFn: expr:argValue(index: 2));
				out: out . " else {\n" . elseC . "\t}";
			});
			Conditional:if(check: { expr:argCount() >= 4 }, then: {
				local String is finC: self:inlineBranchBody(anonFn: expr:argValue(index: 3));
				out: out . "\n" . finC;
			});
		});
		self:inlineReturnVar: savedVar;
		self:inlineReturnLabel: savedLbl;
		self:argMode: savedArg;
		return out;
	}

	## Inlines one value-branch closure's body: every statement as-is, the
	## final return replaced by the yield assignment. The yield mirrors
	## emitReturn's ARC three-way (owned-local swap, fresh-cast, retain) so
	## scope releases cannot dangle the result.
	##
	## @param anonFn: The branch's ANON_FN.
	## @param yieldVar: The statement-expression's result variable.
	## @param yieldT: The unified yield type name.
	## @return: C statement text.
	Function of String is inlineBranchBodyYield(Expression is anonFn, String is yieldVar, String is yieldT){
		local String is bodyC: '';
		local String is yieldCType: self:cTypeFor(typeName: yieldT);
		local Int is bodyLen: anonFn:anonBody:length();
		local Int is bi: 0;
		anonFn:anonBody:each(action: local Function(Statement is st){
			Conditional:if(check: { bi == bodyLen - 1 && st:kind == StatementKind:RETURN && st:hasReturnExpr }, then: {
				local ExpressionKind is retKind: st:returnExpr:kind;
				Conditional:if(check: { (retKind == ExpressionKind:ARRAY || retKind == ExpressionKind:MAP) && (yieldT:startsWith(prefix: 'Array') || yieldT:startsWith(prefix: 'Map')) }, then: {
					self:setContainerHint(t: yieldT);
				});
				local Boolean is savedArg: self:argMode;
				self:argMode: false;
				local String is retC: self:generateExpression(expr: st:returnExpr);
				self:argMode: savedArg;
				Conditional:if(check: { self:isArcType(typeName: yieldT) }, then: {
					# FUNCTIONS.md Part IV V2: a yield does not end the enclosing
					# scope — the source local may be read after the
					# if-expression, so the yield RETAINS (the ARC-safe copy)
					# instead of the return path's ownership NULL-swap. A fresh
					# allocation flows unclaimed into the result variable.
					Conditional:if(check: { self:isFreshConstructorCall(expr: st:returnExpr) }, then: {
						retC: '(' . yieldCType . ')(' . retC . ')';
					}, else: {
						retC: '(' . yieldCType . ')spec_retain((void*)(' . retC . '))';
					});
				});
				bodyC: bodyC . "\t" . yieldVar . ' = ' . retC . ";\n";
			}, else: {
				bodyC: bodyC . "\t" . self:generateStatement(stmt: st);
			});
			bi: bi + 1;
		});
		bodyC: bodyC . self:scopeReleases(stmts: anonFn:anonBody);
		return bodyC;
	}

	## Inlines one branch closure's body statements.
	##
	## @param anonFn: The branch's ANON_FN.
	## @return: C statement text.
	Function of String is inlineBranchBody(Expression is anonFn){
		local String is bodyC: '';
		anonFn:anonBody:each(action: local Function(Statement is st){
			bodyC: bodyC . "\t" . self:generateStatement(stmt: st);
		});
		bodyC: bodyC . self:scopeReleases(stmts: anonFn:anonBody);
		return bodyC;
	}

	## anon function bodies become the loop's condition and body.
	##
	## @param loopVars: Scoped loop variable declarations.
	## @param evalExpr: The evaluate ANON_FN.
	## @param iterExpr: The iteration ANON_FN.
	## @return: C statement expression.
	Function of String is generateInlineWhileLoop(Array of Parameter is loopVars, Expression is evalExpr, Expression is iterExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;

		local Map of String to String is savedVars: Map:init();
		local Array of String is vKeys: self:localVars:keys();
		vKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
		});

		local String is declsC: '';
		loopVars:each(action: local Function(Parameter is p){
			local String is pTypeName: self:formatTypeString(t: p:paramType);
			self:localVars:set(key: p:name, value: pTypeName);
			local String is pCType: self:cTypeFor(typeName: pTypeName);
			local String is pNameC: self:utils:cIdent(name: p:name);
			local String is pInitC: '0';
			Conditional:if(check: { p:hasDefault }, then: {
				pInitC: self:generateExpression(expr: p:defaultExpr);
			});
			declsC: declsC . '    ' . pCType . ' ' . pNameC . ' = ' . pInitC . ";\n";
		});

		local String is evVar: '_ev_' . id;
		self:inlineReturnVar: evVar;
		self:inlineReturnLabel: 'break';
		local String is evalBodyC: '';
		local Int is evalCount: evalExpr:anonBody:length();
		local Int is evIdx: 0;
		evalExpr:anonBody:each(action: local Function(Statement is s){
			evIdx: evIdx + 1;
			Conditional:if(check: { s:kind == StatementKind:EXPR && evIdx == evalCount && self:inlineReturnVar != '' }, then: {
				local String is exprC: self:generateExpression(expr: s:exprStmt);
				evalBodyC: evalBodyC . '    ' . self:inlineReturnVar . ' = ' . exprC . "; break;\n";
			}, else: {
				evalBodyC: evalBodyC . self:generateStatement(stmt: s);
			});
		});
		evalBodyC: evalBodyC . self:scopeReleases(stmts: evalExpr:anonBody);

		# FUNCTIONS.md hardening: the iteration closure's returns drive the
		# loop — `return true` continues (skipping the rest of the body),
		# `return false` stops it, `return <expr>` decides at runtime. The
		# body is generated with a real return variable; a body without any
		# return defaults to continue.
		local String is itVar: '_it_' . id;
		self:inlineReturnVar: itVar;
		self:inlineReturnLabel: 'break';
		local String is iterBodyC: '';
		iterExpr:anonBody:each(action: local Function(Statement is s){
			iterBodyC: iterBodyC . self:generateStatement(stmt: s);
		});
		iterBodyC: iterBodyC . self:scopeReleases(stmts: iterExpr:anonBody);

		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is loopReleasesC: '';
		loopVars:each(action: local Function(Parameter is p){
			local String is pTypeName: self:formatTypeString(t: p:paramType);
			Conditional:if(check: { self:isArcType(typeName: pTypeName) }, then: {
				local String is pNameC: self:utils:cIdent(name: p:name);
				loopReleasesC: loopReleasesC . '    if (' . pNameC . ') { spec_release((void*)' . pNameC . '); ' . pNameC . " = NULL; }\n";
			});
		});

		local String is out: "({ " . declsC . "while (1) {\n        bool " . evVar . " = false;\n        do {\n" . evalBodyC . "        } while (0);\n        if (!" . evVar . ") break;\n        bool " . itVar . " = true;\n        do {\n" . iterBodyC . "        } while (0);\n        if (!" . itVar . ") break;\n    }\n" . loopReleasesC . "})";
		self:localVars: savedVars;
		return out;
	}

	## FUNCTIONS.md II.4: inlines an `until(evaluate:, iteration:)` — the
	## do-while: the body runs once, then the predicate decides. The body's
	## returns drive the loop exactly like [generateInlineWhileLoop].
	##
	## @param evalExpr: The evaluate ANON_FN.
	## @param iterExpr: The iteration ANON_FN.
	## @return: C statement expression.
	Function of String is generateInlineUntil(Expression is evalExpr, Expression is iterExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;

		local String is evVar: '_ev_' . id;
		self:inlineReturnVar: evVar;
		self:inlineReturnLabel: 'break';
		local String is evalBodyC: '';
		local Int is evalCount: evalExpr:anonBody:length();
		local Int is evIdx: 0;
		evalExpr:anonBody:each(action: local Function(Statement is s){
			evIdx: evIdx + 1;
			Conditional:if(check: { s:kind == StatementKind:EXPR && evIdx == evalCount && self:inlineReturnVar != '' }, then: {
				local String is exprC: self:generateExpression(expr: s:exprStmt);
				evalBodyC: evalBodyC . '    ' . self:inlineReturnVar . ' = ' . exprC . "; break;\n";
			}, else: {
				evalBodyC: evalBodyC . self:generateStatement(stmt: s);
			});
		});
		evalBodyC: evalBodyC . self:scopeReleases(stmts: evalExpr:anonBody);

		local String is itVar: '_it_' . id;
		self:inlineReturnVar: itVar;
		self:inlineReturnLabel: 'break';
		local String is iterBodyC: '';
		iterExpr:anonBody:each(action: local Function(Statement is s){
			iterBodyC: iterBodyC . self:generateStatement(stmt: s);
		});
		iterBodyC: iterBodyC . self:scopeReleases(stmts: iterExpr:anonBody);

		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is out: "({ while (1) {\n        bool " . itVar . " = true;\n        do {\n" . iterBodyC . "        } while (0);\n        if (!" . itVar . ") break;\n        bool " . evVar . " = false;\n        do {\n" . evalBodyC . "        } while (0);\n        if (!" . evVar . ") break;\n    }\n})";
		return out;
	}

	## FUNCTIONS.md II.4: inlines a `repeat(count:, worker:)` — the body
	## runs exactly [count] times; the worker's returns drive the loop
	## (`return true` continues, `return false` stops).
	##
	## @param countExpr: The count expression.
	## @param workerExpr: The worker ANON_FN.
	## @return: C statement expression.
	Function of String is generateInlineRepeat(Expression is countExpr, Expression is workerExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;

		local String is countC: self:generateExpression(expr: countExpr);

		local String is itVar: '_it_' . id;
		self:inlineReturnVar: itVar;
		self:inlineReturnLabel: 'break';
		local String is workerBodyC: '';
		workerExpr:anonBody:each(action: local Function(Statement is s){
			workerBodyC: workerBodyC . self:generateStatement(stmt: s);
		});
		workerBodyC: workerBodyC . self:scopeReleases(stmts: workerExpr:anonBody);

		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is out: "({ long long _rn_" . id . " = (long long)(" . countC . "); for (long long _ri_" . id . " = 0; _ri_" . id . " < _rn_" . id . "; _ri_" . id . "++) {\n        bool " . itVar . " = true;\n        do {\n" . workerBodyC . "        } while (0);\n        if (!" . itVar . ") break;\n    }\n})";
		return out;
	}

	## Inlines a While:condition predicate loop: evaluate/iteration anon
	## function bodies become the loop's condition and step.
	##
	## @param evalExpr: The evaluate ANON_FN.
	## @param iterExpr: The iteration ANON_FN.
	## @return: C statement expression.
	Function of String is generateInlineWhileCondition(Expression is evalExpr, Expression is iterExpr){
		return self:generateInlineWhileLoop(loopVars: [], evalExpr: evalExpr, iterExpr: iterExpr);
	}

	## Scans a member list for a field by name.
	Class of Loop is FieldMemberLoop{

		replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
		];
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
			Conditional:if(check: { m:kind == MemberKind:FIELD && m:name == self:fieldName }, then: {
				self:res: m;
				self:found: true;
				return false;
			});
			return true;
		}
	}

	## Scans a member list for a method by name.
	Class of Loop is MethodMemberLoop{

		replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
		];
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
			Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == self:methodName }, then: {
				self:res: m;
				self:found: true;
				return false;
			});
			return true;
		}
	}

}
