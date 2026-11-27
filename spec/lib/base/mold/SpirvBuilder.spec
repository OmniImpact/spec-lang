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

	Function is emitWord(Int is w){
		words:add(item: w);
	}

	Function is emitOp1(Int is op, Int is a){
		:emitWord(w: (2 * 65536) + op);
		:emitWord(w: a);
	}

	Function is emitOp2(Int is op, Int is a, Int is b){
		:emitWord(w: (3 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
	}

	Function is emitOp3(Int is op, Int is a, Int is b, Int is c){
		:emitWord(w: (4 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
	}

	Function is emitOp4(Int is op, Int is a, Int is b, Int is c, Int is d){
		:emitWord(w: (5 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
		:emitWord(w: d);
	}

	Function is emitOp5(Int is op, Int is a, Int is b, Int is c, Int is d, Int is e){
		:emitWord(w: (6 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
		:emitWord(w: d);
		:emitWord(w: e);
	}

	Function is emitOp6(Int is op, Int is a, Int is b, Int is c, Int is d, Int is e, Int is f){
		:emitWord(w: (7 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
		:emitWord(w: d);
		:emitWord(w: e);
		:emitWord(w: f);
	}

	Function is emitOp7(Int is op, Int is a, Int is b, Int is c, Int is d, Int is e, Int is f, Int is g){
		:emitWord(w: (8 * 65536) + op);
		:emitWord(w: a);
		:emitWord(w: b);
		:emitWord(w: c);
		:emitWord(w: d);
		:emitWord(w: e);
		:emitWord(w: f);
		:emitWord(w: g);
	}

	Function is emitHeader(Int is bound){
		:emitWord(w: 119734787);
		:emitWord(w: 65536);
		:emitWord(w: 0);
		:emitWord(w: bound);
		:emitWord(w: 0);
	}

	Function is materialize(){
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

	## Builds a 3D lit/reflective vertex shader (vec3 pos, vec3 color, vec3 normal + 128-byte push constants).
	Function is buildLitReflectVertexShader(){
		words: Array([
			119734787, 65536, 851979, 43, 0, 131089, 1, 393227, 1, 1280527431, 1685353262, 808793134, 0, 196622, 0, 1,
			786447, 0, 4, 1852399981, 0, 13, 25, 36, 37, 39, 40, 42, 196679, 11, 2, 327752,
			11, 0, 11, 0, 327752, 11, 1, 11, 1, 327752, 11, 2, 11, 3, 327752, 11,
			3, 11, 4, 196679, 17, 2, 262216, 17, 0, 5, 327752, 17, 0, 7, 16, 327752,
			17, 0, 35, 0, 327752, 17, 1, 35, 64, 327752, 17, 2, 35, 68, 327752, 17,
			3, 35, 72, 327752, 17, 4, 35, 76, 327752, 17, 5, 35, 80, 327752, 17, 6,
			35, 84, 327752, 17, 7, 35, 88, 327752, 17, 8, 35, 92, 262215, 25, 30, 0,
			262215, 36, 30, 0, 262215, 37, 30, 1, 262215, 39, 30, 1, 262215, 40, 30, 2,
			262215, 42, 30, 2, 131091, 2, 196641, 3, 2, 196630, 6, 32, 262167, 7, 6, 4,
			262165, 8, 32, 0, 262187, 8, 9, 1, 262172, 10, 6, 9, 393246, 11, 7, 6,
			10, 10, 262176, 12, 3, 11, 262203, 12, 13, 3, 262165, 14, 32, 1, 262187, 14,
			15, 0, 262168, 16, 7, 4, 720926, 17, 16, 6, 6, 6, 6, 6, 6, 6,
			6, 262176, 18, 9, 17, 262203, 18, 19, 9, 262176, 20, 9, 16, 262167, 23, 6,
			3, 262176, 24, 1, 23, 262203, 24, 25, 1, 262187, 6, 27, 1065353216, 262176, 33, 3,
			7, 262176, 35, 3, 23, 262203, 35, 36, 3, 262203, 24, 37, 1, 262203, 35, 39,
			3, 262203, 24, 40, 1, 262203, 35, 42, 3, 327734, 2, 4, 0, 3, 131320, 5,
			327745, 20, 21, 19, 15, 262205, 16, 22, 21, 262205, 23, 26, 25, 327761, 6, 28,
			26, 0, 327761, 6, 29, 26, 1, 327761, 6, 30, 26, 2, 458832, 7, 31, 28,
			29, 30, 27, 327825, 7, 32, 22, 31, 327745, 33, 34, 13, 15, 196670, 34, 32,
			262205, 23, 38, 37, 196670, 36, 38, 262205, 23, 41, 40, 196670, 39, 41, 196670, 42,
			26, 65789, 65592
		]);
		:materialize();
	}

	## Builds a per-fragment Blinn-Phong + cube-room reflection fragment shader driven by 128-byte push constants.
	Function is buildLitReflectFragmentShader(){
		words: Array([
			119734787, 65536, 851979, 464, 0, 131089, 1, 393227, 1, 1280527431, 1685353262, 808793134, 0, 196622, 0, 1,
			589839, 4, 4, 1852399981, 0, 172, 182, 183, 210, 196624, 4, 7, 262215, 172, 30, 1,
			262215, 182, 30, 0, 262215, 183, 30, 0, 196679, 195, 2, 262216, 195, 0, 5, 327752,
			195, 0, 7, 16, 327752, 195, 0, 35, 0, 327752, 195, 1, 35, 64, 327752, 195,
			2, 35, 68, 327752, 195, 3, 35, 72, 327752, 195, 4, 35, 76, 327752, 195, 5,
			35, 80, 327752, 195, 6, 35, 84, 327752, 195, 7, 35, 88, 327752, 195, 8, 35,
			92, 262215, 210, 30, 2, 131091, 2, 196641, 3, 2, 196630, 6, 32, 262167, 7, 6,
			3, 262165, 15, 32, 0, 262187, 15, 16, 0, 262187, 6, 21, 925353388, 131092, 22, 262187,
			6, 57, 1065353216, 262187, 6, 62, 3204448256, 262187, 6, 69, 1056964608, 262187, 6, 114, 0, 262187,
			6, 116, 1064514355, 262187, 6, 117, 1060655596, 262187, 6, 118, 1043878380, 393260, 7, 119, 116, 117,
			118, 262187, 6, 120, 1048576000, 262187, 6, 121, 1063339950, 262187, 6, 122, 1055286886, 393260, 7, 123,
			120, 121, 122, 262167, 124, 22, 3, 262187, 6, 147, 1050924810, 262187, 6, 148, 1056293519, 262187,
			6, 149, 1064682127, 393260, 7, 150, 147, 148, 149, 262187, 6, 151, 1061158912, 262187, 6, 152,
			1050253722, 393260, 7, 153, 151, 152, 121, 262187, 6, 161, 1049582633, 393260, 7, 162, 116, 161,
			161, 262187, 6, 163, 1046562734, 262187, 6, 164, 1062836634, 262187, 6, 165, 1063675494, 393260, 7, 166,
			163, 164, 165, 262176, 171, 1, 7, 262203, 171, 172, 1, 262187, 6, 176, 1036831949, 262167,
			180, 6, 4, 262176, 181, 3, 180, 262203, 181, 182, 3, 262203, 171, 183, 1, 262168,
			194, 180, 4, 720926, 195, 194, 6, 6, 6, 6, 6, 6, 6, 6, 262176, 196,
			9, 195, 262203, 196, 197, 9, 262165, 198, 32, 1, 262187, 198, 199, 3, 262176, 200,
			9, 6, 262187, 198, 203, 4, 262187, 198, 206, 5, 262203, 171, 210, 1, 262187, 198,
			215, 6, 262187, 198, 218, 7, 262187, 198, 221, 8, 262187, 6, 239, 1061662228, 262187, 6,
			244, 1090519040, 262187, 6, 245, 1115684864, 262187, 198, 246, 1, 262187, 198, 281, 2, 393260, 7,
			457, 57, 57, 57, 393260, 7, 458, 62, 62, 62, 393260, 7, 459, 69, 69, 69,
			393260, 7, 460, 114, 114, 114, 327734, 2, 4, 0, 3, 131320, 5, 196855, 294, 0,
			196859, 16, 295, 131320, 295, 262205, 7, 173, 172, 327828, 6, 175, 173, 173, 327864, 22,
			177, 175, 176, 196855, 179, 0, 262394, 177, 178, 179, 131320, 178, 262205, 7, 184, 183,
			327761, 6, 185, 184, 0, 327761, 6, 186, 184, 1, 327761, 6, 187, 184, 2, 458832,
			180, 188, 185, 186, 187, 57, 196670, 182, 188, 131321, 294, 131320, 179, 393228, 7, 192,
			1, 69, 173, 327745, 200, 201, 197, 199, 262205, 6, 202, 201, 327745, 200, 204, 197,
			203, 262205, 6, 205, 204, 327745, 200, 207, 197, 206, 262205, 6, 208, 207, 393296, 7,
			209, 202, 205, 208, 262205, 7, 211, 210, 327811, 7, 212, 209, 211, 393228, 7, 213,
			1, 69, 212, 327745, 200, 216, 197, 215, 262205, 6, 217, 216, 327745, 200, 219, 197,
			218, 262205, 6, 220, 219, 327745, 200, 222, 197, 221, 262205, 6, 223, 222, 393296, 7,
			224, 217, 220, 223, 327811, 7, 226, 224, 211, 393228, 7, 227, 1, 69, 226, 327809,
			7, 231, 227, 213, 393228, 7, 232, 1, 69, 231, 327828, 6, 236, 192, 227, 458764,
			6, 237, 1, 40, 236, 114, 327813, 6, 241, 239, 237, 327809, 6, 242, 163, 241,
			327745, 200, 247, 197, 246, 262205, 6, 248, 247, 524300, 6, 249, 1, 46, 244, 245,
			248, 327828, 6, 253, 192, 232, 458764, 6, 254, 1, 40, 253, 114, 458764, 6, 256,
			1, 26, 254, 249, 327813, 6, 259, 256, 248, 262205, 7, 261, 183, 327822, 7, 263,
			261, 242, 393296, 7, 265, 259, 259, 259, 327809, 7, 266, 263, 265, 262271, 7, 269,
			213, 458764, 7, 271, 1, 71, 269, 192, 196855, 430, 0, 196859, 16, 320, 131320, 320,
			327761, 6, 322, 271, 0, 393228, 6, 323, 1, 4, 322, 327864, 22, 324, 323, 21,
			393385, 6, 461, 324, 21, 322, 327761, 6, 332, 271, 1, 393228, 6, 333, 1, 4,
			332, 327864, 22, 334, 333, 21, 393385, 6, 462, 334, 21, 332, 327761, 6, 342, 271,
			2, 393228, 6, 343, 1, 4, 342, 327864, 22, 344, 343, 21, 393385, 6, 463, 344,
			21, 342, 393296, 7, 351, 461, 462, 463, 327816, 7, 354, 457, 351, 327811, 7, 357,
			458, 211, 327813, 7, 359, 357, 354, 327811, 7, 362, 459, 211, 327813, 7, 364, 362,
			354, 458764, 7, 367, 1, 40, 359, 364, 327761, 6, 369, 367, 0, 327761, 6, 371,
			367, 1, 327761, 6, 373, 367, 2, 458764, 6, 374, 1, 37, 371, 373, 458764, 6,
			375, 1, 37, 369, 374, 327822, 7, 379, 271, 375, 327809, 7, 380, 211, 379, 393228,
			7, 382, 1, 4, 380, 327761, 6, 384, 382, 0, 327761, 6, 386, 382, 1, 327870,
			22, 387, 384, 386, 196855, 394, 0, 262394, 387, 388, 394, 131320, 388, 327761, 6, 392,
			382, 2, 327870, 22, 393, 384, 392, 131321, 394, 131320, 394, 458997, 22, 395, 387, 320,
			393, 388, 196855, 429, 0, 262394, 395, 396, 402, 131320, 402, 327870, 22, 407, 386, 384,
			196855, 414, 0, 262394, 407, 408, 414, 131320, 408, 327761, 6, 412, 382, 2, 327870, 22,
			413, 386, 412, 131321, 414, 131320, 414, 458997, 22, 415, 407, 402, 413, 408, 196855, 428,
			0, 262394, 415, 416, 422, 131320, 422, 327761, 6, 424, 380, 2, 327866, 22, 425, 424,
			114, 393296, 124, 426, 425, 425, 425, 393385, 7, 427, 426, 162, 166, 131321, 430, 131320,
			416, 327761, 6, 418, 380, 1, 327866, 22, 419, 418, 114, 393296, 124, 420, 419, 419,
			419, 393385, 7, 421, 420, 150, 153, 131321, 430, 131320, 428, 65791, 131320, 396, 327761, 6,
			398, 380, 0, 327866, 22, 399, 398, 114, 393296, 124, 400, 399, 399, 399, 393385, 7,
			401, 400, 119, 123, 131321, 430, 131320, 429, 65791, 131320, 430, 590069, 7, 455, 401, 396,
			421, 416, 427, 422, 327745, 200, 282, 197, 281, 262205, 6, 283, 282, 393296, 7, 284,
			283, 283, 283, 524300, 7, 285, 1, 46, 266, 455, 284, 524300, 7, 289, 1, 43,
			285, 460, 457, 327761, 6, 290, 289, 0, 327761, 6, 291, 289, 1, 327761, 6, 292,
			289, 2, 458832, 180, 293, 290, 291, 292, 57, 196670, 182, 293, 131321, 294, 131320, 294,
			65789, 65592
		]);
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

	Function is destroy(){
		:dispose();
	}
}
