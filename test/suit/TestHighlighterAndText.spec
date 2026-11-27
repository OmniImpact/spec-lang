#! specunit: suite

Class of SpecUnitTest is TestHighlighterAndText{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sew', HAlign],
		['base', 'scrap', 'highlighter', [Highlighter, HighlighterC, HighlighterPython, HighlighterRust]],
		['base', 'scrap', 'text', [CodeEditorView, TextScrap]]
	];

	Function is testCodeHighlighterExtensionsAndClone(){
		local HighlighterC is hc: HighlighterC();
		Assert:areEqualString('c', hc:languageId());
		Assert:isTrue(hc:matchesExtension(lowPath: 'main.cpp'));
		Assert:isFalse(hc:matchesExtension(lowPath: 'main.py'));

		local HighlighterPython is hp: HighlighterPython();
		Assert:isTrue(hp:matchesExtension(lowPath: 'script.py'));

		local CodeEditorView is ed: CodeEditorView();
		ed:activeHighlighter: HighlighterRust() as Highlighter;
		local Highlighter is copy: ed:createWrapContext();
		Assert:areEqualString('rust', copy:languageId());
		Assert:isTrue(copy:matchesExtension(lowPath: 'lib.rs'));
	}

	Function is testTextScrapAlignmentAndStaticContent(){
		local TextScrap is ts: TextScrap(content: 'Static Hello', align: HAlign:CENTER);
		Assert:isTrue(ts:align == HAlign:CENTER);
		Assert:areEqualString('Static Hello', ts:text:current());
	}
}
