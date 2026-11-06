#! Package base:compiler:parser
#! The fancy-family escape table, applied by both template consumers
#! ([FancyEscapeLoop] for hole-free content and [TemplateSplitLoop] for
#! literal chunks): given the character following a backslash, return its
#! expansion. Unknown escapes pass the escaped character through.

Class is TemplateEscapes{
	namespace: ['base', 'compiler', 'parser'];

	## Expands one escaped character.
	##
	## @param escaped: The character after the backslash.
	## @return: Its expansion.
	Function of String is expand(String is escaped){
		when (escaped) {
			is 'n': { return "\n"; }
			is 't': { return "\t"; }
			is 'r': { return "\r"; }
			is 'e': { return String:fromCharCode(code: 27); }
			is '"': { return "\""; }
			is "\\": { return "\\"; }
			is '`': { return "`"; }
			is '{': { return "{"; }
			else: { return escaped; }
		}
	}
}
