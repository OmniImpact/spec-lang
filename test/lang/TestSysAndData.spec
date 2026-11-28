#! specunit: suite

Class of SpecUnitTest is TestSysAndData{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'core', SpecError],
		['base', 'struct', Array],
		['base', 'data', as Csv()],
		['base', 'math', as Math()],
		['base', 'sys', FileStream],
		['base', 'sys', Logger],
		['base', 'sys', as File()],
		['base', 'sys', as Dir()],
		['base', 'sys', as Path()],
		['base', 'sys', as DateTime()],
		['base', 'sys', as Process()],
		['base', 'sys', as Uri()]
	];

	Function is testFileStreamAndDirAndPath(){
		local String is baseDir: Uri:systemTempDir() . '/spec_sys_test_' . (Process:getPid() as String);
		local String is subDir: Path:join(a: baseDir, b: 'nested/leaf');
		Assert:isTrue(Dir:makeDirAll(path: subDir));
		Assert:isTrue(Dir:isDir(path: subDir));

		local String is fPath: Path:join(a: subDir, b: 'stream.txt');
		Assert:areEqualString('stream.txt', Path:basename(path: fPath));
		Assert:areEqualString('.txt', Path:extension(path: fPath));
		Assert:areEqualString('stream', Path:stem(path: fPath));
		Assert:areEqualString(subDir, Path:dirname(path: fPath));
		Assert:areEqualString('/a/c', Path:normalize(path: '/a/b/../c/./'));
		Assert:isTrue(Path:isAbsolute(path: '/a/c'));
		Assert:isFalse(Path:isAbsolute(path: 'rel/path'));

		local FileStream is ws: FileStream:init();
		Assert:isTrue(ws:open(path: fPath, mode: 'wb'));
		Assert:areEqualInt(11, ws:writeString(text: 'hello-world'));
		Assert:areEqualInt(11, ws:tell());
		Assert:isTrue(ws:flush());
		ws:close();
		Assert:isFalse(ws:isOpen());

		local FileStream is rs: FileStream:init();
		Assert:isTrue(rs:open(path: fPath, mode: 'rb'));
		Assert:areEqualString('hello', rs:readString(maxBytes: 5));
		Assert:isTrue(rs:seek(offset: 6, whence: 0));
		Assert:areEqualInt(6, rs:tell());
		Assert:areEqualString('world', rs:readString(maxBytes: 10));
		rs:close();

		File:fileRemove(path: fPath, onError: local Function(SpecError of FileError is _e){});
		Assert:isTrue(Dir:removeDir(path: subDir));
		Assert:isTrue(Dir:removeDir(path: Path:join(a: baseDir, b: 'nested')));
		Assert:isTrue(Dir:removeDir(path: baseDir));
	}

	Function is testDateTimeParseIsoAndLogger(){
		local DateTime is fallback: DateTime:of(year: 2000, month: 1, day: 1);
		local DateTime is dt: DateTime:parseIso(text: '2026-11-27T14:35:42.25Z', default: fallback);
		Assert:areEqualInt(2026, dt:getYear());
		Assert:areEqualInt(11, dt:getMonth());
		Assert:areEqualInt(27, dt:getDay());
		Assert:areEqualInt(14, dt:getHour());
		Assert:areEqualInt(35, dt:getMinute());
		Assert:areEqualInt(42, dt:getSecond());
		Assert:areEqualInt(250, dt:getMillisecond());
		Assert:areEqualInt(0, dt:getOffsetSec());

		local DateTime is dtOff: DateTime:parseIso(text: '2026-07-04T09:15:00-05:00', default: fallback);
		Assert:areEqualInt(-18000, dtOff:getOffsetSec());
		Assert:areEqualString('2026-07-04T09:15:00.000-05:00', dtOff:formatIso());

		local DateTime is bad: DateTime:parseIso(text: 'not-a-date', default: fallback);
		Assert:areEqualInt(2000, bad:getYear());

		# Logger level filtering + file sink
		local String is logPath: Uri:systemTempDir() . '/spec_log_test_' . (Process:getPid() as String) . '.log';
		File:fileRemove(path: logPath, onError: local Function(SpecError of FileError is _e){});
		local Logger is logger: Logger(tag: 'net', minLevel: 2, filePath: logPath);
		logger:info(message: 'should-skip');
		logger:warn(message: 'warn-msg');
		logger:error(message: 'err-msg');
		local String is logOut: File:fileRead(path: logPath, onSuccess: local Function(String is _s){}, onError: local Function(SpecError of FileError is _e){}, default: '');
		Assert:isFalse(logOut:contains(needle: 'should-skip'));
		Assert:isTrue(logOut:contains(needle: '[WARN] [net] warn-msg'));
		Assert:isTrue(logOut:contains(needle: '[ERROR] [net] err-msg'));
		File:fileRemove(path: logPath, onError: local Function(SpecError of FileError is _e){});
	}

	Function is testCsvAndMathEdgeCases(){
		local String is raw: "name,note,val\n\"Alice, A.\",\"says \"\"hi\"\"\",42\nBob,\"line1\nline2\",99\n";
		local Array of Array of String is rows: Csv:parse(text: raw);
		Assert:areEqualInt(3, rows:length());
		Assert:areEqualString('Alice, A.', rows:get(index: 1):get(index: 0, default: ''));
		Assert:areEqualString('says "hi"', rows:get(index: 1):get(index: 1, default: ''));
		Assert:areEqualString("line1\nline2", rows:get(index: 2):get(index: 1, default: ''));
		local String is back: Csv:stringify(rows: rows);
		local Array of Array of String is rows2: Csv:parse(text: back);
		Assert:areEqualInt(3, rows2:length());
		Assert:areEqualString('says "hi"', rows2:get(index: 1):get(index: 1, default: ''));

		# Math edge cases
		Assert:areClose(3.0, Math:round(value: 2.5), 0.0001);
		Assert:areClose(-3.0, Math:round(value: -2.5), 0.0001);
		Assert:areClose(2.0, Math:floor(value: 2.9), 0.0001);
		Assert:areClose(3.0, Math:ceil(value: 2.1), 0.0001);
		Assert:areClose(5.0, Math:hypot(x: 3.0, y: 4.0), 0.0001);
		Assert:areClose(1.0, Math:sin(value: Math:pi() * 0.5), 0.0001);
		Assert:areClose(1.0, Math:cos(value: 0.0), 0.0001);
	}
}
