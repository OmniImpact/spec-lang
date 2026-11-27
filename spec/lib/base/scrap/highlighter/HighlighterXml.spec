#! Package base:scrap
#! Syntax highlighter for generic XML documents (`.xml`, `.svg`, `.xsd`, `.xsl`, `.plist`, `.csproj`, `.props`), inheriting `MarkupHighlighter`.

Class of MarkupHighlighter is HighlighterXml{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'scrap', 'highlighter', MarkupHighlighter]
	];

	replace Function is init(){
		:langId: 'xml';
		:langDisplay: 'XML';
		:extensions: Array(['.xml', '.svg', '.xsd', '.xsl', '.plist', '.csproj', '.props']);
	}
}
