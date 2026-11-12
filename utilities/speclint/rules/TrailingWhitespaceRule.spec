#! Package speclint:rules
#! Detects trailing whitespace characters at the end of lines.

Class of LintRule is TrailingWhitespaceRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['speclint', SourceMasker],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is id(){
		return 'trailing-whitespace';
	}

	replace Function of String is description(){
		return 'Detects trailing spaces or tabs at line ends.';
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
			if({ !masker:isInsideString() }, {
				if({ line:length() > 0 && (line:charAt(index: line:length() - 1, default: ' ') == ' ' || line:charAt(index: line:length() - 1, default: ' ') == "\t") }, {
					issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: 'Trailing whitespace detected.'));
				});
			});
		});
	}
}
