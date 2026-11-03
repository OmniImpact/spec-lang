use crate::ast::*;
use crate::lexer::Lexer;
use crate::parser::Parser;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

pub struct ModuleLoader {
    loaded_files: HashSet<PathBuf>,
    search_paths: Vec<PathBuf>,
}

impl ModuleLoader {
    pub fn new(input_file: &Path) -> Self {
        let mut search_paths = Vec::new();

        // 1. Directory of the input file
        if let Some(parent) = input_file.parent() {
            if parent.as_os_str().is_empty() {
                search_paths.push(PathBuf::from("."));
            } else {
                search_paths.push(parent.to_path_buf());
            }
        }

        // 2. Standard library in workspace root: "lib"
        search_paths.push(PathBuf::from("lib"));

        // 3. Current working directory
        search_paths.push(PathBuf::from("."));

        Self {
            loaded_files: HashSet::new(),
            search_paths,
        }
    }

    pub fn load_program(&mut self, root_path: &Path) -> Result<Program, String> {
        let canonical_root = fs::canonicalize(root_path)
            .map_err(|e| format!("Error canonicalizing '{}': {}", root_path.display(), e))?;
        self.loaded_files.insert(canonical_root);

        let source = fs::read_to_string(root_path)
            .map_err(|e| format!("Error reading '{}': {}", root_path.display(), e))?;

        let mut lexer = Lexer::new(&source);
        let tokens = lexer
            .tokenize()
            .map_err(|e| format!("Lexer error in '{}': {}", root_path.display(), e))?;

        let mut parser = Parser::new(tokens);
        let mut root_program = parser
            .parse_program()
            .map_err(|e| format!("Parser error in '{}': {}", root_path.display(), e))?;

        let mut all_classes = Vec::new();
        let mut seen_class_names = HashSet::new();
        let mut all_enums = Vec::new();
        let mut seen_enum_names = HashSet::new();

        for e in &root_program.enums {
            seen_enum_names.insert(e.name.clone());
            all_enums.push(e.clone());
        }

        // Root entry classes first
        for c in &root_program.classes {
            seen_class_names.insert(c.name.clone());
            all_classes.push(c.clone());
        }

        // Collect all 'using' import paths from root classes
        let mut pending_imports = Vec::new();
        for c in &root_program.classes {
            self.collect_imports(c, &mut pending_imports);
        }

        // Iteratively resolve imports
        while let Some(import_path) = pending_imports.pop() {
            let files = self.resolve_import(&import_path)?;
            for file in files {
                let canonical = match fs::canonicalize(&file) {
                    Ok(c) => c,
                    Err(_) => continue,
                };
                if self.loaded_files.insert(canonical) {
                    let dep_src = fs::read_to_string(&file)
                        .map_err(|e| format!("Error reading module '{}': {}", file.display(), e))?;
                    let mut dep_lex = Lexer::new(&dep_src);
                    let dep_toks = dep_lex
                        .tokenize()
                        .map_err(|e| format!("Lexer error in '{}': {}", file.display(), e))?;
                    let mut dep_parser = Parser::new(dep_toks);
                    let dep_prog = dep_parser
                        .parse_program()
                        .map_err(|e| format!("Parser error in '{}': {}", file.display(), e))?;

                    for dep_c in &dep_prog.classes {
                        if seen_class_names.insert(dep_c.name.clone()) {
                            all_classes.push(dep_c.clone());
                        }
                        self.collect_imports(dep_c, &mut pending_imports);
                    }
                    for dep_e in &dep_prog.enums {
                        if seen_enum_names.insert(dep_e.name.clone()) {
                            all_enums.push(dep_e.clone());
                        }
                    }
                }
            }
        }

        root_program.classes = all_classes;
        root_program.enums = all_enums;
        Ok(root_program)
    }

    fn collect_imports(&self, class_def: &ClassDef, acc: &mut Vec<Vec<String>>) {
        for m in &class_def.members {
            if let Member::Field { name, init, .. } = m {
                if name == "using" {
                    if let Some(Expression::ArrayLiteral(items)) = init {
                        for item in items {
                            match item {
                                Expression::Path(segments) => acc.push(segments.clone()),
                                Expression::Identifier(id) => acc.push(vec![id.clone()]),
                                _ => {}
                            }
                        }
                    }
                }
            }
        }
    }

    fn resolve_import(&self, segments: &[String]) -> Result<Vec<PathBuf>, String> {
        let is_wildcard = segments.last().map(|s| s.as_str()) == Some("*");
        let mut results = Vec::new();

        if is_wildcard {
            let rel_dir = segments[..segments.len() - 1].join("/");
            for base in &self.search_paths {
                let candidate = base.join(&rel_dir);
                if candidate.is_dir() {
                    if let Ok(entries) = fs::read_dir(&candidate) {
                        let mut dir_files = Vec::new();
                        for entry in entries.flatten() {
                            let p = entry.path();
                            if p.is_file() && p.extension().map_or(false, |ext| ext == "spec") {
                                dir_files.push(p);
                            }
                        }
                        dir_files.sort();
                        results.extend(dir_files);
                    }
                }
            }
        } else {
            let rel_file = format!("{}.spec", segments.join("/"));
            for base in &self.search_paths {
                let candidate = base.join(&rel_file);
                if candidate.is_file() {
                    results.push(candidate);
                    break;
                }
            }
        }

        Ok(results)
    }
}
