#! Package specunit
#! The SpecUnit test base class — discovery by inheritance, not by name.
#! A suite's test class extends this base (`Class of SpecUnitTest is
#! TestByte`); the runner discovers every registered class whose lattice
#! contains the base, so nothing outside the framework's hierarchy is
#! ever executed (see KNOWLEDGE-SPECDEV.md §4a).
#!
#! The base is also the suite ENTRY: the argv-Map init the generated
#! main prefers constructs the runner and runs this file's test classes,
#! so a suite compiles with plain `spec` — there is no compiler test
#! mode. The companion empty init keeps test classes instantiate-able
#! (the runner's per-test fresh instance). Declaration order matters:
#! the argv-Map init must come first so it owns overload index 0, and
#! the entry resolver's argv-preference then selects exactly it.
#!
#! The base provides overridable members returning the test identity:
#! - name: the instance's own class name (via the reflection registry).
#! - description: "Unit test: <name> has <n> tests", where <n> is the
#!   class's test-method count (methods starting with `test`, own plus
#!   inherited).
#! Subclasses override with the standard `replace` discipline.

Class is SpecUnitTest{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitRunner],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Conditional()]
	];

	## Stamped by the argv-Map entry init before any test runs (held
	## arrays are the sanctioned mutable held shape — the reference is
	## immutable, the contents are not): proof the entry constructed
	## through the INHERITED base init at the owner's symbol (the
	## entry-init emission contract, locked by TestEntryInheritedInit).
	held Array of Boolean is entryStamped: [];

	## The entry hook: the argv-Map entry init calls it before the
	## runner starts. Suites replace it (single signature — the
	## overloaded init itself cannot be replaced) to observe entry
	## selection; the default is inert. See TestEntryPreference.
	Function is onEntry(Map of String to String is args){
	}

	## The suite entry: the generated main prefers an init that takes
	## the command-line argv Map, so a suite binary's main constructs
	## the root test class and lands here — stamp the entry contract,
	## fire the hook, hand off to the runner.
	replace Function is init(Map of String to String is args){
		SpecUnitTest:entryStamped:add(item: true);
		self:onEntry(args: args);
		self:runTests();
	}

	## The runner invocation: discover and run this file's test
	## classes, scoped to the root file's basename. A suite that pins
	## entry-selection semantics replaces onEntry; runTests is the
	## framework hand-off any entry-side code can call.
	Function is runTests(){
		local String is cn: Introspection:typeIdentity(obj: self);
		local String is src: Introspection:classSourceFile(className: cn);
		local SpecUnitRunner is runner: SpecUnitRunner:init();
		runner:runAll(sourcePrefix: self:sourceBase(path: src));
	}

	## The per-test construction path: the runner instantiates test
	## classes with no arguments (the xUnit fresh-instance rule).
	replace Function is init(){
	}

	## The test identity: the instance's own class name by default.
	## Deliberately NOT named test* — the runner discovers test methods
	## by the `test` prefix, and the base's identity members must stay
	## outside that namespace (methodNames includes inherited members).
	##
	## @return: The test name.
	Function of String is name(){
		return Introspection:typeIdentity(obj: self);
	}

	## The test description: "Unit test: <name> has <n> tests", where <n>
	## counts this class's test methods (own plus inherited).
	##
	## @return: The test description.
	Function of String is description(){
		return 'Unit test: ' . self:name() . ' has ' . (self:methodCount() as String) . ' tests';
	}

	## The number of test methods this class declares or inherits.
	##
	## @return: The test-method count.
	Function of Int is methodCount(){
		local Int is n: 0;
		Introspection:functions(className: self:name()):each(action: local Function(Array of String is path){
			Conditional:if(check: { path:get(index: 1):startsWith(prefix: 'test') }, then: {
				n: n + 1;
			});
		});
		return n;
	}

	## The source file's basename — the discovery prefix the runner
	## filters on (classSourceFile values begin with this basename).
	##
	## @param path: A source path.
	## @return: The basename, extension included.
	Function of String is sourceBase(String is path){
		local Array of String is segs: path:split(delimiter: '/');
		return segs:get(index: segs:length() - 1);
	}
}
