#! Package base:compiler:llvm
#! Emits the target-agnostic LLVM IR runtime prelude (ARC, claim pool,
#! closures, boxes, Mem intrinsics, LoopControl, string/container constructors,
#! math intrinsics, CLI arguments, and atomic slots).

Class is LlvmRuntimePrelude{
	namespace: ['base', 'compiler', 'llvm'];

	replace Function is init(){
	}

	Function of Str is emitArcAndPool(){
		return '''
@_spec_tls_i64 = internal thread_local global [16 x i64] zeroinitializer
@g_spec_active_threads = external global i32
@.str.oom = private unnamed_addr constant [14 x i8] c"Out of memory\00"
%struct.SpecHeader = type { i32, i32, ptr }
define internal noalias ptr @spec_rt_alloc(i64 %size, ptr %destroy) alwaysinline {
  %da = ptrtoint ptr %destroy to i64
  %oa = call i64 @Arc_allocObj(ptr null, i64 %size, i64 %da)
  %obj = inttoptr i64 %oa to ptr
  ret ptr %obj
}
define internal i64 @_spec_rt_alloc_kinded(i64 %size, i64 %kind) alwaysinline {
  %isone = icmp eq i64 %kind, 1
  %dp = select i1 %isone, ptr @HashTable_mapDestroy, ptr null
  %da = ptrtoint ptr %dp to i64
  %oa = call i64 @Arc_allocObj(ptr null, i64 %size, i64 %da)
  ret i64 %oa
}
@.str.uaf_retain = private unnamed_addr constant [36 x i8] c"arc: retain of already-freed object\00"
@.str.uaf_release = private unnamed_addr constant [37 x i8] c"arc: release of already-freed object\00"
define internal ptr @spec_rt_retain(ptr %obj) alwaysinline {
  %isnull = icmp eq ptr %obj, null
  br i1 %isnull, label %done, label %chk_mt
chk_mt:
  %h = getelementptr inbounds %struct.SpecHeader, ptr %obj, i64 -1
  %dfp = getelementptr inbounds i8, ptr %h, i64 8
  %df = load i64, ptr %dfp, align 8
  %is_freed = icmp eq i64 %df, 73083690742142
  br i1 %is_freed, label %uaf, label %chk_mt_ok
uaf:
  call void @spec_panic(ptr @.str.uaf_retain)
  unreachable
chk_mt_ok:
  %mt = load atomic i32, ptr @g_spec_active_threads acquire, align 4
  %is_mt = icmp sgt i32 %mt, 0
  br i1 %is_mt, label %atomic_path, label %fast_path
fast_path:
  %sfp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 1
  %sf = load i32, ptr %sfp, align 4
  %imm = and i32 %sf, 1
  %is_imm = icmp ne i32 %imm, 0
  br i1 %is_imm, label %done, label %fast_inc
fast_inc:
  %rc = load i32, ptr %h, align 4
  %rc1 = add i32 %rc, 1
  store i32 %rc1, ptr %h, align 4
  br label %done
atomic_path:
  %sfp2 = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 1
  %sf2 = load atomic i32, ptr %sfp2 monotonic, align 4
  %imm2 = and i32 %sf2, 1
  %is_imm2 = icmp ne i32 %imm2, 0
  br i1 %is_imm2, label %done, label %atomic_inc
atomic_inc:
  %unused = atomicrmw add ptr %h, i32 1 monotonic, align 4
  br label %done
done:
  ret ptr %obj
}
define internal void @spec_rt_release(ptr %obj) alwaysinline {
  %isnull = icmp eq ptr %obj, null
  br i1 %isnull, label %done, label %chk_mt
chk_mt:
  %h = getelementptr inbounds %struct.SpecHeader, ptr %obj, i64 -1
  %dfp = getelementptr inbounds i8, ptr %h, i64 8
  %df = load i64, ptr %dfp, align 8
  %is_freed = icmp eq i64 %df, 73083690742142
  br i1 %is_freed, label %uaf, label %chk_mt_ok
uaf:
  call void @spec_panic(ptr @.str.uaf_release)
  unreachable
chk_mt_ok:
  %mt = load atomic i32, ptr @g_spec_active_threads acquire, align 4
  %is_mt = icmp sgt i32 %mt, 0
  br i1 %is_mt, label %atomic_path, label %fast_path
fast_path:
  %sfp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 1
  %sf = load i32, ptr %sfp, align 4
  %imm = and i32 %sf, 1
  %is_imm = icmp ne i32 %imm, 0
  br i1 %is_imm, label %done, label %fast_dec
fast_dec:
  %rc = load i32, ptr %h, align 4
  %is_one = icmp eq i32 %rc, 1
  br i1 %is_one, label %fast_destroy, label %fast_chk0
fast_destroy:
  store i32 0, ptr %h, align 4
  %oa1 = ptrtoint ptr %obj to i64
  call void @Arc_destroyObj(ptr null, i64 %oa1)
  br label %done
fast_chk0:
  %is_zero = icmp eq i32 %rc, 0
  br i1 %is_zero, label %reentrant_slow, label %fast_store
fast_store:
  %rc1 = sub i32 %rc, 1
  store i32 %rc1, ptr %h, align 4
  br label %done
atomic_path:
  %sfp2 = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 1
  %sf2 = load atomic i32, ptr %sfp2 monotonic, align 4
  %imm2 = and i32 %sf2, 1
  %is_imm2 = icmp ne i32 %imm2, 0
  br i1 %is_imm2, label %done, label %atomic_chk0
atomic_chk0:
  %rc0 = load atomic i32, ptr %h monotonic, align 4
  %is0 = icmp eq i32 %rc0, 0
  br i1 %is0, label %reentrant_slow, label %atomic_dec
atomic_dec:
  %old = atomicrmw sub ptr %h, i32 1 acq_rel, align 4
  %is1 = icmp eq i32 %old, 1
  br i1 %is1, label %atomic_destroy, label %done
atomic_destroy:
  %oa2 = ptrtoint ptr %obj to i64
  call void @Arc_destroyObj(ptr null, i64 %oa2)
  br label %done
reentrant_slow:
  %oa0 = ptrtoint ptr %obj to i64
  call void @Arc_release(ptr null, i64 %oa0)
  br label %done
done:
  ret void
}
define internal i64 @spec_pool_frame() alwaysinline {
  %t = call i64 @Pool_poolFrame(ptr null)
  ret i64 %t
}
define internal void @spec_pool_release_to(i64 %mark) alwaysinline {
  call void @Pool_poolReleaseTo(ptr null, i64 %mark)
  ret void
}
define internal void @spec_pool_release_to_transfer(i64 %mark, ptr %keep) alwaysinline {
  %ka = ptrtoint ptr %keep to i64
  call void @Pool_releaseToTransferring(ptr null, i64 %mark, i64 %ka)
  ret void
}
define internal void @spec_pool_unclaim_addr(i64 %addr) alwaysinline {
  call void @Pool_unclaimAddr(ptr null, i64 %addr)
  ret void
}
define internal ptr @spec_claim_pool(ptr %obj) alwaysinline {
  %oa = ptrtoint ptr %obj to i64
  %ra = call i64 @Pool_claimPool(ptr null, i64 %oa)
  %res = inttoptr i64 %ra to ptr
  ret ptr %res
}
define void @spec_pool_thread_cleanup() nounwind {
  call void @Cleanup_threadCleanup(ptr null)
  call void @Pool_threadCleanup(ptr null)
  ret void
}''';
	}

	Function of Str is emitClosuresAndBoxes(){
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
  call ptr @spec_claim_pool(ptr %old_p)
  br label %store_val
store_val:
  store i64 %new_i, ptr %vp
  br label %done
done:
  ret void
}''';
	}

	Function of Str is emitMemIntrinsics(){
		return '''
define internal i64 @__spec_mem_alloc(i64 %bytes) alwaysinline {
  %a = call i64 @Heap_allocMem(ptr null, i64 %bytes)
  ret i64 %a
}
define internal i64 @__spec_mem_realloc(i64 %ptr, i64 %bytes) alwaysinline {
  %a = call i64 @Heap_reallocMem(ptr null, i64 %ptr, i64 %bytes)
  ret i64 %a
}
define internal void @__spec_mem_free(i64 %ptr) alwaysinline {
  call void @Heap_freeMem(ptr null, i64 %ptr)
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
  %b = call noalias ptr @spec_rt_alloc(i64 64, ptr @spec_buf_destroy)
  %es_p = getelementptr inbounds i8, ptr %b, i64 24
  store i64 1, ptr %es_p, align 8
  %has_src = icmp ne i64 %srcAddr, 0
  %pos_len = icmp sgt i64 %len, 0
  %non_empty = and i1 %has_src, %pos_len
  br i1 %non_empty, label %chk_sbo, label %empty
empty:
  %len_p0 = getelementptr inbounds i8, ptr %b, i64 8
  store i64 0, ptr %len_p0, align 8
  %ib0 = getelementptr inbounds i8, ptr %b, i64 36
  store ptr %ib0, ptr %b, align 8
  %cap_p0 = getelementptr inbounds i8, ptr %b, i64 16
  store i64 24, ptr %cap_p0, align 8
  ret ptr %b
chk_sbo:
  %len_p = getelementptr inbounds i8, ptr %b, i64 8
  store i64 %len, ptr %len_p, align 8
  %src = inttoptr i64 %srcAddr to ptr
  %fits_sbo = icmp ule i64 %len, 23
  br i1 %fits_sbo, label %sbo, label %heap
sbo:
  %ib1 = getelementptr inbounds i8, ptr %b, i64 36
  store ptr %ib1, ptr %b, align 8
  %cap_p1 = getelementptr inbounds i8, ptr %b, i64 16
  store i64 24, ptr %cap_p1, align 8
  call ptr @memcpy(ptr %ib1, ptr %src, i64 %len)
  ret ptr %b
heap:
  %need = add i64 %len, 1
  %hda = call i64 @__spec_mem_alloc(i64 %need)
  %hd = inttoptr i64 %hda to ptr
  store ptr %hd, ptr %b, align 8
  %cap_p2 = getelementptr inbounds i8, ptr %b, i64 16
  store i64 %need, ptr %cap_p2, align 8
  %ck_p2 = getelementptr inbounds i8, ptr %b, i64 40
  store i64 0, ptr %ck_p2, align 8
  call ptr @memcpy(ptr %hd, ptr %src, i64 %len)
  %nul_p = getelementptr inbounds i8, ptr %hd, i64 %len
  store i8 0, ptr %nul_p, align 1
  ret ptr %b
}
define internal ptr @__spec_mem_intern_str(ptr %b) alwaysinline {
  %c = call ptr @spec_buf_to_cstring(ptr %b)
  %s = call ptr @spec_string_intern(ptr %c)
  ret ptr %s
}
define internal ptr @__spec_intern_cached(ptr %lit, ptr %slot) alwaysinline {
  %c = load atomic ptr, ptr %slot acquire, align 8
  %ok = icmp ne ptr %c, null
  br i1 %ok, label %hit, label %miss
hit:
  ret ptr %c
miss:
  %s = call ptr @spec_string_intern(ptr %lit)
  store atomic ptr %s, ptr %slot release, align 8
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

	Function of Str is emitTypeAndStringHelpers(){
		return '''
@_spec_intern_state = internal global [2 x i64] zeroinitializer, align 8
define internal ptr @spec_string_intern(ptr %c) nounwind {
  %ca = ptrtoint ptr %c to i64
  %sa = ptrtoint ptr @_spec_intern_state to i64
  %ra = call i64 @Intern_internCstr(ptr null, i64 %ca, i64 %sa)
  %s = inttoptr i64 %ra to ptr
  ret ptr %s
}
declare void @spec_pal_format_float(double, i64) nounwind
declare i64 @spec_pal_random_bytes(i64, i64) nounwind
declare i64 @spec_pal_slab_alloc() nounwind
declare void @spec_pal_slab_free(i64) nounwind
declare i64 @spec_pal_vm_alloc(i64) nounwind
declare void @spec_pal_vm_free(i64, i64) nounwind
declare i64 @spec_pal_vm_realloc(i64, i64, i64) nounwind
define internal i64 @__spec_mem_slab_alloc() alwaysinline {
  %a = call i64 @spec_pal_slab_alloc()
  %isnull = icmp eq i64 %a, 0
  br i1 %isnull, label %oom, label %ok
oom:
  call void @spec_panic(ptr @.str.oom)
  br label %ok
ok:
  ret i64 %a
}
define internal void @__spec_mem_slab_free(i64 %addr) alwaysinline {
  call void @spec_pal_slab_free(i64 %addr)
  ret void
}
define internal i64 @__spec_mem_vm_alloc(i64 %bytes) alwaysinline {
  %a = call i64 @spec_pal_vm_alloc(i64 %bytes)
  %isnull = icmp eq i64 %a, 0
  br i1 %isnull, label %oom, label %ok
oom:
  call void @spec_panic(ptr @.str.oom)
  br label %ok
ok:
  ret i64 %a
}
define internal void @__spec_mem_vm_free(i64 %addr, i64 %bytes) alwaysinline {
  call void @spec_pal_vm_free(i64 %addr, i64 %bytes)
  ret void
}
define internal i64 @__spec_mem_vm_realloc(i64 %addr, i64 %oldBytes, i64 %newBytes) alwaysinline {
  %a = call i64 @spec_pal_vm_realloc(i64 %addr, i64 %oldBytes, i64 %newBytes)
  %isnull = icmp eq i64 %a, 0
  br i1 %isnull, label %oom, label %ok
oom:
  call void @spec_panic(ptr @.str.oom)
  br label %ok
ok:
  ret i64 %a
}
define internal i1 @__spec_mem_is_multithreaded() alwaysinline {
  %mt = load atomic i32, ptr @g_spec_active_threads acquire, align 4
  %is_mt = icmp sgt i32 %mt, 0
  ret i1 %is_mt
}
define internal ptr @spec_to_string_float(double %v) nounwind {
  %buf = alloca [64 x i8], align 8
  %ba = ptrtoint ptr %buf to i64
  call void @spec_pal_format_float(double %v, i64 %ba)
  %s = call ptr @spec_string_intern(ptr %buf)
  ret ptr %s
}
declare void @spec_panic(ptr) noreturn nounwind
declare void @spec_panic_byte_range(i64) noreturn nounwind
declare void @spec_panic_cast(ptr, ptr) noreturn nounwind
declare i32 @strcmp(ptr nocapture readonly, ptr nocapture readonly) nounwind willreturn memory(read)
declare i64 @strlen(ptr nocapture readonly) nounwind willreturn memory(read)
declare noalias ptr @malloc(i64) nounwind willreturn allockind("alloc,uninitialized") allocsize(0)
declare noalias ptr @calloc(i64, i64) nounwind willreturn allockind("alloc,zeroed") allocsize(0, 1)
declare ptr @realloc(ptr, i64) nounwind willreturn allockind("realloc") allocsize(1)
declare void @free(ptr) nounwind willreturn allockind("free")
declare ptr @memcpy(ptr noalias returned writeonly, ptr noalias nocapture readonly, i64) nounwind willreturn
declare ptr @memmove(ptr returned, ptr nocapture readonly, i64) nounwind willreturn
declare ptr @memset(ptr returned writeonly, i32, i64) nounwind willreturn
declare i32 @memcmp(ptr nocapture readonly, ptr nocapture readonly, i64) nounwind willreturn memory(read)
%struct.SpecBuf = type { ptr, i64, i64, i64, i32 }
@.str.tn_empty = private unnamed_addr constant [1 x i8] zeroinitializer
define void @spec_buf_destroy(ptr %self) nounwind {
  %isnull = icmp eq ptr %self, null
  br i1 %isnull, label %done, label %chk
chk:
  %d = load ptr, ptr %self, align 8
  %dnull = icmp eq ptr %d, null
  br i1 %dnull, label %done, label %chk_sbo
chk_sbo:
  %inl = getelementptr inbounds i8, ptr %self, i64 36
  %is_sbo = icmp eq ptr %d, %inl
  br i1 %is_sbo, label %done, label %do_free
do_free:
  %da = ptrtoint ptr %d to i64
  call void @__spec_mem_free(i64 %da)
  store ptr null, ptr %self, align 8
  %ck_p = getelementptr inbounds i8, ptr %self, i64 40
  %ck = load i64, ptr %ck_p, align 8
  %has_ck = icmp sgt i64 %ck, 0
  br i1 %has_ck, label %free_ck, label %done
free_ck:
  call void @__spec_mem_free(i64 %ck)
  store i64 0, ptr %ck_p, align 8
  br label %done
done:
  ret void
}
define internal ptr @spec_buf_to_cstring(ptr %b) alwaysinline {
  %isnull = icmp eq ptr %b, null
  br i1 %isnull, label %empty, label %chk
chk:
  %lp = getelementptr inbounds i8, ptr %b, i64 8
  %len = load i64, ptr %lp, align 8
  %is_zero = icmp eq i64 %len, 0
  br i1 %is_zero, label %empty, label %ok
ok:
  %d = load ptr, ptr %b, align 8
  ret ptr %d
empty:
  ret ptr @.str.tn_empty
}
define internal ptr @spec_string_copy(ptr %b) alwaysinline {
  %isnull = icmp eq ptr %b, null
  br i1 %isnull, label %empty, label %chk
chk:
  %lp = getelementptr inbounds %struct.SpecBuf, ptr %b, i32 0, i32 1
  %len = load i64, ptr %lp
  %dp = getelementptr inbounds %struct.SpecBuf, ptr %b, i32 0, i32 0
  %d = load ptr, ptr %dp
  %da = ptrtoint ptr %d to i64
  %s = call ptr @__spec_mem_str_from_bytes(i64 %da, i64 %len)
  ret ptr %s
empty:
  %e = call ptr @__spec_mem_str_from_bytes(i64 0, i64 0)
  ret ptr %e
}
define internal ptr @spec_string_concat(ptr %a, ptr %b) {
  %a_null = icmp eq ptr %a, null
  br i1 %a_null, label %copy_a, label %chk_uniq
chk_uniq:
  %h = getelementptr inbounds %struct.SpecHeader, ptr %a, i64 -1
  %sfp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 1
  %sf = load atomic i32, ptr %sfp monotonic, align 4
  %imm = and i32 %sf, 1
  %is_imm = icmp ne i32 %imm, 0
  br i1 %is_imm, label %copy_a, label %chk_rc
chk_rc:
  %rcp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 0
  %rc = load atomic i32, ptr %rcp monotonic, align 4
  %is_one = icmp eq i32 %rc, 1
  br i1 %is_one, label %inplace, label %copy_a
inplace:
  call void @Buf_bufAppendBuf(ptr null, ptr %a, ptr %b)
  ret ptr %a
copy_a:
  %ac = call ptr @spec_string_copy(ptr %a)
  call void @Buf_bufAppendBuf(ptr null, ptr %ac, ptr %b)
  call ptr @spec_claim_pool(ptr %ac)
  ret ptr %ac
}
define internal noalias ptr @Vector_vecNew() alwaysinline {
  %a = call noalias ptr @spec_rt_alloc(i64 40, ptr @Vector_vecDestroy)
  ret ptr %a
}
define internal noalias ptr @Vector_vecNewObject() alwaysinline {
  %a = call noalias ptr @spec_rt_alloc(i64 40, ptr @Vector_vecDestroy)
  %kp = getelementptr inbounds i8, ptr %a, i64 24
  store i32 1, ptr %kp, align 8
  ret ptr %a
}
define internal noalias ptr @Vector_byteBufNew() alwaysinline {
  %b = call noalias ptr @spec_rt_alloc(i64 24, ptr @Vector_byteBufDestroy)
  ret ptr %b
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
  %dp = getelementptr inbounds %struct.SpecHeader, ptr %h, i32 0, i32 2
  %d = load ptr, ptr %dp
  %ismap = icmp eq ptr %d, @HashTable_mapDestroy
  br i1 %ismap, label %ret_map, label %chk_arr
ret_map:
  %sm = call ptr @spec_string_intern(ptr @.str.tn_map)
  ret ptr %sm
chk_arr:
  %isarr = icmp eq ptr %d, @Vector_vecDestroy
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

	Function of Str is emitMathHelpers(){
		return '''
declare double @sqrt(double) nounwind willreturn
declare double @round(double) nounwind willreturn
declare double @ceil(double) nounwind willreturn
declare double @floor(double) nounwind willreturn
declare double @fabs(double) nounwind willreturn
declare double @fmin(double, double) nounwind willreturn
declare double @fmax(double, double) nounwind willreturn
declare double @fma(double, double, double) nounwind willreturn
declare double @sin(double) nounwind willreturn
declare double @cos(double) nounwind willreturn
declare double @tan(double) nounwind willreturn
declare double @atan2(double, double) nounwind willreturn
declare double @log(double) nounwind willreturn
declare double @log2(double) nounwind willreturn
declare double @pow(double, double) nounwind willreturn
declare double @exp(double) nounwind willreturn
declare double @log10(double) nounwind willreturn
declare double @cbrt(double) nounwind willreturn
declare double @asin(double) nounwind willreturn
declare double @acos(double) nounwind willreturn
declare double @atan(double) nounwind willreturn
define internal double @spec_math_log(double %v) alwaysinline nounwind {
  %le = fcmp ole double %v, 0.0
  br i1 %le, label %z, label %ok
z:
  ret double 0.0
ok:
  %r = call double @log(double %v)
  ret double %r
}
define internal double @spec_math_log2(double %v) alwaysinline nounwind {
  %le = fcmp ole double %v, 0.0
  br i1 %le, label %z, label %ok
z:
  ret double 0.0
ok:
  %r = call double @log2(double %v)
  ret double %r
}
define internal double @spec_math_log10(double %v) alwaysinline nounwind {
  %le = fcmp ole double %v, 0.0
  br i1 %le, label %z, label %ok
z:
  ret double 0.0
ok:
  %r = call double @log10(double %v)
  ret double %r
}
define internal i64 @__spec_rng_next() alwaysinline nounwind {
  %x0 = load i64, ptr @_spec_tls_i64, align 8
  %s1 = lshr i64 %x0, 12
  %x1 = xor i64 %x0, %s1
  %s2 = shl i64 %x1, 25
  %x2 = xor i64 %x1, %s2
  %s3 = lshr i64 %x2, 27
  %x3 = xor i64 %x2, %s3
  store i64 %x3, ptr @_spec_tls_i64, align 8
  %res = mul i64 %x3, 2685821657736338717
  ret i64 %res
}
define void @spec_fast_random_seed(i64 %idx) nounwind {
  %m = mul i64 %idx, -4658895280553007687
  %a = add i64 %m, -7723592293110705685
  %s0 = xor i64 %a, -7046029254386353131
  %isz = icmp eq i64 %s0, 0
  %s1 = select i1 %isz, i64 1, i64 %s0
  store i64 %s1, ptr @_spec_tls_i64, align 8
  %r1 = call i64 @__spec_rng_next()
  %r2 = call i64 @__spec_rng_next()
  %r3 = call i64 @__spec_rng_next()
  ret void
}
declare i64 @spec_time_monotonic_ns()
define internal double @spec_math_random(double %min, double %max) alwaysinline nounwind {
  %st = load i64, ptr @_spec_tls_i64, align 8
  %uninit = icmp eq i64 %st, 0
  br i1 %uninit, label %seed, label %gen
seed:
  %addr = ptrtoint ptr @_spec_tls_i64 to i64
  %ns = call i64 @spec_time_monotonic_ns()
  %sd = xor i64 %addr, %ns
  call void @spec_fast_random_seed(i64 %sd)
  br label %gen
gen:
  %rnd = call i64 @__spec_rng_next()
  %top = lshr i64 %rnd, 11
  %flt = uitofp i64 %top to double
  %u = fmul double %flt, 0x3CA0000000000000
  %ge = fcmp oge double %min, %max
  br i1 %ge, label %ret_u, label %scale
ret_u:
  ret double %u
scale:
  %diff = fsub double %max, %min
  %prod = fmul double %u, %diff
  %res = fadd double %min, %prod
  ret double %res
}''';
	}

	Function of Str is emitCliAndAtomics(){
		return '''
@_spec_cli_argc = internal global i64 0, align 8
@_spec_cli_argv = internal global i64 0, align 8
define internal ptr @spec_cli_args_map(i64 %argc, ptr %argv) {
  store i64 %argc, ptr @_spec_cli_argc, align 8
  %av = ptrtoint ptr %argv to i64
  store i64 %av, ptr @_spec_cli_argv, align 8
  %m = call ptr @CliArgs_parseMap(ptr null, i64 %argc, i64 %av)
  ret ptr %m
}
define internal ptr @spec_process_raw_args() {
  %ac = load i64, ptr @_spec_cli_argc, align 8
  %av = load i64, ptr @_spec_cli_argv, align 8
  %r = call ptr @CliArgs_rawArgs(ptr null, i64 %ac, i64 %av)
  call ptr @spec_rt_retain(ptr %r)
  ret ptr %r
}
@_spec_atomic_levels = internal global [54 x ptr] zeroinitializer, align 8
@_spec_atomic_lock = internal global i32 0, align 4
declare i64 @llvm.ctlz.i64(i64, i1 immarg)
define internal ptr @__spec_atomic_slot_ptr(i64 %slot) {
  %lt0 = icmp slt i64 %slot, 0
  br i1 %lt0, label %ret_null, label %chk_l0
ret_null:
  ret ptr null
chk_l0:
  %in_l0 = icmp slt i64 %slot, 1024
  br i1 %in_l0, label %lvl0, label %lvl_hi
lvl0:
  br label %lookup
lvl_hi:
  %u = add i64 %slot, 1024
  %lz = call i64 @llvm.ctlz.i64(i64 %u, i1 true)
  %msb = sub i64 63, %lz
  %l_hi = sub i64 %msb, 10
  %ge54 = icmp sge i64 %l_hi, 54
  br i1 %ge54, label %ret_null, label %calc_hi
calc_hi:
  %sh = add i64 %l_hi, 10
  %base = shl i64 1, %sh
  %off_hi = sub i64 %u, %base
  br label %lookup
lookup:
  %level = phi i64 [ 0, %lvl0 ], [ %l_hi, %calc_hi ]
  %offset = phi i64 [ %slot, %lvl0 ], [ %off_hi, %calc_hi ]
  %seg_sz = phi i64 [ 1024, %lvl0 ], [ %base, %calc_hi ]
  %lp = getelementptr inbounds [54 x ptr], ptr @_spec_atomic_levels, i64 0, i64 %level
  %seg = load atomic ptr, ptr %lp acquire, align 8
  %has_seg = icmp ne ptr %seg, null
  br i1 %has_seg, label %got_seg, label %spin
spin:
  %old = atomicrmw xchg ptr @_spec_atomic_lock, i32 1 acquire, align 4
  %locked = icmp eq i32 %old, 0
  br i1 %locked, label %crit, label %spin
crit:
  %seg2 = load atomic ptr, ptr %lp monotonic, align 8
  %has_seg2 = icmp ne ptr %seg2, null
  br i1 %has_seg2, label %unlock, label %alloc_seg
alloc_seg:
  %seg_bytes = mul i64 %seg_sz, 8
  %new_seg_a = call i64 @__spec_mem_alloc(i64 %seg_bytes)
  %new_seg = inttoptr i64 %new_seg_a to ptr
  store atomic ptr %new_seg, ptr %lp release, align 8
  br label %unlock
unlock:
  %seg3 = phi ptr [ %seg2, %crit ], [ %new_seg, %alloc_seg ]
  store atomic i32 0, ptr @_spec_atomic_lock release, align 4
  br label %got_seg
got_seg:
  %s = phi ptr [ %seg, %lookup ], [ %seg3, %unlock ]
  %ep = getelementptr inbounds i64, ptr %s, i64 %offset
  ret ptr %ep
}
define internal i64 @spec_atomic_add(i64 %slot, i64 %v) {
  %p = call ptr @__spec_atomic_slot_ptr(i64 %slot)
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %zero, label %ok
zero:
  ret i64 0
ok:
  %old = atomicrmw add ptr %p, i64 %v seq_cst, align 8
  %res = add i64 %old, %v
  ret i64 %res
}
define internal i64 @spec_atomic_put(i64 %slot, i64 %v) {
  %p = call ptr @__spec_atomic_slot_ptr(i64 %slot)
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %zero, label %ok
zero:
  ret i64 0
ok:
  %old = atomicrmw xchg ptr %p, i64 %v seq_cst, align 8
  ret i64 %old
}
define internal i64 @spec_atomic_get(i64 %slot) {
  %p = call ptr @__spec_atomic_slot_ptr(i64 %slot)
  %isnull = icmp eq ptr %p, null
  br i1 %isnull, label %zero, label %ok
zero:
  ret i64 0
ok:
  %val = load atomic i64, ptr %p seq_cst, align 8
  ret i64 %val
}''';
	}

	Function of Str is emitAll(){
		return ```
{{:emitArcAndPool()}}
{{:emitClosuresAndBoxes()}}
{{:emitMemIntrinsics()}}
{{:emitTypeAndStringHelpers()}}
{{:emitMathHelpers()}}
{{:emitCliAndAtomics()}}```;
	}
}
