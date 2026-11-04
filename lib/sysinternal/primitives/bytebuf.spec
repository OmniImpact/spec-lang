#! Package sysinternal:primitives
#! The unified growable buffer: the C-level floor for all growable sequences.
#! This class is only accessible from sys: wrapper classes. It maps directly to
#! the SpecBuf C struct (elem_size=1 for byte buffers, elem_size=8 for pointer slots).
#! Methods are declarations only — the compiler generates the C implementations.

## Growable buffer. Internal representation for String and binary data.
##
## All operations are O(1) amortized (append) or O(1) (indexed access).
## Not thread-safe: each buffer is owned by a single scope or container.
## elem_size determines the storage layout:
##   1 = contiguous bytes (the string builder floor)
##   8 = pointer slots (objects, strings, primitives-as-intptr)
## elem_kind determines element ownership:
##   0 = none (raw values)
##   1 = object (ARC-managed, retain/release)
##   2 = string (owned copy, strdup/free)
Class is ByteBuf

	Function is init()

	Function is push(Byte is b)

	Function is append(ByteBuf is other)

	Function of Byte is get(Int is index, Byte is default, Function is error)

	Function is set(Int is index, Byte is b, Function is error)

	Function of Byte is pop(Byte is default, Function is error)

	Function of Int is length()

	Function is clear()

	Function of String is toCString()

