mod ast;
mod codegen;
mod lexer;
mod linter;
mod loader;
mod parser;

use std::env;
use std::fs;
use std::process::{exit, Command};

fn print_usage() {
    eprintln!("Usage: spec -i <input.spec> -o <output_binary>");
    eprintln!("       spec --lint <input.spec>");
}

fn run_linter(file_path: &str) {
    let source = match fs::read_to_string(file_path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Error reading '{}': {}", file_path, e);
            exit(1);
        }
    };

    let mut lexer = lexer::Lexer::new(&source);
    let program = match lexer.tokenize() {
        Ok(tokens) => {
            let mut parser = parser::Parser::new(tokens);
            parser.parse_program().ok()
        }
        Err(_) => None,
    };

    let issues = linter::Linter::lint_source(&source, program.as_ref());

    println!("Checking '{}' for Spec code standards...", file_path);
    let mut warnings = 0;
    let mut notices = 0;

    for issue in &issues {
        if issue.is_warning {
            warnings += 1;
            println!("  [Warning] Line {}: {}", issue.line, issue.message);
        } else {
            notices += 1;
            if issue.line > 0 {
                println!("  [Notice]  Line {}: {}", issue.line, issue.message);
            } else {
                println!("  [Notice]  {}", issue.message);
            }
        }
    }

    println!("\nLint summary for {}: {} warning(s), {} notice(s).", file_path, warnings, notices);
    if warnings > 0 {
        exit(1);
    } else {
        println!("All standard checks passed successfully.");
        exit(0);
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut input_file: Option<String> = None;
    let mut output_file: Option<String> = None;
    let mut lint_mode = false;
    let mut lint_target: Option<String> = None;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--lint" | "-l" | "lint" => {
                lint_mode = true;
                if i + 1 < args.len() && !args[i + 1].starts_with('-') {
                    lint_target = Some(args[i + 1].clone());
                    i += 1;
                }
            }
            "-i" => {
                if i + 1 < args.len() {
                    input_file = Some(args[i + 1].clone());
                    i += 1;
                } else {
                    eprintln!("Error: -i requires an argument");
                    exit(1);
                }
            }
            "-o" => {
                if i + 1 < args.len() {
                    output_file = Some(args[i + 1].clone());
                    i += 1;
                } else {
                    eprintln!("Error: -o requires an argument");
                    exit(1);
                }
            }
            "-h" | "--help" => {
                print_usage();
                exit(0);
            }
            other => {
                if !other.starts_with('-') && lint_mode && lint_target.is_none() {
                    lint_target = Some(other.to_string());
                } else {
                    eprintln!("Unknown argument: {}", other);
                    print_usage();
                    exit(1);
                }
            }
        }
        i += 1;
    }

    if lint_mode {
        let target = lint_target.or(input_file).unwrap_or_else(|| {
            eprintln!("Error: Missing file to lint");
            print_usage();
            exit(1);
        });
        run_linter(&target);
        return;
    }

    let input_path = match input_file {
        Some(f) => f,
        None => {
            eprintln!("Error: Missing input file (-i)");
            print_usage();
            exit(1);
        }
    };

    let output_path = match output_file {
        Some(f) => f,
        None => {
            eprintln!("Error: Missing output file (-o)");
            print_usage();
            exit(1);
        }
    };

    // 1. Lex and Parse with multi-file module loader
    let mut loader = loader::ModuleLoader::new(std::path::Path::new(&input_path));
    let program = match loader.load_program(std::path::Path::new(&input_path)) {
        Ok(prog) => prog,
        Err(e) => {
            eprintln!("Compilation error: {}", e);
            exit(1);
        }
    };

    // 3. Generate C code
    let mut codegen = codegen::CodeGenerator::new();
    let c_code = match codegen.generate(&program) {
        Ok(code) => code,
        Err(e) => {
            eprintln!("Codegen error: {}", e);
            exit(1);
        }
    };

    // 4. Write C code to temporary file
    let c_path = format!("{}.c", output_path);
    if let Err(e) = fs::write(&c_path, &c_code) {
        eprintln!("Error writing intermediate C file '{}': {}", c_path, e);
        exit(1);
    }

    // 5. Compile with GCC
    let status = Command::new("gcc")
        .arg("-O2")
        .arg(&c_path)
        .arg("-o")
        .arg(&output_path)
        .arg("-pthread")
        .arg("-lm")
        .status();

    match status {
        Ok(s) if s.success() => {
            // Compilation succeeded! Clean up intermediate .c file
            let _ = fs::remove_file(&c_path);
        }
        Ok(s) => {
            eprintln!("gcc exited with status: {}", s);
            exit(1);
        }
        Err(e) => {
            eprintln!("Failed to execute gcc: {}", e);
            exit(1);
        }
    }
}
