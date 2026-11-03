#[derive(Debug, Clone, PartialEq)]
pub enum TokenKind {
    // Keywords
    Class,
    Extends,
    Local,
    Replace,
    Is,
    Of,
    To,
    If,
    Else,
    Return,
    True,
    False,
    While,
    Break,

    // Literals and Identifiers
    Ident(String),
    StringLit(String),
    NumberLit(i64),
    FloatLit(f64),

    // Comparison & Logical Symbols
    EqualEqual,   // ==
    BangEqual,    // !=
    LessEqual,    // <=
    GreaterEqual, // >=
    Less,         // <
    Greater,      // >
    AmpAmp,       // &&
    PipePipe,     // ||
    Bang,         // !

    // Symbols
    Colon,
    Semicolon,
    Comma,
    Dot,
    Star,
    Plus,
    Minus,
    Slash,
    Percent,
    LBrace,
    RBrace,
    LParen,
    RParen,
    LBracket,
    RBracket,

    Eof,
}

#[derive(Debug, Clone)]
pub struct Token {
    pub kind: TokenKind,
    pub line: usize,
    pub col: usize,
}

pub struct Lexer<'a> {
    chars: Vec<char>,
    pos: usize,
    line: usize,
    col: usize,
    _source: &'a str,
}

impl<'a> Lexer<'a> {
    pub fn new(source: &'a str) -> Self {
        Self {
            chars: source.chars().collect(),
            pos: 0,
            line: 1,
            col: 1,
            _source: source,
        }
    }

    fn peek(&self) -> Option<char> {
        self.chars.get(self.pos).copied()
    }

    fn peek_at(&self, idx: usize) -> Option<char> {
        self.chars.get(idx).copied()
    }

    fn advance(&mut self) -> Option<char> {
        if let Some(ch) = self.peek() {
            self.pos += 1;
            if ch == '\n' {
                self.line += 1;
                self.col = 1;
            } else {
                self.col += 1;
            }
            Some(ch)
        } else {
            None
        }
    }

    pub fn tokenize(&mut self) -> Result<Vec<Token>, String> {
        let mut tokens = Vec::new();
        loop {
            self.skip_whitespace_and_comments();
            let start_line = self.line;
            let start_col = self.col;

            let ch = match self.peek() {
                Some(c) => c,
                None => {
                    tokens.push(Token {
                        kind: TokenKind::Eof,
                        line: self.line,
                        col: self.col,
                    });
                    break;
                }
            };

            let kind = match ch {
                '{' => {
                    self.advance();
                    TokenKind::LBrace
                }
                '}' => {
                    self.advance();
                    TokenKind::RBrace
                }
                '(' => {
                    self.advance();
                    TokenKind::LParen
                }
                ')' => {
                    self.advance();
                    TokenKind::RParen
                }
                '[' => {
                    self.advance();
                    TokenKind::LBracket
                }
                ']' => {
                    self.advance();
                    TokenKind::RBracket
                }
                ':' => {
                    self.advance();
                    TokenKind::Colon
                }
                ';' => {
                    self.advance();
                    TokenKind::Semicolon
                }
                ',' => {
                    self.advance();
                    TokenKind::Comma
                }
                '.' => {
                    self.advance();
                    TokenKind::Dot
                }
                '+' => {
                    self.advance();
                    TokenKind::Plus
                }
                '-' => {
                    self.advance();
                    TokenKind::Minus
                }
                '*' => {
                    self.advance();
                    TokenKind::Star
                }
                '/' => {
                    self.advance();
                    TokenKind::Slash
                }
                '%' => {
                    self.advance();
                    TokenKind::Percent
                }
                '=' => {
                    self.advance();
                    if self.peek() == Some('=') {
                        self.advance();
                        TokenKind::EqualEqual
                    } else {
                        return Err(format!(
                            "Unexpected character '=' at line {}, col {}",
                            start_line, start_col
                        ));
                    }
                }
                '!' => {
                    self.advance();
                    if self.peek() == Some('=') {
                        self.advance();
                        TokenKind::BangEqual
                    } else {
                        TokenKind::Bang
                    }
                }
                '<' => {
                    self.advance();
                    if self.peek() == Some('=') {
                        self.advance();
                        TokenKind::LessEqual
                    } else {
                        TokenKind::Less
                    }
                }
                '>' => {
                    self.advance();
                    if self.peek() == Some('=') {
                        self.advance();
                        TokenKind::GreaterEqual
                    } else {
                        TokenKind::Greater
                    }
                }
                '&' => {
                    self.advance();
                    if self.peek() == Some('&') {
                        self.advance();
                        TokenKind::AmpAmp
                    } else {
                        return Err(format!(
                            "Unexpected character '&' at line {}, col {}",
                            start_line, start_col
                        ));
                    }
                }
                '|' => {
                    self.advance();
                    if self.peek() == Some('|') {
                        self.advance();
                        TokenKind::PipePipe
                    } else {
                        return Err(format!(
                            "Unexpected character '|' at line {}, col {}",
                            start_line, start_col
                        ));
                    }
                }
                '\'' | '"' => self.lex_string(ch)?,
                c if c.is_ascii_digit() => self.lex_number()?,
                c if is_ident_start(c) => self.lex_ident_or_keyword(),
                _ => {
                    return Err(format!(
                        "Unexpected character '{}' at line {}, col {}",
                        ch, start_line, start_col
                    ));
                }
            };

            tokens.push(Token {
                kind,
                line: start_line,
                col: start_col,
            });
        }
        Ok(tokens)
    }

    fn skip_whitespace_and_comments(&mut self) {
        while let Some(ch) = self.peek() {
            if ch.is_whitespace() {
                self.advance();
            } else if ch == '#' {
                // Single line comment
                while let Some(c) = self.peek() {
                    self.advance();
                    if c == '\n' {
                        break;
                    }
                }
            } else {
                break;
            }
        }
    }

    fn lex_string(&mut self, quote: char) -> Result<TokenKind, String> {
        let start_line = self.line;
        let start_col = self.col;
        self.advance(); // consume opening quote
        let mut s = String::new();

        if quote == '\'' {
            // Single-quote: raw/literal string (only escapes \' and \\)
            while let Some(ch) = self.peek() {
                if ch == '\'' {
                    self.advance();
                    return Ok(TokenKind::StringLit(s));
                } else if ch == '\\' {
                    self.advance();
                    match self.peek() {
                        Some('\'') => {
                            self.advance();
                            s.push('\'');
                        }
                        Some('\\') => {
                            self.advance();
                            s.push('\\');
                        }
                        _ => {
                            s.push('\\');
                        }
                    }
                } else {
                    s.push(ch);
                    self.advance();
                }
            }
        } else {
            // Double-quote: supports whitespace escape characters (\n, \t, \r, etc.)
            while let Some(ch) = self.peek() {
                if ch == '"' {
                    self.advance();
                    return Ok(TokenKind::StringLit(s));
                } else if ch == '\\' {
                    self.advance();
                    match self.advance() {
                        Some('n') => s.push('\n'),
                        Some('t') => s.push('\t'),
                        Some('r') => s.push('\r'),
                        Some('v') => s.push('\x0b'),
                        Some('f') => s.push('\x0c'),
                        Some('\\') => s.push('\\'),
                        Some('"') => s.push('"'),
                        Some('0') => s.push('\0'),
                        Some(other) => s.push(other),
                        None => {
                            return Err(format!(
                                "Unterminated string literal at line {}, col {}",
                                start_line, start_col
                            ));
                        }
                    }
                } else {
                    s.push(ch);
                    self.advance();
                }
            }
        }

        Err(format!(
            "Unterminated string literal at line {}, col {}",
            start_line, start_col
        ))
    }

    fn lex_number(&mut self) -> Result<TokenKind, String> {
        let mut num_str = String::new();
        while let Some(ch) = self.peek() {
            if ch.is_ascii_digit() {
                num_str.push(ch);
                self.advance();
            } else {
                break;
            }
        }

        // Check if this is a float (e.g. 3.14)
        if self.peek() == Some('.') {
            if let Some(next) = self.peek_at(self.pos + 1) {
                if next.is_ascii_digit() {
                    num_str.push('.');
                    self.advance(); // consume '.'
                    while let Some(ch) = self.peek() {
                        if ch.is_ascii_digit() {
                            num_str.push(ch);
                            self.advance();
                        } else {
                            break;
                        }
                    }
                    let val = num_str
                        .parse::<f64>()
                        .map_err(|e| format!("Invalid float '{}': {}", num_str, e))?;
                    return Ok(TokenKind::FloatLit(val));
                }
            }
        }

        let val = num_str
            .parse::<i64>()
            .map_err(|e| format!("Invalid number '{}': {}", num_str, e))?;
        Ok(TokenKind::NumberLit(val))
    }

    fn lex_ident_or_keyword(&mut self) -> TokenKind {
        let mut s = String::new();
        while let Some(ch) = self.peek() {
            if is_ident_continue(ch) {
                s.push(ch);
                self.advance();
            } else {
                break;
            }
        }

        match s.as_str() {
            "class" => TokenKind::Class,
            "extends" => TokenKind::Extends,
            "local" => TokenKind::Local,
            "replace" => TokenKind::Replace,
            "is" => TokenKind::Is,
            "of" => TokenKind::Of,
            "to" => TokenKind::To,
            "if" => TokenKind::If,
            "else" => TokenKind::Else,
            "return" => TokenKind::Return,
            "while" => TokenKind::While,
            "break" => TokenKind::Break,
            "true" => TokenKind::True,
            "false" => TokenKind::False,
            _ => TokenKind::Ident(s),
        }
    }
}

fn is_ident_start(c: char) -> bool {
    c.is_alphabetic() || c == '_'
}

fn is_ident_continue(c: char) -> bool {
    c.is_alphanumeric() || c == '_'
}
