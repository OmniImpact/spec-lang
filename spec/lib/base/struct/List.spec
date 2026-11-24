#! Package base:struct
#! Lean growable sequence declared with [T] syntax. [Byte] is a compact byte buffer
#! (the string-builder floor); other element types use a pointer vector.

## A lean growable sequence declared with [T] syntax (e.g. [Byte], [String]).
##
## Fallible reads take a mandatory default: value used whenever there is no
## successful answer, plus an optional error: callback invoked in addition when
## a problem occurs. Bracket indexing is not provided on List; use get.
Class of Mergeable is List of T{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'core', Mergeable],
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Int is data: 0;
	local Int is len: 0;
	local Int is cap: 0;
	local Int is elemKind: 0;
	local Boolean is byteMode: false;

	replace Function is init(Boolean is byteMode: false, Int is elemKind: 0){
		:byteMode: byteMode;
		:elemKind: elemKind;
	}

	Function is destroy(){
		if({ :data != 0 }, {
			if({ !:byteMode && :elemKind == 1 }, {
				local Int is i: 0;
				while({ i < :len }, {
					local Int is it: Mem:loadI64(ptr: :data, byteOffset: i * 8);
					if({ it != 0 }, { Mem:releaseAddr(objAddr: it); });
					i: i + 1;
				});
			});
			Mem:free(ptr: :data);
			:data: 0;
		});
	}

	## Returns the raw backing buffer address (for low-level I/O bridges).
	Function of Int is rawDataAddr(){
		return :data;
	}

	## Returns whether this list stores packed 1-byte elements ([Byte]).
	Function of Boolean is isByteMode(){
		return :byteMode;
	}

	## Adopts a newly allocated raw byte buffer into this [List of Byte].
	Function is adoptRawBuffer(Int is dataPtr, Int is length, Int is capacity){
		if({ :data != 0 }, {
			Mem:free(ptr: :data);
		});
		:data: dataPtr;
		:len: length;
		:cap: capacity;
	}

	local Function is appendRawBytes(Int is srcAddr, Int is count){
		if({ count <= 0 || srcAddr == 0 }, { return; });
		if({ :len + count > :cap }, {
			local Int is ncap: if({ :cap == 0 }, { 16 }, { :cap });
			while({ ncap < :len + count }, { ncap: ncap * 2; });
			:data: Mem:realloc(ptr: :data, bytes: ncap);
			:cap: ncap;
		});
		Mem:copy(dst: :data + :len, src: srcAddr, bytes: count);
		:len: :len + count;
	}

	## Appends [item] to this list. Infallible: the backing buffer grows.
	Function is push(T is item){
		local Int is itemBits: Mem:objToAddr(obj: item);
		if({ :byteMode }, {
			if({ :len >= :cap }, {
				local Int is ncap: if({ :cap == 0 }, { 16 }, { :cap * 2 });
				:data: Mem:realloc(ptr: :data, bytes: ncap);
				:cap: ncap;
			});
			Mem:storeByte(ptr: :data, byteOffset: :len, val: itemBits);
			:len: :len + 1;
			return;
		});
		if({ :len >= :cap }, {
			local Int is ncap2: if({ :cap == 0 }, { 8 }, { :cap * 2 });
			:data: Mem:realloc(ptr: :data, bytes: ncap2 * 8);
			:cap: ncap2;
		});
		if({ :elemKind == 1 && itemBits != 0 }, {
			Mem:retainAddr(objAddr: itemBits);
		});
		Mem:storeI64(ptr: :data, byteOffset: :len * 8, val: itemBits);
		:len: :len + 1;
	}

	## Appends the bytes of [value] to a [Byte] buffer. Infallible: the buffer grows.
	Function is appendString(String is value){
		local Int is sAddr: Mem:objToAddr(obj: value);
		if({ sAddr == 0 }, { return; });
		local Int is n: Mem:loadI64(ptr: sAddr, byteOffset: 8);
		if({ n <= 0 }, { return; });
		local Int is sData: Mem:loadI64(ptr: sAddr, byteOffset: 0);
		:appendRawBytes(srcAddr: sData, count: n);
	}

	## Returns the element at [index], panicking if out of bounds.
	##
	## @param index: Zero-based position.
	Function of T is get(Int is index){
		if({ index < 0 || index >= :len }, {
			Mem:panic(msg: 'List index out of bounds: index ' . (index as String) . ' for length ' . (:len as String));
			return Mem:addrToObj(addr: 0);
		});
		if({ :byteMode }, {
			return Mem:addrToObj(addr: Mem:loadByte(ptr: :data, byteOffset: index));
		});
		local Int is valAddr: Mem:loadI64(ptr: :data, byteOffset: index * 8);
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:retainAddr(objAddr: valAddr);
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		return Mem:addrToObj(addr: valAddr);
	}

	## Overwrites the element at [index], panicking if out of bounds.
	Function is set(Int is index, T is item){
		if({ index < 0 || index >= :len }, {
			Mem:panic(msg: 'List assignment index out of bounds: index ' . (index as String) . ' for length ' . (:len as String));
			return;
		});
		local Int is itemBits: Mem:objToAddr(obj: item);
		if({ :byteMode }, {
			Mem:storeByte(ptr: :data, byteOffset: index, val: itemBits);
			return;
		});
		if({ :elemKind == 1 }, {
			if({ itemBits != 0 }, { Mem:retainAddr(objAddr: itemBits); });
			local Int is oldAddr: Mem:loadI64(ptr: :data, byteOffset: index * 8);
			if({ oldAddr != 0 }, { Mem:releaseAddr(objAddr: oldAddr); });
		});
		Mem:storeI64(ptr: :data, byteOffset: index * 8, val: itemBits);
	}

	## Removes and returns the last element, panicking if empty.
	Function of T is pop(){
		if({ :len == 0 }, {
			Mem:panic(msg: 'List pop on empty list');
			return Mem:addrToObj(addr: 0);
		});
		:len: :len - 1;
		if({ :byteMode }, {
			return Mem:addrToObj(addr: Mem:loadByte(ptr: :data, byteOffset: :len));
		});
		local Int is valAddr: Mem:loadI64(ptr: :data, byteOffset: :len * 8);
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		return Mem:addrToObj(addr: valAddr);
	}

	## Returns the number of elements.
	Function of Int is length(){
		return :len;
	}

	## Returns whether the list contains zero elements.
	Function of Boolean is isEmpty(){
		return :len == 0;
	}

	## Removes all elements. Capacity is retained for byte buffers.
	Function is clear(){
		if({ :byteMode }, {
			:len: 0;
			return;
		});
		local Int is oldData: :data;
		local Int is oldLen: :len;
		:data: 0;
		:len: 0;
		:cap: 0;
		if({ oldData != 0 }, {
			if({ :elemKind == 1 }, {
				local Int is i: 0;
				while({ i < oldLen }, {
					local Int is elem: Mem:loadI64(ptr: oldData, byteOffset: i * 8);
					if({ elem != 0 }, { Mem:releaseAddr(objAddr: elem); });
					i: i + 1;
				});
			});
			Mem:free(ptr: oldData);
		});
	}

	## Returns the buffered bytes as a string ([Byte] buffers only).
	replace Function of String is toString(){
		if({ :len <= 0 || :data == 0 }, { return ''; });
		return Mem:strFromBytes(srcAddr: :data, len: :len);
	}

	## Appends all bytes of [other] into this [Byte] buffer.
	Function is appendBytes(List of Byte is other){
		local Int is n: other:length();
		if({ n <= 0 }, { return; });
		local Int is oAddr: Mem:objToAddr(obj: other);
		if({ Mem:objToAddr(obj: :) == oAddr }, {
			if({ :len + n > :cap }, {
				local Int is ncap: if({ :cap == 0 }, { 16 }, { :cap });
				while({ ncap < :len + n }, { ncap: ncap * 2; });
				:data: Mem:realloc(ptr: :data, bytes: ncap);
				:cap: ncap;
			});
			Mem:move(dst: :data + :len, src: :data, bytes: n);
			:len: :len + n;
			return;
		});
		:appendRawBytes(srcAddr: other:rawDataAddr(), count: n);
	}

	## Appends [count] bytes starting at [start] from [other] into this [Byte] buffer.
	Function is appendRange(List of Byte is other, Int is start, Int is count){
		if({ count <= 0 }, { return; });
		local Int is oLen: other:length();
		local Int is s: if({ start < 0 }, { 0 }, { start });
		if({ s >= oLen }, { return; });
		local Int is n: if({ s + count > oLen }, { oLen - s }, { count });
		if({ n <= 0 }, { return; });
		local Int is oAddr: Mem:objToAddr(obj: other);
		if({ Mem:objToAddr(obj: :) == oAddr }, {
			if({ :len + n > :cap }, {
				local Int is ncap: if({ :cap == 0 }, { 16 }, { :cap });
				while({ ncap < :len + n }, { ncap: ncap * 2; });
				:data: Mem:realloc(ptr: :data, bytes: ncap);
				:cap: ncap;
			});
			Mem:move(dst: :data + :len, src: :data + s, bytes: n);
			:len: :len + n;
			return;
		});
		:appendRawBytes(srcAddr: other:rawDataAddr() + s, count: n);
	}

	## Returns a new [List of Byte] containing bytes [start..end).
	Function of List of Byte is slice(Int is start, Int is end){
		local [Byte] is out;
		local Int is s: if({ start < 0 }, { 0 }, { start });
		local Int is e: if({ end > :len }, { :len }, { end });
		if({ e > s && :data != 0 }, {
			out:appendRawBytes(srcAddr: :data + s, count: e - s);
		});
		return out;
	}

	## Appends a 16-bit big-endian unsigned integer.
	Function is pushU16BE(Int is v){
		:push(item: Mem:addrToObj(addr: (v >> 8) & 255));
		:push(item: Mem:addrToObj(addr: v & 255));
	}

	## Appends a 32-bit big-endian unsigned integer.
	Function is pushU32BE(Int is v){
		:push(item: Mem:addrToObj(addr: (v >> 24) & 255));
		:push(item: Mem:addrToObj(addr: (v >> 16) & 255));
		:push(item: Mem:addrToObj(addr: (v >> 8) & 255));
		:push(item: Mem:addrToObj(addr: v & 255));
	}

	## Appends a 32-bit little-endian unsigned integer.
	Function is pushU32LE(Int is v){
		:push(item: Mem:addrToObj(addr: v & 255));
		:push(item: Mem:addrToObj(addr: (v >> 8) & 255));
		:push(item: Mem:addrToObj(addr: (v >> 16) & 255));
		:push(item: Mem:addrToObj(addr: (v >> 24) & 255));
	}

	## Reads a 16-bit big-endian unsigned integer at [offset], or [default] if out of bounds.
	Function of Int is readU16BE(Int is offset, Int is default: 0){
		if({ offset < 0 || offset + 2 > :len || :data == 0 }, { return default; });
		local Int is b0: Mem:loadByte(ptr: :data, byteOffset: offset);
		local Int is b1: Mem:loadByte(ptr: :data, byteOffset: offset + 1);
		return (b0 << 8) | b1;
	}

	## Reads a 32-bit big-endian unsigned integer at [offset], or [default] if out of bounds.
	Function of Int is readU32BE(Int is offset, Int is default: 0){
		if({ offset < 0 || offset + 4 > :len || :data == 0 }, { return default; });
		local Int is b0: Mem:loadByte(ptr: :data, byteOffset: offset);
		local Int is b1: Mem:loadByte(ptr: :data, byteOffset: offset + 1);
		local Int is b2: Mem:loadByte(ptr: :data, byteOffset: offset + 2);
		local Int is b3: Mem:loadByte(ptr: :data, byteOffset: offset + 3);
		return ((b0 << 24) | (b1 << 16) | (b2 << 8) | b3) & 4294967295;
	}

	## Reads a 32-bit little-endian unsigned integer at [offset], or [default] if out of bounds.
	Function of Int is readU32LE(Int is offset, Int is default: 0){
		if({ offset < 0 || offset + 4 > :len || :data == 0 }, { return default; });
		local Int is b0: Mem:loadByte(ptr: :data, byteOffset: offset);
		local Int is b1: Mem:loadByte(ptr: :data, byteOffset: offset + 1);
		local Int is b2: Mem:loadByte(ptr: :data, byteOffset: offset + 2);
		local Int is b3: Mem:loadByte(ptr: :data, byteOffset: offset + 3);
		return (b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)) & 4294967295;
	}

	## Merges all elements of [other] into this list (appending in order).
	##
	## @param other: Source list to append.
	replace Function is merge(List of T is other){
		local Int is n: other:length();
		if({ n <= 0 }, { return; });
		if({ :byteMode }, {
			local Int is oAddr: Mem:objToAddr(obj: other);
			if({ Mem:objToAddr(obj: :) == oAddr }, {
				if({ :len + n > :cap }, {
					local Int is ncap: if({ :cap == 0 }, { 16 }, { :cap });
					while({ ncap < :len + n }, { ncap: ncap * 2; });
					:data: Mem:realloc(ptr: :data, bytes: ncap);
					:cap: ncap;
				});
				Mem:move(dst: :data + :len, src: :data, bytes: n);
				:len: :len + n;
				return;
			});
			:appendRawBytes(srcAddr: other:rawDataAddr(), count: n);
			return;
		});
		local Int is i: 0;
		while({ i < n }, {
			local Int is bits: Mem:loadI64(ptr: other:rawDataAddr(), byteOffset: i * 8);
			:push(item: Mem:addrToObj(addr: bits));
			i: i + 1;
		});
	}

}
