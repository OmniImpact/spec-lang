#! Package base:sys
#! Cross-platform filesystem path manipulation utilities.

Class is Path{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Returns `true` if [path] is absolute (`/` prefix or Windows drive prefix).
	Function of Boolean is isAbsolute(String is path){
		if({ path:startsWith(prefix: '/') || path:startsWith(prefix: "\\") }, { return true; });
		if({ path:length() >= 2 && path:substring(start: 1, end: 2) == ':' }, { return true; });
		return false;
	}

	## Normalizes separators to `/` and resolves `.` and `..` segments.
	Function of String is normalize(String is path){
		if({ path == '' }, { return '.'; });
		local String is p: path:replaceAll(search: "\\", replacement: '/');
		local Boolean is abs: p:startsWith(prefix: '/');
		local Array of String is parts: p:split(delimiter: '/');
		local Array of String is stack: Array();
		local Int is i: 0;
		while({ i < parts:length() }, {
			local String is seg: parts:get(index: i, default: '');
			if({ seg == '' || seg == '.' }, {
				# skip
			}, {
				if({ seg == '..' }, {
					if({ stack:length() > 0 && stack:get(index: stack:length() - 1, default: '') != '..' }, {
						stack:pop(default: '');
					}, {
						if({ !abs }, { stack:add(item: '..'); });
					});
				}, {
					stack:add(item: seg);
				});
			});
			i: i + 1;
		});
		if({ stack:length() == 0 }, {
			return if({ abs }, { '/' }, { '.' });
		});
		local String is out: if({ abs }, { '/' }, { '' });
		i: 0;
		while({ i < stack:length() }, {
			if({ i > 0 }, { out: out . '/'; });
			out: out . stack:get(index: i, default: '');
			i: i + 1;
		});
		return out;
	}

	## Joins [a] and [b] with `/` (returns normalized [b] if [b] is absolute).
	Function of String is join(String is a, String is b){
		if({ a == '' }, { return :normalize(path: b); });
		if({ b == '' }, { return :normalize(path: a); });
		if({ :isAbsolute(path: b) }, { return :normalize(path: b); });
		return :normalize(path: a . '/' . b);
	}

	local Function of Int is lastByteIndex(String is s, Int is ch){
		local Int is i: s:byteLength() - 1;
		while({ i >= 0 }, {
			if({ s:byteAt(index: i, default: 0) == ch }, { return i; });
			i: i - 1;
		});
		return -1;
	}

	## Returns the final path component (filename) of [path].
	Function of String is basename(String is path){
		local String is n: :normalize(path: path);
		if({ n == '/' || n == '.' }, { return n; });
		local Int is slash: :lastByteIndex(s: n, ch: 47);
		if({ slash < 0 }, { return n; });
		return n:substring(start: slash + 1, end: n:length());
	}

	## Returns the parent directory of [path].
	Function of String is dirname(String is path){
		local String is n: :normalize(path: path);
		if({ n == '/' }, { return '/'; });
		local Int is slash: :lastByteIndex(s: n, ch: 47);
		if({ slash < 0 }, { return '.'; });
		if({ slash == 0 }, { return '/'; });
		return n:substring(start: 0, end: slash);
	}

	## Returns the file extension including leading `.` (e.g. `'.spec'`), or `''`.
	Function of String is extension(String is path){
		local String is base: :basename(path: path);
		local Int is dot: :lastByteIndex(s: base, ch: 46);
		if({ dot <= 0 }, { return ''; });
		return base:substring(start: dot, end: base:length());
	}

	## Returns the filename without its last extension.
	Function of String is stem(String is path){
		local String is base: :basename(path: path);
		local Int is dot: :lastByteIndex(s: base, ch: 46);
		if({ dot <= 0 }, { return base; });
		return base:substring(start: 0, end: dot);
	}
}
