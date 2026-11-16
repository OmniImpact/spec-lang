#! Package base:struct
#! Contiguous dynamic collections and associative hash maps.

## An associative key-value map.
##
## Runtime-managed: instances are the runtime's
## SpecMap objects (8-bucket growing hash table); this declaration is the API
## surface. Values are stored either as refcounted strings or in the any
## slot, per the value's type; the typed getters read the matching slot.

Class is Map of K to V{
	namespace: ['base', 'struct'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as HashTable()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Looks up the value mapped to [key], returning [default] if not found.
	##
	## @param key: Lookup key string.
	## @param default: Fallback value returned if key is absent.
	## @return: Mapped value, or [default].
	## @fallback: Returns [default] when [key] does not exist in the map.
	Function of V is get(K is key, Any is default){
	}

	## Looks up a string value by key, returning [default] if not found.
	##
	## @param key: Lookup key.
	## @param default: Fallback string returned if key is absent.
	## @return: Mapped value, or [default].
	## @fallback: Returns [default] when [key] does not exist in the map.
	Function of String is getString(K is key, String is default){
	}

	## Looks up an integer value by key, returning [default] if not found.
	##
	## @param key: Lookup key.
	## @param default: Fallback integer returned if key is absent.
	## @return: Mapped value, or [default].
	Function of Int is getInt(K is key, Int is default){
		local String is s: self:getString(key: key, default: '');
		if({ s:length() > 0 }, {
			return s:parseInt(base: 10, default: default);
		});
		return default;
	}

	## Looks up a float value by key, returning [default] if not found.
	##
	## @param key: Lookup key.
	## @param default: Fallback float returned if key is absent.
	## @return: Mapped value, or [default].
	Function of Float is getFloat(K is key, Float is default){
	}

	## Looks up a boolean value by key, returning [default] if not found.
	##
	## @param key: Lookup key.
	## @param default: Fallback boolean returned if key is absent.
	## @return: Mapped value, or [default].
	Function of Boolean is getBool(K is key, Boolean is default){
		local String is s: self:getString(key: key, default: '');
		return match(on: s, when: [
			'true': { true },
			'false': { false },
			else: { default }
		]);
	}

	## Inserts or updates an entry in the map.
	##
	## @param key: Entry key.
	## @param value: Entry value.
	Function is set(K is key, Any is value){
	}

	## Determines whether an entry exists for the specified key.
	##
	## @param key: Key to test.
	## @return: `true` if key is present, `false` otherwise.
	Function of Boolean is has(K is key){
	}

	## Removes the entry associated with [key].
	##
	## @param key: Key to remove.
	## @return: `true` if removed, `false` if key was not present.
	Function of Boolean is remove(K is key){
	}

	## Returns an array containing all keys currently present in the map.
	##
	## @return: [Array] of keys.
	Function of Array of K is keys(){
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

	## Returns whether the map contains zero entries.
	##
	## @return: `true` if empty, `false` otherwise.
	Function of Boolean is isEmpty(){
		return self:length() == 0;
	}

	## Returns an array containing all values in key iteration order.
	##
	## @return: [Array] of values.
	Function of Array is values(){
		local Array is out: [];
		self:each(action: local Function(K is k, Any is v){
			out:add(item: v);
		});
		return out;
	}

	## Removes all entries from the map.
	Function is clear(){
		local Array of K is ks: self:keys();
		ks:each(action: local Function(K is k){
			self:remove(key: k);
		});
	}

	## Copies all entries from [other] into this map, overwriting matching keys.
	##
	## @param other: Source map to merge in.
	Function is merge(Map of K to V is other){
		local Array of K is ks: other:keys();
		ks:each(action: local Function(K is k){
			local String is sv: other:getString(key: k, default: '');
			if({ sv != '' }, {
				self:set(key: k, value: sv);
			}, {
				self:set(key: k, value: other:get(key: k, default: ''));
			});
		});
	}

	## Returns a new map containing entries for which [predicate](key, value) returns `true`.
	##
	## @param predicate: Function taking (key, value) and returning `Boolean`.
	## @return: Filtered [Map].
	Function of Map is filter(Function of Boolean is predicate){
		local Map is out: [:];
		self:each(action: local Function(K is k, Any is v){
			if({ predicate(k, v) }, {
				out:set(key: k, value: v);
			});
		});
		return out;
	}

	## Returns `true` if any entry satisfies [predicate](key, value).
	##
	## @param predicate: Function taking (key, value) and returning `Boolean`.
	## @return: `true` if any entry matches.
	Function of Boolean is any(Function of Boolean is predicate){
		local Boolean is found: false;
		self:each(action: local Function(K is k, Any is v){
			if({ !found && predicate(k, v) }, {
				found: true;
			});
		});
		return found;
	}

	## Counts entries for which [predicate](key, value) returns `true`.
	##
	## @param predicate: Function taking (key, value) and returning `Boolean`.
	## @return: Count of matching entries.
	Function of Int is count(Function of Boolean is predicate){
		local Int is total: 0;
		self:each(action: local Function(K is k, Any is v){
			if({ predicate(k, v) }, {
				total: total + 1;
			});
		});
		return total;
	}
}
