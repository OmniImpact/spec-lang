#! Package base:compiler:parser
#! Desugars a VALUE enum (variants without payloads) into the class
#! model: the variants become HELD members holding
#! enum instances constructed with their tags, the backing value rides
#! a synthesized instance field, and the per-enum contract methods
#! (value/of/values/toString) are synthesized as plain Spec members.
#! name/ordinal are NOT synthesized — the Enum root implements the
#! identity scan reflectively over the held metadata. The tagged shape
#! (variants with parameters) desugars to nested subclasses whose
#! field-reader name/ordinal replace the root's reflective scan.

Class is EnumDesugar{
	namespace: ['base', 'compiler', 'parser'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'sys', as Conditional()]
	];

	## Rewrites a parsed enum into its class-model form, in place.
	## Value enums (payload-less variants) desugar to held members; tagged
	## enums (variants with parameters) desugar to nested subclasses —
	## the payload fields are real fields, the base carries the tag
	## machinery, and the variant constructors resolve as nested-class
	## construction shorthand (`Result:Ok(data: 'x')`).
	##
	## @param c: The parsed enum ClassInfo (baseClass stays the enum root).
	## @param backingType: The sugar's `of` type (Int when unspelled).
	## @return: The same ClassInfo, desugared.
	Function of Boolean is isArrayExpr(Expression is expr){
		return match(on: expr, when: [
			Expression:ArrayLit: local Function of Boolean(Array of Expression is items){ return true; },
			else: { false }
		]);
	}

	Function of ClassInfo is desugar(ClassInfo is c, String is backingType){
		local Boolean is isTagged: false;
		c:members:each(action: local Function(Member is m){
			local Boolean is isVariant: m:modifiers:indexOf(search: 'static', default: -1) >= 0;
			if({ isVariant && m:params:length() > 0 }, {
				isTagged: true;
			});
			if({ !isVariant && !(m:hasInit && self:isArrayExpr(expr: m:initExpr) && m:params:length() == 0) }, {
				isTagged: true;
			});
		});
		if({ isTagged }, {
			return self:desugarTagged(c: c);
		});
		return self:desugarValue(c: c, backingType: backingType);
	}

	## The tagged desugaring: the base carries the tag machinery, each
	## variant becomes a nested subclass with real payload fields.
	##
	## @param c: The parsed enum ClassInfo.
	## @return: The same ClassInfo, desugared.
	Function of ClassInfo is desugarTagged(ClassInfo is c){
		local String is name: c:name;
		local Array of Member is out: [];
		local Array of Member is variants: [];
		local Array of Member is common: [];
		c:members:each(action: local Function(Member is m){
			if({ m:hasInit && self:isArrayExpr(expr: m:initExpr) && m:params:length() == 0 }, {
				out:add(item: m);
			}, {
				if({ m:modifiers:indexOf(search: 'static', default: -1) >= 0 }, {
					variants:add(item: m);
				}, {
					common:add(item: m);
				});
			});
		});

		# The tag machinery: the base's fields and the reflective readers.
		local Member is tagField: Member:init(kind: MemberKind:FIELD);
		tagField:memberType: Type:init(name: 'Int');
		tagField:name: '_tag';
		out:add(item: tagField);
		local Member is vnameField: Member:init(kind: MemberKind:FIELD);
		vnameField:memberType: Type:init(name: 'String');
		vnameField:name: '_variant_name';
		out:add(item: vnameField);
		local Member is nameFn: Member:init(kind: MemberKind:METHOD);
		nameFn:modifiers: ['replace'];
		nameFn:memberType: Type:init(name: 'String');
		nameFn:name: 'name';
		local Array of Statement is nameBody: [];
		nameBody:add(item: self:tailReturn(expr: self:selfPath(member: '_variant_name')));
		nameFn:body: nameBody;
		out:add(item: nameFn);
		local Member is ordFn: Member:init(kind: MemberKind:METHOD);
		ordFn:modifiers: ['replace'];
		ordFn:memberType: Type:init(name: 'Int');
		ordFn:name: 'ordinal';
		local Array of Statement is ordBody: [];
		ordBody:add(item: self:tailReturn(expr: self:selfPath(member: '_tag')));
		ordFn:body: ordBody;
		out:add(item: ordFn);

		# Shared product members (common fields and methods).
		common:each(action: local Function(Member is cm){
			out:add(item: cm);
		});

		# The variants: nested subclasses carrying real payload fields,
		# their constructors stamping the tag and the variant name.
		local Int is idx: 0;
		variants:each(action: local Function(Member is m){
			local ClassInfo is sub: ClassInfo:init(name: m:name, baseClass: name, members: []);
			sub:setLine(line: m:line);
			sub:setSourceFile(file: c:sourceFile);
			local Array of Member is subMembers: [];
			m:params:each(action: local Function(Parameter is p){
				local Member is pf: Member:init(kind: MemberKind:FIELD);
				pf:memberType: p:paramType;
				pf:name: p:name;
				subMembers:add(item: pf);
			});
			local Member is subInit: Member:init(kind: MemberKind:METHOD);
			subInit:memberType: Type:init(name: '');
			subInit:name: 'init';
			subInit:params: m:params;
			local Array of Statement is initBody: [];
			m:params:each(action: local Function(Parameter is p){
				local Statement is a: Statement:Assign(assignTarget: self:selfPath(member: p:name), assignValue: self:ident(name: p:name));
				initBody:add(item: a);
			});
			local Expression is tagNum: Expression:NumberLit(value: idx, text: '' . idx);
			local Statement is tagAssign: Statement:Assign(assignTarget: self:selfPath(member: '_tag'), assignValue: tagNum);
			initBody:add(item: tagAssign);
			local Statement is vnameAssign: Statement:Assign(assignTarget: self:selfPath(member: '_variant_name'), assignValue: self:strLit(text: m:name));
			initBody:add(item: vnameAssign);
			subInit:body: initBody;
			subMembers:add(item: subInit);
			sub:members: subMembers;
			local Member is nest: Member:init(kind: MemberKind:CLASS);
			nest:name: m:name;
			nest:nestedClass: sub;
			nest:line: m:line;
			out:add(item: nest);
			idx: idx + 1;
		});

		c:members: out;
		return c;
	}

	## The value-enum desugaring.
	##
	## @param c: The parsed enum ClassInfo.
	## @param backingType: The sugar's `of` type (Int when unspelled).
	## @return: The same ClassInfo, desugared.
	Function of ClassInfo is desugarValue(ClassInfo is c, String is backingType){
		local String is name: c:name;
		local Array of Member is out: [];
		local Array of Member is variants: [];
		local Array of Member is common: [];
		# Loader directives (array-valued members) stay plain members;
		# variants collect for the held rewrite; common members preserved.
		c:members:each(action: local Function(Member is m){
			if({ m:hasInit && self:isArrayExpr(expr: m:initExpr) && m:params:length() == 0 }, {
				out:add(item: m);
			}, {
				if({ m:modifiers:indexOf(search: 'static', default: -1) >= 0 }, {
					variants:add(item: m);
				}, {
					common:add(item: m);
				});
			});
		});

		# The synthesized contract methods call `Conditional:if` — the
		# class gains the as-import (the standard Conditional grant).
		local Member is using: Member:init(kind: MemberKind:FIELD);
		using:memberType: Type:init(name: '');
		using:name: 'using';
		local Array of Expression is entryItems: [];
		entryItems:add(item: self:strLit(text: 'base'));
		entryItems:add(item: self:strLit(text: 'sys'));
		local Expression is asFn: Expression:UsingAs(className: 'Conditional', args: []);
		entryItems:add(item: asFn);
		local Expression is entry: Expression:ArrayLit(items: entryItems);
		local Array of Expression is usingItems: [entry];
		local Expression is usingArr: Expression:ArrayLit(items: usingItems);
		using:initExpr: usingArr;
		using:hasInit: true;
		out:add(item: using);

		# The synthesized backing field and constructor: the tag travels
		# as the instance's own data.
		local Member is backing: Member:init(kind: MemberKind:FIELD);
		backing:memberType: Type:init(name: backingType);
		backing:name: '_backing';
		out:add(item: backing);

		local Member is ctor: Member:init(kind: MemberKind:METHOD);
		ctor:memberType: Type:init(name: '');
		ctor:name: 'init';
		local Array of Parameter is ctorParams: [];
		local Parameter is cp: Parameter:init(name: 'v', paramType: Type:init(name: backingType));
		ctorParams:add(item: cp);
		ctor:params: ctorParams;
		local Array of Statement is ctorBody: [];
		local Statement is assign: Statement:Assign(assignTarget: self:selfPath(member: '_backing'), assignValue: self:ident(name: 'v'));
		ctorBody:add(item: assign);
		ctor:body: ctorBody;
		out:add(item: ctor);

		# The variants: held members holding instances constructed with
		# their tags. Untagged variants keep their ordinal-as-tag.
		variants:each(action: local Function(Member is m){
			local Member is hv: Member:init(kind: MemberKind:FIELD);
			hv:modifiers: ['held'];
			hv:memberType: Type:init(name: name);
			hv:name: m:name;
			hv:initExpr: self:ctorCall(enumName: name, tagExpr: m:initExpr);
			hv:hasInit: true;
			hv:line: m:line;
			out:add(item: hv);
		});

		# The contract methods, synthesized from the variant list.
		# name/ordinal are NOT synthesized: the Enum root implements the
		# identity scan reflectively over the held metadata (the variants
		# are the held fields in declaration order), and every desugared
		# enum inherits it.
		out:add(item: self:synthValue(backingType: backingType));
		out:add(item: self:synthOf(name: name, backingType: backingType, variants: variants));
		out:add(item: self:synthValues(name: name, variants: variants));
		# The sugar's render contract: variants render their NAME (the
		# legacy emission's behavior), not the default TypeName@hash.
		local Array of Statement is tsBody: [];
		variants:each(action: local Function(Member is v){
			local Expression is cond: self:eq(left: self:ident(name: 'self'), right: self:variantRef(enumName: name, variant: v:name));
			tsBody:add(item: self:guardIf(cond: cond, val: self:strLit(text: v:name)));
		});
		tsBody:add(item: self:tailReturn(expr: self:strLit(text: name)));
		out:add(item: self:synthToString(body: tsBody));

		common:each(action: local Function(Member is cm){
			out:add(item: cm);
		});

		c:members: out;
		return c;
	}

	## Builds `Name:init(tag)` — the variant's holding initializer.
	Function of Expression is ctorCall(String is enumName, Expression is tagExpr){
		local Array of NamedArg is args: [];
		args:add(item: NamedArg:init(name: '', value: tagExpr));
		return Expression:Call(call: CallData:init(target: self:ident(name: enumName), name: 'init', args: args));
	}

	Function of Expression is ident(String is name){
		return Expression:Ident(name: name);
	}

	Function of Expression is selfPath(String is member){
		return Expression:Path(segments: ['self', member]);
	}

	## Builds `Name:Variant` — the qualified held reference.
	Function of Expression is variantRef(String is enumName, String is variant){
		return Expression:Path(segments: [enumName, variant]);
	}

	## Builds the equality `left == right`.
	Function of Expression is eq(Expression is left, Expression is right){
		return Expression:Binary(op: '==', left: left, right: right);
	}

	## Builds `{ return <expr>; }` — the single-statement closure body.
	Function of Array of Statement is returnBody(Expression is expr){
		local Array of Statement is body: [];
		local Statement is r: Statement:Return(returnExpr: expr, hasReturnExpr: true);
		body:add(item: r);
		return body;
	}

	## Builds `if({ <cond> }, { return <val>; });`
	## as an expression statement.
	Function of Statement is guardIf(Expression is cond, Expression is val){
		local Array of NamedArg is args: [];
		local Expression is checkFn: Expression:AnonFn(returnType: Type:init(name: ''), params: [], body: self:returnBody(expr: cond));
		args:add(item: NamedArg:init(name: 'check', value: checkFn));
		local Expression is thenFn: Expression:AnonFn(returnType: Type:init(name: ''), params: [], body: self:returnBody(expr: val));
		args:add(item: NamedArg:init(name: 'then', value: thenFn));
		local Expression is call: Expression:Call(call: CallData:init(target: self:ident(name: 'Conditional'), name: 'if', args: args));
		local Statement is s: Statement:Expr(exprStmt: call);
		return s;
	}

	## name(): the identity scan over the variants.
	Function of Member is synthName(String is name, Array of Member is variants){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:memberType: Type:init(name: 'String');
		m:name: 'name';
		local Array of Statement is body: [];
		variants:each(action: local Function(Member is v){
			local Expression is cond: self:eq(left: self:ident(name: 'self'), right: self:variantRef(enumName: name, variant: v:name));
			body:add(item: self:guardIf(cond: cond, val: self:strLit(text: v:name)));
		});
		body:add(item: self:tailReturn(expr: self:strLit(text: '')));
		m:body: body;
		return m;
	}

	## ordinal(): the declaration-order index.
	Function of Member is synthOrdinal(String is name, Array of Member is variants){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:memberType: Type:init(name: 'Int');
		m:name: 'ordinal';
		local Array of Statement is body: [];
		local Int is idx: 0;
		variants:each(action: local Function(Member is v){
			local Expression is cond: self:eq(left: self:ident(name: 'self'), right: self:variantRef(enumName: name, variant: v:name));
			local Expression is num: Expression:NumberLit(value: idx, text: '' . idx);
			body:add(item: self:guardIf(cond: cond, val: num));
			idx: idx + 1;
		});
		local Expression is none: Expression:NumberLit(value: -1, text: '-1');
		body:add(item: self:tailReturn(expr: none));
		m:body: body;
		return m;
	}

	## value(): the backing tag rides the instance.
	Function of Member is synthValue(String is backingType){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:memberType: Type:init(name: backingType);
		m:name: 'value';
		local Array of Statement is body: [];
		body:add(item: self:tailReturn(expr: self:selfPath(member: '_backing')));
		m:body: body;
		return m;
	}

	## of(v): the reverse lookup over the tags; the first variant is the
	## no-match default (the sugar's historical empty-tag default).
	## HELD: the class-name dispatch is receiver-free.
	Function of Member is synthOf(String is name, String is backingType, Array of Member is variants){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:modifiers: ['held'];
		m:memberType: Type:init(name: name);
		m:name: 'of';
		local Array of Parameter is params: [];
		# The parameter is 'value' — the sugar's call convention
		# (Color:of(value: ...)). The call-argument formatter matches
		# call-site names against parameter names, so any other spelling
		# drops the argument and every lookup degenerates to the
		# no-match default.
		params:add(item: Parameter:init(name: 'value', paramType: Type:init(name: backingType)));
		m:params: params;
		local Array of Statement is body: [];
		local Member is first: variants:get(index: 0);
		variants:each(action: local Function(Member is v){
			local Expression is cond: self:eq(left: self:ident(name: 'value'), right: v:initExpr);
			body:add(item: self:guardIf(cond: cond, val: self:variantRef(enumName: name, variant: v:name)));
		});
		body:add(item: self:tailReturn(expr: self:variantRef(enumName: name, variant: first:name)));
		m:body: body;
		return m;
	}

	## toString(): the variant name — the sugar's render contract. The
	## name() dispatch needs the variants, so the caller wires the body.
	Function of Member is synthToString(Array of Statement is body){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:modifiers: ['replace'];
		m:memberType: Type:init(name: 'String');
		m:name: 'toString';
		m:body: body;
		return m;
	}

	## values(): the instances in declaration order. HELD: receiver-free.
	Function of Member is synthValues(String is name, Array of Member is variants){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:modifiers: ['held'];
		m:memberType: Type:init(name: 'Array of ' . name);
		m:name: 'values';
		local Array of Statement is body: [];
		local Statement is decl: Statement:VarDecl(modifiers: ['local'], varType: Type:init(name: 'Array of ' . name), varName: 'all', initExpr: Expression:ArrayLit(items: []), hasInit: true);
		body:add(item: decl);
		variants:each(action: local Function(Member is v){
			local Array of NamedArg is args: [];
			args:add(item: NamedArg:init(name: 'item', value: self:variantRef(enumName: name, variant: v:name)));
			local Expression is call: Expression:Call(call: CallData:init(target: self:ident(name: 'all'), name: 'add', args: args));
			local Statement is s: Statement:Expr(exprStmt: call);
			body:add(item: s);
		});
		body:add(item: self:tailReturn(expr: self:ident(name: 'all')));
		m:body: body;
		return m;
	}

	Function of Expression is strLit(String is text){
		return Expression:StringLit(value: text);
	}

	## The final `return <expr>;` of a synthesized body.
	Function of Statement is tailReturn(Expression is expr){
		local Statement is r: Statement:Return(returnExpr: expr, hasReturnExpr: true);
		return r;
	}
}
