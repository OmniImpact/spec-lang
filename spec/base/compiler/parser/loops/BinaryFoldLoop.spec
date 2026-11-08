#! Package base:compiler:parser:loops
#! Folds one binary precedence level: consumes matching operators and
## left-folds their operands into BINARY expressions.
##
## One instance replaces the eleven same-shaped precedence loops of the
## previous compiler: the operator set and the next-lower level arrive as
## parameters.

Class of Loop is BinaryFoldLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'parser', PrecedenceLevel],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
	];

	local Parser is parser;
	local Expression is currentExpr;

	## Operators this level folds (lexeme strings; two-char operators are
	## single tokens).
	local Array of String is ops: [];

	## The next-lower precedence level for right operands; NONE descends to
	## unary parsing (the tightest level).
	local PrecedenceLevel is next: PrecedenceLevel:NONE;

	replace Function is init(Parser is parser, Expression is expr, Array of String is ops, PrecedenceLevel is next){
		self:parser: parser;
		self:currentExpr: expr;
		self:ops: ops;
		self:next: next;
	}

	replace Function of Boolean is evaluate(){
		local String is val: self:parser:peek():getValue();
		return self:ops:indexOf(search: val, default: -1) >= 0;
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local Token is opTok: self:parser:advance();
		local String is op: opTok:getValue();
		Conditional:if(check: { op == Keyword:IS:value() }, then: {
			# The identity keyword compares equal: normalize to '==' so the
			# checker and generator see one operator.
			op: '==';
		});
		local Expression is right: Expression:init(kind: ExpressionKind:UNKNOWN);
		Conditional:if(check: { self:next == PrecedenceLevel:NONE }, then: {
			right: self:parser:parseUnary();
		}, else: {
			right: self:parser:parseLevel(level: self:next);
		});
		local Expression is binExpr: Expression:init(kind: ExpressionKind:BINARY);
		binExpr:binaryOp: op;
		binExpr:leftExpr: self:currentExpr;
		binExpr:rightExpr: right;
		self:currentExpr: binExpr;
		return true;
	}
}
