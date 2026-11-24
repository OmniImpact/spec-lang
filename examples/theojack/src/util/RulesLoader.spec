#! Package theojack:util
#! Loads TheoJack rules from JSON into pure [RuleItem] models.

Class is RulesLoader{
	replace [String] is namespace: ['theojack', 'util'];

	merge [[String]] is using: [
		['base', 'data', as Json()],
		['base', 'struct', Map],
		['base', 'sys', as File()],
		['theojack', 'model', [Card, RuleItem]]
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

	Function of [RuleItem] is loadItems(){
		local [RuleItem] is out: [];
		local String is raw: fileRead(path: resolvePath(), default: '');
		if({ raw == '' }, { return out; });
		local Array of Any is items: parseArrayText(text: raw);
		local Card is parser: Card();
		local Int is i: 0;
		while({ i < items:length() }, {
			local Map of String to Any is entry: items:get(index: i);
			local String is kind: if({ entry:has(key: 'type') }, { asString(val: entry:getChecked(key: 'type')) }, { '' });
			if({ (kind == 'header' || kind == 'text') && entry:has(key: 'content') }, {
				out:push(item: RuleItem(
					kind: kind,
					text: asString(val: entry:getChecked(key: 'content'))
				));
			});
			if({ kind == 'bullet' && entry:has(key: 'content') }, {
				local Array of Any is lines: entry:getChecked(key: 'content');
				local [String] is bullets: [];
				local Int is bi: 0;
				while({ bi < lines:length() }, {
					bullets:push(item: asString(val: lines:get(index: bi)));
					bi: bi + 1;
				});
				out:push(item: RuleItem(kind: 'bullet', bullets: bullets));
			});
			if({ kind == 'cards' && entry:has(key: 'content') }, {
				local Array of Any is codes: entry:getChecked(key: 'content');
				local [Card] is cards: [];
				local Int is ci: 0;
				while({ ci < codes:length() }, {
					cards:push(item: parser:fromNotation(code: asString(val: codes:get(index: ci))));
					ci: ci + 1;
				});
				out:push(item: RuleItem(kind: 'cards', cards: cards));
			});
			i: i + 1;
		});
		return out;
	}
}
