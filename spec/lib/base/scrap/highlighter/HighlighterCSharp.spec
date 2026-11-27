#! Package base:scrap
#! Syntax highlighter for C# source files (`.cs`), inheriting `CodeHighlighter`.

Class of CodeHighlighter is HighlighterCSharp{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', CodeHighlighter]
	];

	replace Function is init(){
		:langId: 'csharp';
		:langDisplay: 'C#';
		:extensions: Array(['.cs']);
		:lineCommentPrefix: '//';
		:hasBlockComments: true;
		:keywords: ' abstract as async await base bool break byte case catch char checked class const continue decimal default delegate do double else enum event explicit extern false finally fixed float for foreach goto if implicit in int interface internal is lock long namespace new null object operator out override params private protected public readonly ref return sbyte sealed short sizeof stackalloc static string struct switch this throw true try typeof uint ulong unchecked unsafe ushort using var virtual void volatile while ';
	}
}
