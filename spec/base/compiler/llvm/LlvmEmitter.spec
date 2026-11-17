#! Package base:compiler:llvm
#! Emits target-agnostic LLVM IR (.ll text with opaque ptr) from an IrModule.

Class is LlvmEmitter{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'compiler', 'ir', IrParam],
		['base', 'compiler', 'ir', IrStruct],
		['base', 'compiler', 'ir', IrFunction],
		['base', 'compiler', 'ir', IrModule],
		['base', 'compiler', 'llvm', LlvmStructLayout],
		['base', 'struct', Array],
		['base', 'sys', as Buf()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	replace Function is init(){
	}

	Function of String is llvmType(IrType is ty){
		return match(on: ty, when: [
			IrType:Void: { 'void' },
			IrType:I1: { 'i1' },
			IrType:I64: { 'i64' },
			IrType:F64: { 'double' },
			IrType:Ptr: { 'ptr' }
		]);
	}

	local Function of String is emitArcAndPool(){
		return '''
@_spec_pool_stack = external thread_local global ptr
@_spec_pool_top = external thread_local global i64
@_spec_pool_cap = external thread_local global i64
@_spec_tls_i64 = internal thread_local global [16 x i64] zeroinitializer
@.str.oom = private unnamed_addr constant [14 x i8] c"Out of memory\00"
%struct.SpecHeader = type { i32, ptr, i32, i32 }
define internal ptr @spec_rt_alloc(i64 %size, ptr %destroy) {
  %tsz = add i64 %size, 24
  %h = call ptr @calloc(i64 1, i64 %tsz)
  %isnull = icmp eq ptr %h, null
  br i1 %isnull, label %oom, label %ok
oom:
  call void @spec_panic(ptr @.str.oom)
  br label %ok
ok:
  %rcp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 0
  store i32 1, ptr %rcp
  %dp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 1
  store ptr %destroy, ptr %dp
  %obj = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 1
  ret ptr %obj
}
define internal ptr @spec_rt_retain(ptr %obj) alwaysinline {
  %isnull = icmp eq ptr %obj, null
  br i1 %isnull, label %done, label %chk
chk:
  %h = getelementptr inbounds %struct.SpecHeader, ptr %obj, i64 -1
  %sfp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 2
  %sf = load atomic i32, ptr %sfp monotonic, align 4
  %imm = and i32 %sf, 1
  %is_imm = icmp ne i32 %imm, 0
  br i1 %is_imm, label %done, label %inc
inc:
  %rcp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 0
  %old = atomicrmw add ptr %rcp, i32 1 monotonic, align 4
  br label %done
done:
  ret ptr %obj
}
define internal void @spec_rt_release(ptr %obj) {
  %isnull = icmp eq ptr %obj, null
  br i1 %isnull, label %done, label %chk
chk:
  %h = getelementptr inbounds %struct.SpecHeader, ptr %obj, i64 -1
  %sfp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 2
  %sf = load atomic i32, ptr %sfp monotonic, align 4
  %imm = and i32 %sf, 1
  %is_imm = icmp ne i32 %imm, 0
  br i1 %is_imm, label %done, label %dec
dec:
  %rcp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 0
  %old = atomicrmw sub ptr %rcp, i32 1 acq_rel, align 4
  %is_last = icmp eq i32 %old, 1
  br i1 %is_last, label %dtor, label %done
dtor:
  %dp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 1
  %d = load ptr, ptr %dp
  store ptr null, ptr %dp
  %has_d = icmp ne ptr %d, null
  br i1 %has_d, label %call_d, label %free_h
call_d:
  call void %d(ptr %obj)
  br label %free_h
free_h:
  call void @free(ptr %h)
  br label %done
done:
  ret void
}
define internal i64 @spec_pool_frame() alwaysinline {
  %t = load i64, ptr @_spec_pool_top
  ret i64 %t
}
define internal void @spec_pool_release_to(i64 %mark) {
  br label %hdr
hdr:
  %top = load i64, ptr @_spec_pool_top
  %gt = icmp ugt i64 %top, %mark
  br i1 %gt, label %body, label %done
body:
  %ntop = sub i64 %top, 1
  store i64 %ntop, ptr @_spec_pool_top
  %stk = load ptr, ptr @_spec_pool_stack
  %slot = getelementptr ptr, ptr %stk, i64 %ntop
  %obj = load ptr, ptr %slot
  %nn = icmp ne ptr %obj, null
  br i1 %nn, label %rel, label %hdr
rel:
  call void @spec_rt_release(ptr %obj)
  br label %hdr
done:
  ret void
}
define internal ptr @spec_claim_pool(ptr %obj) {
  %isnull = icmp eq ptr %obj, null
  br i1 %isnull, label %done, label %chk
chk:
  %top = load i64, ptr @_spec_pool_top
  %cap = load i64, ptr @_spec_pool_cap
  %eq = icmp eq i64 %top, %cap
  br i1 %eq, label %grow, label %push
grow:
  %isz = icmp eq i64 %cap, 0
  %cap2 = mul i64 %cap, 2
  %ncap = select i1 %isz, i64 8, i64 %cap2
  %bytes = mul i64 %ncap, 8
  %ostk = load ptr, ptr @_spec_pool_stack
  %oaddr = ptrtoint ptr %ostk to i64
  %naddr = call i64 @__spec_mem_realloc(i64 %oaddr, i64 %bytes)
  %nstk = inttoptr i64 %naddr to ptr
  store ptr %nstk, ptr @_spec_pool_stack
  store i64 %ncap, ptr @_spec_pool_cap
  br label %push
push:
  %stk = load ptr, ptr @_spec_pool_stack
  %slot = getelementptr ptr, ptr %stk, i64 %top
  store ptr %obj, ptr %slot
  %ntop = add i64 %top, 1
  store i64 %ntop, ptr @_spec_pool_top
  br label %done
done:
  ret ptr %obj
}''';
	}

	local Function of String is emitClosuresAndBoxes(){
		return '''
%struct.SpecClosure = type { ptr, ptr, ptr }
define internal void @__spec_closure_destroy(ptr %self) {
  %isnull = icmp eq ptr %self, null
  br i1 %isnull, label %done, label %chk
chk:
  %ep = getelementptr inbounds %struct.SpecClosure, ptr %self, i32 0, i32 1
  %env = load ptr, ptr %ep
  %dp = getelementptr inbounds %struct.SpecClosure, ptr %self, i32 0, i32 2
  %d = load ptr, ptr %dp
  %has_env = icmp ne ptr %env, null
  %has_d = icmp ne ptr %d, null
  %both = and i1 %has_env, %has_d
  br i1 %both, label %call_d, label %done
call_d:
  call void %d(ptr %env)
  store ptr null, ptr %ep
  br label %done
done:
  ret void
}
define internal ptr @spec_rt_closure_new(ptr %fn, ptr %env, ptr %destroy_env) {
  %c = call ptr @spec_rt_alloc(i64 24, ptr @__spec_closure_destroy)
  %fp = getelementptr inbounds %struct.SpecClosure, ptr %c, i32 0, i32 0
  store ptr %fn, ptr %fp
  %ep = getelementptr inbounds %struct.SpecClosure, ptr %c, i32 0, i32 1
  store ptr %env, ptr %ep
  %dp = getelementptr inbounds %struct.SpecClosure, ptr %c, i32 0, i32 2
  store ptr %destroy_env, ptr %dp
  ret ptr %c
}
%struct.SpecBox = type { i64, i1 }
define internal void @__spec_box_destroy(ptr %self) {
  %isnull = icmp eq ptr %self, null
  br i1 %isnull, label %done, label %chk
chk:
  %ap = getelementptr inbounds %struct.SpecBox, ptr %self, i32 0, i32 1
  %is_arc = load i1, ptr %ap
  br i1 %is_arc, label %rel, label %done
rel:
  %vp = getelementptr inbounds %struct.SpecBox, ptr %self, i32 0, i32 0
  %vi = load i64, ptr %vp
  %nz = icmp ne i64 %vi, 0
  br i1 %nz, label %do_rel, label %done
do_rel:
  %vptr = inttoptr i64 %vi to ptr
  call void @spec_rt_release(ptr %vptr)
  store i64 0, ptr %vp
  br label %done
done:
  ret void
}
define internal ptr @spec_rt_box_new(i64 %val, i1 %is_arc) {
  %b = call ptr @spec_rt_alloc(i64 16, ptr @__spec_box_destroy)
  %vp = getelementptr inbounds %struct.SpecBox, ptr %b, i32 0, i32 0
  store i64 %val, ptr %vp
  %ap = getelementptr inbounds %struct.SpecBox, ptr %b, i32 0, i32 1
  store i1 %is_arc, ptr %ap
  ret ptr %b
}
define internal ptr @spec_rt_box_get(ptr %b) {
  %isnull = icmp eq ptr %b, null
  br i1 %isnull, label %null_ret, label %ok
null_ret:
  ret ptr null
ok:
  %vp = getelementptr inbounds %struct.SpecBox, ptr %b, i32 0, i32 0
  %vi = load i64, ptr %vp
  %vptr = inttoptr i64 %vi to ptr
  %ap = getelementptr inbounds %struct.SpecBox, ptr %b, i32 0, i32 1
  %is_arc = load i1, ptr %ap
  %nz = icmp ne i64 %vi, 0
  %do_arc = and i1 %is_arc, %nz
  br i1 %do_arc, label %arc, label %done
arc:
  call ptr @spec_rt_retain(ptr %vptr)
  call ptr @spec_claim_pool(ptr %vptr)
  br label %done
done:
  ret ptr %vptr
}
define internal void @spec_rt_box_set(ptr %b, ptr %new_val) {
  %isnull = icmp eq ptr %b, null
  br i1 %isnull, label %done, label %ok
ok:
  %ap = getelementptr inbounds %struct.SpecBox, ptr %b, i32 0, i32 1
  %is_arc = load i1, ptr %ap
  %vp = getelementptr inbounds %struct.SpecBox, ptr %b, i32 0, i32 0
  %new_i = ptrtoint ptr %new_val to i64
  br i1 %is_arc, label %arc, label %store_val
arc:
  %nn = icmp ne ptr %new_val, null
  br i1 %nn, label %do_ret, label %chk_old
do_ret:
  call ptr @spec_rt_retain(ptr %new_val)
  br label %chk_old
chk_old:
  %old_i = load i64, ptr %vp
  %onz = icmp ne i64 %old_i, 0
  br i1 %onz, label %do_rel, label %store_val
do_rel:
  %old_p = inttoptr i64 %old_i to ptr
  call void @spec_rt_release(ptr %old_p)
  br label %store_val
store_val:
  store i64 %new_i, ptr %vp
  br label %done
done:
  ret void
}''';
	}

	local Function of String is emitMemIntrinsics(){
		return '''
define internal i64 @__spec_mem_alloc(i64 %bytes) alwaysinline {
  %le = icmp sle i64 %bytes, 0
  %sz = select i1 %le, i64 1, i64 %bytes
  %p = call ptr @calloc(i64 1, i64 %sz)
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %oom, label %ok
oom:
  call void @spec_panic(ptr @.str.oom)
  br label %ok
ok:
  %addr = ptrtoint ptr %p to i64
  ret i64 %addr
}
define internal i64 @__spec_mem_realloc(i64 %ptr, i64 %bytes) alwaysinline {
  %le = icmp sle i64 %bytes, 0
  %sz = select i1 %le, i64 1, i64 %bytes
  %old = inttoptr i64 %ptr to ptr
  %p = call ptr @realloc(ptr %old, i64 %sz)
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %oom, label %ok
oom:
  call void @spec_panic(ptr @.str.oom)
  br label %ok
ok:
  %addr = ptrtoint ptr %p to i64
  ret i64 %addr
}
define internal void @__spec_mem_free(i64 %ptr) alwaysinline {
  %nz = icmp ne i64 %ptr, 0
  br i1 %nz, label %do_free, label %done
do_free:
  %p = inttoptr i64 %ptr to ptr
  call void @free(ptr %p)
  br label %done
done:
  ret void
}
define internal void @__spec_mem_copy(i64 %dst, i64 %src, i64 %bytes) alwaysinline {
  %gt = icmp sgt i64 %bytes, 0
  br i1 %gt, label %do_cp, label %done
do_cp:
  %d = inttoptr i64 %dst to ptr
  %s = inttoptr i64 %src to ptr
  call ptr @memcpy(ptr %d, ptr %s, i64 %bytes)
  br label %done
done:
  ret void
}
define internal void @__spec_mem_move(i64 %dst, i64 %src, i64 %bytes) alwaysinline {
  %gt = icmp sgt i64 %bytes, 0
  br i1 %gt, label %do_mv, label %done
do_mv:
  %d = inttoptr i64 %dst to ptr
  %s = inttoptr i64 %src to ptr
  call ptr @memmove(ptr %d, ptr %s, i64 %bytes)
  br label %done
done:
  ret void
}
define internal void @__spec_mem_set(i64 %dst, i64 %val, i64 %bytes) alwaysinline {
  %gt = icmp sgt i64 %bytes, 0
  br i1 %gt, label %do_set, label %done
do_set:
  %d = inttoptr i64 %dst to ptr
  %v32 = trunc i64 %val to i32
  call ptr @memset(ptr %d, i32 %v32, i64 %bytes)
  br label %done
done:
  ret void
}
define internal i64 @__spec_mem_cmp(i64 %a, i64 %b, i64 %bytes) alwaysinline {
  %le = icmp sle i64 %bytes, 0
  br i1 %le, label %zero, label %do_cmp
zero:
  ret i64 0
do_cmp:
  %pa = inttoptr i64 %a to ptr
  %pb = inttoptr i64 %b to ptr
  %r32 = call i32 @memcmp(ptr %pa, ptr %pb, i64 %bytes)
  %r64 = sext i32 %r32 to i64
  ret i64 %r64
}
define internal i64 @__spec_mem_cstr_len(i64 %addr) alwaysinline {
  %eq = icmp eq i64 %addr, 0
  br i1 %eq, label %zero, label %do_len
zero:
  ret i64 0
do_len:
  %p = inttoptr i64 %addr to ptr
  %n = call i64 @strlen(ptr %p)
  ret i64 %n
}
define internal i64 @__spec_mem_load_i64(i64 %base, i64 %off) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  %v = load i64, ptr %p
  ret i64 %v
}
define internal void @__spec_mem_store_i64(i64 %base, i64 %off, i64 %val) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  store i64 %val, ptr %p
  ret void
}
define internal i64 @__spec_mem_tls_get_i64(i64 %slot) alwaysinline {
  %m = and i64 %slot, 15
  %p = getelementptr [16 x i64], ptr @_spec_tls_i64, i64 0, i64 %m
  %v = load i64, ptr %p
  ret i64 %v
}
define internal void @__spec_mem_tls_set_i64(i64 %slot, i64 %val) alwaysinline {
  %m = and i64 %slot, 15
  %p = getelementptr [16 x i64], ptr @_spec_tls_i64, i64 0, i64 %m
  store i64 %val, ptr %p
  ret void
}
define internal i64 @__spec_mem_load_i32(i64 %base, i64 %off) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  %v = load i32, ptr %p
  %ext = zext i32 %v to i64
  ret i64 %ext
}
define internal void @__spec_mem_store_i32(i64 %base, i64 %off, i64 %val) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  %tr = trunc i64 %val to i32
  store i32 %tr, ptr %p
  ret void
}
define internal i64 @__spec_mem_load_byte(i64 %base, i64 %off) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  %v = load i8, ptr %p
  %ext = zext i8 %v to i64
  ret i64 %ext
}
define internal void @__spec_mem_store_byte(i64 %base, i64 %off, i64 %val) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  %tr = trunc i64 %val to i8
  store i8 %tr, ptr %p
  ret void
}
define internal ptr @__spec_mem_load_ptr(i64 %base, i64 %off) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  %v = load ptr, ptr %p
  ret ptr %v
}
define internal void @__spec_mem_store_ptr(i64 %base, i64 %off, ptr %val) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  store ptr %val, ptr %p
  ret void
}
define internal double @__spec_mem_load_f64(i64 %base, i64 %off) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  %v = load double, ptr %p
  ret double %v
}
define internal void @__spec_mem_store_f64(i64 %base, i64 %off, double %val) alwaysinline {
  %p0 = inttoptr i64 %base to ptr
  %p = getelementptr i8, ptr %p0, i64 %off
  store double %val, ptr %p
  ret void
}
define internal i64 @__spec_mem_obj_to_addr(ptr %obj) alwaysinline {
  %a = ptrtoint ptr %obj to i64
  ret i64 %a
}
define internal ptr @__spec_mem_addr_to_obj(i64 %addr) alwaysinline {
  %p = inttoptr i64 %addr to ptr
  ret ptr %p
}
define internal i64 @__spec_mem_retain_addr(i64 %addr) alwaysinline {
  %nz = icmp ne i64 %addr, 0
  br i1 %nz, label %do_ret, label %done
do_ret:
  %p = inttoptr i64 %addr to ptr
  call ptr @spec_rt_retain(ptr %p)
  br label %done
done:
  ret i64 %addr
}
define internal void @__spec_mem_release_addr(i64 %addr) alwaysinline {
  %nz = icmp ne i64 %addr, 0
  br i1 %nz, label %do_rel, label %done
do_rel:
  %p = inttoptr i64 %addr to ptr
  call void @spec_rt_release(ptr %p)
  br label %done
done:
  ret void
}
define internal i64 @__spec_mem_claim_pool_addr(i64 %addr) alwaysinline {
  %nz = icmp ne i64 %addr, 0
  br i1 %nz, label %do_cl, label %done
do_cl:
  %p = inttoptr i64 %addr to ptr
  call ptr @spec_claim_pool(ptr %p)
  br label %done
done:
  ret i64 %addr
}
define internal ptr @__spec_mem_str_from_bytes(i64 %srcAddr, i64 %len) alwaysinline {
  %p = inttoptr i64 %srcAddr to ptr
  %s = call ptr @spec_string_from_bytes(ptr %p, i64 %len)
  ret ptr %s
}
define internal ptr @__spec_mem_intern_str(ptr %b) alwaysinline {
  %c = call ptr @spec_buf_to_cstring(ptr %b)
  %s = call ptr @spec_string_intern(ptr %c)
  ret ptr %s
}
define internal void @__spec_mem_panic(ptr %b) alwaysinline {
  %c = call ptr @spec_buf_to_cstring(ptr %b)
  call void @spec_panic(ptr %c)
  ret void
}
define internal i64 @__spec_mem_float_to_bits(double %v) alwaysinline {
  %b = bitcast double %v to i64
  ret i64 %b
}
define internal double @__spec_mem_bits_to_float(i64 %b) alwaysinline {
  %v = bitcast i64 %b to double
  ret double %v
}
define internal i64 @__spec_mem_atomic_load_i32(i64 %addr) alwaysinline {
  %p = inttoptr i64 %addr to ptr
  %v = load atomic i32, ptr %p monotonic, align 4
  %ext = zext i32 %v to i64
  ret i64 %ext
}
define internal void @__spec_mem_atomic_store_i32(i64 %addr, i64 %val) alwaysinline {
  %p = inttoptr i64 %addr to ptr
  %tr = trunc i64 %val to i32
  store atomic i32 %tr, ptr %p release, align 4
  ret void
}
define internal i64 @__spec_mem_atomic_add_i32(i64 %addr, i64 %delta) alwaysinline {
  %p = inttoptr i64 %addr to ptr
  %tr = trunc i64 %delta to i32
  %old = atomicrmw add ptr %p, i32 %tr monotonic, align 4
  %ext = zext i32 %old to i64
  ret i64 %ext
}
define internal i64 @__spec_mem_atomic_sub_i32(i64 %addr, i64 %delta) alwaysinline {
  %p = inttoptr i64 %addr to ptr
  %tr = trunc i64 %delta to i32
  %old = atomicrmw sub ptr %p, i32 %tr acq_rel, align 4
  %ext = zext i32 %old to i64
  ret i64 %ext
}
define internal i64 @__spec_mem_atomic_load_i64(i64 %addr) alwaysinline {
  %p = inttoptr i64 %addr to ptr
  %v = load atomic i64, ptr %p acquire, align 8
  ret i64 %v
}
define internal void @__spec_mem_atomic_store_i64(i64 %addr, i64 %val) alwaysinline {
  %p = inttoptr i64 %addr to ptr
  store atomic i64 %val, ptr %p release, align 8
  ret void
}
define internal i64 @__spec_mem_atomic_add_i64(i64 %addr, i64 %delta) alwaysinline {
  %p = inttoptr i64 %addr to ptr
  %old = atomicrmw add ptr %p, i64 %delta seq_cst, align 8
  ret i64 %old
}
define internal i1 @__spec_mem_atomic_cas_i64(i64 %addr, i64 %exp, i64 %des) alwaysinline {
  %p = inttoptr i64 %addr to ptr
  %res = cmpxchg ptr %p, i64 %exp, i64 %des acq_rel monotonic, align 8
  %ok = extractvalue { i64, i1 } %res, 1
  ret i1 %ok
}
define internal void @__spec_mem_call_destroy(i64 %fnAddr, i64 %objAddr) alwaysinline {
  %fn = inttoptr i64 %fnAddr to ptr
  %obj = inttoptr i64 %objAddr to ptr
  call void %fn(ptr %obj)
  ret void
}
define internal ptr @__spec_mem_call_construct(i64 %fnAddr) alwaysinline {
  %fn = inttoptr i64 %fnAddr to ptr
  %obj = call ptr %fn()
  ret ptr %obj
}
define internal i64 @__spec_mem_class_reg_addr() alwaysinline {
  %a = ptrtoint ptr @spec_class_registry to i64
  ret i64 %a
}
define internal i64 @__spec_mem_class_reg_count() alwaysinline {
  %c32 = call i32 @spec_class_registry_count()
  %c64 = zext i32 %c32 to i64
  ret i64 %c64
}
define internal i64 @__spec_mem_held_reg_addr() alwaysinline {
  %a = ptrtoint ptr @spec_held_registry to i64
  ret i64 %a
}
define internal ptr @__spec_mem_cstr_to_str(i64 %cstrAddr) alwaysinline {
  %p = inttoptr i64 %cstrAddr to ptr
  %s = call ptr @spec_string_intern(ptr %p)
  ret ptr %s
}''';
	}

	local Function of String is emitLoopControl(){
		return '''
%struct.SpecLoopControl = type { i8, ptr, ptr }
define internal ptr @LoopControl_new() alwaysinline {
  %c = call ptr @spec_rt_alloc(i64 24, ptr null)
  ret ptr %c
}
define internal void @LoopControl_stop(ptr %c) alwaysinline {
  %nn = icmp ne ptr %c, null
  br i1 %nn, label %ok, label %done
ok:
  store i8 1, ptr %c
  br label %done
done:
  ret void
}
define internal i1 @spec_loop_control_is_stopped(ptr %c) alwaysinline {
  %isnull = icmp eq ptr %c, null
  br i1 %isnull, label %no, label %ok
no:
  ret i1 0
ok:
  %v = load i8, ptr %c
  %b = icmp ne i8 %v, 0
  ret i1 %b
}
define internal void @spec_loop_control_complete(ptr %c) alwaysinline {
  %isnull = icmp eq ptr %c, null
  br i1 %isnull, label %done, label %chk
chk:
  %fnp = getelementptr inbounds %struct.SpecLoopControl, ptr %c, i32 0, i32 2
  %fn = load ptr, ptr %fnp
  %fnn = icmp ne ptr %fn, null
  br i1 %fnn, label %call, label %done
call:
  %cbp = getelementptr inbounds %struct.SpecLoopControl, ptr %c, i32 0, i32 1
  %cb = load ptr, ptr %cbp
  call void %fn(ptr %cb, ptr %c)
  br label %done
done:
  ret void
}
define internal ptr @spec_loop_control_with_callback(ptr %cb, ptr %on_complete) alwaysinline {
  %c = call ptr @spec_rt_alloc(i64 24, ptr null)
  %cbp = getelementptr inbounds %struct.SpecLoopControl, ptr %c, i32 0, i32 1
  store ptr %cb, ptr %cbp
  %fnp = getelementptr inbounds %struct.SpecLoopControl, ptr %c, i32 0, i32 2
  store ptr %on_complete, ptr %fnp
  ret ptr %c
}''';
	}

	local Function of String is emitTypeAndStringHelpers(){
		return '''
declare ptr @spec_string_intern(ptr)
declare ptr @spec_string_from_bytes(ptr, i64)
declare ptr @spec_string_concat(ptr, ptr)
declare i1 @spec_string_equals(ptr, ptr)
declare i64 @spec_string_compare(ptr, ptr)
declare ptr @spec_buf_to_cstring(ptr)
declare ptr @spec_to_string_int(i64)
declare ptr @spec_to_string_float(double)
declare ptr @spec_bytebuffer_new()
declare void @spec_map_destroy(ptr)
declare void @spec_array_destroy(ptr)
declare void @spec_buf_destroy(ptr)
declare void @spec_panic(ptr)
declare void @spec_panic_byte_range(i64)
declare void @spec_panic_cast(ptr, ptr)
declare i32 @strcmp(ptr, ptr)
declare i64 @strlen(ptr)
declare ptr @calloc(i64, i64)
declare ptr @realloc(ptr, i64)
declare void @free(ptr)
declare ptr @memcpy(ptr, ptr, i64)
declare ptr @memmove(ptr, ptr, i64)
declare ptr @memset(ptr, i32, i64)
declare i32 @memcmp(ptr, ptr, i64)
%struct.SpecBuf = type { ptr, i64, i64, i64, i32 }
define internal ptr @spec_string_copy(ptr %b) alwaysinline {
  %isnull = icmp eq ptr %b, null
  br i1 %isnull, label %empty, label %chk
chk:
  %lp = getelementptr inbounds %struct.SpecBuf, ptr %b, i32 0, i32 1
  %len = load i64, ptr %lp
  %dp = getelementptr inbounds %struct.SpecBuf, ptr %b, i32 0, i32 0
  %d = load ptr, ptr %dp
  %s = call ptr @spec_string_from_bytes(ptr %d, i64 %len)
  ret ptr %s
empty:
  %e = call ptr @spec_string_from_bytes(ptr null, i64 0)
  ret ptr %e
}
define internal i1 @__spec_cstr_eq(ptr %a, ptr %b) {
  %r = call i32 @strcmp(ptr %a, ptr %b)
  %eq = icmp eq i32 %r, 0
  ret i1 %eq
}
define internal i64 @__spec_check_byte(i64 %v) {
  %lt = icmp slt i64 %v, 0
  %gt = icmp sgt i64 %v, 255
  %bad = or i1 %lt, %gt
  br i1 %bad, label %fail, label %ok
fail:
  call void @spec_panic_byte_range(i64 %v)
  br label %ok
ok:
  ret i64 %v
}
@.str.tn_empty = private unnamed_addr constant [1 x i8] zeroinitializer
@.str.tn_map = private unnamed_addr constant [4 x i8] c"Map\00"
@.str.tn_arr = private unnamed_addr constant [6 x i8] c"Array\00"
@.str.tn_str = private unnamed_addr constant [7 x i8] c"String\00"
@.str.bool_true = private unnamed_addr constant [5 x i8] c"true\00"
@.str.bool_false = private unnamed_addr constant [6 x i8] c"false\00"
define internal ptr @spec_to_string_bool(i1 %v) alwaysinline {
  %c = select i1 %v, ptr @.str.bool_true, ptr @.str.bool_false
  %s = call ptr @spec_string_intern(ptr %c)
  ret ptr %s
}
define internal ptr @spec_type_name(ptr %obj) {
  %addr = ptrtoint ptr %obj to i64
  %bad = icmp ult i64 %addr, 4096
  br i1 %bad, label %empty, label %ok
empty:
  %e = call ptr @spec_string_intern(ptr @.str.tn_empty)
  ret ptr %e
ok:
  %h = getelementptr inbounds %struct.SpecHeader, ptr %obj, i64 -1
  %dp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 1
  %d = load ptr, ptr %dp
  %ismap = icmp eq ptr %d, @spec_map_destroy
  br i1 %ismap, label %ret_map, label %chk_arr
ret_map:
  %sm = call ptr @spec_string_intern(ptr @.str.tn_map)
  ret ptr %sm
chk_arr:
  %isarr = icmp eq ptr %d, @spec_array_destroy
  br i1 %isarr, label %ret_arr, label %chk_str
ret_arr:
  %sa = call ptr @spec_string_intern(ptr @.str.tn_arr)
  ret ptr %sa
chk_str:
  %isstr = icmp eq ptr %d, @spec_buf_destroy
  br i1 %isstr, label %ret_str, label %ret_cls
ret_str:
  %ss = call ptr @spec_string_intern(ptr @.str.tn_str)
  ret ptr %ss
ret_cls:
  %tn = load ptr, ptr %obj
  %sc = call ptr @spec_string_intern(ptr %tn)
  ret ptr %sc
}''';
	}

	local Function of String is emitMathHelpers(){
		return '''
declare double @sqrt(double)
declare double @round(double)
declare double @ceil(double)
declare double @floor(double)
declare double @fabs(double)
declare double @fmin(double, double)
declare double @fmax(double, double)
declare double @fma(double, double, double)
declare double @sin(double)
declare double @cos(double)
declare double @tan(double)
declare double @atan2(double, double)
declare double @log(double)
declare double @log2(double)
declare double @pow(double, double)
declare double @exp(double)
declare double @log10(double)
declare double @cbrt(double)
declare double @asin(double)
declare double @acos(double)
declare double @atan(double)
define internal double @spec_math_log(double %v) alwaysinline {
  %le = fcmp ole double %v, 0.0
  br i1 %le, label %z, label %ok
z:
  ret double 0.0
ok:
  %r = call double @log(double %v)
  ret double %r
}
define internal double @spec_math_log2(double %v) alwaysinline {
  %le = fcmp ole double %v, 0.0
  br i1 %le, label %z, label %ok
z:
  ret double 0.0
ok:
  %r = call double @log2(double %v)
  ret double %r
}
define internal double @spec_math_log10(double %v) alwaysinline {
  %le = fcmp ole double %v, 0.0
  br i1 %le, label %z, label %ok
z:
  ret double 0.0
ok:
  %r = call double @log10(double %v)
  ret double %r
}
declare double @spec_math_random(double, double)''';
	}

	local Function of String is emitOsPalDeclarations(){
		return '''
declare void @spec_print(ptr)
declare void @spec_print_line(ptr)
declare void @spec_error_line(ptr)
declare void @spec_read_line(ptr)
declare ptr @spec_read_bytes(i64)
declare void @spec_console_binary_mode()
declare void @spec_process_exit(i64)
declare ptr @spec_process_os_name()
declare i64 @spec_process_get_pid()
declare ptr @spec_process_getenv(ptr, ptr)
declare i64 @spec_process_execute(ptr, ptr)
declare ptr @spec_process_raw_args()
declare ptr @spec_process_measure(ptr, ptr)
declare void @spec_process_sleep(i64)
declare i64 @spec_mem_peak_kb()
declare i64 @spec_thread_count()
declare void @spec_monitor_start()
declare void @spec_monitor_stop()
declare i64 @spec_monitor_avg_mem_kb()
declare i64 @spec_monitor_peak_mem_kb()
declare i64 @spec_monitor_avg_cpu_pct()
declare i64 @spec_monitor_peak_cpu_pct()
declare i64 @spec_atomic_add(i64, i64)
declare i64 @spec_atomic_put(i64, i64)
declare i64 @spec_atomic_get(i64)
declare i64 @spec_parallel_run(i64, i64, ptr)
declare ptr @spec_parallel_sync(ptr)
declare ptr @spec_parallel_sync_with(i64, ptr)
declare i64 @spec_clock_ms()
declare i1 @spec_file_exists(ptr)
declare i1 @spec_file_remove(ptr)
declare i1 @spec_file_remove_cb(ptr, ptr)
declare ptr @spec_file_read(ptr, ptr, ptr, ptr)
declare void @spec_file_read_async(ptr, ptr, ptr, ptr)
declare i1 @spec_file_write(ptr, ptr, ptr, ptr)
declare i1 @spec_file_append(ptr, ptr, ptr, ptr)
declare void @spec_file_write_async(ptr, ptr, ptr, ptr)
declare ptr @spec_file_temp(ptr)
declare ptr @spec_file_temp_cb(ptr, ptr)
declare ptr @spec_dir_list(ptr)
declare ptr @spec_dir_list_cb(ptr, ptr)
declare ptr @spec_exe_dir()
declare i64 @spec_file_size(ptr)
declare i64 @spec_time_monotonic_ns()
declare i64 @spec_time_monotonic_us()
declare i64 @spec_time_monotonic_ms()
declare i64 @spec_time_epoch_ms()
declare i64 @spec_time_epoch_ns()
declare void @spec_time_sleep_ms(i64)
declare void @spec_time_sleep_us(i64)
declare void @spec_time_sleep_ns(i64)
declare i64 @spec_time_local_offset_sec(i64)
declare i64 @spec_time_set_timeout(i64, ptr)
declare i64 @spec_time_set_interval(i64, i64, ptr)
declare i1 @spec_time_cancel_timer(i64)
declare i64 @spec_term_width()
declare i64 @spec_term_height()
declare ptr @spec_array_new()
declare ptr @spec_array_new_object()
declare ptr @spec_map_new()
declare ptr @spec_map_new_object()
declare ptr @spec_map_new_typed(i64, i64)
declare ptr @spec_cli_args_map(i64, ptr)
declare void @spec_drain_async_tasks()
declare i64 @spec_tcp_connect(ptr, i64, i64)
declare i64 @spec_tcp_connect_cb(ptr, i64, i64, ptr)
declare i64 @spec_tcp_listen(ptr, i64, i64)
declare i64 @spec_tcp_listen_cb(ptr, i64, i64, ptr)
declare i64 @spec_socket_accept(i64)
declare i64 @spec_socket_accept_cb(i64, ptr)
declare i64 @spec_socket_send(i64, ptr)
declare i64 @spec_socket_send_cb(i64, ptr, ptr)
declare i64 @spec_socket_send_str(i64, ptr)
declare i64 @spec_socket_send_str_cb(i64, ptr, ptr)
declare ptr @spec_socket_recv(i64, i64)
declare ptr @spec_socket_recv_cb(i64, i64, ptr)
declare ptr @spec_socket_recv_str(i64, i64)
declare ptr @spec_socket_recv_str_cb(i64, i64, ptr)
declare i64 @spec_socket_close(i64)
declare i64 @spec_socket_poll(i64, i64, i64)
declare i64 @spec_socket_set_timeout(i64, i64)
declare i64 @spec_audio_open(i64, i64, i64)
declare i64 @spec_audio_open_cb(i64, i64, i64, ptr)
declare i64 @spec_audio_write(i64, ptr)
declare i64 @spec_audio_write_cb(i64, ptr, ptr)
declare i64 @spec_audio_drain(i64)
declare void @spec_audio_close(i64)''';
	}

	Function of String is emitModule(IrModule is mod){
		local String is out: ```
; Spec LLVM IR
{{self:emitArcAndPool()}}
{{self:emitClosuresAndBoxes()}}
{{self:emitMemIntrinsics()}}
{{self:emitLoopControl()}}
{{self:emitTypeAndStringHelpers()}}
{{self:emitMathHelpers()}}
{{self:emitOsPalDeclarations()}}

```;

		# Module globals (held fields, etc.)
		local Int is gi: 0;
		while({ gi < mod:globalNames:length() }, {
			local String is gn: mod:globalNames:get(index: gi, default: '');
			local IrType is gt: mod:globalTypes:get(index: gi);
			local String is giv: mod:globalInits:get(index: gi, default: 'zeroinitializer');
			out: out . '@' . gn . ' = internal global ' . self:llvmType(ty: gt) . ' ' . giv . "\n";
			gi++;
		});
		if({ mod:globalNames:length() > 0 }, { out: out . "\n"; });

		# Struct types, vtables, and reflection metadata
		local LlvmStructLayout is methodMetaLayout: LlvmStructLayout:methodMeta();
		local LlvmStructLayout is classMetaLayout: LlvmStructLayout:classMeta();
		local LlvmStructLayout is heldEntryLayout: LlvmStructLayout:heldEntry();
		local String is methodMetaType: methodMetaLayout:llvmType();
		local String is heldEntryType: heldEntryLayout:llvmType();
		local Array of String is classMetaRefs: [];
		local Array of String is heldEntryItems: [];
		local Int is si: 0;
		while({ si < mod:structs:length() }, {
			local IrStruct is st: mod:structs:get(index: si);
			local String is fieldsStr: '';
			local Int is fi: 0;
			while({ fi < st:fieldTypes:length() }, {
				if({ fi > 0 }, { fieldsStr: fieldsStr . ', '; });
				fieldsStr: fieldsStr . self:llvmType(ty: st:fieldTypes:get(index: fi));
				fi++;
			});
			out: out . '%struct.' . st:name . ' = type { ' . fieldsStr . " }\n";
			local String is qn: if({ st:qualifiedName != '' }, { st:qualifiedName }, { st:name });
			out: out . self:emitCStrGlobal(sym: '@.typename.' . st:name, val: qn);
			local Int is vtLen: st:vtableFns:length();
			if({ vtLen > 0 }, {
				local String is vtItems: '';
				local Int is vi: 0;
				while({ vi < vtLen }, {
					if({ vi > 0 }, { vtItems: vtItems . ', '; });
					local String is vfn: st:vtableFns:get(index: vi, default: 'null');
					if({ vfn == 'null' }, {
						vtItems: vtItems . 'ptr null';
					}, {
						vtItems: vtItems . 'ptr @' . vfn;
					});
					vi++;
				});
				out: out . '@.vtable.' . st:name . ' = constant [' . (vtLen as String) . ' x ptr] [' . vtItems . "]\n";
			}, {
				out: out . '@.vtable.' . st:name . " = constant [1 x ptr] zeroinitializer\n";
			});

			# Reflection metadata for this struct
			out: out . self:emitCStrGlobal(sym: '@.src.' . st:name, val: st:sourceFileBase);
			local String is basesRef: 'null';
			if({ st:baseNames:length() > 0 }, {
				local String is bItems: '';
				local Int is bi: 0;
				while({ bi < st:baseNames:length() }, {
					local String is bn: st:baseNames:get(index: bi, default: '');
					local String is bSym: '@.bname.' . st:name . '.' . (bi as String);
					out: out . self:emitCStrGlobal(sym: bSym, val: bn);
					if({ bi > 0 }, { bItems: bItems . ', '; });
					bItems: bItems . 'ptr ' . bSym;
					bi++;
				});
				out: out . '@.bases.' . st:name . ' = private constant [' . (st:baseNames:length() as String) . ' x ptr] [' . bItems . "]\n";
				basesRef: '@.bases.' . st:name;
			});

			local String is methodsRef: 'null';
			if({ st:metaMethodNames:length() > 0 }, {
				local String is mItems: '';
				local Int is mi: 0;
				while({ mi < st:metaMethodNames:length() }, {
					local String is mn: st:metaMethodNames:get(index: mi, default: '');
					local String is mSym: '@.mname.' . st:name . '.' . (mi as String);
					out: out . self:emitCStrGlobal(sym: mSym, val: mn);
					local String is mfn: st:metaMethodFns:get(index: mi, default: 'null');
					local String is mfnRef: if({ mfn == 'null' }, { 'null' }, { '@' . mfn });
					local Int is mfl: st:metaMethodFlags:get(index: mi, default: 0);
					local Int is mln: st:metaMethodLines:get(index: mi, default: 0);
					if({ mi > 0 }, { mItems: mItems . ', '; });
					mItems: mItems . methodMetaLayout:formatConst(values: [mSym, mfnRef, mfl as String, mln as String]);
					mi++;
				});
				out: out . '@.methods.' . st:name . ' = private constant [' . (st:metaMethodNames:length() as String) . ' x ' . methodMetaType . '] [' . mItems . "]\n";
				methodsRef: '@.methods.' . st:name;
			});

			local String is ctorPtr: if({ st:constructFn == 'null' }, { 'null' }, { '@' . st:constructFn });
			out: out . '@.meta.' . st:name . ' = private constant ' . classMetaLayout:formatConst(values: ['@.typename.' . st:name, '@.src.' . st:name, basesRef, st:baseNames:length() as String, ctorPtr, methodsRef, st:metaMethodNames:length() as String]) . "\n";
			classMetaRefs:add(item: 'ptr @.meta.' . st:name);

			if({ st:heldNames:length() > 0 }, {
				local String is hnItems: '';
				local String is hgItems: '';
				local Int is hi: 0;
				while({ hi < st:heldNames:length() }, {
					local String is hn: st:heldNames:get(index: hi, default: '');
					local String is hSym: '@.hname.' . st:name . '.' . (hi as String);
					out: out . self:emitCStrGlobal(sym: hSym, val: hn);
					local String is hg: st:heldGetters:get(index: hi, default: 'null');
					local String is hgPtr: if({ hg == 'null' }, { 'null' }, { '@' . hg });
					if({ hi > 0 }, {
						hnItems: hnItems . ', ';
						hgItems: hgItems . ', ';
					});
					hnItems: hnItems . 'ptr ' . hSym;
					hgItems: hgItems . 'ptr ' . hgPtr;
					hi++;
				});
				out: out . '@.held_names.' . st:name . ' = private constant [' . (st:heldNames:length() as String) . ' x ptr] [' . hnItems . "]\n";
				out: out . '@.held_getters.' . st:name . ' = private constant [' . (st:heldGetters:length() as String) . ' x ptr] [' . hgItems . "]\n";
				heldEntryItems:add(item: heldEntryLayout:formatConst(values: ['@.typename.' . st:name, '@.held_names.' . st:name, st:heldNames:length() as String, '@.held_getters.' . st:name]));
			});
			si++;
		});
		if({ mod:structs:length() > 0 }, { out: out . "\n"; });

		# Global class and held registries
		local Int is cmCount: classMetaRefs:length();
		if({ cmCount > 0 }, {
			local String is cmList: '';
			local Int is ci: 0;
			while({ ci < cmCount }, {
				if({ ci > 0 }, { cmList: cmList . ', '; });
				cmList: cmList . classMetaRefs:get(index: ci, default: 'ptr null');
				ci++;
			});
			out: out . '@spec_class_registry = constant [' . (cmCount as String) . ' x ptr] [' . cmList . "]\n";
		}, {
			out: out . "@spec_class_registry = constant [1 x ptr] zeroinitializer\n";
		});
		out: out . 'define i32 @spec_class_registry_count() {' . "\n  ret i32 " . (cmCount as String) . "\n}\n";

		heldEntryItems:add(item: heldEntryType . ' zeroinitializer');
		local String is heList: '';
		local Int is hei: 0;
		while({ hei < heldEntryItems:length() }, {
			if({ hei > 0 }, { heList: heList . ', '; });
			heList: heList . heldEntryItems:get(index: hei, default: '');
			hei++;
		});
		out: out . '@spec_held_registry = constant [' . (heldEntryItems:length() as String) . ' x ' . heldEntryType . '] [' . heList . "]\n\n";

		# String literal globals (null-terminated)
		local Int is li: 0;
		while({ li < mod:stringLiterals:length() }, {
			local String is raw: mod:stringLiterals:get(index: li, default: '');
			local Int is byteLen: raw:length() + 1;
			local String is esc: self:escapeLlvmBytes(s: raw);
			out: out . '@.str.' . (li as String) . ' = private unnamed_addr constant [' . (byteLen as String) . ' x i8] c"' . esc . "\\00\"\n";
			li++;
		});
		if({ mod:stringLiterals:length() > 0 }, { out: out . "\n"; });

		# Functions
		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			out: out . self:emitFunction(fn: mod:functions:get(index: fi)) . "\n";
			fi++;
		});
		return out;
	}

	local Function of String is emitCStrGlobal(String is sym, String is val){
		local Int is byteLen: val:length() + 1;
		local String is esc: self:escapeLlvmBytes(s: val);
		return sym . ' = private unnamed_addr constant [' . (byteLen as String) . ' x i8] c"' . esc . "\\00\"\n";
	}

	local Function of String is escapeLlvmBytes(String is s){
		local String is hex: '0123456789ABCDEF';
		local String is res: '';
		local Int is len: Buf:bufLength(b: s);
		local Int is i: 0;
		while({ i < len }, {
			local Int is b: Buf:bufGetByte(b: s, idx: i, def: 0);
			if({ b < 32 || b >= 127 || b == 34 || b == 92 }, {
				local Int is hi: (b >> 4) & 15;
				local Int is lo: b & 15;
				res: res . '\\' . Buf:stringSubstring(b: hex, start: hi, end: hi + 1) . Buf:stringSubstring(b: hex, start: lo, end: lo + 1);
			}, {
				res: res . Buf:stringSubstring(b: s, start: i, end: i + 1);
			});
			i++;
		});
		return res;
	}

	local Function of Boolean is blockCallsFn(IrBlock is blk, String is fnName){
		local Int is ii: 0;
		while({ ii < blk:insts:length() }, {
			local Boolean is hit: match(on: blk:insts:get(index: ii), when: [
				IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
					return callee == fnName;
				},
				else: { return false; }
			]);
			if({ hit }, { return true; });
			ii++;
		});
		return false;
	}

	local Function of Boolean is fnIsSmallAcyclicLeaf(IrFunction is fn){
		if({ fn:blocks:length() == 0 || fn:blocks:length() > 6 || fn:name == 'main' }, { return false; });
		local Map of String to Int is blkIdx: Map:init();
		local Int is totalInsts: 0;
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			blkIdx:set(key: blk:label, value: bi);
			totalInsts: totalInsts + blk:insts:length();
			if({ totalInsts > 40 }, { return false; });
			if({ self:blockCallsFn(blk: blk, fnName: fn:name) }, { return false; });
			bi++;
		});
		bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is n: blk:insts:length();
			if({ n > 0 }, {
				local Boolean is backedge: match(on: blk:insts:get(index: n - 1), when: [
					IrInst:Br: local Function of Boolean(String is target){
						return blkIdx:get(key: target, default: 0) <= bi;
					},
					IrInst:CondBr: local Function of Boolean(String is cond, String is thenLabel, String is elseLabel){
						return blkIdx:get(key: thenLabel, default: 0) <= bi || blkIdx:get(key: elseLabel, default: 0) <= bi;
					},
					else: { return false; }
				]);
				if({ backedge }, { return false; });
			});
			bi++;
		});
		return true;
	}

	local Function of String is emitFunction(IrFunction is fn){
		local String is retStr: self:llvmType(ty: fn:retType);
		local String is paramsStr: '';
		local Int is pi: 0;
		while({ pi < fn:params:length() }, {
			if({ pi > 0 }, { paramsStr: paramsStr . ', '; });
			local IrParam is p: fn:params:get(index: pi);
			paramsStr: paramsStr . self:llvmType(ty: p:ty) . ' ' . p:name;
			pi++;
		});

		if({ fn:isExternal }, {
			return 'declare ' . retStr . ' @' . fn:name . '(' . paramsStr . ")\n";
		});

		local String is inlineAttr: '';
		if({ self:fnIsSmallAcyclicLeaf(fn: fn) }, {
			inlineAttr: ' alwaysinline';
		});

		local String is out: 'define ' . retStr . ' @' . fn:name . '(' . paramsStr . ')' . inlineAttr . " {\n";
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			out: out . blk:label . ":\n";
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				out: out . '  ' . self:emitInst(inst: blk:insts:get(index: ii)) . "\n";
				ii++;
			});
			bi++;
		});
		out: out . "}\n";
		return out;
	}

	local Function of String is emitInst(IrInst is inst){
		return match(on: inst, when: [
			IrInst:ConstInt: local Function of String(String is dst, Int is value){
				return dst . ' = add i64 0, ' . (value as String);
			},
			IrInst:ConstFloat: local Function of String(String is dst, String is text){
				return dst . ' = fadd double 0.0, ' . text;
			},
			IrInst:ConstBool: local Function of String(String is dst, Boolean is value){
				if({ value }, { return dst . ' = add i1 0, 1'; });
				return dst . ' = add i1 0, 0';
			},
			IrInst:ConstString: local Function of String(String is dst, Int is strId){
				return dst . ' = call ptr @spec_string_intern(ptr @.str.' . (strId as String) . ')';
			},
			IrInst:Alloca: local Function of String(String is slot, IrType is ty){
				return slot . ' = alloca ' . self:llvmType(ty: ty);
			},
			IrInst:Load: local Function of String(String is dst, String is slot, IrType is ty){
				local String is t: self:llvmType(ty: ty);
				return dst . ' = load ' . t . ', ptr ' . slot;
			},
			IrInst:Store: local Function of String(String is slot, String is val, IrType is ty){
				local String is t: self:llvmType(ty: ty);
				return 'store ' . t . ' ' . val . ', ptr ' . slot;
			},
			IrInst:BinOp: local Function of String(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
				local String is t: self:llvmType(ty: ty);
				local String is llvmOp: self:llvmBinOp(op: op, ty: ty);
				return dst . ' = ' . llvmOp . ' ' . t . ' ' . lhs . ', ' . rhs;
			},
			IrInst:UnaryOp: local Function of String(String is dst, String is op, String is operand, IrType is ty){
				if({ op == '-' }, {
					if({ ty == IrType:F64 }, { return dst . ' = fneg double ' . operand; });
					return dst . ' = sub i64 0, ' . operand;
				});
				if({ op == '!' }, {
					return dst . ' = xor i1 ' . operand . ', 1';
				});
				if({ op == '~' }, {
					return dst . ' = xor i64 ' . operand . ', -1';
				});
				return dst . ' = add i64 0, ' . operand;
			},
			IrInst:Cmp: local Function of String(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
				local String is t: self:llvmType(ty: ty);
				if({ ty == IrType:F64 }, {
					local String is fpred: 'oeq';
					if({ op == '!=' }, { fpred: 'one'; });
					if({ op == '<' }, { fpred: 'olt'; });
					if({ op == '<=' }, { fpred: 'ole'; });
					if({ op == '>' }, { fpred: 'ogt'; });
					if({ op == '>=' }, { fpred: 'oge'; });
					return dst . ' = fcmp ' . fpred . ' double ' . lhs . ', ' . rhs;
				});
				local String is ipred: 'eq';
				if({ op == '!=' }, { ipred: 'ne'; });
				if({ op == '<' }, { ipred: 'slt'; });
				if({ op == '<=' }, { ipred: 'sle'; });
				if({ op == '>' }, { ipred: 'sgt'; });
				if({ op == '>=' }, { ipred: 'sge'; });
				return dst . ' = icmp ' . ipred . ' ' . t . ' ' . lhs . ', ' . rhs;
			},
			IrInst:IrCall: local Function of String(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
				local String is argsStr: '';
				local Int is ai: 0;
				while({ ai < args:length() }, {
					if({ ai > 0 }, { argsStr: argsStr . ', '; });
					argsStr: argsStr . self:llvmType(ty: argTypes:get(index: ai)) . ' ' . args:get(index: ai, default: '');
					ai++;
				});
				local String is rt: self:llvmType(ty: retType);
				if({ hasDst }, {
					return dst . ' = call ' . rt . ' @' . callee . '(' . argsStr . ')';
				});
				return 'call ' . rt . ' @' . callee . '(' . argsStr . ')';
			},
			IrInst:IndirectCall: local Function of String(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, Array of IrType is argTypes, Array of String is args){
				local String is argsStr: '';
				local Int is ai: 0;
				while({ ai < args:length() }, {
					if({ ai > 0 }, { argsStr: argsStr . ', '; });
					argsStr: argsStr . self:llvmType(ty: argTypes:get(index: ai)) . ' ' . args:get(index: ai, default: '');
					ai++;
				});
				local String is rt: self:llvmType(ty: retType);
				if({ hasDst }, {
					return dst . ' = call ' . rt . ' ' . fnPtr . '(' . argsStr . ')';
				});
				return 'call ' . rt . ' ' . fnPtr . '(' . argsStr . ')';
			},
			IrInst:GlobalAddr: local Function of String(String is dst, String is globalName){
				return dst . ' = getelementptr i8, ptr @' . globalName . ', i64 0';
			},
			IrInst:AllocObj: local Function of String(String is dst, String is structName, String is destroyFn){
				local LlvmStructLayout is hdr: LlvmStructLayout:objHeader();
				local String is tnIdx: hdr:fieldIndex(name: 'type_name') as String;
				local String is vtIdx: hdr:fieldIndex(name: 'vtable') as String;
				local String is szPtr: dst . '_szp';
				local String is szVal: dst . '_sz';
				local String is tnPtr: dst . '_tnp';
				local String is vtPtr: dst . '_vtp';
				return szPtr . ' = getelementptr %struct.' . structName . ", ptr null, i32 1\n  "
					. szVal . ' = ptrtoint ptr ' . szPtr . " to i64\n  "
					. dst . ' = call ptr @spec_rt_alloc(i64 ' . szVal . ', ptr ' . destroyFn . ")\n  "
					. tnPtr . ' = getelementptr inbounds %struct.' . structName . ', ptr ' . dst . ', i32 0, i32 ' . tnIdx . "\n  "
					. 'store ptr @.typename.' . structName . ', ptr ' . tnPtr . "\n  "
					. vtPtr . ' = getelementptr inbounds %struct.' . structName . ', ptr ' . dst . ', i32 0, i32 ' . vtIdx . "\n  "
					. 'store ptr @.vtable.' . structName . ', ptr ' . vtPtr;
			},
			IrInst:FieldPtr: local Function of String(String is dst, String is objPtr, String is structName, Int is fieldIndex){
				return dst . ' = getelementptr inbounds %struct.' . structName . ', ptr ' . objPtr . ', i32 0, i32 ' . (fieldIndex as String);
			},
			IrInst:PtrElem: local Function of String(String is dst, String is basePtr, Int is index){
				return dst . ' = getelementptr ptr, ptr ' . basePtr . ', i64 ' . (index as String);
			},
			IrInst:IrCast: local Function of String(String is dst, String is val, IrType is fromType, IrType is toType){
				if({ fromType == IrType:I64 && toType == IrType:F64 }, { return dst . ' = sitofp i64 ' . val . ' to double'; });
				if({ fromType == IrType:F64 && toType == IrType:I64 }, { return dst . ' = fptosi double ' . val . ' to i64'; });
				if({ (fromType == IrType:I64 || fromType == IrType:I1) && toType == IrType:Ptr }, {
					return dst . ' = inttoptr ' . self:llvmType(ty: fromType) . ' ' . val . ' to ptr';
				});
				if({ fromType == IrType:Ptr && (toType == IrType:I64 || toType == IrType:I1) }, {
					return dst . ' = ptrtoint ptr ' . val . ' to ' . self:llvmType(ty: toType);
				});
				if({ fromType == IrType:F64 && toType == IrType:Ptr }, {
					local String is bits: dst . '_bits';
					return bits . " = bitcast double " . val . " to i64\n  "
						. dst . ' = inttoptr i64 ' . bits . ' to ptr';
				});
				if({ fromType == IrType:Ptr && toType == IrType:F64 }, {
					local String is bits: dst . '_bits';
					return bits . " = ptrtoint ptr " . val . " to i64\n  "
						. dst . ' = bitcast i64 ' . bits . ' to double';
				});
				if({ fromType == IrType:I1 && toType == IrType:I64 }, { return dst . ' = zext i1 ' . val . ' to i64'; });
				if({ fromType == IrType:I64 && toType == IrType:I1 }, { return dst . ' = icmp ne i64 ' . val . ', 0'; });
				return dst . ' = bitcast ' . self:llvmType(ty: fromType) . ' ' . val . ' to ' . self:llvmType(ty: toType);
			},
			IrInst:Retain: local Function of String(String is val){
				return 'call ptr @spec_rt_retain(ptr ' . val . ')';
			},
			IrInst:Release: local Function of String(String is val){
				return 'call void @spec_rt_release(ptr ' . val . ')';
			},
			IrInst:Ret: local Function of String(Boolean is hasVal, String is val, IrType is ty){
				if({ hasVal }, {
					return 'ret ' . self:llvmType(ty: ty) . ' ' . val;
				});
				return 'ret void';
			},
			IrInst:Br: local Function of String(String is target){
				return 'br label %' . target;
			},
			IrInst:CondBr: local Function of String(String is cond, String is thenLabel, String is elseLabel){
				return 'br i1 ' . cond . ', label %' . thenLabel . ', label %' . elseLabel;
			}
		]);
	}

	local Function of String is llvmBinOp(String is op, IrType is ty){
		if({ ty == IrType:F64 }, {
			if({ op == '+' }, { return 'fadd'; });
			if({ op == '-' }, { return 'fsub'; });
			if({ op == '*' }, { return 'fmul'; });
			if({ op == '/' }, { return 'fdiv'; });
			return 'fadd';
		});
		if({ op == '+' }, { return 'add'; });
		if({ op == '-' }, { return 'sub'; });
		if({ op == '*' }, { return 'mul'; });
		if({ op == '/' }, { return 'sdiv'; });
		if({ op == '%' }, { return 'srem'; });
		if({ op == '&' || op == '&&' }, { return 'and'; });
		if({ op == '|' || op == '||' }, { return 'or'; });
		if({ op == '^' }, { return 'xor'; });
		if({ op == '<<' }, { return 'shl'; });
		if({ op == '>>' }, { return 'ashr'; });
		return 'add';
	}
}
