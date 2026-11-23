#! Package speclsp
#! Native Language Server Protocol (LSP) server for Spec.
#! Speaks JSON-RPC 2.0 over stdin/stdout and imports the compiler frontend
#! in-process for diagnostics, hover, go-to-definition, and completion.

Class is SpecLsp{
	namespace: ['speclsp'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'loader', Loader],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'checker', TypeError],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', Error],
		['base', 'core', Result],
		['base', 'core', SpecError],
		['base', 'data', JsonError],
		['base', 'data', as Json()],
		['base', 'data', JsonNull],
		['base', 'data', JsonBool],
		['base', 'data', JsonNumber],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Output()],
		['base', 'sys', as Input()],
		['base', 'sys', as Process()],
		['base', 'sys', as File()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Uri()],
		['base', 'sys', as Dir()],
		['base', 'sys', SourceLocation]
	];

	local Boolean is shutdownRequested: false;
	local String is workspaceRoot: '';
	local Map of String to String is docTexts: [:];
	local Map of String to String is docPaths: [:];
	local Map of String to ProgramNode is docPrograms: [:];

	local Function of String is trimStr(String is s){
		local Int is len: s:length();
		local Int is start: 0;
		local Boolean is scanningStart: true;
		while({ scanningStart && start < len }, {
			local Int is b: s:byteAt(index: start, default: 0);
			if({ b == 32 || b == 9 || b == 13 || b == 10 }, {
				start: start + 1;
			}, {
				scanningStart: false;
			});
		});
		local Int is end: len;
		local Boolean is scanningEnd: true;
		while({ scanningEnd && end > start }, {
			local Int is b: s:byteAt(index: end - 1, default: 0);
			if({ b == 32 || b == 9 || b == 13 || b == 10 }, {
				end: end - 1;
			}, {
				scanningEnd: false;
			});
		});
		return s:substring(start: start, end: end);
	}

	local Function of String is readMessage(){
		local Int is contentLength: -1;
		local Boolean is readingHeaders: true;
		local Boolean is eof: false;
		local Boolean is gotLine: false;
		local String is line: '';
		while({ readingHeaders }, {
			gotLine: false;
			line: '';
			Input:readLine(onLine: local Function(String is t){
				gotLine: true;
				line: t;
			});
			if({ !gotLine }, {
				eof: true;
				readingHeaders: false;
			}, {
				local String is trimmed: trimStr(s: line);
				if({ trimmed == '' }, {
					readingHeaders: false;
				}, {
					local Int is colonIdx: trimmed:indexOf(needle: ':', default: -1);
					if({ colonIdx > 0 }, {
						local String is hName: trimmed:substring(start: 0, end: colonIdx);
						local String is hVal: trimStr(s: trimmed:substring(start: colonIdx + 1, end: trimmed:length()));
						if({ hName == 'Content-Length' || hName == 'content-length' }, {
							contentLength: hVal as Int;
						});
					});
				});
			});
		});
		if({ eof || contentLength <= 0 }, {
			return '';
		});
		return Input:readBytes(count: contentLength);
	}

	local Function is sendRawMessage(String is body){
		local Int is byteLen: body:length();
		Output:consOut(text: "Content-Length: " . (byteLen as String) . "\r\n\r\n" . body);
	}

	local Function is sendMessage(Map of String to Any is msg){
		sendRawMessage(body: Json:stringify(value: msg));
	}

	local Function is sendResponse(Any is reqId, Any is result){
		local Map of String to Any is resp: [:];
		resp['jsonrpc']: '2.0';
		resp['id']: reqId;
		resp['result']: result;
		sendMessage(msg: resp);
	}

	local Function of JsonNumber is jInt(Int is n){
		return JsonNumber:init(rawText: n as String, isFloating: false);
	}

	local Function of JsonBool is jBool(Boolean is b){
		return JsonBool:init(value: b);
	}

	local Function is sendError(Any is reqId, Int is code, String is message){
		local Map of String to Any is errObj: [:];
		errObj['code']: jInt(n: code);
		errObj['message']: message;
		local Map of String to Any is resp: [:];
		resp['jsonrpc']: '2.0';
		resp['id']: reqId;
		resp['error']: errObj;
		sendMessage(msg: resp);
	}

	local Function is sendNotificationRaw(String is method, String is paramsJson){
		sendRawMessage(body: '{"jsonrpc":"2.0","method":' . Json:stringify(value: method) . ',"params":' . paramsJson . '}');
	}

	local Function of String is makeRangeJson(Int is line1Based, Int is col1Based, Int is length){
		local Int is l0: if({ line1Based > 0 }, { line1Based - 1 }, { 0 });
		local Int is c0: if({ col1Based > 0 }, { col1Based - 1 }, { 0 });
		local Int is endC: if({ length > 0 }, { c0 + length }, { c0 + 1 });
		return '{"start":{"line":' . (l0 as String) . ',"character":' . (c0 as String) . '},"end":{"line":' . (l0 as String) . ',"character":' . (endC as String) . '}}';
	}

	local Function of String is makeDiagnosticJson(Int is line, Int is col, Int is length, String is message, Int is severity){
		return '{"range":' . makeRangeJson(line1Based: line, col1Based: col, length: length) . ',"severity":' . (severity as String) . ',"source":"speclsp","message":' . Json:stringify(value: message) . '}';
	}

	local Function is publishDiagnostics(String is uri, Array of String is diags){
		sendNotificationRaw(method: 'textDocument/publishDiagnostics', paramsJson: '{"uri":' . Json:stringify(value: uri) . ',"diagnostics":[' . diags:join(separator: ',') . ']}');
	}

	local Function of String is uriToPath(String is uri){
		if({ uri:startsWith(prefix: 'file://') }, {
			return Uri:parse(text: uri):toFilePath();
		});
		return uri;
	}

	local Function of String is pathToUri(String is filePath){
		return Uri:fromFilePath(filePath: filePath):toString();
	}

	local Function is addDirIfExists(Loader is loader, String is dirPath){
		if({ dirPath != '' && fileExists(path: dirPath) }, {
			loader:addSourceDir(dir: dirPath);
		});
	}

	local Function is addProjectSourceDirs(Loader is loader, String is parentDir){
		local String is dir: parentDir;
		while([Boolean is searching: dir != ''], { searching }, {
			local Array of String is parts: dir:split(delimiter: '/');
			local String is baseName: parts:get(index: parts:length() - 1, default: '');
			local String is namedPath: "{{dir}}/{{baseName}}.json";
			local String is manifestPath: if({ baseName != '' && fileExists(path: namedPath) }, { namedPath }, { "{{dir}}/specbuild.json" });
			if({ fileExists(path: manifestPath) }, {
				local String is raw: fileRead(path: manifestPath, default: '');
				if({ raw != '' }, {
					local Result of Map of String to Any to JsonError is manR: Json:parseMapResult(text: raw);
					match(on: manR, when: [
						Result:Ok: local Function of Void(Map is parsed){
							local Array is srcDirs: Json:getArray(obj: parsed, key: 'source_dirs');
							local Int is n: srcDirs:length();
							while([Int is i: 0], { i < n }, {
								local String is sd: Json:getStringAt(arr: srcDirs, index: i, default: '');
								if({ sd != '' }, {
									addDirIfExists(loader: loader, dirPath: dir . '/' . sd);
								});
								i++;
							});
						},
						Result:Err: local Function of Void(SpecError of JsonError is e){
						}
					]);
				});
				searching: false;
			}, {
				if({ :workspaceRoot != '' && dir == :workspaceRoot }, {
					searching: false;
				}, {
					local String is up: Uri:fromFilePath(filePath: Uri:fromFilePath(filePath: dir):dirPath()):toFilePath();
					if({ up == '' || up == dir }, {
						searching: false;
					}, {
						dir: up;
					});
				});
			});
		});

		if({ :workspaceRoot != '' }, {
			addDirIfExists(loader: loader, dirPath: :workspaceRoot . '/spec');
			addDirIfExists(loader: loader, dirPath: :workspaceRoot . '/utilities/specunit');
		});

		local String is exeDir: Dir:exeDir();
		if({ exeDir != '' }, {
			addDirIfExists(loader: loader, dirPath: exeDir . '/../spec');
			addDirIfExists(loader: loader, dirPath: exeDir . '/../utilities/specunit');
		});
	}

	local Function is analyzeFullFile(String is uri, String is filePath){
		local Array of String is diags: Array();
		if({ filePath == '' || !fileExists(path: filePath) }, {
			publishDiagnostics(uri: uri, diags: diags);
			return;
		});

		local Loader is loader: Loader:init();
		local String is parentDir: Uri:fromFilePath(filePath: Uri:fromFilePath(filePath: filePath):dirPath()):toFilePath();
		if({ parentDir != '' }, {
			loader:addSourceDir(dir: parentDir);
		});
		if({ :workspaceRoot != '' }, {
			loader:addSourceDir(dir: :workspaceRoot);
		});
		if({ parentDir != '' }, {
			addProjectSourceDirs(loader: loader, parentDir: parentDir);
		});

		local ProgramNode is prog: loader:loadProgram(rootPath: filePath);
		local Array of String is parseErrors: loader:getParseErrors();
		if({ parseErrors:length() > 0 }, {
			parseErrors:each(action: local Function(String is errStr){
				diags:add(item: makeDiagnosticJson(line: 1, col: 1, length: 1, message: errStr, severity: 1));
			});
			loader:cleanup();
			:docPrograms[uri]: prog;
			publishDiagnostics(uri: uri, diags: diags);
			return;
		});
		loader:cleanup();

		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is typeErrors: tc:checkProgram(program: prog);
		tc:cleanup();

		typeErrors:each(action: local Function(TypeError is te){
			if({ te:file == '' || te:file == filePath }, {
				diags:add(item: makeDiagnosticJson(line: te:line, col: te:col, length: te:length, message: te:message, severity: 1));
			});
		});

		:docPrograms[uri]: prog;
		publishDiagnostics(uri: uri, diags: diags);
	}

	local Function is analyzeSyntaxOnly(String is uri, String is text){
		local Array of String is diags: Array();
		local Lexer is lx: Lexer:init(source: text);
		local Parser is p: Parser:init(tokens: lx:tokenize());
		p:parseProgram();
		if({ p:hasErrors() }, {
			p:getErrors():each(action: local Function(Error is err){
				local SourceLocation is loc: err:getLocation();
				diags:add(item: makeDiagnosticJson(line: loc:getLine(), col: loc:getCol(), length: loc:getLength(), message: err:getMessage(), severity: 1));
			});
		});
		publishDiagnostics(uri: uri, diags: diags);
	}

	local Function of Boolean is isIdentChar(Int is b){
		return (b >= 97 && b <= 122) || (b >= 65 && b <= 90) || (b >= 48 && b <= 57) || b == 95;
	}

	local Function of String is getLineAt(String is text, Int is targetLine0){
		local Int is len: text:length();
		local Int is curLine: 0;
		local Int is lineStart: 0;
		local Int is i: 0;
		local String is result: '';
		local Boolean is found: false;
		while({ !found && i <= len }, {
			local Boolean is isEnd: i == len;
			local Int is b: if({ !isEnd }, { text:byteAt(index: i, default: 0) }, { 10 });
			if({ b == 10 || isEnd }, {
				if({ curLine == targetLine0 }, {
					local Int is endIdx: i;
					if({ endIdx > lineStart && text:byteAt(index: endIdx - 1, default: 0) == 13 }, {
						endIdx: endIdx - 1;
					});
					result: text:substring(start: lineStart, end: endIdx);
					found: true;
				});
				curLine: curLine + 1;
				lineStart: i + 1;
			});
			i: i + 1;
		});
		return result;
	}

	local Function of Array of String is extractSymbolAt(String is text, Int is line0, Int is char0){
		local String is lineStr: getLineAt(text: text, targetLine0: line0);
		local Int is len: lineStr:length();
		if({ len == 0 }, {
			return ['', ''];
		});
		local Int is pos: if({ char0 >= len }, { len - 1 }, { char0 });
		if({ pos < 0 }, { pos: 0; });

		local Int is start: pos;
		while({ start > 0 && isIdentChar(b: lineStr:byteAt(index: start - 1, default: 0)) }, {
			start: start - 1;
		});
		local Int is end: pos;
		while({ end < len && isIdentChar(b: lineStr:byteAt(index: end, default: 0)) }, {
			end: end + 1;
		});
		local String is word: lineStr:substring(start: start, end: end);
		local String is qualifier: '';

		if({ start >= 2 && lineStr:byteAt(index: start - 1, default: 0) == 58 }, {
			local Int is qEnd: start - 1;
			local Int is qStart: qEnd;
			while({ qStart > 0 && isIdentChar(b: lineStr:byteAt(index: qStart - 1, default: 0)) }, {
				qStart: qStart - 1;
			});
			qualifier: lineStr:substring(start: qStart, end: qEnd);
		});
		return [qualifier, word];
	}

	local Function of String is formatType(Type is t){
		if({ t:params:length() == 0 }, {
			return t:name;
		});
		if({ t:name == 'Map' && t:params:length() == 2 }, {
			return 'Map of ' . formatType(t: t:params:get(index: 0)) . ' to ' . formatType(t: t:params:get(index: 1));
		});
		return t:name . ' of ' . formatType(t: t:params:get(index: 0));
	}

	local Function of String is formatMemberSig(ClassInfo is cls, Member is m){
		if({ m:kind == MemberKind:METHOD }, {
			local String is sig: 'Function';
			if({ m:memberType:name == 'Function' }, {
				if({ m:memberType:params:length() > 0 }, {
					sig: sig . ' of ' . formatType(t: m:memberType:params:get(index: 0));
				});
			}, {
				if({ m:memberType:name != '' && m:memberType:name != 'Void' }, {
					sig: sig . ' of ' . formatType(t: m:memberType);
				});
			});
			sig: sig . ' is ' . cls:name . ':' . m:name . '(';
			local Int is pi: 0;
			m:params:each(action: local Function(Parameter is p){
				if({ pi > 0 }, {
					sig: sig . ', ';
				});
				sig: sig . formatType(t: p:paramType) . ' is ' . p:name;
				pi: pi + 1;
			});
			return sig . ')';
		});
		if({ m:kind == MemberKind:FIELD }, {
			return formatType(t: m:memberType) . ' is ' . cls:name . ':' . m:name;
		});
		return 'Class ' . cls:name . ':' . m:name;
	}

	local Function of ClassInfo is findClass(ProgramNode is prog, String is name){
		local ClassInfo is found: ClassInfo:init(name: '', baseClass: '', members: []);
		local Boolean is matched: false;
		prog:classes:each(action: local Function(ClassInfo is c){
			if({ !matched && c:name == name }, {
				found: c;
				matched: true;
			});
		});
		return found;
	}

	local Function is handleHover(Any is reqId, Map of String to Any is params){
		local Map of String to Any is td: Json:getObject(obj: params, key: 'textDocument');
		local String is uri: Json:getString(obj: td, key: 'uri', default: '');
		local Map of String to Any is pos: Json:getObject(obj: params, key: 'position');
		local Int is line0: Json:getInt(obj: pos, key: 'line', default: 0);
		local Int is char0: Json:getInt(obj: pos, key: 'character', default: 0);

		if({ !:docTexts:has(key: uri) || !:docPrograms:has(key: uri) }, {
			sendResponse(reqId: reqId, result: JsonNull:init());
			return;
		});

		local String is text: :docTexts:getString(key: uri, default: '');
		local ProgramNode is prog: :docPrograms:get(key: uri, default: ProgramNode:init(classes: []));
		local Array of String is sym: extractSymbolAt(text: text, line0: line0, char0: char0);
		local String is qual: sym:get(index: 0, default: '');
		local String is word: sym:get(index: 1, default: '');

		if({ word == '' }, {
			sendResponse(reqId: reqId, result: JsonNull:init());
			return;
		});

		local String is hoverMd: '';
		if({ qual != '' }, {
			local ClassInfo is qc: findClass(prog: prog, name: qual);
			if({ qc:name != '' }, {
				qc:members:each(action: local Function(Member is m){
					if({ hoverMd == '' && m:name == word }, {
						hoverMd: "```spec\n" . formatMemberSig(cls: qc, m: m) . "\n```";
					});
				});
			});
		});

		if({ hoverMd == '' }, {
			local ClassInfo is cls: findClass(prog: prog, name: word);
			if({ cls:name != '' }, {
				local String is parents: '';
				if({ cls:baseClasses:length() > 0 }, {
					parents: ' of ' . cls:baseClasses:join(separator: ', ');
				});
				hoverMd: "```spec\nClass" . parents . " is " . cls:name . "\n```";
			});
		});

		if({ hoverMd == '' }, {
			local String is filePath: :docPaths:getString(key: uri, default: '');
			prog:classes:each(action: local Function(ClassInfo is c){
				if({ hoverMd == '' && c:sourceFile == filePath }, {
					c:members:each(action: local Function(Member is m){
						if({ hoverMd == '' && m:name == word }, {
							hoverMd: "```spec\n" . formatMemberSig(cls: c, m: m) . "\n```";
						});
					});
				});
			});
		});

		if({ hoverMd == '' }, {
			sendResponse(reqId: reqId, result: JsonNull:init());
			return;
		});

		local Map of String to Any is contents: [:];
		contents['kind']: 'markdown';
		contents['value']: hoverMd;
		local Map of String to Any is result: [:];
		result['contents']: contents;
		sendResponse(reqId: reqId, result: result);
	}

	local Function is handleDefinition(Any is reqId, Map of String to Any is params){
		local Map of String to Any is td: Json:getObject(obj: params, key: 'textDocument');
		local String is uri: Json:getString(obj: td, key: 'uri', default: '');
		local Map of String to Any is pos: Json:getObject(obj: params, key: 'position');
		local Int is line0: Json:getInt(obj: pos, key: 'line', default: 0);
		local Int is char0: Json:getInt(obj: pos, key: 'character', default: 0);

		if({ !:docTexts:has(key: uri) || !:docPrograms:has(key: uri) }, {
			sendResponse(reqId: reqId, result: JsonNull:init());
			return;
		});

		local String is text: :docTexts:getString(key: uri, default: '');
		local ProgramNode is prog: :docPrograms:get(key: uri, default: ProgramNode:init(classes: []));
		local Array of String is sym: extractSymbolAt(text: text, line0: line0, char0: char0);
		local String is qual: sym:get(index: 0, default: '');
		local String is word: sym:get(index: 1, default: '');

		if({ word == '' }, {
			sendResponse(reqId: reqId, result: JsonNull:init());
			return;
		});

		local String is targetFile: '';
		local Int is targetLine: 0;

		if({ qual != '' }, {
			local ClassInfo is qc: findClass(prog: prog, name: qual);
			if({ qc:name != '' }, {
				qc:members:each(action: local Function(Member is m){
					if({ targetFile == '' && m:name == word && m:line > 0 }, {
						targetFile: if({ m:sourceFile != '' }, { m:sourceFile }, { qc:sourceFile });
						targetLine: m:line;
					});
				});
			});
		});

		if({ targetFile == '' }, {
			local ClassInfo is cls: findClass(prog: prog, name: word);
			if({ cls:name != '' && cls:sourceFile != '' && cls:line > 0 }, {
				targetFile: cls:sourceFile;
				targetLine: cls:line;
			});
		});

		if({ targetFile == '' }, {
			local String is filePath: :docPaths:getString(key: uri, default: '');
			prog:classes:each(action: local Function(ClassInfo is c){
				if({ targetFile == '' && c:sourceFile == filePath }, {
					c:members:each(action: local Function(Member is m){
						if({ targetFile == '' && m:name == word && m:line > 0 }, {
							targetFile: if({ m:sourceFile != '' }, { m:sourceFile }, { c:sourceFile });
							targetLine: m:line;
						});
					});
				});
			});
		});

		if({ targetFile == '' }, {
			sendResponse(reqId: reqId, result: JsonNull:init());
			return;
		});

		sendRawMessage(body: '{"jsonrpc":"2.0","id":' . Json:stringify(value: reqId) . ',"result":{"uri":' . Json:stringify(value: pathToUri(filePath: targetFile)) . ',"range":' . makeRangeJson(line1Based: targetLine, col1Based: 1, length: word:length()) . '}}');
	}

	local Function of String is makeCompletionItemJson(String is label, Int is kind, String is detail){
		local String is out: '{"label":' . Json:stringify(value: label) . ',"kind":' . (kind as String);
		if({ detail != '' }, {
			out: out . ',"detail":' . Json:stringify(value: detail);
		});
		return out . '}';
	}

	local Function is handleCompletion(Any is reqId, Map of String to Any is params){
		local Map of String to Any is td: Json:getObject(obj: params, key: 'textDocument');
		local String is uri: Json:getString(obj: td, key: 'uri', default: '');
		local Map of String to Any is pos: Json:getObject(obj: params, key: 'position');
		local Int is line0: Json:getInt(obj: pos, key: 'line', default: 0);
		local Int is char0: Json:getInt(obj: pos, key: 'character', default: 0);

		local Array of String is items: Array();
		local String is text: :docTexts:getString(key: uri, default: '');
		local ProgramNode is prog: :docPrograms:get(key: uri, default: ProgramNode:init(classes: []));

		local String is lineStr: getLineAt(text: text, targetLine0: line0);
		local Int is cPos: if({ char0 > lineStr:length() }, { lineStr:length() }, { char0 });
		local Boolean is hasColonPrefix: false;
		local String is receiverName: '';

		if({ cPos > 0 && lineStr:byteAt(index: cPos - 1, default: 0) == 58 }, {
			hasColonPrefix: true;
			local Int is rEnd: cPos - 1;
			local Int is rStart: rEnd;
			while({ rStart > 0 && isIdentChar(b: lineStr:byteAt(index: rStart - 1, default: 0)) }, {
				rStart: rStart - 1;
			});
			receiverName: lineStr:substring(start: rStart, end: rEnd);
		});

		if({ hasColonPrefix && receiverName != '' }, {
			local ClassInfo is rc: findClass(prog: prog, name: receiverName);
			if({ rc:name != '' }, {
				rc:members:each(action: local Function(Member is m){
					local Int is kind: if({ m:kind == MemberKind:METHOD }, { 2 }, { 5 });
					items:add(item: makeCompletionItemJson(label: m:name, kind: kind, detail: formatMemberSig(cls: rc, m: m)));
				});
			});
			sendRawMessage(body: '{"jsonrpc":"2.0","id":' . Json:stringify(value: reqId) . ',"result":[' . items:join(separator: ',') . ']}');
			return;
		});

		local Array of String is keywords: Array(['local', 'contained', 'replace', 'merge', 'held', 'is', 'as', 'of', 'to', 'return', 'Class', 'Enum']);
		keywords:each(action: local Function(String is kw){
			items:add(item: makeCompletionItemJson(label: kw, kind: 14, detail: 'keyword'));
		});

		local Array of String is prims: Array(['Int', 'Byte', 'Float', 'Boolean', 'String', 'Function', 'Any']);
		prims:each(action: local Function(String is pt){
			items:add(item: makeCompletionItemJson(label: pt, kind: 7, detail: 'primitive type'));
		});

		prog:classes:each(action: local Function(ClassInfo is c){
			items:add(item: makeCompletionItemJson(label: c:name, kind: 7, detail: 'Class'));
		});

		sendRawMessage(body: '{"jsonrpc":"2.0","id":' . Json:stringify(value: reqId) . ',"result":[' . items:join(separator: ',') . ']}');
	}

	local Function is handleRequest(Map of String to Any is req){
		local String is method: Json:getString(obj: req, key: 'method', default: '');
		local Boolean is hasId: req:has(key: 'id');
		local Any is reqId: if({ hasId }, { req['id'] }, { JsonNull:init() });
		local Map of String to Any is params: Json:getObject(obj: req, key: 'params');

		match(on: method, when: [
			'initialize': {
				local String is rootUri: Json:getString(obj: params, key: 'rootUri', default: '');
				if({ rootUri != '' }, {
					:workspaceRoot: uriToPath(uri: rootUri);
				}, {
					local String is rootPath: Json:getString(obj: params, key: 'rootPath', default: '');
					if({ rootPath != '' }, {
						:workspaceRoot: rootPath;
					});
				});

				local Map of String to Any is caps: [:];
				caps['textDocumentSync']: jInt(n: 1);
				caps['hoverProvider']: jBool(b: true);
				caps['definitionProvider']: jBool(b: true);

				local Map of String to Any is compOpts: [:];
				local Array of String is triggers: Array([':']);
				compOpts['triggerCharacters']: triggers;
				caps['completionProvider']: compOpts;

				local Map of String to Any is info: [:];
				info['name']: 'speclsp';
				info['version']: '0.1.0';

				local Map of String to Any is res: [:];
				res['capabilities']: caps;
				res['serverInfo']: info;
				sendResponse(reqId: reqId, result: res);
			},
			'initialized': { },
			'shutdown': {
				:shutdownRequested: true;
				sendResponse(reqId: reqId, result: JsonNull:init());
			},
			'exit': {
				local Int is exitCode: if({ :shutdownRequested }, { 0 }, { 1 });
				Process:exit(status: exitCode);
			},
			'textDocument/didOpen': {
				local Map of String to Any is td: Json:getObject(obj: params, key: 'textDocument');
				local String is uri: Json:getString(obj: td, key: 'uri', default: '');
				local String is text: Json:getString(obj: td, key: 'text', default: '');
				local String is fpath: uriToPath(uri: uri);
				:docTexts[uri]: text;
				:docPaths[uri]: fpath;
				analyzeFullFile(uri: uri, filePath: fpath);
			},
			'textDocument/didSave': {
				local Map of String to Any is td: Json:getObject(obj: params, key: 'textDocument');
				local String is uri: Json:getString(obj: td, key: 'uri', default: '');
				local String is fpath: uriToPath(uri: uri);
				if({ fpath != '' && fileExists(path: fpath) }, {
					:docTexts[uri]: fileRead(path: fpath, default: '', onSuccess: {}, onError: {});
				});
				:docPaths[uri]: fpath;
				analyzeFullFile(uri: uri, filePath: fpath);
			},
			'textDocument/didChange': {
				local Map of String to Any is td: Json:getObject(obj: params, key: 'textDocument');
				local String is uri: Json:getString(obj: td, key: 'uri', default: '');
				local Array of Any is changes: Json:getArray(obj: params, key: 'contentChanges');
				if({ changes:length() > 0 }, {
					local Any is lastChange: changes:get(index: changes:length() - 1);
					local String is newText: Json:getString(obj: lastChange, key: 'text', default: '');
					:docTexts[uri]: newText;
					analyzeSyntaxOnly(uri: uri, text: newText);
				});
			},
			'textDocument/didClose': {
				local Map of String to Any is td: Json:getObject(obj: params, key: 'textDocument');
				local String is uri: Json:getString(obj: td, key: 'uri', default: '');
				:docTexts:remove(key: uri);
				:docPaths:remove(key: uri);
				:docPrograms:remove(key: uri);
				local Array of String is emptyDiags: Array();
				publishDiagnostics(uri: uri, diags: emptyDiags);
			},
			'textDocument/hover': {
				handleHover(reqId: reqId, params: params);
			},
			'textDocument/definition': {
				handleDefinition(reqId: reqId, params: params);
			},
			'textDocument/completion': {
				handleCompletion(reqId: reqId, params: params);
			},
			else: {
				if({ hasId }, {
					sendError(reqId: reqId, code: -32601, message: "Method not found: " . method);
				});
			}
		]);
	}

	Function is init(Map of String to String is args){
		:docPrograms: [:];
		Input:setBinaryMode();
		local Boolean is running: true;
		while({ running }, {
			local String is payload: readMessage();
			if({ payload == '' }, {
				running: false;
			}, {
				local Any is parsed: Json:parse(text: payload);
				handleRequest(req: parsed);
			});
		});
	}
}
