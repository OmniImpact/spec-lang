#! Package speclint
#! Pure-Spec code linter enforcing tab-based indentation, formatting,
#! and AST idioms, plus the Phase 0.5 worklist audit.

## Pure-Spec code linter enforcing tab-based indentation, formatting,
## and AST idioms, plus the Phase 0.5 worklist audit.
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
		['base', 'sys', Output],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'sys', as Loops()],
		['base', 'sys', as Output()],
		['speclint', LintIssue],
		['base', 'sys', as Conditional()]
	];

	## Audit name sets (Phase 0.5): every enum and class name in
	## the loaded program, nested classes included.
	local Map of String to String is auditEnums: Map:init();
	local Map of String to String is auditClasses: Map:init();

	## Worklist notices gathered by the audit pass.
	local Array of LintIssue is auditIssues: [];

	## The class whose members are currently being audited (with save and
	## restore around nested-class recursion).
	local ClassInfo is auditOwner: ClassInfo:init(name: '', baseClass: '', members: []);

	## Depth of While/Loop callback bodies the standards walk is inside
	## (E10: construction inside a loop body is a hoist hint).
	local Int is lintLoopDepth: 0;

	## Quote state carried across lines by [maskLineStateful]: '' outside
	## any string, or the active quote — `'` a raw string, `"` an escaped
	## string, `'''` a raw multi-line string. Lines that START inside a
	## string are string DATA (the C runtime held in RuntimePrelude.spec
	## is the mass case), not Spec style, and are skipped.
	local String is lintQuote: '';

	## The tab indent of the line that opened each open brace, LIFO — the
	## closing-brace rule's expectation: a block's closer sits at the
	## indent of the line that opened it. A depth delta cannot express
	## this (an if-line opens two braces but one indent level), and a
	## `}, {` continuation closes and reopens at the statement's own
	## indent, which the stack records naturally.
	local Array of Int is openTabs: [];

	## Loaded class nodes by name, for the inherited-import walk.
	local Map of String to ClassInfo is auditClassNodes: Map:init();

	## Lowercase floor singletons routed by name (R1-R3 removes
	## them, so their call sites belong on the worklist).
	local Array of String is floorAliases: [];

	## Type-level exempt receivers (X3): primitives, base
	## conversion targets, containers.
	local Array of String is exemptClasses: [];

	replace Function is init(){
		self:auditEnums: Map:init();
		self:auditClasses: Map:init();
		self:auditClassNodes: Map:init();
		self:auditIssues: [];
		self:lintLoopDepth: 0;
		self:lintQuote: '';
		self:openTabs: [];
		self:floorAliases: [];
		self:exemptClasses: ['Int', 'Byte', 'Float', 'Boolean', 'String', 'Any', 'Hex', 'Bin', 'Oct', 'Array', 'Map', 'List'];
	}

	## Inspects indentation whitespace line-by-line.
	##
	## Checks: leading spaces after tabs, trailing whitespace, and closing-brace
	## alignment (string literals — single-line and multi-line — and comments
	## are masked so brace characters inside them are ignored; lines that
	## START inside a multi-line string are string data and skipped whole).
	## A closing brace — column-0 or tab-indented — must sit at the tab
	## indent of the line that opened its block; `}, {` continuations
	## close and reopen at that same indent, which the [openTabs] stack
	## records naturally.
	##
	## @param source: Raw source code string.
	## @param issues: Destination issues array.
	Function is lintIndentation(String is source, Array of LintIssue is issues){
		local Int is lineNum: 0;
		local Int is stmtTabs: 0;
		local Boolean is prevOpen: false;
		self:lintQuote: '';
		self:openTabs: [];
		# Own the lines array: a fresh call result rides the claim pool,
		# and this loop's bodies claim repeatedly — 32 claims would evict it
		# mid-iteration. A var-decl init is a consumption position.
		local Array of String is srcLines: source:lines();
		srcLines:each(action: local Function(String is line){
			lineNum: lineNum + 1;
			# A line that STARTS inside a multi-line string is string data
			# — advance the quote scanner, check nothing.
			if({ self:lintQuote != '' }, {
				self:maskLineStateful(line: line);
				prevOpen: false;
				return;
			});
			local String is masked: self:maskLineStateful(line: line);
			local Int is tabs: line:countLeading(search: "\t");
			local String is rest: line:substring(start: tabs, end: line:length());
			local Int is spaces: rest:countLeading(search: ' ');
			if({ spaces > 0 }, {
				local String is msg: 'Space-based indentation detected (' . (spaces as String) . ' space(s)). Spec standard requires tabs.';
				issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
			});
			# Trailing whitespace is only judgeable when the line closes
			# every string it opens — a line ending inside a string ends
			# in string content.
			if({ self:lintQuote == '' }, {
				if({ line:length() > 0 && (line:charAt(index: line:length() - 1, default: ' ') == ' ' || line:charAt(index: line:length() - 1, default: ' ') == "\t") }, {
					issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: 'Trailing whitespace detected.'));
				});
			});

			# Leading-trim the masked line once: its first non-whitespace
			# character classifies the line and drives the brace stack.
			local String is trimmed: masked;
			local Boolean is trimming: true;
			while({ trimming && trimmed:length() > 0 }, {
				local String is first: trimmed:charAt(index: 0, default: '');
				if({ first == ' ' || first == "\t" }, {
					trimmed: trimmed:substring(start: 1, end: trimmed:length());
				}, {
					trimming: false;
				});
			});
			local String is firstCh: trimmed:charAt(index: 0, default: '');
			# The indent a brace opened on this line belongs to: a line
			# continuing the previous statement (leading operator, or a
			# predecessor that ended mid-expression — a trailing operator
			# or chain dot; NOT a comma, which closes every match-table
			# entry) carries the statement's own indent, so a `then: {`
			# opened on a continued condition records the if-line's tabs.
			# A `}, {` seam records its own line's tabs; closer lines
			# update nothing.
			local Int is pushTabs: tabs;
			if({ trimmed:length() > 0 }, {
				if({ firstCh == '&' || firstCh == '|' || firstCh == '.' || firstCh == '?' || prevOpen }, {
					pushTabs: stmtTabs;
				}, {
					if({ firstCh != '}' }, {
						stmtTabs: tabs;
					});
				});
			});
			# Closing-brace alignment: any line whose first non-whitespace
			# masked character is '}' — column-0 and tab-indented closers
			# alike — must sit at the opener's recorded indent.
			if({ trimmed:length() > 0 && firstCh == '}' }, {
				local Int is openCount: self:openTabs:length();
				if({ openCount > 0 }, {
					local Int is expectedTabs: (self:openTabs:get(index: openCount - 1)) as Int;
					if({ tabs != expectedTabs }, {
						local String is msg: 'Closing brace indented at ' . (tabs as String) . ' tab(s); the block opened at ' . (expectedTabs as String) . ' tab(s).';
						issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
					});
				});
			});
			local Int is ci: 0;
			while({ ci < masked:length() }, {
				local String is ch: masked:charAt(index: ci, default: '');
				match(on: ch, when: [
					'{': { self:openTabs:add(item: pushTabs); },
					'}': {
						# A stray closer with nothing open is itself a
						# misalignment; keep the stack from underflowing.
						if({ self:openTabs:length() > 0 }, {
							self:openTabs:removeAt(index: self:openTabs:length() - 1, default: 0);
						});
					}
				]);
				ci: ci + 1;
			});
			# Whether the NEXT line continues this one: the masked line
			# ends mid-expression (trailing operator or chain dot).
			local String is tail: masked;
			local Boolean is tTrimming: true;
			while({ tTrimming && tail:length() > 0 }, {
				local String is last: tail:charAt(index: tail:length() - 1, default: '');
				if({ last == ' ' || last == "\t" }, {
					tail: tail:substring(start: 0, end: tail:length() - 1);
				}, {
					tTrimming: false;
				});
			});
			prevOpen: tail:endsWith(suffix: '&&') || tail:endsWith(suffix: '||') || tail:endsWith(suffix: '&') || tail:endsWith(suffix: '|') || tail:endsWith(suffix: '+') || tail:endsWith(suffix: '-') || tail:endsWith(suffix: '*') || tail:endsWith(suffix: '.') || tail:endsWith(suffix: '?');
		});
	}

	## Returns a line with string contents and comments replaced by spaces so
	## that brace counting only sees structural characters. Quote state
	## carries across lines through [lintQuote]: raw `'...'`, escaped
	## `"..."`, and raw multi-line `'''...'''` all mask — the mass case is
	## the C runtime held in RuntimePrelude.spec's triple-quoted string,
	## whose lines are DATA, not Spec style. Backslashes escape only
	## inside double quotes (the raw families keep bytes verbatim, per
	## the lexer's two-family rule).
	##
	## @param line: Raw source line.
	## @return: Masked line of identical length.
	Function of String is maskLineStateful(String is line){
		local String is out: '';
		local Int is i: 0;
		while({ i < line:length() }, {
			local String is ch: line:charAt(index: i, default: '');
			if({ self:lintQuote != '' }, {
				if({ self:lintQuote == "'''" && self:matchTriple(line: line, index: i) }, {
					self:lintQuote: '';
					out: out . '   ';
					i: i + 2;
				}, {
					# The lexer's readString skips the char after a
					# backslash in BOTH quote families (a raw '\''
					# is a quoted quote); the verbatim triple does not.
					if({ self:lintQuote != "'''" && ch == "\\" }, {
						out: out . '  ';
						i: i + 1;
					}, {
						if({ ch == self:lintQuote }, {
							self:lintQuote: '';
							out: out . ' ';
						}, {
							out: out . ' ';
						});
					});
				});
			}, {
				match(on: ch, when: [
					['"', '\'']: {
						if({ self:matchTriple(line: line, index: i) }, {
							self:lintQuote: "'''";
							out: out . '   ';
							i: i + 2;
						}, {
							self:lintQuote: ch;
							out: out . ' ';
						});
					},
					'#': {
						i: line:length();
					},
					else: {
						out: out . ch;
					}
				]);
			});
			i: i + 1;
		});
		return out;
	}

	## True when [index] starts a `'''` sequence in [line] — the raw
	## multi-line string delimiter the stateful masker opens and closes on.
	##
	## @param line: The line being scanned.
	## @param index: The candidate index.
	## @return: true when chars [index..index+2] are all single quotes.
	Function of Boolean is matchTriple(String is line, Int is index){
		return index + 2 < line:length()
			&& line:charAt(index: index, default: '') == '\''
			&& line:charAt(index: index + 1, default: '') == '\''
			&& line:charAt(index: index + 2, default: '') == '\'';
	}

	## Inspects an expression node for optional arguments and idioms.
	##
	## @param expr: [Expression] AST node.
	## @param issues: Destination issues array.
	Function is lintExpression(Expression is expr, Array of LintIssue is issues){
		local ExpressionKind is kind: expr:kind;

		match(on: kind, when: [
			ExpressionKind:CALL: {
				local String is method: expr:methodName;
				local Array of NamedArg is args: expr:methodArgs;

				# E10: a constructor call inside a While/Loop
				# callback body allocates per iteration — hoisting hint.
				if({ method == 'init' && self:lintLoopDepth > 0 && self:isClassSpell(target: expr:methodTarget) }, {
					issues:add(item: LintIssue:init(line: 0, isWarning: true, message: 'Construction inside a loop body: hoist the instance out of the loop (E10).'));
				});

				match(on: method, when: [
					'getString': {
						local Boolean is hasDefault: false;
						args:each(action: local Function(NamedArg is arg){
							if({ arg:name == 'default' }, {
								hasDefault: true;
							});
						});
						if({ hasDefault }, {
							issues:add(item: LintIssue:init(line: 0, isWarning: false, message: 'Method call \'getString\' provides optional parameter \'default\'.'));
						});
					},
					'random': {
						local String is msg: 'Method call \'math:random\' provides optional min/max range parameters.';
						if({ args:length() == 0 }, {
							msg: 'Method call \'math:random\' omits optional min/max parameters (using default [0.0, 1.0)).';
						});
						issues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
					}
				]);

				self:lintExpression(expr: expr:methodTarget, issues: issues);
				local Boolean is isLoopDriver: self:isLoopSpell(target: expr:methodTarget);
				args:each(action: local Function(NamedArg is arg){
					if({ isLoopDriver && arg:value:kind == ExpressionKind:ANON_FN }, {
						local Int is savedDepth: self:lintLoopDepth;
						self:lintLoopDepth: self:lintLoopDepth + 1;
						self:lintExpression(expr: arg:value, issues: issues);
						self:lintLoopDepth: savedDepth;
					}, {
						self:lintExpression(expr: arg:value, issues: issues);
					});
				});
			},
			ExpressionKind:BINARY: {
				self:lintExpression(expr: expr:leftExpr, issues: issues);
				self:lintExpression(expr: expr:rightExpr, issues: issues);
			},
			ExpressionKind:UNARY: {
				self:lintExpression(expr: expr:unaryExpr, issues: issues);
			},
			ExpressionKind:ARRAY: {
				expr:arrayItems:each(action: local Function(Expression is item){
					self:lintExpression(expr: item, issues: issues);
				});
			},
			ExpressionKind:ANON_FN: {
				expr:anonBody:each(action: local Function(Statement is st){
					self:lintStatement(stmt: st, issues: issues);
				});
			}
		]);
	}

	## True when [target] spells a loop driver — a While/Loop class-name
	## receiver. Purely syntactic: the standards walk has no class table.
	##
	## @param target: The call's receiver expression.
	## @return: true when the receiver names While or Loop.
	Function of Boolean is isLoopSpell(Expression is target){
		local String is name: '';
		match(on: target:kind, when: [
			ExpressionKind:IDENT: {
				name: target:str;
			},
			ExpressionKind:PATH: {
				local Array of String is segs: target:pathSegments;
				if({ segs:length() > 0 }, {
					name: segs:get(index: segs:length() - 1);
				});
			}
		]);
		return name == 'Loops' || name == 'Loop';
	}

	## True when [target] spells an UpperCamel (class-like) receiver —
	## the shape of a constructor call `X:init(...)`.
	##
	## @param target: The call's receiver expression.
	## @return: true when the receiver is class-spelled.
	Function of Boolean is isClassSpell(Expression is target){
		local String is name: '';
		match(on: target:kind, when: [
			ExpressionKind:IDENT: {
				name: target:str;
			},
			ExpressionKind:PATH: {
				local Array of String is segs: target:pathSegments;
				if({ segs:length() > 0 }, {
					name: segs:get(index: segs:length() - 1);
				});
			}
		]);
		return self:isUpperName(name: name);
	}

	## Inspects a statement node.
	##
	## @param stmt: [Statement] AST node.
	## @param issues: Destination issues array.
	Function is lintStatement(Statement is stmt, Array of LintIssue is issues){
		local StatementKind is kind: stmt:kind;

		match(on: kind, when: [
			StatementKind:VAR_DECL: {
				if({ stmt:hasInit }, {
					self:lintExpression(expr: stmt:initExpr, issues: issues);
				});
			},
			StatementKind:ASSIGN: {
				self:lintExpression(expr: stmt:assignTarget, issues: issues);
				self:lintExpression(expr: stmt:assignValue, issues: issues);
			},
			StatementKind:RETURN: {
				if({ stmt:hasReturnExpr }, {
					self:lintExpression(expr: stmt:returnExpr, issues: issues);
				});
			},
			StatementKind:CLASS: {
				self:lintClass(classDef: stmt:nestedClass, issues: issues);
			},
			StatementKind:EXPR: {
				self:lintExpression(expr: stmt:exprStmt, issues: issues);
			}
		]);
	}

	## Inspects all members of a class definition.
	##
	## @param classDef: [ClassInfo] definition.
	## @param issues: Destination issues array.
	Function is lintClass(ClassInfo is classDef, Array of LintIssue is issues){
		classDef:members:each(action: local Function(Member is m){
			match(on: m:kind, when: [
				MemberKind:METHOD: {
					m:body:each(action: local Function(Statement is s){
						self:lintStatement(stmt: s, issues: issues);
					});
				},
				MemberKind:CLASS: {
					self:lintClass(classDef: m:nestedClass, issues: issues);
				}
			]);
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

	## Phase 0.5 worklist audit: reports every call whose
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
		if({ c:baseClass == 'Enum' }, {
			self:auditEnums:set(key: c:name, value: 'true');
		}, {
			self:auditClasses:set(key: c:name, value: 'true');
		});
		self:auditClassNodes:set(key: c:name, value: c);
		c:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:CLASS }, {
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

	## Walks one statement, auditing every expression it contains (when
	## arms and merge forwards included — the metric must not undercount).
	##
	## @param stmt: [Statement] AST node.
	## @param file: Source file the statement lives in.
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

	## Walks one expression, auditing calls it contains — through casts,
	## if/else and when expressions, map literals, index and field access,
	## and anonymous function bodies.
	##
	## @param expr: [Expression] AST node.
	## @param file: Source file the expression lives in.
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

	## Classifies one call's receiver (§2.2, §4): flags
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
				# Migrated: the owning class (or an ancestor) instance-imports
				# this class (§2.1), so the prefix call is the
				# new model.
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
		return self:auditImportsAsAnywhere(clsName: self:auditOwner:name, targetName: name);
	}

	## Recursive import search over the audit's ancestor lattice.
	##
	## @param clsName: Class being visited.
	## @param targetName: The imported class name sought.
	## @param hops: Recursion budget guard.
	## @return: true when found on this class or an ancestor.
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

	## True when [name] starts with an uppercase letter (the type naming
	## convention); variables and fields are lowerCamel. The 26-way match
	## is deliberate: relational operators on Strings compile to raw
	## pointer comparison (see D5), so `first >= 'A'` is not
	## a legal test.
	##
	## @param name: Identifier to classify.
	## @return: true when the name is UpperCamel.
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
	##
	## @param filePath: Audited root file path.
	## @param issues: Worklist notices.
	Function is auditReport(String is filePath, Array of LintIssue is issues){
		Output:line('Instance-model audit of \'' . filePath . '\':');
		issues:each(action: local Function(LintIssue is issue){
			Output:line(issue:toString());
		});
		Output:line('Instance-model worklist: ' . (issues:length() as String) . ' call site(s) must migrate (Phase 0.5).');
	}
}
