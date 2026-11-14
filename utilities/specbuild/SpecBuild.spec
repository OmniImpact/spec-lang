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
	namespace: ['specbuild'];

	replace Array of Array of String is using: [
		['base', 'data', as Json()],
		['base', 'data', JsonNumber],
		['base', 'data', JsonBool],
		['base', 'data', JsonNull],
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
		['base', 'iterator']
	];

	## Directory portion of a file path ('' when the path has no slash).
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

	## Resolves a path relative to the configuration file's directory.
	Function of String is resolvePath(String is baseDir, String is relPath){
		if({ relPath == '' || relPath:startsWith(prefix: '/') }, {
			return relPath;
		});
		if({ baseDir == '' || baseDir == '.' }, {
			return relPath;
		});
		if({ relPath == '.' }, {
			return baseDir;
		});
		if({ relPath:startsWith(prefix: baseDir . '/') }, {
			return relPath;
		});
		if({ relPath:startsWith(prefix: '../') && !baseDir:contains(needle: '/') }, {
			return relPath:substring(start: 3, end: relPath:length());
		});
		return baseDir . '/' . relPath;
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
		Output:line('  test     Execute project unit tests via runner');
		Output:line('  lint     Run speclint over project source directories');
		Output:line('  clean    Remove compiled output binary');
		Output:line('  help     Display usage instructions');
		Output:line('');
		Output:line('Options:');
		Output:line('  -c, --config <file.json>   Path to build manifest (default: specbuild.json)');
		Output:line('  -v, --verbose              Display detailed compiler commands');
		Output:line('  -h, --help                 Display this help message');
	}

	replace Function is init(Map of String to String is args){
		if({ args:has(key: 'h') || args:has(key: 'help') }, {
			self:printHelp();
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
				if({ pos0 == 'build' || pos0 == 'test' || pos0 == 'clean' || pos0 == 'lint' || pos0 == 'help' }, {
					command: pos0;
					if({ pos1 != '' && pos1:endsWith(suffix: '.json') && configPath == '' }, {
						configPath: pos1;
					});
				}, {
					if({ configPath == '' }, {
						configPath: pos0;
					});
				});
			});
		});

		if({ command == 'help' }, {
			self:printHelp();
			Process:exit(status: 0);
		});

		if({ configPath == '' }, {
			configPath: 'specbuild.json';
		});

		if({ !fileExists(path: configPath) }, {
			if({ fileExists(path: configPath . '.json') }, {
				configPath: configPath . '.json';
			}, {
				Stderr:line('[specbuild] Error: Configuration file not found: ' . configPath);
				Process:exit(status: 1);
			});
		});

		local String is rawText: fileRead(path: configPath, default: '');
		local Any is parsedConfig: Json:parse(text: rawText);
		if({ Json:hasError() }, {
			Stderr:line('[specbuild] Error: Failed to parse ' . configPath . ': ' . Json:errorMessage());
			Process:exit(status: 1);
		});

		local String is cfgType: Introspection:typeIdentity(obj: parsedConfig);
		if({ cfgType != 'Map' }, {
			Stderr:line('[specbuild] Error: Configuration root in ' . configPath . ' must be a JSON object');
			Process:exit(status: 1);
		});

		local Map is cfg: parsedConfig as Map;
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

		local String is configDir: self:dirOf(path: configPath);
		local String is resolvedSource: self:resolvePath(baseDir: configDir, relPath: source);
		local String is output: self:resolvePath(baseDir: configDir, relPath: rawOutput);

		if({ command == 'clean' }, {
			if({ output == '' }, {
				output: self:resolvePath(baseDir: configDir, relPath: 'bin/' . name);
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
			local String is linter: self:resolveLinter(custom: '');
			local Array of String is lintArgs: [];
			local Int is dirCount: sourceDirs:length();
			if({ dirCount == 0 }, {
				lintArgs:add(item: '-t');
				if({ configDir != '' }, {
					lintArgs:add(item: configDir);
				}, {
					lintArgs:add(item: '.');
				});
			}, {
				while([Int is di: 0], { di < dirCount }, {
					local String is sd: Json:getStringAt(arr: sourceDirs, index: di, default: '');
					if({ sd != '' }, {
						lintArgs:add(item: '-t');
						lintArgs:add(item: self:resolvePath(baseDir: configDir, relPath: sd));
					});
					di++;
				});
			});
			Output:line('[specbuild] Linting ' . name . ' via ' . linter);
			local Int is lintCode: Process:execute(command: linter, args: lintArgs);
			Process:exit(status: lintCode);
		});

		if({ command == 'test' }, {
			local String is runnerName: Json:getString(obj: testsCfg, key: 'runner', default: 'specunit');
			local String is runner: self:resolveRunner(custom: runnerName);
			local Array is testDirs: Json:getArray(obj: testsCfg, key: 'dirs');
			local Array of String is testArgs: [];
			local Int is tdCount: testDirs:length();
			if({ tdCount == 0 }, {
				testArgs:add(item: '-t');
				testArgs:add(item: self:resolvePath(baseDir: configDir, relPath: 'tests'));
			}, {
				while([Int is ti: 0], { ti < tdCount }, {
					local String is td: Json:getStringAt(arr: testDirs, index: ti, default: '');
					if({ td != '' }, {
						testArgs:add(item: '-t');
						testArgs:add(item: self:resolvePath(baseDir: configDir, relPath: td));
					});
					ti++;
				});
			});
			Output:line('[specbuild] Running tests for ' . name . ' via ' . runner);
			local Int is testCode: Process:execute(command: runner, args: testArgs);
			Process:exit(status: testCode);
		});

		# Default command: build
		if({ resolvedSource == '' }, {
			Stderr:line('[specbuild] Error: Missing required property "source" in ' . configPath);
			Process:exit(status: 1);
		});

		if({ !fileExists(path: resolvedSource) }, {
			Stderr:line('[specbuild] Error: Source file not found: ' . resolvedSource);
			Process:exit(status: 1);
		});

		if({ output == '' }, {
			output: self:resolvePath(baseDir: configDir, relPath: 'bin/' . name);
		});

		local String is outParent: self:dirOf(path: output);
		if({ outParent != '' && !fileExists(path: outParent) }, {
			Process:execute(command: 'mkdir', args: ['-p', outParent]);
		});

		local String is compiler: self:resolveCompiler(custom: '');
		local Array of String is specArgs: ['-i', resolvedSource, '-o', output];

		local Int is sLen: sourceDirs:length();
		while([Int is si: 0], { si < sLen }, {
			local String is sd: Json:getStringAt(arr: sourceDirs, index: si, default: '');
			if({ sd != '' }, {
				specArgs:add(item: '-s');
				specArgs:add(item: self:resolvePath(baseDir: configDir, relPath: sd));
			});
			si++;
		});

		local Int is fLen: flags:length();
		while([Int is fi: 0], { fi < fLen }, {
			local String is flg: Json:getStringAt(arr: flags, index: fi, default: '');
			if({ flg != '' }, {
				specArgs:add(item: flg);
			});
			fi++;
		});

		Output:line('[specbuild] Building ' . name . ' v' . version);
		Output:line('  source:  ' . resolvedSource);
		Output:line('  output:  ' . output);

		if({ verbose }, {
			local String is cmdLine: compiler;
			local Int is aiLen: specArgs:length();
			while([Int is ai: 0], { ai < aiLen }, {
				cmdLine: cmdLine . ' ' . specArgs:get(index: ai, default: '');
				ai++;
			});
			Output:line('  command: ' . cmdLine);
		});

		local Int is exitCode: Process:execute(command: compiler, args: specArgs);
		if({ exitCode != 0 }, {
			Stderr:line('[specbuild] Build failed with exit code ' . (exitCode as String));
			Process:exit(status: exitCode);
		});

		Output:line('[specbuild] Build succeeded -> ' . output);
	}
}
