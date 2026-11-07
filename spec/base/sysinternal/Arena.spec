#! Package base:sysinternal
#! The compilation arena: bump allocation with wholesale drain.
##
## O(1) per allocation, no per-object header, no fragmentation. Objects
## allocated in an arena are never individually released — the whole
## arena drains at once. Arena-owned objects must not outlive their
## arena or be stored in ARC-owned structures.

Class is Arena{
	namespace: ['base', 'sysinternal'];

	## Creates an empty arena.
	##
	## @return: The new arena.
	Function of Arena is arenaNew();

	## Bump-allocates [size] bytes (zero-initialized, 16-byte aligned).
	##
	## @param arena: The arena.
	## @param size: Byte count.
	## @return: The allocated block.
	Function of String is arenaAlloc(Arena is arena, Int is size);

	## Frees every block the arena handed out and resets it to empty.
	##
	## @param arena: The arena.
	Function is arenaDrain(Arena is arena);

	## Bytes currently handed out by the arena (introspection).
	##
	## @param arena: The arena.
	## @return: The live byte count.
	Function of Int is arenaUsed(Arena is arena);

	## Activates the process object arena: container and string
	## allocations route to the arena from this point. The compiler's
	## driver calls this in init; user programs never do and stay ARC.
	Function is activateProcessArena();
}
