#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, Linter, TypeChecker, CodeGenerator, Driver, and Loader.

## Resolves and loads multi-file package imports across the Spec project and standard library.
Class is Loader{

	replace Array of String is using: [
		base:io:File,
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:ClassInfo,
		base:reflect:Member,
		compiler:Token,
		compiler:Lexer,
		compiler:Parser,
		base:meta:*
	];

	local Map of String to String is loadedFiles: Map:init();
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
			self:pos: self:pos + 1;
			if (ch == ':') {
				self:res: self:res . '/';
			} else {
				self:res: self:res . ch;
			}
			return true;
		}
	}

	## Converts a Spec package identifier path (e.g. "base:struct:Array") into a filesystem path.
	##
	## @param rawPath: Colon-separated package identifier.
	## @return: Resolved filesystem path string, or empty string if not found.
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
			is 'base:sys:*': [
				'lib/base/sys/Parallel.spec',
				'lib/base/sys/Process.spec',
				'lib/base/sys/SourceLocation.spec',
				'lib/base/sys/StackFrame.spec'
			];
			is 'base:math:*': [
				'lib/base/math/Math.spec'
			];
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
	local Function is loadFile(String is filePath){
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
			lexer:getErrors():each(action: local Function(String is err){
				self:parseErrors:add(item: '  [LexError] [' . filePath . '] ' . err);
			});
		}
		local Parser is parser: Parser:init(tokens: tokens);
		parser:setSourceFile(file: filePath);
		local ProgramNode is prog: parser:parseProgram();
		if (parser:hasErrors()) {
			parser:getErrors():each(action: local Function(String is err){
				self:parseErrors:add(item: err);
			});
		}

		prog:getClasses():each(action: local Function(ClassInfo is c){
			c:getMembers():each(action: local Function(Member is m){
				m:setSourceFile(file: filePath);
			});
			local String is gName: self:groupTargetOf(c: c);
			if (!self:seenClassNames:has(key: c:getName())) {
				self:seenClassNames:set(key: c:getName(), value: 'true');
				self:loadedClasses:add(item: c);
				if (gName != '' && gName != c:getName()) {
					self:groupTargets:add(item: gName);
					self:groupFragments:add(item: c);
				}
			} else {
				if (gName == c:getName()) {
					local ClassInfo is existing: self:findLoadedClass(name: c:getName());
					if (existing:getName() != '') {
						self:mergeFragmentInto(target: existing, frag: c);
					}
				}
			}
			self:collectImportsFromClass(c: c);
		});
	}

	## Gathers and loads all `using` imports declared in a class definition.
	##
	## @param c: Target [ClassInfo] definition.
	local Function is collectImportsFromClass(ClassInfo is c){
		c:getMembers():each(action: local Function(Member is m){
			if (m:getName() == 'using' && m:getHasInit()) {
				local Expression is initExpr: m:getInitExpr();
				if (initExpr:getKind() == 'ARRAY') {
					initExpr:arrayItems:each(action: local Function(Expression is item){
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
								self:parseErrors:add(item: '  [LoadError] Cannot resolve import \'' . importStr . '\' declared in class \'' . c:getName() . '\'.');
							}
						}
					});
				}
			}
		});
	}

	## Extracts the load-time group target declared via the `group` pseudo-field.
	##
	## The field is optional; when present it must be a single-entry string array
	## naming the class this fragment merges into. Fragments must not declare
	## `extends` (enums included). An empty string means "not a fragment".
	##
	## @param c: Candidate [ClassInfo] definition.
	## @return: Group target class name, or empty string when not a fragment.
	local Function of String is groupTargetOf(ClassInfo is c){
		local Array of Member is members: c:getMembers();
		local Int is idx: 0;
		local String is target: '';
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < members:length();
			},
			iteration: local Function of Boolean(){
				local Member is m: members:get(index: idx);
				if (m:getName() == 'group' && m:getHasInit()) {
					local Expression is initExpr: m:getInitExpr();
					if (initExpr:getKind() == 'ARRAY') {
						if (initExpr:arrayItems:length() != 1) {
							self:parseErrors:add(item: '  [LoadError] ClassInfo \'' . c:getName() . '\' declares a group with ' . initExpr:arrayItems:length() . ' entries; exactly one target is required.');
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
		if (target != '' && c:getBaseClass() != '') {
			self:parseErrors:add(item: '  [LoadError] Group fragment \'' . c:getName() . '\' must not declare parent classes.');
			target: '';
		}
		return target;
	}

	## Finds an already-loaded class by name.
	##
	## @param name: ClassInfo name to locate.
	## @return: The loaded [ClassInfo], or an empty-named ClassInfo when absent.
	local Function of ClassInfo is findLoadedClass(String is name){
		local Int is idx: 0;
		local ClassInfo is res: ClassInfo:init(name: '', baseClass: '', members: []);
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < self:loadedClasses:length() && res:getName() == '';
			},
			iteration: local Function of Boolean(){
				local ClassInfo is c: self:loadedClasses:get(index: idx);
				if (c:getName() == name) {
					res: c;
				}
				idx: idx + 1;
				return true;
			}
		);
		return res;
	}

	## Finds a named member on a class (empty-named members such as nested
	## classes are ignored).
	##
	## @param target: [ClassInfo] whose members are searched.
	## @param name: Member name to locate.
	## @return: The existing [Member], or an empty-named Member when absent.
	local Function of Member is findMemberNamed(ClassInfo is target, String is name){
		if (name == '') {
			return Member:init(kind: '');
		}
		local Array of Member is members: target:getMembers();
		local Int is idx: 0;
		local Member is res: Member:init(kind: '');
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < members:length() && res:getName() == '';
			},
			iteration: local Function of Boolean(){
				local Member is m: members:get(index: idx);
				if (m:getName() == name) {
					res: m;
				}
				idx: idx + 1;
				return true;
			}
		);
		return res;
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
	local Function is mergeFragmentInto(ClassInfo is target, ClassInfo is frag){
		if (target:getBaseClass() == 'Enum') {
			self:parseErrors:add(item: '  [LoadError] Group target \'' . target:getName() . '\' is an Enum; grouping is only supported for classes.');
			return;
		}
		local Array of Member is fragMembers: frag:getMembers();
		local Int is idx: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < fragMembers:length();
			},
			iteration: local Function of Boolean(){
				local Member is m: fragMembers:get(index: idx);
				local String is mName: m:getName();
				if (mName != 'using' && mName != 'group') {
					local Member is dup: self:findMemberNamed(target: target, name: mName);
					if (dup:getName() != '') {
						self:parseErrors:add(item: '  [LoadError] Duplicate member \'' . mName . '\' in class \'' . target:getName() . '\' (' . m:getSourceFile() . ' conflicts with declaration in ' . dup:getSourceFile() . ').');
					} else {
						target:getMembers():add(item: m);
					}
				}
				idx: idx + 1;
				return true;
			}
		);

		# Union the fragment's `using` entries into the target's `using` array.
		local Member is fragUsing: self:findMemberNamed(target: frag, name: 'using');
		if (fragUsing:getName() == 'using') {
			local Member is targetUsing: self:findMemberNamed(target: target, name: 'using');
			if (targetUsing:getName() == 'using') {
				local Expression is fragItems: fragUsing:getInitExpr();
				local Expression is targetItems: targetUsing:getInitExpr();
				if (fragItems:getKind() == 'ARRAY' && targetItems:getKind() == 'ARRAY') {
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
				target:getMembers():add(item: fragUsing);
			}
		}

		# Strip the `group` declaration from the merged class.
		self:stripMemberNamed(target: target, name: 'group');

		# Enforce the single-init rule across the merged class.
		local Int is initCount: 0;
		local String is initFile: '';
		local Array of Member is mergedMembers: target:getMembers();
		local Int is scan: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return scan < mergedMembers:length();
			},
			iteration: local Function of Boolean(){
				local Member is m: mergedMembers:get(index: scan);
				if (m:getName() == 'init') {
					initCount: initCount + 1;
					initFile: m:getSourceFile();
				}
				scan: scan + 1;
				return true;
			}
		);
		if (initCount > 1) {
			self:parseErrors:add(item: '  [LoadError] Multiple init methods in class \'' . target:getName() . '\' (last declared in ' . initFile . '); a grouped class may declare at most one.');
		}
	}

	## Removes members with the given name from a class.
	##
	## @param target: [ClassInfo] to modify.
	## @param name: Member name to strip.
	local Function is stripMemberNamed(ClassInfo is target, String is name){
		local Array of Member is members: target:getMembers();
		local Int is idx: members:length() - 1;
		While:condition(
			evaluate: local Function of Boolean(){
				return idx >= 0;
			},
			iteration: local Function of Boolean(){
				local Member is m: members:get(index: idx);
				if (m:getName() == name) {
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
	local Function is removeClassFromLoaded(ClassInfo is c){
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
	local Function is mergeGroups(){
		local Int is idx: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < self:groupTargets:length();
			},
			iteration: local Function of Boolean(){
				local String is gName: self:groupTargets:get(index: idx);
				local ClassInfo is frag: self:groupFragments:get(index: idx);
				local ClassInfo is target: self:findLoadedClass(name: gName);
				if (target:getName() == '') {
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
		self:loadFile(filePath: 'lib/base/core/Stringable.spec');
		self:loadFile(filePath: 'lib/base/core/Any.spec');

		self:loadFile(filePath: rootPath);
		self:appendImplicitAny();
		self:mergeGroups();

		return ProgramNode:init(classes: self:loadedClasses);
	}

	## Appends `Any` as the parent of every class without explicit parents
	## (enums excluded).
	Function is appendImplicitAny(){
		self:loadedClasses:each(action: local Function(ClassInfo is c){
			if (c:getBaseClass() != 'Enum' && c:getBaseClasses():length() == 0 && c:getName() != 'Any' && c:getName() != 'Stringable') {
				c:withBaseClasses(name: c:getName(), baseClasses: ['Any'], members: c:getMembers());
			}
		});
	}

}
