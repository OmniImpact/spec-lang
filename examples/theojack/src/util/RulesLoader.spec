#! Package theojack:util
#! Loads TheoJack rules from JSON and builds scrollable Theo widgets.

Class is RulesLoader{
	replace [String] is namespace: ['theojack', 'util'];

	merge [[String]] is using: [
		['base', 'data', as Json()],
		['base', 'struct', Map],
		['base', 'sys', as File()],
		['base', 'theo', [Widget, Col, Row, TextLine, TextGraphic, TheoColor]],
		['theojack', 'model', [Card, CardStyle]],
		['theojack', 'view', CardView]
	];

	String is filePath: 'rules.json';

	replace Function is init(String is filePath: 'rules.json'){
		:filePath: filePath;
	}

	Function of String is resolvePath(){
		if({ fileExists(path: filePath) }, { return filePath; });
		if({ fileExists(path: 'examples/theojack/rules.json') }, { return 'examples/theojack/rules.json'; });
		return filePath;
	}

	Function of Array of Widget is loadWidgets(CardStyle is style: CardStyle:WIREFRAME){
		local Array of Widget is out: Array();
		local String is raw: fileRead(path: resolvePath(), default: '');
		if({ raw == '' }, { return out; });
		local Array of Any is items: parseArrayText(text: raw);
		local Card is parser: Card();
		local Int is i: 0;
		while({ i < items:length() }, {
			local Map of String to Any is entry: items:get(index: i);
			local String is kind: if({ entry:has(key: 'type') }, { asString(val: entry:getChecked(key: 'type')) }, { '' });
			if({ kind == 'header' && entry:has(key: 'content') }, {
				out:add(item: TextLine(
					value: asString(val: entry:getChecked(key: 'content')),
					color: TheoColor:ansi(code: 220),
					bold: true
				));
			});
			if({ kind == 'text' && entry:has(key: 'content') }, {
				out:add(item: TextGraphic(
					graphic: asString(val: entry:getChecked(key: 'content'))
				));
			});
			if({ kind == 'bullet' && entry:has(key: 'content') }, {
				local Array of Any is lines: entry:getChecked(key: 'content');
				local Array of Widget is bulletRows: Array();
				local Int is bi: 0;
				while({ bi < lines:length() }, {
					local String is bText: asString(val: lines:get(index: bi));
					bulletRows:add(item: Row(
						gap: 1,
						children: Array([
							TextLine(value: '•', color: TheoColor:ansi(code: 220), bold: true),
							TextGraphic(graphic: bText)
						])
					));
					bi: bi + 1;
				});
				out:add(item: Col(gap: 0, padX: 1, children: bulletRows));
			});
			if({ kind == 'cards' && entry:has(key: 'content') }, {
				local Array of Any is codes: entry:getChecked(key: 'content');
				local Array of Widget is rowKids: Array();
				local Int is ci: 0;
				while({ ci < codes:length() }, {
					local String is code: asString(val: codes:get(index: ci));
					rowKids:add(item: CardView(card: parser:fromNotation(code: code), style: style));
					ci: ci + 1;
				});
				out:add(item: Row(gap: 2, children: rowKids));
			});
			i: i + 1;
		});
		return out;
	}
}
