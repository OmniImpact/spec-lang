#! Package speclint:rules
#! Flags excessive consecutive blank lines (3+) and missing trailing newline at EOF.

Class of LintRule is BlankLinesRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['speclint', SourceMasker],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is id(){
		return 'blank-lines';
	}

	replace Function of String is description(){
		return 'Flags 3+ consecutive blank lines or missing trailing newline at end of file.';
	}

	replace Function of Boolean is isWarning(){
		return false;
	}

	replace Function is checkSource(String is source, [LintIssue] is issues){
		if({ source:length() == 0 }, { return; });
		local Int is lineNum: 0;
		local Int is blankRun: 0;
		local Boolean is reportedRun: false;
		local SourceMasker is masker: SourceMasker:init();
		local Array of String is srcLines: source:lines();

		srcLines:each(action: local Function(String is line){
			lineNum: lineNum + 1;
			local Boolean is wasInStr: masker:isInsideString();
			masker:maskLine(line: line);
			if({ wasInStr }, {
				blankRun: 0;
				reportedRun: false;
				return;
			});
			if({ line:trim():length() == 0 }, {
				blankRun: blankRun + 1;
				if({ blankRun >= 3 && !reportedRun }, {
					reportedRun: true;
					issues:push(item: LintIssue:init(
						ruleId: :id(),
						line: lineNum,
						isWarning: :isWarning(),
						message: 'More than 2 consecutive blank lines.'
					));
				});
			}, {
				blankRun: 0;
				reportedRun: false;
			});
		});

		local Int is lastByte: source:byteAt(index: source:length() - 1, default: -1);
		if({ lastByte != 10 }, {
			issues:push(item: LintIssue:init(
				ruleId: :id(),
				line: lineNum,
				isWarning: :isWarning(),
				message: 'File should end with a trailing newline.'
			));
		});
	}
}
