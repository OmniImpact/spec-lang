#! SpecUnit port (from entry_init_preference_test.spec): the entry-init
#! PREFERENCE — an argv-capable init wins over an empty init wherever
#! each sits on the lattice. The suite observes the entry through the
#! base's onEntry hook (fired only from the argv-Map init, before the
#! runner starts): if the preference broke and the empty init were
#! chosen, the hook would never fire and the flag below would stay
#! empty; if the entry machinery broke entirely, the suite would exit 0
#! with no report table — the runner's table gate fails that shape.
#! The preference is therefore locked from both directions. (The test
#! class cannot replace the base's overloaded init itself — replacing
#! one overload of several is a compile error — so the hook is the
#! seam.)

Class of SpecUnitTest is TestEntryPreference{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	## Stamped by onEntry — the argv-Map form, proving main fed the
	## command-line Map to the argv-capable init and not the empty one.
	held Array of Boolean is argvEntrySeen: [];

	replace Function is onEntry(Map of String to String is args){
		TestEntryPreference:argvEntrySeen:add(item: true);
	}

	Function is testArgvMapEntryWon(){
		Assert:areEqualInt(1, TestEntryPreference:argvEntrySeen:length());
	}

	Function is testEntryRanBeforeTests(){
		# The base's own stamp: the inherited argv-Map init ran on the
		# lattice before any test executed.
		Assert:areEqualInt(1, SpecUnitTest:entryStamped:length());
	}
}
