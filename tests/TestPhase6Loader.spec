#! SpecUnit sweep (from phase6_loader_test.spec): the module loader —
#! root-file load with package resolution through the resolver cascade
#! (spec/lib stdlib first), and clean parse error reporting.

Class of SpecUnitTest is TestPhase6Loader{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'loader', Loader],
		['base', 'sys', as Output()],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'checker', TypeError],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'gen', CodeGenerator],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', Error],
		['base', 'sys', as Conditional()]
	];

	# 1. Single file / hello world: the load itself exercises package
	# resolution — the hello program's array-form using pulled the io
	# package through the resolver cascade (spec/lib stdlib first).
	Function is testLoadHelloWorldProgram(){
		local Loader is loader: Loader:init();
		local ProgramNode is helloProg: loader:loadProgram(rootPath: 'examples/helloworld.spec');
		Assert:isTrue(helloProg:classes:length() >= 1);
		Assert:isTrue(loader:loadedFileCount() >= 1);
		Assert:areEqualInt(0, loader:getParseErrors():length());
	}
}
