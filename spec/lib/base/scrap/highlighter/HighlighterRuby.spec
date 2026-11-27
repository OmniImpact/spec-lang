#! Package base:scrap
#! Syntax highlighter for Ruby source files (`.rb`), inheriting `Highlighter`.

Class of Highlighter is HighlighterRuby{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', 'highlighter', Highlighter]
	];

	replace Function of String is languageId(){
		return 'ruby';
	}

	replace Function of String is displayName(){
		return 'Ruby';
	}

	replace Function of Highlighter is clone(){
		return HighlighterRuby() as Highlighter;
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.rb');
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
			spaceWrappedKeywords: ' BEGIN END alias and begin break case class def defined? do else elsif end ensure false for if in module next nil not or redo rescue retry return self super then true undef unless until when while yield '
		);
	}
}
