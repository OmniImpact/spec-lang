#! Package speclint:rules
#! Validates closing-brace alignment against block opening indents.

Class of LintRule is BraceAlignmentRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['speclint', SourceMasker],
		['base', 'struct', Array],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is id(){
		return 'brace-alignment';
	}

	replace Function of String is description(){
		return 'Enforces closing braces sit at the tab indent of the line that opened the block.';
	}

	replace Function of Boolean is isWarning(){
		return true;
	}

	replace Function is checkSource(String is source, Array of LintIssue is issues){
		local Int is lineNum: 0;
		local Int is stmtTabs: 0;
		local Boolean is prevOpen: false;
		local Array of Int is openTabs: [];
		local SourceMasker is masker: SourceMasker:init();
		local Array of String is srcLines: source:lines();
		srcLines:each(action: local Function(String is line){
			lineNum: lineNum + 1;
			if({ masker:isInsideString() }, {
				masker:maskLine(line: line);
				prevOpen: false;
				return;
			});
			local String is masked: masker:maskLine(line: line);
			local Int is tabs: line:countLeading(search: "\t");

			local String is trimmed: masked;
			local Boolean is trimming: true;
			while({ trimming && trimmed:length() > 0 }, {
				local String is first: trimmed:charAt(index: 0, default: '');
				if({ first == ' ' || first == "\t" }, {
					trimmed: trimmed:substring(start: 1, end: trimmed:length());
				}, {
					trimming: false;
				});
			});
			local String is firstCh: trimmed:charAt(index: 0, default: '');
			local Int is pushTabs: tabs;
			if({ trimmed:length() > 0 }, {
				if({ firstCh == '&' || firstCh == '|' || firstCh == '.' || firstCh == '?' || prevOpen }, {
					pushTabs: stmtTabs;
				}, {
					if({ firstCh != '}' }, {
						stmtTabs: tabs;
					});
				});
			});

			if({ trimmed:length() > 0 && firstCh == '}' }, {
				local Int is openCount: openTabs:length();
				if({ openCount > 0 }, {
					local Int is expectedTabs: (openTabs:get(index: openCount - 1)) as Int;
					if({ tabs != expectedTabs }, {
						local String is msg: 'Closing brace indented at ' . (tabs as String) . ' tab(s); the block opened at ' . (expectedTabs as String) . ' tab(s).';
						issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
					});
				});
			});

			local Int is ci: 0;
			while({ ci < masked:length() }, {
				local String is ch: masked:charAt(index: ci, default: '');
				match(on: ch, when: [
					'{': { openTabs:add(item: pushTabs); },
					'}': {
						if({ openTabs:length() > 0 }, {
							openTabs:removeAt(index: openTabs:length() - 1, default: 0);
						});
					}
				]);
				ci: ci + 1;
			});

			local String is tail: masked;
			local Boolean is tTrimming: true;
			while({ tTrimming && tail:length() > 0 }, {
				local String is last: tail:charAt(index: tail:length() - 1, default: '');
				if({ last == ' ' || last == "\t" }, {
					tail: tail:substring(start: 0, end: tail:length() - 1);
				}, {
					tTrimming: false;
				});
			});
			prevOpen: tail:endsWith(suffix: '&&') || tail:endsWith(suffix: '||') || tail:endsWith(suffix: '&') || tail:endsWith(suffix: '|') || tail:endsWith(suffix: '+') || tail:endsWith(suffix: '-') || tail:endsWith(suffix: '*') || tail:endsWith(suffix: '.') || tail:endsWith(suffix: '?');
		});
	}
}
