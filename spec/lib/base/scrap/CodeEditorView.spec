#! Package base:scrap
#! Syntax-highlighting code editor extending `TextView` with pluggable `ScrapHighlighter` instances.

Class of TextView is CodeEditorView{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'fabric', DrawContext],
		['base', 'scrap', TextView],
		['base', 'scrap', ScrapHighlighter],
		['base', 'scrap', SpecHighlighter],
		['base', 'scrap', MarkdownHighlighter],
		['base', 'scrap', JsonHighlighter]
	];

	TextEmitter is filePath: TextEmitter(initial: '');
	String is language: '';
	Array of ScrapHighlighter is highlighters: Array();
	ScrapHighlighter is activeHighlighter: ScrapHighlighter();

	replace Function is init(
		TextEmitter is text: TextEmitter(initial: ''),
		TextEmitter is filePath: TextEmitter(initial: ''),
		String is language: '',
		BoolEmitter is wrap: BoolEmitter(initial: false),
		BoolEmitter is lineNumbers: BoolEmitter(initial: false),
		BoolEmitter is monospace: BoolEmitter(initial: false),
		TextEmitter is cursorStatus: TextEmitter(initial: 'Ln 1, Col 1'),
		Function is onTextChange: local Function(String is _next){},
		Function is onRightClickMenu: local Function(Int is _x, Int is _y){},
		Function is onClipboardWrite: local Function(String is _text){},
		Function of String is onClipboardRead: local Function of String(){ '' },
		Float is padPt: 12.0,
		Float is lineGapPt: 4.0
	){
		:initTextView(
			text: text,
			wrap: wrap,
			lineNumbers: lineNumbers,
			monospace: monospace,
			cursorStatus: cursorStatus,
			onTextChange: onTextChange,
			onRightClickMenu: onRightClickMenu,
			onClipboardWrite: onClipboardWrite,
			onClipboardRead: onClipboardRead,
			padPt: padPt,
			lineGapPt: lineGapPt
		);
		:filePath: filePath;
		:language: language;
		:highlighters: Array([
			SpecHighlighter() as ScrapHighlighter,
			MarkdownHighlighter() as ScrapHighlighter,
			JsonHighlighter() as ScrapHighlighter
		]);
		:activeHighlighter: ScrapHighlighter();
		:updateHighlighter();

		signalBag:track(
			slot: 'filePath',
			emitter: :filePath,
			collector: :filePath:collect(onEmit: local Function(String is _p){
				:updateHighlighter();
				invalidate();
			})
		);
	}

	## Registers a custom `ScrapHighlighter` implementation and refreshes matching.
	Function is registerHighlighter(ScrapHighlighter is highlighter){
		highlighters:add(item: highlighter);
		:updateHighlighter();
		invalidate();
	}

	local Function is updateHighlighter(){
		local String is lang: language:toLower();
		local String is low: filePath:current():toLower();
		local Int is i: 0;
		while({ i < highlighters:length() }, {
			local ScrapHighlighter is h: highlighters:get(index: i);
			if({ lang != '' }, {
				if({ h:languageId() == lang }, {
					activeHighlighter: h;
					return;
				});
			}, {
				if({ h:matchesExtension(lowPath: low) }, {
					activeHighlighter: h;
					return;
				});
			});
			i: i + 1;
		});
		activeHighlighter: ScrapHighlighter();
	}

	replace Function is paintLineText(DrawContext is ctx, Int is x, Int is y, String is lineStr, Int is rLine, Int is rStart, Int is fpx){
		activeHighlighter:monoMode: monoCached;
		activeHighlighter:paintLine(ctx: ctx, theme: activeTheme, x: x, y: y, lineStr: lineStr, fpx: fpx);
	}
}
