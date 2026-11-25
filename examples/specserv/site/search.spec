#! Package site
#! Dynamic SpecServePage that searches HTML documentation pages using base:data:Xml.

Class of SpecServePage is SearchPage{
	replace [String] is namespace: ['site'];

	merge [[String]] is using: [
		['base', 'net', SpecServePage],
		['base', 'data', [Xml, XmlNode]],
		['base', 'struct', [Array, Map]],
		['base', 'sys', [as Dir(), as File(), as Process()]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is query: '';
	String is resultHtml: '';

	local Function of String is escapeHtml(String is s){
		return s:replaceAll(search: '&', replacement: '&amp;')
			:replaceAll(search: '<', replacement: '&lt;')
			:replaceAll(search: '>', replacement: '&gt;')
			:replaceAll(search: '"', replacement: '&quot;');
	}

	local Function of String is makeSnippet(String is text, Int is matchPos, Int is qLen){
		local Int is start: matchPos - 70;
		if({ start < 0 }, { start: 0; });
		local Int is endPos: matchPos + qLen + 110;
		if({ endPos > text:length() }, { endPos: text:length(); });
		local String is prefix: if({ start > 0 }, { '...' }, { '' });
		local String is suffix: if({ endPos < text:length() }, { '...' }, { '' });
		return prefix . text:substring(start: start, end: endPos) . suffix;
	}

	replace Function is init(Map of String to String is getArgs: Map:init(), Map of String to String is postArgs: Map:init()){
		query: getArgs:getString(key: 'q', default: '');
		if({ query == '' }, {
			query: postArgs:getString(key: 'q', default: '');
		});
		query: query:trim();

		local String is docRoot: getEnv(key: 'SPECSERV_ROOT', default: '.');
		local String is qLower: query:toLower();
		local Xml is xml: Xml();

		local String is cards: '';
		local Int is matchCount: 0;

		if({ query != '' }, {
			local Array of String is entries: dirList(path: docRoot);
			times(count: entries:length(), worker: local Function(Int is i){
				local String is fname: entries:get(index: i, default: '');
				if({ fname:toLower():endsWith(suffix: '.html') }, {
					local String is fullPath: docRoot . '/' . fname;
					local String is html: fileRead(path: fullPath, onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');
					local XmlNode is doc: xml:parseHtml(input: html);
					local String is title: doc:firstByTag(tagName: 'title'):visibleText():trim();
					if({ title == '' }, { title: fname; });
					local XmlNode is bodyNode: doc:firstByTag(tagName: 'body');
					local String is visible: if({ bodyNode:tag != '' }, { bodyNode:visibleText() }, { doc:visibleText() });
					local String is visLower: visible:toLower();
					local Int is pos: visLower:indexOf(search: qLower, default: -1);
					if({ pos >= 0 }, {
						matchCount++;
						local String is snippet: makeSnippet(text: visible, matchPos: pos, qLen: query:length());
						cards: cards . '<div class="card">'
							. '<h3><a href="/' . escapeHtml(s: fname) . '">' . escapeHtml(s: title) . '</a>'
							. '<span class="badge">' . escapeHtml(s: fname) . '</span></h3>'
							. '<p class="snippet">' . escapeHtml(s: snippet) . '</p>'
							. '</div>';
					});
				});
			});
		});

		local String is safeQ: escapeHtml(s: query);
		local String is summary: if({ query == '' }, {
			'<p>Enter a search term above to search all HTML documentation pages.</p>'
		}, {
			'<p>Found <strong>' . (matchCount as String) . '</strong> page(s) matching <code>' . safeQ . '</code>.</p>'
		});
		if({ query != '' && matchCount == 0 }, {
			cards: '<div class="card"><p>No HTML pages matched <code>' . safeQ . '</code>. Try searching for <em>ARC</em>, <em>match</em>, <em>ThreadScope</em>, or <em>Xml</em>.</p></div>';
		});

		resultHtml: '<!DOCTYPE html>'
			. '<html lang="en"><head><meta charset="utf-8" />'
			. '<title>Search: ' . safeQ . ' - Spec Docs</title>'
			. '<link rel="stylesheet" href="/styles.css" /></head><body>'
			. '<header>'
			. '<a class="brand" href="/index.html"><img src="/logo.svg" alt="Spec logo" /><span>Spec Docs</span></a>'
			. '<nav>'
			. '<a href="/index.html">Overview</a>'
			. '<a href="/syntax.html">Syntax</a>'
			. '<a href="/keywords.html">Keywords</a>'
			. '<a href="/stdlib.html">Standard Library</a>'
			. '<a href="/notes.txt">Notes</a>'
			. '<form class="search-form" action="/search.spec" method="get">'
			. '<input type="text" name="q" value="' . safeQ . '" placeholder="Search docs (/)..." />'
			. '<button type="submit">Search</button>'
			. '</form></nav></header>'
			. '<main><h1>Documentation Search</h1>'
			. summary
			. cards
			. '</main><footer>Served by SpecServ · Dynamic SpecServePage powered by base:data:Xml</footer>'
			. '<script src="/app.js"></script></body></html>';
	}

	replace Function of Int is statusCode(){ 200 }

	replace Function of String is contentType(){ 'text/html; charset=utf-8' }

	replace Function of Map of String to String is headers(){
		local Map of String to String is h: Map:init();
		h:set(key: 'Cache-Control', value: 'no-store');
		return h;
	}

	replace Function of String is body(){ resultHtml }
}
