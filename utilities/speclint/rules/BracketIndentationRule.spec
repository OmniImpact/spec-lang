#! Package speclint:rules
#! Enforces tab indentation inside multi-line `[...]` arrays/maps and `(...)` call/group blocks.

Class of LintRule is BracketIndentationRule{
	replace [String] is namespace: ['speclint', 'rules'];

	replace [[String]] is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['speclint', SourceMasker],
		['base', 'struct', Array],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is id(){
		return 'bracket-indentation';
	}

	replace Function of String is description(){
		return 'Enforces +1 tab indentation inside multi-line [...] and (...) blocks and aligned closing delimiters.';
	}

	replace Function of Boolean is isWarning(){
		return true;
	}

	replace Function is checkSource(String is source, [LintIssue] is issues){
		local Int is lineNum: 0;
		local [Int] is openTabs: [];
		local [Int] is openLines: [];
		local [String] is openChars: [];
		local SourceMasker is masker: SourceMasker:init();
		local Array of String is srcLines: source:lines();

		srcLines:each(action: local Function(String is line){
			lineNum: lineNum + 1;
			if({ masker:isInsideString() }, {
				masker:maskLine(line: line);
				return;
			});
			local String is masked: masker:maskLine(line: line);
			local Int is tabs: line:countLeading(search: "\t");
			local String is trimmed: masked:trim();
			local String is firstCh: trimmed:charAt(index: 0, default: '');

			if({ trimmed:length() > 0 && openTabs:length() > 0 }, {
				local Int is topIdx: openTabs:length() - 1;
				local Int is expBase: openTabs:get(index: topIdx);
				local Int is openedAt: openLines:get(index: topIdx);
				local String is openCh: openChars:get(index: topIdx);
				local String is closeCh: if({ openCh == '[' }, { ']' }, { ')' });

				if({ lineNum > openedAt }, {
					if({ firstCh == closeCh }, {
						if({ tabs != expBase }, {
							issues:push(item: LintIssue:init(
								ruleId: :id(),
								line: lineNum,
								isWarning: :isWarning(),
								message: "Closing '" . closeCh . "' at tab depth " . (tabs as String) . " should align with opening '" . openCh . "' at tab depth " . (expBase as String) . " (line " . (openedAt as String) . ")."
							));
						});
					}, {
						if({ firstCh != '}' && tabs < expBase + 1 }, {
							issues:push(item: LintIssue:init(
								ruleId: :id(),
								line: lineNum,
								isWarning: :isWarning(),
								message: "Line inside multi-line '" . openCh . "...' block (opened on line " . (openedAt as String) . ") should be indented at least " . ((expBase + 1) as String) . " tab(s), found " . (tabs as String) . "."
							));
						});
					});
				});
			});

			times(count: masked:length(), worker: local Function(Int is i){
				local String is ch: masked:charAt(index: i, default: '');
				if({ ch == '[' || ch == '(' }, {
					openTabs:push(item: tabs);
					openLines:push(item: lineNum);
					openChars:push(item: ch);
				}, {
					if({ ch == ']' || ch == ')' }, {
						if({ openTabs:length() > 0 }, {
							openTabs:pop();
							openLines:pop();
							openChars:pop();
						});
					});
				});
			});
		});
	}
}
