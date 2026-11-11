#! Package base:struct
#! Contiguous dynamic collections and associative hash maps.

## An associative key-value map with string keys.
##
## Runtime-managed: instances are the runtime's
## SpecMap objects (64-bucket FNV-1a hash); this declaration is the API
## surface. Values are stored either as refcounted strings or in the any
## slot, per the value's type; the typed getters read the matching slot.

Class is Map of K to V{
	namespace: ['base', 'struct'];

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
];

	## Looks up the value mapped to [key], returning [default] if not found.
	##
	## @param key: Lookup key string.
	## @param default: Fallback value returned if key is absent.
	## @return: Mapped value, or [default].
	## @fallback: Returns [default] when [key] does not exist in the map.
	Function of V is get(String is key, Any is default){
	}

	## Looks up a string value by key, returning [default] if not found.
	##
	## @param key: Lookup key string.
	## @param default: Fallback string returned if key is absent.
	## @return: Mapped value, or [default].
	## @fallback: Returns [default] when [key] does not exist in the map.
	Function of String is getString(String is key, String is default){
	}

	## Looks up an integer value by key, returning [default] if not found.
	##
	## @param key: Lookup key string.
	## @param default: Fallback integer returned if key is absent.
	## @return: Mapped value, or [default].
	Function of Int is getInt(String is key, Int is default){
		local String is s: self:getString(key: key, default: '');
		if({ s:length() > 0 }, {
			return s:parseInt(base: 10, default: default);
		});
		return default;
	}

	## Looks up a float value by key, returning [default] if not found.
	##
	## @param key: Lookup key string.
	## @param default: Fallback float returned if key is absent.
	## @return: Mapped value, or [default].
	Function of Float is getFloat(String is key, Float is default){
	}

	## Looks up a boolean value by key, returning [default] if not found.
	##
	## @param key: Lookup key string.
	## @param default: Fallback boolean returned if key is absent.
	## @return: Mapped value, or [default].
	Function of Boolean is getBool(String is key, Boolean is default){
		local String is s: self:getString(key: key, default: '');
		return match(on: s, when: [
			'true': { true },
			'false': { false },
			else: { default }
		]);
	}

	## Inserts or updates an entry in the map.
	##
	## @param key: Entry key string.
	## @param value: Entry value.
	Function is set(String is key, Any is value){
	}

	## Determines whether an entry exists for the specified key.
	##
	## @param key: Key to test.
	## @return: `true` if key is present, `false` otherwise.
	Function of Boolean is has(String is key){
	}

	## Removes the entry associated with [key].
	##
	## @param key: Key to remove.
	## @return: `true` if removed, `false` if key was not present.
	Function of Boolean is remove(String is key){
	}

	## Returns an array containing all keys currently present in the map.
	##
	## @return: [Array] of key strings.
	Function of Array of String is keys(){
	}

	## Returns the total number of entries in the map.
	##
	## @return: Entry count.
	Function of Int is length(){
	}

	## Iterates through each key-value pair, invoking [action] with (key, value).
	##
	## @param action: Function invoked with (key, value) for each entry.
	Function is each(Function is action){
	}
}
