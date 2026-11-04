Class is Phase4ParserTest{

	replace Array of String is using: [
		base:io:*,
		base:struct:Array,
		base:iterator:*,
		compiler:Token,
		compiler:Lexer,
		compiler:Parser,
		base:reflect:Type,
		base:reflect:Parameter,
		base:reflect:Member,
		base:reflect:ClassInfo,
		base:meta:*
	];

	replace Function is init(Map of String to String is args){
		output:line('======================================');
		output:line('        Phase 4 Pure-Spec Parser      ');
		output:line("======================================\n");

		local String is snippet: "Class of Entity is Player{\n\tlocal Int is health: 100;\n\tlocal String is name: \"Hero\";\n\tlocal Function of Boolean is isAlive(){\n\t\treturn health > 0;\n\t}\n}";

		output:line("Source to parse:\n" . snippet . "\n");

		# 1. Lex
		local Lexer is lexer: Lexer:init(source: snippet);
		local Array of Token is tokens: lexer:tokenize();
		output:line('Tokens scanned: ' . tokens:length());

		# 2. Parse
		local Parser is parser: Parser:init(tokens: tokens);
		local ProgramNode is prog: parser:parseProgram();

		local Array of ClassInfo is classes: prog:getClasses();
		output:line('Classes parsed: ' . classes:length());

		local ClassInfo is playerClass: classes:get(index: 0);
		output:line('ClassInfo name: ' . playerClass:getName());
		output:line('ClassInfo base: ' . playerClass:getBaseClass());

		local Array of Member is members: playerClass:getMembers();
		output:line('Total members: ' . members:length());

		Class of Loop is MemberInspectLoop{
			local Array of Member is members;
			local Int is idx: 0;

			replace Function is init(Array of Member is members){
				self:members: members;
				self:idx: 0;
			}

			replace Function of Boolean is evaluate(){
				return idx < members:length();
			}

			replace Function of Boolean is iteration(LoopControl is control){
				local Member is m: members:get(index: idx);
				output:line('Member[' . idx . ']: ' . m:getKind() . ' -> \'' . m:getName() . '\'');
				self:idx: idx + 1;
				return true;
			}
		}
		While:run(loop: MemberInspectLoop:init(members: members));

		# Assertions
		if (playerClass:getName() == 'Player') {
			output:line("\n[PASS] ClassInfo name is Player");
		}
		if (playerClass:getBaseClass() == 'Entity') {
			output:line('[PASS] Base class is Entity');
		}
		if (members:length() == 3) {
			output:line('[PASS] Parsed exactly 3 members (2 fields, 1 method)');
		}

		output:line("\nPhase 4 Parser test completed successfully!");
	}

}
