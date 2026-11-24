#! Package speclint:rules
#! Warns when an explicit `as` cast narrows width, changes signedness in a
#! potentially lossy direction, or truncates floating-point precision.
#! Lossless widening casts (e.g. Byte/UInt8 -> Int, Float32 -> Float) and
#! in-range numeric literals produce no warning or notice.

Class of LintRule is NarrowingCastRule{
	replace [String] is namespace: ['speclint', 'rules'];

	replace [[String]] is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Expression],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Map of String to String is fieldTypes: Map:init();
	local Map of String to String is localTypes: Map:init();

	replace Function of String is id(){
		return 'narrowing-cast';
	}

	replace Function of String is description(){
		return 'Warns on explicit numeric casts that may lose precision or sign; lossless widening casts stay silent.';
	}

	replace Function of Boolean is isWarning(){
		return true;
	}

	local Function of Int is intBitWidth(Primitive is p){
		return match(on: p, when: [
			[Primitive:INT8, Primitive:BYTE, Primitive:UINT8]: { 8 },
			[Primitive:INT16, Primitive:UINT16]: { 16 },
			[Primitive:INT32, Primitive:UINT32, Primitive:RUNE]: { 32 },
			[Primitive:INT, Primitive:UINT64, Primitive:ISIZE, Primitive:USIZE]: { 64 },
			[Primitive:INT128, Primitive:UINT128]: { 128 },
			else: { 0 }
		]);
	}

	local Function of Boolean is isSignedIntPrim(Primitive is p){
		return p == Primitive:INT8 || p == Primitive:INT16 || p == Primitive:INT32 || p == Primitive:INT || p == Primitive:INT128 || p == Primitive:ISIZE;
	}

	local Function of Boolean is isUnsignedIntPrim(Primitive is p){
		return p == Primitive:BYTE || p == Primitive:UINT8 || p == Primitive:UINT16 || p == Primitive:UINT32 || p == Primitive:UINT64 || p == Primitive:UINT128 || p == Primitive:USIZE || p == Primitive:RUNE;
	}

	local Function of Boolean is isFloatPrim(Primitive is p){
		return p == Primitive:FLOAT32 || p == Primitive:FLOAT;
	}

	local Function of Boolean is literalFitsIn(Int is val, Primitive is dst){
		return match(on: dst, when: [
			[Primitive:BYTE, Primitive:UINT8]: { val >= 0 && val <= 255 },
			Primitive:INT8: { val >= -128 && val <= 127 },
			Primitive:UINT16: { val >= 0 && val <= 65535 },
			Primitive:INT16: { val >= -32768 && val <= 32767 },
			Primitive:UINT32: { val >= 0 && val <= 4294967295 },
			Primitive:INT32: { val >= -2147483648 && val <= 2147483647 },
			Primitive:RUNE: { val >= 0 && val <= 1114111 },
			[Primitive:UINT64, Primitive:USIZE, Primitive:UINT128]: { val >= 0 },
			[Primitive:INT, Primitive:ISIZE, Primitive:INT128, Primitive:FLOAT, Primitive:FLOAT32]: { true },
			else: { true }
		]);
	}

	## True when casting from [src] to [dst] is guaranteed lossless (widening or identical).
	local Function of Boolean is isLosslessWidening(Primitive is src, Primitive is dst){
		if({ src == dst }, { return true; });
		local Boolean is sSigned: :isSignedIntPrim(p: src);
		local Boolean is dSigned: :isSignedIntPrim(p: dst);
		local Boolean is sUnsigned: :isUnsignedIntPrim(p: src);
		local Boolean is dUnsigned: :isUnsignedIntPrim(p: dst);
		local Boolean is sFloat: :isFloatPrim(p: src);
		local Boolean is dFloat: :isFloatPrim(p: dst);
		local Int is sBits: :intBitWidth(p: src);
		local Int is dBits: :intBitWidth(p: dst);

		if({ sSigned && dSigned }, { return dBits >= sBits; });
		if({ sUnsigned && dUnsigned }, { return dBits >= sBits; });
		if({ sUnsigned && dSigned }, { return dBits > sBits; });
		if({ sSigned && dUnsigned }, { return false; });
		if({ (sSigned || sUnsigned) && dFloat }, {
			if({ dst == Primitive:FLOAT32 }, { return sBits <= 16; });
			return sBits <= 32;
		});
		if({ sFloat && dFloat }, {
			return src == Primitive:FLOAT32 && dst == Primitive:FLOAT;
		});
		if({ sFloat && (dSigned || dUnsigned) }, { return false; });
		return true;
	}

	local Function of String is inferExprTypeName(Expression is expr){
		return match(on: expr, when: [
			Expression:NumberLit: local Function of String(Int is _v, String is _t){ return Primitive:INT:value(); },
			Expression:FloatLit: local Function of String(String is _t){ return Primitive:FLOAT:value(); },
			Expression:Ident: local Function of String(String is name){
				if({ :localTypes:has(key: name) }, { return :localTypes:get(key: name, default: ''); });
				if({ :fieldTypes:has(key: name) }, { return :fieldTypes:get(key: name, default: ''); });
				return '';
			},
			Expression:Cast: local Function of String(Expression is _inner, String is target, [Expression] is _args){
				return target;
			},
			Expression:Unary: local Function of String(String is op, Expression is operand){
				if({ op == '-' || op == '~' }, { return :inferExprTypeName(expr: operand); });
				return '';
			},
			else: { '' }
		]);
	}

	replace Function is checkClass(ClassInfo is classDef, [LintIssue] is issues){
		local Map of String to String is savedFields: :fieldTypes;
		:fieldTypes: Map();
		while([Int is mi: 0], { mi < classDef:members:length() }, {
			local Member is m: classDef:members:get(index: mi);
			if({ m:kind == MemberKind:FIELD }, {
				:fieldTypes:set(key: m:name, value: m:memberType:name);
			});
			mi++;
		});
		while([Int is mi: 0], { mi < classDef:members:length() }, {
			local Member is m: classDef:members:get(index: mi);
			match(on: m:kind, when: [
				MemberKind:FIELD: {
					if({ m:hasInit }, {
						:checkExpression(expr: m:initExpr, issues: issues);
					});
				},
				MemberKind:METHOD: {
					local Map of String to String is savedLocals: :localTypes;
					:localTypes: Map();
					while([Int is pi: 0], { pi < m:params:length() }, {
						local Parameter is p: m:params:get(index: pi);
						:localTypes:set(key: p:name, value: p:paramType:name);
						pi++;
					});
					while([Int is si: 0], { si < m:body:length() }, {
						:checkStatement(stmt: m:body:get(index: si), issues: issues);
						si++;
					});
					:localTypes: savedLocals;
				},
				MemberKind:CLASS: {
					:checkClass(classDef: m:nestedClass, issues: issues);
				},
				else: {}
			]);
			mi++;
		});
		:fieldTypes: savedFields;
	}

	replace Function is checkStatement(Statement is stmt, [LintIssue] is issues){
		match(on: stmt, when: [
			Statement:VarDecl: local Function([String] is _mods, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				:localTypes:set(key: varName, value: varType:name);
				if({ hasInit }, {
					:checkExpression(expr: initExpr, issues: issues);
				});
			}
		], default: {
			:traverseStatement(stmt: stmt, issues: issues);
		});
	}

	replace Function is checkExpression(Expression is expr, [LintIssue] is issues){
		match(on: expr, when: [
			Expression:Cast: local Function(Expression is inner, String is target, [Expression] is _args){
				local Primitive is dstPrim: Primitive:of(target);
				local Boolean is dstNumeric: :isSignedIntPrim(p: dstPrim) || :isUnsignedIntPrim(p: dstPrim) || :isFloatPrim(p: dstPrim);
				if({ dstNumeric }, {
					local Boolean is handledLit: false;
					match(on: inner, when: [
						Expression:NumberLit: local Function(Int is val, String is _t){
							handledLit: true;
							if({ !:literalFitsIn(val: val, dst: dstPrim) }, {
								issues:push(item: LintIssue:init(line: expr:line, isWarning: true, message: 'Narrowing cast: literal ' . (val as String) . ' loses precision or sign when cast to ' . target . '.'));
							});
						},
						Expression:FloatLit: local Function(String is _t){
							handledLit: true;
							if({ !:isFloatPrim(p: dstPrim) }, {
								issues:push(item: LintIssue:init(line: expr:line, isWarning: true, message: 'Narrowing cast: Float literal loses fractional precision when cast to ' . target . '.'));
							});
						},
						Expression:Unary: local Function(String is op, Expression is sub){
							if({ op == '-' }, {
								match(on: sub, when: [
									Expression:NumberLit: local Function(Int is val, String is _t){
										handledLit: true;
										if({ !:literalFitsIn(val: 0 - val, dst: dstPrim) }, {
											issues:push(item: LintIssue:init(line: expr:line, isWarning: true, message: 'Narrowing cast: literal -' . (val as String) . ' loses precision or sign when cast to ' . target . '.'));
										});
									}
								], default: {});
							});
						}
					], default: {});
					if({ !handledLit }, {
						local String is srcName: :inferExprTypeName(expr: inner);
						local Primitive is srcPrim: Primitive:of(srcName);
						local Boolean is srcNumeric: :isSignedIntPrim(p: srcPrim) || :isUnsignedIntPrim(p: srcPrim) || :isFloatPrim(p: srcPrim);
						if({ srcNumeric && !:isLosslessWidening(src: srcPrim, dst: dstPrim) }, {
							issues:push(item: LintIssue:init(line: expr:line, isWarning: true, message: 'Narrowing cast from ' . srcName . ' to ' . target . ' may lose precision or sign.'));
						});
					});
				});
			}
		], default: {});
		:traverseExpression(expr: expr, issues: issues);
	}
}
