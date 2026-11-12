#! Package speclint:rules
#! Enforces tab-based indentation across source files.

Class of LintRule is TabIndentationRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['speclint', SourceMasker],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is id(){
		return 'tab-indentation';
	}

	replace Function of String is description(){
		return 'Enforces tab-based indentation (spaces after tabs are forbidden).';
	}

	replace Function of Boolean is isWarning(){
		return true;
	}

	replace Function is checkSource(String is source, Array of LintIssue is issues){
		local SourceMasker is masker: SourceMasker:init();
		local Int is lineNum: 0;
		local Array of String is srcLines: source:lines();
		srcLines:each(action: local Function(String is line){
			lineNum: lineNum + 1;
			if({ masker:isInsideString() }, {
				masker:maskLine(line: line);
				return;
			});
			masker:maskLine(line: line);
			local Int is tabs: line:countLeading(search: "\t");
			local String is rest: line:substring(start: tabs, end: line:length());
			local Int is spaces: rest:countLeading(search: ' ');
			if({ spaces > 0 }, {
				local String is msg: 'Space-based indentation detected (' . (spaces as String) . ' space(s)). Spec standard requires tabs.';
				issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
			});
		});
	}
}
