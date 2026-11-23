#! specunit: suite
#! Comprehensive unit test suite for the SpecBuild build orchestrator.

Class of SpecUnitTest is TestSpecBuild{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'core', Result],
		['base', 'core', SpecError],
		['base', 'data', JsonError],
		['base', 'data', as Json()],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Uri()],
		['specbuild', SpecBuild]
	];

	Function of String is dirOf(String is path){
		local String is dp: Uri:fromFilePath(filePath: path):dirPath();
		return Uri:fromFilePath(filePath: dp):toFilePath();
	}

	Function of String is resolveRoot(){
		if({ fileExists(path: 'utilities/specbuild/SpecBuild.spec') }, {
			return '.';
		});
		local String is specEnv: Process:getEnv(key: 'SPEC_BIN', default: '');
		if({ specEnv != '' }, {
			local String is d: :dirOf(path: specEnv);
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
		local String is exeSuf: Uri:exeSuffix();
		local String is cand: root . '/bin/specbuild' . exeSuf;
		if({ fileExists(path: cand) }, {
			return cand;
		});
		if({ exeSuf != '' && fileExists(path: root . '/bin/specbuild') }, {
			return root . '/bin/specbuild';
		});

		local String is compiler: '';
		local String is specEnv: Process:getEnv(key: 'SPEC_BIN', default: '');
		if({ specEnv != '' && fileExists(path: specEnv) }, {
			compiler: specEnv;
		}, {
			if({ fileExists(path: root . '/bin/spec' . exeSuf) }, {
				compiler: root . '/bin/spec' . exeSuf;
			}, {
				if({ fileExists(path: root . '/bin/spec') }, {
					compiler: root . '/bin/spec';
				}, {
					compiler: 'spec';
				});
			});
		});

		local String is srcPath: root . '/utilities/specbuild/SpecBuild.spec';
		if({ fileExists(path: srcPath) }, {
			Process:execute(command: compiler, args: Array(['-i', srcPath, '-s', root . '/spec', '-o', cand, '--quiet']));
			if({ fileExists(path: cand) }, {
				return cand;
			});
		});

		return cand;
	}

	Function is testSpecBuildConfigParsing(){
		local String is manifest: '{"name": "test_app", "version": "1.2.3", "source": "src/Main.spec", "source_dirs": ["src", "lib"], "output": "bin/test_app"}';
		local Result of Map of String to Any to JsonError is r: Json:parseMapResult(text: manifest);
		local Map of String to Any is cfg: [:];
		match(on: r, when: [
			Result:Ok: local Function of Void(Map of String to Any is v){
				cfg: v;
			},
			Result:Err: local Function of Void(SpecError of JsonError is e){
			}
		]);
		Assert:isTrue(cfg:has(key: 'name'));
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
		local String is root: :resolveRoot();
		local String is specDir: root . '/spec';
		local String is tmpDir: Uri:systemTempDir();
		local String is appSrcFile: tmpDir . '/sb_app.spec';
		local String is manifestFile: tmpDir . '/sb_manifest.json';
		local String is outBin: tmpDir . '/sb_app_bin' . Uri:exeSuffix();
		local String is outBinNoExt: tmpDir . '/sb_app_bin';

		local String is appSrc: "Class is SbApp{\n\treplace Array of Array of String is using: [\n\t\t['base', 'sys', as Output()]\n\t];\n\treplace Function is init(){\n\t\tline('SB_APP_OK');\n\t}\n}\n";
		fileWrite(path: appSrcFile, content: appSrc);

		local String is manifest: '{"name": "sb_app", "version": "0.1.0", "source": "sb_app.spec", "source_dirs": [".", "' . specDir . '"], "output": "sb_app_bin"}';
		fileWrite(path: manifestFile, content: manifest);

		if({ fileExists(path: outBin) }, {
			fileRemove(path: outBin);
		});
		if({ fileExists(path: outBinNoExt) }, {
			fileRemove(path: outBinNoExt);
		});

		local String is sbBin: :resolveSpecBuild(root: root);
		local Int is buildCode: Process:execute(command: sbBin, args: Array([manifestFile]));
		Assert:areEqualInt(0, buildCode);
		Assert:isTrue(fileExists(path: outBin));

		local Int is runCode: Process:execute(command: outBin, args: Array());
		Assert:areEqualInt(0, runCode);

		local Int is cleanCode: Process:execute(command: sbBin, args: Array([manifestFile, 'clean']));
		Assert:areEqualInt(0, cleanCode);
		Assert:isFalse(fileExists(path: outBin));

		fileRemove(path: appSrcFile);
		fileRemove(path: manifestFile);
	}
}
