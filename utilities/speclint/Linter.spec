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
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'lexer', Keyword],
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
		['speclint', 'rules', BracketIndentationRule],
		['speclint', 'rules', BlankLinesRule],
		['speclint', 'rules', UnnecessarySelfColonRule],
		['speclint', 'rules', InitShorthandRule],
		['speclint', 'rules', UnusedUsingRule],
		['speclint', 'rules', HeldErrorStateRule],
		['speclint', 'rules', TemplateStringRule],
		['speclint', 'rules', MergeUsingRule],
		['speclint', 'rules', CompactUsingRule],
		['speclint', 'rules', NarrowingCastRule],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Conditional()]
	];

	## Registered lint rules discovered via reflection or fallback.
	Array of LintRule is rules: Array();

	## Audit name sets (Phase 0.5): every enum and class name in
	## the loaded program, nested classes included.
	local Map of String to String is auditEnums: Map:init();
	local Map of String to String is auditClasses: Map:init();

	## Worklist notices gathered by the audit pass.
	local Array of LintIssue is auditIssues: Array();

	## The class whose members are currently being audited (with save and
	## restore around nested-class recursion).
	local ClassInfo is auditOwner: ClassInfo:init(name: '', baseClass: '', members: Array());

	## Loaded class nodes by name, for the inherited-import walk.
	local Map of String to ClassInfo is auditClassNodes: Map:init();
	local Array of ClassInfo is auditClassList: Array();

	## Lowercase floor singletons routed by name.
	local Array of String is floorAliases: Array();

	## Type-level exempt receivers (X3): primitives, base
	## conversion targets, containers.
	local Array of String is exemptClasses: Array();

	replace Function is init(){
		:rules: Array();
		:auditEnums: Map:init();
		:auditClasses: Map:init();
		:auditClassNodes: Map:init();
		:auditClassList: Array();
		:auditIssues: Array();
		:floorAliases: Array();
		:exemptClasses: Array(['Int', 'Byte', 'Float', 'Boolean', 'String', 'Any', 'Hex', 'Bin', 'Oct', 'Array', 'Map', 'List']);
		:discoverRules();
	}

	## Discovers rules via reflection over the class registry, falling
	## back to explicit registration if reflection finds none.
	Function is discoverRules(){
		:rules: Array();
		classNames():each(action: local Function(String is cn){
			if({ extendsClass(className: cn, baseName: 'LintRule') && cn != 'LintRule' }, {
				local LintRule is rule: instantiate(className: cn) as LintRule;
				:rules:add(item: rule);
			});
		});
		if({ :rules:length() == 0 }, {
			:registerDefaultRules();
		});
	}

	## Explicit fallback registration of default rules.
	Function is registerDefaultRules(){
		:rules:add(item: TabIndentationRule:init());
		:rules:add(item: TrailingWhitespaceRule:init());
		:rules:add(item: BraceAlignmentRule:init());
		:rules:add(item: LoopConstructionRule:init());
		:rules:add(item: GetStringDefaultRule:init());
		:rules:add(item: MathRandomRule:init());
		:rules:add(item: EncourageAsConditionalRule:init());
		:rules:add(item: EncourageAsLoopsRule:init());
		:rules:add(item: BracketIndentationRule:init());
		:rules:add(item: BlankLinesRule:init());
		:rules:add(item: UnnecessarySelfColonRule:init());
		:rules:add(item: InitShorthandRule:init());
		:rules:add(item: UnusedUsingRule:init());
		:rules:add(item: TemplateStringRule:init());
		:rules:add(item: MergeUsingRule:init());
		:rules:add(item: CompactUsingRule:init());
	}

	## Adds a custom rule to the linter.
	##
	## @param rule: [LintRule] instance to add.
	Function is addRule(LintRule is rule){
		:rules:add(item: rule);
	}

	## Analyzes source code text and optional AST, returning all detected lint issues.
	##
	## @param source: Raw source code string.
	## @param program: Parsed [ProgramNode] AST.
	## @return: [Array] of [LintIssue] items.
	Function of Array of LintIssue is lint(String is source, ProgramNode is program){
		local Array of LintIssue is issues: Array();

		# 1. Source-level checks across registered rules
		:rules:each(action: local Function(LintRule is r){
			r:checkSource(source: source, issues: issues);
		});

		# 2. AST-level checks across registered rules
		:rules:each(action: local Function(LintRule is r){
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

		local Int is warnings: :countWarnings(issues: issues);
		local Int is notices: :countNotices(issues: issues);
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
		:auditIssues: Array();
		:buildAuditNameSets(classes: program:classes);
		program:classes:each(action: local Function(ClassInfo is c){
			:auditClass(classDef: c);
		});
		return :auditIssues;
	}

	## Registers one class or enum name, nested classes included.
	Function is registerAuditName(ClassInfo is c){
		if({ c:baseClass == 'Enum' }, {
			:auditEnums:set(key: c:name, value: 'true');
		}, {
			:auditClasses:set(key: c:name, value: 'true');
		});
		:auditClassNodes:set(key: c:name, value: c);
		:auditClassList:add(item: c);
		c:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:CLASS }, {
				:registerAuditName(c: m:nestedClass);
			});
		});
	}

	## Collects class and enum names into the audit sets.
	Function is buildAuditNameSets(Array of ClassInfo is classes){
		classes:each(action: local Function(ClassInfo is c){
			:registerAuditName(c: c);
		});
	}

	## Audits every method body of a class definition, nested classes included.
	Function is auditClass(ClassInfo is classDef){
		local ClassInfo is savedOwner: :auditOwner;
		:auditOwner: classDef;
		classDef:members:each(action: local Function(Member is m){
			match(on: m:kind, when: [
				MemberKind:METHOD: {
					local Int is si: 0;
					while({ si < m:body:length() }, {
						:auditStatement(stmt: m:body:get(index: si), file: m:sourceFile);
						si++;
					});
				},
				MemberKind:CLASS: {
					:auditClass(classDef: m:nestedClass);
				},
				else: {}
			]);
		});
		:auditOwner: savedOwner;
	}

	## Walks one statement, auditing every expression it contains.
	Function is auditStatement(Statement is stmt, String is file){
		match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				if({ hasInit }, {
					:auditExpression(expr: initExpr, file: file);
				});
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				:auditExpression(expr: assignTarget, file: file);
				:auditExpression(expr: assignValue, file: file);
			},
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ hasReturnExpr }, {
					:auditExpression(expr: returnExpr, file: file);
				});
			},
			Statement:ClassDecl: local Function(ClassInfo is nestedClass){
				:auditClass(classDef: nestedClass);
			},
			Statement:Expr: local Function(Expression is exprStmt){
				:auditExpression(expr: exprStmt, file: file);
			},
			Statement:Forward: local Function(Array of NamedArg is forwardArgs){
				forwardArgs:each(action: local Function(NamedArg is arg){
					:auditExpression(expr: arg:value, file: file);
				});
			}
		]);
	}

	## Walks one expression, auditing calls it contains.
	Function is auditExpression(Expression is expr, String is file){
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				:auditReceiver(call: cd, file: file);
				:auditExpression(expr: cd:target, file: file);
				cd:args:each(action: local Function(NamedArg is arg){
					:auditExpression(expr: arg:value, file: file);
				});
			},
			Expression:Binary: local Function(String is op, Expression is leftExpr, Expression is rightExpr){
				:auditExpression(expr: leftExpr, file: file);
				:auditExpression(expr: rightExpr, file: file);
			},
			Expression:Unary: local Function(String is op, Expression is operand){
				:auditExpression(expr: operand, file: file);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				items:each(action: local Function(Expression is item){
					:auditExpression(expr: item, file: file);
				});
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				keys:each(action: local Function(Expression is k){
					:auditExpression(expr: k, file: file);
				});
				values:each(action: local Function(Expression is v){
					:auditExpression(expr: v, file: file);
				});
			},
			Expression:Cast: local Function(Expression is target, String is targetType, Array of Expression is args){
				:auditExpression(expr: target, file: file);
				args:each(action: local Function(Expression is a){
					:auditExpression(expr: a, file: file);
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is field){
				:auditExpression(expr: target, file: file);
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				:auditExpression(expr: target, file: file);
				:auditExpression(expr: index, file: file);
			},
			Expression:AnonFn: local Function(Type is returnType, [Parameter] is params, [Statement] is body){
				local Int is si: 0;
				while({ si < body:length() }, {
					:auditStatement(stmt: body:get(index: si), file: file);
					si++;
				});
			}
		], default: {});
	}

	## Classifies one call's receiver: flags class-named calls invoking non-init members.
	Function is auditReceiver(CallData is call, String is file){
		local String is name: '';
		local Boolean is isFloorChain: false;
		local Boolean is recognizedTarget: false;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is targetName){
				name: targetName;
				recognizedTarget: true;
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 }, {
					name: segs:get(index: segs:length() - 1);
					segs:each(action: local Function(String is seg){
						if({ seg == 'sysinternal' }, {
							isFloorChain: true;
						});
					});
					recognizedTarget: true;
				});
			}
		], default: {});
		if({ !recognizedTarget || isFloorChain || name == '' || name == ':' }, {
			return;
		});
		if({ call:name == 'init' }, {
			return;
		});
		if({ :isUpperName(name: name) }, {
			if({ :auditEnums:has(key: name) }, {
				return;
			});
			local Boolean is isExempt: false;
			:exemptClasses:each(action: local Function(String is e){
				if({ e == name }, {
					isExempt: true;
				});
			});
			if({ isExempt }, {
				return;
			});
			if({ !:auditClasses:has(key: name) }, {
				return;
			});
			if({ :auditOwnerImportsAs(name: name) }, {
				return;
			});
			if({ :isHeldMember(clsName: name, memberName: call:name) }, {
				return;
			});
		}, {
			local Boolean is isAlias: false;
			:floorAliases:each(action: local Function(String is a){
				if({ a == name }, {
					isAlias: true;
				});
			});
			if({ !isAlias }, {
				return;
			});
		});
		local String is msg: 'Instance-model worklist: \'' . name . ':' . call:name . '\' calls a member through a class name (' . file . ').';
		:auditIssues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
	}

	## True when the class under audit, or any ancestor, instance-imports [name].
	Function of Boolean is auditOwnerImportsAs(String is name){
		return :auditImportsAsAnywhere(clsName: :auditOwner:name, targetName: name);
	}

	## Recursive import search over the audit's ancestor lattice.
	Function of Boolean is auditImportsAsAnywhere(String is clsName, String is targetName, Map of String to String is visited: Map:init()){
		if({ clsName == '' || clsName == 'Any' || visited:has(key: clsName) }, {
			return false;
		});
		visited:set(key: clsName, value: 'true');
		local ClassInfo is cls: :auditClassNodes:get(key: clsName, default: :auditOwner);
		if({ cls:name != clsName }, {
			return false;
		});
		if({ cls:instanceImportsAs(name: targetName) }, {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			if({ !viaParent && :auditImportsAsAnywhere(clsName: baseName, targetName: targetName, visited: visited) }, {
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
		:auditClassList:each(action: local Function(ClassInfo is cls){
			if({ !found && cls:name == clsName }, {
				cls:members:each(action: local Function(Member is m){
					if({ !found && m:name == memberName && m:hasModifier(kw: Keyword:HELD) }, {
						found: true;
					});
				});
				if({ !found }, {
					cls:baseClasses:each(action: local Function(String is baseName){
						if({ !found && :isHeldMember(clsName: baseName, memberName: memberName, visited: visited) }, {
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
