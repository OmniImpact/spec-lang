#! Package base:scrap
#! Syntax highlighter for Python source files (`.py`), inheriting `ScrapHighlighter`.

Class of ScrapHighlighter is PythonHighlighter{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', ScrapHighlighter]
	];

	replace Function of String is languageId(){
		return 'python';
	}

	replace Function of String is displayName(){
		return 'Python';
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.py');
	}

	replace Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		:paintCodeLine(
			ctx: ctx,
			theme: theme,
			x: x,
			y: y,
			lineStr: lineStr,
			fpx: fpx,
			lineComment: '#',
			blockComments: false,
			spaceWrappedKeywords: ' False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield '
		);
	}
}
