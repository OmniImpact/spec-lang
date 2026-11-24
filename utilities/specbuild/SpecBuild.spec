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
##   test     Execute project unit tests via runner
##   lint     Run speclint over project source directories
##   clean    Remove compiled output binary
##   help     Display usage instructions

Class is SpecBuild{
	replace [String] is namespace: ['specbuild'];

	replace [[String]] is using: [
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'core', Result],
		['base', 'core', SpecError],
		['base', 'data', JsonError],
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
		if({ args:has(key: 'h') || args:has(key: 'help') }, {
			:printHelp();
			Process:exit(status: 0);
		});

		local String is configPath: '';
		local String is command: 'build';
		local Boolean is verbose: args:has(key: 'v') || args:has(key: 'verbose');

		if({ args:has(key: 'c') }, {
			configPath: args:getString(key: 'c', default: '');
		});
		if({ configPath == '' && args:has(key: 'config') }, {
			configPath: args:getString(key: 'config', default: '');
		});

		local String is pos0: args:getString(key: '0', default: '');
		local String is pos1: args:getString(key: '1', default: '');

		if({ pos0 != '' }, {
			if({ pos0:endsWith(suffix: '.json') }, {
				if({ configPath == '' }, {
					configPath: pos0;
				});
				if({ pos1 != '' }, {
					command: pos1;
				});
			}, {
				if({ pos0 == 'build' || pos0 == 'run' || pos0 == 'test' || pos0 == 'clean' || pos0 == 'lint' || pos0 == 'help' }, {
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
		local String is source: Json:getString(obj: cfg, key: 'source', default: '');
		if({ source == '' }, {
			source: Json:getString(obj: cfg, key: 'entry', default: '');
		});
		local String is rawOutput: Json:getString(obj: cfg, key: 'output', default: '');
		local Array is sourceDirs: Json:getArray(obj: cfg, key: 'source_dirs');
		local Array is flags: Json:getArray(obj: cfg, key: 'flags');
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
		bSec:addLine(text: 'Build succeeded -> ' . output, color: CleoColor:ansi(code: 252), rightText: '✔ BUILT');
		ui:render();

		if({ command == 'run' }, {
			local Int is runCode: Process:execute(command: output, args: Array());
			Process:exit(status: runCode);
		});
	}
}
