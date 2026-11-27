#! Package base:scrap
#! Syntax-highlighting code editor extending `TextView` with pluggable `Highlighter` instances.

Class of TextView is CodeEditorView{
	replace [String] is namespace: ['base', 'scrap', 'text'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'fabric', DrawContext],
		['base', 'scrap', 'text', TextView],
		['base', 'scrap', 'highlighter', Highlighter],
		['base', 'scrap', 'highlighter', HighlighterSpec],
		['base', 'scrap', 'highlighter', HighlighterMarkdown],
		['base', 'scrap', 'highlighter', HighlighterJson],
		['base', 'scrap', 'highlighter', HighlighterC],
		['base', 'scrap', 'highlighter', HighlighterPython],
		['base', 'scrap', 'highlighter', HighlighterJava],
		['base', 'scrap', 'highlighter', HighlighterRuby],
		['base', 'scrap', 'highlighter', HighlighterRust],
		['base', 'scrap', 'highlighter', HighlighterJavaScript],
		['base', 'scrap', 'highlighter', HighlighterKotlin],
		['base', 'scrap', 'highlighter', HighlighterCss]
	];

	TextEmitter is filePath: TextEmitter(initial: '');
	TextEmitter is language: TextEmitter(initial: '');
	Array of Highlighter is highlighters: Array();
	Highlighter is activeHighlighter: Highlighter();

	replace Function is init(
		TextEmitter is text: TextEmitter(initial: ''),
		TextEmitter is filePath: TextEmitter(initial: ''),
		TextEmitter is language: TextEmitter(initial: ''),
		BoolEmitter is wrap: BoolEmitter(initial: false),
		BoolEmitter is lineNumbers: BoolEmitter(initial: false),
		BoolEmitter is monospace: BoolEmitter(initial: false),
		TextEmitter is cursorStatus: TextEmitter(initial: 'Ln 1, Col 1'),
		Function is onTextChange: local Function(String is _next){},
		Function is onRightClickMenu: local Function(Int is _x, Int is _y){},
		Function is onClipboardWrite: local Function(String is _text){},
		Function of String is onClipboardRead: local Function of String(){ '' },
		Float is padPt: 0.0,
		Float is lineGapPt: 0.0
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
			HighlighterSpec() as Highlighter,
			HighlighterMarkdown() as Highlighter,
			HighlighterJson() as Highlighter,
			HighlighterC() as Highlighter,
			HighlighterPython() as Highlighter,
			HighlighterJava() as Highlighter,
			HighlighterRuby() as Highlighter,
			HighlighterRust() as Highlighter,
			HighlighterJavaScript() as Highlighter,
			HighlighterKotlin() as Highlighter,
			HighlighterCss() as Highlighter
		]);
		:activeHighlighter: Highlighter();
		:updateHighlighter();

		signalBag:track(
			slot: 'filePath',
			emitter: :filePath,
			collector: :filePath:collect(onEmit: local Function(String is _p){
				:updateHighlighter();
				invalidate();
			})
		);
		signalBag:track(
			slot: 'language',
			emitter: :language,
			collector: :language:collect(onEmit: local Function(String is _l){
				:updateHighlighter();
				invalidate();
			})
		);
	}

	## Registers a custom `Highlighter` implementation and refreshes matching.
	Function is registerHighlighter(Highlighter is highlighter){
		highlighters:add(item: highlighter);
		:updateHighlighter();
		invalidate();
	}

	## Returns the registered language highlighters in detection order.
	Function of Array of Highlighter is registeredHighlighters(){
		return highlighters;
	}

	## Resolves the highlighter for [langOverride] (if non-empty) or [path] extension.
	Function of Highlighter is highlighterFor(String is langOverride, String is path){
		local String is lang: langOverride:toLower();
		local String is low: path:toLower();
		local Int is i: 0;
		while({ i < highlighters:length() }, {
			local Highlighter is h: highlighters:get(index: i);
			if({ lang != '' }, {
				if({ h:languageId() == lang }, { return h; });
			}, {
				if({ h:matchesExtension(lowPath: low) }, { return h; });
			});
			i: i + 1;
		});
		return Highlighter();
	}

	local Function is updateHighlighter(){
		activeHighlighter: :highlighterFor(langOverride: language:current(), path: filePath:current());
	}

	replace Function is paintLineText(DrawContext is ctx, Int is x, Int is y, String is lineStr, Int is rLine, Int is rStart, Int is fpx){
		activeHighlighter:monoMode: monoCached;
		activeHighlighter:paintLine(ctx: ctx, theme: activeTheme, x: x, y: y, lineStr: lineStr, fpx: fpx);
	}

	replace Function of Int is measureLinePrefix(DrawContext is ctx, String is lineStr, Int is col, Int is fpx){
		activeHighlighter:monoMode: monoCached;
		return activeHighlighter:measureLinePrefix(ctx: ctx, theme: activeTheme, lineStr: lineStr, fpx: fpx, col: col);
	}

	replace Function of Highlighter is createWrapContext(){
		return activeHighlighter:clone();
	}

	replace Function is measureLineAdvancesInCtx(Highlighter is hl, String is lineStr, Int is fpx, Boolean is mono, Int is outAdvI32Ptr, Int is scratchPtr){
		hl:monoMode: mono;
		hl:measureLineAdvances(ctx: DrawContext:shared, theme: activeTheme, lineStr: lineStr, fpx: fpx, outAdvI32Ptr: outAdvI32Ptr, scratchPtr: scratchPtr);
	}
}
