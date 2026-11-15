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
			local String is d: self:dirOf(path: specEnv);
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
		local String is specBin: self:resolveCompiler(root: root);
		local String is tmpDir: self:dirOf(path: Uri:tempFile());
		local String is built: tmpDir . '/specinit_test_bin' . exeSuf;
		Process:execute(command: specBin, args: ['--quiet', '-i', root . '/utilities/specinit/SpecInit.spec', '-o', built]);
		return built;
	}

	Function is testHelpAndScaffoldAppAndLib(){
		local String is root: self:resolveRoot();
		local String is si: self:resolveSpecInit(root: root);
		Assert:isTrue(fileExists(path: si));
		if({ !fileExists(path: si) }, {
			return;
		});

		local Int is helpCode: Process:execute(command: si, args: ['--help']);
		Assert:areEqualInt(0, helpCode);

		local String is pid: Process:getPid() as String;
		local String is tmpDir: self:dirOf(path: Uri:tempFile());
		local String is appDir: tmpDir . '/specinit_app_' . pid;
		local String is libDir: tmpDir . '/specinit_lib_' . pid;

		local Int is appCode: Process:execute(command: si, args: [appDir, '--app', '--force']);
		Assert:areEqualInt(0, appCode);
		Assert:isTrue(fileExists(path: appDir . '/specbuild.json'));
		Assert:isTrue(fileExists(path: appDir . '/.gitignore'));
		Assert:isTrue(fileExists(path: appDir . '/src/Main.spec'));
		Assert:isTrue(fileExists(path: appDir . '/tests/MainTest.spec'));

		local String is appManifestRaw: fileRead(path: appDir . '/specbuild.json', default: '', onSuccess: {}, onError: {});
		local Any is parsedApp: Json:parse(text: appManifestRaw);
		Assert:areEqualString('src/Main.spec', Json:getString(obj: parsedApp, key: 'source', default: ''));

		# Without --force, re-running on existing project must fail cleanly (exit 1)
		local Int is dupCode: Process:execute(command: si, args: [appDir]);
		Assert:areEqualInt(1, dupCode);

		local Int is libCode: Process:execute(command: si, args: [libDir, '--lib', '--force']);
		Assert:areEqualInt(0, libCode);
		Assert:isTrue(fileExists(path: libDir . '/specbuild.json'));
		Assert:isTrue(fileExists(path: libDir . '/.gitignore'));
		local String is libManifestRaw: fileRead(path: libDir . '/specbuild.json', default: '', onSuccess: {}, onError: {});
		local Any is parsedLib: Json:parse(text: libManifestRaw);
		Assert:areEqualString('0.1.0', Json:getString(obj: parsedLib, key: 'version', default: ''));
	}
}
