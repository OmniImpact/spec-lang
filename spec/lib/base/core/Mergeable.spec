#! Package base:core
#! Contract for types whose instances can be merged (used by the `merge` field modifier).

## Contract supplying in-place merging of an incoming value onto `self`.
##
## Classes extending [Mergeable] (such as [List], [Array], [Map], or user
## configuration/value types) can be used with the `merge` field modifier in
## subclasses: the parent field initializer runs first, and the child's
## initializer is merged onto it via [merge].
Class is Mergeable{
	replace [String] is namespace: ['base', 'core'];

	## Merges [other] into this instance.
	##
	## @param other: The incoming value to merge onto this one.
	Function is merge(Any is other);
}
