#! Package base:theo
#! Syntax-highlighted multi-line text editing widget extending [TextArea].

Class of TextArea is CodeTextArea{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [TextArea, FocusTarget, TheoBuffer, SyntaxHighlighter, SyntaxTheme]],
		['base', 'signal', [TextEmitter, TextCollector]],
		['base', 'sys', as Conditional()]
	];

	SyntaxHighlighter is highlighter: SyntaxHighlighter();
	SyntaxTheme is syntaxTheme: SyntaxTheme();
	Boolean is hasCustomSyntaxTheme: false;
	String is language: 'auto';
	Array of TextEmitter is pathEmitters: Array();
	Array of TextCollector is pathCollectors: Array();

	local Function is syncLanguage(String is filePath){
		if({ language == 'auto' }, {
			highlighter:setLanguageFromPath(path: filePath);
		}, {
			highlighter:language: language;
		});
		highlighter:computeStates(lines: lines);
	}

	replace Function is init(
		String is value: '',
		String is filePath: '',
		String is language: 'auto',
		SyntaxTheme is syntaxTheme: SyntaxTheme(),
		Boolean is useThemeSyntax: true,
		FocusTarget is focusTarget: FocusTarget(),
		Function is onChange: local Function(String is _s){}
	){
		:focusTarget: focusTarget;
		:onChange: onChange;
		:boundEmitters: Array();
		:boundCollectors: Array();
		:pathEmitters: Array();
		:pathCollectors: Array();
		:highlighter: SyntaxHighlighter();
		:syntaxTheme: syntaxTheme;
		:hasCustomSyntaxTheme: !useThemeSyntax;
		:language: language;
		setText(text: value);
		syncLanguage(filePath: filePath);
	}

	Function is bindFilePath(TextEmitter is filePath){
		if({ pathEmitters:length() > 0 && pathCollectors:length() > 0 }, {
			pathEmitters:get(index: 0):detach(collector: pathCollectors:get(index: 0));
		});
		:pathEmitters: Array([filePath]);
		syncLanguage(filePath: filePath:current());
		local TextCollector is pCol: filePath:collect(onEmit: local Function(String is nextPath){
			syncLanguage(filePath: nextPath);
			invalidate();
		});
		:pathCollectors: Array([pCol]);
	}

	held Function of CodeTextArea is fromEmitters(
		TextEmitter is value,
		TextEmitter is filePath,
		String is language: 'auto',
		SyntaxTheme is syntaxTheme: SyntaxTheme(),
		Boolean is useThemeSyntax: true,
		FocusTarget is focusTarget: FocusTarget(),
		Function is onChange: local Function(String is _s){}
	){
		local CodeTextArea is ed: CodeTextArea(
			value: value:current(),
			filePath: filePath:current(),
			language: language,
			syntaxTheme: syntaxTheme,
			useThemeSyntax: useThemeSyntax,
			focusTarget: focusTarget,
			onChange: onChange
		);
		ed:bindValue(value: value);
		ed:bindFilePath(filePath: filePath);
		return ed;
	}

	Function is setFilePath(String is filePath){
		syncLanguage(filePath: filePath);
		invalidate();
	}

	Function is setLanguage(String is nextLanguage){
		:language: nextLanguage;
		highlighter:language: nextLanguage;
		highlighter:computeStates(lines: lines);
		invalidate();
	}

	replace Function is onLinesChanged(){
		highlighter:computeStates(lines: lines);
	}

	replace Function is paintLine(TheoBuffer is buf, Int is y, Int is lineIndex, String is rawLine, Int is scrollX){
		local SyntaxTheme is effTheme: if({ hasCustomSyntaxTheme }, { syntaxTheme }, { activeTheme:syntaxTheme });
		highlighter:paintLine(
			buf: buf,
			x: boxX,
			y: y,
			maxW: boxW,
			scrollX: scrollX,
			rawLine: rawLine,
			lineIndex: lineIndex,
			theme: effTheme
		);
	}

	replace Function is dispose(){
		if({ boundEmitters:length() > 0 && boundCollectors:length() > 0 }, {
			boundEmitters:get(index: 0):detach(collector: boundCollectors:get(index: 0));
			:boundEmitters: Array();
			:boundCollectors: Array();
		});
		if({ pathEmitters:length() > 0 && pathCollectors:length() > 0 }, {
			pathEmitters:get(index: 0):detach(collector: pathCollectors:get(index: 0));
			:pathEmitters: Array();
			:pathCollectors: Array();
		});
	}
}