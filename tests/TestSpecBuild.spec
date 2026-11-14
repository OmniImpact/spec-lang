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
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['specbuild', SpecBuild]
	];

	Function of String is dirOf(String is path){
		local Int is lastIdx: -1;
		local Int is len: path:length();
		while([Int is pos: 0], { pos < len }, {
			local String is ch: path:charAt(index: pos, default: '');
			if({ ch == '/' || ch == '\\' }, {
				lastIdx: pos;
			});
			pos++;
		});
		if({ lastIdx < 0 }, {
			return '';
		});
		return path:substring(start: 0, end: lastIdx);
	}

	Function of String is resolveRoot(){
		if({ fileExists(path: 'utilities/specbuild/SpecBuild.spec') }, {
			return '.';
		});
		local String is specEnv: Process:getEnv(key: 'SPEC_BIN', default: '');
		if({ specEnv != '' }, {
			local String is d: self:dirOf(path: specEnv);
			if({ fileExists(path: d . '/../utilities/specbuild/SpecBuild.spec') }, {
				return d . '/..';
			});
		});
		local String is exeDir: Dir:exeDir();
		if({ exeDir != '' && fileExists(path: exeDir . '/../utilities/specbuild/SpecBuild.spec') }, {
			return exeDir . '/..';
		});
		if({ fileExists(path: '/home/daniel/Projects/Spec/utilities/specbuild/SpecBuild.spec') }, {
			return '/home/daniel/Projects/Spec';
		});
		return '.';
	}

	Function of String is resolveSpecBuild(String is root){
		local String is cand: root . '/bin/specbuild';
		if({ fileExists(path: cand) }, {
			return cand;
		});

		local String is compiler: root . '/bin/spec';
		if({ !fileExists(path: compiler) }, {
			compiler: 'spec';
		});

		local String is srcPath: root . '/utilities/specbuild/SpecBuild.spec';
		if({ fileExists(path: srcPath) }, {
			Process:execute(command: 'mkdir', args: ['-p', root . '/bin']);
			Process:execute(command: compiler, args: ['-i', srcPath, '-s', root . '/spec', '-o', cand, '--quiet']);
			if({ fileExists(path: cand) }, {
				return cand;
			});
		});

		return cand;
	}

	Function is testSpecBuildConfigParsing(){
		local String is manifest: '{"name": "test_app", "version": "1.2.3", "source": "src/Main.spec", "source_dirs": ["src", "lib"], "output": "bin/test_app"}';
		local Any is parsed: Json:parse(text: manifest);
		Assert:isFalse(Json:hasError());
		local Map is cfg: parsed as Map;
		Assert:areEqualString('test_app', Json:getString(obj: cfg, key: 'name'));
		Assert:areEqualString('1.2.3', Json:getString(obj: cfg, key: 'version'));
		Assert:areEqualString('src/Main.spec', Json:getString(obj: cfg, key: 'source'));
		Assert:areEqualString('bin/test_app', Json:getString(obj: cfg, key: 'output'));
		local Array is sdirs: Json:getArray(obj: cfg, key: 'source_dirs');
		Assert:areEqualInt(2, sdirs:length());
		Assert:areEqualString('src', Json:getStringAt(arr: sdirs, index: 0));
		Assert:areEqualString('lib', Json:getStringAt(arr: sdirs, index: 1));
	}

	Function is testBuildAndCleanLifecycle(){
		local String is root: self:resolveRoot();
		local String is specDir: root . '/spec';
		local String is appSrc: "Class is SbApp{\n\treplace Array of Array of String is using: [\n\t\t['base', 'sys', as Output()]\n\t];\n\treplace Function is init(){\n\t\tline('SB_APP_OK');\n\t}\n}\n";
		fileWrite(path: '/tmp/sb_app.spec', content: appSrc);

		local String is manifest: '{"name": "sb_app", "version": "0.1.0", "source": "sb_app.spec", "source_dirs": [".", "' . specDir . '"], "output": "sb_app_bin"}';
		fileWrite(path: '/tmp/sb_manifest.json', content: manifest);

		if({ fileExists(path: '/tmp/sb_app_bin') }, {
			fileRemove(path: '/tmp/sb_app_bin');
		});

		local String is sbBin: self:resolveSpecBuild(root: root);
		local Int is buildCode: Process:execute(command: sbBin, args: ['/tmp/sb_manifest.json']);
		Assert:areEqualInt(0, buildCode);
		Assert:isTrue(fileExists(path: '/tmp/sb_app_bin'));

		local Int is runCode: Process:execute(command: '/tmp/sb_app_bin', args: []);
		Assert:areEqualInt(0, runCode);

		local Int is cleanCode: Process:execute(command: sbBin, args: ['/tmp/sb_manifest.json', 'clean']);
		Assert:areEqualInt(0, cleanCode);
		Assert:isFalse(fileExists(path: '/tmp/sb_app_bin'));

		fileRemove(path: '/tmp/sb_app.spec');
		fileRemove(path: '/tmp/sb_manifest.json');
	}
}
