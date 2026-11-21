#! Package base:compiler:checker
#! Semantic analysis: the bidirectional type checker.
##
## Core design: `inferExpressionType(expr, expected)` — the expected type
## flows DOWN from the four contextual sites (variable declarations,
## assignments, returns, field initializers) so array/map literals type
## directly from their declared container and no hint state exists. Where
## no expectation exists, the expression infers bottom-up as before.
##
## Type-name conventions (documented in WellKnown):
## containers are written 'Array:X' / 'Map:K:V' / 'List:X' internally, with
## 'Array of X' accepted on input; both void spellings compare via isVoid.

Class is TypeChecker{
	namespace: ['base', 'compiler', 'checker'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', ClassBindings],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'ast', ContractMethod],
		['base', 'compiler', 'ast', MetadataField],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', WellKnown],
		['base', 'compiler', Error],
		['base', 'compiler', ErrorText],
		['base', 'sys', SourceLocation],
		['base', 'compiler', 'checker', TypeError],
		['base', 'compiler', 'checker', as TypeDomain()],
		['base', 'iterator'],
		['base', 'sys', as Loops()],
		['base', 'sys', as Reflection()],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
];

	## Registered classes: name -> "true".
	local Map of String to String is registeredClasses: Map:init();
	local ErrorText is errText: ErrorText:init();
	local Map of String to Type is typeNodeCache: Map:init();

	## the per-scope nested-type map — bare
	## nested-class name -> ';'-joined qualified identities visible in
	## [nestedScopeFor]. Built once per scope (own nested classes, the
	## as-imported classes' nested classes, the base lattice), cleared and
	## rebuilt when the scope changes; the per-reference cost is one
	## lookup.
	local Map of String to String is nestedScopeMap: Map:init();

	## The scope [nestedScopeMap] was built for ('' initially).
	local String is nestedScopeFor: '';

	## All enum type names in the program.
	local Map of String to String is allEnumNames: Map:init();

	## Enum variant name -> parent enum name.
	local Map of String to String is allEnumVariants: Map:init();

	## String-backed enum names.
	local Map of String to String is allStringBackedEnums: Map:init();

	## Local variables in the current scope: name -> type name.
	local Map of String to String is localVars: Map:init();

	## Field types of the current class: name -> type name.
	local Map of String to String is fieldTypes: Map:init();

	## Fields of the current class not yet definitely assigned in init.
	local Map of String to String is unassignedFields: Map:init();

	## Source line of the expression currently being checked.
	local Int is currentLine: 0;

	## Whether the method being checked carries `merge`.
	local Boolean is currentMethodIsMerge: false;

	## Whether a held field's initializer is being checked: no instance
	## context exists (no self, no instance fields, no implicit-self
	## calls), and same-class held references would deadlock the
	## once-guards.
	local Boolean is inHeldInit: false;

	## Whether a held function's body is being checked: the same
	## no-instance rule as held initializers, but same-class held
	## references are fine (the call triggers the other member's lazy
	## construction on demand — no deadlock).
	local Boolean is inHeldFunction: false;

	## True while a held body infers the TARGET of a function-variable
	## invocation (self:missing()): the closure call never touches the
	## instance, so the no-instance error does not apply
	## The resolution hook's missing branch.
	local Boolean is inHeldFnVarTarget: false;

	## Name of the method being checked (forward resolution).
	local String is currentMethodName: '';

	## Whether a forward statement was seen in the current method.
	local Boolean is forwardSeen: false;

	## Anonymous-function nesting depth (forwards are top-level only).
	local Int is anonDepth: 0;
	# inside a Conditional branch-closure argument —
	# its body inlines into the enclosing method, so returns flow to the
	# method's return type, not the closure's.
	local Boolean is inBranchClosure: false;

	## Class currently being analyzed.
	local String is currentClassName: '';
	local ClassInfo is currentClassDef: ClassInfo:init(name: '', baseClass: '', members: []);

	## Source file of the class currently being analyzed.
	local String is currentSourceFile: '';

	## Return type name of the method currently being checked.
	local String is currentMethodReturnType: '';

	## the anon-fn node whose body is being checked
	## (the Kotlin write-back target for void-declared closures).
	local Expression is currentAnonNode: Expression:Unknown;

	## inside a value-yielding branch's then/otherwise
	## closure (the call site expects a value).
	local Boolean is inValueBranch: false;

	## checking the last statement of a value-yielding
	## branch closure — its return establishes the branch's yield type.
	local Boolean is checkingValueYield: false;

	## the expected type of the value-yielding branch
	## being checked — flows into its yields so nested branch calls type in
	## context.
	local String is currentYieldExpected: '';

	## True while checking the body of a `lazy({ ... })` initializer:
	## external locals and instance fields are read-only inside it.
	local Boolean is inLazyBlock: false;

	## Local variables declared inside the current `lazy({ ... })` block,
	## which may be freely mutated within that block.
	local Map of String to String is lazyLocalVars: Map:init();

	## Method-level generic templates discovered during type checking (`Owner:method -> tpName`),
	## their grounding status (`Owner:method -> true`), and their declaring source locations.
	local Map of String to String is genericMethodTemplates: Map:init();
	local Map of String to Boolean is groundedGenericMethods: Map:init();
	local Map of String to Int is genericMethodLines: Map:init();
	local Map of String to String is genericMethodFiles: Map:init();
	local Map of String to Boolean is currentMethodTypeParams: Map:init();

	## Accumulated type errors.
	local Array of TypeError is errors: [];

	## All class definitions in the program (nested included).
	local Array of ClassInfo is programClasses: [];

	## Well-known names (builtin types, sentinels).
	local WellKnown is names: WellKnown:init();

	## The shared floor-class classification (emission + call contracts).
	local ClassBindings is bindings: ClassBindings:init();

	replace Function is init(){
		:programClasses: [];
		:registeredClasses: Map:init();
		:allEnumNames: Map:init();
		:allEnumVariants: Map:init();
		:allStringBackedEnums: Map:init();
		:genericMethodTemplates: Map:init();
		:groundedGenericMethods: Map:init();
		:genericMethodLines: Map:init();
		:genericMethodFiles: Map:init();
		:currentMethodTypeParams: Map:init();
		:localVars: Map:init();
		:fieldTypes: Map:init();
		:unassignedFields: Map:init();
		:nestedScopeMap: Map:init();
		:nestedScopeFor: '';
		:currentLine: 0;
		:currentSourceFile: '';
	}

	## Records a type error with provenance.
	##
	## @param line: Source line number.
	## @param msg: Diagnostic message.
	Function is addError(Int is line, String is msg, Int is col: 0, Int is length: 0){
		local String is fullMsg: if({ :currentSourceFile != '' }, { '[' . :currentSourceFile . '] ' . msg }, { msg });
		local Error is e: Error:init(message: fullMsg, location: SourceLocation:init(file: :currentSourceFile, line: line, col: col, length: length));
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: line, col: col);
		:errors:add(item: TypeError:init(line: line, message: fullMsg, col: col, length: length, file: :currentSourceFile));
	}

	## True when the name is one of the two void spellings.
	##
	## @param t: Type name.
	## @return: true for 'void' and 'Void'.
	Function of Boolean is isVoid(String is t){
		# One canonical AST spelling: 'Void' (Primitive.VOID). The C
		# spelling 'void' exists only at the emission boundary (the
		# generator's formatter) — checker state carries the AST spelling.
		return t == Primitive:VOID:value();
	}

	## True when the name is a primitive type name (not a class).
	##
	## @param t: Type name.
	## @return: true per the [Primitive] vocabulary.
	Function of Boolean is isPrimitive(String is t){
		return Primitive:of(t) != Primitive:NONE;
	}

	Function of Boolean is isUnsignedInt(String is t){
		return t == 'UInt8' || t == 'UInt16' || t == 'UInt32' || t == 'UInt64';
	}

	Function of Boolean is isIntLike(String is t){
		return t == Primitive:INT:value() || t == 'Byte' || :isUnsignedInt(t: t);
	}

	## Formats a [Type] descriptor for a variable or field (preserving
	## "Function:RetType").
	##
	## @param t: Type descriptor.
	## @return: Type name string.
	Function of String is formatVarTypeString(Type is t){
		if({ Primitive:of(t:name) == Primitive:FUNCTION }, {
			if({ t:params:length() > 0 }, {
				local Type is ret: if({ t:params:length() >= 2 }, { t:params:get(index: 1) }, { t:params:get(index: 0) });
				return TypeDomain:makeFunction(ret: :formatTypeString(t: ret));
			});
			return 'Function';
		});
		return :formatTypeString(t: t);
	}

	## Formats a [Type] descriptor into the internal colon form
	## (Array:X, Map:K:V); Function formats to its return type.
	##
	## @param t: Type descriptor.
	## @return: Type name string.
	Function of String is formatTypeString(Type is t){
		local String is baseName: t:name;
		if({ Primitive:of(baseName) == Primitive:FUNCTION }, {
			if({ t:params:length() > 0 }, {
				local Type is ret: if({ t:params:length() >= 2 }, { t:params:get(index: 1) }, { t:params:get(index: 0) });
				if({ Primitive:of(ret:name) == Primitive:FUNCTION }, {
					return :formatVarTypeString(t: ret);
				});
				return :formatTypeString(t: ret);
			});
			return :names:voidName();
		});
		if({ t:params:length() == 1 }, {
			local Type is p0: t:params:get(index: 0);
			# the stamp vocabulary repeats — the
			# interning collapses the retained copies to one object.
			return (baseName . ':' . :formatVarTypeString(t: p0)):intern();
		});
		if({ t:params:length() >= 2 }, {
			local Type is p0: t:params:get(index: 0);
			local Type is p1: t:params:get(index: 1);
			return (baseName . ':' . :formatVarTypeString(t: p0) . ':' . :formatVarTypeString(t: p1)):intern();
		});
		return baseName;
	}

	## Substitutes a class's generic type parameters in a structured [Type] node.
	Function of Type is substituteTypeNode(Type is t, ClassInfo is cls, Array of Type is typeArgs){
		local Array of String is tps: cls:typeParams;
		if({ tps:length() == 0 || typeArgs:length() == 0 || t:name == '' }, {
			return t;
		});
		local Int is idx: tps:indexOf(search: t:name, default: -1);
		if({ idx >= 0 && t:params:length() == 0 }, {
			if({ idx < typeArgs:length() }, {
				return typeArgs:get(index: idx):clone();
			});
			return Type:init(name: Primitive:ANY:value());
		});
		local Array of Type is newParams: [];
		local Int is pi: 0;
		while({ pi < t:params:length() }, {
			newParams:add(item: :substituteTypeNode(t: t:params:get(index: pi), cls: cls, typeArgs: typeArgs));
			pi++;
		});
		local String is bName: t:name;
		if({ idx >= 0 && idx < typeArgs:length() }, {
			bName: typeArgs:get(index: idx):name;
		});
		return Type:withParams(name: bName, params: newParams);
	}

	## Converts a canonical type name string into a structured [Type] tree (`name` + `Array of Type`).
	Function of Type is parseTypeNode(String is s){
		if({ s == '' }, { return Type:init(name: ''); });
		if({ :typeNodeCache:has(key: s) }, {
			return :typeNodeCache:get(key: s);
		});
		if({ !s:contains(needle: ':') && !s:contains(needle: ' of ') }, {
			local Type is simpleT: Type:init(name: s);
			:typeNodeCache:set(key: s, value: simpleT);
			return simpleT;
		});
		if({ :registeredClasses:has(key: s) }, {
			local Type is clsT: Type:init(name: s);
			:typeNodeCache:set(key: s, value: clsT);
			return clsT;
		});
		local String is norm: :normalizeContainerType(t: s);
		local Array of String is rawParts: norm:split(delimiter: ':');
		local Array of Type is stack: [];
		local Int is idx: rawParts:length() - 1;
		while({ idx >= 0 }, {
			local String is seg: rawParts:get(index: idx, default: '');
			local Int is arity: 0;
			if({ seg == 'Array' || seg == 'List' || seg == 'Function' }, {
				arity: 1;
			}, {
				if({ seg == 'Map' }, {
					arity: 2;
				}, {
					local ClassInfo is cls: :findClass(name: seg);
					if({ cls:name != '' && cls:typeParams:length() > 0 }, {
						arity: cls:typeParams:length();
					});
				});
			});
			if({ arity > 0 && stack:length() >= arity }, {
				local Array of Type is tArgs: [];
				local Int is ki: 0;
				while({ ki < arity }, {
					tArgs:add(item: stack:pop(default: Type:init(name: '')));
					ki++;
				});
				stack:add(item: Type:withParams(name: seg, params: tArgs));
			}, {
				stack:add(item: Type:init(name: seg));
			});
			idx: idx - 1;
		});
		local Type is parsedT: if({ stack:length() > 0 }, { stack:get(index: stack:length() - 1) }, { Type:init(name: s) });
		:typeNodeCache:set(key: s, value: parsedT);
		return parsedT;
	}

	## Substitutes a class's generic type parameters in a member type name.
	##
	## @param rawType: Declared type name (may reference type params).
	## @param cls: The declaring class.
	## @param typeArgs: The concrete type arguments.
	## @return: The substituted type name.
	Function of String is substituteTypeParam(String is rawType, ClassInfo is cls, Array of String is typeArgs){
		local Array of String is tps: cls:typeParams;
		if({ tps:length() == 0 || typeArgs:length() == 0 }, {
			return rawType;
		});
		local Array of Type is argNodes: [];
		typeArgs:each(action: local Function(String is ta){
			argNodes:add(item: :parseTypeNode(s: ta));
		});
		local Type is rawNode: :parseTypeNode(s: rawType);
		local Type is subNode: :substituteTypeNode(t: rawNode, cls: cls, typeArgs: argNodes);
		return :formatVarTypeString(t: subNode);
	}

	## Infers the grounded generic type ('Box:String', 'Pair:String:Int', 'SpecError:FileOpError')
	## for a constructor call `C:init(...)` from contextual expectation and/or argument types,
	## operating over structured [Type] trees (`Array of Type`).
	Function of String is inferGenericInitType(String is baseClassName, String is targetType, Member is initMem, CallData is call, String is expected){
		local ClassInfo is cls: :findClass(name: baseClassName);
		if({ cls:name == '' || cls:typeParams:length() == 0 }, {
			return targetType;
		});
		local Type is expNode: :parseTypeNode(s: expected);
		local Array of Type is expParams: if({ expNode:name == cls:name }, { expNode:params }, { [] });
		local Array of Type is resolvedArgs: [];
		local Boolean is allResolved: true;
		local Int is tpIdx: 0;
		while({ tpIdx < cls:typeParams:length() }, {
			local String is tpName: cls:typeParams:get(index: tpIdx);
			local Type is argNode: Type:init(name: '');
			if({ expParams:length() > tpIdx }, {
				argNode: expParams:get(index: tpIdx);
			});
			if({ argNode:name == '' || argNode:name == Primitive:ANY:value() }, {
				local Int is pIdx: 0;
				initMem:params:each(action: local Function(Parameter is p){
					if({ (argNode:name == '' || argNode:name == Primitive:ANY:value()) && p:paramType:name == tpName }, {
						local Int is posIdx: 0;
						call:args:each(action: local Function(NamedArg is a){
							if({ argNode:name == '' || argNode:name == Primitive:ANY:value() }, {
								if({ (p:name != '' && a:name == p:name) || (a:name == '' && posIdx == pIdx) }, {
									local String is candT: a:value:resolvedType;
									if({ candT != '' && candT != Primitive:ANY:value() }, {
										argNode: :parseTypeNode(s: candT);
									});
								});
							});
							posIdx: posIdx + 1;
						});
					});
					pIdx: pIdx + 1;
				});
			});
			if({ argNode:name == '' || argNode:name == Primitive:ANY:value() }, {
				allResolved: false;
			}, {
				resolvedArgs:add(item: argNode);
			});
			tpIdx: tpIdx + 1;
		});
		if({ allResolved && resolvedArgs:length() == cls:typeParams:length() }, {
			return :formatTypeString(t: Type:withParams(name: cls:name, params: resolvedArgs));
		});
		if({ expNode:name == cls:name && expParams:length() > 0 }, {
			return :formatTypeString(t: expNode);
		});
		return targetType;
	}

	## Finds a class descriptor by name.
	##
	## @param name: Target class name.
	## @return: The descriptor, or an unnamed one when absent.
	Function of ClassInfo is findClass(String is name){
		local ClassInfo is res: ClassInfo:init(name: '', baseClass: '', members: []);
		local Boolean is found: false;
		local Int is count: :programClasses:length();
		local Boolean is hasColon: name:contains(needle: ':');
		local ClassInfo is floorCand: ClassInfo:init(name: '', baseClass: '', members: []);
		while(
			[Int is idx: 0],
			{ !found && idx < count },
			{
				local ClassInfo is cand: :programClasses:get(index: idx);
				idx++;
				if({ hasColon }, {
					local String is candQ: cand:namespaceJoined() . ':' . cand:name;
					if({ candQ == name }, {
						res: cand;
						found: true;
					});
				}, {
					if({ cand:name == name }, {
						local Array of String is cSegs: cand:namespaceSegments();
						local Boolean is isFloor: cSegs:length() > 0 && cSegs:get(index: cSegs:length() - 1) == 'sysinternal';
						if({ !isFloor }, {
							res: cand;
							found: true;
						}, {
							if({ floorCand:name == '' }, {
								floorCand: cand;
							});
						});
					});
				});
			}
		);
		if({ found }, {
			return res;
		});
		if({ !hasColon && floorCand:name != '' }, {
			return floorCand;
		});
		if({ hasColon }, {
			local ClassInfo is qMatch: ClassInfo:init(name: '', baseClass: '', members: []);
			:programClasses:each(action: local Function(ClassInfo is c){
				if({ qMatch:name == '' && c:qualifiedName() == name }, {
					qMatch: c;
				});
			});
			if({ qMatch:name != '' }, {
				return qMatch;
			});
		});
		return res;
	}

	## True when [subName] inherits from [baseName] (transitively).
	##
	## @param subName: Candidate subtype.
	## @param baseName: Candidate base type.
	## @return: Subclass relationship.
	Function of Boolean is isSubclassOf(String is subName, String is baseName){
		if({ subName == '' || baseName == '' }, {
			return false;
		});
		if({ subName == baseName }, {
			return true;
		});
		local ClassInfo is subCls: :findClass(name: subName);
		if({ subCls:name == '' }, {
			return false;
		});
		if({ subCls:qualifiedName() == baseName }, {
			return true;
		});
		local ClassInfo is baseCls: :findClass(name: baseName);
		if({ baseCls:name != '' && subCls:qualifiedName() == baseCls:qualifiedName() }, {
			return true;
		});
		local Boolean is matched: false;
		subCls:baseClasses:each(action: local Function(String is pName){
			if({ pName == baseName || :isSubclassOf(subName: pName, baseName: baseName) }, {
				matched: true;
			});
		});
		return matched;
	}

	## True when [name] is part of the implicit root declaration spine
	## (`Class -> Stringable -> Loadable -> base:sysinternal:Loadable -> Any`
	## or `Enum`). Every class inherits these implicitly, so they do not
	## count as a shared user parent class when unifying array element types.
	##
	## @param name: Class name.
	## @return: true when [name] is an implicit root class.
	Function of Boolean is isImplicitRootClass(String is name){
		return name == 'Any' || name == 'Class' || name == 'Stringable' || name == 'Loadable' || name == 'base:sysinternal:Loadable' || name == 'Enum';
	}

	## Collects all non-implicit-root ancestor classes of [className] in
	## declaration order across single and multiple inheritance.
	##
	## @param className: Starting class name.
	## @param visited: Cycle/revisit guard map.
	## @param acc: Output array of ancestor class names.
	Function is collectUserAncestors(String is className, Map of String to String is visited: Map:init(), Array of String is acc){
		if({ className == '' || :isImplicitRootClass(name: className) || visited:has(key: className) }, {
			return;
		});
		visited:set(key: className, value: 'true');
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			return;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !:isImplicitRootClass(name: baseName) && !visited:has(key: baseName) }, {
				local Boolean is present: false;
				acc:each(action: local Function(String is existing){
					if({ existing == baseName }, {
						present: true;
					});
				});
				if({ !present }, {
					acc:add(item: baseName);
				});
			});
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			:collectUserAncestors(className: baseName, visited: visited, acc: acc);
		});
	}

	## Normalizes 'of' and 'to' container type spellings ('Array of String',
	## 'Map of String to Int') to the canonical colon form ('Array:String',
	## 'Map:String:Int').
	##
	## @param t: Type name.
	## @return: Normalized type name.
	Function of String is normalizeContainerType(String is t){
		local String is norm: t;
		local Int is ofIdx: norm:indexOf(search: ' of ', default: -1);
		while({ ofIdx > 0 }, {
			norm: norm:substring(start: 0, end: ofIdx) . ':' . norm:substring(start: ofIdx + 4, end: norm:length());
			ofIdx: norm:indexOf(search: ' of ', default: -1);
		});
		local Int is toIdx: norm:indexOf(search: ' to ', default: -1);
		while({ toIdx > 0 }, {
			norm: norm:substring(start: 0, end: toIdx) . ':' . norm:substring(start: toIdx + 4, end: norm:length());
			toIdx: norm:indexOf(search: ' to ', default: -1);
		});
		return norm;
	}

	## Validates that all element types in an array are mutually compatible:
	## either all the same primitive type, all the same class/container type,
	## or all sharing a user parent class via single or multiple inheritance.
	## Emits a diagnostic and returns '' when incompatible.
	##
	## @param elemTypes: Inferred types of the array's elements.
	## @return: The unified element type, or '' when empty or incompatible.
	Function of String is unifyArrayElementTypes(Array of String is elemTypes){
		local Array of String is concrete: [];
		elemTypes:each(action: local Function(String is rawT){
			if({ rawT != '' && rawT != Primitive:ANY:value() }, {
				concrete:add(item: :normalizeContainerType(t: rawT));
			});
		});
		if({ concrete:length() == 0 }, {
			return '';
		});
		local String is firstT: concrete:get(index: 0);
		if({ concrete:length() == 1 }, {
			return firstT;
		});
		local Boolean is allSame: true;
		concrete:each(action: local Function(String is ct){
			if({ ct != firstT }, {
				allSame: false;
			});
		});
		if({ allSame }, {
			return firstT;
		});
		# Function references / closures.
		if({ TypeDomain:isFunction(t: firstT) }, {
			local String is badFn: '';
			concrete:each(action: local Function(String is ct){
				if({ badFn == '' && !TypeDomain:isFunction(t: ct) }, {
					badFn: ct;
				});
			});
			if({ badFn != '' }, {
				:addError(line: :currentLine, msg: "Incompatible array element types: '" . firstT . "' and '" . badFn . "' (array elements must all be the same primitive type, the same class type, or share a parent class).");
				return '';
			});
			return 'Function';
		});
		# Primitive types must all be the exact same primitive type.
		if({ :isPrimitive(t: firstT) }, {
			local String is badPrim: '';
			concrete:each(action: local Function(String is ct){
				if({ badPrim == '' && ct != firstT }, {
					badPrim: ct;
				});
			});
			:addError(line: :currentLine, msg: "Incompatible array element types: '" . firstT . "' and '" . badPrim . "' (array elements must all be the same primitive type, the same class type, or share a parent class).");
			return '';
		});
		# Nested container types (Array, List, Map).
		if({ TypeDomain:isContainer(t: firstT) }, {
			local String is firstBase: TypeDomain:baseName(t: firstT);
			local String is badCont: '';
			concrete:each(action: local Function(String is ct){
				if({ badCont == '' && TypeDomain:baseName(t: ct) != firstBase }, {
					badCont: ct;
				});
			});
			if({ badCont != '' }, {
				:addError(line: :currentLine, msg: "Incompatible array element types: '" . firstT . "' and '" . badCont . "' (array elements must all be the same primitive type, the same class type, or share a parent class).");
				return '';
			});
			if({ firstBase == 'Array' || firstBase == 'List' }, {
				local Array of String is innerTypes: [];
				concrete:each(action: local Function(String is ct){
					local String is et: TypeDomain:elemType(t: ct);
					if({ et != '' }, {
						innerTypes:add(item: et);
					});
				});
				if({ innerTypes:length() == 0 }, {
					return firstBase;
				});
				local String is innerU: :unifyArrayElementTypes(elemTypes: innerTypes);
				if({ innerU == '' }, {
					return '';
				});
				return (firstBase . ':' . innerU):intern();
			});
			return firstT;
		});
		# Class / enum types: check that none of the remaining elements are
		# primitives, containers, or distinct traditional enums.
		local String is mismatchT: '';
		concrete:each(action: local Function(String is ct){
			if({ mismatchT == '' && ct != firstT }, {
				if({ :isPrimitive(t: ct) || TypeDomain:isFunction(t: ct) || TypeDomain:isContainer(t: ct) || :allEnumNames:has(key: firstT) || :allEnumNames:has(key: ct) }, {
					mismatchT: ct;
				});
			});
		});
		if({ mismatchT != '' }, {
			:addError(line: :currentLine, msg: "Incompatible array element types: '" . firstT . "' and '" . mismatchT . "' (array elements must all be the same primitive type, the same class type, or share a parent class).");
			return '';
		});
		# Search for a shared user parent class across single and multiple inheritance.
		local Array of String is candidates: [firstT];
		:collectUserAncestors(className: firstT, acc: candidates);
		local String is sharedParent: '';
		candidates:each(action: local Function(String is cand){
			if({ sharedParent == '' && !:isImplicitRootClass(name: cand) }, {
				local Boolean is allMatch: true;
				concrete:each(action: local Function(String is ct){
					if({ allMatch && !:isSubclassOf(subName: ct, baseName: cand) }, {
						allMatch: false;
					});
				});
				if({ allMatch }, {
					sharedParent: cand;
				});
			});
		});
		if({ sharedParent != '' }, {
			return sharedParent;
		});
		local String is badCls: '';
		concrete:each(action: local Function(String is ct){
			if({ badCls == '' && ct != firstT }, {
				badCls: ct;
			});
		});
		:addError(line: :currentLine, msg: "Incompatible array element types: '" . firstT . "' and '" . badCls . "' (array elements must all be the same primitive type, the same class type, or share a parent class).");
		return '';
	}

	## Determines whether a structured source [Type] node is assignable to a target [Type] node.
	Function of Boolean is isAssignableNode(Type is targetNode, Type is sourceNode){
		local String is tBase: targetNode:name;
		local String is sBase: sourceNode:name;
		if({ tBase == '' || sBase == '' || tBase == Primitive:ANY:value() || sBase == Primitive:ANY:value() }, {
			return true;
		});
		if({ targetNode:equals(other: sourceNode) }, {
			return true;
		});
		if({ tBase == 'Float' && sBase == Primitive:INT:value() }, {
			return true;
		});
		if({ tBase == 'Function' && sBase == 'Function' }, {
			if({ targetNode:params:length() == 0 }, {
				return true;
			});
			if({ sourceNode:params:length() == 0 }, {
				return false;
			});
			local Type is tRet: if({ targetNode:params:length() >= 2 }, { targetNode:params:get(index: 1) }, { targetNode:params:get(index: 0) });
			local Type is sRet: if({ sourceNode:params:length() >= 2 }, { sourceNode:params:get(index: 1) }, { sourceNode:params:get(index: 0) });
			if({ tRet:name == Primitive:ANY:value() || sRet:name == Primitive:ANY:value() || tRet:equals(other: sRet) }, {
				return true;
			});
			return false;
		});
		if({ tBase == sBase || :isSubclassOf(subName: sBase, baseName: tBase) }, {
			if({ targetNode:params:length() > 0 && sourceNode:params:length() > 0 }, {
				local Boolean is argsOk: true;
				local Int is pIdx: 0;
				while({ argsOk && pIdx < targetNode:params:length() && pIdx < sourceNode:params:length() }, {
					local Type is tp: targetNode:params:get(index: pIdx);
					local Type is sp: sourceNode:params:get(index: pIdx);
					if({ !:isAssignableNode(targetNode: tp, sourceNode: sp) }, {
						argsOk: false;
					});
					pIdx: pIdx + 1;
				});
				return argsOk;
			});
			return true;
		});
		return false;
	}

	## Determines whether a source type is assignable to a target type.
	##
	## @param target: Target type name.
	## @param source: Source type name.
	## @return: true when compatible.
	Function of Boolean is isAssignable(String is target, String is source){
		if({ target == source || target == Primitive:ANY:value() || source == Primitive:ANY:value() || target == '' || source == '' }, {
			return true;
		});
		return :isAssignableNode(targetNode: :parseTypeNode(s: target), sourceNode: :parseTypeNode(s: source));
	}

	## the member-lookup root for a (possibly
	## qualified) receiver type. The qualified nested-class reference
	## ('Outer:Inner') resolves to the inner class itself; container and
	## grounded forms ('Array:String', 'Box of Int') resolve no qualified
	## class and keep the bare-root walk. The of-form arrives with its
	## arguments still attached — the callers' of-branch grounds them.
	##
	## @param className: The receiver type string.
	## @return: The class name to start the member walk from.
	Function of String is memberLookupRoot(String is className){
		local String is root: className:split(delimiter: ':'):get(index: 0);
		if({ className:contains(needle: ':') }, {
			local ClassInfo is qCls: :findClass(name: className);
			if({ qCls:name != '' && qCls:qualifiedName() == className }, {
				root: className;
			});
		});
		return root;
	}

	## Looks up a member of any kind by name on a class or its bases.
	##
	## @param className: Class whose members are searched.
	## @param methodName: Member name to locate.
	## @return: The member, or an empty-named one when absent.
	Function of Member is lookupAnyMember(String is className, String is methodName){
		if({ className == '' || className == Primitive:ANY:value() }, {
			return Member:init(kind: MemberKind:FIELD);
		});
		local String is baseClassName: :memberLookupRoot(className: className);
		local ClassInfo is cls: :findClass(name: baseClassName);
		if({ cls:name == '' }, {
			return Member:init(kind: MemberKind:FIELD);
		});
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:members:each(action: local Function(Member is m){
			if({ res:name == '' && !m:hasModifier(kw: Keyword:HELD) && m:kind == MemberKind:METHOD && m:name == methodName }, {
				res: m;
			});
		});
		if({ res:name != '' }, {
			return res;
		});
		local Member is inherited: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ inherited:name == '' }, {
				inherited: :lookupAnyMember(className: baseName, methodName: methodName);
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
		local ClassInfo is cls: :findClass(name: enumName);
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:members:each(action: local Function(Member is m){
			if({ res:name == '' && m:kind == MemberKind:FIELD && m:name == variantName }, {
				res: m;
			});
		});
		return res;
	}

	## Looks up a field's static type on a class and its ancestors.
	##
	## @param className: Starting class name.
	## @param fieldName: Field name.
	## @return: The field type name, or '' when absent.
	Function of String is lookupFieldType(String is className, String is fieldName){
		if({ className == '' || className == Primitive:ANY:value() }, {
			return '';
		});
		local Type is recvNode: :parseTypeNode(s: className);
		local String is baseClassName: if({ recvNode:params:length() > 0 }, { recvNode:name }, { :memberLookupRoot(className: className) });
		local ClassInfo is cls: :findClass(name: baseClassName);
		if({ cls:name == '' }, {
			return '';
		});
		local Member is foundM: Member:init(kind: MemberKind:FIELD);
		cls:members:each(action: local Function(Member is m){
			if({ foundM:name == '' && !m:hasModifier(kw: Keyword:HELD) && m:kind == MemberKind:FIELD && m:name == fieldName }, {
				foundM: m;
			});
		});
		if({ foundM:name != '' }, {
			local Type is subNode: :substituteTypeNode(t: foundM:memberType, cls: cls, typeArgs: recvNode:params);
			return :formatVarTypeString(t: subNode);
		});
		local String is inherited: '';
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ inherited == '' }, {
				inherited: :lookupFieldType(className: baseName, fieldName: fieldName);
			});
		});
		return inherited;
	}

	## Looks up a method's return type on a class and its ancestors.
	##
	## @param className: Starting class name.
	## @param methodName: Method name.
	## @return: The return type name, or '' when absent.
	Function of String is lookupMethodReturnType(String is className, String is methodName){
		if({ className == '' || className == Primitive:ANY:value() }, {
			return '';
		});
		local Type is recvNode: :parseTypeNode(s: className);
		local String is baseClassName: if({ recvNode:params:length() > 0 }, { recvNode:name }, { :memberLookupRoot(className: className) });
		if({ methodName == ContractMethod:INIT:value() && :registeredClasses:has(key: baseClassName) && !:allEnumNames:has(key: baseClassName) }, {
			return className;
		});
		local ClassInfo is cls: :findClass(name: baseClassName);
		if({ cls:name == '' }, {
			return '';
		});
		local Member is foundM: Member:init(kind: MemberKind:FIELD);
		cls:members:each(action: local Function(Member is m){
			if({ foundM:name == '' && !m:hasModifier(kw: Keyword:HELD) && m:kind == MemberKind:METHOD && m:name == methodName }, {
				foundM: m;
			});
		});
		if({ foundM:name != '' }, {
			local Type is subNode: :substituteTypeNode(t: foundM:memberType, cls: cls, typeArgs: recvNode:params);
			return :formatTypeString(t: subNode);
		});
		local String is inherited: '';
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ inherited == '' }, {
				inherited: :lookupMethodReturnType(className: baseName, methodName: methodName);
			});
		});
		return inherited;
	}

	## Type-checks a Conditional:match arm table: keys
	## resolve against the subject class's held members (an array key
	## matches several), `else` names the fallback, and the arm closures
	## unify into the match's type. Exhaustiveness keys on the Enum
	## root: an Enum-rooted subject requires full coverage of its held
	## fields or an else arm; a value-yielding match over any other
	## class requires else (the subject may match no key).
	##
	## @param subj: The `on:` subject expression.
	## @param arms: The literal arm table (a MAP expression).
	## @return: The unified yield type, or Void.
	Function of Boolean is isNonEmptyMatchDefault(Expression is expr){
		return match(on: expr, when: [
			Expression:AnonFn: local Function of Boolean(Type is returnType, Array of Parameter is params, Array of Statement is body){
				return body:length() > 0;
			},
			else: { true }
		]);
	}

	Function of String is checkMatchArmYield(Expression is val, String is expected){
		local Boolean is savedArmValue: :inValueBranch;
		local String is savedArmExpected: :currentYieldExpected;
		if({ expected != '' && !:isVoid(t: expected) }, {
			:inValueBranch: true;
			:currentYieldExpected: expected;
		});
		:inferExpressionType(expr: val);
		:inValueBranch: savedArmValue;
		:currentYieldExpected: savedArmExpected;
		local String is valT: val:resolvedType;
		if({ valT:startsWith(prefix: 'Function:') && valT:length() > 9 }, {
			local String is yieldT: valT:substring(start: 9, end: valT:length());
			if({ !:isVoid(t: yieldT) }, {
				return yieldT;
			});
		});
		return '';
	}

	Function of String is checkMatchArms(Expression is subj, Expression is arms, String is expected, Expression is defaultArm, Boolean is hasDefault, Boolean is hasExplicitDefault: false){
		local String is subjT: :inferExpressionType(expr: subj);
		# The full subject type, generic spellings included. The stripping
		# below feeds held-member resolution; generic variant payload
		# binding grounds its type args from the full spelling.
		local String is subjFull: subjT;
		# Strip container/generic spellings to the base class name.
		if({ subjT:contains(needle: ' of ') }, {
			subjT: subjT:substring(start: 0, end: subjT:indexOf(search: ' of ', default: 0));
		});
		if({ subjT:contains(needle: ':') }, {
			subjT: subjT:split(delimiter: ':'):get(index: 0);
		});
		if({ subjT == '' || subjT == Primitive:ANY:value() || !:registeredClasses:has(key: subjT) }, {
			:addError(line: :currentLine, msg: 'Conditional:match subjects must be class-typed values; \'' . subjT . '\' cannot be matched.');
			return 'Any';
		});
		# Match is identity dispatch over class instances: a
		# primitive-typed held constant carries no association with its
		# owner class, so it is not a match subject — EXCEPT String,
		# whose string-literal keys compare by value (the CBackendUtils/
		# TemplateEscapes shape).
		if({ :isPrimitive(t: subjT) && subjT != Primitive:STRING:value() && subjT != 'Str' }, {
			:addError(line: :currentLine, msg: 'Match subjects are class instances; primitive-typed held constants are compared directly with == or spec_string_equals.');
			return 'Any';
		});
		local Boolean is rooted: :isSubclassOf(subName: subjT, baseName: :names:enumHeader());
		local Array of String is covered: [];
		local Boolean is hasElse: false;
		local Boolean is anyValue: false;
		local Boolean is anyVoid: false;
		local String is resT: '';
		local Boolean is bad: false;
		local Array of Expression is armKeys: [];
		local Array of Expression is armVals: [];
		match(on: arms, when: [
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				armKeys: keys;
				armVals: values;
			},
			else: {}
		]);
		local Int is keyTotal: armKeys:length();
		local Int is ki: 0;
		repeat(count: keyTotal, worker: {
			local Expression is key: armKeys:get(index: ki);
				local Expression is val: armVals:get(index: ki);
				ki: ki + 1;
				local Boolean is keyIsElse: match(on: key, when: [
					Expression:Ident: local Function of Boolean(String is name){ return name == 'else'; },
					else: { false }
				]);
				# The else arm closes the table: arms after it are dead.
				if({ hasElse && !keyIsElse }, {
					:addError(line: :currentLine, msg: 'Match arms after else are unreachable; move else last.');
					bad: true;
				});
				if({ keyIsElse }, {
					if({ hasElse }, {
						:addError(line: :currentLine, msg: 'Duplicate else arm in the match table.');
					});
					hasElse: true;
				}, {
					local Array of Expression is keyTargets: match(on: key, when: [
						Expression:ArrayLit: local Function of Array of Expression(Array of Expression is items){ return items; },
						else: { [key] }
					]);
					keyTargets:each(action: local Function(Expression is one){
						# String-literal keys match String subjects by value.
						local Boolean is handledStr: match(on: one, when: [
							Expression:StringLit: local Function of Boolean(String is value){
								if({ subjT != Primitive:STRING:value() }, {
									:addError(line: :currentLine, msg: 'String-literal match keys match String subjects; \'' . subjT . '\' is not one.');
									bad: true;
								}, {
									local String is target: 'str:' . value;
									if({ covered:indexOf(search: target, default: -1) >= 0 }, {
										:addError(line: :currentLine, msg: 'Duplicate match key \'' . value . '\'.');
										bad: true;
									}, {
										covered:add(item: target);
									});
								});
								return true;
							},
							else: { false }
						]);
						if({ handledStr }, {
							return;
						});
						local String is keyName: match(on: one, when: [
							Expression:Ident: local Function of String(String is name){ return name; },
							Expression:Path: local Function of String(Array of String is segments){
								return if({ segments:length() > 0 }, {
									segments:get(index: segments:length() - 1)
								}, {
									''
								});
							},
							else: { '' }
						]);
						if({ keyName == '' }, {
							:addError(line: :currentLine, msg: 'Match keys must be held-member references.');
							bad: true;
						}, {
							# Held members first; the variant registry is the
							# interim bridge — today's enum
							# variants match until the sugar migrates.
							local String is owner: :findHeldOwnerClass(className: subjT, memberName: keyName);
							if({ owner == '' && :allEnumNames:has(key: subjT) }, {
								# The interim bridge: today's
								# enum variants ARE the subject enum's own member
								# list — resolved directly, no global registry
								# (variant names collide across enums).
								local ClassInfo is enumCls: :findClass(name: subjT);
								local Boolean is variantFound: false;
								enumCls:members:each(action: local Function(Member is m){
									local Boolean is initIsArr: m:hasInit && match(on: m:initExpr, when: [
										Expression:ArrayLit: local Function of Boolean(Array of Expression is items){ return true; },
										else: { false }
									]);
									if({ !variantFound && m:name == keyName && !initIsArr }, {
										variantFound: true;
									});
								});
								if({ variantFound }, {
									owner: subjT;
								});
							}, {
								# The class-model bridge: a
								# desugared TAGGED enum's variants are its nested
								# subclasses — the key admits when one matches.
								if({ :bindings:isClassModelEnum(c: :findClass(name: subjT)) }, {
									local ClassInfo is cmCls: :findClass(name: subjT);
									cmCls:members:each(action: local Function(Member is m){
										if({ owner == '' && m:kind == MemberKind:CLASS && m:nestedClass:name == keyName }, {
											owner: subjT;
										});
									});
								});
							});
							if({ owner == '' }, {
								:addError(line: :currentLine, msg: 'Match key \'' . keyName . '\' is not a held member of \'' . subjT . '\'.');
								bad: true;
							}, {
								local String is target: owner . ':' . keyName;
								if({ covered:indexOf(search: target, default: -1) >= 0 }, {
									:addError(line: :currentLine, msg: 'Duplicate match key \'' . keyName . '\'.');
									bad: true;
								}, {
									covered:add(item: target);
									if({ :allEnumNames:has(key: owner) || :bindings:isClassModelEnum(c: :findClass(name: owner)) }, {
										# Payload arms (the Stage-5 form pulled forward):
										# an arm closure's parameters bind the tagged
										# variant's constructor payloads — type them
										# from the variant's declared parameters.
										match(on: val, when: [
											Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
												if({ params:length() > 0 }, {
												# The variant's parameter surface: the legacy
														# member (today's enums) or the desugared
														# nested subclass's init.
														local Member is pvMem: Member:init(kind: MemberKind:FIELD);
														local ClassInfo is subCls: :findClass(name: owner . ':' . keyName);
														if({ :allEnumNames:has(key: owner) }, {
															local ClassInfo is pvCls: :findClass(name: owner);
															pvCls:members:each(action: local Function(Member is m){
																local Boolean is initIsArr: m:hasInit && match(on: m:initExpr, when: [
																	Expression:ArrayLit: local Function of Boolean(Array of Expression is items){ return true; },
																	else: { false }
																]);
																if({ pvMem:name == '' && m:name == keyName && !initIsArr }, {
																	pvMem: m;
																});
															});
														}, {
															if({ subCls:name != '' }, {
																subCls:members:each(action: local Function(Member is m){
																	if({ pvMem:name == '' && m:kind == MemberKind:METHOD && m:name == 'init' }, {
																		pvMem: m;
																	});
																});
															});
														});
														if({ params:length() > pvMem:params:length() }, {
															:addError(line: :currentLine, msg: 'Match arm for \'' . owner . ':' . keyName . '\' binds ' . (params:length() as String) . ' parameter(s), but the variant declares ' . (pvMem:params:length() as String) . '.');
															bad: true;
														});
														# Generic variants: the grounded subject type
														# ('Maybe:Int') supplies the type args the
														# variant's parameters are read against.
														local Array of String is groundedArgs: [];
														if({ subCls:typeParams:length() > 0 }, {
															local Type is subjNode: :parseTypeNode(s: subjFull);
															if({ subjNode:name == subCls:name || subjNode:name == owner }, {
																subjNode:params:each(action: local Function(Type is pa){
																	groundedArgs:add(item: :formatVarTypeString(t: pa));
																});
															});
														});
														local Int is pbi: 0;
														params:each(action: local Function(Parameter is bp){
															if({ pbi < pvMem:params:length() }, {
																local Parameter is vp: pvMem:params:get(index: pbi);
																if({ bp:paramType:name == '' || bp:paramType:name == Primitive:ANY:value() }, {
																	if({ groundedArgs:length() > pbi }, {
																		bp:paramType: :parseTypeNode(s: groundedArgs:get(index: pbi)):clone();
																	}, {
																		bp:paramType: vp:paramType;
																	});
																}, {
																	local String is bpT: :formatVarTypeString(t: bp:paramType);
																	local String is vpT: :formatVarTypeString(t: vp:paramType);
																	if({ groundedArgs:length() > 0 }, {
																		vpT: :substituteTypeParam(rawType: vpT, cls: subCls, typeArgs: groundedArgs);
																	});
																	if({ !:isAssignable(target: bpT, source: vpT) }, {
																		:addError(line: :currentLine, msg: 'Match arm parameter \'' . bp:name . '\' for \'' . owner . ':' . keyName . '\' has type \'' . bpT . '\', expected \'' . vpT . '\'.');
																		bad: true;
																	});
																});
															});
															pbi: pbi + 1;
														});
												});
											},
											else: {}
										]);
									}, {
										:checkMemberVisibility(ownerClass: owner, member: :findHeldMember(className: subjT, memberName: keyName), memberName: keyName);
									});
								});
							});
						});
					});
				});
				local Boolean is valIsAnon: match(on: val, when: [
					Expression:AnonFn: local Function of Boolean(Type is returnType, Array of Parameter is params, Array of Statement is body){ return true; },
					else: { false }
				]);
				if({ !valIsAnon }, {
					:addError(line: :currentLine, msg: 'Match arm bodies must be closures: \'key: { ... }\'.');
					bad: true;
				}, {
					# A value-context match arms its closures with the
					# expected yield: the arm's trailing expression IS the
					# arm's value (the parser's explicit-terminator form),
					# typed against the match's expected type — not against
					# the enclosing method's return.
					local Boolean is savedArmValue: :inValueBranch;
					local String is savedArmExpected: :currentYieldExpected;
					if({ expected != '' && !:isVoid(t: expected) }, {
						:inValueBranch: true;
						:currentYieldExpected: expected;
					});
					:inferExpressionType(expr: val);
					:inValueBranch: savedArmValue;
					:currentYieldExpected: savedArmExpected;
					local String is valT: val:resolvedType;
					if({ valT:startsWith(prefix: 'Function:') && valT:length() > 9 }, {
						local String is yieldT: valT:substring(start: 9, end: valT:length());
						if({ :isVoid(t: yieldT) }, {
							anyVoid: true;
						}, {
							anyValue: true;
							if({ resT == '' }, {
								resT: yieldT;
							}, {
								if({ !:isAssignable(target: resT, source: yieldT) && !:isAssignable(target: yieldT, source: resT) }, {
									:addError(line: :currentLine, msg: 'The match arms yield incompatible types (\'' . resT . '\' and \'' . yieldT . '\').');
									bad: true;
								});
							});
						});
					}, {
						anyVoid: true;
					});
				});
		});
		if({ hasDefault }, {
			if({ hasElse }, {
				:addError(line: :currentLine, msg: 'Match has both an else arm and a non-empty default; use only one.');
				bad: true;
			}, {
				hasElse: true;
				local Boolean is defIsAnon: false;
				match(on: defaultArm, when: [
					Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
						if({ params:length() > 0 }, {
							:addError(line: :currentLine, msg: 'Match default arm takes no parameters.');
							bad: true;
						});
						defIsAnon: true;
					}
				], default: {});
				if({ !defIsAnon }, {
					:addError(line: :currentLine, msg: 'Match arm bodies must be closures: \'key: { ... }\'.');
					bad: true;
				}, {
					local String is defYieldT: :checkMatchArmYield(val: defaultArm, expected: expected);
					if({ defYieldT != '' }, {
						anyValue: true;
						if({ resT == '' }, {
							resT: defYieldT;
						}, {
							if({ !:isAssignable(target: resT, source: defYieldT) && !:isAssignable(target: defYieldT, source: resT) }, {
								:addError(line: :currentLine, msg: 'The match arms yield incompatible types (\'' . resT . '\' and \'' . defYieldT . '\').');
								bad: true;
							});
						});
					}, {
						anyVoid: true;
					});
				});
			});
		});
		if({ bad }, {
			return if({ anyValue && resT != '' }, { resT }, { 'Void' });
		});
		if({ anyValue && anyVoid }, {
			:addError(line: :currentLine, msg: 'The match arms mix value-yielding and void closures.');
		});
		if({ rooted }, {
			local ClassInfo is subjCls: :findClass(name: subjT);
			local Boolean is todayEnum: :allEnumNames:has(key: subjT);
			local String is missing: '';
			subjCls:members:each(action: local Function(Member is m){
				# Class-model enum: nested subclasses (tagged enum) OR held
				# fields (value/plain enum) are the closed variant set.
				# Legacy/plain enum: non-array members in allEnumNames.
				local Boolean is initIsArr: m:hasInit && match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function of Boolean(Array of Expression is items){ return true; },
					else: { false }
				]);
				local Boolean is variantMember: false;
				if({ todayEnum }, {
					variantMember: !initIsArr;
				}, {
					variantMember: m:kind == MemberKind:CLASS || (m:kind == MemberKind:FIELD && m:hasModifier(kw: Keyword:HELD));
				});
				if({ variantMember }, {
					local String is vName: if({ m:kind == MemberKind:CLASS }, { m:nestedClass:name }, { m:name });
					if({ covered:indexOf(search: subjT . ':' . vName, default: -1) < 0 }, {
						if({ missing != '' }, {
							missing: missing . ', ';
						});
						missing: missing . subjT . ':' . vName;
					});
				});
			});
			if({ missing != '' && !hasElse && !hasExplicitDefault }, {
				:addError(line: :currentLine, msg: 'Non-exhaustive match: missing arm(s) ' . missing . ' of \'' . subjT . '\'; add arms or an else.');
			});
			if({ missing == '' && (hasElse || hasExplicitDefault) }, {
				:addError(line: :currentLine, msg: 'Redundant else arm in exhaustive match on \'' . subjT . '\'; all variants are already covered.');
			});
		});
		if({ anyValue && !hasElse && !rooted }, {
			:addError(line: :currentLine, msg: 'A value-yielding match requires an else arm (the subject may match no key).');
		});
		return if({ anyValue && resT != '' }, { resT }, { 'Void' });
	}

	## Validates the PREDICATE arm table — the subject-less match
	## (`match(when: [...])` with no `on:`). The keys are closures: the
	## first that holds runs its arm, `else` names the fallback. No
	## held resolution and no enum coverage apply (there is no subject
	## to close a set over), so the value form requires `else` — Never
	## Null holds the same way the unrooted subject matches do. The
	## keys coerce to Boolean before their bodies check (the branch
	## call's check-closure rule). Compile-time only: the runtime
	## dispatch serves the string-keyed subject tables, and a runtime
	## map can neither preserve scan order nor carry closure keys.
	##
	## @param arms: The literal arm table (a MAP expression).
	## @return: The unified arm-yield type ('Void' when none yields).
	Function of String is checkPredicateArms(Expression is arms, String is expected, Expression is defaultArm, Boolean is hasDefault){
		local Boolean is hasElse: false;
		local Boolean is anyValue: false;
		local Boolean is anyVoid: false;
		local String is resT: '';
		local Boolean is bad: false;
		local Array of Expression is armKeys: [];
		local Array of Expression is armVals: [];
		match(on: arms, when: [
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				armKeys: keys;
				armVals: values;
			},
			else: {}
		]);
		local Int is keyTotal: armKeys:length();
		local Int is ki: 0;
		repeat(count: keyTotal, worker: {
			local Expression is key: armKeys:get(index: ki);
				local Expression is val: armVals:get(index: ki);
				ki: ki + 1;
				local Boolean is keyIsElse: match(on: key, when: [
					Expression:Ident: local Function of Boolean(String is name){ return name == 'else'; },
					else: { false }
				]);
				# The else arm closes the table: arms after it are dead.
				if({ hasElse && !keyIsElse }, {
					:addError(line: :currentLine, msg: 'Match arms after else are unreachable; move else last.');
					bad: true;
				});
				if({ keyIsElse }, {
					if({ hasElse }, {
						:addError(line: :currentLine, msg: 'Duplicate else arm in the match table.');
					});
					hasElse: true;
				}, {
					local Boolean is keyOk: false;
					match(on: key, when: [
						Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
							if({ params:length() > 0 }, {
								:addError(line: :currentLine, msg: 'Predicate match keys take no parameters.');
								bad: true;
							});
							if({ returnType:name == '' || returnType:name == :names:voidName() }, {
								returnType:name: Primitive:BOOLEAN:value();
							});
							keyOk: true;
						}
					], default: {});
					if({ !keyOk }, {
						:addError(line: :currentLine, msg: 'Predicate match keys must be closures: `{ condition }`.');
						bad: true;
					}, {
						:inferExpressionType(expr: key);
					});
				});
				local Boolean is valIsAnon: match(on: val, when: [
					Expression:AnonFn: local Function of Boolean(Type is returnType, Array of Parameter is params, Array of Statement is body){
						if({ params:length() > 0 }, {
							:addError(line: :currentLine, msg: 'Predicate match arms take no parameters (there is no subject to bind).');
							bad: true;
						});
						return true;
					},
					else: { false }
				]);
				if({ !valIsAnon }, {
					:addError(line: :currentLine, msg: 'Match arm bodies must be closures: \'key: { ... }\'.');
					bad: true;
				}, {
					# the same value-context arm yield as the subject form:
					# the arm's trailing expression types against the match's
					# expected type.
					local Boolean is savedArmValue: :inValueBranch;
					local String is savedArmExpected: :currentYieldExpected;
					if({ expected != '' && !:isVoid(t: expected) }, {
						:inValueBranch: true;
						:currentYieldExpected: expected;
					});
					:inferExpressionType(expr: val);
					:inValueBranch: savedArmValue;
					:currentYieldExpected: savedArmExpected;
					local String is valT: val:resolvedType;
					if({ valT:startsWith(prefix: 'Function:') && valT:length() > 9 }, {
						local String is yieldT: valT:substring(start: 9, end: valT:length());
						if({ :isVoid(t: yieldT) }, {
							anyVoid: true;
						}, {
							anyValue: true;
							if({ resT == '' }, {
								resT: yieldT;
							}, {
								if({ !:isAssignable(target: resT, source: yieldT) && !:isAssignable(target: yieldT, source: resT) }, {
									:addError(line: :currentLine, msg: 'The match arms yield incompatible types (\'' . resT . '\' and \'' . yieldT . '\').');
									bad: true;
								});
							});
						});
					}, {
						anyVoid: true;
					});
				});
		});
		if({ hasDefault }, {
			if({ hasElse }, {
				:addError(line: :currentLine, msg: 'Match has both an else arm and a non-empty default; use only one.');
				bad: true;
			}, {
				hasElse: true;
				local Boolean is defIsAnon: false;
				match(on: defaultArm, when: [
					Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
						if({ params:length() > 0 }, {
							:addError(line: :currentLine, msg: 'Match default arm takes no parameters.');
							bad: true;
						});
						defIsAnon: true;
					}
				], default: {});
				if({ !defIsAnon }, {
					:addError(line: :currentLine, msg: 'Match arm bodies must be closures: \'key: { ... }\'.');
					bad: true;
				}, {
					local String is defYieldT: :checkMatchArmYield(val: defaultArm, expected: expected);
					if({ defYieldT != '' }, {
						anyValue: true;
						if({ resT == '' }, {
							resT: defYieldT;
						}, {
							if({ !:isAssignable(target: resT, source: defYieldT) && !:isAssignable(target: defYieldT, source: resT) }, {
								:addError(line: :currentLine, msg: 'The match arms yield incompatible types (\'' . resT . '\' and \'' . defYieldT . '\').');
								bad: true;
							});
						});
					}, {
						anyVoid: true;
					});
				});
			});
		});
		if({ bad }, {
			return if({ anyValue && resT != '' }, { resT }, { 'Void' });
		});
		if({ anyValue && anyVoid }, {
			:addError(line: :currentLine, msg: 'The match arms mix value-yielding and void closures.');
		});
		if({ anyValue && !hasElse }, {
			:addError(line: :currentLine, msg: 'A value-yielding predicate match requires an else arm (no key may hold).');
		});
		return if({ anyValue && resT != '' }, { resT }, { 'Void' });
	}

	## Validates call-site argument types against the resolved signature.
	##
	## Named arguments match by parameter name; unmatched named arguments
	## fall back to positional matching. Any-typed parameters and arguments
	## are skipped; builtin stub signatures are exempt.
	##
	## @param callExpr: The CALL expression.
	Function is checkCallArguments(Expression is callExpr){
		local CallData is cd: match(on: callExpr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: { CallData:init(target: Expression:Unknown, name: '', args: []) }
		]);
		local String is targetType: cd:target:resolvedType;
		if({ targetType == :names:selfIdent() || targetType == '' }, {
			targetType: :currentClassName;
		});
		if({ targetType == '' || targetType == Primitive:ANY:value() || :allEnumNames:has(key: targetType) }, {
			return;
		});
		local Array of String is parts: targetType:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		if({ baseClassName == '' || baseClassName == Primitive:ANY:value() || baseClassName == 'Loops' }, {
			return;
		});
		local Member is m: :lookupOverloadedMember(className: :memberLookupRoot(className: targetType), methodName: cd:name, idx: cd:overloadIndex);
		local String is sigDisplay: baseClassName;
		if({ m:kind != MemberKind:METHOD }, {
			# No instance method: the receiver shape
			# may still reach a held function — a bare class-name root,
			# never self or an instance-typed name.
			local String is sigRoot: '';
			match(on: cd:target, when: [
				Expression:Ident: local Function(String is name){ sigRoot: name; },
				Expression:Path: local Function(Array of String is segments){
					if({ segments:length() > 0 }, {
						sigRoot: segments:get(index: 0);
					});
				}
			], default: {});
			if({ sigRoot != '' && sigRoot != :names:selfIdent() && !:localVars:has(key: sigRoot) && !:fieldTypes:has(key: sigRoot) && :registeredClasses:has(key: sigRoot) }, {
				m: :findHeldMethod(className: sigRoot, methodName: cd:name);
				if({ m:name != '' }, {
					sigDisplay: sigRoot;
				});
			});
		});
		if({ m:kind != MemberKind:METHOD || m:name == '' }, {
			return;
		});
		local String is groundedTarget: targetType;
		if({ (cd:name == 'init' || m:hasModifier(kw: Keyword:HELD)) && callExpr:resolvedType != '' }, {
			groundedTarget: callExpr:resolvedType;
		});
		local Type is gNode: :parseTypeNode(s: groundedTarget);
		local Array of String is recvTypeArgs: [];
		gNode:params:each(action: local Function(Type is pt){
			recvTypeArgs:add(item: :formatTypeString(t: pt));
		});
		local ClassInfo is recvClsInfo: :findClass(name: baseClassName);
		local String is mTp: :detectMethodTypeParamForMember(m: m, cls: recvClsInfo);
		:validateArgsAgainstSignature(callExpr: callExpr, params: m:params, recvCls: recvClsInfo, displayTarget: sigDisplay, recvTypeArgs: recvTypeArgs, methodTypeParam: mTp);
		if({ cd:name == 'init' && m:params:length() > 0 }, {
			local Parameter is lastP: m:params:get(index: m:params:length() - 1);
			if({ lastP:isVariadic && lastP:paramType:name == 'Map' }, {
				:checkVariadicInitRequiredFields(recvCls: recvClsInfo, cd: cd);
			});
		});
	}

	local Function is checkVariadicInitRequiredFields(ClassInfo is recvCls, CallData is cd){
		if({ recvCls:name == '' || :isBindingDeclaration(cls: recvCls) }, { return; });
		recvCls:members:each(action: local Function(Member is fm){
			# Required-field validation covers PUBLIC fields only: `local`/
			# `contained` fields are invisible outside the declaring class,
			# so no caller can ever supply them (e.g. Stack's private
			# `T is zeroDefault` Never-Null fallback).
			if({ fm:kind == MemberKind:FIELD && !fm:hasInit && !fm:hasModifier(kw: Keyword:HELD) && !fm:hasModifier(kw: Keyword:LOCAL) && !fm:hasModifier(kw: Keyword:CONTAINED) && fm:name != 'using' && fm:name != 'namespace' && fm:name != 'castable' && fm:name != 'group' }, {
				local String is fTypeStr: :formatVarTypeString(t: fm:memberType);
				local Boolean is supplied: false;
				cd:args:each(action: local Function(NamedArg is a){
					if({ !supplied && a:name == fm:name }, {
						local String is argT: a:value:resolvedType;
						if({ argT != '' && (argT == fTypeStr || :isAssignable(target: fTypeStr, source: argT)) }, {
							supplied: true;
						});
					});
				});
				if({ !supplied }, {
					:addError(line: :currentLine, msg: "Field '" . fm:name . "' of '" . recvCls:name . "' has no default value and is not assigned with matching type '" . :displayType(t: fTypeStr) . "' in constructor call.");
				});
			});
		});
	}

	## Validates a call's arguments against an explicit parameter list:
	## named arguments match by parameter name, positional by index,
	## defaults fill the rest. Shared by the instance and the held
	## dispatch paths.
	##
	## @param callExpr: The CALL expression.
	## @param params: The signature's parameters.
	## @param recvCls: The declaring class.
	## @param displayTarget: The display spelling for diagnostics.
	## @param recvTypeArgs: Concrete generic type arguments of the receiver.
	## @param methodTypeParam: Method-level type parameter name ('' when none).
	Function is validateArgsAgainstSignature(Expression is callExpr, Array of Parameter is params, ClassInfo is recvCls, String is displayTarget, Array of String is recvTypeArgs: [], String is methodTypeParam: ''){
		local CallData is cd: match(on: callExpr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: { CallData:init(target: Expression:Unknown, name: '', args: []) }
		]);
		if({ params:length() == 0 }, {
			if({ cd:args:length() > 0 && !:isBindingDeclaration(cls: recvCls) && displayTarget != 'Conditional' && displayTarget != 'Loops' }, {
				:addError(line: :currentLine, msg: "No signature of '" . displayTarget . "." . cd:name . "' takes " . (cd:args:length() as String) . " argument(s).");
			});
			return;
		});
		local Array of String is recvTypeParams: recvCls:typeParams;
		local Int is pIdx: 0;
		params:each(action: local Function(Parameter is p){
			local String is pName: p:name;
			local String is pT: p:paramType:name;
			if({ p:isVariadic }, {
				if({ pT == 'Array' }, {
					local String is elemT: Primitive:ANY:value();
					if({ p:paramType:params:length() >= 1 }, {
						elemT: :formatVarTypeString(t: p:paramType:params:get(index: 0));
						if({ recvTypeParams:length() > 0 && recvTypeArgs:length() > 0 }, {
							elemT: :substituteTypeParam(rawType: elemT, cls: recvCls, typeArgs: recvTypeArgs);
						});
					});
					local Int is ai: 0;
					cd:args:each(action: local Function(NamedArg is a){
						if({ ai >= pIdx && a:name == '' }, {
							local String is argT: a:value:resolvedType;
							if({ elemT != Primitive:ANY:value() && argT != '' && argT != Primitive:ANY:value() && !:isAssignable(target: elemT, source: argT) }, {
								local String is msg: :errText:errCannotAssignArg(label: 'position ' . (ai + 1), target: displayTarget, method: cd:name, fromType: argT, toType: :displayType(t: elemT));
								:addError(line: :currentLine, msg: msg);
							});
						});
						ai: ai + 1;
					});
				}, {
					local String is valT: Primitive:ANY:value();
					if({ p:paramType:params:length() >= 2 }, {
						valT: :formatVarTypeString(t: p:paramType:params:get(index: 1));
						if({ recvTypeParams:length() > 0 && recvTypeArgs:length() > 0 }, {
							valT: :substituteTypeParam(rawType: valT, cls: recvCls, typeArgs: recvTypeArgs);
						});
					});
					local Map of String to String is fixedNames: Map:init();
					local Int is fni: 0;
					while({ fni < pIdx }, {
						fixedNames:set(key: params:get(index: fni):name, value: '1');
						fni++;
					});
					cd:args:each(action: local Function(NamedArg is a){
						if({ a:name != '' && !fixedNames:has(key: a:name) }, {
							local String is argT: a:value:resolvedType;
							if({ valT != Primitive:ANY:value() && argT != '' && argT != Primitive:ANY:value() && !:isAssignable(target: valT, source: argT) }, {
								local String is msg: :errText:errCannotAssignArg(label: a:name, target: displayTarget, method: cd:name, fromType: argT, toType: :displayType(t: valT));
								:addError(line: :currentLine, msg: msg);
							});
						});
					});
				});
				pIdx: pIdx + 1;
				return;
			});
			# a Function-typed param enforces
			# assignability in the colon form — the raw name would broaden
			# every Function param to plain Function (the void-into-check
			# hole).
			local String is pTF: pT;
			if({ pT:startsWith(prefix: 'Function') || p:paramType:params:length() > 0 }, {
				pTF: :formatVarTypeString(t: p:paramType);
			});
			if({ recvTypeParams:length() > 0 && recvTypeArgs:length() > 0 }, {
				pTF: :substituteTypeParam(rawType: pTF, cls: recvCls, typeArgs: recvTypeArgs);
			});
			local Boolean is isMethodGenericParam: methodTypeParam != '' && (pTF == methodTypeParam || pTF == 'Function:' . methodTypeParam);
			local Boolean is isUngroundedExternalGeneric: isMethodGenericParam || (recvTypeArgs:length() == 0 && recvCls:name != :currentClassName && recvTypeParams:indexOf(search: pTF, default: -1) >= 0);
			if({ pT != :names:selfFieldMarker() && pTF != Primitive:ANY:value() && pTF != '' && !isUngroundedExternalGeneric }, {
				local Expression is matchedValue: Expression:Unknown;
				local Boolean is found: false;
				local Int is posIdx: 0;
				cd:args:each(action: local Function(NamedArg is a){
					if({ !found && pName != '' && a:name == pName }, {
						matchedValue: a:value;
						found: true;
					});
				});
				if({ !found }, {
					cd:args:each(action: local Function(NamedArg is a){
						if({ !found && a:name == '' && posIdx == pIdx }, {
							matchedValue: a:value;
							found: true;
						});
						posIdx: posIdx + 1;
					});
				});
				if({ found }, {
					local String is argT: matchedValue:resolvedType;
					if({ argT != '' && argT != Primitive:ANY:value() && !:isAssignable(target: pTF, source: argT) }, {
						local String is label: if({ pName != '' }, { pName }, { 'position ' . (pIdx + 1) });
						local String is msg: :errText:errCannotAssignArg(label: label, target: displayTarget, method: cd:name, fromType: argT, toType: :displayType(t: pTF));
						:addError(line: :currentLine, msg: msg);
					});
				}, {
					if({ !p:hasDefault && !:isBindingDeclaration(cls: recvCls) }, {
						# Binding declarations (sysinternal + runtime-managed)
						# sketch API surface, not call contracts — their C
						# implementations carry optional/variadic semantics.
						local String is msg: :errText:errMissingArg(paramName: pName, target: displayTarget, method: cd:name);
						:addError(line: :currentLine, msg: msg);
					});
				});
			});
			pIdx: pIdx + 1;
		});
	}

	## §I.2: resolves one same-name member group to the
	## overload the call selects, stamping expr:num. Candidates
	## are the same-name METHOD members of the nearest declaring ancestor
	## (all parents walked, first subtree wins). Stage 1 filters by arity
	## (all-positional) or name-set (all-named) — mixed calls are
	## rejected. Stage 2, among multiple survivors, filters by exact type
	## match. Exactly one candidate or a compile error; a single candidate
	## short-circuits (legacy semantics, assignability checked
	## downstream).
	##
	## @param className: The (possibly grounded) receiver class name.
	## @param methodName: The called member's name.
	## @param expr: The CALL expression, stamped on selection.
	## @return: The selected member, or an empty node when unresolved.
	Function of Member is selectOverload(String is className, String is methodName, Expression is expr){
		local Member is none: Member:init(kind: MemberKind:METHOD);
		local String is baseName: :memberLookupRoot(className: className);
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		:collectOverloadGroup(className: baseName, methodName: methodName, acc: group, ownerAcc: ownerAcc);
		if({ group:length() == 0 }, {
			return none;
		});
		local CallData is cd: match(on: expr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: { CallData:init(target: Expression:Unknown, name: '', args: []) }
		]);
		# §I.3: no mixed calls — enforced globally, including
		# single-member names. The scoped-region desugaring no longer
		# produces mixed calls: its remainder binds to the unbound last
		# Function parameter instead of riding as an argument (§as).
		local Array of NamedArg is allArgs: cd:args;
		local Array of NamedArg is args: allArgs;
		local Boolean is isScoped: cd:scopedRemainder;
		if({ isScoped }, {
			# The scope slot binds the remainder: the explicit arguments are
			# every argument but the last.
			args: allArgs:slice(start: 0, end: allArgs:length() - 1);
		});
		local Boolean is allPos: true;
		local Boolean is allNamed: true;
		args:each(action: local Function(NamedArg is a){
			if({ a:name == '' }, {
				allNamed: false;
			}, {
				allPos: false;
			});
		});
		if({ !allPos && !allNamed }, {
			:addError(line: :currentLine, msg: 'Mixed positional and named arguments are not supported; use one form (§I.3).');
			return none;
		});
		if({ group:length() == 1 }, {
			local Member is only: group:get(index: 0);
			if({ isScoped && !:scopeSlotOk(m: only, explicitCount: args:length()) }, {
				:addError(line: :currentLine, msg: 'The scoped region requires exactly one unbound Function parameter at the end of \'' . baseName . '.' . methodName . '\' (§as).');
				return none;
			});
			cd:overloadIndex: 0;
			return only;
		});
		if({ allNamed }, {
			local Boolean is dupArg: false;
			while([Int is ai: 0], { !dupArg && ai < args:length() }, {
				while([Int is aj: ai + 1], { !dupArg && aj < args:length() }, {
					local NamedArg is argA: args:get(index: ai);
					local NamedArg is argB: args:get(index: aj);
					if({ argA:name == argB:name }, {
						dupArg: true;
					});
					aj++;
				});
				ai++;
			});
			if({ dupArg }, {
				:addError(line: :currentLine, msg: 'Duplicate named argument in call to \'' . baseName . '.' . methodName . '\'.');
				return none;
			});
		});
		local Array of Member is survivors: [];
		# §as: a scoped remainder binds to an unbound last
		# Function parameter — it never widens the arity. Pass 1: exact
		# arity on the explicit arguments. Pass 2 (only when pass 1 is
		# empty and the call is scoped): params == explicit + 1 with the
		# last parameter Function-typed — the open scope slot.
		local Int is wantCount: args:length();
		group:each(action: local Function(Member is m){
			local Boolean is hasVar: m:params:length() > 0 && m:params:get(index: m:params:length() - 1):isVariadic;
			if({ hasVar && !isScoped }, {
				local Parameter is vp: m:params:get(index: m:params:length() - 1);
				local Int is fixedCount: m:params:length() - 1;
				if({ allPos }, {
					if({ vp:paramType:name == 'Array' || wantCount == 0 }, {
						local Boolean is fixedOk: true;
						local Int is pi: wantCount;
						while({ fixedOk && pi < fixedCount }, {
							if({ !m:params:get(index: pi):hasDefault }, { fixedOk: false; });
							pi++;
						});
						if({ fixedOk }, { survivors:add(item: m); });
					});
					return;
				});
				if({ vp:paramType:name == 'Map' }, {
					local Boolean is fixedMatch: true;
					local Int is fi: 0;
					while({ fixedMatch && fi < fixedCount }, {
						local Parameter is fp: m:params:get(index: fi);
						local Boolean is present: false;
						args:each(action: local Function(NamedArg is a){
							if({ a:name == fp:name }, { present: true; });
						});
						if({ !present && !fp:hasDefault }, { fixedMatch: false; });
						fi++;
					});
					if({ fixedMatch }, { survivors:add(item: m); });
				});
				return;
			});
			if({ m:params:length() < wantCount || (isScoped && m:params:length() != wantCount) }, {
				return;
			});
			if({ allPos }, {
				local Boolean is tailDefaulted: true;
				local Int is pi: wantCount;
				while({ tailDefaulted && pi < m:params:length() }, {
					local Parameter is tp: m:params:get(index: pi);
					if({ !tp:hasDefault }, {
						tailDefaulted: false;
					});
					pi++;
				});
				if({ tailDefaulted }, {
					survivors:add(item: m);
				});
				return;
			});
			local Boolean is namesMatch: true;
			# Every supplied named argument must correspond to a parameter of m.
			args:each(action: local Function(NamedArg is a){
				if({ namesMatch }, {
					local Boolean is known: false;
					m:params:each(action: local Function(Parameter is p){
						if({ p:name == a:name }, {
							known: true;
						});
					});
					if({ !known }, {
						namesMatch: false;
					});
				});
			});
			local Int is npIdx: 0;
			m:params:each(action: local Function(Parameter is p){
				# The scope slot (the last parameter) is bound by the
				# remainder, not by a named argument.
				if({ namesMatch && !(isScoped && npIdx == m:params:length() - 1) }, {
					local Boolean is present: false;
					args:each(action: local Function(NamedArg is a){
						if({ a:name == p:name }, {
							present: true;
						});
					});
					if({ !present && !p:hasDefault }, {
						namesMatch: false;
					});
				});
				npIdx: npIdx + 1;
			});
			if({ namesMatch }, {
				survivors:add(item: m);
				return;
			});
		});
		if({ survivors:length() == 0 && isScoped }, {
			# Pass 2: the open scope slot — params == explicit + 1, last
			# parameter Function-typed.
			local Array of Member is slots: [];
			group:each(action: local Function(Member is m){
				if({ :scopeSlotOk(m: m, explicitCount: args:length()) }, {
					slots:add(item: m);
				});
			});
			if({ slots:length() == 1 }, {
				local Member is sel: slots:get(index: 0);
				cd:overloadIndex: :indexOfMember(group: group, m: sel);
				return sel;
			});
		});
		if({ survivors:length() == 0 }, {
			if({ allPos }, {
				:addError(line: :currentLine, msg: 'No signature of \'' . baseName . '.' . methodName . '\' takes ' . (args:length() as String) . ' argument(s).');
			}, {
				:addError(line: :currentLine, msg: 'No signature of \'' . baseName . '.' . methodName . '\' matches the named arguments.');
			});
			return none;
		});
		if({ survivors:length() == 1 }, {
			local Member is sel: survivors:get(index: 0);
			if({ isScoped && !:scopeSlotOk(m: sel, explicitCount: args:length()) }, {
				:addError(line: :currentLine, msg: 'The scoped region has no open scope slot in \'' . baseName . '.' . methodName . '\': every parameter is already bound (§as).');
				return none;
			});
			cd:overloadIndex: :indexOfMember(group: group, m: sel);
			return sel;
		});
		local Array of Member is exact: [];
		survivors:each(action: local Function(Member is m){
			if({ :exactTypeMatch(m: m, expr: expr) }, {
				exact:add(item: m);
			});
		});
		if({ exact:length() == 1 }, {
			local Member is sel: exact:get(index: 0);
			if({ isScoped && !:scopeSlotOk(m: sel, explicitCount: args:length()) }, {
				:addError(line: :currentLine, msg: 'The scoped region has no open scope slot in \'' . baseName . '.' . methodName . '\': every parameter is already bound (§as).');
				return none;
			});
			cd:overloadIndex: :indexOfMember(group: group, m: sel);
			return sel;
		});
		if({ isScoped && exact:length() == 0 }, {
			# Pass 2: the open scope slot — params == explicit + 1, last
			# parameter Function-typed.
			local Array of Member is slots: [];
			group:each(action: local Function(Member is m){
				if({ :scopeSlotOk(m: m, explicitCount: args:length()) }, {
					slots:add(item: m);
				});
			});
			if({ slots:length() == 1 }, {
				local Member is sel: slots:get(index: 0);
				cd:overloadIndex: :indexOfMember(group: group, m: sel);
				return sel;
			});
		});
		if({ exact:length() > 1 }, {
			# Prefer an exact-arity match over one that relies on default parameters.
			local Array of Member is exactArity: [];
			exact:each(action: local Function(Member is m){
				if({ m:params:length() == wantCount }, {
					exactArity:add(item: m);
				});
			});
			if({ exactArity:length() == 1 }, {
				local Member is sel: exactArity:get(index: 0);
				if({ isScoped && !:scopeSlotOk(m: sel, explicitCount: args:length()) }, {
					:addError(line: :currentLine, msg: 'The scoped region has no open scope slot in \'' . baseName . '.' . methodName . '\': every parameter is already bound (§as).');
					return none;
				});
				cd:overloadIndex: :indexOfMember(group: group, m: sel);
				return sel;
			});
			:addError(line: :currentLine, msg: 'Ambiguous call to \'' . baseName . '.' . methodName . '\': the arguments match multiple overloads; use named arguments (§I.2).');
			return none;
		});
		local String is argTypes: '';
		args:each(action: local Function(NamedArg is a){
			local String is at: a:value:resolvedType;
			if({ at == '' }, {
				at: 'Any';
			});
			if({ argTypes == '' }, {
				argTypes: at;
			}, {
				argTypes: argTypes . ', ' . at;
			});
		});
		:addError(line: :currentLine, msg: 'No exact overload of \'' . baseName . '.' . methodName . '\' for (' . argTypes . '); cast the arguments or give the signatures distinct names (§I.2).');
		return none;
	}
	## Collects the same-name METHOD members of the nearest declaring
	## ancestor: the first subtree (class, then parents in declaration
	## order) that declares the name wins; deeper walk stops there.
	## Walks every parent (multiple inheritance), first-wins.
	##
	## @param className: The class to start from.
	## @param methodName: The member name.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	## @param acc: The collected group (nearest-declaration semantics).
	## @param ownerAcc: The declaring class name accumulator (reference).
	Function is collectOverloadGroup(String is className, String is methodName, Map of String to String is visited: Map:init(), Array of Member is acc, Array of String is ownerAcc){
		if({ ownerAcc:length() > 0 || acc:length() > 0 || className == '' || className == 'Any' || visited:has(key: className) }, {
			return;
		});
		visited:set(key: className, value: 'true');
		# the qualified nested-class name walks the inner class
		# itself; container forms don't resolve qualified and fall back to
		# the bare root.
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			cls: :findClass(name: className:split(delimiter: ':'):get(index: 0));
		});
		if({ cls:name == '' }, {
			return;
		});
		cls:members:each(action: local Function(Member is m){
			# Instance overloads are held-blind: the
			# class-name prefix reaches exactly the held members.
			if({ m:kind == MemberKind:METHOD && m:name == methodName && !m:hasModifier(kw: Keyword:HELD) }, {
				acc:add(item: m);
			});
		});
		if({ acc:length() > 0 }, {
			# the owner's qualified identity — the bare name of a
			# nested class is not unique across outers.
			ownerAcc:add(item: cls:qualifiedName());
			return;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			:collectOverloadGroup(className: baseName, methodName: methodName, visited: visited, acc: acc, ownerAcc: ownerAcc);
		});
	}

	## §as: true when [m]'s last parameter is the open scope
	## slot — exactly [explicitCount] parameters precede it and the slot is
	## Function-typed (the remainder is a closure).
	##
	## @param m: The candidate overload.
	## @param explicitCount: The explicit argument count.
	## @return: true when the scope slot is open and valid.
	Function of Boolean is scopeSlotOk(Member is m, Int is explicitCount){
		if({ m:params:length() != explicitCount + 1 }, {
			return false;
		});
		local Parameter is slot: m:params:get(index: m:params:length() - 1);
		return slot:paramType:name == 'Function';
	}

	Function of Boolean is isUnboundTypeIdent(String is tp, ClassInfo is cls){
		if({ tp == '' || tp == :names:selfFieldMarker() || :isPrimitive(t: tp) || :registeredClasses:has(key: tp) || :allEnumNames:has(key: tp) }, {
			return false;
		});
		if({ cls:typeParams:indexOf(search: tp, default: -1) >= 0 }, {
			return false;
		});
		return true;
	}

	Function is collectUnboundTypeIdents(Type is t, ClassInfo is cls, Array of String is out){
		if({ :isUnboundTypeIdent(tp: t:name, cls: cls) && out:indexOf(search: t:name, default: -1) < 0 }, {
			out:add(item: t:name);
		});
		t:params:each(action: local Function(Type is p){
			:collectUnboundTypeIdents(t: p, cls: cls, out: out);
		});
	}

	## Detects a valid method-level type parameter on [m] in [cls]: an unbound
	## identifier that appears in at least one parameter type AND in at least
	## one other parameter type or the method's return type. A single-position
	## unknown identifier is NOT a method type parameter (it is an unknown/typo'd type).
	Function of String is detectMethodTypeParamForMember(Member is m, ClassInfo is cls){
		if({ m:name == '' || m:kind != MemberKind:METHOD }, {
			return '';
		});
		local Map of String to Int is paramCounts: Map:init();
		m:params:each(action: local Function(Parameter is p){
			local Array of String is idents: [];
			:collectUnboundTypeIdents(t: p:paramType, cls: cls, out: idents);
			idents:each(action: local Function(String is id){
				paramCounts:set(key: id, value: paramCounts:get(key: id, default: 0) + 1);
			});
		});
		local Array of String is retIdents: [];
		:collectUnboundTypeIdents(t: m:memberType, cls: cls, out: retIdents);
		local String is foundTp: '';
		local Array of String is pKeys: paramCounts:keys();
		pKeys:each(action: local Function(String is id){
			if({ foundTp == '' }, {
				local Int is cnt: paramCounts:get(key: id, default: 0);
				if({ cnt >= 2 || retIdents:indexOf(search: id, default: -1) >= 0 }, {
					foundTp: id;
				});
			});
		});
		return foundTp;
	}

	Function of Boolean is isMethodTypeParam(String is tp, Member is m: Member:init(kind: MemberKind:METHOD), ClassInfo is cls: ClassInfo:init(name: '', baseClass: '', members: [])){
		local ClassInfo is effCls: if({ cls:name != '' }, { cls }, { :currentClassDef });
		if({ !:isUnboundTypeIdent(tp: tp, cls: effCls) }, {
			return false;
		});
		if({ m:name != '' }, {
			return :detectMethodTypeParamForMember(m: m, cls: effCls) == tp;
		});
		return :currentMethodTypeParams:has(key: tp);
	}

	## True when every argument's inferred type equals the bound
	## parameter's declared type (positional by index, named by name).
	##
	## @param m: The candidate overload.
	## @param expr: The CALL expression.
	## @return: true when all argument types match exactly.
	Function of Boolean is exactTypeMatch(Member is m, Expression is expr){
		local CallData is cd: match(on: expr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: { CallData:init(target: Expression:Unknown, name: '', args: []) }
		]);
		local Boolean is allMatch: true;
		local Int is posIdx: 0;
		m:params:each(action: local Function(Parameter is p){
			if({ p:isVariadic }, {
				posIdx: posIdx + 1;
				return;
			});
			local Expression is bound: Expression:Unknown;
			local Boolean is found: false;
			if({ p:name != '' }, {
				cd:args:each(action: local Function(NamedArg is a){
					if({ !found && a:name == p:name }, {
						bound: a:value;
						found: true;
					});
				});
			});
			if({ !found && posIdx < cd:args:length() }, {
				local NamedArg is pa: cd:args:get(index: posIdx);
				if({ pa:name == '' }, {
					bound: pa:value;
					found: true;
				});
			});
			# a Function-typed param compares in the
			# colon form ('Function of Boolean' -> 'Function:Boolean') — the
			# raw name erases the return type and matches every closure.
			local String is pT: p:paramType:name;
			if({ pT:startsWith(prefix: 'Function') }, {
				pT: :formatVarTypeString(t: p:paramType);
			});
			if({ !found }, {
				if({ !p:hasDefault }, {
					allMatch: false;
				});
			}, {
				if({ bound:resolvedType == '' }, {
					allMatch: false;
				}, {
					if({ bound:resolvedType != pT }, {
						local Boolean is genericMatch: false;
						if({ pT:startsWith(prefix: 'Function:') && bound:resolvedType:startsWith(prefix: 'Function:') }, {
							local String is pRet: pT:substring(start: 9, end: pT:length());
							local String is bRet: bound:resolvedType:substring(start: 9, end: bound:resolvedType:length());
							if({ :isMethodTypeParam(tp: pRet, m: m) && bRet != '' && !:isVoid(t: bRet) }, {
								genericMatch: true;
							});
						});
						if({ :isMethodTypeParam(tp: pT, m: m) && !:isVoid(t: bound:resolvedType) }, {
							genericMatch: true;
						});
						if({ !genericMatch }, {
							allMatch: false;
						});
					});
				});
			});
			posIdx: posIdx + 1;
		});
		return allMatch;
	}
	## The 0-based position of [m] within [group] (identity compare).
	##
	## @param group: The same-name member group.
	## @param m: The selected member.
	## @return: The overload index.
	Function of Int is indexOfMember(Array of Member is group, Member is m){
		local Int is idx: 0;
		local Int is hit: 0;
		group:each(action: local Function(Member is g){
			if({ g == m }, {
				hit: idx;
			});
			idx: idx + 1;
		});
		return hit;
	}
	## The selected overload's return type. Single-member names keep the
	## legacy lookup (of-form handling, substitution); overloaded names
	## substitute against the selected member directly (colon-form
	## grounding).
	##
	## @param className: The (possibly grounded) receiver class name.
	## @param selected: The stamped, selected member.
	## @param expr: The CALL expression (for method-level type parameter substitution).
	## @return: The resolved return type.
	Function of String is selectedReturnType(String is className, Member is selected, Expression is expr: Expression:Unknown){
		local String is baseName: :memberLookupRoot(className: className);
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		:collectOverloadGroup(className: baseName, methodName: selected:name, acc: group, ownerAcc: ownerAcc);
		local String is ownerName: if({ ownerAcc:length() > 0 }, { ownerAcc:get(index: 0) }, { baseName });
		local ClassInfo is ownerCls: :findClass(name: ownerName);
		local String is rawT: :formatTypeString(t: selected:memberType);
		local String is mTp: :detectMethodTypeParamForMember(m: selected, cls: ownerCls);
		local CallData is cd: match(on: expr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: { CallData:init(target: Expression:Unknown, name: '', args: []) }
		]);
		if({ cd:args:length() > 0 && rawT != '' && mTp != '' }, {
			local Int is posIdx: 0;
			selected:params:each(action: local Function(Parameter is p){
				local Expression is bound: Expression:Unknown;
				local Boolean is found: false;
				if({ p:name != '' }, {
					cd:args:each(action: local Function(NamedArg is a){
						if({ !found && a:name == p:name }, {
							bound: a:value;
							found: true;
						});
					});
				});
				if({ !found && posIdx < cd:args:length() }, {
					local NamedArg is pa: cd:args:get(index: posIdx);
					if({ pa:name == '' }, {
						bound: pa:value;
						found: true;
					});
				});
				if({ found && bound:resolvedType != '' }, {
					local String is pTF: :formatVarTypeString(t: p:paramType);
					if({ pTF:startsWith(prefix: 'Function:') && bound:resolvedType:startsWith(prefix: 'Function:') }, {
						local String is pRet: pTF:substring(start: 9, end: pTF:length());
						local String is bRet: bound:resolvedType:substring(start: 9, end: bound:resolvedType:length());
						if({ pRet == mTp && bRet != '' }, {
							:groundedGenericMethods:set(key: ownerName . ':' . selected:name, value: true);
							if({ rawT == pRet }, { rawT: bRet; });
							if({ rawT:endsWith(suffix: ':' . pRet) }, {
								rawT: rawT:substring(start: 0, end: rawT:length() - pRet:length()) . bRet;
							});
						});
					});
					if({ pTF == mTp }, {
						:groundedGenericMethods:set(key: ownerName . ':' . selected:name, value: true);
						if({ rawT == pTF }, { rawT: bound:resolvedType; });
						if({ rawT:endsWith(suffix: ':' . pTF) }, {
							rawT: rawT:substring(start: 0, end: rawT:length() - pTF:length()) . bound:resolvedType;
						});
					});
				});
				posIdx: posIdx + 1;
			});
		});
		if({ group:length() <= 1 || ownerAcc:length() == 0 }, {
			if({ rawT != :formatTypeString(t: selected:memberType) }, {
				return rawT;
			});
			return :lookupMethodReturnType(className: className, methodName: selected:name);
		});
		if({ ownerCls:name == '' }, {
			return '';
		});
		local Type is recvNode: :parseTypeNode(s: className);
		local Type is rawNode: :parseTypeNode(s: rawT);
		local Type is subNode: :substituteTypeNode(t: rawNode, cls: ownerCls, typeArgs: recvNode:params);
		return :formatTypeString(t: subNode);
	}
	## The stamped member for a call: the idx-th same-name METHOD member at
	## the nearest declaring ancestor (idx below zero resolves as the
	## first — the legacy single-member shape).
	##
	## @param className: The receiver base class name.
	## @param methodName: The called member's name.
	## @param idx: The stamped overload index.
	## @return: The member, or an empty node when absent.
	Function of Member is lookupOverloadedMember(String is className, String is methodName, Int is idx){
		local Member is none: Member:init(kind: MemberKind:METHOD);
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		:collectOverloadGroup(className: :memberLookupRoot(className: className), methodName: methodName, acc: group, ownerAcc: ownerAcc);
		if({ group:length() == 0 }, {
			return none;
		});
		local Int is use: idx;
		if({ use < 0 }, {
			use: 0;
		});
		if({ use >= group:length() }, {
			use: group:length() - 1;
		});
		local Member is cand: group:get(index: use);
		return cand;
	}
	## True when the current class, or any ancestor (all parents,
	## transitively), instance-imports [className] — as-imports are
	## inherited like the fields they synthesize (§2.1).
	##
	## @param className: Receiver class name.
	## @return: true when imported somewhere up the chain.
	Function of Boolean is isAsImportedInherited(String is className){
		return :importsAsAnywhere(clsName: :currentClassName, targetName: className);
	}

	## Whether a local or field named [name] shadows the bare-call
	## resolution (E9). Only a Function-typed binding does: the bare
	## `name(...)` form is a call, and a call resolves to a callable —
	## a non-Function local that happens to share the name (a String
	## `line` beside an imported Output:line) must not silence the
	## provider. The parser normalizes every bare call to the
	## self-receiver shape, so this guard is what keeps ordinary
	## variable names out of the call's way.
	##
	## @param name: The bare call's method name.
	## @return: true when a Function-typed local or field holds the name.
	Function of Boolean is shadowsAsFunction(String is name, Boolean is isBareCall: true){
		if({ !isBareCall }, {
			return :fieldTypes:getString(key: name, default: ''):startsWith(prefix: 'Function');
		});
		local String is t: :localVars:getString(key: name, default: :fieldTypes:getString(key: name, default: ''));
		return t:startsWith(prefix: 'Function');
	}

	## Recursive import search over the ancestor lattice.
	##
	## @param clsName: Class being visited.
	## @param targetName: The imported class name sought.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	## @return: true when found on this class or an ancestor.
	Function of Boolean is importsAsAnywhere(String is clsName, String is targetName, Map of String to String is visited: Map:init()){
		if({ clsName == '' || clsName == 'Any' || visited:has(key: clsName) }, {
			return false;
		});
		visited:set(key: clsName, value: 'true');
		local ClassInfo is cls: :findClass(name: clsName);
		if({ cls:name == '' }, {
			return false;
		});
		if({ cls:instanceImportsAs(name: targetName) }, {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !viaParent && :importsAsAnywhere(clsName: baseName, targetName: targetName, visited: visited) }, {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## §2.3: collects the as-imported classes providing
	## [methodName] for the bare scope of the current class — own
	## bindings plus every ancestor's, one level deep. Order-stable
	## diagnostics; duplicates dropped.
	##
	## @param methodName: The bare-called function name.
	## @return: Provider class names in walk order.
	Function of Array of String is bareScopeProviders(String is methodName){
		local Array of String is out: [];
		:collectBareProviders(clsName: :currentClassName, methodName: methodName, acc: out);
		return out;
	}

	## Recursive provider collection over the ancestor lattice.
	##
	## @param clsName: Class being visited.
	## @param methodName: The bare-called function name.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	## @param acc: The provider accumulator.
	Function is collectBareProviders(String is clsName, String is methodName, Map of String to String is visited: Map:init(), Array of String is acc){
		if({ clsName == '' || clsName == 'Any' || visited:has(key: clsName) }, {
			return;
		});
		visited:set(key: clsName, value: 'true');
		local ClassInfo is cls: :findClass(name: clsName);
		if({ cls:name == '' }, {
			return;
		});
		cls:members:each(action: local Function(Member is m){
			if({ m:name == 'using' && m:hasInit }, {
				match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function(Array of Expression is items){
						items:each(action: local Function(Expression is item){
							match(on: item, when: [
								Expression:ArrayLit: local Function(Array of Expression is subItems){
									subItems:each(action: local Function(Expression is seg){
										match(on: seg, when: [
											Expression:UsingAs: local Function(String is className, Array of NamedArg is args){
												if({ seg:usingAsAlias == '' }, {
													local Boolean is already: false;
													acc:each(action: local Function(String is got){
														if({ got == className }, {
															already: true;
														});
													});
													local String is pOwner: :findMemberOwnerClass(className: className, memberName: methodName);
													if({ !already && className != :currentClassName && pOwner != '' && pOwner != 'Class' && pOwner != 'Stringable' && pOwner != 'Loadable' && pOwner != 'Any' }, {
														acc:add(item: className);
													});
												});
											},
											Expression:ArrayLit: local Function(Array of Expression is grpItems){
												grpItems:each(action: local Function(Expression is gseg){
													match(on: gseg, when: [
														Expression:UsingAs: local Function(String is className, Array of NamedArg is args){
															if({ gseg:usingAsAlias == '' }, {
																local Boolean is already: false;
																acc:each(action: local Function(String is got){
																	if({ got == className }, {
																		already: true;
																	});
																});
																local String is pOwner: :findMemberOwnerClass(className: className, memberName: methodName);
																if({ !already && className != :currentClassName && pOwner != '' && pOwner != 'Class' && pOwner != 'Stringable' && pOwner != 'Loadable' && pOwner != 'Any' }, {
																	acc:add(item: className);
																});
															});
														},
														else: {}
													]);
												});
											},
											else: {}
										]);
									});
								},
								else: {}
							]);
						});
					},
					else: {}
				]);
			});
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			:collectBareProviders(clsName: baseName, methodName: methodName, visited: visited, acc: acc);
		});
	}

	## the per-scope nested-type
	## map. Built once for [className] — own nested classes, the
	## as-imported classes' nested classes, then the base lattice (the
	## outer link serves the inner-of-inner walk) — so a bare nested
	## reference resolves with ONE lookup instead of a per-type lattice
	## walk. [nestedScopeMap] is cleared and rebuilt when the scope
	## changes, keeping the working set small.
	##
	## @param className: The class whose scope resolves the reference.
	## @param typeName: The bare nested-class name sought.
	## @return: The ';'-joined qualified identities, or '' when none.
	Function of String is nestedScopeResolve(String is className, String is typeName){
		if({ :nestedScopeFor != className }, {
			:nestedScopeMap: Map:init();
			:nestedScopeFor: className;
			:collectNestedScopeEntries(clsName: className);
		});
		return :nestedScopeMap:getString(key: typeName, default: '');
	}

	## One scope-map pass over the ancestor lattice: every visited class
	## contributes its own nested classes and its as-imported classes'
	## nested classes to [nestedScopeMap].
	##
	## @param clsName: Class being visited.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	Function is collectNestedScopeEntries(String is clsName, Map of String to String is visited: Map:init()){
		if({ clsName == '' || clsName == 'Any' || visited:has(key: clsName) }, {
			return;
		});
		visited:set(key: clsName, value: 'true');
		local ClassInfo is cls: :findClass(name: clsName);
		if({ cls:name == '' }, {
			return;
		});
		# Own nested classes.
		cls:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:CLASS }, {
				:appendNestedScopeEntry(bare: m:nestedClass:name, q: m:nestedClass:qualifiedName());
			});
		});
		# The as-imported classes' nested classes.
		cls:members:each(action: local Function(Member is m){
			if({ m:name == 'using' && m:hasInit }, {
				match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function(Array of Expression is items){
						items:each(action: local Function(Expression is item){
							match(on: item, when: [
								Expression:ArrayLit: local Function(Array of Expression is segs){
									segs:each(action: local Function(Expression is seg){
										match(on: seg, when: [
											Expression:UsingAs: local Function(String is className, Array of NamedArg is args){
												local ClassInfo is provCls: :findClass(name: className);
												if({ provCls:name != '' }, {
													provCls:members:each(action: local Function(Member is nm){
														if({ nm:kind == MemberKind:CLASS }, {
															:appendNestedScopeEntry(bare: nm:nestedClass:name, q: nm:nestedClass:qualifiedName());
														});
													});
												});
											}
										], default: {});
									});
								}
							], default: {});
						});
					}
				], default: {});
			});
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			:collectNestedScopeEntries(clsName: baseName, visited: visited);
		});
	}

	## Adds one qualified identity under its bare name, deduplicating.
	##
	## @param bare: The nested class's bare name (the map key).
	## @param q: The qualified identity ('Outer:Inner').
	Function is appendNestedScopeEntry(String is bare, String is q){
		if({ bare == '' || q == '' }, {
			return;
		});
		local String is cur: :nestedScopeMap:getString(key: bare, default: '');
		if({ cur == '' }, {
			:nestedScopeMap:set(key: bare, value: q);
		}, {
			local Boolean is dup: false;
			cur:split(delimiter: ';'):each(action: local Function(String is got){
				if({ got == q }, {
					dup: true;
				});
			});
			if({ !dup }, {
				:nestedScopeMap:set(key: bare, value: cur . ';' . q);
			});
		});
	}

	## True when an ancestor of [className] (any parent, transitively)
	## declares [methodName] as a method. The starting class's own members
	## are excluded — an overload group on the class itself is legal.
	##
	## @param className: The class whose ancestors are walked.
	## @param methodName: The member name.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	## @return: true when an ancestor declares the name.
	Function of Boolean is ancestorDeclares(String is className, String is methodName, Map of String to String is visited: Map:init()){
		if({ className == '' || className == 'Any' || visited:has(key: className) }, {
			return false;
		});
		visited:set(key: className, value: 'true');
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: :findClass(name: parts:get(index: 0));
		if({ cls:name == '' }, {
			return false;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !viaParent && :declaresOrInherits(className: baseName, methodName: methodName, visited: visited) }, {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## True when [className] declares [methodName] or inherits it from an
	## ancestor (all parents walked, nearest declaration wins).
	##
	## @param className: Class being visited.
	## @param methodName: The member name.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	## @return: true when declared here or inherited.
	Function of Boolean is declaresOrInherits(String is className, String is methodName, Map of String to String is visited: Map:init()){
		if({ className == '' || className == 'Any' || visited:has(key: className) }, {
			return false;
		});
		visited:set(key: className, value: 'true');
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: :findClass(name: parts:get(index: 0));
		if({ cls:name == '' }, {
			return false;
		});
		local Boolean is found: false;
		cls:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:METHOD && m:name == methodName }, {
				found: true;
			});
		});
		if({ found }, {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !viaParent && :declaresOrInherits(className: baseName, methodName: methodName, visited: visited) }, {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## True when the nearest declaring ancestor of [methodName] above
	## [className] carries an overload group (two or more same-name
	## methods) — such names cannot be replaced or merged. The starting
	## class's own members are excluded.
	##
	## @param className: The class whose ancestors are walked.
	## @param methodName: The member name.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	## @return: true when the inherited name is overloaded.
	Function of Boolean is ancestorOverloaded(String is className, String is methodName, Map of String to String is visited: Map:init()){
		if({ className == '' || className == 'Any' || visited:has(key: className) }, {
			return false;
		});
		visited:set(key: className, value: 'true');
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: :findClass(name: parts:get(index: 0));
		if({ cls:name == '' }, {
			return false;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !viaParent && :nearestGroupOverloaded(className: baseName, methodName: methodName, visited: visited) }, {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## True when the nearest declaration of [methodName] at or above
	## [className] is an overload group.
	##
	## @param className: Class being visited.
	## @param methodName: The member name.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	## @return: true when the nearest declaration is overloaded.
	Function of Boolean is nearestGroupOverloaded(String is className, String is methodName, Map of String to String is visited: Map:init()){
		if({ className == '' || className == 'Any' || visited:has(key: className) }, {
			return false;
		});
		visited:set(key: className, value: 'true');
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: :findClass(name: parts:get(index: 0));
		if({ cls:name == '' }, {
			return false;
		});
		local Int is groupSize: cls:members:count(predicate: local Function of Boolean(Member is m){
			return m:kind == MemberKind:METHOD && m:name == methodName;
		});
		if({ groupSize >= 2 }, {
			return true;
		});
		if({ groupSize == 1 }, {
			return false;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !viaParent && :nearestGroupOverloaded(className: baseName, methodName: methodName, visited: visited) }, {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## §I.1: validates every class's same-name METHOD groups —
	## identical signatures are the duplicate error; overload groups must
	## declare concrete parameter types and must not shadow an inherited
	## name (the virtual machinery is name-keyed; overloads dispatch
	## directly). The per-member body nests instead of returning early: an
	## iteration closure's early `return` compiles to a loop `break`.
	Function is checkOverloadLegality(){
		:programClasses:each(action: local Function(ClassInfo is c){
			local Array of Member is members: c:members;
			while([Int is i: 0], { i < members:length() }, {
				local Member is m: members:get(index: i);
				if({ m:kind == MemberKind:METHOD }, {
					# a same-name METHOD before i: the group's legality checks
					# run once per name, on the first declaration.
					local Boolean is earlier: members:slice(start: 0, end: i):any(predicate: local Function of Boolean(Member is g){
						return g:kind == MemberKind:METHOD && g:name == m:name;
					});
					if({ !earlier }, {
						local Int is groupSize: members:count(predicate: local Function of Boolean(Member is g){
							return g:kind == MemberKind:METHOD && g:name == m:name;
						});
						if({ groupSize >= 2 }, {
							while([Int is a: 0], { a < members:length() }, {
								local Member is ma: members:get(index: a);
								if({ ma:kind == MemberKind:METHOD && ma:name == m:name }, {
									while([Int is b: a + 1], { b < members:length() }, {
										local Member is mb: members:get(index: b);
										if({ mb:kind == MemberKind:METHOD && mb:name == m:name && :checkerSameSignature(a: ma, b: mb) }, {
											:addError(line: m:line, msg: 'Methods \'' . m:name . '\' in class \'' . c:name . '\' declare identical signatures; overloads must differ (§I.1).');
										});
										b++;
									});
								});
								a++;
							});
							local Boolean is nonConcrete: members:any(predicate: local Function of Boolean(Member is g){
								if({ g:kind != MemberKind:METHOD || g:name != m:name }, {
									return false;
								});
								return g:params:any(predicate: local Function of Boolean(Parameter is pp){
									local String is pt: pp:paramType:name;
									return pt == '' || pt == Primitive:ANY:value() || pt == :names:selfFieldMarker() || c:typeParams:indexOf(search: pt, default: -1) >= 0;
								});
							});
							if({ nonConcrete }, {
								:addError(line: m:line, msg: 'Overloaded method \'' . m:name . '\' must declare concrete parameter types (§I.3).');
							});
							if({ m:name != 'init' && m:name != 'SpecErrorHandler' && :ancestorDeclares(className: c:name, methodName: m:name) }, {
								:addError(line: m:line, msg: 'Cannot overload \'' . m:name . '\': the name is declared on an ancestor (§I.3).');
							});
						});
					});
				});
				i++;
			});
		});
	}

	## §I.1: signature equality for the legality pass —
	## parameter count, names, and types all equal; type spellings are
	## canonicalized before comparison.
	##
	## @param a: First member.
	## @param b: Second member.
	## @return: true when signatures are identical.
	Function of Boolean is checkerSameSignature(Member is a, Member is b){
		if({ a:params:length() != b:params:length() }, {
			return false;
		});
		local Boolean is same: true;
		while([Int is idx: 0], { same && idx < a:params:length() }, {
			local Parameter is pa: a:params:get(index: idx);
			local Parameter is pb: b:params:get(index: idx);
			if({ pa:name != pb:name || :formatTypeString(t: pa:paramType) != :formatTypeString(t: pb:paramType) }, {
				same: false;
			});
			idx++;
		});
		return same;
	}

	## §I.6: the import gate. True when [targetName] is
	## usable by [className] in type positions and for construction:
	## the X3 stratum, the class itself, an ancestor, the same source
	## file, or any using entry of the class or its ancestors (type
	## imports, as-imports, and package wildcards all grant).
	##
	## @param className: The enclosing class.
	## @param targetName: The referenced class name.
	## @return: true when access is granted.
	Function of Boolean is classHasAccess(String is className, String is targetName){
		if({ targetName == '' || :isPrimitive(t: targetName) || targetName == 'Array' || targetName == 'Map' || targetName == 'List' || targetName == 'Str' || targetName == 'String' || targetName == 'SpecError' || targetName == 'Function' || targetName == 'LoopControl' }, {
			return true;
		});
		return :accessInClass(className: className, targetName: targetName);
	}

	## True when segment array [fullSegs] equals [prefixSegs] or begins with [prefixSegs] as a package prefix.
	Function of Boolean is namespaceHasPrefix(Array of String is fullSegs, Array of String is prefixSegs){
		if({ prefixSegs:length() == 0 || fullSegs:length() < prefixSegs:length() }, {
			return false;
		});
		local Int is i: 0;
		while({ i < prefixSegs:length() }, {
			if({ fullSegs:get(index: i) != prefixSegs:get(index: i) }, {
				return false;
			});
			i: i + 1;
		});
		return true;
	}

	## True when segment array [segs] exactly equals [want].
	Function of Boolean is namespaceEquals(Array of String is segs, Array of String is want){
		if({ segs:length() != want:length() }, {
			return false;
		});
		return :namespaceHasPrefix(fullSegs: segs, prefixSegs: want);
	}

	## The compilation-unit grant: any class declared in [sourceFile] is
	## accessible, and any same-file class's using entries grant the
	## target (type import, as-import, or package wildcard).
	##
	## @param sourceFile: The visiting class's source file.
	## @param targetName: The referenced class name.
	## @param targetNsSegs: The target's declared namespace segments ([] when unknown).
	## @return: true when the file grants access.
	Function of Boolean is fileGrants(String is sourceFile, String is targetName, Array of String is targetNsSegs){
		# An empty sourceFile is one anonymous unit (the self-checking
		# snippets): its classes grant one another.
		local Boolean is granted: false;
		:programClasses:each(action: local Function(ClassInfo is c){
			if({ !granted && c:sourceFile == sourceFile }, {
				# the flattened nested classes match their qualified
				# identity too — the outer's own rewritten references
				# ('LibA:Helper') grant as the bare declaration does.
				if({ c:name == targetName || c:qualifiedName() == targetName }, {
					granted: true;
					return;
				});
				c:members:each(action: local Function(Member is m){
					if({ !granted && m:name == 'using' && m:hasInit }, {
						match(on: m:initExpr, when: [
							Expression:ArrayLit: local Function(Array of Expression is items){
								items:each(action: local Function(Expression is item){
									if({ !granted }, {
										match(on: item, when: [
											Expression:ArrayLit: local Function(Array of Expression is segs){
												local String is terminal: '';
												local Array of String is terminals: [];
												local Array of String is nsSegs: [];
												segs:each(action: local Function(Expression is seg){
													match(on: seg, when: [
														Expression:Ident: local Function(String is s){
															terminal: s;
														},
														Expression:UsingAs: local Function(String is className, Array of NamedArg is args){
															terminal: className;
														},
														Expression:ArrayLit: local Function(Array of Expression is grpItems){
															grpItems:each(action: local Function(Expression is g){
																match(on: g, when: [
																	Expression:Ident: local Function(String is gs){
																		terminals:add(item: gs);
																	},
																	Expression:UsingAs: local Function(String is gclassName, Array of NamedArg is gargs){
																		terminals:add(item: gclassName);
																	}
																], default: {});
															});
														},
														Expression:StringLit: local Function(String is s){
															if({ s != '*' }, {
																nsSegs:add(item: s);
															});
														}
													], default: {
													});
												});
												# The as-form and plain type import both grant the class
												# itself (type annotations, construction, static/instance
												# calls) as well as qualified nested references ('Outer:Inner').
												local String is targetRoot: targetName:split(delimiter: ':'):get(index: 0);
												if({ terminal == targetName || terminal == targetRoot }, {
													granted: true;
												});
												terminals:each(action: local Function(String is tm){
													if({ tm == targetName || tm == targetRoot }, {
														granted: true;
													});
												});
												if({ terminal == '' && terminals:length() == 0 && targetNsSegs:length() > 0 && :namespaceHasPrefix(fullSegs: targetNsSegs, prefixSegs: nsSegs) }, {
													granted: true;
												});
											}
										], default: {
										});
									});
								});
							}
						], default: {
						});
					});
				});
			});
		});
		return granted;
	}

	## Recursive access walk over the ancestor lattice.
	##
	## @param className: Class being visited.
	## @param targetName: The referenced class name.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	## @return: true when access is granted at this level or above.
	Function of Boolean is accessInClass(String is className, String is targetName, Map of String to String is visited: Map:init()){
		if({ visited:has(key: className) || className == '' }, {
			return false;
		});
		visited:set(key: className, value: 'true');
		if({ className == targetName }, {
			return true;
		});
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: :findClass(name: parts:get(index: 0));
		if({ cls:name == '' }, {
			return false;
		});
		local Array of String is targetNsSegs: [];
		local ClassInfo is tgt: :findClass(name: targetName);
		if({ tgt:name != '' }, {
			targetNsSegs: tgt:namespaceSegments();
		});
		# The file's compilation unit: same-file classes are accessible, and
		# every same-file class's using declaration grants (nested classes
		# live under the outer class's using).
		if({ :fileGrants(sourceFile: cls:sourceFile, targetName: targetName, targetNsSegs: targetNsSegs) }, {
			return true;
		});
		local Boolean is granted: false;
		cls:members:each(action: local Function(Member is m){
			if({ !granted && m:name == 'using' && m:hasInit }, {
				match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function(Array of Expression is items){
						items:each(action: local Function(Expression is item){
							if({ !granted }, {
								match(on: item, when: [
									Expression:ArrayLit: local Function(Array of Expression is segs){
										local String is terminal: '';
										local Array of String is terminals: [];
										local Array of String is nsSegs: [];
										segs:each(action: local Function(Expression is seg){
											match(on: seg, when: [
												Expression:Ident: local Function(String is s){
													terminal: s;
												},
												Expression:UsingAs: local Function(String is className, Array of NamedArg is args){
													terminal: className;
												},
												Expression:ArrayLit: local Function(Array of Expression is grpItems){
													grpItems:each(action: local Function(Expression is g){
														match(on: g, when: [
															Expression:Ident: local Function(String is gs){
																terminals:add(item: gs);
															},
															Expression:UsingAs: local Function(String is gclassName, Array of NamedArg is gargs){
																terminals:add(item: gclassName);
															}
														], default: {});
													});
												},
												Expression:StringLit: local Function(String is s){
													if({ s != '*' }, {
														nsSegs:add(item: s);
													});
												}
											], default: {});
										});
										# The as-form and plain type import both grant the class
										# itself (type annotations, construction, static/instance
										# calls) as well as qualified nested references ('Outer:Inner').
										local String is targetRoot2: targetName:split(delimiter: ':'):get(index: 0);
										if({ terminal == targetName || terminal == targetRoot2 }, {
											granted: true;
										});
										terminals:each(action: local Function(String is tm){
											if({ tm == targetName || tm == targetRoot2 }, {
												granted: true;
											});
										});
										if({ terminal == '' && terminals:length() == 0 && targetNsSegs:length() > 0 && :namespaceHasPrefix(fullSegs: targetNsSegs, prefixSegs: nsSegs) }, {
											granted: true;
										});
									}
								], default: {});
							});
						});
					}
				], default: {});
			});
		});
		if({ granted }, {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !viaParent && :accessInClass(className: baseName, targetName: targetName, visited: visited) }, {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## §I.6: gates a declared type — the base name and every
		## type argument must be accessible from the enclosing class.
	##
	## @param t: The declared type.
	## @param line: The declaration's source line.
	Function is validateTypeAccess(Type is t, Int is line){
		if({ t:name == '' }, {
			return;
		});
		if({ t:name:startsWith(prefix: 'Function:') }, {
			:addError(line: line, msg: "Function type must use 'Function of <Ret>' or 'Function of <Arg> to <Ret>', not colon syntax.");
			return;
		});
		# the bare nested-class
		# reference resolves through the per-scope map — one lookup. Exactly
		# one provider rewrites the type to its qualified identity (the
		# parent grant covers it downstream); several collide and force the
		# qualification — the same rule the bare function calls run.
		if({ !t:name:contains(needle: ':') }, {
			local String is idents: :nestedScopeResolve(className: :currentClassName, typeName: t:name);
			if({ idents != '' }, {
				local Array of String is provs: idents:split(delimiter: ';');
				if({ provs:length() == 1 }, {
					t:name: provs:get(index: 0);
				});
				if({ provs:length() > 1 }, {
					local String is listed: '';
					provs:each(action: local Function(String is p){
						if({ listed == '' }, {
							listed: p;
						}, {
							listed: listed . ' and ' . p;
						});
					});
					:addError(line: line, msg: 'Type \'' . t:name . '\' is provided by ' . listed . '; qualify the reference.');
					return;
				});
			});
		});
		if({ :registeredClasses:has(key: t:name) && !:classHasAccess(className: :currentClassName, targetName: t:name) }, {
			:addError(line: line, msg: '\'' . t:name . '\' is not imported by \'' . :currentClassName . '\'; add it to the using declaration (§I.6).');
		}, {
			if({ t:name != :names:selfFieldMarker() && !:isPrimitive(t: t:name) && !:registeredClasses:has(key: t:name) && !:allEnumNames:has(key: t:name) && :currentClassDef:typeParams:indexOf(search: t:name, default: -1) < 0 && !:currentMethodTypeParams:has(key: t:name) }, {
				:addError(line: line, msg: 'Unknown or unimported type \'' . t:name . '\' in \'' . :currentClassName . '\'.');
			});
		});
		t:params:each(action: local Function(Type is p){
			:validateTypeAccess(t: p, line: line);
		});
	}

	## Types anonymous-function callback parameters for the container
	## higher-order methods whose signatures the string type format cannot
	## express (fold's accumulator+element, Map each's key+value). One table
	## replacing the per-method special cases of the previous compiler.
	##
	## @param targetType: The container's type name.
	## @param method: The container method name.
	## @param expr: The CALL expression.
	Function is bindContainerCallbackParams(String is targetType, String is method, Expression is expr){
		local Type is targetNode: :parseTypeNode(s: targetType);
		local Type is cbElemNode: Type:init(name: Primitive:ANY:value());
		if({ (targetNode:name == 'Array' || targetNode:name == 'List') && targetNode:params:length() > 0 }, {
			cbElemNode: targetNode:params:get(index: 0);
		});
		local CallData is cd: match(on: expr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: { CallData:init(target: Expression:Unknown, name: '', args: []) }
		]);
		if({ cbElemNode:name != Primitive:ANY:value() && cbElemNode:name != '' }, {
			if({ method == 'fold' && cd:args:length() >= 2 }, {
				local NamedArg is a0: cd:args:get(index: 0);
				local String is initType: :inferExpressionType(expr: a0:value);
				local NamedArg is a1: cd:args:get(index: 1);
				local Expression is av: a1:value;
				match(on: av, when: [
					Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
						if({ params:length() >= 1 }, {
							local Parameter is p0: params:get(index: 0);
							if({ p0:paramType:name == Primitive:ANY:value() || p0:paramType:name == '' }, {
								p0:paramType: :parseTypeNode(s: initType);
							});
						});
						if({ params:length() >= 2 }, {
							local Parameter is p1: params:get(index: 1);
							if({ p1:paramType:name == Primitive:ANY:value() || p1:paramType:name == '' }, {
								p1:paramType: cbElemNode:clone();
							});
						});
					},
					else: {}
				]);
			}, {
				cd:args:each(action: local Function(NamedArg is arg){
					local Expression is av: arg:value;
					match(on: av, when: [
						Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
							params:each(action: local Function(Parameter is p){
								if({ p:paramType:name == Primitive:ANY:value() || p:paramType:name == '' }, {
									p:paramType: cbElemNode:clone();
								});
							});
						},
						else: {}
					]);
				});
			});
		}, {
			if({ targetNode:name == 'Map' && method == 'each' }, {
				local Type is keyNode: if({ targetNode:params:length() >= 1 }, { targetNode:params:get(index: 0) }, { Type:init(name: 'String') });
				local Type is valNode: if({ targetNode:params:length() >= 2 }, { targetNode:params:get(index: 1) }, { Type:init(name: Primitive:STRING:value()) });
				cd:args:each(action: local Function(NamedArg is arg){
					local Expression is av: arg:value;
					match(on: av, when: [
						Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
							if({ params:length() >= 1 }, {
								local Parameter is p0: params:get(index: 0);
								if({ p0:paramType:name == Primitive:ANY:value() || p0:paramType:name == '' }, {
									p0:paramType: keyNode:clone();
								});
							});
							if({ params:length() >= 2 }, {
								local Parameter is p1: params:get(index: 1);
								if({ p1:paramType:name == Primitive:ANY:value() || p1:paramType:name == '' }, {
									p1:paramType: valNode:clone();
								});
							});
						},
						else: {}
					]);
				});
			});
		});
	}

	## Infers and resolves the resulting type of an expression node,
	## annotating `expr:resolvedType`.
	##
	## Bidirectional core: [expected] carries the contextual type from the
	## declaration/assignment/return site; array and map literals adopt it
	## True when [cls]'s declarations are environment bindings rather than
	## authoritative contracts: sysinternal C-floor bindings (structural,
	## permanent — the namespace is the annotation) and, for the runtime-managed
	## runtime-managed classes whose C implementations carry optional or
	## packages, whose C implementations carry optional or variadic semantics. Call
	## sites against these classes skip argument validation.
	##
	## @param cls: The receiving class.
	## @return: true when calls against it skip argument validation.
	Function of Boolean is isBindingDeclaration(ClassInfo is cls){
		local ClassBindings is b: :bindings;
		return b:isTransparent(c: cls);
	}

	## directly, replacing the previous compiler's mutable container hint.
	local Function of String is inferIdentExpr(String is name){
		if({ name == :names:selfIdent() }, {
			# A held member body has no instance
			# — except a function-variable call target: the closure
			# invocation never touches the instance.
			if({ (:inHeldInit || :inHeldFunction) && !:inHeldFnVarTarget }, {
				:addError(line: :currentLine, msg: 'A held member body has no instance: \':\' is not available.');
			});
			return :currentClassName;
		});
		if({ :localVars:has(key: name) }, {
			return :localVars:getString(key: name, default: Primitive:ANY:value());
		});
		if({ :fieldTypes:has(key: name) }, {
			# A held initializer has no instance: instance fields
			# are not reachable from it.
			if({ :inHeldInit }, {
				:addError(line: :currentLine, msg: 'A held initializer has no instance: field \'' . name . '\' is not reachable from it.');
			});
			if({ :unassignedFields:has(key: name) }, {
				:addError(line: :currentLine, msg: 'Field \'' . name . '\' in class \'' . :currentClassName . '\' is read before being initialized.');
			});
			local String is owner: :findMemberOwnerClass(className: :currentClassName, memberName: name);
			if({ owner != '' }, {
				:checkMemberVisibility(ownerClass: owner, member: :findAncestorMember(className: :currentClassName, memberName: name), memberName: name);
			});
			return :fieldTypes:getString(key: name, default: Primitive:ANY:value());
		});
		if({ :allEnumVariants:has(key: name) }, {
			return :allEnumVariants:getString(key: name, default: Primitive:ANY:value());
		});
		if({ :registeredClasses:has(key: name) }, {
			return name;
		});
		if({ :isPrimitive(t: name) }, {
			return name;
		});
		if({ name != '' }, {
			:addError(line: :currentLine, msg: 'Undefined identifier \'' . name . '\'.');
		});
		return 'Any';
	}

	local Function of String is inferPathExpr(Array of String is segs){
		local String is res: 'Any';
		if({ segs:length() == 0 }, {
			return res;
		});
		local String is root: segs:get(index: 0);
		local String is rootType: '';
		# Held admission: the first segment after a class-name root resolved as a held field —
		# the path resolution loop below then consumes it via lookupHeldFieldType.
		local Boolean is heldAdmitted: false;
		local Boolean is chainResolved: false;
		if({ root == :names:selfIdent() }, {
			if({ :inHeldInit || :inHeldFunction }, {
				:addError(line: :currentLine, msg: 'A held member body has no instance: \':\' is not available.');
			});
			rootType: :currentClassName;
			if({ segs:length() >= 2 && :unassignedFields:has(key: segs:get(index: 1)) }, {
				:addError(line: :currentLine, msg: 'Field \'' . segs:get(index: 1) . '\' in class \'' . :currentClassName . '\' is read before being initialized.');
			});
			if({ segs:length() >= 2 }, {
				local String is fName: segs:get(index: 1);
				if({ :lookupFieldType(className: :currentClassName, fieldName: fName) != '' }, {
					local String is fOwner: :findMemberOwnerClass(className: :currentClassName, memberName: fName);
					if({ fOwner != '' }, {
						:checkMemberVisibility(ownerClass: fOwner, member: :findAncestorMember(className: :currentClassName, memberName: fName), memberName: fName);
					});
				}, {
					if({ :findHeldMember(className: :currentClassName, memberName: fName):name != '' }, {
						:addError(line: :currentLine, msg: 'Held member \'' . :currentClassName . ':' . fName . '\' is class-scoped: reach it through the class name, not an instance.');
					});
				});
			});
		}, {
			if({ :localVars:has(key: root) }, {
				rootType: :localVars:getString(key: root, default: '');
			}, {
				if({ :fieldTypes:has(key: root) }, {
					if({ :unassignedFields:has(key: root) }, {
						:addError(line: :currentLine, msg: 'Field \'' . root . '\' in class \'' . :currentClassName . '\' is read before being initialized.');
					});
					rootType: :fieldTypes:getString(key: root, default: '');
				}, {
					if({ :allEnumNames:has(key: root) }, {
						rootType: root;
					}, {
						if({ :registeredClasses:has(key: root) }, {
							rootType: root;
							if({ segs:length() >= 2 }, {
								local ClassInfo is chainCls: :findClass(name: root);
								local Boolean is chainOk: chainCls:name != '';
								local Int is chainIdx: 1;
								while({ chainOk && chainIdx < segs:length() }, {
									local String is nextType: '';
									chainCls:members:each(action: local Function(Member is m){
										if({ m:kind == MemberKind:CLASS && m:nestedClass:name == segs:get(index: chainIdx) }, {
											nextType: chainCls:qualifiedName() . ':' . segs:get(index: chainIdx);
										});
									});
									if({ nextType != '' }, {
										chainCls: :findClass(name: nextType);
										if({ chainCls:name == '' }, {
											chainOk: false;
										});
										chainIdx: chainIdx + 1;
									}, {
										chainOk: false;
									});
								});
								if({ chainOk && chainIdx == segs:length() }, {
									rootType: chainCls:qualifiedName();
									chainResolved: true;
								});
							});
							local Member is heldM: Member:init(kind: MemberKind:FIELD);
							if({ segs:length() >= 2 && !chainResolved }, {
								heldM: :findHeldMember(className: root, memberName: segs:get(index: 1));
							});
							if({ heldM:name != '' && heldM:kind == MemberKind:FIELD }, {
								local String is heldOwner: :findHeldOwnerClass(className: root, memberName: heldM:name);
								if({ :inHeldInit && heldOwner == :currentClassName }, {
									:addError(line: :currentLine, msg: 'Held initializer of \'' . :currentClassName . '\' cannot reference held member \'' . root . ':' . heldM:name . '\' of the same class; the once-guards would deadlock.');
								});
								:checkMemberVisibility(ownerClass: heldOwner, member: heldM, memberName: heldM:name);
								heldAdmitted: true;
							}, {
								if({ segs:length() >= 2 && :findHeldMethod(className: root, methodName: segs:get(index: 1)):name != '' }, {
									:addError(line: :currentLine, msg: 'Held function \'' . root . ':' . segs:get(index: 1) . '\' must be called; bare references to held functions are not supported (the call form is ' . root . ':' . segs:get(index: 1) . '(...)).');
									rootType: '';
								}, {
									if({ segs:length() >= 2 }, {
										local Member is resolver: :findHeldMethod(className: root, methodName: ContractMethod:RESOLVE_HELD:value());
										local Boolean is declaredInstance: :lookupFieldType(className: root, fieldName: segs:get(index: 1)) != '' || :lookupAnyMember(className: root, methodName: segs:get(index: 1)):kind == MemberKind:METHOD;
										if({ !chainResolved && !:allEnumNames:has(key: root) && !:isPrimitive(t: root) && root != 'Array' && root != 'Map' && root != 'List' && root != 'Str' && root != 'String' && root != 'SpecError' && root != 'Function' && root != 'LoopControl' && (resolver:name == '' || declaredInstance) }, {
											:addError(line: :currentLine, msg: 'Fields are not reachable through the class-name prefix \'' . root . '\'; only held members are (§2.3).');
											rootType: '';
										}, {
											if({ resolver:name != '' && !declaredInstance }, {
												if({ :inHeldFunction && :currentMethodName == ContractMethod:RESOLVE_HELD:value() && root == :currentClassName }, {
													:addError(line: :currentLine, msg: 'The resolution hook cannot resolve through its own class prefix (\'' . root . ':' . segs:get(index: 1) . '\'); declare the member, or return it from the resolver directly.');
												});
												:checkMemberVisibility(ownerClass: :findHeldMethodOwner(className: root, methodName: ContractMethod:RESOLVE_HELD:value()), member: resolver, memberName: ContractMethod:RESOLVE_HELD:value());
												res: :formatTypeString(t: resolver:memberType);
												heldAdmitted: true;
											});
										});
									});
								});
							});
						});
					});
				});
			});
		});
		local String is currType: rootType;
		local Int is pIdx: 1;
		while({ !chainResolved && currType != '' && pIdx < segs:length() }, {
			local String is seg: segs:get(index: pIdx);
			pIdx: pIdx + 1;
			if({ !:allEnumNames:has(key: currType) }, {
				if({ heldAdmitted && pIdx == 2 }, {
					currType: :lookupHeldFieldType(className: currType, fieldName: seg);
				}, {
					currType: :lookupFieldType(className: currType, fieldName: seg);
				});
			});
		});
		if({ currType != '' }, {
			res: currType;
		}, {
			if({ segs:length() >= 2 && !heldAdmitted && rootType != '' && rootType != Primitive:ANY:value() }, {
				local String is rBase: rootType:split(delimiter: ':'):get(index: 0);
				if({ :registeredClasses:has(key: rBase) && :findHeldMember(className: rBase, memberName: segs:get(index: 1)):name != '' }, {
					:addError(line: :currentLine, msg: 'Held member \'' . rBase . ':' . segs:get(index: 1) . '\' is class-scoped: reach it through the class name, not an instance.');
				});
			});
		});
		return res;
	}

	local Function of String is inferBinaryExpr(String is op, Expression is left, Expression is right, String is expected){
		local String is leftT: :inferExpressionType(expr: left, expected: expected);
		local String is rightT: :inferExpressionType(expr: right, expected: expected);
		local String is res: Primitive:INT:value();
		match(on: op, when: [
			'.': {
				res: Primitive:STRING:value();
			},
			['==', '!=', 'is', '<', '<=', '>', '>=']: {
				res: Primitive:BOOLEAN:value();
				local Boolean is isRel: op == '<' || op == '<=' || op == '>' || op == '>=';
				local Boolean is leftStr: leftT == 'String' || leftT == 'Str';
				local Boolean is rightStr: rightT == 'String' || rightT == 'Str';
				if({ isRel && (leftStr || rightStr) && !(leftStr && rightStr) }, {
					:addError(line: :currentLine, msg: 'Relational operator \'' . op . '\' requires two String operands (got \'' . leftT . '\' and \'' . rightT . '\').');
				});
			},
			['&&', '||']: {
				res: Primitive:BOOLEAN:value();
			},
			['+', '-', '*', '/', '%']: {
				if({ leftT == 'Float' || rightT == 'Float' }, {
					res: 'Float';
				}, {
					if({ :isUnsignedInt(t: leftT) }, {
						res: leftT;
					}, {
						if({ :isUnsignedInt(t: rightT) }, {
							res: rightT;
						}, {
							res: Primitive:INT:value();
						});
					});
				});
			},
			['&', '|', '^', '<<', '>>']: {
				res: if({ :isUnsignedInt(t: leftT) }, { leftT }, { if({ :isUnsignedInt(t: rightT) }, { rightT }, { Primitive:INT:value() }) });
				if({ (leftT != '' && leftT != 'Any' && !:isIntLike(t: leftT)) ||
					(rightT != '' && rightT != 'Any' && !:isIntLike(t: rightT)) }, {
					local String is msg: :errText:errBitwiseOperandsInt(op: op, leftT: leftT, rightT: rightT);
					:addError(line: :currentLine, msg: msg);
				});
			},
			else: {
				res: Primitive:INT:value();
			}
		]);
		return res;
	}

	local Function of String is inferCastExpr(Expression is inner, String is target, Array of Expression is args){
		local String is innerT: :inferExpressionType(expr: inner);
		local String is src: if({ innerT != '' }, { innerT }, { Primitive:ANY:value() });
		local Boolean is isFormat: target == 'Hex' || target == 'Bin' || target == 'Oct';
		if({ args:length() > 0 && !isFormat }, {
			:addError(line: :currentLine, msg: 'Cast \'as ' . target . '\' takes no arguments.');
		});
		if({ isFormat }, {
			if({ args:length() > 1 }, {
				:addError(line: :currentLine, msg: 'Cast \'as ' . target . '\' accepts at most one width argument.');
			});
			if({ src != 'Any' && src != 'String' && src != 'Str' && src != Primitive:INT:value() }, {
				:addError(line: :currentLine, msg: 'Cast \'as ' . target . '\' requires an Int or String operand (got \'' . src . '\').');
			});
			return if({ src == 'String' || src == 'Str' }, { Primitive:INT:value() }, { 'String' });
		});
		if({ :allEnumNames:has(key: target) }, {
			:addError(line: :currentLine, msg: 'Cannot cast to enum \'' . target . '\'; construct a variant instead.');
			return target;
		});
		if({ :castableMethod(srcType: src, target: target) != '' }, {
			return target;
		});
		if({ :isPrimitive(t: target) && target != Primitive:ANY:value() }, {
			if({ !:isCastable(src: src, target: target) }, {
				:addError(line: :currentLine, msg: 'Cannot cast \'' . src . '\' to \'' . target . '\'.');
			});
			return target;
		});
		if({ :registeredClasses:has(key: target) || :registeredClasses:has(key: target:split(delimiter: ':'):get(index: 0)) }, {
			local Boolean is related: src == Primitive:ANY:value() || :isSubclassOf(subName: src, baseName: target) || :isSubclassOf(subName: target, baseName: src);
			if({ !related }, {
				:addError(line: :currentLine, msg: 'Cannot cast \'' . src . '\' to unrelated class \'' . target . '\'.');
			});
			return target;
		});
		:addError(line: :currentLine, msg: 'Unknown cast target \'' . target . '\'.');
		return 'Any';
	}

	local Function of String is inferUnaryExpr(String is op, Expression is operand){
		local String is innerT: :inferExpressionType(expr: operand);
		if({ op == '~' && innerT != '' && innerT != 'Any' && !:isIntLike(t: innerT) }, {
			local String is msg: :errText:errBitwiseComplementInt(innerT: innerT);
			:addError(line: :currentLine, msg: msg);
		});
		if({ op == '++' || op == '--' || op == 'post++' || op == 'post--' }, {
			if({ innerT != '' && innerT != 'Any' && !:isIntLike(t: innerT) }, {
				local String is msg: :errText:errOperatorRequiresInt(op: op, innerT: innerT);
				:addError(line: :currentLine, msg: msg);
			});
			if({ :inLazyBlock && !:isLazyLocalTarget(expr: operand) }, {
				:addError(line: :currentLine, msg: "Cannot modify external state inside a 'lazy' initializer; 'lazy' blocks have read-only access to outer variables and fields.");
			});
		});
		if({ op == '!' }, {
			return Primitive:BOOLEAN:value();
		});
		return innerT;
	}

	local Function of String is inferArrayLitExpr(Array of Expression is items, String is expected){
		local Boolean is hasExpectedContainer: TypeDomain:isOfBase(t: expected, base: 'Array') || TypeDomain:isOfBase(t: expected, base: 'List');
		local String is elemT: if({ hasExpectedContainer }, { TypeDomain:elemType(t: expected) }, { '' });
		local Array of String is itemTypes: [];
		items:each(action: local Function(Expression is item){
			local String is itemT: :inferExpressionType(expr: item, expected: elemT);
			if({ :isVoid(t: itemT) }, {
				:addError(line: :currentLine, msg: 'Array elements cannot be void.');
			}, {
				if({ itemT != '' && itemT != Primitive:ANY:value() }, {
					itemTypes:add(item: itemT);
				});
			});
		});
		local String is unifiedElemType: :unifyArrayElementTypes(elemTypes: itemTypes);
		if({ hasExpectedContainer }, {
			if({ elemT != '' && elemT != Primitive:ANY:value() }, {
				itemTypes:each(action: local Function(String is itemT){
					local Boolean is elemOk: :isAssignable(target: elemT, source: itemT);
					if({ :isPrimitive(t: elemT) && !TypeDomain:isFunction(t: elemT) && itemT != elemT }, {
						elemOk: false;
					});
					if({ !elemOk }, {
						:addError(line: :currentLine, msg: "Cannot assign 'Array:" . itemT . "' to 'Array:" . elemT . "'.");
					});
				});
			});
			if({ elemT == '' && expected == 'Array' && unifiedElemType != '' }, {
				return TypeDomain:makeArray(elem: unifiedElemType);
			});
			return expected;
		});
		return TypeDomain:makeArray(elem: unifiedElemType);
	}

	local Function of String is inferMapLitExpr(Array of Expression is keys, Array of Expression is values, String is expected){
		if({ TypeDomain:isOfBase(t: expected, base: 'Map') }, {
			local String is keyT: TypeDomain:mapKeyType(t: expected);
			local String is valT: TypeDomain:mapValType(t: expected);
			keys:each(action: local Function(Expression is k){
				local String is kT: :inferExpressionType(expr: k);
				if({ keyT != '' && kT != '' && kT != Primitive:ANY:value() && !:isAssignable(target: keyT, source: kT) }, {
					local String is kDisplay: if({ keyT != '' }, { keyT }, { 'String' });
					:addError(line: :currentLine, msg: "Cannot assign '" . kT . "' key to 'Map:" . kDisplay . ":" . valT . "'.");
				});
			});
			values:each(action: local Function(Expression is v){
				local String is vT: :inferExpressionType(expr: v);
				if({ valT != '' && vT != '' && vT != Primitive:ANY:value() && !:isAssignable(target: valT, source: vT) }, {
					local String is kDisplay: if({ keyT != '' }, { keyT }, { 'String' });
					:addError(line: :currentLine, msg: "Cannot assign 'Map:" . kDisplay . ":" . vT . "' to 'Map:" . kDisplay . ":" . valT . "'.");
				});
			});
			return expected;
		});
		local String is firstKeyType: '';
		local String is firstValType: '';
		keys:each(action: local Function(Expression is k){
			local String is kt: :inferExpressionType(expr: k);
			if({ firstKeyType == '' && kt != '' && kt != Primitive:ANY:value() }, {
				firstKeyType: kt;
			});
		});
		values:each(action: local Function(Expression is v){
			local String is vt: :inferExpressionType(expr: v);
			if({ firstValType == '' && vt != '' && vt != Primitive:ANY:value() }, {
				firstValType: vt;
			});
		});
		return TypeDomain:makeMap(key: firstKeyType, val: firstValType);
	}

	local Function of String is inferFieldAccessExpr(Expression is target, String is fName){
		local String is leftT: :inferExpressionType(expr: target);
		if({ leftT == '' || leftT == 'Any' || :isPrimitive(t: leftT) }, {
			return 'Any';
		});
		local String is faBase: TypeDomain:baseName(t: leftT);
		local String is fOwner: :findMemberOwnerClass(className: faBase, memberName: fName);
		if({ fOwner != '' }, {
			:checkMemberVisibility(ownerClass: fOwner, member: :findAncestorMember(className: faBase, memberName: fName), memberName: fName);
		});
		local String is fT: :lookupFieldType(className: leftT, fieldName: fName);
		if({ fT == '' && :registeredClasses:has(key: faBase) && :findHeldMember(className: faBase, memberName: fName):name != '' }, {
			:addError(line: :currentLine, msg: 'Held member \'' . faBase . ':' . fName . '\' is class-scoped: reach it through the class name, not an instance.');
		});
		return if({ fT != '' }, { fT }, { 'Any' });
	}

	local Function of String is inferIndexExpr(Expression is target, Expression is index){
		local String is leftT: :inferExpressionType(expr: target);
		:inferExpressionType(expr: index);
		if({ TypeDomain:isParameterized(t: leftT, base: 'Array') }, {
			return TypeDomain:elemType(t: leftT);
		});
		if({ TypeDomain:isOfBase(t: leftT, base: 'Map') }, {
			local String is mv: TypeDomain:mapValType(t: leftT);
			return if({ mv != '' }, { mv }, { Primitive:STRING:value() });
		});
		return 'Any';
	}

	local Function of String is inferAnonFnExpr(Expression is expr, Type is returnType, Array of Parameter is params, Array of Statement is body, String is expected){
		local Map of String to String is savedVars: Map:init();
		local Array of String is existingKeys: :localVars:keys();
		existingKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: :localVars:getString(key: k, default: ''));
		});
		local Map of String to String is savedLazyVars: Map:init();
		if({ :inLazyBlock }, {
			local Array of String is lazyKeys: :lazyLocalVars:keys();
			lazyKeys:each(action: local Function(String is k){
				savedLazyVars:set(key: k, value: :lazyLocalVars:getString(key: k, default: ''));
			});
		});
		local String is savedRet: :currentMethodReturnType;
		local Expression is savedAnonNode: :currentAnonNode;
		:currentAnonNode: expr;
		local Boolean is savedYieldFlag: :checkingValueYield;
		:checkingValueYield: false;

		if({ !:inBranchClosure }, {
			if({ TypeDomain:hasFunctionReturn(t: expected) && :isVoid(t: :resolveReturnType(t: returnType)) }, {
				returnType:name: TypeDomain:functionReturn(t: expected);
				returnType:params: [];
			});
			:currentMethodReturnType: :resolveReturnType(t: returnType);
		});
		params:each(action: local Function(Parameter is p){
			local String is pFmt: :formatVarTypeString(t: p:paramType);
			:localVars:set(key: p:name, value: pFmt);
			if({ :inLazyBlock }, {
				:lazyLocalVars:set(key: p:name, value: pFmt);
			});
		});
		local Int is bodyLen: body:length();
		local Int is bodyIdx: 0;
		body:each(action: local Function(Statement is s){
			:anonDepth: :anonDepth + 1;
			if({ :inValueBranch && bodyIdx == bodyLen - 1 }, {
				:checkingValueYield: true;
			});
			:checkStatement(stmt: s);
			:checkingValueYield: false;
			:anonDepth: :anonDepth - 1;
			bodyIdx: bodyIdx + 1;
		});

		:localVars: savedVars;
		if({ :inLazyBlock }, {
			:lazyLocalVars: savedLazyVars;
		});
		:currentMethodReturnType: savedRet;
		local Int is lastIdx: body:length() - 1;
		if({ lastIdx >= 0 }, {
			local Statement is lastStmt: body:get(index: lastIdx);
			match(on: lastStmt, when: [
				Statement:Expr: local Function(Expression is exprStmt){
					local String is lastT: exprStmt:resolvedType;
					local String is curRetT: :resolveReturnType(t: returnType);
					if({ :isVoid(t: curRetT) }, {
						if({ lastT != '' && !:isVoid(t: lastT) }, {
							returnType:name: lastT;
							returnType:params: [];
						});
					}, {
						if({ lastT != '' && !:isAssignable(target: curRetT, source: lastT) }, {
							local String is msg: :errText:errClosureReturnType(actual: lastT, expected: curRetT);
							:addError(line: :currentLine, msg: msg);
						});
					});
				},
				else: {}
			]);
		});
		:currentAnonNode: savedAnonNode;
		:checkingValueYield: savedYieldFlag;
		local String is anonRetStr: :resolveReturnType(t: returnType);
		if({ anonRetStr != '' && !:isVoid(t: anonRetStr) }, {
			return 'Function:' . anonRetStr;
		});
		return 'Function';
	}

	##
	## @param expr: AST expression node.
	## @param expected: Contextual type ('' when none).
	## @return: Resolved type name string.
	Function of String is inferExpressionType(Expression is expr, String is expected: ''){
		local String is res: 'Any';

		local Boolean is isUsingAs: false;
		match(on: expr, when: [
			Expression:UsingAs: local Function(String is className, Array of NamedArg is args){
				:addError(line: :currentLine, msg: 'Instance imports (as ClassName()) may only appear as entries of a using declaration (E1).');
				expr:setResolvedType(t: '');
				isUsingAs: true;
			}
		], default: {});
		if({ isUsingAs }, {
			return '';
		});

		match(on: expr, when: [
			Expression:StringLit: local Function(String is value){
				res: Primitive:STRING:value();
			},
			Expression:NumberLit: local Function(Int is value, String is text){
				res: Primitive:INT:value();
			},
			Expression:FloatLit: local Function(String is text){
				res: Primitive:FLOAT:value();
			},
			Expression:BoolLit: local Function(Boolean is value){
				res: Primitive:BOOLEAN:value();
			},
			Expression:Ident: local Function(String is name){
				res: :inferIdentExpr(name: name);
			},
			Expression:Path: local Function(Array of String is segs){
				res: :inferPathExpr(segs: segs);
			},
			Expression:Binary: local Function(String is op, Expression is left, Expression is right){
				res: :inferBinaryExpr(op: op, left: left, right: right, expected: expected);
			},
			Expression:Cast: local Function(Expression is inner, String is target, Array of Expression is args){
				res: :inferCastExpr(inner: inner, target: target, args: args);
			},
			Expression:Unary: local Function(String is op, Expression is operand){
				res: :inferUnaryExpr(op: op, operand: operand);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				res: :inferArrayLitExpr(items: items, expected: expected);
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				res: :inferMapLitExpr(keys: keys, values: values, expected: expected);
			},
			Expression:FieldAccess: local Function(Expression is target, String is fName){
				res: :inferFieldAccessExpr(target: target, fName: fName);
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				res: :inferIndexExpr(target: target, index: index);
			},
			Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
				res: :inferAnonFnExpr(expr: expr, returnType: returnType, params: params, body: body, expected: expected);
			},
			Expression:Call: local Function(CallData is call){
					res: :inferCall(expr: expr, call: call, expected: expected);
				expr:setResolvedTypeNode(tn: :parseTypeNode(s: res), t: res);
				:checkCallArguments(callExpr: expr);
			},
			else: {
				res: 'Any';
			}
		], default: {});

		expr:setResolvedTypeNode(tn: :parseTypeNode(s: res), t: res);
		return res;
	}

	local Function is validateCallReceiverModel(String is recvName, CallData is call, Boolean is targetIsPath, Array of String is targetPathSegs){
		if({ recvName != '' && call:name != 'init' }, {
			local Boolean is isSysinternalPath: targetIsPath && targetPathSegs:indexOf(search: 'sysinternal', default: -1) >= 0;
			local Boolean is isTypeLevel: isSysinternalPath || :allEnumNames:has(key: recvName) || :isPrimitive(t: recvName) || recvName == 'Array' || recvName == 'Map' || recvName == 'List' || recvName == 'Str' || recvName == 'String' || recvName == 'Function' || recvName == 'LoopControl' || :bindings:isClassModelEnum(c: :findClass(name: recvName));
			if({ :findHeldMethod(className: recvName, methodName: call:name):name != '' }, {
				isTypeLevel: true;
			});
			if({ !isTypeLevel }, {
				if({ !:isAsImportedInherited(className: recvName) }, {
					if({ recvName == :currentClassName }, {
						:addError(line: :currentLine, msg: 'Cannot call members of \'' . recvName . '\' through the class name inside \'' . recvName . '\' itself; use : (§2.2).');
					}, {
						:addError(line: :currentLine, msg: 'Members of \'' . recvName . '\' are callable only through an instance; instance-import it (\'as ' . recvName . '()\') (§I.6).');
					});
				});
			});
		});
		if({ recvName == '' && call:name == 'init' }, {
			:addError(line: :currentLine, msg: '\'init\' is construct-only; call it on the class name (E7).');
		});
	}

	local Function of String is inferMatchCall(Expression is expr, CallData is call, String is expected, Boolean is targetIsSelf){
		if({ targetIsSelf }, {
			call:bareProvider: 'Conditional';
		});
		local Expression is matchSubj: Expression:Unknown;
		local Expression is matchArms: Expression:Unknown;
		local Expression is matchDefault: Expression:Unknown;
		local Boolean is hasMatchSubj: false;
		local Boolean is hasMatchArms: false;
		local Boolean is hasMatchDefault: false;
		local Boolean is matchArmsIsMap: false;
		call:args:each(action: local Function(NamedArg is arg){
			if({ arg:name == 'on' }, {
				matchSubj: arg:value;
				hasMatchSubj: true;
			});
			if({ arg:name == 'when' }, {
				matchArms: arg:value;
				hasMatchArms: true;
			});
			if({ arg:name == 'default' }, {
				matchDefault: arg:value;
				hasMatchDefault: true;
			});
		});
		if({ hasMatchArms }, {
			match(on: matchArms, when: [
				Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
					matchArmsIsMap: true;
				}
			], default: {});
		});
		if({ matchArmsIsMap }, {
			local Boolean is defaultActive: hasMatchDefault && :isNonEmptyMatchDefault(expr: matchDefault);
			if({ hasMatchSubj }, {
				local String is matchRes: :checkMatchArms(subj: matchSubj, arms: matchArms, expected: expected, defaultArm: matchDefault, hasDefault: defaultActive, hasExplicitDefault: hasMatchDefault);
				expr:setResolvedType(t: matchRes);
				return matchRes;
			});
			local String is predRes: :checkPredicateArms(arms: matchArms, expected: expected, defaultArm: matchDefault, hasDefault: defaultActive);
			expr:setResolvedType(t: predRes);
			return predRes;
		});
		if({ !hasMatchSubj && hasMatchArms }, {
			:addError(line: :currentLine, msg: 'A predicate match table is compile-time: the keys are closures and the scan order matters — write the arm table as a literal.');
			expr:setResolvedType(t: Primitive:ANY:value());
			return Primitive:ANY:value();
		});
		return '';
	}

	local Function of String is unifyValueBranchTypes(Expression is expr){
		local String is thenT: '';
		local String is elseT: '';
		match(on: expr:argValue(index: 1), when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				thenT: :resolveReturnType(t: rt);
			}
		], default: {});
		match(on: expr:argValue(index: 2), when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				elseT: :resolveReturnType(t: rt);
			}
		], default: {});
		if({ :isVoid(t: thenT) || :isVoid(t: elseT) }, {
			:addError(line: :currentLine, msg: :errText:errBranchRequiresExpressions());
			return :names:voidName();
		});
		if({ !:isAssignable(target: thenT, source: elseT) && !:isAssignable(target: elseT, source: thenT) }, {
			:addError(line: :currentLine, msg: :errText:errBranchMismatchedTypes(thenType: thenT, elseType: elseT));
			return thenT;
		});
		return if({ thenT == Primitive:ANY:value() }, { elseT }, { thenT });
	}

	local Function of String is inferBareScopeCall(Expression is expr, CallData is call, String is expected, String is provider){
		if({ (provider == 'Conditional' || provider:endsWith(suffix: ':Conditional')) && call:name == 'try' && expr:argCount() == 2 }, {
			return :inferTryCall(expr: expr, call: call, expected: expected);
		});
		local Boolean is bareIsBranch: provider == 'Conditional' && expr:argCount() >= 2 && expr:argCount() <= 4;
		local Boolean is bareIsLazy: provider == 'Lazy' && call:name == 'lazy';
		local Boolean is bareArg1Anon: false;
		local Boolean is bareArg2Anon: false;
		if({ bareIsBranch && expr:argCount() == 3 }, {
			match(on: expr:argValue(index: 1), when: [
				Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
					bareArg1Anon: true;
				}
			], default: {});
			match(on: expr:argValue(index: 2), when: [
				Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
					bareArg2Anon: true;
				}
			], default: {});
		});
		local Boolean is bareIsValue: bareIsBranch && expr:argCount() == 3 && expected != '' && !:isVoid(t: expected) && bareArg1Anon && bareArg2Anon;
		local Map of String to String is savedLoopVars;
		local Map of String to String is savedLoopLazyVars;
		if({ provider == 'Loops' }, {
			savedLoopVars: Map:init();
			local Array of String is lvKeys: :localVars:keys();
			lvKeys:each(action: local Function(String is k){
				savedLoopVars:set(key: k, value: :localVars:getString(key: k, default: ''));
			});
			if({ :inLazyBlock }, {
				savedLoopLazyVars: Map:init();
				local Array of String is llvKeys: :lazyLocalVars:keys();
				llvKeys:each(action: local Function(String is k){
					savedLoopLazyVars:set(key: k, value: :lazyLocalVars:getString(key: k, default: ''));
				});
			});
			local Boolean is bareHasLoopVars: false;
			call:args:each(action: local Function(NamedArg is arg){
				match(on: arg:value, when: [
					Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
						if({ ps:length() > 0 && bd:length() == 0 }, {
							bareHasLoopVars: true;
							ps:each(action: local Function(Parameter is p){
								if({ p:hasDefault }, {
									:inferExpressionType(expr: p:defaultExpr);
								});
								local String is pFmt: :formatVarTypeString(t: p:paramType);
								:localVars:set(key: p:name, value: pFmt);
								if({ :inLazyBlock }, {
									:lazyLocalVars:set(key: p:name, value: pFmt);
								});
							});
						});
					}
				], default: {});
			});
			local Int is barePos: 0;
			call:args:each(action: local Function(NamedArg is arg){
				local Boolean is bareClosureSlot: arg:name == 'evaluate' || arg:name == 'iterate' || arg:name == 'iteration' || (arg:name == '' && barePos > 0);
				if({ bareHasLoopVars && bareClosureSlot }, {
					local Boolean is valIsAnon: false;
					match(on: arg:value, when: [
						Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
							valIsAnon: true;
						}
					], default: {});
					if({ !valIsAnon }, {
						:addError(line: :currentLine, msg: :errText:errLoopVarsClosureLiteral());
					});
				});
				barePos: barePos + 1;
			});
		});
		local Int is bareIdx: 0;
		local String is bareLazyRet: 'Any';
		if({ bareIsLazy }, {
			bareLazyRet: :inferLazyCall(call: call, expected: expected);
		}, {
			if({ provider == 'Loops' }, {
				local Boolean is savedLoopBranch: :inBranchClosure;
				:inBranchClosure: false;
				call:args:each(action: local Function(NamedArg is arg){
					if({ arg:name == 'evaluate' }, {
						match(on: arg:value, when: [
							Expression:AnonFn: local Function(Type is returnType, Array of Parameter is ps, Array of Statement is bd){
								if({ returnType:name == '' || returnType:name == :names:voidName() }, {
									returnType:name: Primitive:BOOLEAN:value();
								});
							}
						], default: {});
					});
					:inferExpressionType(expr: arg:value);
				});
				:inBranchClosure: savedLoopBranch;
			}, {
				:inBranchClosure: false;
				call:args:each(action: local Function(NamedArg is arg){
					if({ bareIsBranch && bareIdx == 0 }, {
						match(on: arg:value, when: [
							Expression:AnonFn: local Function(Type is returnType, Array of Parameter is ps, Array of Statement is bd){
								if({ returnType:name == '' || returnType:name == :names:voidName() }, {
									returnType:name: Primitive:BOOLEAN:value();
								});
							}
						], default: {});
					});
					if({ bareIsBranch && bareIdx >= 1 }, {
						:inBranchClosure: true;
						:inValueBranch: bareIsValue;
						:currentYieldExpected: '';
						if({ bareIsValue }, {
							:currentYieldExpected: expected;
						});
					});
					:inferExpressionType(expr: arg:value);
					:inBranchClosure: false;
					:inValueBranch: false;
					:currentYieldExpected: '';
					bareIdx: bareIdx + 1;
				});
			});
		});
		:selectOverload(className: provider, methodName: call:name, expr: expr);
		local Member is bareSelected: :lookupOverloadedMember(className: provider, methodName: call:name, idx: call:overloadIndex);
		if({ bareSelected:name != '' }, {
			:checkMemberVisibility(ownerClass: provider, member: bareSelected, memberName: call:name);
		});
		if({ provider == 'Loops' }, {
			:localVars: savedLoopVars;
			if({ :inLazyBlock }, {
				:lazyLocalVars: savedLoopLazyVars;
			});
			call:bareProvider: provider;
			expr:setResolvedType(t: 'Void');
			return 'Void';
		});
		if({ bareIsLazy }, {
			call:bareProvider: provider;
			expr:setResolvedType(t: bareLazyRet);
			return bareLazyRet;
		});
		call:bareProvider: provider;
		local String is providerRet: '';
		if({ bareSelected:name != '' }, {
			providerRet: :selectedReturnType(className: provider, selected: bareSelected, expr: expr);
		});
		if({ providerRet == '' }, {
			providerRet: :lookupMethodReturnType(className: provider, methodName: call:name);
		});
		if({ providerRet == '' }, {
			providerRet: 'Any';
		});
		if({ bareIsValue }, {
			local String is valRes: :unifyValueBranchTypes(expr: expr);
			expr:setResolvedType(t: valRes);
			return valRes;
		});
		expr:setResolvedType(t: providerRet);
		return providerRet;
	}

	## `try(body:, guard:)` — runs the body region; if it unwinds with a
	## `SpecError`, runs the guard with that error and yields the guard's
	## value. Both args must be literal regions: the lowering is frame-local
	## (a plain call cannot catch and resume — the post-call unwind check is
	## frame-terminal). The construct's type is the expected type when one
	## flows in, else the body region's declared yield type.
	local Function of String is inferTryCall(Expression is expr, CallData is call, String is expected){
		local NamedArg is bodyNa: call:args:get(index: 0);
		local NamedArg is guardNa: call:args:get(index: 1);
		local Int is nai: 0;
		while({ nai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: nai);
			if({ na:name == 'body' }, {
				bodyNa: na;
			}, {
				if({ na:name == 'guard' }, {
					guardNa: na;
				});
			});
			nai++;
		});
		local Boolean is bodyAnon: false;
		local Boolean is guardAnon: false;
		local Type is bodyRet: Type:init(name: '');
		local Array of Parameter is bodyParams: [];
		local Array of Parameter is guardParams: [];
		match(on: bodyNa:value, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				bodyAnon: true;
				bodyRet: rt;
				bodyParams: ps;
			}
		], default: {});
		match(on: guardNa:value, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				guardAnon: true;
				guardParams: ps;
			}
		], default: {});
		if({ !bodyAnon || !guardAnon }, {
			:addError(line: :currentLine, msg: 'try requires literal body and guard regions — a plain call cannot catch and resume.');
			expr:setResolvedType(t: '');
			return '';
		});
		if({ bodyParams:length() != 0 }, {
			:addError(line: :currentLine, msg: 'try body region takes no parameters.');
			expr:setResolvedType(t: '');
			return '';
		});
		if({ guardParams:length() != 1 || :formatVarTypeString(t: guardParams:get(index: 0):paramType) != 'SpecError' }, {
			:addError(line: :currentLine, msg: 'try guard region takes exactly one SpecError parameter.');
			expr:setResolvedType(t: '');
			return '';
		});
		local String is resTy: expected;
		if({ resTy == '' }, {
			resTy: bodyRet:name;
			if({ resTy == '' || :isVoid(t: resTy) }, {
				resTy: 'Any';
			});
		});
		# Infer both regions with the construct's type flowing as the yield
		# expectation (the branch-closure mechanism value-yielding `if` uses).
		:inBranchClosure: true;
		:inValueBranch: true;
		:currentYieldExpected: resTy;
		:inferExpressionType(expr: bodyNa:value, expected: resTy);
		:inBranchClosure: true;
		:inValueBranch: true;
		:currentYieldExpected: resTy;
		:inferExpressionType(expr: guardNa:value, expected: resTy);
		:inBranchClosure: false;
		:inValueBranch: false;
		:currentYieldExpected: '';
		expr:setResolvedType(t: resTy);
		return resTy;
	}

	local Function of Boolean is isValueBranchCall(Expression is expr, Boolean is isBranchCall, String is expected){
		if({ !isBranchCall || expr:argCount() != 3 || expected == '' || :isVoid(t: expected) }, {
			return false;
		});
		local Boolean is arg1IsAnon: false;
		local Boolean is arg2IsAnon: false;
		local Array of Statement is tAnonBody: [];
		local Array of Statement is eAnonBody: [];
		match(on: expr:argValue(index: 1), when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				arg1IsAnon: true;
				tAnonBody: bd;
			}
		], default: {});
		match(on: expr:argValue(index: 2), when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				arg2IsAnon: true;
				eAnonBody: bd;
			}
		], default: {});
		if({ !arg1IsAnon || !arg2IsAnon }, {
			return false;
		});
		local Int is tLen: tAnonBody:length();
		local Int is eLen: eAnonBody:length();
		if({ tLen == 0 || eLen == 0 }, {
			return false;
		});
		local Statement is tLast: tAnonBody:get(index: tLen - 1);
		local Statement is eLast: eAnonBody:get(index: eLen - 1);
		local Boolean is tHasRet: match(on: tLast, when: [
			Statement:Return: local Function of Boolean(Expression is returnExpr, Boolean is hasReturnExpr){
				return hasReturnExpr;
			},
			else: { false }
		]);
		local Boolean is eHasRet: match(on: eLast, when: [
			Statement:Return: local Function of Boolean(Expression is returnExpr, Boolean is hasReturnExpr){
				return hasReturnExpr;
			},
			else: { false }
		]);
		return tHasRet && eHasRet;
	}

	local Function of String is inferWhileLoopCall(Expression is expr, CallData is call, String is targetType, String is method){
		local Map of String to String is savedWhileVars: Map:init();
		local Array of String is existingKeys: :localVars:keys();
		existingKeys:each(action: local Function(String is k){
			savedWhileVars:set(key: k, value: :localVars:getString(key: k, default: ''));
		});
		local Map of String to String is savedWhileLazyVars: Map:init();
		if({ :inLazyBlock }, {
			local Array of String is lExistingKeys: :lazyLocalVars:keys();
			lExistingKeys:each(action: local Function(String is k){
				savedWhileLazyVars:set(key: k, value: :lazyLocalVars:getString(key: k, default: ''));
			});
		});
		local Boolean is hasLoopVars: false;
		local Int is posIdx: 0;
		call:args:each(action: local Function(NamedArg is arg){
			match(on: arg:value, when: [
				Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
					if({ ps:length() > 0 && bd:length() == 0 }, {
						hasLoopVars: true;
						ps:each(action: local Function(Parameter is p){
							if({ p:hasDefault }, {
								:inferExpressionType(expr: p:defaultExpr);
							});
							local String is pFmt: :formatVarTypeString(t: p:paramType);
							:localVars:set(key: p:name, value: pFmt);
							if({ :inLazyBlock }, {
								:lazyLocalVars:set(key: p:name, value: pFmt);
							});
						});
					});
				}
			], default: {});
			local Boolean is closureSlot: arg:name == 'evaluate' || arg:name == 'iterate' || arg:name == 'iteration' || arg:name == 'worker' || (arg:name == '' && ((hasLoopVars && (posIdx == 1 || posIdx == 2)) || (!hasLoopVars && (posIdx == 0 || posIdx == 1))));
			local Boolean is argIsAnon: false;
			match(on: arg:value, when: [
				Expression:AnonFn: local Function(Type is returnType, Array of Parameter is ps, Array of Statement is bd){
					argIsAnon: true;
					if({ arg:name == 'evaluate' }, {
						if({ returnType:name == '' || returnType:name == :names:voidName() }, {
							returnType:name: Primitive:BOOLEAN:value();
						});
					}, {
						if({ arg:name == '' }, {
							if({ (hasLoopVars && posIdx == 1) || (!hasLoopVars && posIdx == 0) }, {
								if({ returnType:name == '' || returnType:name == :names:voidName() }, {
									returnType:name: Primitive:BOOLEAN:value();
								});
							});
						});
					});
				}
			], default: {});
			if({ hasLoopVars && closureSlot && !argIsAnon }, {
				:addError(line: :currentLine, msg: :errText:errLoopVarsClosureLiteral());
			});
			posIdx: posIdx + 1;
		});
		:bindContainerCallbackParams(targetType: targetType, method: method, expr: expr);
		local Boolean is savedLoopBranch: :inBranchClosure;
		:inBranchClosure: false;
		local Int is loopArgIdx: 0;
		call:args:each(action: local Function(NamedArg is arg){
			if({ arg:name == 'evaluate' || (arg:name == '' && ((hasLoopVars && loopArgIdx == 1) || (!hasLoopVars && loopArgIdx == 0))) }, {
				match(on: arg:value, when: [
					Expression:AnonFn: local Function(Type is returnType, Array of Parameter is ps, Array of Statement is bd){
						if({ returnType:name == '' || returnType:name == :names:voidName() }, {
							returnType:name: Primitive:BOOLEAN:value();
						});
					}
				], default: {});
			});
			:inferExpressionType(expr: arg:value);
			loopArgIdx: loopArgIdx + 1;
		});
		:inBranchClosure: savedLoopBranch;
		:localVars: savedWhileVars;
		if({ :inLazyBlock }, {
			:lazyLocalVars: savedWhileLazyVars;
		});
		expr:setResolvedType(t: 'Void');
		return 'Void';
	}

	local Function is inferCallArgs(CallData is call, String is targetType, String is method, String is expected, Boolean is isBranchCall, Boolean is isValueBranch){
		local Int is argIdx: 0;
		# Ambient branch-closure state belongs to the ENCLOSING region
		# inference (a try body's flags must survive a nested call's own
		# arg inference), so this function restores rather than clears.
		local Boolean is savedBranch: :inBranchClosure;
		local Boolean is savedValue: :inValueBranch;
		local String is savedYieldExp: :currentYieldExpected;
		call:args:each(action: local Function(NamedArg is arg){
			if({ isBranchCall && argIdx == 0 }, {
				match(on: arg:value, when: [
					Expression:AnonFn: local Function(Type is returnType, Array of Parameter is ps, Array of Statement is bd){
						if({ returnType:name == '' || returnType:name == :names:voidName() }, {
							returnType:name: Primitive:BOOLEAN:value();
						});
					}
				], default: {});
			});
			local String is callArgExp: '';
			if({ isBranchCall && argIdx >= 1 }, {
				:inBranchClosure: true;
				:inValueBranch: isValueBranch;
				:currentYieldExpected: '';
				if({ isValueBranch }, {
					:currentYieldExpected: expected;
				});
			});
			if({ !isBranchCall && expected != '' && !:isVoid(t: expected) }, {
				local Type is expNode: :parseTypeNode(s: expected);
				if({ expNode:params:length() == 1 }, {
					local Type is expArg0: expNode:params:get(index: 0);
					if({ expArg0:name != '' && !:isVoid(t: expArg0:name) && expArg0:name != Primitive:ANY:value() }, {
						local Boolean is paramExpectsTypedFn: false;
						local Member is expCallee: :lookupAnyMember(className: targetType, methodName: method);
						if({ expCallee:name == '' }, {
							expCallee: :findHeldMethod(className: targetType, methodName: method);
						});
						local Member is expTypedCallee: :lookupAnyMember(className: targetType, methodName: method . 'Typed');
						local Array of Member is expCandidates: [expCallee, expTypedCallee];
						expCandidates:each(action: local Function(Member is cm){
							if({ !paramExpectsTypedFn && cm:name != '' }, {
								local Int is pi: 0;
								cm:params:each(action: local Function(Parameter is cp){
									local Boolean is pMatch: if({ arg:name != '' }, { cp:name == arg:name }, { pi == argIdx });
									if({ pMatch && cp:paramType:name == 'Function' && cp:paramType:params:length() > 0 }, {
										paramExpectsTypedFn: true;
									});
									pi++;
								});
							});
						});
						if({ paramExpectsTypedFn }, {
							match(on: arg:value, when: [
								Expression:AnonFn: local Function(Type is _fnRt, Array of Parameter is _fnPs, Array of Statement is _fnBd){
									callArgExp: 'Function:' . :formatTypeString(t: expArg0);
								}
							], default: {});
						});
					});
				});
			});
			:inferExpressionType(expr: arg:value, expected: callArgExp);
			:inBranchClosure: savedBranch;
			:inValueBranch: savedValue;
			:currentYieldExpected: savedYieldExp;
			argIdx: argIdx + 1;
		});
		:inBranchClosure: savedBranch;
		:inValueBranch: savedValue;
		:currentYieldExpected: savedYieldExp;
	}

	local Function is checkThreadScopeOpenArgs(CallData is call){
		if({ :namespaceEquals(segs: :currentClassDef:namespaceSegments(), want: ['base', 'sys', 'thread']) }, {
			return;
		});
		local Boolean is hasOnErrorArg: false;
		call:args:each(action: local Function(NamedArg is arg){
			if({ arg:name == 'onError' }, {
				hasOnErrorArg: true;
				match(on: arg:value, when: [
					Expression:AnonFn: local Function(Type is fnRetT, Array of Parameter is _p, Array of Statement is _b){
						local String is rt: :resolveReturnType(t: fnRetT);
						if({ rt != Primitive:BOOLEAN:value() }, {
							:addError(line: :currentLine, msg: "ThreadScope:open 'onError' handler must return Boolean (true if handled, false to keep bubbling), found '" . rt . "'.");
						});
					}
				], default: {});
			});
		});
		if({ !hasOnErrorArg && !:classHasCustomErrorHandler(className: :currentClassName) }, {
			:addError(line: :currentLine, msg: "ThreadScope:open requires either an 'onError:' handler argument or an enclosing class that replaces 'SpecErrorHandler'.");
		});
	}

	local Function of String is inferHeldCall(Expression is expr, CallData is call, String is heldRoot, String is method, Member is heldCallFn, String is expected){
		local String is heldOwner: :findHeldMethodOwner(className: heldRoot, methodName: method);
		:checkMemberVisibility(ownerClass: heldOwner, member: heldCallFn, memberName: method);
		if({ heldRoot == 'ThreadScope' && method == 'open' }, {
			:checkThreadScopeOpenArgs(call: call);
		});
		local String is heldRet: :resolveReturnType(t: heldCallFn:memberType);
		local ClassInfo is hOwnerCls: :findClass(name: heldOwner);
		if({ hOwnerCls:typeParams:length() > 0 }, {
			local String is tp0: hOwnerCls:typeParams:get(index: 0);
			if({ heldRet == hOwnerCls:name . ':' . tp0 || heldRet == hOwnerCls:name }, {
				local String is inferredArgT: '';
				if({ heldCallFn:params:length() > 0 && call:args:length() > 0 }, {
					local Parameter is hp0: heldCallFn:params:get(index: 0);
					local String is hp0Str: :formatVarTypeString(t: hp0:paramType);
					if({ hp0Str:endsWith(suffix: ':' . tp0) }, {
						local String is hpPrefix: hp0Str:substring(start: 0, end: hp0Str:length() - tp0:length());
						local NamedArg is ca0: call:args:get(index: 0);
						local String is ca0T: ca0:value:resolvedType;
						if({ ca0T:startsWith(prefix: hpPrefix) && ca0T:length() > hpPrefix:length() }, {
							inferredArgT: ca0T:substring(start: hpPrefix:length(), end: ca0T:length());
						});
					});
				});
				if({ inferredArgT != '' && inferredArgT != tp0 }, {
					heldRet: hOwnerCls:name . ':' . inferredArgT;
				}, {
					if({ expected:startsWith(prefix: hOwnerCls:name . ':') || expected:startsWith(prefix: hOwnerCls:name . ' of ') }, {
						heldRet: expected;
					});
				});
			});
		});
		expr:setResolvedType(t: heldRet);
		return heldRet;
	}

	local Function is checkThreadingCallRules(String is targetType, String is recvName, CallData is call, String is method){
		if({ (targetType == 'ThreadScope' || recvName == 'ThreadScope') && method == 'init' && :currentClassName != 'ThreadScope' }, {
			:addError(line: :currentLine, msg: "Cannot construct 'ThreadScope' directly with 'ThreadScope:init'; use 'ThreadScope:open(body: ...)' so all spawned threads are joined before scope exit.");
		});
		if({ (targetType == 'ThreadScope' || recvName == 'ThreadScope') && method == 'open' }, {
			:checkThreadScopeOpenArgs(call: call);
		});
		if({ (targetType == 'ThreadScope' || recvName == 'ThreadScope') && (method == 'joinAll' || method == 'destroy' || method == 'registerTask') && !:namespaceEquals(segs: :currentClassDef:namespaceSegments(), want: ['base', 'sys', 'thread']) }, {
			:addError(line: :currentLine, msg: "Method 'ThreadScope:" . method . "' is internal to 'base:sys:thread'; 'ThreadScope:open' joins all tasks automatically.");
		});
		if({ (TypeDomain:isOfBase(t: targetType, base: 'Task') || recvName == 'Task') && (method == 'init' || method == 'start' || method == 'markRunning' || method == 'complete' || method == 'completeVoid' || method == 'spawnInScope' || method == 'fail' || method == 'failAddr' || method == 'joinOnly' || method == 'destroy') }, {
			if({ !:namespaceEquals(segs: :currentClassDef:namespaceSegments(), want: ['base', 'sys', 'thread']) }, {
				:addError(line: :currentLine, msg: "Method 'Task:" . method . "' is internal to 'base:sys:thread'; tasks must be spawned via 'scope:spawn(task: ...)' inside a 'ThreadScope:open' block.");
			});
		});
		if({ (targetType == 'Thread' || recvName == 'Thread' || call:bareProvider == 'Thread') && (method == 'threadSpawn' || method == 'threadJoin') }, {
			if({ !:namespaceEquals(segs: :currentClassDef:namespaceSegments(), want: ['base', 'sys', 'thread']) }, {
				:addError(line: :currentLine, msg: "Raw thread management ('Thread:" . method . "') is restricted to 'base:sys:thread'; all threads must be spawned inside a 'ThreadScope:open' block.");
			});
		});
	}

	local Function of String is inferParallelCall(CallData is call, String is method){
		if({ method == 'sync' || method == 'syncWith' }, {
			local Boolean is hasAction: false;
			local String is actRetT: 'Void';
			call:args:each(action: local Function(NamedArg is arg){
				local String is aName: arg:name;
				local String is aType: :inferExpressionType(expr: arg:value);
				if({ aName == 'lock' }, {
					if({ aType != Primitive:INT:value() && aType != 'Any' }, {
						:addError(line: :currentLine, msg: "Parallel:syncWith 'lock' argument must be Int, found '" . aType . "'.");
					});
				}, {
					if({ aName == 'action' }, {
						hasAction: true;
						if({ !aType:startsWith(prefix: 'Function') && aType != 'Any' }, {
							:addError(line: :currentLine, msg: "Parallel:" . method . " 'action' argument must be a Function, found '" . aType . "'.");
						}, {
							if({ aType:startsWith(prefix: 'Function:') && aType:length() > 9 }, {
								actRetT: aType:substring(start: 9, end: aType:length());
							});
						});
					});
				});
			});
			if({ !hasAction }, {
				:addError(line: :currentLine, msg: "Parallel:" . method . " requires 'action' named argument.");
			});
			return actRetT;
		});
		local Boolean is hasScope: false;
		local Boolean is hasWorker: false;
		call:args:each(action: local Function(NamedArg is arg){
			local String is aName: arg:name;
			local String is aType: :inferExpressionType(expr: arg:value);
			if({ aName == 'scope' }, {
				hasScope: true;
				if({ aType != 'ThreadScope' && aType != 'Any' }, {
					:addError(line: :currentLine, msg: 'Parallel:run \'scope\' argument must be ThreadScope, found \'' . aType . '\'.');
				});
			}, {
				if({ aName == 'threads' || aName == 'iterations' }, {
					if({ aType != Primitive:INT:value() && aType != 'Any' }, {
						:addError(line: :currentLine, msg: 'Parallel:run \'' . aName . '\' argument must be Int, found \'' . aType . '\'.');
					});
				}, {
					if({ aName == 'worker' }, {
						hasWorker: true;
						if({ !aType:startsWith(prefix: 'Function') && aType != 'Any' }, {
							:addError(line: :currentLine, msg: 'Parallel:run \'worker\' argument must be a Function, found \'' . aType . '\'.');
						});
					});
				});
			});
		});
		if({ !hasScope }, {
			:addError(line: :currentLine, msg: 'Parallel:run requires \'scope\' (ThreadScope) named argument; all parallel execution must run in a ThreadScope.');
		});
		if({ !hasWorker }, {
			:addError(line: :currentLine, msg: 'Parallel:run requires \'worker\' named argument.');
		});
		return Primitive:INT:value();
	}

	local Function of String is inferRegisteredClassCall(Expression is expr, CallData is call, String is targetType, String is method, Boolean is targetIsSelf){
		if({ TypeDomain:isOfBase(t: targetType, base: 'List') && (method == 'get' || method == 'pop') }, {
			local Boolean is hasDefault: false;
			call:args:each(action: local Function(NamedArg is arg){
				if({ arg:name == 'default' }, {
					hasDefault: true;
				});
			});
			if({ !hasDefault }, {
				:addError(line: :currentLine, msg: 'List \'' . method . '\' requires a \'default:\' argument.');
			});
		});
		local Member is selected: :selectOverload(className: targetType, methodName: method, expr: expr);
		if({ selected:name != '' && call:args:length() > 0 }, {
			local Member is typedVariant: :lookupAnyMember(className: targetType, methodName: method . 'Typed');
			if({ typedVariant:name != '' }, {
				local NamedArg is tvArg0: call:args:get(index: 0);
				if({ TypeDomain:hasFunctionReturn(t: tvArg0:value:resolvedType) }, {
					selected: typedVariant;
				});
			});
		});
		local String is res: '';
		if({ selected:name != '' }, {
			res: :selectedReturnType(className: targetType, selected: selected, expr: expr);
		});
		if({ res == '' }, {
			res: targetType;
			match(on: method, when: [
				'toString': { res: Primitive:STRING:value(); },
				'length': { res: Primitive:INT:value(); },
				'isEmpty': { res: Primitive:BOOLEAN:value(); },
				'count': { res: Primitive:INT:value(); },
				'any': { res: Primitive:BOOLEAN:value(); },
				'has': { res: Primitive:BOOLEAN:value(); },
				'getString': { res: Primitive:STRING:value(); },
				'getInt': { res: Primitive:INT:value(); },
				'getFloat': { res: Primitive:FLOAT:value(); },
				'getBool': { res: Primitive:BOOLEAN:value(); },
				'indexOf': { res: Primitive:INT:value(); },
				'join': { res: Primitive:STRING:value(); },
				'keys': {
					local String is mk: TypeDomain:mapKeyType(t: targetType);
					res: if({ mk != '' }, { TypeDomain:makeArray(elem: mk) }, { 'Array of String' });
				},
				'add': { res: :names:voidName(); },
				'set': { res: :names:voidName(); },
				'clear': { res: :names:voidName(); },
				'each': { res: :names:voidName(); },
				'push': { res: :names:voidName(); },
				'remove': { res: Primitive:BOOLEAN:value(); },
				else: {}
			]);
			if({ res == targetType }, {
				if({ (TypeDomain:isParameterized(t: targetType, base: 'Array') || TypeDomain:isParameterized(t: targetType, base: 'List')) && (method == 'get' || method == 'pop' || method == 'removeAt') }, {
					res: TypeDomain:elemType(t: targetType);
				});
				if({ TypeDomain:isParameterized(t: targetType, base: 'Map') && (method == 'get' || method == 'getString') }, {
					local String is mv: TypeDomain:mapValType(t: targetType);
					if({ mv != '' }, { res: mv; });
				});
			});
		});
		if({ TypeDomain:isOfBase(t: targetType, base: 'Map') && method == 'keys' && (:currentClassName != 'Map' || !targetIsSelf) }, {
			local String is kRaw: TypeDomain:mapKeyType(t: targetType);
			local String is kType: if({ kRaw != '' && kRaw != 'Any' }, { kRaw }, { Primitive:STRING:value() });
			res: TypeDomain:makeArray(elem: kType);
		});
		if({ TypeDomain:isOfBase(t: targetType, base: 'Flow') }, {
			if({ method == 'map' && call:args:length() > 0 }, {
				local String is mFnRet: TypeDomain:functionReturn(t: call:args:get(index: 0):value:resolvedType);
				if({ mFnRet != '' }, {
					res: TypeDomain:makeFlow(elem: mFnRet);
				});
			});
			if({ (method == 'filter' || method == 'take' || method == 'onEach' || method == 'onCompletion' || method == 'buffer') && TypeDomain:isParameterized(t: targetType, base: 'Flow') }, {
				res: targetType;
			});
		});
		return res;
	}

	## Infers a CALL expression: container methods, enum methods, registered
	## class methods, and the builtin fallback table. Container callback
	## parameters are typed here (bidirectional flow into anonymous
	## functions); arguments then infer bottom-up.
	##
	## @param expr: The CALL expression.
	## @param expected: Contextual type ('' when none).
	## @return: Resolved type name string.
	Function of String is inferCall(Expression is expr, CallData is call, String is expected: ''){
		local Boolean is savedFnVarTarget: :inHeldFnVarTarget;
		local Boolean is targetIsSelf: false;
		local Boolean is targetIsIdent: false;
		local Boolean is targetIsPath: false;
		local String is targetStr: '';
		local Array of String is targetPathSegs: [];
		match(on: call:target, when: [
			Expression:Ident: local Function(String is name){
				targetIsIdent: true;
				targetStr: name;
				targetIsSelf: name == :names:selfIdent();
			},
			Expression:Path: local Function(Array of String is segs){
				targetIsPath: true;
				targetPathSegs: segs;
			}
		], default: {});
		if({ targetIsSelf && call:isBareCall && :registeredClasses:has(key: call:name) && !:allEnumNames:has(key: call:name) && !:shadowsAsFunction(name: call:name, isBareCall: true) && :findMemberOwnerClass(className: :currentClassName, memberName: call:name) == '' && :bareScopeProviders(methodName: call:name):length() == 0 }, {
			local String is ctorCls: call:name;
			call:target: Expression:Ident(name: ctorCls);
			call:name: 'init';
			call:isBareCall: false;
			targetIsIdent: true;
			targetIsSelf: false;
			targetStr: ctorCls;
		});
		if({ targetIsSelf && call:isBareCall && :localVars:getString(key: call:name, default: ''):startsWith(prefix: 'Function') }, {
			:inHeldFnVarTarget: true;
		});
		local String is targetType: :inferExpressionType(expr: call:target);
		:inHeldFnVarTarget: savedFnVarTarget;
		local String is method: call:name;
		local String is res: 'Any';

		local String is targetName: targetStr;
		if({ targetName == '' && targetIsPath && targetPathSegs:length() > 0 }, {
			targetName: targetPathSegs:get(index: targetPathSegs:length() - 1);
		});

		# Nested-construction shorthand: `Result:Ok(data: 'x')` ≡ `Result:Ok:init(data: 'x')`.
		if({ (targetIsIdent || targetIsPath) && method != 'init' && :registeredClasses:has(key: targetName) && !:localVars:has(key: targetName) && !:fieldTypes:has(key: targetName) }, {
			local ClassInfo is ncCls: :findClass(name: targetName);
			local Boolean is hasNested: false;
			if({ ncCls:name != '' }, {
				ncCls:members:each(action: local Function(Member is m){
					if({ !hasNested && m:kind == MemberKind:CLASS && m:nestedClass:name == method }, {
						hasNested: true;
					});
				});
			});
			if({ hasNested }, {
				local Array of String is segs: [targetName, method];
				call:target: Expression:Path(segments: segs);
				call:name: 'init';
				targetIsIdent: false;
				targetIsSelf: false;
				targetIsPath: true;
				targetPathSegs: segs;
				targetName: method;
				method: 'init';
				targetType: :inferExpressionType(expr: call:target);
			});
		});

		local String is recvName: '';
		if({ targetIsIdent || targetIsPath }, {
			local String is cand: targetName;
			if({ cand != '' && cand != :names:selfIdent() && :registeredClasses:has(key: cand) && !:localVars:has(key: cand) && !:fieldTypes:has(key: cand) }, {
				recvName: cand;
			});
		});
		:validateCallReceiverModel(recvName: recvName, call: call, targetIsPath: targetIsPath, targetPathSegs: targetPathSegs);

		if({ method == 'match' && (call:bareProvider == 'Conditional' || targetType == 'Conditional' || (targetIsIdent && ((targetStr == 'match' && :isAsImportedInherited(className: 'Conditional')) || (targetIsSelf && call:isBareCall && :isAsImportedInherited(className: 'Conditional'))))) }, {
			local String is matchRes: :inferMatchCall(expr: expr, call: call, expected: expected, targetIsSelf: targetIsSelf);
			if({ matchRes != '' }, {
				return matchRes;
			});
		});

		if({ method == 'try' && expr:argCount() == 2 && (call:bareProvider == 'Conditional' || call:bareProvider:endsWith(suffix: ':Conditional') || targetType == 'Conditional' || (targetIsIdent && targetStr == 'try' && :isAsImportedInherited(className: 'Conditional')) || (targetIsSelf && call:isBareCall && :isAsImportedInherited(className: 'Conditional'))) }, {
			return :inferTryCall(expr: expr, call: call, expected: expected);
		});

		if({ recvName == '' && targetIsSelf && call:name != 'init' && call:name != 'typeName' && !:shadowsAsFunction(name: call:name, isBareCall: call:isBareCall) }, {
			local String is ownOwner: :findMemberOwnerClass(className: :currentClassName, memberName: call:name);
			local Array of String is bsProviders: [];
			if({ call:isBareCall }, {
				bsProviders: :bareScopeProviders(methodName: call:name);
			});
			local Int is providerTotal: bsProviders:length() + if({ ownOwner != '' }, { 1 }, { 0 });
			if({ providerTotal > 1 }, {
				local String is listed: if({ ownOwner != '' }, { 'the enclosing class' }, { '' });
				bsProviders:each(action: local Function(String is prov){
					listed: if({ listed == '' }, { prov }, { listed . ' and ' . prov });
				});
				:addError(line: :currentLine, msg: 'Function \'' . call:name . '\' is provided by ' . listed . '; qualify the call (:' . call:name . ' or the class name) (§2.3).');
				expr:setResolvedType(t: '');
				return '';
			});
			if({ providerTotal == 0 }, {
				:addError(line: :currentLine, msg: 'Undefined function \'' . call:name . '\' on class \'' . :currentClassName . '\' (E9).');
				expr:setResolvedType(t: '');
				return '';
			});
			if({ ownOwner == '' }, {
				return :inferBareScopeCall(expr: expr, call: call, expected: expected, provider: bsProviders:get(index: 0));
			});
		});

		local Boolean is isBranchCall: call:name == 'if' && expr:argCount() >= 2 && expr:argCount() <= 4 && (((targetType == 'Conditional' && targetIsIdent) || (targetIsSelf && :currentClassName == 'Conditional')) || call:bareProvider == 'Conditional' || (targetIsIdent && targetStr == 'if' && :isAsImportedInherited(className: 'Conditional')));
		local Boolean is isValueBranch: :isValueBranchCall(expr: expr, isBranchCall: isBranchCall, expected: expected);
		:inBranchClosure: false;
		local Boolean is isLazyCall: ((targetType == 'Lazy' || targetName == 'Lazy') && (method == 'lazy' || method == 'eval')) || (targetIsSelf && :currentClassName == 'Lazy' && method == 'lazy');
		local String is qualLazyRet: 'Any';
		local Boolean is isWhileLoop: (targetType == 'Loops' || targetName == 'Loops') && (method == 'loop' || method == 'init' || method == 'while' || method == 'until' || method == 'repeat');

		if({ isWhileLoop }, {
			return :inferWhileLoopCall(expr: expr, call: call, targetType: targetType, method: method);
		});

		:bindContainerCallbackParams(targetType: targetType, method: method, expr: expr);
		if({ isLazyCall }, {
			qualLazyRet: :inferLazyCall(call: call, expected: expected);
		}, {
			:inferCallArgs(call: call, targetType: targetType, method: method, expected: expected, isBranchCall: isBranchCall, isValueBranch: isValueBranch);
		});

		if({ targetType == :names:selfIdent() || targetType == '' }, {
			targetType: :currentClassName;
			if({ :inHeldInit || :inHeldFunction }, {
				:addError(line: :currentLine, msg: :errText:errHeldNoInstance(method: method));
			});
		});

		local Member is heldCallFn: Member:init(kind: MemberKind:METHOD);
		local String is heldRoot: '';
		if({ targetIsIdent || targetIsPath }, {
			heldRoot: if({ targetIsPath && targetPathSegs:length() > 0 }, { targetPathSegs:get(index: 0) }, { targetStr });
			if({ heldRoot != '' && heldRoot != :names:selfIdent() && !:localVars:has(key: heldRoot) && !:fieldTypes:has(key: heldRoot) && :registeredClasses:has(key: heldRoot) && method != 'init' }, {
				heldCallFn: :findHeldMethod(className: heldRoot, methodName: method);
			});
		});
		if({ heldCallFn:name != '' }, {
			return :inferHeldCall(expr: expr, call: call, heldRoot: heldRoot, method: method, heldCallFn: heldCallFn, expected: expected);
		});
		if({ targetType != '' && targetType != Primitive:ANY:value() && !:allEnumNames:has(key: targetType) }, {
			local String is iBase: TypeDomain:baseName(t: targetType);
			if({ :registeredClasses:has(key: iBase) && :lookupMethodReturnType(className: iBase, methodName: method) == '' && :findHeldMethod(className: iBase, methodName: method):name != '' }, {
				:addError(line: :currentLine, msg: :errText:errHeldClassScoped(className: iBase, method: method));
			});
		});

		if({ targetIsPath }, {
			local String is qJoined: targetPathSegs:join(sep: ':');
			if({ qJoined:contains(needle: ':sysinternal:') }, {
				local ClassInfo is callerCls: :currentClassDef;
				local Array of String is callerSegs: callerCls:namespaceSegments();
				local String is floorClsName: targetPathSegs:get(index: targetPathSegs:length() - 1);
				local Boolean is sysWrapper: callerSegs:length() >= 2 && callerSegs:get(index: 0) == 'base' &&
					(callerSegs:get(index: 1) == 'sys' || callerSegs:get(index: 1) == 'sysinternal' || callerCls:name == floorClsName);
				if({ !sysWrapper }, {
					:addError(line: :currentLine, msg: :errText:errSysinternalRestricted(caller: callerCls:namespaceJoined()));
				});
				res: if({ isLazyCall }, { qualLazyRet }, { :lookupMethodReturnType(className: qJoined, methodName: method) });
				expr:setResolvedType(t: res);
				return res;
			});
		});

		if({ targetType == Primitive:ANY:value() || targetType == '' }, {
			if({ targetIsPath }, {
				local ClassInfo is qCls: :findClass(name: method);
				if({ qCls:name == method }, {
					targetType: method;
				});
			}, {
				match(on: call:target, when: [
					Expression:Call: local Function(CallData is qInnerCall){
						match(on: qInnerCall:target, when: [
							Expression:Path: local Function(Array of String is qSegs){
								local String is qCand: qInnerCall:name;
								local ClassInfo is qCls: :findClass(name: qCand);
								if({ qCand != '' && qCls:name == qCand }, {
									targetType: qCand;
								});
							}
						], default: {});
					}
				], default: {});
			});
		});

		if({ !:allEnumNames:has(key: targetType) && targetType != '' && targetType != 'Any' }, {
			local String is cBase: TypeDomain:baseName(t: targetType);
			local String is mOwner: :findMemberOwnerClass(className: cBase, memberName: method);
			if({ mOwner != '' }, {
				:checkMemberVisibility(ownerClass: mOwner, member: :lookupAnyMember(className: cBase, methodName: method), memberName: method);
			});
		});
		if({ targetType == Primitive:ANY:value() && method != 'toString' && method != 'typeName' && method != 'init' }, {
			:addError(line: :currentLine, msg: :errText:errMemberNotRootContract(member: method));
		});

		local String is fnVarT: '';
		if({ targetIsSelf }, {
			fnVarT: if({ call:isBareCall }, { :localVars:getString(key: method, default: :fieldTypes:getString(key: method, default: '')) }, { :fieldTypes:getString(key: method, default: '') });
		}, {
			if({ targetType != '' && targetType != Primitive:ANY:value() && !:allEnumNames:has(key: targetType) }, {
				local String is ft: :lookupFieldType(className: TypeDomain:baseName(t: targetType), fieldName: method);
				if({ TypeDomain:isFunction(t: ft) }, {
					fnVarT: ft;
				});
			});
		});
		:checkThreadingCallRules(targetType: targetType, recvName: recvName, call: call, method: method);

		if({ targetType == 'Parallel' && (method == 'sync' || method == 'syncWith' || method == 'run') }, {
			res: :inferParallelCall(call: call, method: method);
		}, {
			if({ TypeDomain:isFunction(t: fnVarT) }, {
				res: TypeDomain:functionReturn(t: fnVarT, default: 'Any');
			}, {
				if({ :allEnumVariants:has(key: method) && (:allEnumNames:has(key: targetType) || targetType == :currentClassName) }, {
					res: :allEnumVariants:getString(key: method, default: Primitive:ANY:value());
				}, {
					if({ method == 'typeName' && :registeredClasses:has(key: targetType) }, {
						res: Primitive:STRING:value();
					}, {
						if({ method == 'init' && :registeredClasses:has(key: targetType) && !:allEnumNames:has(key: targetType) }, {
							local Member is selInit: :selectOverload(className: targetType, methodName: 'init', expr: expr);
							local String is initBaseName: TypeDomain:baseName(t: targetType);
							if({ !:classHasAccess(className: :currentClassName, targetName: initBaseName) }, {
								:addError(line: :currentLine, msg: :errText:errTypeNotImported(targetType: targetType, currentClass: :currentClassName));
							});
							res: :inferGenericInitType(baseClassName: initBaseName, targetType: targetType, initMem: selInit, call: call, expected: expected);
						}, {
							if({ :registeredClasses:has(key: TypeDomain:baseName(t: targetType)) && !:allEnumNames:has(key: targetType) }, {
								res: :inferRegisteredClassCall(expr: expr, call: call, targetType: targetType, method: method, targetIsSelf: targetIsSelf);
							}, {
								if({ TypeDomain:isOfBase(t: targetType, base: 'Array') && method == 'map' }, {
									local String is mappedElem: Primitive:ANY:value();
									if({ call:args:length() > 0 }, {
										local NamedArg is a0: call:args:get(index: 0);
										match(on: a0:value, when: [
											Expression:AnonFn: local Function(Type is fnRetType, Array of Parameter is ps, Array of Statement is bd){
												local String is fnRet: fnRetType:name;
												if({ fnRet != '' && !:isVoid(t: fnRet) && fnRet != Primitive:ANY:value() }, {
													mappedElem: :formatTypeString(t: fnRetType);
												});
											}
										], default: {});
									});
									res: if({ mappedElem != Primitive:ANY:value() }, { TypeDomain:makeArray(elem: mappedElem) }, { 'Array' });
								}, {
									if({ TypeDomain:isOfBase(t: targetType, base: 'Array') && method == 'fold' }, {
										res: if({ call:args:length() > 0 }, { call:args:get(index: 0):value:resolvedType }, { 'Any' });
									}, {
										if({ :allEnumNames:has(key: targetType) }, {
											match(on: method, when: [
												'name': { res: Primitive:STRING:value(); },
												'ordinal': { res: Primitive:INT:value(); },
												'values': { res: TypeDomain:makeArray(elem: targetType); },
												'of': { res: targetType; },
												'value': { res: if({ :allStringBackedEnums:has(key: targetType) }, { 'String' }, { Primitive:INT:value() }); },
												else: { res: 'Any'; }
											]);
										}, {
											if({ targetType == Primitive:INT:value() && method == 'toBase' }, {
												res: Primitive:STRING:value();
											}, {
												local String is uBase: TypeDomain:baseName(t: targetType);
												if({ :registeredClasses:has(key: uBase) && :findClass(name: uBase):name != '' }, {
													:addError(line: :currentLine, msg: :errText:errMemberNotDeclared(member: method, targetType: targetType));
												});
												res: 'Any';
											});
										});
									});
								});
							});
						});
					});
				});
			});
		});

		if({ isValueBranch }, {
			res: :unifyValueBranchTypes(expr: expr);
		}, {
			if({ isBranchCall }, {
				res: :names:voidName();
			});
			if({ isLazyCall }, {
				res: qualLazyRet;
			});
		});
		return res;
	}

	## Infers a `lazy({ ... })` or `base:sysinternal:Lazy:eval({ ... })` call,
	## enforcing read-only access to external state inside the initializer closure
	## and unwrapping the closure's yielded return type `T`.
	##
	## @param call: The CallData node.
	## @param expected: Contextual expected type from the declaration/assignment site.
	## @return: The unwrapped return type `T` of the lazy initializer.
	Function of String is inferLazyCall(CallData is call, String is expected){
		local Boolean is savedBranch: :inBranchClosure;
		local Boolean is savedValBranch: :inValueBranch;
		local String is savedYieldExp: :currentYieldExpected;
		local Boolean is savedInLazy: :inLazyBlock;
		local Map of String to String is savedLazyLocals: :lazyLocalVars;

		:inBranchClosure: false;
		:inValueBranch: expected != '' && !:isVoid(t: expected);
		:currentYieldExpected: if({ expected != '' && !:isVoid(t: expected) }, { expected }, { '' });
		:inLazyBlock: true;
		:lazyLocalVars: Map:init();

		call:args:each(action: local Function(NamedArg is arg){
			:inferExpressionType(expr: arg:value);
		});

		:inBranchClosure: savedBranch;
		:inValueBranch: savedValBranch;
		:currentYieldExpected: savedYieldExp;
		:inLazyBlock: savedInLazy;
		:lazyLocalVars: savedLazyLocals;

		local String is lazyRet: 'Any';
		if({ call:args:length() > 0 }, {
			local NamedArg is a0: call:args:get(index: 0);
			local String is fnT: a0:value:resolvedType;
			if({ fnT:startsWith(prefix: 'Function:') && fnT:length() > 9 }, {
				lazyRet: fnT:substring(start: 9, end: fnT:length());
			}, {
				if({ fnT == 'Function' }, {
					lazyRet: :names:voidName();
				});
			});
		});
		return lazyRet;
	}

	## True when [className] or one of its non-root ancestors explicitly declares `SpecErrorHandler`.
	Function of Boolean is classHasCustomErrorHandler(String is className){
		return :classHasCustomErrorHandlerWalk(className: className, visited: []);
	}

	Function of Boolean is classHasCustomErrorHandlerWalk(String is className, Array of String is visited){
		if({ className == '' || className == 'Class' || className == 'Stringable' || className == 'Loadable' || className == 'Any' || className == 'Enum' }, {
			return false;
		});
		if({ visited:indexOf(search: className, default: -1) >= 0 }, {
			return false;
		});
		visited:add(item: className);
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			return false;
		});
		local Boolean is found: false;
		cls:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:METHOD && m:name == 'SpecErrorHandler' }, {
				found: true;
			});
		});
		if({ found }, {
			return true;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !found && :classHasCustomErrorHandlerWalk(className: baseName, visited: visited) }, {
				found: true;
			});
		});
		return found;
	}

	## True when [t] is `ThreadScope` or embeds `ThreadScope` as a type argument.
	Function of Boolean is containsThreadScopeType(String is t){
		if({ t == 'ThreadScope' }, { return true; });
		if({ t:contains(needle: ':ThreadScope') || t:contains(needle: 'ThreadScope:') || t:contains(needle: ' of ThreadScope') }, {
			return true;
		});
		return false;
	}

	## True when [expr] is rooted in a local variable declared inside the
	## current `lazy({ ... })` block (`:lazyLocalVars`).
	Function of Boolean is isLazyLocalTarget(Expression is expr){
		return match(on: expr, when: [
			Expression:Ident: local Function of Boolean(String is name){
				return name != :names:selfIdent() && :lazyLocalVars:has(key: name);
			},
			Expression:Path: local Function of Boolean(Array of String is segs){
				if({ segs:length() == 0 }, { return false; });
				local String is root: segs:get(index: 0);
				return root != :names:selfIdent() && :lazyLocalVars:has(key: root);
			},
			Expression:FieldAccess: local Function of Boolean(Expression is target, String is _f){
				return :isLazyLocalTarget(expr: target);
			},
			Expression:Index: local Function of Boolean(Expression is target, Expression is _idx){
				return :isLazyLocalTarget(expr: target);
			},
			else: { false }
		]);
	}

	## Declared primitive conversion compatibility for `as` casts: the
	## machine conversions (widen, truncate, parse). Transitional until the
	## primitive classes land in Spec and declare their conversions.
	##
	## @param src: Operand type name.
	## @param target: Cast target name.
	## @return: true when the conversion is declared.
	Function of Boolean is isCastable(String is src, String is target){
		if({ src == target || src == Primitive:ANY:value() }, {
			return true;
		});
		if({ target == Primitive:INT:value() }, {
			return src == 'Float' || src == 'String' || src == 'Str' || src == 'Byte' || :isUnsignedInt(t: src);
		});
		if({ target == 'Float' }, {
			return :isIntLike(t: src);
		});
		if({ target == 'Byte' }, {
			return :isIntLike(t: src);
		});
		if({ :isUnsignedInt(t: target) }, {
			return :isIntLike(t: src) || src == 'Float' || src == 'String' || src == 'Str';
		});
		if({ target == 'String' || target == 'Str' }, {
			return true;
		});
		return false;
	}

	## Resolves a `castable` declaration: returns the method name declared to
	## produce [target] from [srcType], or '' when none. The mapped function
	## must exist on the class (or an ancestor) and declare the target as its
	## return type; mismatches are compile errors at the cast site.
	##
	## @param srcType: The source value's type name.
	## @param target: The cast target name.
	## @return: The producing method name, or ''.
	Function of String is castableMethod(String is srcType, String is target){
		if({ srcType == '' || srcType == Primitive:ANY:value() || :isPrimitive(t: srcType) }, {
			return '';
		});
		local Array of String is srcParts: srcType:split(delimiter: ':');
		local ClassInfo is cls: :findClass(name: srcParts:get(index: 0));
		if({ cls:name == '' }, {
			return '';
		});
		# castable is a metadata FIELD declared on the class itself — the
		# method-only member lookup cannot see it, and ancestor searches skip
		# the declaring class. Search own members directly.
		local Member is castM: Member:init(kind: MemberKind:FIELD);
		local Int is castIdx: 0;
		local String is castTargetName: MetadataField:CASTABLE:value();
		while({ castM:name == '' && castIdx < cls:members:length() }, {
			local Member is m: cls:members:get(index: castIdx);
			castIdx: castIdx + 1;
			if({ m:kind == MemberKind:FIELD && m:name == castTargetName }, {
				castM: m;
			});
		});
		if({ castM:name == '' }, {
			return '';
		});
		if({ !castM:hasInit }, {
			return '';
		});
		local String is found: '';
		match(on: castM:initExpr, when: [
			Expression:ArrayLit: local Function(Array of Expression is items){
				items:each(action: local Function(Expression is entry){
					if({ found == '' }, {
						match(on: entry, when: [
							Expression:ArrayLit: local Function(Array of Expression is pair){
								if({ pair:length() == 2 }, {
									local String is entryTarget: '';
									local String is entryFn: '';
									local Expression is p0: pair:get(index: 0);
									local Expression is p1: pair:get(index: 1);
									match(on: p0, when: [
										Expression:Ident: local Function(String is s){ entryTarget: s; },
										Expression:StringLit: local Function(String is s){ entryTarget: s; }
									], default: {});
									match(on: p1, when: [
										Expression:Ident: local Function(String is s){ entryFn: s; },
										Expression:StringLit: local Function(String is s){ entryFn: s; }
									], default: {});
									if({ entryTarget == target }, {
										local String is fnRet: :lookupMethodReturnType(className: srcType, methodName: entryFn);
										if({ fnRet != target }, {
											:addError(line: :currentLine, msg: 'Cast \'as ' . target . '\' maps to \'' . entryFn . '\', which returns \'' . fnRet . '\', not \'' . target . '\'.');
											found: entryFn;
											return;
										});
										found: entryFn;
									});
								});
							}
						], default: {});
					});
				});
			}
		], default: {});
		return found;
	}

	## Validates type safety of a statement node.
	##
	## @param stmt: AST statement node.
	Function is checkStatement(Statement is stmt){
		if({ stmt:line > 0 }, {
			:currentLine: stmt:line;
		});
		match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				# the access gate resolves the bare nested
				# reference BEFORE the scope map stamps it — the checker and
				# the gen agree on the qualified identity.
				:validateTypeAccess(t: varType, line: stmt:line);
				local String is fullType: :formatVarTypeString(t: varType);
				:localVars:set(key: varName, value: fullType);
				if({ :inLazyBlock }, {
					:lazyLocalVars:set(key: varName, value: fullType);
				});

				if({ fullType == 'List' }, {
					local String is msg: 'Bare List type requires [T] element syntax.';
					:addError(line: stmt:line, msg: msg);
				});
				if({ !:namespaceEquals(segs: :currentClassDef:namespaceSegments(), want: ['base', 'sys', 'thread']) && :containsThreadScopeType(t: fullType) }, {
					:addError(line: stmt:line, msg: "Cannot declare local variable '" . varName . "' of type '" . :displayType(t: fullType) . "'; 'ThreadScope' is lexically bound to 'ThreadScope:open(body: { (ThreadScope is scope) ... })' and cannot be stored in local variables.");
				});

				if({ hasInit }, {
					# Bidirectional: the declared type flows into the
					# initializer, typing container literals directly.
					local String is initType: :inferExpressionType(expr: initExpr, expected: fullType);
					if({ !:isAssignable(target: fullType, source: initType) }, {
						local String is msg: :errText:errTypeMismatchDecl(varName: varName, initType: initType, fullType: fullType);
						# a void expression consumed as a
						# value explains itself instead of cascading into the
						# generic mismatch.
						if({ :isVoid(t: initType) }, {
							local String is note: :voidUseNote(expr: initExpr);
							if({ note != '' }, {
								msg: 'cannot initialize \'' . fullType . '\': ' . note;
							});
						});
						:addError(line: stmt:line, msg: msg);
					});
				});
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				if({ :inLazyBlock && !:isLazyLocalTarget(expr: assignTarget) }, {
					:addError(line: stmt:line, msg: "Cannot modify external state inside a 'lazy' initializer; 'lazy' blocks have read-only access to outer variables and fields.");
				});
				# Held members are read-only: a
				# class-name prefix target resolves to the shared held
				# slot, and assignment through it is rejected.
				# a resolution-hook name is a cached single copy too.
				match(on: assignTarget, when: [
					Expression:Path: local Function(Array of String is hSegs){
						if({ hSegs:length() >= 2 }, {
							local String is hRoot: hSegs:get(index: 0);
							local String is hName: hSegs:get(index: 1);
							local Boolean is hReadOnly: :findHeldMember(className: hRoot, memberName: hName):name != '';
							local Boolean is hHooked: false;
							if({ !hReadOnly && :findHeldMethod(className: hRoot, methodName: ContractMethod:RESOLVE_HELD:value()):name != '' }, {
								hHooked: :lookupFieldType(className: hRoot, fieldName: hName) == '' && :lookupAnyMember(className: hRoot, methodName: hName):kind != MemberKind:METHOD && :findHeldMethod(className: hRoot, methodName: hName):name == '';
							});
							if({ hRoot != :names:selfIdent() && !:localVars:has(key: hRoot) && !:fieldTypes:has(key: hRoot) && (hReadOnly || hHooked) }, {
								local String is hMsg: if({ hReadOnly }, { 'Held member \'' . hRoot . ':' . hName . '\' is read-only: held members are class-scoped single copies, assigned once by their initializer.' }, { 'Resolved member \'' . hRoot . ':' . hName . '\' is read-only: resolution-hook values are cached single copies.' });
								:addError(line: stmt:line, msg: hMsg);
							});
						});
						if({ hSegs:length() == 2 && hSegs:get(index: 0) == :names:selfIdent() }, {
							:unassignedFields:remove(key: hSegs:get(index: 1));
						});
					},
					Expression:Ident: local Function(String is name){
						local Boolean is removed: :unassignedFields:remove(key: name);
					}
				], default: {});
				local String is targetType: :inferExpressionType(expr: assignTarget);
				local String is valType: :inferExpressionType(expr: assignValue, expected: targetType);
				if({ !:namespaceEquals(segs: :currentClassDef:namespaceSegments(), want: ['base', 'sys', 'thread']) && (:containsThreadScopeType(t: targetType) || :containsThreadScopeType(t: valType)) }, {
					:addError(line: stmt:line, msg: "Cannot assign 'ThreadScope'; 'ThreadScope' is lexically scoped to 'ThreadScope:open' and cannot be reassigned or stored.");
				});
				if({ !:isAssignable(target: targetType, source: valType) }, {
						local String is msg: :errText:errTypeMismatchAssign(valType: valType, targetType: targetType);
						# the same for assignments.
						if({ :isVoid(t: valType) }, {
							local String is note: :voidUseNote(expr: assignValue);
							if({ note != '' }, {
								msg: 'cannot assign a void expression to \'' . targetType . '\': ' . note;
							});
						});
						:addError(line: stmt:line, msg: msg);
				});
			},
			Statement:Forward: local Function(Array of NamedArg is forwardArgs){
				:checkForward(args: forwardArgs, line: stmt:line);
			},
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ hasReturnExpr }, {
					# Bidirectional: the declared return type flows in — and a
					# value-yielding branch's yield takes the branch's own
					# expected type (nested branch calls type in context).
					local String is yieldExpected: :currentMethodReturnType;
					if({ :checkingValueYield && :currentYieldExpected != '' }, {
						yieldExpected: :currentYieldExpected;
					});
					local String is retType: :inferExpressionType(expr: returnExpr, expected: yieldExpected);
					# the last statement of a
					# value-yielding branch closure establishes the branch's
					# yield type (the inBranchClosure method-routing does not
					# apply to it).
					if({ :checkingValueYield }, {
						match(on: :currentAnonNode, when: [
							Expression:AnonFn: local Function(Type is returnType, Array of Parameter is ps, Array of Statement is bd){
								local String is curRetT: :resolveReturnType(t: returnType);
								if({ :isVoid(t: curRetT) }, {
									returnType:name: retType;
									returnType:params: [];
									:currentMethodReturnType: retType;
								}, {
									if({ !:isAssignable(target: curRetT, source: retType) }, {
										local String is msg: 'Branch yields mismatched types: expected \'' . curRetT . '\', found \'' . retType . '\'.';
										:addError(line: stmt:line, msg: msg);
									});
								});
							}
						], default: {});
					}, {
						# A return inside an untyped closure infers the closure's
						# return type — including returns nested in statement-form
						# branches: the inline machinery routes them out of the
						# CLOSURE, so they type against it, not against the
						# enclosing method. Only a value-branch's yield (which
						# types against the branch's expected type above) keeps
						# the method-level routing.
						local Boolean is inferredClosureRet: false;
						if({ :anonDepth > 0 && !:checkingValueYield && :isVoid(t: :currentMethodReturnType) }, {
							match(on: :currentAnonNode, when: [
								Expression:AnonFn: local Function(Type is returnType, Array of Parameter is ps, Array of Statement is bd){
									if({ :isVoid(t: :resolveReturnType(t: returnType)) }, {
										returnType:name: retType;
										returnType:params: [];
										:currentMethodReturnType: retType;
										inferredClosureRet: true;
									});
								}
							], default: {});
						});
						if({ !inferredClosureRet }, {
							if({ !:isAssignable(target: :currentMethodReturnType, source: retType) }, {
								local String is msg: 'Method declared return type \'' . :currentMethodReturnType . '\', but returned \'' . retType . '\' (method ' . :currentMethodName . ' of ' . :currentClassName . ', stmt line ' . (stmt:line as String) . ', depth ' . (:anonDepth as String) . ', inBranch ' . (:inBranchClosure as String) . ', expr line ' . (returnExpr:line as String) . ').';
								:addError(line: stmt:line, msg: msg);
							});
						});
					});
				}, {
					if({ :currentMethodReturnType != 'void' && :currentMethodReturnType != 'Void' && :currentMethodReturnType != '' && :currentMethodReturnType != 'Any' }, {
						local String is msg: :errText:errMethodEmptyReturn(expected: :currentMethodReturnType);
						:addError(line: stmt:line, msg: msg);
					});
				});
			},
			Statement:Expr: local Function(Expression is exprStmt){
				# Bound so the arm stays void: a trailing value-yielding
				# expression statement IS the arm's yield (the Kotlin
				# last-expression rule), and this arm is statement-form.
				local String is exprT: :inferExpressionType(expr: exprStmt);
			},
			Statement:ClassDecl: local Function(ClassInfo is nestedClass){
				local String is savedClass: :currentClassName;
				local ClassInfo is savedClassDef: :currentClassDef;
				local String is savedRet: :currentMethodReturnType;
				local Map of String to String is savedVars: Map:init();
				local Array of String is vKeys: :localVars:keys();
				vKeys:each(action: local Function(String is k){
					savedVars:set(key: k, value: :localVars:getString(key: k, default: ''));
				});
				local Map of String to String is savedFields: Map:init();
				local Array of String is fKeys: :fieldTypes:keys();
				fKeys:each(action: local Function(String is k){
					savedFields:set(key: k, value: :fieldTypes:getString(key: k, default: ''));
				});
				local Map of String to String is savedUnassigned: Map:init();
				local Array of String is uKeys: :unassignedFields:keys();
				uKeys:each(action: local Function(String is k){
					savedUnassigned:set(key: k, value: :unassignedFields:getString(key: k, default: ''));
				});

				:checkClass(classDef: nestedClass);

				:currentClassName: savedClass;
				:currentClassDef: savedClassDef;
				:currentMethodReturnType: savedRet;
				:localVars: savedVars;
				:fieldTypes: savedFields;
				:unassignedFields: savedUnassigned;
			}
		]);
	}

	## the diagnostic display form of a type
	## name — the internal colon form ('Function:Boolean') renders the way
	## the language spells it ('Function of Boolean').
	##
	## @param t: Internal type name.
	## @return: The display name.
	Function of String is displayType(String is t){
		local String is out: '';
		while([Int is i: 0], { i < t:length() }, {
			if({ i + 9 <= t:length() && t:substring(start: i, end: i + 9) == 'Function:' }, {
				out: out . 'Function of ';
				i: i + 9;
			}, {
				out: out . t:charAt(index: i, default: '');
				i++;
			});
		});
		return out;
	}

	## the void-in-value-context hint. Describes
	## WHY an expression computes no value, derived from the CALLEE'S
	## DECLARATION — the function's name, its void return, and how many of
	## its declared parameters the call binds. No per-class special cases:
	## the same note serves every callable in the language. Reads the AST
	## and already-resolved types only — never re-infers.
	##
	## @param expr: The void expression being consumed.
	## @return: The hint text, or ''.
	Function of String is voidUseNote(Expression is expr){
		local String is note: '';
		match(on: expr, when: [
			Expression:Call: local Function(CallData is call){
				local String is targetT: call:target:resolvedType;
				if({ targetT == :names:selfIdent() || targetT == '' }, {
					targetT: :currentClassName;
				});
				local ClassInfo is tc: :findClass(name: targetT:split(delimiter: ':'):get(index: 0));
				if({ tc:name != '' }, {
					local Member is m: :lookupOverloadedMember(className: targetT, methodName: call:name, idx: call:overloadIndex);
					if({ m:name != '' }, {
						local String is mRet: :resolveReturnType(t: m:memberType);
						if({ :isVoid(t: mRet) }, {
							note: '\'' . targetT . '.' . call:name . '\' declares no return value';
							if({ call:args:length() < m:params:length() }, {
								note: note . ' (' . (call:args:length() as String) . ' of ' . (m:params:length() as String) . ' declared parameters bound)';
							});
							local Array of Member is group: [];
							local Array of String is groupOwners: [];
							:collectOverloadGroup(className: targetT, methodName: call:name, acc: group, ownerAcc: groupOwners);
							local Int is maxParams: m:params:length();
							group:each(action: local Function(Member is g){
								if({ g:params:length() > maxParams }, {
									maxParams: g:params:length();
								});
							});
							if({ maxParams > m:params:length() }, {
								local String is names: '';
								group:each(action: local Function(Member is g){
									if({ g:params:length() == maxParams }, {
										g:params:each(action: local Function(Parameter is p){
											if({ names:endsWith(suffix: p:name) == false }, {
												if({ names != '' }, {
													names: names . ', ';
												});
												names: names . p:name;
											});
										});
									});
								});
								note: note . ' (' . (maxParams as String) . ' parameters are available: ' . names . ')';
							});
						});
					});
				});
			}
		], default: {});
		return note;
	}

	## Validates a merge-forward statement against its parent method:
	## merge context, single-use, arity, naming, and argument types.
	##
	## @param args: The FORWARD arguments.
	## @param line: Source line number.
	Function is checkForward(Array of NamedArg is args, Int is line){
		if({ !:currentMethodIsMerge }, {
			:addError(line: line, msg: :errText:errForwardRequiresMerge());
			return;
		});
		if({ :anonDepth > 0 }, {
			:addError(line: line, msg: :errText:errForwardNestedNotAllowed());
			return;
		});
		if({ :forwardSeen }, {
			:addError(line: line, msg: :errText:errForwardMultipleNotAllowed(method: :currentMethodName));
			return;
		});
		:forwardSeen: true;

		local Member is superM: :findFirstSuperMethod(className: :currentClassName, methodName: :currentMethodName);
		if({ superM:name == '' }, {
			:addError(line: line, msg: :errText:errForwardNoParentMethod(method: :currentMethodName));
			return;
		});
		local Array of Parameter is params: superM:params;

		if({ args:length() > params:length() }, {
			:addError(line: line, msg: :errText:errForwardArgCountMismatch(method: :currentMethodName, parentMethod: superM:name, passed: args:length(), accepted: params:length()));
			return;
		});
		if({ args:length() < params:length() }, {
			local Int is nIdx: 0;
			args:each(action: local Function(NamedArg is a){
				if({ a:name == '' }, {
					:addError(line: line, msg: :errText:errForwardNamedRequired(argNum: nIdx + 1, method: :currentMethodName));
				});
				nIdx: nIdx + 1;
			});
		});

		local Int is pIdx: 0;
		params:each(action: local Function(Parameter is p){
			local Expression is matchedValue: Expression:Unknown;
			local Boolean is found: false;
			args:each(action: local Function(NamedArg is a){
				if({ !found && a:name != '' && a:name == p:name }, {
					matchedValue: a:value;
					found: true;
				});
			});
			if({ !found && pIdx < args:length() }, {
				local NamedArg is posArg: args:get(index: pIdx);
				if({ posArg:name == '' }, {
					matchedValue: posArg:value;
					found: true;
				});
			});
			if({ found }, {
				local String is argT: :inferExpressionType(expr: matchedValue);
				local String is pT: p:paramType:name;
				if({ pT != Primitive:ANY:value() && pT != '' && argT != '' && argT != Primitive:ANY:value() && !:isAssignable(target: pT, source: argT) }, {
					local String is label: if({ p:name != '' }, { p:name }, { 'position ' . (pIdx + 1) });
					local String is msg: 'Forward argument \'' . label . '\' of \'' . :currentMethodName . '\': cannot assign \'' . argT . '\' to \'' . pT . '\'.';
					:addError(line: line, msg: msg);
				});
			}, {
				if({ !p:hasDefault }, {
					local String is msg: 'Forward statement omits \'' . p:name . '\' of \'' . :currentMethodName . '\' which has no default value.';
					:addError(line: line, msg: msg);
				});
			});
			pIdx: pIdx + 1;
		});
	}

	## Resolves the concrete return type of a method signature.
	##
	## @param t: Declared type descriptor.
	## @return: Return type name string.
	Function of String is resolveReturnType(Type is t){
		return :formatTypeString(t: t);
	}

	## Validates a method member definition.
	##
	## @param method: Method member descriptor.
	Function is checkMethod(Member is method){
		if({ method:line > 0 }, {
			:currentLine: method:line;
		});
		if({ method:sourceFile != '' }, {
			:currentSourceFile: method:sourceFile;
		});
		:currentMethodName: method:name;
		:forwardSeen: false;
		:anonDepth: 0;
		:currentMethodIsMerge: method:hasModifier(kw: Keyword:MERGE);
		:currentMethodTypeParams: Map:init();
		local String is mTp: :detectMethodTypeParamForMember(m: method, cls: :currentClassDef);
		if({ mTp != '' }, {
			:currentMethodTypeParams:set(key: mTp, value: true);
			local String is gmKey: :currentClassName . ':' . method:name;
			:genericMethodTemplates:set(key: gmKey, value: mTp);
			:genericMethodLines:set(key: gmKey, value: method:line);
			:genericMethodFiles:set(key: gmKey, value: :currentSourceFile);
		});
		local Int is declPIdx: 0;
		method:params:each(action: local Function(Parameter is p){
			if({ p:isVariadic }, {
				if({ declPIdx != method:params:length() - 1 }, {
					:addError(line: method:line, msg: "Variadic parameter '*" . p:name . "' in '" . :currentClassName . ":" . method:name . "' must be the last parameter.");
				});
				local String is vtn: p:paramType:name;
				if({ vtn != 'Array' && vtn != 'Map' }, {
					:addError(line: method:line, msg: "Variadic parameter '*" . p:name . "' must have type 'Array' or 'Map', got '" . vtn . "'.");
				});
			});
			:validateTypeAccess(t: p:paramType, line: method:line);
			# IV.6 strictness: the declaration-side default is construction
			# the declaring class bakes in — it gates against the declaring
			# class's imports exactly like a body expression.
			if({ p:hasDefault }, {
				:inferExpressionType(expr: p:defaultExpr);
			});
			declPIdx: declPIdx + 1;
		});
		:validateTypeAccess(t: method:memberType, line: method:line);
		local Member is mergeTarget: :findFirstSuperMethod(className: :currentClassName, methodName: method:name);
		if({ mergeTarget:name != '' && :ancestorOverloaded(className: :currentClassName, methodName: method:name) }, {
			:addError(line: method:line, msg: :errText:errCannotOverrideOverload(method: method:name));
		});
		if({ :currentMethodIsMerge && mergeTarget:name == '' }, {
			:addError(line: method:line, msg: :errText:errMergeNoParent(method: method:name, className: :currentClassName));
		});
		method:params:each(action: local Function(Parameter is p){
			if({ p:paramType:name == :names:selfFieldMarker() }, {
				local String is ft: :fieldTypes:getString(key: p:name, default: Primitive:ANY:value());
				p:paramType: :parseTypeNode(s: ft);
				:unassignedFields:remove(key: p:name);
			});
			if({ p:hasDefault }, {
				local String is pTypeStr: :formatVarTypeString(t: p:paramType);
				local String is defType: p:defaultExpr:resolvedType;
				if({ defType == '' }, {
					defType: :inferExpressionType(expr: p:defaultExpr, expected: pTypeStr);
				});
				if({ pTypeStr != '' && defType != '' && !:isAssignable(target: pTypeStr, source: defType) }, {
					:addError(line: method:line, msg: "Default value for parameter '" . p:name . "' in '" . :currentClassName . ":" . method:name . "' has type '" . :displayType(t: defType) . "', expected '" . :displayType(t: pTypeStr) . "'.");
				});
			});
		});
		:currentMethodReturnType: :resolveReturnType(t: method:memberType);
		if({ !:namespaceEquals(segs: :currentClassDef:namespaceSegments(), want: ['base', 'sys', 'thread']) && :containsThreadScopeType(t: :currentMethodReturnType) }, {
			:addError(line: method:line, msg: "Method '" . :currentClassName . ":" . method:name . "' cannot return 'ThreadScope'; 'ThreadScope' is lexically scoped to 'ThreadScope:open' and cannot escape.");
		});
		if({ :currentMethodReturnType == '' || :isVoid(t: :currentMethodReturnType) }, {
			if({ method:name == ContractMethod:EVALUATE:value() || method:name == ContractMethod:ITERATION:value() }, {
				:currentMethodReturnType: 'Boolean';
				method:memberType: Type:init(name: 'Boolean');
			});
		});
		:localVars: Map:init();

		method:params:each(action: local Function(Parameter is p){
			:localVars:set(key: p:name, value: :formatVarTypeString(t: p:paramType));
		});

		method:body:each(action: local Function(Statement is stmt){
			:checkStatement(stmt: stmt);
		});

		if({ !:isVoid(t: :currentMethodReturnType) && method:body:length() > 0 }, {
			local Statement is lastStmt: method:body:get(index: method:body:length() - 1);
			match(on: lastStmt, when: [
				Statement:Expr: local Function(Expression is exprStmt){
					local String is lastT: exprStmt:resolvedType;
					if({ lastT != '' && !:isVoid(t: lastT) && !:isAssignable(target: :currentMethodReturnType, source: lastT) }, {
						:addError(line: lastStmt:line, msg: "Implicit return value in '" . :currentClassName . ":" . method:name . "' has type '" . :displayType(t: lastT) . "', expected '" . :displayType(t: :currentMethodReturnType) . "'.");
					});
				},
				else: {}
			]);
		});

		if({ :currentMethodIsMerge && !:forwardSeen && method:body:length() > 0 }, {
			:addError(line: method:line, msg: :errText:errMergeMustForward(method: method:name, className: :currentClassName));
		});
		:currentMethodTypeParams: Map:init();
		:currentMethodIsMerge: false;
		:currentMethodName: '';
	}

	## Finds the nearest parent implementation of a method (merge target),
	## walking base classes in declaration order.
	##
	## @param className: Child class whose parents are searched.
	## @param methodName: Method name to locate.
	## @return: The parent member, or an empty-named one when absent.
	Function of Member is findFirstSuperMethod(String is className, String is methodName){
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			return Member:init(kind: MemberKind:FIELD);
		});
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ res:name == '' }, {
				local Member is m: :lookupAnyMember(className: baseName, methodName: methodName);
				if({ m:kind == MemberKind:METHOD }, {
					res: m;
				});
			});
		});
		return res;
	}

	## Collects every ancestor class declaring a concrete implementation of a
	## method, deduplicating shared bases by name.
	##
	## @param className: Class whose ancestors are searched.
	## @param methodName: Method name to collect.
	## @param seen: Dedup map of visited class names.
	## @param acc: Output array of declaring class names.
	Function is collectConcreteDeclarers(String is className, String is methodName, Map of String to String is seen, Array of String is acc){
		if({ seen:has(key: className) }, {
			return;
		});
		seen:set(key: className, value: 'true');
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			return;
		});
		cls:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:METHOD && m:name == methodName && m:body:length() > 0 }, {
				local Boolean is present: false;
				acc:each(action: local Function(String is n){
					if({ !present && n == className }, {
						present: true;
					});
				});
				if({ !present }, {
					acc:add(item: className);
				});
			});
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			:collectConcreteDeclarers(className: baseName, methodName: methodName, seen: seen, acc: acc);
		});
	}

	## Finds a member of any kind with the given name across all ancestors.
	##
	## @param className: Starting class whose bases are searched.
	## @param memberName: Member name to locate.
	## @return: The ancestor member, or an empty-named one when absent.
	Function of Member is findAncestorMember(String is className, String is memberName){
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			return Member:init(kind: MemberKind:FIELD);
		});
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ res:name == '' }, {
				local ClassInfo is anc: :findClass(name: baseName);
				if({ anc:name != '' }, {
					anc:members:each(action: local Function(Member is m){
						if({ res:name == '' && m:name == memberName }, {
							res: m;
						});
					});
				});
			});
		});
		if({ res:name == '' }, {
			cls:baseClasses:each(action: local Function(String is baseName){
				if({ res:name == '' }, {
					res: :findAncestorMember(className: baseName, memberName: memberName);
				});
			});
		});
		return res;
	}

	## Finds the nearest ancestor class declaring a member with the name.
	##
	## @param className: Starting class whose bases are searched.
	## @param memberName: Member name to locate.
	## @return: The declaring ancestor\'s name, or '' when absent.
	Function of String is findMemberOwnerClass(String is className, String is memberName){
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			return '';
		});
		local String is owner: '';
		cls:members:each(action: local Function(Member is m){
			if({ owner == '' && m:name == memberName }, {
				owner: cls:name;
			});
		});
		if({ owner != '' }, {
			return owner;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ owner == '' }, {
				owner: :findMemberOwnerClass(className: baseName, memberName: memberName);
			});
		});
		return owner;
	}

	## Finds the nearest class (self, then ancestors) declaring a HELD
	## FIELD with the name. The class-name prefix
	## reaches exactly these members.
	##
	## @param className: Starting class whose bases are searched.
	## @param memberName: Member name to locate.
	## @return: The declaring class\'s name, or '' when absent.
	Function of String is findHeldOwnerClass(String is className, String is memberName){
		if({ className == '' || className == Primitive:ANY:value() }, {
			return '';
		});
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			return '';
		});
		local String is owner: '';
		cls:members:each(action: local Function(Member is m){
			if({ owner == '' && m:name == memberName && m:kind == MemberKind:FIELD && m:hasModifier(kw: Keyword:HELD) }, {
				owner: cls:name;
			});
		});
		if({ owner != '' }, {
			return owner;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ owner == '' }, {
				owner: :findHeldOwnerClass(className: baseName, memberName: memberName);
			});
		});
		return owner;
	}

	## Finds the nearest HELD FIELD declaration (own, then ancestors).
	##
	## @param className: Starting class whose bases are searched.
	## @param memberName: Member name to locate.
	## @return: The member, or an empty-named one when absent.
	Function of Member is findHeldMember(String is className, String is memberName){
		local String is owner: :findHeldOwnerClass(className: className, memberName: memberName);
		if({ owner == '' }, {
			return Member:init(kind: MemberKind:FIELD);
		});
		local ClassInfo is cls: :findClass(name: owner);
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:members:each(action: local Function(Member is m){
			if({ res:name == '' && m:name == memberName && m:kind == MemberKind:FIELD && m:hasModifier(kw: Keyword:HELD) }, {
				res: m;
			});
		});
		return res;
	}

	## Finds the nearest HELD FUNCTION declaration (own, then ancestors).
	##
	## @param className: Starting class whose bases are searched.
	## @param methodName: Held function name to locate.
	## @return: The member, or an empty-named one when absent.
	Function of Member is findHeldMethod(String is className, String is methodName){
		if({ className == '' || className == Primitive:ANY:value() }, {
			return Member:init(kind: MemberKind:METHOD);
		});
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			return Member:init(kind: MemberKind:METHOD);
		});
		local Member is res: Member:init(kind: MemberKind:METHOD);
		cls:members:each(action: local Function(Member is m){
			if({ res:name == '' && m:name == methodName && m:kind == MemberKind:METHOD && m:hasModifier(kw: Keyword:HELD) }, {
				res: m;
			});
		});
		if({ res:name != '' }, {
			return res;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ res:name == '' }, {
				res: :findHeldMethod(className: baseName, methodName: methodName);
			});
		});
		return res;
	}

	## Finds the nearest class declaring a HELD FUNCTION with the name
	## (nearest declaration wins).
	##
	## @param className: Starting class whose bases are searched.
	## @param methodName: Held function name to locate.
	## @return: The declaring class\'s name, or '' when absent.
	Function of String is findHeldMethodOwner(String is className, String is methodName){
		if({ className == '' || className == Primitive:ANY:value() }, {
			return '';
		});
		local ClassInfo is cls: :findClass(name: className);
		if({ cls:name == '' }, {
			return '';
		});
		local String is owner: '';
		cls:members:each(action: local Function(Member is m){
			if({ owner == '' && m:name == methodName && m:kind == MemberKind:METHOD && m:hasModifier(kw: Keyword:HELD) }, {
				owner: cls:name;
			});
		});
		if({ owner != '' }, {
			return owner;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ owner == '' }, {
				owner: :findHeldMethodOwner(className: baseName, methodName: methodName);
			});
		});
		return owner;
	}

	## Looks up a held field's static type through the class lattice.
	##
	## @param className: Starting class name.
	## @param fieldName: Held field name.
	## @return: The field type name, or '' when absent.
	Function of String is lookupHeldFieldType(String is className, String is fieldName){
		local Member is m: :findHeldMember(className: className, memberName: fieldName);
		if({ m:name == '' || m:kind != MemberKind:FIELD }, {
			return '';
		});
		return :formatTypeString(t: m:memberType);
	}

	## Validates visibility for a member access: `local` restricts to the
	## declaring class, `contained` to it and its subclasses.
	##
	## @param ownerClass: Declaring class (empty = none, allowed).
	## @param member: The resolved member.
	## @param memberName: Member name for diagnostics.
	Function is checkMemberVisibility(String is ownerClass, Member is member, String is memberName){
		if({ ownerClass == '' || ownerClass == 'Any' || memberName == ContractMethod:INIT:value() }, {
			return;
		});
		if({ member:hasModifier(kw: Keyword:LOCAL) }, {
			if({ :currentClassName != ownerClass }, {
				local String is msg: :errText:errMemberLocal(member: memberName, ownerClass: ownerClass, currentClass: :currentClassName);
				:addError(line: :currentLine, msg: msg);
			});
		}, {
			if({ member:hasModifier(kw: Keyword:CONTAINED) }, {
				if({ !:isSubclassOf(subName: :currentClassName, baseName: ownerClass) }, {
					local String is msg: :errText:errMemberContained(member: memberName, ownerClass: ownerClass, currentClass: :currentClassName);
					:addError(line: :currentLine, msg: msg);
				});
			});
		});
	}

	## Validates that `replace` and `merge` members actually target an
	## ancestor declaration of the same kind, and that they carry no
	## visibility modifiers. Root-contract members are exempt.
	##
	## @param classDef: Class to validate.
	Function is checkShadowTargets(ClassInfo is classDef){
		classDef:members:each(action: local Function(Member is m){
			local Boolean is hasReplace: m:hasModifier(kw: Keyword:REPLACE);
			local Boolean is hasMerge: m:hasModifier(kw: Keyword:MERGE);
			if({ hasReplace || hasMerge }, {
				if({ m:hasModifier(kw: Keyword:LOCAL) || m:hasModifier(kw: Keyword:CONTAINED) }, {
					local String is msg: 'Member \'' . m:name . '\' in class \'' . classDef:name . '\' combines \'replace\'/\'merge\' with a visibility modifier; replace and merge members are public by definition.';
					:addError(line: m:line, msg: msg);
					return;
				});
			});
			if({ !hasReplace && !hasMerge }, {
				return;
			});
			local String is name: m:name;
			if({ name == ContractMethod:INIT:value() || name == ContractMethod:USING:value() || name == ContractMethod:TO_STRING:value() }, {
				return;
			});
			if({ :findMemberOwnerClass(className: classDef:name, memberName: name) == Primitive:ANY:value() }, {
				# Root-contract member: Any declares it public, so overriding
				# is always legitimate.
				return;
			});
			local Member is anc: :findAncestorMember(className: classDef:name, memberName: name);
			if({ anc:name == '' }, {
				local String is what: if({ hasMerge }, { 'merge' }, { 'replace' });
				local String is msg: 'Member \'' . name . '\' in class \'' . classDef:name . '\' declares \'' . what . '\' but no ancestor declares a member with that name.';
				:addError(line: m:line, msg: msg);
			}, {
				if({ anc:hasModifier(kw: Keyword:LOCAL) || anc:hasModifier(kw: Keyword:CONTAINED) }, {
					local String is vis: if({ anc:hasModifier(kw: Keyword:LOCAL) }, { 'local' }, { 'contained' });
					local String is msg: 'Member \'' . name . '\' in class \'' . classDef:name . '\' targets a ' . vis . ' ancestor member; ' . vis . ' members cannot be replaced or merged.';
					:addError(line: m:line, msg: msg);
				}, {
					if({ anc:kind != m:kind }, {
						local String is msg: 'Member \'' . name . '\' in class \'' . classDef:name . '\' is a ' . m:kind:value() . ' but the ancestor member it targets is a ' . anc:kind:value() . '.';
						:addError(line: m:line, msg: msg);
					});
				});
			});
		});
	}

	## Validates a class's held members: `held`
	## composes with the visibility modifiers but not with `replace`/
	## `merge` (held members are single-copy and cannot be overridden);
	## held fields require initializers (the lazy once-pattern constructs
	## them); held functions are not yet supported.
	##
	## @param classDef: Class to validate.
	Function is checkHeldMembers(ClassInfo is classDef){
		classDef:members:each(action: local Function(Member is m){
			if({ !m:hasModifier(kw: Keyword:HELD) }, {
				# The resolution hook spelling is reserved: a plain method
				# named 'resolveHeld' would silently never hook
				# .
				if({ m:kind == MemberKind:METHOD && m:name == ContractMethod:RESOLVE_HELD:value() }, {
					:addError(line: m:line, msg: 'The resolution hook \'' . m:name . '\' in class \'' . classDef:name . '\' must be held: declare it \'held Function of Any is resolveHeld(String is name)\'.');
				});
				return;
			});
			if({ m:hasModifier(kw: Keyword:REPLACE) || m:hasModifier(kw: Keyword:MERGE) }, {
				:addError(line: m:line, msg: :errText:errHeldCombinesReplaceMerge(member: m:name, className: classDef:name));
				return;
			});
			if({ m:name == MetadataField:USING:value() || m:name == MetadataField:NAMESPACE:value() || m:name == MetadataField:CASTABLE:value() }, {
				:addError(line: m:line, msg: 'Loader directive \'' . m:name . '\' in class \'' . classDef:name . '\' cannot be \'held\'.');
				return;
			});
			if({ m:kind == MemberKind:CLASS }, {
				:addError(line: m:line, msg: 'Nested class \'' . m:name . '\' in class \'' . classDef:name . '\' cannot be \'held\'.');
				return;
			});
			if({ m:kind == MemberKind:METHOD }, {
				# Held functions: class-scoped, receiver-free. They are not
				# root-contract members (no vtable involvement) and do not
				# overload — one name, one signature, one symbol.
				if({ m:name == ContractMethod:INIT:value() || m:name == ContractMethod:EVALUATE:value() || m:name == ContractMethod:ITERATION:value() || m:name == ContractMethod:TO_STRING:value() }, {
					:addError(line: m:line, msg: 'Held function \'' . m:name . '\' in class \'' . classDef:name . '\' cannot be a root-contract member; held functions take no receiver and never dispatch dynamically.');
					return;
				});
				# The resolution hook: exactly
				# 'held Function of <T> is resolveHeld(String is name,
				# Function of <T> is missing)' — the SECOND argument is the
				# runtime-provided safe failure branch, and it must return
				# the SAME type the resolver searches for. Never Null: the
				# default branch panics with context; the resolver invokes
				# it when the name cannot be resolved. A hook-resolved name
				# compiles for any spelling, so the failure path is part of
				# the contract, not an afterthought. The non-held spelling
				# is a pointed error too (a plain method by that name would
				# silently never hook).
				if({ m:name == ContractMethod:RESOLVE_HELD:value() }, {
					# The resolver's return: a method's memberType is the full
					# Function type with the return in params[0] (the direct
					# spelling 'HE is resolveHeld(...)' is also accepted).
					local String is resRetName: m:memberType:name;
					if({ m:memberType:name == 'Function' && m:memberType:params:length() > 0 }, {
						local Type is resRetT: m:memberType:params:get(index: 0);
						resRetName: resRetT:name;
					});
					local Boolean is sigOk: false;
					if({ m:params:length() == 2 }, {
						local Parameter is nameP: m:params:get(index: 0);
						local Parameter is missP: m:params:get(index: 1);
						local Type is missT: missP:paramType;
						local Type is missRet: missT:params:get(index: 0);
						if({ nameP:paramType:name == Primitive:STRING:value() && missT:name == 'Function' && missT:params:length() > 0 }, {
							sigOk: missRet:name == resRetName && resRetName != '' && !:isVoid(t: resRetName);
						});
					});
					if({ !sigOk }, {
						:addError(line: m:line, msg: 'The resolution hook \'' . m:name . '\' in class \'' . classDef:name . '\' must be declared exactly \'held Function of <T> is resolveHeld(String is name, Function of <T> is missing)\'; the missing branch is provided by the runtime and must return the same type the resolver searches for.');
					});
				});
				local Boolean is dupHeld: false;
				classDef:members:each(action: local Function(Member is g){
					if({ g != m && g:kind == MemberKind:METHOD && g:name == m:name && g:hasModifier(kw: Keyword:HELD) }, {
						dupHeld: true;
					});
				});
				if({ dupHeld }, {
					:addError(line: m:line, msg: :errText:errHeldDuplicate(member: m:name));
				});
				return;
			});
			if({ !m:hasInit }, {
				:addError(line: m:line, msg: :errText:errHeldFieldRequiresInitializer(field: m:name, className: classDef:name));
				return;
			});
		});
	}

	## Rejects ambiguous inherited implementations: two distinct ancestors
	## with concrete bodies for the same method, where the class does not
	## declare it itself. Abstract declarations compose; diamond bases
	## deduplicate by name, and only maximal declarers compete.
	##
	## @param classDef: Class to validate.
	Function is checkMethodConflicts(ClassInfo is classDef){
		local Map of String to String is seenMethods: Map:init();
		classDef:baseClasses:each(action: local Function(String is baseName){
			local ClassInfo is anc: :findClass(name: baseName);
			if({ anc:name != '' }, {
				anc:members:each(action: local Function(Member is m){
					if({ m:kind == MemberKind:METHOD }, {
						seenMethods:set(key: m:name, value: 'true');
					});
				});
			});
		});
		local Array of String is names: seenMethods:keys();
		names:each(action: local Function(String is mName){
			local Boolean is declaredLocally: false;
			classDef:members:each(action: local Function(Member is m){
				if({ m:kind == MemberKind:METHOD && m:name == mName }, {
					declaredLocally: true;
				});
			});
			if({ !declaredLocally }, {
				local Map of String to String is seen: Map:init();
				local Array of String is declarers: [];
				classDef:baseClasses:each(action: local Function(String is baseName){
					:collectConcreteDeclarers(className: baseName, methodName: mName, seen: seen, acc: declarers);
				});
				local Array of String is maximal: [];
				declarers:each(action: local Function(String is d){
					local Boolean is isSubsumed: false;
					declarers:each(action: local Function(String is other){
						if({ !isSubsumed && other != d && :isSubclassOf(subName: other, baseName: d) }, {
							isSubsumed: true;
						});
					});
					if({ !isSubsumed }, {
						maximal:add(item: d);
					});
				});
				if({ maximal:length() >= 2 }, {
					local String is msg: :errText:errConflictingInheritedMethods(className: classDef:name, method: mName, classA: maximal:get(index: 0), classB: maximal:get(index: 1));
					:addError(line: classDef:line, msg: msg);
				});
			});
		});
	}

	## Validates inheritance, interface contracts, and override signatures.
	##
	## @param classDef: Class to inspect.
	Function is checkInheritance(ClassInfo is classDef){
		:currentSourceFile: classDef:sourceFile;
		local Boolean is hasInit: false;
		classDef:members:each(action: local Function(Member is m){
			if({ m:name == ContractMethod:INIT:value() }, {
				hasInit: true;
			});
		});

		classDef:baseClasses:each(action: local Function(String is baseName){
			local ClassInfo is parent: :findClass(name: baseName);
			# The outer-link relation is an ACCESS scope, not an is-a
			# contract: the enclosing class's members surface to the inner
			# through the walk, and the inner's own same-named members
			# SHADOW them silently — no abstract obligation, no replace
			# requirement, no signature merge (IV.2).
			if({ parent:name == baseName && !(classDef:outerName != '' && (classDef:outerName == baseName || classDef:outerName:contains(needle: ':' . baseName))) }, {
				# 1. Enforce abstract member implementation on concrete classes
				# with init. The implicit root Any is exempt: its members carry
				# concrete defaults. (The outer-link relation is exempt by the
				# gate above — the inner-class link is an access scope.)
				if({ hasInit && baseName != Primitive:ANY:value() }, {
					parent:members:each(action: local Function(Member is parentM){
						local Boolean is isAbstract: (parentM:kind == MemberKind:FIELD && !parentM:hasInit) ||
							(parentM:kind == MemberKind:METHOD && parentM:body:length() == 0);
						if({ isAbstract }, {
							local Boolean is isImplemented: false;
							local Int is mIdx: 0;
							while({ !isImplemented && mIdx < classDef:members:length() }, {
								local Member is subM: classDef:members:get(index: mIdx);
								mIdx: mIdx + 1;
								if({ subM:name == parentM:name }, {
									if({ (subM:kind == MemberKind:METHOD && subM:body:length() > 0) || (subM:kind == MemberKind:FIELD && subM:hasInit) }, {
										isImplemented: true;
									});
								});
							});
							if({ !isImplemented }, {
								local String is msg: :errText:errUnimplementedAbstract(className: classDef:name, member: parentM:name, parentClass: baseName);
								:addError(line: classDef:line, msg: msg);
							});
						});
					});
				});

				# 2. Strict replace check & method signature matching on overrides
				classDef:members:each(action: local Function(Member is subM){
					# the nested-class members are declarations of
					# types, not overrides of the ancestor's surface.
					if({ subM:kind == MemberKind:CLASS }, {
						return;
					});
					# Declarative metadata (namespace/using/group) is per-class
					# by design and never participates in override matching.
					if({ subM:name == MetadataField:NAMESPACE:value() || subM:name == MetadataField:USING:value() || subM:name == MetadataField:CASTABLE:value() }, {
						return;
					});
					parent:members:each(action: local Function(Member is parentM){
						if({ parentM:kind == MemberKind:CLASS }, {
							return;
						});
						if({ subM:name == parentM:name }, {
							if({ parentM:hasModifier(kw: Keyword:LOCAL) || parentM:hasModifier(kw: Keyword:CONTAINED) }, {
								local String is vis: if({ parentM:hasModifier(kw: Keyword:LOCAL) }, { 'local' }, { 'contained' });
								local String is msg: 'Member \'' . subM:name . '\' is ' . vis . ' in ancestor \'' . baseName . '\' and cannot be replaced or merged.';
								:addError(line: subM:line, msg: msg);
							});
							local Boolean is hasReplace: subM:hasModifier(kw: Keyword:REPLACE);
							local Boolean is hasMerge: subM:hasModifier(kw: Keyword:MERGE);
							if({ hasMerge }, {
								if({ subM:kind == MemberKind:METHOD }, {
									if({ parentM:kind == MemberKind:METHOD && parentM:body:length() == 0 }, {
										local String is msg: 'Cannot merge method \'' . subM:name . '\' in class \'' . classDef:name . '\' with abstract method from \'' . baseName . '\'.';
										:addError(line: subM:line, msg: msg);
									});
								}, {
									:applyMerge(classDef: classDef, subM: subM, parentM: parentM, baseName: baseName);
								});
							}, {
								if({ !hasReplace }, {
									local String is msg: 'Member \'' . subM:name . '\' in class \'' . classDef:name . '\' overrides ancestor member from \'' . baseName . '\', but is missing \'replace\' modifier.';
									:addError(line: subM:line, msg: msg);
								});
							});

							if({ subM:kind == MemberKind:METHOD && parentM:kind == MemberKind:METHOD }, {
								# Root-contract carve-out: init/using/toString declared
								# in Any are name reservations; per-class signatures
								# are legitimate. Override must still carry replace.
								if({ baseName == Primitive:ANY:value() }, {
									if({ !subM:hasModifier(kw: Keyword:REPLACE) && !subM:hasModifier(kw: Keyword:MERGE) }, {
										local String is msg: 'Member \'' . subM:name . '\' in class \'' . classDef:name . '\' overrides root-contract member from \'Any\', but is missing \'replace\' modifier.';
										:addError(line: subM:line, msg: msg);
									});
									return;
								});
								# constructors are per-class —
								# they are not polymorphic. An init never enters the
								# ancestor signature/return compatibility checks at all
								# (inner classes inherit their enclosing class, whose
								# init differs by design — and whose parameter list may
								# be empty, so the param-merge below cannot run on it).
								if({ subM:name == 'init' }, {
									return;
								});
								if({ subM:params:length() != parentM:params:length() }, {
									local String is msg: 'Method \'' . subM:name . '\' in class \'' . classDef:name . '\' parameter count mismatch with ancestor in \'' . baseName . '\'.';
									:addError(line: subM:line, msg: msg);
								}, {
									local Int is pIdx: 0;
									subM:params:each(action: local Function(Parameter is subP){
										local Parameter is parentP: parentM:params:get(index: pIdx);
										if({ subP:paramType:name == 'Any' || subP:paramType:name == '' }, {
											subP:paramType: parentP:paramType;
										});
										pIdx: pIdx + 1;
									});
								});
								local String is subRet: :resolveReturnType(t: subM:memberType);
								local String is parentRet: :resolveReturnType(t: parentM:memberType);
								if({ subM:memberType:name == '' || :isVoid(t: subM:memberType:name) }, {
									subM:memberType: parentM:memberType;
								}, {
									if({ !:isAssignable(target: subRet, source: parentRet) }, {
										local String is msg: 'Method \'' . subM:name . '\' in class \'' . classDef:name . '\' return type \'' . subRet . '\' does not match ancestor return type \'' . parentRet . '\'.';
										:addError(line: subM:line, msg: msg);
									});
								});
							});
						});
					});
				});
			});
		});
		:checkMethodConflicts(classDef: classDef);
		:checkShadowTargets(classDef: classDef);
		:checkHeldMembers(classDef: classDef);
	}

	## Folds a `merge` field override into its parent array literal: the
	## child initializer is rewritten to parent items followed by child
	## items, so the merge ceases to exist before code generation.
	##
	## @param classDef: Declaring class.
	## @param subM: Child field member carrying `merge`.
	## @param parentM: Ancestor member being merged with.
	## @param baseName: Ancestor class name for diagnostics.
	Function is applyMerge(ClassInfo is classDef, Member is subM, Member is parentM, String is baseName){
		if({ subM:kind != MemberKind:FIELD }, {
			:addError(line: subM:line, msg: '\'merge\' is only valid on fields; member \'' . subM:name . '\' in class \'' . classDef:name . '\' is not a field.');
			return;
		});
		local String is typeName: subM:memberType:name;
		if({ !typeName:startsWith(prefix: 'Array') }, {
			:addError(line: subM:line, msg: '\'merge\' requires an Array field; \'' . typeName . '\' is not mergeable.');
			return;
		});
		if({ !parentM:hasInit }, {
			return;
		});
		local Expression is parentInit: parentM:initExpr;
		local Array of Expression is parentItems: [];
		local Boolean is parentIsArray: false;
		match(on: parentInit, when: [
			Expression:ArrayLit: local Function(Array of Expression is items){
				parentIsArray: true;
				parentItems: items;
			}
		], default: {});
		if({ !parentIsArray }, {
			:addError(line: subM:line, msg: '\'merge\' requires a constant array literal in parent \'' . baseName . '.' . parentM:name . '.');
			return;
		});
		if({ !subM:hasInit }, {
			return;
		});
		local Expression is childInit: subM:initExpr;
		local Array of Expression is childItems: [];
		local Boolean is childIsArray: false;
		match(on: childInit, when: [
			Expression:ArrayLit: local Function(Array of Expression is items){
				childIsArray: true;
				childItems: items;
			}
		], default: {});
		if({ !childIsArray }, {
			:addError(line: subM:line, msg: '\'merge\' requires a constant array literal initializer on \'' . classDef:name . '.' . subM:name . '.');
			return;
		});
		local Array of Expression is combined: [];
		parentItems:each(action: local Function(Expression is item){
			combined:add(item: item);
		});
		childItems:each(action: local Function(Expression is item){
			combined:add(item: item);
		});
		local Expression is folded: Expression:ArrayLit(items: combined);
		folded:setLine(line: childInit:line);
		subM:initExpr: folded;
	}

	## Populates `fieldTypes` for a class including inherited fields.
	##
	## @param classDef: Class to collect from.
	Function is collectClassFieldTypes(ClassInfo is classDef){
		classDef:baseClasses:each(action: local Function(String is baseName){
			local ClassInfo is parent: :findClass(name: baseName);
			if({ parent:name != '' }, {
				:collectClassFieldTypes(classDef: parent);
			});
		});
		classDef:members:each(action: local Function(Member is m){
			# Metadata members carry no type and are not fields of the
			# generated struct; HELD members are class-scoped
			#  — an instance reference reaches exactly the
			# instance members, so held names stay out of fieldTypes.
			if({ m:kind == MemberKind:FIELD && m:memberType:name != '' && !m:hasModifier(kw: Keyword:HELD) }, {
				:fieldTypes:set(key: m:name, value: :formatVarTypeString(t: m:memberType));
			});
		});
	}

	## Validates all members of a class definition.
	##
	## @param classDef: Class definition.
	## The SpecErrorHandler boundary is typed: every handler must return
	## Boolean (the unwind walk consumes the result as handled), take
	## exactly one parameter, and that parameter must be the error
	## currency — bare `SpecError` (the catch-all) or `SpecError of <kind
	## enum>` (typed dispatch, plan 1.4). A class may declare several
	## handlers: at most one catch-all and no duplicate kind enums; the
	## emitter generates a dispatcher that routes by the raised error's
	## kind, most-specific (kinded) first, and leaves non-matching kinds
	## unhandled (re-raise) unless the catch-all claims them.
	Function is checkSpecErrorHandlerGroup(ClassInfo is classDef){
		local Array of Member is handlers: [];
		classDef:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:METHOD && m:name == 'SpecErrorHandler' && !m:hasModifier(kw: Keyword:HELD) }, {
				handlers:add(item: m);
			});
		});
		if({ handlers:length() == 0 }, { return; });
		local Int is catchAllCount: 0;
		local Array of String is seenKinds: [];
		local Int is hi: 0;
		while({ hi < handlers:length() }, {
			local Member is m: handlers:get(index: hi);
			:currentLine: m:line;
			if({ m:sourceFile != '' }, {
				:currentSourceFile: m:sourceFile;
			});
			if({ m:params:length() != 1 }, {
				:addError(line: m:line, msg: 'SpecErrorHandler must take exactly one parameter; found ' . (m:params:length() as String) . '.');
			}, {
				local Parameter is p: m:params:get(index: 0);
				local String is pTy: :formatVarTypeString(t: p:paramType);
				# The currency parameter normalizes to 'SpecError' (bare, the
				# catch-all), 'SpecError:Any' (same), or 'SpecError:<KindEnum>'
				# ('SpecError of K' source spelling); accept all renderings. Enum
				# recognition goes through the class model (every enum desugars to
				# an Enum-rooted class) — allEnumNames is vestigial and stays empty.
				local Boolean is paramOk: false;
				local String is kindTy: '';
				if({ pTy == 'SpecError' || pTy == 'SpecError:Any' }, {
					paramOk: true;
					catchAllCount: catchAllCount + 1;
				}, {
					if({ pTy:startsWith(prefix: 'SpecError:') }, {
						kindTy: pTy:substring(start: 10, end: pTy:length());
					}, {
						if({ pTy:startsWith(prefix: 'SpecError of ') }, {
							kindTy: pTy:substring(start: 12, end: pTy:length());
						});
					});
					local ClassInfo is kindCls: :findClass(name: kindTy);
					paramOk: kindCls:name != '' && kindCls:baseClass == :names:enumHeader();
				});
				if({ !paramOk }, {
					:addError(line: m:line, msg: 'SpecErrorHandler parameter must be SpecError or SpecError of <kind enum>; found \'' . pTy . '\'.');
				}, {
					if({ kindTy != '' }, {
						local Boolean is dup: false;
						local Int is si: 0;
						while({ si < seenKinds:length() }, {
							if({ seenKinds:get(index: si, default: '') == kindTy }, {
								dup: true;
							});
							si++;
						});
						if({ dup }, {
							:addError(line: m:line, msg: 'Duplicate SpecErrorHandler kind \'' . kindTy . '\'; a class declares each kind at most once.');
						}, {
							seenKinds:add(item: kindTy);
						});
					});
				});
			});
			local String is retTy: :resolveReturnType(t: m:memberType);
			if({ retTy != 'Boolean' }, {
				:addError(line: m:line, msg: 'SpecErrorHandler must return Boolean; found \'' . retTy . '\'.');
			});
			hi++;
		});
		if({ catchAllCount > 1 }, {
			local Member is second: handlers:get(index: 1);
			:currentLine: second:line;
			:addError(line: second:line, msg: 'A class may declare at most one catch-all SpecErrorHandler; found ' . (catchAllCount as String) . '.');
		});
	}

	Function is checkClass(ClassInfo is classDef){
		:currentClassName: classDef:name;
		:currentClassDef: classDef;
		:currentSourceFile: classDef:sourceFile;
		:fieldTypes: Map:init();
		:collectClassFieldTypes(classDef: classDef);

		classDef:members:each(action: local Function(Member is m){
			match(on: m:kind, when: [
				MemberKind:FIELD: {
					:currentLine: m:line;
					if({ m:sourceFile != '' }, {
						:currentSourceFile: m:sourceFile;
					});
					# Declarative metadata properties (using, namespace, group)
					# are loader directives, not checked code: their
					# initializers may reference classes the using itself
					# loads, so type validation is skipped. The as-import's
					# synthesized hidden field (_import_X, §10) is
					# the as-form's own materialization — its type reference
					# rides the as-form, not the plain type import.
					if({ !m:name:startsWith(prefix: '_import_') }, {
						:validateTypeAccess(t: m:memberType, line: m:line);
					});
					if({ m:name != MetadataField:USING:value() && m:name != MetadataField:NAMESPACE:value() && m:name != MetadataField:CASTABLE:value() && !m:name:startsWith(prefix: '_import_') }, {
						local String is declaredType: :formatVarTypeString(t: m:memberType);
						if({ !:namespaceEquals(segs: :currentClassDef:namespaceSegments(), want: ['base', 'sys', 'thread']) && :containsThreadScopeType(t: declaredType) }, {
							:addError(line: m:line, msg: "Cannot store 'ThreadScope' in field '" . classDef:name . ":" . m:name . "'; 'ThreadScope' is lexically scoped to 'ThreadScope:open' and cannot escape.");
						});
						if({ m:hasInit }, {
							# Bidirectional: the declared type flows in.
							# A HELD initializer has no instance scope
							# : the flag rejects self, instance fields,
							# and implicit-self calls inside it.
							local Boolean is savedHeldInit: :inHeldInit;
							if({ m:hasModifier(kw: Keyword:HELD) }, {
								:inHeldInit: true;
							});
							local String is initType: :inferExpressionType(expr: m:initExpr, expected: declaredType);
							:inHeldInit: savedHeldInit;
							if({ !:isAssignable(target: declaredType, source: initType) }, {
								local String is msg: 'Type mismatch in field \'' . classDef:name . ':' . m:name . '\': cannot assign \'' . initType . '\' to \'' . declaredType . '\'.';
								:addError(line: m:line, msg: msg);
							});
						});
					});
				},
				else: {}
			]);
		});

		:checkSpecErrorHandlerGroup(classDef: classDef);

		classDef:members:each(action: local Function(Member is m){
			match(on: m:kind, when: [
				MemberKind:METHOD: {
					:unassignedFields: Map:init();
					if({ m:name == ContractMethod:INIT:value() }, {
						classDef:members:each(action: local Function(Member is fm){
							if({ fm:kind == MemberKind:FIELD && !fm:hasInit && fm:name != ContractMethod:USING:value() && !fm:hasModifier(kw: Keyword:HELD) }, {
								:unassignedFields:set(key: fm:name, value: 'true');
							});
						});
					});
					# Held functions: no instance context
					# — fieldTypes cleared, so bare instance-field names do
					# not resolve; the no-instance checks reject self.
					local Boolean is savedHeldFn: :inHeldFunction;
					local Map of String to String is savedFnFields: :fieldTypes;
					if({ m:hasModifier(kw: Keyword:HELD) }, {
						:inHeldFunction: true;
						:fieldTypes: Map:init();
					});
					:checkMethod(method: m);
					:inHeldFunction: savedHeldFn;
					:fieldTypes: savedFnFields;
					:unassignedFields: Map:init();
				},
				MemberKind:CLASS: {
					local String is savedClass: :currentClassName;
					local ClassInfo is savedClassDef: :currentClassDef;
					local Map of String to String is savedFields: Map:init();
					local Array of String is fKeys: :fieldTypes:keys();
					fKeys:each(action: local Function(String is k){
						savedFields:set(key: k, value: :fieldTypes:getString(key: k, default: ''));
					});
					local Map of String to String is savedUnassigned: Map:init();
					local Array of String is uKeys: :unassignedFields:keys();
					uKeys:each(action: local Function(String is k){
						savedUnassigned:set(key: k, value: :unassignedFields:getString(key: k, default: ''));
					});

					:checkClass(classDef: m:nestedClass);

					:currentClassName: savedClass;
					:currentClassDef: savedClassDef;
					:fieldTypes: savedFields;
					:unassignedFields: savedUnassigned;
				},
				else: {}
			]);
		});
	}

	## Collects nested class definitions from a statement tree.
	##
	## @param stmt: The statement to walk.
	## @param acc: Output array.
	Function is collectClassesFromStatement(Statement is stmt, Array of ClassInfo is acc){
		match(on: stmt, when: [
			Statement:ClassDecl: local Function(ClassInfo is nestedClass){
				:collectClasses(c: nestedClass, acc: acc);
			},
			else: {}
		]);
	}

	## Collects a class and all nested definitions into the flat registry.
	##
	## @param c: The class to collect.
	## @param acc: Output array.
	Function is collectClasses(ClassInfo is c, Array of ClassInfo is acc){
		acc:add(item: c);
		c:members:each(action: local Function(Member is m){
			match(on: m:kind, when: [
				MemberKind:CLASS: {
					:collectClasses(c: m:nestedClass, acc: acc);
				},
				MemberKind:METHOD: {
					m:body:each(action: local Function(Statement is s){
						:collectClassesFromStatement(stmt: s, acc: acc);
					});
				},
				else: {}
			]);
		});
	}



	## Validates one class's instance imports (as-form using entries,
	## §2.1): the target must be a loaded non-enum class, and
	## v1 restricts the form to field-less classes with no constructor
	## arguments — the elided dispatch covers the whole known migration
	## surface; the synthetic-field form is deferred. At most one import
	## per class name (E2, E3).
	##
	## @param classDef: Class definition.
	Function is checkInstanceImports(ClassInfo is classDef){
		local Map of String to String is seen: Map:init();
		classDef:members:each(action: local Function(Member is m){
			if({ m:name != 'using' || !m:hasInit }, {
				return;
			});
			match(on: m:initExpr, when: [
				Expression:ArrayLit: local Function(Array of Expression is items){
					items:each(action: local Function(Expression is item){
						match(on: item, when: [
							Expression:ArrayLit: local Function(Array of Expression is segs){
								local String is asName: '';
								local String is asAlias: '';
								segs:each(action: local Function(Expression is seg){
									match(on: seg, when: [
										Expression:UsingAs: local Function(String is className, Array of NamedArg is args){
											asName: className;
											asAlias: seg:usingAsAlias;
										}
									], default: {});
								});
								if({ asName == '' }, {
									return;
								});
								local String is seenKey: if({ asAlias != '' }, { asAlias }, { asName });
								if({ seen:has(key: seenKey) }, {
									:addError(line: m:line, msg: :errText:errDuplicateInstanceImport(className: classDef:name, asName: seenKey));
									return;
								});
								seen:set(key: seenKey, value: 'true');
								local ClassInfo is target: :findClass(name: asName);
								if({ target:name == '' }, {
									return;
								});
								if({ target:baseClass == :names:enumHeader() }, {
									:addError(line: m:line, msg: :errText:errCannotInstanceImportEnum(asName: asName));
									return;
								});
								if({ target:typeParams:length() > 0 }, {
									:addError(line: m:line, msg: 'Generic classes cannot be instance-imported yet (§10).');
									return;
								});
							}
						], default: {});
					});
				}
			], default: {});
		});
	}

	## Collects the instance-import target names of one class.
	##
	## @param classDef: Class definition.
	## @return: The as-form target class names, declaration order.
	Function of Array of String is instanceImportTargets(ClassInfo is classDef){
		local Array of String is out: [];
		classDef:members:each(action: local Function(Member is m){
			if({ m:name == 'using' && m:hasInit }, {
				match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function(Array of Expression is items){
						items:each(action: local Function(Expression is item){
							match(on: item, when: [
								Expression:ArrayLit: local Function(Array of Expression is segs){
									segs:each(action: local Function(Expression is seg){
										match(on: seg, when: [
											Expression:UsingAs: local Function(String is className, Array of NamedArg is args){
												out:add(item: className);
											}
										], default: {});
									});
								}
							], default: {});
						});
					}
				], default: {});
			});
		});
		return out;
	}

	## Verifies the instance-import graph is a DAG (E4):
	## A importing as B and B importing as A would recurse construction
	## forever at first init. DFS with gray/black coloring.
	Function is checkInstanceImportGraph(){
		local Map of String to String is color: Map:init();
		:programClasses:each(action: local Function(ClassInfo is c){
			:visitImportNode(c: c, color: color, path: '');
		});
	}

	## One DFS visit of the import graph.
	##
	## @param c: Class being visited.
	## @param color: Node states ('g' in progress, 'b' done).
	## @param path: Cycle-report prefix.
	Function is visitImportNode(ClassInfo is c, Map of String to String is color, String is path){
		local String is state: color:getString(key: c:name, default: '');
		if({ state == 'b' }, {
			return;
		});
		if({ state == 'g' }, {
			:addError(line: 0, msg: :errText:errInstanceImportCycle(cycle: path . c:name));
			return;
		});
		color:set(key: c:name, value: 'g');
		local Array of String is targets: :instanceImportTargets(classDef: c);
		targets:each(action: local Function(String is t){
			local ClassInfo is next: :findClass(name: t);
			if({ next:name != '' }, {
				:visitImportNode(c: next, color: color, path: path . c:name . ' -> ');
			});
		});
		color:set(key: c:name, value: 'b');
	}

	Function of Array of TypeError is checkProgram(ProgramNode is program){
		:errors: [];
		local Array of ClassInfo is flattened: [];
		program:classes:each(action: local Function(ClassInfo is c){
			:collectClasses(c: c, acc: flattened);
		});
		# the same-named inner classes
		# under DIFFERENT enclosing classes are distinct by qualified
		# identity — the ambiguity moves to the reference (the provider
		# walk names the providers). The duplicate WITHIN one outer stays
		# the declaration error.
		local Map of String to String is innerSeen: Map:init();
		flattened:each(action: local Function(ClassInfo is c){
			if({ c:outerName != '' }, {
				if({ innerSeen:has(key: c:qualifiedName()) }, {
					local String is msg: 'Inner class \'' . c:qualifiedName() . '\' is declared more than once in \'' . c:outerName . '\'; rename one.';
					:addError(line: c:line, msg: msg);
				}, {
					innerSeen:set(key: c:qualifiedName(), value: c:outerName);
				});
			});
		});
		:programClasses: flattened;

		:registeredClasses: Map:init();
		:allEnumNames: Map:init();
		:allEnumVariants: Map:init();
		:allStringBackedEnums: Map:init();
		:genericMethodTemplates: Map:init();
		:groundedGenericMethods: Map:init();
		:genericMethodLines: Map:init();
		:genericMethodFiles: Map:init();
		:currentMethodTypeParams: Map:init();

		# Builtin container types resolve like primitives: their methods
		# work with or without an import (the container branches
		# were unconditional). When the declaration is loaded its real
		# signatures apply; when not, calls resolve to the container type.
		local Array of String is builtinNames: ['Array', 'Map', 'List', 'String', 'Function', 'LoopControl', 'Output', 'Error', 'Math', 'Process', 'File', 'Input', 'Ansi', 'Parallel', 'Loops', 'Loop', 'LoopCallback', 'InputHandler'];
		builtinNames:each(action: local Function(String is bn){
			:registeredClasses:set(key: bn, value: bn);
		});
		flattened:each(action: local Function(ClassInfo is c){
			:registeredClasses:set(key: c:name, value: c:name);
			# the nested classes register under
			# their qualified identity too — 'Outer:Inner' resolves in the
			# constructor and static-call paths.
			if({ c:outerName != '' }, {
				:registeredClasses:set(key: c:qualifiedName(), value: c:qualifiedName());
			});
			if({ c:baseClass == :names:enumHeader() && !:bindings:isClassModelEnum(c: c) }, {
				:allEnumNames:set(key: c:name, value: 'true');
				c:members:each(action: local Function(Member is m){
					# The namespace declaration is metadata, not a variant.
					local Boolean is isArrayInit: false;
					if({ m:hasInit }, {
						match(on: m:initExpr, when: [
							Expression:ArrayLit: local Function(Array of Expression is items){
								isArrayInit: true;
							}
						], default: {});
					});
					if({ isArrayInit }, {
						return;
					});
					:allEnumVariants:set(key: m:name, value: c:name);
					if({ m:memberType:name == Primitive:STRING:value() }, {
						:allStringBackedEnums:set(key: c:name, value: 'true');
					});
				});
			});
		});

		# E2/E3: validate as-form instance imports per class.
		flattened:each(action: local Function(ClassInfo is c){
			:checkInstanceImports(classDef: c);
		});
		# E4: the instance-import graph must be a DAG.
		:checkInstanceImportGraph();
		# §I.1: overload legality across all classes.
		:checkOverloadLegality();

		# Pass 1: Inheritance contract validation & type propagation
		flattened:each(action: local Function(ClassInfo is c){
			:checkInheritance(classDef: c);
		});

		# Pass 2: Full expression type inference & AST annotation
		program:classes:each(action: local Function(ClassInfo is c){
			:checkClass(classDef: c);
		});

		local Array of String is gmKeys: :genericMethodTemplates:keys();
		gmKeys:each(action: local Function(String is gmKey){
			if({ !:groundedGenericMethods:has(key: gmKey) }, {
				local Int is cIdx: gmKey:indexOf(search: ':', default: -1);
				local String is ownerName: if({ cIdx > 0 }, { gmKey:substring(start: 0, end: cIdx) }, { gmKey });
				local String is mName: if({ cIdx > 0 }, { gmKey:substring(start: cIdx + 1, end: gmKey:length()) }, { gmKey });
				local ClassInfo is ownerCls: :findClass(name: ownerName);
				local Array of String is nsSegs: ownerCls:namespaceSegments();
				local Boolean is isStdlibOwner: nsSegs:length() > 0 && nsSegs:get(index: 0) == 'base';
				if({ !isStdlibOwner }, {
					local String is tpName: :genericMethodTemplates:getString(key: gmKey, default: '');
					local Int is ln: :genericMethodLines:get(key: gmKey, default: 0);
					local String is savedFile: :currentSourceFile;
					:currentSourceFile: :genericMethodFiles:getString(key: gmKey, default: '');
					:addError(line: ln, msg: "Generic method '" . ownerName . ":" . mName . "' (type parameter '" . tpName . "') is defined but never grounded by any concrete call.");
					:currentSourceFile: savedFile;
				});
			});
		});

		return :errors;
	}

	## Releases semantic maps, scopes, and caches after type checking completes.
	Function is cleanup(){
		:registeredClasses: Map:init();
		:nestedScopeMap: Map:init();
		:allEnumNames: Map:init();
		:allEnumVariants: Map:init();
		:allStringBackedEnums: Map:init();
		:programClasses: [];
		:localVars: Map:init();
		:fieldTypes: Map:init();
		:unassignedFields: Map:init();
		:currentClassDef: ClassInfo:init(name: '', baseClass: '', members: []);
		:genericMethodTemplates: Map:init();
		:groundedGenericMethods: Map:init();
		:genericMethodLines: Map:init();
		:genericMethodFiles: Map:init();
		:currentMethodTypeParams: Map:init();
		:errors: [];
	}
}
