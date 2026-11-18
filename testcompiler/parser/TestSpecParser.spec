#! Parser port check: precedence folding, template desugaring, enum and
#! generic-class declarations, interface-style members, and error provenance.

Class of SpecUnitTest is TestSpecParser{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', Error],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'lexer', Punctuation],
		['base', 'compiler', 'ast', Type]
	];

	## Tokenizes and parses a source string.
	##
	## @param src: Spec source text.
	## @return: The parse errors rendered, empty when clean.
	Function of Array of String is parseOf(String is src){
		local Lexer is lx: Lexer:init(source: src);
		local Array of Token is toks: lx:tokenize();
		local Parser is p: Parser:init(tokens: toks);
		local ProgramNode is prog: p:parseProgram();
		local Array of String is msgs: [];
		p:getErrors():each(action: local Function(Error is e){
			msgs:add(item: e:getMessage());
		});
		return msgs;
	}

	Function is testPrecedenceFolding(){
		local Lexer is lx: Lexer:init(source: 'Class is T{ Function is go(){ local Int is n: 1 + 2 * 3; } }');
		local Parser is p: Parser:init(tokens: lx:tokenize());
		local ProgramNode is prog: p:parseProgram();
		local ClassInfo is cls: prog:classes:get(index: 0);
		local Member is go: cls:members:get(index: 0);
		local Statement is vd: go:body:get(index: 0);
		local Expression is init: Expression:Unknown;
		match(on: vd, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				init: initExpr;
			},
			else: {}
		]);
		Assert:isFalse(p:hasErrors());
		Assert:areEqualString('VarDecl', vd:name());
		local Boolean is initOk: false;
		match(on: init, when: [
			Expression:Binary: local Function(String is op, Expression is leftExpr, Expression is rightExpr){
				Assert:areEqualString('+', op);
				match(on: rightExpr, when: [
					Expression:Binary: local Function(String is rop, Expression is rl, Expression is rr){
						Assert:areEqualString('*', rop);
						initOk: true;
					}
				], default: {});
			}
		], default: {});
		Assert:isTrue(initOk);
	}

	Function is testTemplateDesugarsToConcatChain(){
		local Lexer is lx2: Lexer:init(source: 'Class is T{ Function is go(){ local String is s: "n={{1 + 2}} \{\{x\}\}"; } }');
		local Parser is p2: Parser:init(tokens: lx2:tokenize());
		local ProgramNode is prog2: p2:parseProgram();
		local ClassInfo is cls2: prog2:classes:get(index: 0);
		local Member is m2: cls2:members:get(index: 0);
		local Statement is vd2: m2:body:get(index: 0);
		local Expression is s2: Expression:Unknown;
		match(on: vd2, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				s2: initExpr;
			},
			else: {}
		]);
		Assert:isFalse(p2:hasErrors());
		local Boolean is s2Ok: false;
		match(on: s2, when: [
			Expression:Binary: local Function(String is op, Expression is leftExpr, Expression is rightExpr){
				Assert:areEqualString('.', op);
				match(on: leftExpr, when: [
					Expression:Binary: local Function(String is lop, Expression is ll, Expression is lr){
						match(on: lr, when: [
							Expression:Binary: local Function(String is lrop, Expression is lrl, Expression is lrr){
								s2Ok: true;
							}
						], default: {});
					}
				], default: {});
			}
		], default: {});
		Assert:isTrue(s2Ok);
	}

	Function is testEnumAndGenericClassParseClean(){
		local Array of String is errs: self:parseOf(src: "Enum of String is Level { NONE: '', WARN: 'WRN' }
Class is Box of T{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function of T is get(){ return self:item; }
	local T is item;
}");
		Assert:areEqualInt(0, errs:length());
	}

	Function is testInterfaceStyleDeclarationParses(){
		local Array of String is errs2: self:parseOf(src: "Class is Floor{ namespace: ['base', 'x'];
	Function of Int is op(String is b); }");
		Assert:areEqualInt(0, errs2:length());
	}

	Function is testParseErrorsCarryProvenance(){
		local Lexer is lx3: Lexer:init(source: 'Class is T{ Function is go(){ local Int is n: ; } }');
		local Parser is p3: Parser:init(tokens: lx3:tokenize());
		local ProgramNode is prog3: p3:parseProgram();
		Assert:isTrue(p3:hasErrors());
		Assert:areEqualInt(1, p3:getErrors():get(index: 0):getTrace():length());
	}
}
