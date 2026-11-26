#! Package base:scrap
#! Syntax highlighter for Java source files (`.java`), inheriting `ScrapHighlighter`.

Class of ScrapHighlighter is JavaHighlighter{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', ScrapHighlighter]
	];

	replace Function of String is languageId(){
		return 'java';
	}

	replace Function of String is displayName(){
		return 'Java';
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.java');
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
			spaceWrappedKeywords: ' abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for goto if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while true false null '
		);
	}
}
