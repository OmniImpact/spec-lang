#! Package base:compiler:linter
#! Pure-Spec code linter enforcing tab-based indentation, formatting,
#! and AST idioms, plus the INSTANCE.md Phase 0.5 worklist audit.

## Pure-Spec code linter enforcing tab-based indentation, formatting,
## and AST idioms, plus the INSTANCE.md Phase 0.5 worklist audit.
Class is Linter{
	namespace: ['base', 'compiler', 'linter'];

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
		['base', 'compiler', 'ast', WhenArm],
		['base', 'io', Output],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator']
	];

	## Audit name sets (INSTANCE.md Phase 0.5): every enum and class name in
	## the loaded program, nested classes included.
	local Map of String to String is auditEnums: Map:init();
	local Map of String to String is auditClasses: Map:init();

	## Worklist notices gathered by the audit pass.
	local Array of LintIssue is auditIssues: [];

	## Lowercase floor singletons routed by name (INSTANCE.md R1-R3 removes
	## them, so their call sites belong on the worklist).
	local Array of String is floorAliases: [];

	## Type-level exempt receivers (INSTANCE.md X3): primitives, base
	## conversion targets, containers.
	local Array of String is exemptClasses: [];

	replace Function is init(){
		self:auditEnums: Map:init();
		self:auditClasses: Map:init();
		self:auditIssues: [];
		self:floorAliases: ['output', 'error', 'math'];
		self:exemptClasses: ['Int', 'Byte', 'Float', 'Boolean', 'String', 'Any', 'Hex', 'Bin', 'Oct', 'Array', 'Map', 'List'];
	}

	## Inspects indentation whitespace line-by-line.
	##
	## Checks: leading spaces after tabs, trailing whitespace, and closing-brace
	## alignment against the current nesting depth (string literals and
	## comments are masked so brace characters inside them are ignored).
	##
	## @param source: Raw source code string.
	## @param issues: Destination issues array.
	Function is lintIndentation(String is source, Array of LintIssue is issues){
		local Int is lineNum: 0;
		local Int is depth: 0;
		# Own the lines array: a fresh call result rides the claim pool,
    # and this loop's bodies claim repeatedly — 32 claims would evict it
    # mid-iteration. A var-decl init is a consumption position.
    local Array of String is srcLines: source:lines();
    srcLines:each(action: local Function(String is line){
			lineNum: lineNum + 1;
			local Int is tabs: line:countLeading(search: "\t");
			local String is rest: line:substring(start: tabs, end: line:length());
			local Int is spaces: rest:countLeading(search: ' ');
			if (spaces > 0) {
				local String is msg: 'Space-based indentation detected (' . (spaces as String) . ' space(s)). Spec standard requires tabs.';
				issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
			}
			if (line:length() > 0 && (line:charAt(index: line:length() - 1, default: ' ') == ' ' || line:charAt(index: line:length() - 1, default: ' ') == "\t")) {
				issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: 'Trailing whitespace detected.'));
			}

			# Mask strings and comments, then validate brace alignment.
			local String is masked: self:maskLine(line: line);
			local String is body: masked;
			local Boolean is trimming: true;
			While:condition(
				evaluate: local Function of Boolean(){ return trimming && body:length() > 0; },
				iteration: local Function(){
					local String is last: body:charAt(index: body:length() - 1, default: '');
					if (last == ' ' || last == "\t") {
						body: body:substring(start: 0, end: body:length() - 1);
					} else {
						trimming: false;
					}
				}
			);
			if (body:length() > 0 && body:charAt(index: 0, default: '') == '}') {
				local Int is expectedTabs: depth - 1;
				if (expectedTabs < 0) {
					expectedTabs: 0;
				}
				if (tabs != expectedTabs) {
					local String is msg: 'Closing brace indented at ' . (tabs as String) . ' tab(s); nesting depth expects ' . (expectedTabs as String) . '.';
					issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
				}
			}
			local Int is ci: 0;
			While:condition(
				evaluate: local Function of Boolean(){ return ci < masked:length(); },
				iteration: local Function(){
					local String is ch: masked:charAt(index: ci, default: '');
					if (ch == '{') {
						depth: depth + 1;
					} else if (ch == '}') {
						depth: depth - 1;
					}
					ci: ci + 1;
				}
			);
		});
	}

	## Returns a line with string contents and comments replaced by spaces so
	## that brace counting only sees structural characters.
	##
	## @param line: Raw source line.
	## @return: Masked line of identical length.
	Function of String is maskLine(String is line){
		local String is out: '';
		local String is quote: '';
		local Int is i: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return i < line:length(); },
			iteration: local Function(){
				local String is ch: line:charAt(index: i, default: '');
				if (quote != '') {
					if (ch == "\\") {
						out: out . '  ';
						i: i + 1;
					} else if (ch == quote) {
						quote: '';
						out: out . ' ';
					} else {
						out: out . ' ';
					}
				} else if (ch == '"' || ch == '\'') {
					quote: ch;
					out: out . ' ';
				} else if (ch == '#') {
					i: line:length();
				} else {
					out: out . ch;
				}
				i: i + 1;
			}
		);
		return out;
	}

	## Inspects an expression node for optional arguments and idioms.
	##
	## @param expr: [Expression] AST node.
	## @param issues: Destination issues array.
	Function is lintExpression(Expression is expr, Array of LintIssue is issues){
		local ExpressionKind is kind: expr:kind;

		when (kind) {
			is ExpressionKind:CALL: {
				local String is method: expr:methodName;
				local Array of NamedArg is args: expr:methodArgs;

				when (method) {
					is 'getString': {
						local Boolean is hasDefault: false;
						args:each(action: local Function(NamedArg is arg){
							if (arg:name == 'default') {
								hasDefault: true;
							}
						});
						if (hasDefault) {
							issues:add(item: LintIssue:init(line: 0, isWarning: false, message: 'Method call \'getString\' provides optional parameter \'default\'.'));
						}
					}
					is 'random': {
						local String is msg: 'Method call \'math:random\' provides optional min/max range parameters.';
						if (args:length() == 0) {
							msg: 'Method call \'math:random\' omits optional min/max parameters (using default [0.0, 1.0)).';
						}
						issues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
					}
					else: {}
				}

				self:lintExpression(expr: expr:methodTarget, issues: issues);
				args:each(action: local Function(NamedArg is arg){
					self:lintExpression(expr: arg:value, issues: issues);
				});
			}
			is ExpressionKind:BINARY: {
				self:lintExpression(expr: expr:leftExpr, issues: issues);
				self:lintExpression(expr: expr:rightExpr, issues: issues);
			}
			is ExpressionKind:UNARY: {
				self:lintExpression(expr: expr:unaryExpr, issues: issues);
			}
			is ExpressionKind:ARRAY: {
				expr:arrayItems:each(action: local Function(Expression is item){
					self:lintExpression(expr: item, issues: issues);
				});
			}
			else: {}
		}
	}

	## Inspects a statement node.
	##
	## @param stmt: [Statement] AST node.
	## @param issues: Destination issues array.
	Function is lintStatement(Statement is stmt, Array of LintIssue is issues){
		local StatementKind is kind: stmt:kind;

		when (kind) {
			is StatementKind:VAR_DECL: {
				if (stmt:hasInit) {
					self:lintExpression(expr: stmt:initExpr, issues: issues);
				}
			}
			is StatementKind:ASSIGN: {
				self:lintExpression(expr: stmt:assignTarget, issues: issues);
				self:lintExpression(expr: stmt:assignValue, issues: issues);
			}
			is StatementKind:IF: {
				self:lintExpression(expr: stmt:ifCondition, issues: issues);
				stmt:thenBranch:each(action: local Function(Statement is s){
					self:lintStatement(stmt: s, issues: issues);
				});
				if (stmt:hasElse) {
					stmt:elseBranch:each(action: local Function(Statement is s){
						self:lintStatement(stmt: s, issues: issues);
					});
				}
			}
			is StatementKind:RETURN: {
				if (stmt:hasReturnExpr) {
					self:lintExpression(expr: stmt:returnExpr, issues: issues);
				}
			}
			is StatementKind:CLASS: {
				self:lintClass(classDef: stmt:nestedClass, issues: issues);
			}
			is StatementKind:EXPR: {
				self:lintExpression(expr: stmt:exprStmt, issues: issues);
			}
			else: {}
		}
	}

	## Inspects all members of a class definition.
	##
	## @param classDef: [ClassInfo] definition.
	## @param issues: Destination issues array.
	Function is lintClass(ClassInfo is classDef, Array of LintIssue is issues){
		classDef:members:each(action: local Function(Member is m){
			when (m:kind) {
				is MemberKind:METHOD: {
					m:body:each(action: local Function(Statement is s){
						self:lintStatement(stmt: s, issues: issues);
					});
				}
				is MemberKind:CLASS: {
					self:lintClass(classDef: m:nestedClass, issues: issues);
				}
				else: {}
			}
		});
	}

	## Analyzes source code text and optional AST, returning all detected lint issues.
	##
	## @param source: Raw source code string.
	## @param program: Parsed [ProgramNode] AST.
	## @return: [Array] of [LintIssue] items.
	Function of Array of LintIssue is lint(String is source, ProgramNode is program){
		local Array of LintIssue is issues: [];

		# 1. Indentation Check
		self:lintIndentation(source: source, issues: issues);

		# 2. AST Checks
		program:classes:each(action: local Function(ClassInfo is c){
			self:lintClass(classDef: c, issues: issues);
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
			if (issue:isWarning) {
				res: res + 1;
			}
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
			if (!issue:isWarning) {
				res: res + 1;
			}
		});
		return res;
	}

	## Prints formatted lint diagnostics to standard output.
	##
	## @param filePath: Source file path.
	## @param issues: Array of detected [LintIssue] items.
	Function is report(String is filePath, Array of LintIssue is issues){
		output:line('Checking \'' . filePath . '\' for Spec code standards...');
		issues:each(action: local Function(LintIssue is issue){
			output:line(issue:toString());
		});

		local Int is warnings: self:countWarnings(issues: issues);
		local Int is notices: self:countNotices(issues: issues);
		output:line("\nLint summary for " . filePath . ': ' . (warnings as String) . ' warning(s), ' . (notices as String) . ' notice(s).');
		if (warnings == 0) {
			output:line('All standard checks passed successfully.');
		}
	}

	## INSTANCE.md Phase 0.5 worklist audit: reports every call whose
	## receiver names a class (or floor alias) with a non-init method,
	## excluding the exempt strata (§4). Purely informational — the
	## burn-down metric for the instance-based call model. Requires the
	## LOADED program: enum and class knowledge comes from the loader,
	## not from spelling.
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

	## Registers one class or enum name, nested classes included (a nested
	## class is callable by its bare name). Recurses through members, never
	## across an array literal — the claim pool evicts pool-held arrays
	## when a nested self-call claims (see Loader.spec's note).
	##
	## @param c: Candidate [ClassInfo] definition.
	Function is registerAuditName(ClassInfo is c){
		if (c:baseClass == 'Enum') {
			self:auditEnums:set(key: c:name, value: 'true');
		} else {
			self:auditClasses:set(key: c:name, value: 'true');
		}
		c:members:each(action: local Function(Member is m){
			if (m:kind == MemberKind:CLASS) {
				self:registerAuditName(c: m:nestedClass);
			}
		});
	}

	## Collects class and enum names into the audit sets.
	##
	## @param classes: Candidate [ClassInfo] definitions.
	Function is buildAuditNameSets(Array of ClassInfo is classes){
		classes:each(action: local Function(ClassInfo is c){
			self:registerAuditName(c: c);
		});
	}

	## Audits every method body of a class definition, nested classes included.
	##
	## @param classDef: [ClassInfo] definition.
	Function is auditClass(ClassInfo is classDef){
		classDef:members:each(action: local Function(Member is m){
			when (m:kind) {
				is MemberKind:METHOD: {
					m:body:each(action: local Function(Statement is s){
						self:auditStatement(stmt: s, file: m:sourceFile);
					});
				}
				is MemberKind:CLASS: {
					self:auditClass(classDef: m:nestedClass);
				}
				else: {}
			}
		});
	}

	## Walks one statement, auditing every expression it contains (when
	## arms and merge forwards included — the metric must not undercount).
	##
	## @param stmt: [Statement] AST node.
	## @param file: Source file the statement lives in.
	Function is auditStatement(Statement is stmt, String is file){
		when (stmt:kind) {
			is StatementKind:VAR_DECL: {
				if (stmt:hasInit) {
					self:auditExpression(expr: stmt:initExpr, file: file);
				}
			}
			is StatementKind:ASSIGN: {
				self:auditExpression(expr: stmt:assignTarget, file: file);
				self:auditExpression(expr: stmt:assignValue, file: file);
			}
			is StatementKind:IF: {
				self:auditExpression(expr: stmt:ifCondition, file: file);
				stmt:thenBranch:each(action: local Function(Statement is s){
					self:auditStatement(stmt: s, file: file);
				});
				if (stmt:hasElse) {
					stmt:elseBranch:each(action: local Function(Statement is s){
						self:auditStatement(stmt: s, file: file);
					});
				}
			}
			is StatementKind:RETURN: {
				if (stmt:hasReturnExpr) {
					self:auditExpression(expr: stmt:returnExpr, file: file);
				}
			}
			is StatementKind:CLASS: {
				self:auditClass(classDef: stmt:nestedClass);
			}
			is StatementKind:EXPR: {
				self:auditExpression(expr: stmt:exprStmt, file: file);
			}
			is StatementKind:WHEN: {
				self:auditExpression(expr: stmt:whenSubject, file: file);
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					self:auditWhenArm(arm: arm, file: file);
				});
			}
			is StatementKind:FORWARD: {
				stmt:forwardArgs:each(action: local Function(NamedArg is arg){
					self:auditExpression(expr: arg:value, file: file);
				});
			}
			else: {}
		}
	}

	## Audits one when arm: guard conditions, statement body, or value
	## expression.
	##
	## @param arm: [WhenArm] AST node.
	## @param file: Source file the arm lives in.
	Function is auditWhenArm(WhenArm is arm, String is file){
		arm:conditions:each(action: local Function(Expression is cond){
			self:auditExpression(expr: cond, file: file);
		});
		if (arm:hasValueExpr) {
			self:auditExpression(expr: arm:valueExpr, file: file);
		}
		arm:body:each(action: local Function(Statement is s){
			self:auditStatement(stmt: s, file: file);
		});
	}

	## Walks one expression, auditing calls it contains — through casts,
	## if/else and when expressions, map literals, index and field access,
	## and anonymous function bodies.
	##
	## @param expr: [Expression] AST node.
	## @param file: Source file the expression lives in.
	Function is auditExpression(Expression is expr, String is file){
		when (expr:kind) {
			is ExpressionKind:CALL: {
				self:auditReceiver(callExpr: expr, file: file);
				self:auditExpression(expr: expr:methodTarget, file: file);
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					self:auditExpression(expr: arg:value, file: file);
				});
			}
			is ExpressionKind:BINARY: {
				self:auditExpression(expr: expr:leftExpr, file: file);
				self:auditExpression(expr: expr:rightExpr, file: file);
			}
			is ExpressionKind:UNARY: {
				self:auditExpression(expr: expr:unaryExpr, file: file);
			}
			is ExpressionKind:ARRAY: {
				expr:arrayItems:each(action: local Function(Expression is item){
					self:auditExpression(expr: item, file: file);
				});
			}
			is ExpressionKind:MAP: {
				expr:mapKeys:each(action: local Function(Expression is k){
					self:auditExpression(expr: k, file: file);
				});
				expr:mapValues:each(action: local Function(Expression is v){
					self:auditExpression(expr: v, file: file);
				});
			}
			is ExpressionKind:CAST: {
				self:auditExpression(expr: expr:leftExpr, file: file);
				expr:castArgs:each(action: local Function(Expression is a){
					self:auditExpression(expr: a, file: file);
				});
			}
			is ExpressionKind:FIELD_ACCESS: {
				self:auditExpression(expr: expr:leftExpr, file: file);
			}
			is ExpressionKind:INDEX: {
				self:auditExpression(expr: expr:leftExpr, file: file);
				expr:castArgs:each(action: local Function(Expression is a){
					self:auditExpression(expr: a, file: file);
				});
			}
			is ExpressionKind:IF_ELSE: {
				self:auditExpression(expr: expr:condExpr, file: file);
				self:auditExpression(expr: expr:thenExpr, file: file);
				self:auditExpression(expr: expr:elseExpr, file: file);
			}
			is ExpressionKind:WHEN: {
				self:auditExpression(expr: expr:whenSubject, file: file);
				expr:whenArms:each(action: local Function(WhenArm is arm){
					self:auditWhenArm(arm: arm, file: file);
				});
			}
			is ExpressionKind:ANON_FN: {
				expr:anonBody:each(action: local Function(Statement is s){
					self:auditStatement(stmt: s, file: file);
				});
			}
			else: {}
		}
	}

	## Classifies one call's receiver (INSTANCE.md §2.2, §4): flags
	## class-named and floor-alias receivers invoking non-init members;
	## skips self, variables and fields, enums, the exempt type-level
	## strata, and sysinternal floor chains. Unknown uppercase names stay
	## silent — the metric must not guess.
	##
	## @param callExpr: The CALL expression.
	## @param file: Source file the call lives in.
	Function is auditReceiver(Expression is callExpr, String is file){
		local String is name: '';
		local Boolean is isFloorChain: false;
		if (callExpr:methodTarget:kind == ExpressionKind:IDENT) {
			name: callExpr:methodTarget:stringValue;
		} else if (callExpr:methodTarget:kind == ExpressionKind:PATH) {
			local Array of String is segs: callExpr:methodTarget:pathSegments;
			if (segs:length() == 0) {
				return;
			}
			name: segs:get(index: segs:length() - 1);
			segs:each(action: local Function(String is seg){
				if (seg == 'sysinternal') {
					isFloorChain: true;
				}
			});
		} else {
			return;
		}
		if (isFloorChain || name == '' || name == 'self') {
			return;
		}
		if (callExpr:methodName == 'init') {
			return;
		}
		if (self:isUpperName(name: name)) {
			if (self:auditEnums:has(key: name)) {
				return;
			}
			local Boolean is isExempt: false;
			self:exemptClasses:each(action: local Function(String is e){
				if (e == name) {
					isExempt: true;
				}
			});
			if (isExempt) {
				return;
			}
			if (!self:auditClasses:has(key: name)) {
				return;
			}
		} else {
			local Boolean is isAlias: false;
			self:floorAliases:each(action: local Function(String is a){
				if (a == name) {
					isAlias: true;
				}
			});
			if (!isAlias) {
				return;
			}
		}
		local String is msg: 'Instance-model worklist: \'' . name . ':' . callExpr:methodName . '\' calls a member through a class name (' . file . ').';
		self:auditIssues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
	}

	## True when [name] starts with an uppercase letter (the type naming
	## convention); variables and fields are lowerCamel. The 26-way match
	## is deliberate: relational operators on Strings compile to raw
	## pointer comparison (see INSTANCE.md D5), so `first >= 'A'` is not
	## a legal test.
	##
	## @param name: Identifier to classify.
	## @return: true when the name is UpperCamel.
	Function of Boolean is isUpperName(String is name){
		if (name:length() == 0) {
			return false;
		}
		local String is first: name:charAt(index: 0, default: '');
		when (first) {
			is 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M':
				{ return true; }
			is 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z':
				{ return true; }
			else: { return false; }
		}
	}

	## Prints the audit worklist: per-site lines, then the total count.
	##
	## @param filePath: Audited root file path.
	## @param issues: Worklist notices.
	Function is auditReport(String is filePath, Array of LintIssue is issues){
		output:line('Instance-model audit of \'' . filePath . '\':');
		issues:each(action: local Function(LintIssue is issue){
			output:line(issue:toString());
		});
		output:line('Instance-model worklist: ' . (issues:length() as String) . ' call site(s) must migrate (INSTANCE.md Phase 0.5).');
	}
}
