#! Package base:compiler:pal
#! Composes the per-domain C PAL emitters into the standalone C runtime source (`spec_runtime.c`).

Class is RuntimePrelude{
	namespace: ['base', 'compiler', 'pal'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'pal', PalCore],
		['base', 'compiler', 'pal', PalDir],
		['base', 'compiler', 'pal', PalFile],
		['base', 'compiler', 'pal', PalProcess],
		['base', 'compiler', 'pal', PalTime],
		['base', 'compiler', 'pal', PalConsole],
		['base', 'compiler', 'pal', PalSocket],
		['base', 'compiler', 'pal', PalAudio]
	];

	Function of String is emitHeader(){
		local PalCore is core: PalCore:init();
		local PalFile is file: PalFile:init();
		local PalProcess is proc: PalProcess:init();
		local PalSocket is sock: PalSocket:init();
		local PalAudio is audio: PalAudio:init();
		return core:emitHeader() . file:emitHeader() . proc:emitHeader() . sock:emitHeader() . audio:emitHeader();
	}

	Function of String is emitBody(){
		local PalCore is core: PalCore:init();
		local PalDir is dir: PalDir:init();
		local PalFile is file: PalFile:init();
		local PalProcess is proc: PalProcess:init();
		local PalTime is time: PalTime:init();
		local PalConsole is cons: PalConsole:init();
		local PalSocket is sock: PalSocket:init();
		local PalAudio is audio: PalAudio:init();
		return core:emitBody() . dir:emitBody() . file:emitBody() . proc:emitBody() . time:emitBody() . cons:emitBody() . sock:emitBody() . audio:emitBody();
	}

	Function of String is emitRuntime(){
		return self:emitHeader() . "\n" . self:emitBody();
	}
}
