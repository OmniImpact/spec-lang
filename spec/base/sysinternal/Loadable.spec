#! Package base:sysinternal
#! The loadable root: an Any that can be loaded — a class body's
#! machinery, as a contract.

## A Loadable is an Any that can be loaded: it carries a namespace,
## declares package dependencies, and can be constructed. The three
## machinery members every class body carries, as the concrete
## defaults — the loader consumes each by name:
##
## `namespace` — the canonical package declaration; the loader consumes
## it as the import-acceptance identity.
##
## `using` — the package dependencies; the loader resolves them and
## grants the imports (plain: type references; `as`: the function
## surface).
##
## `init` — the construction slot; every class declares how its
## instances are built, and the loader synthesizes an empty one when
## absent.

Class of Any is Loadable{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [];

	replace Array of String is namespace: [];

	replace Function is init(){
		return;
	}
}
