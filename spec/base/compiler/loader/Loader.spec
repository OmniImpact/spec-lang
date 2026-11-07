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
		['spec', 'base', 'sysinternal', Buf],
		['spec', 'base', 'sysinternal', Dir],
		['lib', 'base', 'struct', Array],
		['lib', 'base', 'struct', Map],
		['lib', 'base', 'iterator']
	];

	local Map of String to String is loadedFiles: Map:init();
	local String is rootInputPath: '';
	local Array of ClassInfo is loadedClasses: [];
	local Map of String to String is seenClassNames: Map:init();
	local Array of String is parseErrors: [];

	## Group targets declared by fragments via the `group` pseudo-field (load order).
	local Array of String is groupTargets: [];

	## Group fragments corresponding to [groupTargets] (load order).
	local Array of ClassInfo is groupFragments: [];

	replace Function is init(){
		self:loadedFiles: Map:init();
		self:loadedClasses: [];
		self:seenClassNames: Map:init();
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

	## Expands wildcard package import paths into standard library file lists.
	##
	## @param rawPath: Wildcard package identifier (e.g. "base:io:*").
	## @return: Array of constituent file paths.
	Function of Array of String is expandWildcard(String is rawPath){
		return when (rawPath) {
			is 'base:io:*': [
				'lib/base/io/File.spec',
				'lib/base/io/Input.spec',
				'lib/base/io/InputHandler.spec',
				'lib/base/io/Output.spec',
				'lib/base/io/Ansi.spec'
			];
			is 'base:iterator:*': [
				'lib/base/iterator/Loop.spec',
				'lib/base/iterator/LoopControl.spec',
				'lib/base/iterator/LoopCallback.spec',
				'lib/base/iterator/While.spec'
			];
			is 'base:meta:*': [
				'lib/base/meta/AST.spec'
			];
			is 'base:reflect:*': [
				'lib/base/reflect/Type.spec',
				'lib/base/reflect/Parameter.spec',
				'lib/base/reflect/Member.spec',
				'lib/base/reflect/ClassInfo.spec'
			];
			is 'base:struct:*': [
				'lib/base/struct/Array.spec',
				'lib/base/struct/Map.spec'
			];
			is 'base:core:*': [
				'lib/base/core/String.spec',
				'lib/base/core/Stringable.spec',
				'lib/base/core/Any.spec'
			];
			is 'base:sysinternal:*': [
				'lib/base/sysinternal/Buf.spec',
				'lib/base/sysinternal/Dir.spec'
			];
			is 'base:sys:*': [
				'lib/base/sys/Parallel.spec',
				'lib/base/sys/Process.spec',
				'lib/base/sys/SourceLocation.spec',
				'lib/base/sys/StackFrame.spec'
			];
			is 'base:math:*': [
				'lib/base/math/Math.spec'
			];
			# At Phase H (self-hosting) this group switches to the spec/
			# tree; until then it names the fossil's own sources, which a
			# user program never imports.
			is 'compiler:*': [
				'lib/compiler/Token.spec',
				'lib/compiler/Lexer.spec',
				'lib/compiler/Parser.spec',
				'lib/compiler/Linter.spec',
				'lib/compiler/TypeChecker.spec',
				'lib/compiler/CBackendUtils.spec',
				'lib/compiler/RuntimePrelude.spec',
				'lib/compiler/DeclarationGenerator.spec',
				'lib/compiler/BuiltinCallGenerator.spec',
				'lib/compiler/CodeGenerator.spec',
				'lib/compiler/Loader.spec',
				'lib/compiler/Driver.spec'
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
			if (!self:seenClassNames:has(key: c:name)) {
				self:seenClassNames:set(key: c:name, value: 'true');
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
								self:loadFile(filePath: f);
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

	## Scan roots for package resolution: the spec executable's directory
	## and its parent (a bin/-layout install keeps packages at the prefix),
	## then the input file's directory and up to three of its ancestors —
	## so a binary run outside the project tree (tests, installed tools)
	## still finds the project's packages.
	Function of Array of String is scanRoots(){
		local Array of String is roots: [];
		local String is exeDir: Dir:exeDir();
		roots:add(item: exeDir);
		local String is upDir: self:dirOf(path: exeDir);
		if (upDir != '') {
			roots:add(item: upDir);
		}
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
		# The working directory closes the walk: relative input paths bottom
		# out above the project root, which for a tool invoked from the
		# project is exactly where the packages live.
		roots:add(item: '.');
		return roots;
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
		self:parseErrors: [];
		self:groupTargets: [];
		self:groupFragments: [];

		# Root class lattice preloads, before any user code.
		self:loadFile(filePath: 'lib/base/core/String.spec');
		self:loadFile(filePath: 'lib/base/sysinternal/Buf.spec');
		self:loadFile(filePath: 'lib/base/sysinternal/Dir.spec');
		self:loadFile(filePath: 'lib/base/core/Stringable.spec');
		self:loadFile(filePath: 'lib/base/core/Any.spec');

		self:rootInputPath: rootPath;
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
