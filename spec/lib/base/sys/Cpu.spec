#! Package base:sys
#! Runtime CPU feature queries for SIMD dispatch and `--cpu native` constant folding.

Class is Cpu{
	replace [String] is namespace: ['base', 'sys'];

	merge [[String]] is using: [
		['base', 'sys', as Process()]
	];

	## True when hardware SIMD vector operations (SSE2/AVX2/NEON) are available.
	Function of Boolean is hasSimd(){ cpuHasSimd() }

	## True when x86 AVX2 is supported on the current CPU.
	Function of Boolean is hasAvx2(){ cpuHasAvx2() }
}
