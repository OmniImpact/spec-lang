#! Package specserv:server
#! Compiles, caches, and executes `.spec` pages implementing `base:net:SpecServePage`.

Class is SpecPageRunner{
	replace [String] is namespace: ['specserv', 'server'];

	merge [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'data', as Json()],
		['base', 'struct', [Array, Map]],
		['base', 'sys', [as Dir(), as File(), as Process(), as Time()]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Int is statusCode: 200;
	String is contentType: 'text/html; charset=utf-8';
	Map of String to String is headers: Map:init();
	String is body: '';
	Boolean is ok: false;
	String is errorMessage: '';

	Function of String is sanitizeKey(String is path){
		local String is out: '';
		local Int is n: path:length();
		times(count: n, worker: local Function(Int is i){
			local String is ch: path:charAt(index: i, default: '');
			if({ (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9') }, {
				out: out . ch;
			}, {
				out: out . '_';
			});
		});
		return out;
	}

	## Extracts the class name declared with `Class of SpecServePage is <Name>`.
	Function of String is extractPageClass(String is src){
		local Int is idx: src:indexOf(search: 'Class of SpecServePage is ', default: -1);
		if({ idx < 0 }, {
			idx: src:indexOf(search: 'Class of base:net:SpecServePage is ', default: -1);
			if({ idx < 0 }, { return ''; });
			idx: idx + 35;
		}, {
			idx: idx + 26;
		});
		local String is rest: src:substring(start: idx, end: src:length()):trim();
		local String is name: '';
		local Int is i: 0;
		while({ i < rest:length() }, {
			local String is ch: rest:charAt(index: i, default: '');
			if({ ch == '{' || ch == ' ' || ch == "\t" || ch == "\n" || ch == "\r" }, {
				return name;
			});
			name: name . ch;
			i++;
		});
		return name;
	}

	## Extracts the namespace segments from `replace [String] is namespace: [...]`.
	Function of [String] is extractNamespace(String is src){
		local [String] is out: [];
		local Int is idx: src:indexOf(search: 'namespace:', default: -1);
		if({ idx < 0 }, { return out; });
		local Int is ob: src:indexOfFrom(search: '[', from: idx, default: -1);
		local Int is cb: src:indexOfFrom(search: ']', from: idx, default: -1);
		if({ ob < 0 || cb <= ob }, { return out; });
		local String is inner: src:substring(start: ob + 1, end: cb);
		local Array of String is parts: inner:split(delimiter: ',');
		times(count: parts:length(), worker: local Function(Int is i){
			local String is p: parts:get(index: i, default: ''):trim();
			if({ (p:startsWith(prefix: '\'') && p:endsWith(suffix: '\'')) || (p:startsWith(prefix: '"') && p:endsWith(suffix: '"')) }, {
				if({ p:length() >= 2 }, {
					out:push(item: p:substring(start: 1, end: p:length() - 1));
				});
			});
		});
		return out;
	}

	Function of String is findSpecCompiler(){
		local String is exeDirPath: exeDir();
		if({ exeDirPath != '' && fileExists(path: exeDirPath . '/spec') }, {
			return exeDirPath . '/spec';
		});
		if({ fileExists(path: 'bin/spec') }, { return 'bin/spec'; });
		return 'spec';
	}

	Function of String is findStdlibDir(){
		if({ dirList(path: 'spec'):length() > 0 }, { return 'spec'; });
		local String is exeDirPath: exeDir();
		if({ exeDirPath != '' && dirList(path: exeDirPath . '/../spec'):length() > 0 }, {
			return exeDirPath . '/../spec';
		});
		return 'spec';
	}

	Function of String is shellQuote(String is s){
		return '\'' . s:replaceAll(search: '\'', replacement: '\'\\\'\'') . '\'';
	}

	Function of String is parentDir(String is path){
		local Int is lastSlash: -1;
		times(count: path:length(), worker: local Function(Int is i){
			if({ path:charAt(index: i, default: '') == '/' }, {
				lastSlash: i;
			});
		});
		if({ lastSlash > 0 }, { return path:substring(start: 0, end: lastSlash); });
		return '';
	}

	Function of String is serializeStrMap(Map of String to String is m){
		local String is out: '{';
		local Array of String is ks: m:keys();
		times(count: ks:length(), worker: local Function(Int is i){
			if({ i > 0 }, { out: out . ','; });
			local String is k: ks:get(index: i, default: '');
			local String is v: m:getString(key: k, default: '');
			out: out . '"' . escapeString(str: k) . '":"' . escapeString(str: v) . '"';
		});
		return out . '}';
	}

	Function of SpecPageRunner is runPage(String is specPath, String is docRoot, Map of String to String is getArgs, Map of String to String is postArgs){
		local SpecPageRunner is res: SpecPageRunner();
		local String is src: fileRead(path: specPath, onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');
		local String is clsName: extractPageClass(src: src);
		if({ clsName == '' }, {
			res:statusCode: 403;
			res:errorMessage: 'Spec file does not implement SpecServePage';
			return res;
		});

		local [String] is ns: extractNamespace(src: src);
		local String is usingEntry: '[';
		local String is nsRelDir: '';
		times(count: ns:length(), worker: local Function(Int is ni){
			local String is seg: ns:get(index: ni);
			usingEntry: usingEntry . '\'' . seg . '\', ';
			nsRelDir: nsRelDir . '/' . seg;
		});
		usingEntry: usingEntry . clsName . ']';

		local String is cacheDir: '/tmp/specserv_cache';
		local String is nsDir: cacheDir . nsRelDir;
		execute(command: 'mkdir', args: Array(['-p', nsDir]));
		local String is key: sanitizeKey(path: specPath);
		local String is binPath: cacheDir . '/' . key . '.bin';
		local String is metaPath: cacheDir . '/' . key . '.meta';
		local String is expectedMeta: specPath . ':' . (src:length() as String);
		local String is existingMeta: fileRead(path: metaPath, onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');

		if({ existingMeta != expectedMeta || !fileExists(path: binPath) }, {
			local String is stagedPagePath: nsDir . '/' . clsName . '.spec';
			fileWrite(path: stagedPagePath, content: src, onSuccess: local Function(Int is _n){}, onError: local Function(Any is _e){});
			local String is runnerPath: cacheDir . '/' . key . '_runner.spec';
			local String is runnerSrc: "#! Package specserv:runner\n"
				. "Class is SpecServRunner{\n"
				. "\treplace [String] is namespace: ['specserv', 'runner'];\n"
				. "\tmerge [[String]] is using: [\n"
				. "\t\t['base', 'core', SpecError],\n"
				. "\t\t['base', 'data', as Json()],\n"
				. "\t\t['base', 'net', SpecServePage],\n"
				. "\t\t['base', 'struct', [Array, Map]],\n"
				. "\t\t['base', 'sys', [as File(), as Process()]],\n"
				. "\t\t['base', 'sys', as Loops()],\n"
				. "\t\t" . usingEntry . "\n"
				. "\t];\n"
				. "\treplace Function is init(){\n"
				. "\t\tlocal String is reqPath: getEnv(key: 'SPECSERV_REQ', default: '');\n"
				. "\t\tlocal String is respPath: getEnv(key: 'SPECSERV_RESP', default: '');\n"
				. "\t\tlocal Map of String to String is gArgs: Map:init();\n"
				. "\t\tlocal Map of String to String is pArgs: Map:init();\n"
				. "\t\tif({ reqPath != '' && fileExists(path: reqPath) }, {\n"
				. "\t\t\tlocal String is reqTxt: fileRead(path: reqPath, onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');\n"
				. "\t\t\tlocal Map of String to Any is root: parseObjectText(text: reqTxt);\n"
				. "\t\t\tif({ root:has(key: 'get') }, {\n"
				. "\t\t\t\tlocal Map of String to Any is gm: root:get(key: 'get', default: Map:init()) as Map;\n"
				. "\t\t\t\tlocal Array of String is gks: gm:keys();\n"
				. "\t\t\t\ttimes(count: gks:length(), worker: local Function(Int is i){\n"
				. "\t\t\t\t\tlocal String is k: gks:get(index: i, default: '');\n"
				. "\t\t\t\t\tgArgs:set(key: k, value: getString(obj: gm, key: k, default: ''));\n"
				. "\t\t\t\t});\n"
				. "\t\t\t});\n"
				. "\t\t\tif({ root:has(key: 'post') }, {\n"
				. "\t\t\t\tlocal Map of String to Any is pm: root:get(key: 'post', default: Map:init()) as Map;\n"
				. "\t\t\t\tlocal Array of String is pks: pm:keys();\n"
				. "\t\t\t\ttimes(count: pks:length(), worker: local Function(Int is i){\n"
				. "\t\t\t\t\tlocal String is k: pks:get(index: i, default: '');\n"
				. "\t\t\t\t\tpArgs:set(key: k, value: getString(obj: pm, key: k, default: ''));\n"
				. "\t\t\t\t});\n"
				. "\t\t\t});\n"
				. "\t\t});\n"
				. "\t\tlocal " . clsName . " is page: " . clsName . "(getArgs: gArgs, postArgs: pArgs);\n"
				. "\t\tlocal String is hdrJson: '{';\n"
				. "\t\tlocal Map of String to String is ph: page:headers();\n"
				. "\t\tlocal Array of String is hks: ph:keys();\n"
				. "\t\ttimes(count: hks:length(), worker: local Function(Int is i){\n"
				. "\t\t\tif({ i > 0 }, { hdrJson: hdrJson . ','; });\n"
				. "\t\t\tlocal String is k: hks:get(index: i, default: '');\n"
				. "\t\t\thdrJson: hdrJson . '\"' . escapeString(str: k) . '\":\"' . escapeString(str: ph:getString(key: k, default: '')) . '\"';\n"
				. "\t\t});\n"
				. "\t\thdrJson: hdrJson . '}';\n"
				. "\t\tlocal String is outJson: '{\"status\":' . (page:statusCode() as String)\n"
				. "\t\t\t. ',\"contentType\":\"' . escapeString(str: page:contentType()) . '\"'\n"
				. "\t\t\t. ',\"headers\":' . hdrJson\n"
				. "\t\t\t. ',\"body\":\"' . escapeString(str: page:body()) . '\"}';\n"
				. "\t\tif({ respPath != '' }, {\n"
				. "\t\t\tfileWrite(path: respPath, content: outJson, onSuccess: local Function(Int is _n){}, onError: local Function(Any is _e){});\n"
				. "\t\t});\n"
				. "\t}\n"
				. "}\n";
			fileWrite(path: runnerPath, content: runnerSrc, onSuccess: local Function(Int is _n){}, onError: local Function(Any is _e){});
			local String is compiler: findSpecCompiler();
			local String is stdlib: findStdlibDir();
			local String is pDir: parentDir(path: specPath);
			local String is pageDir: if({ pDir != '' }, { pDir }, { docRoot });
			local Int is code: execute(
				command: compiler,
				args: Array(['--quiet', '-i', runnerPath, '-s', cacheDir, '-s', docRoot, '-s', pageDir, '-s', stdlib, '-o', binPath])
			);
			if({ code != 0 }, {
				res:statusCode: 500;
				res:errorMessage: 'Failed to compile SpecServePage: ' . specPath;
				return res;
			});
			fileWrite(path: metaPath, content: expectedMeta, onSuccess: local Function(Int is _n){}, onError: local Function(Any is _e){});
		});

		local String is seq: monotonicNs() as String;
		local String is reqPath: cacheDir . '/req_' . seq . '.json';
		local String is respPath: cacheDir . '/resp_' . seq . '.json';

		local String is reqJson: '{"get":' . serializeStrMap(m: getArgs) . ',"post":' . serializeStrMap(m: postArgs) . '}';
		fileWrite(path: reqPath, content: reqJson, onSuccess: local Function(Int is _n){}, onError: local Function(Any is _e){});

		local String is cmd: 'SPECSERV_ROOT=' . shellQuote(s: docRoot)
			. ' SPECSERV_REQ=' . shellQuote(s: reqPath)
			. ' SPECSERV_RESP=' . shellQuote(s: respPath)
			. ' ' . shellQuote(s: binPath);
		local Int is runCode: execute(command: 'sh', args: Array(['-c', cmd]));
		fileRemove(path: reqPath, onError: local Function(Any is _e){});

		if({ runCode != 0 || !fileExists(path: respPath) }, {
			if({ fileExists(path: respPath) }, {
				fileRemove(path: respPath, onError: local Function(Any is _e){});
			});
			res:statusCode: 500;
			res:errorMessage: 'Error executing SpecServePage';
			return res;
		});

		local String is respTxt: fileRead(path: respPath, onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');
		fileRemove(path: respPath, onError: local Function(Any is _e){});

		local Map of String to Any is ro: parseObjectText(text: respTxt);
		if({ !ro:has(key: 'status') }, {
			res:statusCode: 500;
			res:errorMessage: 'Invalid response from SpecServePage';
			return res;
		});
		res:statusCode: getInt(obj: ro, key: 'status', default: 200);
		res:contentType: getString(obj: ro, key: 'contentType', default: 'text/html; charset=utf-8');
		res:body: getString(obj: ro, key: 'body', default: '');
		if({ ro:has(key: 'headers') }, {
			local Map of String to Any is hm: ro:get(key: 'headers', default: Map:init()) as Map;
			local Array of String is hks: hm:keys();
			times(count: hks:length(), worker: local Function(Int is i){
				local String is k: hks:get(index: i, default: '');
				res:headers:set(key: k, value: getString(obj: hm, key: k, default: ''));
			});
		});
		res:ok: true;
		return res;
	}
}
