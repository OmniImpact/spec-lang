#! Package base:scrap
#! Syntax highlighter for C and C++ source files (`.c`, `.h`, `.cpp`, `.hpp`, `.cc`), inheriting `ScrapHighlighter`.

Class of ScrapHighlighter is CHighlighter{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', ScrapHighlighter]
	];

	replace Function of String is languageId(){
		return 'c';
	}

	replace Function of String is displayName(){
		return 'C / C++';
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.c') || endsWith(s: lowPath, suffix: '.h')
			|| endsWith(s: lowPath, suffix: '.cpp') || endsWith(s: lowPath, suffix: '.hpp')
			|| endsWith(s: lowPath, suffix: '.cc') || endsWith(s: lowPath, suffix: '.cxx')
			|| endsWith(s: lowPath, suffix: '.hh');
	}

	replace Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		:paintCodeLine(
			ctx: ctx,
			theme: theme,
			x: x,
			y: y,
			lineStr: lineStr,
			fpx: fpx,
			lineComment: '//',
			blockComments: true,
			spaceWrappedKeywords: ' auto break case char class const continue default do double else enum extern float for goto if inline int long namespace private protected public register restrict return short signed sizeof static struct switch template typedef typename union unsigned using virtual void volatile while true false NULL nullptr '
		);
	}
}
