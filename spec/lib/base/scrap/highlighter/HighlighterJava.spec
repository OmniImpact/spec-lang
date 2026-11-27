#! Package base:scrap
#! Syntax highlighter for Java source files (`.java`), inheriting `CodeHighlighter`.

Class of CodeHighlighter is HighlighterJava{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', CodeHighlighter]
	];

	replace Function is init(){
		:langId: 'java';
		:langDisplay: 'Java';
		:extensions: Array(['.java']);
		:lineCommentPrefix: '//';
		:hasBlockComments: true;
		:keywords: ' abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for goto if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while true false null ';
	}
}
