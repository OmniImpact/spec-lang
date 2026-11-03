#! Package examples:regression
#! Tracks load-time class grouping (partial classes) via the `group` pseudo-field.

## NEGATIVE test: this file MUST FAIL TO LOAD. That is its correct behavior.
##
## Guarded behavior: two fragments declaring the same member in one group is
## a LoadError that names the conflicting member and both source files.
## Duplicate members must never be silently merged or overridden.
##
## Required diagnostic:
## - LoadError: Duplicate member 'value' in class 'Merged'.
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains the duplicate-member LoadError.

Class is DupSource{

	replace local Array of String is group: [Merged];

	replace local Function of Int is value(){
		return 1;
	}
}

Class is DupConflict{

	replace local Array of String is group: [Merged];

	replace local Function of Int is value(){
		return 2;
	}
}

Class is Merged{

}
