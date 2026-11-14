#! Package base:sys
#! Uniform Resource Identifier (URI) and cross-platform path abstraction.
##
## Centralizes URI parsing and filesystem path conversions across POSIX and
## Windows platforms. Supports file:// URIs, Windows drive letters, UNC paths,
## path normalization (resolving . and .. segments), and relative resolution.

Class is Uri{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Process()]
	];

	## URI scheme (e.g. 'file', 'http', or '' for relative/schemeless).
	local String is scheme: '';

	## Authority component (e.g. host, or host:port, or UNC server).
	local String is authority: '';

	## Normalized hierarchical path using forward slashes.
	## Windows drive letters start with a leading slash in URI form (e.g. '/C:/dir').
	local String is path: '';

	## Query component (without leading '?').
	local String is query: '';

	## Fragment component (without leading '#').
	local String is fragment: '';

	## Initializes a URI instance.
	replace Function is init(String is scheme: '', String is authority: '', String is path: '', String is query: '', String is fragment: ''){
		self:scheme: scheme;
		self:authority: authority;
		self:path: path;
		self:query: query;
		self:fragment: fragment;
	}

	## True if [ch] is an ASCII letter.
	Function of Boolean is isAlpha(String is ch){
		if({ ch:length() != 1 }, {
			return false;
		});
		return (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z');
	}

	## True if [p] starts with a Windows drive letter (e.g. 'C:' or '/C:').
	Function of Boolean is hasDrivePrefix(String is p){
		local Int is len: p:length();
		if({ len >= 2 }, {
			local String is c0: p:charAt(index: 0, default: '');
			local String is c1: p:charAt(index: 1, default: '');
			if({ self:isAlpha(ch: c0) && c1 == ':' }, {
				return true;
			});
		});
		if({ len >= 3 }, {
			local String is c0: p:charAt(index: 0, default: '');
			local String is c1: p:charAt(index: 1, default: '');
			local String is c2: p:charAt(index: 2, default: '');
			if({ c0 == '/' && self:isAlpha(ch: c1) && c2 == ':' }, {
				return true;
			});
		});
		return false;
	}

	## Normalizes a path by replacing backslashes with slashes, collapsing redundant
	## slashes, and resolving '.' and '..' segments.
	Function of String is cleanPath(String is rawPath){
		if({ rawPath == '' }, {
			return '';
		});
		local String is p: rawPath:replaceAll(search: '\\', replacement: '/');
		local Boolean is isAbs: p:startsWith(prefix: '/');

		# Check if starts with a Windows drive letter: 'C:' or 'C:/...'
		local String is drivePrefix: '';
		if({ p:length() >= 2 }, {
			local String is c0: p:charAt(index: 0, default: '');
			local String is c1: p:charAt(index: 1, default: '');
			if({ self:isAlpha(ch: c0) && c1 == ':' }, {
				drivePrefix: c0 . ':';
				p: p:substring(start: 2, end: p:length());
				if({ p:startsWith(prefix: '/') }, {
					isAbs: true;
				});
			});
		});
		if({ drivePrefix == '' && p:length() >= 3 }, {
			local String is c0: p:charAt(index: 0, default: '');
			local String is c1: p:charAt(index: 1, default: '');
			local String is c2: p:charAt(index: 2, default: '');
			if({ c0 == '/' && self:isAlpha(ch: c1) && c2 == ':' }, {
				drivePrefix: '/' . c1 . ':';
				isAbs: true;
				p: p:substring(start: 3, end: p:length());
			});
		});

		local Array of String is rawSegs: p:split(delimiter: '/');
		local Array of String is segs: [];
		local Int is rawLen: rawSegs:length();
		while([Int is i: 0], { i < rawLen }, {
			local String is seg: rawSegs:get(index: i, default: '');
			if({ seg != '' && seg != '.' }, {
				if({ seg == '..' }, {
					if({ segs:length() > 0 }, {
						local String is top: segs:get(index: segs:length() - 1, default: '');
						if({ top == '..' }, {
							if({ !isAbs }, {
								segs:add(item: '..');
							});
						}, {
							segs:pop(default: '');
						});
					}, {
						if({ !isAbs }, {
							segs:add(item: '..');
						});
					});
				}, {
					segs:add(item: seg);
				});
			});
			i++;
		});

		local String is joined: segs:join(separator: '/');
		if({ drivePrefix != '' }, {
			if({ isAbs }, {
				if({ joined != '' }, {
					return drivePrefix . '/' . joined;
				}, {
					return drivePrefix . '/';
				});
			}, {
				if({ joined != '' }, {
					return drivePrefix . joined;
				}, {
					return drivePrefix;
				});
			});
		});

		if({ isAbs }, {
			return '/' . joined;
		});
		if({ joined == '' }, {
			return '.';
		});
		return joined;
	}

	## Creates a URI from a local or UNC filesystem path.
	## Handles Windows drive letters ('C:\foo' -> 'file:///C:/foo'), UNC paths
	## ('\\server\share\file' -> 'file://server/share/file'), and POSIX paths.
	Function of Uri is fromFilePath(String is filePath){
		if({ filePath == '' }, {
			return Uri:init();
		});
		local String is p: filePath:replaceAll(search: '\\', replacement: '/');

		# UNC path: //server/share/...
		if({ p:startsWith(prefix: '//') }, {
			local String is rest: p:substring(start: 2, end: p:length());
			local Int is slashIdx: rest:indexOf(search: '/', default: -1);
			if({ slashIdx < 0 }, {
				return Uri:init(scheme: 'file', authority: rest, path: '/');
			});
			local String is auth: rest:substring(start: 0, end: slashIdx);
			local String is rem: rest:substring(start: slashIdx, end: rest:length());
			return Uri:init(scheme: 'file', authority: auth, path: self:cleanPath(rawPath: rem));
		});

		# Windows drive letter: C:/... or C:...
		if({ p:length() >= 2 }, {
			local String is c0: p:charAt(index: 0, default: '');
			local String is c1: p:charAt(index: 1, default: '');
			if({ self:isAlpha(ch: c0) && c1 == ':' }, {
				local String is norm: self:cleanPath(rawPath: '/' . p);
				return Uri:init(scheme: 'file', authority: '', path: norm);
			});
		});
		if({ p:length() >= 3 }, {
			local String is c0: p:charAt(index: 0, default: '');
			local String is c1: p:charAt(index: 1, default: '');
			local String is c2: p:charAt(index: 2, default: '');
			if({ c0 == '/' && self:isAlpha(ch: c1) && c2 == ':' }, {
				local String is norm: self:cleanPath(rawPath: p);
				return Uri:init(scheme: 'file', authority: '', path: norm);
			});
		});

		# POSIX absolute path: /foo/...
		if({ p:startsWith(prefix: '/') }, {
			local String is norm: self:cleanPath(rawPath: p);
			return Uri:init(scheme: 'file', authority: '', path: norm);
		});

		# Relative path
		local String is norm: self:cleanPath(rawPath: p);
		return Uri:init(scheme: '', authority: '', path: norm);
	}

	## Parses an RFC URI string or filesystem path into a Uri.
	Function of Uri is parse(String is text){
		if({ text == '' }, {
			return Uri:init();
		});

		# file:// URI
		if({ text:startsWith(prefix: 'file://') }, {
			local String is rest: text:substring(start: 7, end: text:length());
			if({ rest:startsWith(prefix: '/') }, {
				# file:///path
				return self:fromFilePath(filePath: rest);
			});
			local Int is slashIdx: rest:indexOf(search: '/', default: -1);
			if({ slashIdx < 0 }, {
				return Uri:init(scheme: 'file', authority: rest, path: '/');
			});
			local String is auth: rest:substring(start: 0, end: slashIdx);
			local String is rem: rest:substring(start: slashIdx, end: rest:length());
			return Uri:init(scheme: 'file', authority: auth, path: self:cleanPath(rawPath: rem));
		});

		# Other scheme: scheme://...
		if({ text:contains(needle: '://') }, {
			local Int is sEnd: text:indexOf(search: '://', default: -1);
			local String is sch: text:substring(start: 0, end: sEnd);
			local String is afterSch: text:substring(start: sEnd + 3, end: text:length());
			local String is auth: '';
			local String is p: '';
			local Int is slashIdx: afterSch:indexOf(search: '/', default: -1);
			if({ slashIdx < 0 }, {
				auth: afterSch;
				p: '/';
			}, {
				auth: afterSch:substring(start: 0, end: slashIdx);
				p: afterSch:substring(start: slashIdx, end: afterSch:length());
			});
			return Uri:init(scheme: sch, authority: auth, path: self:cleanPath(rawPath: p));
		});

		# Schemeless string -> treat as filesystem path
		return self:fromFilePath(filePath: text);
	}

	## Returns a standardized filesystem path representation using forward slashes.
	## Strips leading '/' for Windows drive letters (e.g. '/C:/dir' -> 'C:/dir').
	Function of String is toFilePath(){
		if({ self:path == '' }, {
			return '';
		});
		local String is p: self:path;
		# Strip leading slash before Windows drive letter: /C:/foo -> C:/foo
		if({ p:length() >= 3 }, {
			local String is c0: p:charAt(index: 0, default: '');
			local String is c1: p:charAt(index: 1, default: '');
			local String is c2: p:charAt(index: 2, default: '');
			if({ c0 == '/' && self:isAlpha(ch: c1) && c2 == ':' }, {
				return p:substring(start: 1, end: p:length());
			});
		});
		if({ self:authority != '' }, {
			return '//' . self:authority . p;
		});
		return p;
	}

	## Returns an OS-native filesystem path representation (using '\' on Windows).
	Function of String is toNativeFilePath(){
		local String is fp: self:toFilePath();
		if({ Process:osName() == 'windows' }, {
			return fp:replaceAll(search: '/', replacement: '\\');
		});
		return fp;
	}

	## True if this is an absolute URI or path.
	Function of Boolean is isAbsolute(){
		if({ self:scheme != '' }, {
			return true;
		});
		if({ self:path:startsWith(prefix: '/') }, {
			return true;
		});
		return self:hasDrivePrefix(p: self:path);
	}

	## Returns the parent directory path of this URI.
	Function of String is dirPath(){
		local String is p: self:path;
		if({ p == '' || p == '/' }, {
			return p;
		});
		local Int is lastSlash: -1;
		local Int is len: p:length();
		while([Int is i: 0], { i < len }, {
			if({ p:charAt(index: i, default: '') == '/' }, {
				lastSlash: i;
			});
			i++;
		});
		if({ lastSlash < 0 }, {
			return '';
		});
		if({ lastSlash == 0 }, {
			return '/';
		});
		# If at root of drive letter: /C:/foo -> parent is /C:/
		if({ lastSlash == 3 && p:length() >= 3 }, {
			local String is c0: p:charAt(index: 0, default: '');
			local String is c1: p:charAt(index: 1, default: '');
			local String is c2: p:charAt(index: 2, default: '');
			if({ c0 == '/' && self:isAlpha(ch: c1) && c2 == ':' }, {
				return p:substring(start: 0, end: 4);
			});
		});
		return p:substring(start: 0, end: lastSlash);
	}

	## Returns the filename portion of this URI including extension.
	Function of String is baseName(){
		local String is p: self:path;
		if({ p == '' || p == '/' }, {
			return '';
		});
		local Int is lastSlash: -1;
		local Int is len: p:length();
		while([Int is i: 0], { i < len }, {
			if({ p:charAt(index: i, default: '') == '/' }, {
				lastSlash: i;
			});
			i++;
		});
		if({ lastSlash < 0 }, {
			return p;
		});
		return p:substring(start: lastSlash + 1, end: len);
	}

	## Returns the file extension including the leading dot, or '' if none.
	Function of String is extName(){
		local String is bn: self:baseName();
		if({ bn == '' }, {
			return '';
		});
		local Int is lastDot: -1;
		local Int is len: bn:length();
		while([Int is i: 0], { i < len }, {
			if({ bn:charAt(index: i, default: '') == '.' }, {
				lastDot: i;
			});
			i++;
		});
		if({ lastDot <= 0 }, {
			return '';
		});
		return bn:substring(start: lastDot, end: len);
	}

	## Resolves a relative path or URI against this URI.
	Function of Uri is resolve(String is relativePath){
		local Uri is rel: self:fromFilePath(filePath: relativePath);
		if({ rel:isAbsolute() }, {
			return rel;
		});
		local String is baseDir: self:dirPath();
		local String is joined: '';
		if({ baseDir != '' }, {
			if({ baseDir:endsWith(suffix: '/') }, {
				joined: baseDir . rel:path;
			}, {
				joined: baseDir . '/' . rel:path;
			});
		}, {
			joined: rel:path;
		});
		local String is norm: self:cleanPath(rawPath: joined);
		return Uri:init(scheme: self:scheme, authority: self:authority, path: norm);
	}

	## Formats as a URI string.
	replace Function of String is toString(){
		if({ self:scheme == 'file' }, {
			if({ self:authority != '' }, {
				return 'file://' . self:authority . self:path;
			});
			if({ self:path:startsWith(prefix: '/') }, {
				return 'file://' . self:path;
			});
			return 'file:///' . self:path;
		});
		if({ self:scheme != '' }, {
			return self:scheme . '://' . self:authority . self:path;
		});
		return self:path;
	}
}
