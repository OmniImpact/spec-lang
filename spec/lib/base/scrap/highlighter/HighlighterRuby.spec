#! Package base:scrap
#! Syntax highlighter for Ruby source files (`.rb`), inheriting `CodeHighlighter`.

Class of CodeHighlighter is HighlighterRuby{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', CodeHighlighter]
	];

	replace Function is init(){
		:langId: 'ruby';
		:langDisplay: 'Ruby';
		:extensions: Array(['.rb']);
		:lineCommentPrefix: '#';
		:hasBlockComments: false;
		:keywords: ' BEGIN END alias and begin break case class def defined? do else elsif end ensure false for if in module next nil not or redo rescue retry return self super then true undef unless until when while yield ';
	}
}
