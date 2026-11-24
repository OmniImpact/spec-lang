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
	replace [String] is namespace: ['base', 'compiler', 'parser'];

	replace [[String]] is using: [
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
			Expression:ArrayLit: local Function of Boolean([Expression] is items){ return true; },
			else: { false }
		]);
	}

	local Function of Boolean is hasStaticMod(Member is m){
		local Boolean is found: false;
		while([Int is i: 0], { !found && i < m:modifiers:length() }, {
			if({ m:modifiers:get(index: i) == 'static' }, { found: true; });
			i++;
		});
		return found;
	}

	Function of ClassInfo is desugar(ClassInfo is c, String is backingType){
		local Boolean is isTagged: false;
		while([Int is mi: 0], { !isTagged && mi < c:members:length() }, {
			local Member is m: c:members:get(index: mi);
			local Boolean is isVariant: :hasStaticMod(m: m);
			if({ isVariant && m:params:length() > 0 }, {
				isTagged: true;
			});
			if({ !isVariant && !(m:hasInit && :isArrayExpr(expr: m:initExpr) && m:params:length() == 0) }, {
				isTagged: true;
			});
			mi++;
		});
		if({ isTagged }, {
			return :desugarTagged(c: c);
		});
		return :desugarValue(c: c, backingType: backingType);
	}

	## The tagged desugaring: the base carries the tag machinery, each
	## variant becomes a nested subclass with real payload fields.
	##
	## @param c: The parsed enum ClassInfo.
	## @return: The same ClassInfo, desugared.
	Function of ClassInfo is desugarTagged(ClassInfo is c){
		local String is name: c:name;
		local [Member] is out: [];
		local [Member] is variants: [];
		local [Member] is common: [];
		while([Int is mi: 0], { mi < c:members:length() }, {
			local Member is m: c:members:get(index: mi);
			if({ m:hasInit && :isArrayExpr(expr: m:initExpr) && m:params:length() == 0 }, {
				out:push(item: m);
			}, {
				if({ :hasStaticMod(m: m) }, {
					variants:push(item: m);
				}, {
					common:push(item: m);
				});
			});
			mi++;
		});

		# The tag machinery: the base's fields and the reflective readers.
		local Member is tagField: Member(kind: MemberKind:FIELD);
		tagField:memberType: Type(name: 'Int');
		tagField:name: '_tag';
		out:push(item: tagField);
		local Member is vnameField: Member(kind: MemberKind:FIELD);
		vnameField:memberType: Type(name: 'String');
		vnameField:name: '_variant_name';
		out:push(item: vnameField);
		local Member is nameFn: Member(kind: MemberKind:METHOD);
		nameFn:modifiers: ['replace'];
		nameFn:memberType: Type(name: 'String');
		nameFn:name: 'name';
		local [Statement] is nameBody: [];
		nameBody:push(item: :tailReturn(expr: :selfPath(member: '_variant_name')));
		nameFn:body: nameBody;
		out:push(item: nameFn);
		local Member is ordFn: Member(kind: MemberKind:METHOD);
		ordFn:modifiers: ['replace'];
		ordFn:memberType: Type(name: 'Int');
		ordFn:name: 'ordinal';
		local [Statement] is ordBody: [];
		ordBody:push(item: :tailReturn(expr: :selfPath(member: '_tag')));
		ordFn:body: ordBody;
		out:push(item: ordFn);

		# Shared product members (common fields and methods).
		while([Int is ci: 0], { ci < common:length() }, {
			out:push(item: common:get(index: ci));
			ci++;
		});

		# The variants: nested subclasses carrying real payload fields,
		# their constructors stamping the tag and the variant name.
		while([Int is idx: 0], { idx < variants:length() }, {
			local Member is m: variants:get(index: idx);
			local ClassInfo is sub: ClassInfo(name: m:name, baseClass: name, members: []);
			sub:setLine(line: m:line);
			sub:setSourceFile(file: c:sourceFile);
			local [Member] is subMembers: [];
			while([Int is pi: 0], { pi < m:params:length() }, {
				local Parameter is p: m:params:get(index: pi);
				local Member is pf: Member(kind: MemberKind:FIELD);
				pf:memberType: p:paramType;
				pf:name: p:name;
				subMembers:push(item: pf);
				pi++;
			});
			local Member is subInit: Member(kind: MemberKind:METHOD);
			subInit:memberType: Type(name: '');
			subInit:name: 'init';
			subInit:params: m:params;
			# Generic enums: the nested variant checks as its own class, so it
			# carries the root's type parameters — payload field types bound
			# to them pass validation and substitute at instantiation.
			sub:setTypeParams(params: c:typeParams);
			local [Statement] is initBody: [];
			while([Int is pi: 0], { pi < m:params:length() }, {
				local Parameter is p: m:params:get(index: pi);
				local Statement is a: Statement:Assign(assignTarget: :selfPath(member: p:name), assignValue: :ident(name: p:name));
				initBody:push(item: a);
				pi++;
			});
			local Expression is tagNum: Expression:NumberLit(value: idx, text: '' . idx);
			local Statement is tagAssign: Statement:Assign(assignTarget: :selfPath(member: '_tag'), assignValue: tagNum);
			initBody:push(item: tagAssign);
			local Statement is vnameAssign: Statement:Assign(assignTarget: :selfPath(member: '_variant_name'), assignValue: :strLit(text: m:name));
			initBody:push(item: vnameAssign);
			subInit:body: initBody;
			subMembers:push(item: subInit);
			sub:members: subMembers;
			local Member is nest: Member(kind: MemberKind:CLASS);
			nest:name: m:name;
			nest:nestedClass: sub;
			nest:line: m:line;
			out:push(item: nest);
			idx++;
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
		local [Member] is out: [];
		local [Member] is variants: [];
		local [Member] is common: [];
		# Loader directives (array-valued members) stay plain members;
		# variants collect for the held rewrite; common members preserved.
		while([Int is mi: 0], { mi < c:members:length() }, {
			local Member is m: c:members:get(index: mi);
			if({ m:hasInit && :isArrayExpr(expr: m:initExpr) && m:params:length() == 0 }, {
				out:push(item: m);
			}, {
				if({ :hasStaticMod(m: m) }, {
					variants:push(item: m);
				}, {
					common:push(item: m);
				});
			});
			mi++;
		});

		# The synthesized contract methods call `Conditional:if` — the
		# class gains the as-import (the standard Conditional grant).
		local Member is using: Member(kind: MemberKind:FIELD);
		local Type is usingInner: Type(name: 'List');
		usingInner:params: [Type(name: 'String')];
		local Type is usingType: Type(name: 'List');
		usingType:params: [usingInner];
		using:memberType: usingType;
		using:name: 'using';
		local [Expression] is entryItems: [];
		entryItems:push(item: :strLit(text: 'base'));
		entryItems:push(item: :strLit(text: 'sys'));
		local [NamedArg] is emptyAsArgs: [];
		local Expression is asFn: Expression:UsingAs(className: 'Conditional', args: emptyAsArgs);
		entryItems:push(item: asFn);
		local Expression is entry: Expression:ArrayLit(items: entryItems);
		local [Expression] is usingItems: [entry];
		local Expression is usingArr: Expression:ArrayLit(items: usingItems);
		using:initExpr: usingArr;
		using:hasInit: true;
		out:push(item: using);

		# The synthesized backing field and constructor: the tag travels
		# as the instance's own data.
		local Member is backing: Member(kind: MemberKind:FIELD);
		backing:memberType: Type(name: backingType);
		backing:name: '_backing';
		out:push(item: backing);

		local Member is ctor: Member(kind: MemberKind:METHOD);
		ctor:memberType: Type(name: '');
		ctor:name: 'init';
		local [Parameter] is ctorParams: [];
		local Parameter is cp: Parameter(name: 'v', paramType: Type(name: backingType));
		ctorParams:push(item: cp);
		ctor:params: ctorParams;
		local [Statement] is ctorBody: [];
		local Statement is assign: Statement:Assign(assignTarget: :selfPath(member: '_backing'), assignValue: :ident(name: 'v'));
		ctorBody:push(item: assign);
		ctor:body: ctorBody;
		out:push(item: ctor);

		# The variants: held members holding instances constructed with
		# their tags. Untagged variants keep their ordinal-as-tag.
		while([Int is vi: 0], { vi < variants:length() }, {
			local Member is m: variants:get(index: vi);
			local Member is hv: Member(kind: MemberKind:FIELD);
			hv:modifiers: ['held'];
			hv:memberType: Type(name: name);
			hv:name: m:name;
			hv:initExpr: :ctorCall(enumName: name, tagExpr: m:initExpr);
			hv:hasInit: true;
			hv:line: m:line;
			out:push(item: hv);
			vi++;
		});

		# The contract methods, synthesized from the variant list.
		# name/ordinal are NOT synthesized: the Enum root implements the
		# identity scan reflectively over the held metadata (the variants
		# are the held fields in declaration order), and every desugared
		# enum inherits it.
		out:push(item: :synthValue(backingType: backingType));
		out:push(item: :synthOf(name: name, backingType: backingType, variants: variants));
		out:push(item: :synthValues(name: name, variants: variants));
		# The sugar's render contract: variants render their NAME (the
		# legacy emission's behavior), not the default TypeName@hash.
		local [Statement] is tsBody: [];
		while([Int is vi: 0], { vi < variants:length() }, {
			local Member is v: variants:get(index: vi);
			local Expression is cond: :eq(left: :ident(name: ':'), right: :variantRef(enumName: name, variant: v:name));
			tsBody:push(item: :guardIf(cond: cond, val: :strLit(text: v:name)));
			vi++;
		});
		tsBody:push(item: :tailReturn(expr: :strLit(text: name)));
		out:push(item: :synthToString(body: tsBody));

		while([Int is ci: 0], { ci < common:length() }, {
			out:push(item: common:get(index: ci));
			ci++;
		});

		c:members: out;
		return c;
	}

	## Builds `Name:init(tag)` — the variant's holding initializer.
	Function of Expression is ctorCall(String is enumName, Expression is tagExpr){
		local [NamedArg] is args: [];
		args:push(item: NamedArg(name: '', value: tagExpr));
		return Expression:Call(call: CallData(target: :ident(name: enumName), name: 'init', args: args));
	}

	Function of Expression is ident(String is name){
		return Expression:Ident(name: name);
	}

	Function of Expression is selfPath(String is member){
		return Expression:Path(segments: [':', member]);
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
	Function of [Statement] is returnBody(Expression is expr){
		local [Statement] is body: [];
		local Statement is r: Statement:Return(returnExpr: expr, hasReturnExpr: true);
		body:push(item: r);
		return body;
	}

	## Builds `if({ <cond> }, { return <val>; });`
	## as an expression statement.
	Function of Statement is guardIf(Expression is cond, Expression is val){
		local [NamedArg] is args: [];
		local [Parameter] is emptyParams: [];
		local Expression is checkFn: Expression:AnonFn(returnType: Type(name: ''), params: emptyParams, body: :returnBody(expr: cond));
		args:push(item: NamedArg(name: 'check', value: checkFn));
		local Expression is thenFn: Expression:AnonFn(returnType: Type(name: ''), params: emptyParams, body: :returnBody(expr: val));
		args:push(item: NamedArg(name: 'then', value: thenFn));
		local Expression is call: Expression:Call(call: CallData(target: :ident(name: 'Conditional'), name: 'if', args: args));
		local Statement is s: Statement:Expr(exprStmt: call);
		return s;
	}

	## value(): the backing tag rides the instance.
	Function of Member is synthValue(String is backingType){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:memberType: Type:init(name: backingType);
		m:name: 'value';
		local [Statement] is body: [];
		body:push(item: :tailReturn(expr: :selfPath(member: '_backing')));
		m:body: body;
		return m;
	}

	## of(v): the reverse lookup over the tags; the first variant is the
	## no-match default (the sugar's historical empty-tag default).
	## HELD: the class-name dispatch is receiver-free.
	Function of Member is synthOf(String is name, String is backingType, [Member] is variants){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:modifiers: ['held'];
		m:memberType: Type:init(name: name);
		m:name: 'of';
		local [Parameter] is params: [];
		# The parameter is 'value' — the sugar's call convention
		# (Color:of(value: ...)). The call-argument formatter matches
		# call-site names against parameter names, so any other spelling
		# drops the argument and every lookup degenerates to the
		# no-match default.
		params:push(item: Parameter(name: 'value', paramType: Type(name: backingType)));
		m:params: params;
		local [Statement] is body: [];
		local Member is first: variants:get(index: 0);
		while([Int is vi: 0], { vi < variants:length() }, {
			local Member is v: variants:get(index: vi);
			local Expression is cond: :eq(left: :ident(name: 'value'), right: v:initExpr);
			body:push(item: :guardIf(cond: cond, val: :variantRef(enumName: name, variant: v:name)));
			vi++;
		});
		body:push(item: :tailReturn(expr: :variantRef(enumName: name, variant: first:name)));
		m:body: body;
		return m;
	}

	## toString(): the variant name — the sugar's render contract. The
	## name() dispatch needs the variants, so the caller wires the body.
	Function of Member is synthToString([Statement] is body){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:modifiers: ['replace'];
		m:memberType: Type:init(name: 'String');
		m:name: 'toString';
		m:body: body;
		return m;
	}

	## values(): the instances in declaration order. HELD: receiver-free.
	Function of Member is synthValues(String is name, [Member] is variants){
		local Member is m: Member:init(kind: MemberKind:METHOD);
		m:modifiers: ['held'];
		local Type is listT: Type(name: 'List');
		listT:params: [Type(name: name)];
		m:memberType: listT;
		m:name: 'values';
		local [Statement] is body: [];
		local Type is declT: Type(name: 'List');
		declT:params: [Type(name: name)];
		local [Expression] is emptyItems: [];
		local Statement is decl: Statement:VarDecl(modifiers: ['local'], varType: declT, varName: 'all', initExpr: Expression:ArrayLit(items: emptyItems), hasInit: true);
		body:push(item: decl);
		while([Int is vi: 0], { vi < variants:length() }, {
			local Member is v: variants:get(index: vi);
			local [NamedArg] is args: [];
			args:push(item: NamedArg(name: 'item', value: :variantRef(enumName: name, variant: v:name)));
			local Expression is call: Expression:Call(call: CallData(target: :ident(name: 'all'), name: 'push', args: args));
			local Statement is s: Statement:Expr(exprStmt: call);
			body:push(item: s);
			vi++;
		});
		body:push(item: :tailReturn(expr: :ident(name: 'all')));
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
