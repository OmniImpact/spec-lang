#! Package theojack:util
#! JSON persistence for TheoJack user options.

Class is OptionsStorage{
	replace [String] is namespace: ['theojack', 'util'];

	merge [[String]] is using: [
		['base', 'data', as Json()],
		['base', 'struct', Map],
		['base', 'sys', as File()],
		['theojack', 'model', CardStyle]
	];

	String is filePath: 'theojack_options.json';

	replace Function is init(String is filePath: 'theojack_options.json'){
		:filePath: filePath;
	}

	Function of CardStyle is styleFromName(String is name){
		if({ name == CardStyle:BLACK:value() }, { return CardStyle:BLACK; });
		if({ name == CardStyle:WHITE:value() }, { return CardStyle:WHITE; });
		if({ name == CardStyle:METALLIC:value() }, { return CardStyle:METALLIC; });
		return CardStyle:WIREFRAME;
	}

	Function of CardStyle is loadCardStyle(){
		local String is raw: fileRead(path: filePath, default: '');
		if({ raw == '' }, {
			return CardStyle:WIREFRAME;
		});
		local Map of String to Any is obj: parseObjectText(text: raw);
		if({ !obj:has(key: 'cardStyle') }, {
			return CardStyle:WIREFRAME;
		});
		local String is val: asString(val: obj:getChecked(key: 'cardStyle'));
		return styleFromName(name: val);
	}

	Function is saveCardStyle(CardStyle is style){
		local Map of String to Any is obj: ['cardStyle': style:value()];
		local String is text: stringify(value: obj);
		fileWrite(path: filePath, content: text);
	}
}
