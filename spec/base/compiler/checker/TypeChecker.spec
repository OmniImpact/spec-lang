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
		['base', 'io', as Output()]
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

	## Class currently being analyzed.
	local String is currentClassName: '';

	## Source file of the class currently being analyzed.
	local String is currentSourceFile: '';

	## Return type name of the method currently being checked.
	local String is currentMethodReturnType: '';

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
		local String is fullMsg: if (self:currentSourceFile != '') '[' . self:currentSourceFile . '] ' . msg else msg;
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
		if (Primitive:of(t:name) == Primitive:FUNCTION) {
			if (t:params:length() > 0) {
				local Type is ret: t:params:get(index: 0);
				return 'Function:' . self:formatTypeString(t: ret);
			}
			return 'Function';
		}
		return self:formatTypeString(t: t);
	}

	## Formats a [Type] descriptor into the internal colon form
	## (Array:X, Map:K:V); Function formats to its return type.
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

	## Substitutes a class's generic type parameters in a member type name.
	##
	## @param rawType: Declared type name (may reference type params).
	## @param cls: The declaring class.
	## @param typeArgs: The concrete type arguments.
	## @return: The substituted type name.
	Function of String is substituteTypeParam(String is rawType, ClassInfo is cls, Array of String is typeArgs){
		local Array of String is tps: cls:typeParams;
		if (tps:length() == 0 || typeArgs:length() == 0) {
			return rawType;
		}
		local Int is idx: tps:indexOf(search: rawType, default: -1);
		if (idx >= 0) {
			# Grounded when the container carries type arguments; a bare
			# container ('Array' without 'of T') degrades to Any.
			if (idx < typeArgs:length()) {
				return typeArgs:get(index: idx);
			}
			return Primitive:ANY:value();
		}
		if (rawType:startsWith(prefix: 'Array:') && rawType:length() > 6) {
			local String is elem: rawType:substring(start: 6, end: rawType:length());
			local Int is eIdx: tps:indexOf(search: elem, default: -1);
			if (eIdx >= 0 && eIdx < typeArgs:length()) {
				return 'Array:' . typeArgs:get(index: eIdx);
			}
		}
		if (rawType:startsWith(prefix: 'List:') && rawType:length() > 5) {
			local String is elem: rawType:substring(start: 5, end: rawType:length());
			local Int is eIdx: tps:indexOf(search: elem, default: -1);
			if (eIdx >= 0 && eIdx < typeArgs:length()) {
				return 'List:' . typeArgs:get(index: eIdx);
			}
		}
		return rawType;
	}

	## Finds a class descriptor by name.
	##
	## @param name: Target class name.
	## @return: The descriptor, or an unnamed one when absent.
	Function of ClassInfo is findClass(String is name){
		local ClassSearchLoop is s: ClassSearchLoop:init(list: self:programClasses, target: name);
		While:run(loop: s);
		if (s:found) {
			return s:res;
		}
		return ClassInfo:init(name: '', baseClass: '', members: []);
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

	## Determines whether a source type is assignable to a target type.
	##
	## @param target: Target type name.
	## @param source: Source type name.
	## @return: true when compatible.
	Function of Boolean is isAssignable(String is target, String is source){
		if (target == source || target == Primitive:ANY:value() || source == Primitive:ANY:value() || target == '' || source == '') {
			return true;
		}
		# Implicit numeric widening: Int assigns to Float (explicit casts
		# handle the narrowing directions).
		if (target == 'Float' && source == Primitive:INT:value()) {
			return true;
		}
		# Function types are mutually compatible across signatures
		# (higher-order parameters accept any callable of the shape).
		if (target:startsWith(prefix: 'Function') && source:startsWith(prefix: 'Function')) {
			return true;
		}
		local ClassInfo is curCls: self:findClass(name: self:currentClassName);
		if (curCls:typeParams:indexOf(search: target, default: -1) >= 0 || curCls:typeParams:indexOf(search: source, default: -1) >= 0) {
			return true;
		}
		# Of-form containers ('Array of String'): normalize to the colon
		# form so the type-argument comparison below sees the args. Map's
		# two args join with ' to ' — split them back out.
		local String is tNorm: target;
		local String is sNorm: source;
		local Int is tOf: target:indexOf(search: ' of ', default: -1);
		local Int is sOf: source:indexOf(search: ' of ', default: -1);
		if (tOf > 0) {
			tNorm: target:substring(start: 0, end: tOf) . ':' . target:substring(start: tOf + 4, end: target:length());
		}
		if (sOf > 0) {
			sNorm: source:substring(start: 0, end: sOf) . ':' . source:substring(start: sOf + 4, end: source:length());
		}
		local Int is tTo: tNorm:indexOf(search: ' to ', default: -1);
		local Int is sTo: sNorm:indexOf(search: ' to ', default: -1);
		if (tTo > 0) {
			tNorm: tNorm:substring(start: 0, end: tTo) . ':' . tNorm:substring(start: tTo + 4, end: tNorm:length());
		}
		if (sTo > 0) {
			sNorm: sNorm:substring(start: 0, end: sTo) . ':' . sNorm:substring(start: sTo + 4, end: sNorm:length());
		}
		local Array of String is tParts: tNorm:split(delimiter: ':');
		local Array of String is sParts: sNorm:split(delimiter: ':');
		if (tParts:length() > 0 && sParts:length() > 0) {
			local String is tBase: tParts:get(index: 0);
			local String is sBase: sParts:get(index: 0);
			if (tBase == sBase || self:isSubclassOf(subName: sBase, baseName: tBase)) {
				if (tParts:length() > 1 && sParts:length() > 1) {
					local Boolean is argsOk: true;
					local Int is pIdx: 1;
					While:condition(
						evaluate: local Function of Boolean(){
							return pIdx < tParts:length() && pIdx < sParts:length();
						},
						iteration: local Function of Boolean(){
							local String is tp: tParts:get(index: pIdx);
							local String is sp: sParts:get(index: pIdx);
							if (!self:isAssignable(target: tp, source: sp)) {
								argsOk: false;
							}
							pIdx: pIdx + 1;
							return true;
						}
					);
					return argsOk;
				}
				return true;
			}
		}
		if (self:isSubclassOf(subName: source, baseName: target)) {
			return true;
		}
		return false;
	}

	## Looks up a member of any kind by name on a class or its bases.
	##
	## @param className: Class whose members are searched.
	## @param methodName: Member name to locate.
	## @return: The member, or an empty-named one when absent.
	Function of Member is lookupAnyMember(String is className, String is methodName){
		if (className == '' || className == Primitive:ANY:value()) {
			return Member:init(kind: MemberKind:FIELD);
		}
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:name == '') {
			return Member:init(kind: MemberKind:FIELD);
		}
		local MethodSearchLoop is ml: MethodSearchLoop:init(members: cls:members, methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			return ml:res;
		}
		local Member is inherited: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			if (inherited:name == '') {
				inherited: self:lookupAnyMember(className: baseName, methodName: methodName);
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
		local FieldSearchLoop is fl: FieldSearchLoop:init(members: cls:members, fieldName: variantName);
		While:run(loop: fl);
		if (fl:found) {
			return fl:res;
		}
		return Member:init(kind: MemberKind:FIELD);
	}

	## Looks up a field's static type on a class and its ancestors.
	##
	## @param className: Starting class name.
	## @param fieldName: Field name.
	## @return: The field type name, or '' when absent.
	Function of String is lookupFieldType(String is className, String is fieldName){
		if (className == '' || className == Primitive:ANY:value()) {
			return '';
		}
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
		# Of-form generic receivers ('Box of Int'): split the base and the
		# type argument so substitution can ground T.
		local Int is ofIdx: className:indexOf(search: ' of ', default: -1);
		if (ofIdx > 0 && typeArgs:length() == 0) {
			baseClassName: className:substring(start: 0, end: ofIdx);
			typeArgs:add(item: className:substring(start: ofIdx + 4, end: className:length()));
		}
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:name == '') {
			return '';
		}
		local FieldSearchLoop is fl: FieldSearchLoop:init(members: cls:members, fieldName: fieldName);
		While:run(loop: fl);
		if (fl:found) {
			local Member is foundM: fl:res;
			local String is rawT: self:formatTypeString(t: foundM:memberType);
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
	## @return: The return type name, or '' when absent.
	Function of String is lookupMethodReturnType(String is className, String is methodName){
		if (className == '' || className == Primitive:ANY:value()) {
			return '';
		}
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
		# Of-form generic receivers ('Box of Int'): split the base and the
		# type argument so substitution can ground T.
		local Int is ofIdx: className:indexOf(search: ' of ', default: -1);
		if (ofIdx > 0 && typeArgs:length() == 0) {
			baseClassName: className:substring(start: 0, end: ofIdx);
			typeArgs:add(item: className:substring(start: ofIdx + 4, end: className:length()));
		}
		if (methodName == ContractMethod:INIT:value() && self:registeredClasses:has(key: baseClassName) && !self:allEnumNames:has(key: baseClassName)) {
			return className;
		}
		local ClassInfo is cls: self:findClass(name: baseClassName);
		if (cls:name == '') {
			return '';
		}
		local MethodSearchLoop is ml: MethodSearchLoop:init(members: cls:members, methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			local Member is foundM: ml:res;
			local String is rawT: self:formatTypeString(t: foundM:memberType);
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

	## Validates call-site argument types against the resolved signature.
	##
	## Named arguments match by parameter name; unmatched named arguments
	## fall back to positional matching. Any-typed parameters and arguments
	## are skipped; builtin stub signatures are exempt.
	##
	## @param callExpr: The CALL expression.
	Function is checkCallArguments(Expression is callExpr){
		local String is targetType: callExpr:methodTarget:resolvedType;
		if (targetType == self:names:selfIdent() || targetType == '') {
			targetType: self:currentClassName;
		}
		if (targetType == '' || targetType == Primitive:ANY:value() || self:allEnumNames:has(key: targetType)) {
			return;
		}
		local Array of String is parts: targetType:split(delimiter: ':');
		local String is baseClassName: parts:get(index: 0);
		if (baseClassName == '' || baseClassName == Primitive:ANY:value() || baseClassName == 'While') {
			return;
		}
		local Member is m: self:lookupOverloadedMember(className: baseClassName, methodName: callExpr:methodName, idx: callExpr:overloadIndex);
		if (m:kind != MemberKind:METHOD) {
			return;
		}
		local Array of Parameter is params: m:params;
		if (params:length() == 0) {
			return;
		}
		local ClassInfo is recvCls: self:findClass(name: baseClassName);
		local Array of String is recvTypeParams: recvCls:typeParams;
		local Int is pIdx: 0;
		params:each(action: local Function(Parameter is p){
			local String is pName: p:name;
			local String is pT: p:paramType:name;
			if (pT != self:names:selfFieldMarker() && pT != Primitive:ANY:value() && pT != '' && recvTypeParams:indexOf(search: pT, default: -1) < 0) {
				local Expression is matchedValue: Expression:init(kind: ExpressionKind:UNKNOWN);
				local Boolean is found: false;
				local Int is posIdx: 0;
				callExpr:methodArgs:each(action: local Function(NamedArg is a){
					if (!found && pName != '' && a:name == pName) {
						matchedValue: a:value;
						found: true;
					}
				});
				if (!found) {
					callExpr:methodArgs:each(action: local Function(NamedArg is a){
						if (!found && a:name == '' && posIdx == pIdx) {
							matchedValue: a:value;
							found: true;
						}
						posIdx: posIdx + 1;
					});
				}
				if (found) {
					local String is argT: matchedValue:resolvedType;
					if (argT != '' && argT != Primitive:ANY:value() && !self:isAssignable(target: pT, source: argT)) {
						local String is label: if (pName != '') pName else 'position ' . (pIdx + 1);
						local String is msg: 'Argument \'' . label . '\' for \'' . baseClassName . '.' . callExpr:methodName . '\': cannot assign \'' . argT . '\' to \'' . pT . '\'.';
						self:addError(line: self:currentLine, msg: msg);
					}
				} else if (!p:hasDefault && !self:isBindingDeclaration(cls: recvCls)) {
					# Binding declarations (sysinternal + runtime-managed)
					# sketch API surface, not call contracts — their C
					# implementations carry optional/variadic semantics.
					local String is msg: 'Missing argument \'' . pName . '\' for \'' . baseClassName . '.' . callExpr:methodName . '\'.';
					self:addError(line: self:currentLine, msg: msg);
				}
			}
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
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseName: parts:get(index: 0);
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		self:collectOverloadGroup(className: baseName, methodName: methodName, hops: 0, acc: group, ownerAcc: ownerAcc);
		if (group:length() == 0) {
			return none;
		}
		local Array of NamedArg is args: expr:methodArgs;
		local Boolean is allPos: true;
		local Boolean is allNamed: true;
		args:each(action: local Function(NamedArg is a){
			if (a:name == '') {
				allNamed: false;
			} else {
				allPos: false;
			}
		});
		# FUNCTIONS.md §I.3: no mixed calls — enforced globally, including
		# single-member names. The one sanctioned shape: the scoped-region
		# desugaring's trailing callback (named arguments, then exactly one
		# positional block last).
		local Boolean is isDesugaredShape: false;
		if (!allPos && !allNamed) {
			local Int is posCount: 0;
			local Int is lastIdx: args:length() - 1;
			args:each(action: local Function(NamedArg is a){
				if (a:name == '') {
					posCount: posCount + 1;
				}
			});
			local NamedArg is lastArg: args:get(index: lastIdx);
			if (posCount == 1 && lastArg:name == '') {
				isDesugaredShape: true;
			}
		}
		if (!allPos && !allNamed && !isDesugaredShape) {
			self:addError(line: self:currentLine, msg: 'Mixed positional and named arguments are not supported; use one form (FUNCTIONS.md §I.3).');
			return none;
		}
		if (group:length() == 1) {
			local Member is only: group:get(index: 0);
			expr:overloadIndex: 0;
			return only;
		}
		if (allNamed) {
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
							if (argA:name == argB:name) {
								dupArg: true;
							}
							aj: aj + 1;
							return true;
						}
					);
					ai: ai + 1;
					return true;
				}
			);
			if (dupArg) {
				self:addError(line: self:currentLine, msg: 'Duplicate named argument in call to \'' . baseName . '.' . methodName . '\'.');
				return none;
			}
		}
		local Array of Member is survivors: [];
		group:each(action: local Function(Member is m){
			if (m:params:length() != args:length()) {
				return;
			}
			if (allPos) {
				survivors:add(item: m);
				return;
			}
			local Boolean is namesMatch: true;
			m:params:each(action: local Function(Parameter is p){
				local Boolean is present: false;
				args:each(action: local Function(NamedArg is a){
					if (a:name == p:name) {
						present: true;
					}
				});
				if (!present) {
					namesMatch: false;
				}
			});
			if (namesMatch) {
				survivors:add(item: m);
				return;
			}
			if (isDesugaredShape) {
				# The trailing positional block binds to the last parameter;
				# every named argument must name a real parameter.
				local Boolean is namedOk: true;
				args:each(action: local Function(NamedArg is a){
					if (a:name == '') {
						return;
					}
					local Boolean is hit: false;
					m:params:each(action: local Function(Parameter is p){
						if (p:name == a:name) {
							hit: true;
						}
					});
					if (!hit) {
						namedOk: false;
					}
				});
				if (namedOk) {
					survivors:add(item: m);
				}
			}
		});
		if (survivors:length() == 0) {
			if (allPos) {
				self:addError(line: self:currentLine, msg: 'No signature of \'' . baseName . '.' . methodName . '\' takes ' . (args:length() as String) . ' argument(s).');
			} else {
				self:addError(line: self:currentLine, msg: 'No signature of \'' . baseName . '.' . methodName . '\' matches the named arguments.');
			}
			return none;
		}
		if (survivors:length() == 1) {
			local Member is sel: survivors:get(index: 0);
			expr:overloadIndex: self:indexOfMember(group: group, m: sel);
			return sel;
		}
		local Array of Member is exact: [];
		survivors:each(action: local Function(Member is m){
			if (self:exactTypeMatch(m: m, expr: expr)) {
				exact:add(item: m);
			}
		});
		if (exact:length() == 1) {
			local Member is sel: exact:get(index: 0);
			expr:overloadIndex: self:indexOfMember(group: group, m: sel);
			return sel;
		}
		if (exact:length() > 1) {
			self:addError(line: self:currentLine, msg: 'Ambiguous call to \'' . baseName . '.' . methodName . '\': the arguments match multiple overloads; use named arguments (FUNCTIONS.md §I.2).');
			return none;
		}
		local String is argTypes: '';
		args:each(action: local Function(NamedArg is a){
			local String is at: a:value:resolvedType;
			if (at == '') {
				at: 'Any';
			}
			if (argTypes == '') {
				argTypes: at;
			} else {
				argTypes: argTypes . ', ' . at;
			}
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
		if (ownerAcc:length() > 0 || acc:length() > 0 || className == '' || className == 'Any' || hops >= 8) {
			return;
		}
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		if (cls:name == '') {
			return;
		}
		cls:members:each(action: local Function(Member is m){
			if (m:kind == MemberKind:METHOD && m:name == methodName) {
				acc:add(item: m);
			}
		});
		if (acc:length() > 0) {
			ownerAcc:add(item: cls:name);
			return;
		}
		cls:baseClasses:each(action: local Function(String is baseName){
			self:collectOverloadGroup(className: baseName, methodName: methodName, hops: hops + 1, acc: acc, ownerAcc: ownerAcc);
		});
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
			if (p:name != '') {
				expr:methodArgs:each(action: local Function(NamedArg is a){
					if (!found && a:name == p:name) {
						bound: a:value;
						found: true;
					}
				});
			}
			if (!found && posIdx < expr:methodArgs:length()) {
				local NamedArg is pa: expr:methodArgs:get(index: posIdx);
				if (pa:name == '') {
					bound: pa:value;
					found: true;
				}
			}
			if (!found || bound:resolvedType == '' || bound:resolvedType != p:paramType:name) {
				allMatch: false;
			}
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
			if (g == m) {
				hit: idx;
			}
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
		local Array of String is parts: className:split(delimiter: ':');
		local String is baseName: parts:get(index: 0);
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		self:collectOverloadGroup(className: baseName, methodName: selected:name, hops: 0, acc: group, ownerAcc: ownerAcc);
		if (group:length() <= 1 || ownerAcc:length() == 0) {
			return self:lookupMethodReturnType(className: className, methodName: selected:name);
		}
		local String is owner: ownerAcc:get(index: 0);
		local ClassInfo is ownerCls: self:findClass(name: owner);
		if (ownerCls:name == '') {
			return '';
		}
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
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
		local Array of String is parts: className:split(delimiter: ':');
		local Array of Member is group: [];
		local Array of String is ownerAcc: [];
		self:collectOverloadGroup(className: parts:get(index: 0), methodName: methodName, hops: 0, acc: group, ownerAcc: ownerAcc);
		if (group:length() == 0) {
			return none;
		}
		local Int is use: idx;
		if (use < 0) {
			use: 0;
		}
		if (use >= group:length()) {
			use: group:length() - 1;
		}
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
		if (clsName == '' || clsName == 'Any' || hops >= 8) {
			return false;
		}
		local ClassInfo is cls: self:findClass(name: clsName);
		if (cls:name == '') {
			return false;
		}
		if (cls:instanceImportsAs(name: targetName)) {
			return true;
		}
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if (!viaParent && self:importsAsAnywhere(clsName: baseName, targetName: targetName, hops: hops + 1)) {
				viaParent: true;
			}
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
		if (clsName == '' || clsName == 'Any' || hops >= 8) {
			return;
		}
		local ClassInfo is cls: self:findClass(name: clsName);
		if (cls:name == '') {
			return;
		}
		cls:members:each(action: local Function(Member is m){
			if (m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) {
				m:initExpr:arrayItems:each(action: local Function(Expression is item){
					if (item:kind == ExpressionKind:ARRAY) {
						item:arrayItems:each(action: local Function(Expression is seg){
							if (seg:kind == ExpressionKind:USING_AS) {
								local String is prov: seg:stringValue;
								local Boolean is already: false;
								acc:each(action: local Function(String is got){
									if (got == prov) {
										already: true;
									}
								});
								if (!already && self:findMemberOwnerClass(className: prov, memberName: methodName) != '') {
									acc:add(item: prov);
								}
							}
						});
					}
				});
			}
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
		if (className == '' || className == 'Any' || hops >= 8) {
			return false;
		}
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		if (cls:name == '') {
			return false;
		}
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if (!viaParent && self:declaresOrInherits(className: baseName, methodName: methodName, hops: hops + 1)) {
				viaParent: true;
			}
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
		if (className == '' || className == 'Any' || hops >= 8) {
			return false;
		}
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		if (cls:name == '') {
			return false;
		}
		local Boolean is found: false;
		cls:members:each(action: local Function(Member is m){
			if (m:kind == MemberKind:METHOD && m:name == methodName) {
				found: true;
			}
		});
		if (found) {
			return true;
		}
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if (!viaParent && self:declaresOrInherits(className: baseName, methodName: methodName, hops: hops + 1)) {
				viaParent: true;
			}
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
		if (className == '' || className == 'Any' || hops >= 8) {
			return false;
		}
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		if (cls:name == '') {
			return false;
		}
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if (!viaParent && self:nearestGroupOverloaded(className: baseName, methodName: methodName, hops: hops + 1)) {
				viaParent: true;
			}
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
		if (className == '' || className == 'Any' || hops >= 8) {
			return false;
		}
		local Array of String is parts: className:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: parts:get(index: 0));
		if (cls:name == '') {
			return false;
		}
		local Int is groupSize: 0;
		cls:members:each(action: local Function(Member is m){
			if (m:kind == MemberKind:METHOD && m:name == methodName) {
				groupSize: groupSize + 1;
			}
		});
		if (groupSize >= 2) {
			return true;
		}
		if (groupSize == 1) {
			return false;
		}
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if (!viaParent && self:nearestGroupOverloaded(className: baseName, methodName: methodName, hops: hops + 1)) {
				viaParent: true;
			}
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
					if (m:kind == MemberKind:METHOD) {
						local Boolean is earlier: false;
						local Int is j: 0;
						While:condition(
							evaluate: local Function of Boolean(){ return !earlier && j < i; },
							iteration: local Function of Boolean(){
								local Member is g: members:get(index: j);
								if (g:kind == MemberKind:METHOD && g:name == m:name) {
									earlier: true;
								}
								j: j + 1;
								return true;
							}
						);
						if (!earlier) {
							local Int is groupSize: 0;
							local Int is k: 0;
							While:condition(
								evaluate: local Function of Boolean(){ return k < members:length(); },
								iteration: local Function of Boolean(){
									local Member is g: members:get(index: k);
									if (g:kind == MemberKind:METHOD && g:name == m:name) {
										groupSize: groupSize + 1;
									}
									k: k + 1;
									return true;
								}
							);
							if (groupSize >= 2) {
								local Int is a: 0;
								While:condition(
									evaluate: local Function of Boolean(){ return a < members:length(); },
									iteration: local Function of Boolean(){
										local Member is ma: members:get(index: a);
										if (ma:kind == MemberKind:METHOD && ma:name == m:name) {
											local Int is b: a + 1;
											While:condition(
												evaluate: local Function of Boolean(){ return b < members:length(); },
												iteration: local Function of Boolean(){
													local Member is mb: members:get(index: b);
													if (mb:kind == MemberKind:METHOD && mb:name == m:name && self:checkerSameSignature(a: ma, b: mb)) {
														self:addError(line: m:line, msg: 'Methods \'' . m:name . '\' in class \'' . c:name . '\' declare identical signatures; overloads must differ (FUNCTIONS.md §I.1).');
													}
													b: b + 1;
													return true;
												}
											);
										}
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
										if (g:kind == MemberKind:METHOD && g:name == m:name) {
											g:params:each(action: local Function(Parameter is pp){
												local String is pt: pp:paramType:name;
												if (pt == '' || pt == Primitive:ANY:value() || pt == self:names:selfFieldMarker() || c:typeParams:indexOf(search: pt, default: -1) >= 0) {
													nonConcrete: true;
												}
											});
										}
										p: p + 1;
										return true;
									}
								);
								if (nonConcrete) {
									self:addError(line: m:line, msg: 'Overloaded method \'' . m:name . '\' must declare concrete parameter types (FUNCTIONS.md §I.3).');
								}
								if (m:name != 'init' && self:ancestorDeclares(className: c:name, methodName: m:name, hops: 0)) {
									self:addError(line: m:line, msg: 'Cannot overload \'' . m:name . '\': the name is declared on an ancestor (FUNCTIONS.md §I.3).');
								}
							}
						}
					}
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
		if (a:params:length() != b:params:length()) {
			return false;
		}
		local Boolean is same: true;
		local Int is idx: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return same && idx < a:params:length(); },
			iteration: local Function of Boolean(){
				local Parameter is pa: a:params:get(index: idx);
				local Parameter is pb: b:params:get(index: idx);
				if (pa:name != pb:name || self:formatTypeString(t: pa:paramType) != self:formatTypeString(t: pb:paramType)) {
					same: false;
				}
				idx: idx + 1;
				return true;
			}
		);
		return same;
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
		if (subjectType == '' || !self:allEnumNames:has(key: subjectType)) {
			return;
		}
		local Map of String to String is covered: Map:init();
		local Boolean is hasElse: false;
		arms:each(action: local Function(WhenArm is arm){
			if (arm:isElse) {
				hasElse: true;
			}
			arm:conditions:each(action: local Function(Expression is c){
				local String is variantName: '';
				if (c:kind == ExpressionKind:CALL && self:allEnumVariants:has(key: c:methodName) && self:allEnumVariants:getString(key: c:methodName, default: '') == subjectType) {
					variantName: c:methodName;
				} else if (c:kind == ExpressionKind:IDENT && self:allEnumVariants:has(key: c:stringValue) && self:allEnumVariants:getString(key: c:stringValue, default: '') == subjectType) {
					variantName: c:stringValue;
				} else if (c:kind == ExpressionKind:PATH && c:pathSegments:length() >= 2 && c:pathSegments:get(index: 0) == subjectType && self:allEnumVariants:has(key: c:pathSegments:get(index: 1))) {
					variantName: c:pathSegments:get(index: 1);
				}
				if (variantName != '') {
					covered:set(key: variantName, value: 'true');
				}
			});
		});
		if (hasElse) {
			return;
		}
		local ClassInfo is enumCls: self:findClass(name: subjectType);
		local Array of String is missing: [];
		enumCls:members:each(action: local Function(Member is m){
			if (!covered:has(key: m:name)) {
				missing:add(item: m:name);
			}
		});
		if (missing:length() > 0) {
			local String is msg: 'Non-exhaustive \'when\': enum \'' . subjectType . '\' variant(s) not covered (e.g. \'' . missing:get(index: 0) . '\'). Add matching arm(s) or an \'else:\' fallback.';
			self:addError(line: line, msg: msg);
		}
	}

	## Binds payload-carrying variant conditions (is Value:Num(n)) into the
	## local scope, typing each bound identifier from the variant's declared
	## parameters.
	##
	## @param arm: The when arm.
	Function is bindWhenPatternVars(WhenArm is arm){
		arm:conditions:each(action: local Function(Expression is c){
			if (c:kind == ExpressionKind:CALL && self:allEnumVariants:has(key: c:methodName)) {
				local String is enumName: self:allEnumVariants:getString(key: c:methodName, default: '');
				local Member is vMem: self:lookupEnumVariant(enumName: enumName, variantName: c:methodName);
				local Int is idx: 0;
				c:methodArgs:each(action: local Function(NamedArg is arg){
					if (idx < vMem:params:length()) {
						local Expression is av: arg:value;
						if (av:kind == ExpressionKind:IDENT) {
							local Parameter is pDef: vMem:params:get(index: idx);
							self:localVars:set(key: av:stringValue, value: self:formatVarTypeString(t: pDef:paramType));
						}
					}
					idx: idx + 1;
				});
				c:resolvedType: enumName;
			} else {
				self:inferExpressionType(expr: c);
			}
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
		if (targetType:startsWith(prefix: 'Array of ') && targetType:length() > 9) {
			cbElem: targetType:substring(start: 9, end: targetType:length());
		} else if (targetType:startsWith(prefix: 'Array:') && targetType:length() > 6) {
			cbElem: targetType:substring(start: 6, end: targetType:length());
		}
		if (cbElem != Primitive:ANY:value()) {
			local String is elemTypeName: cbElem;
			if (method == 'fold' && expr:methodArgs:length() >= 2) {
				local NamedArg is a0: expr:methodArgs:get(index: 0);
				local String is initType: self:inferExpressionType(expr: a0:value);
				local NamedArg is a1: expr:methodArgs:get(index: 1);
				local Expression is av: a1:value;
				if (av:kind == ExpressionKind:ANON_FN) {
					if (av:anonParams:length() >= 1) {
						local Parameter is p0: av:anonParams:get(index: 0);
						if (p0:paramType:name == Primitive:ANY:value() || p0:paramType:name == '') {
							p0:paramType: Type:init(name: initType);
						}
					}
					if (av:anonParams:length() >= 2) {
						local Parameter is p1: av:anonParams:get(index: 1);
						if (p1:paramType:name == Primitive:ANY:value() || p1:paramType:name == '') {
							p1:paramType: Type:init(name: elemTypeName);
						}
					}
				}
			} else {
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					local Expression is av: arg:value;
					if (av:kind == ExpressionKind:ANON_FN) {
						av:anonParams:each(action: local Function(Parameter is p){
							if (p:paramType:name == Primitive:ANY:value() || p:paramType:name == '') {
								p:paramType: Type:init(name: elemTypeName);
							}
						});
					}
				});
			}
		} else if (targetType:startsWith(prefix: 'Map:') && method == 'each') {
			local String is afterMap: targetType:substring(start: 4, end: targetType:length());
			local Int is colonIdx: afterMap:indexOf(search: ':', default: -1);
			local String is valTypeName: Primitive:STRING:value();
			if (colonIdx >= 0 && colonIdx + 1 < afterMap:length()) {
				valTypeName: afterMap:substring(start: colonIdx + 1, end: afterMap:length());
			}
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				local Expression is av: arg:value;
				if (av:kind == ExpressionKind:ANON_FN) {
					if (av:anonParams:length() >= 1) {
						local Parameter is p0: av:anonParams:get(index: 0);
						if (p0:paramType:name == Primitive:ANY:value() || p0:paramType:name == '') {
							p0:paramType: Type:init(name: 'String');
						}
					}
					if (av:anonParams:length() >= 2) {
						local Parameter is p1: av:anonParams:get(index: 1);
						if (p1:paramType:name == Primitive:ANY:value() || p1:paramType:name == '') {
							p1:paramType: Type:init(name: valTypeName);
						}
					}
				}
			});
		}
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

		if (kind == ExpressionKind:USING_AS) {
			self:addError(line: self:currentLine, msg: 'Instance imports (as ClassName()) may only appear as entries of a using declaration (INSTANCE.md E1).');
			expr:resolvedType: '';
			return '';
		}

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
				if (name == self:names:selfIdent()) {
					res: self:currentClassName;
				} else if (self:localVars:has(key: name)) {
					res: self:localVars:getString(key: name, default: Primitive:ANY:value());
				} else if (self:fieldTypes:has(key: name)) {
					if (self:unassignedFields:has(key: name)) {
						self:addError(line: self:currentLine, msg: 'Field \'' . name . '\' in class \'' . self:currentClassName . '\' is read before being initialized.');
					}
					local String is owner: self:findMemberOwnerClass(className: self:currentClassName, memberName: name);
					if (owner != '') {
						self:checkMemberVisibility(ownerClass: owner, member: self:findAncestorMember(className: self:currentClassName, memberName: name), memberName: name);
					}
					res: self:fieldTypes:getString(key: name, default: Primitive:ANY:value());
				} else if (self:allEnumVariants:has(key: name)) {
					res: self:allEnumVariants:getString(key: name, default: Primitive:ANY:value());
				} else if (self:registeredClasses:has(key: name)) {
					res: name;
				} else if (self:isPrimitive(t: name)) {
					res: name;
				} else if (name != '') {
					self:addError(line: self:currentLine, msg: 'Undefined identifier \'' . name . '\'.');
				}
			}
			is ExpressionKind:PATH: {
				local Array of String is segs: expr:pathSegments;
				if (segs:length() > 0) {
					local String is root: segs:get(index: 0);
					local String is rootType: '';
					if (root == self:names:selfIdent()) {
						rootType: self:currentClassName;
						if (segs:length() >= 2 && self:unassignedFields:has(key: segs:get(index: 1))) {
							self:addError(line: self:currentLine, msg: 'Field \'' . segs:get(index: 1) . '\' in class \'' . self:currentClassName . '\' is read before being initialized.');
						}
						if (segs:length() >= 2) {
							local String is fName: segs:get(index: 1);
							local String is fOwner: self:findMemberOwnerClass(className: self:currentClassName, memberName: fName);
							if (fOwner != '') {
								self:checkMemberVisibility(ownerClass: fOwner, member: self:findAncestorMember(className: self:currentClassName, memberName: fName), memberName: fName);
							}
						}
					} else if (self:localVars:has(key: root)) {
						rootType: self:localVars:getString(key: root, default: '');
					} else if (self:fieldTypes:has(key: root)) {
						if (self:unassignedFields:has(key: root)) {
							self:addError(line: self:currentLine, msg: 'Field \'' . root . '\' in class \'' . self:currentClassName . '\' is read before being initialized.');
						}
						rootType: self:fieldTypes:getString(key: root, default: '');
					} else if (self:allEnumNames:has(key: root)) {
						rootType: root;
					} else if (self:registeredClasses:has(key: root)) {
						rootType: root;
						# INSTANCE.md §2.3: fields and values are not reachable
						# through a class-name prefix — methods only. A PATH
						# rooted at a non-type-level class name with further
						# segments is a prefixed field access: rejected.
						if (segs:length() >= 2 && !self:allEnumNames:has(key: root) && !self:isPrimitive(t: root) && root != 'Array' && root != 'Map' && root != 'List' && root != 'String' && root != 'Function' && root != 'LoopControl') {
							self:addError(line: self:currentLine, msg: 'Fields are not reachable through the class-name prefix \'' . root . '\'; call a method on the instance (INSTANCE.md §2.3).');
							rootType: '';
						}
					}
					local PathResolveLoop is pLoop: PathResolveLoop:init(tc: self, segs: segs, rootType: rootType);
					While:run(loop: pLoop);
					if (pLoop:currType != '') {
						res: pLoop:currType;
					}
				}
			}
			is ExpressionKind:BINARY: {
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr);
				local String is rightT: self:inferExpressionType(expr: expr:rightExpr);
				local String is op: expr:binaryOp;
				when (op) {
					is '.': {
						res: Primitive:STRING:value();
					}
					is '==', '!=', 'is', '<', '<=', '>', '>=': {
						res: Primitive:BOOLEAN:value();
					}
					is '&&', '||': {
						res: Primitive:BOOLEAN:value();
					}
					is '+', '-', '*', '/', '%': {
						res: if (leftT == 'Float' || rightT == 'Float') 'Float' else Primitive:INT:value();
					}
					is '&', '|', '^', '<<', '>>': {
						res: Primitive:INT:value();
						if ((leftT != '' && leftT != 'Any' && leftT != Primitive:INT:value()) ||
							(rightT != '' && rightT != 'Any' && rightT != Primitive:INT:value())) {
							local String is msg: 'Bitwise operator \'' . op . '\' requires Int operands (got \'' . leftT . '\' and \'' . rightT . '\').';
							self:addError(line: self:currentLine, msg: msg);
						}
					}
					else: {
						res: Primitive:INT:value();
					}
				}
			}
			is ExpressionKind:CAST: {
				local String is innerT: self:inferExpressionType(expr: expr:leftExpr);
				local String is target: expr:castTarget;
				local String is src: if (innerT != '') innerT else Primitive:ANY:value();
				local Boolean is isFormat: target == 'Hex' || target == 'Bin' || target == 'Oct';
				# Every non-format cast takes no arguments.
				if (expr:castArgs:length() > 0 && !isFormat) {
					self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' takes no arguments.');
				}
				when (target) {
					is 'Hex', 'Bin', 'Oct': {
						if (expr:castArgs:length() > 1) {
							self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' accepts at most one width argument.');
						}
						if (src != 'Any' && src != 'String' && src != Primitive:INT:value()) {
							self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' requires an Int or String operand (got \'' . src . '\').');
						}
						res: if (src == 'String') Primitive:INT:value() else 'String';
					}
					else: {
						if (self:allEnumNames:has(key: target)) {
							self:addError(line: self:currentLine, msg: 'Cannot cast to enum \'' . target . '\'; construct a variant instead.');
							res: target;
						} else if (self:castableMethod(srcType: src, target: target) != '') {
							# Declared cast: the source class maps the target to a
							# producing method (G6 emits the call).
							res: target;
						} else if (self:isPrimitive(t: target) && target != Primitive:ANY:value()) {
							# Primitive conversion casts take priority over the
							# class-cast path: Int as String is the machine
							# conversion even though a String class is loaded.
							# Any is excluded — it is the universal class-cast
							# target, always related. These die when the
							# primitive classes land in Spec and declare their
							# conversions.
							if (!self:isCastable(src: src, target: target)) {
								self:addError(line: self:currentLine, msg: 'Cannot cast \'' . src . '\' to \'' . target . '\'.');
							}
							res: target;
						} else if (self:registeredClasses:has(key: target) || self:registeredClasses:has(key: target:split(delimiter: ':'):get(index: 0))) {
							# Class casts are inheritance-based: unrelated classes
							# cannot cast, Any casts to anything.
							local Boolean is related: src == Primitive:ANY:value() || self:isSubclassOf(subName: src, baseName: target) || self:isSubclassOf(subName: target, baseName: src);
							if (!related) {
								self:addError(line: self:currentLine, msg: 'Cannot cast \'' . src . '\' to unrelated class \'' . target . '\'.');
							}
							res: target;
						} else {
							self:addError(line: self:currentLine, msg: 'Unknown cast target \'' . target . '\'.');
							res: 'Any';
						}
					}
				}
			}
			is ExpressionKind:UNARY: {
				local String is innerT: self:inferExpressionType(expr: expr:unaryExpr);
				if (expr:unaryOp == '~' && innerT != '' && innerT != 'Any' && innerT != Primitive:INT:value()) {
					local String is msg: 'Bitwise complement \'~\' requires an Int operand (got \'' . innerT . '\').';
					self:addError(line: self:currentLine, msg: msg);
				}
				if ((expr:unaryOp == '++' || expr:unaryOp == '--' || expr:unaryOp == 'post++' || expr:unaryOp == 'post--') && innerT != '' && innerT != 'Any' && innerT != Primitive:INT:value()) {
					local String is msg: 'Operator \'' . expr:unaryOp . '\' requires an Int operand (got \'' . innerT . '\').';
					self:addError(line: self:currentLine, msg: msg);
				}
				if (expr:unaryOp == '!') {
					res: Primitive:BOOLEAN:value();
				} else {
					res: innerT;
				}
			}
			is ExpressionKind:ARRAY: {
				# Bidirectional: a container expectation from the declaration
				# site types the literal directly — no hint state. The
				# elements must still be assignable to the declared element
				# type ('Array of Int is flags: ['on']' is a compile error).
				if (expected != '' && (expected:startsWith(prefix: 'Array') || expected:startsWith(prefix: 'List'))) {
					local String is elemT: '';
					local Int is eColon: expected:indexOf(search: ':', default: -1);
					local Int is eOf: expected:indexOf(search: ' of ', default: -1);
					if (eColon >= 0 && (expected:startsWith(prefix: 'Array:') || expected:startsWith(prefix: 'List:'))) {
						elemT: expected:substring(start: eColon + 1, end: expected:length());
					} else if (eOf >= 0) {
						elemT: expected:substring(start: eOf + 4, end: expected:length());
					}
					expr:arrayItems:each(action: local Function(Expression is item){
						local String is itemT: self:inferExpressionType(expr: item);
						if (elemT != '' && itemT != '' && itemT != Primitive:ANY:value() && !self:isAssignable(target: elemT, source: itemT)) {
							self:addError(line: self:currentLine, msg: "Cannot assign 'Array:" . itemT . "' to 'Array:" . elemT . "'.");
						}
					});
					res: expected;
				} else {
					local String is firstElemType: '';
					expr:arrayItems:each(action: local Function(Expression is item){
						local String is itemT: self:inferExpressionType(expr: item);
						if (firstElemType == '' && itemT != '' && itemT != Primitive:ANY:value()) {
							firstElemType: itemT;
						}
					});
					if (firstElemType != '') {
						res: 'Array:' . firstElemType;
					} else {
						res: 'Array';
					}
				}
			}
			is ExpressionKind:MAP: {
				if (expected != '' && expected:startsWith(prefix: 'Map')) {
					# Value type from the expectation ('Map of K to V' both
					# spellings); values must be assignable to it.
					local String is valT: '';
					# Both spellings: 'Map of K to V' and the canonical
					# colon form 'Map:K:V' (formatTypeString's output).
					local Array of String is mParts: expected:split(delimiter: ':');
					if (mParts:length() > 2) {
						valT: mParts:get(index: 2);
					} else {
						local String is kv: expected:substring(start: 4, end: expected:length());
						if (kv:startsWith(prefix: ' of ')) {
							kv: kv:substring(start: 4, end: kv:length());
						}
						local Int is toIdx: kv:indexOf(search: ' to ', default: -1);
						if (toIdx >= 0) {
							valT: kv:substring(start: toIdx + 4, end: kv:length());
						}
					}
					expr:mapKeys:each(action: local Function(Expression is k){
						self:inferExpressionType(expr: k);
					});
					expr:mapValues:each(action: local Function(Expression is v){
						local String is vT: self:inferExpressionType(expr: v);
						if (valT != '' && vT != '' && vT != Primitive:ANY:value() && !self:isAssignable(target: valT, source: vT)) {
							self:addError(line: self:currentLine, msg: "Cannot assign 'Map:String:" . vT . "' to 'Map:String:" . valT . "'.");
						}
					});
					res: expected;
				} else {
					local String is firstKeyType: '';
					local String is firstValType: '';
					expr:mapKeys:each(action: local Function(Expression is k){
						local String is kt: self:inferExpressionType(expr: k);
						if (firstKeyType == '' && kt != '' && kt != Primitive:ANY:value()) {
							firstKeyType: kt;
						}
					});
					expr:mapValues:each(action: local Function(Expression is v){
						local String is vt: self:inferExpressionType(expr: v);
						if (firstValType == '' && vt != '' && vt != Primitive:ANY:value()) {
							firstValType: vt;
						}
					});
					if (firstKeyType != '' && firstValType != '') {
						res: 'Map:' . firstKeyType . ':' . firstValType;
					} else {
						res: 'Map';
					}
				}
			}
			is ExpressionKind:FIELD_ACCESS: {
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr);
				if (leftT == '' || leftT == 'Any' || self:isPrimitive(t: leftT)) {
					res: 'Any';
				} else {
					local Array of String is faParts: leftT:split(delimiter: ':');
					local String is faBase: faParts:get(index: 0);
					local String is fName: expr:stringValue;
					local String is fOwner: self:findMemberOwnerClass(className: faBase, memberName: fName);
					if (fOwner != '') {
						self:checkMemberVisibility(ownerClass: fOwner, member: self:findAncestorMember(className: faBase, memberName: fName), memberName: fName);
					}
					local String is fT: self:lookupFieldType(className: leftT, fieldName: fName);
					res: if (fT != '') fT else 'Any';
				}
			}
			is ExpressionKind:INDEX: {
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr);
				self:inferExpressionType(expr: expr:rightExpr);
				# Element extraction accepts both container spellings.
				if (leftT:startsWith(prefix: 'Array of ') && leftT:length() > 9) {
					res: leftT:substring(start: 9, end: leftT:length());
				} else if (leftT:startsWith(prefix: 'Array:') && leftT:length() > 6) {
					res: leftT:substring(start: 6, end: leftT:length());
				} else if (leftT:startsWith(prefix: 'Map:') && leftT:length() > 4) {
					local String is afterMap: leftT:substring(start: 4, end: leftT:length());
					local Int is colonIdx: afterMap:indexOf(search: ':', default: -1);
					if (colonIdx >= 0 && colonIdx + 1 < afterMap:length()) {
						res: afterMap:substring(start: colonIdx + 1, end: afterMap:length());
					} else {
						res: Primitive:STRING:value();
					}
				} else if (leftT == 'Map') {
					res: Primitive:STRING:value();
				} else {
					res: 'Any';
				}
			}
			is ExpressionKind:IF_ELSE: {
				self:inferExpressionType(expr: expr:condExpr);
				local String is thenT: self:inferExpressionType(expr: expr:thenExpr);
				local String is elseT: self:inferExpressionType(expr: expr:elseExpr);
				res: if (thenT != '' && thenT != Primitive:ANY:value()) thenT else elseT;
			}
			is ExpressionKind:WHEN: {
				local String is subjectType: self:inferExpressionType(expr: expr:whenSubject);
				local String is armType: 'Any';
				expr:whenArms:each(action: local Function(WhenArm is arm){
					self:bindWhenPatternVars(arm: arm);
					if (arm:hasValueExpr) {
						local String is vt: self:inferExpressionType(expr: arm:valueExpr);
						if (armType == Primitive:ANY:value() && vt != '' && vt != Primitive:ANY:value()) {
							armType: vt;
						}
					}
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

				self:currentMethodReturnType: self:resolveReturnType(t: expr:anonReturnType);
				expr:anonParams:each(action: local Function(Parameter is p){
					self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
				});
				expr:anonBody:each(action: local Function(Statement is s){
					self:anonDepth: self:anonDepth + 1;
					self:checkStatement(stmt: s);
					self:anonDepth: self:anonDepth - 1;
				});

				self:localVars: savedVars;
				self:currentMethodReturnType: savedRet;
				local String is anonRetName: expr:anonReturnType:name;
				if (anonRetName != '' && !self:isVoid(t: anonRetName)) {
					res: 'Function:' . self:formatTypeString(t: expr:anonReturnType);
				} else {
					res: 'Function';
				}
			}
			is ExpressionKind:CALL: {
				res: self:inferCall(expr: expr, expected: expected);
			}
			else: {
				res: 'Any';
			}
		}

		if (kind == ExpressionKind:CALL) {
			self:checkCallArguments(callExpr: expr);
		}

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
		if (targetName == '' && expr:methodTarget:kind == ExpressionKind:PATH && expr:methodTarget:pathSegments:length() > 0) {
			targetName: expr:methodTarget:pathSegments:get(index: expr:methodTarget:pathSegments:length() - 1);
		}

		# INSTANCE.md E5/E7: the call model. A class-name receiver admits
		# only init, unless the enclosing class instance-imports the class
		# (elided dispatch) or the stratum is type-level by design (enums,
		# primitives, containers, transparent runtime types). Conversely,
		# init on a non-class receiver is construct-only and banned.
		local String is recvName: '';
		if (expr:methodTarget:kind == ExpressionKind:IDENT || expr:methodTarget:kind == ExpressionKind:PATH) {
			local String is cand: targetName;
			if (cand != '' && cand != self:names:selfIdent() && self:registeredClasses:has(key: cand) && !self:localVars:has(key: cand) && !self:fieldTypes:has(key: cand)) {
				recvName: cand;
			}
		}
		if (recvName != '' && expr:methodName != 'init') {
			local Boolean is isTypeLevel: self:allEnumNames:has(key: recvName) || self:isPrimitive(t: recvName) || recvName == 'Array' || recvName == 'Map' || recvName == 'List' || recvName == 'String' || recvName == 'Function' || recvName == 'LoopControl';
			if (!isTypeLevel) {
				if (!self:isAsImportedInherited(className: recvName)) {
					if (recvName == self:currentClassName) {
						self:addError(line: self:currentLine, msg: 'Cannot call members of \'' . recvName . '\' through the class name inside \'' . recvName . '\' itself; use self (INSTANCE.md §2.2).');
					} else {
						self:addError(line: self:currentLine, msg: 'Members of \'' . recvName . '\' are callable only through an instance; instance-import it (\'as ' . recvName . '()\') or construct one (INSTANCE.md E5).');
					}
				}
			}
		}
		if (recvName == '' && expr:methodName == 'init') {
			self:addError(line: self:currentLine, msg: '\'init\' is construct-only; call it on the class name (INSTANCE.md E7).');
		}

		# INSTANCE.md §2.3/E9: bare-scope resolution for self-receiver
		# calls. The providers are the enclosing class (own and inherited
		# members) plus its as-imported classes, one level deep. Exactly
		# one provider resolves; two or more collide and force
		# qualification; zero is an error — the old behavior silently
		# invented CurrentClass_method and died in gcc.
		if (recvName == '' && expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:stringValue == self:names:selfIdent() && expr:methodName != 'init' && expr:methodName != 'typeName' && !self:localVars:has(key: expr:methodName) && !self:fieldTypes:has(key: expr:methodName)) {
			local String is ownOwner: self:findMemberOwnerClass(className: self:currentClassName, memberName: expr:methodName);
			local Array of String is bsProviders: self:bareScopeProviders(methodName: expr:methodName);
			local Int is providerTotal: bsProviders:length() + (if (ownOwner != '') 1 else 0);
			if (providerTotal > 1) {
				local String is listed: '';
				if (ownOwner != '') {
					listed: 'the enclosing class';
				}
				bsProviders:each(action: local Function(String is prov){
					if (listed == '') {
						listed: prov;
					} else {
						listed: listed . ' and ' . prov;
					}
				});
				self:addError(line: self:currentLine, msg: 'Function \'' . expr:methodName . '\' is provided by ' . listed . '; qualify the call (' . self:names:selfIdent() . ':' . expr:methodName . ' or the class name) (INSTANCE.md §2.3).');
				expr:resolvedType: '';
				return '';
			}
			if (providerTotal == 0) {
				self:addError(line: self:currentLine, msg: 'Undefined function \'' . expr:methodName . '\' on class \'' . self:currentClassName . '\' (INSTANCE.md E9).');
				expr:resolvedType: '';
				return '';
			}
			if (ownOwner == '') {
				local String is provider: bsProviders:get(index: 0);
				# The bare-scope branch runs before arg inference: type the
				# arguments now so overload selection sees exact types.
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					self:inferExpressionType(expr: arg:value);
				});
				self:selectOverload(className: provider, methodName: expr:methodName, expr: expr);
				expr:bareProvider: provider;
				local String is providerRet: self:lookupMethodReturnType(className: provider, methodName: expr:methodName);
				if (providerRet == '') {
					providerRet: 'Any';
				}
				res: providerRet;
				expr:resolvedType: res;
				return res;
			}
		}
		local Boolean is isWhileLoop: (targetType == 'While' || targetName == 'While') && (method == 'loop' || method == 'init' || method == 'condition');
		local Map of String to String is savedWhileVars;
		if (isWhileLoop) {
			savedWhileVars: Map:init();
			local Array of String is existingKeys: self:localVars:keys();
			existingKeys:each(action: local Function(String is k){
				savedWhileVars:set(key: k, value: self:localVars:getString(key: k, default: ''));
			});
			local Int is posIdx: 0;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				if (arg:value:kind == ExpressionKind:ARRAY && arg:value:anonParams:length() > 0) {
					arg:value:anonParams:each(action: local Function(Parameter is p){
						if (p:hasDefault) {
							self:inferExpressionType(expr: p:defaultExpr);
						}
						self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
					});
				}
				if (arg:name == 'evaluate' && arg:value:kind == ExpressionKind:ANON_FN) {
					if (arg:value:anonReturnType:name == '' || arg:value:anonReturnType:name == self:names:voidName()) {
						arg:value:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
					}
				} else if (arg:name == '' && arg:value:kind == ExpressionKind:ANON_FN) {
					if (posIdx == 1 || (posIdx == 0 && expr:methodArgs:length() == 2)) {
						if (arg:value:anonReturnType:name == '' || arg:value:anonReturnType:name == self:names:voidName()) {
							arg:value:anonReturnType: Type:init(name: Primitive:BOOLEAN:value());
						}
					}
				}
				posIdx: posIdx + 1;
			});
		}

		self:bindContainerCallbackParams(targetType: targetType, method: method, expr: expr);
		expr:methodArgs:each(action: local Function(NamedArg is arg){
			self:inferExpressionType(expr: arg:value);
		});

		if (isWhileLoop) {
			self:localVars: savedWhileVars;
			expr:resolvedType: 'Void';
			return 'Void';
		}

		if (targetType == self:names:selfIdent() || targetType == '') {
			targetType: self:currentClassName;
		}

		# Sysinternal floor access by qualified chain: ONLY base:sys
		# wrappers may call the floor — everyone else goes through the
		# same-name wrapper (the sysinternal discipline).
		if (expr:methodTarget:kind == ExpressionKind:PATH) {
			local String is qJoined: '';
			expr:methodTarget:pathSegments:each(action: local Function(String is seg){
				if (qJoined == '') {
					qJoined: seg;
				} else {
					qJoined: qJoined . ':' . seg;
				}
			});
			if (qJoined:contains(needle: ':sysinternal:')) {
				local ClassInfo is callerCls: self:findClass(name: self:currentClassName);
				local String is callerNs: callerCls:namespaceJoined();
				if (callerNs != 'base:sys') {
					self:addError(line: self:currentLine, msg: 'The sysinternal floor is only accessible from base:sys wrappers; call the base:sys wrapper instead (call from \'' . callerNs . '\').');
				}
				res: self:lookupMethodReturnType(className: qJoined, methodName: method);
				expr:resolvedType: res;
				return res;
			}
		}

		# Namespace-qualified chains: `base:sysinternal:Buf()` and method
		# calls on one — the chain's type is the named class.
		if (targetType == Primitive:ANY:value() || targetType == '') {
			if (expr:methodTarget:kind == ExpressionKind:PATH) {
				local ClassInfo is qCls: self:findClass(name: method);
				if (qCls:name == method) {
					targetType: method;
				}
			} else if (expr:methodTarget:kind == ExpressionKind:CALL) {
				local Expression is qInner: expr:methodTarget;
				if (qInner:methodTarget:kind == ExpressionKind:PATH) {
					local String is qCand: qInner:methodName;
					local ClassInfo is qCls: self:findClass(name: qCand);
					if (qCand != '' && qCls:name == qCand) {
						targetType: qCand;
					}
				}
			}
		}

		if (!self:allEnumNames:has(key: targetType) && targetType != '' && targetType != 'Any') {
			local Array of String is cParts: targetType:split(delimiter: ':');
			local String is cBase: cParts:get(index: 0);
			local String is mOwner: self:findMemberOwnerClass(className: cBase, memberName: method);
			if (mOwner != '') {
				self:checkMemberVisibility(ownerClass: mOwner, member: self:lookupAnyMember(className: cBase, methodName: method), memberName: method);
			}
		}
		if (targetType == Primitive:ANY:value() && method != 'toString' && method != 'typeName' && method != 'init') {
			self:addError(line: self:currentLine, msg: 'Member \'' . method . '\' is not part of the root contract; cast the Any-typed value to a concrete class before calling it (value as ClassName).');
		}

		local String is fnVarT: '';
		if (expr:methodTarget:kind == ExpressionKind:IDENT && expr:methodTarget:stringValue == self:names:selfIdent()) {
			fnVarT: self:localVars:getString(key: method, default: self:fieldTypes:getString(key: method, default: ''));
		}
		if (targetType == 'Parallel' && method == 'run') {
			local Boolean is hasWorker: false;
			expr:methodArgs:each(action: local Function(NamedArg is arg){
				local String is aName: arg:name;
				local String is aType: self:inferExpressionType(expr: arg:value);
				if (aName == 'threads' || aName == 'iterations') {
					if (aType != Primitive:INT:value() && aType != 'Any') {
						self:addError(line: self:currentLine, msg: 'Parallel:run \'' . aName . '\' argument must be Int, found \'' . aType . '\'.');
					}
				} else if (aName == 'worker') {
					hasWorker: true;
					if (!aType:startsWith(prefix: 'Function') && aType != 'Any') {
						self:addError(line: self:currentLine, msg: 'Parallel:run \'worker\' argument must be a Function, found \'' . aType . '\'.');
					}
				}
			});
			if (!hasWorker) {
				self:addError(line: self:currentLine, msg: 'Parallel:run requires \'worker\' named argument.');
			}
			res: Primitive:INT:value();
		} else if (fnVarT:startsWith(prefix: 'Function')) {
			if (fnVarT:startsWith(prefix: 'Function:') && fnVarT:length() > 9) {
				res: fnVarT:substring(start: 9, end: fnVarT:length());
			} else {
				res: 'Any';
			}
		} else if (self:allEnumVariants:has(key: method) && (self:allEnumNames:has(key: targetType) || targetType == self:currentClassName)) {
			res: self:allEnumVariants:getString(key: method, default: Primitive:ANY:value());
		} else if (method == 'typeName' && self:registeredClasses:has(key: targetType)) {
			res: Primitive:STRING:value();
		} else if (method == 'init' && self:registeredClasses:has(key: targetType) && !self:allEnumNames:has(key: targetType)) {
			# FUNCTIONS.md §I.2: init overloads are selected and stamped like any member.
			self:selectOverload(className: targetType, methodName: 'init', expr: expr);
			res: targetType;
		} else if (self:registeredClasses:has(key: targetType:split(delimiter: ':'):get(index: 0)) && !self:allEnumNames:has(key: targetType)) {
			# List get/pop REQUIRE a 'default:' argument (Never Null).
			if ((targetType == 'List' || targetType:startsWith(prefix: 'List:') || targetType:startsWith(prefix: 'List of ')) && (method == 'get' || method == 'pop')) {
				local Boolean is hasDefault: false;
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					if (arg:name == 'default') {
						hasDefault: true;
					}
				});
				if (!hasDefault) {
					self:addError(line: self:currentLine, msg: 'List \'' . method . '\' requires a \'default:\' argument.');
				}
			}
			# Specialized containers ('Array:String') resolve through their
			# base class's declarations with type-argument substitution;
			# when the declaration is not loaded, the element type comes
			# from the type string itself.
			local Member is selected: self:selectOverload(className: targetType, methodName: method, expr: expr);
			local String is cRet: '';
			if (selected:name != '') {
				cRet: self:selectedReturnType(className: targetType, selected: selected);
			}
			if (cRet == '' || self:isVoid(t: cRet)) {
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
				if (res == targetType) {
					if ((targetType:startsWith(prefix: 'Array') || targetType:startsWith(prefix: 'List')) && scParts:length() > 1 && (method == 'get' || method == 'pop' || method == 'removeAt')) {
						res: scParts:get(index: 1);
					}
					if (targetType:startsWith(prefix: 'Map') && scParts:length() > 2 && (method == 'get' || method == 'getString')) {
						res: scParts:get(index: 2);
					}
				}
			} else {
				res: cRet;
			}
		} else if (targetType:startsWith(prefix: 'Array') && method == 'map') {
			local String is mappedElem: Primitive:ANY:value();
			if (expr:methodArgs:length() > 0) {
				local NamedArg is a0: expr:methodArgs:get(index: 0);
				local Expression is fnExpr: a0:value;
				if (fnExpr:kind == ExpressionKind:ANON_FN) {
					local String is fnRet: fnExpr:anonReturnType:name;
					if (fnRet != '' && !self:isVoid(t: fnRet) && fnRet != Primitive:ANY:value()) {
						mappedElem: self:formatTypeString(t: fnExpr:anonReturnType);
					}
				}
			}
			res: if (mappedElem != Primitive:ANY:value()) 'Array:' . mappedElem else 'Array';
		} else if (targetType:startsWith(prefix: 'Array') && method == 'fold') {
			if (expr:methodArgs:length() > 0) {
				local NamedArg is a0: expr:methodArgs:get(index: 0);
				res: a0:value:resolvedType;
			} else {
				res: 'Any';
			}
		} else if (self:allEnumNames:has(key: targetType)) {
			when (method) {
				is 'name': { res: Primitive:STRING:value(); }
				is 'ordinal': { res: Primitive:INT:value(); }
				is 'values': { res: 'Array:' . targetType; }
				is 'of': { res: targetType; }
				is 'value': {
					res: if (self:allStringBackedEnums:has(key: targetType)) 'String' else Primitive:INT:value();
				}
				else: { res: 'Any'; }
			}
		} else if (targetType == Primitive:INT:value() && method == 'toBase') {
			# Int:toBase is a floor binding (spec_int_to_base) returning a
			# String; Int has no loaded declaration to consult.
			res: Primitive:STRING:value();
		} else {
			# Undeclared members are compile errors on LOADED classes; an
			# unloaded class (floor singleton used without import) resolves
			# as Any — the runtime magic defines it.
			local Array of String is uParts: targetType:split(delimiter: ':');
			if (self:registeredClasses:has(key: uParts:get(index: 0)) && self:findClass(name: uParts:get(index: 0)):name != '') {
				self:addError(line: self:currentLine, msg: 'Member \'' . method . '\' is not declared on class \'' . targetType . '\'.');
			}
			res: 'Any';
		}
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
		if (src == target || src == Primitive:ANY:value()) {
			return true;
		}
		if (target == Primitive:INT:value()) {
			return src == 'Float' || src == 'String' || src == 'Byte';
		}
		if (target == 'Float') {
			return src == Primitive:INT:value();
		}
		if (target == 'Byte') {
			return src == Primitive:INT:value();
		}
		if (target == 'String') {
			return true;
		}
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
		if (srcType == '' || srcType == Primitive:ANY:value() || self:isPrimitive(t: srcType)) {
			return '';
		}
		local Array of String is srcParts: srcType:split(delimiter: ':');
		local ClassInfo is cls: self:findClass(name: srcParts:get(index: 0));
		if (cls:name == '') {
			return '';
		}
		# castable is a metadata FIELD declared on the class itself — the
		# method-only member lookup cannot see it, and ancestor searches skip
		# the declaring class. Search own members directly.
		local FieldSearchLoop is castLoop: FieldSearchLoop:init(members: cls:members, fieldName: MetadataField:CASTABLE:value());
		While:run(loop: castLoop);
		if (!castLoop:found) {
			return '';
		}
		local Member is castM: castLoop:res;
		if (!castM:hasInit || castM:initExpr:kind != ExpressionKind:ARRAY) {
			return '';
		}
		local String is found: '';
		castM:initExpr:arrayItems:each(action: local Function(Expression is entry){
			if (found == '' && entry:kind == ExpressionKind:ARRAY && entry:arrayItems:length() == 2) {
				local Expression is tExpr: entry:arrayItems:get(index: 0);
				local Expression is fExpr: entry:arrayItems:get(index: 1);
				local String is entryTarget: tExpr:stringValue;
				local String is entryFn: fExpr:stringValue;
				if (entryTarget == target) {
					local String is fnRet: self:lookupMethodReturnType(className: srcType, methodName: entryFn);
					if (fnRet != target) {
						self:addError(line: self:currentLine, msg: 'Cast \'as ' . target . '\' maps to \'' . entryFn . '\', which returns \'' . fnRet . '\', not \'' . target . '\'.');
						found: entryFn;
						return;
					}
					found: entryFn;
				}
			}
		});
		return found;
	}

	## Validates type safety of a statement node.
	##
	## @param stmt: AST statement node.
	Function is checkStatement(Statement is stmt){
		if (stmt:line > 0) {
			self:currentLine: stmt:line;
		}
		local StatementKind is kind: stmt:kind;

		when (kind) {
			is StatementKind:VAR_DECL: {
				local String is varName: stmt:varName;
				local String is fullType: self:formatVarTypeString(t: stmt:varType);
				self:localVars:set(key: varName, value: fullType);

				if (fullType == 'List') {
					local String is msg: 'Bare List type requires [T] element syntax.';
					self:addError(line: stmt:line, msg: msg);
				}

				if (stmt:hasInit) {
					# Bidirectional: the declared type flows into the
					# initializer, typing container literals directly.
					local String is initType: self:inferExpressionType(expr: stmt:initExpr, expected: fullType);
					if (!self:isAssignable(target: fullType, source: initType)) {
						local String is msg: 'Type mismatch in variable declaration for \'' . varName . '\': cannot assign \'' . initType . '\' to \'' . fullType . '\'.';
						self:addError(line: stmt:line, msg: msg);
					}
				}
			}
			is StatementKind:ASSIGN: {
				if (stmt:assignTarget:kind == ExpressionKind:PATH) {
					local Array of String is tSegs: stmt:assignTarget:pathSegments;
					if (tSegs:length() == 2 && tSegs:get(index: 0) == self:names:selfIdent()) {
						self:unassignedFields:remove(key: tSegs:get(index: 1));
					}
				} else if (stmt:assignTarget:kind == ExpressionKind:IDENT) {
					self:unassignedFields:remove(key: stmt:assignTarget:stringValue);
				}
				local String is targetType: self:inferExpressionType(expr: stmt:assignTarget);
				local String is valType: self:inferExpressionType(expr: stmt:assignValue, expected: targetType);
				if (!self:isAssignable(target: targetType, source: valType)) {
					local String is msg: 'Type mismatch in assignment: cannot assign \'' . valType . '\' to \'' . targetType . '\'.';
					self:addError(line: stmt:line, msg: msg);
				}
			}
			is StatementKind:IF: {
				local String is condType: self:inferExpressionType(expr: stmt:ifCondition);
				if (condType != 'Boolean' && condType != Primitive:ANY:value()) {
					local String is msg: 'Condition in \'if\' must be Boolean, found \'' . condType . '\'.';
					self:addError(line: stmt:line, msg: msg);
				}
				stmt:thenBranch:each(action: local Function(Statement is s){
					self:checkStatement(stmt: s);
				});
				if (stmt:hasElse) {
					stmt:elseBranch:each(action: local Function(Statement is s){
						self:checkStatement(stmt: s);
					});
				}
			}
			is StatementKind:WHEN: {
				local String is stmtSubjectType: self:inferExpressionType(expr: stmt:whenSubject);
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					self:bindWhenPatternVars(arm: arm);
					if (arm:hasValueExpr) {
						self:inferExpressionType(expr: arm:valueExpr);
					}
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
				if (stmt:hasReturnExpr) {
					# Bidirectional: the declared return type flows in.
					local String is retType: self:inferExpressionType(expr: stmt:returnExpr, expected: self:currentMethodReturnType);
					if (!self:isAssignable(target: self:currentMethodReturnType, source: retType)) {
						local String is msg: 'Method declared return type \'' . self:currentMethodReturnType . '\', but returned \'' . retType . '\'.';
						self:addError(line: stmt:line, msg: msg);
					}
				} else {
					if (self:currentMethodReturnType != 'void' && self:currentMethodReturnType != 'Void' && self:currentMethodReturnType != '' && self:currentMethodReturnType != 'Any') {
						local String is msg: 'Method expects return value of type \'' . self:currentMethodReturnType . '\', but found empty return.';
						self:addError(line: stmt:line, msg: msg);
					}
				}
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

	## Validates a merge-forward statement against its parent method:
	## merge context, single-use, arity, naming, and argument types.
	##
	## @param stmt: The FORWARD statement.
	Function is checkForward(Statement is stmt){
		if (!self:currentMethodIsMerge) {
			self:addError(line: stmt:line, msg: 'Forward statement `(args...)` requires the enclosing method to declare \'merge\'.');
			return;
		}
		if (self:anonDepth > 0) {
			self:addError(line: stmt:line, msg: 'Forward statement is not allowed inside a nested function.');
			return;
		}
		if (self:forwardSeen) {
			self:addError(line: stmt:line, msg: 'Multiple forward statements in method \'' . self:currentMethodName . '\'; at most one is allowed.');
			return;
		}
		self:forwardSeen: true;

		local Member is superM: self:findFirstSuperMethod(className: self:currentClassName, methodName: self:currentMethodName);
		if (superM:name == '') {
			self:addError(line: stmt:line, msg: 'Forward statement in \'' . self:currentMethodName . '\': no parent method to delegate to.');
			return;
		}
		local Array of Parameter is params: superM:params;
		local Array of NamedArg is args: stmt:forwardArgs;

		if (args:length() > params:length()) {
			self:addError(line: stmt:line, msg: 'Forward statement passes ' . args:length() . ' arguments but parent \'' . superM:name . '\' accepts ' . params:length() . '.');
			return;
		}
		if (args:length() < params:length()) {
			local Int is nIdx: 0;
			args:each(action: local Function(NamedArg is a){
				if (a:name == '') {
					self:addError(line: stmt:line, msg: 'Partial forward requires named arguments; argument ' . (nIdx + 1) . ' of \'' . self:currentMethodName . '\' is unnamed.');
				}
				nIdx: nIdx + 1;
			});
		}

		local Int is pIdx: 0;
		params:each(action: local Function(Parameter is p){
			local Expression is matchedValue: Expression:init(kind: ExpressionKind:UNKNOWN);
			local Boolean is found: false;
			args:each(action: local Function(NamedArg is a){
				if (!found && a:name != '' && a:name == p:name) {
					matchedValue: a:value;
					found: true;
				}
			});
			if (!found && pIdx < args:length()) {
				local NamedArg is posArg: args:get(index: pIdx);
				if (posArg:name == '') {
					matchedValue: posArg:value;
					found: true;
				}
			}
			if (found) {
				local String is argT: self:inferExpressionType(expr: matchedValue);
				local String is pT: p:paramType:name;
				if (pT != Primitive:ANY:value() && pT != '' && argT != '' && argT != Primitive:ANY:value() && !self:isAssignable(target: pT, source: argT)) {
					local String is label: if (p:name != '') p:name else 'position ' . (pIdx + 1);
					local String is msg: 'Forward argument \'' . label . '\' of \'' . self:currentMethodName . '\': cannot assign \'' . argT . '\' to \'' . pT . '\'.';
					self:addError(line: stmt:line, msg: msg);
				}
			} else if (!p:hasDefault) {
				local String is msg: 'Forward statement omits \'' . p:name . '\' of \'' . self:currentMethodName . '\' which has no default value.';
				self:addError(line: stmt:line, msg: msg);
			}
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
		if (method:line > 0) {
			self:currentLine: method:line;
		}
		if (method:sourceFile != '') {
			self:currentSourceFile: method:sourceFile;
		}
		self:currentMethodName: method:name;
		self:forwardSeen: false;
		self:anonDepth: 0;
		self:currentMethodIsMerge: method:hasModifier(kw: Keyword:MERGE);
		local Member is mergeTarget: self:findFirstSuperMethod(className: self:currentClassName, methodName: method:name);
		if (mergeTarget:name != '' && self:ancestorOverloaded(className: self:currentClassName, methodName: method:name, hops: 0)) {
			self:addError(line: method:line, msg: 'Cannot replace or merge an overloaded method (\'' . method:name . '\' has multiple signatures); give each signature a distinct name (FUNCTIONS.md §I.3).');
		}
		if (self:currentMethodIsMerge && mergeTarget:name == '') {
			self:addError(line: method:line, msg: 'Method \'' . method:name . '\' in class \'' . self:currentClassName . '\' declares \'merge\' but no parent declares a method with that name.');
		}
		method:params:each(action: local Function(Parameter is p){
			if (p:paramType:name == self:names:selfFieldMarker()) {
				local String is ft: self:fieldTypes:getString(key: p:name, default: Primitive:ANY:value());
				p:paramType: Type:init(name: ft);
				self:unassignedFields:remove(key: p:name);
			}
		});
		self:currentMethodReturnType: self:resolveReturnType(t: method:memberType);
		if (self:currentMethodReturnType == '' || self:isVoid(t: self:currentMethodReturnType)) {
			if (method:name == ContractMethod:EVALUATE:value() || method:name == ContractMethod:ITERATION:value()) {
				self:currentMethodReturnType: 'Boolean';
				method:memberType: Type:init(name: 'Boolean');
			}
		}
		self:localVars: Map:init();

		method:params:each(action: local Function(Parameter is p){
			self:localVars:set(key: p:name, value: self:formatVarTypeString(t: p:paramType));
		});

		method:body:each(action: local Function(Statement is stmt){
			self:checkStatement(stmt: stmt);
		});

		if (self:currentMethodIsMerge && !self:forwardSeen && method:body:length() > 0) {
			self:addError(line: method:line, msg: 'Merge method \'' . method:name . '\' in class \'' . self:currentClassName . '\' must contain a forward statement `(args...)`.');
		}
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
		if (cls:name == '') {
			return Member:init(kind: MemberKind:FIELD);
		}
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			if (res:name == '') {
				local Member is m: self:lookupAnyMember(className: baseName, methodName: methodName);
				if (m:kind == MemberKind:METHOD) {
					res: m;
				}
			}
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
		if (seen:has(key: className)) {
			return;
		}
		seen:set(key: className, value: 'true');
		local ClassInfo is cls: self:findClass(name: className);
		if (cls:name == '') {
			return;
		}
		cls:members:each(action: local Function(Member is m){
			if (m:kind == MemberKind:METHOD && m:name == methodName && m:body:length() > 0) {
				local Boolean is present: false;
				acc:each(action: local Function(String is n){
					if (!present && n == className) {
						present: true;
					}
				});
				if (!present) {
					acc:add(item: className);
				}
			}
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
		if (cls:name == '') {
			return Member:init(kind: MemberKind:FIELD);
		}
		local Member is res: Member:init(kind: MemberKind:FIELD);
		cls:baseClasses:each(action: local Function(String is baseName){
			if (res:name == '') {
				local ClassInfo is anc: self:findClass(name: baseName);
				if (anc:name != '') {
					anc:members:each(action: local Function(Member is m){
						if (res:name == '' && m:name == memberName) {
							res: m;
						}
					});
				}
			}
		});
		if (res:name == '') {
			cls:baseClasses:each(action: local Function(String is baseName){
				if (res:name == '') {
					res: self:findAncestorMember(className: baseName, memberName: memberName);
				}
			});
		}
		return res;
	}

	## Finds the nearest ancestor class declaring a member with the name.
	##
	## @param className: Starting class whose bases are searched.
	## @param memberName: Member name to locate.
	## @return: The declaring ancestor\'s name, or '' when absent.
	Function of String is findMemberOwnerClass(String is className, String is memberName){
		local ClassInfo is cls: self:findClass(name: className);
		if (cls:name == '') {
			return '';
		}
		local String is owner: '';
		cls:members:each(action: local Function(Member is m){
			if (owner == '' && m:name == memberName) {
				owner: cls:name;
			}
		});
		if (owner != '') {
			return owner;
		}
		cls:baseClasses:each(action: local Function(String is baseName){
			if (owner == '') {
				owner: self:findMemberOwnerClass(className: baseName, memberName: memberName);
			}
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
		if (ownerClass == '' || ownerClass == 'Any' || memberName == ContractMethod:INIT:value()) {
			return;
		}
		if (member:hasModifier(kw: Keyword:LOCAL)) {
			if (self:currentClassName != ownerClass) {
				local String is msg: 'Member \'' . memberName . '\' is local to class \'' . ownerClass . '\' and cannot be accessed from \'' . self:currentClassName . '\'.';
				self:addError(line: self:currentLine, msg: msg);
			}
		} else if (member:hasModifier(kw: Keyword:CONTAINED)) {
			if (!self:isSubclassOf(subName: self:currentClassName, baseName: ownerClass)) {
				local String is msg: 'Member \'' . memberName . '\' is contained in class \'' . ownerClass . '\' and cannot be accessed from unrelated class \'' . self:currentClassName . '\'.';
				self:addError(line: self:currentLine, msg: msg);
			}
		}
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
			if (hasReplace || hasMerge) {
				if (m:hasModifier(kw: Keyword:LOCAL) || m:hasModifier(kw: Keyword:CONTAINED)) {
					local String is msg: 'Member \'' . m:name . '\' in class \'' . classDef:name . '\' combines \'replace\'/\'merge\' with a visibility modifier; replace and merge members are public by definition.';
					self:addError(line: m:line, msg: msg);
					return;
				}
			}
			if (!hasReplace && !hasMerge) {
				return;
			}
			local String is name: m:name;
			if (name == ContractMethod:INIT:value() || name == ContractMethod:USING:value() || name == ContractMethod:TO_STRING:value()) {
				return;
			}
			if (self:findMemberOwnerClass(className: classDef:name, memberName: name) == Primitive:ANY:value()) {
				# Root-contract member: Any declares it public, so overriding
				# is always legitimate.
				return;
			}
			local Member is anc: self:findAncestorMember(className: classDef:name, memberName: name);
			if (anc:name == '') {
				local String is what: if (hasMerge) 'merge' else 'replace';
				local String is msg: 'Member \'' . name . '\' in class \'' . classDef:name . '\' declares \'' . what . '\' but no ancestor declares a member with that name.';
				self:addError(line: m:line, msg: msg);
			} else if (anc:hasModifier(kw: Keyword:LOCAL) || anc:hasModifier(kw: Keyword:CONTAINED)) {
				local String is vis: if (anc:hasModifier(kw: Keyword:LOCAL)) 'local' else 'contained';
				local String is msg: 'Member \'' . name . '\' in class \'' . classDef:name . '\' targets a ' . vis . ' ancestor member; ' . vis . ' members cannot be replaced or merged.';
				self:addError(line: m:line, msg: msg);
			} else if (anc:kind != m:kind) {
				local String is msg: 'Member \'' . name . '\' in class \'' . classDef:name . '\' is a ' . m:kind:value() . ' but the ancestor member it targets is a ' . anc:kind:value() . '.';
				self:addError(line: m:line, msg: msg);
			}
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
			if (anc:name != '') {
				anc:members:each(action: local Function(Member is m){
					if (m:kind == MemberKind:METHOD) {
						seenMethods:set(key: m:name, value: 'true');
					}
				});
			}
		});
		local Array of String is names: seenMethods:keys();
		names:each(action: local Function(String is mName){
			local Boolean is declaredLocally: false;
			classDef:members:each(action: local Function(Member is m){
				if (m:kind == MemberKind:METHOD && m:name == mName) {
					declaredLocally: true;
				}
			});
			if (!declaredLocally) {
				local Map of String to String is seen: Map:init();
				local Array of String is declarers: [];
				classDef:baseClasses:each(action: local Function(String is baseName){
					self:collectConcreteDeclarers(className: baseName, methodName: mName, seen: seen, acc: declarers);
				});
				local Array of String is maximal: [];
				declarers:each(action: local Function(String is d){
					local Boolean is isSubsumed: false;
					declarers:each(action: local Function(String is other){
						if (!isSubsumed && other != d && self:isSubclassOf(subName: other, baseName: d)) {
							isSubsumed: true;
						}
					});
					if (!isSubsumed) {
						maximal:add(item: d);
					}
				});
				if (maximal:length() >= 2) {
					local String is msg: 'ClassInfo \'' . classDef:name . '\' inherits conflicting implementations of \'' . mName . '\' from \'' . maximal:get(index: 0) . '\' and \'' . maximal:get(index: 1) . '\'; declare the method (replace or merge) to resolve the conflict.';
					self:addError(line: classDef:line, msg: msg);
				}
			}
		});
	}

	## Validates inheritance, interface contracts, and override signatures.
	##
	## @param classDef: Class to inspect.
	Function is checkInheritance(ClassInfo is classDef){
		self:currentSourceFile: classDef:sourceFile;
		local Boolean is hasInit: false;
		classDef:members:each(action: local Function(Member is m){
			if (m:name == ContractMethod:INIT:value()) {
				hasInit: true;
			}
		});

		classDef:baseClasses:each(action: local Function(String is baseName){
			local ClassInfo is parent: self:findClass(name: baseName);
			if (parent:name == baseName) {
				# 1. Enforce abstract member implementation on concrete classes
				# with init. The implicit root Any is exempt: its members carry
				# concrete defaults.
				if (hasInit && baseName != Primitive:ANY:value()) {
					parent:members:each(action: local Function(Member is parentM){
						local Boolean is isAbstract: (parentM:kind == MemberKind:FIELD && !parentM:hasInit) ||
							(parentM:kind == MemberKind:METHOD && parentM:body:length() == 0);
						if (isAbstract) {
							local MemberImplementLoop is chk: MemberImplementLoop:init(members: classDef:members, target: parentM);
							While:run(loop: chk);
							if (!chk:implemented) {
								local String is msg: 'ClassInfo \'' . classDef:name . '\' does not implement abstract member \'' . parentM:name . '\' required by parent \'' . baseName . '\'.';
								self:addError(line: classDef:line, msg: msg);
							}
						}
					});
				}

				# 2. Strict replace check & method signature matching on overrides
				classDef:members:each(action: local Function(Member is subM){
					# Declarative metadata (namespace/using/group) is per-class
					# by design and never participates in override matching.
					if (subM:name == MetadataField:NAMESPACE:value() || subM:name == MetadataField:USING:value() || subM:name == MetadataField:GROUP:value() || subM:name == MetadataField:CASTABLE:value()) {
						return;
					}
					parent:members:each(action: local Function(Member is parentM){
						if (subM:name == parentM:name) {
							if (parentM:hasModifier(kw: Keyword:LOCAL) || parentM:hasModifier(kw: Keyword:CONTAINED)) {
								local String is vis: if (parentM:hasModifier(kw: Keyword:LOCAL)) 'local' else 'contained';
								local String is msg: 'Member \'' . subM:name . '\' is ' . vis . ' in ancestor \'' . baseName . '\' and cannot be replaced or merged.';
								self:addError(line: subM:line, msg: msg);
							}
							local Boolean is hasReplace: subM:hasModifier(kw: Keyword:REPLACE);
							local Boolean is hasMerge: subM:hasModifier(kw: Keyword:MERGE);
							if (hasMerge) {
								if (subM:kind == MemberKind:METHOD) {
									if (parentM:kind == MemberKind:METHOD && parentM:body:length() == 0) {
										local String is msg: 'Cannot merge method \'' . subM:name . '\' in class \'' . classDef:name . '\' with abstract method from \'' . baseName . '\'.';
										self:addError(line: subM:line, msg: msg);
									}
								} else {
									self:applyMerge(classDef: classDef, subM: subM, parentM: parentM, baseName: baseName);
								}
							} else if (!hasReplace) {
								local String is msg: 'Member \'' . subM:name . '\' in class \'' . classDef:name . '\' overrides ancestor member from \'' . baseName . '\', but is missing \'replace\' modifier.';
								self:addError(line: subM:line, msg: msg);
							}

							if (subM:kind == MemberKind:METHOD && parentM:kind == MemberKind:METHOD) {
								# Root-contract carve-out: init/using/toString declared
								# in Any are name reservations; per-class signatures
								# are legitimate. Override must still carry replace.
								if (baseName == Primitive:ANY:value()) {
									if (!subM:hasModifier(kw: Keyword:REPLACE) && !subM:hasModifier(kw: Keyword:MERGE)) {
										local String is msg: 'Member \'' . subM:name . '\' in class \'' . classDef:name . '\' overrides root-contract member from \'Any\', but is missing \'replace\' modifier.';
										self:addError(line: subM:line, msg: msg);
									}
									return;
								}
								if (subM:params:length() != parentM:params:length()) {
									local String is msg: 'Method \'' . subM:name . '\' in class \'' . classDef:name . '\' parameter count mismatch with ancestor in \'' . baseName . '\'.';
									self:addError(line: subM:line, msg: msg);
								} else {
									local Int is pIdx: 0;
									subM:params:each(action: local Function(Parameter is subP){
										local Parameter is parentP: parentM:params:get(index: pIdx);
										if (subP:paramType:name == 'Any' || subP:paramType:name == '') {
											subP:paramType: parentP:paramType;
										}
										pIdx: pIdx + 1;
									});
								}
								local String is subRet: self:resolveReturnType(t: subM:memberType);
								local String is parentRet: self:resolveReturnType(t: parentM:memberType);
								if (subM:memberType:name == '' || self:isVoid(t: subM:memberType:name)) {
									subM:memberType: parentM:memberType;
								} else if (!self:isAssignable(target: subRet, source: parentRet)) {
									local String is msg: 'Method \'' . subM:name . '\' in class \'' . classDef:name . '\' return type \'' . subRet . '\' does not match ancestor return type \'' . parentRet . '\'.';
									self:addError(line: subM:line, msg: msg);
								}
							}
						}
					});
				});
			}
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
		if (subM:kind != MemberKind:FIELD) {
			self:addError(line: subM:line, msg: '\'merge\' is only valid on fields; member \'' . subM:name . '\' in class \'' . classDef:name . '\' is not a field.');
			return;
		}
		local String is typeName: subM:memberType:name;
		if (!typeName:startsWith(prefix: 'Array')) {
			self:addError(line: subM:line, msg: '\'merge\' requires an Array field; \'' . typeName . '\' is not mergeable.');
			return;
		}
		if (!parentM:hasInit) {
			return;
		}
		local Expression is parentInit: parentM:initExpr;
		if (parentInit:kind != ExpressionKind:ARRAY) {
			self:addError(line: subM:line, msg: '\'merge\' requires a constant array literal in parent \'' . baseName . '.' . parentM:name . '.');
			return;
		}
		if (!subM:hasInit) {
			return;
		}
		local Expression is childInit: subM:initExpr;
		if (childInit:kind != ExpressionKind:ARRAY) {
			self:addError(line: subM:line, msg: '\'merge\' requires a constant array literal initializer on \'' . classDef:name . '.' . subM:name . '.');
			return;
		}
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
			if (parent:name != '') {
				self:collectClassFieldTypes(classDef: parent);
			}
		});
		classDef:members:each(action: local Function(Member is m){
			# Metadata members carry no type and are not fields of the
			# generated struct.
			if (m:kind == MemberKind:FIELD && m:memberType:name != '') {
				self:fieldTypes:set(key: m:name, value: self:formatVarTypeString(t: m:memberType));
			}
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
					if (m:sourceFile != '') {
						self:currentSourceFile: m:sourceFile;
					}
					# Declarative metadata properties (using, namespace, group)
					# are loader directives, not checked code: their
					# initializers may reference classes the using itself
					# loads, so type validation is skipped.
					if (m:name != MetadataField:USING:value() && m:name != MetadataField:NAMESPACE:value() && m:name != MetadataField:GROUP:value() && m:name != MetadataField:CASTABLE:value()) {
						local String is declaredType: self:formatVarTypeString(t: m:memberType);
						if (m:hasInit) {
							# Bidirectional: the declared type flows in.
							local String is initType: self:inferExpressionType(expr: m:initExpr, expected: declaredType);
							if (!self:isAssignable(target: declaredType, source: initType)) {
								local String is msg: 'Type mismatch in field \'' . classDef:name . ':' . m:name . '\': cannot assign \'' . initType . '\' to \'' . declaredType . '\'.';
								self:addError(line: m:line, msg: msg);
							}
						}
					}
				}
				else: {}
			}
		});

		classDef:members:each(action: local Function(Member is m){
			when (m:kind) {
				is MemberKind:METHOD: {
					self:unassignedFields: Map:init();
					if (m:name == ContractMethod:INIT:value()) {
						classDef:members:each(action: local Function(Member is fm){
							if (fm:kind == MemberKind:FIELD && !fm:hasInit && fm:name != ContractMethod:USING:value()) {
								self:unassignedFields:set(key: fm:name, value: 'true');
							}
						});
					}
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
			if (m:name != 'using' || !m:hasInit || m:initExpr:kind != ExpressionKind:ARRAY) {
				return;
			}
			m:initExpr:arrayItems:each(action: local Function(Expression is item){
				if (item:kind != ExpressionKind:ARRAY) {
					return;
				}
				local Expression is asExpr: Expression:init(kind: ExpressionKind:UNKNOWN);
				item:arrayItems:each(action: local Function(Expression is seg){
					if (seg:kind == ExpressionKind:USING_AS) {
						asExpr: seg;
					}
				});
				if (asExpr:stringValue == '') {
					return;
				}
				local String is asName: asExpr:stringValue;
				if (seen:has(key: asName)) {
					self:addError(line: m:line, msg: 'Class \'' . classDef:name . '\' instance-imports \'' . asName . '\' more than once (INSTANCE.md E3).');
					return;
				}
				seen:set(key: asName, value: 'true');
				local ClassInfo is target: self:findClass(name: asName);
				if (target:name == '') {
					return;
				}
				if (target:baseClass == self:names:enumHeader()) {
					self:addError(line: m:line, msg: 'Cannot instance-import enum \'' . asName . '\'; enums are type-level (INSTANCE.md E2).');
					return;
				}
					if (target:typeParams:length() > 0) {
						self:addError(line: m:line, msg: 'Generic classes cannot be instance-imported yet (INSTANCE.md §10).');
						return;
					}
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
			if (m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) {
				m:initExpr:arrayItems:each(action: local Function(Expression is item){
					if (item:kind == ExpressionKind:ARRAY) {
						item:arrayItems:each(action: local Function(Expression is seg){
							if (seg:kind == ExpressionKind:USING_AS) {
								out:add(item: seg:stringValue);
							}
						});
					}
				});
			}
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
		if (state == 'b') {
			return;
		}
		if (state == 'g') {
			self:addError(line: 0, msg: 'Instance import cycle: ' . path . c:name . ' (INSTANCE.md E4); construction would recurse forever.');
			return;
		}
		color:set(key: c:name, value: 'g');
		local Array of String is targets: self:instanceImportTargets(classDef: c);
		targets:each(action: local Function(String is t){
			local ClassInfo is next: self:findClass(name: t);
			if (next:name != '') {
				self:visitImportNode(c: next, color: color, path: path . c:name . ' -> ');
			}
		});
		color:set(key: c:name, value: 'b');
	}

	Function of Array of TypeError is checkProgram(ProgramNode is program){
		self:errors: [];
		local Array of ClassInfo is flattened: [];
		program:classes:each(action: local Function(ClassInfo is c){
			self:collectClasses(c: c, acc: flattened);
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
			if (c:baseClass == self:names:enumHeader()) {
				self:allEnumNames:set(key: c:name, value: 'true');
				c:members:each(action: local Function(Member is m){
					# The namespace declaration is metadata, not a variant.
					if (m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) {
						return;
					}
					self:allEnumVariants:set(key: m:name, value: c:name);
					if (m:memberType:name == Primitive:STRING:value()) {
						self:allStringBackedEnums:set(key: c:name, value: 'true');
					}
				});
			}
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
