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
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', ClassBindings],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', WhenArm],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'ast', ContractMethod],
		['base', 'compiler', 'ast', MetadataField],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', WellKnown],
		['base', 'compiler', Error],
		['base', 'compiler', 'checker', TypeError],
		['base', 'compiler', 'checker', 'loops', ClassSearchLoop],
		['base', 'compiler', 'checker', 'loops', FieldSearchLoop],
		['base', 'compiler', 'checker', 'loops', MethodSearchLoop],
		['base', 'compiler', 'checker', 'loops', PathResolveLoop],
		['base', 'compiler', 'checker', 'loops', MemberImplementLoop],
		['base', 'iterator'],
		['base', 'iterator', as While()],
		['base', 'sys', as Reflection()],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
];

	## Registered classes: name -> "true".
	local Map of String to String is registeredClasses: Map:init();

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

	## Name of the method being checked (forward resolution).
	local String is currentMethodName: '';

	## Whether a forward statement was seen in the current method.
	local Boolean is forwardSeen: false;

	## Anonymous-function nesting depth (forwards are top-level only).
	local Int is anonDepth: 0;
	# FUNCTIONS.md Part II: inside a Conditional branch-closure argument —
	# its body inlines into the enclosing method, so returns flow to the
	# method's return type, not the closure's.
	local Boolean is inBranchClosure: false;

	## Class currently being analyzed.
	local String is currentClassName: '';

	## Source file of the class currently being analyzed.
	local String is currentSourceFile: '';

	## Return type name of the method currently being checked.
	local String is currentMethodReturnType: '';

	## FUNCTIONS.md Part II: the anon-fn node whose body is being checked
	## (the Kotlin write-back target for void-declared closures).
	local Expression is currentAnonNode: Expression:init(kind: ExpressionKind:UNKNOWN);

	## FUNCTIONS.md Part II: inside a value-yielding branch's then/otherwise
	## closure (the call site expects a value).
	local Boolean is inValueBranch: false;

	## FUNCTIONS.md Part II: checking the last statement of a value-yielding
	## branch closure — its return establishes the branch's yield type.
	local Boolean is checkingValueYield: false;

	## FUNCTIONS.md Part II: the expected type of the value-yielding branch
	## being checked — flows into its yields so nested branch calls type in
	## context.
	local String is currentYieldExpected: '';

	## Accumulated type errors.
	local Array of TypeError is errors: [];

	## All class definitions in the program (nested included).
	local Array of ClassInfo is programClasses: [];

	## Well-known names (builtin types, sentinels).
	local WellKnown is names: WellKnown:init();

	## The shared floor-class classification (emission + call contracts).
	local ClassBindings is bindings: ClassBindings:init();

	replace Function is init(){
		self:programClasses: [];
		self:registeredClasses: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();
		self:localVars: Map:init();
		self:fieldTypes: Map:init();
		self:unassignedFields: Map:init();
		self:currentLine: 0;
		self:currentSourceFile: '';
	}

	## Records a type error with provenance.
	##
	## @param line: Source line number.
	## @param msg: Diagnostic message.
	Function is addError(Int is line, String is msg){
		local String is fullMsg: Conditional:if(check: { self:currentSourceFile != '' }, then: { '[' . self:currentSourceFile . '] ' . msg }, else: { msg });
		local Error is e: Error:init(message: fullMsg);
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: line, col: 0);
		self:errors:add(item: TypeError:init(line: line, message: fullMsg));
	}

	## True when the name is one of the two void spellings.
	##
	## @param t: Type name.
	## @return: true for 'void' and 'Void'.
	Function of Boolean is isVoid(String is t){
		return t == Primitive:VOID:value() || t == self:names:voidMemberType();
	}

	## True when the name is a primitive type name (not a class).
	##
	## @param t: Type name.
	## @return: true per the [Primitive] vocabulary.
	Function of Boolean is isPrimitive(String is t){
		return Primitive:of(t) != Primitive:NONE;
	}

	## Formats a [Type] descriptor for a variable or field (preserving
	## "Function:RetType").
	##
	## @param t: Type descriptor.
	## @return: Type name string.
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

	## Formats a [Type] descriptor into the internal colon form
	## (Array:X, Map:K:V); Function formats to its return type.
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

	## Substitutes a class's generic type parameters in a member type name.
	##
	## @param rawType: Declared type name (may reference type params).
	## @param cls: The declaring class.
	## @param typeArgs: The concrete type arguments.
	## @return: The substituted type name.
	Function of String is substituteTypeParam(String is rawType, ClassInfo is cls, Array of String is typeArgs){
		local Array of String is tps: cls:typeParams;
		Conditional:if(check: { tps:length() == 0 || typeArgs:length() == 0 }, then: {
			return rawType;
		});
		local Int is idx: tps:indexOf(search: rawType, default: -1);
		Conditional:if(check: { idx >= 0 }, then: {
			# Grounded when the container carries type arguments; a bare
			# container ('Array' without 'of T') degrades to Any.
			Conditional:if(check: { idx < typeArgs:length() }, then: {
				return typeArgs:get(index: idx);
			});
			return Primitive:ANY:value();
		});
		Conditional:if(check: { rawType:startsWith(prefix: 'Array:') && rawType:length() > 6 }, then: {
			local String is elem: rawType:substring(start: 6, end: rawType:length());
			local Int is eIdx: tps:indexOf(search: elem, default: -1);
			Conditional:if(check: { eIdx >= 0 && eIdx < typeArgs:length() }, then: {
				return 'Array:' . typeArgs:get(index: eIdx);
			});
		});
		Conditional:if(check: { rawType:startsWith(prefix: 'List:') && rawType:length() > 5 }, then: {
			local String is elem: rawType:substring(start: 5, end: rawType:length());
			local Int is eIdx: tps:indexOf(search: elem, default: -1);
			Conditional:if(check: { eIdx >= 0 && eIdx < typeArgs:length() }, then: {
				return 'List:' . typeArgs:get(index: eIdx);
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
		While:run(loop: s);
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

	## Determines whether a source type is assignable to a target type.
	##
	## @param target: Target type name.
	## @param source: Source type name.
	## @return: true when compatible.
	Function of Boolean is isAssignable(String is target, String is source){
		Conditional:if(check: { target == source || target == Primitive:ANY:value() || source == Primitive:ANY:value() || target == '' || source == '' }, then: {
			return true;
		});
		# Implicit numeric widening: Int assigns to Float (explicit casts
		# handle the narrowing directions).
		Conditional:if(check: { target == 'Float' && source == Primitive:INT:value() }, then: {
			return true;
		});
		# FUNCTIONS.md Part IV V1: Function assignability is directional. A
		# typed closure feeds an untyped param (covariance — the callback
		# idiom); a TYPED param accepts only a closure promising the same
		# return type. A void or differently-typed closure would read
		# garbage through the typed invocation (the check closure's bool
		# cast), so the narrowing direction rejects.
		Conditional:if(check: { target:startsWith(prefix: 'Function') && source:startsWith(prefix: 'Function') }, then: {
			Conditional:if(check: { !target:startsWith(prefix: 'Function:') }, then: {
				return true;
			});
			Conditional:if(check: { !source:startsWith(prefix: 'Function:') }, then: {
				return false;
			});
			local String is tRet: target:substring(start: 9, end: target:length());
			local String is sRet: source:substring(start: 9, end: source:length());
			Conditional:if(check: { tRet == sRet || tRet == Primitive:ANY:value() || sRet == Primitive:ANY:value() }, then: {
				return true;
			});
			return false;
		});
		local ClassInfo is curCls: self:findClass(name: self:currentClassName);
		Conditional:if(check: { curCls:typeParams:indexOf(search: target, default: -1) >= 0 || curCls:typeParams:indexOf(search: source, default: -1) >= 0 }, then: {
			return true;
		});
		# Of-form containers ('Array of String'): normalize to the colon
		# form so the type-argument comparison below sees the args. Map's
		# two args join with ' to ' — split them back out.
		local String is tNorm: target;
		local String is sNorm: source;
		local Int is tOf: target:indexOf(search: ' of ', default: -1);
		local Int is sOf: source:indexOf(search: ' of ', default: -1);
		Conditional:if(check: { tOf > 0 }, then: {
			tNorm: target:substring(start: 0, end: tOf) . ':' . target:substring(start: tOf + 4, end: target:length());
		});
		Conditional:if(check: { sOf > 0 }, then: {
			sNorm: source:substring(start: 0, end: sOf) . ':' . source:substring(start: sOf + 4, end: source:length());
		});
		local Int is tTo: tNorm:indexOf(search: ' to ', default: -1);
		local Int is sTo: sNorm:indexOf(search: ' to ', default: -1);
		Conditional:if(check: { tTo > 0 }, then: {
			tNorm: tNorm:substring(start: 0, end: tTo) . ':' . tNorm:substring(start: tTo + 4, end: tNorm:length());
		});
		Conditional:if(check: { sTo > 0 }, then: {
			sNorm: sNorm:substring(start: 0, end: sTo) . ':' . sNorm:substring(start: sTo + 4, end: sNorm:length());
		});
		local Array of String is tParts: tNorm:split(delimiter: ':');
		local Array of String is sParts: sNorm:split(delimiter: ':');
		Conditional:if(check: { tParts:length() > 0 && sParts:length() > 0 }, then: {
			local String is tBase: tParts:get(index: 0);
			local String is sBase: sParts:get(index: 0);
			Conditional:if(check: { tBase == sBase || self:isSubclassOf(subName: sBase, baseName: tBase) }, then: {
				Conditional:if(check: { tParts:length() > 1 && sParts:length() > 1 }, then: {
					local Boolean is argsOk: true;
					local Int is pIdx: 1;
					While:condition(
						evaluate: local Function of Boolean(){
							return pIdx < tParts:length() && pIdx < sParts:length();
						},
						iteration: local Function of Boolean(){
							local String is tp: tParts:get(index: pIdx);
							local String is sp: sParts:get(index: pIdx);
							Conditional:if(check: { !self:isAssignable(target: tp, source: sp) }, then: {
								argsOk: false;
							});
							pIdx: pIdx + 1;
							return true;
						}
					);
					return argsOk;
				});
				return true;
			});
		});
		Conditional:if(check: { self:isSubclassOf(subName: source, baseName: target) }, then: {
			return true;
		});
		return false;
	}

	## FUNCTIONS.md Part IV IV.2c: the member-lookup root for a (possibly
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
		Conditional:if(check: { className:contains(needle: ':') }, then: {
			local ClassInfo is qCls: self:findClass(name: className);
			Conditional:if(check: { qCls:name != '' && qCls:qualifiedName() == className }, then: {
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
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return Member:init(kind: MemberKind:FIELD);
		});
		local String is baseClassName: self:memberLookupRoot(className: className);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		Conditional:if(check: { cls:name == '' }, then: {
			return Member:init(kind: MemberKind:FIELD);
		});
		local MethodSearchLoop is ml: MethodSearchLoop:init(members: cls:members, methodName: methodName);
		While:run(loop: ml);
		Conditional:if(check: { ml:found }, then: {
			return ml:res;
		});
		local Member is inherited: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { inherited:name == '' }, then: {
				inherited: self:lookupAnyMember(className: baseName, methodName: methodName);
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
		local FieldSearchLoop is fl: FieldSearchLoop:init(members: cls:members, fieldName: variantName);
		While:run(loop: fl);
		Conditional:if(check: { fl:found }, then: {
			return fl:res;
		});
		return Member:init(kind: MemberKind:FIELD);
	}

	## Looks up a field's static type on a class and its ancestors.
	##
	## @param className: Starting class name.
	## @param fieldName: Field name.
	## @return: The field type name, or '' when absent.
	Function of String is lookupFieldType(String is className, String is fieldName){
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return '';
		});
		local String is baseClassName: self:memberLookupRoot(className: className);
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
		local FieldSearchLoop is fl: FieldSearchLoop:init(members: cls:members, fieldName: fieldName);
		While:run(loop: fl);
		Conditional:if(check: { fl:found }, then: {
			local Member is foundM: fl:res;
			local String is rawT: self:formatTypeString(t: foundM:memberType);
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
	## @return: The return type name, or '' when absent.
	Function of String is lookupMethodReturnType(String is className, String is methodName){
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return '';
		});
		local String is baseClassName: self:memberLookupRoot(className: className);
		local Array of String is typeArgs: [];
		# The resolved qualified root absorbs the colon chain — the segments
		# after it are the nested path, not type arguments ('LibA:Helper').
		# Bare colon forms ground as before ('Array:String').
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
		Conditional:if(check: { methodName == ContractMethod:INIT:value() && self:registeredClasses:has(key: baseClassName) && !self:allEnumNames:has(key: baseClassName) }, then: {
			return className;
		});
		local ClassInfo is cls: self:findClass(name: baseClassName);
		Conditional:if(check: { cls:name == '' }, then: {
			return '';
		});
		local MethodSearchLoop is ml: MethodSearchLoop:init(members: cls:members, methodName: methodName);
		While:run(loop: ml);
		Conditional:if(check: { ml:found }, then: {
			local Member is foundM: ml:res;
			local String is rawT: self:formatTypeString(t: foundM:memberType);
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

	## Validates call-site argument types against the resolved signature.
	##
	## Named arguments match by parameter name; unmatched named arguments
	## fall back to positional matching. Any-typed parameters and arguments
	## are skipped; builtin stub signatures are exempt.
	##
	## @param callExpr: The CALL expression.
	Function is checkCallArguments(Expression is callExpr){
		local String is targetType: callExpr:methodTarget:resolvedType;
		Conditional:if(check: { targetType == self:names:selfIdent() || targetType == '' }, then: {
			targetType: self:currentClassName;
		});
		Conditional:if(check: { targetType == '' || targetType == Primitive:ANY:value() || self:allEnumNames:has(key: targetType) }, then: {
			return;
		});
		local Array of String is parts: targetType:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		Conditional:if(check: { baseClassName == '' || baseClassName == Primitive:ANY:value() || baseClassName == 'While' }, then: {
			return;
		});
		local Member is m: self:lookupOverloadedMember(className: self:memberLookupRoot(className: targetType), methodName: callExpr:methodName, idx: callExpr:overloadIndex);
		Conditional:if(check: { m:kind != MemberKind:METHOD }, then: {
			return;
		});
		local Array of Parameter is params: m:params;
		Conditional:if(check: { params:length() == 0 }, then: {
			return;
		});
		local ClassInfo is recvCls: self:findClass(name: baseClassName);
		local Array of String is recvTypeParams: recvCls:typeParams;
		local Int is pIdx: 0;
		params:each(action: local Function(Parameter is p){
			local String is pName: p:name;
			local String is pT: p:paramType:name;
			# FUNCTIONS.md Part IV V1: a Function-typed param enforces
			# assignability in the colon form — the raw name would broaden
			# every Function param to plain Function (the void-into-check
			# hole).
			local String is pTF: pT;
			Conditional:if(check: { pT:startsWith(prefix: 'Function') }, then: {
				pTF: self:formatVarTypeString(t: p:paramType);
			});
			Conditional:if(check: { pT != self:names:selfFieldMarker() && pT != Primitive:ANY:value() && pT != '' && recvTypeParams:indexOf(search: pT, default: -1) < 0 }, then: {
				local Expression is matchedValue: Expression:init(kind: ExpressionKind:UNKNOWN);
				local Boolean is found: false;
				local Int is posIdx: 0;
				callExpr:methodArgs:each(action: local Function(NamedArg is a){
					Conditional:if(check: { !found && pName != '' && a:name == pName }, then: {
						matchedValue: a:value;
						found: true;
					});
				});
				Conditional:if(check: { !found }, then: {
					callExpr:methodArgs:each(action: local Function(NamedArg is a){
						Conditional:if(check: { !found && a:name == '' && posIdx == pIdx }, then: {
							matchedValue: a:value;
							found: true;
						});
						posIdx: posIdx + 1;
					});
				});
				Conditional:if(check: { found }, then: {
					local String is argT: matchedValue:resolvedType;
					Conditional:if(check: { argT != '' && argT != Primitive:ANY:value() && !self:isAssignable(target: pTF, source: argT) }, then: {
						local String is label: Conditional:if(check: { pName != '' }, then: { pName }, else: { 'position ' . (pIdx + 1) });
						local String is msg: 'Argument \'' . label . '\' for \'' . baseClassName . '.' . callExpr:methodName . '\': cannot assign \'' . argT . '\' to \'' . self:displayType(t: pTF) . '\'.';
						self:addError(line: self:currentLine, msg: msg);
					});
				}, else: {
					Conditional:if(check: { !p:hasDefault && !self:isBindingDeclaration(cls: recvCls) }, then: {
						# Binding declarations (sysinternal + runtime-managed)
						# sketch API surface, not call contracts — their C
						# implementations carry optional/variadic semantics.
						local String is msg: 'Missing argument \'' . pName . '\' for \'' . baseClassName . '.' . callExpr:methodName . '\'.';
						self:addError(line: self:currentLine, msg: msg);
					});
				});
			});
			pIdx: pIdx + 1;
		});
	}

	## FUNCTIONS.md §I.2: resolves one same-name member group to the
	## overload the call selects, stamping expr:overloadIndex. Candidates
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
		local String is baseName: self:memberLookupRoot(className: className);
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		self:collectOverloadGroup(className: baseName, methodName: methodName, hops: 0, acc: group, ownerAcc: ownerAcc);
		Conditional:if(check: { group:length() == 0 }, then: {
			return none;
		});
		# FUNCTIONS.md §I.3: no mixed calls — enforced globally, including
		# single-member names. The scoped-region desugaring no longer
		# produces mixed calls: its remainder binds to the unbound last
		# Function parameter instead of riding as an argument (§as).
		local Array of NamedArg is allArgs: expr:methodArgs;
		local Array of NamedArg is args: allArgs;
		local Boolean is isScoped: expr:scopedRemainder;
		Conditional:if(check: { isScoped }, then: {
			local Array of NamedArg is explicit: [];
			local Int is ei: 0;
			While:condition(
				evaluate: local Function of Boolean(){ return ei < allArgs:length() - 1; },
				iteration: local Function of Boolean(){
					explicit:add(item: allArgs:get(index: ei));
					ei: ei + 1;
					return true;
				}
			);
			args: explicit;
		});
		local Boolean is allPos: true;
		local Boolean is allNamed: true;
		args:each(action: local Function(NamedArg is a){
			Conditional:if(check: { a:name == '' }, then: {
				allNamed: false;
			}, else: {
				allPos: false;
			});
		});
		Conditional:if(check: { !allPos && !allNamed }, then: {
			self:addError(line: self:currentLine, msg: 'Mixed positional and named arguments are not supported; use one form (FUNCTIONS.md §I.3).');
			return none;
		});
		Conditional:if(check: { group:length() == 1 }, then: {
			local Member is only: group:get(index: 0);
			Conditional:if(check: { isScoped && !self:scopeSlotOk(m: only, explicitCount: args:length()) }, then: {
				self:addError(line: self:currentLine, msg: 'The scoped region requires exactly one unbound Function parameter at the end of \'' . baseName . '.' . methodName . '\' (FUNCTIONS.md §as).');
				return none;
			});
			expr:overloadIndex: 0;
			return only;
		});
		Conditional:if(check: { allNamed }, then: {
			local Boolean is dupArg: false;
			local Int is ai: 0;
			While:condition(
				evaluate: local Function of Boolean(){ return !dupArg && ai < args:length(); },
				iteration: local Function of Boolean(){
					local Int is aj: ai + 1;
					While:condition(
						evaluate: local Function of Boolean(){ return !dupArg && aj < args:length(); },
						iteration: local Function of Boolean(){
							local NamedArg is argA: args:get(index: ai);
							local NamedArg is argB: args:get(index: aj);
							Conditional:if(check: { argA:name == argB:name }, then: {
								dupArg: true;
							});
							aj: aj + 1;
							return true;
						}
					);
					ai: ai + 1;
					return true;
				}
			);
			Conditional:if(check: { dupArg }, then: {
				self:addError(line: self:currentLine, msg: 'Duplicate named argument in call to \'' . baseName . '.' . methodName . '\'.');
				return none;
			});
		});
		local Array of Member is survivors: [];
		# FUNCTIONS.md §as: a scoped remainder binds to an unbound last
		# Function parameter — it never widens the arity. Pass 1: exact
		# arity on the explicit arguments. Pass 2 (only when pass 1 is
		# empty and the call is scoped): params == explicit + 1 with the
		# last parameter Function-typed — the open scope slot.
		local Int is wantCount: args:length();
		group:each(action: local Function(Member is m){
			Conditional:if(check: { m:params:length() != wantCount }, then: {
				return;
			});
			Conditional:if(check: { allPos }, then: {
				survivors:add(item: m);
				return;
			});
			local Boolean is namesMatch: true;
			local Int is npIdx: 0;
			m:params:each(action: local Function(Parameter is p){
				# The scope slot (the last parameter) is bound by the
				# remainder, not by a named argument.
				Conditional:if(check: { !(isScoped && npIdx == m:params:length() - 1) }, then: {
					local Boolean is present: false;
					args:each(action: local Function(NamedArg is a){
						Conditional:if(check: { a:name == p:name }, then: {
							present: true;
						});
					});
					Conditional:if(check: { !present }, then: {
						namesMatch: false;
					});
				});
				npIdx: npIdx + 1;
			});
			Conditional:if(check: { namesMatch }, then: {
				survivors:add(item: m);
				return;
			});
		});
		Conditional:if(check: { survivors:length() == 0 && isScoped }, then: {
			# Pass 2: the open scope slot — params == explicit + 1, last
			# parameter Function-typed.
			local Array of Member is slots: [];
			group:each(action: local Function(Member is m){
				Conditional:if(check: { self:scopeSlotOk(m: m, explicitCount: args:length()) }, then: {
					slots:add(item: m);
				});
			});
			Conditional:if(check: { slots:length() == 1 }, then: {
				local Member is sel: slots:get(index: 0);
				expr:overloadIndex: self:indexOfMember(group: group, m: sel);
				return sel;
			});
		});
		Conditional:if(check: { survivors:length() == 0 }, then: {
			Conditional:if(check: { allPos }, then: {
				self:addError(line: self:currentLine, msg: 'No signature of \'' . baseName . '.' . methodName . '\' takes ' . (args:length() as String) . ' argument(s).');
			}, else: {
				self:addError(line: self:currentLine, msg: 'No signature of \'' . baseName . '.' . methodName . '\' matches the named arguments.');
			});
			return none;
		});
		Conditional:if(check: { survivors:length() == 1 }, then: {
			local Member is sel: survivors:get(index: 0);
			Conditional:if(check: { isScoped && !self:scopeSlotOk(m: sel, explicitCount: args:length()) }, then: {
				self:addError(line: self:currentLine, msg: 'The scoped region has no open scope slot in \'' . baseName . '.' . methodName . '\': every parameter is already bound (FUNCTIONS.md §as).');
				return none;
			});
			expr:overloadIndex: self:indexOfMember(group: group, m: sel);
			return sel;
		});
		local Array of Member is exact: [];
		survivors:each(action: local Function(Member is m){
			Conditional:if(check: { self:exactTypeMatch(m: m, expr: expr) }, then: {
				exact:add(item: m);
			});
		});
		Conditional:if(check: { exact:length() == 1 }, then: {
			local Member is sel: exact:get(index: 0);
			Conditional:if(check: { isScoped && !self:scopeSlotOk(m: sel, explicitCount: args:length()) }, then: {
				self:addError(line: self:currentLine, msg: 'The scoped region has no open scope slot in \'' . baseName . '.' . methodName . '\': every parameter is already bound (FUNCTIONS.md §as).');
				return none;
			});
			expr:overloadIndex: self:indexOfMember(group: group, m: sel);
			return sel;
		});
		Conditional:if(check: { isScoped && exact:length() == 0 }, then: {
			# Pass 2: the open scope slot — params == explicit + 1, last
			# parameter Function-typed.
			local Array of Member is slots: [];
			group:each(action: local Function(Member is m){
				Conditional:if(check: { self:scopeSlotOk(m: m, explicitCount: args:length()) }, then: {
					slots:add(item: m);
				});
			});
			Conditional:if(check: { slots:length() == 1 }, then: {
				local Member is sel: slots:get(index: 0);
				expr:overloadIndex: self:indexOfMember(group: group, m: sel);
				return sel;
			});
		});
		Conditional:if(check: { exact:length() > 1 }, then: {
			self:addError(line: self:currentLine, msg: 'Ambiguous call to \'' . baseName . '.' . methodName . '\': the arguments match multiple overloads; use named arguments (FUNCTIONS.md §I.2).');
			return none;
		});
		local String is argTypes: '';
		args:each(action: local Function(NamedArg is a){
			local String is at: a:value:resolvedType;
			Conditional:if(check: { at == '' }, then: {
				at: 'Any';
			});
			Conditional:if(check: { argTypes == '' }, then: {
				argTypes: at;
			}, else: {
				argTypes: argTypes . ', ' . at;
			});
		});
		self:addError(line: self:currentLine, msg: 'No exact overload of \'' . baseName . '.' . methodName . '\' for (' . argTypes . '); cast the arguments or give the signatures distinct names (FUNCTIONS.md §I.2).');
		return none;
	}
	## Collects the same-name METHOD members of the nearest declaring
	## ancestor: the first subtree (class, then parents in declaration
	## order) that declares the name wins; deeper walk stops there.
	## Walks every parent (multiple inheritance), first-wins.
	##
	## @param className: The class to start from.
	## @param methodName: The member name.
	## @param hops: Recursion budget guard.
	## @param acc: The collected group (nearest-declaration semantics).
	## @param ownerAcc: The declaring class name accumulator (reference).
	Function is collectOverloadGroup(String is className, String is methodName, Int is hops, Array of Member is acc, Array of String is ownerAcc){
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
			ownerAcc:add(item: cls:name);
			return;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			self:collectOverloadGroup(className: baseName, methodName: methodName, hops: hops + 1, acc: acc, ownerAcc: ownerAcc);
		});
	}

	## FUNCTIONS.md §as: true when [m]'s last parameter is the open scope
	## slot — exactly [explicitCount] parameters precede it and the slot is
	## Function-typed (the remainder is a closure).
	##
	## @param m: The candidate overload.
	## @param explicitCount: The explicit argument count.
	## @return: true when the scope slot is open and valid.
	Function of Boolean is scopeSlotOk(Member is m, Int is explicitCount){
		Conditional:if(check: { m:params:length() != explicitCount + 1 }, then: {
			return false;
		});
		local Parameter is slot: m:params:get(index: m:params:length() - 1);
		return slot:paramType:name == 'Function';
	}

	## True when every argument's inferred type equals the bound
	## parameter's declared type (positional by index, named by name).
	##
	## @param m: The candidate overload.
	## @param expr: The CALL expression.
	## @return: true when all argument types match exactly.
	Function of Boolean is exactTypeMatch(Member is m, Expression is expr){
		local Boolean is allMatch: true;
		local Int is posIdx: 0;
		m:params:each(action: local Function(Parameter is p){
			local Expression is bound: Expression:init(kind: ExpressionKind:UNKNOWN);
			local Boolean is found: false;
			Conditional:if(check: { p:name != '' }, then: {
				expr:methodArgs:each(action: local Function(NamedArg is a){
					Conditional:if(check: { !found && a:name == p:name }, then: {
						bound: a:value;
						found: true;
					});
				});
			});
			Conditional:if(check: { !found && posIdx < expr:methodArgs:length() }, then: {
				local NamedArg is pa: expr:methodArgs:get(index: posIdx);
				Conditional:if(check: { pa:name == '' }, then: {
					bound: pa:value;
					found: true;
				});
			});
			# FUNCTIONS.md Part IV V1: a Function-typed param compares in the
			# colon form ('Function of Boolean' -> 'Function:Boolean') — the
			# raw name erases the return type and matches every closure.
			local String is pT: p:paramType:name;
			Conditional:if(check: { pT:startsWith(prefix: 'Function') }, then: {
				pT: self:formatVarTypeString(t: p:paramType);
			});
			Conditional:if(check: { !found || bound:resolvedType == '' || bound:resolvedType != pT }, then: {
				allMatch: false;
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
			Conditional:if(check: { g == m }, then: {
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
	## @return: The resolved return type.
	Function of String is selectedReturnType(String is className, Member is selected){
		local String is baseName: self:memberLookupRoot(className: className);
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		self:collectOverloadGroup(className: baseName, methodName: selected:name, hops: 0, acc: group, ownerAcc: ownerAcc);
		Conditional:if(check: { group:length() <= 1 || ownerAcc:length() == 0 }, then: {
			return self:lookupMethodReturnType(className: className, methodName: selected:name);
		});
		local String is owner: ownerAcc:get(index: 0);
		local ClassInfo is ownerCls: self:findClass(name: owner);
		Conditional:if(check: { ownerCls:name == '' }, then: {
			return '';
		});
		local Array of String is typeArgs: [];
		# The resolved qualified root absorbs the colon chain (IV.2c); bare
		# colon forms ground their segments as type arguments.
		Conditional:if(check: { baseName != className }, then: {
			local Array of String is parts: className:split(delimiter: ':');
			typeArgs: parts:slice(start: 1, end: parts:length());
		});
		local String is rawT: self:formatTypeString(t: selected:memberType);
		return self:substituteTypeParam(rawType: rawT, cls: ownerCls, typeArgs: typeArgs);
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
		self:collectOverloadGroup(className: self:memberLookupRoot(className: className), methodName: methodName, hops: 0, acc: group, ownerAcc: ownerAcc);
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
	## True when the current class, or any ancestor (all parents,
	## transitively), instance-imports [className] — as-imports are
	## inherited like the fields they synthesize (INSTANCE.md §2.1).
	##
	## @param className: Receiver class name.
	## @return: true when imported somewhere up the chain.
	Function of Boolean is isAsImportedInherited(String is className){
		return self:importsAsAnywhere(clsName: self:currentClassName, targetName: className, hops: 0);
	}

	## Recursive import search over the ancestor lattice.
	##
	## @param clsName: Class being visited.
	## @param targetName: The imported class name sought.
	## @param hops: Recursion budget guard.
	## @return: true when found on this class or an ancestor.
	Function of Boolean is importsAsAnywhere(String is clsName, String is targetName, Int is hops){
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
			Conditional:if(check: { !viaParent && self:importsAsAnywhere(clsName: baseName, targetName: targetName, hops: hops + 1) }, then: {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## FUNCTIONS.md §2.3: collects the as-imported classes providing
	## [methodName] for the bare scope of the current class — own
	## bindings plus every ancestor's, one level deep. Order-stable
	## diagnostics; duplicates dropped.
	##
	## @param methodName: The bare-called function name.
	## @return: Provider class names in walk order.
	Function of Array of String is bareScopeProviders(String is methodName){
		local Array of String is out: [];
		self:collectBareProviders(clsName: self:currentClassName, methodName: methodName, hops: 0, acc: out);
		return out;
	}

	## Recursive provider collection over the ancestor lattice.
	##
	## @param clsName: Class being visited.
	## @param methodName: The bare-called function name.
	## @param hops: Recursion budget guard.
	## @param acc: The provider accumulator.
	Function is collectBareProviders(String is clsName, String is methodName, Int is hops, Array of String is acc){
		Conditional:if(check: { clsName == '' || clsName == 'Any' || hops >= 64 }, then: {
			return;
		});
		local ClassInfo is cls: self:findClass(name: clsName);
		Conditional:if(check: { cls:name == '' }, then: {
			return;
		});
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, then: {
				m:initExpr:arrayItems:each(action: local Function(Expression is item){
					Conditional:if(check: { item:kind == ExpressionKind:ARRAY }, then: {
						item:arrayItems:each(action: local Function(Expression is seg){
							Conditional:if(check: { seg:kind == ExpressionKind:USING_AS }, then: {
								local String is prov: seg:stringValue;
								local Boolean is already: false;
								acc:each(action: local Function(String is got){
									Conditional:if(check: { got == prov }, then: {
										already: true;
									});
								});
								Conditional:if(check: { !already && self:findMemberOwnerClass(className: prov, memberName: methodName) != '' }, then: {
									acc:add(item: prov);
								});
							});
						});
					});
				});
			});
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			self:collectBareProviders(clsName: baseName, methodName: methodName, hops: hops + 1, acc: acc);
		});
	}

	## True when an ancestor of [className] (any parent, transitively)
	## declares [methodName] as a method. The starting class's own members
	## are excluded — an overload group on the class itself is legal.
	##
	## @param className: The class whose ancestors are walked.
	## @param methodName: The member name.
	## @param hops: Recursion budget guard.
	## @return: true when an ancestor declares the name.
	Function of Boolean is ancestorDeclares(String is className, String is methodName, Int is hops){
		Conditional:if(check: { className == '' || className == 'Any' || hops >= 64 }, then: {
			return false;
		});
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		Conditional:if(check: { cls:name == '' }, then: {
			return false;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:declaresOrInherits(className: baseName, methodName: methodName, hops: hops + 1) }, then: {
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
	## @param hops: Recursion budget guard.
	## @return: true when declared here or inherited.
	Function of Boolean is declaresOrInherits(String is className, String is methodName, Int is hops){
		Conditional:if(check: { className == '' || className == 'Any' || hops >= 64 }, then: {
			return false;
		});
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		Conditional:if(check: { cls:name == '' }, then: {
			return false;
		});
		local Boolean is found: false;
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == methodName }, then: {
				found: true;
			});
		});
		Conditional:if(check: { found }, then: {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:declaresOrInherits(className: baseName, methodName: methodName, hops: hops + 1) }, then: {
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
	## @param hops: Recursion budget guard.
	## @return: true when the inherited name is overloaded.
	Function of Boolean is ancestorOverloaded(String is className, String is methodName, Int is hops){
		Conditional:if(check: { className == '' || className == 'Any' || hops >= 64 }, then: {
			return false;
		});
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		Conditional:if(check: { cls:name == '' }, then: {
			return false;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:nearestGroupOverloaded(className: baseName, methodName: methodName, hops: hops + 1) }, then: {
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
	## @param hops: Recursion budget guard.
	## @return: true when the nearest declaration is overloaded.
	Function of Boolean is nearestGroupOverloaded(String is className, String is methodName, Int is hops){
		Conditional:if(check: { className == '' || className == 'Any' || hops >= 64 }, then: {
			return false;
		});
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		Conditional:if(check: { cls:name == '' }, then: {
			return false;
		});
		local Int is groupSize: 0;
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == methodName }, then: {
				groupSize: groupSize + 1;
			});
		});
		Conditional:if(check: { groupSize >= 2 }, then: {
			return true;
		});
		Conditional:if(check: { groupSize == 1 }, then: {
			return false;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:nearestGroupOverloaded(className: baseName, methodName: methodName, hops: hops + 1) }, then: {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## FUNCTIONS.md §I.1: validates every class's same-name METHOD groups —
	## identical signatures are the duplicate error; overload groups must
	## declare concrete parameter types and must not shadow an inherited
	## name (the virtual machinery is name-keyed; overloads dispatch
	## directly). The per-member body nests instead of returning early: an
	## iteration closure's early `return` compiles to a loop `break`.
	Function is checkOverloadLegality(){
		self:programClasses:each(action: local Function(ClassInfo is c){
			local Array of Member is members: c:members;
			local Int is i: 0;
			While:condition(
				evaluate: local Function of Boolean(){ return i < members:length(); },
				iteration: local Function of Boolean(){
					local Member is m: members:get(index: i);
					Conditional:if(check: { m:kind == MemberKind:METHOD }, then: {
						local Boolean is earlier: false;
						local Int is j: 0;
						While:condition(
							evaluate: local Function of Boolean(){ return !earlier && j < i; },
							iteration: local Function of Boolean(){
								local Member is g: members:get(index: j);
								Conditional:if(check: { g:kind == MemberKind:METHOD && g:name == m:name }, then: {
									earlier: true;
								});
								j: j + 1;
								return true;
							}
						);
						Conditional:if(check: { !earlier }, then: {
							local Int is groupSize: 0;
							local Int is k: 0;
							While:condition(
								evaluate: local Function of Boolean(){ return k < members:length(); },
								iteration: local Function of Boolean(){
									local Member is g: members:get(index: k);
									Conditional:if(check: { g:kind == MemberKind:METHOD && g:name == m:name }, then: {
										groupSize: groupSize + 1;
									});
									k: k + 1;
									return true;
								}
							);
							Conditional:if(check: { groupSize >= 2 }, then: {
								local Int is a: 0;
								While:condition(
									evaluate: local Function of Boolean(){ return a < members:length(); },
									iteration: local Function of Boolean(){
										local Member is ma: members:get(index: a);
										Conditional:if(check: { ma:kind == MemberKind:METHOD && ma:name == m:name }, then: {
											local Int is b: a + 1;
											While:condition(
												evaluate: local Function of Boolean(){ return b < members:length(); },
												iteration: local Function of Boolean(){
													local Member is mb: members:get(index: b);
													Conditional:if(check: { mb:kind == MemberKind:METHOD && mb:name == m:name && self:checkerSameSignature(a: ma, b: mb) }, then: {
														self:addError(line: m:line, msg: 'Methods \'' . m:name . '\' in class \'' . c:name . '\' declare identical signatures; overloads must differ (FUNCTIONS.md §I.1).');
													});
													b: b + 1;
													return true;
												}
											);
										});
										a: a + 1;
										return true;
									}
								);
								local Boolean is nonConcrete: false;
								local Int is p: 0;
								While:condition(
									evaluate: local Function of Boolean(){ return !nonConcrete && p < members:length(); },
									iteration: local Function of Boolean(){
										local Member is g: members:get(index: p);
										Conditional:if(check: { g:kind == MemberKind:METHOD && g:name == m:name }, then: {
											g:params:each(action: local Function(Parameter is pp){
												local String is pt: pp:paramType:name;
												Conditional:if(check: { pt == '' || pt == Primitive:ANY:value() || pt == self:names:selfFieldMarker() || c:typeParams:indexOf(search: pt, default: -1) >= 0 }, then: {
													nonConcrete: true;
												});
											});
										});
										p: p + 1;
										return true;
									}
								);
								Conditional:if(check: { nonConcrete }, then: {
									self:addError(line: m:line, msg: 'Overloaded method \'' . m:name . '\' must declare concrete parameter types (FUNCTIONS.md §I.3).');
								});
								Conditional:if(check: { m:name != 'init' && self:ancestorDeclares(className: c:name, methodName: m:name, hops: 0) }, then: {
									self:addError(line: m:line, msg: 'Cannot overload \'' . m:name . '\': the name is declared on an ancestor (FUNCTIONS.md §I.3).');
								});
							});
						});
					});
					i: i + 1;
					return true;
				}
			);
		});
	}

	## FUNCTIONS.md §I.1: signature equality for the legality pass —
	## parameter count, names, and types all equal; type spellings are
	## canonicalized before comparison.
	##
	## @param a: First member.
	## @param b: Second member.
	## @return: true when signatures are identical.
	Function of Boolean is checkerSameSignature(Member is a, Member is b){
		Conditional:if(check: { a:params:length() != b:params:length() }, then: {
			return false;
		});
		local Boolean is same: true;
		local Int is idx: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return same && idx < a:params:length(); },
			iteration: local Function of Boolean(){
				local Parameter is pa: a:params:get(index: idx);
				local Parameter is pb: b:params:get(index: idx);
				Conditional:if(check: { pa:name != pb:name || self:formatTypeString(t: pa:paramType) != self:formatTypeString(t: pb:paramType) }, then: {
					same: false;
				});
				idx: idx + 1;
				return true;
			}
		);
		return same;
	}

	## FUNCTIONS.md §I.6: the import gate. True when [targetName] is
	## usable by [className] in type positions and for construction:
	## the X3 stratum, the class itself, an ancestor, the same source
	## file, or any using entry of the class or its ancestors (type
	## imports, as-imports, and package wildcards all grant).
	##
	## @param className: The enclosing class.
	## @param targetName: The referenced class name.
	## @return: true when access is granted.
	Function of Boolean is classHasAccess(String is className, String is targetName){
		Conditional:if(check: { targetName == '' || self:isPrimitive(t: targetName) || targetName == 'Array' || targetName == 'Map' || targetName == 'List' || targetName == 'String' || targetName == 'Function' || targetName == 'LoopControl' }, then: {
			return true;
		});
		return self:accessInClass(className: className, targetName: targetName, hops: 0);
	}

	## The compilation-unit grant: any class declared in [sourceFile] is
	## accessible, and any same-file class's using entries grant the
	## target (type import, as-import, or package wildcard).
	##
	## @param sourceFile: The visiting class's source file.
	## @param targetName: The referenced class name.
	## @param targetNs: The target's declared namespace ('' when unknown).
	## @return: true when the file grants access.
	Function of Boolean is fileGrants(String is sourceFile, String is targetName, String is targetNs){
		# An empty sourceFile is one anonymous unit (the self-checking
		# snippets): its classes grant one another.
		local Boolean is granted: false;
		self:programClasses:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { !granted && c:sourceFile == sourceFile }, then: {
				Conditional:if(check: { c:name == targetName }, then: {
					granted: true;
					return;
				});
				c:members:each(action: local Function(Member is m){
					Conditional:if(check: { !granted && m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, then: {
						m:initExpr:arrayItems:each(action: local Function(Expression is item){
							Conditional:if(check: { !granted && item:kind == ExpressionKind:ARRAY }, then: {
								local String is terminal: '';
								local String is nsJoined: '';
								item:arrayItems:each(action: local Function(Expression is seg){
									Conditional:if(check: { seg:kind == ExpressionKind:IDENT || seg:kind == ExpressionKind:USING_AS }, then: {
										terminal: seg:stringValue;
									}, else: {
										Conditional:if(check: { nsJoined == '' }, then: {
											nsJoined: seg:stringValue;
										}, else: {
											nsJoined: nsJoined . ':' . seg:stringValue;
										});
									});
								});
								# FUNCTIONS.md Part IV IV.2c: the qualified nested reference
								# ('Outer:Inner') rides the parent's grant — the terminal
								# matches the target's root segment.
								local String is targetRoot: targetName:split(delimiter: ':'):get(index: 0);
								Conditional:if(check: { terminal == targetName || terminal == targetRoot }, then: {
									granted: true;
								});
								Conditional:if(check: { terminal == '' && targetNs != '' && (targetNs == nsJoined || targetNs:startsWith(prefix: nsJoined . ':')) }, then: {
									granted: true;
								});
							});
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
	## @param hops: Recursion budget guard.
	## @return: true when access is granted at this level or above.
	Function of Boolean is accessInClass(String is className, String is targetName, Int is hops){
		Conditional:if(check: { hops >= 64 || className == '' }, then: {
			return false;
		});
		Conditional:if(check: { className == targetName }, then: {
			return true;
		});
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		Conditional:if(check: { cls:name == '' }, then: {
			return false;
		});
		local String is targetNs: '';
		local ClassInfo is tgt: self:findClass(name: targetName);
		Conditional:if(check: { tgt:name != '' }, then: {
			targetNs: tgt:namespaceJoined();
		});
		# The file's compilation unit: same-file classes are accessible, and
		# every same-file class's using declaration grants (nested classes
		# live under the outer class's using).
		Conditional:if(check: { self:fileGrants(sourceFile: cls:sourceFile, targetName: targetName, targetNs: targetNs) }, then: {
			return true;
		});
		local Boolean is granted: false;
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { !granted && m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, then: {
				m:initExpr:arrayItems:each(action: local Function(Expression is item){
					Conditional:if(check: { !granted && item:kind == ExpressionKind:ARRAY }, then: {
						local String is terminal: '';
						local String is nsJoined: '';
						item:arrayItems:each(action: local Function(Expression is seg){
							Conditional:if(check: { seg:kind == ExpressionKind:IDENT || seg:kind == ExpressionKind:USING_AS }, then: {
								terminal: seg:stringValue;
							}, else: {
								Conditional:if(check: { nsJoined == '' }, then: {
									nsJoined: seg:stringValue;
								}, else: {
									nsJoined: nsJoined . ':' . seg:stringValue;
								});
							});
						});
						# FUNCTIONS.md Part IV IV.2c: the same root-segment grant for
						# the qualified nested reference.
						local String is targetRoot2: targetName:split(delimiter: ':'):get(index: 0);
						Conditional:if(check: { terminal == targetName || terminal == targetRoot2 }, then: {
							granted: true;
						});
						Conditional:if(check: { terminal == '' && targetNs != '' && (targetNs == nsJoined || targetNs:startsWith(prefix: nsJoined . ':')) }, then: {
							granted: true;
						});
					});
				});
			});
		});
		Conditional:if(check: { granted }, then: {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:accessInClass(className: baseName, targetName: targetName, hops: hops + 1) }, then: {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## FUNCTIONS.md §I.6: gates a declared type — the base name and every
		## type argument must be accessible from the enclosing class.
	##
	## @param t: The declared type.
	## @param line: The declaration's source line.
	Function is validateTypeAccess(Type is t, Int is line){
		Conditional:if(check: { t:name == '' }, then: {
			return;
		});
		Conditional:if(check: { self:registeredClasses:has(key: t:name) && !self:classHasAccess(className: self:currentClassName, targetName: t:name) }, then: {
			self:addError(line: line, msg: '\'' . t:name . '\' is not imported by \'' . self:currentClassName . '\'; add it to the using declaration (FUNCTIONS.md §I.6).');
		});
		t:params:each(action: local Function(Type is p){
			self:validateTypeAccess(t: p, line: line);
		});
	}

	## Enforces compile-time exhaustiveness of `when` over an enum subject.
	##
	## Conditions may reference variants as bare identifiers, payload calls,
	## or qualified paths. With any variant uncovered and no else arm, a
	## compile error is raised.
	##
	## @param subjectType: Static type of the when subject.
	## @param arms: The when arms.
	## @param line: Source line for diagnostics.
	Function is checkWhenExhaustive(String is subjectType, Array of WhenArm is arms, Int is line){
		Conditional:if(check: { subjectType == '' || !self:allEnumNames:has(key: subjectType) }, then: {
			return;
		});
		local Map of String to String is covered: Map:init();
		local Boolean is hasElse: false;
		arms:each(action: local Function(WhenArm is arm){
			Conditional:if(check: { arm:isElse }, then: {
				hasElse: true;
			});
			arm:conditions:each(action: local Function(Expression is c){
				local String is variantName: '';
				Conditional:if(check: { c:kind == ExpressionKind:CALL && self:allEnumVariants:has(key: c:methodName) && self:allEnumVariants:getString(key: c:methodName, default: '') == subjectType }, then: {
					variantName: c:methodName;
				}, else: {
					Conditional:if(check: { c:kind == ExpressionKind:IDENT && self:allEnumVariants:has(key: c:stringValue) && self:allEnumVariants:getString(key: c:stringValue, default: '') == subjectType }, then: {
						variantName: c:stringValue;
					}, else: {
						Conditional:if(check: { c:kind == ExpressionKind:PATH && c:pathSegments:length() >= 2 && c:pathSegments:get(index: 0) == subjectType && self:allEnumVariants:has(key: c:pathSegments:get(index: 1)) }, then: {
							variantName: c:pathSegments:get(index: 1);
						});
					});
				});
				Conditional:if(check: { variantName != '' }, then: {
					covered:set(key: variantName, value: 'true');
				});
			});
		});
		Conditional:if(check: { hasElse }, then: {
			return;
		});
		local ClassInfo is enumCls: self:findClass(name: subjectType);
		local Array of String is missing: [];
		enumCls:members:each(action: local Function(Member is m){
			Conditional:if(check: { !covered:has(key: m:name) }, then: {
				missing:add(item: m:name);
			});
		});
		Conditional:if(check: { missing:length() > 0 }, then: {
			local String is msg: 'Non-exhaustive \'when\': enum \'' . subjectType . '\' variant(s) not covered (e.g. \'' . missing:get(index: 0) . '\'). Add matching arm(s) or an \'else:\' fallback.';
			self:addError(line: line, msg: msg);
		});
	}

	## Binds payload-carrying variant conditions (is Value:Num(n)) into the
	## local scope, typing each bound identifier from the variant's declared
	## parameters.
	##
	## @param arm: The when arm.
	Function is bindWhenPatternVars(WhenArm is arm){
		arm:conditions:each(action: local Function(Expression is c){
			Conditional:if(check: { c:kind == ExpressionKind:CALL && self:allEnumVariants:has(key: c:methodName) }, then: {
				local String is enumName: self:allEnumVariants:getString(key: c:methodName, default: '');
				local Member is vMem: self:lookupEnumVariant(enumName: enumName, variantName: c:methodName);
				local Int is idx: 0;
				c:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { idx < vMem:params:length() }, then: {
						local Expression is av: arg:value;
						Conditional:if(check: { av:kind == ExpressionKind:IDENT }, then: {
							local Parameter is pDef: vMem:params:get(index: idx);
							self:localVars:set(key: av:stringValue, value: self:formatVarTypeString(t: pDef:paramType));
						});
					});
					idx: idx + 1;
				});
				c:resolvedType: enumName;
			}, else: {
				self:inferExpressionType(expr: c);
			});
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
		local String is cbElem: Primitive:ANY:value();
		Conditional:if(check: { targetType:startsWith(prefix: 'Array of ') && targetType:length() > 9 }, then: {
			cbElem: targetType:substring(start: 9, end: targetType:length());
		}, else: {
			Conditional:if(check: { targetType:startsWith(prefix: 'Array:') && targetType:length() > 6 }, then: {
				cbElem: targetType:substring(start: 6, end: targetType:length());
			});
		});
		Conditional:if(check: { cbElem != Primitive:ANY:value() }, then: {
			local String is elemTypeName: cbElem;
			Conditional:if(check: { method == 'fold' && expr:methodArgs:length() >= 2 }, then: {
				local NamedArg is a0: expr:methodArgs:get(index: 0);
				local String is initType: self:inferExpressionType(expr: a0:value);
				local NamedArg is a1: expr:methodArgs:get(index: 1);
				local Expression is av: a1:value;
				Conditional:if(check: { av:kind == ExpressionKind:ANON_FN }, then: {
					Conditional:if(check: { av:anonParams:length() >= 1 }, then: {
						local Parameter is p0: av:anonParams:get(index: 0);
						Conditional:if(check: { p0:paramType:name == Primitive:ANY:value() || p0:paramType:name == '' }, then: {
							p0:paramType: Type:init(name: initType);
						});
					});
					Conditional:if(check: { av:anonParams:length() >= 2 }, then: {
						local Parameter is p1: av:anonParams:get(index: 1);
						Conditional:if(check: { p1:paramType:name == Primitive:ANY:value() || p1:paramType:name == '' }, then: {
							p1:paramType: Type:init(name: elemTypeName);
						});
					});
				});
			}, else: {
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					local Expression is av: arg:value;
					Conditional:if(check: { av:kind == ExpressionKind:ANON_FN }, then: {
						av:anonParams:each(action: local Function(Parameter is p){
							Conditional:if(check: { p:paramType:name == Primitive:ANY:value() || p:paramType:name == '' }, then: {
								p:paramType: Type:init(name: elemTypeName);
							});
						});
					});
				});
			});
		}, else: {
			Conditional:if(check: { targetType:startsWith(prefix: 'Map:') && method == 'each' }, then: {
				local String is afterMap: targetType:substring(start: 4, end: targetType:length());
				local Int is colonIdx: afterMap:indexOf(search: ':', default: -1);
				local String is valTypeName: Primitive:STRING:value();
				Conditional:if(check: { colonIdx >= 0 && colonIdx + 1 < afterMap:length() }, then: {
					valTypeName: afterMap:substring(start: colonIdx + 1, end: afterMap:length());
				});
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					local Expression is av: arg:value;
					Conditional:if(check: { av:kind == ExpressionKind:ANON_FN }, then: {
						Conditional:if(check: { av:anonParams:length() >= 1 }, then: {
							local Parameter is p0: av:anonParams:get(index: 0);
							Conditional:if(check: { p0:paramType:name == Primitive:ANY:value() || p0:paramType:name == '' }, then: {
								p0:paramType: Type:init(name: 'String');
							});
						});
						Conditional:if(check: { av:anonParams:length() >= 2 }, then: {
							local Parameter is p1: av:anonParams:get(index: 1);
							Conditional:if(check: { p1:paramType:name == Primitive:ANY:value() || p1:paramType:name == '' }, then: {
								p1:paramType: Type:init(name: valTypeName);
							});
						});
					});
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
		local ClassBindings is b: self:bindings;
		return b:isTransparent(c: cls);
	}

	## directly, replacing the previous compiler's mutable container hint.
	##
	## @param expr: AST expression node.
	## @param expected: Contextual type ('' when none).
	## @return: Resolved type name string.
	Function of String is inferExpressionType(Expression is expr, String is expected: ''){
		local ExpressionKind is kind: expr:kind;
		local String is res: 'Any';

		Conditional:if(check: { kind == ExpressionKind:USING_AS }, then: {
			self:addError(line: self:currentLine, msg: 'Instance imports (as ClassName()) may only appear as entries of a using declaration (INSTANCE.md E1).');
			expr:resolvedType: '';
			return '';
		});

		when (kind) {
			is ExpressionKind:STRING: {
				res: Primitive:STRING:value();
			}
			is ExpressionKind:NUMBER: {
				res: Primitive:INT:value();
			}
			is ExpressionKind:FLOAT: {
				res: Primitive:FLOAT:value();
			}
			is ExpressionKind:BOOL: {
				res: Primitive:BOOLEAN:value();
			}
			is ExpressionKind:IDENT: {
				local String is name: expr:stringValue;
				Conditional:if(check: { name == self:names:selfIdent() }, then: {
					res: self:currentClassName;
				}, else: {
					Conditional:if(check: { self:localVars:has(key: name) }, then: {
						res: self:localVars:getString(key: name, default: Primitive:ANY:value());
					}, else: {
						Conditional:if(check: { self:fieldTypes:has(key: name) }, then: {
							Conditional:if(check: { self:unassignedFields:has(key: name) }, then: {
								self:addError(line: self:currentLine, msg: 'Field \'' . name . '\' in class \'' . self:currentClassName . '\' is read before being initialized.');
							});
							local String is owner: self:findMemberOwnerClass(className: self:currentClassName, memberName: name);
							Conditional:if(check: { owner != '' }, then: {
								self:checkMemberVisibility(ownerClass: owner, member: self:findAncestorMember(className: self:currentClassName, memberName: name), memberName: name);
							});
							res: self:fieldTypes:getString(key: name, default: Primitive:ANY:value());
						}, else: {
							Conditional:if(check: { self:allEnumVariants:has(key: name) }, then: {
								res: self:allEnumVariants:getString(key: name, default: Primitive:ANY:value());
							}, else: {
								Conditional:if(check: { self:registeredClasses:has(key: name) }, then: {
									res: name;
								}, else: {
									Conditional:if(check: { self:isPrimitive(t: name) }, then: {
										res: name;
									}, else: {
										Conditional:if(check: { name != '' }, then: {
											self:addError(line: self:currentLine, msg: 'Undefined identifier \'' . name . '\'.');
										});
									});
								});
							});
						});
					});
				});
			}
			is ExpressionKind:PATH: {
				local Array of String is segs: expr:pathSegments;
				Conditional:if(check: { segs:length() > 0 }, then: {
					local String is root: segs:get(index: 0);
					local String is rootType: '';
					Conditional:if(check: { root == self:names:selfIdent() }, then: {
						rootType: self:currentClassName;
						Conditional:if(check: { segs:length() >= 2 && self:unassignedFields:has(key: segs:get(index: 1)) }, then: {
							self:addError(line: self:currentLine, msg: 'Field \'' . segs:get(index: 1) . '\' in class \'' . self:currentClassName . '\' is read before being initialized.');
						});
						Conditional:if(check: { segs:length() >= 2 }, then: {
							local String is fName: segs:get(index: 1);
							local String is fOwner: self:findMemberOwnerClass(className: self:currentClassName, memberName: fName);
							Conditional:if(check: { fOwner != '' }, then: {
								self:checkMemberVisibility(ownerClass: fOwner, member: self:findAncestorMember(className: self:currentClassName, memberName: fName), memberName: fName);
							});
						});
					}, else: {
						Conditional:if(check: { self:localVars:has(key: root) }, then: {
							rootType: self:localVars:getString(key: root, default: '');
						}, else: {
							Conditional:if(check: { self:fieldTypes:has(key: root) }, then: {
								Conditional:if(check: { self:unassignedFields:has(key: root) }, then: {
									self:addError(line: self:currentLine, msg: 'Field \'' . root . '\' in class \'' . self:currentClassName . '\' is read before being initialized.');
								});
								rootType: self:fieldTypes:getString(key: root, default: '');
							}, else: {
								Conditional:if(check: { self:allEnumNames:has(key: root) }, then: {
									rootType: root;
								}, else: {
									Conditional:if(check: { self:registeredClasses:has(key: root) }, then: {
										rootType: root;
										# FUNCTIONS.md Part IV IV.2c: a nested-class reference
										# through the enclosing class's name — 'Outer:Inner' —
										# resolves the inner class's qualified identity. The
										# second segment names a CLASS-kind member.
										Conditional:if(check: { segs:length() == 2 }, then: {
											local ClassInfo is outerCls: self:findClass(name: root);
											Conditional:if(check: { outerCls:name != '' }, then: {
												outerCls:members:each(action: local Function(Member is m){
													Conditional:if(check: { m:kind == MemberKind:CLASS && m:nestedClass:name == segs:get(index: 1) }, then: {
														rootType: outerCls:qualifiedName() . ':' . segs:get(index: 1);
													});
												});
											});
										});
										# INSTANCE.md §2.3: fields and values are not reachable
										# through a class-name prefix — methods only. A PATH
										# rooted at a non-type-level class name with further
										# segments is a prefixed field access: rejected.
										Conditional:if(check: { segs:length() >= 2 && !self:allEnumNames:has(key: root) && !self:isPrimitive(t: root) && root != 'Array' && root != 'Map' && root != 'List' && root != 'String' && root != 'Function' && root != 'LoopControl' && rootType != root . ':' . segs:get(index: 1) }, then: {
											self:addError(line: self:currentLine, msg: 'Fields are not reachable through the class-name prefix \'' . root . '\'; call a method on the instance (INSTANCE.md §2.3).');
											rootType: '';
										});
									});
								});
							});
						});
					});
					local PathResolveLoop is pLoop: PathResolveLoop:init(tc: self, segs: segs, rootType: rootType);
					While:run(loop: pLoop);
					Conditional:if(check: { pLoop:currType != '' }, then: {
						res: pLoop:currType;
					});
				});
			}
			is ExpressionKind:BINARY: {
				# FUNCTIONS.md Part II: the expected type flows into the
				# operands so a value-yielding branch call nested in an
				# expression (e.g. `n + if(...)`) types in context.
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr, expected: expected);
				local String is rightT: self:inferExpressionType(expr: expr:rightExpr, expected: expected);
				local String is op: expr:binaryOp;
				when (op) {
					is '.': {
						res: Primitive:STRING:value();
					}
					is '==', '!=', 'is', '<', '<=', '>', '>=': {
						res: Primitive:BOOLEAN:value();
						# FUNCTIONS.md hardening (D5): relational ordering on
						# String is lexicographic — and only String-to-String.
						local Boolean is isRel: op == '<' || op == '<=' || op == '>' || op == '>=';
						local Boolean is leftStr: leftT == 'String';
						local Boolean is rightStr: rightT == 'String';
						Conditional:if(check: { isRel && (leftStr || rightStr) && !(leftStr && rightStr) }, then: {
							self:addError(line: self:currentLine, msg: 'Relational operator \'' . op . '\' requires two String operands (got \'' . leftT . '\' and \'' . rightT . '\').');
						});
					}
					is '&&', '||': {
						res: Primitive:BOOLEAN:value();
					}
					is '+', '-', '*', '/', '%': {
						res: Conditional:if(check: { leftT == 'Float' || rightT == 'Float' }, then: { 'Float' }, else: { Primitive:INT:value() });
					}
					is '&', '|', '^', '<<', '>>': {
						res: Primitive:INT:value();
						Conditional:if(check: { (leftT != '' && leftT != 'Any' && leftT != Primitive:INT:value()) ||
							(rightT != '' && rightT != 'Any' && rightT != Primitive:INT:value()) }, then: {
							local String is msg: 'Bitwise operator \'' . op . '\' requires Int operands (got \'' . leftT . '\' and \'' . rightT . '\').';
							self:addError(line: self:currentLine, msg: msg);
						});
					}
					else: {
						res: Primitive:INT:value();
					}
				}
			}
			is ExpressionKind:CAST: {
				local String is innerT: self:inferExpressionType(expr: expr:leftExpr);
				local String is target: expr:castTarget;
				local String is src: Conditional:if(check: { innerT != '' }, then: { innerT }, else: { Primitive:ANY:value() });
				local Boolean is isFormat: target == 'Hex' || target == 'Bin' || target == 'Oct';
				# Every non-format cast takes no arguments.
				Conditional:if(check: { expr:castArgs:length() > 0 && !isFormat }, then: {
					self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' takes no arguments.');
				});
				when (target) {
					is 'Hex', 'Bin', 'Oct': {
						Conditional:if(check: { expr:castArgs:length() > 1 }, then: {
							self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' accepts at most one width argument.');
						});
						Conditional:if(check: { src != 'Any' && src != 'String' && src != Primitive:INT:value() }, then: {
							self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' requires an Int or String operand (got \'' . src . '\').');
						});
						res: Conditional:if(check: { src == 'String' }, then: { Primitive:INT:value() }, else: { 'String' });
					}
					else: {
						Conditional:if(check: { self:allEnumNames:has(key: target) }, then: {
							self:addError(line: self:currentLine, msg: 'Cannot cast to enum \'' . target . '\'; construct a variant instead.');
							res: target;
						}, else: {
							Conditional:if(check: { self:castableMethod(srcType: src, target: target) != '' }, then: {
								# Declared cast: the source class maps the target to a
								# producing method (G6 emits the call).
								res: target;
							}, else: {
								Conditional:if(check: { self:isPrimitive(t: target) && target != Primitive:ANY:value() }, then: {
									# Primitive conversion casts take priority over the
									# class-cast path: Int as String is the machine
									# conversion even though a String class is loaded.
									# Any is excluded — it is the universal class-cast
									# target, always related. These die when the
									# primitive classes land in Spec and declare their
									# conversions.
									Conditional:if(check: { !self:isCastable(src: src, target: target) }, then: {
										self:addError(line: self:currentLine, msg: 'Cannot cast \'' . src . '\' to \'' . target . '\'.');
									});
									res: target;
								}, else: {
									Conditional:if(check: { self:registeredClasses:has(key: target) || self:registeredClasses:has(key: target:split(delimiter: ':'):get(index: 0)) }, then: {
										# Class casts are inheritance-based: unrelated classes
										# cannot cast, Any casts to anything.
										local Boolean is related: src == Primitive:ANY:value() || self:isSubclassOf(subName: src, baseName: target) || self:isSubclassOf(subName: target, baseName: src);
										Conditional:if(check: { !related }, then: {
											self:addError(line: self:currentLine, msg: 'Cannot cast \'' . src . '\' to unrelated class \'' . target . '\'.');
										});
										res: target;
									}, else: {
										self:addError(line: self:currentLine, msg: 'Unknown cast target \'' . target . '\'.');
										res: 'Any';
									});
								});
							});
						});
					}
				}
			}
			is ExpressionKind:UNARY: {
				local String is innerT: self:inferExpressionType(expr: expr:unaryExpr);
				Conditional:if(check: { expr:unaryOp == '~' && innerT != '' && innerT != 'Any' && innerT != Primitive:INT:value() }, then: {
					local String is msg: 'Bitwise complement \'~\' requires an Int operand (got \'' . innerT . '\').';
					self:addError(line: self:currentLine, msg: msg);
				});
				Conditional:if(check: { (expr:unaryOp == '++' || expr:unaryOp == '--' || expr:unaryOp == 'post++' || expr:unaryOp == 'post--') && innerT != '' && innerT != 'Any' && innerT != Primitive:INT:value() }, then: {
					local String is msg: 'Operator \'' . expr:unaryOp . '\' requires an Int operand (got \'' . innerT . '\').';
					self:addError(line: self:currentLine, msg: msg);
				});
				Conditional:if(check: { expr:unaryOp == '!' }, then: {
					res: Primitive:BOOLEAN:value();
				}, else: {
					res: innerT;
				});
			}
			is ExpressionKind:ARRAY: {
				# Bidirectional: a container expectation from the declaration
				# site types the literal directly — no hint state. The
				# elements must still be assignable to the declared element
				# type ('Array of Int is flags: ['on']' is a compile error).
				Conditional:if(check: { expected != '' && (expected:startsWith(prefix: 'Array') || expected:startsWith(prefix: 'List')) }, then: {
					local String is elemT: '';
					local Int is eColon: expected:indexOf(search: ':', default: -1);
					local Int is eOf: expected:indexOf(search: ' of ', default: -1);
					Conditional:if(check: { eColon >= 0 && (expected:startsWith(prefix: 'Array:') || expected:startsWith(prefix: 'List:')) }, then: {
						elemT: expected:substring(start: eColon + 1, end: expected:length());
					}, else: {
						Conditional:if(check: { eOf >= 0 }, then: {
							elemT: expected:substring(start: eOf + 4, end: expected:length());
						});
					});
					expr:arrayItems:each(action: local Function(Expression is item){
						local String is itemT: self:inferExpressionType(expr: item);
						Conditional:if(check: { elemT != '' && itemT != '' && itemT != Primitive:ANY:value() && !self:isAssignable(target: elemT, source: itemT) }, then: {
							self:addError(line: self:currentLine, msg: "Cannot assign 'Array:" . itemT . "' to 'Array:" . elemT . "'.");
						});
					});
					res: expected;
				}, else: {
					local String is firstElemType: '';
					expr:arrayItems:each(action: local Function(Expression is item){
						local String is itemT: self:inferExpressionType(expr: item);
						Conditional:if(check: { firstElemType == '' && itemT != '' && itemT != Primitive:ANY:value() }, then: {
							firstElemType: itemT;
						});
					});
					Conditional:if(check: { firstElemType != '' }, then: {
						res: 'Array:' . firstElemType;
					}, else: {
						res: 'Array';
					});
				});
			}
			is ExpressionKind:MAP: {
				Conditional:if(check: { expected != '' && expected:startsWith(prefix: 'Map') }, then: {
					# Value type from the expectation ('Map of K to V' both
					# spellings); values must be assignable to it.
					local String is valT: '';
					# Both spellings: 'Map of K to V' and the canonical
					# colon form 'Map:K:V' (formatTypeString's output).
					local Array of String is mParts: expected:split(delimiter: ':');
					Conditional:if(check: { mParts:length() > 2 }, then: {
						valT: mParts:get(index: 2);
					}, else: {
						local String is kv: expected:substring(start: 4, end: expected:length());
						Conditional:if(check: { kv:startsWith(prefix: ' of ') }, then: {
							kv: kv:substring(start: 4, end: kv:length());
						});
						local Int is toIdx: kv:indexOf(search: ' to ', default: -1);
						Conditional:if(check: { toIdx >= 0 }, then: {
							valT: kv:substring(start: toIdx + 4, end: kv:length());
						});
					});
					expr:mapKeys:each(action: local Function(Expression is k){
						self:inferExpressionType(expr: k);
					});
					expr:mapValues:each(action: local Function(Expression is v){
						local String is vT: self:inferExpressionType(expr: v);
						Conditional:if(check: { valT != '' && vT != '' && vT != Primitive:ANY:value() && !self:isAssignable(target: valT, source: vT) }, then: {
							self:addError(line: self:currentLine, msg: "Cannot assign 'Map:String:" . vT . "' to 'Map:String:" . valT . "'.");
						});
					});
					res: expected;
				}, else: {
					local String is firstKeyType: '';
					local String is firstValType: '';
					expr:mapKeys:each(action: local Function(Expression is k){
						local String is kt: self:inferExpressionType(expr: k);
						Conditional:if(check: { firstKeyType == '' && kt != '' && kt != Primitive:ANY:value() }, then: {
							firstKeyType: kt;
						});
					});
					expr:mapValues:each(action: local Function(Expression is v){
						local String is vt: self:inferExpressionType(expr: v);
						Conditional:if(check: { firstValType == '' && vt != '' && vt != Primitive:ANY:value() }, then: {
							firstValType: vt;
						});
					});
					Conditional:if(check: { firstKeyType != '' && firstValType != '' }, then: {
						res: 'Map:' . firstKeyType . ':' . firstValType;
					}, else: {
						res: 'Map';
					});
				});
			}
			is ExpressionKind:FIELD_ACCESS: {
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr);
				Conditional:if(check: { leftT == '' || leftT == 'Any' || self:isPrimitive(t: leftT) }, then: {
					res: 'Any';
				}, else: {
					local Array of String is faParts: leftT:split(delimiter: ':');
					local String is faBase: faParts:get(index: 0);
					local String is fName: expr:stringValue;
					local String is fOwner: self:findMemberOwnerClass(className: faBase, memberName: fName);
					Conditional:if(check: { fOwner != '' }, then: {
						self:checkMemberVisibility(ownerClass: fOwner, member: self:findAncestorMember(className: faBase, memberName: fName), memberName: fName);
					});
					local String is fT: self:lookupFieldType(className: leftT, fieldName: fName);
					res: Conditional:if(check: { fT != '' }, then: { fT }, else: { 'Any' });
				});
			}
			is ExpressionKind:INDEX: {
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr);
				self:inferExpressionType(expr: expr:rightExpr);
				# Element extraction accepts both container spellings.
				Conditional:if(check: { leftT:startsWith(prefix: 'Array of ') && leftT:length() > 9 }, then: {
					res: leftT:substring(start: 9, end: leftT:length());
				}, else: {
					Conditional:if(check: { leftT:startsWith(prefix: 'Array:') && leftT:length() > 6 }, then: {
						res: leftT:substring(start: 6, end: leftT:length());
					}, else: {
						Conditional:if(check: { leftT:startsWith(prefix: 'Map:') && leftT:length() > 4 }, then: {
							local String is afterMap: leftT:substring(start: 4, end: leftT:length());
							local Int is colonIdx: afterMap:indexOf(search: ':', default: -1);
							Conditional:if(check: { colonIdx >= 0 && colonIdx + 1 < afterMap:length() }, then: {
								res: afterMap:substring(start: colonIdx + 1, end: afterMap:length());
							}, else: {
								res: Primitive:STRING:value();
							});
						}, else: {
							Conditional:if(check: { leftT == 'Map' }, then: {
								res: Primitive:STRING:value();
							}, else: {
								res: 'Any';
							});
						});
					});
				});
			}
			is ExpressionKind:WHEN: {
				local String is subjectType: self:inferExpressionType(expr: expr:whenSubject);
				local String is armType: 'Any';
				expr:whenArms:each(action: local Function(WhenArm is arm){
					self:bindWhenPatternVars(arm: arm);
					Conditional:if(check: { arm:hasValueExpr }, then: {
						local String is vt: self:inferExpressionType(expr: arm:valueExpr);
						Conditional:if(check: { armType == Primitive:ANY:value() && vt != '' && vt != Primitive:ANY:value() }, then: {
							armType: vt;
						});
					});
					arm:body:each(action: local Function(Statement is s){
						self:checkStatement(stmt: s);
					});
				});
				self:checkWhenExhaustive(subjectType: subjectType, arms: expr:whenArms, line: self:currentLine);
				res: armType;
			}
			is ExpressionKind:ANON_FN: {
				local Map of String to String is savedVars: Map:init();
				local Array of String is existingKeys: self:localVars:keys();
				existingKeys:each(action: local Function(String is k){
					savedVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
				});
				local String is savedRet: self:currentMethodReturnType;
				local Expression is savedAnonNode: self:currentAnonNode;
				self:currentAnonNode: expr;
				# FUNCTIONS.md Part II: the yield flag scopes to THIS closure —
				# the enclosing closure's last-statement check must not leak
				# into nested closures' return typing.
				local Boolean is savedYieldFlag: self:checkingValueYield;
				self:checkingValueYield: false;

				Conditional:if(check: { !self:inBranchClosure }, then: {
					# FUNCTIONS.md Part IV V1: the bidirectional closure typing —
					# a closure literal assigned into a `Function of X` context
					# types its body against X, so its own type comes out
					# `Function of X` and the narrowed param accepts it.
					Conditional:if(check: { expected:startsWith(prefix: 'Function:') && self:isVoid(t: expr:anonReturnType:name) }, then: {
						expr:anonReturnType: Type:init(name: expected:substring(start: 9, end: expected:length()));
					});
					self:currentMethodReturnType: self:resolveReturnType(t: expr:anonReturnType);
				});
				expr:anonParams:each(action: local Function(Parameter is p){
					self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
				});
				local Int is bodyLen: expr:anonBody:length();
				local Int is bodyIdx: 0;
				expr:anonBody:each(action: local Function(Statement is s){
					self:anonDepth: self:anonDepth + 1;
					# FUNCTIONS.md Part II: the last statement of a
					# value-yielding branch closure is the branch's yield.
					Conditional:if(check: { self:inValueBranch && bodyIdx == bodyLen - 1 }, then: {
						self:checkingValueYield: true;
					});
					self:checkStatement(stmt: s);
					self:checkingValueYield: false;
					self:anonDepth: self:anonDepth - 1;
					bodyIdx: bodyIdx + 1;
				});

				self:localVars: savedVars;
				self:currentMethodReturnType: savedRet;
				# FUNCTIONS.md Part II: the Kotlin convention — the closure
				# body determines the return. Return-site write-backs happened
				# during the body check (the RETURN arm); here only the
				# explicit-terminator last-expression form is handled, reading
				# the type the body check already resolved — never
				# re-inferring.
				local Int is lastIdx: expr:anonBody:length() - 1;
				Conditional:if(check: { lastIdx >= 0 }, then: {
					local Statement is lastStmt: expr:anonBody:get(index: lastIdx);
					Conditional:if(check: { lastStmt:kind == StatementKind:EXPR }, then: {
						local String is lastT: lastStmt:exprStmt:resolvedType;
						Conditional:if(check: { self:isVoid(t: expr:anonReturnType:name) }, then: {
							Conditional:if(check: { lastT != '' && !self:isVoid(t: lastT) }, then: {
								expr:anonReturnType: Type:init(name: lastT);
							});
						}, else: {
							Conditional:if(check: { lastT != '' && !self:isAssignable(target: expr:anonReturnType:name, source: lastT) }, then: {
								local String is msg: 'The closure\'s last expression yields \'' . lastT . '\', but the closure must return \'' . expr:anonReturnType:name . '\' (FUNCTIONS.md Part II).';
								self:addError(line: self:currentLine, msg: msg);
							});
						});
					});
				});
				self:currentAnonNode: savedAnonNode;
				self:checkingValueYield: savedYieldFlag;
				local String is anonRetName: expr:anonReturnType:name;
				Conditional:if(check: { anonRetName != '' && !self:isVoid(t: anonRetName) }, then: {
					res: 'Function:' . self:formatTypeString(t: expr:anonReturnType);
				}, else: {
					res: 'Function';
				});
			}
			is ExpressionKind:CALL: {
				res: self:inferCall(expr: expr, expected: expected);
			}
			else: {
				res: 'Any';
			}
		}

		Conditional:if(check: { kind == ExpressionKind:CALL }, then: {
			self:checkCallArguments(callExpr: expr);
		});

		expr:resolvedType: res;
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
	Function of String is inferCall(Expression is expr, String is expected: ''){
		local String is targetType: self:inferExpressionType(expr: expr:methodTarget);
		local String is method: expr:methodName;
		local String is res: 'Any';

		local String is targetName: expr:methodTarget:stringValue;
		Conditional:if(check: { targetName == '' && expr:methodTarget:kind == ExpressionKind:PATH && expr:methodTarget:pathSegments:length() > 0 }, then: {
			targetName: expr:methodTarget:pathSegments:get(index: expr:methodTarget:pathSegments:length() - 1);
		});

		# INSTANCE.md E5/E7: the call model. A class-name receiver admits
		# only init, unless the enclosing class instance-imports the class
		# (elided dispatch) or the stratum is type-level by design (enums,
		# primitives, containers, transparent runtime types). Conversely,
		# init on a non-class receiver is construct-only and banned.
		local String is recvName: '';
		Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:IDENT || expr:methodTarget:kind == ExpressionKind:PATH }, then: {
			local String is cand: targetName;
			Conditional:if(check: { cand != '' && cand != self:names:selfIdent() && self:registeredClasses:has(key: cand) && !self:localVars:has(key: cand) && !self:fieldTypes:has(key: cand) }, then: {
				recvName: cand;
			});
		});
		Conditional:if(check: { recvName != '' && expr:methodName != 'init' }, then: {
			local Boolean is isTypeLevel: self:allEnumNames:has(key: recvName) || self:isPrimitive(t: recvName) || recvName == 'Array' || recvName == 'Map' || recvName == 'List' || recvName == 'String' || recvName == 'Function' || recvName == 'LoopControl';
			Conditional:if(check: { !isTypeLevel }, then: {
				Conditional:if(check: { !self:isAsImportedInherited(className: recvName) }, then: {
					Conditional:if(check: { recvName == self:currentClassName }, then: {
						self:addError(line: self:currentLine, msg: 'Cannot call members of \'' . recvName . '\' through the class name inside \'' . recvName . '\' itself; use self (INSTANCE.md §2.2).');
					}, else: {
						self:addError(line: self:currentLine, msg: 'Members of \'' . recvName . '\' are callable only through an instance; instance-import it (\'as ' . recvName . '()\') (FUNCTIONS.md §I.6).');
					});
				});
			});
		});
		Conditional:if(check: { recvName == '' && expr:methodName == 'init' }, then: {
			self:addError(line: self:currentLine, msg: '\'init\' is construct-only; call it on the class name (INSTANCE.md E7).');
		});

		# INSTANCE.md §2.3/E9: bare-scope resolution for self-receiver
		# calls. The providers are the enclosing class (own and inherited
		# members) plus its as-imported classes, one level deep. Exactly
		# one provider resolves; two or more collide and force
		# qualification; zero is an error — the old behavior silently
		# invented CurrentClass_method and died in gcc.
		Conditional:if(check: { recvName == '' && expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:stringValue == self:names:selfIdent() && expr:methodName != 'init' && expr:methodName != 'typeName' && !self:localVars:has(key: expr:methodName) && !self:fieldTypes:has(key: expr:methodName) }, then: {
			local String is ownOwner: self:findMemberOwnerClass(className: self:currentClassName, memberName: expr:methodName);
			local Array of String is bsProviders: self:bareScopeProviders(methodName: expr:methodName);
			local Int is providerTotal: bsProviders:length() + Conditional:if(check: { ownOwner != '' }, then: { 1 }, else: { 0 });
			Conditional:if(check: { providerTotal > 1 }, then: {
				local String is listed: '';
				Conditional:if(check: { ownOwner != '' }, then: {
					listed: 'the enclosing class';
				});
				bsProviders:each(action: local Function(String is prov){
					Conditional:if(check: { listed == '' }, then: {
						listed: prov;
					}, else: {
						listed: listed . ' and ' . prov;
					});
				});
				self:addError(line: self:currentLine, msg: 'Function \'' . expr:methodName . '\' is provided by ' . listed . '; qualify the call (' . self:names:selfIdent() . ':' . expr:methodName . ' or the class name) (INSTANCE.md §2.3).');
				expr:resolvedType: '';
				return '';
			});
			Conditional:if(check: { providerTotal == 0 }, then: {
				self:addError(line: self:currentLine, msg: 'Undefined function \'' . expr:methodName . '\' on class \'' . self:currentClassName . '\' (INSTANCE.md E9).');
				expr:resolvedType: '';
				return '';
			});
			Conditional:if(check: { ownOwner == '' }, then: {
				local String is provider: bsProviders:get(index: 0);
				# The bare-scope branch runs before arg inference: type the
				# arguments now so overload selection sees exact types. Branch
				# closures (args 1+) of a Conditional call keep the enclosing
				# method's return type (FUNCTIONS.md Part II).
				local Boolean is bareIsBranch: provider == 'Conditional' && expr:argCount() >= 2 && expr:argCount() <= 4;
				# FUNCTIONS.md Part IV: the bare form carries the value-yield
				# semantics exactly like the qualified call.
				local Boolean is bareIsValue: bareIsBranch && expr:argCount() == 3 && expected != '' && !self:isVoid(t: expected) && expr:argValue(index: 1):kind == ExpressionKind:ANON_FN && expr:argValue(index: 2):kind == ExpressionKind:ANON_FN;
				local Int is bareIdx: 0;
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { bareIsBranch && bareIdx >= 1 }, then: {
						self:inBranchClosure: true;
						self:inValueBranch: bareIsValue;
						self:currentYieldExpected: '';
						Conditional:if(check: { bareIsValue }, then: {
							self:currentYieldExpected: expected;
						});
					});
					self:inferExpressionType(expr: arg:value);
					self:inBranchClosure: false;
					self:inValueBranch: false;
					self:currentYieldExpected: '';
					bareIdx: bareIdx + 1;
				});
				self:selectOverload(className: provider, methodName: expr:methodName, expr: expr);
				# FUNCTIONS.md Part IV IV.1: the as-import grants FUNCTIONS
				# ONLY under the callee's visibility — a `local` member of the
				# imported class is not callable through the import. The same
				# check the qualified path runs.
				local Member is bareSelected: self:lookupOverloadedMember(className: provider, methodName: expr:methodName, idx: expr:overloadIndex);
				Conditional:if(check: { bareSelected:name != '' }, then: {
					self:checkMemberVisibility(ownerClass: provider, member: bareSelected, memberName: expr:methodName);
				});
				expr:bareProvider: provider;
				local String is providerRet: self:lookupMethodReturnType(className: provider, methodName: expr:methodName);
				Conditional:if(check: { providerRet == '' }, then: {
					providerRet: 'Any';
				});
				Conditional:if(check: { bareIsValue }, then: {
					local Expression is bareThen: expr:argValue(index: 1);
					local Expression is bareElse: expr:argValue(index: 2);
					local String is bareThenT: bareThen:anonReturnType:name;
					local String is bareElseT: bareElse:anonReturnType:name;
					Conditional:if(check: { self:isVoid(t: bareThenT) || self:isVoid(t: bareElseT) }, then: {
						self:addError(line: self:currentLine, msg: 'A value-yielding branch requires both branches to end in an expression (FUNCTIONS.md Part II).');
						res: 'void';
					}, else: {
						Conditional:if(check: { !self:isAssignable(target: bareThenT, source: bareElseT) && !self:isAssignable(target: bareElseT, source: bareThenT) }, then: {
							self:addError(line: self:currentLine, msg: 'Branch yields mismatched types: \'' . bareThenT . '\' and \''. bareElseT . '\'.');
							res: bareThenT;
						}, else: {
							res: Conditional:if(check: { bareThenT == Primitive:ANY:value() }, then: { bareElseT }, else: { bareThenT });
						});
					});
					expr:resolvedType: res;
					return res;
				});
				res: providerRet;
				expr:resolvedType: res;
				return res;
			});
		});
		# FUNCTIONS.md Part II: is this a Conditional branch call? Branch
		# closure bodies (arguments 1+) type-check against the enclosing
		# method's return type — they inline into it. The self-call
		# disjunct lets the wrapper's own self-calls pre-type their check
		# closures too.
		local Boolean is isBranchCall: expr:methodName == 'if' && expr:argCount() >= 2 && expr:argCount() <= 4 && (((targetType == 'Conditional' && expr:methodTarget:kind == ExpressionKind:IDENT) || (expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:stringValue == self:names:selfIdent() && self:currentClassName == 'Conditional')) || expr:bareProvider == 'Conditional');
		# FUNCTIONS.md Part II: the value-yielding form — a 3-arg branch
		# call in a context that expects a value (a declaration, an
		# assignment, a return). Both branch closures must be inline
		# literals; their last expressions are the yields.
		local Boolean is isValueBranch: isBranchCall && expr:argCount() == 3 && expected != '' && !self:isVoid(t: expected) && expr:argValue(index: 1):kind == ExpressionKind:ANON_FN && expr:argValue(index: 2):kind == ExpressionKind:ANON_FN;
		# FUNCTIONS.md Part II: the value form is structural — BOTH branch
		# closures must end in a return-expression (the yield). Closures that
		# end in assignments are statement-style branches even in a
		# value-typed context; they stay void-routed.
		Conditional:if(check: { isValueBranch }, then: {
			local Expression is tAnon: expr:argValue(index: 1);
			local Expression is eAnon: expr:argValue(index: 2);
			local Int is tLen: tAnon:anonBody:length();
			local Int is eLen: eAnon:anonBody:length();
			Conditional:if(check: { tLen == 0 || eLen == 0 }, then: {
				isValueBranch: false;
			}, else: {
				local Statement is tLast: tAnon:anonBody:get(index: tLen - 1);
				local Statement is eLast: eAnon:anonBody:get(index: eLen - 1);
				Conditional:if(check: { !(tLast:kind == StatementKind:RETURN && tLast:hasReturnExpr) || !(eLast:kind == StatementKind:RETURN && eLast:hasReturnExpr) }, then: {
					isValueBranch: false;
				});
			});
		});
		local Int is argIdx: 0;
		local Boolean is savedBranchFlag: self:inBranchClosure;
		self:inBranchClosure: false;
		local Boolean is isWhileLoop: (targetType == 'While' || targetName == 'While') && (method == 'loop' || method == 'init' || method == 'condition');
		local Map of String to String is savedWhileVars;
		Conditional:if(check: { isWhileLoop }, then: {
			savedWhileVars: Map:init();
			local Array of String is existingKeys: self:localVars:keys();
			existingKeys:each(action: local Function(String is k){
				savedWhileVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
			});
			local Int is posIdx: 0;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:if(check: { arg:value:kind == ExpressionKind:ARRAY && arg:value:anonParams:length() > 0 }, then: {
					arg:value:anonParams:each(action: local Function(Parameter is p){
						Conditional:if(check: { p:hasDefault }, then: {
							self:inferExpressionType(expr: p:defaultExpr);
						});
						self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
					});
				});
				Conditional:if(check: { arg:name == 'evaluate' && arg:value:kind == ExpressionKind:ANON_FN }, then: {
					Conditional:if(check: { arg:value:anonReturnType:name == '' || arg:value:anonReturnType:name == self:names:voidName() }, then: {
						arg:value:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
					});
				}, else: {
					Conditional:if(check: { arg:name == '' && arg:value:kind == ExpressionKind:ANON_FN }, then: {
						Conditional:if(check: { posIdx == 1 || (posIdx == 0 && expr:methodArgs:length() == 2) }, then: {
							Conditional:if(check: { arg:value:anonReturnType:name == '' || arg:value:anonReturnType:name == self:names:voidName() }, then: {
								arg:value:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
							});
						});
					});
				});
				posIdx: posIdx + 1;
			});
		});

		self:bindContainerCallbackParams(targetType: targetType, method: method, expr: expr);
		expr:methodArgs:each(action: local Function(NamedArg is arg){
			Conditional:if(check: { isBranchCall && argIdx == 0 && arg:value:kind == ExpressionKind:ANON_FN }, then: {
				Conditional:if(check: { arg:value:anonReturnType:name == '' || arg:value:anonReturnType:name == self:names:voidName() }, then: {
					arg:value:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
				});
			});
			Conditional:if(check: { isBranchCall && argIdx >= 1 }, then: {
				self:inBranchClosure: true;
				self:inValueBranch: isValueBranch;
				self:currentYieldExpected: '';
				Conditional:if(check: { isValueBranch }, then: {
					self:currentYieldExpected: expected;
				});
			});
			self:inferExpressionType(expr: arg:value);
			self:inBranchClosure: false;
			self:inValueBranch: false;
			self:currentYieldExpected: '';
			argIdx: argIdx + 1;
		});

		Conditional:if(check: { isWhileLoop }, then: {
			self:localVars: savedWhileVars;
			expr:resolvedType: 'Void';
			return 'Void';
		});

		Conditional:if(check: { targetType == self:names:selfIdent() || targetType == '' }, then: {
			targetType: self:currentClassName;
		});

		# Sysinternal floor access by qualified chain: ONLY base:sys
		# wrappers may call the floor — everyone else goes through the
		# same-name wrapper (the sysinternal discipline).
		Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:PATH }, then: {
			local String is qJoined: '';
			expr:methodTarget:pathSegments:each(action: local Function(String is seg){
				Conditional:if(check: { qJoined == '' }, then: {
					qJoined: seg;
				}, else: {
					qJoined: qJoined . ':' . seg;
				});
			});
			Conditional:if(check: { qJoined:contains(needle: ':sysinternal:') }, then: {
				local ClassInfo is callerCls: self:findClass(name: self:currentClassName);
				local String is callerNs: callerCls:namespaceJoined();
				Conditional:if(check: { callerNs != 'base:sys' }, then: {
					self:addError(line: self:currentLine, msg: 'The sysinternal floor is only accessible from base:sys wrappers; call the base:sys wrapper instead (call from \'' . callerNs . '\').');
				});
				res: self:lookupMethodReturnType(className: qJoined, methodName: method);
				expr:resolvedType: res;
				return res;
			});
		});

		# Namespace-qualified chains: `base:sysinternal:Buf()` and method
		# calls on one — the chain's type is the named class.
		Conditional:if(check: { targetType == Primitive:ANY:value() || targetType == '' }, then: {
			Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:PATH }, then: {
				local ClassInfo is qCls: self:findClass(name: method);
				Conditional:if(check: { qCls:name == method }, then: {
					targetType: method;
				});
			}, else: {
				Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:CALL }, then: {
					local Expression is qInner: expr:methodTarget;
					Conditional:if(check: { qInner:methodTarget:kind == ExpressionKind:PATH }, then: {
						local String is qCand: qInner:methodName;
						local ClassInfo is qCls: self:findClass(name: qCand);
						Conditional:if(check: { qCand != '' && qCls:name == qCand }, then: {
							targetType: qCand;
						});
					});
				});
			});
		});

		Conditional:if(check: { !self:allEnumNames:has(key: targetType) && targetType != '' && targetType != 'Any' }, then: {
			local Array of String is cParts: targetType:split(delimiter: ':');
			local String is cBase: cParts:get(index: 0);
			local String is mOwner: self:findMemberOwnerClass(className: cBase, memberName: method);
			Conditional:if(check: { mOwner != '' }, then: {
				self:checkMemberVisibility(ownerClass: mOwner, member: self:lookupAnyMember(className: cBase, methodName: method), memberName: method);
			});
		});
		Conditional:if(check: { targetType == Primitive:ANY:value() && method != 'toString' && method != 'typeName' && method != 'init' }, then: {
			self:addError(line: self:currentLine, msg: 'Member \'' . method . '\' is not part of the root contract; cast the Any-typed value to a concrete class before calling it (value as ClassName).');
		});

		local String is fnVarT: '';
		Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:stringValue == self:names:selfIdent() }, then: {
			fnVarT: self:localVars:getString(key: method, default: self:fieldTypes:getString(key: method, default: ''));
		});
		Conditional:if(check: { targetType == 'Parallel' && method == 'run' }, then: {
			local Boolean is hasWorker: false;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				local String is aName: arg:name;
				local String is aType: self:inferExpressionType(expr: arg:value);
				Conditional:if(check: { aName == 'threads' || aName == 'iterations' }, then: {
					Conditional:if(check: { aType != Primitive:INT:value() && aType != 'Any' }, then: {
						self:addError(line: self:currentLine, msg: 'Parallel:run \'' . aName . '\' argument must be Int, found \'' . aType . '\'.');
					});
				}, else: {
					Conditional:if(check: { aName == 'worker' }, then: {
						hasWorker: true;
						Conditional:if(check: { !aType:startsWith(prefix: 'Function') && aType != 'Any' }, then: {
							self:addError(line: self:currentLine, msg: 'Parallel:run \'worker\' argument must be a Function, found \'' . aType . '\'.');
						});
					});
				});
			});
			Conditional:if(check: { !hasWorker }, then: {
				self:addError(line: self:currentLine, msg: 'Parallel:run requires \'worker\' named argument.');
			});
			res: Primitive:INT:value();
		}, else: {
			Conditional:if(check: { fnVarT:startsWith(prefix: 'Function') }, then: {
				Conditional:if(check: { fnVarT:startsWith(prefix: 'Function:') && fnVarT:length() > 9 }, then: {
					res: fnVarT:substring(start: 9, end: fnVarT:length());
				}, else: {
					res: 'Any';
				});
			}, else: {
				Conditional:if(check: { self:allEnumVariants:has(key: method) && (self:allEnumNames:has(key: targetType) || targetType == self:currentClassName) }, then: {
					res: self:allEnumVariants:getString(key: method, default: Primitive:ANY:value());
				}, else: {
					Conditional:if(check: { method == 'typeName' && self:registeredClasses:has(key: targetType) }, then: {
						res: Primitive:STRING:value();
					}, else: {
						Conditional:if(check: { method == 'init' && self:registeredClasses:has(key: targetType) && !self:allEnumNames:has(key: targetType) }, then: {
							# FUNCTIONS.md §I.2: init overloads are selected and stamped like any member.
							self:selectOverload(className: targetType, methodName: 'init', expr: expr);
							# FUNCTIONS.md §I.6: construction requires the import too — the
							# X3 stratum, the class itself, an ancestor, the same file, or the
							# class's own using grants it.
							Conditional:if(check: { !self:classHasAccess(className: self:currentClassName, targetName: targetType:split(delimiter: ':'):get(index: 0)) }, then: {
								self:addError(line: self:currentLine, msg: '\'' . targetType . '\' is not imported by \'' . self:currentClassName . '\'; add it to the using declaration to construct it (FUNCTIONS.md §I.6).');
							});
							res: targetType;
						}, else: {
							Conditional:if(check: { self:registeredClasses:has(key: targetType:split(delimiter: ':'):get(index: 0)) && !self:allEnumNames:has(key: targetType) }, then: {
								# List get/pop REQUIRE a 'default:' argument (Never Null).
								Conditional:if(check: { (targetType == 'List' || targetType:startsWith(prefix: 'List:') || targetType:startsWith(prefix: 'List of ')) && (method == 'get' || method == 'pop') }, then: {
									local Boolean is hasDefault: false;
									expr:methodArgs:each(action: local Function(NamedArg is arg){
										Conditional:if(check: { arg:name == 'default' }, then: {
											hasDefault: true;
										});
									});
									Conditional:if(check: { !hasDefault }, then: {
										self:addError(line: self:currentLine, msg: 'List \'' . method . '\' requires a \'default:\' argument.');
									});
								});
								# Specialized containers ('Array:String') resolve through their
								# base class's declarations with type-argument substitution;
								# when the declaration is not loaded, the element type comes
								# from the type string itself.
								local Member is selected: self:selectOverload(className: targetType, methodName: method, expr: expr);
								local String is cRet: '';
								Conditional:if(check: { selected:name != '' }, then: {
									cRet: self:selectedReturnType(className: targetType, selected: selected);
								});
								# FUNCTIONS.md Part IV V3: a LOADED void declaration keeps
								# its void — the fallback below is for UNLOADED classes
								# only. Resolving a void member as the receiver made
								# every void call lie about its type.
								Conditional:if(check: { cRet != '' }, then: {
									res: cRet;
								}, else: {
									# Unloaded declaration: resolve from the builtin method table
									# with element types from the type string.
									res: targetType;
									# Unloaded declaration: resolve from the builtin method table
									# with element types from the type string.
									res: targetType;
									local Array of String is scParts: targetType:split(delimiter: ':');
									when (method) {
										is 'toString': { res: Primitive:STRING:value(); }
										is 'length': { res: Primitive:INT:value(); }
										is 'isEmpty': { res: Primitive:BOOLEAN:value(); }
										is 'count': { res: Primitive:INT:value(); }
										is 'any': { res: Primitive:BOOLEAN:value(); }
										is 'has': { res: Primitive:BOOLEAN:value(); }
										is 'getString': { res: Primitive:STRING:value(); }
										is 'getInt': { res: Primitive:INT:value(); }
										is 'getFloat': { res: Primitive:FLOAT:value(); }
										is 'getBool': { res: Primitive:BOOLEAN:value(); }
										is 'indexOf': { res: Primitive:INT:value(); }
										is 'join': { res: Primitive:STRING:value(); }
										is 'keys': { res: 'Array of String'; }
										is 'add': { res: 'void'; }
										is 'set': { res: 'void'; }
										is 'clear': { res: 'void'; }
										is 'each': { res: 'void'; }
										is 'push': { res: 'void'; }
										is 'remove': { res: Primitive:BOOLEAN:value(); }
										else: {}
									}
									Conditional:if(check: { res == targetType }, then: {
										Conditional:if(check: { (targetType:startsWith(prefix: 'Array') || targetType:startsWith(prefix: 'List')) && scParts:length() > 1 && (method == 'get' || method == 'pop' || method == 'removeAt') }, then: {
											res: scParts:get(index: 1);
										});
										Conditional:if(check: { targetType:startsWith(prefix: 'Map') && scParts:length() > 2 && (method == 'get' || method == 'getString') }, then: {
											res: scParts:get(index: 2);
										});
									});
								});
							}, else: {
								Conditional:if(check: { targetType:startsWith(prefix: 'Array') && method == 'map' }, then: {
									local String is mappedElem: Primitive:ANY:value();
									Conditional:if(check: { expr:methodArgs:length() > 0 }, then: {
										local NamedArg is a0: expr:methodArgs:get(index: 0);
										local Expression is fnExpr: a0:value;
										Conditional:if(check: { fnExpr:kind == ExpressionKind:ANON_FN }, then: {
											local String is fnRet: fnExpr:anonReturnType:name;
											Conditional:if(check: { fnRet != '' && !self:isVoid(t: fnRet) && fnRet != Primitive:ANY:value() }, then: {
												mappedElem: self:formatTypeString(t: fnExpr:anonReturnType);
											});
										});
									});
									res: Conditional:if(check: { mappedElem != Primitive:ANY:value() }, then: { 'Array:' . mappedElem }, else: { 'Array' });
								}, else: {
									Conditional:if(check: { targetType:startsWith(prefix: 'Array') && method == 'fold' }, then: {
										Conditional:if(check: { expr:methodArgs:length() > 0 }, then: {
											local NamedArg is a0: expr:methodArgs:get(index: 0);
											res: a0:value:resolvedType;
										}, else: {
											res: 'Any';
										});
									}, else: {
										Conditional:if(check: { self:allEnumNames:has(key: targetType) }, then: {
											when (method) {
												is 'name': { res: Primitive:STRING:value(); }
												is 'ordinal': { res: Primitive:INT:value(); }
												is 'values': { res: 'Array:' . targetType; }
												is 'of': { res: targetType; }
												is 'value': {
													res: Conditional:if(check: { self:allStringBackedEnums:has(key: targetType) }, then: { 'String' }, else: { Primitive:INT:value() });
												}
												else: { res: 'Any'; }
											}
										}, else: {
											Conditional:if(check: { targetType == Primitive:INT:value() && method == 'toBase' }, then: {
												# Int:toBase is a floor binding (spec_int_to_base) returning a
												# String; Int has no loaded declaration to consult.
												res: Primitive:STRING:value();
											}, else: {
												# Undeclared members are compile errors on LOADED classes; an
												# unloaded class (floor singleton used without import) resolves
												# as Any — the runtime magic defines it.
												local Array of String is uParts: targetType:split(delimiter: ':');
												Conditional:if(check: { self:registeredClasses:has(key: uParts:get(index: 0)) && self:findClass(name: uParts:get(index: 0)):name != '' }, then: {
													self:addError(line: self:currentLine, msg: 'Member \'' . method . '\' is not declared on class \'' . targetType . '\'.');
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
		Conditional:if(check: { isValueBranch }, then: {
			# FUNCTIONS.md Part II: the value-yielding form — both branch
			# closures' established return types must unify. Read from the
			# nodes (the write-backs happened during the body check); never
			# re-infer.
			local Expression is thenAnon: expr:argValue(index: 1);
			local Expression is elseAnon: expr:argValue(index: 2);
			local String is thenT: thenAnon:anonReturnType:name;
			local String is elseT: elseAnon:anonReturnType:name;
			Conditional:if(check: { self:isVoid(t: thenT) || self:isVoid(t: elseT) }, then: {
				self:addError(line: self:currentLine, msg: 'A value-yielding branch requires both branches to end in an expression (FUNCTIONS.md Part II).');
				res: 'void';
			}, else: {
				Conditional:if(check: { !self:isAssignable(target: thenT, source: elseT) && !self:isAssignable(target: elseT, source: thenT) }, then: {
					self:addError(line: self:currentLine, msg: 'Branch yields mismatched types: \'' . thenT . '\' and \'' . elseT . '\'.');
					res: thenT;
				}, else: {
					res: Conditional:if(check: { thenT == Primitive:ANY:value() }, then: { elseT }, else: { thenT });
				});
			});
		}, else: {
			Conditional:if(check: { isBranchCall }, then: {
				# Branch calls are statements: void.
				res: 'void';
			});
		});
		return res;
	}

	## Declared primitive conversion compatibility for `as` casts: the
	## machine conversions (widen, truncate, parse). Transitional until the
	## primitive classes land in Spec and declare their conversions.
	##
	## @param src: Operand type name.
	## @param target: Cast target name.
	## @return: true when the conversion is declared.
	Function of Boolean is isCastable(String is src, String is target){
		Conditional:if(check: { src == target || src == Primitive:ANY:value() }, then: {
			return true;
		});
		Conditional:if(check: { target == Primitive:INT:value() }, then: {
			return src == 'Float' || src == 'String' || src == 'Byte';
		});
		Conditional:if(check: { target == 'Float' }, then: {
			return src == Primitive:INT:value();
		});
		Conditional:if(check: { target == 'Byte' }, then: {
			return src == Primitive:INT:value();
		});
		Conditional:if(check: { target == 'String' }, then: {
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
		Conditional:if(check: { srcType == '' || srcType == Primitive:ANY:value() || self:isPrimitive(t: srcType) }, then: {
			return '';
		});
		local Array of String is srcParts: srcType:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: srcParts:get(index: 0));
		Conditional:if(check: { cls:name == '' }, then: {
			return '';
		});
		# castable is a metadata FIELD declared on the class itself — the
		# method-only member lookup cannot see it, and ancestor searches skip
		# the declaring class. Search own members directly.
		local FieldSearchLoop is castLoop: FieldSearchLoop:init(members: cls:members, fieldName: MetadataField:CASTABLE:value());
		While:run(loop: castLoop);
		Conditional:if(check: { !castLoop:found }, then: {
			return '';
		});
		local Member is castM: castLoop:res;
		Conditional:if(check: { !castM:hasInit || castM:initExpr:kind != ExpressionKind:ARRAY }, then: {
			return '';
		});
		local String is found: '';
		castM:initExpr:arrayItems:each(action: local Function(Expression is entry){
			Conditional:if(check: { found == '' && entry:kind == ExpressionKind:ARRAY && entry:arrayItems:length() == 2 }, then: {
				local Expression is tExpr: entry:arrayItems:get(index: 0);
				local Expression is fExpr: entry:arrayItems:get(index: 1);
				local String is entryTarget: tExpr:stringValue;
				local String is entryFn: fExpr:stringValue;
				Conditional:if(check: { entryTarget == target }, then: {
					local String is fnRet: self:lookupMethodReturnType(className: srcType, methodName: entryFn);
					Conditional:if(check: { fnRet != target }, then: {
						self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' maps to \'' . entryFn . '\', which returns \'' . fnRet . '\', not \'' . target . '\'.');
						found: entryFn;
						return;
					});
					found: entryFn;
				});
			});
		});
		return found;
	}

	## Validates type safety of a statement node.
	##
	## @param stmt: AST statement node.
	Function is checkStatement(Statement is stmt){
		Conditional:if(check: { stmt:line > 0 }, then: {
			self:currentLine: stmt:line;
		});
		local StatementKind is kind: stmt:kind;

		when (kind) {
			is StatementKind:VAR_DECL: {
				local String is varName: stmt:varName;
				local String is fullType: self:formatVarTypeString(t: stmt:varType);
				self:localVars:set(key: varName, value: fullType);

				Conditional:if(check: { fullType == 'List' }, then: {
					local String is msg: 'Bare List type requires [T] element syntax.';
					self:addError(line: stmt:line, msg: msg);
				});
				self:validateTypeAccess(t: stmt:varType, line: stmt:line);

				Conditional:if(check: { stmt:hasInit }, then: {
					# Bidirectional: the declared type flows into the
					# initializer, typing container literals directly.
					local String is initType: self:inferExpressionType(expr: stmt:initExpr, expected: fullType);
					Conditional:if(check: { !self:isAssignable(target: fullType, source: initType) }, then: {
						local String is msg: 'Type mismatch in variable declaration for \'' . varName . '\': cannot assign \'' . initType . '\' to \'' . fullType . '\'.';
						# FUNCTIONS.md Part IV V3: a void expression consumed as a
						# value explains itself instead of cascading into the
						# generic mismatch.
						Conditional:if(check: { self:isVoid(t: initType) }, then: {
							local String is note: self:voidUseNote(expr: stmt:initExpr);
							Conditional:if(check: { note != '' }, then: {
								msg: 'cannot initialize \'' . fullType . '\' from a void expression: ' . note;
							});
						});
						self:addError(line: stmt:line, msg: msg);
					});
				});
			}
			is StatementKind:ASSIGN: {
				Conditional:if(check: { stmt:assignTarget:kind == ExpressionKind:PATH }, then: {
					local Array of String is tSegs: stmt:assignTarget:pathSegments;
					Conditional:if(check: { tSegs:length() == 2 && tSegs:get(index: 0) == self:names:selfIdent() }, then: {
						self:unassignedFields:remove(key: tSegs:get(index: 1));
					});
				}, else: {
					Conditional:if(check: { stmt:assignTarget:kind == ExpressionKind:IDENT }, then: {
						self:unassignedFields:remove(key: stmt:assignTarget:stringValue);
					});
				});
				local String is targetType: self:inferExpressionType(expr: stmt:assignTarget);
				local String is valType: self:inferExpressionType(expr: stmt:assignValue, expected: targetType);
					Conditional:if(check: { !self:isAssignable(target: targetType, source: valType) }, then: {
						local String is msg: 'Type mismatch in assignment: cannot assign \'' . valType . '\' to \'' . targetType . '\'.';
						# FUNCTIONS.md Part IV V3: the same for assignments.
						Conditional:if(check: { self:isVoid(t: valType) }, then: {
							local String is note: self:voidUseNote(expr: stmt:assignValue);
							Conditional:if(check: { note != '' }, then: {
								msg: 'cannot assign a void expression to \'' . targetType . '\': ' . note;
							});
						});
						self:addError(line: stmt:line, msg: msg);
					});
			}
			is StatementKind:WHEN: {
				local String is stmtSubjectType: self:inferExpressionType(expr: stmt:whenSubject);
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					self:bindWhenPatternVars(arm: arm);
					Conditional:if(check: { arm:hasValueExpr }, then: {
						self:inferExpressionType(expr: arm:valueExpr);
					});
					arm:body:each(action: local Function(Statement is s){
						self:checkStatement(stmt: s);
					});
				});
				self:checkWhenExhaustive(subjectType: stmtSubjectType, arms: stmt:whenArms, line: stmt:line);
			}
			is StatementKind:FORWARD: {
				self:checkForward(stmt: stmt);
			}
			is StatementKind:RETURN: {
				Conditional:if(check: { stmt:hasReturnExpr }, then: {
					# Bidirectional: the declared return type flows in — and a
					# value-yielding branch's yield takes the branch's own
					# expected type (nested branch calls type in context).
					local String is yieldExpected: self:currentMethodReturnType;
					Conditional:if(check: { self:checkingValueYield && self:currentYieldExpected != '' }, then: {
						yieldExpected: self:currentYieldExpected;
					});
					local String is retType: self:inferExpressionType(expr: stmt:returnExpr, expected: yieldExpected);
					# FUNCTIONS.md Part II: the last statement of a
					# value-yielding branch closure establishes the branch's
					# yield type (the inBranchClosure method-routing does not
					# apply to it).
					Conditional:if(check: { self:checkingValueYield }, then: {
						Conditional:if(check: { self:isVoid(t: self:currentAnonNode:anonReturnType:name) }, then: {
							self:currentAnonNode:anonReturnType: Type:init(name: retType);
							self:currentMethodReturnType: retType;
						}, else: {
							Conditional:if(check: { !self:isAssignable(target: self:currentAnonNode:anonReturnType:name, source: retType) }, then: {
								local String is msg: 'Branch yields mismatched types: expected \'' . self:currentAnonNode:anonReturnType:name . '\', found \'' . retType . '\'.';
								self:addError(line: stmt:line, msg: msg);
							});
						});
					}, else: {
						Conditional:if(check: { self:anonDepth > 0 && !self:inBranchClosure && self:currentAnonNode:kind == ExpressionKind:ANON_FN && self:isVoid(t: self:currentAnonNode:anonReturnType:name) && self:isVoid(t: self:currentMethodReturnType) }, then: {
							self:currentAnonNode:anonReturnType: Type:init(name: retType);
							self:currentMethodReturnType: retType;
						}, else: {
							Conditional:if(check: { !self:isAssignable(target: self:currentMethodReturnType, source: retType) }, then: {
								local String is msg: 'Method declared return type \'' . self:currentMethodReturnType . '\', but returned \'' . retType . '\'.';
								self:addError(line: stmt:line, msg: msg);
							});
						});
					});
				}, else: {
					Conditional:if(check: { self:currentMethodReturnType != 'void' && self:currentMethodReturnType != 'Void' && self:currentMethodReturnType != '' && self:currentMethodReturnType != 'Any' }, then: {
						local String is msg: 'Method expects return value of type \'' . self:currentMethodReturnType . '\', but found empty return.';
						self:addError(line: stmt:line, msg: msg);
					});
				});
			}
			is StatementKind:EXPR: {
				self:inferExpressionType(expr: stmt:exprStmt);
			}
			is StatementKind:CLASS: {
				local String is savedClass: self:currentClassName;
				local String is savedRet: self:currentMethodReturnType;
				local Map of String to String is savedVars: Map:init();
				local Array of String is vKeys: self:localVars:keys();
				vKeys:each(action: local Function(String is k){
					savedVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
				});
				local Map of String to String is savedFields: Map:init();
				local Array of String is fKeys: self:fieldTypes:keys();
				fKeys:each(action: local Function(String is k){
					savedFields:set(key: k, value: self:fieldTypes:getString(key: k, default: ''));
				});
				local Map of String to String is savedUnassigned: Map:init();
				local Array of String is uKeys: self:unassignedFields:keys();
				uKeys:each(action: local Function(String is k){
					savedUnassigned:set(key: k, value: self:unassignedFields:getString(key: k, default: ''));
				});

				self:checkClass(classDef: stmt:nestedClass);

				self:currentClassName: savedClass;
				self:currentMethodReturnType: savedRet;
				self:localVars: savedVars;
				self:fieldTypes: savedFields;
				self:unassignedFields: savedUnassigned;
			}
			else: {}
		}
	}

	## FUNCTIONS.md Part IV V5: the diagnostic display form of a type
	## name — the internal colon form ('Function:Boolean') renders the way
	## the language spells it ('Function of Boolean').
	##
	## @param t: Internal type name.
	## @return: The display name.
	Function of String is displayType(String is t){
		local String is out: '';
		local Int is i: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return i < t:length();
			},
			iteration: local Function(){
				Conditional:if(check: { i + 9 <= t:length() && t:substring(start: i, end: i + 9) == 'Function:' }, then: {
					out: out . 'Function of ';
					i: i + 9;
				}, else: {
					out: out . t:charAt(index: i, default: '');
					i: i + 1;
				});
				return true;
			}
		);
		return out;
	}

	## FUNCTIONS.md Part IV V3: the void-in-value-context hint. Describes
	## WHY an expression computes no value, derived from the CALLEE'S
	## DECLARATION — the function's name, its void return, and how many of
	## its declared parameters the call binds. No per-class special cases:
	## the same note serves every callable in the language. Reads the AST
	## and already-resolved types only — never re-infers.
	##
	## @param expr: The void expression being consumed.
	## @return: The hint text, or ''.
	Function of String is voidUseNote(Expression is expr){
		Conditional:if(check: { expr:kind != ExpressionKind:CALL }, then: {
			return '';
		});
		local String is targetT: expr:methodTarget:resolvedType;
		Conditional:if(check: { targetT == self:names:selfIdent() || targetT == '' }, then: {
			targetT: self:currentClassName;
		});
		local ClassInfo is tc: self:findClass(name: targetT:split(delimiter: ':'):get(index: 0));
		Conditional:if(check: { tc:name == '' }, then: {
			return '';
		});
		local Member is m: self:lookupOverloadedMember(className: targetT, methodName: expr:methodName, idx: expr:overloadIndex);
		Conditional:if(check: { m:name == '' }, then: {
			return '';
		});
		local String is mRet: self:resolveReturnType(t: m:memberType);
		Conditional:if(check: { !self:isVoid(t: mRet) }, then: {
			return '';
		});
		local String is note: '\'' . targetT . '.' . expr:methodName . '\' declares no return value';
		# FUNCTIONS.md Part IV V3: a partially-bound void call — the
		# unbound parameters' effects are absent. The arity gap is the
		# general signal (a 2-arg conditional's missing else is one case
		# of it, not a special one).
		Conditional:if(check: { expr:argCount() < m:params:length() }, then: {
			note: note . ' (' . (expr:argCount() as String) . ' of ' . (m:params:length() as String) . ' declared parameters bound)';
		});
		# FUNCTIONS.md Part IV V3: a sibling overload binding MORE parameters
		# is the general signal that this call's effects are incomplete — a
		# 2-arg conditional's missing else is one case of it, not a special
		# one. Name the sibling's parameters so the user sees what to add.
		local Array of Member is group: [];
		local Array of String is groupOwners: [];
		self:collectOverloadGroup(className: targetT, methodName: expr:methodName, hops: 0, acc: group, ownerAcc: groupOwners);
		local Int is maxParams: m:params:length();
		group:each(action: local Function(Member is g){
			Conditional:if(check: { g:params:length() > maxParams }, then: {
				maxParams: g:params:length();
			});
		});
		Conditional:if(check: { maxParams > m:params:length() }, then: {
			local String is names: '';
			group:each(action: local Function(Member is g){
				Conditional:if(check: { g:params:length() == maxParams }, then: {
					g:params:each(action: local Function(Parameter is p){
						Conditional:if(check: { names:endsWith(suffix: p:name) == false }, then: {
							Conditional:if(check: { names != '' }, then: {
								names: names . ', ';
							});
							names: names . p:name;
						});
					});
				});
			});
			note: note . ' (' . (maxParams as String) . ' parameters are available: ' . names . ')';
		});
		return note;
	}

	## Validates a merge-forward statement against its parent method:
	## merge context, single-use, arity, naming, and argument types.
	##
	## @param stmt: The FORWARD statement.
	Function is checkForward(Statement is stmt){
		Conditional:if(check: { !self:currentMethodIsMerge }, then: {
			self:addError(line: stmt:line, msg: 'Forward statement `(args...)` requires the enclosing method to declare \'merge\'.');
			return;
		});
		Conditional:if(check: { self:anonDepth > 0 }, then: {
			self:addError(line: stmt:line, msg: 'Forward statement is not allowed inside a nested function.');
			return;
		});
		Conditional:if(check: { self:forwardSeen }, then: {
			self:addError(line: stmt:line, msg: 'Multiple forward statements in method \'' . self:currentMethodName . '\'; at most one is allowed.');
			return;
		});
		self:forwardSeen: true;

		local Member is superM: self:findFirstSuperMethod(className: self:currentClassName, methodName: self:currentMethodName);
		Conditional:if(check: { superM:name == '' }, then: {
			self:addError(line: stmt:line, msg: 'Forward statement in \'' . self:currentMethodName . '\': no parent method to delegate to.');
			return;
		});
		local Array of Parameter is params: superM:params;
		local Array of NamedArg is args: stmt:forwardArgs;

		Conditional:if(check: { args:length() > params:length() }, then: {
			self:addError(line: stmt:line, msg: 'Forward statement passes ' . args:length() . ' arguments but parent \'' . superM:name . '\' accepts ' . params:length() . '.');
			return;
		});
		Conditional:if(check: { args:length() < params:length() }, then: {
			local Int is nIdx: 0;
			args:each(action: local Function(NamedArg is a){
				Conditional:if(check: { a:name == '' }, then: {
					self:addError(line: stmt:line, msg: 'Partial forward requires named arguments; argument ' . (nIdx + 1) . ' of \'' . self:currentMethodName . '\' is unnamed.');
				});
				nIdx: nIdx + 1;
			});
		});

		local Int is pIdx: 0;
		params:each(action: local Function(Parameter is p){
			local Expression is matchedValue: Expression:init(kind: ExpressionKind:UNKNOWN);
			local Boolean is found: false;
			args:each(action: local Function(NamedArg is a){
				Conditional:if(check: { !found && a:name != '' && a:name == p:name }, then: {
					matchedValue: a:value;
					found: true;
				});
			});
			Conditional:if(check: { !found && pIdx < args:length() }, then: {
				local NamedArg is posArg: args:get(index: pIdx);
				Conditional:if(check: { posArg:name == '' }, then: {
					matchedValue: posArg:value;
					found: true;
				});
			});
			Conditional:if(check: { found }, then: {
				local String is argT: self:inferExpressionType(expr: matchedValue);
				local String is pT: p:paramType:name;
				Conditional:if(check: { pT != Primitive:ANY:value() && pT != '' && argT != '' && argT != Primitive:ANY:value() && !self:isAssignable(target: pT, source: argT) }, then: {
					local String is label: Conditional:if(check: { p:name != '' }, then: { p:name }, else: { 'position ' . (pIdx + 1) });
					local String is msg: 'Forward argument \'' . label . '\' of \'' . self:currentMethodName . '\': cannot assign \'' . argT . '\' to \'' . pT . '\'.';
					self:addError(line: stmt:line, msg: msg);
				});
			}, else: {
				Conditional:if(check: { !p:hasDefault }, then: {
					local String is msg: 'Forward statement omits \'' . p:name . '\' of \'' . self:currentMethodName . '\' which has no default value.';
					self:addError(line: stmt:line, msg: msg);
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
		return self:formatTypeString(t: t);
	}

	## Validates a method member definition.
	##
	## @param method: Method member descriptor.
	Function is checkMethod(Member is method){
		Conditional:if(check: { method:line > 0 }, then: {
			self:currentLine: method:line;
		});
		Conditional:if(check: { method:sourceFile != '' }, then: {
			self:currentSourceFile: method:sourceFile;
		});
		self:currentMethodName: method:name;
		self:forwardSeen: false;
		self:anonDepth: 0;
		self:currentMethodIsMerge: method:hasModifier(kw: Keyword:MERGE);
		method:params:each(action: local Function(Parameter is p){
			self:validateTypeAccess(t: p:paramType, line: method:line);
		});
		self:validateTypeAccess(t: method:memberType, line: method:line);
		local Member is mergeTarget: self:findFirstSuperMethod(className: self:currentClassName, methodName: method:name);
		Conditional:if(check: { mergeTarget:name != '' && self:ancestorOverloaded(className: self:currentClassName, methodName: method:name, hops: 0) }, then: {
			self:addError(line: method:line, msg: 'Cannot replace or merge an overloaded method (\'' . method:name . '\' has multiple signatures); give each signature a distinct name (FUNCTIONS.md §I.3).');
		});
		Conditional:if(check: { self:currentMethodIsMerge && mergeTarget:name == '' }, then: {
			self:addError(line: method:line, msg: 'Method \'' . method:name . '\' in class \'' . self:currentClassName . '\' declares \'merge\' but no parent declares a method with that name.');
		});
		method:params:each(action: local Function(Parameter is p){
			Conditional:if(check: { p:paramType:name == self:names:selfFieldMarker() }, then: {
				local String is ft: self:fieldTypes:getString(key: p:name, default: Primitive:ANY:value());
				p:paramType: Type:init(name: ft);
				self:unassignedFields:remove(key: p:name);
			});
		});
		self:currentMethodReturnType: self:resolveReturnType(t: method:memberType);
		Conditional:if(check: { self:currentMethodReturnType == '' || self:isVoid(t: self:currentMethodReturnType) }, then: {
			Conditional:if(check: { method:name == ContractMethod:EVALUATE:value() || method:name == ContractMethod:ITERATION:value() }, then: {
				self:currentMethodReturnType: 'Boolean';
				method:memberType: Type:init(name: 'Boolean');
			});
		});
		self:localVars: Map:init();

		method:params:each(action: local Function(Parameter is p){
			self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
		});

		method:body:each(action: local Function(Statement is stmt){
			self:checkStatement(stmt: stmt);
		});

		Conditional:if(check: { self:currentMethodIsMerge && !self:forwardSeen && method:body:length() > 0 }, then: {
			self:addError(line: method:line, msg: 'Merge method \'' . method:name . '\' in class \'' . self:currentClassName . '\' must contain a forward statement `(args...)`.');
		});
		self:currentMethodIsMerge: false;
		self:currentMethodName: '';
	}

	## Finds the nearest parent implementation of a method (merge target),
	## walking base classes in declaration order.
	##
	## @param className: Child class whose parents are searched.
	## @param methodName: Method name to locate.
	## @return: The parent member, or an empty-named one when absent.
	Function of Member is findFirstSuperMethod(String is className, String is methodName){
		local ClassInfo is cls: self:findClass(name: className);
		Conditional:if(check: { cls:name == '' }, then: {
			return Member:init(kind: MemberKind:FIELD);
		});
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { res:name == '' }, then: {
				local Member is m: self:lookupAnyMember(className: baseName, methodName: methodName);
				Conditional:if(check: { m:kind == MemberKind:METHOD }, then: {
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
		Conditional:if(check: { seen:has(key: className) }, then: {
			return;
		});
		seen:set(key: className, value: 'true');
		local ClassInfo is cls: self:findClass(name: className);
		Conditional:if(check: { cls:name == '' }, then: {
			return;
		});
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == methodName && m:body:length() > 0 }, then: {
				local Boolean is present: false;
				acc:each(action: local Function(String is n){
					Conditional:if(check: { !present && n == className }, then: {
						present: true;
					});
				});
				Conditional:if(check: { !present }, then: {
					acc:add(item: className);
				});
			});
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			self:collectConcreteDeclarers(className: baseName, methodName: methodName, seen: seen, acc: acc);
		});
	}

	## Finds a member of any kind with the given name across all ancestors.
	##
	## @param className: Starting class whose bases are searched.
	## @param memberName: Member name to locate.
	## @return: The ancestor member, or an empty-named one when absent.
	Function of Member is findAncestorMember(String is className, String is memberName){
		local ClassInfo is cls: self:findClass(name: className);
		Conditional:if(check: { cls:name == '' }, then: {
			return Member:init(kind: MemberKind:FIELD);
		});
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { res:name == '' }, then: {
				local ClassInfo is anc: self:findClass(name: baseName);
				Conditional:if(check: { anc:name != '' }, then: {
					anc:members:each(action: local Function(Member is m){
						Conditional:if(check: { res:name == '' && m:name == memberName }, then: {
							res: m;
						});
					});
				});
			});
		});
		Conditional:if(check: { res:name == '' }, then: {
			cls:baseClasses:each(action: local Function(String is baseName){
				Conditional:if(check: { res:name == '' }, then: {
					res: self:findAncestorMember(className: baseName, memberName: memberName);
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
		local ClassInfo is cls: self:findClass(name: className);
		Conditional:if(check: { cls:name == '' }, then: {
			return '';
		});
		local String is owner: '';
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { owner == '' && m:name == memberName }, then: {
				owner: cls:name;
			});
		});
		Conditional:if(check: { owner != '' }, then: {
			return owner;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { owner == '' }, then: {
				owner: self:findMemberOwnerClass(className: baseName, memberName: memberName);
			});
		});
		return owner;
	}

	## Validates visibility for a member access: `local` restricts to the
	## declaring class, `contained` to it and its subclasses.
	##
	## @param ownerClass: Declaring class (empty = none, allowed).
	## @param member: The resolved member.
	## @param memberName: Member name for diagnostics.
	Function is checkMemberVisibility(String is ownerClass, Member is member, String is memberName){
		Conditional:if(check: { ownerClass == '' || ownerClass == 'Any' || memberName == ContractMethod:INIT:value() }, then: {
			return;
		});
		Conditional:if(check: { member:hasModifier(kw: Keyword:LOCAL) }, then: {
			Conditional:if(check: { self:currentClassName != ownerClass }, then: {
				local String is msg: 'Member \'' . memberName . '\' is local to class \'' . ownerClass . '\' and cannot be accessed from \'' . self:currentClassName . '\'.';
				self:addError(line: self:currentLine, msg: msg);
			});
		}, else: {
			Conditional:if(check: { member:hasModifier(kw: Keyword:CONTAINED) }, then: {
				Conditional:if(check: { !self:isSubclassOf(subName: self:currentClassName, baseName: ownerClass) }, then: {
					local String is msg: 'Member \'' . memberName . '\' is contained in class \'' . ownerClass . '\' and cannot be accessed from unrelated class \'' . self:currentClassName . '\'.';
					self:addError(line: self:currentLine, msg: msg);
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
			Conditional:if(check: { hasReplace || hasMerge }, then: {
				Conditional:if(check: { m:hasModifier(kw: Keyword:LOCAL) || m:hasModifier(kw: Keyword:CONTAINED) }, then: {
					local String is msg: 'Member \'' . m:name . '\' in class \'' . classDef:name . '\' combines \'replace\'/\'merge\' with a visibility modifier; replace and merge members are public by definition.';
					self:addError(line: m:line, msg: msg);
					return;
				});
			});
			Conditional:if(check: { !hasReplace && !hasMerge }, then: {
				return;
			});
			local String is name: m:name;
			Conditional:if(check: { name == ContractMethod:INIT:value() || name == ContractMethod:USING:value() || name == ContractMethod:TO_STRING:value() }, then: {
				return;
			});
			Conditional:if(check: { self:findMemberOwnerClass(className: classDef:name, memberName: name) == Primitive:ANY:value() }, then: {
				# Root-contract member: Any declares it public, so overriding
				# is always legitimate.
				return;
			});
			local Member is anc: self:findAncestorMember(className: classDef:name, memberName: name);
			Conditional:if(check: { anc:name == '' }, then: {
				local String is what: Conditional:if(check: { hasMerge }, then: { 'merge' }, else: { 'replace' });
				local String is msg: 'Member \'' . name . '\' in class \'' . classDef:name . '\' declares \'' . what . '\' but no ancestor declares a member with that name.';
				self:addError(line: m:line, msg: msg);
			}, else: {
				Conditional:if(check: { anc:hasModifier(kw: Keyword:LOCAL) || anc:hasModifier(kw: Keyword:CONTAINED) }, then: {
					local String is vis: Conditional:if(check: { anc:hasModifier(kw: Keyword:LOCAL) }, then: { 'local' }, else: { 'contained' });
					local String is msg: 'Member \'' . name . '\' in class \'' . classDef:name . '\' targets a ' . vis . ' ancestor member; ' . vis . ' members cannot be replaced or merged.';
					self:addError(line: m:line, msg: msg);
				}, else: {
					Conditional:if(check: { anc:kind != m:kind }, then: {
						local String is msg: 'Member \'' . name . '\' in class \'' . classDef:name . '\' is a ' . m:kind:value() . ' but the ancestor member it targets is a ' . anc:kind:value() . '.';
						self:addError(line: m:line, msg: msg);
					});
				});
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
			local ClassInfo is anc: self:findClass(name: baseName);
			Conditional:if(check: { anc:name != '' }, then: {
				anc:members:each(action: local Function(Member is m){
					Conditional:if(check: { m:kind == MemberKind:METHOD }, then: {
						seenMethods:set(key: m:name, value: 'true');
					});
				});
			});
		});
		local Array of String is names: seenMethods:keys();
		names:each(action: local Function(String is mName){
			local Boolean is declaredLocally: false;
			classDef:members:each(action: local Function(Member is m){
				Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == mName }, then: {
					declaredLocally: true;
				});
			});
			Conditional:if(check: { !declaredLocally }, then: {
				local Map of String to String is seen: Map:init();
				local Array of String is declarers: [];
				classDef:baseClasses:each(action: local Function(String is baseName){
					self:collectConcreteDeclarers(className: baseName, methodName: mName, seen: seen, acc: declarers);
				});
				local Array of String is maximal: [];
				declarers:each(action: local Function(String is d){
					local Boolean is isSubsumed: false;
					declarers:each(action: local Function(String is other){
						Conditional:if(check: { !isSubsumed && other != d && self:isSubclassOf(subName: other, baseName: d) }, then: {
							isSubsumed: true;
						});
					});
					Conditional:if(check: { !isSubsumed }, then: {
						maximal:add(item: d);
					});
				});
				Conditional:if(check: { maximal:length() >= 2 }, then: {
					local String is msg: 'ClassInfo \'' . classDef:name . '\' inherits conflicting implementations of \'' . mName . '\' from \'' . maximal:get(index: 0) . '\' and \'' . maximal:get(index: 1) . '\'; declare the method (replace or merge) to resolve the conflict.';
					self:addError(line: classDef:line, msg: msg);
				});
			});
		});
	}

	## Validates inheritance, interface contracts, and override signatures.
	##
	## @param classDef: Class to inspect.
	Function is checkInheritance(ClassInfo is classDef){
		self:currentSourceFile: classDef:sourceFile;
		local Boolean is hasInit: false;
		classDef:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:name == ContractMethod:INIT:value() }, then: {
				hasInit: true;
			});
		});

		classDef:baseClasses:each(action: local Function(String is baseName){
			local ClassInfo is parent: self:findClass(name: baseName);
			Conditional:if(check: { parent:name == baseName }, then: {
				# 1. Enforce abstract member implementation on concrete classes
				# with init. The implicit root Any is exempt: its members carry
				# concrete defaults. The outer-link relation is exempt too: the
				# inner-class link is an ACCESS scope, not an is-a contract —
				# the enclosing class's unimplemented members are not the
				# inner's obligation.
				Conditional:if(check: { hasInit && baseName != Primitive:ANY:value() && !(classDef:outerName != '' && (classDef:outerName == baseName || classDef:outerName:contains(needle: ':' . baseName))) }, then: {
					parent:members:each(action: local Function(Member is parentM){
						local Boolean is isAbstract: (parentM:kind == MemberKind:FIELD && !parentM:hasInit) ||
							(parentM:kind == MemberKind:METHOD && parentM:body:length() == 0);
						Conditional:if(check: { isAbstract }, then: {
							local MemberImplementLoop is chk: MemberImplementLoop:init(members: classDef:members, target: parentM);
							While:run(loop: chk);
							Conditional:if(check: { !chk:implemented }, then: {
								local String is msg: 'ClassInfo \'' . classDef:name . '\' does not implement abstract member \'' . parentM:name . '\' required by parent \'' . baseName . '\'.';
								self:addError(line: classDef:line, msg: msg);
							});
						});
					});
				});

				# 2. Strict replace check & method signature matching on overrides
				classDef:members:each(action: local Function(Member is subM){
					# Declarative metadata (namespace/using/group) is per-class
					# by design and never participates in override matching.
					Conditional:if(check: { subM:name == MetadataField:NAMESPACE:value() || subM:name == MetadataField:USING:value() || subM:name == MetadataField:CASTABLE:value() }, then: {
						return;
					});
					parent:members:each(action: local Function(Member is parentM){
						Conditional:if(check: { subM:name == parentM:name }, then: {
							Conditional:if(check: { parentM:hasModifier(kw: Keyword:LOCAL) || parentM:hasModifier(kw: Keyword:CONTAINED) }, then: {
								local String is vis: Conditional:if(check: { parentM:hasModifier(kw: Keyword:LOCAL) }, then: { 'local' }, else: { 'contained' });
								local String is msg: 'Member \'' . subM:name . '\' is ' . vis . ' in ancestor \'' . baseName . '\' and cannot be replaced or merged.';
								self:addError(line: subM:line, msg: msg);
							});
							local Boolean is hasReplace: subM:hasModifier(kw: Keyword:REPLACE);
							local Boolean is hasMerge: subM:hasModifier(kw: Keyword:MERGE);
							Conditional:if(check: { hasMerge }, then: {
								Conditional:if(check: { subM:kind == MemberKind:METHOD }, then: {
									Conditional:if(check: { parentM:kind == MemberKind:METHOD && parentM:body:length() == 0 }, then: {
										local String is msg: 'Cannot merge method \'' . subM:name . '\' in class \'' . classDef:name . '\' with abstract method from \'' . baseName . '\'.';
										self:addError(line: subM:line, msg: msg);
									});
								}, else: {
									self:applyMerge(classDef: classDef, subM: subM, parentM: parentM, baseName: baseName);
								});
							}, else: {
								Conditional:if(check: { !hasReplace }, then: {
									local String is msg: 'Member \'' . subM:name . '\' in class \'' . classDef:name . '\' overrides ancestor member from \'' . baseName . '\', but is missing \'replace\' modifier.';
									self:addError(line: subM:line, msg: msg);
								});
							});

							Conditional:if(check: { subM:kind == MemberKind:METHOD && parentM:kind == MemberKind:METHOD }, then: {
								# Root-contract carve-out: init/using/toString declared
								# in Any are name reservations; per-class signatures
								# are legitimate. Override must still carry replace.
								Conditional:if(check: { baseName == Primitive:ANY:value() }, then: {
									Conditional:if(check: { !subM:hasModifier(kw: Keyword:REPLACE) && !subM:hasModifier(kw: Keyword:MERGE) }, then: {
										local String is msg: 'Member \'' . subM:name . '\' in class \'' . classDef:name . '\' overrides root-contract member from \'Any\', but is missing \'replace\' modifier.';
										self:addError(line: subM:line, msg: msg);
									});
									return;
								});
								# FUNCTIONS.md Part IV IV.2: constructors are per-class —
								# they are not polymorphic. An init never enters the
								# ancestor signature/return compatibility checks at all
								# (inner classes inherit their enclosing class, whose
								# init differs by design — and whose parameter list may
								# be empty, so the param-merge below cannot run on it).
								Conditional:if(check: { subM:name == 'init' }, then: {
									return;
								});
								Conditional:if(check: { subM:params:length() != parentM:params:length() }, then: {
									local String is msg: 'Method \'' . subM:name . '\' in class \'' . classDef:name . '\' parameter count mismatch with ancestor in \'' . baseName . '\'.';
									self:addError(line: subM:line, msg: msg);
								}, else: {
									local Int is pIdx: 0;
									subM:params:each(action: local Function(Parameter is subP){
										local Parameter is parentP: parentM:params:get(index: pIdx);
										Conditional:if(check: { subP:paramType:name == 'Any' || subP:paramType:name == '' }, then: {
											subP:paramType: parentP:paramType;
										});
										pIdx: pIdx + 1;
									});
								});
								local String is subRet: self:resolveReturnType(t: subM:memberType);
								local String is parentRet: self:resolveReturnType(t: parentM:memberType);
								Conditional:if(check: { subM:memberType:name == '' || self:isVoid(t: subM:memberType:name) }, then: {
									subM:memberType: parentM:memberType;
								}, else: {
									Conditional:if(check: { !self:isAssignable(target: subRet, source: parentRet) }, then: {
										local String is msg: 'Method \'' . subM:name . '\' in class \'' . classDef:name . '\' return type \'' . subRet . '\' does not match ancestor return type \'' . parentRet . '\'.';
										self:addError(line: subM:line, msg: msg);
									});
								});
							});
						});
					});
				});
			});
		});
		self:checkMethodConflicts(classDef: classDef);
		self:checkShadowTargets(classDef: classDef);
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
		Conditional:if(check: { subM:kind != MemberKind:FIELD }, then: {
			self:addError(line: subM:line, msg: '\'merge\' is only valid on fields; member \'' . subM:name . '\' in class \'' . classDef:name . '\' is not a field.');
			return;
		});
		local String is typeName: subM:memberType:name;
		Conditional:if(check: { !typeName:startsWith(prefix: 'Array') }, then: {
			self:addError(line: subM:line, msg: '\'merge\' requires an Array field; \'' . typeName . '\' is not mergeable.');
			return;
		});
		Conditional:if(check: { !parentM:hasInit }, then: {
			return;
		});
		local Expression is parentInit: parentM:initExpr;
		Conditional:if(check: { parentInit:kind != ExpressionKind:ARRAY }, then: {
			self:addError(line: subM:line, msg: '\'merge\' requires a constant array literal in parent \'' . baseName . '.' . parentM:name . '.');
			return;
		});
		Conditional:if(check: { !subM:hasInit }, then: {
			return;
		});
		local Expression is childInit: subM:initExpr;
		Conditional:if(check: { childInit:kind != ExpressionKind:ARRAY }, then: {
			self:addError(line: subM:line, msg: '\'merge\' requires a constant array literal initializer on \'' . classDef:name . '.' . subM:name . '.');
			return;
		});
		local Array of Expression is combined: [];
		parentInit:arrayItems:each(action: local Function(Expression is item){
			combined:add(item: item);
		});
		childInit:arrayItems:each(action: local Function(Expression is item){
			combined:add(item: item);
		});
		local Expression is folded: subM:initExpr;
		folded:arrayItems: combined;
	}

	## Populates `fieldTypes` for a class including inherited fields.
	##
	## @param classDef: Class to collect from.
	Function is collectClassFieldTypes(ClassInfo is classDef){
		classDef:baseClasses:each(action: local Function(String is baseName){
			local ClassInfo is parent: self:findClass(name: baseName);
			Conditional:if(check: { parent:name != '' }, then: {
				self:collectClassFieldTypes(classDef: parent);
			});
		});
		classDef:members:each(action: local Function(Member is m){
			# Metadata members carry no type and are not fields of the
			# generated struct.
			Conditional:if(check: { m:kind == MemberKind:FIELD && m:memberType:name != '' }, then: {
				self:fieldTypes:set(key: m:name, value: self:formatVarTypeString(t: m:memberType));
			});
		});
	}

	## Validates all members of a class definition.
	##
	## @param classDef: Class definition.
	Function is checkClass(ClassInfo is classDef){
		self:currentClassName: classDef:name;
		self:currentSourceFile: classDef:sourceFile;
		self:fieldTypes: Map:init();
		self:collectClassFieldTypes(classDef: classDef);

		classDef:members:each(action: local Function(Member is m){
			when (m:kind) {
				is MemberKind:FIELD: {
					self:currentLine: m:line;
					Conditional:if(check: { m:sourceFile != '' }, then: {
						self:currentSourceFile: m:sourceFile;
					});
					# Declarative metadata properties (using, namespace, group)
					# are loader directives, not checked code: their
					# initializers may reference classes the using itself
					# loads, so type validation is skipped.
					self:validateTypeAccess(t: m:memberType, line: m:line);
					Conditional:if(check: { m:name != MetadataField:USING:value() && m:name != MetadataField:NAMESPACE:value() && m:name != MetadataField:CASTABLE:value() }, then: {
						local String is declaredType: self:formatVarTypeString(t: m:memberType);
						Conditional:if(check: { m:hasInit }, then: {
							# Bidirectional: the declared type flows in.
							local String is initType: self:inferExpressionType(expr: m:initExpr, expected: declaredType);
							Conditional:if(check: { !self:isAssignable(target: declaredType, source: initType) }, then: {
								local String is msg: 'Type mismatch in field \'' . classDef:name . ':' . m:name . '\': cannot assign \'' . initType . '\' to \'' . declaredType . '\'.';
								self:addError(line: m:line, msg: msg);
							});
						});
					});
				}
				else: {}
			}
		});

		classDef:members:each(action: local Function(Member is m){
			when (m:kind) {
				is MemberKind:METHOD: {
					self:unassignedFields: Map:init();
					Conditional:if(check: { m:name == ContractMethod:INIT:value() }, then: {
						classDef:members:each(action: local Function(Member is fm){
							Conditional:if(check: { fm:kind == MemberKind:FIELD && !fm:hasInit && fm:name != ContractMethod:USING:value() }, then: {
								self:unassignedFields:set(key: fm:name, value: 'true');
							});
						});
					});
					self:checkMethod(method: m);
					self:unassignedFields: Map:init();
				}
				is MemberKind:CLASS: {
					local String is savedClass: self:currentClassName;
					local Map of String to String is savedFields: Map:init();
					local Array of String is fKeys: self:fieldTypes:keys();
					fKeys:each(action: local Function(String is k){
						savedFields:set(key: k, value: self:fieldTypes:getString(key: k, default: ''));
					});
					local Map of String to String is savedUnassigned: Map:init();
					local Array of String is uKeys: self:unassignedFields:keys();
					uKeys:each(action: local Function(String is k){
						savedUnassigned:set(key: k, value: self:unassignedFields:getString(key: k, default: ''));
					});

					self:checkClass(classDef: m:nestedClass);

					self:currentClassName: savedClass;
					self:fieldTypes: savedFields;
					self:unassignedFields: savedUnassigned;
				}
				else: {}
			}
		});
	}

	## Collects nested class definitions from a statement tree.
	##
	## @param stmt: The statement to walk.
	## @param acc: Output array.
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

	## Collects a class and all nested definitions into the flat registry.
	##
	## @param c: The class to collect.
	## @param acc: Output array.
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



	## Validates one class's instance imports (as-form using entries,
	## INSTANCE.md §2.1): the target must be a loaded non-enum class, and
	## v1 restricts the form to field-less classes with no constructor
	## arguments — the elided dispatch covers the whole known migration
	## surface; the synthetic-field form is deferred. At most one import
	## per class name (INSTANCE.md E2, E3).
	##
	## @param classDef: Class definition.
	Function is checkInstanceImports(ClassInfo is classDef){
		local Map of String to String is seen: Map:init();
		classDef:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:name != 'using' || !m:hasInit || m:initExpr:kind != ExpressionKind:ARRAY }, then: {
				return;
			});
			m:initExpr:arrayItems:each(action: local Function(Expression is item){
				Conditional:if(check: { item:kind != ExpressionKind:ARRAY }, then: {
					return;
				});
				local Expression is asExpr: Expression:init(kind: ExpressionKind:UNKNOWN);
				item:arrayItems:each(action: local Function(Expression is seg){
					Conditional:if(check: { seg:kind == ExpressionKind:USING_AS }, then: {
						asExpr: seg;
					});
				});
				Conditional:if(check: { asExpr:stringValue == '' }, then: {
					return;
				});
				local String is asName: asExpr:stringValue;
				Conditional:if(check: { seen:has(key: asName) }, then: {
					self:addError(line: m:line, msg: 'Class \'' . classDef:name . '\' instance-imports \'' . asName . '\' more than once (INSTANCE.md E3).');
					return;
				});
				seen:set(key: asName, value: 'true');
				local ClassInfo is target: self:findClass(name: asName);
				Conditional:if(check: { target:name == '' }, then: {
					return;
				});
				Conditional:if(check: { target:baseClass == self:names:enumHeader() }, then: {
					self:addError(line: m:line, msg: 'Cannot instance-import enum \'' . asName . '\'; enums are type-level (INSTANCE.md E2).');
					return;
				});
					Conditional:if(check: { target:typeParams:length() > 0 }, then: {
						self:addError(line: m:line, msg: 'Generic classes cannot be instance-imported yet (INSTANCE.md §10).');
						return;
					});
			});
		});
	}

	## Collects the instance-import target names of one class.
	##
	## @param classDef: Class definition.
	## @return: The as-form target class names, declaration order.
	Function of Array of String is instanceImportTargets(ClassInfo is classDef){
		local Array of String is out: [];
		classDef:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, then: {
				m:initExpr:arrayItems:each(action: local Function(Expression is item){
					Conditional:if(check: { item:kind == ExpressionKind:ARRAY }, then: {
						item:arrayItems:each(action: local Function(Expression is seg){
							Conditional:if(check: { seg:kind == ExpressionKind:USING_AS }, then: {
								out:add(item: seg:stringValue);
							});
						});
					});
				});
			});
		});
		return out;
	}

	## Verifies the instance-import graph is a DAG (INSTANCE.md E4):
	## A importing as B and B importing as A would recurse construction
	## forever at first init. DFS with gray/black coloring.
	Function is checkInstanceImportGraph(){
		local Map of String to String is color: Map:init();
		self:programClasses:each(action: local Function(ClassInfo is c){
			self:visitImportNode(c: c, color: color, path: '');
		});
	}

	## One DFS visit of the import graph.
	##
	## @param c: Class being visited.
	## @param color: Node states ('g' in progress, 'b' done).
	## @param path: Cycle-report prefix.
	Function is visitImportNode(ClassInfo is c, Map of String to String is color, String is path){
		local String is state: color:getString(key: c:name, default: '');
		Conditional:if(check: { state == 'b' }, then: {
			return;
		});
		Conditional:if(check: { state == 'g' }, then: {
			self:addError(line: 0, msg: 'Instance import cycle: ' . path . c:name . ' (INSTANCE.md E4); construction would recurse forever.');
			return;
		});
		color:set(key: c:name, value: 'g');
		local Array of String is targets: self:instanceImportTargets(classDef: c);
		targets:each(action: local Function(String is t){
			local ClassInfo is next: self:findClass(name: t);
			Conditional:if(check: { next:name != '' }, then: {
				self:visitImportNode(c: next, color: color, path: path . c:name . ' -> ');
			});
		});
		color:set(key: c:name, value: 'b');
	}

	Function of Array of TypeError is checkProgram(ProgramNode is program){
		self:errors: [];
		local Array of ClassInfo is flattened: [];
		program:classes:each(action: local Function(ClassInfo is c){
			self:collectClasses(c: c, acc: flattened);
		});
		# FUNCTIONS.md Part IV IV.2: same-named inner classes under
		# different enclosing classes are distinct by intent but ambiguous
		# in the flat registry — resolve nothing, name the collision.
		local Map of String to String is innerSeen: Map:init();
		flattened:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { c:outerName != '' }, then: {
				Conditional:if(check: { innerSeen:has(key: c:name) }, then: {
					local String is msg: 'Same-named inner class \'' . c:name . '\' declared under more than one enclosing class (last under \'' . c:outerName . '\'); rename one (FUNCTIONS.md Part IV IV.2).';
					self:addError(line: c:line, msg: msg);
				}, else: {
					innerSeen:set(key: c:name, value: c:outerName);
				});
			});
		});
		self:programClasses: flattened;

		self:registeredClasses: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();

		# Builtin container types resolve like primitives: their methods
		# work with or without an import (the container branches
		# were unconditional). When the declaration is loaded its real
		# signatures apply; when not, calls resolve to the container type.
		local Array of String is builtinNames: ['Array', 'Map', 'List', 'String', 'Function', 'LoopControl', 'Output', 'Error', 'Math', 'Process', 'File', 'Input', 'Ansi', 'Parallel', 'While', 'Loop', 'LoopCallback', 'InputHandler'];
		builtinNames:each(action: local Function(String is bn){
			self:registeredClasses:set(key: bn, value: bn);
		});
		flattened:each(action: local Function(ClassInfo is c){
			self:registeredClasses:set(key: c:name, value: c:name);
			# FUNCTIONS.md Part IV IV.2c: the nested classes register under
			# their qualified identity too — 'Outer:Inner' resolves in the
			# constructor and static-call paths.
			Conditional:if(check: { c:outerName != '' }, then: {
				self:registeredClasses:set(key: c:qualifiedName(), value: c:qualifiedName());
			});
			Conditional:if(check: { c:baseClass == self:names:enumHeader() }, then: {
				self:allEnumNames:set(key: c:name, value: 'true');
				c:members:each(action: local Function(Member is m){
					# The namespace declaration is metadata, not a variant.
					Conditional:if(check: { m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, then: {
						return;
					});
					self:allEnumVariants:set(key: m:name, value: c:name);
					Conditional:if(check: { m:memberType:name == Primitive:STRING:value() }, then: {
						self:allStringBackedEnums:set(key: c:name, value: 'true');
					});
				});
			});
		});

		# INSTANCE.md E2/E3: validate as-form instance imports per class.
		flattened:each(action: local Function(ClassInfo is c){
			self:checkInstanceImports(classDef: c);
		});
		# INSTANCE.md E4: the instance-import graph must be a DAG.
		self:checkInstanceImportGraph();
		# FUNCTIONS.md §I.1: overload legality across all classes.
		self:checkOverloadLegality();

		# Pass 1: Inheritance contract validation & type propagation
		flattened:each(action: local Function(ClassInfo is c){
			self:checkInheritance(classDef: c);
		});

		# Pass 2: Full expression type inference & AST annotation
		program:classes:each(action: local Function(ClassInfo is c){
			self:checkClass(classDef: c);
		});

		return self:errors;
	}
}
