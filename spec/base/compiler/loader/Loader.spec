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
		['base', 'io', File],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'sys', Buf],
		['base', 'sys', Dir],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator']
	];

	local Map of String to String is loadedFiles: Map:init();
	local String is rootInputPath: '';
	local Array of ClassInfo is loadedClasses: [];
	local Map of String to String is seenClassNames: Map:init();
	local Map of String to String is seenBareNames: Map:init();
	local Array of String is parseErrors: [];

	## Group targets declared by fragments via the `group` pseudo-field (load order).
	local Array of String is groupTargets: [];

	## Group fragments corresponding to [groupTargets] (load order).
	local Array of ClassInfo is groupFragments: [];

	replace Function is init(){
		self:loadedFiles: Map:init();
		self:loadedClasses: [];
		self:seenClassNames: Map:init();
		self:seenBareNames: Map:init();
		self:parseErrors: [];
		self:groupTargets: [];
		self:groupFragments: [];
	}

	Function of Array of String is getParseErrors(){
		return self:parseErrors;
	}

	## Recursively reads, tokenizes, and parses a source file and its transitive dependencies.
	##
	## @param filePath: Path to target `.spec` file.
	Function is loadFile(String is filePath){
		if (self:loadedFiles:has(key: filePath)) {
			return;
		}
		self:loadedFiles:set(key: filePath, value: 'true');

		if (!File:exists(path: filePath)) {
			self:parseErrors:add(item: '  [LoadError] Module file not found: ' . filePath);
			return;
		}

		local String is src: File:read(path: filePath, default: '');
		local Lexer is lexer: Lexer:init(source: src);
		local Array of Token is tokens: lexer:tokenize();
		if (lexer:hasErrors()) {
			local Array of Error is lexErrors: lexer:getErrors();
			lexErrors:each(action: local Function(Error is err){
				self:parseErrors:add(item: '  [LexError] [' . filePath . '] ' . err:toString());
			});
		}
		local Parser is parser: Parser:init(tokens: tokens);
		parser:setSourceFile(file: filePath);
		local ProgramNode is prog: parser:parseProgram();
		if (parser:hasErrors()) {
			local Array of Error is parseErrs: parser:getErrors();
			parseErrs:each(action: local Function(Error is err){
				self:parseErrors:add(item: err:toString());
			});
		}

		prog:classes:each(action: local Function(ClassInfo is c){
			c:members:each(action: local Function(Member is m){
				m:setSourceFile(file: filePath);
			});
			local String is gName: self:groupTargetOf(c: c);
			# Class identity is namespace-qualified: a base:sys wrapper and
			# its same-name sysinternal floor coexist in one program. A
			# NON-floor class whose bare name is already registered is a
			# legacy/migration duplicate — the scan-root priority already
			# preferred the new tree, so it is skipped.
			local String is qName: c:namespaceJoined() . ':' . c:name;
			local Boolean is isFloor: c:namespaceJoined():endsWith(suffix: ':sysinternal') || c:namespaceJoined() == 'sysinternal';
			local Boolean is dup: self:seenClassNames:has(key: qName);
			if (!isFloor && !dup && self:seenBareNames:has(key: c:name)) {
				dup: true;
			}
			if (!dup) {
				self:seenClassNames:set(key: qName, value: 'true');
				self:seenBareNames:set(key: c:name, value: 'true');
				self:loadedClasses:add(item: c);
				if (gName != '' && gName != c:name) {
					self:groupTargets:add(item: gName);
					self:groupFragments:add(item: c);
				}
			} else {
				if (gName == c:name) {
					local LoadedClassSearchLoop is find: LoadedClassSearchLoop:init(list: self:loadedClasses, target: c:name);
					While:run(loop: find);
					if (find:found) {
						self:mergeFragmentInto(target: find:res, frag: c);
					}
				}
			}
			self:collectImportsFromClass(c: c);
		});
	}

	## Gathers and loads all `using` imports declared in a class definition.
	##
	## @param c: Target [ClassInfo] definition.
	Function is collectImportsFromClass(ClassInfo is c){
		c:members:each(action: local Function(Member is m){
			if (m:name == 'using' && m:hasInit) {
				local Expression is initExpr: m:initExpr;
				if (initExpr:kind == ExpressionKind:ARRAY) {
					initExpr:arrayItems:each(action: local Function(Expression is item){
						if (item:kind == ExpressionKind:ARRAY) {
							self:loadArrayFormUsing(item: item, c: c);
							return;
						}
						self:parseErrors:add(item: '  [LoadError] Malformed import in class \'' . c:name . '\': using entries are package-segment arrays.');
					});
				}
			}
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
		# 1. The input file's tree (project packages override).
		local String is inDir: self:dirOf(path: self:rootInputPath);
		if (inDir != '') {
			self:scanTree(dir: inDir, depth: 0);
		}
		# 2. The executable's tree — walking UP while the location holds no
		# .spec content (a bin/-layout install keeps the sources at the
		# prefix), bounded at three hops and never reaching a filesystem
		# root's vast subtrees.
		local String is exeDir: Dir:exeDir();
		local Int is ups: 0;
		# The walk-up loop tracks how many files the scan has indexed: it
		# keeps climbing while the executable's locations have yielded no
		# .spec content at all.
		local Int is indexed: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return ups < 3 && indexed == 0;
			},
			iteration: local Function of Boolean(){
				self:scanTree(dir: exeDir, depth: 0);
				indexed: self:classPaths:keys():length();
				if (indexed == 0) {
					exeDir: self:dirOf(path: exeDir);
				}
				ups: ups + 1;
				return true;
			}
		);
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
		if (depth > 8) {
			return;
		}
		local Array of String is entries: Dir:dirList(path: dir);
		entries:each(action: local Function(String is name){
			if (name:startsWith(prefix: '.')) {
				return;
			}
			local String is child: Buf:stringCopy(b: dir . '/' . name);
			if (name:endsWith(suffix: '.spec')) {
				local String is stem: name:substring(start: 0, end: name:length() - 5);
				if (self:classPaths:has(key: stem)) {
					self:classPaths:set(key: stem, value: self:classPaths:getString(key: stem, default: '') . ';' . child);
				} else {
					self:classPaths:set(key: stem, value: child);
				}
				if (self:packageDirs:has(key: dir)) {
					self:packageDirs:set(key: dir, value: self:packageDirs:getString(key: dir, default: '') . ';' . name);
				} else {
					self:packageDirs:set(key: dir, value: name);
				}
				return;
			}
			local Array of String is subEntries: Dir:dirList(path: child);
			if (subEntries:length() > 0) {
				self:scanTree(dir: child, depth: depth + 1);
			}
		});
	}

	## The candidate paths recorded for [className], in scan order.
	##
	## @param className: The class whose file is wanted.
	## @return: Candidate paths (first-found wins the try order).
	Function of Array of String is candidatesFor(String is className){
		local Array of String is out: [];
		local String is joined: self:classPaths:getString(key: className, default: '');
		local Int is start: 0;
		local Int is i: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return i <= joined:length();
			},
			iteration: local Function of Boolean(){
				if (i == joined:length() || joined:charAt(index: i, default: '') == ';') {
					if (i > start) {
						out:add(item: joined:substring(start: start, end: i));
					}
					start: i + 1;
				}
				i: i + 1;
				return true;
			}
		);
		return out;
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
			if (!ok) {
				# A package-form request (no class name) accepts any class
				# declaring the namespace; a class form requires the class.
				if (className == '') {
					if (c:namespaceJoined() == nsJoined) {
						ok: true;
					}
				} else {
					if (c:name == className && c:namespaceJoined() == nsJoined) {
						ok: true;
					}
				}
			}
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
		if (!self:indexBuilt) {
			self:buildScanIndex();
		}
		local String is nsJoined: '';
		parts:each(action: local Function(String is seg){
			if (nsJoined == '') {
				nsJoined: seg;
			} else {
				nsJoined: nsJoined . ':' . seg;
			}
		});
		local String is wanted: nsJoined . ':' . termClass;
		local Array of String is cands: self:candidatesFor(className: termClass);
		# Class form: try each candidate file; accept the first whose load
		# declares the requested class in the requested namespace.
		local Boolean is resolved: false;
		if (termClass != '') {
			cands:each(action: local Function(String is cand){
				if (!resolved) {
					self:loadFile(filePath: cand);
					if (self:provides(nsJoined: nsJoined, className: termClass)) {
						resolved: true;
					}
				}
			});
		}
		# Wildcard form (no trailing class): everything in the PACKAGE.
		# The package's directory locates the candidates; the namespace is
		# the authority. Class form never reaches here — the map is the
		# whole mechanism, and the convention is one class per named file.
		if (!resolved && termClass == '') {
			local String is dirSuffix: '/' . nsJoined:replaceAll(search: ':', replacement: '/');
			# The keys array is owned (a var-decl init is a consumption
			# position): nested loadFile calls claim hundreds of pool slots
			# and would evict a pool-held keys array mid-iteration.
			local Array of String is allDirs: self:packageDirs:keys();
			allDirs:each(action: local Function(String is dirPath){
				if (dirPath:endsWith(suffix: dirSuffix)) {
					local String is namesJoined: self:packageDirs:getString(key: dirPath, default: '');
					local Array of String is names: namesJoined:split(delimiter: ';');
					names:each(action: local Function(String is name){
						self:loadFile(filePath: Buf:stringCopy(b: dirPath . '/' . name));
					});
				}
			});
			if (self:provides(nsJoined: nsJoined, className: '')) {
				resolved: true;
			}
		}
		if (!resolved) {
			self:parseErrors:add(item: '  [LoadError] Cannot resolve import \'[' . wanted . ']' . '\' declared in class \'' . c:name . '\'.');
		}
	}

	## Parses one array-form using entry and resolves it.
	##
	## @param item: The ARRAY expression naming the package segments.
	## @param c: The importing class.
	Function is loadArrayFormUsing(Expression is item, ClassInfo is c){
		local Array of Expression is segs: item:arrayItems;
		if (segs:length() == 0) {
			return;
		}
		local Array of String is parts: [];
		local String is termClass: '';
		segs:each(action: local Function(Expression is seg){
			if (seg:kind == ExpressionKind:IDENT) {
				termClass: seg:stringValue;
			} else if (seg:kind == ExpressionKind:USING_AS) {
				# Instance-import form (INSTANCE.md §2.1): resolves exactly
				# like the class form; the as-ness stays on the using member
				# for the checker, generator, and audit.
				termClass: seg:stringValue;
			} else {
				parts:add(item: seg:stringValue);
			}
		});
		self:resolveImport(parts: parts, termClass: termClass, c: c);
	}

	## Directory portion of a file path ('' when the path has no slash).
	Function of String is dirOf(String is path){
		local LastSlashLoop is loop: LastSlashLoop:init(src: path);
		While:run(loop: loop);
		if (loop:lastIdx < 0) {
			return '';
		}
		return path:substring(start: 0, end: loop:lastIdx);
	}

	## Walks a path tracking the final slash index.
	Class of Loop is LastSlashLoop{
		local String is src;
		local Int is pos: 0;
		local Int is lastIdx: -1;

		replace Function is init(String is src){
			self:src: src;
			self:pos: 0;
			self:lastIdx: -1;
		}

		replace Function of Boolean is evaluate(){
			return self:pos < self:src:length();
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:src:charAt(index: self:pos, default: '');
			if (ch == '/') {
				self:lastIdx: self:pos;
			}
			self:pos: self:pos + 1;
			return true;
		}
	}

	## Extracts the load-time group target declared via the `group` pseudo-field.
	##
	## The field is optional; when present it must be a single-entry string array
	## naming the class this fragment merges into. Fragments must not declare
	## `extends` (enums included). An empty string means "not a fragment".
	##
	## @param c: Candidate [ClassInfo] definition.
	## @return: Group target class name, or empty string when not a fragment.
	Function of String is groupTargetOf(ClassInfo is c){
		local Array of Member is members: c:members;
		local Int is idx: 0;
		local String is target: '';
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < members:length();
			},
			iteration: local Function of Boolean(){
				local Member is m: members:get(index: idx);
				if (m:name == 'group' && m:hasInit) {
					local Expression is initExpr: m:initExpr;
					if (initExpr:kind == ExpressionKind:ARRAY) {
						if (initExpr:arrayItems:length() != 1) {
							self:parseErrors:add(item: '  [LoadError] ClassInfo \'' . c:name . '\' declares a group with ' . (initExpr:arrayItems:length() as String) . ' entries; exactly one target is required.');
						} else {
							local Expression is firstItem: initExpr:arrayItems:get(index: 0);
							target: firstItem:stringValue;
						}
					}
				}
				idx: idx + 1;
				return true;
			}
		);
		if (target != '' && c:baseClass != '') {
			self:parseErrors:add(item: '  [LoadError] Group fragment \'' . c:name . '\' must not declare parent classes.');
			target: '';
		}
		return target;
	}

	## Finds an already-loaded class by name.
	Class of Loop is LoadedClassSearchLoop{
		local Array of ClassInfo is list;
		local String is target;
		local Int is idx: 0;
		local ClassInfo is res;
		local Boolean is found: false;

		replace Function is init(Array of ClassInfo is list, String is target){
			self:list: list;
			self:target: target;
			self:idx: 0;
			self:found: false;
		}

		replace Function of Boolean is evaluate(){
			return !self:found && self:idx < self:list:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			local ClassInfo is cand: self:list:get(index: self:idx);
			self:idx: self:idx + 1;
			if (cand:name == self:target) {
				self:res: cand;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	## Finds a named member on a class (nested-class members have no name
	## and never match).
	Class of Loop is NamedMemberLoop{
		local Array of Member is members;
		local String is target;
		local Int is idx: 0;
		local Member is res;
		local Boolean is found: false;

		replace Function is init(Array of Member is members, String is target){
			self:members: members;
			self:target: target;
			self:idx: 0;
			self:found: false;
		}

		replace Function of Boolean is evaluate(){
			return !self:found && self:idx < self:members:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (self:target != '' && m:name == self:target) {
				self:res: m;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	## Merges a group fragment's members into its target class.
	##
	## Appends members in fragment order, rejecting duplicate member names with
	## both source files named. Unions the fragment's `using` entries into the
	## target's `using` array (or transplants the member when the target has
	## none), strips `group` declarations, and enforces the single-`init` rule.
	##
	## @param target: Merge destination [ClassInfo].
	## @param frag: Group fragment [ClassInfo] to merge in.
	Function is mergeFragmentInto(ClassInfo is target, ClassInfo is frag){
		if (target:baseClass == 'Enum') {
			self:parseErrors:add(item: '  [LoadError] Group target \'' . target:name . '\' is an Enum; grouping is only supported for classes.');
			return;
		}
		local Array of Member is fragMembers: frag:members;
		local Int is idx: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < fragMembers:length();
			},
			iteration: local Function of Boolean(){
				local Member is m: fragMembers:get(index: idx);
				local String is mName: m:name;
				if (mName != 'using' && mName != 'group') {
					local NamedMemberLoop is dup: NamedMemberLoop:init(members: target:members, target: mName);
					While:run(loop: dup);
					if (dup:found) {
						self:parseErrors:add(item: '  [LoadError] Duplicate member \'' . mName . '\' in class \'' . target:name . '\' (' . m:sourceFile . ' conflicts with declaration in ' . dup:res:sourceFile . ').');
					} else {
						target:members:add(item: m);
					}
				}
				idx: idx + 1;
				return true;
			}
		);

		# Union the fragment's `using` entries into the target's `using` array.
		local NamedMemberLoop is fragUsing: NamedMemberLoop:init(members: frag:members, target: 'using');
		While:run(loop: fragUsing);
		if (fragUsing:found) {
			local NamedMemberLoop is targetUsing: NamedMemberLoop:init(members: target:members, target: 'using');
			While:run(loop: targetUsing);
			if (targetUsing:found) {
				local Expression is fragItems: fragUsing:res:initExpr;
				local Expression is targetItems: targetUsing:res:initExpr;
				if (fragItems:kind == ExpressionKind:ARRAY && targetItems:kind == ExpressionKind:ARRAY) {
					fragItems:arrayItems:each(action: local Function(Expression is item){
						local Boolean is present: false;
						targetItems:arrayItems:each(action: local Function(Expression is existing){
							if (!present && existing:stringValue == item:stringValue) {
								present: true;
							}
						});
						if (!present) {
							targetItems:arrayItems:add(item: item);
						}
					});
				}
			} else {
				target:members:add(item: fragUsing:res);
			}
		}

		# Strip the `group` declaration from the merged class.
		self:stripMemberNamed(target: target, name: 'group');

		# Enforce the single-init rule across the merged class.
		local Int is initCount: 0;
		local String is initFile: '';
		local Array of Member is mergedMembers: target:members;
		local Int is scan: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return scan < mergedMembers:length();
			},
			iteration: local Function of Boolean(){
				local Member is m: mergedMembers:get(index: scan);
				if (m:name == 'init') {
					initCount: initCount + 1;
					initFile: m:sourceFile;
				}
				scan: scan + 1;
				return true;
			}
		);
		if (initCount > 1) {
			self:parseErrors:add(item: '  [LoadError] Multiple init methods in class \'' . target:name . '\' (last declared in ' . initFile . '); a grouped class may declare at most one.');
		}
	}

	## Removes members with the given name from a class.
	##
	## @param target: [ClassInfo] to modify.
	## @param name: Member name to strip.
	Function is stripMemberNamed(ClassInfo is target, String is name){
		local Array of Member is members: target:members;
		local Int is idx: members:length() - 1;
		While:condition(
			evaluate: local Function of Boolean(){
				return idx >= 0;
			},
			iteration: local Function of Boolean(){
				local Member is m: members:get(index: idx);
				if (m:name == name) {
					members:removeAt(index: idx, default: m);
				}
				idx: idx - 1;
				return true;
			}
		);
	}

	## Removes a class from the loaded registry (used to dissolve fragments).
	##
	## @param c: [ClassInfo] to remove.
	Function is removeClassFromLoaded(ClassInfo is c){
		local Int is idx: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < self:loadedClasses:length();
			},
			iteration: local Function of Boolean(){
				local ClassInfo is cur: self:loadedClasses:get(index: idx);
				if (cur == c) {
					self:loadedClasses:removeAt(index: idx, default: c);
					return false;
				}
				idx: idx + 1;
				return true;
			}
		);
	}

	## Merges every declared group fragment into its target class.
	##
	## Runs once after all files are loaded. Fragments whose target class does
	## not exist yet contribute to a freshly created class named after the
	## group (a class may live entirely across fragments). Fragments are then
	## dissolved from the loaded registry.
	Function is mergeGroups(){
		local Int is idx: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < self:groupTargets:length();
			},
			iteration: local Function of Boolean(){
				local String is gName: self:groupTargets:get(index: idx);
				local ClassInfo is frag: self:groupFragments:get(index: idx);
				local LoadedClassSearchLoop is find: LoadedClassSearchLoop:init(list: self:loadedClasses, target: gName);
				While:run(loop: find);
				local ClassInfo is target: find:res;
				if (!find:found) {
					target: ClassInfo:init(name: gName, baseClass: '', members: []);
					self:loadedClasses:add(item: target);
				}
				if (target != frag) {
					self:mergeFragmentInto(target: target, frag: frag);
					self:removeClassFromLoaded(c: frag);
				}
				idx: idx + 1;
				return true;
			}
		);
	}

	## Coordinates root file loading and dependency traversal to produce a unified [ProgramNode].
	##
	## @param rootPath: Filesystem path to the application entry file.
	## @return: Merged [ProgramNode] AST containing root and imported classes.
	Function of ProgramNode is loadProgram(String is rootPath){
		self:loadedFiles: Map:init();
		self:loadedClasses: [];
		self:seenClassNames: Map:init();
		self:seenBareNames: Map:init();
		self:parseErrors: [];
		self:groupTargets: [];
		self:groupFragments: [];

		# The input path anchors the scan roots before any resolution.
		self:rootInputPath: rootPath;

		# Root class lattice preloads, before any user code. Resolution
		# prefers the migration stdlib (spec/lib) over the legacy lib.
		# Root lattice preloads load the base:sys WRAPPERS; the wrappers'
		# using-imports pull the sysinternal floor in transitively, so the
		# floor is never loaded except behind its wrapper.
		local Array of String is preloads: [
			'String',
			'Array',
			'Map',
			'Buf',
			'Dir',
			'Stringable',
			'Any'
		];
		preloads:each(action: local Function(String is cls){
			if (!self:indexBuilt) {
				self:buildScanIndex();
			}
			local Array of String is cands: self:candidatesFor(className: cls);
			cands:each(action: local Function(String is cand){
				if (!self:loadedFiles:has(key: cand)) {
					self:loadFile(filePath: cand);
				}
			});
		});

		self:loadFile(filePath: rootPath);
		self:appendImplicitAny();
		self:mergeGroups();

		return ProgramNode:init(classes: self:loadedClasses);
	}

	## Appends `Any` as the parent of every class without explicit parents
	## (enums excluded).
	Function is appendImplicitAny(){
		self:loadedClasses:each(action: local Function(ClassInfo is c){
			if (c:baseClass != 'Enum' && c:baseClasses:length() == 0 && c:name != 'Any' && c:name != 'Stringable') {
				c:withBaseClasses(name: c:name, baseClasses: ['Any'], members: c:members);
			}
		});
	}

}
