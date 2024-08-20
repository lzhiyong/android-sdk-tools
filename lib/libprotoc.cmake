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

add_library(libprotoc STATIC
    ${SRC}/protobuf/src/google/protobuf/any_lite.cc
    ${SRC}/protobuf/src/google/protobuf/arena.cc
    ${SRC}/protobuf/src/google/protobuf/extension_set.cc
    ${SRC}/protobuf/src/google/protobuf/generated_enum_util.cc
    ${SRC}/protobuf/src/google/protobuf/generated_message_table_driven_lite.cc
    ${SRC}/protobuf/src/google/protobuf/generated_message_util.cc
    ${SRC}/protobuf/src/google/protobuf/implicit_weak_message.cc
    ${SRC}/protobuf/src/google/protobuf/io/coded_stream.cc
    ${SRC}/protobuf/src/google/protobuf/io/io_win32.cc
    ${SRC}/protobuf/src/google/protobuf/io/strtod.cc
    ${SRC}/protobuf/src/google/protobuf/io/zero_copy_stream.cc
    ${SRC}/protobuf/src/google/protobuf/io/zero_copy_stream_impl.cc
    ${SRC}/protobuf/src/google/protobuf/io/zero_copy_stream_impl_lite.cc
    ${SRC}/protobuf/src/google/protobuf/message_lite.cc
    ${SRC}/protobuf/src/google/protobuf/parse_context.cc
    ${SRC}/protobuf/src/google/protobuf/repeated_field.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/bytestream.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/common.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/int128.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/status.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/statusor.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/stringpiece.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/stringprintf.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/structurally_valid.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/strutil.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/time.cc
    ${SRC}/protobuf/src/google/protobuf/wire_format_lite.cc
    ${SRC}/protobuf/src/google/protobuf/any.cc
    ${SRC}/protobuf/src/google/protobuf/any.pb.cc
    ${SRC}/protobuf/src/google/protobuf/api.pb.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/importer.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/parser.cc
    ${SRC}/protobuf/src/google/protobuf/descriptor.cc
    ${SRC}/protobuf/src/google/protobuf/descriptor.pb.cc
    ${SRC}/protobuf/src/google/protobuf/descriptor_database.cc
    ${SRC}/protobuf/src/google/protobuf/duration.pb.cc
    ${SRC}/protobuf/src/google/protobuf/dynamic_message.cc
    ${SRC}/protobuf/src/google/protobuf/empty.pb.cc
    ${SRC}/protobuf/src/google/protobuf/extension_set_heavy.cc
    ${SRC}/protobuf/src/google/protobuf/field_mask.pb.cc
    ${SRC}/protobuf/src/google/protobuf/generated_message_reflection.cc
    ${SRC}/protobuf/src/google/protobuf/generated_message_table_driven.cc
    ${SRC}/protobuf/src/google/protobuf/io/gzip_stream.cc
    ${SRC}/protobuf/src/google/protobuf/io/printer.cc
    ${SRC}/protobuf/src/google/protobuf/io/tokenizer.cc
    ${SRC}/protobuf/src/google/protobuf/map_field.cc
    ${SRC}/protobuf/src/google/protobuf/message.cc
    ${SRC}/protobuf/src/google/protobuf/reflection_ops.cc
    ${SRC}/protobuf/src/google/protobuf/service.cc
    ${SRC}/protobuf/src/google/protobuf/source_context.pb.cc
    ${SRC}/protobuf/src/google/protobuf/struct.pb.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/mathlimits.cc
    ${SRC}/protobuf/src/google/protobuf/stubs/substitute.cc
    ${SRC}/protobuf/src/google/protobuf/text_format.cc
    ${SRC}/protobuf/src/google/protobuf/timestamp.pb.cc
    ${SRC}/protobuf/src/google/protobuf/type.pb.cc
    ${SRC}/protobuf/src/google/protobuf/unknown_field_set.cc
    ${SRC}/protobuf/src/google/protobuf/util/delimited_message_util.cc
    ${SRC}/protobuf/src/google/protobuf/util/field_comparator.cc
    ${SRC}/protobuf/src/google/protobuf/util/field_mask_util.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/datapiece.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/default_value_objectwriter.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/error_listener.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/field_mask_utility.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/json_escaping.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/json_objectwriter.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/json_stream_parser.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/object_writer.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/proto_writer.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/protostream_objectsource.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/protostream_objectwriter.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/type_info.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/type_info_test_helper.cc
    ${SRC}/protobuf/src/google/protobuf/util/internal/utility.cc
    ${SRC}/protobuf/src/google/protobuf/util/json_util.cc
    ${SRC}/protobuf/src/google/protobuf/util/message_differencer.cc
    ${SRC}/protobuf/src/google/protobuf/util/time_util.cc
    ${SRC}/protobuf/src/google/protobuf/util/type_resolver_util.cc
    ${SRC}/protobuf/src/google/protobuf/wire_format.cc
    ${SRC}/protobuf/src/google/protobuf/wrappers.pb.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/code_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/command_line_interface.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_enum.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_enum_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_extension.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_file.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_helpers.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_map_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_message.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_message_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_padding_optimizer.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_primitive_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_service.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/cpp/cpp_string_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_doc_comment.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_enum.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_enum_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_field_base.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_helpers.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_map_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_message.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_message_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_primitive_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_reflection_class.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_repeated_enum_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_repeated_message_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_repeated_primitive_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_source_generator_base.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/csharp/csharp_wrapper_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_context.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_doc_comment.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_enum.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_enum_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_enum_field_lite.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_enum_lite.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_extension.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_extension_lite.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_file.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_generator_factory.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_helpers.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_map_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_map_field_lite.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_message.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_message_builder.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_message_builder_lite.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_message_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_message_field_lite.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_message_lite.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_name_resolver.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_primitive_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_primitive_field_lite.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_service.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_shared_code_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_string_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/java/java_string_field_lite.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/js/js_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/js/well_known_types_embed.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_enum.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_enum_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_extension.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_file.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_helpers.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_map_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_message.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_message_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_oneof.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/objectivec/objectivec_primitive_field.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/php/php_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/plugin.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/plugin.pb.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/python/python_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/ruby/ruby_generator.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/subprocess.cc
    ${SRC}/protobuf/src/google/protobuf/compiler/zip_writer.cc
    )

target_compile_definitions(libprotoc PRIVATE -DHAVE_ZLIB=1)
target_include_directories(libprotoc PRIVATE 
    ${SRC}/protobuf/android
    ${SRC}/protobuf/src
    )
    
add_executable(protoc ${SRC}/protobuf/src/google/protobuf/compiler/main.cc)
target_include_directories(protoc PRIVATE 
    ${SRC}/protobuf/android
    ${SRC}/protobuf/src
    )
target_link_libraries(protoc libprotoc liblog dl z)