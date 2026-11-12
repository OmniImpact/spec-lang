#! Package speclint
#! Pure-Spec modular code linter with reflection-based rule discovery
#! and Phase 0.5 instance-model audit.

Class is Linter{
	namespace: ['speclint'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'sys', Output],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'sys', as Loops()],
		['base', 'sys', as Output()],
		['speclint', LintIssue],
		['speclint', LintRule],
		['speclint', SourceMasker],
		['speclint', 'rules'],
		['speclint', 'rules', TabIndentationRule],
		['speclint', 'rules', TrailingWhitespaceRule],
		['speclint', 'rules', BraceAlignmentRule],
		['speclint', 'rules', LoopConstructionRule],
		['speclint', 'rules', GetStringDefaultRule],
		['speclint', 'rules', MathRandomRule],
		['speclint', 'rules', EncourageAsConditionalRule],
		['speclint', 'rules', EncourageAsLoopsRule],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Conditional()]
	];

	## Registered lint rules discovered via reflection or fallback.
	Array of LintRule is rules: [];

	## Audit name sets (Phase 0.5): every enum and class name in
	## the loaded program, nested classes included.
	local Map of String to String is auditEnums: Map:init();
	local Map of String to String is auditClasses: Map:init();

	## Worklist notices gathered by the audit pass.
	local Array of LintIssue is auditIssues: [];

	## The class whose members are currently being audited (with save and
	## restore around nested-class recursion).
	local ClassInfo is auditOwner: ClassInfo:init(name: '', baseClass: '', members: []);

	## Loaded class nodes by name, for the inherited-import walk.
	local Map of String to ClassInfo is auditClassNodes: Map:init();
	local Array of ClassInfo is auditClassList: [];

	## Lowercase floor singletons routed by name.
	local Array of String is floorAliases: [];

	## Type-level exempt receivers (X3): primitives, base
	## conversion targets, containers.
	local Array of String is exemptClasses: [];

	replace Function is init(){
		self:rules: [];
		self:auditEnums: Map:init();
		self:auditClasses: Map:init();
		self:auditClassNodes: Map:init();
		self:auditClassList: [];
		self:auditIssues: [];
		self:floorAliases: [];
		self:exemptClasses: ['Int', 'Byte', 'Float', 'Boolean', 'String', 'Any', 'Hex', 'Bin', 'Oct', 'Array', 'Map', 'List'];
		self:discoverRules();
	}

	## Discovers rules via reflection over the class registry, falling
	## back to explicit registration if reflection finds none.
	Function is discoverRules(){
		self:rules: [];
		classNames():each(action: local Function(String is cn){
			if({ extendsClass(className: cn, baseName: 'LintRule') && cn != 'LintRule' }, {
				local LintRule is rule: instantiate(className: cn) as LintRule;
				self:rules:add(item: rule);
			});
		});
		if({ self:rules:length() == 0 }, {
			self:registerDefaultRules();
		});
	}

	## Explicit fallback registration of default rules.
	Function is registerDefaultRules(){
		self:rules:add(item: TabIndentationRule:init());
		self:rules:add(item: TrailingWhitespaceRule:init());
		self:rules:add(item: BraceAlignmentRule:init());
		self:rules:add(item: LoopConstructionRule:init());
		self:rules:add(item: GetStringDefaultRule:init());
		self:rules:add(item: MathRandomRule:init());
		self:rules:add(item: EncourageAsConditionalRule:init());
		self:rules:add(item: EncourageAsLoopsRule:init());
	}

	## Adds a custom rule to the linter.
	##
	## @param rule: [LintRule] instance to add.
	Function is addRule(LintRule is rule){
		self:rules:add(item: rule);
	}

	## Analyzes source code text and optional AST, returning all detected lint issues.
	##
	## @param source: Raw source code string.
	## @param program: Parsed [ProgramNode] AST.
	## @return: [Array] of [LintIssue] items.
	Function of Array of LintIssue is lint(String is source, ProgramNode is program){
		local Array of LintIssue is issues: [];

		# 1. Source-level checks across registered rules
		self:rules:each(action: local Function(LintRule is r){
			r:checkSource(source: source, issues: issues);
		});

		# 2. AST-level checks across registered rules
		self:rules:each(action: local Function(LintRule is r){
			r:checkProgram(program: program, issues: issues);
		});

		return issues;
	}

	## Counts the total number of warnings in an issues list.
	##
	## @param issues: Issues array.
	## @return: Count of warnings.
	Function of Int is countWarnings(Array of LintIssue is issues){
		local Int is res: 0;
		issues:each(action: local Function(LintIssue is issue){
			if({ issue:isWarning }, {
				res: res + 1;
			});
		});
		return res;
	}

	## Counts the total number of notices in an issues list.
	##
	## @param issues: Issues array.
	## @return: Count of notices.
	Function of Int is countNotices(Array of LintIssue is issues){
		local Int is res: 0;
		issues:each(action: local Function(LintIssue is issue){
			if({ !issue:isWarning }, {
				res: res + 1;
			});
		});
		return res;
	}

	## Prints formatted lint diagnostics to standard output.
	##
	## @param filePath: Source file path.
	## @param issues: Array of detected [LintIssue] items.
	Function is report(String is filePath, Array of LintIssue is issues){
		Output:line('Checking \'' . filePath . '\' for Spec code standards...');
		issues:each(action: local Function(LintIssue is issue){
			Output:line(issue:toString());
		});

		local Int is warnings: self:countWarnings(issues: issues);
		local Int is notices: self:countNotices(issues: issues);
		Output:line("\nLint summary for " . filePath . ': ' . (warnings as String) . ' warning(s), ' . (notices as String) . ' notice(s).');
		if({ warnings == 0 }, {
			Output:line('All standard checks passed successfully.');
		});
	}

	## =========================================================================
	## Phase 0.5 Worklist Audit (Instance-Model Transition)
	## =========================================================================

	## Phase 0.5 worklist audit: reports every call whose receiver names a class
	## (or floor alias) with a non-init method, excluding the exempt strata.
	##
	## @param program: Loaded [ProgramNode].
	## @return: [Array] of [LintIssue] worklist notices.
	Function of Array of LintIssue is auditProgram(ProgramNode is program){
		self:auditIssues: [];
		self:buildAuditNameSets(classes: program:classes);
		program:classes:each(action: local Function(ClassInfo is c){
			self:auditClass(classDef: c);
		});
		return self:auditIssues;
	}

	## Registers one class or enum name, nested classes included.
	Function is registerAuditName(ClassInfo is c){
		if({ c:baseClass == 'Enum' }, {
			self:auditEnums:set(key: c:name, value: 'true');
		}, {
			self:auditClasses:set(key: c:name, value: 'true');
		});
		self:auditClassNodes:set(key: c:name, value: c);
		self:auditClassList:add(item: c);
		c:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:CLASS }, {
				self:registerAuditName(c: m:nestedClass);
			});
		});
	}

	## Collects class and enum names into the audit sets.
	Function is buildAuditNameSets(Array of ClassInfo is classes){
		classes:each(action: local Function(ClassInfo is c){
			self:registerAuditName(c: c);
		});
	}

	## Audits every method body of a class definition, nested classes included.
	Function is auditClass(ClassInfo is classDef){
		local ClassInfo is savedOwner: self:auditOwner;
		self:auditOwner: classDef;
		classDef:members:each(action: local Function(Member is m){
			match(on: m:kind, when: [
				MemberKind:METHOD: {
					m:body:each(action: local Function(Statement is s){
						self:auditStatement(stmt: s, file: m:sourceFile);
					});
				},
				MemberKind:CLASS: {
					self:auditClass(classDef: m:nestedClass);
				}
			]);
		});
		self:auditOwner: savedOwner;
	}

	## Walks one statement, auditing every expression it contains.
	Function is auditStatement(Statement is stmt, String is file){
		match(on: stmt:kind, when: [
			StatementKind:VAR_DECL: {
				if({ stmt:hasInit }, {
					self:auditExpression(expr: stmt:initExpr, file: file);
				});
			},
			StatementKind:ASSIGN: {
				self:auditExpression(expr: stmt:assignTarget, file: file);
				self:auditExpression(expr: stmt:assignValue, file: file);
			},
			StatementKind:RETURN: {
				if({ stmt:hasReturnExpr }, {
					self:auditExpression(expr: stmt:returnExpr, file: file);
				});
			},
			StatementKind:CLASS: {
				self:auditClass(classDef: stmt:nestedClass);
			},
			StatementKind:EXPR: {
				self:auditExpression(expr: stmt:exprStmt, file: file);
			},
			StatementKind:FORWARD: {
				stmt:forwardArgs:each(action: local Function(NamedArg is arg){
					self:auditExpression(expr: arg:value, file: file);
				});
			}
		]);
	}

	## Walks one expression, auditing calls it contains.
	Function is auditExpression(Expression is expr, String is file){
		match(on: expr:kind, when: [
			ExpressionKind:CALL: {
				self:auditReceiver(callExpr: expr, file: file);
				self:auditExpression(expr: expr:methodTarget, file: file);
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					self:auditExpression(expr: arg:value, file: file);
				});
			},
			ExpressionKind:BINARY: {
				self:auditExpression(expr: expr:leftExpr, file: file);
				self:auditExpression(expr: expr:rightExpr, file: file);
			},
			ExpressionKind:UNARY: {
				self:auditExpression(expr: expr:unaryExpr, file: file);
			},
			ExpressionKind:ARRAY: {
				expr:arrayItems:each(action: local Function(Expression is item){
					self:auditExpression(expr: item, file: file);
				});
			},
			ExpressionKind:MAP: {
				expr:mapKeys:each(action: local Function(Expression is k){
					self:auditExpression(expr: k, file: file);
				});
				expr:mapValues:each(action: local Function(Expression is v){
					self:auditExpression(expr: v, file: file);
				});
			},
			ExpressionKind:CAST: {
				self:auditExpression(expr: expr:leftExpr, file: file);
				expr:castArgs:each(action: local Function(Expression is a){
					self:auditExpression(expr: a, file: file);
				});
			},
			ExpressionKind:FIELD_ACCESS: {
				self:auditExpression(expr: expr:leftExpr, file: file);
			},
			ExpressionKind:INDEX: {
				self:auditExpression(expr: expr:leftExpr, file: file);
				expr:castArgs:each(action: local Function(Expression is a){
					self:auditExpression(expr: a, file: file);
				});
			},
			ExpressionKind:ANON_FN: {
				expr:anonBody:each(action: local Function(Statement is s){
					self:auditStatement(stmt: s, file: file);
				});
			}
		]);
	}

	## Classifies one call's receiver: flags class-named calls invoking non-init members.
	Function is auditReceiver(Expression is callExpr, String is file){
		local String is name: '';
		local Boolean is isFloorChain: false;
		if({ callExpr:methodTarget:kind == ExpressionKind:IDENT }, {
			name: callExpr:methodTarget:str;
		}, {
			if({ callExpr:methodTarget:kind == ExpressionKind:PATH }, {
				local Array of String is segs: callExpr:methodTarget:pathSegments;
				if({ segs:length() == 0 }, {
					return;
				});
				name: segs:get(index: segs:length() - 1);
				segs:each(action: local Function(String is seg){
					if({ seg == 'sysinternal' }, {
						isFloorChain: true;
					});
				});
			}, {
				return;
			});
		});
		if({ isFloorChain || name == '' || name == 'self' }, {
			return;
		});
		if({ callExpr:methodName == 'init' }, {
			return;
		});
		if({ self:isUpperName(name: name) }, {
			if({ self:auditEnums:has(key: name) }, {
				return;
			});
			local Boolean is isExempt: false;
			self:exemptClasses:each(action: local Function(String is e){
				if({ e == name }, {
					isExempt: true;
				});
			});
			if({ isExempt }, {
				return;
			});
			if({ !self:auditClasses:has(key: name) }, {
				return;
			});
			if({ self:auditOwnerImportsAs(name: name) }, {
				return;
			});
			if({ self:isHeldMember(clsName: name, memberName: callExpr:methodName) }, {
				return;
			});
		}, {
			local Boolean is isAlias: false;
			self:floorAliases:each(action: local Function(String is a){
				if({ a == name }, {
					isAlias: true;
				});
			});
			if({ !isAlias }, {
				return;
			});
		});
		local String is msg: 'Instance-model worklist: \'' . name . ':' . callExpr:methodName . '\' calls a member through a class name (' . file . ').';
		self:auditIssues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
	}

	## True when the class under audit, or any ancestor, instance-imports [name].
	Function of Boolean is auditOwnerImportsAs(String is name){
		return self:auditImportsAsAnywhere(clsName: self:auditOwner:name, targetName: name);
	}

	## Recursive import search over the audit's ancestor lattice.
	Function of Boolean is auditImportsAsAnywhere(String is clsName, String is targetName, Map of String to String is visited: Map:init()){
		if({ clsName == '' || clsName == 'Any' || visited:has(key: clsName) }, {
			return false;
		});
		visited:set(key: clsName, value: 'true');
		local ClassInfo is cls: self:auditClassNodes:get(key: clsName, default: self:auditOwner);
		if({ cls:name != clsName }, {
			return false;
		});
		if({ cls:instanceImportsAs(name: targetName) }, {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !viaParent && self:auditImportsAsAnywhere(clsName: baseName, targetName: targetName, visited: visited) }, {
				viaParent: true;
			});
		});
		return viaParent;
	}

	## True when [memberName] is a held member on [clsName] or any of its ancestors.
	Function of Boolean is isHeldMember(String is clsName, String is memberName, Map of String to String is visited: Map:init()){
		if({ clsName == '' || clsName == 'Any' || visited:has(key: clsName) }, {
			return false;
		});
		visited:set(key: clsName, value: 'true');
		local Boolean is found: false;
		self:auditClassList:each(action: local Function(ClassInfo is cls){
			if({ !found && cls:name == clsName }, {
				cls:members:each(action: local Function(Member is m){
					if({ !found && m:name == memberName && m:hasModifier(kw: Keyword:HELD) }, {
						found: true;
					});
				});
				if({ !found }, {
					cls:baseClasses:each(action: local Function(String is baseName){
						if({ !found && self:isHeldMember(clsName: baseName, memberName: memberName, visited: visited) }, {
							found: true;
						});
					});
				});
			});
		});
		return found;
	}

	## True when [name] starts with an uppercase letter.
	Function of Boolean is isUpperName(String is name){
		if({ name:length() == 0 }, {
			return false;
		});
		local String is first: name:charAt(index: 0, default: '');
		return match(on: first, when: [
			['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']: { true },
			['N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']: { true },
			else: { false }
		]);
	}

	## Prints the audit worklist: per-site lines, then the total count.
	Function is auditReport(String is filePath, Array of LintIssue is issues){
		Output:line('Instance-model audit of \'' . filePath . '\':');
		issues:each(action: local Function(LintIssue is issue){
			Output:line(issue:toString());
		});
		Output:line('Instance-model worklist: ' . (issues:length() as String) . ' call site(s) must migrate (Phase 0.5).');
	}
}
