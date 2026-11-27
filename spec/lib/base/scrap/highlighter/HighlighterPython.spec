#! Package base:scrap
#! Syntax highlighter for Python source files (`.py`), inheriting `CodeHighlighter`.

Class of CodeHighlighter is HighlighterPython{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', CodeHighlighter]
	];

	replace Function is init(){
		:langId: 'python';
		:langDisplay: 'Python';
		:extensions: Array(['.py']);
		:lineCommentPrefix: '#';
		:hasBlockComments: false;
		:keywords: ' False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield ';
	}
}
