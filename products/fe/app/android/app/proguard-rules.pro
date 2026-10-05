# fbjni is called by ExecuTorch's native code; R8 cannot see these JNI lookups.
# In particular, removing its exception/HybridData classes aborts PTE loading.
-keep class com.facebook.jni.** { *; }
