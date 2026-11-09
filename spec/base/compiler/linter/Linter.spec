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
		['base', 'iterator'],
		['base', 'iterator', as While()],
		['base', 'io', as Output()]
,
		['base', 'compiler', 'linter', LintIssue],
		['base', 'sys', as Conditional()]
	];

	## Audit name sets (INSTANCE.md Phase 0.5): every enum and class name in
	## the loaded program, nested classes included.
	local Map of String to String is auditEnums: Map:init();
	local Map of String to String is auditClasses: Map:init();

	## Worklist notices gathered by the audit pass.
	local Array of LintIssue is auditIssues: [];

	## The class whose members are currently being audited (with save and
	## restore around nested-class recursion).
	local ClassInfo is auditOwner: ClassInfo:init(name: '', baseClass: '', members: []);

	## Depth of While/Loop callback bodies the standards walk is inside
	## (INSTANCE.md E10: construction inside a loop body is a hoist hint).
	local Int is lintLoopDepth: 0;

	## Loaded class nodes by name, for the inherited-import walk.
	local Map of String to ClassInfo is auditClassNodes: Map:init();

	## Lowercase floor singletons routed by name (INSTANCE.md R1-R3 removes
	## them, so their call sites belong on the worklist).
	local Array of String is floorAliases: [];

	## Type-level exempt receivers (INSTANCE.md X3): primitives, base
	## conversion targets, containers.
	local Array of String is exemptClasses: [];

	replace Function is init(){
		self:auditEnums: Map:init();
		self:auditClasses: Map:init();
		self:auditClassNodes: Map:init();
		self:auditIssues: [];
		self:lintLoopDepth: 0;
		self:floorAliases: [];
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
			Conditional:if(check: { spaces > 0 }, then: {
				local String is msg: 'Space-based indentation detected (' . (spaces as String) . ' space(s)). Spec standard requires tabs.';
				issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
			});
			Conditional:if(check: { line:length() > 0 && (line:charAt(index: line:length() - 1, default: ' ') == ' ' || line:charAt(index: line:length() - 1, default: ' ') == "\t") }, then: {
				issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: 'Trailing whitespace detected.'));
			});

			# Mask strings and comments, then validate brace alignment.
			local String is masked: self:maskLine(line: line);
			local String is body: masked;
			local Boolean is trimming: true;
			While:condition(
				evaluate: local Function of Boolean(){ return trimming && body:length() > 0; },
				iteration: local Function(){
					local String is last: body:charAt(index: body:length() - 1, default: '');
					Conditional:if(check: { last == ' ' || last == "\t" }, then: {
						body: body:substring(start: 0, end: body:length() - 1);
					}, else: {
						trimming: false;
					});
				}
			);
			Conditional:if(check: { body:length() > 0 && body:charAt(index: 0, default: '') == '}' }, then: {
				local Int is expectedTabs: depth - 1;
				Conditional:if(check: { expectedTabs < 0 }, then: {
					expectedTabs: 0;
				});
				Conditional:if(check: { tabs != expectedTabs }, then: {
					local String is msg: 'Closing brace indented at ' . (tabs as String) . ' tab(s); nesting depth expects ' . (expectedTabs as String) . '.';
					issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
				});
			});
			local Int is ci: 0;
			While:condition(
				evaluate: local Function of Boolean(){ return ci < masked:length(); },
				iteration: local Function(){
					local String is ch: masked:charAt(index: ci, default: '');
					Conditional:if(check: { ch == '{' }, then: {
						depth: depth + 1;
					}, else: {
						Conditional:if(check: { ch == '}' }, then: {
							depth: depth - 1;
						});
					});
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
				Conditional:if(check: { quote != '' }, then: {
					Conditional:if(check: { ch == "\\" }, then: {
						out: out . '  ';
						i: i + 1;
					}, else: {
						Conditional:if(check: { ch == quote }, then: {
							quote: '';
							out: out . ' ';
						}, else: {
							out: out . ' ';
						});
					});
				}, else: {
					Conditional:if(check: { ch == '"' || ch == '\'' }, then: {
						quote: ch;
						out: out . ' ';
					}, else: {
						Conditional:if(check: { ch == '#' }, then: {
							i: line:length();
						}, else: {
							out: out . ch;
						});
					});
				});
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

				# INSTANCE.md E10: a constructor call inside a While/Loop
				# callback body allocates per iteration — hoisting hint.
				Conditional:if(check: { method == 'init' && self:lintLoopDepth > 0 && self:isClassSpell(target: expr:methodTarget) }, then: {
					issues:add(item: LintIssue:init(line: 0, isWarning: true, message: 'Construction inside a loop body: hoist the instance out of the loop (INSTANCE.md E10).'));
				});

				when (method) {
					is 'getString': {
						local Boolean is hasDefault: false;
						args:each(action: local Function(NamedArg is arg){
							Conditional:if(check: { arg:name == 'default' }, then: {
								hasDefault: true;
							});
						});
						Conditional:if(check: { hasDefault }, then: {
							issues:add(item: LintIssue:init(line: 0, isWarning: false, message: 'Method call \'getString\' provides optional parameter \'default\'.'));
						});
					}
					is 'random': {
						local String is msg: 'Method call \'math:random\' provides optional min/max range parameters.';
						Conditional:if(check: { args:length() == 0 }, then: {
							msg: 'Method call \'math:random\' omits optional min/max parameters (using default [0.0, 1.0)).';
						});
						issues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
					}
					else: {}
				}

				self:lintExpression(expr: expr:methodTarget, issues: issues);
				local Boolean is isLoopDriver: self:isLoopSpell(target: expr:methodTarget);
				args:each(action: local Function(NamedArg is arg){
					Conditional:if(check: { isLoopDriver && arg:value:kind == ExpressionKind:ANON_FN }, then: {
						local Int is savedDepth: self:lintLoopDepth;
						self:lintLoopDepth: self:lintLoopDepth + 1;
						self:lintExpression(expr: arg:value, issues: issues);
						self:lintLoopDepth: savedDepth;
					}, else: {
						self:lintExpression(expr: arg:value, issues: issues);
					});
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
			is ExpressionKind:ANON_FN: {
				expr:anonBody:each(action: local Function(Statement is st){
					self:lintStatement(stmt: st, issues: issues);
				});
			}
			else: {}
		}
	}

	## True when [target] spells a loop driver — a While/Loop class-name
	## receiver. Purely syntactic: the standards walk has no class table.
	##
	## @param target: The call's receiver expression.
	## @return: true when the receiver names While or Loop.
	Function of Boolean is isLoopSpell(Expression is target){
		local String is name: '';
		Conditional:if(check: { target:kind == ExpressionKind:IDENT }, then: {
			name: target:stringValue;
		}, else: {
			Conditional:if(check: { target:kind == ExpressionKind:PATH }, then: {
				local Array of String is segs: target:pathSegments;
				Conditional:if(check: { segs:length() > 0 }, then: {
					name: segs:get(index: segs:length() - 1);
				});
			});
		});
		return name == 'While' || name == 'Loops' || name == 'Loop';
	}

	## True when [target] spells an UpperCamel (class-like) receiver —
	## the shape of a constructor call `X:init(...)`.
	##
	## @param target: The call's receiver expression.
	## @return: true when the receiver is class-spelled.
	Function of Boolean is isClassSpell(Expression is target){
		local String is name: '';
		Conditional:if(check: { target:kind == ExpressionKind:IDENT }, then: {
			name: target:stringValue;
		}, else: {
			Conditional:if(check: { target:kind == ExpressionKind:PATH }, then: {
				local Array of String is segs: target:pathSegments;
				Conditional:if(check: { segs:length() > 0 }, then: {
					name: segs:get(index: segs:length() - 1);
				});
			});
		});
		return self:isUpperName(name: name);
	}

	## Inspects a statement node.
	##
	## @param stmt: [Statement] AST node.
	## @param issues: Destination issues array.
	Function is lintStatement(Statement is stmt, Array of LintIssue is issues){
		local StatementKind is kind: stmt:kind;

		when (kind) {
			is StatementKind:VAR_DECL: {
				Conditional:if(check: { stmt:hasInit }, then: {
					self:lintExpression(expr: stmt:initExpr, issues: issues);
				});
			}
			is StatementKind:ASSIGN: {
				self:lintExpression(expr: stmt:assignTarget, issues: issues);
				self:lintExpression(expr: stmt:assignValue, issues: issues);
			}
			is StatementKind:RETURN: {
				Conditional:if(check: { stmt:hasReturnExpr }, then: {
					self:lintExpression(expr: stmt:returnExpr, issues: issues);
				});
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
			Conditional:if(check: { issue:isWarning }, then: {
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
			Conditional:if(check: { !issue:isWarning }, then: {
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
		Conditional:if(check: { warnings == 0 }, then: {
			Output:line('All standard checks passed successfully.');
		});
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
		Conditional:if(check: { c:baseClass == 'Enum' }, then: {
			self:auditEnums:set(key: c:name, value: 'true');
		}, else: {
			self:auditClasses:set(key: c:name, value: 'true');
		});
		self:auditClassNodes:set(key: c:name, value: c);
		c:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:kind == MemberKind:CLASS }, then: {
				self:registerAuditName(c: m:nestedClass);
			});
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

	## Audits every method body of a class definition, nested classes
	## included. The owning class is remembered (with save and restore
	## around nesting) so migrated as-import receivers can leave the
	## worklist.
	##
	## @param classDef: [ClassInfo] definition.
	Function is auditClass(ClassInfo is classDef){
		local ClassInfo is savedOwner: self:auditOwner;
		self:auditOwner: classDef;
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
		self:auditOwner: savedOwner;
	}

	## Walks one statement, auditing every expression it contains (when
	## arms and merge forwards included — the metric must not undercount).
	##
	## @param stmt: [Statement] AST node.
	## @param file: Source file the statement lives in.
	Function is auditStatement(Statement is stmt, String is file){
		when (stmt:kind) {
			is StatementKind:VAR_DECL: {
				Conditional:if(check: { stmt:hasInit }, then: {
					self:auditExpression(expr: stmt:initExpr, file: file);
				});
			}
			is StatementKind:ASSIGN: {
				self:auditExpression(expr: stmt:assignTarget, file: file);
				self:auditExpression(expr: stmt:assignValue, file: file);
			}
			is StatementKind:RETURN: {
				Conditional:if(check: { stmt:hasReturnExpr }, then: {
					self:auditExpression(expr: stmt:returnExpr, file: file);
				});
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
		Conditional:if(check: { arm:hasValueExpr }, then: {
			self:auditExpression(expr: arm:valueExpr, file: file);
		});
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
		Conditional:if(check: { callExpr:methodTarget:kind == ExpressionKind:IDENT }, then: {
			name: callExpr:methodTarget:stringValue;
		}, else: {
			Conditional:if(check: { callExpr:methodTarget:kind == ExpressionKind:PATH }, then: {
				local Array of String is segs: callExpr:methodTarget:pathSegments;
				Conditional:if(check: { segs:length() == 0 }, then: {
					return;
				});
				name: segs:get(index: segs:length() - 1);
				segs:each(action: local Function(String is seg){
					Conditional:if(check: { seg == 'sysinternal' }, then: {
						isFloorChain: true;
					});
				});
			}, else: {
				return;
			});
		});
		Conditional:if(check: { isFloorChain || name == '' || name == 'self' }, then: {
			return;
		});
		Conditional:if(check: { callExpr:methodName == 'init' }, then: {
			return;
		});
		Conditional:if(check: { self:isUpperName(name: name) }, then: {
			Conditional:if(check: { self:auditEnums:has(key: name) }, then: {
				return;
			});
			local Boolean is isExempt: false;
			self:exemptClasses:each(action: local Function(String is e){
				Conditional:if(check: { e == name }, then: {
					isExempt: true;
				});
			});
			Conditional:if(check: { isExempt }, then: {
				return;
			});
			Conditional:if(check: { !self:auditClasses:has(key: name) }, then: {
				return;
			});
			Conditional:if(check: { self:auditOwnerImportsAs(name: name) }, then: {
				# Migrated: the owning class (or an ancestor) instance-imports
				# this class (INSTANCE.md §2.1), so the prefix call is the
				# new model.
				return;
			});
		}, else: {
			local Boolean is isAlias: false;
			self:floorAliases:each(action: local Function(String is a){
				Conditional:if(check: { a == name }, then: {
					isAlias: true;
				});
			});
			Conditional:if(check: { !isAlias }, then: {
				return;
			});
		});
		local String is msg: 'Instance-model worklist: \'' . name . ':' . callExpr:methodName . '\' calls a member through a class name (' . file . ').';
		self:auditIssues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
	}

	## True when the class under audit, or any ancestor, instance-imports
	## [name] — as-imports are inherited like the fields they synthesize.
	##
	## @param name: Receiver class name.
	## @return: true when imported somewhere up the chain.
	## True when the class under audit, or any ancestor (all parents,
	## transitively), instance-imports [name] — as-imports are inherited
	## like the fields they synthesize.
	##
	## @param name: Receiver class name.
	## @return: true when imported somewhere up the chain.
	Function of Boolean is auditOwnerImportsAs(String is name){
		return self:auditImportsAsAnywhere(clsName: self:auditOwner:name, targetName: name, hops: 0);
	}

	## Recursive import search over the audit's ancestor lattice.
	##
	## @param clsName: Class being visited.
	## @param targetName: The imported class name sought.
	## @param hops: Recursion budget guard.
	## @return: true when found on this class or an ancestor.
	Function of Boolean is auditImportsAsAnywhere(String is clsName, String is targetName, Int is hops){
		Conditional:if(check: { clsName == '' || clsName == 'Any' || hops >= 64 }, then: {
			return false;
		});
		local ClassInfo is cls: self:auditClassNodes:get(key: clsName, default: self:auditOwner);
		Conditional:if(check: { cls:name != clsName }, then: {
			return false;
		});
		Conditional:if(check: { cls:instanceImportsAs(name: targetName) }, then: {
			return true;
		});
		local Boolean is viaParent: false;
		cls:baseClasses:each(action: local Function(String is baseName){
			Conditional:if(check: { !viaParent && self:auditImportsAsAnywhere(clsName: baseName, targetName: targetName, hops: hops + 1) }, then: {
				viaParent: true;
			});
		});
		return viaParent;
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
		Conditional:if(check: { name:length() == 0 }, then: {
			return false;
		});
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
		Output:line('Instance-model audit of \'' . filePath . '\':');
		issues:each(action: local Function(LintIssue is issue){
			Output:line(issue:toString());
		});
		Output:line('Instance-model worklist: ' . (issues:length() as String) . ' call site(s) must migrate (INSTANCE.md Phase 0.5).');
	}
}
