#! specunit: suite

Class of SpecUnitTest is TestHighlighterAndText{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sew', HAlign],
		['base', 'scrap', 'highlighter', [Highlighter, HighlighterC, HighlighterPython, HighlighterRust, HighlighterJavaScript, HighlighterKotlin, HighlighterCss, HighlighterCSharp, HighlighterPhp, HighlighterSql, HighlighterHtml, HighlighterXml]],
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

	Function is testJavaScriptKotlinCssHighlighters(){
		local CodeEditorView is ed: CodeEditorView();

		local Highlighter is js: ed:highlighterFor(langOverride: '', path: 'app.js');
		Assert:areEqualString('javascript', js:languageId());
		Assert:areEqualString('JavaScript', js:displayName());
		Assert:isTrue(js:matchesExtension(lowPath: 'index.mjs'));
		Assert:isTrue(js:matchesExtension(lowPath: 'comp.jsx'));

		local Highlighter is kt: ed:highlighterFor(langOverride: '', path: 'Main.kt');
		Assert:areEqualString('kotlin', kt:languageId());
		Assert:areEqualString('Kotlin', kt:displayName());
		Assert:isTrue(kt:matchesExtension(lowPath: 'build.gradle.kts'));

		local Highlighter is css: ed:highlighterFor(langOverride: '', path: 'styles.css');
		Assert:areEqualString('css', css:languageId());
		Assert:areEqualString('CSS', css:displayName());
		Assert:areEqualString('css', css:clone():languageId());
	}

	Function is testCSharpPhpSqlHtmlXmlHighlighters(){
		local CodeEditorView is ed: CodeEditorView();

		local Highlighter is cs: ed:highlighterFor(langOverride: '', path: 'Program.cs');
		Assert:areEqualString('csharp', cs:languageId());
		Assert:areEqualString('C#', cs:displayName());

		local Highlighter is php: ed:highlighterFor(langOverride: '', path: 'index.php');
		Assert:areEqualString('php', php:languageId());
		Assert:areEqualString('PHP', php:displayName());

		local Highlighter is sql: ed:highlighterFor(langOverride: '', path: 'query.sql');
		Assert:areEqualString('sql', sql:languageId());
		Assert:areEqualString('SQL', sql:displayName());
		Assert:areEqualString('sql', sql:clone():languageId());

		local Highlighter is html: ed:highlighterFor(langOverride: '', path: 'page.html');
		Assert:areEqualString('html', html:languageId());
		Assert:areEqualString('HTML', html:displayName());
		Assert:isTrue(html:matchesExtension(lowPath: 'index.htm'));

		local Highlighter is xml: ed:highlighterFor(langOverride: '', path: 'config.xml');
		Assert:areEqualString('xml', xml:languageId());
		Assert:areEqualString('XML', xml:displayName());
		Assert:isTrue(xml:matchesExtension(lowPath: 'icon.svg'));
		Assert:areEqualString('xml', xml:clone():languageId());
	}

	Function is testTextScrapAlignmentAndStaticContent(){
		local TextScrap is ts: TextScrap(content: 'Static Hello', align: HAlign:CENTER);
		Assert:isTrue(ts:align == HAlign:CENTER);
		Assert:areEqualString('Static Hello', ts:text:current());
	}
}
