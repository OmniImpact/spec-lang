use crate::ast::*;

pub struct LintIssue {
    pub line: usize,
    pub is_warning: bool,
    pub message: String,
}

pub struct Linter;

impl Linter {
    pub fn lint_source(source: &str, program: Option<&Program>) -> Vec<LintIssue> {
        let mut issues = Vec::new();

        // 1. Indentation Check:
        // Spec standard is tab-based indentation. Detect space-based indentation.
        for (i, line) in source.lines().enumerate() {
            let line_num = i + 1;
            let mut leading_spaces = 0;
            for ch in line.chars() {
                if ch == ' ' {
                    leading_spaces += 1;
                } else if ch == '\t' {
                    // Tab is expected standard
                } else {
                    break;
                }
            }

            if leading_spaces > 0 {
                issues.push(LintIssue {
                    line: line_num,
                    is_warning: true,
                    message: format!(
                        "Space-based indentation detected ({} space{}). Spec standard requires tabs.",
                        leading_spaces,
                        if leading_spaces == 1 { "" } else { "s" }
                    ),
                });
            }
        }

        // 2. Optional Parameters and Syntax Analysis (from AST):
        if let Some(prog) = program {
            Self::lint_ast(prog, &mut issues);
        }

        issues
    }

    fn lint_ast(program: &Program, issues: &mut Vec<LintIssue>) {
        for class_def in &program.classes {
            Self::lint_class(class_def, issues);
        }
    }

    fn lint_class(class_def: &ClassDef, issues: &mut Vec<LintIssue>) {
        for member in &class_def.members {
            match member {
                Member::Method { body, .. } => {
                    for stmt in body {
                        Self::lint_statement(stmt, issues);
                    }
                }
                Member::Class(nested) => {
                    Self::lint_class(nested, issues);
                }
                _ => {}
            }
        }
    }

    fn lint_statement(stmt: &Statement, issues: &mut Vec<LintIssue>) {
        match stmt {
            Statement::VariableDecl { init, .. } => {
                if let Some(expr) = init {
                    Self::lint_expr(expr, issues);
                }
            }
            Statement::Assignment { target, value } => {
                Self::lint_expr(target, issues);
                Self::lint_expr(value, issues);
            }
            Statement::If {
                condition,
                then_branch,
                else_branch,
            } => {
                Self::lint_expr(condition, issues);
                for s in then_branch {
                    Self::lint_statement(s, issues);
                }
                if let Some(else_stmts) = else_branch {
                    for s in else_stmts {
                        Self::lint_statement(s, issues);
                    }
                }
            }
            Statement::Return(opt_expr) => {
                if let Some(expr) = opt_expr {
                    Self::lint_expr(expr, issues);
                }
            }
            Statement::Class(nested) => {
                Self::lint_class(nested, issues);
            }
            Statement::Expression(expr) => {
                Self::lint_expr(expr, issues);
            }
        }
    }

    fn lint_expr(expr: &Expression, issues: &mut Vec<LintIssue>) {
        match expr {
            Expression::MethodCall { method, target, args } => {
                if method == "getString" {
                    let has_default = args.iter().any(|a| a.name.as_deref() == Some("default"));
                    if has_default {
                        issues.push(LintIssue {
                            line: 0,
                            is_warning: false,
                            message: "Method call 'getString' provides optional parameter 'default'.".to_string(),
                        });
                    }
                } else if method == "random" {
                    if args.is_empty() {
                        issues.push(LintIssue {
                            line: 0,
                            is_warning: false,
                            message: "Method call 'math:random' omits optional min/max parameters (using default [0.0, 1.0)).".to_string(),
                        });
                    } else {
                        issues.push(LintIssue {
                            line: 0,
                            is_warning: false,
                            message: "Method call 'math:random' provides optional min/max range parameters.".to_string(),
                        });
                    }
                }

                Self::lint_expr(target, issues);
                for arg in args {
                    Self::lint_expr(&arg.value, issues);
                }
            }
            Expression::Binary { left, right, .. } => {
                Self::lint_expr(left, issues);
                Self::lint_expr(right, issues);
            }
            Expression::Unary { expr, .. } => {
                Self::lint_expr(expr, issues);
            }
            Expression::Index { target, index } => {
                Self::lint_expr(target, issues);
                Self::lint_expr(index, issues);
            }
            Expression::ArrayLiteral(items) => {
                for item in items {
                    Self::lint_expr(item, issues);
                }
            }
            Expression::AnonymousFunction { body, .. } => {
                for s in body {
                    Self::lint_statement(s, issues);
                }
            }
            _ => {}
        }
    }
}
