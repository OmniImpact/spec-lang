#! Package base:compiler:parser
#! The fancy-family escape table, applied by both template consumers
#! ([FancyEscapeLoop] for hole-free content and [TemplateSplitLoop] for
#! literal chunks): given the character following a backslash, return its
#! expansion. Unknown escapes pass the escaped character through.

Class is TemplateEscapes{
	namespace: ['base', 'compiler', 'parser'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	## Expands one escaped character.
	##
	## @param escaped: The character after the backslash.
	## @return: Its expansion.
	Function of String is expand(String is escaped){
		return Conditional:match(on: escaped, when: [
			'n': { "\n" },
			't': { "\t" },
			'r': { "\r" },
			'e': { String:fromCharCode(code: 27) },
			'"': { "\"" },
			"\\": { "\\" },
			'`': { "`" },
			'{': { "{" },
			else: { escaped }
		]);
	}
}
