#! Package speclint
#! One diagnostic produced by the Linter: a line, a severity, a message.

## Represents an issue or diagnostic notice detected by the Spec linter.
Class is LintIssue{
	replace [String] is namespace: ['speclint'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];

	## One-based line number where the issue was found (0 if general).
	Int is line: 0;

	## `true` if this is a standard violation warning, `false` for informational notices.
	Boolean is isWarning: false;

	## Informational description of the issue.
	String is message: '';

	## Initializes a lint issue.
	replace Function is init(Int is line, Boolean is isWarning, String is message){
		:line: line;
		:isWarning: isWarning;
		:message: message;
	}

	## Returns whether this issue is a warning.
	##
	## @return: `true` if warning, `false` if notice.
	Function of Boolean is getIsWarning(){
		return :isWarning;
	}

	## Formats the issue for terminal display.
	##
	## @return: Formatted display string.
	replace Function of String is toString(){
		local String is tag: if({ :isWarning }, { '[Warning]' }, { '[Notice] ' });
		local String is loc: if({ :line > 0 }, { 'Line ' . (:line as String) . ': ' }, { '' });
		return '  ' . tag . ' ' . loc . :message;
	}
}
