#! Package base:scrap
#! Syntax highlighter for C and C++ source files (`.c`, `.h`, `.cpp`, `.hpp`, `.cc`), inheriting `CodeHighlighter`.

Class of CodeHighlighter is HighlighterC{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', CodeHighlighter]
	];

	replace Function is init(){
		:langId: 'c';
		:langDisplay: 'C / C++';
		:extensions: Array(['.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.hh']);
		:lineCommentPrefix: '//';
		:hasBlockComments: true;
		:keywords: ' auto break case char class const continue default do double else enum extern float for goto if inline int long namespace private protected public register restrict return short signed sizeof static struct switch template typedef typename union unsigned using virtual void volatile while true false NULL nullptr ';
	}
}
