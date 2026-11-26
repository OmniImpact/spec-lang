#! Package base:scrap
#! Common interface and shared drawing/scanning helpers for pluggable syntax highlighters in `CodeEditorView`.

Class is ScrapHighlighter{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	Boolean is monoMode: false;

	Function of String is languageId(){
		return 'plain';
	}

	Function of Boolean is matchesExtension(String is lowPath){
		return false;
	}

	Function of Boolean is endsWith(String is s, String is suffix){
		local Int is sl: s:length();
		local Int is fl: suffix:length();
		if({ sl < fl }, { return false; });
		return s:substring(start: sl - fl, end: sl) == suffix;
	}

	Function of Boolean is isAlpha(Int is b){
		return (b >= 65 && b <= 90) || (b >= 97 && b <= 122) || b == 95;
	}

	Function of Boolean is isDigit(Int is b){
		return b >= 48 && b <= 57;
	}

	Function of Boolean is isIdentChar(Int is b){
		return :isAlpha(b: b) || :isDigit(b: b);
	}

	Function of Int is drawSpan(
		DrawContext is ctx,
		Int is curX,
		Int is y,
		String is seg,
		Int is color,
		Int is fpx,
		Boolean is bold: false,
		Boolean is italic: false
	){
		if({ seg == '' }, { return curX; });
		ctx:drawText(x: curX, y: y, text: seg, color: color, pixelHeight: fpx, bold: bold, italic: italic, mono: monoMode);
		return curX + ctx:measureTextWidth(text: seg, pixelHeight: fpx, bold: bold, italic: italic, mono: monoMode);
	}

	Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		ctx:drawText(x: x, y: y, text: lineStr, color: theme:textPrimary, pixelHeight: fpx, mono: monoMode);
	}
}
