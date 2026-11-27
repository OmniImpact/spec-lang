#! Package base:scrap
#! Data-driven syntax highlighter base for C-family and scripting languages sharing `Highlighter:paintCodeLine`.

Class of Highlighter is CodeHighlighter{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', 'highlighter', Highlighter]
	];

	String is langId: 'plain';
	String is langDisplay: 'Plain Text';
	Array of String is extensions: Array();
	String is lineCommentPrefix: '//';
	Boolean is hasBlockComments: false;
	String is keywords: ' ';

	replace Function is init(
		String is langId: 'plain',
		String is langDisplay: 'Plain Text',
		Array of String is extensions: Array(),
		String is lineCommentPrefix: '//',
		Boolean is hasBlockComments: false,
		String is keywords: ' '
	){
		:langId: langId;
		:langDisplay: langDisplay;
		:extensions: extensions;
		:lineCommentPrefix: lineCommentPrefix;
		:hasBlockComments: hasBlockComments;
		:keywords: keywords;
	}

	replace Function of String is languageId(){
		return langId;
	}

	replace Function of String is displayName(){
		return langDisplay;
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		local Int is i: 0;
		while({ i < extensions:length() }, {
			if({ endsWith(s: lowPath, suffix: extensions:get(index: i)) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function of Highlighter is clone(){
		return CodeHighlighter(
			langId: langId,
			langDisplay: langDisplay,
			extensions: extensions,
			lineCommentPrefix: lineCommentPrefix,
			hasBlockComments: hasBlockComments,
			keywords: keywords
		) as Highlighter;
	}

	replace Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		:paintCodeLine(
			ctx: ctx,
			theme: theme,
			x: x,
			y: y,
			lineStr: lineStr,
			fpx: fpx,
			lineComment: lineCommentPrefix,
			blockComments: hasBlockComments,
			spaceWrappedKeywords: keywords
		);
	}
}
