#! Package speclint:rules
#! Suggests fancy template strings (`` `...{{expr}}...` ``) instead of `.` string concatenation with expressions.

Class of LintRule is TemplateStringRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['speclint', SourceMasker],
		['base', 'compiler', 'ast', Expression],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	local [String] is maskedLines: [];

	replace Function is checkSource(String is source, [LintIssue] is issues){
		:maskedLines: [];
		local SourceMasker is masker: SourceMasker:init();
		source:lines():each(action: local Function(String is line){
			:maskedLines:push(item: masker:maskLine(line: line));
		});
	}

	replace Function of String is id(){
		return 'template-string';
	}

	replace Function of String is description(){
		return 'Suggests fancy template strings (`...{{expr}}...`) when concatenating literals with expressions.';
	}

	replace Function of Boolean is isWarning(){
		return false;
	}

	local Function of Boolean is isStrLit(Expression is expr){
		local Boolean is res: false;
		match(on: expr, when: [
			Expression:StringLit: local Function(String is _v){
				res: true;
			}
		], default: {});
		return res;
	}

	local Function of Boolean is isDotConcat(Expression is expr){
		local Boolean is res: false;
		match(on: expr, when: [
			Expression:Binary: local Function(String is op, Expression is _l, Expression is _r){
				if({ op == '.' }, { res: true; });
			}
		], default: {});
		return res;
	}

	local Function of Boolean is chainHasStrLit(Expression is expr){
		if({ :isStrLit(expr: expr) }, { return true; });
		local Boolean is res: false;
		match(on: expr, when: [
			Expression:Binary: local Function(String is op, Expression is l, Expression is r){
				if({ op == '.' }, {
					res: :chainHasStrLit(expr: l) || :chainHasStrLit(expr: r);
				});
			}
		], default: {});
		return res;
	}

	local Function of Boolean is chainHasNonLit(Expression is expr){
		if({ :isStrLit(expr: expr) }, { return false; });
		local Boolean is res: true;
		match(on: expr, when: [
			Expression:Binary: local Function(String is op, Expression is l, Expression is r){
				if({ op == '.' }, {
					res: :chainHasNonLit(expr: l) || :chainHasNonLit(expr: r);
				});
			}
		], default: {});
		return res;
	}

	local Function is traverseNonConcat(Expression is expr, [LintIssue] is issues){
		match(on: expr, when: [
			Expression:Binary: local Function(String is op, Expression is l, Expression is r){
				if({ op == '.' }, {
					:traverseNonConcat(expr: l, issues: issues);
					:traverseNonConcat(expr: r, issues: issues);
					return;
				});
			}
		], default: {});
		:traverseExpression(expr: expr, issues: issues);
	}

	replace Function is checkExpression(Expression is expr, [LintIssue] is issues){
		if({ :isDotConcat(expr: expr) }, {
			local String is mline: '';
			if({ expr:line >= 1 && expr:line <= :maskedLines:length() }, {
				mline: :maskedLines:get(index: expr:line - 1);
			});
			if({ mline:contains(needle: '.') && :chainHasStrLit(expr: expr) && :chainHasNonLit(expr: expr) }, {
				issues:push(item: LintIssue:init(
					ruleId: :id(),
					line: expr:line,
					isWarning: :isWarning(),
					message: 'Consider using a template string ("...{{expr}}...") instead of `.` concatenation.'
				));
			});
			:traverseNonConcat(expr: expr, issues: issues);
			return;
		});
		:traverseExpression(expr: expr, issues: issues);
	}
}
