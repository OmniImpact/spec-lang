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
		['lib', 'base', 'io', File],
		['spec', 'base', 'compiler', 'ast', ProgramNode],
		['spec', 'base', 'compiler', 'ast', ClassInfo],
		['spec', 'base', 'compiler', 'ast', Member],
		['spec', 'base', 'compiler', 'ast', ExpressionKind],
		['spec', 'base', 'compiler', 'lexer', Lexer],
		['spec', 'base', 'compiler', 'parser', Parser],
		['spec', 'lib', 'base', 'sys', Buf],
		['spec', 'lib', 'base', 'sys', Dir],
		['lib', 'base', 'struct', Array],
		['lib', 'base', 'struct', Map],
		['lib', 'base', 'iterator']
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

	## Converts a colon-package path to a slash directory path.
	Class of Loop is PathConvLoop{
		local String is src;
		local Int is pos: 0;
		local String is res: '';

		replace Function is init(String is src){
			self:src: src;
			self:pos: 0;
			self:res: '';
		}

		replace Function of Boolean is evaluate(){
			return self:pos < self:src:length();
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:src:charAt(index: self:pos, default: '');
			if (ch == ':') {
				self:res: self:res . '/';
			} else {
				self:res: self:res . ch;
			}
			self:pos: self:pos + 1;
			return true;
		}
	}

	## Resolves an import path to an existing .spec file: as given, then
	## under lib/. Returns '' when unresolvable.
	##
	## @param rawPath: Package identifier or relative path.
	## @return: The resolved file path, or ''.
	Function of String is resolvePath(String is rawPath){
		local PathConvLoop is loop: PathConvLoop:init(src: rawPath);
		While:run(loop: loop);
		local String is converted: loop:res;

		# Stdlib resolution first (spec/lib preferred over legacy lib).
		local String is std: self:resolveLibFile(relUnderLib: converted . '.spec');
		if (std != '') {
			return std;
		}

		local String is cand1: converted . '.spec';
		if (File:exists(path: cand1)) {
			return cand1;
		}

		local String is cand2: 'lib/' . converted . '.spec';
		if (File:exists(path: cand2)) {
			return cand2;
		}

		return '';
	}

	## Expands wildcard package import paths into standard library file
	## lists. Entries are lib-root-relative ('base/io/File.spec') so the
	## caller resolves them through [resolveLibFile] — the migration stdlib
	## (spec/lib) shadows the legacy lib per file. The compiler:* group
	## names the fossil compiler's own sources and dies with it.
	##
	## @param rawPath: Wildcard package identifier (e.g. "base:io:*").
	## @return: Array of lib-root-relative file paths.
	Function of Array of String is expandWildcard(String is rawPath){
		return when (rawPath) {
			is 'base:io:*': [
				'base/io/File.spec',
				'base/io/Input.spec',
				'base/io/InputHandler.spec',
				'base/io/Output.spec',
				'base/io/Ansi.spec'
			];
			is 'base:iterator:*': [
				'base/iterator/Loop.spec',
				'base/iterator/LoopControl.spec',
				'base/iterator/LoopCallback.spec',
				'base/iterator/While.spec'
			];
			is 'base:meta:*': [
				'base/meta/AST.spec'
			];
			is 'base:reflect:*': [
				'base/reflect/Type.spec',
				'base/reflect/Parameter.spec',
				'base/reflect/Member.spec',
				'base/reflect/ClassInfo.spec'
			];
			is 'base:struct:*': [
				'base/struct/Array.spec',
				'base/struct/Map.spec'
			];
			is 'base:core:*': [
				'base/core/String.spec',
				'base/core/Stringable.spec',
				'base/core/Any.spec'
			];
			is 'base:sysinternal:*': [
				'base/sys/Buf.spec',
				'base/sysinternal/Dir.spec'
			];
			is 'base:sys:*': [
				'base/sys/Parallel.spec',
				'base/sys/Process.spec',
				'base/sys/SourceLocation.spec',
				'base/sys/StackFrame.spec'
			];
			is 'base:math:*': [
				'base/math/Math.spec'
			];
			else: [];
		};
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
						local String is importStr: item:stringValue;
						local Array of String is wildcards: self:expandWildcard(rawPath: importStr);
						if (wildcards:length() > 0) {
							wildcards:each(action: local Function(String is f){
								local String is wPath: self:resolveLibFile(relUnderLib: f);
								if (wPath != '') {
									self:loadFile(filePath: wPath);
								}
							});
						} else {
							local String is resolved: self:resolvePath(rawPath: importStr);
							if (resolved != '') {
								self:loadFile(filePath: resolved);
							} else {
								self:parseErrors:add(item: '  [LoadError] Cannot resolve import \'' . importStr . '\' declared in class \'' . c:name . '\'.');
							}
						}
					});
				}
			}
		});
	}

	## Resolves one array-form using entry against the scan roots (the spec
	## executable's directory and the input file's directory). String segments
	## name the package; the last element being a bare class identifier loads
	## that one class, a string loads the whole package directory.
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
			} else {
				parts:add(item: seg:stringValue);
			}
		});
		local Array of String is roots: self:scanRoots();
		local Boolean is resolved: false;
		roots:each(action: local Function(String is root){
			local String is dir: root;
			parts:each(action: local Function(String is p){
				dir: dir . '/' . p;
			});
			# Ownership note: concat results ride the claim pool, and nested
			# package loading recycles slots across loadFile calls — a recycled
			# slot frees a path the parser's sourceFile field still holds. The
			# floor copy hands loadFile an unambiguously owned string.
			if (termClass != '') {
				local String is classFile: Buf:stringCopy(b: dir . '/' . termClass . '.spec');
				if (File:exists(path: classFile)) {
					resolved: true;
					self:loadFile(filePath: classFile);
					return;
				}
				# The class may share a file with its package siblings (e.g.
				# LintIssue inside Linter.spec): load the whole directory.
				if (File:exists(path: dir)) {
					resolved: true;
					local Array of String is dirNames: Dir:dirList(path: dir);
					dirNames:each(action: local Function(String is nm){
						if (nm:endsWith(suffix: '.spec')) {
							self:loadFile(filePath: Buf:stringCopy(b: dir . '/' . nm));
						}
					});
				}
				return;
			}
			if (File:exists(path: dir)) {
				resolved: true;
				local Array of String is names: Dir:dirList(path: dir);
				names:each(action: local Function(String is nm){
					if (nm:endsWith(suffix: '.spec')) {
						self:loadFile(filePath: Buf:stringCopy(b: dir . '/' . nm));
					}
				});
			}
		});
		if (!resolved) {
			local String is wanted: '';
			parts:each(action: local Function(String is p){
				if (wanted == '') {
					wanted: p;
				} else {
					wanted: wanted . ':' . p;
				}
			});
			if (termClass != '') {
				if (wanted == '') {
					wanted: termClass;
				} else {
					wanted: wanted . ':' . termClass;
				}
			}
			self:parseErrors:add(item: '  [LoadError] Cannot resolve import \'[' . wanted . ']' . '\' declared in class \'' . c:name . '\'.');
		}
	}

	## Number of files loaded so far (package-resolution progress metric).
	##
	## @return: The loaded-file count.
	Function of Int is loadedFileCount(){
		return self:loadedFiles:length();
	}

	## Scan roots for package resolution, in priority order: the input
	## file's directory and up to three ancestors (so a binary run outside
	## the project layout still finds the project's packages), then the spec
	## executable's directory and its parent (a bin/-layout install keeps
	## packages at the prefix), then the working directory. Input-relative
	## roots come first so the migration stdlib (spec/lib) shadows the
	## legacy lib while both exist; the legacy lib only serves classes the
	## migration has not absorbed yet.
	Function of Array of String is scanRoots(){
		local Array of String is roots: [];
		local String is inDir: self:dirOf(path: self:rootInputPath);
		local Int is hops: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return inDir != '' && hops < 4;
			},
			iteration: local Function of Boolean(){
				roots:add(item: inDir);
				inDir: self:dirOf(path: inDir);
				hops: hops + 1;
				return true;
			}
		);
		local String is exeDir: Dir:exeDir();
		roots:add(item: exeDir);
		local String is upDir: self:dirOf(path: exeDir);
		if (upDir != '') {
			roots:add(item: upDir);
		}
		roots:add(item: '.');
		return roots;
	}

	## Resolves a lib-root-relative path (e.g. 'base/core/String.spec')
	## against the scan roots under three prefixes, in shadowing priority:
	## the migration stdlib (spec/lib), the compiler distribution tree
	## (spec/ — where the sysinternal floor lives), then the legacy lib.
	## Returns '' when no root serves the file.
	##
	## @param relUnderLib: Path relative to the lib root.
	## @return: The resolved file path, or ''.
	Function of String is resolveLibFile(String is relUnderLib){
		local Array of String is roots: self:scanRoots();
		local String is found: '';
		local Int is ri: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return found == '' && ri < roots:length();
			},
			iteration: local Function of Boolean(){
				local String is root: roots:get(index: ri);
				ri: ri + 1;
				local String is cand: root . '/spec/lib/' . relUnderLib;
				if (File:exists(path: cand)) {
					found: cand;
					return true;
				}
				cand: root . '/spec/' . relUnderLib;
				if (File:exists(path: cand)) {
					found: cand;
					return true;
				}
				cand: root . '/lib/' . relUnderLib;
				if (File:exists(path: cand)) {
					found: cand;
				}
				return true;
			}
		);
		return found;
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
			'base/core/String.spec',
			'base/sys/Buf.spec',
			'base/sys/Dir.spec',
			'base/core/Stringable.spec',
			'base/core/Any.spec'
		];
		preloads:each(action: local Function(String is rel){
			local String is path: self:resolveLibFile(relUnderLib: rel);
			if (path != '') {
				self:loadFile(filePath: path);
			}
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
