#! specunit: negative
#! expect: Cannot instance-import enum 'ExpressionKind'

#! N8: as-import of an enum (E2).

Class is N8EnumImport {
	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', as ExpressionKind()]
	];
	replace Function is init(Map of String to String is args) {}
}
