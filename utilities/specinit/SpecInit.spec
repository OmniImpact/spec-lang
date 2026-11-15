#! Package specinit
#! The SpecInit project scaffolder: creates new Spec applications and libraries
#! with a specbuild.json manifest, .gitignore, source files, and starter SpecUnit tests.
##
## Usage:
##   specinit <project_path> [--app | --lib] [--force]
##   specinit --help

Class is SpecInit{
	namespace: ['specinit'];

	replace Array of Array of String is using: [
		['base', 'data', as Json()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Output()],
		['base', 'sys', as Stderr()],
		['base', 'sys', as Process()],
		['base', 'sys', as File()],
		['base', 'sys', as Buf()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Uri()]
	];

	Function is printUsage(){
		Output:line(text: "SpecInit — Spec Project Scaffolder");
		Output:line(text: "Usage: specinit <project_path> [--app | --lib] [--force]");
		Output:line(text: "");
		Output:line(text: "Options:");
		Output:line(text: "  --app     Create an executable application project (default)");
		Output:line(text: "  --lib     Create a reusable library project");
		Output:line(text: "  --force   Overwrite existing files if specbuild.json already exists");
		Output:line(text: "  --help    Display this help message");
	}

	local Function of String is joinPath(String is baseDir, String is relPath){
		if({ baseDir == '' || baseDir == '.' }, {
			return Uri:fromFilePath(filePath: relPath):toFilePath();
		});
		local Uri is baseUri: Uri:fromFilePath(filePath: baseDir . '/dummy');
		return baseUri:resolve(relativePath: relPath):toFilePath();
	}

	local Function of String is extractProjectName(String is path){
		local String is norm: Uri:fromFilePath(filePath: path):toFilePath();
		local Int is len: norm:length();
		while({ len > 1 && (norm:substring(start: len - 1, end: len) == '/' || norm:substring(start: len - 1, end: len) == '\\') }, {
			norm: norm:substring(start: 0, end: len - 1);
			len: norm:length();
		});
		local Int is lastSlash: -1;
		while([Int is i: 0], { i < len }, {
			local String is ch: norm:substring(start: i, end: i + 1);
			if({ ch == '/' || ch == '\\' }, {
				lastSlash: i;
			});
			i: i + 1;
		});
		if({ lastSlash >= 0 && lastSlash + 1 < len }, {
			return norm:substring(start: lastSlash + 1, end: len);
		});
		return norm;
	}

	local Function of String is sanitizeIdent(String is raw, Boolean is isPascal){
		local String is out: '';
		local Boolean is capNext: isPascal;
		local Int is len: raw:length();
		while([Int is i: 0], { i < len }, {
			local String is ch: raw:substring(start: i, end: i + 1);
			local Int is code: Buf:bufGetByte(b: raw, idx: i, def: 0);
			local Boolean is isLower: code >= 97 && code <= 122;
			local Boolean is isUpper: code >= 65 && code <= 90;
			local Boolean is isDigit: code >= 48 && code <= 57;
			if({ isLower || isUpper || isDigit }, {
				if({ out == '' && isDigit }, {
					out: 'p';
				});
				if({ capNext && isLower }, {
					out: out . String:fromCharCode(code: code - 32);
				}, {
					if({ !capNext && isUpper && !isPascal }, {
						out: out . String:fromCharCode(code: code + 32);
					}, {
						out: out . ch;
					});
				});
				capNext: false;
			}, {
				capNext: true;
			});
			i: i + 1;
		});
		if({ out == '' }, {
			return if({ isPascal }, { 'App' }, { 'app' });
		});
		return out;
	}

	local Function of Boolean is ensureDir(String is dirPath){
		if({ dirPath == '' || dirPath == '.' }, {
			return true;
		});
		local Int is code: Process:execute(command: 'mkdir', args: ['-p', dirPath]);
		return code == 0;
	}

	local Function of Boolean is writeFileChecked(String is path, String is content){
		local Boolean is ok: File:fileWrite(path: path, content: content, onSuccess: {}, onError: {});
		if({ !ok }, {
			Stderr:line(text: "Error: Failed to write '" . path . "'");
		});
		return ok;
	}

	local Function of String is buildManifest(String is projectName, String is entrySource, String is outputBin, Array of String is sourceDirs){
		local Map of String to Any is manifest: [:];
		manifest['name']: projectName;
		manifest['version']: '0.1.0';
		manifest['source']: entrySource;
		manifest['source_dirs']: sourceDirs;
		manifest['output']: outputBin;

		local Array of String is flags: ['--quiet'];
		manifest['flags']: flags;

		local Map of String to Any is tests: [:];
		local Array of String is testDirs: ['tests'];
		tests['dirs']: testDirs;
		tests['runner']: 'specunit';
		manifest['tests']: tests;

		return Json:format(value: manifest) . "\n";
	}

	local Function of String is buildGitignore(){
		return "bin/\n.spec_cache/\n*.c\n*.o\n";
	}

	local Function of String is buildMainSpec(String is projectName, String is pkgName){
		local String is s: "#! " . projectName . " — Spec Application\n\n";
		s: s . "Class is Main{\n";
		s: s . "\tnamespace: ['" . pkgName . "'];\n\n";
		s: s . "\treplace Array of Array of String is using: [\n";
		s: s . "\t\t['base', 'sys', as Output()],\n";
		s: s . "\t\t['base', 'struct', Map]\n";
		s: s . "\t];\n\n";
		s: s . "\tFunction is init(Map of String to String is args){\n";
		s: s . "\t\tOutput:line(text: \"Hello from " . projectName . "!\");\n";
		s: s . "\t}\n";
		s: s . "}\n";
		return s;
	}

	local Function of String is buildLibSpec(String is projectName, String is pkgName, String is className){
		local String is s: "#! " . projectName . " — Spec Library\n\n";
		s: s . "Class is " . className . "{\n";
		s: s . "\tnamespace: ['" . pkgName . "'];\n\n";
		s: s . "\tFunction of String is version(){\n";
		s: s . "\t\treturn '0.1.0';\n";
		s: s . "\t}\n\n";
		s: s . "\tFunction of String is greet(String is name){\n";
		s: s . "\t\treturn \"Hello, \" . name . \"!\";\n";
		s: s . "\t}\n";
		s: s . "}\n";
		return s;
	}

	local Function of String is buildAppTestSpec(String is projectName, String is pkgName){
		local String is s: "#! specunit: suite\n";
		s: s . "#! Starter unit tests for " . projectName . ".\n\n";
		s: s . "Class of SpecUnitTest is MainTest{\n";
		s: s . "\tnamespace: ['" . pkgName . "', 'tests'];\n\n";
		s: s . "\treplace Array of Array of String is using: [\n";
		s: s . "\t\t['specunit', SpecUnitTest],\n";
		s: s . "\t\t['specunit', SpecUnitRunner],\n";
		s: s . "\t\t['specunit', as Assert()]\n";
		s: s . "\t];\n\n";
		s: s . "\tFunction is testSanity(){\n";
		s: s . "\t\tAssert:isTrue(true);\n";
		s: s . "\t\tAssert:areEqualInt(2, 1 + 1);\n";
		s: s . "\t}\n";
		s: s . "}\n";
		return s;
	}

	local Function of String is buildLibTestSpec(String is projectName, String is pkgName, String is className, String is testClass){
		local String is s: "#! specunit: suite\n";
		s: s . "#! Starter unit tests for " . projectName . ".\n\n";
		s: s . "Class of SpecUnitTest is " . testClass . "{\n";
		s: s . "\tnamespace: ['" . pkgName . "', 'tests'];\n\n";
		s: s . "\treplace Array of Array of String is using: [\n";
		s: s . "\t\t['specunit', SpecUnitTest],\n";
		s: s . "\t\t['specunit', SpecUnitRunner],\n";
		s: s . "\t\t['specunit', as Assert()],\n";
		s: s . "\t\t['" . pkgName . "', " . className . "]\n";
		s: s . "\t];\n\n";
		s: s . "\tFunction is testLibrary(){\n";
		s: s . "\t\tlocal " . className . " is lib: " . className . ":init();\n";
		s: s . "\t\tAssert:areEqualString('0.1.0', lib:version());\n";
		s: s . "\t\tAssert:areEqualString('Hello, Spec!', lib:greet(name: 'Spec'));\n";
		s: s . "\t}\n";
		s: s . "}\n";
		return s;
	}

	Function is init(Map of String to String is args){
		if({ args:has(key: 'h') || args:has(key: 'help') }, {
			printUsage();
			return;
		});

		local String is targetPath: args:getString(key: '0', default: '');
		local Boolean is isLib: args:has(key: 'lib');
		local Boolean is force: args:has(key: 'f') || args:has(key: 'force');

		if({ args:has(key: '1') }, {
			Stderr:line(text: "Error: Unexpected argument '" . args:getString(key: '1', default: '') . "'");
			printUsage();
			Process:exit(status: 2);
		});

		if({ targetPath == '' }, {
			Stderr:line(text: "Error: Missing <project_path> argument.");
			printUsage();
			Process:exit(status: 2);
		});

		local String is projectName: extractProjectName(path: targetPath);
		if({ projectName == '' || projectName == '.' }, {
			projectName: 'spec_project';
		});
		local String is pkgName: sanitizeIdent(raw: projectName, isPascal: false);
		local String is pascalName: sanitizeIdent(raw: projectName, isPascal: true);

		local String is manifestPath: joinPath(baseDir: targetPath, relPath: 'specbuild.json');
		if({ File:fileExists(path: manifestPath) && !force }, {
			Stderr:line(text: "Error: '" . manifestPath . "' already exists. Pass --force to overwrite.");
			Process:exit(status: 1);
		});

		local String is srcDir: joinPath(baseDir: targetPath, relPath: 'src');
		local String is testsDir: joinPath(baseDir: targetPath, relPath: 'tests');
		if({ !ensureDir(dirPath: targetPath) || !ensureDir(dirPath: srcDir) || !ensureDir(dirPath: testsDir) }, {
			Stderr:line(text: "Error: Could not create project directories under '" . targetPath . "'");
			Process:exit(status: 1);
		});

		local String is gitignorePath: joinPath(baseDir: targetPath, relPath: '.gitignore');
		if({ !writeFileChecked(path: gitignorePath, content: buildGitignore()) }, {
			Process:exit(status: 1);
		});

		if({ isLib }, {
			local String is libFile: pascalName . '.spec';
			local String is testClass: pascalName . 'Test';
			local String is testFile: testClass . '.spec';
			local String is entryRel: 'tests/' . testFile;
			local String is outRel: 'bin/' . pkgName . '_tests';
			local Array of String is srcDirs: ['src', 'tests'];

			if({ !writeFileChecked(path: manifestPath, content: buildManifest(projectName: projectName, entrySource: entryRel, outputBin: outRel, sourceDirs: srcDirs)) }, {
				Process:exit(status: 1);
			});
			if({ !writeFileChecked(path: joinPath(baseDir: srcDir, relPath: libFile), content: buildLibSpec(projectName: projectName, pkgName: pkgName, className: pascalName)) }, {
				Process:exit(status: 1);
			});
			if({ !writeFileChecked(path: joinPath(baseDir: testsDir, relPath: testFile), content: buildLibTestSpec(projectName: projectName, pkgName: pkgName, className: pascalName, testClass: testClass)) }, {
				Process:exit(status: 1);
			});
		}, {
			local String is entryRel: 'src/Main.spec';
			local String is outRel: 'bin/' . pkgName;
			local Array of String is srcDirs: ['src'];

			if({ !writeFileChecked(path: manifestPath, content: buildManifest(projectName: projectName, entrySource: entryRel, outputBin: outRel, sourceDirs: srcDirs)) }, {
				Process:exit(status: 1);
			});
			if({ !writeFileChecked(path: joinPath(baseDir: srcDir, relPath: 'Main.spec'), content: buildMainSpec(projectName: projectName, pkgName: pkgName)) }, {
				Process:exit(status: 1);
			});
			if({ !writeFileChecked(path: joinPath(baseDir: testsDir, relPath: 'MainTest.spec'), content: buildAppTestSpec(projectName: projectName, pkgName: pkgName)) }, {
				Process:exit(status: 1);
			});
		});

		local String is modeLabel: if({ isLib }, { 'library' }, { 'application' });
		Output:line(text: "Initialized Spec " . modeLabel . " project '" . projectName . "' at " . targetPath);
	}
}
