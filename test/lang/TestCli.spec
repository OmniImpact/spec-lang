#! specunit: suite

Class of SpecUnitTest is TestCli{
	replace [String] is namespace: ['test', 'lang'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'cli', Cli],
		['base', 'struct', Array]
	];

	local Function of String is sampleSchema(){
		return '{"name":"mytool","version":"1.2.3","description":"Sample CLI","usage":"mytool [options]","options":['
			. '{"short":"s","long":"spec","type":"string","default":"bin/spec","arg":"path","description":"Compiler path"},'
			. '{"short":"t","long":"tests","type":"list","required":true,"arg":"dir","description":"Test dir"},'
			. '{"short":"j","long":"threads","type":"int","default":"4","arg":"N","description":"Threads"},'
			. '{"long":"pretty","type":"bool","description":"Pretty UI"}'
			. ']}';
	}

	Function is testParseShortLongAndDefaults(){
		local Cli is cli: Cli(quiet: true, jsonText: sampleSchema());
		local Boolean is ok: cli:parse(rawArgs: Array(['-s', '/usr/bin/spec', '-t', 'test', '--tests=testcompiler', '--pretty', 'extra']));
		Assert:isTrue(ok);
		Assert:areEqualString('/usr/bin/spec', cli:getString(name: 'spec'));
		Assert:areEqualInt(4, cli:getInt(name: 'threads'));
		Assert:isTrue(cli:getBool(name: 'pretty'));
		local Array of String is ts: cli:getList(name: 'tests');
		Assert:areEqualInt(2, ts:length());
		Assert:areEqualString('test', ts:get(index: 0, default: ''));
		Assert:areEqualString('testcompiler', ts:get(index: 1, default: ''));
		Assert:areEqualInt(1, cli:positionals():length());
		Assert:areEqualString('extra', cli:positionals():get(index: 0, default: ''));
	}

	Function is testHelpAndRequiredValidation(){
		local Cli is cli: Cli(quiet: true, jsonText: sampleSchema());
		local Boolean is helpOk: cli:parse(rawArgs: Array(['--help']));
		Assert:isFalse(helpOk);
		Assert:isTrue(cli:helpRequested);
		local String is helpTxt: cli:formatHelp();
		Assert:isTrue(helpTxt:contains(needle: 'mytool 1.2.3 - Sample CLI'));
		Assert:isTrue(helpTxt:contains(needle: '-s, --spec <path>'));
		Assert:isTrue(helpTxt:contains(needle: '--pretty'));
		Assert:isTrue(helpTxt:contains(needle: '-h, --help'));

		local Cli is cli2: Cli(quiet: true, jsonText: sampleSchema());
		local Boolean is reqOk: cli2:parse(rawArgs: Array(['--pretty']));
		Assert:isFalse(reqOk);
		Assert:isFalse(cli2:helpRequested);
		Assert:isTrue(cli2:errorMessage:contains(needle: 'tests'));
	}
}
