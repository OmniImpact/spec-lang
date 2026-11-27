#! Package base:scrap
#! Syntax highlighter for JavaScript source files (`.js`, `.mjs`, `.cjs`, `.jsx`), inheriting `CodeHighlighter`.

Class of CodeHighlighter is HighlighterJavaScript{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', CodeHighlighter]
	];

	replace Function is init(){
		:langId: 'javascript';
		:langDisplay: 'JavaScript';
		:extensions: Array(['.js', '.mjs', '.cjs', '.jsx']);
		:lineCommentPrefix: '//';
		:hasBlockComments: true;
		:keywords: ' async await break case catch class const continue debugger default delete do else export extends false finally for from function if import in instanceof let new null of return static super switch this throw true try typeof undefined var void while with yield ';
	}
}
