#! Package base:compiler
#! The well-known names of the language: builtin type names and the
#! parser's sentinel markers.
##
## Centralized so passes reference intent (names:intName()) instead of
## scattering raw literals; a spelling change happens in exactly one
## place. Stateless utility: construct-and-call is the whole protocol.

Class is WellKnown{
	namespace: ['base', 'compiler'];

	## The Int builtin type name.
	Function of String is intName(){
		return 'Int';
	}

	## The Any builtin type name.
	Function of String is anyName(){
		return 'Any';
	}

	## The Void builtin type name.
	Function of String is voidName(){
		return 'Void';
	}

	## The Function builtin type name.
	Function of String is fnName(){
		return 'Function';
	}

	## The List builtin type name.
	Function of String is listName(){
		return 'List';
	}

	## The void spelling used for untyped method member types (the checker
	## and generator distinguish it from [voidName]; the split is fossil
	## legacy the new checker will normalize).
	Function of String is voidMemberType(){
		return 'void';
	}

	## The rejected legacy class-declaration spelling, recognized only to
	## produce its pointed diagnostic.
	Function of String is legacyClassSpelling(){
		return 'class';
	}

	## The receiver-field parameter marker type name.
	Function of String is selfFieldMarker(){
		return 'SELF_FIELD';
	}

	## The implicit receiver identifier.
	Function of String is selfIdent(){
		return 'self';
	}

	## The root class every class declaration derives from.
	Function of String is classHeader(){
		return 'Class';
	}

	## The root class every enum declaration derives from.
	Function of String is enumHeader(){
		return 'Enum';
	}

	## The true-literal lexeme.
	Function of String is boolTrue(){
		return 'true';
	}

	## The wildcard lexeme (all-members path access).
	Function of String is wildcard(){
		return '*';
	}
}
