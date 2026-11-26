#! Package base:scrap
#! Syntax highlighter for Rust source files (`.rs`), inheriting `ScrapHighlighter`.

Class of ScrapHighlighter is RustHighlighter{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', ScrapHighlighter]
	];

	replace Function of String is languageId(){
		return 'rust';
	}

	replace Function of String is displayName(){
		return 'Rust';
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.rs');
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
			spaceWrappedKeywords: ' as async await break const continue crate dyn else enum extern false fn for if impl in let loop match mod move mut pub ref return self Self static struct super trait true type unsafe use where while '
		);
	}
}
