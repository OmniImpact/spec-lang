#! Parser port check: precedence folding, template desugaring, enum and
#! generic-class declarations, interface-style members, and error provenance.

Class is SpecParserTest{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'io', Output],
		['base', 'io', as Output()]
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

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec Parser Test ===');
		local Int is failures: 0;

		# Precedence: 1 + 2 * 3 folds multiplicative under additive.
		local Lexer is lx: Lexer:init(source: 'Class is T{ Function is go(){ local Int is n: 1 + 2 * 3; } }');
		local Parser is p: Parser:init(tokens: lx:tokenize());
		local ProgramNode is prog: p:parseProgram();
		local ClassInfo is cls: prog:classes:get(index: 0);
		local Member is go: cls:members:get(index: 0);
		local Statement is vd: go:body:get(index: 0);
		local Expression is init: vd:initExpr;
		if (!p:hasErrors() && vd:kind == StatementKind:VAR_DECL && init:kind == ExpressionKind:BINARY && init:binaryOp == '+' && init:rightExpr:binaryOp == '*') {
			Output:line('[PASS] precedence folding (additive over multiplicative)');
		} else {
			Output:line('[FAIL] precedence folding');
			failures: failures + 1;
		}

		# Template desugars to a concat chain; braces escape stays literal.
		local Lexer is lx2: Lexer:init(source: 'Class is T{ Function is go(){ local String is s: "n={{1 + 2}} \{\{x\}\}"; } }');
		local Parser is p2: Parser:init(tokens: lx2:tokenize());
		local ProgramNode is prog2: p2:parseProgram();
		local ClassInfo is cls2: prog2:classes:get(index: 0);
		local Member is m2: cls2:members:get(index: 0);
		local Statement is vd2: m2:body:get(index: 0);
		local Expression is s2: vd2:initExpr;
		if (!p2:hasErrors() && s2:kind == ExpressionKind:BINARY && s2:binaryOp == '.' && s2:leftExpr:rightExpr:kind == ExpressionKind:BINARY) {
			Output:line('[PASS] template desugars to concat chain');
		} else {
			Output:line('[FAIL] template desugar');
			failures: failures + 1;
		}

		# Enum with tags and a generic class parse.
		local Array of String is errs: self:parseOf(src: "Enum of String is Level { NONE: '', WARN: 'WRN' }
Class is Box of T{

	replace Array of Array of String is using: [
		['base', 'io', as Output()]
	];
	replace Function of T is get(){ return self:item; }
	local T is item;
}");
		if (errs:length() == 0) {
			Output:line('[PASS] enum + generic class parse clean');
		} else {
			Output:line('[FAIL] enum/generic: ' . errs:join(separator: ' | '));
			failures: failures + 1;
		}

		# Interface-style floor declaration parses body-less.
		local Array of String is errs2: self:parseOf(src: "Class is Floor{ namespace: ['base', 'x'];
	Function of Int is op(String is b); }");
		if (errs2:length() == 0) {
			Output:line('[PASS] interface-style declaration parses');
		} else {
			Output:line('[FAIL] interface-style: ' . errs2:join(separator: ' | '));
			failures: failures + 1;
		}

		# A syntax error is an Error with provenance.
		local Lexer is lx3: Lexer:init(source: 'Class is T{ Function is go(){ local Int is n: ; } }');
		local Parser is p3: Parser:init(tokens: lx3:tokenize());
		local ProgramNode is prog3: p3:parseProgram();
		if (p3:hasErrors() && p3:getErrors():get(index: 0):getTrace():length() == 1) {
			Output:line('[PASS] parse errors carry provenance');
		} else {
			Output:line('[FAIL] parse error provenance');
			failures: failures + 1;
		}

		if (failures == 0) {
			Output:line('[PASS] spec parser test complete');
		} else {
			Output:line('[FAIL] spec parser test: ' . (failures as String) . ' failures');
		}
	}
}
