#! specunit: suite
#! Comprehensive unit test suite for the SpecBuild build orchestrator.

Class of SpecUnitTest is TestSpecBuild{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'data', as Json()],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['specbuild', SpecBuild]
	];

	Function is testSpecBuildConfigParsing(){
		local String is manifest: '{"name": "test_app", "version": "1.2.3", "type": "binary", "entry": "src/Main.spec", "source_dirs": ["src", "lib"], "output": "bin/test_app"}';
		local Any is parsed: Json:parse(text: manifest);
		Assert:isFalse(Json:hasError());
		local Map is cfg: parsed as Map;
		Assert:areEqualString('test_app', Json:getString(obj: cfg, key: 'name'));
		Assert:areEqualString('1.2.3', Json:getString(obj: cfg, key: 'version'));
		Assert:areEqualString('src/Main.spec', Json:getString(obj: cfg, key: 'entry'));
		Assert:areEqualString('bin/test_app', Json:getString(obj: cfg, key: 'output'));
		local Array is sdirs: Json:getArray(obj: cfg, key: 'source_dirs');
		Assert:areEqualInt(2, sdirs:length());
		Assert:areEqualString('src', Json:getStringAt(arr: sdirs, index: 0));
		Assert:areEqualString('lib', Json:getStringAt(arr: sdirs, index: 1));
	}

	Function is testBuildAndCleanLifecycle(){
		local String is appSrc: "Class is SbApp{\n\treplace Array of Array of String is using: [\n\t\t['base', 'sys', as Output()]\n\t];\n\treplace Function is init(){\n\t\tline('SB_APP_OK');\n\t}\n}\n";
		fileWrite(path: '/tmp/sb_app.spec', content: appSrc);

		local String is manifest: '{"name": "sb_app", "version": "0.1.0", "type": "binary", "entry": "/tmp/sb_app.spec", "source_dirs": ["/tmp"], "output": "/tmp/sb_app_bin"}';
		fileWrite(path: '/tmp/sb_manifest.json', content: manifest);

		# Build via bin/specbuild
		local Int is buildCode: Process:execute(command: 'bin/specbuild', args: ['/tmp/sb_manifest.json']);
		Assert:areEqualInt(0, buildCode);
		Assert:isTrue(fileExists(path: '/tmp/sb_app_bin'));

		# Run the built binary
		local Int is runCode: Process:execute(command: '/tmp/sb_app_bin', args: []);
		Assert:areEqualInt(0, runCode);

		# Clean via bin/specbuild
		local Int is cleanCode: Process:execute(command: 'bin/specbuild', args: ['/tmp/sb_manifest.json', 'clean']);
		Assert:areEqualInt(0, cleanCode);
		Assert:isFalse(fileExists(path: '/tmp/sb_app_bin'));

		# Cleanup temp fixture files
		fileRemove(path: '/tmp/sb_app.spec');
		fileRemove(path: '/tmp/sb_manifest.json');
	}
}
