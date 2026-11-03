use crate::ast::*;
use crate::lexer::{Token, TokenKind};

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, pos: 0 }
    }

    fn peek(&self) -> &TokenKind {
        &self.peek_token().kind
    }

    fn peek_token(&self) -> &Token {
        if self.pos < self.tokens.len() {
            &self.tokens[self.pos]
        } else {
            &self.tokens[self.tokens.len() - 1]
        }
    }

    fn peek_next(&self) -> &TokenKind {
        if self.pos + 1 < self.tokens.len() {
            &self.tokens[self.pos + 1].kind
        } else {
            &TokenKind::Eof
        }
    }

    fn peek_token_at(&self, idx: usize) -> Token {
        if idx < self.tokens.len() {
            self.tokens[idx].clone()
        } else {
            self.tokens[self.tokens.len() - 1].clone()
        }
    }

    fn check(&self, kind: &TokenKind) -> bool {
        self.peek() == kind
    }

    fn advance(&mut self) -> Token {
        let tok = self.peek_token().clone();
        if self.pos < self.tokens.len() {
            self.pos += 1;
        }
        tok
    }

    fn expect(&mut self, kind: &TokenKind) -> Result<Token, String> {
        let tok = self.peek_token().clone();
        if &tok.kind == kind {
            self.advance();
            Ok(tok)
        } else {
            Err(format!(
                "Expected {:?}, found {:?} at line {}, col {}",
                kind, tok.kind, tok.line, tok.col
            ))
        }
    }

    pub fn parse_program(&mut self) -> Result<Program, String> {
        let mut classes = Vec::new();
        while !self.check(&TokenKind::Eof) {
            classes.push(self.parse_class()?);
        }
        Ok(Program { classes })
    }

    pub fn parse_class(&mut self) -> Result<ClassDef, String> {
        self.expect(&TokenKind::Class)?;
        let name = match self.peek_token().clone().kind {
            TokenKind::Ident(n) => {
                self.advance();
                n
            }
            other => {
                return Err(format!(
                    "Expected class name, found {:?} at line {}",
                    other,
                    self.peek_token().line
                ));
            }
        };

        let base_class = if self.check(&TokenKind::Extends) {
            self.advance();
            match self.advance().kind {
                TokenKind::Ident(b) => Some(b),
                other => return Err(format!("Expected base class name, found {:?}", other)),
            }
        } else {
            None
        };

        self.expect(&TokenKind::LBrace)?;
        let mut members = Vec::new();
        while !self.check(&TokenKind::RBrace) && !self.check(&TokenKind::Eof) {
            members.push(self.parse_member()?);
        }
        self.expect(&TokenKind::RBrace)?;

        Ok(ClassDef {
            name,
            base_class,
            members,
        })
    }

    fn parse_member(&mut self) -> Result<Member, String> {
        // Internal class definition
        if self.check(&TokenKind::Class) {
            let class_def = self.parse_class()?;
            return Ok(Member::Class(class_def));
        }

        let mut modifiers = Vec::new();
        while self.check(&TokenKind::Local) || self.check(&TokenKind::Replace) {
            match self.advance().kind {
                TokenKind::Local => modifiers.push("local".to_string()),
                TokenKind::Replace => modifiers.push("replace".to_string()),
                _ => unreachable!(),
            }
        }

        // Check for shorthand method syntax: e.g. init(...) or evaluate(...) or iteration(...)
        if let TokenKind::Ident(id) = self.peek_token().clone().kind {
            if self.peek_next() == &TokenKind::LParen {
                self.advance(); // consume method name
                self.advance(); // consume '('
                let mut params = Vec::new();
                if !self.check(&TokenKind::RParen) {
                    loop {
                        params.push(self.parse_param()?);
                        if self.check(&TokenKind::Comma) {
                            self.advance();
                        } else {
                            break;
                        }
                    }
                }
                self.expect(&TokenKind::RParen)?;
                self.expect(&TokenKind::LBrace)?;
                let mut body = Vec::new();
                while !self.check(&TokenKind::RBrace) && !self.check(&TokenKind::Eof) {
                    body.push(self.parse_statement()?);
                }
                self.expect(&TokenKind::RBrace)?;

                return Ok(Member::Method {
                    modifiers,
                    return_type: None,
                    name: id,
                    params,
                    body,
                });
            }
        }

        let member_type = self.parse_type()?;
        self.expect(&TokenKind::Is)?;

        let name = match self.peek_token().clone().kind {
            TokenKind::Ident(n) => {
                self.advance();
                n
            }
            other => {
                return Err(format!(
                    "Expected member name, found {:?} at line {}",
                    other,
                    self.peek_token().line
                ));
            }
        };

        if self.check(&TokenKind::LParen) {
            // Method
            self.advance();
            let mut params = Vec::new();
            if !self.check(&TokenKind::RParen) {
                loop {
                    params.push(self.parse_param()?);
                    if self.check(&TokenKind::Comma) {
                        self.advance();
                    } else {
                        break;
                    }
                }
            }
            self.expect(&TokenKind::RParen)?;
            self.expect(&TokenKind::LBrace)?;

            let mut body = Vec::new();
            while !self.check(&TokenKind::RBrace) && !self.check(&TokenKind::Eof) {
                body.push(self.parse_statement()?);
            }
            self.expect(&TokenKind::RBrace)?;

            Ok(Member::Method {
                modifiers,
                return_type: Some(member_type),
                name,
                params,
                body,
            })
        } else {
            // Field
            let init = if self.check(&TokenKind::Colon) {
                self.advance();
                Some(self.parse_expression()?)
            } else {
                None
            };
            self.expect(&TokenKind::Semicolon)?;
            Ok(Member::Field {
                modifiers,
                field_type: member_type,
                name,
                init,
            })
        }
    }

    fn parse_param(&mut self) -> Result<Parameter, String> {
        // Shorthand parameter: name without type
        if let TokenKind::Ident(id) = self.peek_token().clone().kind {
            if self.peek_next() == &TokenKind::Comma || self.peek_next() == &TokenKind::RParen {
                self.advance();
                return Ok(Parameter {
                    param_type: None,
                    name: id,
                });
            }
        }

        // Typed parameter: Type is name
        let param_type = self.parse_type()?;
        self.expect(&TokenKind::Is)?;
        let param_name = match self.advance().kind {
            TokenKind::Ident(n) => n,
            other => return Err(format!("Expected parameter name, found {:?}", other)),
        };
        Ok(Parameter {
            param_type: Some(param_type),
            name: param_name,
        })
    }

    fn parse_type(&mut self) -> Result<Type, String> {
        let base_name = match self.peek_token().clone().kind {
            TokenKind::Ident(n) => {
                self.advance();
                n
            }
            other => {
                return Err(format!(
                    "Expected type identifier, found {:?} at line {}",
                    other,
                    self.peek_token().line
                ));
            }
        };

        if self.check(&TokenKind::Of) {
            self.advance();
            let mut params = Vec::new();
            let first = self.parse_type()?;
            params.push(first);

            if self.check(&TokenKind::To) {
                self.advance();
                let second = self.parse_type()?;
                params.push(second);
            }
            Ok(Type::Generic(base_name, params))
        } else {
            Ok(Type::Simple(base_name))
        }
    }

    fn parse_statement(&mut self) -> Result<Statement, String> {
        if self.check(&TokenKind::Class) {
            let class_def = self.parse_class()?;
            return Ok(Statement::Class(class_def));
        }

        if self.check(&TokenKind::If) {
            return self.parse_if();
        }

        if self.check(&TokenKind::Return) {
            return self.parse_return();
        }

        if self.check(&TokenKind::Local) {
            let mut modifiers = Vec::new();
            while self.check(&TokenKind::Local) {
                self.advance();
                modifiers.push("local".to_string());
            }
            let var_type = self.parse_type()?;
            self.expect(&TokenKind::Is)?;
            let name = match self.advance().kind.clone() {
                TokenKind::Ident(n) => n,
                other => return Err(format!("Expected variable name, found {:?}", other)),
            };
            let init = if self.check(&TokenKind::Colon) {
                self.advance();
                Some(self.parse_expression()?)
            } else {
                None
            };
            self.expect(&TokenKind::Semicolon)?;
            return Ok(Statement::VariableDecl {
                modifiers,
                var_type,
                name,
                init,
            });
        }

        // Check if this statement is an assignment: <target> : <value> ;
        if let Some(colon_pos) = self.find_assignment_colon() {
            let target = self.parse_assignment_target(colon_pos)?;
            self.expect(&TokenKind::Colon)?;
            let value = self.parse_expression()?;
            self.expect(&TokenKind::Semicolon)?;
            return Ok(Statement::Assignment { target, value });
        }

        let expr = self.parse_expression()?;
        self.expect(&TokenKind::Semicolon)?;
        Ok(Statement::Expression(expr))
    }

    fn find_assignment_colon(&self) -> Option<usize> {
        if !matches!(self.peek_token().kind, TokenKind::Ident(_)) {
            return None;
        }

        // Find the terminating semicolon of this statement
        let mut depth = 0;
        let mut semi_pos = None;
        let mut i = self.pos;
        while i < self.tokens.len() {
            match self.tokens[i].kind {
                TokenKind::LParen | TokenKind::LBracket | TokenKind::LBrace => depth += 1,
                TokenKind::RParen | TokenKind::RBracket | TokenKind::RBrace => {
                    if depth > 0 {
                        depth -= 1;
                    }
                }
                TokenKind::Semicolon if depth == 0 => {
                    semi_pos = Some(i);
                    break;
                }
                _ => {}
            }
            i += 1;
        }

        let semi_idx = semi_pos?;

        // Check for receiver:field : value; (e.g. self:length: source:length(); or callExpr:methodTarget: currentExpr;)
        if self.pos + 3 < semi_idx
            && self.tokens[self.pos + 1].kind == TokenKind::Colon
            && self.tokens[self.pos + 3].kind == TokenKind::Colon
        {
            let is_rhs_method_call = self.pos + 5 < self.tokens.len()
                && self.tokens[self.pos + 5].kind == TokenKind::LParen;
            if !is_rhs_method_call {
                return Some(self.pos + 3);
            }
        }

        // Check for target : value; (e.g. length: source:length(); or idx: idx + 1;)
        // Note: "self" alone can never be an assignment target (self: value; is invalid).
        if self.pos + 1 < semi_idx && self.tokens[self.pos + 1].kind == TokenKind::Colon {
            let is_self = matches!(&self.tokens[self.pos].kind, TokenKind::Ident(id) if id == "self");
            if !is_self {
                let is_method_call = self.pos + 3 < self.tokens.len()
                    && self.tokens[self.pos + 3].kind == TokenKind::LParen;
                if !is_method_call {
                    return Some(self.pos + 1);
                }
            }
        }

        None
    }

    fn parse_assignment_target(&mut self, colon_pos: usize) -> Result<Expression, String> {
        let mut segments = Vec::new();
        while self.pos < colon_pos {
            match self.advance().kind {
                TokenKind::Ident(n) => segments.push(n),
                TokenKind::Colon => {}
                other => {
                    return Err(format!(
                        "Unexpected token in assignment target: {:?}",
                        other
                    ))
                }
            }
        }
        if segments.len() == 1 {
            Ok(Expression::Identifier(segments.remove(0)))
        } else {
            Ok(Expression::Path(segments))
        }
    }

    fn parse_if(&mut self) -> Result<Statement, String> {
        self.expect(&TokenKind::If)?;
        self.expect(&TokenKind::LParen)?;
        let condition = self.parse_expression()?;
        self.expect(&TokenKind::RParen)?;
        self.expect(&TokenKind::LBrace)?;
        let mut then_branch = Vec::new();
        while !self.check(&TokenKind::RBrace) && !self.check(&TokenKind::Eof) {
            then_branch.push(self.parse_statement()?);
        }
        self.expect(&TokenKind::RBrace)?;

        let else_branch = if self.check(&TokenKind::Else) {
            self.advance(); // consume 'else'
            if self.check(&TokenKind::If) {
                let nested_if = self.parse_if()?;
                Some(vec![nested_if])
            } else {
                self.expect(&TokenKind::LBrace)?;
                let mut else_stmts = Vec::new();
                while !self.check(&TokenKind::RBrace) && !self.check(&TokenKind::Eof) {
                    else_stmts.push(self.parse_statement()?);
                }
                self.expect(&TokenKind::RBrace)?;
                Some(else_stmts)
            }
        } else {
            None
        };

        Ok(Statement::If {
            condition,
            then_branch,
            else_branch,
        })
    }

    fn parse_return(&mut self) -> Result<Statement, String> {
        self.expect(&TokenKind::Return)?;
        let expr = if self.check(&TokenKind::Semicolon) {
            None
        } else {
            Some(self.parse_expression()?)
        };
        self.expect(&TokenKind::Semicolon)?;
        Ok(Statement::Return(expr))
    }

    pub fn parse_expression(&mut self) -> Result<Expression, String> {
        self.parse_logical_or()
    }

    fn parse_logical_or(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_logical_and()?;
        while self.check(&TokenKind::PipePipe) {
            self.advance();
            let right = self.parse_logical_and()?;
            left = Expression::Binary {
                op: BinaryOp::Or,
                left: Box::new(left),
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_logical_and(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_equality()?;
        while self.check(&TokenKind::AmpAmp) {
            self.advance();
            let right = self.parse_equality()?;
            left = Expression::Binary {
                op: BinaryOp::And,
                left: Box::new(left),
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_equality(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_relational()?;
        while self.check(&TokenKind::EqualEqual) || self.check(&TokenKind::BangEqual) {
            let op = match self.advance().kind {
                TokenKind::EqualEqual => BinaryOp::Equal,
                TokenKind::BangEqual => BinaryOp::NotEqual,
                _ => unreachable!(),
            };
            let right = self.parse_relational()?;
            left = Expression::Binary {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_relational(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_concat()?;
        while self.check(&TokenKind::Less)
            || self.check(&TokenKind::LessEqual)
            || self.check(&TokenKind::Greater)
            || self.check(&TokenKind::GreaterEqual)
        {
            let op = match self.advance().kind {
                TokenKind::Less => BinaryOp::Less,
                TokenKind::LessEqual => BinaryOp::LessEqual,
                TokenKind::Greater => BinaryOp::Greater,
                TokenKind::GreaterEqual => BinaryOp::GreaterEqual,
                _ => unreachable!(),
            };
            let right = self.parse_concat()?;
            left = Expression::Binary {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_concat(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_additive()?;
        while self.check(&TokenKind::Dot) {
            self.advance();
            let right = self.parse_additive()?;
            left = Expression::Binary {
                op: BinaryOp::Concat,
                left: Box::new(left),
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_additive(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_multiplicative()?;
        while self.check(&TokenKind::Plus) || self.check(&TokenKind::Minus) {
            let op = match self.advance().kind {
                TokenKind::Plus => BinaryOp::Add,
                TokenKind::Minus => BinaryOp::Sub,
                _ => unreachable!(),
            };
            let right = self.parse_multiplicative()?;
            left = Expression::Binary {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_multiplicative(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_unary()?;
        while self.check(&TokenKind::Star)
            || self.check(&TokenKind::Slash)
            || self.check(&TokenKind::Percent)
        {
            let op = match self.advance().kind {
                TokenKind::Star => BinaryOp::Mul,
                TokenKind::Slash => BinaryOp::Div,
                TokenKind::Percent => BinaryOp::Mod,
                _ => unreachable!(),
            };
            let right = self.parse_unary()?;
            left = Expression::Binary {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_unary(&mut self) -> Result<Expression, String> {
        if self.check(&TokenKind::Minus) {
            self.advance();
            let expr = self.parse_unary()?;
            Ok(Expression::Unary {
                op: UnaryOp::Neg,
                expr: Box::new(expr),
            })
        } else if self.check(&TokenKind::Bang) {
            self.advance();
            let expr = self.parse_unary()?;
            Ok(Expression::Unary {
                op: UnaryOp::Not,
                expr: Box::new(expr),
            })
        } else {
            self.parse_postfix()
        }
    }

    fn parse_argument_list(&mut self) -> Result<Vec<NamedArg>, String> {
        let mut args = Vec::new();
        if !self.check(&TokenKind::RParen) {
            loop {
                let is_named_arg = if let TokenKind::Ident(ref n) = self.peek().clone() {
                    if self.peek_next() == &TokenKind::Colon {
                        let is_upper = n.chars().next().map_or(false, |c| c.is_uppercase());
                        if is_upper {
                            false
                        } else if self.pos + 2 < self.tokens.len() {
                            let colon_tok = &self.tokens[self.pos + 1];
                            let next_tok = &self.tokens[self.pos + 2];
                            if !matches!(next_tok.kind, TokenKind::Ident(_)) {
                                true
                            } else {
                                next_tok.line > colon_tok.line || next_tok.col > colon_tok.col + 1
                            }
                        } else {
                            true
                        }
                    } else {
                        false
                    }
                } else {
                    false
                };

                if is_named_arg {
                    let arg_name = match self.advance().kind {
                        TokenKind::Ident(n) => n,
                        _ => unreachable!(),
                    };
                    self.advance(); // consume ':'
                    let val = self.parse_expression()?;
                    args.push(NamedArg {
                        name: Some(arg_name),
                        value: val,
                    });
                } else {
                    let val = self.parse_expression()?;
                    args.push(NamedArg {
                        name: None,
                        value: val,
                    });
                }

                if self.check(&TokenKind::Comma) {
                    self.advance();
                } else {
                    break;
                }
            }
        }
        self.expect(&TokenKind::RParen)?;
        Ok(args)
    }

    fn parse_postfix(&mut self) -> Result<Expression, String> {
        let mut expr = self.parse_primary()?;

        loop {
            if self.check(&TokenKind::Colon) {
                if self.peek_next() == &TokenKind::Star {
                    self.advance(); // consume ':'
                    self.advance(); // consume '*'
                    match expr {
                        Expression::Identifier(id) => {
                            expr = Expression::Path(vec![id, "*".to_string()]);
                        }
                        Expression::Path(mut segments) => {
                            segments.push("*".to_string());
                            expr = Expression::Path(segments);
                        }
                        _ => return Err("Invalid wildcard path".to_string()),
                    }
                } else if let TokenKind::Ident(id) = self.peek_token_at(self.pos + 1).kind {
                    self.advance(); // consume ':'
                    self.advance(); // consume ident
                    if self.check(&TokenKind::LParen) {
                        self.advance(); // consume '('
                        let args = self.parse_argument_list()?;
                        expr = Expression::MethodCall {
                            target: Box::new(expr),
                            method: id,
                            args,
                        };
                    } else {
                        // Path segment
                        match expr {
                            Expression::Identifier(first) => {
                                expr = Expression::Path(vec![first, id]);
                            }
                            Expression::Path(mut segments) => {
                                segments.push(id);
                                expr = Expression::Path(segments);
                            }
                            _ => {
                                expr = Expression::MethodCall {
                                    target: Box::new(expr),
                                    method: id,
                                    args: Vec::new(),
                                };
                            }
                        }
                    }
                } else {
                    break;
                }
            } else if self.check(&TokenKind::LParen) {
                // Function call on current scope: func(args)
                self.advance(); // consume '('
                let args = self.parse_argument_list()?;
                if let Expression::Identifier(func_name) = expr {
                    expr = Expression::MethodCall {
                        target: Box::new(Expression::Identifier("self".to_string())),
                        method: func_name,
                        args,
                    };
                } else {
                    expr = Expression::MethodCall {
                        target: Box::new(expr),
                        method: "".to_string(),
                        args,
                    };
                }
            } else if self.check(&TokenKind::LBracket) {
                self.advance(); // consume '['
                let index = self.parse_expression()?;
                self.expect(&TokenKind::RBracket)?;
                expr = Expression::Index {
                    target: Box::new(expr),
                    index: Box::new(index),
                };
            } else {
                break;
            }
        }

        Ok(expr)
    }

    fn parse_primary(&mut self) -> Result<Expression, String> {
        let tok = self.peek_token().clone();
        match tok.kind {
            TokenKind::StringLit(s) => {
                self.advance();
                Ok(Expression::StringLiteral(s))
            }
            TokenKind::NumberLit(n) => {
                self.advance();
                Ok(Expression::NumberLiteral(n))
            }
            TokenKind::FloatLit(f) => {
                self.advance();
                Ok(Expression::FloatLiteral(f))
            }
            TokenKind::True => {
                self.advance();
                Ok(Expression::BooleanLiteral(true))
            }
            TokenKind::False => {
                self.advance();
                Ok(Expression::BooleanLiteral(false))
            }
            TokenKind::Ident(id) => {
                self.advance();
                Ok(Expression::Identifier(id))
            }
            TokenKind::LParen => {
                self.advance(); // consume '('
                let expr = self.parse_expression()?;
                self.expect(&TokenKind::RParen)?;
                Ok(expr)
            }
            TokenKind::LBracket => {
                self.advance(); // consume '['
                let mut items = Vec::new();
                if !self.check(&TokenKind::RBracket) {
                    loop {
                        items.push(self.parse_expression()?);
                        if self.check(&TokenKind::Comma) {
                            self.advance();
                        } else {
                            break;
                        }
                    }
                }
                self.expect(&TokenKind::RBracket)?;
                Ok(Expression::ArrayLiteral(items))
            }
            other => Err(format!(
                "Unexpected token {:?} in expression at line {}, col {}",
                other, tok.line, tok.col
            )),
        }
    }
}
