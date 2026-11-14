#! Package base:compiler:loader
#! Resolves and loads multi-file package imports across the Spec project
#! and standard library.
##
## Loads the root source file, walks its `using` declarations (array-form
## package paths, wildcard stdlib groups, and plain file paths), and
## produces one unified ProgramNode: source classes plus every loaded
## floor/lib class — the FULL class set the code generator's registries
## require. Group fragments merge into their targets after loading.

Class is Loader{
	namespace: ['base', 'compiler', 'loader'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as File()],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'sys', as Buf()],
		['base', 'sys', as Dir()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'sys', as Loops()]
,
		['base', 'compiler', 'ast', Expression]
,
		['base', 'compiler', 'ast', Parameter]
,
		['base', 'compiler', 'lexer', Token]
,
		['base', 'compiler', 'ast', Type]
,
		['base', 'compiler', Error],
		['base', 'compiler', ErrorText]
	];

	local Map of String to String is loadedFiles: Map:init();
	local String is rootInputPath: '';
	local Array of ClassInfo is loadedClasses: [];
	local Map of String to String is seenClassNames: Map:init();
	local Map of String to String is seenBareNames: Map:init();
	local Array of String is parseErrors: [];
	local ErrorText is errText: ErrorText:init();
	local Array of String is extraSourceDirs: [];



	replace Function is init(){
		self:loadedFiles: Map:init();
		self:loadedClasses: [];
		self:seenClassNames: Map:init();
		self:seenBareNames: Map:init();
		self:parseErrors: [];
		self:extraSourceDirs: [];
	}

	Function of Array of String is getParseErrors(){
		return self:parseErrors;
	}

	## Releases loaded class lists and tracking maps after program assembly.
	Function is cleanup(){
		self:loadedFiles: Map:init();
		self:loadedClasses: [];
		self:seenClassNames: Map:init();
		self:seenBareNames: Map:init();
		self:parseErrors: [];
		self:extraSourceDirs: [];
	}

	## Adds an explicit source directory to scan for packages and modules.
	Function is addSourceDir(String is dir){
		if({ dir != '' }, {
			self:extraSourceDirs:add(item: dir);
		});
	}

	## Sets explicit source directories to scan for packages and modules.
	Function is setSourceDirs(Array of String is dirs){
		self:extraSourceDirs: dirs;
	}

	## Recursively reads, tokenizes, and parses a source file and its transitive dependencies.
	##
	## @param filePath: Path to target `.spec` file.
	Function is loadFile(String is filePath){
		if({ self:loadedFiles:has(key: filePath) }, {
			return;
		});
		self:loadedFiles:set(key: filePath, value: 'true');

		if({ !fileExists(path: filePath) }, {
			self:parseErrors:add(item: self:errText:errModuleFileNotFound(path: filePath));
			return;
		});

		local String is src: fileRead(path: filePath, default: '');
		local Lexer is lexer: Lexer:init(source: src);
		local Parser is parser: Parser:init(tokens: []);
		parser:setLexer(lexer: lexer);
		parser:setSourceFile(file: filePath);
		local ProgramNode is prog: parser:parseProgram();
		if({ lexer:hasErrors() }, {
			local Array of Error is lexErrors: lexer:getErrors();
			lexErrors:each(action: local Function(Error is err){
				self:parseErrors:add(item: '  [LexError] [' . filePath . '] ' . err:toString());
			});
		});
		if({ parser:hasErrors() }, {
			local Array of Error is parseErrs: parser:getErrors();
			parseErrs:each(action: local Function(Error is err){
				self:parseErrors:add(item: err:toString());
			});
		});

		prog:classes:each(action: local Function(ClassInfo is c){
			c:members:each(action: local Function(Member is m){
				m:setSourceFile(file: filePath);
				if({ m:kind == MemberKind:CLASS }, {
					m:nestedClass:setSourceFile(file: filePath);
				});
			});
			# Class identity is namespace-qualified: a base:sys wrapper and
			# its same-name sysinternal floor coexist in one program. A
			# NON-floor class whose bare name is already registered is a
			# legacy/migration duplicate — the scan-root priority already
			# preferred the new tree, so it is skipped.
			local String is qName: c:namespaceJoined() . ':' . c:name;
			local Boolean is isFloor: c:namespaceJoined():endsWith(suffix: ':sysinternal') || c:namespaceJoined() == 'sysinternal';
			local Boolean is dup: self:seenClassNames:has(key: qName);
			if({ !isFloor && !dup && self:seenBareNames:has(key: c:name) }, {
				dup: true;
			});
			if({ !dup }, {
				self:seenClassNames:set(key: qName, value: 'true');
				if({ !isFloor }, {
					self:seenBareNames:set(key: c:name, value: 'true');
				});
				self:loadedClasses:add(item: c);
			});
			self:collectImportsFromClass(c: c);
		});
	}

	## Gathers and loads all `using` imports declared in a class definition.
	##
	## @param c: Target [ClassInfo] definition.
	Function is collectImportsFromClass(ClassInfo is c){
		c:members:each(action: local Function(Member is m){
			if({ m:name == 'using' && m:hasInit }, {
				local Expression is initExpr: m:initExpr;
				if({ initExpr:kind == ExpressionKind:ARRAY }, {
					initExpr:arrayItems:each(action: local Function(Expression is item){
						if({ item:kind == ExpressionKind:ARRAY }, {
							self:loadArrayFormUsing(item: item, c: c);
							return;
						});
						self:parseErrors:add(item: self:errText:errMalformedImport(className: c:name));
					});
				});
			});
		});
	}

	## Resolves one array-form using entry against the scan roots (the spec
	## executable's directory and the input file's directory). String segments
	## name the package; the last element being a bare class identifier loads
	## that one class, a string loads the whole package directory.
	## The scan map: class name -> ';'-joined candidate file paths. Built
	## once from the two scan trees (the input file's tree first, then the
	## executable's tree), so an import is a single map lookup and the
	## namespace check at load time is the acceptance test.
	local Map of String to String is classPaths: Map:init();

	## Package directories seen while scanning: dir path -> ';'-joined
	## .spec names. The wildcard form (a using entry without a trailing
	## class) resolves through this: everything in the PACKAGE — the
	## classes whose declared namespace matches — loads from here.
	local Map of String to String is packageDirs: Map:init();

	## True once [buildScanIndex] has run.
	local Boolean is indexBuilt: false;

	## Builds the scan map. Two trees, per the resolution model:
	##
	## 1. The directory of the .spec file being compiled, recursively.
	## 2. The directory of the spec executable, recursively — plus its
	##    parent when the executable sits in a bin/-style layout (its own
	##    directory holds no .spec content; the sources live at the prefix).
	##
	## Descent prunes locations with no .spec files or directories and
	## skips dot-directories. The namespace declared inside a file — not
	## its path — determines the package it provides; the map only says
	## where to find candidates, and resolution verifies the namespace.
	Function is buildScanIndex(){
		self:classPaths: Map:init();
		self:packageDirs: Map:init();
		# 0. User-configured source directories (highest priority project roots).
		self:extraSourceDirs:each(action: local Function(String is d){
			if({ d != '' }, {
				self:scanTree(dir: d, depth: 0);
			});
		});
		# 1. The input file's tree (project packages override).
		local String is inDir: self:dirOf(path: self:rootInputPath);
		if({ inDir != '' }, {
			self:scanTree(dir: inDir, depth: 0);
		});
		# 2. The executable's tree — walking UP while the location holds no
		# .spec content (a bin/-layout install keeps the sources at the
		# prefix). no hop count — `dirOf` is pure
		# string work, and the walk terminates at the natural boundary:
		# the filesystem root (`/` yields '' and is never scanned — a
		# root-level fruitless climb would otherwise walk the whole
		# machine). Any install depth works.
		local String is exeDir: Dir:exeDir();
		# The walk-up loop keeps climbing while the executable's locations
		# have yielded no .spec content at all.
		local Int is indexed: 0;
		while({ indexed == 0 && exeDir != '' && exeDir != '/' && exeDir != '\\' && !exeDir:endsWith(suffix: ':') }, {
			self:scanTree(dir: exeDir, depth: 0);
			indexed: self:classPaths:keys():length();
			if({ indexed == 0 }, {
				exeDir: self:dirOf(path: exeDir);
			});
		});
		# 3. The working directory: for a compiler invoked from a project
		# whose packages sit at the cwd, or a stage binary run from the
		# repository root during bootstrap.
		self:scanTree(dir: '.', depth: 0);
		self:indexBuilt: true;
	}

	## Recursively collects .spec files under [dir] into the scan map.
	## Descends only into directories that list entries (the floor's
	## dirList returns empty for files, pruning them naturally), skips
	## dot-directories, and stops at [depth] 6.
	##
	## @param dir: Directory to scan.
	## @param depth: Current recursion depth.
	Function is scanTree(String is dir, Int is depth){
		# the depth is the SYMLINK-CYCLE guard — a
		# cycle of directory symlinks yields a fresh path string per
		# visit, so no visited set can catch it (the documented exception
		# to terminate-on-revisit). 32 levels is beyond any legitimate
		# package tree; a hit means a loop in the filesystem, not a
		# language limit.
		if({ depth > 32 }, {
			return;
		});
		local Array of String is entries: Dir:dirList(path: dir);
		entries:each(action: local Function(String is name){
			if({ name:startsWith(prefix: '.') }, {
				return;
			});
			local String is child: Buf:stringCopy(b: dir . '/' . name);
			if({ name:endsWith(suffix: '.spec') }, {
				local String is stem: name:substring(start: 0, end: name:length() - 5);
				if({ self:classPaths:has(key: stem) }, {
					self:classPaths:set(key: stem, value: self:classPaths:getString(key: stem, default: '') . ';' . child);
				}, {
					self:classPaths:set(key: stem, value: child);
				});
				if({ self:packageDirs:has(key: dir) }, {
					self:packageDirs:set(key: dir, value: self:packageDirs:getString(key: dir, default: '') . ';' . name);
				}, {
					self:packageDirs:set(key: dir, value: name);
				});
				return;
			});
			local Array of String is subEntries: Dir:dirList(path: child);
			if({ subEntries:length() > 0 }, {
				self:scanTree(dir: child, depth: depth + 1);
			});
		});
	}

	## The candidate paths recorded for [className], in scan order.
	##
	## @param className: The class whose file is wanted.
	## @return: Candidate paths (first-found wins the try order).
	Function of Array of String is candidatesFor(String is className){
		local String is joined: self:classPaths:getString(key: className, default: '');
		# The scan order is the try order; empty segments (doubled or
		# trailing delimiters) carry no candidate and drop out.
		return joined:split(delimiter: ';'):filter(predicate: local Function of Boolean(String is seg){
			return seg:length() > 0;
		});
	}

	## Number of files loaded so far (package-resolution progress metric).
	##
	## @return: The loaded-file count.
	Function of Int is loadedFileCount(){
		return self:loadedFiles:length();
	}

	## True when the loaded program now provides [className] declaring the
	## namespace [nsJoined] — the namespace IS the package, so this is the
	## resolution's acceptance test.
	##
	## @param nsJoined: The requested namespace, colon-joined.
	## @param className: The requested class name.
	## @return: true when provided.
	Function of Boolean is provides(String is nsJoined, String is className){
		local Boolean is ok: false;
		self:loadedClasses:each(action: local Function(ClassInfo is c){
			if({ !ok }, {
				# A package-form request (no class name) accepts any class
				# declaring the namespace; a class form requires the class.
				if({ className == '' }, {
					if({ c:namespaceJoined() == nsJoined }, {
						ok: true;
					});
				}, {
					if({ c:name == className && c:namespaceJoined() == nsJoined }, {
						ok: true;
					});
				});
			});
		});
		return ok;
	}

	## Resolves one array-form using entry through the scan map: look up
	## the class name, try each candidate file, and accept the first whose
	## load declares the requested class in the requested namespace.
	##
	## @param parts: The package path segments.
	## @param termClass: The trailing class identifier.
	## @param c: The importing class (for diagnostics).
	Function is resolveImport(Array of String is parts, String is termClass, ClassInfo is c){
		if({ !self:indexBuilt }, {
			self:buildScanIndex();
		});
		local String is nsJoined: '';
		parts:each(action: local Function(String is seg){
			if({ nsJoined == '' }, {
				nsJoined: seg;
			}, {
				nsJoined: nsJoined . ':' . seg;
			});
		});
		local String is wanted: nsJoined . ':' . termClass;
		local Array of String is cands: self:candidatesFor(className: termClass);
		# Class form: try each candidate file; accept the first whose load
		# declares the requested class in the requested namespace.
		local Boolean is resolved: false;
		if({ termClass != '' }, {
			cands:each(action: local Function(String is cand){
				if({ !resolved }, {
					self:loadFile(filePath: cand);
					if({ self:provides(nsJoined: nsJoined, className: termClass) }, {
						resolved: true;
					});
				});
			});
		});
		# Wildcard form (no trailing class): everything in the PACKAGE.
		# The package's directory locates the candidates; the namespace is
		# the authority. Class form never reaches here — the map is the
		# whole mechanism, and the convention is one class per named file.
		if({ !resolved && termClass == '' }, {
			local String is dirSuffix: '/' . nsJoined:replaceAll(search: ':', replacement: '/');
			# The keys array is owned (a var-decl init is a consumption
			# position): nested loadFile calls claim hundreds of pool slots
			# and would evict a pool-held keys array mid-iteration.
			local Array of String is allDirs: self:packageDirs:keys();
			allDirs:each(action: local Function(String is dirPath){
				if({ dirPath:endsWith(suffix: dirSuffix) }, {
					local String is namesJoined: self:packageDirs:getString(key: dirPath, default: '');
					local Array of String is names: namesJoined:split(delimiter: ';');
					names:each(action: local Function(String is name){
						self:loadFile(filePath: Buf:stringCopy(b: dirPath . '/' . name));
					});
				});
			});
			if({ self:provides(nsJoined: nsJoined, className: '') }, {
				resolved: true;
			});
		});
		if({ !resolved }, {
			self:parseErrors:add(item: self:errText:errCannotResolveImport(wanted: wanted, className: c:name));
		});
	}

	## Parses one array-form using entry and resolves it.
	##
	## @param item: The ARRAY expression naming the package segments.
	## @param c: The importing class.
	Function is loadArrayFormUsing(Expression is item, ClassInfo is c){
		local Array of Expression is segs: item:arrayItems;
		if({ segs:length() == 0 }, {
			return;
		});
		local Array of String is parts: [];
		local String is termClass: '';
		segs:each(action: local Function(Expression is seg){
			if({ seg:kind == ExpressionKind:IDENT }, {
				termClass: seg:str;
			}, {
				if({ seg:kind == ExpressionKind:USING_AS }, {
					# Instance-import form (§2.1): resolves exactly
					# like the class form; the as-ness stays on the using member
					# for the checker, generator, and audit.
					termClass: seg:str;
				}, {
					parts:add(item: seg:str);
				});
			});
		});
		self:resolveImport(parts: parts, termClass: termClass, c: c);
	}

	## Directory portion of a file path ('' when the path has no slash).
	Function of String is dirOf(String is path){
		local Int is lastIdx: -1;
		local Int is len: path:length();
		while(
			[Int is pos: 0],
			{ pos < len },
			{
				local String is ch: path:charAt(index: pos, default: '');
				if({ ch == '/' || ch == '\\' }, {
					lastIdx: pos;
				});
				pos++;
			}
		);
		if({ lastIdx < 0 }, {
			return '';
		});
		return path:substring(start: 0, end: lastIdx);
	}

	## True when two members declare the same signature — for methods:
	## parameter count, names, and types all equal; for fields: the declared
	## type (§I.1).
	##
	## @param a: First member.
	## @param b: Second member.
	## @return: true when signatures are identical.
	Function of Boolean is sameSignature(Member is a, Member is b){
		if({ a:kind != b:kind }, {
			return false;
		});
		if({ a:kind == MemberKind:FIELD }, {
			return a:memberType:name == b:memberType:name;
		});
		if({ a:params:length() != b:params:length() }, {
			return false;
		});
		local Boolean is same: true;
		while([Int is idx: 0], { same && idx < a:params:length() }, {
			local Parameter is pa: a:params:get(index: idx);
			local Parameter is pb: b:params:get(index: idx);
			if({ pa:name != pb:name || pa:paramType:name != pb:paramType:name }, {
				same: false;
			});
			idx++;
		});
		return same;
	}

	## Removes a class from the loaded registry (used to dissolve fragments).
	##
	## @param c: [ClassInfo] to remove.
	Function is removeClassFromLoaded(ClassInfo is c){
		local Boolean is found: false;
		while([Int is idx: 0], { !found && idx < self:loadedClasses:length() }, {
			local ClassInfo is cur: self:loadedClasses:get(index: idx);
			if({ cur == c }, {
				self:loadedClasses:removeAt(index: idx, default: c);
				found: true;
			}, {
				idx++;
			});
		});
	}

	Function of ProgramNode is loadProgram(String is rootPath){
		self:loadedFiles: Map:init();
		self:loadedClasses: [];
		self:seenClassNames: Map:init();
		self:seenBareNames: Map:init();
		self:parseErrors: [];

		# The input path anchors the scan roots before any resolution.
		self:rootInputPath: rootPath;

		# Root class lattice preloads, before any user code. Resolution
		# prefers the migration stdlib (spec/lib) over the legacy lib.
		# Root lattice preloads load the base:sys WRAPPERS; the wrappers'
		# using-imports pull the sysinternal floor in transitively, so the
		# floor is never loaded except behind its wrapper.
		local Array of String is preloads: [
			'Any',
			'Loadable',
			'Stringable',
			'Class',
			'Enum',
			'String',
			'Array',
			'Map',
			'Buf',
			'Dir'
		];
		preloads:each(action: local Function(String is cls){
			if({ !self:indexBuilt }, {
				self:buildScanIndex();
			});
			local Array of String is cands: self:candidatesFor(className: cls);
			cands:each(action: local Function(String is cand){
				if({ !self:loadedFiles:has(key: cand) }, {
					self:loadFile(filePath: cand);
				});
			});
		});

		self:loadFile(filePath: rootPath);
		self:appendImplicitClass();
		self:synthesizeInstanceImports();

		return ProgramNode:init(classes: self:loadedClasses);
	}

	## E1/E2 full form: a field-ful class instance-imported
	## via `as X(args)` materializes a real hidden field on the importing
	## class — typed X, initialized `X:init(args)` — so struct layout,
	## per-instance construction, ARC destroy, and constructor-argument
	## checking all run through the ordinary field machinery. Field-less
	## imports synthesize nothing: their methods are self-free and
	## dispatch stays elided (§2.4). Nested classes are included.
	Function is synthesizeInstanceImports(){
		self:synthesizeInto(classes: self:loadedClasses);
	}

	## Recursive synthesis walk over a class list (nested classes included).
	##
	## @param classes: Candidate [ClassInfo] definitions.
	Function is synthesizeInto(Array of ClassInfo is classes){
		classes:each(action: local Function(ClassInfo is c){
			c:members:each(action: local Function(Member is m){
				if({ m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, {
					m:initExpr:arrayItems:each(action: local Function(Expression is item){
						if({ item:kind == ExpressionKind:ARRAY }, {
							item:arrayItems:each(action: local Function(Expression is seg){
								if({ seg:kind == ExpressionKind:USING_AS }, {
									self:synthesizeFor(c: c, asExpr: seg);
								});
							});
						});
					});
				});
			});
			c:members:each(action: local Function(Member is m){
				if({ m:kind == MemberKind:CLASS }, {
					local Array of ClassInfo is one: [m:nestedClass];
					self:synthesizeInto(classes: one);
				});
			});
			# an inner class inherits the enclosing
			# chain's as-imports — its instances carry their own synthesized
			# fields, so the inherited functions dispatch on the inner.
			self:synthesizeInheritedImports(cls: c);
		});
	}

	## Walks [cls]'s base lattice and synthesizes each ancestor's as-entries
	## onto [cls] itself (deduplicated per target by the field-presence
	## check in synthesizeFor).
	##
	## @param cls: The class receiving the inherited imports.
	## @param visited: The visited-class set — the walk marks on entry and
	## terminates on revisit (any depth, cycles included).
	Function is synthesizeInheritedImports(ClassInfo is cls, Map of String to String is visited: Map:init()){
		if({ visited:has(key: cls:name) }, {
			return;
		});
		visited:set(key: cls:name, value: 'true');
		cls:baseClasses:each(action: local Function(String is baseName){
			local ClassInfo is base: self:findLoadedClass(name: baseName);
			if({ base:name != '' }, {
				base:members:each(action: local Function(Member is m){
					if({ m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, {
						m:initExpr:arrayItems:each(action: local Function(Expression is item){
							if({ item:kind == ExpressionKind:ARRAY }, {
								item:arrayItems:each(action: local Function(Expression is seg){
									if({ seg:kind == ExpressionKind:USING_AS }, {
										self:synthesizeFor(c: cls, asExpr: seg);
									});
								});
							});
						});
					});
				});
				self:synthesizeInheritedImports(cls: base, visited: visited);
			});
		});
	}

	## Synthesizes the hidden field for one as-entry when its target is
	## field-ful. The synthesized initializer is the constructor call with
	## the as-form's literal arguments, so argument checking happens
	## through the ordinary field-init path.
	##
	## @param c: The importing class.
	## @param asExpr: The USING_AS expression node.
	Function is synthesizeFor(ClassInfo is c, Expression is asExpr){
		local String is targetName: asExpr:str;
		local ClassInfo is target: self:findLoadedClass(name: targetName);
		if({ target:name == '' }, {
			return;
		});
		if({ !self:isFieldFul(c: target) }, {
			return;
		});
		local String is fieldName: '_import_' . targetName;
		local Boolean is already: false;
		local Array of Member is members: c:members;
		members:each(action: local Function(Member is m){
			if({ !already && m:name == fieldName }, {
				# an inherited-import synthesis
				# finds the field already synthesized from the class's own
				# using (or a prior ancestor hop) — deduplicate silently. A
				# DECLARED member with that name is still a collision.
				if({ m:kind == MemberKind:FIELD && m:hasInit && m:initExpr:kind == ExpressionKind:CALL }, {
					already: true;
				}, {
					self:parseErrors:add(item: self:errText:errSyntheticImportCollision(fieldName: fieldName, className: c:name));
				});
			});
		});
		if({ already }, {
			return;
		});
		local Member is field: Member:init(kind: MemberKind:FIELD);
		field:name: fieldName;
		field:memberType: Type:init(name: targetName);
		local Expression is ctor: Expression:init(kind: ExpressionKind:CALL);
		local Expression is recv: Expression:init(kind: ExpressionKind:IDENT);
		recv:str: targetName;
		ctor:methodTarget: recv;
		ctor:methodName: 'init';
		ctor:methodArgs: asExpr:methodArgs;
		field:hasInit: true;
		field:initExpr: ctor;
		field:setSourceFile(file: c:sourceFile);
		field:setLine(line: asExpr:line);
		members:add(item: field);
	}

	## True when [c] declares real fields (metadata pseudo-members excluded).
	##
	## @param c: Candidate [ClassInfo] definition.
	## @return: true when field-ful.
	Function of Boolean is isFieldFul(ClassInfo is c){
		local Boolean is found: false;
		c:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:FIELD && m:name != 'using' && m:name != 'namespace' && m:name != 'castable' }, {
				found: true;
			});
		});
		return found;
	}

	## Finds an already-loaded class by name (top level only; nested
	## classes are not importable — one class per named file).
	##
	## @param name: Class name.
	## @return: The [ClassInfo], or an empty-named node when absent.
	Function of ClassInfo is findLoadedClass(String is name){
		local ClassInfo is res: ClassInfo:init(name: '', baseClass: '', members: []);
		local Boolean is found: false;
		local Int is count: self:loadedClasses:length();
		while(
			[Int is idx: 0],
			{ !found && idx < count },
			{
				local ClassInfo is cand: self:loadedClasses:get(index: idx);
				idx++;
				if({ cand:name == name }, {
					res: cand;
					found: true;
				});
			}
		);
		return res;
	}

	## Appends `Class` as the parent of every class without explicit parents
	## (enums excluded). The implicit parent is
	## `Class` (the declaration root) so the machinery and the default
	## rendering reach every class; "at the lowest level, anything is
	## Any" holds transitively (Class -> Stringable -> Loadable -> Any).
	## `Any` is the one root and is skipped (a rootless Any plus the
	## implicit Class would cycle). Enum keeps its own root per the
	## enumHeader contract.
	Function is appendImplicitClass(){
		self:loadedClasses:each(action: local Function(ClassInfo is c){
			if({ c:baseClass != 'Enum' && c:baseClasses:length() == 0 && c:name != 'Any' }, {
				c:withBaseClasses(name: c:name, baseClasses: ['Class'], members: c:members);
			});
		});
	}

}
