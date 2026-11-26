#! Package base:mold
#! Pure Spec SPIR-V 1.0 bytecode builder for 3D Vulkan vertex and fragment shaders.

Class is SpirvBuilder{
	replace [String] is namespace: ['base', 'mold'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'struct', Array]
	];

	Array of Int is words: Array();
	Int is bufferAddr: 0;
	Int is bufferBytes: 0;

	## Initializes an empty SPIR-V module word stream.
	replace Function is init(){
		words: Array();
		bufferAddr: 0;
		bufferBytes: 0;
	}

	local Function is emitWord(Int is w){
		words:add(item: w);
	}

	local Function is emitOp1(Int is op, Int is a){
		:emitWord(w: (2 * 65536) + op);
		:emitWord(w: a);
	}

	local Function is emitOp2(Int is op, Int is a, Int is b){
		:emitWord(w: (3 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
	}

	local Function is emitOp3(Int is op, Int is a, Int is b, Int is c){
		:emitWord(w: (4 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
	}

	local Function is emitOp4(Int is op, Int is a, Int is b, Int is c, Int is d){
		:emitWord(w: (5 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
		:emitWord(w: d);
	}

	local Function is emitOp5(Int is op, Int is a, Int is b, Int is c, Int is d, Int is e){
		:emitWord(w: (6 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
		:emitWord(w: d);
		:emitWord(w: e);
	}

	local Function is emitOp6(Int is op, Int is a, Int is b, Int is c, Int is d, Int is e, Int is f){
		:emitWord(w: (7 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
		:emitWord(w: d);
		:emitWord(w: e);
		:emitWord(w: f);
	}

	local Function is emitOp7(Int is op, Int is a, Int is b, Int is c, Int is d, Int is e, Int is f, Int is g){
		:emitWord(w: (8 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
		:emitWord(w: d);
		:emitWord(w: e);
		:emitWord(w: f);
		:emitWord(w: g);
	}

	local Function is emitHeader(Int is bound){
		:emitWord(w: 119734787);
		:emitWord(w: 65536);
		:emitWord(w: 0);
		:emitWord(w: bound);
		:emitWord(w: 0);
	}

	local Function is materialize(){
		:dispose();
		local Int is count: words:length();
		bufferBytes: count * 4;
		bufferAddr: alloc(bytes: bufferBytes);
		times(count: count, worker: local Function(Int is i){
			storeI32(ptr: bufferAddr, byteOffset: i * 4, val: words:get(index: i));
		});
	}

	## Builds the default vertex shader:
	## `layout(location=0) in vec3 pos; layout(location=1) in vec3 col;`
	## `layout(push_constant) uniform PC { mat4 mvp; };`
	## `gl_Position = mvp * vec4(pos, 1.0); outCol = col;`
	Function is buildColorVertexShader(){
		words: Array();
		:emitHeader(bound: 32);

		## OpCapability Shader (17, 1)
		:emitOp1(op: 17, a: 1);
		## OpMemoryModel Logical GLSL450 (14, 0, 1)
		:emitOp2(op: 14, a: 0, b: 1);
		## OpEntryPoint Vertex %21 "main" %15 %16 %18 %20 (8 words: "main" = 0x6E69616D, 0)
		:emitOp7(op: 15, a: 0, b: 21, c: 1852399981, d: 0, e: 15, f: 16, g: 18);
		## Wait: emitOp7 has 7 args (wordCount=8), we need %20 too -> 9 words total
		## Patch word count and append %20:
		words:set(index: words:length() - 8, item: (9 * 65536) + 15);
		:emitWord(w: 20);

		## Decorations
		:emitOp2(op: 71, a: 7, b: 2);            ## OpDecorate %7 Block
		:emitOp3(op: 72, a: 7, b: 0, c: 5);      ## OpMemberDecorate %7 0 ColMajor
		:emitOp4(op: 72, a: 7, b: 0, c: 35, d: 0);  ## OpMemberDecorate %7 0 Offset 0
		:emitOp4(op: 72, a: 7, b: 0, c: 7, d: 16);  ## OpMemberDecorate %7 0 MatrixStride 16
		:emitOp3(op: 71, a: 15, b: 30, c: 0);    ## OpDecorate %15 Location 0
		:emitOp3(op: 71, a: 16, b: 30, c: 1);    ## OpDecorate %16 Location 1
		:emitOp3(op: 71, a: 18, b: 11, c: 0);    ## OpDecorate %18 BuiltIn Position
		:emitOp3(op: 71, a: 20, b: 30, c: 0);    ## OpDecorate %20 Location 0

		## Types & Constants
		:emitOp1(op: 19, a: 1);                  ## %1 = OpTypeVoid
		:emitOp2(op: 33, a: 2, b: 1);            ## %2 = OpTypeFunction %1
		:emitOp2(op: 22, a: 3, b: 32);           ## %3 = OpTypeFloat 32
		:emitOp3(op: 23, a: 4, b: 3, c: 3);      ## %4 = OpTypeVector %3 3
		:emitOp3(op: 23, a: 5, b: 3, c: 4);      ## %5 = OpTypeVector %3 4
		:emitOp3(op: 24, a: 6, b: 5, c: 4);      ## %6 = OpTypeMatrix %5 4
		:emitOp2(op: 30, a: 7, b: 6);            ## %7 = OpTypeStruct %6
		:emitOp3(op: 32, a: 8, b: 9, c: 7);      ## %8 = OpTypePointer PushConstant %7
		:emitOp3(op: 59, a: 8, b: 9, c: 9);      ## %9 = OpVariable %8 PushConstant
		:emitOp3(op: 32, a: 10, b: 9, c: 6);     ## %10 = OpTypePointer PushConstant %6
		:emitOp3(op: 21, a: 11, b: 32, c: 1);    ## %11 = OpTypeInt 32 1
		:emitOp3(op: 43, a: 11, b: 12, c: 0);    ## %12 = OpConstant %11 0
		:emitOp3(op: 43, a: 3, b: 13, c: 1065353216); ## %13 = OpConstant %3 1.0 (0x3F800000)

		## I/O Variables
		:emitOp3(op: 32, a: 14, b: 1, c: 4);     ## %14 = OpTypePointer Input %4
		:emitOp3(op: 59, a: 14, b: 15, c: 1);    ## %15 = OpVariable %14 Input (inPos)
		:emitOp3(op: 59, a: 14, b: 16, c: 1);    ## %16 = OpVariable %14 Input (inColor)
		:emitOp3(op: 32, a: 17, b: 3, c: 5);     ## %17 = OpTypePointer Output %5
		:emitOp3(op: 59, a: 17, b: 18, c: 3);    ## %18 = OpVariable %17 Output (gl_Position)
		:emitOp3(op: 32, a: 19, b: 3, c: 4);     ## %19 = OpTypePointer Output %4
		:emitOp3(op: 59, a: 19, b: 20, c: 3);    ## %20 = OpVariable %19 Output (outColor)

		## main()
		:emitOp4(op: 54, a: 1, b: 21, c: 0, d: 2); ## %21 = OpFunction %1 None %2
		:emitOp1(op: 248, a: 22);                  ## %22 = OpLabel
		:emitOp3(op: 61, a: 4, b: 23, c: 15);      ## %23 = OpLoad %4 %15
		:emitOp4(op: 81, a: 3, b: 24, c: 23, d: 0); ## %24 = OpCompositeExtract %3 %23 0
		:emitOp4(op: 81, a: 3, b: 25, c: 23, d: 1); ## %25 = OpCompositeExtract %3 %23 1
		:emitOp4(op: 81, a: 3, b: 26, c: 23, d: 2); ## %26 = OpCompositeExtract %3 %23 2
		:emitOp6(op: 80, a: 5, b: 27, c: 24, d: 25, e: 26, f: 13); ## %27 = vec4(pos, 1.0)
		:emitOp4(op: 65, a: 10, b: 28, c: 9, d: 12); ## %28 = OpAccessChain %10 %9 %12
		:emitOp3(op: 61, a: 6, b: 29, c: 28);      ## %29 = OpLoad %6 %28
		:emitOp4(op: 145, a: 5, b: 30, c: 29, d: 27); ## %30 = OpMatrixTimesVector %5 %29 %27
		:emitOp2(op: 62, a: 18, b: 30);            ## OpStore %18 %30
		:emitOp3(op: 61, a: 4, b: 31, c: 16);      ## %31 = OpLoad %4 %16
		:emitOp2(op: 62, a: 20, b: 31);            ## OpStore %20 %31
		:emitWord(w: (1 * 65536) + 253);           ## OpReturn
		:emitWord(w: (1 * 65536) + 56);            ## OpFunctionEnd

		:materialize();
	}

	## Builds the default fragment shader:
	## `layout(location=0) in vec3 col; layout(location=0) out vec4 fragColor;`
	## `fragColor = vec4(col, 1.0);`
	Function is buildColorFragmentShader(){
		words: Array();
		:emitHeader(bound: 18);

		:emitOp1(op: 17, a: 1);                    ## OpCapability Shader
		:emitOp2(op: 14, a: 0, b: 1);              ## OpMemoryModel Logical GLSL450
		:emitOp6(op: 15, a: 4, b: 11, c: 1852399981, d: 0, e: 8, f: 10); ## OpEntryPoint Fragment %11 "main" %8 %10
		:emitOp2(op: 16, a: 11, b: 7);             ## OpExecutionMode %11 OriginUpperLeft
		:emitOp3(op: 71, a: 8, b: 30, c: 0);       ## OpDecorate %8 Location 0
		:emitOp3(op: 71, a: 10, b: 30, c: 0);      ## OpDecorate %10 Location 0

		:emitOp1(op: 19, a: 1);                    ## %1 = OpTypeVoid
		:emitOp2(op: 33, a: 2, b: 1);              ## %2 = OpTypeFunction %1
		:emitOp2(op: 22, a: 3, b: 32);             ## %3 = OpTypeFloat 32
		:emitOp3(op: 23, a: 4, b: 3, c: 3);        ## %4 = OpTypeVector %3 3
		:emitOp3(op: 23, a: 5, b: 3, c: 4);        ## %5 = OpTypeVector %3 4
		:emitOp3(op: 43, a: 3, b: 6, c: 1065353216); ## %6 = OpConstant %3 1.0

		:emitOp3(op: 32, a: 7, b: 1, c: 4);        ## %7 = OpTypePointer Input %4
		:emitOp3(op: 59, a: 7, b: 8, c: 1);        ## %8 = OpVariable %7 Input
		:emitOp3(op: 32, a: 9, b: 3, c: 5);        ## %9 = OpTypePointer Output %5
		:emitOp3(op: 59, a: 9, b: 10, c: 3);       ## %10 = OpVariable %9 Output

		:emitOp4(op: 54, a: 1, b: 11, c: 0, d: 2); ## %11 = OpFunction %1 None %2
		:emitOp1(op: 248, a: 12);                  ## %12 = OpLabel
		:emitOp3(op: 61, a: 4, b: 13, c: 8);       ## %13 = OpLoad %4 %8
		:emitOp4(op: 81, a: 3, b: 14, c: 13, d: 0); ## %14 = OpCompositeExtract %3 %13 0
		:emitOp4(op: 81, a: 3, b: 15, c: 13, d: 1); ## %15 = OpCompositeExtract %3 %13 1
		:emitOp4(op: 81, a: 3, b: 16, c: 13, d: 2); ## %16 = OpCompositeExtract %3 %13 2
		:emitOp6(op: 80, a: 5, b: 17, c: 14, d: 15, e: 16, f: 6); ## %17 = vec4(col, 1.0)
		:emitOp2(op: 62, a: 10, b: 17);            ## OpStore %10 %17
		:emitWord(w: (1 * 65536) + 253);           ## OpReturn
		:emitWord(w: (1 * 65536) + 56);            ## OpFunctionEnd

		:materialize();
	}

	## Builds a 2D textured fullscreen overlay vertex shader (vec2 pos, vec2 uv -> gl_Position, uv).
	Function is buildOverlayVertexShader(){
		words: Array();
		:emitHeader(bound: 22);
		:emitOp1(op: 17, a: 1);
		:emitOp2(op: 14, a: 0, b: 1);
		:emitWord(w: (9 * 65536) + 15);
		:emitWord(w: 0);
		:emitWord(w: 15);
		:emitWord(w: 1852399981);
		:emitWord(w: 0);
		:emitWord(w: 9);
		:emitWord(w: 10);
		:emitWord(w: 12);
		:emitWord(w: 14);

		:emitOp3(op: 71, a: 9, b: 30, c: 0);
		:emitOp3(op: 71, a: 10, b: 30, c: 1);
		:emitOp3(op: 71, a: 12, b: 11, c: 0);
		:emitOp3(op: 71, a: 14, b: 30, c: 0);

		:emitOp1(op: 19, a: 1);
		:emitOp2(op: 33, a: 2, b: 1);
		:emitOp2(op: 22, a: 3, b: 32);
		:emitOp3(op: 23, a: 4, b: 3, c: 2);
		:emitOp3(op: 23, a: 5, b: 3, c: 4);
		:emitOp3(op: 43, a: 3, b: 6, c: 0);
		:emitOp3(op: 43, a: 3, b: 7, c: 1065353216);

		:emitOp3(op: 32, a: 8, b: 1, c: 4);
		:emitOp3(op: 59, a: 8, b: 9, c: 1);
		:emitOp3(op: 59, a: 8, b: 10, c: 1);
		:emitOp3(op: 32, a: 11, b: 3, c: 5);
		:emitOp3(op: 59, a: 11, b: 12, c: 3);
		:emitOp3(op: 32, a: 13, b: 3, c: 4);
		:emitOp3(op: 59, a: 13, b: 14, c: 3);

		:emitOp4(op: 54, a: 1, b: 15, c: 0, d: 2);
		:emitOp1(op: 248, a: 16);
		:emitOp3(op: 61, a: 4, b: 17, c: 9);
		:emitOp4(op: 81, a: 3, b: 18, c: 17, d: 0);
		:emitOp4(op: 81, a: 3, b: 19, c: 17, d: 1);
		:emitOp6(op: 80, a: 5, b: 20, c: 18, d: 19, e: 6, f: 7);
		:emitOp2(op: 62, a: 12, b: 20);
		:emitOp3(op: 61, a: 4, b: 21, c: 10);
		:emitOp2(op: 62, a: 14, b: 21);
		:emitWord(w: (1 * 65536) + 253);
		:emitWord(w: (1 * 65536) + 56);
		:materialize();
	}

	## Builds a 2D textured overlay fragment shader sampling binding 0 at interpolated uv.
	Function is buildOverlayFragmentShader(){
		words: Array();
		:emitHeader(bound: 19);
		:emitOp1(op: 17, a: 1);
		:emitOp2(op: 14, a: 0, b: 1);
		:emitWord(w: (7 * 65536) + 15);
		:emitWord(w: 4);
		:emitWord(w: 14);
		:emitWord(w: 1852399981);
		:emitWord(w: 0);
		:emitWord(w: 11);
		:emitWord(w: 13);
		:emitOp2(op: 16, a: 14, b: 7);

		:emitOp3(op: 71, a: 9, b: 34, c: 0);
		:emitOp3(op: 71, a: 9, b: 33, c: 0);
		:emitOp3(op: 71, a: 11, b: 30, c: 0);
		:emitOp3(op: 71, a: 13, b: 30, c: 0);

		:emitOp1(op: 19, a: 1);
		:emitOp2(op: 33, a: 2, b: 1);
		:emitOp2(op: 22, a: 3, b: 32);
		:emitOp3(op: 23, a: 4, b: 3, c: 2);
		:emitOp3(op: 23, a: 5, b: 3, c: 4);
		:emitWord(w: (9 * 65536) + 25);
		:emitWord(w: 6);
		:emitWord(w: 3);
		:emitWord(w: 1);
		:emitWord(w: 0);
		:emitWord(w: 0);
		:emitWord(w: 0);
		:emitWord(w: 1);
		:emitWord(w: 0);
		:emitOp2(op: 27, a: 7, b: 6);

		:emitOp3(op: 32, a: 8, b: 0, c: 7);
		:emitOp3(op: 59, a: 8, b: 9, c: 0);
		:emitOp3(op: 32, a: 10, b: 1, c: 4);
		:emitOp3(op: 59, a: 10, b: 11, c: 1);
		:emitOp3(op: 32, a: 12, b: 3, c: 5);
		:emitOp3(op: 59, a: 12, b: 13, c: 3);

		:emitOp4(op: 54, a: 1, b: 14, c: 0, d: 2);
		:emitOp1(op: 248, a: 15);
		:emitOp3(op: 61, a: 7, b: 16, c: 9);
		:emitOp3(op: 61, a: 4, b: 17, c: 11);
		:emitOp4(op: 87, a: 5, b: 18, c: 16, d: 17);
		:emitOp2(op: 62, a: 13, b: 18);
		:emitWord(w: (1 * 65536) + 253);
		:emitWord(w: (1 * 65536) + 56);
		:materialize();
	}

	## Returns the native memory address of the SPIR-V `uint32_t` words.
	Function of Int is wordsAddr(){
		return bufferAddr;
	}

	## Returns the byte length of the SPIR-V module.
	Function of Int is byteLength(){
		return bufferBytes;
	}

	## Frees the native SPIR-V buffer.
	Function is dispose(){
		if({ bufferAddr != 0 }, {
			free(ptr: bufferAddr);
			bufferAddr: 0;
			bufferBytes: 0;
		});
	}
}
