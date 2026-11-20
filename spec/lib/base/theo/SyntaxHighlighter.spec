#! Package base:theo
#! Multi-language syntax highlighter with off-screen multi-line state tracking.

Class is SyntaxHighlighter{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [TheoBuffer, TheoColor, SyntaxTheme]],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	String is language: 'plain';
	Array of Int is lineStates: [];
	Int is drawCol: 0;

	replace Function is init(String is language: 'plain'){
		:language: language;
		:lineStates: [];
		:drawCol: 0;
	}

	Function is setLanguageFromPath(String is path){
		local String is p: path:toLower();
		if({ p:endsWith(suffix: '.spec') }, { :language: 'spec'; return; });
		if({ p:endsWith(suffix: '.json') }, { :language: 'json'; return; });
		if({ p:endsWith(suffix: '.md') || p:endsWith(suffix: '.markdown') }, { :language: 'markdown'; return; });
		if({ p:endsWith(suffix: '.c') || p:endsWith(suffix: '.h') || p:endsWith(suffix: '.cpp') || p:endsWith(suffix: '.hpp') || p:endsWith(suffix: '.cc') }, { :language: 'c'; return; });
		if({ p:endsWith(suffix: '.py') }, { :language: 'python'; return; });
		if({ p:endsWith(suffix: '.java') }, { :language: 'java'; return; });
		if({ p:endsWith(suffix: '.rb') }, { :language: 'ruby'; return; });
		if({ p:endsWith(suffix: '.rs') }, { :language: 'rust'; return; });
		:language: 'plain';
	}

	local Function of Boolean is isDigit(String is ch){
		return ch >= '0' && ch <= '9';
	}

	local Function of Boolean is isAlpha(String is ch){
		return (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || ch == '_';
	}

	local Function of Boolean is isUpper(String is ch){
		return ch >= 'A' && ch <= 'Z';
	}

	local Function of Boolean is isIdentChar(String is ch){
		return isAlpha(ch: ch) || isDigit(ch: ch);
	}

	local Function of Boolean is isSpace(String is ch){
		return ch == ' ' || ch == "\t";
	}

	local Function of Boolean is isWordInList(String is word, String is spaceWrappedList){
		return spaceWrappedList:contains(substring: " {{word}} ");
	}

	local Function of String is keywordsForLanguage(){
		if({ language == 'spec' }, {
			return ' Class Function is of local replace merge held return if while for each true false null as to in namespace using ';
		});
		if({ language == 'c' }, {
			return ' auto break case char const continue default do double else enum extern float for goto if inline int long register restrict return short signed sizeof static struct switch typedef union unsigned void volatile while true false NULL ';
		});
		if({ language == 'java' }, {
			return ' abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for goto if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while true false null ';
		});
		if({ language == 'rust' }, {
			return ' as async await break const continue crate dyn else enum extern false fn for if impl in let loop match mod move mut pub ref return self Self static struct super trait true type unsafe use where while ';
		});
		if({ language == 'python' }, {
			return ' False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield ';
		});
		if({ language == 'ruby' }, {
			return ' BEGIN END alias and begin break case class def defined? do else elsif end ensure false for if in module next nil not or redo rescue retry return self super then true undef unless until when while yield ';
		});
		return '';
	}

	local Function of Boolean is isBlockCommentLang(){
		return language == 'c' || language == 'java' || language == 'rust';
	}

	local Function of String is lineCommentPrefix(){
		if({ language == 'spec' || language == 'python' || language == 'ruby' }, { return '#'; });
		if({ language == 'c' || language == 'java' || language == 'rust' }, { return '//'; });
		return '';
	}

	local Function of Int is nextLineState(String is ln, Int is state){
		if({ language == 'markdown' }, {
			local Int is i: 0;
			while({ i < ln:length() && isSpace(ch: ln:charAt(index: i, default: ' ')) }, { i: i + 1; });
			if({ i + 2 < ln:length() && ln:substring(start: i, end: i + 3) == '```' }, {
				return if({ state == 2 }, { 0 }, { 2 });
			});
			return state;
		});
		if({ !isBlockCommentLang() && language != 'python' }, {
			return 0;
		});
		local Int is n: ln:length();
		local Int is i: 0;
		local Int is st: state;
		local String is lc: lineCommentPrefix();
		while({ i < n }, {
			if({ st == 1 }, {
				if({ i + 1 < n && ln:charAt(index: i, default: '') == '*' && ln:charAt(index: i + 1, default: '') == '/' }, {
					st: 0;
					i: i + 2;
				}, {
					i: i + 1;
				});
			}, {
				if({ st == 3 || st == 4 }, {
					local String is q: if({ st == 3 }, { '"' }, { "'" });
					if({ ln:charAt(index: i, default: '') == "\\" }, {
						i: i + 2;
					}, {
						if({ i + 2 < n && ln:charAt(index: i, default: '') == q && ln:charAt(index: i + 1, default: '') == q && ln:charAt(index: i + 2, default: '') == q }, {
							st: 0;
							i: i + 3;
						}, {
							i: i + 1;
						});
					});
				}, {
					local String is ch: ln:charAt(index: i, default: '');
					if({ lc == '//' && i + 1 < n && ch == '/' && ln:charAt(index: i + 1, default: '') == '/' }, {
						return st;
					});
					if({ lc == '#' && ch == '#' }, {
						return st;
					});
					if({ isBlockCommentLang() && i + 1 < n && ch == '/' && ln:charAt(index: i + 1, default: '') == '*' }, {
						st: 1;
						i: i + 2;
					}, {
						if({ language == 'python' && i + 2 < n && (ch == '"' || ch == "'") && ln:charAt(index: i + 1, default: '') == ch && ln:charAt(index: i + 2, default: '') == ch }, {
							st: if({ ch == '"' }, { 3 }, { 4 });
							i: i + 3;
						}, {
							if({ ch == '"' || ch == "'" }, {
								local String is q: ch;
								i: i + 1;
								while({ i < n && ln:charAt(index: i, default: '') != q }, {
									if({ ln:charAt(index: i, default: '') == "\\" }, { i: i + 2; }, { i: i + 1; });
								});
								if({ i < n }, { i: i + 1; });
							}, {
								i: i + 1;
							});
						});
					});
				});
			});
		});
		return st;
	}

	Function is computeStates(Array of String is lines){
		:lineStates: [];
		local Int is st: 0;
		local Int is i: 0;
		while({ i < lines:length() }, {
			:lineStates:add(item: st);
			st: nextLineState(ln: lines:get(index: i), state: st);
			i: i + 1;
		});
	}

	local Function of Int is utf8Step(String is s, Int is index){
		local Int is b: s:byteAt(index: index, default: 32);
		if({ b >= 240 && b < 248 }, { return 4; });
		if({ b >= 224 && b < 240 }, { return 3; });
		if({ b >= 192 && b < 224 }, { return 2; });
		return 1;
	}

	local Function is drawSpan(TheoBuffer is buf, Int is x, Int is y, Int is maxW, Int is scrollX, Int is pos, String is text, TheoColor is fg){
		local Int is len: text:length();
		if({ len == 0 }, { return; });
		local Int is visStart: scrollX;
		local Int is visEnd: scrollX + maxW;
		local Int is bi: 0;
		while({ bi < len }, {
			local Int is step: utf8Step(s: text, index: bi);
			local Int is endBi: bi + step;
			if({ endBi > len }, { endBi: len; });
			if({ drawCol >= visStart && drawCol < visEnd }, {
				local String is ch: text:substring(start: bi, end: endBi);
				buf:setCell(x: x + (drawCol - visStart), y: y, ch: ch, fg: fg);
			});
			:drawCol: drawCol + 1;
			bi: endBi;
		});
	}

	local Function is paintJsonLine(TheoBuffer is buf, Int is x, Int is y, Int is maxW, Int is scrollX, String is ln, SyntaxTheme is theme){
		local Int is n: ln:length();
		local Int is i: 0;
		while({ i < n }, {
			local String is ch: ln:charAt(index: i, default: ' ');
			if({ ch == '"' }, {
				local Int is start: i;
				i: i + 1;
				while({ i < n && ln:charAt(index: i, default: '') != '"' }, {
					if({ ln:charAt(index: i, default: '') == "\\" }, { i: i + 2; }, { i: i + 1; });
				});
				if({ i < n }, { i: i + 1; });
				local Int is look: i;
				while({ look < n && isSpace(ch: ln:charAt(index: look, default: ' ')) }, { look: look + 1; });
				local TheoColor is strCol: if({ look < n && ln:charAt(index: look, default: '') == ':' }, { theme:key }, { theme:string });
				drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: ln:substring(start: start, end: i), fg: strCol);
			}, {
				if({ isDigit(ch: ch) || (ch == '-' && i + 1 < n && isDigit(ch: ln:charAt(index: i + 1, default: ' '))) }, {
					local Int is start: i;
					i: i + 1;
					while({ i < n && (isDigit(ch: ln:charAt(index: i, default: ' ')) || ln:charAt(index: i, default: '') == '.' || ln:charAt(index: i, default: '') == 'e' || ln:charAt(index: i, default: '') == 'E' || ln:charAt(index: i, default: '') == '+' || ln:charAt(index: i, default: '') == '-') }, {
						i: i + 1;
					});
					drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: ln:substring(start: start, end: i), fg: theme:number);
				}, {
					if({ isAlpha(ch: ch) }, {
						local Int is start: i;
						while({ i < n && isIdentChar(ch: ln:charAt(index: i, default: ' ')) }, { i: i + 1; });
						local String is word: ln:substring(start: start, end: i);
						local TheoColor is col: if({ word == 'true' || word == 'false' || word == 'null' }, { theme:boolean }, { theme:plain });
						drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: word, fg: col);
					}, {
						local Int is step: utf8Step(s: ln, index: i);
						local Int is endI: i + step;
						if({ endI > n }, { endI: n; });
						local TheoColor is pCol: if({ ch == '{' || ch == '}' || ch == '[' || ch == ']' || ch == ':' || ch == ',' }, { theme:punctuation }, { theme:plain });
						drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: i, text: ln:substring(start: i, end: endI), fg: pCol);
						i: endI;
					});
				});
			});
		});
	}

	local Function is paintMarkdownInline(TheoBuffer is buf, Int is x, Int is y, Int is maxW, Int is scrollX, String is ln, Int is startIdx, TheoColor is baseFg, SyntaxTheme is theme){
		local Int is n: ln:length();
		local Int is i: startIdx;
		while({ i < n }, {
			local String is ch: ln:charAt(index: i, default: ' ');
			if({ ch == '`' }, {
				local Int is start: i;
				i: i + 1;
				while({ i < n && ln:charAt(index: i, default: '') != '`' }, { i: i + 1; });
				if({ i < n }, { i: i + 1; });
				drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: ln:substring(start: start, end: i), fg: theme:key);
			}, {
				if({ ch == '*' && i + 1 < n && ln:charAt(index: i + 1, default: '') == '*' }, {
					local Int is start: i;
					i: i + 2;
					while({ i + 1 < n && !(ln:charAt(index: i, default: '') == '*' && ln:charAt(index: i + 1, default: '') == '*') }, { i: i + 1; });
					if({ i + 1 < n }, { i: i + 2; }, { i: n; });
					drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: ln:substring(start: start, end: i), fg: theme:type);
				}, {
					if({ ch == '[' }, {
						local Int is start: i;
						while({ i < n && ln:charAt(index: i, default: '') != ']' }, { i: i + 1; });
						if({ i < n }, { i: i + 1; });
						drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: ln:substring(start: start, end: i), fg: theme:key);
					}, {
						local Int is step: utf8Step(s: ln, index: i);
						local Int is endI: i + step;
						if({ endI > n }, { endI: n; });
						drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: i, text: ln:substring(start: i, end: endI), fg: baseFg);
						i: endI;
					});
				});
			});
		});
	}

	local Function is paintMarkdownLine(TheoBuffer is buf, Int is x, Int is y, Int is maxW, Int is scrollX, String is ln, Int is startState, SyntaxTheme is theme){
		local Int is n: ln:length();
		local Int is i: 0;
		while({ i < n && isSpace(ch: ln:charAt(index: i, default: ' ')) }, { i: i + 1; });
		if({ i + 2 < n && ln:substring(start: i, end: i + 3) == '```' }, {
			drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: 0, text: ln, fg: theme:punctuation);
			return;
		});
		if({ startState == 2 }, {
			drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: 0, text: ln, fg: theme:string);
			return;
		});
		if({ i < n && ln:charAt(index: i, default: '') == '#' }, {
			drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: 0, text: ln, fg: theme:heading);
			return;
		});
		if({ i < n && ln:charAt(index: i, default: '') == '>' }, {
			drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: 0, text: ln, fg: theme:comment);
			return;
		});
		if({ i + 1 < n && (ln:charAt(index: i, default: '') == '-' || ln:charAt(index: i, default: '') == '*' || ln:charAt(index: i, default: '') == '+') && ln:charAt(index: i + 1, default: '') == ' ' }, {
			drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: 0, text: ln:substring(start: 0, end: i + 1), fg: theme:keyword);
			paintMarkdownInline(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, ln: ln, startIdx: i + 1, baseFg: theme:plain, theme: theme);
			return;
		});
		paintMarkdownInline(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, ln: ln, startIdx: 0, baseFg: theme:plain, theme: theme);
	}

	local Function is paintCodeLine(TheoBuffer is buf, Int is x, Int is y, Int is maxW, Int is scrollX, String is ln, Int is startState, SyntaxTheme is theme){
		local Int is n: ln:length();
		local Int is i: 0;
		local Int is st: startState;
		local String is lc: lineCommentPrefix();
		local String is kws: keywordsForLanguage();
		while({ i < n }, {
			if({ st == 1 }, {
				local Int is start: i;
				while({ i < n && !(i + 1 < n && ln:charAt(index: i, default: '') == '*' && ln:charAt(index: i + 1, default: '') == '/') }, {
					i: i + 1;
				});
				if({ i + 1 < n }, {
					i: i + 2;
					st: 0;
				});
				drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: ln:substring(start: start, end: i), fg: theme:comment);
			}, {
				if({ st == 3 || st == 4 }, {
					local Int is start: i;
					local String is q: if({ st == 3 }, { '"' }, { "'" });
					local Boolean is closed: false;
					while({ !closed && i < n }, {
						if({ ln:charAt(index: i, default: '') == "\\" }, {
							i: i + 2;
						}, {
							if({ i + 2 < n && ln:charAt(index: i, default: '') == q && ln:charAt(index: i + 1, default: '') == q && ln:charAt(index: i + 2, default: '') == q }, {
								i: i + 3;
								st: 0;
								closed: true;
							}, {
								i: i + 1;
							});
						});
					});
					drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: ln:substring(start: start, end: i), fg: theme:string);
				}, {
					local String is ch: ln:charAt(index: i, default: ' ');
					if({ lc == '#' && ch == '#' }, {
						drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: i, text: ln:substring(start: i, end: n), fg: theme:comment);
						return;
					});
					if({ lc == '//' && i + 1 < n && ch == '/' && ln:charAt(index: i + 1, default: '') == '/' }, {
						drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: i, text: ln:substring(start: i, end: n), fg: theme:comment);
						return;
					});
					if({ isBlockCommentLang() && i + 1 < n && ch == '/' && ln:charAt(index: i + 1, default: '') == '*' }, {
						st: 1;
						drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: i, text: '/*', fg: theme:comment);
						i: i + 2;
					}, {
						if({ language == 'python' && i + 2 < n && (ch == '"' || ch == "'") && ln:charAt(index: i + 1, default: '') == ch && ln:charAt(index: i + 2, default: '') == ch }, {
							st: if({ ch == '"' }, { 3 }, { 4 });
							drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: i, text: ln:substring(start: i, end: i + 3), fg: theme:string);
							i: i + 3;
						}, {
							if({ ch == '"' || ch == "'" }, {
								local String is q: ch;
								local Int is start: i;
								i: i + 1;
								while({ i < n && ln:charAt(index: i, default: '') != q }, {
									if({ ln:charAt(index: i, default: '') == "\\" }, { i: i + 2; }, { i: i + 1; });
								});
								if({ i < n }, { i: i + 1; });
								drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: ln:substring(start: start, end: i), fg: theme:string);
							}, {
								if({ isDigit(ch: ch) }, {
									local Int is start: i;
									while({ i < n && (isIdentChar(ch: ln:charAt(index: i, default: ' ')) || ln:charAt(index: i, default: '') == '.') }, { i: i + 1; });
									drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: ln:substring(start: start, end: i), fg: theme:number);
								}, {
									if({ isAlpha(ch: ch) }, {
										local Int is start: i;
										while({ i < n && isIdentChar(ch: ln:charAt(index: i, default: ' ')) }, { i: i + 1; });
										local String is word: ln:substring(start: start, end: i);
										local TheoColor is col: theme:plain;
										if({ isWordInList(word: word, spaceWrappedList: kws) }, {
											col: theme:keyword;
										}, {
											if({ isUpper(ch: ch) }, { col: theme:type; });
										});
										drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: start, text: word, fg: col);
									}, {
										local Int is step: utf8Step(s: ln, index: i);
										local Int is endI: i + step;
										if({ endI > n }, { endI: n; });
										local TheoColor is pCol: if({ isSpace(ch: ch) }, { theme:plain }, { theme:punctuation });
										drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: i, text: ln:substring(start: i, end: endI), fg: pCol);
										i: endI;
									});
								});
							});
						});
					});
				});
			});
		});
	}

	Function is paintLine(TheoBuffer is buf, Int is x, Int is y, Int is maxW, Int is scrollX, String is rawLine, Int is lineIndex, SyntaxTheme is theme){
		:drawCol: 0;
		local String is ln: rawLine:replaceAll(target: "\t", replacement: '    ');
		if({ language == 'plain' }, {
			drawSpan(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, pos: 0, text: ln, fg: theme:plain);
			return;
		});
		local Int is startState: if({ lineIndex >= 0 && lineIndex < lineStates:length() }, { lineStates:get(index: lineIndex) }, { 0 });
		if({ language == 'json' }, {
			paintJsonLine(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, ln: ln, theme: theme);
			return;
		});
		if({ language == 'markdown' }, {
			paintMarkdownLine(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, ln: ln, startState: startState, theme: theme);
			return;
		});
		paintCodeLine(buf: buf, x: x, y: y, maxW: maxW, scrollX: scrollX, ln: ln, startState: startState, theme: theme);
	}
}