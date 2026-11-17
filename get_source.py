#!/usr/bin/env python3
#
# Copyright © 2022 Github Lzhiyong
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pylint: disable=not-callable, line-too-long, no-else-return

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION_HEADER = ROOT / 'patches/misc/platform_tools_version.h'


def tools_version():
    """read PLATFORM_TOOLS_VERSION from patches/misc/platform_tools_version.h"""
    text = VERSION_HEADER.read_text()
    match = re.search(r'^\s*#define\s+PLATFORM_TOOLS_VERSION\s+"([^"]+)"', text, re.M)
    if match is None:
        sys.exit('can not find PLATFORM_TOOLS_VERSION in {}'.format(VERSION_HEADER))
    return match.group(1)


def check(command):
    if shutil.which(command) is None:
        sys.exit('please install the {} package'.format(command))


def clone(repo, default_branch, retries):
    path = ROOT / repo['path']
    if path.exists():
        return '{} already exists, skip'.format(repo['path'])

    # Most dependencies follow the Android release snapshot. The adb module
    # also publishes Platform Tools refs, which are more accurate for adb
    # itself than the superproject snapshot. Prefer that ref when available,
    # then fall back to the shared AOSP snapshot for canary/unpublished tags.
    branches = [repo.get('branch', default_branch)]
    if repo['path'] == 'src/adb' and 'branch' not in repo:
        version = tools_version()
        adb_version = '37.0.1' if version == '37.0.2' else version
        adb_ref = 'platform-tools-' + adb_version
        if adb_ref not in branches:
            branches.insert(0, adb_ref)

    last_error = ''
    for branch in branches:
        command = ['git', 'clone', '-q', '-c', 'advice.detachedHead=false',
                   '--depth', '1', '--branch', branch, repo['url'], str(path)]
        for attempt in range(1, retries + 1):
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                return 'cloned {} ({})'.format(repo['path'], branch)
            last_error = result.stderr
            shutil.rmtree(path, ignore_errors=True)
            if attempt < retries:
                time.sleep(5 * attempt)
    raise RuntimeError('failed to clone {} (tried {}):\n{}'.format(
        repo['url'], ', '.join(branches), last_error))


def replace_in_file(path, old, new):
    path = ROOT / path
    if path.exists():
        text = path.read_text()
        if old in text:
            path.write_text(text.replace(old, new))


def apply_patch(patch):
    """apply a patch file if it is applicable, the patch files of this project
    use different path prefixes, so try both the project root and src/"""
    for workdir in (ROOT, ROOT / 'src'):
        base = ['patch', '-p1', '-s', '-f', '-d', str(workdir), '-i', str(patch)]
        if subprocess.run(base + ['-N', '--dry-run'], capture_output=True).returncode == 0:
            subprocess.run(base + ['-N'], check=True)
            return 'applied'
        if subprocess.run(base + ['-R', '--dry-run'], capture_output=True).returncode == 0:
            return 'already applied'
    return 'not applicable for this version, skipped'


def ensure_art_build_defines():
    """Keep ART's stack/frame limits available in standalone NDK builds.

    The upstream Soong build normally injects these target-specific defines.
    This project builds ART sources outside Soong, so provide the same
    conservative values in the shared header when they are absent.
    """
    path = ROOT / 'src/art/libartbase/arch/instruction_set.h'
    if not path.exists():
        raise RuntimeError('ART instruction_set.h not found: {}'.format(path))

    text = path.read_text()
    marker = 'namespace art {'
    if marker not in text:
        raise RuntimeError('cannot locate namespace art in {}'.format(path))

    definitions = {
        'ART_STACK_OVERFLOW_GAP_arm': 16384,
        'ART_STACK_OVERFLOW_GAP_arm64': 16384,
        'ART_STACK_OVERFLOW_GAP_riscv64': 16384,
        'ART_STACK_OVERFLOW_GAP_x86': 16384,
        'ART_STACK_OVERFLOW_GAP_x86_64': 20480,
        'ART_FRAME_SIZE_LIMIT': 10000,
    }
    # Ignore commented-out Soong examples: they contain the same #define
    # spellings but do not provide macros to the C++ preprocessor.
    active_text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)

    missing = []
    for name, value in definitions.items():
        if not re.search(r'^\s*#\s*define\s+' + re.escape(name) + r'\b', active_text, re.M):
            missing.append('#ifndef {}\n#define {} {}\n#endif'.format(name, name, value))

    if missing:
        block = (
            '// Standalone NDK build equivalents of the defines normally supplied by Soong.\n'
            + '\n'.join(missing)
            + '\n\n'
        )
        text = text.replace(marker, block + marker, 1)
        path.write_text(text)
        print('ART standalone build defines: added {}'.format(', '.join(
            name for name in definitions if name not in active_text)), flush=True)

        # Fail early if a required definition is still absent after editing.
        verified = re.sub(r'/\*.*?\*/|//[^\n]*', '', path.read_text(), flags=re.S)
        unresolved = [
            name for name in definitions
            if not re.search(r'^\s*#\s*define\s+' + re.escape(name) + r'\b', verified, re.M)
        ]
        if unresolved:
            raise RuntimeError('failed to add ART build defines: {}'.format(', '.join(unresolved)))
    else:
        print('ART standalone build defines: already present', flush=True)



def ensure_openscreen_task_runner_compat():
    """Avoid libc++'s unsupported packaged_task<void() noexcept> specialization.

    NDK r27c's libc++ does not provide this specialization when compiling
    Open Screen with the standalone NDK toolchain. AOSP's existing patch may
    not match every platform-tools tag, so normalize the alias after patches.
    """
    path = ROOT / 'src/openscreen/platform/api/task_runner.h'
    if not path.exists():
        raise RuntimeError('Open Screen task_runner.h not found: {}'.format(path))

    text = path.read_text()
    fixed = re.sub(
        r'std::packaged_task\s*<\s*void\s*\(\s*\)\s*noexcept\s*>',
        'std::packaged_task<void()>',
        text,
    )
    if fixed != text:
        path.write_text(fixed)
        print('Open Screen standalone build: normalized packaged_task<void() noexcept>', flush=True)

    verified = path.read_text()
    if 'std::packaged_task<void()>' not in verified:
        raise RuntimeError('Open Screen Task alias is not compatible with NDK libc++: {}'.format(path))
    if 'std::packaged_task<void() noexcept>' in verified:
        raise RuntimeError('unsupported noexcept packaged_task alias remains in {}'.format(path))



def ensure_art_metrics_memory_order_compat():
    """Normalize malformed ART memory_order enum qualification for libc++."""
    path = ROOT / 'src/art/libartbase/base/metrics/metrics.h'
    if not path.exists():
        raise RuntimeError('ART metrics.h not found: {}'.format(path))

    text = path.read_text()
    fixed = re.sub(
        r'std::memory_order::(memory_order_(?:relaxed|consume|acquire|release|acq_rel|seq_cst))',
        r'std::\1',
        text,
    )
    if fixed != text:
        path.write_text(fixed)
        print('ART metrics: normalized malformed std::memory_order enumerators', flush=True)

    verified = path.read_text()
    if re.search(r'std::memory_order::memory_order_', verified):
        raise RuntimeError('malformed std::memory_order enumerator remains in {}'.format(path))



def ensure_art_hash_set_allocator_compat():
    """Use allocator_traits instead of allocator members removed in C++20."""
    path = ROOT / 'src/art/libartbase/base/hash_set.h'
    if not path.exists():
        raise RuntimeError('ART hash_set.h not found: {}'.format(path))

    text = path.read_text()
    destroy_pattern = (
        r'allocfn_\.destroy\(\s*allocfn_\.address\(\s*([^()]+?)\s*\)\s*\)\s*;'
    )
    construct_pattern = (
        r'allocfn_\.construct\(\s*allocfn_\.address\(\s*([^()]+?)\s*\)\s*\)\s*;'
    )
    text, destroyed = re.subn(
        destroy_pattern,
        r'std::allocator_traits<allocator_type>::destroy(allocfn_, std::addressof(\1));',
        text,
    )
    text, constructed = re.subn(
        construct_pattern,
        r'std::allocator_traits<allocator_type>::construct(allocfn_, std::addressof(\1));',
        text,
    )
    if destroyed + constructed == 0 and re.search(r'allocfn_\.(?:construct|destroy)\s*\(', text):
        raise RuntimeError('unrecognized legacy allocator calls in {}'.format(path))
    if destroyed + constructed:
        path.write_text(text)
        print(
            'ART HashSet: migrated {} allocator construct and {} destroy calls to allocator_traits'.format(
                constructed, destroyed
            ),
            flush=True,
        )

    verified = path.read_text()
    if re.search(r'allocfn_\.(?:construct|destroy|address)\s*\(', verified):
        raise RuntimeError('C++20-incompatible allocator member remains in {}'.format(path))


def ensure_libbase_ndk_private_property_api():
    """Expose bionic's private property serial declarations to standalone NDK builds.

    libbase uses __system_property_area_serial/__system_property_serial, which
    are intentionally hidden from the public NDK header. The matching NDK
    sys/_system_properties.h declares these APIs when the opt-in macro is set.
    """
    path = ROOT / 'src/libbase/properties.cpp'
    if not path.exists():
        raise RuntimeError('libbase properties.cpp not found: {}'.format(path))

    text = path.read_text()
    public_include = '#include <sys/system_properties.h>'
    private_include = '#include <sys/_system_properties.h>'
    if private_include not in text:
        if public_include not in text:
            raise RuntimeError('cannot locate system_properties.h include in {}'.format(path))
        text = text.replace(
            public_include,
            public_include + '\n#define _REALLY_INCLUDE_SYS__SYSTEM_PROPERTIES_H_\n' + private_include,
            1,
        )
        path.write_text(text)
        print('libbase: enabled bionic private property serial declarations', flush=True)

    verified = path.read_text()
    if private_include not in verified or '_REALLY_INCLUDE_SYS__SYSTEM_PROPERTIES_H_' not in verified:
        raise RuntimeError('libbase private property declarations were not enabled in {}'.format(path))



def ensure_liblog_ndk_private_property_api():
    """Expose bionic private property serial declarations to standalone liblog builds."""
    path = ROOT / 'src/logging/liblog/properties.cpp'
    if not path.exists():
        raise RuntimeError('liblog properties.cpp not found: {}'.format(path))
    text = path.read_text()
    public_include = '#include <sys/system_properties.h>'
    private_include = '#include <sys/_system_properties.h>'
    if private_include not in text:
        if public_include not in text:
            raise RuntimeError('cannot locate system_properties.h include in {}'.format(path))
        text = text.replace(
            public_include,
            public_include + '\n#define _REALLY_INCLUDE_SYS__SYSTEM_PROPERTIES_H_\n' + private_include,
            1,
        )
        path.write_text(text)
        print('liblog: enabled bionic private property serial declarations', flush=True)
    verified = path.read_text()
    if private_include not in verified or '_REALLY_INCLUDE_SYS__SYSTEM_PROPERTIES_H_' not in verified:
        raise RuntimeError('liblog private property declarations were not enabled in {}'.format(path))


def ensure_liblog_api37_ndk_compat():
    """Keep liblog's timestamped logger implementation usable below API 37.

    The exported API is retained, but the API-30 logger delegates to a private
    implementation rather than calling an API-37 annotated declaration.
    """
    path = ROOT / 'src/logging/liblog/logger_write.cpp'
    if not path.exists():
        raise RuntimeError('liblog logger_write.cpp not found: {}'.format(path))
    text = path.read_text()
    public_name = '__android_log_logd_logger_with_timestamp'
    impl_name = 'logd_logger_with_timestamp_impl'
    old_call = public_name + '(log_message, nullptr);'

    if impl_name not in text:
        signature = 'void ' + public_name + '('
        signature_pos = text.find(signature)
        if signature_pos < 0:
            raise RuntimeError('cannot locate {} definition in {}'.format(public_name, path))

        # Preserve the exported API symbol while moving its body to a private helper.
        body_open = text.find('{', signature_pos)
        if body_open < 0:
            raise RuntimeError('cannot locate timestamp logger function body in {}'.format(path))
        depth = 0
        body_close = -1
        for index in range(body_open, len(text)):
            if text[index] == '{':
                depth += 1
            elif text[index] == '}':
                depth -= 1
                if depth == 0:
                    body_close = index
                    break
        if body_close < 0:
            raise RuntimeError('unterminated timestamp logger function in {}'.format(path))

        text = text[:signature_pos] + text[signature_pos:].replace(
            signature, 'static void ' + impl_name + '(', 1
        )
        text = text.replace(old_call, impl_name + '(log_message, nullptr);', 1)

        wrapper = (
            '\n\nvoid ' + public_name + '(\n'
            '    const struct __android_log_message* log_message,\n'
            '    const struct timespec* timestamp) {\n'
            '  ' + impl_name + '(log_message, timestamp);\n'
            '}\n'
        )
        # Re-find the renamed implementation and its closing brace after edits.
        impl_pos = text.find('static void ' + impl_name + '(')
        impl_open = text.find('{', impl_pos)
        depth = 0
        impl_close = -1
        for index in range(impl_open, len(text)):
            if text[index] == '{':
                depth += 1
            elif text[index] == '}':
                depth -= 1
                if depth == 0:
                    impl_close = index
                    break
        if impl_close < 0:
            raise RuntimeError('unterminated private timestamp logger implementation in {}'.format(path))
        text = text[:impl_close + 1] + wrapper + text[impl_close + 1:]

        # The API-30 wrapper appears before the helper definition.
        wrapper_pos = text.find('void __android_log_logd_logger(')
        if wrapper_pos < 0:
            raise RuntimeError('cannot locate API-30 logger wrapper in {}'.format(path))
        declaration = (
            'static void ' + impl_name + '(\n'
            '    const struct __android_log_message* log_message,\n'
            '    const struct timespec* timestamp);\n\n'
        )
        text = text[:wrapper_pos] + declaration + text[wrapper_pos:]
        path.write_text(text)
        print('liblog: isolated API-37 timestamp logger behind a private helper', flush=True)

    verified = path.read_text()
    if old_call in verified:
        raise RuntimeError('API-30 logger still calls the API-37 timestamp API in {}'.format(path))
    if 'static void ' + impl_name + '(' not in verified:
        raise RuntimeError('private timestamp logger implementation missing in {}'.format(path))
    if 'void ' + public_name + '(' not in verified:
        raise RuntimeError('exported timestamp logger API missing in {}'.format(path))





def ensure_androidfw_combined_iterator_swap_compat():
    """Make CombinedIterator's proxy reference swappable when dereference returns a temporary."""
    path = ROOT / 'src/base/libs/androidfw/include/androidfw/CombinedIterator.h'
    if not path.exists():
        raise RuntimeError('CombinedIterator.h not found: {}'.format(path))
    text = path.read_text()
    anchor = 'friend void swap(RefPair& l, RefPair& r)'
    if anchor in text and 'friend void swap(RefPair&& l, RefPair&& r)' not in text:
        start = text.find(anchor)
        brace = text.find('{', start)
        depth = 0
        end = -1
        for index in range(brace, len(text)):
            if text[index] == '{':
                depth += 1
            elif text[index] == '}':
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end < 0:
            raise RuntimeError('cannot locate RefPair swap body in {}'.format(path))
        body = text[start:end]
        rvalue_body = body.replace('friend void swap(RefPair& l, RefPair& r)',
                                   'friend void swap(RefPair&& l, RefPair&& r)', 1)
        text = text[:end] + '\n\n  ' + rvalue_body.strip() + text[end:]
        path.write_text(text)
        print('androidfw: added rvalue RefPair swap for proxy iterators', flush=True)
    verified = path.read_text()
    if 'friend void swap(RefPair&& l, RefPair&& r)' not in verified:
        raise RuntimeError('rvalue RefPair swap overload missing in {}'.format(path))


def ensure_boringssl_arm_asm_comment_compat():
    """Avoid apostrophes in ARM assembly comments being tokenized by the C preprocessor."""
    path = ROOT / 'src/boringssl/src/gen/bcm/vpaes-armv7-linux.S'
    if not path.exists():
        return
    text = path.read_text()
    fixed = text.replace("Apple's toolchain", 'Apple toolchain')
    if fixed != text:
        path.write_text(fixed)
        print('BoringSSL: normalized apostrophe in ARM assembly comment', flush=True)
    if "Apple's toolchain" in path.read_text():
        raise RuntimeError('preprocessor-incompatible apostrophe remains in {}'.format(path))


def ensure_expat_android_entropy_source():
    """Select Expat's supported /dev/urandom entropy source on Android."""
    path = ROOT / 'CMakeLists.txt'
    text = path.read_text()
    anchor = 'add_subdirectory(src/expat/expat EXCLUDE_FROM_ALL)'
    definition = anchor + '\nif(TARGET expat)\n    target_compile_definitions(expat PRIVATE XML_DEV_URANDOM)\nendif()'
    if anchor not in text:
        raise RuntimeError('cannot locate Expat subdirectory in {}'.format(path))
    if 'target_compile_definitions(expat PRIVATE XML_DEV_URANDOM)' not in text:
        text = text.replace(anchor, definition, 1)
        path.write_text(text)
        print('Expat: enabled Android /dev/urandom entropy source', flush=True)
    if 'target_compile_definitions(expat PRIVATE XML_DEV_URANDOM)' not in path.read_text():
        raise RuntimeError('Expat Android entropy definition missing in {}'.format(path))



def ensure_androidfw_locale_constexpr_compat():
    """Remove invalid constexpr from locale packers using reinterpret_cast."""
    path = ROOT / 'src/base/libs/androidfw/include/androidfw/LocaleDataLookup.h'
    if not path.exists():
        raise RuntimeError('LocaleDataLookup.h not found')
    text = path.read_text()
    fixed = text.replace('constexpr inline uint32_t packLocale(', 'inline uint32_t packLocale(')
    fixed = fixed.replace('constexpr inline uint32_t packScript(', 'inline uint32_t packScript(')
    if fixed != text:
        path.write_text(fixed)
        print('androidfw: removed invalid locale constexpr', flush=True)
    verified = path.read_text()
    if 'constexpr inline uint32_t packLocale(' in verified or 'constexpr inline uint32_t packScript(' in verified:
        raise RuntimeError('invalid locale constexpr remains')



def ensure_bionic_private_property_headers():
    """Expose Bionic private property serial APIs before including the public header."""
    sources = (
        'src/libbase/properties.cpp',
        'src/logging/liblog/properties.cpp',
        'src/core/libcutils/trace-dev.inc',
    )
    public_include = '#include <sys/system_properties.h>'
    private_include = '#include <sys/_system_properties.h>'
    opt_in = '#define _REALLY_INCLUDE_SYS__SYSTEM_PROPERTIES_H_'

    for relative in sources:
        path = ROOT / relative
        if not path.exists():
            continue
        text = path.read_text()
        if public_include not in text:
            continue

        # Normalize any earlier insertion: the opt-in must be defined before
        # system_properties.h is first included, otherwise the private header
        # exposes only the public overloads.
        text = text.replace(opt_in + '\n', '')
        text = text.replace(private_include + '\n', '')
        text = text.replace(
            public_include,
            opt_in + '\n' + public_include + '\n' + private_include,
            1,
        )
        path.write_text(text)

        verified = path.read_text()
        expected = opt_in + '\n' + public_include + '\n' + private_include
        if expected not in verified:
            raise RuntimeError('Bionic private property header order is incorrect in {}'.format(path))
        print('bionic: enabled private property serial APIs in {}'.format(relative), flush=True)

def patches():
    inc = ROOT / 'src/incremental_delivery/sysprop/include'
    inc.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'patches/misc/IncrementalProperties.sysprop.h', inc)
    shutil.copy2(ROOT / 'patches/misc/IncrementalProperties.sysprop.cpp', inc.parent)

    shutil.copy2(ROOT / 'patches/misc/deployagent.inc', ROOT / 'src/adb/fastdeploy/deployagent')
    shutil.copy2(ROOT / 'patches/misc/deployagentscript.inc', ROOT / 'src/adb/fastdeploy/deployagent')

    shutil.copy2(VERSION_HEADER, ROOT / 'src/soong/cc/libbuildversion/include')

    aapt2 = 'src/base/tools/aapt2/'
    replace_in_file(aapt2 + 'ApkInfo.proto', 'frameworks/base/tools/aapt2/Resources.proto', 'Resources.proto')
    replace_in_file(aapt2 + 'Resources.proto', 'frameworks/base/tools/aapt2/Configuration.proto', 'Configuration.proto')
    replace_in_file(aapt2 + 'ResourcesInternal.proto', 'frameworks/base/tools/aapt2/Configuration.proto', 'Configuration.proto')
    replace_in_file(aapt2 + 'ResourcesInternal.proto', 'frameworks/base/tools/aapt2/Resources.proto', 'Resources.proto')

    replace_in_file('src/abseil-cpp/CMakeLists.txt', '/usr/src/googletest', '${CMAKE_SOURCE_DIR}/src/googletest')

    # symlink googletest to boringssl/**/googletest
    dest = ROOT / 'src/boringssl/src/third_party/googletest'
    if dest.parent.exists() and not dest.exists():
        dest.symlink_to(ROOT / 'src/googletest')

    # the source patches only apply to specific versions, apply them when possible
    for patch in sorted((ROOT / 'patches').rglob('*.patch')):
        print('patch {}: {}'.format(patch.relative_to(ROOT), apply_patch(patch)))

    ensure_art_build_defines()
    ensure_openscreen_task_runner_compat()
    ensure_art_metrics_memory_order_compat()
    ensure_art_hash_set_allocator_compat()
    ensure_libbase_ndk_private_property_api()
    ensure_androidfw_combined_iterator_swap_compat()
    ensure_androidfw_locale_constexpr_compat()
    ensure_boringssl_arm_asm_comment_compat()
    ensure_expat_android_entropy_source()
    ensure_bionic_private_property_headers()
    ensure_liblog_ndk_private_property_api()
    ensure_liblog_api37_ndk_compat()



def ensure_androidfw_combined_iterator_swap_compat():
    """Add an ADL-visible rvalue swap overload for CombinedIterator proxy references."""
    path = ROOT / 'src/base/libs/androidfw/include/androidfw/CombinedIterator.h'
    if not path.exists():
        raise RuntimeError('CombinedIterator.h not found: {}'.format(path))
    text = path.read_text()
    signature = 'friend void swap(RefPair& l, RefPair& r)'
    rvalue_signature = 'friend void swap(RefPair&& l, RefPair&& r)'
    if rvalue_signature not in text:
        start = text.find(signature)
        if start < 0:
            raise RuntimeError('RefPair lvalue swap overload not found in {}'.format(path))
        brace = text.find('{', start)
        depth = 0
        end = -1
        for index in range(brace, len(text)):
            if text[index] == '{':
                depth += 1
            elif text[index] == '}':
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end < 0:
            raise RuntimeError('cannot parse RefPair swap body in {}'.format(path))
        body = text[start:end]
        overload = body.replace(signature, rvalue_signature, 1)
        text = text[:end] + '\n\n  ' + overload.strip() + text[end:]
        path.write_text(text)
        print('androidfw: installed rvalue RefPair swap overload', flush=True)
    if rvalue_signature not in path.read_text():
        raise RuntimeError('rvalue RefPair swap overload missing after patch')


def ensure_androidfw_locale_constexpr_compat():
    """Make reinterpret_cast-based locale packers ordinary inline functions."""
    import re
    path = ROOT / 'src/base/libs/androidfw/include/androidfw/LocaleDataLookup.h'
    if not path.exists():
        raise RuntimeError('LocaleDataLookup.h not found: {}'.format(path))
    text = path.read_text()
    fixed = re.sub(
        r'\bconstexpr\s+(?=(?:inline\s+)?uint32_t\s+pack(?:Locale|Script)\s*\()',
        '',
        text,
    )
    if fixed != text:
        path.write_text(fixed)
        print('androidfw: removed invalid constexpr from locale packers', flush=True)
    verified = path.read_text()
    if re.search(r'\bconstexpr\s+(?=(?:inline\s+)?uint32_t\s+pack(?:Locale|Script)\s*\()', verified):
        raise RuntimeError('invalid locale packer constexpr remains in {}'.format(path))


def ensure_expat_android_entropy_source():
    """Enable Expat's real /dev/urandom entropy implementation for Android."""
    path = ROOT / 'CMakeLists.txt'
    text = path.read_text()
    anchor = 'add_subdirectory(src/expat/expat EXCLUDE_FROM_ALL)'
    if anchor not in text:
        raise RuntimeError('cannot locate Expat subdirectory in {}'.format(path))
    definition = 'add_compile_definitions(XML_DEV_URANDOM)'
    if definition not in text:
        text = text.replace(anchor, definition + '\n' + anchor, 1)
        path.write_text(text)
        print('Expat: enabled XML_DEV_URANDOM globally before adding Expat', flush=True)
    if definition not in path.read_text():
        raise RuntimeError('XML_DEV_URANDOM definition missing from {}'.format(path))



def ensure_androidfw_generated_resource_header():
    """Install the aconfig header normally generated by the Android build system."""
    source = ROOT / 'patches/include/android_content_res.h'
    target = ROOT / 'src/base/libs/androidfw/include/android_content_res.h'
    if not source.exists():
        raise RuntimeError('android_content_res.h compatibility header missing: {}'.format(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if not target.exists():
        raise RuntimeError('failed to install {}'.format(target))
    print('androidfw: installed generated aconfig resource header', flush=True)


def ensure_androidfw_resize_and_overwrite_compat():
    """Replace resize_and_overwrite with equivalent C++17 resize + callback logic."""
    candidates = (
        ROOT / 'src/base/libs/androidfw/Util.cpp',
        ROOT / 'src/libbase/file.cpp',
    )
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text()
        marker = 'resize_and_overwrite('
        if marker not in text:
            continue
        start = text.find(marker)
        receiver_match = re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*(?:->|\.)\s*
    version = tools_version()
    parser = argparse.ArgumentParser()
    parser.add_argument('--tags', default='platform-tools-{}'.format(version),
                        help='git tag or branch of the AOSP repositories, default is platform-tools-{} '
                             '(from patches/misc/platform_tools_version.h)'.format(version))
    parser.add_argument('--jobs', type=int, default=8, help='clone N repositories in parallel')
    parser.add_argument('--retries', type=int, default=3, help='retry times of a failed clone')
    parser.add_argument('--skip-patch', action='store_true', help='only clone, do not patch the sources')
    args = parser.parse_args()

    # check necessary packages
    for command in ('git', 'patch', 'go', 'bison', 'flex'):
        check(command)

    repos = json.loads((ROOT / 'repository.json').read_text())
    print('fetching sources: {}'.format(args.tags))
    errors = []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = [pool.submit(clone, repo, args.tags, args.retries) for repo in repos]
        for future in as_completed(futures):
            try:
                print(future.result(), flush=True)
            except RuntimeError as e:
                errors.append(str(e))
    if errors:
        sys.exit('\n'.join(errors))

    if not args.skip_patch:
        patches()
        ensure_expat_android_entropy_source()
        ensure_androidfw_generated_resource_header()
        ensure_androidfw_combined_iterator_swap_compat()
        ensure_androidfw_locale_constexpr_compat()
        ensure_androidfw_resize_and_overwrite_compat()
        ensure_androidfw_resize_and_overwrite_compat()

    print('download success!!')


if __name__ == '__main__':
    main()
, text[:start])
        if receiver_match is None:
            raise RuntimeError('cannot identify resize_and_overwrite receiver in {}'.format(path))
        receiver = receiver_match.group(1)
        access = text[receiver_match.end(1):start].strip()
        open_paren = start + len('resize_and_overwrite')
        depth = 0
        comma = -1
        close_paren = -1
        for index in range(open_paren, len(text)):
            char = text[index]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    close_paren = index
                    break
            elif char == ',' and depth == 1 and comma < 0:
                comma = index
        if comma < 0 or close_paren < 0:
            raise RuntimeError('cannot parse resize_and_overwrite call in {}'.format(path))
        size_expr = text[open_paren + 1:comma].strip()
        callback = text[comma + 1:close_paren].strip()
        if not callback.startswith('['):
            raise RuntimeError('unexpected resize_and_overwrite callback in {}'.format(path))
        member = '.' if access == '.' else '->'
        replacement = (
            receiver + member + 'resize(' + size_expr + ');\n'
            + receiver + member + 'resize((' + callback + ')('
            + receiver + member + 'data(), ' + receiver + member + 'size()))'
        )
        text = text[:receiver_match.start(1)] + replacement + text[close_paren + 1:]
        path.write_text(text)
        if marker in path.read_text():
            raise RuntimeError('resize_and_overwrite remains in {}'.format(path))
        print('C++17: replaced resize_and_overwrite in {}'.format(path.relative_to(ROOT)), flush=True)


def main():
    version = tools_version()
    parser = argparse.ArgumentParser()
    parser.add_argument('--tags', default='platform-tools-{}'.format(version),
                        help='git tag or branch of the AOSP repositories, default is platform-tools-{} '
                             '(from patches/misc/platform_tools_version.h)'.format(version))
    parser.add_argument('--jobs', type=int, default=8, help='clone N repositories in parallel')
    parser.add_argument('--retries', type=int, default=3, help='retry times of a failed clone')
    parser.add_argument('--skip-patch', action='store_true', help='only clone, do not patch the sources')
    args = parser.parse_args()

    # check necessary packages
    for command in ('git', 'patch', 'go', 'bison', 'flex'):
        check(command)

    repos = json.loads((ROOT / 'repository.json').read_text())
    print('fetching sources: {}'.format(args.tags))
    errors = []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = [pool.submit(clone, repo, args.tags, args.retries) for repo in repos]
        for future in as_completed(futures):
            try:
                print(future.result(), flush=True)
            except RuntimeError as e:
                errors.append(str(e))
    if errors:
        sys.exit('\n'.join(errors))

    if not args.skip_patch:
        patches()
        ensure_expat_android_entropy_source()
        ensure_androidfw_locale_constexpr_compat()
        ensure_androidfw_combined_iterator_swap_compat()

    print('download success!!')


if __name__ == '__main__':
    main()
