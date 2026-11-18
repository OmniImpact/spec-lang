#! specunit: suite
#! Unit tests for the Spec Language Server (utilities/speclsp/SpecLsp.spec).

Class of SpecUnitTest is TestSpecLsp{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'data', as Json()],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Uri()],
		['base', 'sys', as Buf()]
	];

	local Function of String is dirOf(String is path){
		local String is dp: Uri:fromFilePath(filePath: path):dirPath();
		return Uri:fromFilePath(filePath: dp):toFilePath();
	}

	local Function of String is resolveRoot(){
		if({ fileExists(path: 'utilities/speclsp/SpecLsp.spec') }, {
			return '.';
		});
		local String is specEnv: Process:getEnv(key: 'SPEC_BIN', default: '');
		if({ specEnv != '' }, {
			local String is d: :dirOf(path: specEnv);
			if({ fileExists(path: d . '/../utilities/speclsp/SpecLsp.spec') }, {
				return d . '/..';
			});
		});
		local String is exeDir: Dir:exeDir();
		if({ exeDir != '' && fileExists(path: exeDir . '/../utilities/speclsp/SpecLsp.spec') }, {
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

	local Function of String is resolveSpecLsp(String is root){
		local String is exeSuf: Uri:exeSuffix();
		local String is cand: root . '/bin/speclsp' . exeSuf;
		if({ fileExists(path: cand) }, {
			return cand;
		});
		local String is specBin: :resolveCompiler(root: root);
		local String is tmpDir: :dirOf(path: Uri:tempFile());
		local String is built: tmpDir . '/speclsp_test_bin' . exeSuf;
		Process:execute(command: specBin, args: ['--quiet', '-i', root . '/utilities/speclsp/SpecLsp.spec', '-o', built]);
		return built;
	}

	local Function of String is lspFrame(String is jsonBody){
		local Int is byteLen: Buf:bufLength(b: jsonBody);
		return "Content-Length: " . (byteLen as String) . "\r\n\r\n" . jsonBody;
	}

	Function is testInitializeDiagnosticsHoverDefinitionCompletionAndShutdown(){
		local String is root: :resolveRoot();
		local String is lsp: :resolveSpecLsp(root: root);
		Assert:isTrue(fileExists(path: lsp));

		local String is pid: Process:getPid() as String;
		local String is tmpDir: :dirOf(path: Uri:tempFile());
		local String is samplePath: tmpDir . '/speclsp_sample_' . pid . '.spec';
		local String is inPath: tmpDir . '/speclsp_in_' . pid . '.bin';
		local String is outPath: tmpDir . '/speclsp_out_' . pid . '.bin';

		local String is sampleSrc: "Class is Foo{\n\tFunction of Int is bar(Int is x){\n\t\treturn x + 1;\n\t}\n\tFunction is main(){\n\t\tlocal Int is v: bar(x: 2);\n\t}\n}\n";
		fileWrite(path: samplePath, content: sampleSrc, onSuccess: {}, onError: {});

		local String is docUri: Uri:fromFilePath(filePath: samplePath):toString();

		local String is reqs: '';
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}');
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","method":"initialized","params":{}}');
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":' . Json:stringify(value: docUri) . ',"languageId":"spec","version":1,"text":' . Json:stringify(value: sampleSrc) . '}}}');
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","id":2,"method":"textDocument/hover","params":{"textDocument":{"uri":' . Json:stringify(value: docUri) . '},"position":{"line":5,"character":18}}}');
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","id":3,"method":"textDocument/definition","params":{"textDocument":{"uri":' . Json:stringify(value: docUri) . '},"position":{"line":5,"character":18}}}');
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","id":4,"method":"textDocument/completion","params":{"textDocument":{"uri":' . Json:stringify(value: docUri) . '},"position":{"line":5,"character":18}}}');
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","method":"textDocument/didChange","params":{"textDocument":{"uri":' . Json:stringify(value: docUri) . ',"version":2},"contentChanges":[{"text":"Class is Bad {\n\tFunction is x( {\n}"}]}}');
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","method":"textDocument/didClose","params":{"textDocument":{"uri":' . Json:stringify(value: docUri) . '}}}');
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","id":5,"method":"shutdown","params":{}}');
		reqs: reqs . :lspFrame(jsonBody: '{"jsonrpc":"2.0","method":"exit","params":{}}');

		fileWrite(path: inPath, content: reqs, onSuccess: {}, onError: {});

		local Int is code: 1;
		if({ Process:osName() == 'windows' }, {
			local String is lspWin: lsp:replaceAll(search: '/', replacement: '\\');
			local String is inWin: inPath:replaceAll(search: '/', replacement: '\\');
			local String is outWin: outPath:replaceAll(search: '/', replacement: '\\');
			code: Process:execute(command: 'cmd.exe', args: ['/c', lspWin . ' < ' . inWin . ' > ' . outWin]);
		}, {
			code: Process:execute(command: '/bin/sh', args: ['-c', lsp . ' < ' . inPath . ' > ' . outPath]);
		});
		Assert:areEqualInt(0, code);

		local String is outRaw: fileRead(path: outPath, default: '', onSuccess: {}, onError: {});
		Assert:isTrue(outRaw:contains(needle: '"hoverProvider":true'));
		Assert:isTrue(outRaw:contains(needle: '"definitionProvider":true'));
		Assert:isTrue(outRaw:contains(needle: '"name":"speclsp"'));
		Assert:isTrue(outRaw:contains(needle: '"textDocument/publishDiagnostics"'));
		Assert:isTrue(outRaw:contains(needle: 'Function of Int is Foo:bar(Int is x)'));
		Assert:isTrue(outRaw:contains(needle: '"start":{"line":1,"character":0}'));
		Assert:isTrue(outRaw:contains(needle: '"label":"local"'));
		Assert:isTrue(outRaw:contains(needle: '"severity":1'));
		Assert:isTrue(outRaw:contains(needle: '"id":5,"result":null') || outRaw:contains(needle: '"result":null,"id":5'));

		fileRemove(path: samplePath);
		fileRemove(path: inPath);
		fileRemove(path: outPath);
	}

}
