#! specunit: suite

#! Entry-selection regression: an entry with no OWN init whose effective
#! init is inherited from an imported package is constructed through the
#! OWNER's C symbol with the owner's arity — ChildApp_new() allocates,
#! BaseApp_init(app, args) constructs. Inherited inits are not flattened
#! into the child, so calling ChildApp_init would hit the empty
#! synthesized stub and silently skip the base construction.

Class of BaseApp is ChildApp{
	replace Array of Array of String is using: [
		['entrybase', BaseApp]
	];
}
