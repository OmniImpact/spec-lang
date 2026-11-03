#[derive(Debug, Clone, PartialEq)]
pub enum Type {
    Simple(String),
    Generic(String, Vec<Type>),
}

#[derive(Debug, Clone, PartialEq)]
pub enum BinaryOp {
    Concat, // .
    Add,    // +
    Sub,    // -
    Mul,    // *
    Div,    // /
    Mod,    // %
    Equal,        // ==
    NotEqual,     // !=
    Less,         // <
    LessEqual,    // <=
    Greater,      // >
    GreaterEqual, // >=
    And,          // &&
    Or,           // ||
}

#[derive(Debug, Clone, PartialEq)]
pub enum UnaryOp {
    Neg, // -
    Not, // !
}

#[derive(Debug, Clone, PartialEq)]
pub struct NamedArg {
    pub name: Option<String>,
    pub value: Expression,
}

#[derive(Debug, Clone, PartialEq)]
pub enum Expression {
    StringLiteral(String),
    NumberLiteral(i64),
    FloatLiteral(f64),
    BooleanLiteral(bool),
    Identifier(String),
    Path(Vec<String>),
    ArrayLiteral(Vec<Expression>),
    Index {
        target: Box<Expression>,
        index: Box<Expression>,
    },
    MethodCall {
        target: Box<Expression>,
        method: String,
        args: Vec<NamedArg>,
    },
    Binary {
        op: BinaryOp,
        left: Box<Expression>,
        right: Box<Expression>,
    },
    Unary {
        op: UnaryOp,
        expr: Box<Expression>,
    },
}

#[derive(Debug, Clone, PartialEq)]
pub struct Parameter {
    pub param_type: Option<Type>,
    pub name: String,
}

#[derive(Debug, Clone, PartialEq)]
pub enum Statement {
    VariableDecl {
        modifiers: Vec<String>,
        var_type: Type,
        name: String,
        init: Option<Expression>,
    },
    Assignment {
        target: Expression,
        value: Expression,
    },
    If {
        condition: Expression,
        then_branch: Vec<Statement>,
        else_branch: Option<Vec<Statement>>,
    },
    While {
        condition: Expression,
        body: Vec<Statement>,
    },
    Break,
    Return(Option<Expression>),
    Class(ClassDef),
    Expression(Expression),
}

#[derive(Debug, Clone, PartialEq)]
pub enum Member {
    Field {
        modifiers: Vec<String>,
        field_type: Type,
        name: String,
        init: Option<Expression>,
    },
    Method {
        modifiers: Vec<String>,
        return_type: Option<Type>,
        name: String,
        params: Vec<Parameter>,
        body: Vec<Statement>,
    },
    Class(ClassDef),
}

#[derive(Debug, Clone, PartialEq)]
pub struct ClassDef {
    pub name: String,
    pub base_class: Option<String>,
    pub members: Vec<Member>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Program {
    pub classes: Vec<ClassDef>,
}
