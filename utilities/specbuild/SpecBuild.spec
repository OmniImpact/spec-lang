#! Package specbuild
#! The SpecBuild orchestrator: manifest-driven project compilation and management.
##
## Reads a specbuild.json manifest, validates source directories, entrypoint source,
## and build flags, and coordinates compiler invocations, test execution, and
## linting. All paths (source, source_dirs, output) are resolved relative to the
## build configuration file.
##
## Usage:
##   specbuild [manifest.json] [command] [options]
##   specbuild [command] [-c <manifest.json>]
##
## Commands:
##   build    Compile target binary (default)
##   run      Compile target binary and execute it
##   install  Compile target binary and install to user desktop/bin
##   test     Execute project unit tests via runner
##   lint     Run speclint over project source directories
##   clean    Remove compiled output binary
##   help     Display usage instructions

Class is SpecBuild{
	replace [String] is namespace: ['specbuild'];

	replace [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'core', Result],
		['base', 'core', SpecError],
		['base', 'data', JsonError],
		['base', 'sys', [Bundle, FileError]],
		['base', 'data', as Json()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Output()],
		['base', 'sys', as Stderr()],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['base', 'sys', as File()],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Uri()],
		['base', 'iterator']
	];

	## Directory portion of a file path ('' when the path has no slash).
	Function of String is dirOf(String is path){
		local String is dp: Uri:fromFilePath(filePath: path):dirPath();
		return Uri:fromFilePath(filePath: dp):toFilePath();
	}

	## Resolves a path relative to the configuration file's directory.
	Function of String is resolvePath(String is baseDir, String is relPath){
		if({ relPath == '' }, {
			return '';
		});
		local Uri is relUri: Uri:fromFilePath(filePath: relPath);
		if({ relUri:isAbsolute() }, {
			return relUri:toFilePath();
		});
		if({ baseDir == '' || baseDir == '.' }, {
			return relUri:toFilePath();
		});
		local Uri is baseUri: Uri:fromFilePath(filePath: baseDir . '/dummy');
		return baseUri:resolve(relativePath: relPath):toFilePath();
	}
	Function of String is resolveCompiler(String is custom){
		if({ custom != '' && fileExists(path: custom) }, {
			return custom;
		});
		local String is envBin: Process:getEnv(key: 'SPEC_BIN', default: '');
		if({ envBin != '' && fileExists(path: envBin) }, {
			return envBin;
		});
		local String is exeDir: Dir:exeDir();
		if({ exeDir != '' && fileExists(path: exeDir . '/spec') }, {
			return exeDir . '/spec';
		});
		if({ exeDir != '' && fileExists(path: exeDir . '/spec.exe') }, {
			return exeDir . '/spec.exe';
		});
		if({ fileExists(path: 'bin/spec') }, {
			return 'bin/spec';
		});
		if({ fileExists(path: 'bin/spec.exe') }, {
			return 'bin/spec.exe';
		});
		return 'spec';
	}

	Function of String is resolveRunner(String is custom){
		if({ custom != '' && fileExists(path: custom) }, {
			return custom;
		});
		local String is exeDir: Dir:exeDir();
		if({ exeDir != '' && fileExists(path: exeDir . '/specunit') }, {
			return exeDir . '/specunit';
		});
		if({ exeDir != '' && fileExists(path: exeDir . '/specunit.exe') }, {
			return exeDir . '/specunit.exe';
		});
		if({ fileExists(path: 'bin/specunit') }, {
			return 'bin/specunit';
		});
		if({ fileExists(path: 'bin/specunit.exe') }, {
			return 'bin/specunit.exe';
		});
		return 'specunit';
	}

	Function of String is resolveLinter(String is custom){
		if({ custom != '' && fileExists(path: custom) }, {
			return custom;
		});
		local String is exeDir: Dir:exeDir();
		if({ exeDir != '' && fileExists(path: exeDir . '/speclint') }, {
			return exeDir . '/speclint';
		});
		if({ exeDir != '' && fileExists(path: exeDir . '/speclint.exe') }, {
			return exeDir . '/speclint.exe';
		});
		if({ fileExists(path: 'bin/speclint') }, {
			return 'bin/speclint';
		});
		if({ fileExists(path: 'bin/speclint.exe') }, {
			return 'bin/speclint.exe';
		});
		return 'speclint';
	}

	local Function is collectBundleEntry(String is srcPath, String is destPath, Array of String is dests, Array of String is payloads){
		if({ !Dir:isDir(path: srcPath) && fileExists(path: srcPath) }, {
			dests:add(item: destPath);
			payloads:add(item: File:fileRead(path: srcPath, onSuccess: {}, onError: {}, default: ''));
			return;
		});
		local Array of String is children: Dir:dirList(path: srcPath);
		local Int is i: 0;
		while({ i < children:length() }, {
			local String is childName: children:get(index: i);
			local String is childSrc: "{{srcPath}}/{{childName}}";
			local String is childDest: if({ destPath == '' }, { childName }, { "{{destPath}}/{{childName}}" });
			collectBundleEntry(srcPath: childSrc, destPath: childDest, dests: dests, payloads: payloads);
			i: i + 1;
		});
	}

	local Function of String is injectCliMetadata(String is rawJson, String is appName, String is appVersion, String is appDescription){
		if({ rawJson:trim() == '' }, { return rawJson; });
		local Map of String to Any is root: Json:parseObjectText(text: rawJson);
		local String is finalName: if({ appName != '' }, { appName }, { Json:getString(obj: root, key: 'name', default: '') });
		local String is finalVer: if({ appVersion != '' }, { appVersion }, { Json:getString(obj: root, key: 'version', default: '') });
		local String is finalDesc: if({ appDescription != '' }, { appDescription }, { Json:getString(obj: root, key: 'description', default: '') });
		local String is usage: Json:getString(obj: root, key: 'usage', default: '');
		local Array of Any is optsArr: Json:getArray(obj: root, key: 'options');

		local String is out: '{"name":"' . Json:escapeString(str: finalName) . '"'
			. ',"version":"' . Json:escapeString(str: finalVer) . '"'
			. ',"description":"' . Json:escapeString(str: finalDesc) . '"';
		if({ usage != '' }, {
			out: out . ',"usage":"' . Json:escapeString(str: usage) . '"';
		});
		out: out . ',"options":[';
		local Int is oi: 0;
		while({ oi < optsArr:length() }, {
			if({ oi > 0 }, { out: out . ','; });
			local Map of String to Any is o: Json:getObjectAt(arr: optsArr, index: oi);
			local String is oShort: Json:getString(obj: o, key: 'short', default: '');
			local String is oLong: Json:getString(obj: o, key: 'long', default: '');
			local String is oType: Json:getString(obj: o, key: 'type', default: 'string');
			local String is oDef: Json:getString(obj: o, key: 'default', default: '');
			local String is oArg: Json:getString(obj: o, key: 'arg', default: '');
			local String is oDesc: Json:getString(obj: o, key: 'description', default: '');
			local Boolean is oReq: Json:getBool(obj: o, key: 'required', default: false);
			out: out . '{"short":"' . Json:escapeString(str: oShort) . '"'
				. ',"long":"' . Json:escapeString(str: oLong) . '"'
				. ',"type":"' . Json:escapeString(str: oType) . '"'
				. ',"default":"' . Json:escapeString(str: oDef) . '"'
				. ',"arg":"' . Json:escapeString(str: oArg) . '"'
				. ',"description":"' . Json:escapeString(str: oDesc) . '"'
				. ',"required":' . if({ oReq }, { 'true' }, { 'false' }) . '}';
			oi: oi + 1;
		});
		out: out . ']}';
		return out;
	}

	local Function is appendBundle(String is configDir, String is output, Array is bundledCfg, String is appName, String is appVersion, String is appDescription, CleoSection is bSec){
		local Array of String is dests: Array();
		local Array of String is payloads: Array();
		local Boolean is hasCliJson: false;
		local Int is i: 0;
		while({ i < bundledCfg:length() }, {
			local Map is entry: Json:getObjectAt(arr: bundledCfg, index: i);
			local String is src: Json:getString(obj: entry, key: 'src', default: Json:getString(obj: entry, key: 'source', default: ''));
			local String is dest: Json:getString(obj: entry, key: 'dest', default: Json:getString(obj: entry, key: 'destination', default: src));
			if({ src != '' }, {
				local String is resolvedSrc: :resolvePath(baseDir: configDir, relPath: src);
				local Int is before: dests:length();
				collectBundleEntry(srcPath: resolvedSrc, destPath: dest, dests: dests, payloads: payloads);
				if({ dests:length() == before }, {
					bSec:addLine(text: "Bundle path not found: {{resolvedSrc}}", color: CleoColor:ansi(code: 203), rightText: '✖ FAILED');
					Process:exit(status: 1);
				});
				if({ dest == 'cli.json' || dest:endsWith(suffix: '/cli.json') }, {
					hasCliJson: true;
				});
			});
			i: i + 1;
		});
		if({ !hasCliJson }, {
			local String is autoCli: :resolvePath(baseDir: configDir, relPath: 'cli.json');
			if({ fileExists(path: autoCli) }, {
				collectBundleEntry(srcPath: autoCli, destPath: 'cli.json', dests: dests, payloads: payloads);
			});
		});
		if({ dests:length() == 0 }, { return; });
		local Int is pi: 0;
		while({ pi < dests:length() }, {
			local String is dPath: dests:get(index: pi, default: '');
			if({ dPath == 'cli.json' || dPath:endsWith(suffix: '/cli.json') }, {
				local String is updated: injectCliMetadata(
					rawJson: payloads:get(index: pi, default: ''),
					appName: appName,
					appVersion: appVersion,
					appDescription: appDescription
				);
				payloads:set(index: pi, item: updated);
			});
			pi: pi + 1;
		});
		local String is blob: Bundle(autoLoad: false):pack(destPaths: dests, payloads: payloads);
		local Boolean is ok: File:fileAppend(
			path: output,
			content: blob,
			onSuccess: local Function(Int is _n){ },
			onError: local Function(SpecError of FileError is _e){ }
		);
		if({ !ok }, {
			bSec:addLine(text: "Failed to append bundle to {{output}}", color: CleoColor:ansi(code: 203), rightText: '✖ FAILED');
			Process:exit(status: 1);
		});
		bSec:addLine(text: "Bundled {{dests:length()}} asset(s)", color: CleoColor:ansi(code: 250), rightText: 'SPECBNDL');
	}

	Function is printHelp() {
		Output:line('SpecBuild - Project Build Orchestrator (Spec 0.1 Alpha)');
		Output:line('');
		Output:line('Usage:');
		Output:line('  specbuild [manifest.json] [command] [options]');
		Output:line('  specbuild [command] [-c <manifest.json>]');
		Output:line('');
		Output:line('Commands:');
		Output:line('  build    Compile target binary (default)');
		Output:line('  run      Compile target binary and execute it');
		Output:line('  install  Compile target binary and install to user desktop/bin');
		Output:line('  test     Execute project unit tests via runner');
		Output:line('  lint     Run speclint over project source directories');
		Output:line('  clean    Remove compiled output binary');
		Output:line('  help     Display usage instructions');
		Output:line('');
		Output:line('Options:');
		Output:line('  -c, --config <file.json>   Path to build manifest (default: <project>.json or specbuild.json)');
		Output:line('  --release, --prod          Build with -O2 optimization for production (default: debug -O0)');
		Output:line('  --debug                    Force debug -O0 build');
		Output:line('  -v, --verbose              Display detailed compiler commands');
		Output:line('  -h, --help                 Display this help message');
	}

	## Resolves the project manifest inside [dir]: checks `<dirname>.json`,
	## then a single `*.json` file in [dir], falling back to `specbuild.json`.
	Function of String is resolveDirManifest(String is dir){
		if({ dir != '.' }, {
			local String is cleanDir: dir;
			if({ cleanDir:endsWith(suffix: '/') && cleanDir:length() > 1 }, {
				cleanDir: cleanDir:substring(start: 0, end: cleanDir:length() - 1);
			});
			local Array of String is parts: cleanDir:split(delimiter: '/');
			local String is baseName: parts:get(index: parts:length() - 1, default: '');
			local String is named: "{{cleanDir}}/{{baseName}}.json";
			if({ baseName != '' && fileExists(path: named) }, {
				return named;
			});
		});
		local String is fallback: if({ dir == '.' }, { 'specbuild.json' }, { "{{dir}}/specbuild.json" });
		if({ fileExists(path: fallback) }, {
			return fallback;
		});
		local String is found: '';
		local Int is count: 0;
		Dir:dirList(path: dir):each(action: local Function(String is entry){
			if({ entry:endsWith(suffix: '.json') && !entry:startsWith(prefix: '.') }, {
				found: if({ dir == '.' }, { entry }, { "{{dir}}/{{entry}}" });
				count: count + 1;
			});
		});
		if({ count == 1 }, {
			return found;
		});
		return fallback;
	}

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():parseOrExit();

		local String is configPath: cli:getString(name: 'config', default: '');
		local String is command: 'build';
		local Boolean is verbose: cli:getBool(name: 'verbose');

		local Array of String is pos: cli:positionals();
		local String is pos0: pos:get(index: 0, default: '');
		local String is pos1: pos:get(index: 1, default: '');

		if({ pos0 != '' }, {
			if({ pos0:endsWith(suffix: '.json') }, {
				if({ configPath == '' }, {
					configPath: pos0;
				});
				if({ pos1 != '' }, {
					command: pos1;
				});
			}, {
				if({ pos0 == 'build' || pos0 == 'run' || pos0 == 'install' || pos0 == 'test' || pos0 == 'clean' || pos0 == 'lint' || pos0 == 'help' }, {
					command: pos0;
					if({ pos1 != '' && pos1:endsWith(suffix: '.json') && configPath == '' }, {
						configPath: pos1;
					});
				}, {
					if({ configPath == '' }, {
						configPath: pos0;
					});
					if({ pos1 != '' }, {
						command: pos1;
					});
				});
			});
		});

		if({ command == 'help' }, {
			:printHelp();
			Process:exit(status: 0);
		});

		if({ configPath == '' }, {
			configPath: resolveDirManifest(dir: '.');
		}, {
			if({ Dir:dirList(path: configPath):length() > 0 }, {
				configPath: resolveDirManifest(dir: configPath);
			});
		});

		if({ !fileExists(path: configPath) }, {
			if({ fileExists(path: "{{configPath}}.json") }, {
				configPath: "{{configPath}}.json";
			}, {
				Stderr:line("[specbuild] Error: Configuration file not found: {{configPath}}");
				Process:exit(status: 1);
			});
		});

		local String is rawText: fileRead(path: configPath, default: '');
		local Result of Map of String to Any to JsonError is cfgR: Json:parseMapResult(text: rawText);
		local String is parseMsg: '';
		match(on: cfgR, when: [
			Result:Ok: local Function of Void(Map of String to Any is v){
			},
			Result:Err: local Function of Void(SpecError of JsonError is e){
				parseMsg: e:description;
			}
		]);
		if({ parseMsg != '' }, {
			Stderr:line('[specbuild] Error: Failed to parse ' . configPath . ': ' . parseMsg);
			Process:exit(status: 1);
		});
		local Map of String to Any is cfg: Map:init();
		match(on: cfgR, when: [
			Result:Ok: local Function of Void(Map of String to Any is v){
				cfg: v;
			},
			Result:Err: local Function of Void(SpecError of JsonError is e){
			}
		]);

		if({ !rawText:trim():startsWith(prefix: '{') }, {
			Stderr:line('[specbuild] Error: Configuration root in ' . configPath . ' must be a JSON object');
			Process:exit(status: 1);
		});

		local String is name: Json:getString(obj: cfg, key: 'name', default: 'app');
		local String is version: Json:getString(obj: cfg, key: 'version', default: '0.1.0');
		local String is description: Json:getString(obj: cfg, key: 'description', default: '');
		local String is rawIcon: Json:getString(obj: cfg, key: 'icon', default: '');
		local String is category: Json:getString(obj: cfg, key: 'category', default: '');
		local Array is fileExtsCfg: Json:getArray(obj: cfg, key: 'file_extensions');
		if({ fileExtsCfg:length() == 0 }, {
			fileExtsCfg: Json:getArray(obj: cfg, key: 'extensions');
		});
		local Array is defaultExtsCfg: Json:getArray(obj: cfg, key: 'default_extensions');
		local String is source: Json:getString(obj: cfg, key: 'source', default: '');
		if({ source == '' }, {
			source: Json:getString(obj: cfg, key: 'entry', default: '');
		});
		local String is rawOutput: Json:getString(obj: cfg, key: 'output', default: '');
		local Array is sourceDirs: Json:getArray(obj: cfg, key: 'source_dirs');
		local Array is flags: Json:getArray(obj: cfg, key: 'flags');
		local Array is bundledCfg: Json:getArray(obj: cfg, key: 'bundled');
		local Map is testsCfg: Json:getObject(obj: cfg, key: 'tests');

		local String is configDir: :dirOf(path: configPath);
		local String is resolvedSource: :resolvePath(baseDir: configDir, relPath: source);
		local String is output: :resolvePath(baseDir: configDir, relPath: rawOutput);

		local String is rawCompiler: Json:getString(obj: cfg, key: 'compiler', default: '');
		local String is customCompiler: '';
		if({ rawCompiler != '' }, {
			customCompiler: :resolvePath(baseDir: configDir, relPath: rawCompiler);
		});
		local String is rawLinter: Json:getString(obj: cfg, key: 'linter', default: '');
		local String is customLinter: '';
		if({ rawLinter != '' }, {
			customLinter: :resolvePath(baseDir: configDir, relPath: rawLinter);
		});

		if({ command == 'clean' }, {
			if({ output == '' }, {
				output: :resolvePath(baseDir: configDir, relPath: 'bin/' . name);
			});
			if({ fileExists(path: output) }, {
				File:fileRemove(path: output);
				Output:line('[specbuild] Removed: ' . output);
			}, {
				if({ fileExists(path: output . '.exe') }, {
					File:fileRemove(path: output . '.exe');
					Output:line('[specbuild] Removed: ' . output . '.exe');
				}, {
					Output:line('[specbuild] Clean: target ' . output . ' does not exist.');
				});
			});
			Process:exit(status: 0);
		});

		if({ command == 'lint' }, {
			local String is linter: :resolveLinter(custom: customLinter);
			local Array of String is lintArgs: Array();
			local Int is dirCount: sourceDirs:length();
			if({ dirCount == 0 }, {
				lintArgs:add(item: '-t');
				if({ configDir != '' }, {
					lintArgs:add(item: configDir);
				}, {
					lintArgs:add(item: '.');
				});
			}, {
				times(count: dirCount, worker: local Function(Int is di){
					local String is sd: Json:getStringAt(arr: sourceDirs, index: di, default: '');
					if({ sd != '' }, {
						lintArgs:add(item: '-t');
						lintArgs:add(item: :resolvePath(baseDir: configDir, relPath: sd));
					});
				});
			});
			Output:line('[specbuild] Linting ' . name . ' via ' . linter);
			local Int is lintCode: Process:execute(command: linter, args: lintArgs);
			Process:exit(status: lintCode);
		});

		if({ command == 'test' }, {
			local String is runnerName: Json:getString(obj: testsCfg, key: 'runner', default: 'specunit');
			local String is resolvedRunner: runnerName;
			if({ runnerName != '' && runnerName != 'specunit' }, {
				resolvedRunner: :resolvePath(baseDir: configDir, relPath: runnerName);
			});
			local String is runner: :resolveRunner(custom: resolvedRunner);
			local String is testCompiler: :resolveCompiler(custom: customCompiler);
			local Array is testDirs: Json:getArray(obj: testsCfg, key: 'dirs');
			local Array of String is testArgs: Array(['-s', testCompiler]);
			local Int is sdCount: sourceDirs:length();
			times(count: sdCount, worker: local Function(Int is si){
				local String is sd: Json:getStringAt(arr: sourceDirs, index: si, default: '');
				if({ sd != '' }, {
					testArgs:add(item: '-S');
					testArgs:add(item: :resolvePath(baseDir: configDir, relPath: sd));
				});
			});
			local Int is tdCount: testDirs:length();
			if({ tdCount == 0 }, {
				testArgs:add(item: '-t');
				testArgs:add(item: :resolvePath(baseDir: configDir, relPath: 'tests'));
			}, {
				times(count: tdCount, worker: local Function(Int is ti){
					local String is td: Json:getStringAt(arr: testDirs, index: ti, default: '');
					if({ td != '' }, {
						testArgs:add(item: '-t');
						testArgs:add(item: :resolvePath(baseDir: configDir, relPath: td));
					});
				});
			});
			Output:line('[specbuild] Running tests for ' . name . ' via ' . runner);
			local Int is testCode: Process:execute(command: runner, args: testArgs);
			Process:exit(status: testCode);
		});

		# Default command: build
		if({ resolvedSource == '' }, {
			Stderr:line('[specbuild] Error: Missing required property \"source\" in ' . configPath);
			Process:exit(status: 1);
		});

		if({ !fileExists(path: resolvedSource) }, {
			Stderr:line('[specbuild] Error: Source file not found: ' . resolvedSource);
			Process:exit(status: 1);
		});

		if({ output == '' }, {
			output: :resolvePath(baseDir: configDir, relPath: 'bin/' . name);
		});

		local String is outParent: :dirOf(path: output);
		if({ outParent != '' && !fileExists(path: outParent) }, {
			Process:execute(command: 'mkdir', args: Array(['-p', outParent]));
		});

		local String is compiler: :resolveCompiler(custom: customCompiler);
		local Array of String is specArgs: Array(['-i', resolvedSource, '-o', output]);
		if({ (args:has(key: 'release') || args:has(key: 'prod')) && !args:has(key: 'debug') }, {
			specArgs:add(item: '--release');
		});
		if({ args:has(key: 'debug') }, {
			specArgs:add(item: '--debug');
		});

		local Int is sLen: sourceDirs:length();
		times(count: sLen, worker: local Function(Int is si){
			local String is sd: Json:getStringAt(arr: sourceDirs, index: si, default: '');
			if({ sd != '' }, {
				specArgs:add(item: '-s');
				specArgs:add(item: :resolvePath(baseDir: configDir, relPath: sd));
			});
		});

		local Int is fLen: flags:length();
		times(count: fLen, worker: local Function(Int is fi){
			local String is flg: Json:getStringAt(arr: flags, index: fi, default: '');
			if({ flg != '' }, {
				specArgs:add(item: flg);
			});
		});

		local Cleo is prepUi: Cleo:toolUi(title: ' specbuild ', directOutput: true);
		local CleoSection is prepSec: prepUi:addToolSection(title: ' Building · ' . name . ' v' . version . ' ');
		prepSec:addLine(text: 'Source: ' . resolvedSource, color: CleoColor:ansi(code: 250), rightText: 'Output: ' . output);
		if({ verbose }, {
			local String is cmdLine: compiler;
			local Int is aiLen: specArgs:length();
			times(count: aiLen, worker: local Function(Int is ai){
				cmdLine: cmdLine . ' ' . specArgs:get(index: ai, default: '');
			});
			prepSec:addLine(text: 'Command: ' . cmdLine, color: CleoColor:ansi(code: 245));
		});
		prepUi:startDirect();
		prepUi:finish();

		local Int is exitCode: Process:execute(command: compiler, args: specArgs);

		local Cleo is ui: Cleo:toolUi(title: ' specbuild ');
		local CleoSection is bSec: ui:addToolSection(title: ' Build · ' . name . ' v' . version . ' ');
		bSec:addLine(text: 'Source: ' . resolvedSource, color: CleoColor:ansi(code: 250), rightText: 'Output: ' . output);
		if({ exitCode != 0 }, {
			bSec:addLine(text: 'Build failed (exit ' . (exitCode as String) . ')', color: CleoColor:ansi(code: 203), rightText: '✖ FAILED');
			ui:render();
			Process:exit(status: exitCode);
		});
		appendBundle(
			configDir: configDir,
			output: output,
			bundledCfg: bundledCfg,
			appName: name,
			appVersion: version,
			appDescription: description,
			bSec: bSec
		);
		bSec:addLine(text: 'Build succeeded -> ' . output, color: CleoColor:ansi(code: 252), rightText: '✔ BUILT');
		ui:render();

		if({ command == 'run' }, {
			local Int is runCode: Process:execute(command: output, args: Array());
			Process:exit(status: runCode);
		});

		if({ command == 'install' }, {
			local String is iconPath: if({ rawIcon != '' }, { :resolvePath(baseDir: configDir, relPath: rawIcon) }, { '' });
			:installApp(
				name: name,
				description: description,
				output: output,
				iconPath: iconPath,
				category: category,
				fileExtsCfg: fileExtsCfg,
				defaultExtsCfg: defaultExtsCfg
			);
		});
	}

	local Function of String is normalizeExt(String is ext){
		local String is e: ext:trim():toLower();
		if({ e == '' }, { return ''; });
		if({ !e:startsWith(prefix: '.') }, { return '.' . e; });
		return e;
	}

	local Function of String is mimeTypeForExt(String is ext){
		local String is e: :normalizeExt(ext: ext);
		if({ e == '.spec' }, { return 'text/x-spec'; });
		if({ e == '.txt' }, { return 'text/plain'; });
		if({ e == '.md' || e == '.markdown' }, { return 'text/markdown'; });
		if({ e == '.json' }, { return 'application/json'; });
		if({ e == '.c' }, { return 'text/x-csrc'; });
		if({ e == '.h' }, { return 'text/x-chdr'; });
		if({ e == '.cpp' || e == '.cc' || e == '.cxx' }, { return 'text/x-c++src'; });
		if({ e == '.hpp' || e == '.hh' || e == '.hxx' }, { return 'text/x-c++hdr'; });
		if({ e == '.py' }, { return 'text/x-python'; });
		if({ e == '.java' }, { return 'text/x-java'; });
		if({ e == '.rs' }, { return 'text/rust'; });
		if({ e == '.rb' }, { return 'application/x-ruby'; });
		if({ e == '.js' || e == '.mjs' || e == '.cjs' || e == '.jsx' }, { return 'text/javascript'; });
		if({ e == '.kt' || e == '.kts' }, { return 'text/x-kotlin'; });
		if({ e == '.css' }, { return 'text/css'; });
		if({ e == '.cs' }, { return 'text/x-csharp'; });
		if({ e == '.php' || e == '.phtml' }, { return 'application/x-php'; });
		if({ e == '.sql' }, { return 'application/sql'; });
		if({ e == '.html' || e == '.htm' || e == '.xhtml' }, { return 'text/html'; });
		if({ e == '.xml' }, { return 'application/xml'; });
		if({ e == '.svg' }, { return 'image/svg+xml'; });
		if({ e:length() > 1 }, {
			return 'text/x-' . e:substring(start: 1, end: e:length());
		});
		return 'text/plain';
	}

	local Function of Boolean is needsCustomMimeDef(String is ext){
		local String is e: :normalizeExt(ext: ext);
		return e == '.spec' || e == '.kt' || e == '.kts';
	}

	local Function of String is normalizeCategory(String is cat){
		local String is c: cat:trim();
		if({ c == '' }, { return 'Utility'; });
		local String is low: c:toLower();
		if({ low == 'utility' || low == 'utilities' || low == 'accessories' }, { return 'Utility'; });
		if({ low == 'development' || low == 'dev' || low == 'ide' }, { return 'Development'; });
		if({ low == 'graphics' }, { return 'Graphics'; });
		if({ low == 'office' }, { return 'Office'; });
		if({ low == 'network' || low == 'internet' }, { return 'Network'; });
		if({ low == 'system' }, { return 'System'; });
		if({ low == 'settings' }, { return 'Settings'; });
		if({ low == 'game' || low == 'games' }, { return 'Game'; });
		return c;
	}

	local Function is appendUniqueStr(Array of String is list, String is val){
		if({ val == '' }, { return; });
		local Int is i: 0;
		while({ i < list:length() }, {
			if({ list:get(index: i, default: '') == val }, { return; });
			i: i + 1;
		});
		list:add(item: val);
	}

	local Function of Boolean is arrayContainsStr(Array of String is list, String is val){
		local Int is i: 0;
		while({ i < list:length() }, {
			if({ list:get(index: i, default: '') == val }, { return true; });
			i: i + 1;
		});
		return false;
	}

	local Function is installApp(
		String is name,
		String is description,
		String is output,
		String is iconPath,
		String is category,
		Array is fileExtsCfg,
		Array is defaultExtsCfg
	){
		local String is os: Process:osName();
		if({ os == 'macos' }, {
			:installMacos(name: name, output: output);
			return;
		});
		if({ os == 'windows' }, {
			:installWindows(name: name, output: output);
			return;
		});
		:installLinux(
			name: name,
			description: description,
			output: output,
			iconPath: iconPath,
			category: category,
			fileExtsCfg: fileExtsCfg,
			defaultExtsCfg: defaultExtsCfg
		);
	}

	local Function is installMacos(String is name, String is output){
		Output:line('[specbuild] macOS install stub: packaging "' . name . '" (' . output . ') into ~/Applications/' . name . '.app is not yet implemented.');
	}

	local Function is installWindows(String is name, String is output){
		Output:line('[specbuild] Windows install stub: installing "' . name . '" (' . output . ') into %LOCALAPPDATA%\\Programs\\' . name . ' is not yet implemented.');
	}

	local Function is installLinux(
		String is name,
		String is description,
		String is output,
		String is iconPath,
		String is category,
		Array is fileExtsCfg,
		Array is defaultExtsCfg
	){
		local String is home: Uri:homeDir();
		if({ home == '' }, {
			Stderr:line('[specbuild] Error: Could not determine user home directory for install.');
			Process:exit(status: 1);
		});

		local String is binDir: home . '/.local/bin';
		local String is appDir: home . '/.local/share/applications';
		local String is mimePkgDir: home . '/.local/share/mime/packages';
		local String is mimeRootDir: home . '/.local/share/mime';
		local String is iconRootDir: home . '/.local/share/icons/hicolor';

		Process:execute(command: 'mkdir', args: Array(['-p', binDir, appDir, mimePkgDir]));

		## 1. Install executable into ~/.local/bin/<name>
		local String is destBin: binDir . '/' . name;
		local Int is cpBin: Process:execute(command: 'cp', args: Array(['-f', output, destBin]));
		if({ cpBin != 0 }, {
			Stderr:line('[specbuild] Error: Failed to copy executable to ' . destBin);
			Process:exit(status: 1);
		});
		Process:execute(command: 'chmod', args: Array(['755', destBin]));

		## 2. Install icon into ~/.local/share/icons/hicolor/...
		local String is iconEntry: '';
		if({ iconPath != '' && fileExists(path: iconPath) }, {
			local String is lowIcon: iconPath:toLower();
			local Boolean is isSvg: lowIcon:endsWith(suffix: '.svg');
			local String is iconSubDir: if({ isSvg }, { iconRootDir . '/scalable/apps' }, { iconRootDir . '/256x256/apps' });
			local String is iconExt: if({ isSvg }, { '.svg' }, { '.png' });
			Process:execute(command: 'mkdir', args: Array(['-p', iconSubDir]));
			local String is destIcon: iconSubDir . '/' . name . iconExt;
			Process:execute(command: 'cp', args: Array(['-f', iconPath, destIcon]));
			iconEntry: name;
		});

		## 3. Collect file extensions, MIME types, and defaults
		local Array of String is defaultExts: Array();
		local Int is di: 0;
		while({ di < defaultExtsCfg:length() }, {
			local String is de: :normalizeExt(ext: Json:getStringAt(arr: defaultExtsCfg, index: di, default: ''));
			:appendUniqueStr(list: defaultExts, val: de);
			di: di + 1;
		});

		local Array of String is mimeTypes: Array();
		local Array of String is defaultMimes: Array();
		local Array of String is customMimes: Array();
		local Array of String is customExts: Array();

		local Int is ei: 0;
		while({ ei < fileExtsCfg:length() }, {
			local String is rawExt: Json:getStringAt(arr: fileExtsCfg, index: ei, default: '');
			local String is ext: '';
			local String is explicitMime: '';
			local Boolean is isDefault: false;
			if({ rawExt != '' }, {
				ext: :normalizeExt(ext: rawExt);
			}, {
				local Map is obj: Json:getObjectAt(arr: fileExtsCfg, index: ei);
				ext: :normalizeExt(ext: Json:getString(obj: obj, key: 'ext', default: ''));
				explicitMime: Json:getString(obj: obj, key: 'mime', default: '');
				isDefault: Json:getBool(obj: obj, key: 'default', default: false);
			});
			if({ ext != '' }, {
				local String is mime: if({ explicitMime != '' }, { explicitMime }, { :mimeTypeForExt(ext: ext) });
				:appendUniqueStr(list: mimeTypes, val: mime);
				if({ isDefault || :arrayContainsStr(list: defaultExts, val: ext) }, {
					:appendUniqueStr(list: defaultMimes, val: mime);
				});
				if({ explicitMime != '' || :needsCustomMimeDef(ext: ext) }, {
					customMimes:add(item: mime);
					customExts:add(item: ext);
				});
			});
			ei: ei + 1;
		});

		## 4. Write custom MIME XML if any custom extensions exist
		if({ customMimes:length() > 0 }, {
			local String is xml: "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<mime-info xmlns=\"http://www.freedesktop.org/standards/shared-mime-info\">\n";
			local Int is ci: 0;
			while({ ci < customMimes:length() }, {
				local String is cm: customMimes:get(index: ci, default: '');
				local String is ce: customExts:get(index: ci, default: '');
				xml: xml . "  <mime-type type=\"" . cm . "\">\n"
					. "    <comment>" . name . " file (" . ce . ")</comment>\n"
					. "    <glob pattern=\"*" . ce . "\"/>\n"
					. "  </mime-type>\n";
				ci: ci + 1;
			});
			xml: xml . "</mime-info>\n";
			local String is mimeXmlPath: mimePkgDir . '/' . name . '.xml';
			File:fileWrite(path: mimeXmlPath, content: xml, onSuccess: {}, onError: {});
			Process:execute(command: 'update-mime-database', args: Array([mimeRootDir]));
		});

		## 5. Write ~/.local/share/applications/<name>.desktop
		local String is normCat: :normalizeCategory(cat: category);
		local String is mimeLine: '';
		local Int is mi: 0;
		while({ mi < mimeTypes:length() }, {
			mimeLine: mimeLine . mimeTypes:get(index: mi, default: '') . ';';
			mi: mi + 1;
		});

		local String is desktop: "[Desktop Entry]\n"
			. "Type=Application\n"
			. "Name=" . name . "\n";
		if({ description != '' }, {
			desktop: desktop . "Comment=" . description . "\n";
		});
		desktop: desktop . "Exec=" . destBin . " %F\n";
		if({ iconEntry != '' }, {
			desktop: desktop . "Icon=" . iconEntry . "\n";
		});
		desktop: desktop . "Terminal=false\n"
			. "Categories=" . normCat . ";\n";
		if({ mimeLine != '' }, {
			desktop: desktop . "MimeType=" . mimeLine . "\n";
		});

		local String is desktopFile: name . '.desktop';
		local String is desktopPath: appDir . '/' . desktopFile;
		File:fileWrite(path: desktopPath, content: desktop, onSuccess: {}, onError: {});

		## 6. Register default MIME associations and refresh Linux desktop menu caches
		local Int is dmi: 0;
		while({ dmi < defaultMimes:length() }, {
			local String is dm: defaultMimes:get(index: dmi, default: '');
			Process:execute(command: 'xdg-mime', args: Array(['default', desktopFile, dm]));
			dmi: dmi + 1;
		});
		Process:execute(command: 'update-desktop-database', args: Array([appDir]));
		if({ iconEntry != '' }, {
			Process:execute(command: 'gtk-update-icon-cache', args: Array(['-f', '-t', iconRootDir]));
		});

		local Cleo is instUi: Cleo:toolUi(title: ' specbuild ');
		local CleoSection is iSec: instUi:addToolSection(title: ' Install · ' . name . ' (Linux) ');
		iSec:addLine(text: 'Binary -> ' . destBin, color: CleoColor:ansi(code: 250), rightText: '✔ BIN');
		if({ iconEntry != '' }, {
			iSec:addLine(text: 'Icon -> ' . iconEntry, color: CleoColor:ansi(code: 250), rightText: '✔ ICON');
		});
		iSec:addLine(text: 'Desktop -> ' . desktopPath, color: CleoColor:ansi(code: 250), rightText: '✔ DESKTOP');
		if({ defaultMimes:length() > 0 }, {
			iSec:addLine(text: 'Default MIME count: ' . (defaultMimes:length() as String), color: CleoColor:ansi(code: 250), rightText: '✔ XDG');
		});
		instUi:render();
	}
}
