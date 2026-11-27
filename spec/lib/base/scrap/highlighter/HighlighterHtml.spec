#! Package base:scrap
#! Syntax highlighter for HTML documents (`.html`, `.htm`, `.xhtml`), inheriting `MarkupHighlighter`.

Class of MarkupHighlighter is HighlighterHtml{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', MarkupHighlighter]
	];

	replace Function is init(){
		:langId: 'html';
		:langDisplay: 'HTML';
		:extensions: Array(['.html', '.htm', '.xhtml']);
	}
}
