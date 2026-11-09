#! Package base:compiler:parser:loops
#! Folds template holes and their following literal chunks into a
## left-associated concat chain ('.' binary expressions) — the same shape
## a programmer would have written by hand, so coercion and ownership
## semantics come free.

Class of Loop is TemplateFoldLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'parser', 'loops', TemplateSplitLoop],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'iterator']
	];

	local Parser is parser;
	local TemplateSplitLoop is split;
	local Int is k: 0;
	local Expression is acc;

	replace Function is init(Parser is parser, TemplateSplitLoop is split, Expression is acc0){
		self:parser: parser;
		self:split: split;
		self:k: 0;
		self:acc: acc0;
	}

	replace Function of Boolean is evaluate(){
		return self:k < self:split:holes:length();
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local Expression is holeE: self:parser:parseTemplateExpression(text: self:split:holes:get(index: self:k));
		local Expression is withHole: Expression:init(kind: ExpressionKind:BINARY);
		withHole:str: '.';
		withHole:leftExpr: self:acc;
		withHole:rightExpr: holeE;
		local Expression is litE: Expression:init(kind: ExpressionKind:STRING);
		litE:str: self:split:lits:get(index: self:k + 1);
		local Expression is withLit: Expression:init(kind: ExpressionKind:BINARY);
		withLit:str: '.';
		withLit:leftExpr: withHole;
		withLit:rightExpr: litE;
		self:acc: withLit;
		self:k: self:k + 1;
		return true;
	}
}
