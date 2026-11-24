#! Package theojack:util
#! JSON persistence for TheoJack user options in the OS-standard config directory.

Class is OptionsStorage{
	replace [String] is namespace: ['theojack', 'util'];

	merge [[String]] is using: [
		['base', 'data', as Json()],
		['base', 'struct', Map],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'sys', as Uri()],
		['theojack', 'model', CardStyle]
	];

	String is filePath: '';
	CardStyle is cardStyle: CardStyle:WIREFRAME;
	Int is startingAmount: 500;
	Int is numRounds: 10;

	replace Function is init(String is filePath: ''){
		if({ filePath != '' }, {
			:filePath: filePath;
		}, {
			:filePath: appConfigDir(appName: 'theojack') . '/options.json';
		});
		load();
	}

	local Function is ensureParentDir(){
		local String is rawDir: fromFilePath(filePath: filePath):dirPath();
		if({ rawDir == '' || rawDir == '.' || rawDir == '/' }, { return; });
		local String is dir: Uri(scheme: 'file', path: rawDir):toNativeFilePath();
		if({ osName() == 'windows' }, {
			execute(command: 'cmd', args: Array(['/c', "if not exist \"{{dir}}\" mkdir \"{{dir}}\""]));
		}, {
			execute(command: 'mkdir', args: Array(['-p', dir]));
		});
	}

	Function of CardStyle is styleFromName(String is name){
		if({ name == CardStyle:BLACK:value() }, { return CardStyle:BLACK; });
		if({ name == CardStyle:WHITE:value() }, { return CardStyle:WHITE; });
		if({ name == CardStyle:METALLIC:value() }, { return CardStyle:METALLIC; });
		return CardStyle:WIREFRAME;
	}

	Function is load(){
		:cardStyle: CardStyle:WIREFRAME;
		:startingAmount: 500;
		:numRounds: 10;
		local String is raw: fileRead(path: filePath, default: '');
		if({ raw == '' }, { return; });
		local Map of String to Any is obj: parseObjectText(text: raw);
		if({ obj:has(key: 'cardStyle') }, {
			:cardStyle: styleFromName(name: asString(val: obj:getChecked(key: 'cardStyle')));
		});
		if({ obj:has(key: 'startingAmount') }, {
			local Int is amt: (asString(val: obj:getChecked(key: 'startingAmount'))) as Int;
			if({ amt > 0 }, { :startingAmount: amt; });
		});
		if({ obj:has(key: 'numRounds') }, {
			local Int is rds: (asString(val: obj:getChecked(key: 'numRounds'))) as Int;
			if({ rds > 0 }, { :numRounds: rds; });
		});
	}

	Function of CardStyle is loadCardStyle(){
		load();
		return cardStyle;
	}

	Function is save(CardStyle is style, Int is startingAmount: 500, Int is numRounds: 10){
		:cardStyle: style;
		:startingAmount: startingAmount;
		:numRounds: numRounds;
		ensureParentDir();
		local Map of String to Any is obj: [
			'cardStyle': style:value(),
			'startingAmount': startingAmount as String,
			'numRounds': numRounds as String
		];
		local String is text: stringify(value: obj);
		fileWrite(path: filePath, content: text);
	}

	Function is saveCardStyle(CardStyle is style){
		save(style: style, startingAmount: startingAmount, numRounds: numRounds);
	}
}
