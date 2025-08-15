// APIパス型
export type APIPath = keyof import("./schema").paths;
// schema.ts から型ユーティリティを生成
import type { components, operations } from "./schema";

// Entry入力型
export type EntryInput = components["schemas"]["Entry-Input"];
// Entry出力型
export type EntryOutput = components["schemas"]["Entry-Output"];
// Entriesレスポンス型
export type EntriesResponse = components["schemas"]["EntriesResponse"];
// Entryレスポンス型
export type EntryResponse = components["schemas"]["EntryResponse"];

// API操作型
export type GetEntriesOperation = operations["get_entries_entries_get"];
export type AddEntryOperation = operations["add_entry_entries_post"];

// レスポンスユーティリティ
export type GetEntriesResponse =
    GetEntriesOperation["responses"][200]["content"]["application/json"];
export type AddEntryResponse = AddEntryOperation["responses"][200]["content"]["application/json"];
export type AddEntryValidationError =
    AddEntryOperation["responses"][422]["content"]["application/json"];
