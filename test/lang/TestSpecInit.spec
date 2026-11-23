#! specunit: suite
#! Unit tests for the SpecInit project scaffolder (utilities/specinit/SpecInit.spec).

Class of SpecUnitTest is TestSpecInit{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'data', as Json()],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Uri()]
	];

	local Function of String is dirOf(String is path){
		local String is dp: Uri:fromFilePath(filePath: path):dirPath();
		return Uri:fromFilePath(filePath: dp):toFilePath();
	}

	local Function of String is resolveRoot(){
		if({ fileExists(path: 'utilities/specinit/SpecInit.spec') }, {
			return '.';
		});
		local String is specEnv: Process:getEnv(key: 'SPEC_BIN', default: '');
		if({ specEnv != '' }, {
			local String is d: :dirOf(path: specEnv);
			if({ fileExists(path: d . '/../utilities/specinit/SpecInit.spec') }, {
				return d . '/..';
			});
		});
		local String is exeDir: Dir:exeDir();
		if({ exeDir != '' && fileExists(path: exeDir . '/../utilities/specinit/SpecInit.spec') }, {
			return exeDir . '/..';
		});
		return '.';
	}

	local Function of String is resolveCompiler(String is root){
		local String is envBin: Process:getEnv(key: 'SPEC_BIN', default: '');
		if({ envBin != '' && fileExists(path: envBin) }, {
			return envBin;
		});
		local String is exeSuf: Uri:exeSuffix();
		if({ fileExists(path: root . '/bin/spec' . exeSuf) }, {
			return root . '/bin/spec' . exeSuf;
		});
		return 'bin/spec' . exeSuf;
	}

	local Function of String is resolveSpecInit(String is root){
		local String is exeSuf: Uri:exeSuffix();
		local String is cand: root . '/bin/specinit' . exeSuf;
		if({ fileExists(path: cand) }, {
			return cand;
		});
		local String is specBin: :resolveCompiler(root: root);
		local String is tmpDir: :dirOf(path: Uri:tempFile());
		local String is built: tmpDir . '/specinit_test_bin' . exeSuf;
		Process:execute(command: specBin, args: Array(['--quiet', '-i', root . '/utilities/specinit/SpecInit.spec', '-o', built]));
		return built;
	}

	Function is testHelpAndScaffoldAppAndLib(){
		local String is root: :resolveRoot();
		local String is si: :resolveSpecInit(root: root);
		Assert:isTrue(fileExists(path: si));
		if({ !fileExists(path: si) }, {
			return;
		});

		local Int is helpCode: Process:execute(command: si, args: Array(['--help']));
		Assert:areEqualInt(0, helpCode);

		local String is pid: Process:getPid() as String;
		local String is tmpDir: :dirOf(path: Uri:tempFile());
		local String is appDir: tmpDir . '/specinit_app_' . pid;
		local String is libDir: tmpDir . '/specinit_lib_' . pid;

		local Int is appCode: Process:execute(command: si, args: Array([appDir, '--app', '--force']));
		Assert:areEqualInt(0, appCode);
		Assert:isTrue(fileExists(path: "{{appDir}}/specinit_app_{{pid}}.json"));
		Assert:isTrue(fileExists(path: appDir . '/.gitignore'));
		Assert:isTrue(fileExists(path: appDir . '/src/Main.spec'));
		Assert:isTrue(fileExists(path: appDir . '/tests/MainTest.spec'));

		local String is appManifestRaw: fileRead(path: "{{appDir}}/specinit_app_{{pid}}.json", default: '', onSuccess: {}, onError: {});
		local Any is parsedApp: Json:parse(text: appManifestRaw);
		Assert:areEqualString('src/Main.spec', Json:getString(obj: parsedApp, key: 'source', default: ''));

		# Without --force, re-running on existing project must fail cleanly (exit 1)
		local Int is dupCode: Process:execute(command: si, args: Array([appDir]));
		Assert:areEqualInt(1, dupCode);

		local Int is libCode: Process:execute(command: si, args: Array([libDir, '--lib', '--force']));
		Assert:areEqualInt(0, libCode);
		Assert:isTrue(fileExists(path: "{{libDir}}/specinit_lib_{{pid}}.json"));
		Assert:isTrue(fileExists(path: libDir . '/.gitignore'));
		local String is libManifestRaw: fileRead(path: "{{libDir}}/specinit_lib_{{pid}}.json", default: '', onSuccess: {}, onError: {});
		local Any is parsedLib: Json:parse(text: libManifestRaw);
		Assert:areEqualString('0.1.0', Json:getString(obj: parsedLib, key: 'version', default: ''));
	}
}
