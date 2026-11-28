#! Package base:sys
#! Leveled structured logger (`DEBUG=0`, `INFO=1`, `WARN=2`, `ERROR=3`) with
#! ISO-8601 UTC timestamps and stderr/stdout/file output.

Class is Logger{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()],
		['base', 'sys', as Stderr()],
		['base', 'sys', as File()],
		['base', 'sys', as DateTime()]
	];

	Int is minLevel: 1;
	String is tag: 'app';
	String is filePath: '';
	Boolean is useStderr: true;

	replace Function is init(String is tag: 'app', Int is minLevel: 1, String is filePath: '', Boolean is useStderr: true){
		:tag: tag;
		:minLevel: minLevel;
		:filePath: filePath;
		:useStderr: useStderr;
	}

	Function of String is formatLine(Int is level, String is message){
		local String is lvlName: 'INFO';
		if({ level <= 0 }, { lvlName: 'DEBUG'; });
		if({ level == 2 }, { lvlName: 'WARN'; });
		if({ level >= 3 }, { lvlName: 'ERROR'; });
		local DateTime is ts: DateTime:utcNow();
		return '[' . ts:formatIso() . '] [' . lvlName . '] [' . :tag . '] ' . message;
	}

	Function is log(Int is level, String is message){
		if({ level < :minLevel }, { return; });
		local String is formatted: :formatLine(level: level, message: message);
		if({ :filePath != '' }, {
			File:fileAppend(path: :filePath, content: formatted . "\n", onSuccess: local Function(Int is _n){}, onError: local Function(SpecError of FileError is _e){});
			return;
		});
		if({ :useStderr }, {
			Stderr:line(formatted);
		}, {
			Output:line(formatted);
		});
	}

	Function is debug(String is message){ :log(level: 0, message: message); }
	Function is info(String is message){ :log(level: 1, message: message); }
	Function is warn(String is message){ :log(level: 2, message: message); }
	Function is error(String is message){ :log(level: 3, message: message); }
}
