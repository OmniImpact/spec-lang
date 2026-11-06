#! Package base:compiler
#! The error-message wordings shared by compiler passes.
##
## Base class so every pass that reports diagnostics inherits one cohesive,
## template-built vocabulary (multiple inheritance per the style contract):
## wording changes happen in exactly one place.

Class is ErrorText{
	replace Array of String is namespace: ['base', 'compiler'];

	## Message for a heredoc whose closing delimiter never appears.
	##
	## @param quote: The three-character delimiter that was expected.
	## @return: Diagnostic wording.
	Function of String is errUnterminatedHeredoc(String is quote){
		return 'Unterminated heredoc (missing closing {{quote}})';
	}

	## Message for a digit that does not belong to the literal's base.
	##
	## @param base: The literal's numeric base.
	## @return: Diagnostic wording.
	Function of String is errInvalidDigitInBase(Int is base){
		return 'Invalid digit in base-{{base}} number literal';
	}

	## Message for a base-prefixed literal with no digits after the prefix.
	##
	## @return: Diagnostic wording.
	Function of String is errMissingDigitsAfterPrefix(){
		return 'Missing digits after base prefix';
	}
}
