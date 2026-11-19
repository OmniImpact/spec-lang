#! Package base:compiler:pal
#! Composes the standalone C runtime source (`spec_runtime.c`) from the real
#! C files in `spec/runtime/` (no embedded C heredocs).

Class is RuntimePrelude{
	namespace: ['base', 'compiler', 'pal'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as File()],
		['base', 'sys', as Dir()]
	];

	local Function of String is resolveRuntimeDir(){
		if({ fileExists(path: 'spec/runtime/pal_headers.h') }, {
			return 'spec/runtime';
		});
		local String is exeDir: Dir:exeDir();
		if({ exeDir != '' }, {
			local String is sibling: exeDir . '/../spec/runtime';
			if({ fileExists(path: sibling . '/pal_headers.h') }, {
				return sibling;
			});
			local String is localSub: exeDir . '/spec/runtime';
			if({ fileExists(path: localSub . '/pal_headers.h') }, {
				return localSub;
			});
		});
		return '';
	}

	local Function of String is readPart(String is dir, String is name){
		return fileRead(path: dir . '/' . name, default: '');
	}

	Function of String is emitHeader(){
		local String is dir: :resolveRuntimeDir();
		if({ dir == '' }, { return ''; });
		return :readPart(dir: dir, name: 'pal_headers.h');
	}

	Function of String is emitBody(){
		local String is dir: :resolveRuntimeDir();
		if({ dir == '' }, { return ''; });
		local Array of String is parts: [
			'pal_core.c',
			'pal_dir.c',
			'pal_file.c',
			'pal_process.c',
			'pal_time.c',
			'pal_console.c',
			'pal_socket.c',
			'pal_audio.c'
		];
		local Array of String is chunks: [];
		local Int is i: 0;
		while({ i < parts:length() }, {
			chunks:add(item: :readPart(dir: dir, name: parts:get(index: i)));
			i: i + 1;
		});
		return chunks:join(sep: '');
	}

	Function of String is emitRuntime(){
		local String is dir: :resolveRuntimeDir();
		if({ dir != '' }, {
			return :emitHeader() . "\n" . :emitBody();
		});
		if({ fileExists(path: 'bootstrap/spec_runtime.c') }, {
			return fileRead(path: 'bootstrap/spec_runtime.c', default: '');
		});
		local String is exeDir: Dir:exeDir();
		if({ exeDir != '' && fileExists(path: exeDir . '/../bootstrap/spec_runtime.c') }, {
			return fileRead(path: exeDir . '/../bootstrap/spec_runtime.c', default: '');
		});
		return '';
	}
}
