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
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'ast', ContractMethod],
		['base', 'compiler', 'ast', MetadataField],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', WellKnown],
		['base', 'compiler', Error],
		['base', 'compiler', 'checker', TypeError],
		['base', 'iterator'],
		['base', 'sys', as Loops()],
		['base', 'sys', as Reflection()],
		['base', 'sys', as Output()],
		['base', 'sys', as Buf()],
		['base', 'sys', as Conditional()]
];

	## Registered classes: name -> "true".
	local Map of String to String is registeredClasses: Map:init();

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

	## Source file of the class currently being analyzed.
	local String is currentSourceFile: '';

	## Return type name of the method currently being checked.
	local String is currentMethodReturnType: '';

	## the anon-fn node whose body is being checked
	## (the Kotlin write-back target for void-declared closures).
	local Expression is currentAnonNode: Expression:init(kind: ExpressionKind:UNKNOWN);

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
		self:nestedScopeMap: Map:init();
		self:nestedScopeFor: '';
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
			# the stamp vocabulary repeats — the
			# interning collapses the retained copies to one object.
			return Buf:intern(s: baseName . ':' . self:formatTypeString(t: p0));
		});
		Conditional:if(check: { t:params:length() >= 2 }, then: {
			local Type is p0: t:params:get(index: 0);
			local Type is p1: t:params:get(index: 1);
			return Buf:intern(s: baseName . ':' . self:formatTypeString(t: p0) . ':' . self:formatTypeString(t: p1));
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
		local ClassInfo is res: ClassInfo:init(name: '', baseClass: '', members: []);
		local Boolean is found: false;
		local Int is count: self:programClasses:length();
		local Boolean is hasColon: name:contains(needle: ':');
		Loops(
			[Int is idx: 0],
			{ !found && idx < count },
			{
				local ClassInfo is cand: self:programClasses:get(index: idx);
				idx++;
				if({ cand:name == name }, {
					res: cand;
					found: true;
				}, {
					if({ hasColon }, {
						local String is candQ: cand:namespaceJoined() . ':' . cand:name;
						if({ candQ == name }, {
							res: cand;
							found: true;
						});
					});
				});
			}
		);
		if({ found }, {
			return res;
		});
		if({ hasColon }, {
			local ClassInfo is qMatch: ClassInfo:init(name: '', baseClass: '', members: []);
			self:programClasses:each(action: local Function(ClassInfo is c){
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
		# Function assignability is directional. A
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
					while(
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
		local Member is res: Member:init(kind: MemberKind:FIELD);
		local Int is idx: 0;
		Loops({ res:name == '' && idx < cls:members:length() }, {
			local Member is m: cls:members:get(index: idx);
			idx: idx + 1;
			if({ !m:hasModifier(kw: Keyword:HELD) && m:kind == MemberKind:METHOD && m:name == methodName }, {
				res: m;
			});
		});
		Conditional:if(check: { res:name != '' }, then: {
			return res;
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
		local Member is res: Member:init(kind: MemberKind:FIELD);
		local Int is idx: 0;
		Loops({ res:name == '' && idx < cls:members:length() }, {
			local Member is m: cls:members:get(index: idx);
			idx: idx + 1;
			if({ m:kind == MemberKind:FIELD && m:name == variantName }, {
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
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return '';
		});
		local String is baseClassName: self:memberLookupRoot(className: className);
		local Array of String is typeArgs: [];
		# The resolved qualified root absorbs the colon chain ; bare
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
		local Member is foundM: Member:init(kind: MemberKind:FIELD);
		local Int is idx: 0;
		Loops({ foundM:name == '' && idx < cls:members:length() }, {
			local Member is m: cls:members:get(index: idx);
			idx: idx + 1;
			if({ !m:hasModifier(kw: Keyword:HELD) && m:kind == MemberKind:FIELD && m:name == fieldName }, {
				foundM: m;
			});
		});
		Conditional:if(check: { foundM:name != '' }, then: {
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
		local Member is foundM: Member:init(kind: MemberKind:FIELD);
		local Int is idx: 0;
		Loops({ foundM:name == '' && idx < cls:members:length() }, {
			local Member is m: cls:members:get(index: idx);
			idx: idx + 1;
			if({ !m:hasModifier(kw: Keyword:HELD) && m:kind == MemberKind:METHOD && m:name == methodName }, {
				foundM: m;
			});
		});
		Conditional:if(check: { foundM:name != '' }, then: {
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
	Function of String is checkMatchArms(Expression is subj, Expression is arms){
		local String is subjT: self:inferExpressionType(expr: subj);
		# Strip container/generic spellings to the base class name.
		Conditional:if(check: { subjT:contains(needle: ' of ') }, then: {
			subjT: subjT:substring(start: 0, end: subjT:indexOf(search: ' of ', default: 0));
		});
		Conditional:if(check: { subjT:contains(needle: ':') }, then: {
			subjT: subjT:split(delimiter: ':'):get(index: 0);
		});
		Conditional:if(check: { subjT == '' || subjT == Primitive:ANY:value() || !self:registeredClasses:has(key: subjT) }, then: {
			self:addError(line: self:currentLine, msg: 'Conditional:match subjects must be class-typed values; \'' . subjT . '\' cannot be matched.');
			return 'Any';
		});
		# Match is identity dispatch over class instances: a
		# primitive-typed held constant carries no association with its
		# owner class, so it is not a match subject — EXCEPT String,
		# whose string-literal keys compare by value (the CBackendUtils/
		# TemplateEscapes shape).
		Conditional:if(check: { self:isPrimitive(t: subjT) && subjT != Primitive:STRING:value() }, then: {
			self:addError(line: self:currentLine, msg: 'Match subjects are class instances; primitive-typed held constants are compared directly with == or spec_string_equals.');
			return 'Any';
		});
		local Boolean is rooted: self:isSubclassOf(subName: subjT, baseName: self:names:enumHeader());
		local Array of String is covered: [];
		local Boolean is hasElse: false;
		local Boolean is anyValue: false;
		local Boolean is anyVoid: false;
		local String is resT: '';
		local Boolean is bad: false;
		local Int is keyTotal: arms:mapKeys:length();
		local Int is ki: 0;
		while(
			evaluate: local Function of Boolean(){ return ki < keyTotal; },
			iteration: local Function of Boolean(){
				local Expression is key: arms:mapKeys:get(index: ki);
				local Expression is val: arms:mapValues:get(index: ki);
				ki: ki + 1;
				# The else arm closes the table: arms after it are dead.
				Conditional:if(check: { hasElse && !(key:kind == ExpressionKind:IDENT && key:str == 'else') }, then: {
					self:addError(line: self:currentLine, msg: 'Match arms after else are unreachable; move else last.');
					bad: true;
				});
				Conditional:if(check: { key:kind == ExpressionKind:IDENT && key:str == 'else' }, then: {
					Conditional:if(check: { hasElse }, then: {
						self:addError(line: self:currentLine, msg: 'Duplicate else arm in the match table.');
					});
					hasElse: true;
				}, else: {
					local Array of Expression is keyTargets: [];
					Conditional:if(check: { key:kind == ExpressionKind:ARRAY }, then: {
						keyTargets: key:arrayItems;
					}, else: {
						keyTargets: [key];
					});
					keyTargets:each(action: local Function(Expression is one){
						# String-literal keys match String subjects by value.
						Conditional:if(check: { one:kind == ExpressionKind:STRING }, then: {
							Conditional:if(check: { subjT != Primitive:STRING:value() }, then: {
								self:addError(line: self:currentLine, msg: 'String-literal match keys match String subjects; \'' . subjT . '\' is not one.');
								bad: true;
							}, else: {
								local String is target: 'str:' . one:str;
								Conditional:if(check: { covered:indexOf(search: target, default: -1) >= 0 }, then: {
									self:addError(line: self:currentLine, msg: 'Duplicate match key \'' . one:str . '\'.');
									bad: true;
								}, else: {
									covered:add(item: target);
								});
							});
							return;
						});
						local String is keyName: '';
						Conditional:if(check: { one:kind == ExpressionKind:IDENT }, then: {
							keyName: one:str;
						}, else: {
							Conditional:if(check: { one:kind == ExpressionKind:PATH && one:pathSegments:length() > 0 }, then: {
								keyName: one:pathSegments:get(index: one:pathSegments:length() - 1);
							});
						});
						Conditional:if(check: { keyName == '' }, then: {
							self:addError(line: self:currentLine, msg: 'Match keys must be held-member references.');
							bad: true;
						}, else: {
							# Held members first; the variant registry is the
							# interim bridge — today's enum
							# variants match until the sugar migrates.
							local String is owner: self:findHeldOwnerClass(className: subjT, memberName: keyName);
							Conditional:if(check: { owner == '' && self:allEnumNames:has(key: subjT) }, then: {
								# The interim bridge: today's
								# enum variants ARE the subject enum's own member
								# list — resolved directly, no global registry
								# (variant names collide across enums).
								local ClassInfo is enumCls: self:findClass(name: subjT);
								local Boolean is variantFound: false;
								enumCls:members:each(action: local Function(Member is m){
									Conditional:if(check: { !variantFound && m:name == keyName && !(m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) }, then: {
										variantFound: true;
									});
								});
								Conditional:if(check: { variantFound }, then: {
									owner: subjT;
								});
							}, else: {
								# The class-model bridge: a
								# desugared TAGGED enum's variants are its nested
								# subclasses — the key admits when one matches.
								Conditional:if(check: { self:bindings:isClassModelEnum(c: self:findClass(name: subjT)) }, then: {
									local ClassInfo is cmCls: self:findClass(name: subjT);
									cmCls:members:each(action: local Function(Member is m){
										Conditional:if(check: { owner == '' && m:kind == MemberKind:CLASS && m:nestedClass:name == keyName }, then: {
											owner: subjT;
										});
									});
								});
							});
							Conditional:if(check: { owner == '' }, then: {
								self:addError(line: self:currentLine, msg: 'Match key \'' . keyName . '\' is not a held member of \'' . subjT . '\'.');
								bad: true;
							}, else: {
								local String is target: owner . ':' . keyName;
								Conditional:if(check: { covered:indexOf(search: target, default: -1) >= 0 }, then: {
									self:addError(line: self:currentLine, msg: 'Duplicate match key \'' . keyName . '\'.');
									bad: true;
								}, else: {
									covered:add(item: target);
									Conditional:if(check: { self:allEnumNames:has(key: owner) }, then: {
										# Payload arms (the Stage-5 form pulled forward):
										# an arm closure's parameters bind the tagged
										# variant's constructor payloads — type them
										# from the variant's declared parameters.
										Conditional:if(check: { val:kind == ExpressionKind:ANON_FN && val:anonParams:length() > 0 }, then: {
											# The variant's parameter surface: the legacy
											# member (today's enums) or the desugared
											# nested subclass's init.
											local Member is pvMem: Member:init(kind: MemberKind:FIELD);
											Conditional:if(check: { self:allEnumNames:has(key: owner) }, then: {
												local ClassInfo is pvCls: self:findClass(name: owner);
												pvCls:members:each(action: local Function(Member is m){
													Conditional:if(check: { pvMem:name == '' && m:name == keyName && !(m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) }, then: {
														pvMem: m;
													});
												});
											}, else: {
												local ClassInfo is subCls: self:findClass(name: owner . ':' . keyName);
												Conditional:if(check: { subCls:name != '' }, then: {
													subCls:members:each(action: local Function(Member is m){
														Conditional:if(check: { pvMem:name == '' && m:kind == MemberKind:METHOD && m:name == 'init' }, then: {
															pvMem: m;
														});
													});
												});
											});
											local Int is pbi: 0;
											val:anonParams:each(action: local Function(Parameter is bp){
												Conditional:if(check: { pbi < pvMem:params:length() }, then: {
													local Parameter is vp: pvMem:params:get(index: pbi);
													bp:paramType: Type:init(name: vp:paramType:name);
												});
												pbi: pbi + 1;
											});
										});
									}, else: {
										self:checkMemberVisibility(ownerClass: owner, member: self:findHeldMember(className: subjT, memberName: keyName), memberName: keyName);
									});
								});
							});
						});
					});
				});
				Conditional:if(check: { val:kind != ExpressionKind:ANON_FN }, then: {
					self:addError(line: self:currentLine, msg: 'Match arm bodies must be closures: \'key: { ... }\'.');
					bad: true;
				}, else: {
					self:inferExpressionType(expr: val);
					local String is valT: val:resolvedType;
					Conditional:if(check: { valT:startsWith(prefix: 'Function:') && valT:length() > 9 }, then: {
						local String is yieldT: valT:substring(start: 9, end: valT:length());
						Conditional:if(check: { self:isVoid(t: yieldT) }, then: {
							anyVoid: true;
						}, else: {
							anyValue: true;
							Conditional:if(check: { resT == '' }, then: {
								resT: yieldT;
							}, else: {
								Conditional:if(check: { !self:isAssignable(target: resT, source: yieldT) && !self:isAssignable(target: yieldT, source: resT) }, then: {
									self:addError(line: self:currentLine, msg: 'The match arms yield incompatible types (\'' . resT . '\' and \'' . yieldT . '\').');
									bad: true;
								});
							});
						});
					}, else: {
						anyVoid: true;
					});
				});
				return true;
			}
		);
		Conditional:if(check: { bad }, then: {
			return Conditional:if(check: { anyValue && resT != '' }, then: { resT }, else: { 'Void' });
		});
		Conditional:if(check: { anyValue && anyVoid }, then: {
			self:addError(line: self:currentLine, msg: 'The match arms mix value-yielding and void closures.');
		});
		Conditional:if(check: { rooted && anyValue }, then: {
			local ClassInfo is subjCls: self:findClass(name: subjT);
			local Boolean is todayEnum: self:allEnumNames:has(key: subjT);
			local String is missing: '';
			subjCls:members:each(action: local Function(Member is m){
				# Class-model: the held fields are the closed set.
				# Today's enum: the variants are (the namespace array is
				# metadata, not a variant — the registry's own convention).
				local Boolean is variantMember: Conditional:if(check: { todayEnum }, then: {
					!(m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY)
				}, else: {
					m:kind == MemberKind:FIELD && m:hasModifier(kw: Keyword:HELD)
				});
				Conditional:if(check: { variantMember }, then: {
					Conditional:if(check: { covered:indexOf(search: subjT . ':' . m:name, default: -1) < 0 }, then: {
						Conditional:if(check: { missing != '' }, then: {
							missing: missing . ', ';
						});
						missing: missing . subjT . ':' . m:name;
					});
				});
			});
			Conditional:if(check: { missing != '' && !hasElse }, then: {
				self:addError(line: self:currentLine, msg: 'Non-exhaustive match: missing arm(s) ' . missing . ' of \'' . subjT . '\'; add arms or an else.');
			});
			# Void-form matches fall through freely: the closed-set demand
			# binds the VALUE form only (a statement match's uncovered
			# subjects simply run nothing — the old `else: {}` was empty
			# by the same reasoning).
		});
		Conditional:if(check: { anyValue && !hasElse && !rooted }, then: {
			self:addError(line: self:currentLine, msg: 'A value-yielding match requires an else arm (the subject may match no key).');
		});
		return Conditional:if(check: { anyValue && resT != '' }, then: { resT }, else: { 'Void' });
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
	Function of String is checkPredicateArms(Expression is arms){
		local Boolean is hasElse: false;
		local Boolean is anyValue: false;
		local Boolean is anyVoid: false;
		local String is resT: '';
		local Boolean is bad: false;
		local Int is keyTotal: arms:mapKeys:length();
		local Int is ki: 0;
		while(
			evaluate: local Function of Boolean(){ return ki < keyTotal; },
			iteration: local Function of Boolean(){
				local Expression is key: arms:mapKeys:get(index: ki);
				local Expression is val: arms:mapValues:get(index: ki);
				ki: ki + 1;
				# The else arm closes the table: arms after it are dead.
				Conditional:if(check: { hasElse && !(key:kind == ExpressionKind:IDENT && key:str == 'else') }, then: {
					self:addError(line: self:currentLine, msg: 'Match arms after else are unreachable; move else last.');
					bad: true;
				});
				Conditional:if(check: { key:kind == ExpressionKind:IDENT && key:str == 'else' }, then: {
					Conditional:if(check: { hasElse }, then: {
						self:addError(line: self:currentLine, msg: 'Duplicate else arm in the match table.');
					});
					hasElse: true;
				}, else: {
					Conditional:if(check: { key:kind != ExpressionKind:ANON_FN }, then: {
						self:addError(line: self:currentLine, msg: 'Predicate match keys must be closures: `{ condition }`.');
						bad: true;
					}, else: {
						Conditional:if(check: { key:anonParams:length() > 0 }, then: {
							self:addError(line: self:currentLine, msg: 'Predicate match keys take no parameters.');
							bad: true;
						});
						Conditional:if(check: { key:anonReturnType:name == '' || key:anonReturnType:name == self:names:voidName() }, then: {
							key:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
						});
						self:inferExpressionType(expr: key);
					});
				});
				Conditional:if(check: { val:kind != ExpressionKind:ANON_FN }, then: {
					self:addError(line: self:currentLine, msg: 'Match arm bodies must be closures: \'key: { ... }\'.');
					bad: true;
				}, else: {
					Conditional:if(check: { val:anonParams:length() > 0 }, then: {
						self:addError(line: self:currentLine, msg: 'Predicate match arms take no parameters (there is no subject to bind).');
						bad: true;
					});
					self:inferExpressionType(expr: val);
					local String is valT: val:resolvedType;
					Conditional:if(check: { valT:startsWith(prefix: 'Function:') && valT:length() > 9 }, then: {
						local String is yieldT: valT:substring(start: 9, end: valT:length());
						Conditional:if(check: { self:isVoid(t: yieldT) }, then: {
							anyVoid: true;
						}, else: {
							anyValue: true;
							Conditional:if(check: { resT == '' }, then: {
								resT: yieldT;
							}, else: {
								Conditional:if(check: { !self:isAssignable(target: resT, source: yieldT) && !self:isAssignable(target: yieldT, source: resT) }, then: {
									self:addError(line: self:currentLine, msg: 'The match arms yield incompatible types (\'' . resT . '\' and \'' . yieldT . '\').');
									bad: true;
								});
							});
						});
					}, else: {
						anyVoid: true;
					});
				});
				return true;
			}
		);
		Conditional:if(check: { bad }, then: {
			return Conditional:if(check: { anyValue && resT != '' }, then: { resT }, else: { 'Void' });
		});
		Conditional:if(check: { anyValue && anyVoid }, then: {
			self:addError(line: self:currentLine, msg: 'The match arms mix value-yielding and void closures.');
		});
		Conditional:if(check: { anyValue && !hasElse }, then: {
			self:addError(line: self:currentLine, msg: 'A value-yielding predicate match requires an else arm (no key may hold).');
		});
		return Conditional:if(check: { anyValue && resT != '' }, then: { resT }, else: { 'Void' });
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
		Conditional:if(check: { baseClassName == '' || baseClassName == Primitive:ANY:value() || baseClassName == 'Loops' }, then: {
			return;
		});
		local Member is m: self:lookupOverloadedMember(className: self:memberLookupRoot(className: targetType), methodName: callExpr:methodName, idx: callExpr:num);
		local String is sigDisplay: baseClassName;
		Conditional:if(check: { m:kind != MemberKind:METHOD }, then: {
			# No instance method: the receiver shape
			# may still reach a held function — a bare class-name root,
			# never self or an instance-typed name.
			Conditional:if(check: { callExpr:methodTarget:kind == ExpressionKind:IDENT || callExpr:methodTarget:kind == ExpressionKind:PATH }, then: {
				local String is sigRoot: callExpr:methodTarget:str;
				Conditional:if(check: { callExpr:methodTarget:kind == ExpressionKind:PATH && callExpr:methodTarget:pathSegments:length() > 0 }, then: {
					sigRoot: callExpr:methodTarget:pathSegments:get(index: 0);
				});
				Conditional:if(check: { sigRoot != '' && sigRoot != self:names:selfIdent() && !self:localVars:has(key: sigRoot) && !self:fieldTypes:has(key: sigRoot) && self:registeredClasses:has(key: sigRoot) }, then: {
					m: self:findHeldMethod(className: sigRoot, methodName: callExpr:methodName);
					Conditional:if(check: { m:name != '' }, then: {
						sigDisplay: sigRoot;
					});
				});
			});
		});
		Conditional:if(check: { m:kind != MemberKind:METHOD }, then: {
			return;
		});
		self:validateArgsAgainstSignature(callExpr: callExpr, params: m:params, recvCls: self:findClass(name: baseClassName), displayTarget: sigDisplay);
	}

	## Validates a call's arguments against an explicit parameter list:
	## named arguments match by parameter name, positional by index,
	## defaults fill the rest. Shared by the instance and the held
	## dispatch paths.
	##
	## @param callExpr: The CALL expression.
	## @param params: The signature's parameters.
	## @param recvCls: The declaring class (its type params are exempt).
	## @param displayTarget: The display spelling for diagnostics.
	Function is validateArgsAgainstSignature(Expression is callExpr, Array of Parameter is params, ClassInfo is recvCls, String is displayTarget){
		Conditional:if(check: { params:length() == 0 }, then: {
			return;
		});
		local Array of String is recvTypeParams: recvCls:typeParams;
		local Int is pIdx: 0;
		params:each(action: local Function(Parameter is p){
			local String is pName: p:name;
			local String is pT: p:paramType:name;
			# a Function-typed param enforces
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
						local String is msg: 'Argument \'' . label . '\' for \'' . displayTarget . '.' . callExpr:methodName . '\': cannot assign \'' . argT . '\' to \'' . self:displayType(t: pTF) . '\'.';
						self:addError(line: self:currentLine, msg: msg);
					});
				}, else: {
					Conditional:if(check: { !p:hasDefault && !self:isBindingDeclaration(cls: recvCls) }, then: {
						# Binding declarations (sysinternal + runtime-managed)
						# sketch API surface, not call contracts — their C
						# implementations carry optional/variadic semantics.
						local String is msg: 'Missing argument \'' . pName . '\' for \'' . displayTarget . '.' . callExpr:methodName . '\'.';
						self:addError(line: self:currentLine, msg: msg);
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
		local String is baseName: self:memberLookupRoot(className: className);
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		self:collectOverloadGroup(className: baseName, methodName: methodName, acc: group, ownerAcc: ownerAcc);
		Conditional:if(check: { group:length() == 0 }, then: {
			return none;
		});
		# §I.3: no mixed calls — enforced globally, including
		# single-member names. The scoped-region desugaring no longer
		# produces mixed calls: its remainder binds to the unbound last
		# Function parameter instead of riding as an argument (§as).
		local Array of NamedArg is allArgs: expr:methodArgs;
		local Array of NamedArg is args: allArgs;
		local Boolean is isScoped: expr:scopedRemainder;
		Conditional:if(check: { isScoped }, then: {
			local Array of NamedArg is explicit: [];
			local Int is ei: 0;
			while(
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
			self:addError(line: self:currentLine, msg: 'Mixed positional and named arguments are not supported; use one form (§I.3).');
			return none;
		});
		Conditional:if(check: { group:length() == 1 }, then: {
			local Member is only: group:get(index: 0);
			Conditional:if(check: { isScoped && !self:scopeSlotOk(m: only, explicitCount: args:length()) }, then: {
				self:addError(line: self:currentLine, msg: 'The scoped region requires exactly one unbound Function parameter at the end of \'' . baseName . '.' . methodName . '\' (§as).');
				return none;
			});
			expr:num: 0;
			return only;
		});
		Conditional:if(check: { allNamed }, then: {
			local Boolean is dupArg: false;
			local Int is ai: 0;
			while(
				evaluate: local Function of Boolean(){ return !dupArg && ai < args:length(); },
				iteration: local Function of Boolean(){
					local Int is aj: ai + 1;
					while(
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
		# §as: a scoped remainder binds to an unbound last
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
				expr:num: self:indexOfMember(group: group, m: sel);
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
				self:addError(line: self:currentLine, msg: 'The scoped region has no open scope slot in \'' . baseName . '.' . methodName . '\': every parameter is already bound (§as).');
				return none;
			});
			expr:num: self:indexOfMember(group: group, m: sel);
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
				self:addError(line: self:currentLine, msg: 'The scoped region has no open scope slot in \'' . baseName . '.' . methodName . '\': every parameter is already bound (§as).');
				return none;
			});
			expr:num: self:indexOfMember(group: group, m: sel);
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
				expr:num: self:indexOfMember(group: group, m: sel);
				return sel;
			});
		});
		Conditional:if(check: { exact:length() > 1 }, then: {
			self:addError(line: self:currentLine, msg: 'Ambiguous call to \'' . baseName . '.' . methodName . '\': the arguments match multiple overloads; use named arguments (§I.2).');
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
		self:addError(line: self:currentLine, msg: 'No exact overload of \'' . baseName . '.' . methodName . '\' for (' . argTypes . '); cast the arguments or give the signatures distinct names (§I.2).');
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
		Conditional:if(check: { ownerAcc:length() > 0 || acc:length() > 0 || className == '' || className == 'Any' || visited:has(key: className) }, then: {
			return;
		});
		visited:set(key: className, value: 'true');
		# the qualified nested-class name walks the inner class
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
			# Instance overloads are held-blind: the
			# class-name prefix reaches exactly the held members.
			Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == methodName && !m:hasModifier(kw: Keyword:HELD) }, then: {
				acc:add(item: m);
			});
		});
		Conditional:if(check: { acc:length() > 0 }, then: {
			# the owner's qualified identity — the bare name of a
			# nested class is not unique across outers.
			ownerAcc:add(item: cls:qualifiedName());
			return;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			self:collectOverloadGroup(className: baseName, methodName: methodName, visited: visited, acc: acc, ownerAcc: ownerAcc);
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
			# a Function-typed param compares in the
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
		self:collectOverloadGroup(className: baseName, methodName: selected:name, acc: group, ownerAcc: ownerAcc);
		Conditional:if(check: { group:length() <= 1 || ownerAcc:length() == 0 }, then: {
			return self:lookupMethodReturnType(className: className, methodName: selected:name);
		});
		local String is owner: ownerAcc:get(index: 0);
		local ClassInfo is ownerCls: self:findClass(name: owner);
		Conditional:if(check: { ownerCls:name == '' }, then: {
			return '';
		});
		local Array of String is typeArgs: [];
		# The resolved qualified root absorbs the colon chain ; bare
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
		self:collectOverloadGroup(className: self:memberLookupRoot(className: className), methodName: methodName, acc: group, ownerAcc: ownerAcc);
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
	## inherited like the fields they synthesize (§2.1).
	##
	## @param className: Receiver class name.
	## @return: true when imported somewhere up the chain.
	Function of Boolean is isAsImportedInherited(String is className){
		return self:importsAsAnywhere(clsName: self:currentClassName, targetName: className);
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
	Function of Boolean is shadowsAsFunction(String is name){
		local String is t: self:localVars:getString(key: name, default: self:fieldTypes:getString(key: name, default: ''));
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
		Conditional:if(check: { clsName == '' || clsName == 'Any' || visited:has(key: clsName) }, then: {
			return false;
		});
		visited:set(key: clsName, value: 'true');
		local ClassInfo is cls: self:findClass(name: clsName);
		Conditional:if(check: { cls:name == '' }, then: {
			return false;
		});
		Conditional:if(check: { cls:instanceImportsAs(name: targetName) }, then: {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:importsAsAnywhere(clsName: baseName, targetName: targetName, visited: visited) }, then: {
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
		self:collectBareProviders(clsName: self:currentClassName, methodName: methodName, acc: out);
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
		Conditional:if(check: { clsName == '' || clsName == 'Any' || visited:has(key: clsName) }, then: {
			return;
		});
		visited:set(key: clsName, value: 'true');
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
								local String is prov: seg:str;
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
			self:collectBareProviders(clsName: baseName, methodName: methodName, visited: visited, acc: acc);
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
		Conditional:if(check: { self:nestedScopeFor != className }, then: {
			self:nestedScopeMap: Map:init();
			self:nestedScopeFor: className;
			self:collectNestedScopeEntries(clsName: className);
		});
		return self:nestedScopeMap:getString(key: typeName, default: '');
	}

	## One scope-map pass over the ancestor lattice: every visited class
	## contributes its own nested classes and its as-imported classes'
	## nested classes to [nestedScopeMap].
	##
	## @param clsName: Class being visited.
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	Function is collectNestedScopeEntries(String is clsName, Map of String to String is visited: Map:init()){
		Conditional:if(check: { clsName == '' || clsName == 'Any' || visited:has(key: clsName) }, then: {
			return;
		});
		visited:set(key: clsName, value: 'true');
		local ClassInfo is cls: self:findClass(name: clsName);
		Conditional:if(check: { cls:name == '' }, then: {
			return;
		});
		# Own nested classes.
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:kind == MemberKind:CLASS }, then: {
				self:appendNestedScopeEntry(bare: m:nestedClass:name, q: m:nestedClass:qualifiedName());
			});
		});
		# The as-imported classes' nested classes.
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, then: {
				m:initExpr:arrayItems:each(action: local Function(Expression is item){
					Conditional:if(check: { item:kind == ExpressionKind:ARRAY }, then: {
						item:arrayItems:each(action: local Function(Expression is seg){
							Conditional:if(check: { seg:kind == ExpressionKind:USING_AS }, then: {
								local ClassInfo is provCls: self:findClass(name: seg:str);
								Conditional:if(check: { provCls:name != '' }, then: {
									provCls:members:each(action: local Function(Member is nm){
										Conditional:if(check: { nm:kind == MemberKind:CLASS }, then: {
											self:appendNestedScopeEntry(bare: nm:nestedClass:name, q: nm:nestedClass:qualifiedName());
										});
									});
								});
							});
						});
					});
				});
			});
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			self:collectNestedScopeEntries(clsName: baseName, visited: visited);
		});
	}

	## Adds one qualified identity under its bare name, deduplicating.
	##
	## @param bare: The nested class's bare name (the map key).
	## @param q: The qualified identity ('Outer:Inner').
	Function is appendNestedScopeEntry(String is bare, String is q){
		Conditional:if(check: { bare == '' || q == '' }, then: {
			return;
		});
		local String is cur: self:nestedScopeMap:getString(key: bare, default: '');
		Conditional:if(check: { cur == '' }, then: {
			self:nestedScopeMap:set(key: bare, value: q);
		}, else: {
			local Boolean is dup: false;
			cur:split(delimiter: ';'):each(action: local Function(String is got){
				Conditional:if(check: { got == q }, then: {
					dup: true;
				});
			});
			Conditional:if(check: { !dup }, then: {
				self:nestedScopeMap:set(key: bare, value: cur . ';' . q);
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
		Conditional:if(check: { className == '' || className == 'Any' || visited:has(key: className) }, then: {
			return false;
		});
		visited:set(key: className, value: 'true');
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		Conditional:if(check: { cls:name == '' }, then: {
			return false;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:declaresOrInherits(className: baseName, methodName: methodName, visited: visited) }, then: {
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
		Conditional:if(check: { className == '' || className == 'Any' || visited:has(key: className) }, then: {
			return false;
		});
		visited:set(key: className, value: 'true');
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
			Conditional:if(check: { !viaParent && self:declaresOrInherits(className: baseName, methodName: methodName, visited: visited) }, then: {
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
		Conditional:if(check: { className == '' || className == 'Any' || visited:has(key: className) }, then: {
			return false;
		});
		visited:set(key: className, value: 'true');
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		Conditional:if(check: { cls:name == '' }, then: {
			return false;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:nearestGroupOverloaded(className: baseName, methodName: methodName, visited: visited) }, then: {
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
		Conditional:if(check: { className == '' || className == 'Any' || visited:has(key: className) }, then: {
			return false;
		});
		visited:set(key: className, value: 'true');
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
			Conditional:if(check: { !viaParent && self:nearestGroupOverloaded(className: baseName, methodName: methodName, visited: visited) }, then: {
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
		self:programClasses:each(action: local Function(ClassInfo is c){
			local Array of Member is members: c:members;
			local Int is i: 0;
			while(
				evaluate: local Function of Boolean(){ return i < members:length(); },
				iteration: local Function of Boolean(){
					local Member is m: members:get(index: i);
					Conditional:if(check: { m:kind == MemberKind:METHOD }, then: {
						local Boolean is earlier: false;
						local Int is j: 0;
						while(
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
							while(
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
								while(
									evaluate: local Function of Boolean(){ return a < members:length(); },
									iteration: local Function of Boolean(){
										local Member is ma: members:get(index: a);
										Conditional:if(check: { ma:kind == MemberKind:METHOD && ma:name == m:name }, then: {
											local Int is b: a + 1;
											while(
												evaluate: local Function of Boolean(){ return b < members:length(); },
												iteration: local Function of Boolean(){
													local Member is mb: members:get(index: b);
													Conditional:if(check: { mb:kind == MemberKind:METHOD && mb:name == m:name && self:checkerSameSignature(a: ma, b: mb) }, then: {
														self:addError(line: m:line, msg: 'Methods \'' . m:name . '\' in class \'' . c:name . '\' declare identical signatures; overloads must differ (§I.1).');
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
								while(
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
									self:addError(line: m:line, msg: 'Overloaded method \'' . m:name . '\' must declare concrete parameter types (§I.3).');
								});
								Conditional:if(check: { m:name != 'init' && self:ancestorDeclares(className: c:name, methodName: m:name) }, then: {
									self:addError(line: m:line, msg: 'Cannot overload \'' . m:name . '\': the name is declared on an ancestor (§I.3).');
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

	## §I.1: signature equality for the legality pass —
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
		while(
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
		Conditional:if(check: { targetName == '' || self:isPrimitive(t: targetName) || targetName == 'Array' || targetName == 'Map' || targetName == 'List' || targetName == 'String' || targetName == 'Function' || targetName == 'LoopControl' }, then: {
			return true;
		});
		return self:accessInClass(className: className, targetName: targetName);
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
				# the flattened nested classes match their qualified
				# identity too — the outer's own rewritten references
				# ('LibA:Helper') grant as the bare declaration does.
				Conditional:if(check: { c:name == targetName || c:qualifiedName() == targetName }, then: {
					granted: true;
					return;
				});
				c:members:each(action: local Function(Member is m){
					Conditional:if(check: { !granted && m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, then: {
						m:initExpr:arrayItems:each(action: local Function(Expression is item){
							Conditional:if(check: { !granted && item:kind == ExpressionKind:ARRAY }, then: {
								local String is terminal: '';
								local Boolean is terminalAs: false;
								local String is nsJoined: '';
								item:arrayItems:each(action: local Function(Expression is seg){
									Conditional:if(check: { seg:kind == ExpressionKind:IDENT || seg:kind == ExpressionKind:USING_AS }, then: {
										terminal: seg:str;
										terminalAs: seg:kind == ExpressionKind:USING_AS;
									}, else: {
										Conditional:if(check: { nsJoined == '' }, then: {
											nsJoined: seg:str;
										}, else: {
											nsJoined: nsJoined . ':' . seg:str;
										});
									});
								});
								# the qualified nested reference
								# ('Outer:Inner') rides the parent's grant — the terminal
								# matches the target's root segment. IV.6 strictness: the
								# as-form grants functions and the qualified nested
								# references; the BARE parent reference (and with it
								# construction) requires the plain type import.
								local String is targetRoot: targetName:split(delimiter: ':'):get(index: 0);
								Conditional:if(check: { terminal == targetName || terminal == targetRoot }, then: {
									Conditional:if(check: { !terminalAs || targetName:contains(needle: ':') }, then: {
										granted: true;
									});
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
	## @param visited: The visited-class set — the walk marks on entry
## and terminates on revisit (any depth, cycles included).
	## @return: true when access is granted at this level or above.
	Function of Boolean is accessInClass(String is className, String is targetName, Map of String to String is visited: Map:init()){
		Conditional:if(check: { visited:has(key: className) || className == '' }, then: {
			return false;
		});
		visited:set(key: className, value: 'true');
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
						local Boolean is terminalAs: false;
						local String is nsJoined: '';
						item:arrayItems:each(action: local Function(Expression is seg){
							Conditional:if(check: { seg:kind == ExpressionKind:IDENT || seg:kind == ExpressionKind:USING_AS }, then: {
								terminal: seg:str;
								terminalAs: seg:kind == ExpressionKind:USING_AS;
							}, else: {
								Conditional:if(check: { nsJoined == '' }, then: {
									nsJoined: seg:str;
								}, else: {
									nsJoined: nsJoined . ':' . seg:str;
								});
							});
						});
						# the same root-segment grant for
						# the qualified nested reference. IV.6 strictness: the as-form
						# grants functions and the qualified nested references; the
						# BARE parent reference (and with it construction) requires
						# the plain type import.
						local String is targetRoot2: targetName:split(delimiter: ':'):get(index: 0);
						Conditional:if(check: { terminal == targetName || terminal == targetRoot2 }, then: {
							Conditional:if(check: { !terminalAs || targetName:contains(needle: ':') }, then: {
								granted: true;
							});
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
			Conditional:if(check: { !viaParent && self:accessInClass(className: baseName, targetName: targetName, visited: visited) }, then: {
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
		Conditional:if(check: { t:name == '' }, then: {
			return;
		});
		# the bare nested-class
		# reference resolves through the per-scope map — one lookup. Exactly
		# one provider rewrites the type to its qualified identity (the
		# parent grant covers it downstream); several collide and force the
		# qualification — the same rule the bare function calls run.
		Conditional:if(check: { !t:name:contains(needle: ':') }, then: {
			local String is idents: self:nestedScopeResolve(className: self:currentClassName, typeName: t:name);
			Conditional:if(check: { idents != '' }, then: {
				local Array of String is provs: idents:split(delimiter: ';');
				Conditional:if(check: { provs:length() == 1 }, then: {
					t:name: provs:get(index: 0);
				});
				Conditional:if(check: { provs:length() > 1 }, then: {
					local String is listed: '';
					provs:each(action: local Function(String is p){
						Conditional:if(check: { listed == '' }, then: {
							listed: p;
						}, else: {
							listed: listed . ' and ' . p;
						});
					});
					self:addError(line: line, msg: 'Type \'' . t:name . '\' is provided by ' . listed . '; qualify the reference.');
					return;
				});
			});
		});
		Conditional:if(check: { self:registeredClasses:has(key: t:name) && !self:classHasAccess(className: self:currentClassName, targetName: t:name) }, then: {
			self:addError(line: line, msg: '\'' . t:name . '\' is not imported by \'' . self:currentClassName . '\'; add it to the using declaration (§I.6).');
		});
		t:params:each(action: local Function(Type is p){
			self:validateTypeAccess(t: p, line: line);
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
			self:addError(line: self:currentLine, msg: 'Instance imports (as ClassName()) may only appear as entries of a using declaration (E1).');
			expr:resolvedType: '';
			return '';
		});

		Conditional:match(on: kind, when: [
			ExpressionKind:STRING: {
				res: Primitive:STRING:value();
			},
			ExpressionKind:NUMBER: {
				res: Primitive:INT:value();
			},
			ExpressionKind:FLOAT: {
				res: Primitive:FLOAT:value();
			},
			ExpressionKind:BOOL: {
				res: Primitive:BOOLEAN:value();
			},
			ExpressionKind:IDENT: {
				local String is name: expr:str;
				Conditional:if(check: { name == self:names:selfIdent() }, then: {
					# A held member body has no instance
					# — except a function-variable call target: the closure
					# invocation never touches the instance.
					Conditional:if(check: { (self:inHeldInit || self:inHeldFunction) && !self:inHeldFnVarTarget }, then: {
						self:addError(line: self:currentLine, msg: 'A held member body has no instance: \'self\' is not available.');
					});
					res: self:currentClassName;
				}, else: {
					Conditional:if(check: { self:localVars:has(key: name) }, then: {
						res: self:localVars:getString(key: name, default: Primitive:ANY:value());
					}, else: {
						Conditional:if(check: { self:fieldTypes:has(key: name) }, then: {
							# A held initializer has no instance: instance fields
							# are not reachable from it.
							Conditional:if(check: { self:inHeldInit }, then: {
								self:addError(line: self:currentLine, msg: 'A held initializer has no instance: field \'' . name . '\' is not reachable from it.');
							});
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
			},
			ExpressionKind:PATH: {
				local Array of String is segs: expr:pathSegments;
				Conditional:if(check: { segs:length() > 0 }, then: {
					local String is root: segs:get(index: 0);
					local String is rootType: '';
					# Held admission: the first segment
					# after a class-name root resolved as a held field — the
					# The path resolution loop below then consumes it via lookupHeldFieldType.
					local Boolean is heldAdmitted: false;
					Conditional:if(check: { root == self:names:selfIdent() }, then: {
						# A held member body has no instance.
						Conditional:if(check: { self:inHeldInit || self:inHeldFunction }, then: {
							self:addError(line: self:currentLine, msg: 'A held member body has no instance: \'self\' is not available.');
						});
						rootType: self:currentClassName;
						Conditional:if(check: { segs:length() >= 2 && self:unassignedFields:has(key: segs:get(index: 1)) }, then: {
							self:addError(line: self:currentLine, msg: 'Field \'' . segs:get(index: 1) . '\' in class \'' . self:currentClassName . '\' is read before being initialized.');
						});
						Conditional:if(check: { segs:length() >= 2 }, then: {
							local String is fName: segs:get(index: 1);
							# Strict held resolution: the
							# instance lookup is the truth — a held name through
							# self is the class-scoped slot reached by its
							# class-name prefix, never by an instance.
							Conditional:if(check: { self:lookupFieldType(className: self:currentClassName, fieldName: fName) != '' }, then: {
								local String is fOwner: self:findMemberOwnerClass(className: self:currentClassName, memberName: fName);
								Conditional:if(check: { fOwner != '' }, then: {
									self:checkMemberVisibility(ownerClass: fOwner, member: self:findAncestorMember(className: self:currentClassName, memberName: fName), memberName: fName);
								});
							}, else: {
								Conditional:if(check: { self:findHeldMember(className: self:currentClassName, memberName: fName):name != '' }, then: {
									self:addError(line: self:currentLine, msg: 'Held member \'' . self:currentClassName . ':' . fName . '\' is class-scoped: reach it through the class name, not an instance.');
								});
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
										# the nested-class chain —
										# 'Outer:Inner' and the inner-of-inner 'Outer:Mid:Deep' —
										# walks CLASS-kind members per segment and resolves to
										# the deepest class's qualified identity.
										local Boolean is chainResolved: false;
										Conditional:if(check: { segs:length() >= 2 }, then: {
											local ClassInfo is chainCls: self:findClass(name: root);
											local Boolean is chainOk: chainCls:name != '';
											local Int is chainIdx: 1;
											while(
												evaluate: local Function of Boolean(){ return chainOk && chainIdx < segs:length(); },
												iteration: local Function of Boolean(){
													local String is nextType: '';
													chainCls:members:each(action: local Function(Member is m){
														Conditional:if(check: { m:kind == MemberKind:CLASS && m:nestedClass:name == segs:get(index: chainIdx) }, then: {
															nextType: chainCls:qualifiedName() . ':' . segs:get(index: chainIdx);
														});
													});
													Conditional:if(check: { nextType != '' }, then: {
														chainCls: self:findClass(name: nextType);
														Conditional:if(check: { chainCls:name == '' }, then: {
															chainOk: false;
														});
														chainIdx: chainIdx + 1;
													}, else: {
														chainOk: false;
													});
													return true;
												}
											);
											Conditional:if(check: { chainOk && chainIdx == segs:length() }, then: {
												rootType: chainCls:qualifiedName();
												chainResolved: true;
											});
										});
										# §2.3, generalized by the
										# class-name prefix reaches exactly the HELD members —
										# an instance reference reaches exactly the instance
										# members. The first segment after a class root resolves
										# as a held field (own, then the lattice, nearest wins);
										# anything else through the prefix stays rejected.
										# The resolved nested-class chains are exempt.
										local Member is heldM: Member:init(kind: MemberKind:FIELD);
										Conditional:if(check: { segs:length() >= 2 && !chainResolved }, then: {
											heldM: self:findHeldMember(className: root, memberName: segs:get(index: 1));
										});
										Conditional:if(check: { heldM:name != '' && heldM:kind == MemberKind:FIELD }, then: {
											local String is heldOwner: self:findHeldOwnerClass(className: root, memberName: heldM:name);
											# The held cycle rule: a held initializer may not
											# reference a held member of its own class — the
											# mutual once-guards would deadlock. Ancestors'
											# held members initialize independently.
											Conditional:if(check: { self:inHeldInit && heldOwner == self:currentClassName }, then: {
												self:addError(line: self:currentLine, msg: 'Held initializer of \'' . self:currentClassName . '\' cannot reference held member \'' . root . ':' . heldM:name . '\' of the same class; the once-guards would deadlock.');
											});
											self:checkMemberVisibility(ownerClass: heldOwner, member: heldM, memberName: heldM:name);
											heldAdmitted: true;
										}, else: {
											Conditional:if(check: { self:findHeldMethod(className: root, methodName: segs:get(index: 1)):name != '' }, then: {
												self:addError(line: self:currentLine, msg: 'Held function \'' . root . ':' . segs:get(index: 1) . '\' must be called; bare references to held functions are not supported (the call form is ' . root . ':' . segs:get(index: 1) . '(...)).');
												rootType: '';
											}, else: {
												# The resolution hook: a name
												# matching no declared member resolves through the
												# class's 'resolveHeld' contract — declared members
												# always win, so an instance member through the
												# prefix keeps its rejection.
												local Member is resolver: self:findHeldMethod(className: root, methodName: ContractMethod:RESOLVE_HELD:value());
												local Boolean is declaredInstance: self:lookupFieldType(className: root, fieldName: segs:get(index: 1)) != '' || self:lookupAnyMember(className: root, methodName: segs:get(index: 1)):kind == MemberKind:METHOD;
												Conditional:if(check: { segs:length() >= 2 && !chainResolved && !self:allEnumNames:has(key: root) && !self:isPrimitive(t: root) && root != 'Array' && root != 'Map' && root != 'List' && root != 'String' && root != 'Function' && root != 'LoopControl' && (resolver:name == '' || declaredInstance) }, then: {
													self:addError(line: self:currentLine, msg: 'Fields are not reachable through the class-name prefix \'' . root . '\'; only held members are (§2.3).');
													rootType: '';
													}, else: {
														Conditional:if(check: { resolver:name != '' && !declaredInstance }, then: {
															# The hook admits — the reference types as the
															# resolver's declared return type
															# §5.4). Anti-recursion: inside the hook body,
															# an unknown name through its own class prefix
															# would recurse forever.
															Conditional:if(check: { self:inHeldFunction && self:currentMethodName == ContractMethod:RESOLVE_HELD:value() && root == self:currentClassName }, then: {
																self:addError(line: self:currentLine, msg: 'The resolution hook cannot resolve through its own class prefix (\'' . root . ':' . segs:get(index: 1) . '\'); declare the member, or return it from the resolver directly.');
															});
															self:checkMemberVisibility(ownerClass: self:findHeldMethodOwner(className: root, methodName: ContractMethod:RESOLVE_HELD:value()), member: resolver, memberName: ContractMethod:RESOLVE_HELD:value());
															res: self:formatTypeString(t: resolver:memberType);
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
					local String is currType: rootType;
					local Int is pIdx: 1;
					Loops({ currType != '' && pIdx < segs:length() }, {
						local String is seg: segs:get(index: pIdx);
						pIdx: pIdx + 1;
						Conditional:if(check: { !self:allEnumNames:has(key: currType) }, then: {
							Conditional:if(check: { heldAdmitted && pIdx == 2 }, then: {
								currType: self:lookupHeldFieldType(className: currType, fieldName: seg);
							}, else: {
								currType: self:lookupFieldType(className: currType, fieldName: seg);
							});
						});
					});
					Conditional:if(check: { currType != '' }, then: {
						res: currType;
					}, else: {
						# Strict held resolution: an
						# instance-typed receiver (a local, a field) whose
						# segment 1 is a held member gets the pointed
						# diagnostic instead of a silent Any.
						Conditional:if(check: { segs:length() >= 2 && !heldAdmitted && rootType != '' && rootType != Primitive:ANY:value() }, then: {
							local String is rBase: rootType:split(delimiter: ':'):get(index: 0);
							Conditional:if(check: { self:registeredClasses:has(key: rBase) && self:findHeldMember(className: rBase, memberName: segs:get(index: 1)):name != '' }, then: {
								self:addError(line: self:currentLine, msg: 'Held member \'' . rBase . ':' . segs:get(index: 1) . '\' is class-scoped: reach it through the class name, not an instance.');
							});
						});
					});
				});
			},
			ExpressionKind:BINARY: {
				# the expected type flows into the
				# operands so a value-yielding branch call nested in an
				# expression (e.g. `n + if(...)`) types in context.
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr, expected: expected);
				local String is rightT: self:inferExpressionType(expr: expr:rightExpr, expected: expected);
				local String is op: expr:str;
				Conditional:match(on: op, when: [
					'.': {
						res: Primitive:STRING:value();
					},
					['==', '!=', 'is', '<', '<=', '>', '>=']: {
						res: Primitive:BOOLEAN:value();
						# hardening (D5): relational ordering on
						# String is lexicographic — and only String-to-String.
						local Boolean is isRel: op == '<' || op == '<=' || op == '>' || op == '>=';
						local Boolean is leftStr: leftT == 'String';
						local Boolean is rightStr: rightT == 'String';
						Conditional:if(check: { isRel && (leftStr || rightStr) && !(leftStr && rightStr) }, then: {
							self:addError(line: self:currentLine, msg: 'Relational operator \'' . op . '\' requires two String operands (got \'' . leftT . '\' and \'' . rightT . '\').');
						});
					},
					['&&', '||']: {
						res: Primitive:BOOLEAN:value();
					},
					['+', '-', '*', '/', '%']: {
						res: Conditional:if(check: { leftT == 'Float' || rightT == 'Float' }, then: { 'Float' }, else: { Primitive:INT:value() });
					},
					['&', '|', '^', '<<', '>>']: {
						res: Primitive:INT:value();
						Conditional:if(check: { (leftT != '' && leftT != 'Any' && leftT != Primitive:INT:value()) ||
							(rightT != '' && rightT != 'Any' && rightT != Primitive:INT:value()) }, then: {
							local String is msg: 'Bitwise operator \'' . op . '\' requires Int operands (got \'' . leftT . '\' and \'' . rightT . '\').';
							self:addError(line: self:currentLine, msg: msg);
						});
					},
					else: {
						res: Primitive:INT:value();
					}
				]);
			},
			ExpressionKind:CAST: {
				local String is innerT: self:inferExpressionType(expr: expr:leftExpr);
				local String is target: expr:str;
				local String is src: Conditional:if(check: { innerT != '' }, then: { innerT }, else: { Primitive:ANY:value() });
				local Boolean is isFormat: target == 'Hex' || target == 'Bin' || target == 'Oct';
				# Every non-format cast takes no arguments.
				Conditional:if(check: { expr:castArgs:length() > 0 && !isFormat }, then: {
					self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' takes no arguments.');
				});
				Conditional:match(on: target, when: [
					['Hex', 'Bin', 'Oct']: {
						Conditional:if(check: { expr:castArgs:length() > 1 }, then: {
							self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' accepts at most one width argument.');
						});
						Conditional:if(check: { src != 'Any' && src != 'String' && src != Primitive:INT:value() }, then: {
							self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' requires an Int or String operand (got \'' . src . '\').');
						});
						res: Conditional:if(check: { src == 'String' }, then: { Primitive:INT:value() }, else: { 'String' });
					},
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
				]);
			},
			ExpressionKind:UNARY: {
				local String is innerT: self:inferExpressionType(expr: expr:unaryExpr);
				Conditional:if(check: { expr:str == '~' && innerT != '' && innerT != 'Any' && innerT != Primitive:INT:value() }, then: {
					local String is msg: 'Bitwise complement \'~\' requires an Int operand (got \'' . innerT . '\').';
					self:addError(line: self:currentLine, msg: msg);
				});
				Conditional:if(check: { (expr:str == '++' || expr:str == '--' || expr:str == 'post++' || expr:str == 'post--') && innerT != '' && innerT != 'Any' && innerT != Primitive:INT:value() }, then: {
					local String is msg: 'Operator \'' . expr:str . '\' requires an Int operand (got \'' . innerT . '\').';
					self:addError(line: self:currentLine, msg: msg);
				});
				Conditional:if(check: { expr:str == '!' }, then: {
					res: Primitive:BOOLEAN:value();
				}, else: {
					res: innerT;
				});
			},
			ExpressionKind:ARRAY: {
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
			},
			ExpressionKind:MAP: {
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
			},
			ExpressionKind:FIELD_ACCESS: {
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr);
				Conditional:if(check: { leftT == '' || leftT == 'Any' || self:isPrimitive(t: leftT) }, then: {
					res: 'Any';
				}, else: {
					local Array of String is faParts: leftT:split(delimiter: ':');
					local String is faBase: faParts:get(index: 0);
					local String is fName: expr:str;
						local String is fOwner: self:findMemberOwnerClass(className: faBase, memberName: fName);
						Conditional:if(check: { fOwner != '' }, then: {
							self:checkMemberVisibility(ownerClass: fOwner, member: self:findAncestorMember(className: faBase, memberName: fName), memberName: fName);
						});
						local String is fT: self:lookupFieldType(className: leftT, fieldName: fName);
						# Strict held resolution: the
						# class-name prefix reaches exactly the held members;
						# an instance receiver reaches exactly the instance
						# members.
						Conditional:if(check: { fT == '' && self:registeredClasses:has(key: faBase) && self:findHeldMember(className: faBase, memberName: fName):name != '' }, then: {
							self:addError(line: self:currentLine, msg: 'Held member \'' . faBase . ':' . fName . '\' is class-scoped: reach it through the class name, not an instance.');
						});
					res: Conditional:if(check: { fT != '' }, then: { fT }, else: { 'Any' });
				});
			},
			ExpressionKind:INDEX: {
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
			},
			ExpressionKind:ANON_FN: {
				local Map of String to String is savedVars: Map:init();
				local Array of String is existingKeys: self:localVars:keys();
				existingKeys:each(action: local Function(String is k){
					savedVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
				});
				local String is savedRet: self:currentMethodReturnType;
				local Expression is savedAnonNode: self:currentAnonNode;
				self:currentAnonNode: expr;
				# the yield flag scopes to THIS closure —
				# the enclosing closure's last-statement check must not leak
				# into nested closures' return typing.
				local Boolean is savedYieldFlag: self:checkingValueYield;
				self:checkingValueYield: false;

				Conditional:if(check: { !self:inBranchClosure }, then: {
					# the bidirectional closure typing —
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
					# the last statement of a
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
				# the Kotlin convention — the closure
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
								local String is msg: 'The closure\'s last expression yields \'' . lastT . '\', but the closure must return \'' . expr:anonReturnType:name . '\'.';
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
			},
			ExpressionKind:CALL: {
				res: self:inferCall(expr: expr, expected: expected);
			},
			else: {
				res: 'Any';
			}
		]);

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
		# A function-variable invocation (self:missing()) inside a held
		# body infers its target through the IDENT arm — exempt the
		# no-instance error for exactly that shape.
		local Boolean is savedFnVarTarget: self:inHeldFnVarTarget;
		Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:str == self:names:selfIdent() && self:localVars:getString(key: expr:methodName, default: ''):startsWith(prefix: 'Function') }, then: {
			self:inHeldFnVarTarget: true;
		});
		local String is targetType: self:inferExpressionType(expr: expr:methodTarget);
		self:inHeldFnVarTarget: savedFnVarTarget;
		local String is method: expr:methodName;
		local String is res: 'Any';

		local String is targetName: expr:methodTarget:str;
		Conditional:if(check: { targetName == '' && expr:methodTarget:kind == ExpressionKind:PATH && expr:methodTarget:pathSegments:length() > 0 }, then: {
			targetName: expr:methodTarget:pathSegments:get(index: expr:methodTarget:pathSegments:length() - 1);
		});

		# Nested-construction shorthand: a class-name
		# receiver naming a nested class constructs it —
		# `Result:Ok(data: 'x')` ≡ `Result:Ok:init(data: 'x')`. The call
		# rewrites in place and falls through to the init path.
		Conditional:if(check: { (expr:methodTarget:kind == ExpressionKind:IDENT || expr:methodTarget:kind == ExpressionKind:PATH) && method != 'init' && self:registeredClasses:has(key: targetName) && !self:localVars:has(key: targetName) && !self:fieldTypes:has(key: targetName) }, then: {
			local ClassInfo is ncCls: self:findClass(name: targetName);
			local Boolean is hasNested: false;
			Conditional:if(check: { ncCls:name != '' }, then: {
				ncCls:members:each(action: local Function(Member is m){
					Conditional:if(check: { !hasNested && m:kind == MemberKind:CLASS && m:nestedClass:name == method }, then: {
						hasNested: true;
					});
				});
			});
			Conditional:if(check: { hasNested }, then: {
				local Array of String is segs: [targetName, method];
				expr:methodTarget: Expression:init(kind: ExpressionKind:PATH);
				expr:methodTarget:makePath(segments: segs);
				expr:methodName: 'init';
				targetType: self:inferExpressionType(expr: expr:methodTarget);
			});
		});

		# E5/E7: the call model. A class-name receiver admits
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
			local Boolean is isTypeLevel: self:allEnumNames:has(key: recvName) || self:isPrimitive(t: recvName) || recvName == 'Array' || recvName == 'Map' || recvName == 'List' || recvName == 'String' || recvName == 'Function' || recvName == 'LoopControl' || self:bindings:isClassModelEnum(c: self:findClass(name: recvName));
			# Desugared enums are type-level by design:
			# their contract methods dispatch through the class name.
			# Held functions: the class-name prefix IS
			# their dispatch — the call is type-level by design, inside
			# the class and out.
			Conditional:if(check: { self:findHeldMethod(className: recvName, methodName: expr:methodName):name != '' }, then: {
				isTypeLevel: true;
			});
			Conditional:if(check: { !isTypeLevel }, then: {
				Conditional:if(check: { !self:isAsImportedInherited(className: recvName) }, then: {
					Conditional:if(check: { recvName == self:currentClassName }, then: {
						self:addError(line: self:currentLine, msg: 'Cannot call members of \'' . recvName . '\' through the class name inside \'' . recvName . '\' itself; use self (§2.2).');
					}, else: {
						self:addError(line: self:currentLine, msg: 'Members of \'' . recvName . '\' are callable only through an instance; instance-import it (\'as ' . recvName . '()\') (§I.6).');
					});
				});
			});
		});
		Conditional:if(check: { recvName == '' && expr:methodName == 'init' }, then: {
			self:addError(line: self:currentLine, msg: '\'init\' is construct-only; call it on the class name (E7).');
		});

		# Conditional:match: the arm-table recognizer —
		# BEFORE the generic argument inference, which would type the
		# table's keys as ordinary expressions (the else key is not one).
		# Keys resolve against the subject's class's held members,
		# exhaustiveness keys on the Enum root, arm closures type here.
		# The bare form (self-receiver, the parser's bare-call shape)
		# is recognized here too — the recognizer returns before the
		# bare-scope branch runs, so the bareProvider stamp happens
		# HERE: the backend's match interceptor keys on it.
		Conditional:if(check: { method == 'match' && (expr:bareProvider == 'Conditional' || targetType == 'Conditional' || (expr:methodTarget:kind == ExpressionKind:IDENT && ((expr:methodTarget:str == 'match' && self:isAsImportedInherited(className: 'Conditional')) || (expr:methodTarget:str == self:names:selfIdent() && self:isAsImportedInherited(className: 'Conditional'))))) }, then: {
			Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:str == self:names:selfIdent() }, then: {
				expr:bareProvider: 'Conditional';
			});
			local Expression is matchSubj: Expression:init(kind: ExpressionKind:UNKNOWN);
			local Expression is matchArms: Expression:init(kind: ExpressionKind:UNKNOWN);
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:if(check: { arg:name == 'on' }, then: {
					matchSubj: arg:value;
				});
				Conditional:if(check: { arg:name == 'when' }, then: {
					matchArms: arg:value;
				});
			});
			Conditional:if(check: { matchArms:kind == ExpressionKind:MAP }, then: {
				Conditional:if(check: { matchSubj:kind != ExpressionKind:UNKNOWN }, then: {
					local String is matchRes: self:checkMatchArms(subj: matchSubj, arms: matchArms);
					expr:resolvedType: matchRes;
					return matchRes;
				}, else: {
					# The PREDICATE form: no subject — the keys are the
					# closures, the first that holds runs its arm.
					local String is predRes: self:checkPredicateArms(arms: matchArms);
					expr:resolvedType: predRes;
					return predRes;
				});
			});
			# A non-literal table — a Map built at runtime, arms held as
			# Function values — flows to the runtime dispatch: the
			# Conditional wrapper's match body serves it (string keys,
			# array keys, identity over the held singletons, else as the
			# fallback). The ordinary call machinery below checks the
			# argument types; payload arms are compile-time by design.
			# The PREDICATE form has no runtime path at all — a runtime
			# map can neither preserve scan order nor carry closure
			# keys — so a non-literal predicate table is a pointed
			# error instead of silent garbage.
			Conditional:if(check: { matchSubj:kind == ExpressionKind:UNKNOWN && matchArms:kind != ExpressionKind:UNKNOWN }, then: {
				self:addError(line: self:currentLine, msg: 'A predicate match table is compile-time: the keys are closures and the scan order matters — write the arm table as a literal.');
				expr:resolvedType: Primitive:ANY:value();
				return Primitive:ANY:value();
			});
		});

		# §2.3/E9: bare-scope resolution for self-receiver
		# calls. The providers are the enclosing class (own and inherited
		# members) plus its as-imported classes, one level deep. Exactly
		# one provider resolves; two or more collide and force
		# qualification; zero is an error — the old behavior silently
		# invented CurrentClass_method and died in gcc.
		Conditional:if(check: { recvName == '' && expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:str == self:names:selfIdent() && expr:methodName != 'init' && expr:methodName != 'typeName' && !self:shadowsAsFunction(name: expr:methodName) }, then: {
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
				self:addError(line: self:currentLine, msg: 'Function \'' . expr:methodName . '\' is provided by ' . listed . '; qualify the call (' . self:names:selfIdent() . ':' . expr:methodName . ' or the class name) (§2.3).');
				expr:resolvedType: '';
				return '';
			});
			Conditional:if(check: { providerTotal == 0 }, then: {
				self:addError(line: self:currentLine, msg: 'Undefined function \'' . expr:methodName . '\' on class \'' . self:currentClassName . '\' (E9).');
				expr:resolvedType: '';
				return '';
			});
				Conditional:if(check: { ownOwner == '' }, then: {
					local String is provider: bsProviders:get(index: 0);
					# The bare-scope branch runs before arg inference: type the
					# arguments now so overload selection sees exact types. Branch
					# closures (args 1+) of a Conditional call keep the enclosing
					# method's return type.
					local Boolean is bareIsBranch: provider == 'Conditional' && expr:argCount() >= 2 && expr:argCount() <= 4;
					# the bare form carries the value-yield
					# semantics exactly like the qualified call.
					local Boolean is bareIsValue: bareIsBranch && expr:argCount() == 3 && expected != '' && !self:isVoid(t: expected) && expr:argValue(index: 1):kind == ExpressionKind:ANON_FN && expr:argValue(index: 2):kind == ExpressionKind:ANON_FN;
					# the bare loop constructs — the vars
					# closure's parameters scope over the closure bodies, so
					# they bind BEFORE the inference and restore after. The
					# evaluate closure coerces to Boolean pre-inference, the
					# same order the qualified machinery runs.
					local Map of String to String is savedLoopVars;
					Conditional:if(check: { provider == 'Loops' }, then: {
						savedLoopVars: Map:init();
						local Array of String is lvKeys: self:localVars:keys();
						lvKeys:each(action: local Function(String is k){
							savedLoopVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
						});
						local Boolean is bareHasLoopVars: false;
						expr:methodArgs:each(action: local Function(NamedArg is arg){
							Conditional:if(check: { arg:value:kind == ExpressionKind:ARRAY && arg:value:anonParams:length() > 0 }, then: {
								bareHasLoopVars: true;
								arg:value:anonParams:each(action: local Function(Parameter is p){
									Conditional:if(check: { p:hasDefault }, then: {
										self:inferExpressionType(expr: p:defaultExpr);
									});
									self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
								});
							});
						});
						# the [vars] parameters scope the closures at
						# the call site — compile-time only. A closure held
						# as a variable was built before these parameters
						# existed and cannot capture them.
						local Int is barePos: 0;
						expr:methodArgs:each(action: local Function(NamedArg is arg){
							local Boolean is bareClosureSlot: arg:name == 'evaluate' || arg:name == 'iterate' || arg:name == 'iteration' || (arg:name == '' && barePos > 0);
							Conditional:if(check: { bareHasLoopVars && bareClosureSlot && arg:value:kind != ExpressionKind:ANON_FN }, then: {
								self:addError(line: self:currentLine, msg: 'The loop variables scope their closures at the call site: a [vars] loop form requires inline literal closures.');
							});
							barePos: barePos + 1;
						});
					});
					local Int is bareIdx: 0;
					Conditional:if(check: { provider == 'Loops' }, then: {
						# the loop closures are callbacks, not branch
						# yields — the enclosing branch's flag must not leak.
						local Boolean is savedLoopBranch: self:inBranchClosure;
						self:inBranchClosure: false;
						expr:methodArgs:each(action: local Function(NamedArg is arg){
							Conditional:if(check: { arg:name == 'evaluate' && arg:value:kind == ExpressionKind:ANON_FN }, then: {
								Conditional:if(check: { arg:value:anonReturnType:name == '' || arg:value:anonReturnType:name == self:names:voidName() }, then: {
									arg:value:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
								});
							});
							self:inferExpressionType(expr: arg:value);
						});
						self:inBranchClosure: savedLoopBranch;
					}, else: {
						# the branch closures type against the branch, not
						# the enclosing frame — the enclosing branch's flag
						# must not leak into the check closure (the same
						# entry reset the qualified branch call makes).
						self:inBranchClosure: false;
						expr:methodArgs:each(action: local Function(NamedArg is arg){
							Conditional:if(check: { bareIsBranch && bareIdx == 0 && arg:value:kind == ExpressionKind:ANON_FN }, then: {
								# the check closure coerces to Boolean
								# before its body check (the qualified
								# branch call's arg-0 rule).
								Conditional:if(check: { arg:value:anonReturnType:name == '' || arg:value:anonReturnType:name == self:names:voidName() }, then: {
									arg:value:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
								});
							});
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
					});
					self:selectOverload(className: provider, methodName: expr:methodName, expr: expr);
					# the as-import grants FUNCTIONS
					# ONLY under the callee's visibility — a `local` member of the
					# imported class is not callable through the import. The same
					# check the qualified path runs.
					local Member is bareSelected: self:lookupOverloadedMember(className: provider, methodName: expr:methodName, idx: expr:num);
					Conditional:if(check: { bareSelected:name != '' }, then: {
						self:checkMemberVisibility(ownerClass: provider, member: bareSelected, memberName: expr:methodName);
					});
					Conditional:if(check: { provider == 'Loops' }, then: {
						self:localVars: savedLoopVars;
						expr:bareProvider: provider;
						res: 'Void';
						expr:resolvedType: res;
						return res;
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
						self:addError(line: self:currentLine, msg: 'A value-yielding branch requires both branches to end in an expression.');
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
		# is this a Conditional branch call? Branch
		# closure bodies (arguments 1+) type-check against the enclosing
		# method's return type — they inline into it. The self-call
		# disjunct lets the wrapper's own self-calls pre-type their check
		# closures too.
		local Boolean is isBranchCall: expr:methodName == 'if' && expr:argCount() >= 2 && expr:argCount() <= 4 && (((targetType == 'Conditional' && expr:methodTarget:kind == ExpressionKind:IDENT) || (expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:str == self:names:selfIdent() && self:currentClassName == 'Conditional')) || expr:bareProvider == 'Conditional' || (expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:str == 'if' && self:isAsImportedInherited(className: 'Conditional')));
		# the value-yielding form — a 3-arg branch
		# call in a context that expects a value (a declaration, an
		# assignment, a return). Both branch closures must be inline
		# literals; their last expressions are the yields.
		local Boolean is isValueBranch: isBranchCall && expr:argCount() == 3 && expected != '' && !self:isVoid(t: expected) && expr:argValue(index: 1):kind == ExpressionKind:ANON_FN && expr:argValue(index: 2):kind == ExpressionKind:ANON_FN;
		# the value form is structural — BOTH branch
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
		# the Loops provider's closure forms share the
			# loop typing (while/loop/until inline closures; repeat counts).
			local Boolean is isWhileLoop: (targetType == 'Loops' || targetName == 'Loops') && (method == 'loop' || method == 'init' || method == 'while' || method == 'until' || method == 'repeat');
		local Map of String to String is savedWhileVars;
		local Boolean is hasLoopVars: false;
		Conditional:if(check: { isWhileLoop }, then: {
			savedWhileVars: Map:init();
			local Array of String is existingKeys: self:localVars:keys();
			existingKeys:each(action: local Function(String is k){
				savedWhileVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
			});
			local Int is posIdx: 0;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:if(check: { arg:value:kind == ExpressionKind:ARRAY && arg:value:anonParams:length() > 0 }, then: {
					hasLoopVars: true;
					arg:value:anonParams:each(action: local Function(Parameter is p){
						Conditional:if(check: { p:hasDefault }, then: {
							self:inferExpressionType(expr: p:defaultExpr);
						});
						self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
					});
				});
				# the [vars] parameters scope the closures at the
				# call site — compile-time only. A closure held as a
				# variable was built before these parameters existed and
				# cannot capture them: reject the combination instead of
				# running it with free identifiers.
				local Boolean is closureSlot: arg:name == 'evaluate' || arg:name == 'iterate' || arg:name == 'iteration' || arg:name == 'worker' || (arg:name == '' && ((hasLoopVars && (posIdx == 1 || posIdx == 2)) || (!hasLoopVars && (posIdx == 0 || posIdx == 1))));
				Conditional:if(check: { hasLoopVars && closureSlot && arg:value:kind != ExpressionKind:ANON_FN }, then: {
					self:addError(line: self:currentLine, msg: 'The loop variables scope their closures at the call site: a [vars] loop form requires inline literal closures.');
				});
				Conditional:if(check: { arg:name == 'evaluate' && arg:value:kind == ExpressionKind:ANON_FN }, then: {
					Conditional:if(check: { arg:value:anonReturnType:name == '' || arg:value:anonReturnType:name == self:names:voidName() }, then: {
						arg:value:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
					});
				}, else: {
					Conditional:if(check: { arg:name == '' && arg:value:kind == ExpressionKind:ANON_FN }, then: {
						Conditional:if(check: { (hasLoopVars && posIdx == 1) || (!hasLoopVars && posIdx == 0) }, then: {
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
		# the loop constructs' closures are callbacks,
		# not branch yields — when the call itself sits inside an
		# enclosing branch closure, that flag must not leak into them
		# (their returns type against the closure, not the method).
		Conditional:if(check: { isWhileLoop }, then: {
			local Boolean is savedLoopBranch: self:inBranchClosure;
			self:inBranchClosure: false;
			local Int is loopArgIdx: 0;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				Conditional:if(check: { (arg:name == 'evaluate' || (arg:name == '' && ((hasLoopVars && loopArgIdx == 1) || (!hasLoopVars && loopArgIdx == 0)))) && arg:value:kind == ExpressionKind:ANON_FN }, then: {
					Conditional:if(check: { arg:value:anonReturnType:name == '' || arg:value:anonReturnType:name == self:names:voidName() }, then: {
						arg:value:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
					});
				});
				self:inferExpressionType(expr: arg:value);
				loopArgIdx: loopArgIdx + 1;
			});
			self:inBranchClosure: savedLoopBranch;
		}, else: {
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
		});

		Conditional:if(check: { isWhileLoop }, then: {
			self:localVars: savedWhileVars;
			expr:resolvedType: 'Void';
			return 'Void';
		});

		Conditional:if(check: { targetType == self:names:selfIdent() || targetType == '' }, then: {
			targetType: self:currentClassName;
			# A held member body has no instance: implicit-self and self
			# calls are not available from it.
			Conditional:if(check: { self:inHeldInit || self:inHeldFunction }, then: {
				self:addError(line: self:currentLine, msg: 'A held member body has no instance: \'' . method . '\' cannot be called on \'self\' from it.');
			});
		});

		# Held functions: a bare class-name target
		# with a held member dispatches the class-scoped call — a
		# receiver-free C function, no vtable.
		local Member is heldCallFn: Member:init(kind: MemberKind:METHOD);
		local String is heldRoot: '';
		Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:IDENT || expr:methodTarget:kind == ExpressionKind:PATH }, then: {
			heldRoot: expr:methodTarget:str;
			Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:PATH && expr:methodTarget:pathSegments:length() > 0 }, then: {
				heldRoot: expr:methodTarget:pathSegments:get(index: 0);
			});
			Conditional:if(check: { heldRoot != '' && heldRoot != self:names:selfIdent() && !self:localVars:has(key: heldRoot) && !self:fieldTypes:has(key: heldRoot) && self:registeredClasses:has(key: heldRoot) }, then: {
				Conditional:if(check: { method != 'init' }, then: {
					heldCallFn: self:findHeldMethod(className: heldRoot, methodName: method);
				});
			});
		});
		Conditional:if(check: { heldCallFn:name != '' }, then: {
			self:checkMemberVisibility(ownerClass: self:findHeldMethodOwner(className: heldRoot, methodName: method), member: heldCallFn, memberName: method);
			local String is heldRet: self:resolveReturnType(t: heldCallFn:memberType);
			expr:resolvedType: heldRet;
			return heldRet;
		});
		# Strict held resolution: an instance
		# receiver never reaches a held function.
		Conditional:if(check: { targetType != '' && targetType != Primitive:ANY:value() && !self:allEnumNames:has(key: targetType) && heldCallFn:name == '' }, then: {
			local String is iBase: targetType:split(delimiter: ':'):get(index: 0);
			Conditional:if(check: { self:registeredClasses:has(key: iBase) && self:lookupMethodReturnType(className: iBase, methodName: method) == '' && self:findHeldMethod(className: iBase, methodName: method):name != '' }, then: {
				self:addError(line: self:currentLine, msg: 'Held function \'' . iBase . ':' . method . '\' is class-scoped: call it through the class name, not an instance.');
			});
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
				# The sysinternal discipline: the floor is reachable from
				# the base:sys wrappers — structurally: the caller's
				# namespace segment array begins ['base', 'sys', ...] (the
				# sub-packages included). Segment comparison is what
				# separates the wrapper package from the floor's own
				# base:sysinternal; a prefix test on the joined string
				# would conflate them.
				local Array of String is callerSegs: callerCls:namespaceSegments();
				local Boolean is sysWrapper: callerSegs:length() >= 2 && callerSegs:get(index: 0) == 'base' && callerSegs:get(index: 1) == 'sys';
				Conditional:if(check: { !sysWrapper }, then: {
					self:addError(line: self:currentLine, msg: 'The sysinternal floor is only accessible from base:sys wrappers; call the base:sys wrapper instead (call from \'' . callerCls:namespaceJoined() . '\').');
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
		Conditional:if(check: { expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:str == self:names:selfIdent() }, then: {
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
							# §I.2: init overloads are selected and stamped like any member.
							self:selectOverload(className: targetType, methodName: 'init', expr: expr);
							# §I.6: construction requires the import too — the
							# X3 stratum, the class itself, an ancestor, the same file, or the
							# class's own using grants it.
							Conditional:if(check: { !self:classHasAccess(className: self:currentClassName, targetName: targetType:split(delimiter: ':'):get(index: 0)) }, then: {
								self:addError(line: self:currentLine, msg: '\'' . targetType . '\' is not imported by \'' . self:currentClassName . '\'; add it to the using declaration to construct it (§I.6).');
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
								# a LOADED void declaration keeps
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
									Conditional:match(on: method, when: [
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
										'keys': { res: 'Array of String'; },
										'add': { res: 'void'; },
										'set': { res: 'void'; },
										'clear': { res: 'void'; },
										'each': { res: 'void'; },
										'push': { res: 'void'; },
										'remove': { res: Primitive:BOOLEAN:value(); },
										else: {}
									]);
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
											Conditional:match(on: method, when: [
												'name': { res: Primitive:STRING:value(); },
												'ordinal': { res: Primitive:INT:value(); },
												'values': { res: 'Array:' . targetType; },
												'of': { res: targetType; },
												'value': {
													res: Conditional:if(check: { self:allStringBackedEnums:has(key: targetType) }, then: { 'String' }, else: { Primitive:INT:value() });
												},
												else: { res: 'Any'; }
											]);
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
			# the value-yielding form — both branch
			# closures' established return types must unify. Read from the
			# nodes (the write-backs happened during the body check); never
			# re-infer.
			local Expression is thenAnon: expr:argValue(index: 1);
			local Expression is elseAnon: expr:argValue(index: 2);
			local String is thenT: thenAnon:anonReturnType:name;
			local String is elseT: elseAnon:anonReturnType:name;
			Conditional:if(check: { self:isVoid(t: thenT) || self:isVoid(t: elseT) }, then: {
				self:addError(line: self:currentLine, msg: 'A value-yielding branch requires both branches to end in an expression.');
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
		local Member is castM: Member:init(kind: MemberKind:FIELD);
		local Int is castIdx: 0;
		local String is castTargetName: MetadataField:CASTABLE:value();
		Loops({ castM:name == '' && castIdx < cls:members:length() }, {
			local Member is m: cls:members:get(index: castIdx);
			castIdx: castIdx + 1;
			if({ m:kind == MemberKind:FIELD && m:name == castTargetName }, {
				castM: m;
			});
		});
		Conditional:if(check: { castM:name == '' }, then: {
			return '';
		});
		Conditional:if(check: { !castM:hasInit || castM:initExpr:kind != ExpressionKind:ARRAY }, then: {
			return '';
		});
		local String is found: '';
		castM:initExpr:arrayItems:each(action: local Function(Expression is entry){
			Conditional:if(check: { found == '' && entry:kind == ExpressionKind:ARRAY && entry:arrayItems:length() == 2 }, then: {
				local Expression is tExpr: entry:arrayItems:get(index: 0);
				local Expression is fExpr: entry:arrayItems:get(index: 1);
				local String is entryTarget: tExpr:str;
				local String is entryFn: fExpr:str;
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

		Conditional:match(on: kind, when: [
			StatementKind:VAR_DECL: {
				local String is varName: stmt:varName;
				# the access gate resolves the bare nested
				# reference BEFORE the scope map stamps it — the checker and
				# the gen agree on the qualified identity.
				self:validateTypeAccess(t: stmt:varType, line: stmt:line);
				local String is fullType: self:formatVarTypeString(t: stmt:varType);
				self:localVars:set(key: varName, value: fullType);

				Conditional:if(check: { fullType == 'List' }, then: {
					local String is msg: 'Bare List type requires [T] element syntax.';
					self:addError(line: stmt:line, msg: msg);
				});

				Conditional:if(check: { stmt:hasInit }, then: {
					# Bidirectional: the declared type flows into the
					# initializer, typing container literals directly.
					local String is initType: self:inferExpressionType(expr: stmt:initExpr, expected: fullType);
					Conditional:if(check: { !self:isAssignable(target: fullType, source: initType) }, then: {
						local String is msg: 'Type mismatch in variable declaration for \'' . varName . '\': cannot assign \'' . initType . '\' to \'' . fullType . '\'.';
						# a void expression consumed as a
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
			},
			StatementKind:ASSIGN: {
				# Held members are read-only: a
				# class-name prefix target resolves to the shared held
				# slot, and assignment through it is rejected.
				# a resolution-hook name is a cached single copy too.
				Conditional:if(check: { stmt:assignTarget:kind == ExpressionKind:PATH && stmt:assignTarget:pathSegments:length() >= 2 }, then: {
					local Array of String is hSegs: stmt:assignTarget:pathSegments;
					local String is hRoot: hSegs:get(index: 0);
					local String is hName: hSegs:get(index: 1);
					local Boolean is hReadOnly: self:findHeldMember(className: hRoot, memberName: hName):name != '';
					local Boolean is hHooked: false;
					Conditional:if(check: { !hReadOnly && self:findHeldMethod(className: hRoot, methodName: ContractMethod:RESOLVE_HELD:value()):name != '' }, then: {
						hHooked: self:lookupFieldType(className: hRoot, fieldName: hName) == '' && self:lookupAnyMember(className: hRoot, methodName: hName):kind != MemberKind:METHOD && self:findHeldMethod(className: hRoot, methodName: hName):name == '';
					});
					Conditional:if(check: { hRoot != self:names:selfIdent() && !self:localVars:has(key: hRoot) && !self:fieldTypes:has(key: hRoot) && (hReadOnly || hHooked) }, then: {
						local String is hMsg: Conditional:if(check: { hReadOnly }, then: { 'Held member \'' . hRoot . ':' . hName . '\' is read-only: held members are class-scoped single copies, assigned once by their initializer.' }, else: { 'Resolved member \'' . hRoot . ':' . hName . '\' is read-only: resolution-hook values are cached single copies.' });
						self:addError(line: stmt:line, msg: hMsg);
					});
				});
				Conditional:if(check: { stmt:assignTarget:kind == ExpressionKind:PATH }, then: {
					local Array of String is tSegs: stmt:assignTarget:pathSegments;
					Conditional:if(check: { tSegs:length() == 2 && tSegs:get(index: 0) == self:names:selfIdent() }, then: {
						self:unassignedFields:remove(key: tSegs:get(index: 1));
					});
				}, else: {
					Conditional:if(check: { stmt:assignTarget:kind == ExpressionKind:IDENT }, then: {
						self:unassignedFields:remove(key: stmt:assignTarget:str);
					});
				});
				local String is targetType: self:inferExpressionType(expr: stmt:assignTarget);
				local String is valType: self:inferExpressionType(expr: stmt:assignValue, expected: targetType);
				Conditional:if(check: { !self:isAssignable(target: targetType, source: valType) }, then: {
						local String is msg: 'Type mismatch in assignment: cannot assign \'' . valType . '\' to \'' . targetType . '\'.';
						# the same for assignments.
						Conditional:if(check: { self:isVoid(t: valType) }, then: {
							local String is note: self:voidUseNote(expr: stmt:assignValue);
							Conditional:if(check: { note != '' }, then: {
								msg: 'cannot assign a void expression to \'' . targetType . '\': ' . note;
							});
						});
						self:addError(line: stmt:line, msg: msg);
					});
			},
			StatementKind:FORWARD: {
				self:checkForward(stmt: stmt);
			},
			StatementKind:RETURN: {
				Conditional:if(check: { stmt:hasReturnExpr }, then: {
					# Bidirectional: the declared return type flows in — and a
					# value-yielding branch's yield takes the branch's own
					# expected type (nested branch calls type in context).
					local String is yieldExpected: self:currentMethodReturnType;
					Conditional:if(check: { self:checkingValueYield && self:currentYieldExpected != '' }, then: {
						yieldExpected: self:currentYieldExpected;
					});
					local String is retType: self:inferExpressionType(expr: stmt:returnExpr, expected: yieldExpected);
					# the last statement of a
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
								local String is msg: 'Method declared return type \'' . self:currentMethodReturnType . '\', but returned \'' . retType . '\' (method ' . self:currentMethodName . ' of ' . self:currentClassName . ', stmt line ' . (stmt:line as String) . ', depth ' . (self:anonDepth as String) . ', inBranch ' . (self:inBranchClosure as String) . ', expr kind ' . (stmt:returnExpr:kind as String) . ', expr str \'' . stmt:returnExpr:str . '\').';
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
			},
			StatementKind:EXPR: {
				# Bound so the arm stays void: a trailing value-yielding
				# expression statement IS the arm's yield (the Kotlin
				# last-expression rule), and this arm is statement-form.
				local String is exprT: self:inferExpressionType(expr: stmt:exprStmt);
			},
			StatementKind:CLASS: {
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
			},
			else: {}
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
		local Int is i: 0;
		while(
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
		local Member is m: self:lookupOverloadedMember(className: targetT, methodName: expr:methodName, idx: expr:num);
		Conditional:if(check: { m:name == '' }, then: {
			return '';
		});
		local String is mRet: self:resolveReturnType(t: m:memberType);
		Conditional:if(check: { !self:isVoid(t: mRet) }, then: {
			return '';
		});
		local String is note: '\'' . targetT . '.' . expr:methodName . '\' declares no return value';
		# a partially-bound void call — the
		# unbound parameters' effects are absent. The arity gap is the
		# general signal (a 2-arg conditional's missing else is one case
		# of it, not a special one).
		Conditional:if(check: { expr:argCount() < m:params:length() }, then: {
			note: note . ' (' . (expr:argCount() as String) . ' of ' . (m:params:length() as String) . ' declared parameters bound)';
		});
		# a sibling overload binding MORE parameters
		# is the general signal that this call's effects are incomplete — a
		# 2-arg conditional's missing else is one case of it, not a special
		# one. Name the sibling's parameters so the user sees what to add.
		local Array of Member is group: [];
		local Array of String is groupOwners: [];
		self:collectOverloadGroup(className: targetT, methodName: expr:methodName, acc: group, ownerAcc: groupOwners);
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
			# IV.6 strictness: the declaration-side default is construction
			# the declaring class bakes in — it gates against the declaring
			# class's imports exactly like a body expression.
			Conditional:if(check: { p:hasDefault }, then: {
				self:inferExpressionType(expr: p:defaultExpr);
			});
		});
		self:validateTypeAccess(t: method:memberType, line: method:line);
		local Member is mergeTarget: self:findFirstSuperMethod(className: self:currentClassName, methodName: method:name);
		Conditional:if(check: { mergeTarget:name != '' && self:ancestorOverloaded(className: self:currentClassName, methodName: method:name) }, then: {
			self:addError(line: method:line, msg: 'Cannot replace or merge an overloaded method (\'' . method:name . '\' has multiple signatures); give each signature a distinct name (§I.3).');
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

	## Finds the nearest class (self, then ancestors) declaring a HELD
	## FIELD with the name. The class-name prefix
	## reaches exactly these members.
	##
	## @param className: Starting class whose bases are searched.
	## @param memberName: Member name to locate.
	## @return: The declaring class\'s name, or '' when absent.
	Function of String is findHeldOwnerClass(String is className, String is memberName){
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return '';
		});
		local ClassInfo is cls: self:findClass(name: className);
		Conditional:if(check: { cls:name == '' }, then: {
			return '';
		});
		local String is owner: '';
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { owner == '' && m:name == memberName && m:kind == MemberKind:FIELD && m:hasModifier(kw: Keyword:HELD) }, then: {
				owner: cls:name;
			});
		});
		Conditional:if(check: { owner != '' }, then: {
			return owner;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { owner == '' }, then: {
				owner: self:findHeldOwnerClass(className: baseName, memberName: memberName);
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
		local String is owner: self:findHeldOwnerClass(className: className, memberName: memberName);
		Conditional:if(check: { owner == '' }, then: {
			return Member:init(kind: MemberKind:FIELD);
		});
		local ClassInfo is cls: self:findClass(name: owner);
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { res:name == '' && m:name == memberName && m:kind == MemberKind:FIELD && m:hasModifier(kw: Keyword:HELD) }, then: {
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
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return Member:init(kind: MemberKind:METHOD);
		});
		local ClassInfo is cls: self:findClass(name: className);
		Conditional:if(check: { cls:name == '' }, then: {
			return Member:init(kind: MemberKind:METHOD);
		});
		local Member is res: Member:init(kind: MemberKind:METHOD);
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { res:name == '' && m:name == methodName && m:kind == MemberKind:METHOD && m:hasModifier(kw: Keyword:HELD) }, then: {
				res: m;
			});
		});
		Conditional:if(check: { res:name != '' }, then: {
			return res;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { res:name == '' }, then: {
				res: self:findHeldMethod(className: baseName, methodName: methodName);
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
		Conditional:if(check: { className == '' || className == Primitive:ANY:value() }, then: {
			return '';
		});
		local ClassInfo is cls: self:findClass(name: className);
		Conditional:if(check: { cls:name == '' }, then: {
			return '';
		});
		local String is owner: '';
		cls:members:each(action: local Function(Member is m){
			Conditional:if(check: { owner == '' && m:name == methodName && m:kind == MemberKind:METHOD && m:hasModifier(kw: Keyword:HELD) }, then: {
				owner: cls:name;
			});
		});
		Conditional:if(check: { owner != '' }, then: {
			return owner;
		});
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { owner == '' }, then: {
				owner: self:findHeldMethodOwner(className: baseName, methodName: methodName);
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
		local Member is m: self:findHeldMember(className: className, memberName: fieldName);
		Conditional:if(check: { m:name == '' || m:kind != MemberKind:FIELD }, then: {
			return '';
		});
		return self:formatTypeString(t: m:memberType);
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

	## Validates a class's held members: `held`
	## composes with the visibility modifiers but not with `replace`/
	## `merge` (held members are single-copy and cannot be overridden);
	## held fields require initializers (the lazy once-pattern constructs
	## them); held functions are not yet supported.
	##
	## @param classDef: Class to validate.
	Function is checkHeldMembers(ClassInfo is classDef){
		classDef:members:each(action: local Function(Member is m){
			Conditional:if(check: { !m:hasModifier(kw: Keyword:HELD) }, then: {
				# The resolution hook spelling is reserved: a plain method
				# named 'resolveHeld' would silently never hook
				# .
				Conditional:if(check: { m:kind == MemberKind:METHOD && m:name == ContractMethod:RESOLVE_HELD:value() }, then: {
					self:addError(line: m:line, msg: 'The resolution hook \'' . m:name . '\' in class \'' . classDef:name . '\' must be held: declare it \'held Function of Any is resolveHeld(String is name)\'.');
				});
				return;
			});
			Conditional:if(check: { m:hasModifier(kw: Keyword:REPLACE) || m:hasModifier(kw: Keyword:MERGE) }, then: {
				self:addError(line: m:line, msg: 'Member \'' . m:name . '\' in class \'' . classDef:name . '\' combines \'held\' with \'replace\'/\'merge\'; held members are single-copy and cannot be overridden.');
				return;
			});
			Conditional:if(check: { m:name == MetadataField:USING:value() || m:name == MetadataField:NAMESPACE:value() || m:name == MetadataField:CASTABLE:value() }, then: {
				self:addError(line: m:line, msg: 'Loader directive \'' . m:name . '\' in class \'' . classDef:name . '\' cannot be \'held\'.');
				return;
			});
			Conditional:if(check: { m:kind == MemberKind:CLASS }, then: {
				self:addError(line: m:line, msg: 'Nested class \'' . m:name . '\' in class \'' . classDef:name . '\' cannot be \'held\'.');
				return;
			});
			Conditional:if(check: { m:kind == MemberKind:METHOD }, then: {
				# Held functions: class-scoped, receiver-free. They are not
				# root-contract members (no vtable involvement) and do not
				# overload — one name, one signature, one symbol.
				Conditional:if(check: { m:name == ContractMethod:INIT:value() || m:name == ContractMethod:EVALUATE:value() || m:name == ContractMethod:ITERATION:value() || m:name == ContractMethod:TO_STRING:value() }, then: {
					self:addError(line: m:line, msg: 'Held function \'' . m:name . '\' in class \'' . classDef:name . '\' cannot be a root-contract member; held functions take no receiver and never dispatch dynamically.');
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
				Conditional:if(check: { m:name == ContractMethod:RESOLVE_HELD:value() }, then: {
					# The resolver's return: a method's memberType is the full
					# Function type with the return in params[0] (the direct
					# spelling 'HE is resolveHeld(...)' is also accepted).
					local String is resRetName: m:memberType:name;
					Conditional:if(check: { m:memberType:name == 'Function' && m:memberType:params:length() > 0 }, then: {
						local Type is resRetT: m:memberType:params:get(index: 0);
						resRetName: resRetT:name;
					});
					local Boolean is sigOk: false;
					Conditional:if(check: { m:params:length() == 2 }, then: {
						local Parameter is nameP: m:params:get(index: 0);
						local Parameter is missP: m:params:get(index: 1);
						local Type is missT: missP:paramType;
						local Type is missRet: missT:params:get(index: 0);
						Conditional:if(check: { nameP:paramType:name == Primitive:STRING:value() && missT:name == 'Function' && missT:params:length() > 0 }, then: {
							sigOk: missRet:name == resRetName && resRetName != '' && !self:isVoid(t: resRetName);
						});
					});
					Conditional:if(check: { !sigOk }, then: {
						self:addError(line: m:line, msg: 'The resolution hook \'' . m:name . '\' in class \'' . classDef:name . '\' must be declared exactly \'held Function of <T> is resolveHeld(String is name, Function of <T> is missing)\'; the missing branch is provided by the runtime and must return the same type the resolver searches for.');
					});
				});
				local Boolean is dupHeld: false;
				classDef:members:each(action: local Function(Member is g){
					Conditional:if(check: { g != m && g:kind == MemberKind:METHOD && g:name == m:name && g:hasModifier(kw: Keyword:HELD) }, then: {
						dupHeld: true;
					});
				});
				Conditional:if(check: { dupHeld }, then: {
					self:addError(line: m:line, msg: 'Held function \'' . m:name . '\' is declared more than once; held functions do not overload.');
				});
				return;
			});
			Conditional:if(check: { !m:hasInit }, then: {
				self:addError(line: m:line, msg: 'Held field \'' . m:name . '\' in class \'' . classDef:name . '\' requires an initializer; held members construct lazily, once, on first access.');
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
			# The outer-link relation is an ACCESS scope, not an is-a
			# contract: the enclosing class's members surface to the inner
			# through the walk, and the inner's own same-named members
			# SHADOW them silently — no abstract obligation, no replace
			# requirement, no signature merge (IV.2).
			Conditional:if(check: { parent:name == baseName && !(classDef:outerName != '' && (classDef:outerName == baseName || classDef:outerName:contains(needle: ':' . baseName))) }, then: {
				# 1. Enforce abstract member implementation on concrete classes
				# with init. The implicit root Any is exempt: its members carry
				# concrete defaults. (The outer-link relation is exempt by the
				# gate above — the inner-class link is an access scope.)
				Conditional:if(check: { hasInit && baseName != Primitive:ANY:value() }, then: {
					parent:members:each(action: local Function(Member is parentM){
						local Boolean is isAbstract: (parentM:kind == MemberKind:FIELD && !parentM:hasInit) ||
							(parentM:kind == MemberKind:METHOD && parentM:body:length() == 0);
						Conditional:if(check: { isAbstract }, then: {
							local Boolean is isImplemented: false;
							local Int is mIdx: 0;
							Loops({ !isImplemented && mIdx < classDef:members:length() }, {
								local Member is subM: classDef:members:get(index: mIdx);
								mIdx: mIdx + 1;
								Conditional:if(check: { subM:name == parentM:name }, then: {
									Conditional:if(check: { (subM:kind == MemberKind:METHOD && subM:body:length() > 0) || (subM:kind == MemberKind:FIELD && subM:hasInit) }, then: {
										isImplemented: true;
									});
								});
							});
							Conditional:if(check: { !isImplemented }, then: {
								local String is msg: 'ClassInfo \'' . classDef:name . '\' does not implement abstract member \'' . parentM:name . '\' required by parent \'' . baseName . '\'.';
								self:addError(line: classDef:line, msg: msg);
							});
						});
					});
				});

				# 2. Strict replace check & method signature matching on overrides
				classDef:members:each(action: local Function(Member is subM){
					# the nested-class members are declarations of
					# types, not overrides of the ancestor's surface.
					Conditional:if(check: { subM:kind == MemberKind:CLASS }, then: {
						return;
					});
					# Declarative metadata (namespace/using/group) is per-class
					# by design and never participates in override matching.
					Conditional:if(check: { subM:name == MetadataField:NAMESPACE:value() || subM:name == MetadataField:USING:value() || subM:name == MetadataField:CASTABLE:value() }, then: {
						return;
					});
					parent:members:each(action: local Function(Member is parentM){
						Conditional:if(check: { parentM:kind == MemberKind:CLASS }, then: {
							return;
						});
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
								# constructors are per-class —
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
		self:checkHeldMembers(classDef: classDef);
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
			# generated struct; HELD members are class-scoped
			#  — an instance reference reaches exactly the
			# instance members, so held names stay out of fieldTypes.
			Conditional:if(check: { m:kind == MemberKind:FIELD && m:memberType:name != '' && !m:hasModifier(kw: Keyword:HELD) }, then: {
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
			Conditional:match(on: m:kind, when: [
				MemberKind:FIELD: {
					self:currentLine: m:line;
					Conditional:if(check: { m:sourceFile != '' }, then: {
						self:currentSourceFile: m:sourceFile;
					});
					# Declarative metadata properties (using, namespace, group)
					# are loader directives, not checked code: their
					# initializers may reference classes the using itself
					# loads, so type validation is skipped. The as-import's
					# synthesized hidden field (_import_X, §10) is
					# the as-form's own materialization — its type reference
					# rides the as-form, not the plain type import.
					Conditional:if(check: { !m:name:startsWith(prefix: '_import_') }, then: {
						self:validateTypeAccess(t: m:memberType, line: m:line);
					});
					Conditional:if(check: { m:name != MetadataField:USING:value() && m:name != MetadataField:NAMESPACE:value() && m:name != MetadataField:CASTABLE:value() && !m:name:startsWith(prefix: '_import_') }, then: {
						local String is declaredType: self:formatVarTypeString(t: m:memberType);
						Conditional:if(check: { m:hasInit }, then: {
							# Bidirectional: the declared type flows in.
							# A HELD initializer has no instance scope
							# : the flag rejects self, instance fields,
							# and implicit-self calls inside it.
							local Boolean is savedHeldInit: self:inHeldInit;
							Conditional:if(check: { m:hasModifier(kw: Keyword:HELD) }, then: {
								self:inHeldInit: true;
							});
							local String is initType: self:inferExpressionType(expr: m:initExpr, expected: declaredType);
							self:inHeldInit: savedHeldInit;
							Conditional:if(check: { !self:isAssignable(target: declaredType, source: initType) }, then: {
								local String is msg: 'Type mismatch in field \'' . classDef:name . ':' . m:name . '\': cannot assign \'' . initType . '\' to \'' . declaredType . '\'.';
								self:addError(line: m:line, msg: msg);
							});
						});
					});
				},
				else: {}
			]);
		});

		classDef:members:each(action: local Function(Member is m){
			Conditional:match(on: m:kind, when: [
				MemberKind:METHOD: {
					self:unassignedFields: Map:init();
					Conditional:if(check: { m:name == ContractMethod:INIT:value() }, then: {
						classDef:members:each(action: local Function(Member is fm){
							Conditional:if(check: { fm:kind == MemberKind:FIELD && !fm:hasInit && fm:name != ContractMethod:USING:value() && !fm:hasModifier(kw: Keyword:HELD) }, then: {
								self:unassignedFields:set(key: fm:name, value: 'true');
							});
						});
					});
					# Held functions: no instance context
					# — fieldTypes cleared, so bare instance-field names do
					# not resolve; the no-instance checks reject self.
					local Boolean is savedHeldFn: self:inHeldFunction;
					local Map of String to String is savedFnFields: self:fieldTypes;
					Conditional:if(check: { m:hasModifier(kw: Keyword:HELD) }, then: {
						self:inHeldFunction: true;
						self:fieldTypes: Map:init();
					});
					self:checkMethod(method: m);
					self:inHeldFunction: savedHeldFn;
					self:fieldTypes: savedFnFields;
					self:unassignedFields: Map:init();
				},
				MemberKind:CLASS: {
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
		Conditional:match(on: stmt:kind, when: [
			StatementKind:CLASS: {
				self:collectClasses(c: stmt:nestedClass, acc: acc);
			}
		]);
	}

	## Collects a class and all nested definitions into the flat registry.
	##
	## @param c: The class to collect.
	## @param acc: Output array.
	Function is collectClasses(ClassInfo is c, Array of ClassInfo is acc){
		acc:add(item: c);
		c:members:each(action: local Function(Member is m){
			Conditional:match(on: m:kind, when: [
				MemberKind:CLASS: {
					self:collectClasses(c: m:nestedClass, acc: acc);
				},
				MemberKind:METHOD: {
					m:body:each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
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
				Conditional:if(check: { asExpr:str == '' }, then: {
					return;
				});
				local String is asName: asExpr:str;
				Conditional:if(check: { seen:has(key: asName) }, then: {
					self:addError(line: m:line, msg: 'Class \'' . classDef:name . '\' instance-imports \'' . asName . '\' more than once (E3).');
					return;
				});
				seen:set(key: asName, value: 'true');
				local ClassInfo is target: self:findClass(name: asName);
				Conditional:if(check: { target:name == '' }, then: {
					return;
				});
				Conditional:if(check: { target:baseClass == self:names:enumHeader() }, then: {
					self:addError(line: m:line, msg: 'Cannot instance-import enum \'' . asName . '\'; enums are type-level (E2).');
					return;
				});
					Conditional:if(check: { target:typeParams:length() > 0 }, then: {
						self:addError(line: m:line, msg: 'Generic classes cannot be instance-imported yet (§10).');
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
								out:add(item: seg:str);
							});
						});
					});
				});
			});
		});
		return out;
	}

	## Verifies the instance-import graph is a DAG (E4):
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
			self:addError(line: 0, msg: 'Instance import cycle: ' . path . c:name . ' (E4); construction would recurse forever.');
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
		# the same-named inner classes
		# under DIFFERENT enclosing classes are distinct by qualified
		# identity — the ambiguity moves to the reference (the provider
		# walk names the providers). The duplicate WITHIN one outer stays
		# the declaration error.
		local Map of String to String is innerSeen: Map:init();
		flattened:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { c:outerName != '' }, then: {
				Conditional:if(check: { innerSeen:has(key: c:qualifiedName()) }, then: {
					local String is msg: 'Inner class \'' . c:qualifiedName() . '\' is declared more than once in \'' . c:outerName . '\'; rename one.';
					self:addError(line: c:line, msg: msg);
				}, else: {
					innerSeen:set(key: c:qualifiedName(), value: c:outerName);
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
		local Array of String is builtinNames: ['Array', 'Map', 'List', 'String', 'Function', 'LoopControl', 'Output', 'Error', 'Math', 'Process', 'File', 'Input', 'Ansi', 'Parallel', 'Loops', 'Loop', 'LoopCallback', 'InputHandler'];
		builtinNames:each(action: local Function(String is bn){
			self:registeredClasses:set(key: bn, value: bn);
		});
		flattened:each(action: local Function(ClassInfo is c){
			self:registeredClasses:set(key: c:name, value: c:name);
			# the nested classes register under
			# their qualified identity too — 'Outer:Inner' resolves in the
			# constructor and static-call paths.
			Conditional:if(check: { c:outerName != '' }, then: {
				self:registeredClasses:set(key: c:qualifiedName(), value: c:qualifiedName());
			});
			Conditional:if(check: { c:baseClass == self:names:enumHeader() && !self:bindings:isClassModelEnum(c: c) }, then: {
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

		# E2/E3: validate as-form instance imports per class.
		flattened:each(action: local Function(ClassInfo is c){
			self:checkInstanceImports(classDef: c);
		});
		# E4: the instance-import graph must be a DAG.
		self:checkInstanceImportGraph();
		# §I.1: overload legality across all classes.
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

	## Releases semantic maps, scopes, and caches after type checking completes.
	Function is cleanup(){
		self:registeredClasses: Map:init();
		self:nestedScopeMap: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();
		self:programClasses: [];
		self:localVars: Map:init();
		self:fieldTypes: Map:init();
		self:unassignedFields: Map:init();
		self:errors: [];
	}
}
