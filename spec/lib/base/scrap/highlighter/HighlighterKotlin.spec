#! Package base:scrap
#! Syntax highlighter for Kotlin source files (`.kt`, `.kts`), inheriting `CodeHighlighter`.

Class of CodeHighlighter is HighlighterKotlin{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', CodeHighlighter]
	];

	replace Function is init(){
		:langId: 'kotlin';
		:langDisplay: 'Kotlin';
		:extensions: Array(['.kt', '.kts']);
		:lineCommentPrefix: '//';
		:hasBlockComments: true;
		:keywords: ' abstract actual annotation as break by catch class companion const constructor continue crossinline data do dynamic else enum expect external false final finally for fun get if import in infix inline inner interface internal is lateinit noinline null object open operator out override package private protected public reified return sealed set super suspend tailrec this throw true try typealias typeof val var vararg when where while ';
	}
}
