#! Package base:scrap
#! Syntax highlighter for Rust source files (`.rs`), inheriting `CodeHighlighter`.

Class of CodeHighlighter is HighlighterRust{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', CodeHighlighter]
	];

	replace Function is init(){
		:langId: 'rust';
		:langDisplay: 'Rust';
		:extensions: Array(['.rs']);
		:lineCommentPrefix: '//';
		:hasBlockComments: true;
		:keywords: ' as async await break const continue crate dyn else enum extern false fn for if impl in let loop match mod move mut pub ref return self Self static struct super trait true type unsafe use where while ';
	}
}
