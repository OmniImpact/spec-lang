#! Package base:scrap
#! Syntax highlighter for PHP source files (`.php`, `.phtml`), inheriting `CodeHighlighter`.

Class of CodeHighlighter is HighlighterPhp{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', CodeHighlighter]
	];

	replace Function is init(){
		:langId: 'php';
		:langDisplay: 'PHP';
		:extensions: Array(['.php', '.phtml']);
		:lineCommentPrefix: '//';
		:hasBlockComments: true;
		:keywords: ' abstract and array as break callable case catch class clone const continue declare default do echo else elseif empty enddeclare endfor endforeach endif endswitch endwhile eval exit extends final finally fn for foreach function global goto if implements include include_once instanceof insteadof interface isset list match namespace new or print private protected public readonly require require_once return static switch throw trait try unset use var while xor yield true false null ';
	}
}
